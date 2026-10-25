"""Phase2 ROI contracts R2–R6/R8 (arch-backend).

Acceptance mirrors PHASE2_ROI_REQUESTS.md. R1/R7 are owned elsewhere.
"""
from __future__ import annotations

import json
from pathlib import Path

import database
import glyph_inference
import pytest
from fastapi.testclient import TestClient

from main import app
from roi_geometry import RoiGeometryError, export_geometry, normalize_roi, to_review_box

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "phase2_roi.sqlite"))
    monkeypatch.setattr(glyph_inference, "INFERENCE_DIR", tmp_path / "crops")
    monkeypatch.delenv("RUBBINGMIND_VISION_API_KEY", raising=False)
    return TestClient(app)


# ----- R2 -----
def test_r2_normalize_glyph_and_review_to_single_schema():
    g = normalize_roi({"x": 10, "y": 20, "w": 64, "h": 48})
    assert g == {"x": 10, "y": 20, "w": 64, "h": 48, "schema": "glyph-bbox", "sourceSchema": "glyph-bbox"}
    r = normalize_roi({"x": 10, "y": 20, "width": 64, "height": 48})
    assert r["w"] == 64 and r["h"] == 48 and r["schema"] == "glyph-bbox"
    assert r["sourceSchema"] == "review-box"
    back = to_review_box(g)
    assert back["width"] == 64 and back["height"] == 48 and back["schema"] == "review-box"
    exported = export_geometry({"x": 1, "y": 2, "width": 3, "height": 4})
    assert set(exported) >= {"x", "y", "w", "h", "schema"}
    assert "width" not in exported and "height" not in exported


def test_r2_rejects_ambiguous_mixed_fields():
    with pytest.raises(RoiGeometryError):
        normalize_roi({"x": 0, "y": 0, "w": 1, "h": 1, "width": 2, "height": 2})


def test_r2_normalize_api(client):
    ok = client.get("/api/roi-geometry/normalize", params={"x": 1, "y": 2, "width": 30, "height": 40})
    assert ok.status_code == 200
    body = ok.json()
    assert body["w"] == 30 and body["schema"] == "glyph-bbox"
    bad = client.get("/api/roi-geometry/normalize", params={"x": 1, "y": 2})
    assert bad.status_code == 422


# ----- R3 -----
def test_r3_roi_compare_without_run_has_reason(client):
    res = client.get("/api/steles/tang_01_duobao/roi-compare")
    assert res.status_code == 200
    body = res.json()
    assert body["beforeImageSha256"] is None and body["afterImageSha256"] is None
    assert body["unavailableReason"] and "runId" in body["unavailableReason"]
    report = client.get("/api/steles/tang_01_duobao/report").json()
    assert "roiCompareSession" in report
    assert report["roiCompareSession"]["unavailableReason"]


def test_r3_roi_compare_missing_run_reason(client):
    res = client.get(
        "/api/steles/tang_01_duobao/roi-compare",
        params={"runId": "20990101T000000_deadbeef", "x": 10, "y": 10, "w": 32, "h": 32},
    )
    assert res.status_code == 200
    assert res.json()["unavailableReason"]


# ----- R4 -----
def test_r4_assessment_exposes_run_link_or_reason(client):
    response = client.get("/api/catalog/tang_01_duobao/assessment")
    if response.status_code == 404:
        pytest.skip("no assessment for sample")
    assert response.status_code == 200
    data = response.json()
    assert "runLink" in data
    if data.get("runId") or data.get("processingRunId"):
        # archived assess28-* ids do not match live ProcessingRun namespace
        if data["runLink"] is None:
            assert data.get("runLinkUnavailableReason")
        else:
            assert data["runLink"]["matched"] is True
            assert data["runLinkUnavailableReason"] is None
    else:
        assert data["runLink"] is None and data.get("runLinkUnavailableReason")


# ----- R5 -----
def test_r5_inference_without_run_has_unavailable_reason(client):
    response = client.post(
        "/api/steles/tang_01_duobao/inferences",
        json={"bbox": {"x": 80, "y": 80, "w": 64, "h": 64}, "context": "", "characterId": "c7"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "algorithmVersion" in body and "effectiveParameters" in body
    assert body["runId"] in (None, "") or body.get("runId") is None
    assert body["effectiveParameters"] is None
    assert body.get("effectiveParametersUnavailableReason")


def test_r5_list_inferences_enriched(client):
    client.post(
        "/api/steles/tang_01_duobao/inferences",
        json={"bbox": {"x": 80, "y": 80, "w": 64, "h": 64}},
    )
    listed = client.get("/api/steles/tang_01_duobao/inferences").json()
    assert listed
    assert "effectiveParametersUnavailableReason" in listed[0]
    assert "algorithmVersion" in listed[0]


# ----- R6 -----
def test_r6_case_stele_mapping_api_and_claim_gate(client):
    overview = client.get("/api/case-stele-mapping").json()
    assert overview.get("policy", {}).get("silentEquateForbidden") is True
    assert overview.get("available") is True
    mapped = client.get("/api/case-stele-mapping/tang-duobao").json()
    assert mapped["mapped"] is True
    assert mapped["steleId"] == "tang_01_duobao"
    assert mapped["sameArtifactClaimAllowed"] is False  # unreviewed
    denied = client.get("/api/case-stele-mapping/tang-duobao/claim/tang_01_duobao")
    assert denied.status_code == 409
    missing = client.get("/api/case-stele-mapping/no-such-case").json()
    assert missing["mapped"] is False and missing["unavailableReason"]
    # mapping file exists in repo
    assert (ROOT / "data/catalog/case_stele_mapping.json").is_file()


# ----- R8 -----
def test_r8_glyph_evaluation_stays_not_evaluated_without_truth(client):
    body = client.get("/api/glyph-evaluation").json()
    assert body["status"] == "not_evaluated"
    assert body["top1"] is None and body["top3"] is None
    assert body.get("rejectionRate") is None
    assert body.get("reason")
