"""E-05 notch passthrough, E-04 measured causes, artifact CI and mechanism selection."""
import numpy as np


def _strokes(size=128):
    image = np.full((size, size), 200, np.uint8)
    image[20:100, 30:36] = 40
    image[60:66, 20:110] = 40
    return image


def _texture(seed=0, size=128):
    """Smooth random texture: no isolated periodic peaks, so notch is not applicable.

    With seed 0 the pre-fix engine (f0c5886) changed 27 pixels of this image through the
    FFT round trip and astype(uint8) truncation (E-05); the fixed engine changes none.
    """
    import cv2
    noise = np.random.default_rng(seed).normal(150, 80, (size, size)).astype(np.float32)
    return np.clip(cv2.GaussianBlur(noise, (0, 0), 1.5) * 1.6 - 90, 0, 255).astype(np.uint8)


def test_notch_without_peaks_returns_input_unchanged():
    from algorithm_engine import algorithm_engine
    from degradation_analysis import change_stats
    image = _texture()
    output, _, details = algorithm_engine.apply_frequency_domain_filter(image, d0=48, filter_type='notch', return_details=True)
    assert details['notchApplied'] is False and details['passthrough'] is True
    assert change_stats(image, output)['isPassthrough'] is True
    assert output is not image  # a copy, the caller's array is never aliased


def test_notch_with_periodic_interference_still_filters():
    from algorithm_engine import algorithm_engine
    image = np.clip(_texture(2).astype(np.float32) + 27 * np.sin(2 * np.pi * np.arange(128)[None, :] / 8), 0, 255).astype(np.uint8)
    output, _, details = algorithm_engine.apply_frequency_domain_filter(image, d0=48, filter_type='notch', return_details=True)
    assert details['notchApplied'] is True and 'passthrough' not in details
    assert not np.array_equal(output, image)


def test_not_applicable_notch_baseline_is_passthrough():
    from degradation_analysis import change_stats
    from experiments.run_ablation import apply_method
    image = _texture(1)
    output, applicability = apply_method(image, 'notch')
    assert applicability == 'not_applicable' and change_stats(image, output)['isPassthrough'] is True


def test_adaptive_processing_path_does_not_use_the_fixed_notch(monkeypatch):
    import base64
    import cv2
    from algorithm_engine import RubbingAlgorithmEngine

    def forbidden(*args, **kwargs):
        raise AssertionError('adaptive path must not call apply_frequency_domain_filter')
    engine = RubbingAlgorithmEngine()
    monkeypatch.setattr(engine, 'apply_frequency_domain_filter', forbidden)
    data = 'data:image/png;base64,' + base64.b64encode(cv2.imencode('.png', cv2.cvtColor(_strokes(), cv2.COLOR_GRAY2BGR))[1].tobytes()).decode()
    assert engine.process_rubbing(data, filter_type='adaptive')['frequency_details']['mode'] == 'adaptive'


def test_measured_causes_carry_value_threshold_and_unavailable_reason():
    from restoration_diagnosis import UNEXPLAINED, measured_causes
    entries, triggered = measured_causes({'edgeF1Delta': -0.1, 'foregroundLossDelta': 0.0, 'ssimDelta': None}, '无图像')
    edge = next(e for e in entries if e['measure'] == 'edgeF1Delta')
    assert edge['triggered'] and edge['value'] == -0.1 and edge['threshold'] == -0.02 and edge['comparator'] == '<'
    ssim = next(e for e in entries if e['measure'] == 'ssimDelta')
    assert ssim['available'] is False and ssim['unavailableReason'] == '无图像' and not ssim['triggered']
    assert triggered == ['边缘保真下降']
    assert measured_causes({})[1] == [UNEXPLAINED]


