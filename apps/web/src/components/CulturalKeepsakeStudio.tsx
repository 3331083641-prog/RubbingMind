import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Download, Stamp, Sparkles, CheckCircle2 } from 'lucide-react';
import { SteleItem } from '../types/stele';
import { getCuratorialInsight } from '../data/curatorialInsights';
import { SealStamp } from './SealStamp';

interface CulturalKeepsakeStudioProps {
  stele: SteleItem;
  rubbingImageUrl?: string;
  externalQuote?: string;
}

type KeepsakeTemplate = 'card' | 'bookmark' | 'poster';
type SealStyle = 'baiwen' | 'zhuwen';

const TEMPLATE_SPECS: Record<
  KeepsakeTemplate,
  { label: string; subtitle: string; width: number; height: number }
> = {
  card: { label: '数字碑帖藏品卡', subtitle: '玄石泥金典藏规格', width: 960, height: 1240 },
  bookmark: { label: '竖排宣纸书签', subtitle: '宿宣古籍界栏直排', width: 640, height: 1480 },
  poster: { label: '当代极简海报', subtitle: '美术馆特展视觉构图', width: 960, height: 1320 },
};

function drawSeal(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  size: number,
  text: string,
  style: SealStyle,
) {
  const chars = Array.from(text.trim() || '墨韵').slice(0, 4);
  ctx.save();
  ctx.translate(x, y);
  const r = 6;
  ctx.beginPath();
  ctx.roundRect(0, 0, size, size, r);
  if (style === 'baiwen') {
    ctx.fillStyle = '#B83222';
    ctx.fill();
    ctx.strokeStyle = '#DF6250';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = '#FAF6EE';
  } else {
    ctx.fillStyle = 'rgba(184, 50, 34, 0.06)';
    ctx.fill();
    ctx.strokeStyle = '#B83222';
    ctx.lineWidth = 4;
    ctx.stroke();
    ctx.fillStyle = '#B83222';
  }

  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  if (chars.length === 4) {
    ctx.font = `700 ${Math.round(size * 0.36)}px "Noto Serif SC", "Source Han Serif SC", serif`;
    // Traditional right-to-left seal grid
    ctx.fillText(chars[0], size * 0.72, size * 0.28);
    ctx.fillText(chars[1], size * 0.72, size * 0.72);
    ctx.fillText(chars[2], size * 0.28, size * 0.28);
    ctx.fillText(chars[3], size * 0.28, size * 0.72);
  } else if (chars.length === 2) {
    ctx.font = `700 ${Math.round(size * 0.42)}px "Noto Serif SC", "Source Han Serif SC", serif`;
    ctx.fillText(chars[0], size * 0.5, size * 0.3);
    ctx.fillText(chars[1], size * 0.5, size * 0.72);
  } else {
    ctx.font = `900 ${Math.round(size * 0.56)}px "Noto Serif SC", "Source Han Serif SC", serif`;
    ctx.fillText(chars.join(''), size * 0.5, size * 0.52);
  }
  ctx.restore();
}

function drawPaperTexture(ctx: CanvasRenderingContext2D, w: number, h: number, dark: boolean) {
  ctx.save();
  for (let i = 0; i < 420; i++) {
    const x = (Math.sin(i * 127.1) * 0.5 + 0.5) * w;
    const y = (Math.cos(i * 311.7) * 0.5 + 0.5) * h;
    const len = 8 + (i % 26);
    ctx.strokeStyle = dark ? 'rgba(229, 203, 152, 0.032)' : 'rgba(92, 72, 48, 0.045)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + len * Math.cos(i), y + len * Math.sin(i));
    ctx.stroke();
  }
  ctx.restore();
}

