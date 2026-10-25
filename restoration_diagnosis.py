"""Explain v2.1 same-batch-retest failures without rescoring or deleting them.

Two cause fields are reported side by side (E-04):
  cause / causeBasis      the original rule, chosen by degradation type
                          ('规则推断（按退化类型）'); kept for compatibility.
  measuredCauses          causes derived from measured quantities. Each entry
                          carries the measure, its value, the threshold and the
                          comparator, and whether it was triggered. Measures that
                          the batch cannot provide are listed as unavailable.
Thresholds are declared constants (MEASURED_CRITERIA_VERSION), not tuned on results.
"""
from __future__ import annotations

import json
from catalog import BASE

RESULT = BASE / 'experiments/results/2026-10-18-v21-heldout/results.json'
CAVEAT = '受控退化下的 PSNR、SSIM 和边缘保真变化，不等于历史碑刻原字已经被复原。'
RULE_BASIS = '规则推断（按退化类型）'
MEASURED_CRITERIA_VERSION = 'measured-causes-v1'
UNEXPLAINED = '未定位到测量原因（待人工复核）'

# (cause, measure, comparator, threshold). Pixel measures need saved images.
CRITERIA = (
    ('笔画前景损失', 'foregroundLossDelta', '>', 0.02),
    ('边缘保真下降', 'edgeF1Delta', '<', -0.02),
    ('细笔画误差增大', 'thinStrokeMaeDelta', '>', 0.5),
    ('结构相似度下降', 'ssimDelta', '<', -0.01),
    ('周期干扰残留', 'periodicEnergyRatio', '>=', 0.5),
    ('引入新的周期峰', 'periodicEnergyOutputWithoutInputPeaks', '>', 0.0),
    ('改动幅度超过输入误差', 'changeToInputErrorRatio', '>', 1.0),
    ('改动落在缺失/平坦区域', 'changedInMissingFraction', '>', 0.2),
    ('强边缘被削弱', 'strongEdgeRetention', '<', 0.85),
    ('对比度被放大', 'contrastRatio', '>', 1.10),
)
_COMPARE = {'>': lambda v, t: v > t, '<': lambda v, t: v < t, '>=': lambda v, t: v >= t}


def measured_causes(measures: dict, unavailable_reason: str | None = None):
    """measures: name -> number or None. Returns (entries, triggered cause names)."""
    values = dict(measures)
    if values.get('periodicPeaksInput') == 0 and values.get('periodicEnergyOutput') is not None:
        values['periodicEnergyOutputWithoutInputPeaks'] = values['periodicEnergyOutput']
    entries = []
    for cause, measure, comparator, threshold in CRITERIA:
        value = values.get(measure)
        available = value is not None
        entries.append({
            'cause': cause, 'measure': measure, 'value': value, 'comparator': comparator, 'threshold': threshold,
            'available': available, 'triggered': bool(available and _COMPARE[comparator](value, threshold)),
            'unavailableReason': None if available else (unavailable_reason or '该量不适用或无法测量'),
        })
    triggered = [e['cause'] for e in entries if e['triggered']]
    return entries, triggered or [UNEXPLAINED]


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


def _numeric_measures(row: dict, baseline: dict | None):
    """The retest batch saved numbers only; pixel measures stay None."""
    def delta(metric):
        if baseline is None or row.get(metric) is None or baseline.get(metric) is None:
            return None
        return row[metric] - baseline[metric]
    ssim_delta = None if row.get('ssim') is None or row.get('inputSsim') is None else row['ssim'] - row['inputSsim']
    return {'psnrDelta': row.get('psnrDeltaFromInput'), 'ssimDelta': ssim_delta,
            'edgeF1Delta': delta('edgeF1'), 'thinStrokeMaeDelta': delta('thinStrokeMae')}


