"""RV-AI05: computed-on-read refuses oversized images; returns undetermined with an explicit reason."""
import hashlib
import json

import cv2
import numpy as np

import museum_processing

STELE = 'qing_02_wushi_reerection'


def _setup(tmp_path, monkeypatch, max_pixels=None, max_bytes=None):
    monkeypatch.setattr(museum_processing, 'BASE', tmp_path)
    monkeypatch.setattr(museum_processing, 'RESULTS_DIR', None)
    museum_processing._READ_CACHE.clear()
    if max_pixels is not None:
        monkeypatch.setattr(museum_processing, 'COMPUTED_ON_READ_MAX_PIXELS', max_pixels)
    if max_bytes is not None:
        monkeypatch.setattr(museum_processing, 'COMPUTED_ON_READ_MAX_BYTES', max_bytes)


def _old_run(tmp_path, run_id, image):
    folder = tmp_path / 'static/results' / STELE / run_id
    folder.mkdir(parents=True)
    raw = cv2.imencode('.png', image)[1].tobytes()
    for role in ('original', 'restored'):
        (folder / f'{role}.png').write_bytes(raw)
    record = {'runId': run_id, 'steleId': STELE, 'algorithmVersion': 'adaptive-rubbing-v2.1',
              'outputImages': {r: f'/static/results/{STELE}/{run_id}/{r}.png' for r in ('original', 'restored')},
              'outputSha256': {r: hashlib.sha256(raw).hexdigest() for r in ('original', 'restored')}}
    (folder / 'processing.json').write_text(json.dumps(record), 'utf-8')
    return folder


def test_pixel_limit_returns_undetermined(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, max_pixels=100)  # 20x20 = 400 > 100
    folder = _old_run(tmp_path, '20261017T000001_0000000a', np.full((20, 20), 40, np.uint8))
    before = (folder / 'processing.json').read_bytes()
    run = museum_processing.read_run(STELE, '20261017T000001_0000000a')
    assert run['isPassthrough'] is None and run['passthroughCriterion'] is None and run['passthroughSource'] is None
    assert '像素超过上限' in run['passthroughUndeterminedReason']
    assert run['grayChangedPixelCount'] is None and run['grayCriterion'] is None
    assert (folder / 'processing.json').read_bytes() == before


def test_byte_limit_returns_undetermined(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, max_bytes=50)  # PNG of 8x8 is > 50 bytes
    _old_run(tmp_path, '20261017T000002_0000000b', np.full((8, 8), 10, np.uint8))
    run = museum_processing.read_run(STELE, '20261017T000002_0000000b')
    assert run['isPassthrough'] is None and '字节超过上限' in run['passthroughUndeterminedReason']


def test_within_limits_still_computes(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, max_pixels=10_000, max_bytes=10_000_000)
    _old_run(tmp_path, '20261017T000003_0000000c', np.full((8, 8), 50, np.uint8))
    run = museum_processing.read_run(STELE, '20261017T000003_0000000c')
    assert run['isPassthrough'] is True and run['passthroughSource'] == 'computed-on-read'
    assert run['grayCriterion'] == 'gray-bt601-pixel-equal-v1'
