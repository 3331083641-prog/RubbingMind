"""Artifact-clustered bootstrap CIs for the v2 and v2-text batches (derived, read-only).

For every split x method x degradation group (plus degradation='ALL'), and for
three scopes (all rows / processed rows / passthrough rows, from
derived/applied_status.json), this reports per metric:

  rowMean        plain mean over rows (the convention of grouped_summary *Mean)
  artifactMean   mean of per-artifact means (the statistic that is bootstrapped)
  ci95           2.5/97.5 percentiles of 1000 resampled artifact means
  gain*          the same for paired gain = output metric - input metric, where the
                 input metric is the 'degraded' row of the same caseId.
                 psnr/ssim/edgeF1 are higher-is-better, so gain > 0 is an improvement.

Each CI uses a fresh numpy.random.default_rng(SEED); the resampling draws
(BOOTSTRAP, K) artifact indices with replacement, K = artifacts in the group.
Groups with K < MIN_RELIABLE_ARTIFACTS are flagged ciReliable=false; empty groups
are null. Historical results files are only read.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SEED = 20261019
BOOTSTRAP = 1000
MIN_RELIABLE_ARTIFACTS = 3
METRICS = ('psnr', 'ssim', 'edgeF1')
SCOPES = ('all', 'processed', 'passthrough')
BATCHES = ('2026-10-17-v2', '2026-10-17-v2-text')


def bootstrap(per_artifact: dict, seed=SEED, n=BOOTSTRAP):
    """per_artifact: sampleId -> list of values. Returns (artifactMean, [lo, hi]) or (None, None)."""
    groups = [float(np.mean(v)) for _, v in sorted(per_artifact.items()) if v]
    if not groups:
        return None, None
    rng = np.random.default_rng(seed)
    draws = rng.choice(np.array(groups), (n, len(groups)), replace=True).mean(axis=1)
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return float(np.mean(groups)), [float(lo), float(hi)]


def _scope_ok(scope, passthrough):
    if scope == 'all':
        return True
    if scope == 'processed':
        return passthrough is False
    return passthrough is True


def stat_block(rows, value_of, seed=SEED):
    per = {}
    values = []
    for r in rows:
        v = value_of(r)
        if v is None:
            continue
        per.setdefault(r['sampleId'], []).append(v)
        values.append(v)
    artifact_mean, ci = bootstrap(per, seed)
    return {
        'rowMean': float(np.mean(values)) if values else None,
        'artifactMean': artifact_mean, 'ci95': ci,
        'valueN': len(values), 'valueArtifactN': len(per),
    }


def load_batch(batch_dir: Path, derived_dir: Path):
    data = json.loads((batch_dir / 'results.json').read_text(encoding='utf-8'))
    status = json.loads((derived_dir / 'applied_status.json').read_text(encoding='utf-8'))
    rows = data['rows']
    if len(status['rows']) != len(rows):
        raise ValueError('派生状态行数与结果文件不一致')
    for index, (row, derived) in enumerate(zip(rows, status['rows'])):
        if derived['rowIndex'] != index or derived['sampleId'] != row['sampleId'] or derived['method'] != row['method']:
            raise ValueError(f'派生状态第 {index} 行与结果不对齐')
    baseline = {r['caseId']: r for r in rows if r['method'] == 'degraded'}
    joined = []
    for row, derived in zip(rows, status['rows']):
        if row.get('error'):
            continue
        base = baseline.get(row['caseId'])
        item = {'sampleId': row['sampleId'], 'split': row['split'], 'method': row['method'],
                'degradation': row['degradation'], 'caseId': row['caseId'],
                'isPassthrough': derived['isPassthrough'], 'appliedStatus': derived['appliedStatus']}
        for metric in METRICS:
            item[metric] = row.get(metric)
            item[metric + 'Gain'] = (row[metric] - base[metric]) if base and row.get(metric) is not None and base.get(metric) is not None else None
        joined.append(item)
    return data, status, joined


def compute(joined, config_seed=None):
    out = []
    keys = sorted({(r['split'], r['method'], r['degradation']) for r in joined})
    keys += sorted({(s, m, 'ALL') for s, m, _ in keys})
    for split, method, degradation in keys:
        group = [r for r in joined if r['split'] == split and r['method'] == method and (degradation == 'ALL' or r['degradation'] == degradation)]
        for scope in SCOPES:
            rows = [r for r in group if _scope_ok(scope, r['isPassthrough'])]
            artifacts = len({r['sampleId'] for r in rows})
            entry = {'split': split, 'method': method, 'degradation': degradation, 'scope': scope,
                     'rowN': len(rows), 'artifactN': artifacts, 'seed': SEED, 'bootstrap': BOOTSTRAP,
                     'ciReliable': artifacts >= MIN_RELIABLE_ARTIFACTS,
                     'ciNote': None if artifacts >= MIN_RELIABLE_ARTIFACTS else ('空组' if artifacts == 0 else f'文物数 {artifacts} < {MIN_RELIABLE_ARTIFACTS}，CI 不可靠')}
            for metric in METRICS:
                for kind, field in (('', metric), ('Gain', metric + 'Gain')):
                    block = stat_block(rows, lambda r, f=field: r[f]) if rows else {'rowMean': None, 'artifactMean': None, 'ci95': None, 'valueN': 0, 'valueArtifactN': 0}
                    name = metric + kind
                    entry[name + 'RowMean'] = block['rowMean']
                    entry[name + 'ArtifactMean'] = block['artifactMean']
                    entry[name + 'CI95Low'] = block['ci95'][0] if block['ci95'] else None
                    entry[name + 'CI95High'] = block['ci95'][1] if block['ci95'] else None
                    entry[name + 'ValueN'] = block['valueN']
                    if kind == 'Gain':
                        ci = block['ci95']
                        entry[name + 'Sign'] = None if ci is None else ('zero' if ci[0] == 0 == ci[1] else 'positive' if ci[0] > 0 else 'negative' if ci[1] < 0 else 'spans_zero')
            out.append(entry)
    return out


def compare_with_grouped_summary(data, results):
    """Stored summary: split x method, all rows, rows with error excluded; CI from a shared rng."""
    from experiments.run_v2 import grouped_summary
    replay = grouped_summary([dict(r, isPassthrough=None) for r in data['rows']], data['config']['seed'])
    stored = {(s['split'], s['method']): s for s in data['summary']}
    mine = {(e['split'], e['method']): e for e in results if e['degradation'] == 'ALL' and e['scope'] == 'all'}
    report = []
    for item in replay:
        key = (item['split'], item['method'])
        old = stored.get(key)
        new = mine.get(key)
        if old is None or new is None:
            continue
        for metric in METRICS:
            report.append({
                'split': key[0], 'method': key[1], 'metric': metric,
                'storedMean': old[metric + 'Mean'], 'myRowMean': new[metric + 'RowMean'],
                'meanAbsDiff': abs(old[metric + 'Mean'] - new[metric + 'RowMean']),
                'storedCI95': old[metric + 'CI95'], 'replayCI95': item[metric + 'CI95'],
                'replayReproducesStored': bool(np.allclose(old[metric + 'CI95'], item[metric + 'CI95'], rtol=0, atol=1e-12)),
                'myCI95': [new[metric + 'CI95Low'], new[metric + 'CI95High']],
                'ciEndpointMaxAbsDiff': max(abs(old[metric + 'CI95'][0] - new[metric + 'CI95Low']), abs(old[metric + 'CI95'][1] - new[metric + 'CI95High'])),
            })
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', default=str(ROOT))
    parser.add_argument('--output-root', default=str(ROOT))
    args = parser.parse_args(argv)
    source = Path(args.source_root).resolve() / 'experiments/results'
    target = Path(args.output_root).resolve() / 'experiments/results'
    printed = []
    for batch in BATCHES:
        derived_dir = target / batch / 'derived'
        data, status, joined = load_batch(source / batch, derived_dir)
        results = compute(joined)
        comparison = compare_with_grouped_summary(data, results)
        payload = {
            'batch': batch, 'experimentId': data['config']['experimentId'],
            'derivedAt': datetime.now(timezone.utc).isoformat(), 'derivedBy': 'experiments/ci_by_artifact.py',
            'seed': SEED, 'bootstrap': BOOTSTRAP, 'percentiles': [2.5, 97.5], 'minReliableArtifacts': MIN_RELIABLE_ARTIFACTS,
            'rngRule': 'each CI uses a fresh numpy.random.default_rng(seed); resample (bootstrap, K) artifact means with replacement',
            'gainDefinition': 'output metric minus the degraded (input) row of the same caseId; psnr/ssim/edgeF1 higher is better',
            'scopeSource': 'derived/applied_status.json isPassthrough (pixel-equal-v1)',
            'sourceResultsSha256': hashlib.sha256((source / batch / 'results.json').read_bytes()).hexdigest(),
            'appliedStatusSha256': hashlib.sha256((derived_dir / 'applied_status.json').read_bytes()).hexdigest(),
            'rowN': len(joined), 'artifactN': len({r['sampleId'] for r in joined}),
            'comparisonWithGroupedSummary': comparison,
            'groups': results,
        }
        (derived_dir / 'ci_by_artifact.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        with (derived_dir / 'ci_by_artifact.csv').open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(results[0]))
            writer.writeheader()
            writer.writerows(results)
        printed.append({'batch': batch, 'groups': len(results),
                        'meanMaxAbsDiff': max(c['meanAbsDiff'] for c in comparison),
                        'replayReproducesStoredAll': all(c['replayReproducesStored'] for c in comparison),
                        'ciEndpointMaxAbsDiff': max(c['ciEndpointMaxAbsDiff'] for c in comparison)})
    print(json.dumps(printed, ensure_ascii=False, indent=2))
    return printed


if __name__ == '__main__':
    main()
