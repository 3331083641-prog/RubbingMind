import React, { useEffect, useRef } from 'react';
import { useExperience } from '../context/ExperienceContext';

interface RubbingRevealCanvasProps {
  /** Ref to the parent hero section to track pointer coordinates without blocking hit-testing */
  hostRef: React.RefObject<HTMLElement | null>;
}

interface GlyphStamp {
  char: string;
  nx: number;
  ny: number;
  size: number;
  isSeal?: boolean;
  reveal: number;
}

const INSCRIPTION_SEEDS: Omit<GlyphStamp, 'reveal'>[] = [
  { char: '大', nx: 0.08, ny: 0.19, size: 54 },
  { char: '唐', nx: 0.08, ny: 0.34, size: 52 },
  { char: '多', nx: 0.08, ny: 0.49, size: 48 },
  { char: '寶', nx: 0.08, ny: 0.64, size: 50 },
  { char: '感', nx: 0.08, ny: 0.79, size: 54 },
  { char: '君', nx: 0.19, ny: 0.24, size: 40 },
  { char: '諱', nx: 0.19, ny: 0.38, size: 38 },
  { char: '全', nx: 0.19, ny: 0.52, size: 42 },
  { char: '景', nx: 0.19, ny: 0.66, size: 38 },
  { char: '完', nx: 0.19, ny: 0.80, size: 40 },
  { char: '金', nx: 0.48, ny: 0.16, size: 46 },
  { char: '石', nx: 0.48, ny: 0.31, size: 44 },
  { char: '永', nx: 0.48, ny: 0.46, size: 42 },
  { char: '壽', nx: 0.48, ny: 0.61, size: 46 },
  { char: '墨', nx: 0.48, ny: 0.78, size: 36, isSeal: true },
  { char: '刊', nx: 0.35, ny: 0.21, size: 36 },
  { char: '石', nx: 0.35, ny: 0.37, size: 36 },
  { char: '傳', nx: 0.35, ny: 0.54, size: 38 },
  { char: '拓', nx: 0.35, ny: 0.71, size: 38 },
  { char: '印', nx: 0.28, ny: 0.84, size: 32, isSeal: true },
];

/**
 * 沉浸序章“拂尘见字 / 数字传拓”交互光墨层
 * pointer-events: none — 绝不阻挡任何按钮点击或视频背景，仅监听父容器指针移动，
 * 如执墨扑与侧光掠过碑面，令历代碑文与朱砂印记缓缓显影。
 */
export const RubbingRevealCanvas: React.FC<RubbingRevealCanvasProps> = ({ hostRef }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const { theme, prefersReducedMotion } = useExperience();
  const themeRef = useRef(theme);
  themeRef.current = theme;

  useEffect(() => {
    const host = hostRef.current;
    const canvas = canvasRef.current;
    if (!host || !canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const glyphs: GlyphStamp[] = INSCRIPTION_SEEDS.map((s) => ({ ...s, reveal: 0.08 }));
    const pointer = { x: -9999, y: -9999, active: false };
    let width = host.clientWidth || 1280;
    let height = host.clientHeight || 720;
    let rafId = 0;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      width = host.clientWidth || 1280;
      height = host.clientHeight || 720;
      canvas.width = Math.max(1, Math.round(width * dpr));
      canvas.height = Math.max(1, Math.round(height * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();

    const drawFrame = () => {
      ctx.clearRect(0, 0, width, height);
      const isXuan = themeRef.current === 'xuan';

      // Soft ink-dabber / archaeological light halo following cursor
      if (pointer.active && !prefersReducedMotion) {
        const grad = ctx.createRadialGradient(pointer.x, pointer.y, 6, pointer.x, pointer.y, 175);
        if (isXuan) {
          grad.addColorStop(0, 'rgba(178, 46, 32, 0.12)');
          grad.addColorStop(0.45, 'rgba(140, 102, 41, 0.08)');
          grad.addColorStop(1, 'rgba(140, 102, 41, 0)');
        } else {
          grad.addColorStop(0, 'rgba(229, 203, 152, 0.14)');
          grad.addColorStop(0.45, 'rgba(195, 57, 39, 0.06)');
          grad.addColorStop(1, 'rgba(201, 166, 107, 0)');
        }
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(pointer.x, pointer.y, 175, 0, Math.PI * 2);
        ctx.fill();
      }

      // Draw ancient calligraphic characters that bloom when brushed
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      for (const g of glyphs) {
        const gx = g.nx * width;
        const gy = g.ny * height;
        if (!prefersReducedMotion && pointer.active) {
          const dist = Math.hypot(pointer.x - gx, pointer.y - gy);
          if (dist < 220) {
            const boost = (1 - dist / 220) * 0.16;
            g.reveal = Math.min(0.95, g.reveal + boost);
          }
        }
        if (!prefersReducedMotion) {
          g.reveal = Math.max(0.06, g.reveal * 0.988);
        } else {
          g.reveal = 0.12;
        }

        if (g.reveal <= 0.03) continue;

        ctx.save();
        ctx.translate(gx, gy);
        if (g.isSeal) {
          const box = g.size * 0.92;
          ctx.globalAlpha = g.reveal * (isXuan ? 0.55 : 0.65);
          ctx.strokeStyle = '#c33927';
          ctx.lineWidth = 1.6;
          ctx.strokeRect(-box / 2, -box / 2, box, box);
          ctx.fillStyle = '#c33927';
          ctx.font = `700 ${Math.round(g.size * 0.62)}px "Noto Serif SC", "Source Han Serif SC", serif`;
          ctx.fillText(g.char, 0, 1);
        } else {
          ctx.globalAlpha = g.reveal * (isXuan ? 0.34 : 0.42);
          ctx.fillStyle = isXuan ? '#2e241b' : '#e5cb98';
          ctx.font = `700 ${g.size}px "Noto Serif SC", "Source Han Serif SC", serif`;
          if (!isXuan && g.reveal > 0.35) {
            ctx.shadowColor = 'rgba(201, 166, 107, 0.35)';
            ctx.shadowBlur = 12;
          }
          ctx.fillText(g.char, 0, 0);
        }
        ctx.restore();
      }
    };

    if (prefersReducedMotion) {
      drawFrame();
      const ro = new ResizeObserver(() => {
        resize();
        drawFrame();
      });
      ro.observe(host);
      return () => ro.disconnect();
    }

    const onPointerMove = (e: PointerEvent) => {
      const rect = host.getBoundingClientRect();
      pointer.x = e.clientX - rect.left;
      pointer.y = e.clientY - rect.top;
      pointer.active = true;
    };
    const onPointerLeave = () => {
      pointer.active = false;
    };

    host.addEventListener('pointermove', onPointerMove, { passive: true });
    host.addEventListener('pointerleave', onPointerLeave);
    const ro = new ResizeObserver(resize);
    ro.observe(host);

    const loop = () => {
      drawFrame();
      rafId = requestAnimationFrame(loop);
    };
    rafId = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(rafId);
      ro.disconnect();
      host.removeEventListener('pointermove', onPointerMove);
      host.removeEventListener('pointerleave', onPointerLeave);
    };
  }, [hostRef, prefersReducedMotion]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      data-testid="rubbing-reveal-canvas"
      className="absolute inset-0 w-full h-full pointer-events-none z-[5]"
    />
  );
};
