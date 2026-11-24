/**
 * 典藏演示态 · 前端离线视觉增强辅助器
 * 仅在后端 FastAPI 服务未连接（offline fallback）时使用，用于在静态预览环境中呈现
 * 完整的分屏对比、朱拓可视化与边缘骨架演示；前端始终显式标注「典藏演示态 · 非后端实测」。
 */

export interface OfflineDemoResult {
  restoredDataUrl: string;
  cinnabarDataUrl: string;
  skeletonDataUrl: string;
  elapsedMs: number;
}

export async function runOfflineDemoSynthesis(imageUrl: string): Promise<OfflineDemoResult> {
  const start = performance.now();
  const img = await new Promise<HTMLImageElement>((resolve, reject) => {
    const el = new Image();
    el.crossOrigin = 'anonymous';
    el.onload = () => resolve(el);
    el.onerror = () => reject(new Error('无法载入演示图像'));
    el.src = imageUrl;
  });

  const maxSide = 960;
  const scale = Math.min(1, maxSide / Math.max(img.naturalWidth || 1, img.naturalHeight || 1));
  const w = Math.max(64, Math.round((img.naturalWidth || 512) * scale));
  const h = Math.max(64, Math.round((img.naturalHeight || 512) * scale));

  const srcCanvas = document.createElement('canvas');
  srcCanvas.width = w;
  srcCanvas.height = h;
  const sctx = srcCanvas.getContext('2d');
  if (!sctx) throw new Error('Canvas 2D context unavailable');
  sctx.drawImage(img, 0, 0, w, h);

  const srcData = sctx.getImageData(0, 0, w, h);
  const data = srcData.data;

  // Compute histogram percentiles for gentle contrast restoration
  const gray = new Uint8Array(w * h);
  const hist = new Uint32Array(256);
  for (let i = 0, p = 0; i < data.length; i += 4, p += 1) {
    const g = Math.round(0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]);
    gray[p] = g;
    hist[g] += 1;
  }

  let lo = 0;
  let hi = 255;
  let acc = 0;
  const total = w * h;
  for (let b = 0; b < 256; b += 1) {
    acc += hist[b];
    if (acc >= total * 0.04) {
      lo = b;
      break;
    }
  }
  acc = 0;
  for (let b = 255; b >= 0; b -= 1) {
    acc += hist[b];
    if (acc >= total * 0.03) {
      hi = b;
      break;
    }
  }
  const span = Math.max(24, hi - lo);

  // 1. Restored gentle local-contrast + 3x3 median/denoise blend
  const restoredCanvas = document.createElement('canvas');
  restoredCanvas.width = w;
  restoredCanvas.height = h;
  const rctx = restoredCanvas.getContext('2d')!;
  const restoredImg = rctx.createImageData(w, h);
  const rBuf = restoredImg.data;

  // 2. Cinnabar rubbing visualization
  const cinnabarCanvas = document.createElement('canvas');
  cinnabarCanvas.width = w;
  cinnabarCanvas.height = h;
  const cctx = cinnabarCanvas.getContext('2d')!;
  const cinnabarImg = cctx.createImageData(w, h);
  const cBuf = cinnabarImg.data;

  // 3. Sobel edge / stroke skeleton visualization
  const skelCanvas = document.createElement('canvas');
  skelCanvas.width = w;
  skelCanvas.height = h;
  const kctx = skelCanvas.getContext('2d')!;
  const skelImg = kctx.createImageData(w, h);
  const kBuf = skelImg.data;

  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      const idx = y * w + x;
      const o = idx * 4;
      // 3x3 light smoothing to calm speckle noise while keeping strokes crisp
      let sum = gray[idx] * 4;
      let wt = 4;
      if (x > 0) { sum += gray[idx - 1]; wt += 1; }
      if (x < w - 1) { sum += gray[idx + 1]; wt += 1; }
      if (y > 0) { sum += gray[idx - w]; wt += 1; }
      if (y < h - 1) { sum += gray[idx + w]; wt += 1; }
      const smooth = sum / wt;
      const norm = Math.max(0, Math.min(1, (smooth - lo) / span));
      // Subtle S-curve to lift calligraphic strokes against stone ground
      const enhanced = Math.round(Math.pow(norm, 0.88) * 255);

      rBuf[o] = enhanced;
      rBuf[o + 1] = Math.round(enhanced * 0.985);
      rBuf[o + 2] = Math.round(enhanced * 0.95);
      rBuf[o + 3] = 255;

      // Cinnabar ink-on-Xuan rendering
      const inkWeight = 1 - enhanced / 255;
      cBuf[o] = Math.round(244 - inkWeight * 58);
      cBuf[o + 1] = Math.round(234 - inkWeight * 184);
      cBuf[o + 2] = Math.round(218 - inkWeight * 186);
      cBuf[o + 3] = 255;

      // Sobel gradient magnitude for stroke contour/skeleton preview
      let mag = 0;
      if (x > 0 && x < w - 1 && y > 0 && y < h - 1) {
        const gx =
          -gray[idx - w - 1] +
          gray[idx - w + 1] -
          2 * gray[idx - 1] +
          2 * gray[idx + 1] -
          gray[idx + w - 1] +
          gray[idx + w + 1];
        const gy =
          -gray[idx - w - 1] -
          2 * gray[idx - w] -
          gray[idx - w + 1] +
          gray[idx + w - 1] +
          2 * gray[idx + w] +
          gray[idx + w + 1];
        mag = Math.min(255, Math.round(Math.hypot(gx, gy) * 0.65));
      }
      const edge = mag > 46 ? mag : 0;
      kBuf[o] = Math.round(edge * 0.35);
      kBuf[o + 1] = Math.round(edge * 0.88);
      kBuf[o + 2] = Math.round(edge * 0.80);
      kBuf[o + 3] = 255;
    }
  }

  rctx.putImageData(restoredImg, 0, 0);
  cctx.putImageData(cinnabarImg, 0, 0);
  kctx.putImageData(skelImg, 0, 0);

  return {
    restoredDataUrl: restoredCanvas.toDataURL('image/png'),
    cinnabarDataUrl: cinnabarCanvas.toDataURL('image/png'),
    skeletonDataUrl: skelCanvas.toDataURL('image/png'),
    elapsedMs: Math.max(42, Math.round(performance.now() - start)),
  };
}
