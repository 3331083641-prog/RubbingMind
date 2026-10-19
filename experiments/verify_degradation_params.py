"""Check the degradation generator of B15 (2026-10-15) against the v2 series (read-only).

For each batch, every stored degraded input is regenerated from the stored reference
PNG with that batch's own degrade() and compared pixel by pixel:
  2026-10-15         experiments/run_ablation.py at commit 10a63f4 (git show), seed per row
  2026-10-17-v2      experiments/results/2026-10-17-v2/source_snapshot/experiments/run_v2.py
  2026-10-17-v2-text experiments/results/2026-10-17-v2-text/source_snapshot/experiments/run_v2.py
Output: experiments/results/<batch>/derived/degradation_check.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
B15_COMMIT = '10a63f4'


def read_gray(path):
    return cv2.imdecode(np.frombuffer(path.read_bytes(), np.uint8), cv2.IMREAD_GRAYSCALE)


def load_b15():
    source = subprocess.check_output(['git', 'show', f'{B15_COMMIT}:experiments/run_ablation.py'], cwd=ROOT)
    module = types.ModuleType('run_ablation_b15')
    module.__file__ = f'{B15_COMMIT}:experiments/run_ablation.py'
    exec(compile(source, module.__file__, 'exec'), module.__dict__)
    return module, {'source': f'git {B15_COMMIT}:experiments/run_ablation.py', 'sha256': hashlib.sha256(source).hexdigest()}


def load_snapshot(batch_dir):
    path = batch_dir / 'source_snapshot/experiments/run_v2.py'
    spec = importlib.util.spec_from_file_location(f'run_v2_{batch_dir.name.replace("-", "_")}', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, {'source': path.relative_to(batch_dir.parent.parent.parent).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def check(batch_dir: Path):
    data = json.loads((batch_dir / 'results.json').read_text(encoding='utf-8'))
    rows = [r for r in data['rows'] if r['method'] == 'degraded']
    cases = []
    if batch_dir.name == '2026-10-15':
        module, code = load_b15()
        for r in rows:
            reference = read_gray(batch_dir / f"{r['sampleId']}_reference.png")
            regenerated = module.degrade(reference, r['degradation'], r['seed'])
            stored = read_gray(batch_dir / r['output'])
            cases.append({'caseId': f"{r['sampleId']}_{r['degradation']}", 'seed': r['seed'], 'strength': None,
                          'pixelEqual': bool(np.array_equal(regenerated, stored)), 'changedPixels': int(np.count_nonzero(regenerated != stored))})
    else:
        module, code = load_snapshot(batch_dir)
        for r in rows:
            reference = read_gray(batch_dir / r['reference'])
            regenerated, params = module.degrade(reference, r['degradation'], r['seed'], r['strength'])
            stored = read_gray(batch_dir / r['input'])
            cases.append({'caseId': r['caseId'], 'seed': r['seed'], 'strength': r['strength'],
                          'pixelEqual': bool(np.array_equal(regenerated, stored)), 'changedPixels': int(np.count_nonzero(regenerated != stored)),
                          'parametersMatchRecord': params == r['degradationParameters']})
    config = data.get('config') or {}
    return {'batch': batch_dir.name, 'derivedAt': datetime.now(timezone.utc).isoformat(), 'derivedBy': 'experiments/verify_degradation_params.py',
            'generatorCode': code, 'configSeed': config.get('seed'), 'strengths': config.get('strengths'),
            'samples': [{'id': s['id'], 'crop': s.get('crop'), 'sourceSha256': s.get('sourceSha256')} for s in (data.get('sources') or [])],
            'casesN': len(cases), 'pixelEqualN': sum(c['pixelEqual'] for c in cases),
            'parametersMatchRecordN': sum(1 for c in cases if c.get('parametersMatchRecord')), 'cases': cases}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', default=str(ROOT))
    parser.add_argument('--output-root', default=str(ROOT))
    parser.add_argument('--batch', action='append')
    args = parser.parse_args(argv)
    source = Path(args.source_root).resolve() / 'experiments/results'
    target = Path(args.output_root).resolve() / 'experiments/results'
    out = []
    for batch in args.batch or ('2026-10-15', '2026-10-17-v2', '2026-10-17-v2-text'):
        result = check(source / batch)
        folder = target / batch / 'derived'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'degradation_check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        out.append({k: result[k] for k in ('batch', 'casesN', 'pixelEqualN', 'parametersMatchRecordN', 'generatorCode', 'configSeed', 'strengths')})
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
