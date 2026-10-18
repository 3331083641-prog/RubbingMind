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
