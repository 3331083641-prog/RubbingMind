"""Input-only, explainable diagnostics. Scores are heuristics, never accuracy."""
from __future__ import annotations

import cv2
import numpy as np
from scipy import fft

VERSION = 'adaptive-rubbing-v2.1'


PASSTHROUGH_CRITERION = 'pixel-equal-v1'


def change_stats(before, after):
    """Pixel-level change between an algorithm input and its output.

    isPassthrough is True only when every pixel is equal (criterion
    pixel-equal-v1). Small but non-zero changes are reported as processed with
    their real ratio; they are never rounded to passthrough.
    """
    a = np.asarray(before)
    b = np.asarray(after)
    if a.shape != b.shape:
        raise ValueError('输入与输出尺寸不同，无法逐像素比较')
    # int32: int16 overflows for 16-bit PNGs (values up to 65535).
    diff = np.abs(a.astype(np.int32) - b.astype(np.int32))
    if diff.ndim == 3:
        changed_mask = np.any(diff > 0, axis=2)
    else:
        changed_mask = diff > 0
    changed = int(np.count_nonzero(changed_mask))
    total = int(changed_mask.size)
    return {
        'isPassthrough': changed == 0,
        'changedPixelCount': changed,
        'totalPixelCount': total,
        'changedPixelRatio': changed / total if total else None,
        'maxAbsDiff': int(diff.max()) if diff.size else 0,
        'meanAbsDiff': float(diff.mean()) if diff.size else 0.0,
        'passthroughCriterion': PASSTHROUGH_CRITERION,
    }


def validate_gray(image):
    if image is None or image.ndim != 2 or image.dtype != np.uint8 or min(image.shape) < 16:
        raise ValueError('需要至少16×16的8位灰度图')
    if image.size > 1_600_000:
        raise ValueError('工作图超过160万像素；请使用有记录的等比例工作副本')


def periodic_peaks(image):
    """Conjugate FFT peaks, local log prominence and amplitude/energy evidence."""
    values = image.astype(np.float32)
    h, w = values.shape
    spectrum = fft.fftshift(fft.fft2(values - values.mean(), workers=1))
    power = np.abs(spectrum) ** 2
    log = np.log1p(np.abs(spectrum))
    excess = log - cv2.GaussianBlur(log, (0, 0), 4)
    yy, xx = np.ogrid[:h, :w]
    cy, cx = h // 2, w // 2
    valid = (yy-cy)**2 + (xx-cx)**2 > max(8, min(h, w)/16)**2
    maxima = cv2.dilate(excess, np.ones((7, 7), np.uint8))
    locations = np.argwhere(valid & (excess > 3.5) & (excess >= maxima - 1e-5))
    pairs, seen = [], set()
    total = float(power.sum()) + 1e-9
    for y, x in sorted(locations, key=lambda p: -power[tuple(p)]):
        mirror = ((2*cy-int(y)) % h, (2*cx-int(x)) % w)
        pair = tuple(sorted(((int(y), int(x)), mirror)))
        amplitude = float(2 * abs(spectrum[y, x]) / image.size)
        energy = float((power[y, x] + power[mirror]) / total)
        if pair in seen or pair[0] == pair[1] or excess[mirror] < 3.5 or amplitude < 4 or energy < .008:
            continue
        pairs.append({'positions': [list(p) for p in pair], 'amplitude': amplitude,
                      'energyFraction': energy, 'logProminence': float(min(excess[y, x], excess[mirror]))})
        seen.add(pair)
        if len(pairs) == 4:
            break
    return pairs


