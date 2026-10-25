"""Representative mechanism cases (E-18): reproducible selection + read-only replay.

Selection (per batch x split, method adaptive_joint, stored v2.0 outputs):
  improvement   processed rows with PSNR gain > 0, sorted by (gain, caseId); median index
  negative      processed rows with PSNR gain < 0, same sort; median index
  passthrough   unchanged output, gate accepted (no fallback_identity); sorted by caseId; median index
  gate_reject   stored decisions contain fallback_identity; sorted by caseId; median index
  notch         stored decisions contain notch and the gate accepted; sorted by (gain, caseId); median index
Median index = (n - 1) // 2. If that case was already chosen for an earlier category,
the nearest unchosen index is used (above first, then below). Nothing is chosen by look.

Replay (stored input PNG only, nothing historical is rewritten):
  historical  experiments/results/<batch>/source_snapshot/degradation_analysis.py
              (the file that generated the stored outputs)
  base        degradation_analysis.py at --base-commit (default f0c5886, v2.1)
  head        degradation_analysis.py in this working tree
Each replay output is compared pixel by pixel with the stored adaptive_joint PNG.
The fixed 'notch' baseline is also replayed with the batch's snapshot algorithm_engine
and with this tree's algorithm_engine (E-05 fix) against the stored notch PNG.
Mechanism images are drawn with the head code.

Binding: each batch writes headCommit into derived/mechanism/index.json.
If that headCommit lags the branch tip, reports must NOT claim mechanism PNGs
are byte-identical to the current tip; see docs/product-upgrade/MECHANISM_HEAD_NOTE.md.
Do not delete experiment raw data; re-run only when intentionally refreshing mechanism.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import scipy
import skimage
from scipy import fft

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import degradation_analysis as head_da  # noqa: E402
from algorithm_engine import RubbingAlgorithmEngine as AlgorithmEngine  # noqa: E402
from experiments.run_ablation import apply_method  # noqa: E402
from restoration_measures import edges, foreground, measure_case  # noqa: E402

BATCHES = ('2026-10-17-v2', '2026-10-17-v2-text')
SPLITS = ('development', 'test')
CATEGORIES = ('improvement', 'negative', 'passthrough', 'gate_reject', 'notch')
PARAMETERS = {'strength': 1.0, 'notch_width': 0.8, 'canny': [80, 160],
              'spectrum': 'log1p(|fftshift(fft2(x - mean(x)))|), min-max to 0..255, VIRIDIS',
              'foreground': 'Otsu, minority class (degradation_analysis.analyze_degradation)',
              'skeleton': 'AlgorithmEngine.extract_stroke_skeleton (Otsu + skimage skeletonize)',
              'diff': '|out - in|, scaled by max(1, P99) to 0..255, INFERNO'}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def module_from_source(name, source: bytes, filename):
    module = types.ModuleType(name)
    module.__file__ = filename
    exec(compile(source, filename, 'exec'), module.__dict__)
    return module


def module_from_file(name, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_gray(path: Path):
    image = cv2.imdecode(np.frombuffer(path.read_bytes(), np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f'无法解码 {path}')
    return image


def compare(a, b):
    stats = head_da.change_stats(a, b)
    return {'pixelEqual': stats['isPassthrough'], 'changedPixelCount': stats['changedPixelCount'],
            'maxAbsDiff': stats['maxAbsDiff'], 'meanAbsDiff': stats['meanAbsDiff']}


def _pick(candidates, chosen):
    if not candidates:
        return None, None
    order = [(len(candidates) - 1) // 2]
    for step in range(1, len(candidates)):
        order += [order[0] + step, order[0] - step]
    for index in order:
        if 0 <= index < len(candidates) and candidates[index]['caseId'] not in chosen:
            return index, candidates[index]
    return None, None


def select(rows, status, split):
    base = {r['caseId']: r for r in rows if r['method'] == 'degraded'}
    pool = []
    for index, row in enumerate(rows):
        if row['method'] != 'adaptive_joint' or row['split'] != split or row.get('error'):
            continue
        ops = [d['operator'] for d in row['diagnostics']['decisions']]
        pool.append({'rowIndex': index, 'caseId': row['caseId'], 'ops': ops, 'gain': row['psnr'] - base[row['caseId']]['psnr'],
                     'passthrough': status[index]['isPassthrough']})
    rules = {
        'improvement': (lambda p: p['passthrough'] is False and p['gain'] > 0, 'gain'),
        'negative': (lambda p: p['passthrough'] is False and p['gain'] < 0, 'gain'),
        'passthrough': (lambda p: p['passthrough'] is True and 'fallback_identity' not in p['ops'], 'caseId'),
        'gate_reject': (lambda p: 'fallback_identity' in p['ops'], 'caseId'),
        'notch': (lambda p: 'notch' in p['ops'] and 'fallback_identity' not in p['ops'], 'gain'),
    }
    chosen, picks = set(), []
    for category in CATEGORIES:
        keep, key = rules[category]
        candidates = sorted((p for p in pool if keep(p)), key=lambda p: (p['gain'], p['caseId']) if key == 'gain' else p['caseId'])
        index, pick = _pick(candidates, chosen)
        if pick is None:
            picks.append({'category': category, 'missing': True, 'candidateN': len(candidates)})
            continue
        chosen.add(pick['caseId'])
        picks.append({'category': category, 'rowIndex': pick['rowIndex'], 'caseId': pick['caseId'], 'rank': index,
                      'candidateN': len(candidates), 'sortKey': key})
    return picks


def spectrum_image(image, peaks):
    values = image.astype(np.float32)
    log = np.log1p(np.abs(fft.fftshift(fft.fft2(values - values.mean(), workers=1))))
    norm = cv2.normalize(log, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    color = cv2.applyColorMap(norm, cv2.COLORMAP_VIRIDIS)
    for pair in peaks:
        for y, x in pair['positions']:
            cv2.circle(color, (int(x), int(y)), 5, (0, 0, 255), 1)
    return color


def notch_mask(shape, peaks, width):
    h, w = shape
    yy, xx = np.ogrid[:h, :w]
    mask = np.ones(shape, np.float32)
    for pair in peaks:
        for y, x in pair['positions']:
            mask *= 1 - np.exp(-((yy - y) ** 2 + (xx - x) ** 2) / (2 * width ** 2))
    return mask


def heat(diff):
    scale = max(1.0, float(np.percentile(diff, 99)))
    return cv2.applyColorMap(np.clip(diff / scale * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO), scale


def write_png(folder: Path, name, image, description, manifest):
    ok, data = cv2.imencode('.png', image)
    if not ok:
        raise ValueError(name)
    (folder / name).write_bytes(data.tobytes())
    manifest.append({'file': name, 'description': description, 'shape': list(image.shape), 'bytes': len(data), 'sha256': sha(data.tobytes())})


def run_case(batch_dir: Path, out_root: Path, row, base_row, notch_row, pick, versions, engines, head_commit):
    folder = out_root / row['caseId']
    folder.mkdir(parents=True, exist_ok=True)
    raw_input = (batch_dir / row['input']).read_bytes()
    damaged = read_gray(batch_dir / row['input'])
    reference = read_gray(batch_dir / row['reference'])
    stored = read_gray(batch_dir / row['output'])
    replays, outputs = {}, {}
    for label, module in versions.items():
        output, meta = module['module'].AdaptiveRubbingRestorer().restore(damaged, strength=PARAMETERS['strength'], notch_width=PARAMETERS['notch_width'])
        outputs[label] = (output, meta)
        replays[label] = {'code': module['info'], 'operators': [d['operator'] for d in meta['decisions']],
                          'gateAccepted': meta['fidelityGate']['accepted'], 'versionString': meta.get('version'),
                          'vsStoredOutput': compare(stored, output), 'vsInput': compare(damaged, output)}
    replays['head']['vsBase'] = compare(outputs['base'][0], outputs['head'][0])
    stored_ops = [d['operator'] for d in row['diagnostics']['decisions']]
    replays['historical']['operatorsMatchStored'] = replays['historical']['operators'] == stored_ops

    notch_stored = read_gray(batch_dir / notch_row['output'])
    notch_replay = {'storedApplicability': notch_row['applicability']}
    for label, engine in engines.items():
        output, applicability = engine['apply'](damaged)
        notch_replay[label] = {'code': engine['info'], 'applicability': applicability,
                               'vsStoredNotch': compare(notch_stored, output), 'vsInput': compare(damaged, output)}

    head_out, head_meta = outputs['head']
    manifest = []
    peaks_in = head_meta['features']['periodicPeaks']
    peaks_out = head_da.periodic_peaks(head_out)
    write_png(folder, 'spectrum_input.png', spectrum_image(damaged, peaks_in), '输入 log 幅度谱；红圈为检出的共轭周期峰', manifest)
    write_png(folder, 'spectrum_output.png', spectrum_image(head_out, peaks_out), 'head 重算输出的 log 幅度谱；红圈为残留峰', manifest)
    notch_applied = any(d['operator'] == 'notch' for d in head_meta['decisions'])
    if notch_applied:
        write_png(folder, 'notch_mask.png', (notch_mask(damaged.shape, peaks_in, PARAMETERS['notch_width']) * 255).astype(np.uint8),
                  '陷波掩膜（fftshift 坐标，白=保留，黑=抑制）', manifest)
    for label, image in (('reference', reference), ('input', damaged), ('output', head_out)):
        write_png(folder, f'foreground_{label}.png', foreground(image) * 255, f'{label} 二值前景（Otsu 少数类）', manifest)
        write_png(folder, f'skeleton_{label}.png', AlgorithmEngine().extract_stroke_skeleton(image), f'{label} 骨架', manifest)
        write_png(folder, f'edges_{label}.png', edges(image).astype(np.uint8) * 255, f'{label} Canny(80,160) 边缘', manifest)
    diff = np.abs(head_out.astype(np.float32) - damaged.astype(np.float32))
    diff_scale = None
    if diff.max() > 0:
        image, diff_scale = heat(diff)
        write_png(folder, 'diff_output_input.png', image, '|head 输出 − 输入|，按 P99 归一', manifest)
    mismatch = np.abs(head_out.astype(np.float32) - stored.astype(np.float32))
    mismatch_scale = None
    if mismatch.max() > 0:
        image, mismatch_scale = heat(mismatch)
        write_png(folder, 'diff_head_vs_stored.png', image, '|head 重算输出 − 已存输出|，按 P99 归一', manifest)

    record = {
        'batch': batch_dir.name, 'split': row['split'], 'sampleId': row['sampleId'], 'caseId': row['caseId'],
        'degradation': row['degradation'], 'strength': row['strength'], 'category': pick['category'],
        'selection': {k: pick[k] for k in ('rank', 'candidateN', 'sortKey')},
        'storedFiles': {'reference': row['reference'], 'input': row['input'], 'output': row['output'], 'notchOutput': notch_row['output']},
        'inputSha256': sha(raw_input), 'inputSha256Recorded': row['inputSha256'], 'inputShaMatches': sha(raw_input) == row['inputSha256'],
        'storedOutputSha256': sha((batch_dir / row['output']).read_bytes()), 'storedOutputShaMatches': sha((batch_dir / row['output']).read_bytes()) == row['outputSha256'],
        'storedMetrics': {'psnrInput': base_row['psnr'], 'psnrOutput': row['psnr'], 'psnrGain': row['psnr'] - base_row['psnr'],
                          'ssimGain': row['ssim'] - base_row['ssim'], 'edgeF1Gain': row['edgeF1'] - base_row['edgeF1']},
        'storedDiagnostics': {'algorithmVersion': row.get('algorithmVersion'), 'operators': stored_ops,
                              'decisions': row['diagnostics']['decisions'], 'fidelityGate': row['diagnostics']['fidelityGate'],
                              'selectedOutput': row['diagnostics'].get('selectedOutput')},
        'headCommit': head_commit, 'parameters': PARAMETERS,
        'replays': replays, 'notchBaselineReplay': notch_replay,
        'mechanism': {
            'code': 'head', 'features': {k: head_meta['features'][k] for k in ('noiseSigmaMAD', 'impulseFraction', 'periodicPeaks', 'thinStrokeRisk', 'highFrequencyEnergyFraction')},
            'decisions': head_meta['decisions'], 'fidelityGate': head_meta['fidelityGate'], 'algorithmOutputMode': head_meta.get('algorithmOutputMode', head_meta.get('outputMode')),
            'changeStats': head_meta.get('changeStats'), 'notchApplied': notch_applied, 'peaksOutput': peaks_out,
            'diffScaleP99': diff_scale, 'headVsStoredScaleP99': mismatch_scale,
            'measures': measure_case(reference, damaged, head_out),
            'measuresStoredOutput': measure_case(reference, damaged, stored),
        },
        'images': manifest,
    }
    (folder / 'mechanism.json').write_text(json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    return record


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', default=str(ROOT))
    parser.add_argument('--output-root', default=str(ROOT))
    parser.add_argument('--base-commit', default='f0c5886')
    args = parser.parse_args(argv)
    source = Path(args.source_root).resolve() / 'experiments/results'
    target = Path(args.output_root).resolve() / 'experiments/results'
    head_commit = git('rev-parse', 'HEAD').decode().strip()
    dirty = bool(git('status', '--porcelain', '--', 'degradation_analysis.py', 'algorithm_engine.py', 'restoration_measures.py').strip())
    base_source = git('show', f'{args.base_commit}:degradation_analysis.py')
    base_commit = git('rev-parse', args.base_commit).decode().strip()
    environment = {'python': platform.python_version(), 'numpy': np.__version__, 'opencv': cv2.__version__,
                   'scipy': scipy.__version__, 'scikitImage': skimage.__version__}
    summary = []
    for batch in BATCHES:
        batch_dir = source / batch
        data = json.loads((batch_dir / 'results.json').read_text(encoding='utf-8'))
        status = json.loads((target / batch / 'derived/applied_status.json').read_text(encoding='utf-8'))['rows']
        rows = data['rows']
        snapshot = batch_dir / 'source_snapshot'
        versions = {
            'historical': {'module': module_from_file(f'da_hist_{batch.replace("-", "_")}', snapshot / 'degradation_analysis.py'),
                           'info': {'source': f'experiments/results/{batch}/source_snapshot/degradation_analysis.py',
                                    'sha256': sha((snapshot / 'degradation_analysis.py').read_bytes()),
                                    'recordedCodeSha256': data['environment']['codeSha256']['degradation_analysis.py']}},
            'base': {'module': module_from_source('da_base', base_source, f'{base_commit}:degradation_analysis.py'),
                     'info': {'source': f'git {base_commit}:degradation_analysis.py', 'sha256': sha(base_source)}},
            'head': {'module': head_da, 'info': {'source': 'working tree degradation_analysis.py', 'commit': head_commit,
                                                 'uncommittedChanges': dirty, 'sha256': sha((ROOT / 'degradation_analysis.py').read_bytes())}},
        }
        snapshot_engine = module_from_file(f'ae_hist_{batch.replace("-", "_")}', snapshot / 'algorithm_engine.py').RubbingAlgorithmEngine()
        head_engine = AlgorithmEngine()

        def snapshot_notch(image, engine=snapshot_engine):
            result, _, details = engine.apply_frequency_domain_filter(image, d0=48, filter_type='notch', return_details=True)
            return result, 'applied' if details['notchApplied'] else 'not_applicable'

        engines = {
            'historicalEngine': {'apply': snapshot_notch, 'info': {'source': f'experiments/results/{batch}/source_snapshot/algorithm_engine.py',
                                                                   'sha256': sha((snapshot / 'algorithm_engine.py').read_bytes())}},
            'headEngine': {'apply': lambda image: apply_method(image, 'notch'),
                           'info': {'source': 'working tree algorithm_engine.py (E-05 fix)', 'commit': head_commit, 'uncommittedChanges': dirty,
                                    'sha256': sha((ROOT / 'algorithm_engine.py').read_bytes())}},
        }
        by_case = {}
        for r in rows:
            by_case.setdefault(r['caseId'], {})[r['method']] = r
        out_root = target / batch / 'derived/mechanism'
        cases = []
        for split in SPLITS:
            for pick in select(rows, status, split):
                if pick.get('missing'):
                    cases.append({'split': split, **pick})
                    continue
                row = rows[pick['rowIndex']]
                record = run_case(batch_dir, out_root, row, by_case[row['caseId']]['degraded'], by_case[row['caseId']]['notch'],
                                  pick, versions, engines, head_commit)
                cases.append({'split': split, 'category': pick['category'], 'caseId': row['caseId'], 'sampleId': row['sampleId'],
                              'degradation': row['degradation'], 'strength': row['strength'], 'psnrGain': record['storedMetrics']['psnrGain'],
                              'historicalEqualsStored': record['replays']['historical']['vsStoredOutput']['pixelEqual'],
                              'baseEqualsStored': record['replays']['base']['vsStoredOutput']['pixelEqual'],
                              'headEqualsBase': record['replays']['head']['vsBase']['pixelEqual'],
                              'headChangedVsStored': record['replays']['head']['vsStoredOutput']['changedPixelCount'],
                              'notchHistoricalEqualsStored': record['notchBaselineReplay']['historicalEngine']['vsStoredNotch']['pixelEqual'],
                              'notchHeadEqualsStored': record['notchBaselineReplay']['headEngine']['vsStoredNotch']['pixelEqual'],
                              'imageBytes': sum(i['bytes'] for i in record['images']), 'directory': f'derived/mechanism/{row["caseId"]}'})
        index = {'batch': batch, 'derivedAt': datetime.now(timezone.utc).isoformat(), 'derivedBy': 'experiments/mechanism_cases.py',
                 'selectionRule': __doc__.split('Replay')[0].strip(), 'headCommit': head_commit, 'baseCommit': base_commit,
                 'environment': environment, 'recordedEnvironment': {k: data['environment'].get(k) for k in ('python', 'numpy', 'opencv', 'scikitImage')},
                 'cases': cases}
        out_root.mkdir(parents=True, exist_ok=True)
        (out_root / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        summary.append(index)
    print(json.dumps([{'batch': s['batch'], 'cases': s['cases']} for s in summary], ensure_ascii=False, indent=1))
    return summary


if __name__ == '__main__':
    main()
