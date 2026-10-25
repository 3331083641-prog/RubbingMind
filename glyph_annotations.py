"""Human glyph labels and held-out evaluation.

Predictions are never promoted into ground truth. With no verified labels the
metrics stay unassessed; this module does not invent an accuracy number.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from catalog import BASE

ANNOTATION_DIR = BASE / 'data' / 'catalog' / 'glyph-annotations'
from runtime_paths import runtime_dir

RUNTIME_DIR = runtime_dir() / 'glyph-annotations'
REQUIRED = ('steleId', 'bbox', 'glyph', 'sourceCitation', 'annotator', 'reviewStatus', 'damageLevel', 'split')
VERIFIED = 'human_verified'


def load_annotations():
    records = []
    paths = []
    if ANNOTATION_DIR.is_dir():
        paths.extend(sorted(ANNOTATION_DIR.glob('*.json')))
    runtime = RUNTIME_DIR / 'annotations.jsonl'
    if runtime.is_file():
        for line in runtime.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if isinstance(item, dict):
                item = dict(item)
                item['_file'] = runtime.name
                records.append(item)
    for path in paths:
        payload = json.loads(path.read_text(encoding='utf-8'))
        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if not isinstance(item, dict):
                continue
            item = dict(item)
            item['_file'] = path.name
            records.append(item)
    return records


def verified_annotations():
    usable = []
    for item in load_annotations():
        if item.get('reviewStatus') != VERIFIED:
            continue
        if item.get('labelOrigin') == 'model_prediction':
            continue
        if any(not str(item.get(key, '')).strip() for key in REQUIRED):
            continue
        if len(str(item.get('glyph'))) != 1:
            continue
        usable.append(item)
    return usable


def save_human_annotation(payload: dict):
    """Store a human note. This route cannot mint a verified test label or a model ground truth."""
    if payload.get('labelOrigin') == 'model_prediction':
        raise ValueError('不能把模型预测写成人工标注')
    glyph = str(payload.get('glyph') or '').strip()
    if len(glyph) != 1:
        raise ValueError('核定字符必须是一个字')
    stele_id = str(payload.get('steleId') or '').strip()
    citation = str(payload.get('sourceCitation') or '').strip()
    annotator = str(payload.get('annotator') or '').strip()
    image_sha = str(payload.get('imageSha256') or '').strip()
    box = payload.get('bbox') or {}
    if not stele_id or not citation or not annotator or len(image_sha) < 32:
        raise ValueError('标注必须绑定文物、出处、标注者和图像 SHA')
    try:
        coords = {key: int(box[key]) for key in ('x', 'y', 'width', 'height')}
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('标注框坐标无效') from exc
    if min(coords.values()) < 0:
        raise ValueError('标注框坐标无效')
    record = {
        'steleId': stele_id,
        'inferenceId': payload.get('inferenceId'),
        'bbox': coords,
        'glyph': glyph,
        'variantNote': str(payload.get('variantNote') or '').strip(),
        'sourceCitation': citation,
        'annotator': annotator,
        'damageLevel': str(payload.get('damageLevel') or '未分级'),
        'imageSha256': image_sha,
        'reviewStatus': 'human_recorded',
        'labelOrigin': 'human',
        'split': 'unassigned',
        'savedAt': datetime.now(timezone.utc).isoformat(),
        'countsAsAccuracy': False,
    }
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    with (RUNTIME_DIR / 'annotations.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + '\n')
    return record


def evaluate(predictions=None):
    """Score only verified labels, split so a stele cannot train and test itself."""
    recorded = [item for item in load_annotations() if item.get('reviewStatus') == 'human_recorded']
    labels = verified_annotations()
    test = [item for item in labels if item.get('split') == 'test']
    train_steles = {item['steleId'] for item in labels if item.get('split') == 'train'}
    leaked = [item for item in test if item['steleId'] in train_steles]
    independent = [item for item in test if item['steleId'] not in train_steles]
    if not independent:
        return {
            'evaluationStatus': 'unassessed',
            'top1': None, 'top3': None, 'rejectionRate': None, 'byDamage': {},
            'verifiedLabels': len(labels), 'recordedLabels': len(recorded),
            'independentTestLabels': 0,
            'excludedBecauseSteleOverlap': len(leaked),
            'reason': '没有按碑刻分开的人工核验测试标注，不计算识别准确率。已记录的人工标注也不自动升为真值。',
        }
    by_id = {}
    for item in predictions or []:
        if item.get('annotationId'):
            by_id[item['annotationId']] = item
    considered = [item for item in independent if item.get('annotationId') in by_id]
    if len(considered) != len(independent):
        return {
            'evaluationStatus': 'unassessed',
            'top1': None, 'top3': None, 'rejectionRate': None, 'byDamage': {},
            'verifiedLabels': len(labels), 'recordedLabels': len(recorded), 'independentTestLabels': len(independent),
            'excludedBecauseSteleOverlap': len(leaked),
            'reason': '人工测试标注尚未全部对应到实际推演记录，不计算识别准确率。',
        }
    hits1 = hits3 = rejected = 0
    by_damage = {}
    for item in considered:
        prediction = by_id[item['annotationId']]
        glyphs = [candidate.get('glyph') for candidate in prediction.get('candidates') or []]
        refused = prediction.get('source') == 'rejected' or prediction.get('status') == 'no_candidate'
        correct1 = bool(glyphs) and glyphs[0] == item['glyph'] and not refused
        correct3 = item['glyph'] in glyphs[:3] and not refused
        hits1 += int(correct1)
        hits3 += int(correct3)
        rejected += int(refused)
        bucket = by_damage.setdefault(item.get('damageLevel') or 'unspecified', {'n': 0, 'top1': 0})
        bucket['n'] += 1
        bucket['top1'] += int(correct1)
    total = len(considered)
    return {
        'evaluationStatus': 'measured',
        'top1': hits1 / total, 'top3': hits3 / total, 'rejectionRate': rejected / total,
        'byDamage': by_damage, 'verifiedLabels': len(labels), 'recordedLabels': len(recorded), 'independentTestLabels': total,
        'excludedBecauseSteleOverlap': len(leaked),
        'reason': '准确率只统计人工核验且碑刻不重叠的测试标注。',
    }
