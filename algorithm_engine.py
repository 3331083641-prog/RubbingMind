# -*- coding: utf-8 -*-
"""
墨韵智考（RubbingMind）- 频空域联合去噪与微痕增强核心算法引擎
集成：
1. 2D-FFT 频域自适应滤波与能量幅度谱伪彩色渲染
2. 空域数学形态学（Top-Hat / Black-Hat / 开闭运算）石花微粒分离
3. Fast Non-Local Means (NLM) 非局部均值边缘保真平滑
4. CLAHE（对比度受限自适应直方图均衡化）微痕特征凸显
5. 宣纸朱砂/金石古籍墨拓仿真渲染引擎
6. PSNR、SSIM、石花抑制率、Tenengrad 梯度边缘增益等全套客观指标计算
"""

import base64
import io
import os
import time
import numpy as np
import cv2
from PIL import Image
from skimage.morphology import skeletonize
from degradation_analysis import AdaptiveRubbingRestorer

try:
    from skimage.metrics import structural_similarity as compute_ssim
    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False


def safe_read_image(image_path_or_bytes, is_gray=False):
    """
    Windows 中文路径兼容读取图像，支持文件路径或 raw bytes
    """
    if isinstance(image_path_or_bytes, (bytes, bytearray)):
        img_arr = np.frombuffer(image_path_or_bytes, dtype=np.uint8)
        flag = cv2.IMREAD_GRAYSCALE if is_gray else cv2.IMREAD_COLOR
        return cv2.imdecode(img_arr, flag)

    if isinstance(image_path_or_bytes, str):
        if not os.path.exists(image_path_or_bytes):
            raise FileNotFoundError(f"图像文件未找到: {image_path_or_bytes}")
        img_arr = np.fromfile(image_path_or_bytes, dtype=np.uint8)
        flag = cv2.IMREAD_GRAYSCALE if is_gray else cv2.IMREAD_COLOR
        return cv2.imdecode(img_arr, flag)

    if isinstance(image_path_or_bytes, np.ndarray):
        if is_gray and len(image_path_or_bytes.shape) == 3:
            return cv2.cvtColor(image_path_or_bytes, cv2.COLOR_BGR2GRAY)
        elif not is_gray and len(image_path_or_bytes.shape) == 2:
            return cv2.cvtColor(image_path_or_bytes, cv2.COLOR_GRAY2BGR)
        return image_path_or_bytes

    raise ValueError("不支持的图像输入类型")


