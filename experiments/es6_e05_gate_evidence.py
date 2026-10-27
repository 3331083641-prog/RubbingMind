"""ES-6 / E-05 gate evidence skeleton (eval-sci).

Never auto-closes TASK_BOARD ES-6. Missing keys => blocked_missing_evidence.
gate_verdict never returns 'closed' (anti fake-green).
"""
from __future__ import annotations

from typing import Any, Mapping

REQUIRED_CLOSE_EVIDENCE = (
    "g1_pixel_equal_head",
    "g2_history_untouched",
    "g3_new_batch_policy",
    "g4_no_museum_processing_edit",
    "green_red_ack",
)

OPEN = "open"
BLOCKED = "blocked_missing_evidence"


def missing_close_evidence(evidence: Mapping[str, Any] | None) -> list[str]:
    """Return required keys that are absent or falsy."""
    ev = evidence or {}
    return [k for k in REQUIRED_CLOSE_EVIDENCE if not ev.get(k)]


def gate_verdict(evidence: Mapping[str, Any] | None) -> str:
    """Skeleton verdict: open or blocked_missing_evidence — never closed."""
    if missing_close_evidence(evidence):
        return BLOCKED
    # Even with all keys present, this skeleton refuses to close (needs Green/red).
    # Presence of keys is necessary but not sufficient; stay open until humans ack.
    return OPEN


def assert_board_still_open(status_text: str) -> None:
    """Raise if status looks fake-green closed."""
    closed_markers = ("已完成", "已关闭", "关闭 ES-6", "✅ 完成")
    open_markers = ("仍进行中", "未关", "进行中", "草案")
    if any(m in status_text for m in closed_markers) and not any(
        m in status_text for m in open_markers
    ):
        raise AssertionError(f"ES-6 status looks closed (fake-green risk): {status_text!r}")
