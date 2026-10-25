"""Phase2 R2: single ROI geometry normalization schema.

Glyph inference uses glyph-bbox {x,y,w,h}.
Catalog review / glyph annotations use review-box {x,y,width,height}.
Export and compare paths MUST go through normalize_roi / to_review_box —
silent mixing of field names is forbidden.
"""
from __future__ import annotations

from typing import Any, Mapping

SCHEMA_GLYPH = "glyph-bbox"
SCHEMA_REVIEW = "review-box"
CANONICAL = SCHEMA_GLYPH  # Phase2 export uses glyph-bbox only


class RoiGeometryError(ValueError):
    """Ambiguous or invalid ROI geometry."""


def detect_schema(box: Mapping[str, Any] | None) -> str | None:
    if not isinstance(box, Mapping):
        return None
    has_wh = "w" in box and "h" in box
    has_width = "width" in box and "height" in box
    if has_wh and has_width:
        # Ambiguous naming — require explicit source_schema.
        return None
    if has_wh:
        return SCHEMA_GLYPH
    if has_width:
        return SCHEMA_REVIEW
    return None


def normalize_roi(box: Mapping[str, Any] | None, *, source_schema: str | None = None) -> dict:
    """Return canonical glyph-bbox dict with schema + sourceSchema markers."""
    if not isinstance(box, Mapping):
        raise RoiGeometryError("ROI 必须是对象")
    schema = source_schema or detect_schema(box)
    if schema is None:
        keys = sorted(box.keys())
        raise RoiGeometryError(
            "无法判定 ROI schema（禁止静默混用 w/h 与 width/height）；"
            f"keys={keys}；请显式传入 source_schema={SCHEMA_GLYPH!r} 或 {SCHEMA_REVIEW!r}"
        )
    if schema not in (SCHEMA_GLYPH, SCHEMA_REVIEW):
        raise RoiGeometryError(f"未知 ROI schema: {schema!r}")
    try:
        x = int(box["x"])
        y = int(box["y"])
        if schema == SCHEMA_GLYPH:
            w = int(box["w"])
            h = int(box["h"])
        else:
            w = int(box["width"])
            h = int(box["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RoiGeometryError("ROI 坐标无效") from exc
    if min(x, y, w, h) < 0:
        raise RoiGeometryError("ROI 坐标不能为负")
    return {
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "schema": CANONICAL,
        "sourceSchema": schema,
    }


def to_review_box(normalized: Mapping[str, Any]) -> dict:
    """Convert a normalized glyph-bbox dict to review-box field names."""
    base = normalize_roi(normalized, source_schema=normalized.get("schema") or SCHEMA_GLYPH)
    return {
        "x": base["x"],
        "y": base["y"],
        "width": base["w"],
        "height": base["h"],
        "schema": SCHEMA_REVIEW,
        "sourceSchema": base["sourceSchema"],
    }


def export_geometry(box: Mapping[str, Any] | None, *, source_schema: str | None = None) -> dict:
    """Phase2 export helper: always one geometry field set (canonical glyph-bbox)."""
    return normalize_roi(box, source_schema=source_schema)
