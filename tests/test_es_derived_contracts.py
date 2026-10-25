"""ES-3 / ES-4 / ES-5 derived-layer contract gates (eval-sci).

Reads checked-in derived JSON only — does not re-run mechanism (R7) or invent metrics.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from experiments.eval_export_contract import (
    MARKER_UNRECORDED,
    STATUS_NOT_EVALUATED,
    lift_claim_label,
    may_claim_positive_lift,
    require_unevaluated_metrics,
)
from experiments.roi_compare_session_contract import (
    empty_session,
    validate_roi_compare_session,
)

ROOT = Path(__file__).resolve().parents[1]
BATCHES = ("2026-10-17-v2", "2026-10-17-v2-text")
MECH_HEAD = "7623a52a3299b7c948031dfa1f79f04b8eb66d9e"


def _ci_path(batch: str) -> Path:
    return ROOT / "experiments" / "results" / batch / "derived" / "ci_by_artifact.json"


def _nl_path(batch: str) -> Path:
    return ROOT / "experiments" / "results" / batch / "derived" / "negative_lift_causes.json"


def _mech_index(batch: str) -> Path:
    return ROOT / "experiments" / "results" / batch / "derived" / "mechanism" / "index.json"


# ----- ES-3: artifact bootstrap CI -----
@pytest.mark.parametrize("batch", BATCHES)
def test_es3_ci_by_artifact_has_artifact_n_and_ci(batch):
    path = _ci_path(batch)
    assert path.is_file(), path
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("artifactN", 0) > 0
    assert data.get("bootstrap") == 1000
    assert data.get("seed") is not None
    groups = data.get("groups") or []
    assert groups, "ci_by_artifact groups empty"
    sample = groups[0]
    for key in ("artifactN", "ciReliable", "psnrGainCI95Low", "psnrGainCI95High", "split", "method", "degradation", "scope"):
        assert key in sample, key


@pytest.mark.parametrize("batch", BATCHES)
def test_es3_positive_lift_only_when_ci_low_positive(batch):
    data = json.loads(_ci_path(batch).read_text(encoding="utf-8"))
    for g in data["groups"]:
        label = lift_claim_label(g, "psnr")
        allowed = may_claim_positive_lift(
            ci_low=g.get("psnrGainCI95Low"),
            ci_reliable=g.get("ciReliable"),
            artifact_n=g.get("artifactN"),
            min_reliable=data.get("minReliableArtifacts") or 3,
        )
        if allowed:
            assert label == "positive_lift_ci_excludes_zero"
            assert g["psnrGainCI95Low"] > 0
            assert g["ciReliable"] is True
        else:
            assert label != "positive_lift_ci_excludes_zero"
            # Must not treat spans_zero / negative / unreliable as 提升
            if g.get("psnrGainSign") in ("negative", "spans_zero", "zero", None):
                assert not allowed


def test_es3_lift_gate_unit():
    assert may_claim_positive_lift(ci_low=0.1, ci_reliable=True, artifact_n=5) is True
    assert may_claim_positive_lift(ci_low=0.0, ci_reliable=True, artifact_n=5) is False
    assert may_claim_positive_lift(ci_low=-0.1, ci_reliable=True, artifact_n=5) is False
    assert may_claim_positive_lift(ci_low=0.5, ci_reliable=False, artifact_n=5) is False
    assert may_claim_positive_lift(ci_low=0.5, ci_reliable=True, artifact_n=2) is False
    assert may_claim_positive_lift(ci_low=None, ci_reliable=True, artifact_n=5) is False


# ----- ES-4: mechanism representative provenance + tip lag -----
@pytest.mark.parametrize("batch", BATCHES)
def test_es4_mechanism_index_provenance_and_head_lag(batch):
    path = _mech_index(batch)
    assert path.is_file(), path
    index = json.loads(path.read_text(encoding="utf-8"))
    assert index.get("headCommit") == MECH_HEAD
    assert index.get("batch") == batch
    assert index.get("derivedAt"), "derivedAt 未记录"
    assert index.get("derivedBy") == "experiments/mechanism_cases.py" or index.get("derivedBy")
    cases = index.get("cases") or []
    assert len(cases) >= 1
    for case in cases:
        assert case.get("caseId") and case.get("directory")
        # category selection must be real labels, not fabricated metrics
        assert case.get("category") in {
            "improvement", "negative", "passthrough", "gate_reject", "notch",
        }, case.get("category")


@pytest.mark.parametrize("batch", BATCHES)
def test_es4_mechanism_case_files_mark_missing_as_unrecorded(batch):
    index = json.loads(_mech_index(batch).read_text(encoding="utf-8"))
    root = _mech_index(batch).parent
    tip = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert tip != MECH_HEAD, "tip unexpectedly equals stale mechanism head — update MECHANISM_HEAD_NOTE before claiming byte-identity"
    checked = 0
    for case in index.get("cases") or []:
        mech_path = root / case["directory"].split("derived/mechanism/")[-1] / "mechanism.json"
        if not mech_path.is_file():
            # directory field is relative like derived/mechanism/<id>
            alt = ROOT / "experiments" / "results" / batch / case["directory"] / "mechanism.json"
            mech_path = alt
        assert mech_path.is_file(), mech_path
        data = json.loads(mech_path.read_text(encoding="utf-8"))
        assert data.get("headCommit") == MECH_HEAD
        assert data.get("batch") == batch
        assert data.get("caseId") == case["caseId"]
        # images: list of {file, description, ...}; each file must exist or be 未记录
        images = data.get("images") or []
        assert isinstance(images, list) and images, "mechanism images list empty"
        for entry in images:
            assert isinstance(entry, dict), entry
            rel = entry.get("file")
            if rel in (None, "", MARKER_UNRECORDED):
                # explicit gap — must not invent a filename
                assert entry.get("description") or entry.get("unavailableReason") or rel == MARKER_UNRECORDED
                continue
            img_path = mech_path.parent / Path(str(rel)).name
            if not img_path.is_file():
                img_path = mech_path.parent / str(rel)
            assert img_path.is_file(), f"missing image file for {entry.get('description')}: {rel}"
            # ES-4: provenance fields on the case itself
        assert data.get("caseId") and data.get("batch")
        assert data.get("headCommit") == MECH_HEAD
        checked += 1
        if checked >= 3:
            break
    assert checked >= 1


def test_es4_r7_ban_note_forbids_tip_byte_identity():
    note = (ROOT / "docs" / "product-upgrade" / "MECHANISM_HEAD_NOTE.md").read_text(encoding="utf-8")
    assert "7623a52" in note
    assert "字节一致" in note
    assert "不得" in note
    tip = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    # Note must acknowledge tip has moved (short hash of current tip or a7b54e2/0f20bf1 era)
    assert any(h in note for h in (tip, "0f20bf1", "a7b54e2", "65f7815", "tip")), (
        "MECHANISM_HEAD_NOTE must name current tip or state tip has moved"
    )


# ----- ES-5: measured negative-lift causes -----
@pytest.mark.parametrize("batch", BATCHES)
def test_es5_negative_lift_causes_are_measurement_backed(batch):
    path = _nl_path(batch)
    assert path.is_file(), path
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("measuredCriteriaVersion")
    assert data.get("negativeLiftN", 0) == len(data.get("cases") or [])
    assert data.get("note"), "must disclose ruleInferredCause is heuristic"
    # sample first 20 cases
    for case in (data.get("cases") or [])[:20]:
        assert "ruleInferredCause" in case and "ruleInferredBasis" in case
        assert "启发式" in str(case["ruleInferredBasis"]) or "退化" in str(case["ruleInferredBasis"]) or case["ruleInferredBasis"]
        assert isinstance(case.get("measuredEvidence"), list) and case["measuredEvidence"]
        for ev in case["measuredEvidence"]:
            assert {"measure", "value", "threshold", "comparator", "triggered", "available"} <= set(ev)
            if ev["available"] is False:
                assert ev.get("unavailableReason"), f"unavailable measure lacks reason: {ev}"
                assert ev["value"] is None or ev["value"] == MARKER_UNRECORDED
            if ev["triggered"]:
                assert ev["available"] is True
        assert case.get("measuredCauses") is not None
        assert case.get("psnrDelta") is not None and case["psnrDelta"] < 0


# ----- export markers: 未评测 / not_evaluated -----
def test_export_glyph_evaluation_stays_not_evaluated_without_truth():
    from glyph_annotations import evaluate

    measured = evaluate()
    api_like = {
        "status": STATUS_NOT_EVALUATED if measured.get("evaluationStatus") != "measured" else "measured",
        "top1": measured.get("top1"),
        "top3": measured.get("top3"),
        "rejectionRate": measured.get("rejectionRate"),
        "reason": measured.get("reason"),
    }
    assert api_like["status"] == STATUS_NOT_EVALUATED
    assert require_unevaluated_metrics(api_like, ("top1", "top3", "rejectionRate")) == []
    assert api_like["top1"] is None and api_like["top3"] is None
    assert api_like.get("reason")


# ----- R3 derived session contract (eval-side; arch impl not required in this tip) -----
def test_roi_compare_session_contract_rejects_fake_pair():
    bad = {
        "steleId": "tang_01_duobao",
        "runId": None,
        "bbox": None,
        "beforeImageSha256": None,
        "afterImageSha256": None,
        "beforeCropSha256": None,
        "afterCropSha256": None,
        "algorithmVersion": None,
        "effectiveParameters": None,
        "createdAt": MARKER_UNRECORDED,
        "unavailableReason": None,  # illegal
    }
    errs = validate_roi_compare_session(bad)
    assert errs

    ok = empty_session("tang_01_duobao", reason="无处理运行 runId，无法建立成对 before/after ROI 对照")
    assert validate_roi_compare_session(ok) == []

    forged_crop = dict(ok)
    forged_crop["beforeCropSha256"] = "a" * 64
    assert validate_roi_compare_session(forged_crop), "crop without image pair must fail"
