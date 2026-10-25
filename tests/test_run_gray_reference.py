"""Green 2026-10-19 (a): gray reference fields next to pixel-equal-v1 (never decide isPassthrough)."""
import hashlib
import json

import cv2
import numpy as np

import museum_processing

STELE = 'qing_02_wushi_reerection'


def _enc(image):
    return cv2.imencode('.png', image)[1].tobytes()


def test_color_input_gray_output_full_channel_changed_gray_unchanged():
    color = np.zeros((6, 10, 3), np.uint8)
    color[:, :, 0], color[:, :, 1], color[:, :, 2] = 40, 120, 200  # a real colour source
    gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
    restored = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)  # pipeline output: gray replicated to 3 channels
    status = museum_processing.run_change_status(_enc(color), _enc(restored))
    assert status['isPassthrough'] is False and status['changedPixelCount'] == 60 and status['changedPixelRatio'] == 1.0
    assert status['passthroughCriterion'] == 'pixel-equal-v1'
    assert status['grayChangedPixelCount'] == 0 and status['grayChangedPixelRatio'] == 0
    assert status['grayCriterion'] == 'working-gray-pixel-equal-v1' and 'BGR→GRAY' in status['grayCriterionRule']
    assert status['graySource'] == 'recorded'
    assert museum_processing.output_mode(status) == 'processed'  # gray never decides the mode


def test_gray_fields_null_when_undeterminable():
    for status in (museum_processing.run_change_status(None, b'x'), museum_processing.run_change_status(b'bad', b'bad')):
        assert all(status[key] is None for key in museum_processing.GRAY_FIELDS)
    small = _enc(np.zeros((3, 3), np.uint8))
    status = museum_processing.run_change_status(_enc(np.zeros((4, 4), np.uint8)), small)
    assert status['isPassthrough'] is None and status['grayChangedPixelCount'] is None and status['grayCriterion'] is None


def test_gray_computed_on_read_for_recorded_runs_without_gray(tmp_path, monkeypatch):
    monkeypatch.setattr(museum_processing, 'BASE', tmp_path)
    monkeypatch.setattr(museum_processing, 'RESULTS_DIR', None)
    museum_processing._READ_CACHE.clear()
    run_id = '20261018T000009_0000000c'
    folder = tmp_path / 'static/results' / STELE / run_id
    folder.mkdir(parents=True)
    gray = np.full((5, 5), 70, np.uint8); out = gray.copy(); out[0, 0] = 90
    raw = {'original': _enc(gray), 'restored': _enc(out)}
    for role, data in raw.items():
        (folder / f'{role}.png').write_bytes(data)
    record = {'runId': run_id, 'steleId': STELE, 'algorithmVersion': 'adaptive-rubbing-v2.1', 'isPassthrough': False,
              'changedPixelCount': 1, 'passthroughCriterion': 'pixel-equal-v1', 'passthroughSource': 'recorded',
              'outputImages': {r: f'/static/results/{STELE}/{run_id}/{r}.png' for r in raw},
              'outputSha256': {r: hashlib.sha256(d).hexdigest() for r, d in raw.items()}}
    (folder / 'processing.json').write_text(json.dumps(record), 'utf-8')
    before = (folder / 'processing.json').read_bytes()
    run = museum_processing.read_run(STELE, run_id)
    assert run['passthroughSource'] == 'recorded' and run['changedPixelCount'] == 1
    assert run['grayChangedPixelCount'] == 1 and run['graySource'] == 'computed-on-read'
    assert (folder / 'processing.json').read_bytes() == before
