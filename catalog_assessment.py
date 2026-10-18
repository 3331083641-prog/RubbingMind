"""Read-only access to the 28 archived assessments. Paths cannot be chosen by the caller."""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from catalog import BASE, load

ASSESS = BASE / 'data/catalog/assessments'
REVIEWS = BASE / 'data/runtime/condition-reviews'
_REVIEW_LOCK = threading.Lock()
_LOCAL_HOSTS = {'127.0.0.1', '::1', 'localhost', 'testclient'}
ID_RE = re.compile(r'^[a-z][a-z0-9_]*$')
DAMAGE_TYPES = {
    '拓纸破损', '扫描模糊', '墨色不均', '字迹漫漶', '残笔', '缺字',
    '裱边或接缝', '石花纹理', '无法判断',
}
SUGGESTED_CONDITIONS = {'轻度影像损伤', '中度影像损伤', '重度影像损伤', '严重漫漶', '无法判断'}


def known_ids():
    return {row['id'] for row in load('steles28.json')}


def _read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_assessment(stele_id: str):
    if not isinstance(stele_id, str) or not ID_RE.fullmatch(stele_id) or stele_id not in known_ids():
        return None
    path = ASSESS / f'{stele_id}.json'
    if not path.is_file():
        return None
    data = _read_json(path)
    if data.get('steleId') != stele_id:
        return None
    return data


def _sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _checked_file(stele_id: str, folder: str, recorded_relative: str | None, recorded_sha: str | None):
    relative = f'data/catalog/assessments/{folder}/{stele_id}.png'
    if recorded_relative != relative:
        return None
    root = (ASSESS / folder).resolve()
    path = (BASE / relative).resolve()
    if path.parent != root or path.name != f'{stele_id}.png' or not path.is_file():
        return None
    digest = _sha(path)
    if recorded_sha and digest != recorded_sha:
        raise ValueError('评估影像SHA-256不匹配')
    return path


def asset_path(stele_id: str, kind: str):
    data = load_assessment(stele_id)
    if data is None or kind not in {'input-roi', 'output'}:
        return None
    if kind == 'output':
        return _checked_file(stele_id, 'outputs', data.get('archivedOutput'), data.get('outputImageSha256'))
    return _checked_file(stele_id, 'inputs', data.get('archivedInput'), data.get('inputImageSha256'))


def _source_public_url(data):
    source = str(data.get('sourceImage') or '')
    prefix = 'apps/web/public/'
    if not source.startswith(prefix):
        return None
    path = (BASE / source).resolve()
    public = (BASE / 'apps/web/public').resolve()
    if public not in path.parents or not path.is_file():
        return None
    if data.get('sourceImageSha256') and _sha(path) != data['sourceImageSha256']:
        raise ValueError('阅读图SHA-256不匹配')
    return '/' + path.relative_to(public).as_posix()


def review_allowed(host: str | None, token: str | None) -> bool:
    """Local single-user writes are allowed. Any other host needs an explicit token."""
    if (host or '') in _LOCAL_HOSTS:
        return True
    expected = os.environ.get('RUBBINGMIND_REVIEW_TOKEN')
    return bool(expected) and token == expected


def review_history(stele_id: str):
    items = []
    legacy = REVIEWS / f'{stele_id}.json'
    if legacy.is_file():
        data = _read_json(legacy)
        if data.get('steleId') == stele_id:
            items.append(data)
    path = REVIEWS / f'{stele_id}.jsonl'
    if path.is_file():
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            if data.get('steleId') == stele_id:
                items.append(data)
    return items


def _review(stele_id: str):
    history = review_history(stele_id)
    return history[-1] if history else None


def _region(stele_id: str):
    path = ASSESS / 'regions' / f'{stele_id}.json'
    if not path.is_file():
        return None
    data = _read_json(path)
    return data if data.get('steleId') == stele_id else None


def _authorship(stele_id: str):
    path = BASE / 'data/catalog/authorship-verification' / f'{stele_id}.json'
    if not path.is_file():
        return None
    data = _read_json(path)
    if data.get('steleId') != stele_id:
        return None
    return {
        'verificationStatus': data.get('verificationStatus'),
        'roles': {
            key: data.get(key) for key in (
                'inscriptionAuthor', 'calligrapher', 'titleCalligrapher', 'engraver', 'steleSubject', 'characterCompilation',
            )
        },
        'evidence': data.get('evidence') or [],
        'conflicts': data.get('conflicts') or [],
        'notes': data.get('notes') or [],
        'reviewedAt': data.get('reviewedAt'),
    }


