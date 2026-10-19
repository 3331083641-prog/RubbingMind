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


GENERIC_VERSION = 'baseline-delta-v1'
BASELINE_METHOD = 'degraded'


def _case_key(row: dict):
    """caseId when recorded; the 2026-10-15 batch has none, so fall back to its generator keys."""
    return row.get('caseId') or (row.get('sampleId'), row.get('degradation'), row.get('strength'), row.get('seed'))


def diagnose_batch(data: dict, experiment_id: str) -> dict:
    """Fact-only diagnosis for any registered batch (ARCHITECTURE_DECISIONS R1-4).

    Compares each method's PSNR with the unprocessed degraded input of the same case.
    Every negative-lift row is listed (no sampling). No cause is inferred.
    """
    rows = [row for row in data.get('rows') or [] if isinstance(row, dict)]
    baselines = {_case_key(row): row for row in rows if row.get('method') == BASELINE_METHOD}
    by_method: dict = {}
    cases = []
    unmatched = 0
    for row in rows:
        method = row.get('method')
        if method == BASELINE_METHOD:
            continue
        stats = by_method.setdefault(method, {'n': 0, 'negativeLift': 0, 'byteIdenticalToInput': 0, 'byteIdentityUnknown': 0, 'unmatched': 0})
        stats['n'] += 1
        base = baselines.get(_case_key(row))
        psnr, base_psnr = row.get('psnr'), (base or {}).get('psnr')
        if base is None or psnr is None or base_psnr is None:
            stats['unmatched'] += 1
            unmatched += 1
            continue
        input_sha = row.get('inputSha256') or base.get('outputSha256')
        identical = (row.get('outputSha256') == input_sha) if row.get('outputSha256') and input_sha else None
        if identical is None:
            stats['byteIdentityUnknown'] += 1
        elif identical:
            stats['byteIdenticalToInput'] += 1
        delta = psnr - base_psnr
        if delta < 0:
            stats['negativeLift'] += 1
            cases.append({
                'caseId': row.get('caseId'), 'sampleId': row.get('sampleId'), 'split': row.get('split'),
                'degradation': row.get('degradation'), 'strength': row.get('strength'), 'seed': row.get('seed'),
                'method': method, 'psnr': psnr, 'baselinePsnr': base_psnr, 'psnrDeltaFromInput': delta,
                'negativeLift': True, 'byteIdenticalToInput': identical,
                'output': row.get('output'), 'outputSha256': row.get('outputSha256'),
            })
    cases.sort(key=lambda c: c['psnrDeltaFromInput'])
    return {
        'experimentId': experiment_id,
        'diagnosisVersion': GENERIC_VERSION,
        'baselineMethod': BASELINE_METHOD,
        'comparison': 'psnr − 同一 case 的 degraded（未处理输入）psnr；< 0 记为负提升',
        'negativeLiftCount': len(cases),
        'unmatchedRowCount': unmatched,
        'byMethod': dict(sorted(by_method.items(), key=lambda kv: str(kv[0]))),
        'cases': cases,
        'causeCounts': None,
        'causeBasis': '未做归因：通用诊断只报告事实，不推断原因。',
        'byteIdentityBasis': 'outputSha256 与输入（inputSha256，缺失时取同 case 的 degraded 输出）相同即为原图返回；像素级判据以评测侧 applied_status 为准。',
        'caveat': CAVEAT,
    }
