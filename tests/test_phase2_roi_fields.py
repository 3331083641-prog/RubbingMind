"""Phase 2 ROI local-compare field contract (PHASE2_ROI_FIELD_GAP G1-G8 / PHASE2_ROI_REQUESTS).

Asserts that report/API responses expose or explicitly lack the seven skeleton fields:
steleId / source SHA / runId / ROI / version / params / time.
Landed R1–R6 gaps are asserted; remaining product gaps (e.g. A24) are xfail/skip with gap ids — never silent pass.
Does not fabricate ground-truth stele labels; uses live API + checked-in TS/source contracts.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import database
import glyph_inference
import pytest
from fastapi.testclient import TestClient

from main import app

ROOT = Path(__file__).resolve().parents[1]
API_TS = ROOT / "apps" / "web" / "src" / "services" / "api.ts"
MAIN_PY = ROOT / "main.py"
MECH_INDEXES = [
    ROOT / "experiments" / "results" / "2026-10-17-v2" / "derived" / "mechanism" / "index.json",
    ROOT / "experiments" / "results" / "2026-10-17-v2-text" / "derived" / "mechanism" / "index.json",
]
MECH_HEAD = "7623a52a3299b7c948031dfa1f79f04b8eb66d9e"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "phase2_roi.sqlite"))
    monkeypatch.setattr(glyph_inference, "INFERENCE_DIR", tmp_path / "crops")
    monkeypatch.delenv("RUBBINGMIND_VISION_API_KEY", raising=False)
    return TestClient(app)


def _create_inference(client):
    # Empty context -> deterministic no_candidate path; still returns full ROI/SHA envelope.
    response = client.post(
        "/api/steles/tang_01_duobao/inferences",
        json={"bbox": {"x": 80, "y": 80, "w": 64, "h": 64}, "context": "", "characterId": "c7"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_inference_has_stele_id_source_sha_runid_roi_time(client):
    """F1/F2/F3/F4/F7: backend inference envelope is traceable."""
    body = _create_inference(client)
    assert body["steleId"] == "tang_01_duobao"
    assert isinstance(body["inputImageSha256"], str) and len(body["inputImageSha256"]) == 64
    assert isinstance(body["cropSha256"], str) and len(body["cropSha256"]) == 64
    assert "runId" in body  # may be null for original image — key must exist
    assert body["bbox"] == {"x": 80, "y": 80, "w": 64, "h": 64}
    roi = body["roi"]
    assert set(roi) >= {
        "imageBBox",
        "mappedSourceBBox",
        "mappedInsideSource",
        "cropWidth",
        "cropHeight",
        "scaleFromSource",
    }
    assert isinstance(body["createdAt"], str) and "T" in body["createdAt"]


def test_report_includes_stele_and_inference_records_with_sha(client):
    """Report path surfaces stele id + inferenceRecords that keep SHA/ROI when present."""
    created = _create_inference(client)
    report = client.get("/api/steles/tang_01_duobao/report").json()
    assert report["stele_id"] == "tang_01_duobao"
    records = report.get("inferenceRecords") or []
    assert any(r.get("inferenceId") == created["inferenceId"] for r in records)
    matched = next(r for r in records if r["inferenceId"] == created["inferenceId"])
    assert matched.get("inputImageSha256") == created["inputImageSha256"]
    assert "roi" in matched and "bbox" in matched
    assert "createdAt" in matched


def test_inference_exposes_version_and_effective_parameters_g5(client):
    """G5/R5: inference envelope exposes algorithmVersion/effectiveParameters (nullable) + reason when unjoined."""
    body = _create_inference(client)
    assert "algorithmVersion" in body
    assert "effectiveParameters" in body
    # original-image inference: runId is null → params stay null with explicit unavailable reason
    if body.get("runId") is None:
        assert body.get("effectiveParameters") is None
        reason = body.get("effectiveParametersUnavailableReason")
        assert isinstance(reason, str) and reason.strip(), body


def test_ts_glyph_inference_record_declares_roi_and_shas_g1():
    """G1/R1: TS GlyphInferenceRecord declares roi + inputImageSha256 + cropSha256 (AB-7 / feature@e9ce60e (via 08d8da8))."""
    text = API_TS.read_text(encoding="utf-8")
    m = re.search(r"export interface GlyphInferenceRecord \{([\s\S]*?)\n\}", text)
    assert m, "GlyphInferenceRecord interface missing"
    block = m.group(1)
    needed = ("roi", "inputImageSha256", "cropSha256")
    for name in needed:
        assert re.search(rf"\b{name}\b", block), f"G1/R1: GlyphInferenceRecord missing {name}"
    for nested in (
        "imageBBox",
        "mappedSourceBBox",
        "mappedInsideSource",
        "cropWidth",
        "cropHeight",
        "scaleFromSource",
    ):
        assert re.search(rf"\b{nested}\b", block), f"G1/R1: roi envelope missing {nested}"



def test_roi_geometry_normalized_for_export_g2(client):
    """G2/R2: dual wire schemas remain, but export normalize path yields single glyph-bbox."""
    from roi_geometry import SCHEMA_GLYPH, export_geometry, normalize_roi

    main = MAIN_PY.read_text(encoding="utf-8")
    assert "class GlyphBox" in main and "class ReviewBox" in main
    glyph = main[main.find("class GlyphBox") : main.find("class GlyphBox") + 200]
    review = main[main.find("class ReviewBox") : main.find("class ReviewBox") + 200]
    assert ("w:" in glyph or "w :" in glyph) and ("h:" in glyph or "h :" in glyph)
    assert "width" in review and "height" in review

    g = normalize_roi({"x": 10, "y": 20, "w": 64, "h": 48})
    r = normalize_roi({"x": 10, "y": 20, "width": 64, "height": 48})
    assert g["schema"] == SCHEMA_GLYPH and r["schema"] == SCHEMA_GLYPH
    assert (g["x"], g["y"], g["w"], g["h"]) == (r["x"], r["y"], r["w"], r["h"])
    exported = export_geometry({"x": 1, "y": 2, "width": 3, "height": 4})
    assert exported["schema"] == SCHEMA_GLYPH and "width" not in exported

    api = client.get(
        "/api/roi-geometry/normalize",
        params={"x": 1, "y": 2, "width": 30, "height": 40},
    )
    assert api.status_code == 200, api.text
    body = api.json()
    assert body["schema"] == "glyph-bbox"
    assert body["sourceSchema"] == "review-box"
    assert (body["x"], body["y"], body["w"], body["h"]) == (1, 2, 30, 40)


def test_paired_roi_compare_session_g3(client):
    """G3/R3: dedicated roi-compare session exists; missing run → explicit unavailableReason."""
    _create_inference(client)
    report = client.get("/api/steles/tang_01_duobao/report").json()
    assert "roiCompareSession" in report

    response = client.get("/api/steles/tang_01_duobao/roi-compare")
    assert response.status_code == 200, response.text
    session = response.json()
    for key in (
        "steleId",
        "runId",
        "bbox",
        "beforeImageSha256",
        "afterImageSha256",
        "beforeCropSha256",
        "afterCropSha256",
        "algorithmVersion",
        "effectiveParameters",
        "createdAt",
        "unavailableReason",
    ):
        assert key in session, key
    assert session["steleId"] == "tang_01_duobao"
    # No processing run on this fixture → must not fabricate paired SHAs
    if session.get("runId") is None:
        assert session.get("beforeCropSha256") is None and session.get("afterCropSha256") is None
        assert isinstance(session.get("unavailableReason"), str) and session["unavailableReason"].strip()


def test_catalog_assessment_run_link_g4(client):
    """G4/R4: assessment exposes runId and/or runLinkUnavailableReason (no silent omit)."""
    response = client.get("/api/catalog/tang_01_duobao/assessment")
    if response.status_code == 404:
        pytest.skip("G4/R4: no assessment payload for sample stele in this worktree")
    assert response.status_code == 200, response.text
    data = response.json()
    has_run = data.get("runId") or data.get("processingRunId")
    reason = data.get("runLinkUnavailableReason")
    assert has_run or reason, sorted(data.keys())[:30]
    # When runLink is null, reason must explain namespace / miss — never silent
    if data.get("runLink") is None:
        assert isinstance(reason, str) and reason.strip(), data


def test_mechanism_case_ids_are_not_product_stele_ids_g6(client):
    """G6/R6: case-stele mapping API exists; unmapped mechanism caseId must not claim same artifact."""
    overview = client.get("/api/case-stele-mapping")
    assert overview.status_code == 200, overview.text
    ov = overview.json()
    assert ov.get("available") is True or ov.get("entries") is not None
    assert (ROOT / "data" / "catalog" / "case_stele_mapping.json").is_file()

    resolved_any = False
    for path in MECH_INDEXES:
        if not path.is_file():
            continue
        index = json.loads(path.read_text(encoding="utf-8"))
        cases = index.get("cases") or []
        assert cases, path
        sample = cases[0]
        case_id = sample.get("caseId") or sample.get("id")
        assert case_id, sample
        entry = client.get(f"/api/case-stele-mapping/{case_id}")
        assert entry.status_code == 200, entry.text
        body = entry.json()
        assert body.get("caseId") == case_id
        # Refuse silent equate: either unmapped, or claim gate closed without human_reviewed
        assert body.get("sameArtifactClaimAllowed") is False
        if not body.get("mapped"):
            assert body.get("steleId") is None
            assert isinstance(body.get("unavailableReason"), str) and body["unavailableReason"].strip()
        resolved_any = True
        break
    if not resolved_any:
        pytest.skip("mechanism index missing; mapping API still asserted via overview")


def test_mechanism_head_commit_lag_documented_g7():
    """G7/R7: headCommit still 7623a52; MECHANISM_HEAD_NOTE must exist."""
    note = ROOT / "docs" / "product-upgrade" / "MECHANISM_HEAD_NOTE.md"
    assert note.is_file(), "MECHANISM_HEAD_NOTE.md required while headCommit lags tip"
    for path in MECH_INDEXES:
        if not path.is_file():
            pytest.skip(f"missing {path}")
        head = json.loads(path.read_text(encoding="utf-8")).get("headCommit")
        assert head == MECH_HEAD, f"{path} headCommit={head}"
    text = note.read_text(encoding="utf-8")
    assert "7623a52" in text
    # Chinese ban phrase from the note
    assert "\u5b57\u8282\u4e00\u81f4" in text  # 字节一致


def test_gap_doc_lists_g1_through_g8():
    gap = (ROOT / "docs" / "product-upgrade" / "PHASE2_ROI_FIELD_GAP.md").read_text(encoding="utf-8")
    req = (ROOT / "docs" / "product-upgrade" / "PHASE2_ROI_REQUESTS.md").read_text(encoding="utf-8")
    for i in range(1, 9):
        assert f"G{i}" in gap and f"R{i}" in req
