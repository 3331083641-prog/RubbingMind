"""Eval-side export markers and lift-claim gates (ES-3 / export contract).

Does not invent metrics. Missing measurements must surface as 未记录 / 未评测 /
not_evaluated rather than numeric placeholders.
"""
from __future__ import annotations

from typing import Any, Mapping

MARKER_UNRECORDED = "未记录"
MARKER_UNEVALUATED = "未评测"
STATUS_NOT_EVALUATED = "not_evaluated"


def may_claim_positive_lift(
    *,
    ci_low: float | None,
    ci_reliable: bool | None,
    artifact_n: int | None = None,
    min_reliable: int = 3,
) -> bool:
    """ES-3 / SPEC §0.3: only claim "提升" when bootstrap CI lower bound > 0 and reliable."""
    if ci_low is None:
        return False
    if ci_reliable is False:
        return False
    if artifact_n is not None and artifact_n < min_reliable:
        return False
    try:
        return float(ci_low) > 0.0
    except (TypeError, ValueError):
        return False


def lift_claim_label(group: Mapping[str, Any], metric: str = "psnr") -> str:
    """Return an explicit claim label; never invent a positive lift."""
    low = group.get(f"{metric}GainCI95Low")
    reliable = group.get("ciReliable")
    n = group.get("artifactN")
    if may_claim_positive_lift(ci_low=low, ci_reliable=reliable, artifact_n=n):
        return "positive_lift_ci_excludes_zero"
    if low is None or group.get(f"{metric}GainValueN") in (0, None):
        return MARKER_UNEVALUATED
    return "no_positive_lift_claim"


def mark_missing(value: Any, *, reason: str | None = None) -> Any:
    """Replace None with 未记录; keep explicit reasons beside null metrics."""
    if value is None:
        return MARKER_UNRECORDED if not reason else {"value": MARKER_UNRECORDED, "reason": reason}
    return value


def require_unevaluated_metrics(payload: Mapping[str, Any], metric_keys: tuple[str, ...]) -> list[str]:
    """Return list of violations where numeric metrics appear under not_evaluated."""
    status = payload.get("status") or payload.get("evaluationStatus")
    if status not in (STATUS_NOT_EVALUATED, "unassessed", MARKER_UNEVALUATED):
        return []
    bad = []
    for key in metric_keys:
        val = payload.get(key)
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            bad.append(key)
    return bad


def summarize_lift_claims(ci_payload: Mapping[str, Any], metric: str = "psnr") -> dict[str, int]:
    """ES-3: count claim labels over ci_by_artifact groups (no recomputation)."""
    counts: dict[str, int] = {}
    for group in ci_payload.get("groups") or []:
        label = lift_claim_label(group, metric)
        counts[label] = counts.get(label, 0) + 1
    return counts


def negative_lift_display(case: Mapping[str, Any]) -> dict[str, Any]:
    """ES-5口径: measuredCauses primary; rule-inferred only as secondary labelled column."""
    basis = case.get("ruleInferredBasis") or "规则推断（按退化类型）"
    return {
        "primaryMeasuredCauses": list(case.get("measuredCauses") or []),
        "measuredEvidence": list(case.get("measuredEvidence") or []),
        "secondaryRuleInferred": {
            "cause": case.get("ruleInferredCause"),
            "basis": basis,
            "displayLabel": f"旧规则推断 · {basis}",
        },
        "psnrDelta": case.get("psnrDelta"),
        "forbidden": "不得把 ruleInferredCause 写成测量结论",
    }


def annotate_ci_lift_claims(ci_payload: Mapping[str, Any], metric: str = "psnr") -> dict[str, Any]:
    """ES-3: copy groups with liftClaimLabel + top-level liftClaimSummary (no bootstrap recompute)."""
    annotated = []
    for group in ci_payload.get("groups") or []:
        row = dict(group)
        row["liftClaimLabel"] = lift_claim_label(group, metric)
        annotated.append(row)
    out = dict(ci_payload)
    out["groups"] = annotated
    out["liftClaimSummary"] = summarize_lift_claims({"groups": annotated}, metric)
    out["liftClaimRule"] = (
        "only claim lift when CI lower bound > 0 and ciReliable and artifactN>=minReliable"
    )
    return out

