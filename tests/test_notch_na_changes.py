"""E-05 classification of notch rows labelled not_applicable whose pixels changed."""

import cv2
import numpy as np

from tests.test_mechanism_ci_causes import _texture


class _PreFixNotch:
    """The pre-fix no-peak path: all-ones mask, FFT round trip, astype(uint8)."""

    def apply_frequency_domain_filter(self, gray, d0=48, filter_type='notch', return_details=False):
        back = np.real(np.fft.ifft2(np.fft.ifftshift(np.fft.fftshift(np.fft.fft2(gray.astype(np.float32))))))
        return np.clip(back, 0, 255).astype(np.uint8), None, {'notchApplied': False}


def _batch(tmp_path, output):
    gray = _texture(0)
    cv2.imwrite(str(tmp_path / 'in.png'), gray)
    cv2.imwrite(str(tmp_path / 'out.png'), output(gray))
    return {'method': 'notch', 'appliedStatus': 'processed_not_applicable_label', 'inputFile': 'in.png', 'outputFile': 'out.png'}


def _engines():
    from algorithm_engine import RubbingAlgorithmEngine
    return {'snapshot': _PreFixNotch(), 'head': RubbingAlgorithmEngine()}


def test_truncation_only_change_is_rounding(tmp_path):
    from experiments.notch_na_changes import ROUNDING, classify
    item = _batch(tmp_path, lambda g: _PreFixNotch().apply_frequency_domain_filter(g)[0])
    label, evidence = classify(tmp_path, item, _engines())
    assert label == ROUNDING, evidence
    assert evidence['signedDiffValues'] == [-1] and evidence['changedPixelCount'] > 0
    assert evidence['headReturnsInput'] and evidence['changedEqualsTruncation']


def test_other_change_is_not_called_rounding(tmp_path):
    from experiments.notch_na_changes import OTHER, classify

    def shifted(gray):
        out = gray.copy(); out[:4, :4] = np.clip(out[:4, :4].astype(int) + 5, 0, 255)
        return out
    label, evidence = classify(tmp_path, _batch(tmp_path, shifted), _engines())
    assert label == OTHER
    assert '差值不全为 -1' in evidence['failedChecks'] and '快照引擎未复现存档输出' in evidence['failedChecks']
