"""Explain existing v2.1 held-out failures without rescoring or deleting them."""
from __future__ import annotations

import json
from catalog import BASE

RESULT = BASE / 'experiments/results/2026-10-18-v21-heldout/results.json'
CAVEAT = '受控退化下的 PSNR、SSIM 和边缘保真变化，不等于历史碑刻原字已经被复原。'


def _cause(row: dict) -> str:
    degradation = row.get('degradation')
    if row.get('fidelityAccepted') is False:
        return '保真门控拒绝'
    if degradation == 'occlusion':
        return '本身信息不可恢复'
    if degradation == 'periodic':
        return '频谱检测不可靠'
    if degradation == 'blur':
        return '输入影像质量限制'
    if degradation == 'gaussian':
        return '算子或参数不适合该噪声'
    if degradation == 'salt_pepper':
        return '算子选择与细笔画保真冲突'
    return '负提升，需对照该样本'


def diagnose(path=RESULT):
    data = json.loads(path.read_text(encoding='utf-8'))
    rows = [row for row in data.get('rows') or [] if row.get('method') == 'adaptive_v21']
    cases = []
    for row in rows:
        delta = row.get('psnrDeltaFromInput')
        unchanged = delta == 0
        if not row.get('negativeLift') and not unchanged:
            continue
        cases.append({
            'sampleId': row.get('sampleId'),
            'degradation': row.get('degradation'),
            'negativeLift': bool(row.get('negativeLift')),
            'unchangedFromInput': unchanged,
            'psnrDeltaFromInput': delta,
            'fidelityAccepted': row.get('fidelityAccepted'),
            'cause': '算法没有修改像素' if unchanged and not row.get('negativeLift') else _cause(row),
        })
    counts = {}
    for case in cases:
        if case['negativeLift']:
            counts[case['cause']] = counts.get(case['cause'], 0) + 1
    return {
        'experimentId': data.get('experimentId') or 'heldout-v20-v21-2026-10-18',
        'method': 'adaptive_v21',
        'negativeLiftCount': sum(1 for case in cases if case['negativeLift']),
        'unchangedCount': sum(1 for case in cases if case['unchangedFromInput']),
        'causeCounts': counts,
        'cases': cases,
        'caveat': CAVEAT,
        'notRetuned': '这份诊断只读取已经固定的留出结果，没有删除负提升，也没有把这 14 件重新当作未见测试集。',
    }
