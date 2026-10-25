"""E-05 evidence: why notch rows recorded as not_applicable still changed pixels.

For every row with method 'notch' and appliedStatus 'processed_not_applicable_label'
(recorded not_applicable, stored output differs from the input), check read-only:

  signedDiffValues        distinct non-zero values of (stored output - input)
  snapshotReproducesStored  the batch's engine (source_snapshot, or GIT_ENGINE), notch d0=48,
                          reproduces the stored output pixel for pixel
  snapshotNotchApplied    the snapshot engine finds a peak pair (should be False)
  headReturnsInput        this tree's algorithm_engine (E-05 fix) returns the input
  floatRoundTripMaxError  max |real(ifft2(fft2(x))) - x| with an all-ones mask
  changedEqualsTruncation the changed pixels are exactly those where
                          astype(uint8) of the round trip falls below the input

Label not-applicable-but-modified-rounding when every check holds (only -1
differences, snapshot reproduces the stored file, no peaks, fix returns the input,
changed pixels = truncated pixels); otherwise not-applicable-but-modified-other
with the failed checks listed. Input and output files are only read.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import types
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from algorithm_engine import RubbingAlgorithmEngine  # noqa: E402

ROUNDING = 'not-applicable-but-modified-rounding'
OTHER = 'not-applicable-but-modified-other'
TARGET_STATUS = 'processed_not_applicable_label'
# Batches without source_snapshot: engine taken from the commit that produced them
# (2026-10-15 was run by git 10a63f4:experiments/run_ablation.py).
GIT_ENGINE = {'2026-10-15': '10a63f4'}


def _read(path: Path):
    image = cv2.imdecode(np.frombuffer(path.read_bytes(), np.uint8), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f'无法解码 {path}')
    return image


def load_engines(batch_dir: Path):
    snapshot = batch_dir / 'source_snapshot/algorithm_engine.py'
    name = 'ae_snapshot_' + hashlib.sha256(str(batch_dir).encode()).hexdigest()[:8]
    if snapshot.is_file():
        source, origin = snapshot.read_bytes(), f'experiments/results/{batch_dir.name}/source_snapshot/algorithm_engine.py'
    elif batch_dir.name in GIT_ENGINE:
        commit = GIT_ENGINE[batch_dir.name]
        source = subprocess.check_output(['git', 'show', f'{commit}:algorithm_engine.py'], cwd=ROOT)
        origin = f'git {commit}:algorithm_engine.py'
    else:
        return None
    module = types.ModuleType(name)
    module.__file__ = origin
    exec(compile(source, origin, 'exec'), module.__dict__)
    return {'snapshot': module.RubbingAlgorithmEngine(), 'head': RubbingAlgorithmEngine(),
            'snapshotSource': origin, 'snapshotSha256': hashlib.sha256(source).hexdigest()}


def classify(batch_dir: Path, item: dict, engines: dict):
    source = _read(batch_dir / item['inputFile'])
    stored = _read(batch_dir / item['outputFile'])
    gray = cv2.cvtColor(source[:, :, :3], cv2.COLOR_BGR2GRAY) if source.ndim == 3 else source
    stored_gray = cv2.cvtColor(stored[:, :, :3], cv2.COLOR_BGR2GRAY) if stored.ndim == 3 else stored
    signed = stored_gray.astype(np.int16) - gray.astype(np.int16)
    values = sorted(int(v) for v in np.unique(signed) if v != 0)
    snap_out, _, snap_details = engines['snapshot'].apply_frequency_domain_filter(gray, d0=48, filter_type='notch', return_details=True)
    head_out, _, head_details = engines['head'].apply_frequency_domain_filter(gray, d0=48, filter_type='notch', return_details=True)
    round_trip = np.real(np.fft.ifft2(np.fft.ifftshift(np.fft.fftshift(np.fft.fft2(gray.astype(np.float32))))))
    truncated = np.clip(round_trip, 0, 255).astype(np.uint8) != gray
    evidence = {
        'inputChannels': 1 if source.ndim == 2 else int(source.shape[2]),
        'outputChannels': 1 if stored.ndim == 2 else int(stored.shape[2]),
        'changedPixelCount': int(np.count_nonzero(signed)),
        'signedDiffValues': values,
        'maxAbsDiff': int(np.abs(signed).max()),
        'snapshotReproducesStored': bool(np.array_equal(snap_out, stored_gray)),
        'snapshotNotchApplied': bool(snap_details.get('notchApplied')),
        'headReturnsInput': bool(np.array_equal(head_out, gray)),
        'headNotchApplied': bool(head_details.get('notchApplied')),
        'floatRoundTripMaxError': float(np.abs(round_trip - gray).max()),
        'changedEqualsTruncation': bool(np.array_equal(truncated, signed != 0)),
    }
    failed = []
    if not values or set(values) - {-1}:
        failed.append('差值不全为 -1')
    if not evidence['snapshotReproducesStored']:
        failed.append('快照引擎未复现存档输出')
    if evidence['snapshotNotchApplied']:
        failed.append('快照引擎检出了峰对')
    if not evidence['headReturnsInput']:
        failed.append('修复后引擎未原样返回输入')
    if not evidence['changedEqualsTruncation']:
        failed.append('改动像素与截断像素不一致')
    evidence['failedChecks'] = failed
    return (ROUNDING if not failed else OTHER), evidence


def annotate(batch_dir: Path, items: list):
    """Add appliedStatusDetail / naChangeEvidence to matching rows in place."""
    targets = [i for i in items if i['method'] == 'notch' and i['appliedStatus'] == TARGET_STATUS]
    if not targets:
        return None
    engines = load_engines(batch_dir)
    if engines is None:
        for item in targets:
            item['appliedStatusDetail'] = OTHER
            item['naChangeEvidence'] = {'failedChecks': ['找不到生成该批次的 algorithm_engine.py，无法复现']}
        return None
    for item in targets:
        item['appliedStatusDetail'], item['naChangeEvidence'] = classify(batch_dir, item, engines)
        item['naChangeEvidence'].update(snapshotSource=engines['snapshotSource'], snapshotSha256=engines['snapshotSha256'])
    return engines['snapshotSha256']
