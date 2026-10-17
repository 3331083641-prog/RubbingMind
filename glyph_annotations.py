"""Human glyph labels and held-out evaluation.

Predictions are never promoted into ground truth. With no verified labels the
metrics stay unassessed; this module does not invent an accuracy number.
"""
from __future__ import annotations

import json
from catalog import BASE

ANNOTATION_DIR = BASE / 'data' / 'catalog' / 'glyph-annotations'
REQUIRED = ('steleId', 'bbox', 'glyph', 'sourceCitation', 'annotator', 'reviewStatus', 'damageLevel', 'split')
VERIFIED = 'human_verified'


def load_annotations():
    if not ANNOTATION_DIR.is_dir():
        return []
    records = []
    for path in sorted(ANNOTATION_DIR.glob('*.json')):
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


def evaluate(predictions=None):
    """Score only verified labels, split so a stele cannot train and test itself."""
    labels = verified_annotations()
    test = [item for item in labels if item.get('split') == 'test']
    train_steles = {item['steleId'] for item in labels if item.get('split') == 'train'}
    leaked = [item for item in test if item['steleId'] in train_steles]
    independent = [item for item in test if item['steleId'] not in train_steles]
    if not independent:
        return {
            'evaluationStatus': 'unassessed',
            'top1': None, 'top3': None, 'rejectionRate': None, 'byDamage': {},
            'verifiedLabels': len(labels), 'independentTestLabels': 0,
            'excludedBecauseSteleOverlap': len(leaked),
            'reason': '没有按碑刻分开的人工核验测试标注，不计算识别准确率。',
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
            'verifiedLabels': len(labels), 'independentTestLabels': len(independent),
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
        'byDamage': by_damage, 'verifiedLabels': len(labels), 'independentTestLabels': total,
        'excludedBecauseSteleOverlap': len(leaked),
        'reason': '准确率只统计人工核验且碑刻不重叠的测试标注。',
    }
