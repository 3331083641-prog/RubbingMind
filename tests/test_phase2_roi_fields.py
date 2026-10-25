"""Phase 2 ROI local-compare field contract (PHASE2_ROI_FIELD_GAP G1-G8 / PHASE2_ROI_REQUESTS).

Asserts that report/API responses expose or explicitly lack the seven skeleton fields:
steleId / source SHA / runId / ROI / version / params / time.
Missing product gaps are xfail/skip with gap ids — never silent pass.
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


def test_inference_lacks_version_and_effective_parameters_marked_g5(client):
    """F5/F6 on inference: currently absent — must not silently pretend they exist (G5/R5)."""
    body = _create_inference(client)
    missing = [k for k in ("algorithmVersion", "effectiveParameters") if k not in body]
    if missing:
        pytest.xfail(
            f"G5/R5: inference omits {missing}; join runId->run.effectiveParameters not on this payload"
        )
    assert "algorithmVersion" in body and "effectiveParameters" in body


def test_ts_glyph_inference_record_declares_roi_and_shas_g1():
    """G1/R1: TS GlyphInferenceRecord must declare roi + inputImageSha256 + cropSha256."""
    text = API_TS.read_text(encoding="utf-8")
    m = re.search(r"export interface GlyphInferenceRecord \{([\s\S]*?)\n\}", text)
    assert m, "GlyphInferenceRecord interface missing"
    block = m.group(1)
    needed = ("roi", "inputImageSha256", "cropSha256")
    absent = [name for name in needed if not re.search(rf"\b{name}\b", block)]
    if absent:
        pytest.xfail(f"G1/R1: TS GlyphInferenceRecord missing {absent} (backend already returns them)")
    for name in needed:
        assert re.search(rf"\b{name}\b", block)


def test_roi_geometry_field_names_are_dual_schemas_g2():
    """G2/R2: GlyphBox uses w/h; ReviewBox uses width/height — gap until normalized."""
    main = MAIN_PY.read_text(encoding="utf-8")
    assert "class GlyphBox" in main and "class ReviewBox" in main
    glyph = main[main.find("class GlyphBox") : main.find("class GlyphBox") + 200]
    review = main[main.find("class ReviewBox") : main.find("class ReviewBox") + 200]
    glyph_wh = ("w:" in glyph or "w :" in glyph) and ("h:" in glyph or "h :" in glyph)
    review_wh = "width" in review and "height" in review
    assert glyph_wh and review_wh
    pytest.xfail("G2/R2: dual ROI schemas (w/h vs width/height) not yet normalized for export")


def test_no_paired_roi_compare_session_on_inference_g3(client):
    """G3/R3: no before/after ROI compare session object on inference/report yet."""
    body = _create_inference(client)
    report = client.get("/api/steles/tang_01_duobao/report").json()
    banned = ("roiCompareSession", "beforeCropSha256", "afterCropSha256", "pairedRoi")
    present = [k for k in banned if k in body or k in report]
    if not present:
        pytest.xfail("G3/R3: paired before/after ROI compare session not implemented")
    assert present


def test_catalog_assessment_run_link_g4(client):
    """G4/R4: assessment payload should expose processing runId or explicit null+reason."""
    response = client.get("/api/catalog/tang_01_duobao/assessment")
    if response.status_code == 404:
        pytest.skip("G4/R4: no assessment payload for sample stele in this worktree")
    assert response.status_code == 200, response.text
    data = response.json()
    has_run = data.get("runId") or data.get("processingRunId")
    if not has_run and not data.get("runLinkUnavailableReason"):
        pytest.xfail(
            "G4/R4: assessment lacks processing runId / runLinkUnavailableReason "
            f"(keys sample={sorted(data.keys())[:20]})"
        )
    assert has_run or data.get("runLinkUnavailableReason")


def test_mechanism_case_ids_are_not_product_stele_ids_g6():
    """G6/R6: mechanism caseIds must not be silently treated as steleIds (no mapping API yet)."""
    for path in MECH_INDEXES:
        if not path.is_file():
            pytest.skip(f"mechanism index missing: {path}")
        index = json.loads(path.read_text(encoding="utf-8"))
        cases = index.get("cases") or []
        assert cases, path
        sample = cases[0]
        case_id = sample.get("caseId") or sample.get("id")
        assert case_id, sample
        pytest.xfail(
            f"G6/R6: no caseId<->steleId mapping API; refusing to equate mechanism "
            f"caseId={case_id!r} with product steleId"
        )


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
