"""Reproducible paired-reference controls; never claims historical glyph recovery."""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import statistics
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import skimage
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from algorithm_engine import algorithm_engine, compute_metrics
CONFIG = Path(__file__).with_name('config.json')
OUT = Path(__file__).parent / 'results' / '2026-10-15'


def degrade(reference: np.ndarray, mode: str, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    h, w = reference.shape
    if mode == 'gaussian':
        result = reference.astype(float) + rng.normal(0, 18, reference.shape)
    elif mode == 'salt_pepper':
        result = reference.copy()
        random = rng.random(reference.shape)
        result[random < .018] = 0
        result[random > .982] = 255
    elif mode == 'periodic':
        x = np.arange(w)[None, :]
        result = reference.astype(float) + 27 * np.sin(2 * np.pi * x / 8)
    elif mode == 'blur':
        result = cv2.GaussianBlur(reference, (0, 0), 1.5)
    elif mode == 'occlusion':
        result = reference.copy()
        x, y = w // 3, h // 3
        result[y:y+28, x:x+45] = np.median(reference)
    else:
        raise ValueError(mode)
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_method(image: np.ndarray, method: str):
    frequency = algorithm_engine.apply_frequency_domain_filter
    if method == 'degraded':
        return image.copy(), 'baseline'
    if method == 'gaussian_lowpass':
        return frequency(image, d0=60, filter_type='gaussian')[0], 'applied'
    if method == 'butterworth_lowpass':
        return frequency(image, d0=60, filter_type='butterworth', order=2)[0], 'applied'
    if method == 'notch':
        result, _, details = frequency(image, d0=48, filter_type='notch', return_details=True)
        return result, 'applied' if details['notchApplied'] else 'not_applicable'
    if method == 'morphology':
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel), 'applied'
    if method == 'fast_nlm':
        return cv2.fastNlMeansDenoising(image, None, h=10, templateWindowSize=7, searchWindowSize=21), 'applied'
    if method == 'nlm_clahe':
        denoised = cv2.fastNlMeansDenoising(image, None, h=10, templateWindowSize=7, searchWindowSize=21)
        return cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(denoised), 'applied'
    if method == 'joint':
        # The joint pipeline is the same frequency+spatial implementation used by the API.
        mode = 'butterworth'
        filtered, _, details = frequency(image, d0=60, filter_type=mode, order=2, return_details=True)
        output = algorithm_engine.apply_spatial_domain_enhancement(filtered, nlm_h=10, clahe_clip=2.5, morph_kernel=3)
        return output, 'notch_applied' if details['notchApplied'] else 'applied'
    raise ValueError(method)


def run(config_path: Path = CONFIG, output_dir: Path = OUT):
    config = json.loads(config_path.read_text(encoding='utf-8'))
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    sources = []
    for sample_index, sample in enumerate(config['samples']):
        source = ROOT / sample['file']
        original = cv2.imdecode(np.frombuffer(source.read_bytes(), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        x0, y0, x1, y1 = sample['crop']
        reference = original[y0:y1, x0:x1]
        assert reference.shape == (256, 256)
        cv2.imwrite(str(output_dir / f"{sample['id']}_reference.png"), reference)
        sources.append({**sample, 'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest()})
        for mode_index, degradation in enumerate(config['degradations']):
            seed = config['seed'] + sample_index * 100 + mode_index
            damaged = degrade(reference, degradation, seed)
            comparison = [('reference', reference)]
            for method in config['methods']:
                start = time.perf_counter()
                output, applicability = apply_method(damaged, method)
                elapsed_ms = (time.perf_counter() - start) * 1000
                filename = f"{sample['id']}_{degradation}_{method}.png"
                cv2.imwrite(str(output_dir / filename), output)
                comparison.append((method, output))
                measured = compute_metrics(reference, output)
                ref_edges = cv2.Canny(reference, 80, 160)>0
                out_edges = cv2.Canny(output, 80, 160)>0
                overlap = np.count_nonzero(ref_edges & out_edges)
                edge_f1 = 2 * overlap / (np.count_nonzero(ref_edges) + np.count_nonzero(out_edges)) if np.any(ref_edges) or np.any(out_edges) else 1.0
                records.append({'sampleId': sample['id'], 'degradation': degradation, 'seed': seed, 'method': method,
                                'applicability': applicability, 'psnr': measured['psnr'], 'ssim': measured['ssim'],
                                'edgeF1': edge_f1, 'processingMs': elapsed_ms, 'output': filename,
                                'outputSha256': hashlib.sha256((output_dir / filename).read_bytes()).hexdigest()})
            sheet = Image.new('RGB', (256 * 3, 282 * 3), '#ece8df')
            draw = ImageDraw.Draw(sheet)
            for index, (label, image) in enumerate(comparison):
                x, y = (index % 3) * 256, (index // 3) * 282
                sheet.paste(Image.fromarray(image).convert('RGB'), (x, y + 26))
                draw.text((x + 6, y + 6), label, fill='#161616')
            sheet.save(output_dir / f"comparison_{sample['id']}_{degradation}.jpg", quality=90)
    methods = config['methods']
    summary = []
    for method in methods:
        values = [r for r in records if r['method'] == method and r['applicability'] != 'not_applicable']
        summary.append({'method': method, 'n': len(values), **{
            metric + suffix: (statistics.mean(row[metric] for row in values) if suffix == 'Mean' else statistics.stdev(row[metric] for row in values) if len(values) > 1 else 0.0)
            for metric in ('psnr', 'ssim', 'edgeF1', 'processingMs') for suffix in ('Mean', 'Std')}})
    with (output_dir / 'results.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0])); writer.writeheader(); writer.writerows(records)
    with (output_dir / 'summary.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    (output_dir / 'results.json').write_text(json.dumps({'config': config, 'sources': sources, 'rows': records, 'summary': summary,
        'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'opencv': cv2.__version__, 'scikitImage': skimage.__version__}},
        ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    return {'cases': len(records), 'summary': summary}


if __name__ == '__main__':
    print(json.dumps(run(), ensure_ascii=False, indent=2))
