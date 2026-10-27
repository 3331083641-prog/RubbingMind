/**
 * 同步对照视图：多幅真实图像共享缩放/拖动；滑杆对比；ROI 框选放大；|out − in| 差分热图。
 * - 图像一律 object-fit: contain，不裁字。
 * - 给了 sha 的图像在显示前做 SHA-256 核对（REPORT_DATA_SPEC §3），不一致不显示并报错。
 * - 差分只用真实像素：H = |out − in|，任一通道取最大；P99 归一化，单色色带；0 像素改动时不画热图。
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { percent } from './format';

export interface TriptychPane { key: string; label: string; src: string | null; sha?: string | null; caption?: string; tone?: 'ref' | 'input' | 'output' | 'passthrough' | 'warn'; emptyReason?: string }
export interface DiffStats { sameSize: boolean; width: number; height: number; changed: number; total: number; ratio: number; max: number; mean: number; p99: number }
interface Props {
  panes: TriptychPane[];
  /** [输入 key, 输出 key]：用于滑杆与差分。 */
  diffPair?: [string, string];
  height?: number;
  title?: React.ReactNode;
  meta?: React.ReactNode;
  onDiffStats?: (stats: DiffStats | null) => void;
  testId?: string;
  compact?: boolean;
  /** 记录已判定为原图返回（DER / 运行字段 isPassthrough=true）：不画热图（SPEC §3）。 */
  knownPassthrough?: boolean;
}
type Loaded = { status: 'loading' } | { status: 'ok'; url: string; bitmap: ImageBitmap | HTMLCanvasElement; w: number; h: number; verified: boolean | null } | { status: 'error'; message: string } | { status: 'empty'; message: string };
type View = { s: number; x: number; y: number };
type Roi = { u: number; v: number; w: number; h: number } | null;

async function sha256Hex(buf: ArrayBuffer): Promise<string | null> {
  if (typeof crypto === 'undefined' || !crypto.subtle) return null;
  const d = await crypto.subtle.digest('SHA-256', buf);
  return Array.from(new Uint8Array(d)).map(b => b.toString(16).padStart(2, '0')).join('');
}