def diagnose(path=RESULT):
    data = json.loads(path.read_text(encoding='utf-8'))
    all_rows = data.get('rows') or []
    baselines = {(r.get('sampleId'), r.get('degradation'), r.get('strength')): r for r in all_rows if r.get('method') == 'degraded'}
    rows = [row for row in all_rows if row.get('method') == 'adaptive_v21']
    cases = []
    for row in rows:
        delta = row.get('psnrDeltaFromInput')
        unchanged = delta == 0
        if not row.get('negativeLift') and not unchanged:
            continue
        measures = _numeric_measures(row, baselines.get((row.get('sampleId'), row.get('degradation'), row.get('strength'))))
        entries, triggered = measured_causes(measures, '本批次未保存图像，像素级量无法测量')
        cases.append({
            'sampleId': row.get('sampleId'),
            'degradation': row.get('degradation'),
            'strength': row.get('strength'),
            'negativeLift': bool(row.get('negativeLift')),
            'unchangedFromInput': unchanged,
            'psnrDeltaFromInput': delta,
            'fidelityAccepted': row.get('fidelityAccepted'),
            'cause': '算法没有修改像素' if unchanged and not row.get('negativeLift') else _cause(row),
            'causeBasis': RULE_BASIS,
            'measuredCauses': triggered if row.get('negativeLift') else [],
            'measuredEvidence': entries if row.get('negativeLift') else [],
            'measures': measures,
        })
    counts, measured_counts = {}, {}
    for case in cases:
        if case['negativeLift']:
            counts[case['cause']] = counts.get(case['cause'], 0) + 1
            for cause in case['measuredCauses']:
                measured_counts[cause] = measured_counts.get(cause, 0) + 1
    return {
        'experimentId': data.get('experimentId') or 'heldout-v20-v21-2026-10-18',
        'displayName': '同批复测 v2.1（v2.0 对照，2026-10-18）',
        'method': 'adaptive_v21',
        'negativeLiftCount': sum(1 for case in cases if case['negativeLift']),
        'unchangedCount': sum(1 for case in cases if case['unchangedFromInput']),
        'causeCounts': counts,
        'causeCountsBasis': RULE_BASIS,
        'measuredCauseCounts': measured_counts,
        'measuredCriteriaVersion': MEASURED_CRITERIA_VERSION,
        'measuredCriteria': [dict(zip(('cause', 'measure', 'comparator', 'threshold'), c)) for c in CRITERIA],
        'measuredNote': '一个负提升可同时触发多个测量原因；本批次没有图像，像素级量标为不可用。阈值为事先声明的常数，没有按结果调整。',
        'cases': cases,
        'caveat': CAVEAT,
        'notRetuned': '这份诊断只读取已经固定的同批复测结果，没有删除负提升；这 14 件与 2026-10-17-v2-text 相同，不是未见测试集。',
    }


GENERIC_VERSION = 'baseline-delta-v1'
BASELINE_METHOD = 'degraded'
BYTE_IDENTICAL_ALIAS = 'byteIdenticalToInput'


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
        stats = by_method.setdefault(method, {'n': 0, 'negativeLift': 0, 'byteIdentical': 0, 'byteIdentityUnknown': 0, 'unmatched': 0})
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
            stats['byteIdentical'] += 1
        delta = psnr - base_psnr
        if delta < 0:
            stats['negativeLift'] += 1
            cases.append({
                'caseId': row.get('caseId'), 'sampleId': row.get('sampleId'), 'split': row.get('split'),
                'degradation': row.get('degradation'), 'strength': row.get('strength'), 'seed': row.get('seed'),
                'method': method, 'psnr': psnr, 'baselinePsnr': base_psnr, 'psnrDeltaFromInput': delta,
                'negativeLift': True, 'byteIdentical': identical,
                'output': row.get('output'), 'outputSha256': row.get('outputSha256'),
            })
    cases.sort(key=lambda c: c['psnrDeltaFromInput'])
    # REPORT_DATA_SPEC §0.3 names the file-SHA flag `byteIdentical`. `byteIdenticalToInput` is kept for one
    # version as a deprecated alias with the same value (BYTE_IDENTICAL_ALIAS), then removed.
    for stats in by_method.values():
        stats[BYTE_IDENTICAL_ALIAS] = stats['byteIdentical']
    for case in cases:
        case[BYTE_IDENTICAL_ALIAS] = case['byteIdentical']
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
        'deprecatedFields': {BYTE_IDENTICAL_ALIAS: '别名，等于 byteIdentical；保留一个版本后移除'},
        'byteIdentityBasis': 'outputSha256 与输入（inputSha256，缺失时取同 case 的 degraded 输出）相同即为原图返回；像素级判据以评测侧 applied_status 为准。',
        'caveat': CAVEAT,
    }