def public_record(stele_id: str):
    data = load_assessment(stele_id)
    if data is None:
        return None
    gate = data.get('fidelityGate') or {}
    unchanged = gate.get('meanAbsoluteChange') == 0
    review = _review(stele_id)
    history = review_history(stele_id)
    source_url = _source_public_url(data)
    region = _region(stele_id)
    return {
        'steleId': data['steleId'],
        'title': data.get('title'),
        'runId': data.get('runId'),
        'algorithmVersion': data.get('algorithmVersion'),
        'parameters': data.get('parameters'),
        'processingTimeMs': data.get('processingTimeMs'),
        'restorationScope': data.get('restorationScope'),
        'cropBox': data.get('cropBox'),
        'imageDimensions': data.get('imageDimensions'),
        'partialResultIsNotFullFrame': data.get('partialResultIsNotFullFrame'),
        'coverage': data.get('coverage'),
        'analysisScope': data.get('analysisScope'),
        'sourceImage': data.get('sourceImage'),
        'sourcePublicUrl': source_url,
        'sourceImageSha256': data.get('sourceImageSha256'),
        'inputImageSha256': data.get('inputImageSha256'),
        'outputImageSha256': data.get('outputImageSha256'),
        'inputRoiUrl': f'/api/catalog/{stele_id}/assessment/assets/input-roi',
        'outputUrl': f'/api/catalog/{stele_id}/assessment/assets/output',
        'fidelityGate': gate,
        'adaptiveDecisions': data.get('adaptiveDecisions'),
        'assessmentStatus': data.get('assessmentStatus'),
        'imageCondition': data.get('imageCondition'),
        'gradeRule': data.get('gradeRule'),
        'gradeReasons': data.get('gradeReasons'),
        'imageConditionReviewStatus': '已保存复核意见，尚未作为正式鉴定' if review else '自动初筛，待人工复核',
        'humanReview': review,
        'reviewHistory': history,
        'expertReview': False,
        'regionAnalysis': region,
        'regionOverlays': _overlays(region, (data.get('imageDimensions') or {}).get('readable')),
        'unchanged': unchanged,
        'unchangedNote': '算法判定无需增强' if unchanged else None,
        'psnr': None,
        'ssim': None,
        'evaluationStatus': '未评测',
        'physicalStoneWeathering': '无可靠原石证据，不评定',
        'physicalWeatheringEvidence': None,
        'authorship': _authorship(stele_id),
        'limitations': [
            '输出是阅读图中心 512 像素局部，不是全幅修复。',
            '没有配对真值，不计算 PSNR 或 SSIM。',
            '全幅对比度和拉普拉斯方差只是扫描影像初筛，不是逐字残泐鉴定。',
            '原石风化没有原石影像或保护记录时不评定。',
        ],
    }


def _analysis_geometry(width: int, height: int, long_side: int = 900):
    longest = max(width, height)
    if longest <= long_side:
        return width, height, 1.0
    ratio = long_side / longest
    return max(1, int(round(width * ratio))), max(1, int(round(height * ratio))), ratio


def _overlays(region, readable):
    """Map the stored 3×3 sample back onto the readable image. Metrics stay measurements."""
    if not region or not readable or len(readable) != 2:
        return []
    width, height = int(readable[0]), int(readable[1])
    view_w, view_h, ratio = _analysis_geometry(width, height, int(region.get('capture', {}).get('analysisLongSide') or 900))
    margin = max(4, int(round(min(view_w, view_h) * float((region.get('mountingAndScan') or {}).get('borderFraction') or 0.08))))
    inner_w = max(3, view_w - 2 * margin)
    inner_h = max(3, view_h - 2 * margin)
    cell_w = inner_w // 3
    cell_h = inner_h // 3
    fading = {(item.get('row'), item.get('col')) for item in region.get('suspectedLocalFading') or []}
    texture = {(item.get('row'), item.get('col')) for item in region.get('suspectedNonTextTexture') or []}
    metrics = {(item.get('row'), item.get('col')): item for item in region.get('textCells') or []}
    overlays = []
    for row in range(3):
        for col in range(3):
            x = margin + col * cell_w
            y = margin + row * cell_h
            box_w = cell_w if col < 2 else inner_w - 2 * cell_w
            box_h = cell_h if row < 2 else inner_h - 2 * cell_h
            kind = '正文抽样'
            reason = '3×3 正文网格的自动抽样。颜色只准备表达测量值，这里先给出分区，不表示已确认的风化。'
            if (row, col) in fading:
                kind = '算法疑似局部变淡'
                reason = '该格对比度低于正文格中位数的 55%。这是算法疑似，不是缺字或风化鉴定。'
            elif (row, col) in texture:
                kind = '算法疑似非文字纹理'
                reason = '墨迹比例低且局部高频较强，可能是纸纹或石花。不能当成原石风化。'
            cell = metrics.get((row, col), {})
            origin_x = min(width - 1, max(0, int(round(x / ratio))))
            origin_y = min(height - 1, max(0, int(round(y / ratio))))
            overlays.append({
                'id': f'cell-{row}-{col}',
                'kind': kind,
                'reason': reason,
                'confirmed': False,
                'row': row,
                'col': col,
                'metrics': {
                    'contrastStd': cell.get('contrastStd'),
                    'laplacianVariance': cell.get('laplacianVariance'),
                    'inkFraction': cell.get('inkFraction'),
                },
                'box': {
                    'x': origin_x,
                    'y': origin_y,
                    'width': min(width - origin_x, max(1, int(round(box_w / ratio)))),
                    'height': min(height - origin_y, max(1, int(round(box_h / ratio)))),
                    'space': 'readable native pixels',
                },
            })
    return overlays


