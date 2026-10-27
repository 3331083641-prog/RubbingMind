"""List the picks of the frontend's temporary representative-sample rule, for reconciliation.

Temporary rule (as given to the frontend): within one batch x split x method x
degradation, take from the actually processed rows (isPassthrough is False,
pixel-equal-v1) the row with the median dPSNR and the row with the minimum
dPSNR, plus one passthrough row (isPassthrough is True).

Tie and parity conventions fixed here (the temporary rule does not state them):
  dPSNR    psnr(method) - psnr(degraded) for the same caseId
  order    rows sorted by (dPSNR, caseId); median = index (n-1)//2 (lower median)
  passthrough  first passthrough row by caseId
  processed    appliedStatus == 'processed' (isPassthrough false); notch rows labelled
               not_applicable whose pixels changed only by E-05 truncation are excluded
Groups without rows of a kind give null. Writes derived/representative_temp_rule.json
for each batch and reports which mechanism cases (derived/mechanism/index.json) are
also picked by the temporary rule. Read-only on results.json.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCHES = ('2026-10-17-v2', '2026-10-17-v2-text')
RULE = 'frontend-temporary-v0: median+min dPSNR of processed rows, plus one passthrough, per batch/split/method/degradation'


def _pick(row, status):
    return None if row is None else {'caseId': row['caseId'], 'sampleId': row['sampleId'], 'gain': row['gain'],
                                     'appliedStatus': status[row['index']]['appliedStatus']}


def picks_for(batch_dir: Path):
    rows = json.loads((batch_dir / 'results.json').read_text(encoding='utf-8'))['rows']
    status = json.loads((batch_dir / 'derived/applied_status.json').read_text(encoding='utf-8'))['rows']
    base = {r['caseId']: r['psnr'] for r in rows if r['method'] == 'degraded'}
    groups = {}
    for index, r in enumerate(rows):
        if r['method'] == 'degraded' or r.get('psnr') is None:
            continue
        item = dict(r, index=index, gain=r['psnr'] - base[r['caseId']])
        groups.setdefault((r['split'], r['method'], r['degradation']), []).append(item)
    out = []
    for (split, method, degradation), members in sorted(groups.items()):
        processed = sorted((m for m in members if status[m['index']]['appliedStatus'] == 'processed'), key=lambda m: (m['gain'], m['caseId']))
        passthrough = sorted((m for m in members if status[m['index']]['isPassthrough'] is True), key=lambda m: m['caseId'])
        out.append({'split': split, 'method': method, 'degradation': degradation, 'n': len(members),
                    'processedN': len(processed), 'passthroughN': len(passthrough),
                    'median': _pick(processed[(len(processed) - 1) // 2] if processed else None, status),
                    'minimum': _pick(processed[0] if processed else None, status),
                    'passthrough': _pick(passthrough[0] if passthrough else None, status)})
    return out


def main(argv=None):
    root = Path(argv[0]).resolve() if argv else ROOT
    report = []
    for batch in BATCHES:
        batch_dir = root / 'experiments/results' / batch
        groups = picks_for(batch_dir)
        picked = {(g['split'], g['method'], p['caseId']): kind for g in groups for kind in ('median', 'minimum', 'passthrough')
                  for p in [g[kind]] if p}
        index_path = batch_dir / 'derived/mechanism/index.json'
        overlap = []
        if index_path.is_file():
            for case in json.loads(index_path.read_text(encoding='utf-8')).get('cases', []):
                if case.get('caseId'):
                    overlap.append({'split': case['split'], 'category': case['category'], 'caseId': case['caseId'],
                                    'alsoPickedAs': picked.get((case['split'], 'adaptive_joint', case['caseId']))})
        payload = {'batch': batch, 'rule': RULE, 'derivedAt': datetime.now(timezone.utc).isoformat(),
                   'derivedBy': 'experiments/representative_temp_rule.py', 'groups': groups,
                   'mechanismCasesOverlap': overlap}
        (batch_dir / 'derived/representative_temp_rule.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        report.append({'batch': batch, 'groups': len(groups), 'overlap': overlap})
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main(sys.argv[1:])
