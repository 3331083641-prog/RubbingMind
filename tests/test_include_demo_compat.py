"""BR-08: EvidenceQueryRequest.includeDemo defaults False; compatible when query() lacks include_demo."""
from fastapi.testclient import TestClient
from main import app


def test_include_demo_default_and_compat(monkeypatch):
    import evidence_retrieval
    calls = []

    def fake_query(question, stele_id=None, limit=12):  # no include_demo param
        calls.append((question, stele_id))
        return {'hits': [], 'demoScope': {'included': False}}

    monkeypatch.setattr(evidence_retrieval, 'query', fake_query)
    client = TestClient(app)
    body = client.post('/api/research/query', json={'question': '今天天气怎么样'}).json()
    assert calls and body['demoScope']['requested'] is False and body['demoScope']['honoured'] is False
    body2 = client.post('/api/research/query', json={'question': '建义样本', 'includeDemo': True}).json()
    assert body2['demoScope']['requested'] is True and body2['demoScope']['honoured'] is False
    assert 'jinshi' in body2['demoScope']['compatNote']


def test_include_demo_forwarded_when_supported(monkeypatch):
    import evidence_retrieval
    seen = {}

    def fake_query(question, stele_id=None, limit=12, include_demo=False):
        seen['include_demo'] = include_demo
        return {'hits': [], 'demoScope': {'included': include_demo, 'optIn': 'include_demo' if include_demo else None}}

    monkeypatch.setattr(evidence_retrieval, 'query', fake_query)
    client = TestClient(app)
    body = client.post('/api/research/query', json={'question': '建义', 'includeDemo': True}).json()
    assert seen['include_demo'] is True and body['demoScope']['included'] is True
