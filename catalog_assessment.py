"""Read-only access to the 28 archived assessments. Paths cannot be chosen by the caller."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from catalog import BASE, load

ASSESS = BASE / 'data/catalog/assessments'
REVIEWS = BASE / 'data/runtime/condition-reviews'
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


def _review(stele_id: str):
    path = REVIEWS / f'{stele_id}.json'
    if not path.is_file():
        return None
    data = _read_json(path)
    return data if data.get('steleId') == stele_id else None


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
    source_url = _source_public_url(data)
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
        'regionAnalysis': _region(stele_id),
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


def save_review(stele_id: str, reviewer: str, damage_types: list, note: str, suggested_condition: str | None):
    if load_assessment(stele_id) is None:
        return None
    reviewer = reviewer.strip()
    note = note.strip()
    if not reviewer or not note:
        raise ValueError('复核者和判断依据不能为空')
    if not damage_types or any(item not in DAMAGE_TYPES for item in damage_types):
        raise ValueError('损伤类型不在允许列表中')
    if suggested_condition is not None and suggested_condition not in SUGGESTED_CONDITIONS:
        raise ValueError('建议等级不在允许列表中')
    REVIEWS.mkdir(parents=True, exist_ok=True)
    record = {
        'steleId': stele_id,
        'reviewer': reviewer,
        'damageTypes': list(dict.fromkeys(damage_types)),
        'note': note,
        'suggestedCondition': suggested_condition,
        'savedAt': datetime.now(timezone.utc).isoformat(),
        'basis': '界面提交的复核意见，不是自动生成的专家鉴定，也不覆盖自动初筛等级。',
    }
    path = REVIEWS / f'{stele_id}.json'
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return record