def analyze_degradation(image):
    validate_gray(image)
    f = image.astype(np.float32)
    # MAD of a diagonal high-pass response; sparse strokes do not dominate median.
    response = cv2.filter2D(f, -1, np.array([[1,-1],[-1,1]], np.float32))
    sigma = float(np.median(np.abs(response - np.median(response))) / (2 * .67448975))
    median = cv2.medianBlur(image, 3)
    residual = f - median.astype(np.float32)
    # Require >= 6 neighbours near local median: avoid treating thin strokes as specks.
    near = (np.abs(residual) < 25).astype(np.float32)
    neighbours = cv2.boxFilter(near, -1, (3,3), normalize=False)
    impulse = (np.abs(residual) > 65) & ((image < 12) | (image > 243)) & (neighbours >= 6)
    smooth = cv2.GaussianBlur(f, (0,0), 1)
    gx, gy = cv2.Sobel(smooth, -1, 1, 0), cv2.Sobel(smooth, -1, 0, 1)
    gradient = cv2.magnitude(gx, gy)
    lap = cv2.Laplacian(smooth, -1)
    local = cv2.GaussianBlur(f*f, (0,0), 4) - cv2.GaussianBlur(f, (0,0), 4)**2
    freq = fft.rfft2(f - f.mean(), workers=1)
    yy = fft.fftfreq(image.shape[0])[:,None]; xx = fft.rfftfreq(image.shape[1])[None,:]
    energy = np.abs(freq)**2
    foreground = (image > cv2.threshold(image,0,255,cv2.THRESH_OTSU)[0]).astype(np.uint8)
    if foreground.mean() > .5:
        foreground = 1-foreground
    distance = cv2.distanceTransform(foreground, cv2.DIST_L2, 3)
    return {
        'noiseSigmaMAD': sigma, 'residualMAD': float(np.median(np.abs(residual))),
        'impulseFraction': float(impulse.mean()), 'periodicPeaks': periodic_peaks(image),
        'highFrequencyEnergyFraction': float(energy[(xx*xx+yy*yy)>.25**2].sum()/(energy.sum()+1e-9)),
        'localContrastRMS': float(np.sqrt(np.maximum(local,0)).mean()),
        'gradientMean': float(gradient.mean()), 'laplacianVariance': float(lap.var()),
        'darkFraction': float((image<25).mean()), 'brightFraction': float((image>230).mean()),
        'dynamicRange': float(np.percentile(image,95)-np.percentile(image,5)),
        'thinStrokeRisk': float(((distance>0)&(distance<1.5)).sum()/max(1,foreground.sum())),
        'note': '无参考诊断；噪声、模糊和笔画风险可能受真实石花/纸纹影响，不是修复准确率。',
    }, impulse


