"""RT-006 partial / RT-007 / RT-011: root fallback, .env.example, start/check scripts."""
from __future__ import annotations

from pathlib import Path

import main as main_mod
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


def test_rt006_root_no_static_index_fallback(monkeypatch, tmp_path):
    """When dist/index.html is missing, / must not serve static/index.html (503)."""
    monkeypatch.setattr(main_mod, "DIST_DIR", str(tmp_path / "missing-dist"))
    client = TestClient(main_mod.app)
    r = client.get("/")
    assert r.status_code == 503
    body = r.json()
    assert body.get("status") == "frontend_build_required"
    # must not look like the legacy Vue shell
    text = r.text.lower()
    assert "vue@" not in text
    assert "rm_api_key" not in text


def test_rt007_env_example_uses_rubbingmind_keys():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    required = [
        "RUBBINGMIND_DEPLOYMENT",
        "RUBBINGMIND_ADMIN_TOKEN",
        "RUBBINGMIND_REVIEW_TOKEN",
        "RUBBINGMIND_VISION_API_KEY",
        "RUBBINGMIND_DB_PATH",
        "RUBBINGMIND_RUNTIME_DIR",
        "RUBBINGMIND_UPLOAD_DIR",
        "RUBBINGMIND_RESULTS_DIR",
    ]
    for key in required:
        assert key in text, f"missing {key}"
    # legacy mismatched names must not reappear as the primary contract
    assert "LLM_API_KEY" not in text
    assert "OPENAI_API_KEY" not in text or "RUBBINGMIND_VISION" in text


def test_rt011_start_and_check_use_api_health_only():
    start = (ROOT / "start.ps1").read_text(encoding="utf-8-sig")
    check = (ROOT / "check.ps1").read_text(encoding="utf-8-sig")
    assert "/api/health" in start
    assert "/api/health" in check
    # readiness must not POST /generate (remote returns 401)
    for label, text in (("start.ps1", start), ("check.ps1", check)):
        posts = [
            ln.strip()
            for ln in text.splitlines()
            if "Invoke-RestMethod" in ln and "/generate" in ln
        ]
        assert posts == [], f"{label} still POSTs /generate: {posts}"
