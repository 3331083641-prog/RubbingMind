"""Phase2 R5: attach algorithmVersion + effectiveParameters onto inference payloads.

When runId is present, join ProcessingRun (recorded or derived-on-read).
When runId is absent, expose nulls with an explicit unavailable reason.
Never invent parameters.
"""
from __future__ import annotations

from typing import Any


REASON_NO_RUN = "inference.runId 为空（常见于 original 图推演），无法 join ProcessingRun.effectiveParameters"
REASON_RUN_MISSING = "inference.runId 非空但 ProcessingRun 不存在或不属于该碑刻"
REASON_PARAMS_UNAVAILABLE = "关联运行存在，但 effectiveParameters 不可用"


def enrich_inference_traceability(record: dict, *, stele_id: str | None = None) -> dict:
    """Return a shallow-copied inference dict with R5 traceability fields."""
    out = dict(record)
    sid = stele_id or out.get("steleId")
    run_id = out.get("runId")
    if not run_id:
        out.setdefault("algorithmVersion", None)
        out.setdefault("effectiveParameters", None)
        out.setdefault("effectiveParametersSource", None)
        out["effectiveParametersUnavailableReason"] = REASON_NO_RUN
        return out

    from museum_processing import read_run

    run = read_run(sid, run_id) if sid else None
    if run is None:
        out["algorithmVersion"] = None
        out["effectiveParameters"] = None
        out["effectiveParametersSource"] = None
        out["effectiveParametersUnavailableReason"] = REASON_RUN_MISSING
        return out

    out["algorithmVersion"] = run.get("algorithmVersion")
    params = run.get("effectiveParameters")
    source = run.get("effectiveParametersSource")
    reason = run.get("effectiveParametersUnavailableReason")
    out["effectiveParameters"] = params
    out["effectiveParametersSource"] = source
    if params is None:
        out["effectiveParametersUnavailableReason"] = reason or REASON_PARAMS_UNAVAILABLE
    else:
        out["effectiveParametersUnavailableReason"] = None
    return out


def enrich_many(records: list[dict], *, stele_id: str | None = None) -> list[dict]:
    return [enrich_inference_traceability(r, stele_id=stele_id) for r in records]