def test_diagnosis_keeps_rule_cause_labelled_and_adds_measured_evidence():
    from restoration_diagnosis import RULE_BASIS, diagnose
    report = diagnose()
    negatives = [c for c in report['cases'] if c['negativeLift']]
    assert negatives and all(c['causeBasis'] == RULE_BASIS for c in report['cases'])
    for case in negatives:
        assert case['measuredCauses']
        assert all({'measure', 'value', 'threshold', 'comparator', 'triggered'} <= set(e) for e in case['measuredEvidence'])
        pixel = next(e for e in case['measuredEvidence'] if e['measure'] == 'changedInMissingFraction')
        assert pixel['available'] is False  # the retest batch saved no images
    assert '留出' not in report['notRetuned'] and '同批复测' in report['notRetuned']


def test_measure_case_foreground_loss_is_measured_from_pixels():
    from restoration_measures import measure_case
    reference = _strokes()
    damaged = reference.copy()
    output = reference.copy()
    output[20:100, 30:36] = 200  # erase one stroke
    m = measure_case(reference, damaged, output)
    assert m['foregroundLossInput'] == 0 and m['foregroundLossOutput'] > 0.3
    assert m['changedPixelRatio'] > 0 and m['edgeF1Delta'] < 0


def test_artifact_bootstrap_is_seeded_and_flags_small_groups():
    from experiments.ci_by_artifact import SEED, bootstrap, compute
    per = {'a': [1.0, 3.0], 'b': [2.0], 'c': [4.0]}
    mean, ci = bootstrap(per)
    assert mean == (2.0 + 2.0 + 4.0) / 3 and ci == bootstrap(per)[1] and ci[0] <= mean <= ci[1]
    assert bootstrap({}) == (None, None)
    rows = []
    for sample, gain, passthrough in (('a', 1.0, False), ('b', 2.0, False), ('c', 0.0, True)):
        rows.append({'sampleId': sample, 'split': 'test', 'method': 'm', 'degradation': 'd', 'caseId': sample,
                     'isPassthrough': passthrough, 'psnr': 20 + gain, 'psnrGain': gain, 'ssim': None, 'ssimGain': None,
                     'edgeF1': None, 'edgeF1Gain': None})
    groups = {(g['degradation'], g['scope']): g for g in compute(rows)}
    processed = groups[('d', 'processed')]
    assert processed['artifactN'] == 2 and processed['ciReliable'] is False and processed['seed'] == SEED
    assert processed['psnrGainRowMean'] == 1.5
    assert groups[('d', 'passthrough')]['psnrGainSign'] == 'zero'
    assert groups[('d', 'all')]['ciReliable'] is True


def test_mechanism_selection_uses_median_rank_and_never_duplicates():
    from experiments.mechanism_cases import select
    rows, status = [], []
    def add(case, method, psnr, ops, passthrough):
        rows.append({'caseId': case, 'method': method, 'split': 'test', 'psnr': psnr, 'error': None,
                     'diagnostics': {'decisions': [{'operator': o} for o in ops]}})
        status.append({'isPassthrough': passthrough})
    for i, gain in enumerate([-3, -1, 1, 2, 5, 0, 0]):
        case = f'c{i}'
        add(case, 'degraded', 20.0, [], True)
        ops = ['notch'] if i in (2, 3) else ['fallback_identity'] if i == 6 else ['identity'] if i == 5 else ['nlm']
        add(case, 'adaptive_joint', 20.0 + gain, ops, gain == 0)
    picks = {p['category']: p for p in select(rows, status, 'test')}
    assert picks['improvement']['caseId'] == 'c3'  # gains 1,2,5 -> median 2
    assert picks['negative']['caseId'] == 'c0'     # gains -3,-1 -> index 0
    assert picks['passthrough']['caseId'] == 'c5' and picks['gate_reject']['caseId'] == 'c6'
    assert picks['notch']['caseId'] == 'c2'        # c3 already chosen -> nearest unchosen
    assert len({p['caseId'] for p in picks.values()}) == len(picks)
