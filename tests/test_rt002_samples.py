"""RT-002: ensure_samples never downloads/synthesizes; health reports samples_missing."""
from __future__ import annotations

import hashlib
from pathlib import Path

import sample_generator as sg


def test_check_samples_ok_on_tracked_files():
    report = sg.check_samples()
    assert report["ok"] is True
    assert report["missing"] == []
    assert report["sha_mismatch"] == []
    assert set(report["present"]) == {f"sample_{i}.png" for i in range(1, 5)}


def test_ensure_samples_is_side_effect_free(tmp_path, monkeypatch):
    """Missing sample => report missing; no new files under SAMPLES_DIR."""
    fake = tmp_path / "samples"
    fake.mkdir()
    # copy only 3 samples
    real = Path(sg.SAMPLES_DIR)
    for i in (1, 2, 3):
        (fake / f"sample_{i}.png").write_bytes((real / f"sample_{i}.png").read_bytes())
    monkeypatch.setattr(sg, "SAMPLES_DIR", str(fake))
    before = {p.name: p.stat().st_mtime_ns for p in fake.iterdir()}
    report = sg.check_samples()
    assert "sample_4.png" in report["missing"]
    assert report["ok"] is False
    after = {p.name for p in fake.iterdir()}
    assert after == set(before)  # no new files
    assert "sample_4.png" not in after
    # legacy API still returns only present
    present = sg.ensure_samples()
    assert "sample_4.png" not in present
    assert set(present) == {"sample_1.png", "sample_2.png", "sample_3.png"}


def test_sha_mismatch_reported_without_rewrite(tmp_path, monkeypatch):
    fake = tmp_path / "samples"
    fake.mkdir()
    real = Path(sg.SAMPLES_DIR)
    for i in range(1, 5):
        data = (real / f"sample_{i}.png").read_bytes()
        if i == 2:
            data = data + bytes([0])  # corrupt
        (fake / f"sample_{i}.png").write_bytes(data)
    monkeypatch.setattr(sg, "SAMPLES_DIR", str(fake))
    report = sg.check_samples()
    assert any(m["key"] == "sample_2.png" for m in report["sha_mismatch"])
    # file not replaced with synth/download
    digest = hashlib.sha256((fake / "sample_2.png").read_bytes()).hexdigest()
    assert digest != sg.EXPECTED_SAMPLE_SHA256["sample_2.png"]


def test_health_reports_samples_missing(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    import main as main_mod
    import sample_generator as sg_mod

    fake = tmp_path / "samples"
    fake.mkdir()
    monkeypatch.setattr(sg_mod, "SAMPLES_DIR", str(fake))
    # also patch main's bound name if any — health calls check_samples from sample_generator
    client = TestClient(main_mod.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "degraded"
    assert set(body["samples_missing"]) == {f"sample_{i}.png" for i in range(1, 5)}
