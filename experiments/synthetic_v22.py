"""Frozen synthetic check for the v2.2 candidate. These are not museum rubbings."""
from __future__ import annotations

import numpy as np

from algorithm_engine import compute_metrics
from degradation_analysis import VERSION, AdaptiveRubbingRestorer, AdaptiveRubbingRestorerV22
from experiments.run_v2 import degrade

SEED = 20261018
SIZE = 128


def reference_image():
    image = np.full((SIZE, SIZE), 214, np.uint8)
    image[28:32, 18:108] = 28
    image[36:96, 46:50] = 28
    image[36:40, 46:78] = 28
    jitter = np.random.default_rng(SEED).integers(0, 6, image.shape, dtype=np.uint8)
    return np.clip(image.astype(np.int16) - jitter, 0, 255).astype(np.uint8)


def run():
    reference = reference_image()
    current = AdaptiveRubbingRestorer()
    candidate = AdaptiveRubbingRestorerV22()
    rows = []
    for mode in ('gaussian', 'occlusion', 'blur'):
        degraded, params = degrade(reference, mode, SEED, 1.0)
        for name, restorer in (('adaptive_v21', current), ('adaptive_v22_candidate', candidate)):
            output, meta = restorer.restore(degraded)
            before = compute_metrics(reference, degraded)
            after = compute_metrics(reference, output)
            rows.append({
                'degradation': mode,
                'method': name,
                'version': meta['version'],
                'selectedOutput': meta['selectedOutput'],
                'operators': [item['operator'] for item in meta['decisions']],
                'inputPsnr': before['psnr'],
                'psnr': after['psnr'],
                'ssim': after['ssim'],
                'negativeLift': after['psnr'] < before['psnr'] - 1e-6,
                'unchanged': bool(np.array_equal(output, degraded)),
                'parameters': params,
            })
    return {
        'experimentId': 'synthetic-v22-candidate-2026-10-18',
        'seed': SEED,
        'source': 'procedural stroke image, not one of the 28 museum rubbings',
        'productionVersion': VERSION,
        'notHistoricalRestoration': '这些 PSNR 和 SSIM 的参照是生成图，不是历史原碑。',
        'resultNote': '这张生成图上，v2.1 对遮挡和模糊已经退回原图，v2.2 没有额外提高 PSNR。默认算法仍是 v2.1。',
        'rows': rows,
    }
