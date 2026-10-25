"""Measured quantities for explaining a restoration result (read-only helpers).

Used by the mechanism cases and by the measured negative-lift causes (E-04).
All functions take 8-bit grayscale arrays and never modify them.
"""
from __future__ import annotations

import cv2
import numpy as np

from degradation_analysis import change_stats, fidelity_diagnostics, missing_information_mask, periodic_peaks

CANNY = (80, 160)


def foreground(image):
    """Minority class after Otsu, as in degradation_analysis.analyze_degradation."""
    mask = (image > cv2.threshold(image, 0, 255, cv2.THRESH_OTSU)[0]).astype(np.uint8)
    if mask.mean() > .5:
        mask = 1 - mask
    return mask


def edges(image):
    return cv2.Canny(image, *CANNY) > 0


def edge_f1(reference, image):
    a, b = edges(reference), edges(image)
    total = np.count_nonzero(a) + np.count_nonzero(b)
    return 2 * np.count_nonzero(a & b) / total if total else 1.0


def thin_stroke_mae(reference, image):
    """MAE on reference Canny pixels (the heldout batch's thinStrokeMae definition)."""
    mask = edges(reference)
    if not mask.any():
        return None
    return float(np.mean(np.abs(reference.astype(np.float32) - image.astype(np.float32))[mask]))


def foreground_loss(reference, image):
    """Fraction of reference foreground pixels that are not foreground in image."""
    ref = foreground(reference).astype(bool)
    if not ref.any():
        return None
    return float(np.count_nonzero(ref & ~foreground(image).astype(bool)) / np.count_nonzero(ref))


def periodic_energy(image):
    peaks = periodic_peaks(image)
    return float(sum(p['energyFraction'] for p in peaks)), len(peaks)


def psnr(reference, image):
    mse = float(np.mean((reference.astype(np.float64) - image.astype(np.float64)) ** 2))
    return None if mse == 0 else float(10 * np.log10(255.0 ** 2 / mse))


def measure_case(reference, damaged, output):
    """Everything is measured from pixels; nothing reads the degradation label."""
    change = change_stats(damaged, output)
    input_energy, input_peaks = periodic_energy(damaged)
    output_energy, output_peaks = periodic_energy(output)
    missing = missing_information_mask(damaged) > 0
    changed = np.abs(damaged.astype(np.int16) - output.astype(np.int16)) > 0
    gate = fidelity_diagnostics(damaged, output, 0.0, periodic=bool(input_peaks))
    input_error = float(np.mean(np.abs(damaged.astype(np.float32) - reference.astype(np.float32))))
    loss_in, loss_out = foreground_loss(reference, damaged), foreground_loss(reference, output)
    mae_in, mae_out = thin_stroke_mae(reference, damaged), thin_stroke_mae(reference, output)
    psnr_in, psnr_out = psnr(reference, damaged), psnr(reference, output)
    return {
        'changedPixelRatio': change['changedPixelRatio'], 'changedPixelCount': change['changedPixelCount'],
        'meanAbsChange': change['meanAbsDiff'], 'maxAbsChange': change['maxAbsDiff'],
        'inputMeanAbsError': input_error,
        'changeToInputErrorRatio': (change['meanAbsDiff'] / input_error) if input_error > 0 else None,
        'psnrInput': psnr_in, 'psnrOutput': psnr_out,
        'psnrDelta': None if psnr_in is None or psnr_out is None else psnr_out - psnr_in,
        'edgeF1Input': edge_f1(reference, damaged), 'edgeF1Output': edge_f1(reference, output),
        'edgeF1Delta': edge_f1(reference, output) - edge_f1(reference, damaged),
        'thinStrokeMaeInput': mae_in, 'thinStrokeMaeOutput': mae_out,
        'thinStrokeMaeDelta': None if mae_in is None or mae_out is None else mae_out - mae_in,
        'foregroundLossInput': loss_in, 'foregroundLossOutput': loss_out,
        'foregroundLossDelta': None if loss_in is None or loss_out is None else loss_out - loss_in,
        'periodicEnergyInput': input_energy, 'periodicPeaksInput': input_peaks,
        'periodicEnergyOutput': output_energy, 'periodicPeaksOutput': output_peaks,
        'periodicEnergyRatio': (output_energy / input_energy) if input_energy > 0 else None,
        'missingMaskPixels': int(np.count_nonzero(missing)),
        'changedInMissingFraction': float(np.count_nonzero(changed & missing) / np.count_nonzero(changed)) if changed.any() else 0.0,
        'strongEdgeRetention': gate['strongEdgeRetention'], 'contrastRatio': gate['contrastRatio'],
    }
