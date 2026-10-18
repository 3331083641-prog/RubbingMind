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


def test_metrics_only_batch_does_not_blank_the_registry():
    from experiment_registry import batches
    ids = [item['id'] for item in batches()]
    assert 'controlled-rubbings-v2-text-2026-10-17' in ids
    assert 'heldout-v20-v21-2026-10-18' not in ids
