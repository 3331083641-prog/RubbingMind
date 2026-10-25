"""Phase2 R3: paired before/after ROI compare session (original vs restored).

Never invent SHA values. Missing images or missing run → explicit unavailableReason.
Crop SHAs require a bbox; image-level SHAs come from the ProcessingRun envelope.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from roi_geometry import RoiGeometryError, normalize_roi


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_session(
    stele_id: str,
    *,
    run_id: str | None = None,
    bbox: dict | None = None,
    reason: str,
) -> dict:
    return {
        "steleId": stele_id,
        "runId": run_id,
        "bbox": bbox,
        "beforeImageSha256": None,
        "afterImageSha256": None,
        "beforeCropSha256": None,
        "afterCropSha256": None,
        "algorithmVersion": None,
        "effectiveParameters": None,
        "createdAt": _now(),
        "unavailableReason": reason,
    }


def build_roi_compare_session(
    stele_id: str,
    run_id: str | None = None,
    bbox: Mapping[str, Any] | None = None,
    *,
    source_schema: str | None = None,
) -> dict:
    """Build a first-class paired ROI compare session for one stele/run/bbox."""
    from museum_processing import read_run

    norm_bbox = None
    if bbox is not None:
        try:
            norm_bbox = normalize_roi(bbox, source_schema=source_schema)
            # Drop markers for the wire session bbox (keep canonical x,y,w,h only + schema tag)
            norm_bbox = {
                "x": norm_bbox["x"],
                "y": norm_bbox["y"],
                "w": norm_bbox["w"],
                "h": norm_bbox["h"],
                "schema": norm_bbox["schema"],
            }
        except RoiGeometryError as exc:
            return _empty_session(stele_id, run_id=run_id, bbox=None, reason=f"bbox 无效：{exc}")

    if not run_id:
        return _empty_session(
            stele_id,
            run_id=None,
            bbox=norm_bbox,
            reason="无处理运行 runId，无法建立成对 before/after ROI 对照；禁止用单图字段冒充成对",
        )

    run = read_run(stele_id, run_id)
    if run is None:
        return _empty_session(
            stele_id,
            run_id=run_id,
            bbox=norm_bbox,
            reason=f"处理运行不存在或不属于该碑刻：runId={run_id}",
        )

    hashes = run.get("outputSha256") or {}
    if not isinstance(hashes, dict):
        hashes = {}
    before = hashes.get("original") or run.get("inputImageSha256")
    after = hashes.get("restored")
    if not before or not after or before == "未记录":
        return {
            **_empty_session(
                stele_id,
                run_id=run_id,
                bbox=norm_bbox,
                reason="运行未记录成对 original/restored 图像 SHA，无法建立 before/after 对照",
            ),
            "algorithmVersion": run.get("algorithmVersion"),
            "effectiveParameters": run.get("effectiveParameters"),
        }

    session = {
        "steleId": stele_id,
        "runId": run_id,
        "bbox": norm_bbox,
        "beforeImageSha256": before,
        "afterImageSha256": after,
        "beforeCropSha256": None,
        "afterCropSha256": None,
        "algorithmVersion": run.get("algorithmVersion"),
        "effectiveParameters": run.get("effectiveParameters"),
        "createdAt": _now(),
        "unavailableReason": None,
    }

    if norm_bbox is None:
        session["unavailableReason"] = (
            "已绑定成对图像 SHA，但未提供 bbox；裁切 SHA 需调用 "
            "GET /api/steles/{id}/roi-compare 并传入 bbox"
        )
        return session

    # Optional crop SHAs when both role images are on disk and verify.
    crop_reason = _try_fill_crop_shas(stele_id, run_id, run, norm_bbox, session)
    if crop_reason and session["beforeCropSha256"] is None:
        # Keep image-level pair; expose crop gap explicitly without clearing image SHAs.
        session["cropUnavailableReason"] = crop_reason
    return session


def _try_fill_crop_shas(stele_id, run_id, run, bbox, session) -> str | None:
    """Best-effort crop SHA from original/restored files; never invent digests."""
    import hashlib
    from pathlib import Path

    try:
        from museum_processing import results_root
        from PIL import Image
    except Exception as exc:  # pragma: no cover
        return f"无法加载裁切依赖：{type(exc).__name__}"

    images = run.get("outputImages") or {}
    roles = {
        "before": images.get("original"),
        "after": images.get("restored"),
    }
    root = results_root() / stele_id / run_id
    digests = {}
    for key, name in roles.items():
        if not name:
            return f"运行缺少 {key} 角色图像文件名，无法计算裁切 SHA"
        path = root / name if not Path(str(name)).is_absolute() else Path(name)
        # outputImages may store relative names or API urls — try basename under run dir
        if not path.is_file():
            path = root / Path(str(name)).name
        if not path.is_file():
            return f"本地缺少 {key} 图像文件，无法计算裁切 SHA"
        expected = session["beforeImageSha256"] if key == "before" else session["afterImageSha256"]
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if expected and actual != expected:
            return f"{key} 图像 SHA 与运行记录不一致，拒绝计算裁切 SHA"
        try:
            with Image.open(path) as im:
                im = im.convert("RGB")
                x, y, w, h = bbox["x"], bbox["y"], bbox["w"], bbox["h"]
                if x + w > im.width or y + h > im.height:
                    return f"bbox 超出 {key} 图像范围"
                crop = im.crop((x, y, x + w, y + h))
                import io
                buf = io.BytesIO()
                crop.save(buf, format="PNG")
                digests[key] = hashlib.sha256(buf.getvalue()).hexdigest()
        except Exception as exc:
            return f"裁切 {key} 失败：{type(exc).__name__}"
    session["beforeCropSha256"] = digests["before"]
    session["afterCropSha256"] = digests["after"]
    return None


def report_roi_compare_stub(stele_id: str, selected_run: dict | None) -> dict:
    """Attachable report field: image-level pair when run exists; never fake crop SHAs."""
    run_id = (selected_run or {}).get("runId")
    return build_roi_compare_session(stele_id, run_id, bbox=None)
