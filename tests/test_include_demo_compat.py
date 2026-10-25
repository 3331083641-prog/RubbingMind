"""BR-08 / C-16: includeDemo defaults False; forwarded to jinshi evidence_retrieval.query."""
from fastapi.testclient import TestClient
from main import app


def test_include_demo_default_and_forwarded(monkeypatch):
    import evidence_retrieval
    seen = []

    def fake_query(question, stele_id=None, limit=12, include_demo=False):
        seen.append(include_demo)
        return {
            "hits": [],
            "evidence": [],
            "entities": [],
            "contentWarnings": [],
            "demoScope": {"included": include_demo, "optIn": "include_demo" if include_demo else None, "syntheticSamples": ["wei-jianyi"]},
            "status": "insufficient_evidence",
            "answer": "",
        }

    monkeypatch.setattr(evidence_retrieval, "query", fake_query)
    client = TestClient(app)
    body = client.post("/api/research/query", json={"question": "今天天气怎么样"}).json()
    assert seen == [False]
    assert body["demoScope"]["included"] is False
    body2 = client.post("/api/research/query", json={"question": "建义样本", "includeDemo": True}).json()
    assert seen[-1] is True and body2["demoScope"]["included"] is True


def test_rm_demo_stele_id_accepted(monkeypatch):
    import evidence_retrieval
    seen = {}

    def fake_query(question, stele_id=None, limit=12, include_demo=False):
        seen["stele_id"] = stele_id
        seen["include_demo"] = include_demo
        return {
            "evidence": [],
            "entities": [],
            "contentWarnings": [],
            "demoScope": {"included": True, "optIn": "demo_scope_id", "syntheticSamples": ["wei-jianyi"]},
            "status": "insufficient_evidence",
            "answer": "",
        }

    monkeypatch.setattr(evidence_retrieval, "query", fake_query)
    client = TestClient(app)
    r = client.post("/api/research/query", json={"question": "建义元年墓志", "steleId": "rm:demo:wei-jianyi"})
    assert r.status_code == 200, r.text
    assert seen["stele_id"] == "rm:demo:wei-jianyi"