function drawVerticalChars(
  ctx: CanvasRenderingContext2D,
  text: string,
  startX: number,
  startY: number,
  colGap: number,
  charGap: number,
  maxPerCol: number,
) {
  const cleaned = text.trim();
  const segments = cleaned.split(/\s+/).filter(Boolean);
  let colIdx = 0;
  for (const seg of segments) {
    const chars = Array.from(seg);
    let rowIdx = 0;
    for (const ch of chars) {
      if (rowIdx >= maxPerCol) {
        rowIdx = 0;
        colIdx += 1;
      }
      ctx.fillText(ch, startX - colIdx * colGap, startY + rowIdx * charGap);
      rowIdx += 1;
    }
    colIdx += 1;
  }
}

export const CulturalKeepsakeStudio: React.FC<CulturalKeepsakeStudioProps> = ({
  stele,
  rubbingImageUrl,
  externalQuote,
}) => {
  const insight = useMemo(() => getCuratorialInsight(stele), [stele]);
  const [template, setTemplate] = useState<KeepsakeTemplate>('card');
  const [quote, setQuote] = useState<string>(insight.keepsakeQuotes[0]?.text || '金石永壽 墨韻長存');
  const [colophon, setColophon] = useState<string>(
    insight.keepsakeQuotes[0]?.colophon || `${stele.dynasty} · ${stele.title}`,
  );
  const [sealText, setSealText] = useState<string>('墨韵智考');
  const [sealStyle, setSealStyle] = useState<SealStyle>('baiwen');
  const [exportedFeedback, setExportedFeedback] = useState<string>('');
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const loadedImageRef = useRef<HTMLImageElement | null>(null);
  const [imgVersion, setImgVersion] = useState(0);

  useEffect(() => {
    setQuote(insight.keepsakeQuotes[0]?.text || '金石永壽 墨韻長存');
    setColophon(insight.keepsakeQuotes[0]?.colophon || `${stele.dynasty} · ${stele.title}`);
  }, [stele.id, insight]);

  useEffect(() => {
    if (externalQuote && externalQuote.trim()) {
      setQuote(externalQuote.trim());
    }
  }, [externalQuote]);

  const effectiveImgUrl = rubbingImageUrl || stele.imageAssets?.cover || stele.raw_image;

  useEffect(() => {
    if (!effectiveImgUrl) {
      loadedImageRef.current = null;
      setImgVersion((v) => v + 1);
      return;
    }
    let alive = true;
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      if (alive) {
        loadedImageRef.current = img;
        setImgVersion((v) => v + 1);
      }
    };
    img.onerror = () => {
      if (alive) {
        loadedImageRef.current = null;
        setImgVersion((v) => v + 1);
      }
    };
    img.src = effectiveImgUrl;
    return () => {
      alive = false;
    };
  }, [effectiveImgUrl]);

  // Real-time high-DPI Canvas Composer
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const spec = TEMPLATE_SPECS[template];
    canvas.width = spec.width;
    canvas.height = spec.height;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = spec.width;
    const h = spec.height;
    const img = loadedImageRef.current;

    if (template === 'card') {
      // 1. Obsidian & Gold Museum Specimen Card
      const bg = ctx.createLinearGradient(0, 0, w, h);
      bg.addColorStop(0, '#10141A');
      bg.addColorStop(1, '#080A0E');
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, w, h);
      drawPaperTexture(ctx, w, h, true);

      // Double museum hairline border
      ctx.strokeStyle = 'rgba(201, 166, 107, 0.45)';
      ctx.lineWidth = 2;
      ctx.strokeRect(34, 34, w - 68, h - 68);
      ctx.strokeStyle = 'rgba(201, 166, 107, 0.16)';
      ctx.lineWidth = 1;
      ctx.strokeRect(46, 46, w - 92, h - 92);

      // Header catalog band (concise left/right labels with guaranteed non-overlap)
      ctx.fillStyle = '#C9A66B';
      ctx.font = '600 18px ui-monospace, Menlo, monospace';
      ctx.textAlign = 'left';
      ctx.fillText('RUBBINGMIND · EPIGRAPHY ARCHIVE', 74, 96);
      ctx.textAlign = 'right';
      const shortDynasty = (stele.dynasty || '').split('·')[0].trim();
      const shortScript = (stele.script_type || '石刻').split('（')[0].trim();
      ctx.fillText(`${shortDynasty} · ${shortScript}`, w - 74, 96);

      // Rubbing window frame
      const frameX = 74;
      const frameY = 128;
      const frameW = w - 148;
      const frameH = 620;
      ctx.fillStyle = '#06080B';
      ctx.fillRect(frameX, frameY, frameW, frameH);
      if (img) {
        const scale = Math.min((frameW - 28) / img.naturalWidth, (frameH - 28) / img.naturalHeight);
        const dw = img.naturalWidth * scale;
        const dh = img.naturalHeight * scale;
        ctx.drawImage(img, frameX + (frameW - dw) / 2, frameY + (frameH - dh) / 2, dw, dh);
      }
      ctx.strokeStyle = 'rgba(201, 166, 107, 0.4)';
      ctx.lineWidth = 1.5;
      ctx.strokeRect(frameX, frameY, frameW, frameH);

      // Quoted inscription hero line
      ctx.fillStyle = '#F2ECE1';
      ctx.textAlign = 'left';
      ctx.font = '700 54px "Noto Serif SC", "Source Han Serif SC", serif';
      ctx.fillText(quote.slice(0, 14), 74, 836);

      // Hairline divider
      ctx.strokeStyle = 'rgba(201, 166, 107, 0.35)';
      ctx.beginPath();
      ctx.moveTo(74, 874);
      ctx.lineTo(w - 74, 874);
      ctx.stroke();

      // Provenance & Colophon block
      ctx.fillStyle = '#E5CB98';
      ctx.font = '600 28px "Noto Serif SC", "Source Han Serif SC", serif';
      ctx.fillText(`《${stele.title}》`, 74, 930);

      ctx.fillStyle = '#B7AFA2';
      ctx.font = '400 22px "Noto Serif SC", "Source Han Serif SC", serif';
      ctx.fillText(colophon.slice(0, 28), 74, 976);
      ctx.font = '400 18px ui-monospace, Menlo, monospace';
      ctx.fillStyle = '#8B867D';
      ctx.fillText(`原刻年代：${stele.originalYear || stele.year || '待考'}`, 74, 1030);
      ctx.fillText(`藏所著录：${stele.collectionInstitution || stele.museum}`, 74, 1064);
      ctx.fillText(`墨韵智考 · 数字留痕藏品卡`, 74, 1138);

      drawSeal(ctx, w - 186, 982, 108, sealText, sealStyle);
    } else if (template === 'bookmark') {
      // 2. Classic Xuan Paper Vertical Bookmark (竖排宣纸书签)
      const bg = ctx.createLinearGradient(0, 0, 0, h);
      bg.addColorStop(0, '#F7F1E5');
      bg.addColorStop(0.5, '#F2E9D8');
      bg.addColorStop(1, '#E8DEC9');
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, w, h);
      drawPaperTexture(ctx, w, h, false);

      // Top ribbon eyelet circle
      ctx.strokeStyle = '#9C7E52';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(w / 2, 62, 18, 0, Math.PI * 2);
      ctx.stroke();

      // Ancient book vertical ruling (界栏线)
      ctx.strokeStyle = 'rgba(139, 105, 60, 0.55)';
      ctx.lineWidth = 2.5;
      ctx.strokeRect(42, 106, w - 84, h - 166);
      ctx.lineWidth = 1;
      ctx.strokeStyle = 'rgba(139, 105, 60, 0.25)';
      ctx.strokeRect(52, 116, w - 104, h - 186);

      // Subtle rubbing vignette at top inside frame
      if (img) {
        ctx.save();
        ctx.beginPath();
        ctx.rect(68, 134, w - 136, 330);
        ctx.clip();
        const scale = Math.max((w - 136) / img.naturalWidth, 330 / img.naturalHeight);
        const dw = img.naturalWidth * scale;
        const dh = img.naturalHeight * scale;
        ctx.globalAlpha = 0.88;
        ctx.drawImage(img, 68 + (w - 136 - dw) / 2, 134 + (330 - dh) / 2, dw, dh);
        ctx.restore();
        ctx.strokeStyle = 'rgba(139, 105, 60, 0.45)';
        ctx.strokeRect(68, 134, w - 136, 330);
      }

      // Vertical ink column rulings
      for (let cx = 148; cx < w - 100; cx += 94) {
        ctx.strokeStyle = 'rgba(139, 105, 60, 0.16)';
        ctx.beginPath();
        ctx.moveTo(cx, 505);
        ctx.lineTo(cx, h - 110);
        ctx.stroke();
      }

      // Vertical calligraphy excerpt
      ctx.fillStyle = '#1E1915';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.font = '700 62px "Noto Serif SC", "Source Han Serif SC", serif';
      drawVerticalChars(ctx, quote, w - 142, 565, 96, 78, 8);

      // Left vertical colophon
      ctx.fillStyle = '#5C4F41';
      ctx.font = '400 24px "Noto Serif SC", "Source Han Serif SC", serif';
      drawVerticalChars(ctx, colophon.slice(0, 18), 112, 580, 34, 34, 18);

      drawSeal(ctx, 76, h - 220, 88, sealText, sealStyle);
    } else {
      // 3. Contemporary Minimalist Cultural Poster (当代极简文化海报)
      ctx.fillStyle = '#F3ECE0';
      ctx.fillRect(0, 0, w, h);
      drawPaperTexture(ctx, w, h, false);

      // Left obsidian vertical pillar accent
      ctx.fillStyle = '#12161C';
      ctx.fillRect(0, 0, 330, h);

      // Cropped high-contrast rubbing art inside dark pillar
      if (img) {
        ctx.save();
        ctx.beginPath();
        ctx.rect(36, 160, 258, 760);
        ctx.clip();
        const scale = Math.max(258 / img.naturalWidth, 760 / img.naturalHeight);
        const dw = img.naturalWidth * scale;
        const dh = img.naturalHeight * scale;
        ctx.drawImage(img, 36 + (258 - dw) / 2, 160 + (760 - dh) / 2, dw, dh);
        ctx.restore();
        ctx.strokeStyle = 'rgba(201, 166, 107, 0.55)';
        ctx.lineWidth = 1.5;
        ctx.strokeRect(36, 160, 258, 760);
      }

      ctx.fillStyle = '#C9A66B';
      ctx.font = '600 18px ui-monospace, Menlo, monospace';
      ctx.textAlign = 'left';
      ctx.fillText('EXHIBITION', 38, 84);
      ctx.fillText('EDITION', 38, 110);

      ctx.fillStyle = '#D9D2C7';
      ctx.font = '400 19px "Noto Serif SC", serif';
      ctx.fillText(stele.dynasty, 38, 990);
      ctx.fillStyle = '#8F8A82';
      ctx.font = '400 16px ui-monospace, Menlo, monospace';
      ctx.fillText(stele.originalYear || stele.year || 'EPIGRAPHY', 38, 1026);
      ctx.fillText('RUBBINGMIND STUDIO', 38, h - 56);

      // Right contemporary generous-whitespace editorial poster area
      const heroChar = Array.from(quote.replace(/\s+/g, ''))[0] || '墨';
      ctx.fillStyle = 'rgba(31, 26, 22, 0.06)';
      ctx.font = '900 420px "Noto Serif SC", "Source Han Serif SC", serif';
      ctx.textAlign = 'center';
      ctx.fillText(heroChar, 650, 520);

      ctx.fillStyle = '#1D1814';
      ctx.textAlign = 'center';
      ctx.font = '700 66px "Noto Serif SC", "Source Han Serif SC", serif';
      drawVerticalChars(ctx, quote, 780, 230, 106, 86, 7);

      // Cinnabar accent bar & metadata
      ctx.fillStyle = '#B83222';
      ctx.fillRect(390, 960, 64, 4);

      ctx.textAlign = 'left';
      ctx.fillStyle = '#1D1814';
      ctx.font = '700 32px "Noto Serif SC", serif';
      ctx.fillText(`《${stele.title}》`, 390, 1020);
      ctx.fillStyle = '#584E43';
      ctx.font = '400 22px "Noto Serif SC", serif';
      ctx.fillText(colophon.slice(0, 24), 390, 1066);
      ctx.fillStyle = '#7E7264';
      ctx.font = '400 18px sans-serif';
      ctx.fillText(`${stele.collectionInstitution || stele.museum} · 数字化美育留痕`, 390, 1112);

      drawSeal(ctx, 786, 1090, 106, sealText, sealStyle);
    }
  }, [template, quote, colophon, sealText, sealStyle, stele, imgVersion]);

  const handleExportPng = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    try {
      const dataUrl = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      const safeTitle = stele.title.replace(/[\\/:*?"<>|\s]+/g, '_').slice(0, 20);
      link.download = `墨韵智考_${TEMPLATE_SPECS[template].label}_${safeTitle}.png`;
      link.href = dataUrl;
      link.click();
      setExportedFeedback('高清 PNG 藏品已导出至本地，欢迎分享传拓之美！');
      window.setTimeout(() => setExportedFeedback(''), 4000);
    } catch {
      setExportedFeedback('导出失败：请确认浏览器允许图片下载。');
    }
  };

  return (
    <section
      aria-label="文化留痕工坊"
      data-testid="keepsake-studio"
      className="rm-book-frame rounded-2xl p-5 space-y-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--rm-border)] pb-3">
        <div className="flex items-center gap-2.5">
          <SealStamp text="留痕" variant="baiwen" size="xs" />
          <div>
            <h3 className="font-serif font-bold text-sm text-[var(--rm-gold-light)] tracking-wide">
              文化留痕 · 当代碑帖藏品与海报工坊
            </h3>
            <p className="text-[11px] text-[var(--rm-ink-muted)] font-sans">
              摘选碑文名句、定制题跋与朱印，实时渲染并导出高清 PNG 藏品图
            </p>
          </div>
        </div>
        <span className="text-[10px] rm-mono-metric px-2 py-0.5 rounded bg-[var(--rm-cinnabar-soft)] text-[var(--rm-cinnabar-bright)] border border-[var(--rm-cinnabar)]/30">
          {TEMPLATE_SPECS[template].width} × {TEMPLATE_SPECS[template].height} PNG
        </span>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
        {/* Left Controls (Col 7) */}
        <div className="xl:col-span-7 space-y-3.5 text-xs">
          {/* Template Switcher */}
          <div className="grid grid-cols-3 gap-2">
            {(Object.keys(TEMPLATE_SPECS) as KeepsakeTemplate[]).map((key) => {
              const active = template === key;
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setTemplate(key)}
                  className={`p-2.5 rounded-xl border text-left transition-all ${
                    active
                      ? 'border-[var(--rm-cinnabar)] bg-[var(--rm-cinnabar-soft)]'
                      : 'border-[var(--rm-border)] bg-[var(--rm-bg-subtle)] hover:border-[var(--rm-gold)]'
                  }`}
                >
                  <span className="font-serif font-bold block text-[var(--rm-ink-primary)]">
                    {TEMPLATE_SPECS[key].label}
                  </span>
                  <span className="text-[10px] text-[var(--rm-ink-muted)] block mt-0.5">
                    {TEMPLATE_SPECS[key].subtitle}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Preset Classical Quote Chips */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-serif text-[var(--rm-ink-muted)] block">
              快速摘选本碑名句：
            </span>
            <div className="flex flex-wrap gap-1.5">
              {insight.keepsakeQuotes.map((q) => (
                <button
                  key={q.text}
                  type="button"
                  onClick={() => {
                    setQuote(q.text);
                    setColophon(q.colophon);
                  }}
                  className="px-2.5 py-1 rounded-lg border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)] hover:border-[var(--rm-gold)] font-serif text-[11px] text-[var(--rm-ink-primary)] transition-colors"
                >
                  <Sparkles className="w-3 h-3 inline mr-1 text-[var(--rm-gold)]" />
                  {q.text}
                </button>
              ))}
            </div>
          </div>

          {/* Quote & Colophon Inputs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label className="space-y-1 block">
              <span className="text-[11px] font-serif text-[var(--rm-ink-secondary)]">主标题 / 摘录碑文</span>
              <input
                type="text"
                value={quote}
                maxLength={24}
                onChange={(e) => setQuote(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[var(--rm-bg-elevated)] border border-[var(--rm-border)] focus:border-[var(--rm-gold)] outline-none font-serif text-[var(--rm-ink-primary)]"
              />
            </label>
            <label className="space-y-1 block">
              <span className="text-[11px] font-serif text-[var(--rm-ink-secondary)]">落款题记</span>
              <input
                type="text"
                value={colophon}
                maxLength={32}
                onChange={(e) => setColophon(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[var(--rm-bg-elevated)] border border-[var(--rm-border)] focus:border-[var(--rm-gold)] outline-none font-serif text-[var(--rm-ink-primary)]"
              />
            </label>
          </div>

          {/* Seal Customization */}
          <div className="flex flex-wrap items-center gap-3 p-3 rounded-xl border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)]">
            <Stamp className="w-4 h-4 text-[var(--rm-cinnabar-bright)] shrink-0" />
            <label className="flex items-center gap-2">
              <span className="font-serif text-[var(--rm-ink-secondary)]">印文 (1-4字)</span>
              <input
                type="text"
                value={sealText}
                maxLength={4}
                onChange={(e) => setSealText(e.target.value)}
                className="w-24 px-2 py-1 rounded bg-[var(--rm-bg-elevated)] border border-[var(--rm-border)] font-serif text-center text-[var(--rm-ink-primary)]"
              />
            </label>
            <div className="flex items-center gap-1 ml-auto">
              <button
                type="button"
                onClick={() => setSealStyle('baiwen')}
                className={`px-2.5 py-1 rounded-md font-serif text-[11px] border ${
                  sealStyle === 'baiwen'
                    ? 'bg-[var(--rm-cinnabar)] text-[#faf6ee] border-[var(--rm-cinnabar)] rm-keep-light-ink'
                    : 'border-[var(--rm-border)] text-[var(--rm-ink-secondary)]'
                }`}
              >
                白文阴刻
              </button>
              <button
                type="button"
                onClick={() => setSealStyle('zhuwen')}
                className={`px-2.5 py-1 rounded-md font-serif text-[11px] border ${
                  sealStyle === 'zhuwen'
                    ? 'bg-[var(--rm-cinnabar)] text-[#faf6ee] border-[var(--rm-cinnabar)] rm-keep-light-ink'
                    : 'border-[var(--rm-border)] text-[var(--rm-ink-secondary)]'
                }`}
              >
                朱文阳刻
              </button>
            </div>
          </div>

          {/* Export CTA */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
            <button
              type="button"
              data-testid="export-keepsake-png"
              onClick={handleExportPng}
              className="px-5 py-2.5 rounded-xl bg-[var(--rm-cinnabar)] text-[#faf6ee] font-serif font-bold text-xs shadow-cinnabar-glow hover:brightness-110 active:scale-95 transition-all inline-flex items-center gap-2 rm-keep-light-ink"
            >
              <Download className="w-4 h-4" />
              <span>导出高清 PNG 藏品图</span>
            </button>
            {exportedFeedback && (
              <span className="text-[11px] text-[var(--rm-celadon-light)] font-serif inline-flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {exportedFeedback}
              </span>
            )}
          </div>
        </div>

        {/* Right Live High-DPI Preview (Col 5) */}
        <div className="xl:col-span-5 flex flex-col items-center justify-center p-3 rounded-xl border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)]">
          <canvas
            ref={canvasRef}
            data-testid="keepsake-canvas"
            className="max-h-[360px] w-auto max-w-full rounded-lg shadow-2xl border border-[var(--rm-border-strong)]"
          />
          <span className="text-[10px] text-[var(--rm-ink-muted)] font-serif mt-2">
            实时高分辨率预览 · 导出即得无水印原图
          </span>
        </div>
      </div>
    </section>
  );
};
