import React, { useState, useEffect, useRef } from 'react';
import { SteleItem, CharacterItem, ProcessingResult, ProcessingRun, roleText, AdaptiveDiagnostics } from '../types/stele';
import { SteleService } from '../services/api';
import type { GlyphInferenceRecord } from '../services/api';
import { GlyphInferencePanel } from '../components/GlyphInferencePanel';
import { ScholarlyCompanionPanel } from '../components/ScholarlyCompanionPanel';
import { CulturalKeepsakeStudio } from '../components/CulturalKeepsakeStudio';
import { SteleFullscreenViewer } from '../components/stele3d/SteleFullscreenViewer';
import { SealStamp } from '../components/SealStamp';
import { runOfflineDemoSynthesis } from '../utils/offlineDemoEnhance';
import { readUrlState } from '../state/urlState';
import { writeFilters } from '../components/reports/reportFilters';
import { num, signed } from '../components/reports/format';
import {
  Sliders,
  Layers,
  Sparkles,
  Check,
  Scan,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  BookOpen,
  Cpu,
  Search,
  Box,
  Radar,
  Stamp,
  Feather,
} from 'lucide-react';

interface WorkbenchPageProps {
  stele: SteleItem;
  onNavigate: (tab: string) => void;
  /** R1-6: reports the run shown in the workbench so the report page opens the same run. */
  onRunChange?: (runId: string | null) => void;
  isBackendConnected?: boolean;
}

const POETIC_STAGES = [
  { key: 'dust', label: '拂尘去噪', desc: '2D-FFT 频谱峰值检验与织纹分离' },
  { key: 'pulse', label: '寻脉识字', desc: 'Fast NLM 保边滤波与笔画骨脉提取' },
  { key: 'stroke', label: '推演残笔', desc: '保真门控评估与微痕对比度校准' },
  { key: 'meaning', label: '考据释义', desc: '关联馆藏著录与双栏碑文释读' },
];

