"""Live report contract: frozen derivatives, provenance checks and legacy bookmarks."""
import hashlib
import json

from fastapi.testclient import TestClient

import experiment_registry
from main import app

EXP = 'controlled-rubbings-v2-text-2026-10-17'
DIR = '2026-10-17-v2-text'
URL = f'/api/experiments/{EXP}/derived/'


def test_report_derivatives_are_reachable_without_development_cache():
    client = TestClient(app)
    for name in ['applied_status.json', 'negative_lift_causes.json', 'mechanism/index.json']:
        response = client.get(URL + name)
        assert response.status_code == 200, (name, response.text)
        assert response.json()['batch'] == DIR
    index = client.get(URL + 'mechanism/index.json').json()
    case_id = index['cases'][0]['caseId']
    detail = client.get(URL + f'mechanism/{case_id}/mechanism.json')
    assert detail.status_code == 200
    assert detail.json()['headCommit'] == index['headCommit']
    image = detail.json()['images'][0]
    response = client.get(URL + f'mechanism/{case_id}/{image["file"]}')
    assert response.status_code == 200
    assert hashlib.sha256(response.content).hexdigest() == image['sha256']


def test_report_reader_rejects_unregistered_and_encoded_paths():
    client = TestClient(app)
    for relative in ['unknown.json', 'mechanism/unknown/mechanism.json',
                     'mechanism/index.json%00', 'mechanism/%252e%252e/main.py',
                     'mechanism/C:/main.py', 'mechanism/../main.py']:
        assert client.get(URL + relative).status_code in (400, 404)


def test_report_reader_refuses_stale_numerical_provenance(tmp_path, monkeypatch):
    monkeypatch.setattr(experiment_registry, 'RESULTS', tmp_path)
    folder = tmp_path / DIR
    derived = folder / 'derived'
    derived.mkdir(parents=True)
    (folder / 'results.json').write_text(json.dumps({
        'config': {'experimentId': EXP}, 'rows': [], 'summary': []}), encoding='utf-8')
    for name in ['applied_status.json', 'negative_lift_causes.json', 'ci_by_artifact.json']:
        (derived / name).write_text(json.dumps({
            'batch': DIR, 'sourceResultsSha256': '0' * 64}), encoding='utf-8')
        response = TestClient(app).get(URL + name)
        assert response.status_code == 409
        assert 'sourceResultsSha256' in response.json()['detail']


def test_legacy_bookmark_redirects_to_current_frontend():
    response = TestClient(app).get('/static/index.html', follow_redirects=False)
    assert response.status_code == 308
    assert response.headers['location'] == '/'