def mat_to_base64(img_mat, ext=".png"):
    """将 OpenCV 矩阵编码为带 MIME 前缀的 Base64 字符串"""
    success, encoded = cv2.imencode(ext, img_mat)
    if not success:
        return ""
    b64_str = base64.b64encode(encoded.tobytes()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"


def base64_to_mat(b64_str, is_gray=False):
    """将 Base64 字符串解析为 OpenCV 矩阵"""
    if "," in b64_str:
        b64_str = b64_str.split(",")[1]
    raw_data = base64.b64decode(b64_str)
    img_arr = np.frombuffer(raw_data, dtype=np.uint8)
    flag = cv2.IMREAD_GRAYSCALE if is_gray else cv2.IMREAD_COLOR
    return cv2.imdecode(img_arr, flag)


def calculate_tenengrad(gray_img):
    """计算 Tenengrad 边缘清晰度算子 (Sobel 梯度平方和均值)"""
    gx = cv2.Sobel(gray_img, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray_img, cv2.CV_64F, 0, 1, ksize=3)
    grad = gx ** 2 + gy ** 2
    return float(np.mean(grad))


def fallback_ssim(img1, img2):
    """当无 skimage 时的高保真 SSIM 备用算法"""
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    kernel = cv2.getGaussianKernel(11, 1.5)
    window = np.outer(kernel, kernel.transpose())

    mu1 = cv2.filter2D(img1, -1, window)[5:-5, 5:-5]
    mu2 = cv2.filter2D(img2, -1, window)[5:-5, 5:-5]
    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = cv2.filter2D(img1 ** 2, -1, window)[5:-5, 5:-5] - mu1_sq
    sigma2_sq = cv2.filter2D(img2 ** 2, -1, window)[5:-5, 5:-5] - mu2_sq
    sigma12 = cv2.filter2D(img1 * img2, -1, window)[5:-5, 5:-5] - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    return float(ssim_map.mean())


def compute_metrics(reference_gray, restored_gray):
    """Paired 8-bit reference metrics. The reference must be an actual experiment target."""
    if reference_gray.shape != restored_gray.shape or reference_gray.dtype != np.uint8 or restored_gray.dtype != np.uint8:
        raise ValueError("配对真值和输出必须是同尺寸的 8 位灰度图")
    if min(reference_gray.shape) < 7:
        raise ValueError("SSIM 需要至少 7×7 像素")
    if not HAS_SKIMAGE:
        raise RuntimeError("配对 SSIM 评测需要 scikit-image")
    mse = float(np.mean((reference_gray.astype(np.float64) - restored_gray.astype(np.float64)) ** 2))
    psnr = float('inf') if mse == 0 else float(10 * np.log10(255.0 ** 2 / mse))
    return {"psnr": psnr, "ssim": float(compute_ssim(reference_gray, restored_gray, data_range=255))}


def compute_diagnostics(input_gray, output_gray):
    """Input/output change diagnostics; neither number measures restoration accuracy."""
    _, before = cv2.threshold(input_gray, 180, 255, cv2.THRESH_BINARY)
    _, after = cv2.threshold(output_gray, 180, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    before_count = int(np.count_nonzero(cv2.morphologyEx(before, cv2.MORPH_TOPHAT, kernel)))
    after_count = int(np.count_nonzero(cv2.morphologyEx(after, cv2.MORPH_TOPHAT, kernel)))
    before_edge = calculate_tenengrad(input_gray)
    after_edge = calculate_tenengrad(output_gray)
    return {
        "isolated_bright_pixel_change_percent": 100.0 * (before_count - after_count) / before_count if before_count else None,
        "tenengrad_change_percent": 100.0 * (after_edge - before_edge) / before_edge if before_edge else None,
        "input_output_mean_absolute_difference": float(np.mean(cv2.absdiff(input_gray, output_gray))),
    }


class RubbingAlgorithmEngine:
    """金石碑拓微痕修复与频空域联合去噪算法引擎"""

    def __init__(self):
        pass

    def apply_frequency_domain_filter(self, gray_img, d0=60, filter_type="butterworth", order=2, return_details=False):
        """
        2D-FFT 频域自适应低通/陷波滤波
        """
        h, w = gray_img.shape
        # 1. 2D-FFT
        f = np.fft.fft2(gray_img.astype(np.float32))
        fshift = np.fft.fftshift(f)

        # 2. 计算对数幅度谱 20 * log(|F| + 1)
        magnitude = 20 * np.log(np.abs(fshift) + 1.0)
        norm_mag = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        spectrum_color = cv2.applyColorMap(norm_mag, cv2.COLORMAP_VIRIDIS)

        # 3. 构造频域低通/带阻滤波器掩码
        cy, cx = h // 2, w // 2
        y, x = np.ogrid[:h, :w]
        dist_sq = (x - cx) ** 2 + (y - cy) ** 2

        details = {"mode": filter_type, "notchApplied": False, "detectedPairs": []}
        if d0 <= 0 or not 1 <= order <= 8:
            raise ValueError("截止频率或滤波器阶数无效")
        if filter_type == "gaussian":
            # 高斯滤波保真度更高，边缘无吉布斯震荡振铃效应
            filter_mask = np.exp(-dist_sq / (2 * (d0 ** 2)))
        elif filter_type == "butterworth":
            filter_mask = 1.0 / (1.0 + (dist_sq / (d0 ** 2)) ** order)
        elif filter_type == "notch":
            # Compare peaks to a smoothed local log-spectrum. Real imagery may have no
            # isolated periodic peaks; in that case leave it unchanged.
            log_spectrum = np.log1p(np.abs(fshift))
            background = cv2.GaussianBlur(log_spectrum, (0, 0), 6)
            excess = log_spectrum - background
            exclusion = max(12, min(h, w) // 12)
            excess[dist_sq < exclusion ** 2] = 0
            threshold = max(2.5, float(np.percentile(excess, 99.9)))
            local_max = cv2.dilate(excess.astype(np.float32), np.ones((9, 9), np.uint8))
            candidates = np.argwhere((excess >= threshold) & (excess >= local_max - 1e-6))
            filter_mask = np.ones((h, w), np.float32)
            seen = set()
            for py, px in sorted(candidates, key=lambda p: -excess[p[0], p[1]]):
                mirror_y, mirror_x = (2 * cy - int(py)) % h, (2 * cx - int(px)) % w
                pair = tuple(sorted(((int(py), int(px)), (mirror_y, mirror_x))))
                if pair in seen or min(excess[py, px], excess[mirror_y, mirror_x]) < threshold:
                    continue
                seen.add(pair)
                details["detectedPairs"].append([list(pair[0]), list(pair[1])])
                for ny, nx in pair:
                    distance = (y - ny) ** 2 + (x - nx) ** 2
                    filter_mask *= 1.0 - np.exp(-distance / (2.0 * max(1.5, d0 / 16.0) ** 2))
                if len(seen) == 8:
                    break
            details["notchApplied"] = bool(seen)
        else:
            raise ValueError("未知频域处理模式")

        # 保留极低频分量避免整体失真
        if filter_type != "notch":
            filter_mask = np.clip(filter_mask * 0.85 + 0.15, 0.0, 1.0)

        # 4. 频域相乘与逆变换
        filtered_fshift = fshift * filter_mask
        f_ishift = np.fft.ifftshift(filtered_fshift)
        img_back = np.fft.ifft2(f_ishift)
        img_back = np.real(img_back)
        img_back = np.clip(img_back, 0, 255).astype(np.uint8)

        return (img_back, spectrum_color, details) if return_details else (img_back, spectrum_color)

    def apply_spatial_domain_enhancement(self, gray_img, nlm_h=10, clahe_clip=2.5, morph_kernel=3):
        """
        空域多尺度非局部均值去噪、形态学石花剥离与 CLAHE 对比度增强
        """
        # 1. 数学形态学开运算去除微小尖锐椒盐石花
        k_size = max(1, int(morph_kernel))
        if k_size % 2 == 0:
            k_size += 1
        elem = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))

        # 顶帽变换获取孤立亮噪点
        tophat = cv2.morphologyEx(gray_img, cv2.MORPH_TOPHAT, elem)
        # 从原图扣除高频孤立顶帽噪点
        denoised_morph = cv2.subtract(gray_img, cv2.multiply(tophat, 0.7).astype(np.uint8))

        # 2. Fast Non-Local Means (NLM) 非局部均值去噪
        nlm_h_val = float(nlm_h)
        if nlm_h_val > 0.5:
            denoised_nlm = cv2.fastNlMeansDenoising(
                denoised_morph,
                None,
                h=nlm_h_val,
                templateWindowSize=7,
                searchWindowSize=21,
            )
        else:
            denoised_nlm = denoised_morph

        # 3. 双边滤波进一步保留字形笔画阶跃边缘
        bilateral = cv2.bilateralFilter(denoised_nlm, d=5, sigmaColor=35, sigmaSpace=35)

        # 4. CLAHE 自适应对比度拉伸微痕
        clahe = cv2.createCLAHE(clipLimit=float(clahe_clip), tileGridSize=(8, 8))
        enhanced = clahe.apply(bilateral)

        # 5. 轻微锐化文字骨架微痕
        gaussian = cv2.GaussianBlur(enhanced, (0, 0), 2.0)
        unsharp = cv2.addWeighted(enhanced, 1.25, gaussian, -0.25, 0)
        unsharp = np.clip(unsharp, 0, 255).astype(np.uint8)

        return unsharp

    def render_cinnabar_rubbing(self, enhanced_gray, orig_bgr, style="cinnabar", seed=0):
        """
        古典宣纸朱砂/墨拓仿真艺术复原
        - 宣纸质感底色：米黄 #f6f0e4 (RGB: 246, 240, 228)
        - 朱砂红字迹：#c83c23 (RGB: 200, 60, 35) 或金石浓墨 #221e1d
        """
        h, w = enhanced_gray.shape

        # 1. 构造宣纸米黄色基底 (Rice Paper Texture Base)
        paper_base = np.zeros((h, w, 3), dtype=np.float32)
        paper_base[:, :, 0] = 228.0  # B
        paper_base[:, :, 1] = 240.0  # G
        paper_base[:, :, 2] = 246.0  # R

        # 叠加微弱木纤维纸纹噪点
        paper_grain = np.random.default_rng(seed).normal(0, 4.0, (h, w, 3)).astype(np.float32)
        paper = np.clip(paper_base + paper_grain, 0, 255)

        # 2. 提取文字微痕二值与柔化掩码 (Soft Ink Mask)
        # 拓片为黑底白字，亮部为笔划
        otsu_val, _ = cv2.threshold(enhanced_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # 建立渐变权重
        ink_weight = np.clip((enhanced_gray.astype(np.float32) - (otsu_val * 0.75)) / (255.0 - otsu_val * 0.75), 0.0, 1.0)
        ink_weight_3c = np.repeat(ink_weight[:, :, None], 3, axis=2)

        # 3. 设定着色目标
        if style == "cinnabar":
            # 朱砂红 (#c83c23 -> BGR: 35, 60, 200)
            target_color = np.array([35.0, 60.0, 200.0], dtype=np.float32)
        elif style == "gold":
            # 泥金 (#d4af37 -> BGR: 55, 175, 212)
            target_color = np.array([55.0, 175.0, 212.0], dtype=np.float32)
        else:
            # 典藏浓墨 (#1f1b19 -> BGR: 25, 27, 31)
            target_color = np.array([25.0, 27.0, 31.0], dtype=np.float32)

        # 4. 混合墨色与宣纸底
        # 在字划处过渡到朱砂色，非字划处保持宣纸色
        rendered = paper * (1.0 - ink_weight_3c) + target_color * ink_weight_3c
        rendered = np.clip(rendered, 0, 255).astype(np.uint8)

        # 5. 添加古籍四周边框与金石钤印质感
        border_color = (target_color * 0.7).astype(int).tolist()
        cv2.rectangle(rendered, (12, 12), (w - 12, h - 12), border_color, 2)
        cv2.rectangle(rendered, (16, 16), (w - 16, h - 16), border_color, 1)

        return rendered

    def process_rubbing(
        self,
        image_input,
        d0=60,
        filter_order=2,
        filter_type="adaptive",
        nlm_h=10,
        clahe_clip=2.5,
        morph_kernel=3,
        damage_mask=None,
        cinnabar_style="cinnabar",
        reference_image=None,
        random_seed=0,
    ):
        """
        全流程频空域联合去噪与微痕修复管线
        返回：4 种 Base64 图像流、量化指标和耗时
        """
        start_time = time.perf_counter()

        # 1. 安全读取图像
        if isinstance(image_input, str) and (image_input.startswith("data:image") or len(image_input) > 200):
            orig_bgr = base64_to_mat(image_input, is_gray=False)
        else:
            orig_bgr = safe_read_image(image_input, is_gray=False)

        if orig_bgr is None:
            raise ValueError("无法解码输入的拓片图像")
        if orig_bgr.shape[0]*orig_bgr.shape[1] > 20_000_000:
            raise ValueError('源图超过2000万像素处理上限；请创建独立工作样本')

        source_shape = list(orig_bgr.shape[:2])
        scale = min(1., (1_600_000 / (orig_bgr.shape[0]*orig_bgr.shape[1]))**.5, 1800/max(orig_bgr.shape[:2]))
        if scale < 1:
            orig_bgr = cv2.resize(orig_bgr, (max(16,int(orig_bgr.shape[1]*scale)),max(16,int(orig_bgr.shape[0]*scale))), interpolation=cv2.INTER_AREA)
        orig_gray = cv2.cvtColor(orig_bgr, cv2.COLOR_BGR2GRAY)

        # 2. 如果存在前端传来的手动风化掩码，先模拟漫漶风化损伤
        if damage_mask is not None:
            if isinstance(damage_mask, str):
                mask_mat = base64_to_mat(damage_mask, is_gray=True)
            else:
                mask_mat = damage_mask

            if mask_mat is None or list(mask_mat.shape[:2]) != source_shape:
                raise ValueError('风化掩码必须与源图同尺寸')
            if scale < 1:
                mask_mat = cv2.resize(mask_mat,(orig_gray.shape[1],orig_gray.shape[0]),interpolation=cv2.INTER_NEAREST)
            if mask_mat is not None:
                mask_norm = (mask_mat > 30).astype(np.float32)
                # 在涂抹区域模拟重度石花斑点与风化磨损
                weather_noise = np.random.default_rng(random_seed).integers(90, 240, orig_gray.shape, dtype=np.uint8)
                orig_gray = np.where(mask_norm > 0.5, cv2.addWeighted(orig_gray, 0.4, weather_noise, 0.6, 0), orig_gray)
                orig_bgr = cv2.cvtColor(orig_gray, cv2.COLOR_GRAY2BGR)

        # 3. 频域滤波与 2D-FFT 频谱伪彩色渲染
        if filter_type == 'adaptive':
            restored_gray, adaptive_details = AdaptiveRubbingRestorer().restore(orig_gray, strength=max(.1,nlm_h/10), notch_width=max(.5,d0/60))
            spectrum = np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(orig_gray))))
            spectrum_color = cv2.applyColorMap(cv2.normalize(spectrum,None,0,255,cv2.NORM_MINMAX).astype(np.uint8),cv2.COLORMAP_VIRIDIS)
            frequency_details = {'mode':'adaptive','notchApplied':any(d['operator']=='notch' for d in adaptive_details['decisions']), 'adaptive':adaptive_details}
        else:
            freq_filtered_gray, spectrum_color, frequency_details = self.apply_frequency_domain_filter(
                orig_gray, d0=d0, filter_type=filter_type, order=filter_order, return_details=True
            )
            restored_gray = self.apply_spatial_domain_enhancement(freq_filtered_gray,nlm_h=nlm_h,clahe_clip=clahe_clip,morph_kernel=morph_kernel)

        # 将去噪后的灰度转为 BGR 显示
        restored_bgr = cv2.cvtColor(restored_gray, cv2.COLOR_GRAY2BGR)

        # 5. 渲染古典宣纸朱砂复原图
        cinnabar_bgr = self.render_cinnabar_rubbing(restored_gray, orig_bgr, style=cinnabar_style, seed=random_seed)

        # 6. 渲染笔画拓扑骨架图（玄青底 + 泥金微痕骨架）
        skeleton_bgr = self.render_stroke_skeleton(restored_gray)

        # 7. 计算质量评价指标
        reference_gray = safe_read_image(reference_image, is_gray=True) if reference_image is not None else None
        if reference_gray is not None and scale < 1:
            raise ValueError('配对评测请预先生成同尺度工作参考图，不隐式缩放真值')
        metrics = compute_metrics(reference_gray, restored_gray) if reference_gray is not None else {"psnr": None, "ssim": None}
        diagnostics = compute_diagnostics(orig_gray, restored_gray)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
        metrics["elapsed_ms"] = elapsed_ms

        # 8. 编码为 Base64 格式
        return {
            "original_b64": mat_to_base64(orig_bgr),
            "restored_b64": mat_to_base64(restored_bgr),
            "fft_spectrum_b64": mat_to_base64(spectrum_color),
            "cinnabar_b64": mat_to_base64(cinnabar_bgr),
            "skeleton_b64": mat_to_base64(skeleton_bgr),
            "binary_skeleton_b64": mat_to_base64(self.extract_stroke_skeleton(restored_gray)),
            "contour_b64": mat_to_base64(cv2.Canny(restored_gray,50,150)),
            "metrics": metrics,
            "diagnostic_metrics": diagnostics,
            "frequency_details": frequency_details,
            "working_image": {'sourceShape':source_shape,'workingShape':list(orig_gray.shape),'scale':scale,'interpolation':'INTER_AREA' if scale<1 else 'none'},
            "random_seed": int(random_seed),
        }

    def extract_stroke_skeleton(self, restored_gray):
        _, binary = cv2.threshold(restored_gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        if np.mean(binary > 0) > .5:
            binary = 255-binary
        return (skeletonize(binary>0)*255).astype(np.uint8)

    def render_stroke_skeleton(self, restored_gray):
        """
        基于形态学骨架抽取与高保真微痕边缘拓扑细化
        渲染成深邃玄青底色 (#0a0d12) 搭配泥金色 (#d4af37) 与青瓷色高光笔画骨架图
        """
        combined = self.extract_stroke_skeleton(restored_gray)

        h, w = restored_gray.shape
        out_bgr = np.zeros((h, w, 3), dtype=np.uint8)
        out_bgr[:, :] = [18, 13, 10]

        glow = cv2.GaussianBlur(combined, (5, 5), 2)
        gold_color = np.array([55.0, 175.0, 212.0], dtype=np.float32)
        weight = (combined.astype(np.float32) * 0.75 + glow.astype(np.float32) * 0.4) / 255.0
        weight = np.clip(weight, 0.0, 1.0)
        weight_3c = np.repeat(weight[:, :, None], 3, axis=2)

        rendered = out_bgr.astype(np.float32) * (1.0 - weight_3c) + gold_color * weight_3c
        return np.clip(rendered, 0, 255).astype(np.uint8)


# 全局单例
algorithm_engine = RubbingAlgorithmEngine()

if __name__ == "__main__":
    test_sample = os.path.join(os.path.dirname(__file__), "static", "samples", "sample_1.png")
    if os.path.exists(test_sample):
        print(f"正在测试算法引擎: {test_sample}")
        out = algorithm_engine.process_rubbing(test_sample)
        print("算法处理成功！指标结果:", out["metrics"])
    else:
        print("测试样本不存在，跳过独立测试。")
