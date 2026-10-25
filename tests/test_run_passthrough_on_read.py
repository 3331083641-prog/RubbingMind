"""Old museum runs: pixel-equal-v1 is computed on read and never written back."""
import hashlib
import json

import cv2
import numpy as np

RUN_ID = '20261001T010203_abcdef01'


def _png(image):
    return cv2.imencode('.png', image)[1].tobytes()


def _old_run(tmp_path, monkeypatch, restored_changed=False, record_sha=True, tamper=False, drop=None):
    import museum_processing
    monkeypatch.setattr(museum_processing, 'BASE', tmp_path)
    # Merge note (arch-backend M-6): keep results in tmp_path even if a results-dir override exists.
    monkeypatch.delenv('RUBBINGMIND_RESULTS_DIR', raising=False)
    monkeypatch.setattr(museum_processing, 'RESULTS_DIR', None, raising=False)
    museum_processing._READ_CACHE.clear()
    folder = tmp_path / 'static/results/stele_x' / RUN_ID
    folder.mkdir(parents=True)
    gray = np.full((16, 16), 120, np.uint8); gray[4:12, 7:9] = 30
    restored = gray.copy()
    if restored_changed:
        restored[0, 0] = 121
    files = {'original': _png(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)), 'restored': _png(cv2.cvtColor(restored, cv2.COLOR_GRAY2BGR))}
    for role, raw in files.items():
        if role != drop:
            (folder / f'{role}.png').write_bytes(raw)
    hashes = {role: hashlib.sha256(raw).hexdigest() for role, raw in files.items()} if record_sha else {}
    if tamper:
        (folder / 'restored.png').write_bytes(_png(cv2.cvtColor(np.zeros_like(gray), cv2.COLOR_GRAY2BGR)))
    images = {role: f'/static/results/stele_x/{RUN_ID}/{role}.png' for role in ('original', 'restored')}
    record = {'runId': RUN_ID, 'steleId': 'stele_x', 'outputImages': images, 'outputSha256': hashes, 'finishedAt': '2026-10-01T01:02:03+00:00'}
    (folder / 'processing.json').write_text(json.dumps(record), encoding='utf-8')
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    data = museum_processing.read_run('stele_x', RUN_ID)
    after = {p.name: p.read_bytes() for p in folder.iterdir()}
    assert before == after, 'read_run must not write back'
    return data


def test_old_run_unchanged_is_computed_on_read_as_passthrough(tmp_path, monkeypatch):
    data = _old_run(tmp_path, monkeypatch)
    assert data['isPassthrough'] is True and data['changedPixelCount'] == 0
    assert data['passthroughSource'] == 'computed-on-read'
    assert data['passthroughCriterion'] == 'pixel-equal-v1'
    assert data['comparedImages'] == ['original', 'restored']
    assert data['outputMode'] == 'passthrough' and data['passthroughUndeterminedReason'] is None
    assert data['grayChangedPixelCount'] == 0 and data['grayCriterion'] == 'gray-bt601-pixel-equal-v1'


def test_old_run_changed_is_computed_on_read_as_processed(tmp_path, monkeypatch):
    data = _old_run(tmp_path, monkeypatch, restored_changed=True)
    assert data['isPassthrough'] is False and data['changedPixelCount'] == 1
    assert data['passthroughSource'] == 'computed-on-read' and data['outputMode'] == 'processed'


def test_old_run_sha_mismatch_is_null(tmp_path, monkeypatch):
    data = _old_run(tmp_path, monkeypatch, tamper=True)
    assert data['isPassthrough'] is None and data['passthroughSource'] is None and data['passthroughCriterion'] is None
    assert data['outputMode'] == 'undetermined' and 'SHA-256' in data['passthroughUndeterminedReason']


def test_old_run_without_recorded_sha_is_null(tmp_path, monkeypatch):
    data = _old_run(tmp_path, monkeypatch, record_sha=False)
    assert data['isPassthrough'] is None and data['passthroughSource'] is None


def test_old_run_missing_image_is_null(tmp_path, monkeypatch):
    data = _old_run(tmp_path, monkeypatch, drop='original')
    assert data['isPassthrough'] is None and data['passthroughSource'] is None
    assert data['passthroughUndeterminedReason'] and ('缺少' in data['passthroughUndeterminedReason'] or 'original' in data['passthroughUndeterminedReason'])


def test_pixel_equal_v1_compares_all_channels():
    from museum_processing import run_change_status
    color = np.full((8, 8, 3), 100, np.uint8); color[..., 2] = 110
    gray = cv2.cvtColor(cv2.cvtColor(color, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    stats = run_change_status(_png(color), _png(gray))
    # Color input, gray output: changed under pixel-equal-v1, unchanged in the gray view.
    assert stats['isPassthrough'] is False and stats['changedPixelCount'] == 64
    assert stats['grayChangedPixelCount'] == 0 and stats['grayChangedPixelRatio'] == 0
    assert stats['passthroughCriterion'] == 'pixel-equal-v1' and stats['passthroughSource'] == 'recorded'
    assert run_change_status(_png(color), _png(color))['isPassthrough'] is True


def test_undeterminable_has_null_criterion_and_source():
    from museum_processing import run_change_status
    color = np.full((8, 8, 3), 100, np.uint8)
    for stats in (run_change_status(_png(color), _png(color[:4])), run_change_status(b'', _png(color)),
                  run_change_status(b'not a png', _png(color))):
        assert stats['isPassthrough'] is None
        assert stats['passthroughCriterion'] is None and stats['passthroughSource'] is None
        assert stats['passthroughUndeterminedReason']


def test_change_stats_does_not_overflow_on_16_bit():
    from degradation_analysis import change_stats
    a = np.zeros((2, 2), np.uint16); b = a.copy(); b[0, 0] = 40000
    stats = change_stats(a, b)
    assert stats['changedPixelCount'] == 1 and stats['maxAbsDiff'] == 40000