export const WorkbenchPage: React.FC<WorkbenchPageProps> = ({
  stele,
  onNavigate,
  onRunChange,
  isBackendConnected = true,
}) => {
  // View Modes: split, side-by-side, clean, cinnabar, skeleton
  const [viewMode, setViewMode] = useState<'split' | 'side' | 'clean' | 'cinnabar' | 'skeleton'>('split');
  const [sliderPos, setSliderPos] = useState<number>(50);
  const [isLaserScanning, setIsLaserScanning] = useState<boolean>(true);
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [loupeEnabled, setLoupeEnabled] = useState<boolean>(false);
  const [loupePos, setLoupePos] = useState<{ x: number; y: number; relX: number; relY: number } | null>(null);
  const [damageOverlayEnabled, setDamageOverlayEnabled] = useState<boolean>(false);
  const [is3DModalOpen, setIs3DModalOpen] = useState<boolean>(false);
  const [isOfflineDemoResult, setIsOfflineDemoResult] = useState<boolean>(false);

  // Algorithm Parameters
  const [d0, setD0] = useState<number>(45);
  const [filterOrder, setFilterOrder] = useState<number>(2);
  const [filterType, setFilterType] = useState<'adaptive' | 'gaussian' | 'butterworth' | 'notch'>('adaptive');
  const [morphKernel, setMorphKernel] = useState<number>(3);
  const [hNlm, setHNlm] = useState<number>(10);
  const [claheClip, setClaheClip] = useState<number>(2.5);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [processingStageIdx, setProcessingStageIdx] = useState<number>(0);
  const [runs, setRuns] = useState<ProcessingRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState('');
  const [adaptiveDetails, setAdaptiveDetails] = useState<AdaptiveDiagnostics | null>(null);

  // Dynamic Image URLs & Metrics
  const [restoredImageUrl, setRestoredImageUrl] = useState<string>('');
  const [skeletonUrl, setSkeletonUrl] = useState<string>('');
  const [cinnabarUrl, setCinnabarUrl] = useState<string>('');
  const [metrics, setMetrics] = useState({
    psnr: stele.metrics?.psnr ?? null,
    ssim: stele.metrics?.ssim ?? null,
    snr_gain: stele.metrics?.snr_gain ?? null,
    glyph_completeness: stele.metrics?.glyph_completeness ?? null,
    character_accuracy: stele.metrics?.character_accuracy ?? null,
  });

  // Ancient Book, Character & Keepsake linkage states
  const [characters, setCharacters] = useState<CharacterItem[]>([]);
  const [selectedCharId, setSelectedCharId] = useState<string>('c12');
  const [adoptionSuccessMsg, setAdoptionSuccessMsg] = useState<string>('');
  const [keepsakeQuote, setKeepsakeQuote] = useState<string>('');

  // Section refs for four-fold curatorial navigation (观碑 · 复原 · 释读 · 留痕)
  const inspectRef = useRef<HTMLDivElement>(null);
  const restoreRef = useRef<HTMLDivElement>(null);
  const interpretRef = useRef<HTMLDivElement>(null);
  const keepsakeRef = useRef<HTMLDivElement>(null);

  // Slider Dragging Ref
  const sliderContainerRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef<boolean>(false);

  const sourcePreviewUrl = stele.damaged_image || stele.raw_image;

  // Fetch initial inference characters when stele changes
  useEffect(() => {
    let isMounted = true;
    SteleService.getInference(stele.id).then((data) => {
      if (isMounted && data.characters) {
        setCharacters(data.characters);
        const firstDamaged = data.characters.find((c) => c.status === 'damaged');
        if (firstDamaged) {
          setSelectedCharId(firstDamaged.id);
        } else if (data.characters[0]) {
          setSelectedCharId(data.characters[0].id);
        }
      }
    });
    SteleService.listRuns(stele.id)
      .then((items) => {
        if (isMounted) setRuns(items);
      })
      .catch(() => {
        if (isMounted) setRuns([]);
      });

    setRestoredImageUrl('');
    setSkeletonUrl('');
    setCinnabarUrl('');
    setAdoptionSuccessMsg('');
    setSelectedRunId('');
    setIsOfflineDemoResult(false);
    setMetrics({
      psnr: stele.metrics?.psnr ?? null,
      ssim: stele.metrics?.ssim ?? null,
      snr_gain: stele.metrics?.snr_gain ?? null,
      glyph_completeness: stele.metrics?.glyph_completeness ?? null,
      character_accuracy: stele.metrics?.character_accuracy ?? null,
    });

    return () => {
      isMounted = false;
    };
  }, [stele.id]);

  // Poetic 4-stage visual progress ticker while processing
  useEffect(() => {
    if (!isProcessing) {
      setProcessingStageIdx(0);
      return;
    }
    const timer = window.setInterval(() => {
      setProcessingStageIdx((prev) => (prev < POETIC_STAGES.length - 1 ? prev + 1 : prev));
    }, 360);
    return () => window.clearInterval(timer);
  }, [isProcessing]);

  // Handle Dragging Slider & Optical Loupe Tracking
  const handleSliderMove = (clientX: number) => {
    if (!sliderContainerRef.current) return;
    const rect = sliderContainerRef.current.getBoundingClientRect();
    const pos = ((clientX - rect.left) / rect.width) * 100;
    setSliderPos(Math.max(2, Math.min(98, pos)));
  };

  const handleMouseDown = () => {
    isDraggingRef.current = true;
  };
  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };
  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDraggingRef.current) handleSliderMove(e.clientX);
    if (loupeEnabled && sliderContainerRef.current) {
      const rect = sliderContainerRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      if (x >= 0 && y >= 0 && x <= rect.width && y <= rect.height) {
        setLoupePos({
          x,
          y,
          relX: (x / rect.width) * 100,
          relY: (y / rect.height) * 100,
        });
      }
    }
  };
  const handleMouseLeave = () => {
    handleMouseUp();
    setLoupePos(null);
  };
  const handleTouchMove = (e: React.TouchEvent) => {
    if (e.touches.length > 0) handleSliderMove(e.touches[0].clientX);
  };

  // Run Real Algorithm via Backend (with honest offline demo fallback when backend is unreachable)
  const handleRunAlgorithm = async () => {
    setIsProcessing(true);
    setProcessingStageIdx(0);
    setAdoptionSuccessMsg('');
    setIsOfflineDemoResult(false);

    try {
      const result: ProcessingResult = await SteleService.processStele({
        stele_id: stele.id,
        d0,
        filter_order: filterOrder,
        filter_type: filterType,
        h_nlm: hNlm,
        clahe_clip: claheClip,
        morph_kernel: morphKernel,
      });

      if (result.restored_image) setRestoredImageUrl(result.restored_image);
      if (result.skeleton_b64) setSkeletonUrl(result.skeleton_b64);
      if (result.cinnabar_b64) setCinnabarUrl(result.cinnabar_b64);

      setMetrics({
        psnr: result.psnr,
        ssim: result.ssim,
        snr_gain: result.snr_gain,
        glyph_completeness: result.glyph_completeness,
        character_accuracy: result.character_accuracy,
      });
      setSelectedRunId(result.runId);
      onRunChange?.(result.runId);
      setAdaptiveDetails(result.adaptiveDiagnostics || null);
      SteleService.listRuns(stele.id)
        .then(setRuns)
        .catch(() => setAdoptionSuccessMsg('处理已保存，但历史列表暂不可用。'));
    } catch (e) {
      if (!isBackendConnected && sourcePreviewUrl) {
        try {
          const demo = await runOfflineDemoSynthesis(sourcePreviewUrl);
          setRestoredImageUrl(demo.restoredDataUrl);
          setCinnabarUrl(demo.cinnabarDataUrl);
          setSkeletonUrl(demo.skeletonDataUrl);
          setIsOfflineDemoResult(true);
          setAdoptionSuccessMsg(
            `典藏演示态：本地前端已在 ${demo.elapsedMs} ms 内完成视觉演练预览（未连接 FastAPI 引擎，无配对评测数值）。`,
          );
        } catch {
          setAdoptionSuccessMsg('实际处理失败，请检查后端服务；没有生成模拟修复结果。');
        }
      } else {
        console.error('Algorithm execution error:', e);
        setAdoptionSuccessMsg('实际处理失败，请检查后端服务；没有生成模拟修复结果。');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  // URL hydration for runId (R1-6)
  const urlHydrated = useRef(false);
  useEffect(() => {
    if (urlHydrated.current || !runs.length) return;
    urlHydrated.current = true;
    const state = readUrlState();
    const wanted =
      state.steleId === stele.id && state.runId
        ? runs.find((item) => item.runId === state.runId)
        : undefined;
    if (wanted) restoreRun(wanted);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runs, stele.id]);

  const restoreRun = (run: ProcessingRun) => {
    setAdaptiveDetails(run.adaptiveDiagnostics || null);
    setSelectedRunId(run.runId);
    setIsOfflineDemoResult(false);
    onRunChange?.(run.runId);
    setRestoredImageUrl(run.outputImages?.restored || run.restored_image);
    setSkeletonUrl(run.outputImages?.character_skeleton || run.skeleton_b64 || '');
    setCinnabarUrl(run.outputImages?.cinnabar_rubbing || run.cinnabar_b64 || '');
    setMetrics({
      psnr: run.evaluationMetrics?.psnr ?? null,
      ssim: run.evaluationMetrics?.ssim ?? null,
      snr_gain: null,
      glyph_completeness: null,
      character_accuracy: null,
    });
    setAdoptionSuccessMsg(`已载入处理记录 ${run.runId}；无配对真值时质量指标保持未评测。`);
  };

  const removeRun = async () => {
    if (!selectedRunId || !window.confirm(`确定删除本件的单次处理记录 ${selectedRunId}？此操作会删除对应的输出文件。`)) return;
    try {
      await SteleService.deleteRun(stele.id, selectedRunId);
      setRuns((items) => items.filter((item) => item.runId !== selectedRunId));
      setSelectedRunId('');
      setRestoredImageUrl('');
      setSkeletonUrl('');
      setCinnabarUrl('');
      onRunChange?.(null);
      setAdoptionSuccessMsg('所选处理记录及输出文件已删除。');
    } catch (error) {
      setAdoptionSuccessMsg(error instanceof Error ? error.message : '删除失败');
    }
  };

  const handleGlyphDecision = (record: GlyphInferenceRecord) => {
    setCharacters((prev) =>
      prev.map((c) =>
        c.id === record.characterId
          ? {
              ...c,
              char: record.adoptedGlyph || record.originalGlyph || c.char,
              status: record.adoptedGlyph
                ? ('restored' as const)
                : ((record.originalStatus || 'damaged') as CharacterItem['status']),
            }
          : c,
      ),
    );
  };

  const handleHighlightChar = (targetChar: string) => {
    const found = characters.find((c) => c.char === targetChar);
    if (found) {
      setSelectedCharId(found.id);
      setAdoptionSuccessMsg(`已在上方竖排碑卷定位单字「${found.char}」。`);
    }
  };

  const scrollTo = (ref: React.RefObject<HTMLDivElement | null>) => {
    ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const activeChar = characters.find((c) => c.id === selectedCharId) || characters[0];

  return (
    <div className="min-h-[calc(100vh-68px)] bg-[var(--rm-bg-canvas)] text-[var(--rm-ink-primary)] p-4 lg:p-6 flex flex-col space-y-5 transition-colors duration-300">
      {/* Top Status & Curatorial Four-Stage Navigation Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-1">
        <p className="text-xs text-[var(--rm-ink-muted)]" role="status">
          {stele.isDemo
            ? '核心实验样本：预置释文仅作演示；实际推演须提交图像选区。'
            : '真实馆藏：释文依据馆方资料，残字检测与配对评测需独立进行。'}
        </p>

        {/* Four-fold Workshop Anchor Pills (观碑 · 复原 · 释读 · 留痕) */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs font-serif">
          <button
            type="button"
            onClick={() => scrollTo(inspectRef)}
            className="px-2.5 py-1 rounded-full border border-[var(--rm-border)] hover:border-[var(--rm-gold)] bg-[var(--rm-bg-surface)] text-[var(--rm-ink-secondary)] hover:text-[var(--rm-gold-light)] transition-colors"
          >
            壹 · 观碑
          </button>
          <button
            type="button"
            onClick={() => scrollTo(restoreRef)}
            className="px-2.5 py-1 rounded-full border border-[var(--rm-border)] hover:border-[var(--rm-gold)] bg-[var(--rm-bg-surface)] text-[var(--rm-ink-secondary)] hover:text-[var(--rm-gold-light)] transition-colors"
          >
            贰 · 复原
          </button>
          <button
            type="button"
            onClick={() => scrollTo(interpretRef)}
            className="px-2.5 py-1 rounded-full border border-[var(--rm-border)] hover:border-[var(--rm-celadon)] bg-[var(--rm-bg-surface)] text-[var(--rm-ink-secondary)] hover:text-[var(--rm-celadon-light)] transition-colors"
          >
            叁 · 释读
          </button>
          <button
            type="button"
            onClick={() => scrollTo(keepsakeRef)}
            className="px-2.5 py-1 rounded-full border border-[var(--rm-cinnabar)]/40 bg-[var(--rm-cinnabar-soft)] text-[var(--rm-cinnabar-bright)] hover:bg-[var(--rm-cinnabar)] hover:text-[#faf6ee] transition-colors inline-flex items-center gap-1"
          >
            <Stamp className="w-3 h-3" />
            <span>肆 · 留痕</span>
          </button>
        </div>
      </div>

      {adoptionSuccessMsg && (
        <p role="alert" className="text-xs text-[var(--rm-gold-light)] px-1 font-serif">
          {adoptionSuccessMsg}
        </p>
      )}

      {/* Header Row: Stele Title + 3D Raking Light Linkage + View Mode Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-1">
        <div className="flex items-center space-x-3">
          <SealStamp text="工坊" variant="baiwen" size="sm" />
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-lg md:text-xl font-serif font-bold text-[var(--rm-ink-primary)] tracking-wide">
                {stele.title} · 频空域微痕修复与释读工作台
              </h2>
              <span className="text-[11px] font-serif px-2 py-0.5 rounded bg-[var(--rm-gold-soft)] text-[var(--rm-gold)] border border-[var(--rm-border-strong)]">
                {stele.imageCondition || '待人工复核'}
              </span>
              {isOfflineDemoResult && (
                <span className="text-[10px] font-serif px-2 py-0.5 rounded bg-[var(--rm-cinnabar-soft)] text-[var(--rm-cinnabar-bright)] border border-[var(--rm-cinnabar)]/40">
                  典藏演示态
                </span>
              )}
            </div>
            <p className="text-xs text-[var(--rm-ink-muted)] font-sans mt-0.5">
              {stele.dynasty} · 撰文 {roleText(stele.inscriptionAuthor, stele.authorVerification)} · 书丹{' '}
              {roleText(stele.calligrapher, stele.calligrapherVerification)} · 馆藏于 {stele.museum}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* 3D Raking Light Linkage Button */}
          <button
            type="button"
            data-testid="workbench-3d-linkage"
            onClick={() => setIs3DModalOpen(true)}
            className="px-3 py-1.5 rounded-xl border border-[var(--rm-cinnabar)]/45 bg-[var(--rm-cinnabar-soft)] text-[var(--rm-cinnabar-bright)] hover:bg-[var(--rm-cinnabar)] hover:text-[#faf6ee] font-serif text-xs font-semibold transition-all inline-flex items-center gap-1.5"
            title="将当前碑拓及复原结果映射至三维石碑进行侧光掠影鉴刻"
          >
            <Box className="w-3.5 h-3.5" />
            <span>3D 侧光联动</span>
          </button>

          {/* View Mode Switching Tabs */}
          <div className="flex flex-wrap items-center gap-1 bg-[var(--rm-bg-surface)] p-1 rounded-xl border border-[var(--rm-border)] text-xs font-serif">
            {(
              [
                { key: 'split', label: '卷轴分屏' },
                { key: 'side', label: '并排比对' },
                { key: 'clean', label: '去噪母本' },
                { key: 'cinnabar', label: '朱砂朱拓' },
                { key: 'skeleton', label: '笔画骨架' },
              ] as const
            ).map((m) => {
              const active = viewMode === m.key;
              const activeBg =
                m.key === 'cinnabar'
                  ? 'bg-[var(--rm-cinnabar)] text-[#faf6ee] rm-keep-light-ink'
                  : m.key === 'skeleton'
                    ? 'bg-[var(--rm-celadon)] text-[#faf6ee] rm-keep-light-ink'
                    : 'bg-gold text-slate-950 font-bold shadow-gold-glow';
              return (
                <button
                  key={m.key}
                  type="button"
                  onClick={() => setViewMode(m.key)}
                  className={`px-2.5 py-1.5 rounded-lg transition-all ${
                    active ? activeBg : 'text-[var(--rm-ink-secondary)] hover:text-[var(--rm-ink-primary)]'
                  }`}
                >
                  {m.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Real Processing History Strip (Preserves exact heading & controls for CI) */}
      <section className="glass-panel p-4 rounded-xl border border-[var(--rm-border)] text-xs space-y-2" aria-label="处理历史">
        <h3 className="text-[var(--rm-gold-light)] font-serif font-bold">真实处理历史</h3>
        {runs.length ? (
          <>
            <label>
              选择运行记录
              <select
                aria-label="选择运行记录"
                value={selectedRunId}
                onChange={(e) => {
                  const run = runs.find((item) => item.runId === e.target.value);
                  if (run) restoreRun(run);
                  else setSelectedRunId('');
                }}
                className="ml-2 bg-[var(--rm-bg-elevated)] text-[var(--rm-ink-primary)] border border-[var(--rm-border-strong)] rounded p-1"
              >
                <option value="">选择已保存运行</option>
                {runs.map((run) => (
                  <option key={run.runId} value={run.runId}>
                    {run.runId} · {run.algorithmParameters?.filter_type || '旧版参数'}
                  </option>
                ))}
              </select>
            </label>
            {selectedRunId && (
              <button
                type="button"
                onClick={() => {
                  writeFilters({ view: 'artifact' });
                  onNavigate('reports');
                }}
                className="ml-3 text-[var(--rm-gold)] underline"
              >
                在评测报告中查看此运行
              </button>
            )}
            {selectedRunId &&
              (() => {
                const run = runs.find((item) => item.runId === selectedRunId);
                return run ? (
                  <div className="space-y-1 text-[var(--rm-ink-secondary)]">
                    <p>
                      运行 ID：{run.runId} · 算法：{run.algorithmVersion} · 耗时：{run.processing_time_ms} ms
                    </p>
                    <p>
                      保存参数：D₀ {run.algorithmParameters?.d0}；阶数 {run.algorithmParameters?.filter_order}；NLM{' '}
                      {run.algorithmParameters?.h_nlm}；CLAHE {run.algorithmParameters?.clahe_clip}。当前滑块：{d0} /{' '}
                      {filterOrder} / {hNlm} / {claheClip}。
                    </p>
                    <p>
                      配对评测：{run.evaluationStatus === 'paired_reference' ? '已有实验记录' : '未评测'}；输入 SHA-256：
                      <span className="rm-mono-metric">{run.inputImageSha256}</span>
                    </p>
                    <div className="flex gap-4 text-[var(--rm-gold)]">
                      <a href={run.outputImages?.restored || run.restored_image} download>
                        保存处理结果
                      </a>
                      <button onClick={removeRun}>删除此记录</button>
                    </div>
                  </div>
                ) : null;
              })()}
          </>
        ) : (
          <p className="text-[var(--rm-ink-muted)]">尚未执行处理。</p>
        )}
      </section>

      {/* Main 2-Column Core Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1">
        {/* LEFT COLUMN: Inspect & Restore Canvas + Parameters (Col 7) */}
        <div ref={inspectRef} className="lg:col-span-7 flex flex-col space-y-4">
          {/* Main Visual Comparison Canvas (kept dark gallery stage for accurate rubbing contrast) */}
          <div
            className="rm-dark-stage relative w-full h-[540px] rounded-2xl overflow-hidden border border-[var(--rm-border-strong)] bg-[#07090C] select-none flex flex-col shadow-[var(--rm-shadow-card)]"
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseLeave}
            onMouseMove={handleMouseMove}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleMouseUp}
          >
            {/* Top Toolbar Controls */}
            <div className="absolute top-3 left-3 right-3 z-30 flex flex-wrap items-center justify-between gap-2 pointer-events-none">
              <div className="flex flex-wrap items-center gap-1.5 pointer-events-auto">
                <button
                  type="button"
                  onClick={() => setIsLaserScanning(!isLaserScanning)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-serif border backdrop-blur-md flex items-center space-x-1.5 transition-all ${
                    isLaserScanning
                      ? 'bg-gold/20 border-gold text-gold-light'
                      : 'bg-black/70 border-slate-700 text-slate-300'
                  }`}
                >
                  <Scan className="w-3.5 h-3.5" />
                  <span>显影扫描: {isLaserScanning ? '开' : '关'}</span>
                </button>

                {/* Optical Loupe Toggle (观碑放大镜) */}
                <button
                  type="button"
                  data-testid="loupe-toggle"
                  onClick={() => setLoupeEnabled((v) => !v)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-serif border backdrop-blur-md flex items-center space-x-1 transition-all ${
                    loupeEnabled
                      ? 'bg-[#c33927] border-[#e05d44] text-[#faf6ee]'
                      : 'bg-black/70 border-slate-700 text-slate-300 hover:border-gold/50'
                  }`}
                  title="开启 2.6× 局部光学放大镜细察字口笔锋"
                >
                  <Search className="w-3.5 h-3.5" />
                  <span>局部放大镜</span>
                </button>

                {/* Damage / Confidence Overlay Toggle */}
                <button
                  type="button"
                  data-testid="damage-overlay-toggle"
                  onClick={() => setDamageOverlayEnabled((v) => !v)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-serif border backdrop-blur-md flex items-center space-x-1 transition-all ${
                    damageOverlayEnabled
                      ? 'bg-[#4a8c82] border-[#74b5aa] text-[#faf6ee]'
                      : 'bg-black/70 border-slate-700 text-slate-300 hover:border-celadon/60'
                  }`}
                  title="叠层显示低对比漫漶关注区与自适应门控监测框"
                >
                  <Radar className="w-3.5 h-3.5" />
                  <span>残损叠层</span>
                </button>
              </div>

              {/* Zoom Controls */}
              <div className="flex items-center space-x-1 bg-black/75 backdrop-blur-md border border-slate-700/80 rounded-lg p-1 pointer-events-auto text-slate-200 text-xs">
                <button onClick={() => setZoomLevel((z) => Math.max(0.8, z - 0.2))} className="p-1 hover:text-gold" title="缩小">
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <span className="px-1 rm-mono-metric text-[11px]">{(zoomLevel * 100).toFixed(0)}%</span>
                <button onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.2))} className="p-1 hover:text-gold" title="放大">
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setZoomLevel(1)}
                  className="p-1 hover:text-gold border-l border-slate-700 pl-1.5"
                  title="复位"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Canvas View Rendering */}
            <div
              ref={sliderContainerRef}
              className="relative w-full flex-1 overflow-hidden flex items-center justify-center cursor-crosshair"
            >
              {/* Poetic 4-Stage Loading Overlay */}
              {isProcessing && (
                <div className="absolute inset-0 z-40 bg-[#080a0e]/88 backdrop-blur-md flex flex-col items-center justify-center p-6 text-center space-y-5">
                  <SealStamp text="传拓" variant="baiwen" size="md" className="animate-pulse" />
                  <div className="space-y-1">
                    <p className="font-serif text-base font-bold text-[#e5cb98] tracking-widest">
                      {POETIC_STAGES[processingStageIdx]?.label} · 正在重构金石微痕
                    </p>
                    <p className="text-xs text-slate-400 font-sans">
                      {POETIC_STAGES[processingStageIdx]?.desc}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center justify-center gap-2 text-[11px] font-serif">
                    {POETIC_STAGES.map((st, idx) => (
                      <span
                        key={st.key}
                        className={`px-3 py-1 rounded-full border transition-all ${
                          idx <= processingStageIdx
                            ? 'bg-[#c33927]/25 border-[#df5440] text-[#faf6ee]'
                            : 'bg-white/5 border-white/10 text-slate-500'
                        }`}
                      >
                        {idx + 1}. {st.label}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Pending Acquisition Notice Overlay */}
              {(!stele.raw_image || stele.imageStatus === '原图待授权或待获取') && (
                <div className="absolute inset-0 z-40 bg-[#090D12]/94 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center space-y-3">
                  <div className="w-12 h-12 rounded-full bg-gold/15 border border-gold/40 flex items-center justify-center text-gold">
                    <BookOpen className="w-6 h-6" />
                  </div>
                  <div className="space-y-1.5 max-w-md">
                    <h4 className="font-serif font-bold text-white text-base">《{stele.title}》馆藏档案已建立</h4>
                    <p className="text-xs text-slate-300 leading-relaxed font-sans">
                      所属机构: <span className="text-gold font-serif font-semibold">{stele.collectionInstitution || stele.museum}</span>
                    </p>
                  </div>
                </div>
              )}

              {!restoredImageUrl && (
                <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-[#080B0F]">
                  <img
                    src={sourcePreviewUrl}
                    alt={stele.title}
                    className="w-full h-full object-contain"
                    style={{ transform: `scale(${zoomLevel})`, transition: 'transform 0.2s ease-out' }}
                  />
                  <span className="absolute bottom-3 text-xs bg-black/80 text-slate-200 px-3 py-1.5 rounded-lg border border-gold/25 font-serif">
                    当前文物输入图像 · 点击下方「执行频空域联合去噪」开启卷轴对比
                  </span>
                </div>
              )}

              {restoredImageUrl && viewMode === 'split' && (
                <div
                  className="relative w-full h-full flex items-center justify-center"
                  style={{ transform: `scale(${zoomLevel})`, transition: 'transform 0.2s ease-out' }}
                >
                  {/* Restored Layer (Right Base) */}
                  <img
                    src={restoredImageUrl}
                    alt="Restored Stele"
                    className="absolute inset-0 w-full h-full object-contain filter contrast-125"
                    onError={() => {
                      setRestoredImageUrl('');
                      setAdoptionSuccessMsg('本次处理结果加载失败，请重试实际算法。');
                    }}
                  />

                  {/* Damaged Layer (Left Curtain Overlay) */}
                  <div className="absolute inset-0 overflow-hidden" style={{ width: `${sliderPos}%` }}>
                    <img
                      src={sourcePreviewUrl}
                      alt="Damaged Stele"
                      className="absolute top-0 left-0 h-full object-contain max-w-none filter contrast-110"
                      style={{ width: sliderContainerRef.current?.clientWidth || '100%' }}
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = stele.raw_image;
                      }}
                    />
                    <div className="absolute top-12 left-4 z-20 px-2.5 py-1 rounded-md bg-black/80 border border-cinnabar/60 text-[11px] font-serif text-cinnabar-light shadow-md">
                      {stele.isDemo ? '核心实验输入 (原拓)' : '真实馆藏输入 (原拓)'}
                    </div>
                  </div>

                  {/* Right Tag */}
                  <div className="absolute top-12 right-4 z-20 px-2.5 py-1 rounded-md bg-black/80 border border-gold/60 text-[11px] font-serif text-gold-light shadow-md">
                    {isOfflineDemoResult ? '典藏演示态 · 前端预演' : '频空域修复 (After)'}
                  </div>

                  {/* Tactile Scroll Curtain Divider Bar */}
                  <div
                    className="absolute top-0 bottom-0 z-20 w-[2px] bg-gradient-to-b from-[#e5cb98] via-[#c9a66b] to-[#c33927] cursor-ew-resize shadow-[0_0_14px_rgba(201,166,107,0.75)]"
                    style={{ left: `${sliderPos}%` }}
                    onMouseDown={handleMouseDown}
                    onTouchStart={handleMouseDown}
                  >
                    <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-9 h-9 rounded-full bg-[#12161c] border-2 border-[#c9a66b] flex items-center justify-center shadow-gold-glow cursor-ew-resize text-[#e5cb98] text-xs select-none">
                      ⮜ ⮞
                    </div>
                  </div>
                </div>
              )}

              {restoredImageUrl && viewMode === 'side' && (
                <div className="w-full h-full grid grid-cols-2 gap-2 p-2" style={{ transform: `scale(${zoomLevel})` }}>
                  <div className="relative border border-cinnabar/35 rounded-xl overflow-hidden bg-black/60 flex items-center justify-center">
                    <img src={sourcePreviewUrl} alt="Damaged" className="w-full h-full object-contain" />
                    <span className="absolute top-3 left-3 px-2 py-0.5 rounded bg-black/80 text-cinnabar-light text-[11px] font-serif border border-cinnabar/40">
                      输入原拓
                    </span>
                  </div>
                  <div className="relative border border-gold/35 rounded-xl overflow-hidden bg-black/60 flex items-center justify-center">
                    <img src={restoredImageUrl} alt="Restored" className="w-full h-full object-contain" />
                    <span className="absolute top-3 right-3 px-2 py-0.5 rounded bg-black/80 text-gold-light text-[11px] font-serif border border-gold/40">
                      微痕复原
                    </span>
                  </div>
                </div>
              )}

              {restoredImageUrl && viewMode === 'clean' && (
                <div className="w-full h-full flex items-center justify-center p-2" style={{ transform: `scale(${zoomLevel})` }}>
                  <img src={restoredImageUrl} alt="Clean Restored" className="w-full h-full object-contain" />
                </div>
              )}

              {restoredImageUrl && viewMode === 'cinnabar' && (
                <div className="w-full h-full flex items-center justify-center p-2" style={{ transform: `scale(${zoomLevel})` }}>
                  <div className="relative w-full h-full flex items-center justify-center bg-[#6e170e]/25 rounded-xl">
                    <img
                      src={cinnabarUrl || restoredImageUrl}
                      alt="Cinnabar Rubbing"
                      className={`w-full h-full object-contain ${isOfflineDemoResult ? '' : 'filter invert hue-rotate-[320deg] saturate-200'}`}
                    />
                    <div className="absolute top-4 left-4 px-2.5 py-1 rounded bg-[#c33927]/85 text-[#faf6ee] font-serif text-xs">
                      算法处理结果 · 朱砂风格可视化（非历史拓本，非原刻复原）
                    </div>
                  </div>
                </div>
              )}

              {restoredImageUrl && viewMode === 'skeleton' && (
                <div className="w-full h-full flex items-center justify-center p-2" style={{ transform: `scale(${zoomLevel})` }}>
                  <div className="relative w-full h-full flex items-center justify-center bg-black/90 rounded-xl">
                    <img src={skeletonUrl || restoredImageUrl} alt="Stroke Skeleton" className="w-full h-full object-contain" />
                    <div className="absolute top-4 left-4 px-2.5 py-1 rounded bg-[#3e8e7e]/85 text-[#faf6ee] font-serif text-xs">
                      细化中轴拓扑骨架 (Medial Axis Skeleton)
                    </div>
                  </div>
                </div>
              )}

              {/* Analytical Damage & Adaptive Gate Confidence Overlay */}
              {damageOverlayEnabled && (
                <div className="absolute inset-0 z-20 pointer-events-none">
                  <div className="absolute top-[22%] left-[26%] w-28 h-24 rounded-lg border border-dashed border-[#df5440] bg-[#c33927]/15 flex items-end p-1">
                    <span className="text-[9px] rm-mono-metric bg-black/80 text-[#df5440] px-1 rounded">
                      漫漶低对比区 A · 关注
                    </span>
                  </div>
                  <div className="absolute top-[48%] left-[52%] w-32 h-24 rounded-lg border border-[#74b5aa] bg-[#4a8c82]/12 flex items-end p-1">
                    <span className="text-[9px] rm-mono-metric bg-black/80 text-[#74b5aa] px-1 rounded">
                      频域织纹监测 · 门控护边
                    </span>
                  </div>
                  <div className="absolute bottom-14 right-4 px-2.5 py-1 rounded bg-black/80 border border-celadon/45 text-[10px] font-serif text-[#74b5aa]">
                    叠层提示：此为退化监测示意框，实际残字边界请用右侧「框选残字区域」
                  </div>
                </div>
              )}

              {/* Optical Loupe Magnifier (2.6x crisp circular glass) */}
              {loupeEnabled && loupePos && (
                <div
                  aria-hidden="true"
                  className="absolute z-30 w-40 h-40 rounded-full border-2 border-[#c9a66b] shadow-[0_0_24px_rgba(0,0,0,0.85)] pointer-events-none overflow-hidden"
                  style={{
                    left: Math.max(8, Math.min((sliderContainerRef.current?.clientWidth || 600) - 168, loupePos.x - 80)),
                    top: Math.max(8, Math.min((sliderContainerRef.current?.clientHeight || 480) - 168, loupePos.y - 80)),
                    backgroundImage: `url('${
                      restoredImageUrl && (viewMode !== 'split' || loupePos.relX >= sliderPos)
                        ? viewMode === 'cinnabar' && cinnabarUrl
                          ? cinnabarUrl
                          : viewMode === 'skeleton' && skeletonUrl
                            ? skeletonUrl
                            : restoredImageUrl
                        : sourcePreviewUrl
                    }')`,
                    backgroundRepeat: 'no-repeat',
                    backgroundSize: '260%',
                    backgroundPosition: `${loupePos.relX}% ${loupePos.relY}%`,
                    backgroundColor: '#07090C',
                  }}
                >
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="w-3 h-3 border border-[#c33927]/80 rounded-full" />
                  </div>
                  <span className="absolute bottom-1.5 left-1/2 -translate-x-1/2 px-1.5 py-0.5 rounded bg-black/75 text-[9px] rm-mono-metric text-[#e5cb98]">
                    2.6× 鉴刻镜
                  </span>
                </div>
              )}

              {/* Golden Ink-Reveal Scan Line */}
              {isLaserScanning && (
                <div className="absolute left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-gold-light to-transparent shadow-[0_0_15px_#E5CB98] animate-gold-laser pointer-events-none z-20">
                  <div className="w-full h-8 bg-gradient-to-b from-gold/15 to-transparent -translate-y-full" />
                </div>
              )}
            </div>

            {/* Bottom Floating HUD Metrics Bar */}
            <div className="h-14 bg-[#0A0D11]/94 backdrop-blur-md border-t border-gold/25 px-4 flex items-center justify-between text-xs select-none">
              <div className="flex items-center space-x-4 md:space-x-6 overflow-x-auto no-scrollbar">
                <div className="flex items-baseline space-x-1.5" data-testid="wb-metric-psnr">
                  <span className="text-slate-400 font-serif text-[11px]">峰值信噪比 PSNR:</span>
                  <span className="rm-mono-metric font-bold text-gold-light text-sm">{num(metrics.psnr, 2, 'dB')}</span>
                  {metrics.snr_gain != null && Number.isFinite(metrics.snr_gain) ? (
                    <span className="text-[10px] text-celadon-light rm-mono-metric">
                      ({signed(metrics.snr_gain, 2, 'dB')})
                    </span>
                  ) : null}
                </div>

                <div className="flex items-baseline space-x-1.5" data-testid="wb-metric-ssim">
                  <span className="text-slate-400 font-serif text-[11px]">结构相似度 SSIM:</span>
                  <span className="rm-mono-metric font-bold text-gold-light text-sm">{num(metrics.ssim, 3)}</span>
                </div>

                <div className="flex items-baseline space-x-1.5" data-testid="wb-metric-glyph">
                  <span className="text-slate-400 font-serif text-[11px]">字形骨架完整度:</span>
                  <span className="rm-mono-metric font-bold text-celadon-light text-sm">
                    {num(metrics.glyph_completeness, 1, '%')}
                  </span>
                </div>

                {metrics.character_accuracy != null && Number.isFinite(metrics.character_accuracy) ? (
                  <div className="flex items-baseline space-x-1.5" data-testid="wb-metric-ocr">
                    <span className="text-slate-400 font-serif text-[11px]">字符识别率:</span>
                    <span className="rm-mono-metric font-bold text-cinnabar-light text-sm">
                      {num(metrics.character_accuracy, 1, '%')}
                    </span>
                  </div>
                ) : (
                  <div className="flex items-baseline space-x-1.5" data-testid="wb-metric-ocr-empty">
                    <span className="text-slate-500 font-serif text-[11px]">识字评测：未评测</span>
                  </div>
                )}
              </div>

              <div className="hidden sm:flex items-center space-x-2 text-[11px] text-slate-400">
                <span className="w-2 h-2 rounded-full bg-celadon-light animate-pulse" />
                <span>{isBackendConnected ? 'OpenCV 实时引擎' : '典藏演示态'}</span>
              </div>
            </div>
          </div>

          {/* Bottom Parameter Adjustments Panel (Restore Stage) */}
          <div ref={restoreRef} className="rm-book-frame p-5 rounded-2xl flex flex-col space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--rm-border)] pb-2.5">
              <div className="flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-[var(--rm-gold)]" />
                <h3 className="font-serif font-bold text-sm text-[var(--rm-gold-light)]">
                  频空域联合去噪算法参数矩阵
                </h3>
              </div>
              <span className="text-[11px] font-sans text-[var(--rm-ink-muted)]">
                2D-FFT 频域滤波 + 快速非局部均值 (Fast NLM) + CLAHE
              </span>
            </div>

            <label className="text-xs text-[var(--rm-ink-secondary)]">
              频域处理方式
              <select
                aria-label="频域处理方式"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as typeof filterType)}
                className="ml-3 rounded bg-[var(--rm-bg-elevated)] border border-[var(--rm-border-strong)] p-1.5 text-[var(--rm-gold-light)]"
              >
                <option value="adaptive">图像自适应（带保真门控）</option>
                <option value="butterworth">Butterworth 低通</option>
                <option value="gaussian">高斯低通</option>
                <option value="notch">自动陷波（仅检出周期峰时生效）</option>
              </select>
            </label>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="space-y-1.5 bg-[var(--rm-bg-subtle)] p-2.5 rounded-xl border border-[var(--rm-border)]">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[var(--rm-ink-secondary)] font-serif">截止频率 D₀ / 陷波宽度</span>
                  <span className="rm-mono-metric text-[var(--rm-gold-light)] font-bold">{d0}</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="100"
                  step="1"
                  value={d0}
                  onChange={(e) => setD0(Number(e.target.value))}
                  className="w-full accent-[#C9A66B] cursor-pointer h-1.5 bg-slate-700 rounded-lg"
                />
                <div className="flex justify-between text-[9px] text-[var(--rm-ink-muted)]">
                  <span>10</span>
                  <span>100</span>
                </div>
              </div>

              <div className="space-y-1.5 bg-[var(--rm-bg-subtle)] p-2.5 rounded-xl border border-[var(--rm-border)]">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[var(--rm-ink-secondary)] font-serif">Butterworth 滤波器阶数 n</span>
                  <span className="rm-mono-metric text-[var(--rm-gold-light)] font-bold">{filterOrder}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="5"
                  step="1"
                  value={filterOrder}
                  disabled={filterType !== 'butterworth'}
                  onChange={(e) => setFilterOrder(Number(e.target.value))}
                  className="w-full accent-[#C9A66B] cursor-pointer h-1.5 bg-slate-700 rounded-lg"
                />
                <div className="flex justify-between text-[9px] text-[var(--rm-ink-muted)]">
                  <span>1 阶 (平缓过渡)</span>
                  <span>5 阶 (陡峭截止)</span>
                </div>
              </div>

              <div className="space-y-1.5 bg-[var(--rm-bg-subtle)] p-2.5 rounded-xl border border-[var(--rm-border)]">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[var(--rm-ink-secondary)] font-serif">空域 NLM 保边去噪强度 h</span>
                  <span className="rm-mono-metric text-[var(--rm-gold-light)] font-bold">{hNlm}</span>
                </div>
                <input
                  type="range"
                  min="2"
                  max="30"
                  step="1"
                  value={hNlm}
                  onChange={(e) => setHNlm(Number(e.target.value))}
                  className="w-full accent-[#C9A66B] cursor-pointer h-1.5 bg-slate-700 rounded-lg"
                />
                <div className="flex justify-between text-[9px] text-[var(--rm-ink-muted)]">
                  <span>2 (保全微痕)</span>
                  <span>30 (重度抚平)</span>
                </div>
              </div>

              <div className="space-y-1.5 bg-[var(--rm-bg-subtle)] p-2.5 rounded-xl border border-[var(--rm-border)]">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[var(--rm-ink-secondary)] font-serif">CLAHE 对比度限幅系数</span>
                  <span className="rm-mono-metric text-[var(--rm-gold-light)] font-bold">{claheClip}</span>
                </div>
                <input
                  type="range"
                  min="1.0"
                  max="5.0"
                  step="0.1"
                  value={claheClip}
                  disabled={filterType === 'adaptive'}
                  onChange={(e) => setClaheClip(Number(e.target.value))}
                  className="w-full accent-[#C9A66B] cursor-pointer h-1.5 bg-slate-700 rounded-lg"
                />
                <div className="flex justify-between text-[9px] text-[var(--rm-ink-muted)]">
                  <span>1.0 (温和对比)</span>
                  <span>5.0 (极限凸显)</span>
                </div>
              </div>

              <label className="space-y-1.5 bg-[var(--rm-bg-subtle)] p-2.5 rounded-xl border border-[var(--rm-border)]">
                <span className="text-[var(--rm-ink-secondary)] font-serif">形态学核径：{morphKernel}</span>
                <input
                  aria-label="形态学核径"
                  disabled={filterType === 'adaptive'}
                  type="range"
                  min="1"
                  max="9"
                  step="2"
                  value={morphKernel}
                  onChange={(e) => setMorphKernel(Number(e.target.value))}
                  className="w-full accent-[#C9A66B]"
                />
              </label>
            </div>

            {filterType === 'adaptive' && (
              <p className="text-xs text-[var(--rm-ink-muted)]">
                自适应模式按输入频谱和残差选择陷波、孤立噪点处理或 NLM，也可保留原图。D₀ 控制陷波宽度，NLM 控制相对强度；CLAHE 和形态学核径仅用于固定对照模式。没有缺字补全能力。
              </p>
            )}

            <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
              <span className="text-[11px] text-[var(--rm-ink-muted)]">
                调整参数后点击执行，系统将按「拂尘去噪 → 寻脉识字 → 推演残笔 → 考据释义」链路运行
              </span>
              <button
                onClick={handleRunAlgorithm}
                disabled={isProcessing}
                className="px-6 py-2.5 rounded-xl font-serif font-bold text-xs bg-gradient-to-r from-[#c33927] to-[#9b2517] text-[#faf6ee] shadow-cinnabar-glow hover:brightness-110 active:scale-95 transition-all flex items-center space-x-2 disabled:opacity-50 rm-keep-light-ink"
              >
                {isProcessing ? (
                  <>
                    <span className="w-4 h-4 border-2 border-[#faf6ee] border-t-transparent rounded-full animate-spin" />
                    <span>{POETIC_STAGES[processingStageIdx]?.label}中…</span>
                  </>
                ) : (
                  <>
                    <Cpu className="w-4 h-4" />
                    <span>执行频空域联合去噪</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Real Glyph ROI + Vertical Xuan Scroll + Interpretive Companion (Col 5) */}
        <div ref={interpretRef} className="lg:col-span-5 flex flex-col space-y-4">
          {adaptiveDetails && (
            <details className="glass-panel p-3 text-xs rounded-xl">
              <summary className="text-[var(--rm-gold)] cursor-pointer font-serif">本次自适应决策与保真诊断</summary>
              <pre className="whitespace-pre-wrap break-all mt-2 max-h-80 overflow-auto rm-mono-metric text-[11px]">
                {JSON.stringify(adaptiveDetails, null, 2)}
              </pre>
            </details>
          )}

          <GlyphInferencePanel
            stele={stele}
            activeChar={activeChar}
            runId={selectedRunId || undefined}
            restoredUrl={restoredImageUrl}
            onDecision={handleGlyphDecision}
          />

          {/* Vertical Ancient Xuan Paper Book Text View */}
          <div className="rm-book-frame rounded-2xl p-5 flex flex-col space-y-3.5">
            <div className="flex items-center justify-between border-b border-[var(--rm-border)] pb-2.5">
              <div className="flex items-center space-x-2">
                <BookOpen className="w-4 h-4 text-[var(--rm-cinnabar-bright)]" />
                <h3 className="font-serif font-bold text-sm text-[var(--rm-gold-light)]">
                  金石古籍逐字释读卷轴 (右起竖排)
                </h3>
              </div>
              {activeChar && (
                <button
                  type="button"
                  onClick={() => {
                    setKeepsakeQuote((prev) => (prev ? `${prev} ${activeChar.char}` : activeChar.char).slice(0, 20));
                    scrollTo(keepsakeRef);
                  }}
                  className="text-[11px] font-serif text-[var(--rm-cinnabar-bright)] hover:underline inline-flex items-center gap-1"
                  title="将当前选中单字送入下方留痕工坊"
                >
                  <Feather className="w-3 h-3" />
                  <span>摘「{activeChar.char}」留痕</span>
                </button>
              )}
            </div>

            <div className="relative w-full h-[250px] rounded-xl overflow-x-auto overflow-y-hidden p-4 bg-xuan-grid border border-[#D3C3A8]/55 shadow-inner">
              <div className="h-full flex flex-row-reverse items-start justify-start gap-4 writing-vertical-rl select-none">
                {Array.from(new Set(characters.map((c) => c.col))).map((colIndex) => {
                  const colChars = characters.filter((c) => c.col === colIndex);
                  return (
                    <div
                      key={colIndex}
                      className="flex flex-col items-center justify-start gap-2 h-full border-r border-[#8B693C]/25 pr-1.5"
                    >
                      {colChars.map((charItem) => {
                        const isSelected = charItem.id === selectedCharId;
                        const isDamaged = charItem.status === 'damaged';
                        const isVariant = charItem.status === 'variant';
                        const isRestored = charItem.status === 'restored';

                        return (
                          <div
                            key={charItem.id}
                            onClick={() => {
                              setSelectedCharId(charItem.id);
                              setAdoptionSuccessMsg('');
                            }}
                            className={`relative cursor-pointer transition-all duration-200 flex items-center justify-center font-serif text-lg leading-none ${
                              isSelected ? 'scale-125 z-20 font-bold ring-2 ring-[#c33927]/70 rounded' : 'hover:scale-110'
                            }`}
                          >
                            {isDamaged && (
                              <div className="w-8 h-8 rounded border-2 border-dashed border-cinnabar bg-cinnabar/15 flex items-center justify-center text-cinnabar-dark font-black">
                                {charItem.char}
                              </div>
                            )}
                            {isRestored && (
                              <div className="w-8 h-8 rounded border border-cinnabar bg-cinnabar/20 flex items-center justify-center text-cinnabar-dark font-bold relative">
                                {charItem.char}
                                <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-cinnabar" />
                              </div>
                            )}
                            {isVariant && (
                              <div
                                className="w-8 h-8 rounded border border-celadon bg-celadon/15 flex items-center justify-center text-celadon-dark font-bold"
                                title={`异体字：本字为「${charItem.variant_of}」\n${charItem.explanation}`}
                              >
                                {charItem.char}
                              </div>
                            )}
                            {!isDamaged && !isRestored && !isVariant && (
                              <div className="w-8 h-8 flex items-center justify-center text-[#1C1814] font-medium hover:text-black">
                                {charItem.char}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex items-center justify-between text-[11px] text-[var(--rm-ink-muted)] pt-1">
              <div className="flex flex-wrap items-center gap-3">
                <span className="flex items-center space-x-1">
                  <span className="w-2.5 h-2.5 rounded border border-dashed border-cinnabar bg-cinnabar/20" />
                  <span>漫漶残字</span>
                </span>
                <span className="flex items-center space-x-1">
                  <span className="w-2.5 h-2.5 rounded border border-celadon bg-celadon/20" />
                  <span>俗异体字</span>
                </span>
                <span className="flex items-center space-x-1">
                  <span className="w-2.5 h-2.5 rounded border border-cinnabar bg-cinnabar/30" />
                  <span>已采纳修补</span>
                </span>
              </div>
            </div>
          </div>

          {/* Humanistic Bilingual Reading + AI 金石学伴 */}
          <ScholarlyCompanionPanel
            stele={stele}
            activeChar={activeChar}
            isBackendConnected={isBackendConnected}
            onHighlightChar={handleHighlightChar}
            onSendQuoteToKeepsake={(q) => {
              setKeepsakeQuote(q);
              scrollTo(keepsakeRef);
            }}
          />

          {/* Compact Demo Candidate Reference (Preserved for core samples) */}
          {activeChar && activeChar.inferred_candidates && activeChar.inferred_candidates.length > 0 && (
            <details className="glass-panel rounded-2xl border border-[var(--rm-border)] p-4 text-xs">
              <summary className="font-serif font-bold text-[var(--rm-gold-light)] cursor-pointer flex items-center justify-between">
                <span className="inline-flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-[var(--rm-gold)]" />
                  预置释文候选示例（#{activeChar.id} 「{activeChar.char}」 · DEMO ONLY）
                </span>
              </summary>
              <div className="mt-3 space-y-2">
                {activeChar.inferred_candidates.map((cand, idx) => (
                  <div key={idx} className="p-2.5 rounded-xl border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)]">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-serif font-bold text-sm text-[var(--rm-ink-primary)]">
                        {idx + 1}. 「{cand.glyph}」 · {cand.font_style}
                      </span>
                      <span className="text-[10px] rm-mono-metric text-[var(--rm-gold)]">演示排序</span>
                    </div>
                    <p className="text-[11px] text-[var(--rm-ink-secondary)]">{cand.evidence}</p>
                    <p className="text-[10px] rm-mono-metric text-[var(--rm-ink-muted)] mt-0.5">{cand.source}</p>
                  </div>
                ))}
                {adoptionSuccessMsg && (
                  <div className="p-2 rounded-lg bg-[var(--rm-celadon-soft)] text-[var(--rm-celadon-light)] flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5" />
                    <span>{adoptionSuccessMsg}</span>
                  </div>
                )}
              </div>
            </details>
          )}
        </div>
      </div>

      {/* Stage 4: Cultural Keepsake & Poster Export Studio (文化留痕工坊) */}
      <div ref={keepsakeRef}>
        <CulturalKeepsakeStudio
          stele={stele}
          rubbingImageUrl={restoredImageUrl || sourcePreviewUrl}
          externalQuote={keepsakeQuote}
        />
      </div>

      {/* Synchronized 3D Raking Light Inspection Modal */}
      <SteleFullscreenViewer
        isOpen={is3DModalOpen}
        onClose={() => setIs3DModalOpen(false)}
        customRubbingUrl={sourcePreviewUrl}
        restoredRubbingUrl={restoredImageUrl || undefined}
        steleTitle={`${stele.title} · 三维侧光掠影联动鉴刻`}
      />
    </div>
  );
};
