"""Held-out comparison of adaptive v2.0 and v2.1. The sample list is fixed before scoring.

The 2026-10-17 batch used the first two works of each dynasty. This batch uses the
last two. It is not retuned after the scores are known, and center crops can still
contain margins. Synthetic damage has a paired crop reference; that PSNR is not a
historical restoration accuracy.
"""
from __future__ import annotations

import importlib.util
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import skimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from algorithm_engine import compute_metrics
from degradation_analysis import AdaptiveRubbingRestorer, VERSION
from experiments.run_ablation import apply_method
from experiments.run_v2 import degrade, sha

OUT = ROOT / 'experiments/results/2026-10-18-v21-heldout'
BASELINE = 'f97ffab'
METHODS = ['degraded', 'gaussian_lowpass', 'butterworth_lowpass', 'notch', 'fast_nlm', 'adaptive_v20', 'adaptive_v21']
DEGRADATIONS = ['gaussian', 'salt_pepper', 'periodic', 'blur', 'occlusion']


def load_v20():
    source = subprocess.check_output(['git', 'show', f'{BASELINE}:degradation_analysis.py'], cwd=ROOT)
    path = ROOT / 'data/runtime/degradation_analysis_f97ffab.py'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(source)
    spec = importlib.util.spec_from_file_location('degradation_v20', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.AdaptiveRubbingRestorer()


def samples():
    catalogue = json.loads((ROOT / 'data/catalog/steles28.json').read_text(encoding='utf-8'))
    selected = []
    previous = {'han_01_caoquan', 'han_02_yiying', 'wei_01_zhangmenglong', 'wei_02_wugaoli', 'tang_01_duobao', 'tang_02_jiucheng',
                'song_01_yuanyou', 'song_02_wenxuan', 'yuan_01_yufu', 'yuan_02_sundeyu', 'ming_01_xianfu', 'ming_02_luxianzhi',
                'qing_01_qianlong_heart_sutra', 'qing_02_wushi_reerection'}
    for dynasty in dict.fromkeys(row['dynasty'] for row in catalogue):
        group = [row for row in catalogue if row['dynasty'] == dynasty]
        for row in group[-2:]:
            path = ROOT / 'apps/web/public' / row['imageAssets']['readable'].split('?')[0].lstrip('/')
            image = cv2.imdecode(np.frombuffer(path.read_bytes(), np.uint8), cv2.IMREAD_GRAYSCALE)
            height, width = image.shape
            x, y = max(0, width // 2 - 128), max(0, height // 2 - 128)
            selected.append({'id': row['id'], 'dynasty': dynasty, 'file': path.relative_to(ROOT).as_posix(),
                             'crop': [x, y, x + 256, y + 256], 'sourceSha256': sha(path),
                             'excludedFromPreviousBatch': row['id'] not in previous})
    if len(selected) != 14 or not all(row['excludedFromPreviousBatch'] for row in selected):
        raise SystemExit('held-out list changed or overlaps the 2026-10-17 batch')
    return selected


def edge_f1(reference, output):
    first = cv2.Canny(reference, 80, 160) > 0
    second = cv2.Canny(output, 80, 160) > 0
    return float(2 * np.count_nonzero(first & second) / max(1, np.count_nonzero(first) + np.count_nonzero(second)))


def thin_mae(reference, output):
    edges = cv2.Canny(reference, 80, 160) > 0
    if not np.any(edges):
        return None
    return float(np.mean(np.abs(reference.astype(np.float32) - output.astype(np.float32))[edges]))


def mean(rows, key):
    values = [row[key] for row in rows if row.get(key) is not None]
    return None if not values else float(np.mean(values))


def main():
    if OUT.exists():
        raise SystemExit(f'{OUT} already exists')
    OUT.mkdir(parents=True)
    old = load_v20()
    new = AdaptiveRubbingRestorer()
    chosen = samples()
    rows = []
    for index, sample in enumerate(chosen):
        source = ROOT / sample['file']
        if sha(source) != sample['sourceSha256']:
            raise SystemExit(f'source changed: {sample["id"]}')
        original = cv2.imdecode(np.frombuffer(source.read_bytes(), np.uint8), cv2.IMREAD_GRAYSCALE)
        x, y, x1, y1 = sample['crop']
        reference = original[y:y1, x:x1]
        if reference.shape != (256, 256):
            raise SystemExit(f'crop is not 256 for {sample["id"]}')
        for mode_index, mode in enumerate(DEGRADATIONS):
            seed = 20261018 + index * 100 + mode_index
            damaged, params = degrade(reference, mode, seed, 1.0)
            input_metrics = compute_metrics(reference, damaged)
            for method in METHODS:
                started = time.perf_counter()
                error = None
                diagnostics = {}
                applicability = 'applied'
                try:
                    if method == 'adaptive_v20':
                        output, diagnostics = old.restore(damaged)
                    elif method == 'adaptive_v21':
                        output, diagnostics = new.restore(damaged)
                    else:
                        output, applicability = apply_method(damaged, method)
                    measured = compute_metrics(reference, output)
                    record = {
                        'psnr': None if not np.isfinite(measured['psnr']) else measured['psnr'],
                        'ssim': measured['ssim'],
                        'edgeF1': edge_f1(reference, output),
                        'thinStrokeMae': thin_mae(reference, output),
                    }
                except Exception as exc:
                    error = f'{type(exc).__name__}: {exc}'
                    applicability = 'failed'
                    output = None
                    record = {'psnr': None, 'ssim': None, 'edgeF1': None, 'thinStrokeMae': None}
                elapsed = (time.perf_counter() - started) * 1000
                gate = diagnostics.get('fidelityGate') if diagnostics else None
                rows.append({
                    'sampleId': sample['id'], 'dynasty': sample['dynasty'], 'degradation': mode, 'strength': 1.0,
                    'seed': seed, 'degradationParameters': params, 'method': method, 'applicability': applicability,
                    'processingMs': elapsed, 'error': error, 'crop': sample['crop'], 'sourceSha256': sample['sourceSha256'],
                    'inputPsnr': None if not np.isfinite(input_metrics['psnr']) else input_metrics['psnr'],
                    'inputSsim': input_metrics['ssim'], 'psnrDeltaFromInput': None if record['psnr'] is None else record['psnr'] - input_metrics['psnr'],
                    'negativeLift': None if record['psnr'] is None else bool(record['psnr'] < input_metrics['psnr']),
                    'fidelityAccepted': None if not gate else bool(gate.get('accepted')),
                    'algorithmVersion': {'adaptive_v20': 'adaptive-rubbing-v2.0', 'adaptive_v21': VERSION}.get(method, 'fixed-baselines-v2'),
                    'diagnosticsOperators': [item.get('operator') for item in diagnostics.get('decisions', [])] if diagnostics else [],
                    **record,
                })
        print(sample['id'], len(rows), flush=True)
    summary = []
    for method in METHODS:
        for mode in DEGRADATIONS + ['all']:
            subset = [row for row in rows if row['method'] == method and (mode == 'all' or row['degradation'] == mode)]
            summary.append({
                'method': method, 'degradation': mode, 'n': len(subset),
                'failed': sum(row['error'] is not None for row in subset),
                'psnrMean': mean(subset, 'psnr'), 'ssimMean': mean(subset, 'ssim'),
                'edgeF1Mean': mean(subset, 'edgeF1'), 'thinStrokeMaeMean': mean(subset, 'thinStrokeMae'),
                'processingMsMean': mean(subset, 'processingMs'),
                'negativeLiftCount': sum(bool(row['negativeLift']) for row in subset),
                'negativeLiftRate': None if not subset else sum(bool(row['negativeLift']) for row in subset) / len(subset),
                'fidelityRejected': sum(row['fidelityAccepted'] is False for row in subset),
            })
    result = {
        'experimentId': 'heldout-v20-v21-2026-10-18',
        'baselineCommit': BASELINE,
        'candidateVersion': VERSION,
        'candidateCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'samplingRule': '每个朝代按馆藏清单取最后两件，中心 256 裁切，强度 1.0。清单在计分前确定，不按分数替换。',
        'notThePreviousBatch': '2026-10-17 v2 使用每朝代前两件。本批使用后两件，但仍是同一批 28 件阅读图，不是新的外部隐藏集。',
        'pairedReference': '配对对象是受控退化前的阅读图局部，不是原石真值。',
        'samples': chosen,
        'rows': rows,
        'summary': summary,
        'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'opencv': cv2.__version__, 'scikitImage': skimage.__version__},
    }
    (OUT / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps([row for row in summary if row['degradation'] in ('all', 'occlusion')], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
