"""Regressions for /api/process-related algorithm behaviour owned by eval-sci.

Covers: change_stats int32 (no overflow on 16-bit), and E-05 notch not-applicable
passthrough in algorithm_engine. Does not re-implement museum_processing fields;
those are owned by agent/arch-backend after the Green 2026-10-19 ruling.
"""
import numpy as np


def test_change_stats_int32_reports_40000_on_uint16():
    from degradation_analysis import change_stats
    a = np.zeros((2, 2), np.uint16)
    b = a.copy()
    b[0, 0] = 40000
    stats = change_stats(a, b)
    assert stats['changedPixelCount'] == 1
    assert stats['maxAbsDiff'] == 40000
    assert stats['isPassthrough'] is False


def test_change_stats_int32_near_uint16_max():
    from degradation_analysis import change_stats
    a = np.array([[0, 65535]], np.uint16)
    b = np.array([[65535, 0]], np.uint16)
    stats = change_stats(a, b)
    assert stats['changedPixelCount'] == 2
    assert stats['maxAbsDiff'] == 65535


def test_notch_not_applicable_returns_input_unchanged():
    """E-05: no peak pair -> copy of input (no FFT round-trip truncation)."""
    import cv2
    from algorithm_engine import RubbingAlgorithmEngine
    noise = np.random.default_rng(0).normal(150, 80, (128, 128)).astype(np.float32)
    gray = np.clip(cv2.GaussianBlur(noise, (0, 0), 1.5) * 1.6 - 90, 0, 255).astype(np.uint8)
    out, _, details = RubbingAlgorithmEngine().apply_frequency_domain_filter(
        gray, d0=48, filter_type='notch', return_details=True)
    assert details.get('notchApplied') is False
    assert details.get('passthrough') is True
    assert np.array_equal(out, gray)
    assert int(np.count_nonzero(out.astype(np.int16) - gray.astype(np.int16))) == 0


def test_process_rubbing_notch_without_peaks_matches_spatial_on_copy():
    """process_rubbing(notch) with no peaks: frequency stage is identity; spatial still runs."""
    import cv2
    from algorithm_engine import RubbingAlgorithmEngine
    noise = np.random.default_rng(1).normal(140, 50, (64, 64)).astype(np.float32)
    gray = np.clip(cv2.GaussianBlur(noise, (0, 0), 1.0), 0, 255).astype(np.uint8)
    bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    engine = RubbingAlgorithmEngine()
    freq, _, details = engine.apply_frequency_domain_filter(gray, d0=48, filter_type='notch', return_details=True)
    assert details.get('notchApplied') is False and np.array_equal(freq, gray)
    # Full pipeline still applies spatial enhancement after the identity frequency stage.
    result = engine.process_rubbing(bgr, filter_type='notch', d0=48, filter_order=2, nlm_h=10)
    assert result.get('error') is None
    assert 'restored_b64' in result