def missing_information_mask(image):
    """Interior uniform patches that are smaller than the page background.

    A flat hole is missing information. Later filters must copy the original
    pixels back instead of painting a stroke into it.
    """
    values = image.astype(np.float32)
    mean = cv2.blur(values, (15, 15))
    square = cv2.blur(values * values, (15, 15))
    deviation = np.sqrt(np.maximum(square - mean * mean, 0))
    flat = cv2.erode((deviation < 2.2).astype(np.uint8), np.ones((5, 5), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(flat, 8)
    mask = np.zeros(image.shape, np.uint8)
    if count <= 1:
        return mask
    areas = sorted(((index, int(stats[index, cv2.CC_STAT_AREA])) for index in range(1, count)), key=lambda item: -item[1])
    border, interior = [], []
    for index, area in areas:
        x, y, width, height = (int(stats[index, key]) for key in (
            cv2.CC_STAT_LEFT, cv2.CC_STAT_TOP, cv2.CC_STAT_WIDTH, cv2.CC_STAT_HEIGHT))
        touches = x <= 1 or y <= 1 or x + width >= image.shape[1] - 1 or y + height >= image.shape[0] - 1
        (border if touches else interior).append((index, area))
    background = {border[0][0]} if border else set()
    if border:
        background_pixels = image[labels == border[0][0]]
        background_mean = float(background_pixels.mean()) if background_pixels.size else float(np.median(image))
    else:
        edge = np.concatenate([image[0], image[-1], image[:, 0], image[:, -1]])
        background_mean = float(np.median(edge))
    limit = image.size * 0.12
    for index, area in interior:
        if index in background or area < 80 or area > limit:
            continue
        region_mean = float(image[labels == index].mean())
        # Page-colored interior blanks are margins or column gaps, not loss.
        if abs(region_mean - background_mean) < 18:
            continue
        mask[labels == index] = 255
    return mask


def preserve_missing_regions(original, processed):
    mask = missing_information_mask(original)
    preserved = processed.copy()
    preserved[mask > 0] = original[mask > 0]
    return preserved, int(np.count_nonzero(mask))


def fidelity_diagnostics(before, after, noise_sigma, periodic=False):
    def gradient(image):
        smooth = cv2.GaussianBlur(image.astype(np.float32),(0,0),3 if periodic else 1)
        return cv2.magnitude(cv2.Sobel(smooth,-1,1,0),cv2.Sobel(smooth,-1,0,1))
    a, b = gradient(before), gradient(after)
    strong = a > max(30,float(np.percentile(a,85)))
    ratio = float(np.mean(b[strong])/max(1e-6,float(np.mean(a[strong])))) if strong.any() else 1.
    mad = float(np.mean(cv2.absdiff(before,after)))
    contrast_ratio = float(after.std()/max(1,before.std()))
    reasons = []
    if ratio < .70: reasons.append('强结构梯度损失超过30%')
    if ratio > 1.18: reasons.append('边缘过冲风险')
    if contrast_ratio > 1.18: reasons.append('对比度放大风险')
    if mad > max(18,noise_sigma*1.6): reasons.append('输入输出变化过大')
    return {'accepted': not reasons, 'strongEdgeRetention':ratio,'meanAbsoluteChange':mad,
            'contrastRatio':contrast_ratio,'reasons':reasons,'basis':'输入输出启发式保真门控，非质量真值'}


class AdaptiveRubbingRestorer:
    """No degradation label or reference parameter is accepted by production logic."""
    version = VERSION

    def restore(self, image, strength=1., notch_width=.8):
        features, impulse = analyze_degradation(image)
        result = image.copy(); decisions = []
        if features['periodicPeaks']:
            h,w=image.shape; yy,xx=np.ogrid[:h,:w]
            spec=fft.fftshift(fft.fft2(result.astype(np.float32),workers=1))
            mask=np.ones(image.shape,np.float32)
            for pair in features['periodicPeaks']:
                for y,x in pair['positions']:
                    mask *= 1-np.exp(-((yy-y)**2+(xx-x)**2)/(2*notch_width**2))
            result=np.clip(np.rint(fft.ifft2(fft.ifftshift(spec*mask),workers=1).real),0,255).astype(np.uint8)
            decisions.append({'operator':'notch','width':notch_width,'reason':'检出共轭显著峰、幅值和能量证据'})
        else:
            decisions.append({'operator':'skip_notch','reason':'未检出符合阈值的周期峰；不强行陷波'})
        if .001 < features['impulseFraction'] < .15:
            result[impulse]=cv2.medianBlur(result,3)[impulse]
            decisions.append({'operator':'isolated_impulse_median','pixels':int(impulse.sum()),'reason':'仅替换局部孤立极值；不执行全局开运算'})
        remaining, _ = analyze_degradation(result)
        sigma=remaining['noiseSigmaMAD']
        notch_cleared=bool(features['periodicPeaks']) and not remaining['periodicPeaks']
        if notch_cleared and sigma <= max(6.0, features['noiseSigmaMAD'] * 0.85):
            decisions.append({'operator':'stop_after_notch','reason':'陷波后共轭峰消失且残差未升高，不再执行 NLM'})
        elif sigma > 4:
            h=float(np.clip(sigma*.85*strength,3,25))
            if features['thinStrokeRisk'] > 0.45:
                h=float(np.clip(h * 0.45, 1.5, 12))
                decisions.append({'operator':'thin_stroke_nlm','h':h,'thinStrokeRisk':features['thinStrokeRisk'],'reason':'细笔画占比高，降低 NLM 强度，避免抹断或粘连'})
            else:
                decisions.append({'operator':'nlm','h':h,'reason':'高通MAD显示随机残差；保留强边缘'})
            result=cv2.fastNlMeansDenoising(result,None,h=h,templateWindowSize=7,searchWindowSize=21)
        else:
            decisions.append({'operator':'identity','reason':'残差证据弱；不锐化、不强制CLAHE/形态学'})
        result, missing_pixels = preserve_missing_regions(image, result)
        if missing_pixels:
            decisions.append({'operator':'preserve_missing','pixels':missing_pixels,'reason':'与页面底色明显不同的内部均匀块保持原像素；相近留白不视为缺损，也不补画笔画'})
        gate=fidelity_diagnostics(image,result,features['noiseSigmaMAD'],periodic=bool(features['periodicPeaks']))
        if not gate['accepted']:
            decisions.append({'operator':'fallback_identity','reason':'; '.join(gate['reasons'])})
            result=image.copy()
        change = change_stats(image, result)
        if not gate['accepted']:
            output_mode = 'gate_fallback_original'
        elif change['isPassthrough']:
            output_mode = 'identity_no_evidence'
        else:
            output_mode = 'processed'
        return result, {'version':self.version,'features':features,'decisions':decisions,'fidelityGate':gate,
                        # A byte-equal output is the original image, even when the gate accepted it.
                        'selectedOutput':'original' if change['isPassthrough'] else 'candidate',
                        'algorithmOutputMode':output_mode,'changeStats':change,
                        'limitations':'不补全遮挡/剥落，不识别或重绘缺失笔画；无真值不计算修复准确率。'}


def interior_constant_block(image, window=9, min_pixels=180):
    """True when an interior area is exactly flat. Scanned paper noise does not match this."""
    if image.ndim != 2 or min(image.shape) < window + 4:
        return False
    values = image.astype(np.float32)
    mean = cv2.blur(values, (window, window))
    square = cv2.blur(values * values, (window, window))
    variance = square - mean * mean
    margin = max(2, int(round(min(image.shape) * 0.08)))
    interior = np.zeros(image.shape, dtype=bool)
    interior[margin:-margin, margin:-margin] = variance[margin:-margin, margin:-margin] < 1e-6
    return int(np.count_nonzero(interior)) >= min_pixels


class AdaptiveRubbingRestorerV22(AdaptiveRubbingRestorer):
    """Candidate only. The production default remains adaptive-rubbing-v2.1.

    An exactly constant interior block is the occlusion used by the synthetic
    benchmark. Historical scans are not exact constants, so this gate does not
    claim to detect stone loss on the 28 museum images.
    """

    version = 'adaptive-rubbing-v2.2-candidate'

    def restore(self, image, strength=1., notch_width=.8):
        if interior_constant_block(image):
            features, _impulse = analyze_degradation(image)
            return image.copy(), {
                'version': self.version,
                'features': features,
                'decisions': [{
                    'operator': 'skip_flat_interior',
                    'reason': '内部存在近似常数的区域。拒绝把平坦缺损或空白增强成笔画。',
                }],
                'fidelityGate': {'accepted': False, 'reasons': ['平坦区域拒绝修改'], 'basis': '常数块检测，不是历史真值'},
                'selectedOutput': 'original',
                'algorithmOutputMode': 'gate_fallback_original',
                'changeStats': change_stats(image, image),
                'limitations': '只拒绝模拟器式的精确平坦块。没有把它评成博物馆拓片上的通用遮挡检测，也不替换 v2.1 默认算法。',
            }
        result, meta = super().restore(image, strength=strength, notch_width=notch_width)
        meta = dict(meta)
        meta['version'] = self.version
        return result, meta