function useLoadedImages(panes: TriptychPane[]) {
  const [loaded, setLoaded] = useState<Record<string, Loaded>>({});
  const sig = panes.map(p => `${p.key}=${p.src}|${p.sha || ''}`).join(';');
  useEffect(() => {
    let live = true; const urls: string[] = [];
    const init: Record<string, Loaded> = {};
    panes.forEach(p => { init[p.key] = p.src ? { status: 'loading' } : { status: 'empty', message: p.emptyReason || '没有图像' }; });
    setLoaded(init);
    panes.filter(p => p.src).forEach(async p => {
      try {
        const res = await fetch(p.src!);
        if (!res.ok) throw new Error(`图像读取失败（HTTP ${res.status}）`);
        const buf = await res.arrayBuffer();
        let verified: boolean | null = null;
        if (p.sha) {
          const got = await sha256Hex(buf);
          if (got == null) verified = null;
          else if (got !== p.sha.toLowerCase()) throw new Error(`SHA-256 不一致：记录 ${p.sha.slice(0, 12)}…，实际 ${got.slice(0, 12)}…；不显示该图`);
          else verified = true;
        }
        const blob = new Blob([buf], { type: res.headers.get('content-type') || 'image/png' });
        const bitmap = await createImageBitmap(blob);
        const url = URL.createObjectURL(blob); urls.push(url);
        if (live) setLoaded(prev => ({ ...prev, [p.key]: { status: 'ok', url, bitmap, w: bitmap.width, h: bitmap.height, verified } }));
      } catch (e) {
        if (live) setLoaded(prev => ({ ...prev, [p.key]: { status: 'error', message: e instanceof Error ? e.message : String(e) } }));
      }
    });
    return () => { live = false; urls.forEach(u => URL.revokeObjectURL(u)); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sig]);
  return loaded;
}

function pixels(src: ImageBitmap | HTMLCanvasElement, w: number, h: number) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const ctx = c.getContext('2d', { willReadFrequently: true })!; ctx.drawImage(src, 0, 0);
  return ctx.getImageData(0, 0, w, h).data;
}
function computeDiff(a: Extract<Loaded, { status: 'ok' }>, b: Extract<Loaded, { status: 'ok' }>): { stats: DiffStats; canvas: HTMLCanvasElement | null } {
  if (a.w !== b.w || a.h !== b.h) return { stats: { sameSize: false, width: b.w, height: b.h, changed: 0, total: 0, ratio: NaN, max: NaN, mean: NaN, p99: NaN }, canvas: null };
  const w = a.w, h = a.h, pa = pixels(a.bitmap, w, h), pb = pixels(b.bitmap, w, h);
  const total = w * h; const D = new Uint8Array(total); const hist = new Uint32Array(256);
  let changed = 0, max = 0, sum = 0;
  for (let i = 0; i < total; i++) {
    const o = i * 4;
    const d = Math.max(Math.abs(pa[o] - pb[o]), Math.abs(pa[o + 1] - pb[o + 1]), Math.abs(pa[o + 2] - pb[o + 2]));
    D[i] = d; hist[d]++; if (d > 0) changed++; if (d > max) max = d; sum += d;
  }
  let acc = 0, p99 = 0; const target = 0.99 * total;
  for (let v = 0; v < 256; v++) { acc += hist[v]; if (acc >= target) { p99 = v; break; } }
  const stats: DiffStats = { sameSize: true, width: w, height: h, changed, total, ratio: changed / total, max, mean: sum / total, p99 };
  if (changed === 0) return { stats, canvas: null };
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const ctx = c.getContext('2d')!; const img = ctx.createImageData(w, h); const norm = Math.max(1, p99);
  for (let i = 0; i < total; i++) {
    const t = Math.min(1, D[i] / norm); const o = i * 4;
    // 单色色带：深墨 #0A0D12 → 暖金 #F5D46E
    img.data[o] = 10 + t * (245 - 10); img.data[o + 1] = 13 + t * (212 - 13); img.data[o + 2] = 18 + t * (110 - 18); img.data[o + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  return { stats, canvas: c };
}

function containRect(boxW: number, boxH: number, w: number, h: number) {
  if (!w || !h || !boxW || !boxH) return { ox: 0, oy: 0, dw: boxW, dh: boxH };
  const k = Math.min(boxW / w, boxH / h); const dw = w * k, dh = h * k;
  return { ox: (boxW - dw) / 2, oy: (boxH - dh) / 2, dw, dh };
}
const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
const TONE: Record<string, string> = { ref: 'border-celadon/50', input: 'border-slate-600', output: 'border-gold/50', passthrough: 'border-cinnabar/70', warn: 'border-cinnabar/70' };

export const SyncedTriptych: React.FC<Props> = ({ panes, diffPair, height = 300, title, meta, onDiffStats, testId, compact, knownPassthrough }) => {
  const loaded = useLoadedImages(panes);
  const [view, setView] = useState<View>({ s: 1, x: 0, y: 0 });
  const [mode, setMode] = useState<'side' | 'slider'>('side');
  const [tool, setTool] = useState<'pan' | 'roi'>('pan');
  const [showDiff, setShowDiff] = useState(true);
  const [slider, setSlider] = useState(50);
  const [roi, setRoi] = useState<Roi>(null);
  const [box, setBox] = useState({ w: 0, h: height });
  const gridRef = useRef<HTMLDivElement>(null);
  const drag = useRef<{ kind: 'pan' | 'roi'; sx: number; sy: number; vx: number; vy: number; u0?: number; v0?: number; key?: string } | null>(null);

  const a = diffPair ? loaded[diffPair[0]] : undefined;
  const b = diffPair ? loaded[diffPair[1]] : undefined;
  const diff = useMemo(() => (a?.status === 'ok' && b?.status === 'ok' ? computeDiff(a, b) : null), [a, b]);
  const diffUrl = useMemo(() => (knownPassthrough ? null : diff?.canvas?.toDataURL('image/png')) || null, [diff, knownPassthrough]);
  useEffect(() => { onDiffStats?.(diff?.stats || null); }, [diff, onDiffStats]);
  useEffect(() => { setView({ s: 1, x: 0, y: 0 }); setRoi(null); }, [panes.map(p => p.src).join('|')]);

  const shown: (TriptychPane & { computed?: boolean })[] = useMemo(() => {
    const list: (TriptychPane & { computed?: boolean })[] = [...panes];
    if (diffPair && showDiff && mode === 'side') list.push({ key: '__diff', label: '差分 |输出 − 输入|', src: diffUrl, computed: true, emptyReason: knownPassthrough ? '本次未改动原图（0 像素），不画热图' : !diff ? '等待两幅图像载入' : !diff.stats.sameSize ? '两幅图尺寸不同，无法逐像素比较' : diff.stats.changed === 0 ? '本次未改动原图（0 像素），不画热图' : '' });
    return list;
  }, [panes, diffPair, showDiff, mode, diffUrl, diff]);

  // 容器尺寸
  useEffect(() => {
    const el = gridRef.current?.querySelector('[data-pane-box]') as HTMLElement | null;
    if (!el) return;
    const ro = new ResizeObserver(() => setBox({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el); setBox({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
  }, [shown.length, mode, height]);

  const clampView = useCallback((v: View): View => ({ s: v.s, x: clamp(v.x, box.w * (1 - v.s), 0), y: clamp(v.y, box.h * (1 - v.s), 0) }), [box]);

  // 滚轮缩放（需要非 passive 监听）
  useEffect(() => {
    const el = gridRef.current; if (!el) return;
    const onWheel = (e: WheelEvent) => {
      const target = (e.target as HTMLElement).closest('[data-pane-box]') as HTMLElement | null; if (!target) return;
      e.preventDefault();
      const r = target.getBoundingClientRect(); const px = e.clientX - r.left, py = e.clientY - r.top;
      setView(v => { const s = clamp(v.s * (e.deltaY < 0 ? 1.2 : 1 / 1.2), 1, 16); return clampView({ s, x: px - (px - v.x) * (s / v.s), y: py - (py - v.y) * (s / v.s) }); });
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, [clampView]);

  const toImage = (key: string, px: number, py: number) => {
    const L = loaded[key]; const w = L?.status === 'ok' ? L.w : 1, h = L?.status === 'ok' ? L.h : 1;
    const { ox, oy, dw, dh } = containRect(box.w, box.h, w, h);
    const cx = (px - view.x) / view.s, cy = (py - view.y) / view.s;
    return { u: clamp((cx - ox) / dw, 0, 1), v: clamp((cy - oy) / dh, 0, 1) };
  };
  const onPointerDown = (key: string) => (e: React.PointerEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect(); const px = e.clientX - r.left, py = e.clientY - r.top;
    e.currentTarget.setPointerCapture(e.pointerId);
    if (tool === 'roi') { const p = toImage(key, px, py); drag.current = { kind: 'roi', sx: px, sy: py, vx: 0, vy: 0, u0: p.u, v0: p.v, key }; setRoi({ u: p.u, v: p.v, w: 0, h: 0 }); }
    else drag.current = { kind: 'pan', sx: e.clientX, sy: e.clientY, vx: view.x, vy: view.y };
  };
  const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const d = drag.current; if (!d) return;
    if (d.kind === 'pan') setView(v => clampView({ s: v.s, x: d.vx + e.clientX - d.sx, y: d.vy + e.clientY - d.sy }));
    else { const r = e.currentTarget.getBoundingClientRect(); const p = toImage(d.key!, e.clientX - r.left, e.clientY - r.top); setRoi({ u: Math.min(d.u0!, p.u), v: Math.min(d.v0!, p.v), w: Math.abs(p.u - d.u0!), h: Math.abs(p.v - d.v0!) }); }
  };
  const onPointerUp = () => { const d = drag.current; drag.current = null; if (d?.kind === 'roi') setRoi(r => (r && r.w > 0.01 && r.h > 0.01 ? r : null)); };
  const zoomBy = (k: number) => setView(v => { const s = clamp(v.s * k, 1, 16); const cx = box.w / 2, cy = box.h / 2; return clampView({ s, x: cx - (cx - v.x) * (s / v.s), y: cy - (cy - v.y) * (s / v.s) }); });

  const paneBody = (p: TriptychPane & { computed?: boolean }, extra?: React.ReactNode) => {
    const L: Loaded | undefined = p.computed ? (p.src ? { status: 'ok', url: p.src, bitmap: diff!.canvas!, w: diff!.stats.width, h: diff!.stats.height, verified: null } : { status: 'empty', message: p.emptyReason || '无差分' }) : loaded[p.key];
    if (!L || L.status === 'loading') return <div className="absolute inset-0 grid place-items-center text-xs text-slate-400">图像载入与校验中…</div>;
    if (L.status === 'error') return <div role="alert" className="absolute inset-0 grid place-items-center p-3 text-xs text-cinnabar-light text-center">{L.message}</div>;
    if (L.status === 'empty') return <div className="absolute inset-0 grid place-items-center p-3 text-xs text-slate-400 text-center">{L.message}</div>;
    const { ox, oy, dw, dh } = containRect(box.w, box.h, L.w, L.h);
    return <div className="absolute inset-0 origin-top-left" style={{ transform: `translate(${view.x}px, ${view.y}px) scale(${view.s})` }}>
      <div className="absolute" style={{ left: ox, top: oy, width: dw, height: dh }}>
        <img src={L.url} alt={p.label} draggable={false} className="w-full h-full object-contain select-none" style={{ imageRendering: view.s >= 3 ? 'pixelated' : 'auto' }} />
        {extra}
        {roi && <div className="absolute border-2 border-gold pointer-events-none" style={{ left: `${roi.u * 100}%`, top: `${roi.v * 100}%`, width: `${roi.w * 100}%`, height: `${roi.h * 100}%`, borderWidth: 2 / view.s }} />}
      </div>
    </div>;
  };

  const sliderPanes = diffPair ? [panes.find(p => p.key === diffPair[0]), panes.find(p => p.key === diffPair[1])] : [];
  const canSlider = diffPair && loaded[diffPair[0]]?.status === 'ok' && loaded[diffPair[1]]?.status === 'ok';
  const btn = (active: boolean) => `px-2 py-1 rounded border text-[11px] ${active ? 'bg-gold text-slate-950 border-gold' : 'border-slate-600 text-slate-300 hover:border-gold/60'}`;

  return <section data-testid={testId} aria-label="同步对照视图" className="space-y-2">
    {(title || meta) && <div className="flex flex-wrap items-baseline justify-between gap-2">{title}<div className="text-[11px] text-slate-400">{meta}</div></div>}
    <div className="flex flex-wrap items-center gap-1.5 print:hidden" role="toolbar" aria-label="对照工具">
      <button type="button" className={btn(mode === 'side')} aria-pressed={mode === 'side'} onClick={() => setMode('side')}>并排</button>
      <button type="button" className={btn(mode === 'slider')} aria-pressed={mode === 'slider'} disabled={!canSlider} onClick={() => setMode('slider')} title={canSlider ? '' : '需要输入与输出两幅图'}>滑杆对比</button>
      <span className="w-px h-4 bg-slate-700 mx-1" />
      <button type="button" className={btn(tool === 'pan')} aria-pressed={tool === 'pan'} onClick={() => setTool('pan')}>拖动</button>
      <button type="button" className={btn(tool === 'roi')} aria-pressed={tool === 'roi'} onClick={() => setTool('roi')}>ROI 框选</button>
      <button type="button" className={btn(false)} onClick={() => zoomBy(1.5)} aria-label="放大">＋</button>
      <button type="button" className={btn(false)} onClick={() => zoomBy(1 / 1.5)} aria-label="缩小">－</button>
      <button type="button" className={btn(false)} onClick={() => { setView({ s: 1, x: 0, y: 0 }); setRoi(null); }}>复位</button>
      <span className="text-[11px] text-slate-400 ml-1">{view.s.toFixed(1)}×</span>
      {diffPair && <label className="ml-auto text-[11px] text-slate-300 flex items-center gap-1"><input type="checkbox" checked={showDiff} onChange={e => setShowDiff(e.target.checked)} />差分热图</label>}
    </div>
    {mode === 'side' || !canSlider ? (
      <div ref={gridRef} className="grid gap-2" style={{ gridTemplateColumns: `repeat(${shown.length}, minmax(0, 1fr))` }}>
        {shown.map(p => <figure key={p.key} className="min-w-0">
          <div data-pane-box onPointerDown={onPointerDown(p.key)} onPointerMove={onPointerMove} onPointerUp={onPointerUp}
            className={`relative overflow-hidden rounded-md border bg-[#05070a] touch-none ${tool === 'roi' ? 'cursor-crosshair' : 'cursor-grab'} ${TONE[p.tone || 'input']}`} style={{ height }}>
            {paneBody(p)}
          </div>
          <figcaption className={`mt-1 text-[11px] leading-snug ${p.tone === 'passthrough' || p.tone === 'warn' ? 'text-cinnabar-light' : 'text-slate-300'}`}>
            <span className="font-medium">{p.label}</span>{p.caption ? <span className="text-slate-400"> · {p.caption}</span> : null}
            {!p.computed && loaded[p.key]?.status === 'ok' && <span className="text-slate-500"> · {(loaded[p.key] as Extract<Loaded, { status: 'ok' }>).w}×{(loaded[p.key] as Extract<Loaded, { status: 'ok' }>).h}{(loaded[p.key] as Extract<Loaded, { status: 'ok' }>).verified === true ? ' · SHA 已核对' : p.sha ? ' · 浏览器无法核对 SHA' : ''}</span>}
          </figcaption>
        </figure>)}
      </div>
    ) : (
      <div ref={gridRef}>
        <figure>
          <div data-pane-box onPointerDown={onPointerDown(diffPair![1])} onPointerMove={onPointerMove} onPointerUp={onPointerUp}
            className={`relative overflow-hidden rounded-md border border-gold/40 bg-[#05070a] touch-none ${tool === 'roi' ? 'cursor-crosshair' : 'cursor-grab'}`} style={{ height: compact ? height : height + 60 }}>
            {paneBody(sliderPanes[0]!)}
            <div className="absolute inset-0" style={{ clipPath: `inset(0 ${100 - slider}% 0 0)` }}>{paneBody(sliderPanes[1]!)}</div>
            <div className="absolute top-0 bottom-0 w-px bg-gold pointer-events-none" style={{ left: `${slider}%` }} />
            <span className="absolute top-1 left-2 text-[10px] bg-black/60 px-1 rounded text-gold-light">左：{sliderPanes[1]?.label}</span>
            <span className="absolute top-1 right-2 text-[10px] bg-black/60 px-1 rounded text-slate-200">右：{sliderPanes[0]?.label}</span>
          </div>
          <input aria-label="滑杆对比位置" type="range" min={0} max={100} value={slider} onChange={e => setSlider(Number(e.target.value))} className="w-full accent-[#D4AF37]" />
          <figcaption className="text-[11px] text-slate-400">滑杆位置为屏幕分割线，左右两侧是同一位置的真实像素；缩放和拖动对两幅图同步。</figcaption>
        </figure>
      </div>
    )}
    {diff && diffPair && <p className="text-[11px] text-slate-300" data-testid="diff-stats">
      {!diff.stats.sameSize ? '两幅图尺寸不同，无法逐像素比较。' : diff.stats.changed === 0
        ? <span className="text-cinnabar-light">浏览器逐像素比较：输出与输入 0 像素不同（{diff.stats.width}×{diff.stats.height}）——未修改输入。</span>
        : <><b className="text-slate-100">改动 {percent(diff.stats.ratio)} 像素，最大差 {diff.stats.max}</b>（浏览器逐像素比较 {diff.stats.changed.toLocaleString()}/{diff.stats.total.toLocaleString()}，平均 {diff.stats.mean.toFixed(2)}）；热图 H = |输出 − 输入|，按 P99 = {diff.stats.p99} 归一化（clip(H / max(1, P99))，单色：深 = 无变化，亮 = 变化大）。{knownPassthrough && <span className="text-cinnabar-light"> 注意：记录判定为原图返回，但浏览器比较有差异，请复核。</span>}</>}
    </p>}
    {roi && <RoiStrip roi={roi} sources={[...panes.map(p => ({ label: p.label, L: loaded[p.key] })), ...(diff?.canvas ? [{ label: '差分', L: { status: 'ok', url: '', bitmap: diff.canvas, w: diff.stats.width, h: diff.stats.height, verified: null } as Loaded }] : [])]} />}
  </section>;
};

const RoiStrip: React.FC<{ roi: NonNullable<Roi>; sources: { label: string; L: Loaded | undefined }[] }> = ({ roi, sources }) => {
  const refs = useRef<(HTMLCanvasElement | null)[]>([]);
  const size = 150;
  useEffect(() => {
    sources.forEach((s, i) => {
      const c = refs.current[i]; if (!c || s.L?.status !== 'ok') return;
      const sx = Math.floor(roi.u * s.L.w), sy = Math.floor(roi.v * s.L.h);
      const sw = Math.max(1, Math.ceil(roi.w * s.L.w)), sh = Math.max(1, Math.ceil(roi.h * s.L.h));
      const k = Math.min(size / sw, size / sh); c.width = Math.round(sw * k); c.height = Math.round(sh * k);
      const ctx = c.getContext('2d')!; ctx.imageSmoothingEnabled = false; ctx.drawImage(s.L.bitmap, sx, sy, sw, sh, 0, 0, c.width, c.height);
    });
  }, [roi, sources]);
  const first = sources.find(s => s.L?.status === 'ok')?.L as Extract<Loaded, { status: 'ok' }> | undefined;
  return <div className="rounded-md border border-gold/30 bg-black/30 p-2" aria-label="ROI 局部放大">
    <p className="text-[11px] text-gold-light mb-1">ROI 局部放大（最近邻，不插值）{first ? `：x ${Math.floor(roi.u * first.w)}, y ${Math.floor(roi.v * first.h)}, ${Math.ceil(roi.w * first.w)}×${Math.ceil(roi.h * first.h)} px` : ''}</p>
    <div className="flex flex-wrap gap-3">{sources.map((s, i) => <figure key={s.label} className="text-center"><canvas ref={el => { refs.current[i] = el; }} className="bg-[#05070a] border border-slate-700" style={{ imageRendering: 'pixelated' }} /><figcaption className="text-[10px] text-slate-400 mt-0.5">{s.label}</figcaption></figure>)}</div>
  </div>;
};
