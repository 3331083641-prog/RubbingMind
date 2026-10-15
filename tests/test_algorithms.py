# -*- coding: utf-8 -*-
"""
墨韵智考 - 核心频空域联合去噪算法单元测试
"""
import os
import sys
import numpy as np
import pytest
from skimage.metrics import structural_similarity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from algorithm_engine import (
    algorithm_engine,
    compute_metrics,
    calculate_tenengrad,
    safe_read_image,
    mat_to_base64
)


def test_frequency_domain_filter():
    """测试 2D-FFT 频域滤波矩阵计算与能量谱生成"""
    test_gray = np.full((128, 128), 50, dtype=np.uint8)
    # 添加高频网格底噪
    test_gray[::4, ::4] = 200
    
    filtered, spectrum = algorithm_engine.apply_frequency_domain_filter(test_gray, d0=40, filter_type="gaussian")
    assert filtered.shape == (128, 128)
    assert spectrum.shape == (128, 128, 3)
    assert filtered.dtype == np.uint8


def test_spatial_domain_enhancement():
    """测试空域形态学顶帽、NLM 非局部均值与 CLAHE 自适应增强"""
    test_gray = np.full((100, 100), 40, dtype=np.uint8)
    test_gray[40:60, 40:60] = 220
    
    enhanced = algorithm_engine.apply_spatial_domain_enhancement(
        test_gray, nlm_h=10.0, clahe_clip=2.5, morph_kernel=3
    )
    assert enhanced.shape == (100, 100)
    assert enhanced.dtype == np.uint8


def test_compute_metrics():
    """测试 PSNR、SSIM 与边缘清晰度量化指标"""
    ref = np.full((100, 100), 100, dtype=np.uint8)
    ref[30:70, 30:70] = 220
    
    noisy = ref.copy()
    noisy[::5, ::5] = 0
    
    metrics = compute_metrics(ref, noisy)
    assert "psnr" in metrics
    assert "ssim" in metrics
    mse = np.mean((ref.astype(float) - noisy.astype(float)) ** 2)
    assert metrics["psnr"] == pytest.approx(10 * np.log10(255 ** 2 / mse))
    assert metrics["ssim"] == pytest.approx(structural_similarity(ref, noisy, data_range=255))
    assert compute_metrics(ref, ref)["psnr"] == float('inf')


def test_full_pipeline_synthetic():
    """测试完整去噪修复流水线在合成拓片上的端到端执行"""
    test_img = np.zeros((120, 120), dtype=np.uint8)
    test_img[30:90, 50:70] = 220
    test_img += np.random.randint(0, 30, (120, 120), dtype=np.uint8)

    res = algorithm_engine.process_rubbing(
        image_input=test_img,
        d0=40.0,
        nlm_h=10.0,
        clahe_clip=2.0,
        morph_kernel=3
    )
    
    assert "metrics" in res
    assert "restored_b64" in res
    assert "fft_spectrum_b64" in res
    assert res["metrics"]["psnr"] is None
    assert res["metrics"]["ssim"] is None
    assert res["diagnostic_metrics"]["input_output_mean_absolute_difference"] >= 0


def test_frequency_modes_and_parameters_change_pixels():
    y, x = np.mgrid[:128, :128]
    clean = np.where((x > 35) & (x < 90) & (y > 25) & (y < 100), 210, 30).astype(np.uint8)
    periodic = np.clip(clean.astype(float) + 28 * np.sin(2 * np.pi * x / 8), 0, 255).astype(np.uint8)
    low_1, _ = algorithm_engine.apply_frequency_domain_filter(periodic, d0=25, filter_type='butterworth', order=1)
    low_5, _ = algorithm_engine.apply_frequency_domain_filter(periodic, d0=25, filter_type='butterworth', order=5)
    assert np.mean(np.abs(low_1.astype(float) - low_5.astype(float))) > 0.1
    notch, _, details = algorithm_engine.apply_frequency_domain_filter(periodic, d0=40, filter_type='notch', return_details=True)
    assert details['notchApplied'] and details['detectedPairs']
    assert np.mean((notch.astype(float) - clean) ** 2) < np.mean((periodic.astype(float) - clean) ** 2)
    spatial_a = algorithm_engine.apply_spatial_domain_enhancement(periodic, nlm_h=2, clahe_clip=1, morph_kernel=1)
    spatial_b = algorithm_engine.apply_spatial_domain_enhancement(periodic, nlm_h=20, clahe_clip=5, morph_kernel=7)
    assert np.mean(np.abs(spatial_a.astype(float) - spatial_b.astype(float))) > 0.1
