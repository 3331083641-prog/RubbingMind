"""ES-3 bootstrap dry-run + ES-6 E-05 gate draft skeletons (eval-sci).

No derived rewrite; no mechanism re-run; ES-6 must stay open (no fake-green close).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from experiments.ci_bootstrap_dry_run import dry_run
from experiments.es6_e05_gate_evidence import (
    BLOCKED,
    OPEN,
    REQUIRED_CLOSE_EVIDENCE,
    assert_board_still_open,
    gate_verdict,
    missing_close_evidence,
)
from experiments.eval_export_contract import (
    MARKER_UNEVALUATED,
    STATUS_NOT_EVALUATED,
    TOPK_UNEVALUATED_KEYS,
    forbid_numeric_topk_without_ground_truth,
    recognition_metrics_unevaluated_payload,
)

ROOT = Path(__file__).resolve().parents[1]


def test_es3_bootstrap_dry_run_readonly_ok_with_open_findings():
    report = dry_run()
    assert report["wroteDerived"] is False
    assert report["recomputedBootstrap"] is False
    assert report["ok"] is True
    assert report["hasOpenFindings"] is True
    for batch in report["batches"]:
        assert batch["ok"] is True
        assert batch["wroteDerived"] is False
        assert batch["bootstrap"] == 1000
        assert batch["seed"] == 20261019
        assert batch["artifactN"] == 14
        assert batch["groupCount"] == 324
        assert batch["sourceResultsSha256Matches"] is True
        # appliedStatus SHA drift is an open finding — do not rewrite derived
        assert batch["appliedStatusSha256Matches"] is False
        assert any("appliedStatusSha256" in f for f in batch["openFindings"])
        assert batch["claimCounts"]["positive_lift_ci_excludes_zero"] == 35
        assert batch["claimCounts"][MARKER_UNEVALUATED] in (92, 98)


def test_es3_bootstrap_dry_run_doc_exists():
    path = ROOT / "docs" / "product-upgrade" / "ES3_BOOTSTRAP_DRY_RUN.md"
    text = path.read_text(encoding="utf-8")
    assert "ci_bootstrap_dry_run" in text
    assert "R7" in text and "A24" in text
    assert "derived" in text


def test_es6_e05_gate_draft_doc_still_open():
    path = ROOT / "docs" / "product-upgrade" / "ES6_E05_GATE_DRAFT.md"
    text = path.read_text(encoding="utf-8")
    assert "ES-6" in text
    assert "E-05" in text
    assert "museum_processing" in text
    assert ("仍进行中" in text) or ("未关" in text)
    assert "草案" in text
    assert "G1" in text and "G5" in text
    assert "缺证据" in text or "blocked_missing_evidence" in text
    assert "反例" in text
    assert "不关闭" in text or "未关" in text
    assert "伪绿" in text
    assert_board_still_open(text)
    # Must not claim E-05 / ES-6 closed
    assert "ES-6 已关闭" not in text
    assert "E-05 已关闭" not in text


def test_es6_e05_g1_engine_criterion_holds_but_board_open():
    """G1 skeleton: HEAD notch NA path is pixel-equal copy; does NOT close ES-6."""
    import cv2
    from algorithm_engine import RubbingAlgorithmEngine

    noise = np.random.default_rng(0).normal(150, 80, (128, 128)).astype(np.float32)
    gray = np.clip(cv2.GaussianBlur(noise, (0, 0), 1.5) * 1.6 - 90, 0, 255).astype(np.uint8)
    out, _, details = RubbingAlgorithmEngine().apply_frequency_domain_filter(
        gray, d0=48, filter_type="notch", return_details=True
    )
    assert details.get("notchApplied") is False
    assert details.get("passthrough") is True
    assert out is not gray
    assert np.array_equal(out, gray)
    assert int(np.count_nonzero(out.astype(np.int16) - gray.astype(np.int16))) == 0
    draft = (ROOT / "docs" / "product-upgrade" / "ES6_E05_GATE_DRAFT.md").read_text(
        encoding="utf-8"
    )
    assert ("未关" in draft) or ("仍进行中" in draft)


def test_es6_e05_g1_prefix_truncation_is_counterexample():
    """Pre-fix FFT round-trip truncation must NOT satisfy G1 pixel equality."""
    gray = np.random.default_rng(2).integers(0, 256, (64, 64), dtype=np.uint8)
    # Historical bug path: all-ones mask FFT round trip + astype(uint8)
    back = np.real(
        np.fft.ifft2(np.fft.ifftshift(np.fft.fftshift(np.fft.fft2(gray.astype(np.float32)))))
    )
    truncated = np.clip(back, 0, 255).astype(np.uint8)
    assert not np.array_equal(truncated, gray)
    diff = truncated.astype(np.int16) - gray.astype(np.int16)
    nonzero = diff[diff != 0]
    assert nonzero.size > 0
    # Typical E-05 signature: only -1 among non-zero diffs
    assert set(np.unique(nonzero).tolist()).issubset({-1})


def test_es6_missing_evidence_must_not_pass():
    assert missing_close_evidence({}) == list(REQUIRED_CLOSE_EVIDENCE)
    assert gate_verdict({}) == BLOCKED
    partial = {k: True for k in REQUIRED_CLOSE_EVIDENCE[:-1]}
    assert gate_verdict(partial) == BLOCKED
    assert "green_red_ack" in missing_close_evidence(partial)
    # Even a fully keyed dict stays open (skeleton never auto-closes)
    full = {k: True for k in REQUIRED_CLOSE_EVIDENCE}
    assert gate_verdict(full) == OPEN
    assert gate_verdict(full) != "closed"


def test_es6_task_board_external_still_in_progress_readonly():
    """Read-only: external TASK_BOARD ES-6 row must still say 进行中 (no fake-green)."""
    board = Path(r"D:\RubbingMind\docs\product-upgrade\TASK_BOARD.md")
    if not board.is_file():
        return  # soft-skip if host path absent
    text = board.read_text(encoding="utf-8")
    rows = [ln for ln in text.splitlines() if ln.startswith("| ES-6 |")]
    assert rows, "TASK_BOARD missing ES-6 row"
    row = rows[0]
    assert "进行中" in row
    assert "已完成" not in row


def test_a24_topk_unevaluated_companion_still_open():
    payload = recognition_metrics_unevaluated_payload()
    assert payload["evaluationStatus"] == STATUS_NOT_EVALUATED
    for key in TOPK_UNEVALUATED_KEYS:
        assert payload[key] == MARKER_UNEVALUATED
    assert forbid_numeric_topk_without_ground_truth(payload) == []
    bad = dict(payload)
    bad["top1Accuracy"] = 0.9
    assert "top1Accuracy" in forbid_numeric_topk_without_ground_truth(bad)
