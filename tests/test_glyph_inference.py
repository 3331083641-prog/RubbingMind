import database
import glyph_inference
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'inference.sqlite'))
    monkeypatch.setattr(glyph_inference, 'INFERENCE_DIR', tmp_path / 'crops')
    monkeypatch.delenv('RUBBINGMIND_VISION_API_KEY', raising=False)
    return TestClient(app)


def test_actual_crop_rule_accept_revoke_and_persistence(client):
    payload = {'bbox': {'x': 80, 'y': 80, 'w': 64, 'h': 64}, 'context': '慶歸法',
               'characterId': 'c7', 'originalGlyph': '□', 'originalStatus': 'damaged'}
    response = client.post('/api/steles/tang_01_duobao/inferences', json=payload)
    assert response.status_code == 200, response.text
    record = response.json()
    assert record['source'] == 'context_rule' and record['candidates'][0]['glyph'] == '胤'
    assert record['candidates'][0]['visualEvidence'] == '规则未分析图像笔画'
    assert 'prob' not in str(record)
    assert client.get(record['cropUrl']).headers['content-type'] == 'image/png'
    assert client.get('/api/steles/tang_01_duobao/inferences').json()[0]['inferenceId'] == record['inferenceId']
    accepted = client.post(f"/api/inferences/{record['inferenceId']}/decision", json={'action': 'accept', 'glyph': '胤'}).json()
    assert accepted['adoptedGlyph'] == '胤' and accepted['status'] == 'human_accepted'
    assert client.post(f"/api/inferences/{record['inferenceId']}/decision", json={'action': 'accept', 'glyph': '銘'}).status_code == 422
    revoked = client.post(f"/api/inferences/{record['inferenceId']}/decision", json={'action': 'revoke'}).json()
    assert revoked['adoptedGlyph'] is None and [event['action'] for event in revoked['decisions']] == ['accept', 'revoke']
    assert glyph_inference.get_inference(record['inferenceId'])['status'] == 'pending_review'


def test_crop_context_and_model_failure_states(client, monkeypatch):
    assert client.post('/api/steles/tang_01_duobao/inferences', json={'bbox': {'x': 10, 'y': 10, 'w': 40, 'h': 40}, 'runId': 'missing'}).status_code == 404
    assert client.post('/api/steles/tang_01_duobao/inferences', json={'bbox': {'x': -1, 'y': 0, 'w': 40, 'h': 40}}).status_code == 422
    assert client.post('/api/steles/tang_01_duobao/inferences', json={'bbox': {'x': 99999, 'y': 0, 'w': 40, 'h': 40}}).status_code == 422
    empty = client.post('/api/steles/tang_01_duobao/inferences', json={'bbox': {'x': 10, 'y': 10, 'w': 40, 'h': 40}, 'context': ''}).json()
    assert empty['status'] == 'no_candidate' and empty['candidates'] == []
    monkeypatch.setenv('RUBBINGMIND_VISION_API_KEY', 'placeholder-local-test-key')
    monkeypatch.setenv('RUBBINGMIND_VISION_BASE_URL', 'http://invalid.example')
    failed = client.post('/api/steles/tang_01_duobao/inferences', json={'bbox': {'x': 10, 'y': 10, 'w': 40, 'h': 40}, 'context': '慶歸法'}).json()
    assert failed['source'] == 'model_unavailable' and failed['candidates'] == []
