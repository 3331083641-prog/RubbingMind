"""The held-out comparison artifact keeps every sample, including occlusion losses."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_heldout_comparison_retains_occlusion_failures():
    result = json.loads((ROOT / 'experiments/results/2026-10-18-v21-heldout/results.json').read_text(encoding='utf-8'))
    assert len(result['samples']) == 14
    assert {row['id'] for row in result['samples']} == {
        'han_03_liqi', 'han_04_shichen', 'wei_03_kouyan', 'wei_04_wangsong',
        'tang_03_yanjiamiao', 'tang_04_xuanmita', 'song_03_daguan', 'song_04_mengying',
        'yuan_03_shengzhu', 'yuan_04_jingyuanchang', 'ming_03_wugou', 'ming_04_tongdian',
        'qing_03_sanxitang_preface', 'qing_04_ayuwang_reliquary',
    }
    occlusion = next(row for row in result['summary'] if row['method'] == 'adaptive_v21' and row['degradation'] == 'occlusion')
    assert occlusion['n'] == 14 and occlusion['failed'] == 0
    assert occlusion['negativeLiftCount'] >= 1
    assert all(row['psnrMean'] is not None for row in result['summary'] if row['failed'] == 0 and row['n'])


def test_metrics_only_batch_stays_visible_without_hiding_image_batches():
    from experiment_registry import batches, export_payload
    listed = {item['id']: item for item in batches()}
    assert 'controlled-rubbings-v2-text-2026-10-17' in listed
    heldout = listed['heldout-v20-v21-2026-10-18']
    assert heldout['metricsOnly'] is True and heldout['imageComparisonAvailable'] is False
    body, media = export_payload(heldout['id'], 'summary.csv')
    assert media == 'text/csv' and b'adaptive_v21' in body and b'occlusion' in body


def test_failure_diagnosis_keeps_negative_cases():
    from restoration_diagnosis import diagnose
    report = diagnose()
    assert report['negativeLiftCount'] > 0
    assert any(case['cause'] == '本身信息不可恢复' and case['negativeLift'] for case in report['cases'])
    assert '历史碑刻' in report['caveat']
    assert '没有删除负提升' in report['notRetuned']
