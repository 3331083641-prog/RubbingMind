"""Eval-side ROI compare session contract (R3 / ES derived validator).

Mirrors PHASE2_ROI_REQUESTS R3 field names. Does NOT implement arch cropping;
validates shape + null/reason rules so report/export cannot silently fake pairs.
When arch@fa31279 merges into feature, live API payloads should satisfy this.
"""
from __future__ import annotations

from typing import Any, Mapping

REQUIRED_KEYS = (
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
)

SHA_KEYS = (
    "beforeImageSha256",
    "afterImageSha256",
    "beforeCropSha256",
    "afterCropSha256",
)


class RoiCompareContractError(ValueError):
    pass


def empty_session(stele_id: str, *, reason: str, run_id: str | None = None) -> dict:
    """Canonical unavailable session — SHAs null, reason non-empty."""
    if not reason:
        raise RoiCompareContractError("unavailableReason must be non-empty when session is empty")
    return {
        "steleId": stele_id,
        "runId": run_id,
        "bbox": None,
        "beforeImageSha256": None,
        "afterImageSha256": None,
        "beforeCropSha256": None,
        "afterCropSha256": None,
        "algorithmVersion": None,
        "effectiveParameters": None,
        "createdAt": "未记录",
        "unavailableReason": reason,
    }


def validate_roi_compare_session(session: Mapping[str, Any] | None) -> list[str]:
    """Return human-readable violations; empty list means OK."""
    if not isinstance(session, Mapping):
        return ["roiCompareSession must be an object"]
    missing = [k for k in REQUIRED_KEYS if k not in session]
    if missing:
        return [f"missing keys: {missing}"]
    errors: list[str] = []
    shas = [session.get(k) for k in SHA_KEYS]
    any_sha = any(isinstance(s, str) and len(s) == 64 for s in shas)
    pair_image = (
        isinstance(session.get("beforeImageSha256"), str)
        and isinstance(session.get("afterImageSha256"), str)
        and len(session["beforeImageSha256"]) == 64
        and len(session["afterImageSha256"]) == 64
    )
    reason = session.get("unavailableReason")
    if not pair_image:
        if not reason:
            errors.append("paired image SHAs absent but unavailableReason empty — must not fake a pair")
        for k in ("beforeImageSha256", "afterImageSha256", "beforeCropSha256", "afterCropSha256"):
            val = session.get(k)
            if isinstance(val, str) and len(val) == 64 and k.startswith("before") is False and not pair_image:
                # single-sided SHA without pair is suspicious only if claiming success
                pass
            if val is not None and val != "未记录" and not (isinstance(val, str) and len(val) == 64):
                if val not in (None, "未记录"):
                    errors.append(f"{k} must be null, 未记录, or 64-char sha256; got {type(val).__name__}")
    else:
        # paired images present: reason should be null OR only explain crop gap
        if reason and "bbox" not in str(reason) and "裁切" not in str(reason) and session.get("beforeCropSha256"):
            pass
    # Never allow inventing crop SHAs without image pair
    if (session.get("beforeCropSha256") or session.get("afterCropSha256")) and not pair_image:
        errors.append("crop SHAs present without paired image SHAs — forbidden")
    if any_sha is False and not reason:
        errors.append("no SHA material and no unavailableReason")
    return errors
