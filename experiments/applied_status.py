"""Shared rules for separating passthrough (output == input) from actual processing.

Criterion pixel-equal-v1: a row is passthrough when its output image has every
pixel equal to the algorithm input. Byte-equal files are a sufficient but not
necessary condition (PNG encoders may differ); pixel equality decides.

Means are reported three ways and never merged silently:
  all          every row with a metric (historical comparability)
  processed    rows whose output changed at least one pixel
  passthrough  rows that returned the input unchanged
"""
from __future__ import annotations

import math
from typing import Iterable

CRITERION = 'pixel-equal-v1'
METRICS = ('psnr', 'ssim', 'edgeF1', 'thinStrokeMae', 'processingMs')


def _mean(values):
    values = [v for v in values if v is not None and isinstance(v, (int, float)) and math.isfinite(v)]
    return (sum(values) / len(values)) if values else None


def is_passthrough(row: dict):
    """True / False / None (undeterminable). Never guesses from PSNR alone."""
    value = row.get('isPassthrough')
    return value if value in (True, False) else None


def split_means(rows: Iterable[dict], metrics=METRICS):
    rows = list(rows)
    processed = [r for r in rows if is_passthrough(r) is False]
    passthrough = [r for r in rows if is_passthrough(r) is True]
    unknown = [r for r in rows if is_passthrough(r) is None]
    result = {
        'n': len(rows), 'processedN': len(processed), 'passthroughN': len(passthrough),
        'undeterminedN': len(unknown), 'artifactN': len({r.get('sampleId') for r in rows}),
        'processedArtifactN': len({r.get('sampleId') for r in processed}),
        'passthroughCriterion': CRITERION,
    }
    for metric in metrics:
        if not any(metric in r for r in rows):
            continue
        result[metric + 'MeanAll'] = _mean(r.get(metric) for r in rows)
        result[metric + 'MeanProcessed'] = _mean(r.get(metric) for r in processed)
        result[metric + 'MeanPassthrough'] = _mean(r.get(metric) for r in passthrough)
    return result
