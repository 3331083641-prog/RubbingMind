"""Measured negative-lift causes for historical image batches (E-04, derived, read-only).

For every non-baseline row whose PSNR is below its input (degraded) row, the
reference, input and output PNGs are read, measured with
restoration_measures.measure_case and classified with
restoration_diagnosis.measured_causes. The rule-inferred cause (by degradation
type, restoration_diagnosis._cause) is kept next to it and labelled as such.
Output: experiments/results/<batch>/derived/negative_lift_causes.{csv,json}.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from restoration_diagnosis import CRITERIA, MEASURED_CRITERIA_VERSION, RULE_BASIS, _cause, measured_causes  # noqa: E402
from restoration_measures import measure_case  # noqa: E402

BATCHES = ('2026-10-15', '2026-10-17-v2', '2026-10-17-v2-text')
CSV_FIELDS = ['batch', 'rowIndex', 'sampleId', 'split', 'caseId', 'degradation', 'strength', 'method', 'psnrDelta',
              'ruleInferredCause', 'ruleInferredBasis', 'measuredCauses'] + [c[1] for c in CRITERIA if c[1] != 'periodicEnergyOutputWithoutInputPeaks'] + ['periodicPeaksInput', 'periodicPeaksOutput', 'changedPixelRatio']


def read(path: Path):
    image = cv2.imdecode(np.frombuffer(path.read_bytes(), np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f'无法解码 {path.name}')
    return image


def batch_rows(batch_dir: Path):
    data = json.loads((batch_dir / 'results.json').read_text(encoding='utf-8'))
    rows = data['rows']
    if batch_dir.name == '2026-10-15':
        reference = {s['id']: f"{s['id']}_reference.png" for s in data['sources']}
        key = lambda r: (r['sampleId'], r['degradation'])
        inputs = {key(r): r for r in rows if r['method'] == 'degraded'}
        return data, [(i, dict(r, caseId=f"{r['sampleId']}_{r['degradation']}", reference=reference[r['sampleId']],
                               input=inputs[key(r)]['output']), inputs[key(r)]) for i, r in enumerate(rows)]
    inputs = {r['caseId']: r for r in rows if r['method'] == 'degraded'}
    return data, [(i, r, inputs[r['caseId']]) for i, r in enumerate(rows)]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', default=str(ROOT))
    parser.add_argument('--output-root', default=str(ROOT))
    parser.add_argument('--batch', action='append', help='只处理指定批次；可重复')
    args = parser.parse_args(argv)
    source = Path(args.source_root).resolve() / 'experiments/results'
    target = Path(args.output_root).resolve() / 'experiments/results'
    report = []
    for batch in (args.batch or BATCHES):
        batch_dir = source / batch
        data, rows = batch_rows(batch_dir)
        cases = []
        cache = {}

        def image(name):
            if name not in cache:
                cache[name] = read(batch_dir / name)
            return cache[name]

        for index, row, base in rows:
            if row['method'] == 'degraded' or row.get('error') or row.get('psnr') is None or base.get('psnr') is None:
                continue
            psnr_delta = row['psnr'] - base['psnr']
            if not psnr_delta < 0:
                continue
            measures = measure_case(image(row['reference']), image(row['input']), image(row['output']))
            measures['ssimDelta'] = row['ssim'] - base['ssim']
            entries, triggered = measured_causes(measures)
            cases.append({'batch': batch, 'rowIndex': index, 'sampleId': row['sampleId'], 'split': row.get('split'),
                          'caseId': row['caseId'], 'degradation': row['degradation'], 'strength': row.get('strength'),
                          'method': row['method'], 'psnrDelta': psnr_delta,
                          'ruleInferredCause': _cause({'degradation': row['degradation'], 'fidelityAccepted': (row.get('diagnostics') or {}).get('fidelityGate', {}).get('accepted')}),
                          'ruleInferredBasis': RULE_BASIS,
                          'measuredCauses': triggered, 'measuredEvidence': entries, 'measures': measures})
        counts = {}
        for case in cases:
            for cause in case['measuredCauses']:
                key = (case['method'], cause)
                counts[key] = counts.get(key, 0) + 1
        payload = {'batch': batch, 'derivedAt': datetime.now(timezone.utc).isoformat(),
                   'derivedBy': 'experiments/derive_negative_lift_causes.py',
                   'sourceResultsSha256': hashlib.sha256((batch_dir / 'results.json').read_bytes()).hexdigest(),
                   'measuredCriteriaVersion': MEASURED_CRITERIA_VERSION,
                   'criteria': [dict(zip(('cause', 'measure', 'comparator', 'threshold'), c)) for c in CRITERIA],
                   'note': '负提升 = PSNR 低于同 case 的 degraded 行。ruleInferredCause 是旧的按退化类型规则推断，仅作对照。一个案例可触发多个测量原因。',
                   'negativeLiftN': len(cases),
                   'measuredCauseCounts': [{'method': m, 'cause': c, 'n': n} for (m, c), n in sorted(counts.items())],
                   'cases': cases}
        out_dir = target / batch / 'derived'
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / 'negative_lift_causes.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        with (out_dir / 'negative_lift_causes.csv').open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction='ignore')
            writer.writeheader()
            for case in cases:
                writer.writerow({**case, **case['measures'], 'measuredCauses': '|'.join(case['measuredCauses'])})
        adaptive = [c for c in cases if c['method'] in ('adaptive_joint',)]
        summary = {}
        for c in adaptive:
            for cause in c['measuredCauses']:
                summary[cause] = summary.get(cause, 0) + 1
        report.append({'batch': batch, 'negativeLiftN': len(cases), 'adaptiveJointNegativeN': len(adaptive), 'adaptiveJointMeasuredCauses': summary})
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    main()
