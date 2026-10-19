"""Additive per-batch metadata for the report UI (ARCHITECTURE_DECISIONS R1-3).

Kept outside experiment_registry._entry so it composes with agent/eval-sci's
displayName/heldOut/appliedStatus fields without touching the same lines.
"""
from __future__ import annotations

from collections import Counter

# REPORT_DATA_SPEC §1(a) line 69: default to the newest batch that has images; never the
# same-batch retest. Pinned explicitly so a new batch cannot silently become the default.
DEFAULT_REPORT_BATCH = 'controlled-rubbings-v2-text-2026-10-17'
DEFAULT_REPORT_BASIS = 'REPORT_DATA_SPEC.md §1(a)：默认最新的有图像批次（BVT），禁止默认同批复测批次。'
LEAKAGE_DIRECTORIES = {'2026-10-15'}


def batch_metadata(entry: dict, data: dict) -> dict:
    rows = data.get('rows') or []
    splits = Counter(row['split'] for row in rows if isinstance(row, dict) and row.get('split'))
    reasons = []
    if entry.get('directory') in LEAKAGE_DIRECTORIES:
        status = 'historical-leakage'
        reasons.append(entry.get('historicalWarning') or '历史批次存在先验泄漏，仅作历史记录。')
    elif entry.get('metricsOnly'):
        status = 'metrics-only'
        reasons.append('本批次没有保存图像，只能展示数值。')
    else:
        status = 'valid'
    if not splits:
        reasons.append('本批未划分 development/test。')
    return {
        'splitAvailable': bool(splits),
        'splits': dict(sorted(splits.items())),
        'rowsWithoutSplit': len(rows) - sum(splits.values()),
        'status': status,
        'statusReasons': reasons,
        'defaultForReport': False,
        'defaultForReportBasis': None,
    }


def mark_default(entries: list[dict]) -> list[dict]:
    """Exactly one batch carries defaultForReport=True, or none when no candidate qualifies."""
    for entry in entries:
        entry['defaultForReport'] = False
        entry['defaultForReportBasis'] = None
    chosen = next((e for e in entries if e['id'] == DEFAULT_REPORT_BATCH and e.get('status') == 'valid'), None)
    if chosen:
        chosen['defaultForReport'] = True
        chosen['defaultForReportBasis'] = DEFAULT_REPORT_BASIS
    return entries
