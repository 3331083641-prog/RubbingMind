"""Passthrough (output == input) must be separated from actual processing."""
import base64
import json
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def test_pixel_criterion_counts_every_changed_pixel():
    from degradation_analysis import change_stats
    a = np.full((10, 10), 100, np.uint8)
    same = change_stats(a, a.copy())
    assert same['isPassthrough'] is True and same['changedPixelCount'] == 0 and same['changedPixelRatio'] == 0
    b = a.copy(); b[0, 0] = 99; b[5, 5] = 110
    changed = change_stats(a, b)
    assert changed['isPassthrough'] is False
    assert changed['changedPixelCount'] == 2 and changed['totalPixelCount'] == 100
    assert abs(changed['changedPixelRatio'] - 0.02) < 1e-12 and changed['maxAbsDiff'] == 10
    color_a = np.zeros((4, 4, 3), np.uint8); color_b = color_a.copy(); color_b[1, 1, 2] = 1
    assert change_stats(color_a, color_b)['changedPixelCount'] == 1  # a pixel, not a channel count


def test_passthrough_rows_are_not_in_processed_mean():
    from experiments.applied_status import split_means
    rows = [
        {'sampleId': 'a', 'psnr': 30.0, 'isPassthrough': False},
        {'sampleId': 'b', 'psnr': 20.0, 'isPassthrough': True},
        {'sampleId': 'c', 'psnr': 10.0, 'isPassthrough': True},
        {'sampleId': 'd', 'psnr': 99.0, 'isPassthrough': None},
    ]
    result = split_means(rows, ('psnr',))
    assert result['processedN'] == 1 and result['passthroughN'] == 2 and result['undeterminedN'] == 1
    assert result['psnrMeanProcessed'] == 30.0
    assert result['psnrMeanPassthrough'] == 15.0
    assert abs(result['psnrMeanAll'] - (30 + 20 + 10 + 99) / 4) < 1e-12


def test_adaptive_identity_branch_is_recorded_as_original():
    from degradation_analysis import AdaptiveRubbingRestorer
    image = np.full((64, 64), 180, np.uint8)
    image[20:44, 30:34] = 40  # one clean stroke, no noise: residual evidence is weak
    output, meta = AdaptiveRubbingRestorer().restore(image)
    assert np.array_equal(output, image)
    assert meta['changeStats']['isPassthrough'] is True
    assert meta['selectedOutput'] == 'original'
    assert meta['outputMode'] in ('identity_no_evidence', 'gate_fallback_original')


def test_adaptive_processed_output_is_not_passthrough():
    from degradation_analysis import AdaptiveRubbingRestorer
    rng = np.random.default_rng(1)
    image = np.clip(150 + rng.normal(0, 25, (96, 96)), 0, 255).astype(np.uint8)
    output, meta = AdaptiveRubbingRestorer().restore(image)
    assert meta['changeStats']['isPassthrough'] is bool(np.array_equal(output, image))
    if not meta['changeStats']['isPassthrough']:
        assert meta['selectedOutput'] == 'candidate' and meta['outputMode'] == 'processed'


def test_compare_v21_exclusion_list_includes_v2_text_batch():
    from experiments.compare_v21 import previous_sample_ids
    seen = previous_sample_ids()
    for sample in ('han_03_liqi', 'tang_04_xuanmita', 'song_03_daguan', 'qing_04_ayuwang_reliquary'):
        assert '2026-10-17-v2-text' in seen[sample]
    assert '2026-10-17-v2' in seen['han_01_caoquan']
    assert not any('2026-10-18-v21-heldout' in batches for batches in seen.values())


def test_historical_retest_samples_were_seen_before():
    from experiments.compare_v21 import previous_sample_ids
    result = json.loads((ROOT / 'experiments/results/2026-10-18-v21-heldout/results.json').read_text(encoding='utf-8'))
    seen = previous_sample_ids()
    assert all(row['id'] in seen for row in result['samples'])


def _png(image):
    ok, data = cv2.imencode('.png', image)
    assert ok
    return 'data:image/png;base64,' + base64.b64encode(data.tobytes()).decode('ascii')


def _run_processing(tmp_path, monkeypatch, change):
    import museum_processing
    monkeypatch.setattr(museum_processing, 'BASE', tmp_path)
    (tmp_path / 'static/samples').mkdir(parents=True)
    gray = np.full((32, 32), 120, np.uint8); gray[8:24, 14:18] = 30
    (tmp_path / 'static/samples/sample_1.png').write_bytes(cv2.imencode('.png', gray)[1].tobytes())
    restored = gray.copy()
    if change:
        restored[0, 0] = 121
    engine = SimpleNamespace(process_rubbing=lambda **kwargs: {
        'original_b64': _png(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)),
        'restored_b64': _png(cv2.cvtColor(restored, cv2.COLOR_GRAY2BGR)),
        'metrics': {'elapsed_ms': 1.0}, 'diagnostic_metrics': {}, 'frequency_details': {'adaptive': {}},
        'working_image': {'sourceShape': [32, 32], 'workingShape': [32, 32], 'scale': 1.0}})
    params = dict(stele_id=None, sample_id='sample_1.png', image_base64=None, d0=45.0, filter_order=2,
                  filter_type='adaptive', h_nlm=10.0, clahe_clip=2.5, morph_kernel=3, damage_mask=None,
                  cinnabar_style='cinnabar', random_seed=0)
    req = SimpleNamespace(**params, model_dump=lambda exclude=None: {k: v for k, v in params.items() if k not in (exclude or set())})
    response = museum_processing.process_verified_request(req, SimpleNamespace(get_stele_by_id=lambda _id: None, retired={}), engine)
    stored = json.loads(next((tmp_path / 'static/results/uploaded-image').glob('*/processing.json')).read_text(encoding='utf-8'))
    return response, stored


def test_museum_processing_marks_unchanged_run_as_passthrough(tmp_path, monkeypatch):
    response, stored = _run_processing(tmp_path, monkeypatch, change=False)
    for record in (response, stored):
        assert record['isPassthrough'] is True
        assert record['changedPixelCount'] == 0 and record['changedPixelRatio'] == 0
        assert record['outputMode'] == 'passthrough'
        assert record['passthroughCriterion'] == 'pixel-equal-v1'
        assert record['passthroughSource'] == 'recorded'
        assert record['comparedImages'] == ['original', 'restored']
    assert stored['effectiveParameters']['strength'] == 1.0
    assert 'clahe_clip' in stored['effectiveParameters']['ignoredRequestParameters']


def test_museum_processing_reports_real_change_ratio(tmp_path, monkeypatch):
    response, _ = _run_processing(tmp_path, monkeypatch, change=True)
    assert response['isPassthrough'] is False
    assert response['changedPixelCount'] == 1 and abs(response['changedPixelRatio'] - 1 / 1024) < 1e-12
    assert response['outputMode'] == 'processed'


def test_registry_never_calls_the_retest_held_out():
    from experiment_registry import batches
    entry = {item['id']: item for item in batches()}['heldout-v20-v21-2026-10-18']
    assert entry['heldOut'] is False
    assert '留出' not in entry['displayName'] and '同批复测' in entry['displayName']
    assert any('2026-10-17-v2-text' in text for text in entry['limitations'])
