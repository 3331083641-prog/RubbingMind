"""Red-team gate (7c0e258) item 4 / REPORT_DATA_SPEC §8: comparedImages array, criterion non-null when
SHA verifies, effectiveParameters derived on read or null with an explicit reason. Nothing is written back."""
import hashlib
import json

import cv2
import numpy as np

import museum_processing

STELE = 'qing_02_wushi_reerection'


def _setup(tmp_path, monkeypatch):
    monkeypatch.setattr(museum_processing, 'BASE', tmp_path)
    monkeypatch.setattr(museum_processing, 'RESULTS_DIR', None)
    museum_processing._READ_CACHE.clear()


def _write(tmp_path, run_id, record, images=True, legacy=False):
    folder = tmp_path / 'static/results' / STELE / run_id
    folder.mkdir(parents=True)
    if images:
        gray = np.full((4, 4), 9, np.uint8)
        raw = {'original': cv2.imencode('.png', gray)[1].tobytes(), 'restored': cv2.imencode('.png', gray)[1].tobytes()}
        for role, data in raw.items():
            (folder / f'{role}.png').write_bytes(data)
        record.setdefault('outputImages', {r: f'/static/results/{STELE}/{run_id}/{r}.png' for r in raw})
        record.setdefault('outputSha256', {r: hashlib.sha256(d).hexdigest() for r, d in raw.items()})
    payload = record if legacy else {'runId': run_id, 'steleId': STELE, **record}  # legacy records had no runId
    (folder / 'processing.json').write_text(json.dumps(payload), 'utf-8')
    return folder


def test_old_run_with_verified_sha_has_non_null_criterion_and_derived_parameters(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    params = {'filter_type': 'adaptive', 'd0': 45.0, 'filter_order': 2, 'h_nlm': 10.0, 'clahe_clip': 2.5, 'morph_kernel': 3}
    folder = _write(tmp_path, '20261017T095714_4c9e66e5', {'algorithmVersion': 'adaptive-rubbing-v2.0', 'algorithmParameters': params})
    before = {p: p.read_bytes() for p in folder.iterdir()}
    run = museum_processing.read_run(STELE, '20261017T095714_4c9e66e5')
    assert run['passthroughCriterion'] == 'pixel-equal-v1' and run['passthroughSource'] == 'computed-on-read'
    assert run['isPassthrough'] is True and run['comparedImages'] == ['original', 'restored']
    assert run['effectiveParameters']['strength'] == 1.0 and run['effectiveParameters']['notchWidth'] == 0.75
    assert run['effectiveParametersSource'] == 'derived-on-read' and run['effectiveParametersUnavailableReason'] is None
    assert {p: p.read_bytes() for p in folder.iterdir()} == before


def test_fixed_path_parameters_derived_and_unknown_version_is_null_with_reason(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    params = {'filter_type': 'butterworth', 'd0': 45.0, 'filter_order': 2, 'h_nlm': 10.0, 'clahe_clip': 2.5, 'morph_kernel': 7}
    _write(tmp_path, '20261017T093048_6fc67e99', {'algorithmVersion': 'frequency-spatial-v2.1', 'algorithmParameters': params})
    fixed = museum_processing.read_run(STELE, '20261017T093048_6fc67e99')
    assert fixed['effectiveParameters'] == {'mode': 'butterworth', 'd0': 45.0, 'filterOrder': 2, 'nlmH': 10.0, 'claheClip': 2.5,
                                            'morphKernel': 7, 'ignoredRequestParameters': []}
    _write(tmp_path, '20261017T093049_6fc67e9a', {'algorithmVersion': 'adaptive-rubbing-v1.9', 'algorithmParameters': {**params, 'filter_type': 'adaptive'}})
    unknown = museum_processing.read_run(STELE, '20261017T093049_6fc67e9a')
    assert unknown['effectiveParameters'] is None and unknown['effectiveParametersSource'] is None
    assert '未经核实' in unknown['effectiveParametersUnavailableReason']


def test_legacy_run_parameters_null_with_reason(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    _write(tmp_path, '20261014T165542_5fc44fba', {'stele_id': STELE, 'restored_image': '', 'parameters': {'d0': 45.0}}, images=False, legacy=True)
    legacy = museum_processing.read_run(STELE, '20261014T165542_5fc44fba')
    assert legacy['algorithmVersion'] == 'legacy-unverified'
    assert legacy['effectiveParameters'] is None and '旧版未核验运行' in legacy['effectiveParametersUnavailableReason']
    assert legacy['passthroughCriterion'] is None and legacy['isPassthrough'] is None  # undeterminable only


def test_compared_images_object_from_older_records_is_normalised(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    _write(tmp_path, '20261019T000001_000000aa', {'algorithmVersion': 'adaptive-rubbing-v2.1', 'isPassthrough': True,
                                                  'passthroughCriterion': 'working-gray-pixel-equal-v1',
                                                  'comparedImages': {'before': 'original', 'after': 'restored'},
                                                  'effectiveParameters': {'mode': 'adaptive'}})
    run = museum_processing.read_run(STELE, '20261019T000001_000000aa')
    assert run['comparedImages'] == ['original', 'restored']
    assert run['passthroughCriterion'] == 'working-gray-pixel-equal-v1'  # SPEC §8: shown as recorded, never rewritten
    assert run['effectiveParametersSource'] == 'recorded'
