"""Phase2 R6: experiment caseId <-> product steleId mapping.

Mechanism / batch caseIds live in a different id domain from museum steleIds.
Cross-domain ROI or mechanism figures MUST carry an explicit mapping; without it,
UI/report must not claim they depict the same artifact.
"""
from __future__ import annotations

import json
from pathlib import Path

from catalog import BASE, load

MAPPING_PATH = BASE / "data" / "catalog" / "case_stele_mapping.json"


def _seed_entries_from_core_links() -> list[dict]:
    """Optional bootstrap rows from core_sample_links (unreviewed same_work only)."""
    entries = []
    try:
        links = load("core_sample_links.json")
    except Exception:
        return entries
    for row in links or []:
        if not isinstance(row, dict):
            continue
        case_id = row.get("coreSampleId")
        stele_id = row.get("museumSteleId")
        if not case_id:
            continue
        entries.append({
            "caseId": case_id,
            "steleId": stele_id,
            "relationship": row.get("relationship") or "same_work",
            "reviewStatus": "unreviewed",
            "note": row.get("note") or "来自 core_sample_links.json；未人工复核不得宣称同一馆藏拓本。",
            "source": "data/catalog/core_sample_links.json",
        })
    return entries


def load_mapping() -> dict:
    if MAPPING_PATH.is_file():
        try:
            data = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return {
                "available": False,
                "source": str(MAPPING_PATH.relative_to(BASE)).replace("\\", "/"),
                "version": None,
                "status": None,
                "entries": [],
                "mappingError": f"case_stele_mapping.json 无法解析：{type(exc).__name__}: {exc}",
            }
        entries = [e for e in (data.get("entries") or []) if isinstance(e, dict) and e.get("caseId")]
        return {
            "available": True,
            "source": "data/catalog/case_stele_mapping.json",
            "version": data.get("version"),
            "status": data.get("status"),
            "entries": entries,
            "mappingError": None,
            "note": data.get("note"),
        }
    # File absent: expose core_sample_links as provisional, still not a silent equate.
    seeded = _seed_entries_from_core_links()
    return {
        "available": bool(seeded),
        "source": "data/catalog/core_sample_links.json" if seeded else None,
        "version": None,
        "status": "provisional-from-core-sample-links",
        "entries": seeded,
        "mappingError": None,
        "note": "尚无 case_stele_mapping.json；暂以 core_sample_links 作 provisional 对照，禁止无 mapping 并排宣称同一文物。",
    }


def resolve_case(case_id: str) -> dict:
    mapping = load_mapping()
    entry = next((e for e in mapping["entries"] if e.get("caseId") == case_id), None)
    if entry is None:
        return {
            "caseId": case_id,
            "steleId": None,
            "mapped": False,
            "sameArtifactClaimAllowed": False,
            "reviewStatus": None,
            "relationship": None,
            "unavailableReason": (
                f"无 caseId={case_id!r} 的对照条目；禁止将机制/实验 caseId 静默当作产品 steleId"
            ),
            "mappingSource": mapping.get("source"),
        }
    stele_id = entry.get("steleId")
    reviewed = entry.get("reviewStatus") == "human_reviewed"
    mapped = bool(stele_id)
    return {
        "caseId": case_id,
        "steleId": stele_id,
        "mapped": mapped,
        "sameArtifactClaimAllowed": bool(mapped and reviewed),
        "reviewStatus": entry.get("reviewStatus"),
        "relationship": entry.get("relationship"),
        "note": entry.get("note"),
        "unavailableReason": None if mapped else (
            f"caseId={case_id!r} 有条目但 steleId 为空（demo_only / 未核实），禁止并排同一文物声明"
        ),
        "mappingSource": entry.get("source") or mapping.get("source"),
        "claimBlockedReason": None if (mapped and reviewed) else (
            "对照未标记 human_reviewed，或 steleId 为空；报告/UI 不得宣称同一文物"
        ),
    }


def mapping_overview() -> dict:
    mapping = load_mapping()
    return {
        **mapping,
        "policy": {
            "silentEquateForbidden": True,
            "sameArtifactClaimRequires": ["mapped steleId", "reviewStatus=human_reviewed"],
            "phase2": "R6/G6",
        },
    }


def assert_same_artifact_claim(case_id: str, stele_id: str) -> dict:
    """Gate for ROI/report mix: returns ok/denied payload (never raises for API use)."""
    resolved = resolve_case(case_id)
    if not resolved["mapped"]:
        return {"allowed": False, "reason": resolved["unavailableReason"], "resolved": resolved}
    if resolved["steleId"] != stele_id:
        return {
            "allowed": False,
            "reason": (
                f"caseId={case_id!r} 映射到 steleId={resolved['steleId']!r}，"
                f"与请求的 steleId={stele_id!r} 不一致"
            ),
            "resolved": resolved,
        }
    if not resolved["sameArtifactClaimAllowed"]:
        return {
            "allowed": False,
            "reason": resolved.get("claimBlockedReason") or "对照未人工复核",
            "resolved": resolved,
        }
    return {"allowed": True, "reason": None, "resolved": resolved}
