"""Same-batch retest of adaptive v2.0 and v2.1 (not a held-out evaluation).

The 2026-10-18 batch used the last two works of each dynasty. Those 14 works had
already been scored in 2026-10-17-v2-text (same source SHA, two overlapping crops),
and v2.1 was changed after that batch's error analysis. The exclusion list is
therefore derived from every earlier results batch, and a run whose samples were
seen before refuses to start unless it is explicitly declared a retest.
Synthetic damage has a paired crop reference; that PSNR is not a historical
restoration accuracy.
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
from degradation_analysis import AdaptiveRubbingRestorer, VERSION, change_stats
from experiments.applied_status import split_means
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


def previous_sample_ids(results_root=None, exclude=None):
    """Map sample id -> earlier batch directories, read from every results.json.

    Nothing is hard-coded: v2, v2-text and any later batch are all included.
    """
    root = Path(results_root) if results_root else ROOT / 'experiments/results'
    exclude = Path(exclude).resolve() if exclude else OUT.resolve()
    seen = {}
    for path in sorted(root.glob('*/results.json')):
        if path.parent.resolve() == exclude:
            continue
        data = json.loads(path.read_text(encoding='utf-8'))
        config = data.get('config') if isinstance(data.get('config'), dict) else {}
        entries = []
        for key in ('sources', 'samples'):
            if isinstance(data.get(key), list):
                entries.extend(data[key])
        if isinstance(config.get('samples'), list):
            entries.extend(config['samples'])
        for entry in entries:
            if isinstance(entry, dict) and entry.get('id'):
                seen.setdefault(entry['id'], set()).add(path.parent.name)
    return {key: sorted(value) for key, value in seen.items()}


def samples(allow_seen=False, results_root=None):
    catalogue = json.loads((ROOT / 'data/catalog/steles28.json').read_text(encoding='utf-8'))
    previous = previous_sample_ids(results_root)
    selected = []
    for dynasty in dict.fromkeys(row['dynasty'] for row in catalogue):
        group = [row for row in catalogue if row['dynasty'] == dynasty]
        for row in group[-2:]:
            path = ROOT / 'apps/web/public' / row['imageAssets']['readable'].split('?')[0].lstrip('/')
            image = cv2.imdecode(np.frombuffer(path.read_bytes(), np.uint8), cv2.IMREAD_GRAYSCALE)
            height, width = image.shape
            x, y = max(0, width // 2 - 128), max(0, height // 2 - 128)
            selected.append({'id': row['id'], 'dynasty': dynasty, 'file': path.relative_to(ROOT).as_posix(),
                             'crop': [x, y, x + 256, y + 256], 'sourceSha256': sha(path),
                             'excludedFromPreviousBatch': row['id'] not in previous,
                             'seenInBatches': previous.get(row['id'], [])})
    if len(selected) != 14:
        raise SystemExit('sample list changed')
    if not allow_seen and not all(row['excludedFromPreviousBatch'] for row in selected):
        raise SystemExit('samples were already scored in an earlier batch; this would be a same-batch retest, not held-out. '
                         'Pass --allow-seen to run it as a declared retest.')
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


def main(allow_seen=False):
    if OUT.exists():
        raise SystemExit(f'{OUT} already exists')
    OUT.mkdir(parents=True)
    old = load_v20()
    new = AdaptiveRubbingRestorer()
    chosen = samples(allow_seen=allow_seen)
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
                    change = change_stats(damaged, output)
                    if method in ('adaptive_v20', 'adaptive_v21') and change['isPassthrough']:
                        applicability = 'passthrough'
                    record = {
                        'isPassthrough': change['isPassthrough'], 'changedPixelCount': change['changedPixelCount'],
                        'changedPixelRatio': change['changedPixelRatio'], 'maxAbsDiff': change['maxAbsDiff'],
                        'passthroughCriterion': change['passthroughCriterion'],
                        'psnr': None if not np.isfinite(measured['psnr']) else measured['psnr'],
                        'ssim': measured['ssim'],
                        'edgeF1': edge_f1(reference, output),
                        'thinStrokeMae': thin_mae(reference, output),
                    }
                except Exception as exc:
                    error = f'{type(exc).__name__}: {exc}'
                    applicability = 'failed'
                    output = None
                    record = {'psnr': None, 'ssim': None, 'edgeF1': None, 'thinStrokeMae': None, 'isPassthrough': None,
                              'changedPixelCount': None, 'changedPixelRatio': None, 'maxAbsDiff': None, 'passthroughCriterion': None}
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
                **{key: value for key, value in split_means(subset, ('psnr', 'ssim', 'edgeF1')).items()
                   if key in ('processedN', 'passthroughN', 'undeterminedN', 'passthroughCriterion', 'psnrMeanProcessed', 'psnrMeanPassthrough',
                              'ssimMeanProcessed', 'ssimMeanPassthrough', 'edgeF1MeanProcessed', 'edgeF1MeanPassthrough')},
                # Negative lift is also reported on processed rows only; a passthrough cannot lower PSNR.
                'negativeLiftCountProcessed': sum(bool(row['negativeLift']) for row in subset if row.get('isPassthrough') is False),
            })
    result = {
        'experimentId': 'heldout-v20-v21-2026-10-18',
        'baselineCommit': BASELINE,
        'candidateVersion': VERSION,
        'candidateCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'samplingRule': '每个朝代按馆藏清单取最后两件，中心 256 裁切，强度 1.0。清单在计分前确定，不按分数替换。',
        'notThePreviousBatch': '同批复测，不是留出：样本是否在此前批次出现过见 samples[*].seenInBatches。',
        'heldOut': all(row['excludedFromPreviousBatch'] for row in chosen),
        'pairedReference': '配对对象是受控退化前的阅读图局部，不是原石真值。',
        'samples': chosen,
        'rows': rows,
        'summary': summary,
        'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'opencv': cv2.__version__, 'scikitImage': skimage.__version__},
    }
    (OUT / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps([row for row in summary if row['degradation'] in ('all', 'occlusion')], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main(allow_seen='--allow-seen' in sys.argv)
