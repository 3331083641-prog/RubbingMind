"""RT-014: /api/process no longer defaults stele_id to tang-duobao."""
from types import SimpleNamespace

from fastapi.testclient import TestClient

import museum_processing
from main import ProcessRequest, app


def _patch(monkeypatch, tmp_path):
    monkeypatch.setattr(museum_processing, 'BASE', tmp_path)
    monkeypatch.setattr(museum_processing, 'RESULTS_DIR', None)


def test_model_has_no_default_artifact():
    assert ProcessRequest().stele_id is None


def test_missing_stele_id_is_422_and_writes_nothing(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    for body in ({}, {'d0': 45, 'filter_type': 'adaptive'}, {'stele_id': None}):
        response = TestClient(app).post('/api/process', json=body)
        assert response.status_code == 422, body
        assert 'stele_id' in response.json()['detail']
    assert not (tmp_path / 'static' / 'results').exists()


def test_frontend_payload_shape_still_processes(monkeypatch, tmp_path):
    """Same keys api.ts processStele sends (stele_id always present)."""
    _patch(monkeypatch, tmp_path)
    import main
    seen = {}
    def fake(req, manager, engine):
        seen['stele_id'] = req.stele_id
        return {'stele_id': req.stele_id, 'runId': 'x'}
    monkeypatch.setattr(main, 'process_verified_request', fake)
    payload = {'stele_id': 'han_01_caoquan', 'd0': 45, 'filter_order': 2, 'filter_type': 'adaptive', 'h_nlm': 10, 'clahe_clip': 2.5, 'morph_kernel': 3}
    response = TestClient(app).post('/api/process', json=payload)
    assert response.status_code == 200 and seen['stele_id'] == 'han_01_caoquan'


def test_sample_id_alone_is_no_longer_rerouted_to_tang_duobao(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    (tmp_path / 'static/samples').mkdir(parents=True)
    (tmp_path / 'static/samples/sample_1.png').write_bytes(b'x')
    def engine_call(**kwargs):
        assert kwargs['image_input'].endswith('sample_1.png')
        return {'error': 'stop here'}
    engine = SimpleNamespace(process_rubbing=engine_call)
    try:
        museum_processing.process_verified_request(ProcessRequest(sample_id='sample_1.png'), SimpleNamespace(get_stele_by_id=lambda _i: None, retired={}), engine)
    except Exception as exc:  # engine error -> 422 by design; what matters is which image was used
        assert getattr(exc, 'status_code', None) == 422