def _checked_source(data: dict) -> Path:
    source = str(data.get('sourceImage') or '')
    path = (BASE / source).resolve()
    root = BASE.resolve()
    if root not in path.parents or not path.is_file():
        raise ValueError('阅读图路径无效')
    if data.get('sourceImageSha256') and _sha(path) != data['sourceImageSha256']:
        raise ValueError('阅读图SHA-256不匹配')
    return path


def region_crop(stele_id: str, x: int, y: int, width: int, height: int):
    data = load_assessment(stele_id)
    if data is None:
        return None
    readable = (data.get('imageDimensions') or {}).get('readable') or [0, 0]
    frame_w, frame_h = int(readable[0]), int(readable[1])
    if min(x, y, width, height) < 0 or x + width > frame_w or y + height > frame_h:
        raise ValueError('分区超出阅读图')
    with Image.open(_checked_source(data)) as image:
        image = image.convert('RGB')
        if image.size != (frame_w, frame_h):
            raise ValueError('阅读图像素尺寸与评估记录不一致，拒绝按错误比例裁切')
        crop = image.crop((x, y, x + width, y + height))
        buffer = io.BytesIO()
        crop.save(buffer, format='PNG')
        return buffer.getvalue()


def save_review(stele_id: str, reviewer: str, damage_types: list, note: str, suggested_condition: str | None, roi: dict | None = None):
    data = load_assessment(stele_id)
    if data is None:
        return None
    reviewer = reviewer.strip()
    note = note.strip()
    if not reviewer or not note:
        raise ValueError('复核者和判断依据不能为空')
    if not damage_types or any(item not in DAMAGE_TYPES for item in damage_types):
        raise ValueError('损伤类型不在允许列表中')
    if suggested_condition is not None and suggested_condition not in SUGGESTED_CONDITIONS:
        raise ValueError('建议等级不在允许列表中')
    linked = None
    if roi is not None:
        readable = (data.get('imageDimensions') or {}).get('readable') or [0, 0]
        frame_w, frame_h = int(readable[0]), int(readable[1])
        x, y, width, height = int(roi['x']), int(roi['y']), int(roi['width']), int(roi['height'])
        if min(x, y, width, height) < 0 or x + width > frame_w or y + height > frame_h:
            raise ValueError('复核区域超出阅读图')
        linked = {'x': x, 'y': y, 'width': width, 'height': height, 'space': 'readable native pixels'}
    REVIEWS.mkdir(parents=True, exist_ok=True)
    with _REVIEW_LOCK:
        history = review_history(stele_id)
        record = {
            'version': len(history) + 1,
            'steleId': stele_id,
            'reviewer': reviewer,
            'reviewerQualification': '界面填写的姓名，系统没有核验专家身份',
            'damageTypes': list(dict.fromkeys(damage_types)),
            'note': note,
            'suggestedCondition': suggested_condition,
            'roi': linked,
            'savedAt': datetime.now(timezone.utc).isoformat(),
            'expertReview': False,
            'basis': '界面提交的复核意见，追加保存，不覆盖先前意见，也不覆盖自动初筛等级。',
        }
        path = REVIEWS / f'{stele_id}.jsonl'
        with path.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + '\n')
        history.append(record)
    return {'latest': record, 'history': history, 'expertReview': False}
