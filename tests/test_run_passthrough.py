"""R1-2 / E-03: run-level isPassthrough per REPORT_DATA_SPEC §8 and honest report wording."""
import base64
import json
from types import SimpleNamespace

import cv2
import numpy as np
from fastapi.testclient import TestClient

import museum_processing
from main import app

STELE = 'qing_02_wushi_reerection'


def _png(image):
    return 'data:image/png;base64,' + base64.b64encode(cv2.imencode('.png', image)[1].tobytes()).decode('ascii')


def _patch(monkeypatch, tmp_path):
    monkeypatch.setattr(museum_processing, 'BASE', tmp_path)
    monkeypatch.setattr(museum_processing, 'RESULTS_DIR', None)


def _process(tmp_path, monkeypatch, changed_pixels):
    _patch(monkeypatch, tmp_path)
    (tmp_path / 'static/samples').mkdir(parents=True)
    gray = np.full((20, 40), 100, np.uint8)
    (tmp_path / 'static/samples/sample_2.png').write_bytes(cv2.imencode('.png', gray)[1].tobytes())
    restored = gray.copy()
    restored.flat[:changed_pixels] = 160
    engine = SimpleNamespace(process_rubbing=lambda **_: {
        'original_b64': _png(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)), 'restored_b64': _png(cv2.cvtColor(restored, cv2.COLOR_GRAY2BGR)),
        'metrics': {'elapsed_ms': 1.0}, 'diagnostic_metrics': {}, 'frequency_details': {}})
    params = dict(stele_id=None, sample_id='sample_2.png', image_base64=None, d0=30.0, filter_order=2, filter_type='adaptive',
                  h_nlm=5.0, clahe_clip=2.0, morph_kernel=3, damage_mask=None, cinnabar_style='cinnabar', random_seed=0)
    req = SimpleNamespace(**params, model_dump=lambda exclude=None: {k: v for k, v in params.items() if k not in (exclude or set())})
    response = museum_processing.process_verified_request(req, SimpleNamespace(get_stele_by_id=lambda _id: None, retired={}), engine)
    stored = json.loads(next((tmp_path / 'static/results/uploaded-image').glob('*/processing.json')).read_text('utf-8'))
    return response, stored


def test_unchanged_output_is_passthrough(tmp_path, monkeypatch):
    response, stored = _process(tmp_path, monkeypatch, 0)
    for record in (response, stored):
        assert record['isPassthrough'] is True and record['outputMode'] == 'passthrough'
        assert record['changedPixelCount'] == 0 and record['changedPixelRatio'] == 0 and record['totalPixelCount'] == 800
        assert record['passthroughCriterion'] == 'working-gray-pixel-equal-v1' and record['passthroughUndeterminedReason'] is None
    assert stored['effectiveParameters']['strength'] == 0.5 and stored['effectiveParameters']['notchWidth'] == 0.5


def test_changed_output_reports_real_ratio(tmp_path, monkeypatch):
    response, _ = _process(tmp_path, monkeypatch, 8)
    assert response['isPassthrough'] is False and response['outputMode'] == 'processed'
    assert response['changedPixelCount'] == 8 and response['changedPixelRatio'] == 8 / 800 and response['maxAbsDiff'] == 60


def test_missing_output_is_undetermined_never_guessed():
    status = museum_processing.run_change_status(None, b'x')
    assert status['isPassthrough'] is None and status['passthroughUndeterminedReason']
    status = museum_processing.run_change_status(b'not-a-png', b'not-a-png')
    assert status['isPassthrough'] is None and status['passthroughUndeterminedReason']


def _write(base, run_id, payload):
    folder = base / 'static/results' / STELE / run_id
    folder.mkdir(parents=True)
    (folder / 'processing.json').write_text(json.dumps(payload, ensure_ascii=False), 'utf-8')


def test_report_wording_follows_output_mode(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path)
    base = {'steleId': STELE, 'algorithmVersion': 'adaptive-rubbing-v2.1', 'evaluationStatus': 'unassessed', 'outputImages': {}}
    _write(tmp_path, '20261018T000001_00000001', dict(base, runId='20261018T000001_00000001', isPassthrough=True, outputMode='passthrough'))
    _write(tmp_path, '20261018T000002_00000002', dict(base, runId='20261018T000002_00000002', isPassthrough=False, outputMode='processed'))
    _write(tmp_path, '20261018T000003_00000003', dict(base, runId='20261018T000003_00000003'))  # saved before the criterion
    client = TestClient(app)
    url = f'/api/steles/{STELE}/report?run_id='
    passthrough = client.get(url + '20261018T000001_00000001').json()['evaluation_summary']
    assert passthrough.startswith('本次未改动原图') and '实际处理已执行' not in passthrough
    assert client.get(url + '20261018T000002_00000002').json()['evaluation_summary'].startswith('实际处理已执行')
    old = client.get(url + '20261018T000003_00000003').json()
    assert old['run']['isPassthrough'] is None and old['run']['outputMode'] == 'undetermined'
    assert old['run']['passthroughUndeterminedReason'] == '该运行保存于判据引入前，未记录改动量'
    assert old['run']['totalPixelCount'] is None and old['run']['meanAbsDiff'] is None
    assert old['evaluation_summary'].startswith('未能判定是否改动原图（该运行保存于判据引入前')
    stored = json.loads((tmp_path / 'static/results' / STELE / '20261018T000003_00000003' / 'processing.json').read_text('utf-8'))
    assert 'isPassthrough' not in stored  # old runs are never rewritten
