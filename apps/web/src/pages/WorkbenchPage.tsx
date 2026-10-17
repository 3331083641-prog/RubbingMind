import React, { useState, useEffect, useRef } from 'react';
import { SteleItem, CharacterItem, ProcessingResult, ProcessingRun } from '../types/stele';
import { SteleService } from '../services/api';
import type { GlyphInferenceRecord } from '../services/api';
import { GlyphInferencePanel } from '../components/GlyphInferencePanel';
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
  Flame, 
  Info, 
  Cpu, 
  ShieldCheck, 
  Activity,
  Maximize2
} from 'lucide-react';

interface WorkbenchPageProps {
  stele: SteleItem;
  onNavigate: (tab: string) => void;
}

export const WorkbenchPage: React.FC<WorkbenchPageProps> = ({ stele, onNavigate }) => {
  // View Modes: split, side-by-side, clean, cinnabar, skeleton
  const [viewMode, setViewMode] = useState<'split' | 'side' | 'clean' | 'cinnabar' | 'skeleton'>('split');
  const [sliderPos, setSliderPos] = useState<number>(50);
  const [isLaserScanning, setIsLaserScanning] = useState<boolean>(true);
  const [zoomLevel, setZoomLevel] = useState<number>(1);

  // Algorithm Parameters
  const [d0, setD0] = useState<number>(45);
  const [filterOrder, setFilterOrder] = useState<number>(2);
  const [filterType, setFilterType] = useState<'adaptive' | 'gaussian' | 'butterworth' | 'notch'>('adaptive');
  const [morphKernel, setMorphKernel] = useState<number>(3);
  const [hNlm, setHNlm] = useState<number>(10);
  const [claheClip, setClaheClip] = useState<number>(2.5);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [runs, setRuns] = useState<ProcessingRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState('');
  const [adaptiveDetails,setAdaptiveDetails]=useState<Record<string,unknown>|null>(null);

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

  // Ancient Book & Character States
  const [characters, setCharacters] = useState<CharacterItem[]>([]);
  const [selectedCharId, setSelectedCharId] = useState<string>('c12'); // default to '感'
  const [adoptionSuccessMsg, setAdoptionSuccessMsg] = useState<string>('');

  // Slider Dragging Ref
  const sliderContainerRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef<boolean>(false);

  // Fetch initial inference characters when stele changes
  useEffect(() => {
    let isMounted = true;
    SteleService.getInference(stele.id).then((data) => {
      if (isMounted && data.characters) {
        setCharacters(data.characters);
        const firstDamaged = data.characters.find(c => c.status === 'damaged');
        if (firstDamaged) {
          setSelectedCharId(firstDamaged.id);
        }
      }
    });
    SteleService.listRuns(stele.id).then(items => { if (isMounted) setRuns(items); }).catch(() => { if (isMounted) setRuns([]); });

    // Reset parameters to stele defaults
    setRestoredImageUrl(''); setSkeletonUrl(''); setCinnabarUrl(''); setAdoptionSuccessMsg('');
    setSelectedRunId('');
    setMetrics({
      psnr: stele.metrics?.psnr ?? null,
      ssim: stele.metrics?.ssim ?? null,
      snr_gain: stele.metrics?.snr_gain ?? null,
      glyph_completeness: stele.metrics?.glyph_completeness ?? null,
      character_accuracy: stele.metrics?.character_accuracy ?? null,
    });

    return () => { isMounted = false; };
  }, [stele.id]);

  // Handle Dragging Slider
  const handleSliderMove = (clientX: number) => {
    if (!sliderContainerRef.current) return;
    const rect = sliderContainerRef.current.getBoundingClientRect();
    const pos = ((clientX - rect.left) / rect.width) * 100;
    setSliderPos(Math.max(2, Math.min(98, pos)));
  };

  const handleMouseDown = () => { isDraggingRef.current = true; };
  const handleMouseUp = () => { isDraggingRef.current = false; };
  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDraggingRef.current) handleSliderMove(e.clientX);
  };
  const handleTouchMove = (e: React.TouchEvent) => {
    if (e.touches.length > 0) handleSliderMove(e.touches[0].clientX);
  };

  // Run Real Algorithm via Backend
  const handleRunAlgorithm = async () => {
    setIsProcessing(true);
    setAdoptionSuccessMsg('');
    try {
      const result: ProcessingResult = await SteleService.processStele({
        stele_id: stele.id,
        d0,
        filter_order: filterOrder,
        filter_type: filterType,
        h_nlm: hNlm,
        clahe_clip: claheClip,
        morph_kernel: morphKernel
      });

      if (result.restored_image) {
        setRestoredImageUrl(result.restored_image);
      }
      if (result.skeleton_b64) {
        setSkeletonUrl(result.skeleton_b64);
      }
      if (result.cinnabar_b64) {
        setCinnabarUrl(result.cinnabar_b64);
      }

      setMetrics({
        psnr: result.psnr,
        ssim: result.ssim,
        snr_gain: result.snr_gain,
        glyph_completeness: result.glyph_completeness,
        character_accuracy: result.character_accuracy
      });
      setSelectedRunId(result.runId);
      setAdaptiveDetails(result.adaptiveDiagnostics||null);
      SteleService.listRuns(stele.id).then(setRuns).catch(() => setAdoptionSuccessMsg('处理已保存，但历史列表暂不可用。'));
    } catch (e) {
      console.error('Algorithm execution error:', e);
      setAdoptionSuccessMsg('实际处理失败，请检查后端服务；没有生成模拟修复结果。');
    } finally {
      setIsProcessing(false);
    }
  };

  const restoreRun = (run: ProcessingRun) => {
    setAdaptiveDetails(run.adaptiveDiagnostics||null);
    setSelectedRunId(run.runId);
    setRestoredImageUrl(run.outputImages?.restored || run.restored_image);
    setSkeletonUrl(run.outputImages?.character_skeleton || run.skeleton_b64 || '');
    setCinnabarUrl(run.outputImages?.cinnabar_rubbing || run.cinnabar_b64 || '');
    setMetrics({psnr:run.evaluationMetrics?.psnr ?? null,ssim:run.evaluationMetrics?.ssim ?? null,
      snr_gain:null,glyph_completeness:null,character_accuracy:null});
    setAdoptionSuccessMsg(`已载入处理记录 ${run.runId}；无配对真值时质量指标保持未评测。`);
  };

  const removeRun = async () => {
    if (!selectedRunId || !window.confirm(`确定删除本件的单次处理记录 ${selectedRunId}？此操作会删除对应的输出文件。`)) return;
    try {
      await SteleService.deleteRun(stele.id, selectedRunId);
      setRuns(items => items.filter(item => item.runId !== selectedRunId));
      setSelectedRunId(''); setRestoredImageUrl(''); setSkeletonUrl(''); setCinnabarUrl('');
      setAdoptionSuccessMsg('所选处理记录及输出文件已删除。');
    } catch (error) { setAdoptionSuccessMsg(error instanceof Error?error.message:'删除失败'); }
  };

  // Update the displayed transcription only after a durable human decision.
  const handleGlyphDecision = (record: GlyphInferenceRecord) => {
    setCharacters((prev) =>
      prev.map((c) =>
        c.id === record.characterId
          ? { ...c, char: record.adoptedGlyph || record.originalGlyph || c.char,
              status: record.adoptedGlyph ? 'restored' as const : (record.originalStatus || 'damaged') as CharacterItem['status'] }
          : c
      )
    );
  };

  // Currently selected character
  const activeChar = characters.find((c) => c.id === selectedCharId) || characters[0];

  return (
    <div className="min-h-[calc(100vh-68px)] bg-[#0A0D12] text-slate-100 p-4 lg:p-6 flex flex-col space-y-4">
      {/* Top Breadcrumb & Quick Stele Info Banner */}
      <p className="text-xs text-slate-400" role="status">{stele.isDemo ? '核心实验样本：预置释文仅作演示；实际推演须提交图像选区。' : '真实馆藏：释文依据馆方资料，残字检测与配对评测需独立进行。'}</p>
      {adoptionSuccessMsg && <p role="alert" className="text-xs text-gold">{adoptionSuccessMsg}</p>}
      <div className="flex flex-wrap items-center justify-between gap-3 px-2">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-cinnabar/20 border border-cinnabar/40 flex items-center justify-center text-cinnabar">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-serif font-bold text-white tracking-wide">
                {stele.title} · 频空域微痕修复与释读工作台
              </h2>
              <span className="text-[11px] font-serif px-2 py-0.5 rounded bg-gold/15 text-gold border border-gold/30">
                {stele.weathering_level}
              </span>
            </div>
            <p className="text-xs text-slate-400 font-sans mt-0.5">
              {stele.dynasty} · {stele.author} · {stele.dimensions} · 馆藏于 {stele.museum}
            </p>
          </div>
        </div>

        {/* View Mode Switching Tabs */}
        <div className="flex items-center space-x-1.5 bg-xuan-panel p-1 rounded-xl border border-gold/20 text-xs font-serif">
          <button
            onClick={() => setViewMode('split')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              viewMode === 'split' ? 'bg-gold text-slate-950 font-bold shadow-gold-glow' : 'text-slate-300 hover:text-white'
            }`}
          >
            左右拉杆对比
          </button>
          <button
            onClick={() => setViewMode('side')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              viewMode === 'side' ? 'bg-gold text-slate-950 font-bold shadow-gold-glow' : 'text-slate-300 hover:text-white'
            }`}
          >
            并排比对
          </button>
          <button
            onClick={() => setViewMode('clean')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              viewMode === 'clean' ? 'bg-gold text-slate-950 font-bold shadow-gold-glow' : 'text-slate-300 hover:text-white'
            }`}
          >
            去噪母本
          </button>
          <button
            onClick={() => setViewMode('cinnabar')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              viewMode === 'cinnabar' ? 'bg-cinnabar text-white font-bold shadow-cinnabar-glow' : 'text-slate-300 hover:text-white'
            }`}
          >
            朱砂朱拓
          </button>
          <button
            onClick={() => setViewMode('skeleton')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              viewMode === 'skeleton' ? 'bg-celadon text-white font-bold shadow-celadon-glow' : 'text-slate-300 hover:text-white'
            }`}
          >
            笔画拓扑骨架
          </button>
        </div>
      </div>

      <section className="glass-panel p-4 rounded-xl border border-gold/20 text-xs space-y-2" aria-label="处理历史">
        <h3 className="text-gold font-serif font-bold">真实处理历史</h3>
        {runs.length ? <>
          <label>选择运行记录
            <select aria-label="选择运行记录" value={selectedRunId} onChange={e => { const run=runs.find(item=>item.runId===e.target.value); if(run) restoreRun(run); else setSelectedRunId(''); }} className="ml-2 bg-slate-900 text-slate-200 border border-slate-700 rounded p-1">
              <option value="">选择已保存运行</option>
              {runs.map(run=><option key={run.runId} value={run.runId}>{run.runId} · {run.algorithmParameters?.filter_type || '旧版参数'}</option>)}
            </select>
          </label>
          {selectedRunId && (() => { const run=runs.find(item=>item.runId===selectedRunId); return run ? <div className="space-y-1 text-slate-300">
            <p>运行 ID：{run.runId} · 算法：{run.algorithmVersion} · 耗时：{run.processing_time_ms} ms</p>
            <p>保存参数：D₀ {run.algorithmParameters?.d0}；阶数 {run.algorithmParameters?.filter_order}；NLM {run.algorithmParameters?.h_nlm}；CLAHE {run.algorithmParameters?.clahe_clip}。当前滑块：{d0} / {filterOrder} / {hNlm} / {claheClip}。</p>
            <p>配对评测：{run.evaluationStatus==='paired_reference'?'已有实验记录':'未评测'}；输入 SHA-256：{run.inputImageSha256}</p>
            <div className="flex gap-4 text-gold"><a href={run.outputImages?.restored || run.restored_image} download>保存处理结果</a><button onClick={removeRun}>删除此记录</button></div>
          </div> : null; })()}
        </> : <p className="text-slate-400">尚未执行处理。</p>}
      </section>

      {/* Main 2-Column Core Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1">
        {/* ========================================================= */}
        {/* LEFT COLUMN: Image Processing Canvas & Parameters (Col 7 - 58%) */}
        {/* ========================================================= */}
        <div className="lg:col-span-7 flex flex-col space-y-4">
          {/* Main Visual Comparison Canvas */}
          <div 
            className="relative w-full h-[540px] rounded-2xl overflow-hidden glass-panel border border-gold/30 bg-[#07090C] select-none flex flex-col"
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onMouseMove={handleMouseMove}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleMouseUp}
          >
            {/* Top Toolbar Controls */}
            <div className="absolute top-3 left-3 right-3 z-30 flex items-center justify-between pointer-events-none">
              <div className="flex items-center space-x-2 pointer-events-auto">
                <button
                  onClick={() => setIsLaserScanning(!isLaserScanning)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-serif border backdrop-blur-md flex items-center space-x-1.5 transition-all ${
                    isLaserScanning 
                      ? 'bg-gold/20 border-gold text-gold-light shadow-gold-glow' 
                      : 'bg-black/60 border-slate-700 text-slate-400'
                  }`}
                >
                  <Scan className="w-3.5 h-3.5" />
                  <span>黄金激光扫描线: {isLaserScanning ? '开' : '关'}</span>
                </button>
              </div>

              {/* Zoom Controls */}
              <div className="flex items-center space-x-1 bg-black/70 backdrop-blur-md border border-slate-700/80 rounded-lg p-1 pointer-events-auto text-slate-300 text-xs">
                <button
                  onClick={() => setZoomLevel((z) => Math.max(0.8, z - 0.2))}
                  className="p-1 hover:text-gold"
                  title="缩小"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <span className="px-1 font-mono text-[11px]">{(zoomLevel * 100).toFixed(0)}%</span>
                <button
                  onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.2))}
                  className="p-1 hover:text-gold"
                  title="放大"
                >
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
              {/* Pending Acquisition Notice Overlay */}
              {(!stele.raw_image || stele.imageStatus === '原图待授权或待获取') && (
                <div className="absolute inset-0 z-40 bg-[#090D12]/94 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center space-y-3">
                  <div className="w-12 h-12 rounded-full bg-gold/15 border border-gold/40 flex items-center justify-center text-gold shadow-gold-glow">
                    <BookOpen className="w-6 h-6" />
                  </div>
                  <div className="space-y-1.5 max-w-md">
                    <h4 className="font-serif font-bold text-white text-base">《{stele.title}》馆藏档案已建立</h4>
                    <p className="text-xs text-slate-300 leading-relaxed font-sans">
                      所属机构: <span className="text-gold font-serif font-semibold">{stele.collectionInstitution || stele.museum}</span> ({stele.collectionNumber || '馆藏著录'})
                    </p>
                    <p className="text-xs text-slate-400 leading-relaxed font-sans pt-1">
                      此通碑拓为真实馆藏著录，原始高清扫描影像依开放授权流程待获取。您可查阅右侧的金石释文与多模态推演候选，或在顶部切换其他已有高清母本的碑拓进行微痕去噪实验。
                    </p>
                  </div>
                  {stele.sourceUrl && (
                    <a
                      href={stele.sourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-1.5 rounded-lg text-xs font-serif bg-gold/15 text-gold border border-gold/40 hover:bg-gold hover:text-slate-950 transition-all inline-flex items-center gap-1.5 shadow-md"
                    >
                      <span>访问官方数字馆藏来源 ↗</span>
                    </a>
                  )}
                </div>
              )}

              {!restoredImageUrl && <div className="absolute inset-0 z-30 flex flex-col items-center justify-center bg-[#090D12]"><img src={stele.damaged_image || stele.raw_image} alt={stele.title} className="w-full h-full object-contain" /><span className="absolute bottom-3 text-xs bg-black/80 p-2">当前文物输入图像 · 尚未生成算法修复结果</span></div>}
              {viewMode === 'split' && (
                <div 
                  className="relative w-full h-full flex items-center justify-center"
                  style={{ transform: `scale(${zoomLevel})`, transition: 'transform 0.2s ease-out' }}
                >
                  {/* Restored Layer (Right Base) */}
                  <img
                    src={restoredImageUrl || undefined}
                    alt="Restored Stele"
                    className="absolute inset-0 w-full h-full object-contain filter contrast-125"
                    onError={() => { setRestoredImageUrl(''); setAdoptionSuccessMsg('本次处理结果加载失败，请重试实际算法。'); }}
                  />

                  {/* Damaged Layer (Left Overlay with Clip Path) */}
                  <div
                    className="absolute inset-0 overflow-hidden"
                    style={{ width: `${sliderPos}%` }}
                  >
                    <img
                      src={stele.damaged_image || stele.raw_image}
                      alt="Damaged Stele"
                      className="absolute top-0 left-0 h-full object-contain max-w-none filter contrast-110"
                      style={{ width: sliderContainerRef.current?.clientWidth || '100%' }}
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = stele.raw_image;
                      }}
                    />
                    {/* Left Tag */}
                    <div className="absolute top-12 left-4 z-20 px-2.5 py-1 rounded-md bg-black/75 border border-cinnabar/60 text-[11px] font-serif text-cinnabar-light shadow-md">
                      {stele.isDemo ? '核心实验输入 (Before)' : '真实馆藏输入 (Before)'}
                    </div>
                  </div>

                  {/* Right Tag */}
                  <div className="absolute top-12 right-4 z-20 px-2.5 py-1 rounded-md bg-black/75 border border-gold/60 text-[11px] font-serif text-gold-light shadow-md">
                    频空域修复 (After)
                  </div>

                  {/* Draggable Vertical Divider Bar */}
                  <div
                    className="absolute top-0 bottom-0 z-20 w-1 bg-gradient-to-b from-gold-light via-gold to-gold-dark cursor-ew-resize shadow-[0_0_12px_#D4AF37]"
                    style={{ left: `${sliderPos}%` }}
                    onMouseDown={handleMouseDown}
                    onTouchStart={handleMouseDown}
                  >
                    {/* Golden Handle Center Knob */}
                    <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-slate-950 border-2 border-gold flex items-center justify-center shadow-gold-glow cursor-ew-resize text-gold text-xs select-none">
                      ⮜ ⮞
                    </div>
                  </div>
                </div>
              )}

              {viewMode === 'side' && (
                <div 
                  className="w-full h-full grid grid-cols-2 gap-2 p-2"
                  style={{ transform: `scale(${zoomLevel})` }}
                >
                  <div className="relative border border-cinnabar/30 rounded-xl overflow-hidden bg-black/60 flex items-center justify-center">
                    <img src={stele.damaged_image || stele.raw_image} alt="Damaged" className="w-full h-full object-contain" />
                    <span className="absolute top-3 left-3 px-2 py-0.5 rounded bg-black/80 text-cinnabar text-[11px] font-serif border border-cinnabar/40">
                      输入图像
                    </span>
                  </div>
                  <div className="relative border border-gold/30 rounded-xl overflow-hidden bg-black/60 flex items-center justify-center">
                    <img src={restoredImageUrl || undefined} alt="Restored" className="w-full h-full object-contain" />
                    <span className="absolute top-3 right-3 px-2 py-0.5 rounded bg-black/80 text-gold text-[11px] font-serif border border-gold/40">
                      修复后
                    </span>
                  </div>
                </div>
              )}

              {viewMode === 'clean' && (
                <div className="w-full h-full flex items-center justify-center p-2" style={{ transform: `scale(${zoomLevel})` }}>
                  <img src={restoredImageUrl || undefined} alt="Clean Restored" className="w-full h-full object-contain" />
                </div>
              )}

              {viewMode === 'cinnabar' && (
                <div className="w-full h-full flex items-center justify-center p-2" style={{ transform: `scale(${zoomLevel})` }}>
                  <div className="relative w-full h-full flex items-center justify-center bg-[#8B1A10]/20 rounded-xl">
                    <img 
                      src={cinnabarUrl || undefined}
                      alt="Cinnabar Rubbing" 
                      className="w-full h-full object-contain filter invert hue-rotate-[320deg] saturate-200" 
                    />
                    <div className="absolute top-4 left-4 px-2.5 py-1 rounded bg-cinnabar/80 text-white font-serif text-xs">
                      实际算法输出 · 朱砂风格可视化（非历史拓本）
                    </div>
                  </div>
                </div>
              )}

              {viewMode === 'skeleton' && (
                <div className="w-full h-full flex items-center justify-center p-2" style={{ transform: `scale(${zoomLevel})` }}>
                  <div className="relative w-full h-full flex items-center justify-center bg-black/90 rounded-xl">
                    <img src={skeletonUrl || undefined} alt="Stroke Skeleton" className="w-full h-full object-contain" />
                    <div className="absolute top-4 left-4 px-2.5 py-1 rounded bg-celadon/80 text-white font-serif text-xs">
                      细化中轴拓扑骨架 (Medial Axis Skeleton)
                    </div>
                  </div>
                </div>
              )}

              {/* Semi-transparent Golden Laser Scanning Line */}
              {isLaserScanning && (
                <div className="absolute left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-gold-light to-transparent shadow-[0_0_15px_#F5D46E] animate-gold-laser pointer-events-none z-20">
                  <div className="w-full h-8 bg-gradient-to-b from-gold/15 to-transparent -translate-y-full" />
                </div>
              )}
            </div>

            {/* Bottom Floating HUD Metrics Bar (Single Row) */}
            <div className="h-14 bg-[#0A0D11]/90 backdrop-blur-md border-t border-gold/25 px-4 flex items-center justify-between text-xs select-none">
              <div className="flex items-center space-x-4 md:space-x-6 overflow-x-auto no-scrollbar">
                <div className="flex items-baseline space-x-1.5">
                  <span className="text-slate-400 font-serif text-[11px]">峰值信噪比 PSNR:</span>
                  <span className="font-mono font-bold text-gold-light text-sm">{metrics.psnr ?? '未评测'} dB</span>
                  <span className="text-[10px] text-celadon-light font-mono">(+{metrics.snr_gain ?? '未评测'}dB)</span>
                </div>

                <div className="flex items-baseline space-x-1.5">
                  <span className="text-slate-400 font-serif text-[11px]">结构相似度 SSIM:</span>
                  <span className="font-mono font-bold text-gold-light text-sm">{metrics.ssim ?? '未评测'}</span>
                </div>

                <div className="flex items-baseline space-x-1.5">
                  <span className="text-slate-400 font-serif text-[11px]">字形骨架完整度:</span>
                  <span className="font-mono font-bold text-celadon-light text-sm">{metrics.glyph_completeness ?? '未评测'}%</span>
                </div>

                <div className="flex items-baseline space-x-1.5">
                  <span className="text-slate-400 font-serif text-[11px]">字符识别率:</span>
                  <span className="font-mono font-bold text-cinnabar-light text-sm">{metrics.character_accuracy ?? '未评测'}%</span>
                </div>
              </div>

              <div className="hidden sm:flex items-center space-x-2 text-[11px] text-slate-400">
                <span className="w-2 h-2 rounded-full bg-celadon-light animate-pulse" />
                <span>OpenCV 实时加速</span>
              </div>
            </div>
          </div>

          {/* Bottom Parameter Adjustments Panel */}
          <div className="glass-panel p-5 rounded-2xl border border-gold/20 flex flex-col space-y-4">
            <div className="flex items-center justify-between border-b border-gold/15 pb-2.5">
              <div className="flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-gold" />
                <h3 className="font-serif font-bold text-sm text-gold-light">
                  频空域联合去噪算法参数矩阵
                </h3>
              </div>
              <span className="text-[11px] font-sans text-slate-400">
                2D-FFT 频域滤波 + 快速非局部均值 (Fast NLM) + CLAHE
              </span>
            </div>

            <label className="text-xs text-slate-300">频域处理方式
              <select aria-label="频域处理方式" value={filterType} onChange={e => setFilterType(e.target.value as typeof filterType)} className="ml-3 rounded bg-slate-900 border border-slate-700 p-1 text-gold-light">
                <option value="adaptive">图像自适应（带保真门控）</option>
                <option value="butterworth">Butterworth 低通</option>
                <option value="gaussian">高斯低通</option>
                <option value="notch">自动陷波（仅检出周期峰时生效）</option>
              </select>
            </label>
            {/* Parameter controls */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              {/* Slider 1: D0 */}
              <div className="space-y-1.5 bg-slate-950/40 p-2.5 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-300 font-serif">截止频率 D₀ / 陷波宽度</span>
                  <span className="font-mono text-gold-light font-bold">{d0}</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="100"
                  step="1"
                  value={d0}
                  onChange={(e) => setD0(Number(e.target.value))}
                  className="w-full accent-[#D4AF37] cursor-pointer h-1.5 bg-slate-700 rounded-lg"
                />
                <div className="flex justify-between text-[9px] text-slate-500">
                  <span>10</span>
                  <span>100</span>
                </div>
              </div>

              {/* Slider 2: Filter Order */}
              <div className="space-y-1.5 bg-slate-950/40 p-2.5 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-300 font-serif">Butterworth 滤波器阶数 n</span>
                  <span className="font-mono text-gold-light font-bold">{filterOrder}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="5"
                  step="1"
                  value={filterOrder}
                  disabled={filterType !== 'butterworth'}
                  onChange={(e) => setFilterOrder(Number(e.target.value))}
                  className="w-full accent-[#D4AF37] cursor-pointer h-1.5 bg-slate-700 rounded-lg"
                />
                <div className="flex justify-between text-[9px] text-slate-500">
                  <span>1 阶 (平缓过渡)</span>
                  <span>5 阶 (陡峭截止)</span>
                </div>
              </div>

              {/* Slider 3: h_nlm */}
              <div className="space-y-1.5 bg-slate-950/40 p-2.5 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-300 font-serif">空域 NLM 保边去噪强度 $h$</span>
                  <span className="font-mono text-gold-light font-bold">{hNlm}</span>
                </div>
                <input
                  type="range"
                  min="2"
                  max="30"
                  step="1"
                  value={hNlm}
                  onChange={(e) => setHNlm(Number(e.target.value))}
                  className="w-full accent-[#D4AF37] cursor-pointer h-1.5 bg-slate-700 rounded-lg"
                />
                <div className="flex justify-between text-[9px] text-slate-500">
                  <span>2 (保全微痕)</span>
                  <span>30 (重度抚平)</span>
                </div>
              </div>

              {/* Slider 4: CLAHE */}
              <div className="space-y-1.5 bg-slate-950/40 p-2.5 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-300 font-serif">CLAHE 对比度限幅系数</span>
                  <span className="font-mono text-gold-light font-bold">{claheClip}</span>
                </div>
                <input
                  type="range"
                  min="1.0"
                  max="5.0"
                  step="0.1"
                  value={claheClip}
                  disabled={filterType === 'adaptive'}
                  onChange={(e) => setClaheClip(Number(e.target.value))}
                  className="w-full accent-[#D4AF37] cursor-pointer h-1.5 bg-slate-700 rounded-lg"
                />
                <div className="flex justify-between text-[9px] text-slate-500">
                  <span>1.0 (温和对比)</span>
                  <span>5.0 (极限凸显)</span>
                </div>
              </div>
              <label className="space-y-1.5 bg-slate-950/40 p-2.5 rounded-xl border border-slate-800">
                <span className="text-slate-300 font-serif">形态学核径：{morphKernel}</span>
                <input aria-label="形态学核径" disabled={filterType === 'adaptive'} type="range" min="1" max="9" step="2" value={morphKernel} onChange={e => setMorphKernel(Number(e.target.value))} className="w-full accent-[#D4AF37]" />
              </label>
            </div>

            {filterType === 'adaptive' && <p className="text-xs text-slate-400">自适应模式按输入频谱和残差选择陷波、孤立噪点处理或NLM，也可保留原图。D₀控制陷波宽度，NLM控制相对强度；CLAHE和形态学核径仅用于固定对照模式。没有缺字补全能力。</p>}
            {/* Run Algorithm Action */}
            <div className="flex items-center justify-between pt-1">
              <span className="text-[11px] text-slate-400">
                调整滑块后，点击右侧按钮立即调用 Python 核心引擎重构微痕
              </span>
              <button
                onClick={handleRunAlgorithm}
                disabled={isProcessing}
                className="px-6 py-2.5 rounded-xl font-serif font-bold text-xs bg-gradient-to-r from-gold to-gold-dark text-slate-950 shadow-gold-glow hover:brightness-110 active:scale-95 transition-all flex items-center space-x-2 disabled:opacity-50"
              >
                {isProcessing ? (
                  <>
                    <span className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    <span>OpenCV 引擎计算中...</span>
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

        {/* ========================================================= */}
        {/* RIGHT COLUMN: Ancient Xuan Paper & Inference (Col 5 - 42%) */}
        {/* ========================================================= */}
        <div className="lg:col-span-5 flex flex-col space-y-4">
          {adaptiveDetails && <details className="glass-panel p-3 text-xs"><summary className="text-gold cursor-pointer">本次自适应决策与保真诊断</summary><pre className="whitespace-pre-wrap break-all mt-2 max-h-80 overflow-auto">{JSON.stringify(adaptiveDetails,null,2)}</pre></details>}
          <GlyphInferencePanel stele={stele} activeChar={activeChar} runId={selectedRunId || undefined} restoredUrl={restoredImageUrl} onDecision={handleGlyphDecision} />
          {/* Top Xuan Paper Ancient Book Text View */}
          <div className="glass-panel rounded-2xl border border-gold/30 p-5 flex flex-col bg-gradient-to-b from-[#131920] to-[#0D1217] space-y-4 shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-gold/15 pb-2.5">
              <div className="flex items-center space-x-2">
                <BookOpen className="w-4 h-4 text-cinnabar" />
                <h3 className="font-serif font-bold text-sm text-gold-light">
                  金石古籍逐字释读卷轴 (右起竖排)
                </h3>
              </div>
              <span className="text-[10px] text-slate-400 font-serif">
                点击字符可关联人工选区
              </span>
            </div>

            {/* Xuan Paper Vertical Container */}
            <div className="relative w-full h-[270px] rounded-xl overflow-x-auto overflow-y-hidden p-4 bg-xuan-grid border border-[#D3C3A8]/40 shadow-inner">
              <div className="h-full flex flex-row-reverse items-start justify-start gap-4 writing-vertical-rl select-none">
                {/* Organize characters into columns of 7-8 chars */}
                {Array.from(new Set(characters.map((c) => c.col))).map((colIndex) => {
                  const colChars = characters.filter((c) => c.col === colIndex);
                  return (
                    <div 
                      key={colIndex} 
                      className="flex flex-col items-center justify-start gap-2.5 h-full border-r border-[#8B693C]/20 pr-1.5"
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
                              isSelected
                                ? 'scale-125 z-20 font-bold'
                                : 'hover:scale-110'
                            }`}
                          >
                            {/* Damaged Character Display */}
                            {isDamaged && (
                              <div className="w-8 h-8 rounded border-2 border-dashed border-cinnabar bg-cinnabar/15 flex items-center justify-center text-cinnabar-dark font-black shadow-cinnabar-glow animate-pulse">
                                {charItem.char}
                              </div>
                            )}

                            {/* Restored Character Display */}
                            {isRestored && (
                              <div className="w-8 h-8 rounded border border-cinnabar bg-cinnabar/20 flex items-center justify-center text-cinnabar-dark font-bold relative">
                                {charItem.char}
                                <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-cinnabar" />
                              </div>
                            )}

                            {/* Variant Character Display */}
                            {isVariant && (
                              <div 
                                className="w-8 h-8 rounded border border-celadon bg-celadon/15 flex items-center justify-center text-celadon-dark font-bold"
                                title={`异体字：本字为「${charItem.variant_of}」\n${charItem.explanation}`}
                              >
                                {charItem.char}
                              </div>
                            )}

                            {/* Normal Clear Character */}
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

            {/* Quick Status Legend */}
            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
              <div className="flex items-center space-x-3">
                <span className="flex items-center space-x-1">
                  <span className="w-2.5 h-2.5 rounded border border-dashed border-cinnabar bg-cinnabar/20" />
                  <span>漫漶残字 (待推演)</span>
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

          {/* Bottom Context-Glyph Bayesian Inference Box */}
          <div className="glass-panel rounded-2xl border border-gold/30 p-5 flex flex-col space-y-4 bg-gradient-to-b from-[#131920] to-[#0A0D12] shadow-xl flex-1">
            <div className="flex items-center justify-between border-b border-gold/15 pb-2.5">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-gold" />
                <h3 className="font-serif font-bold text-sm text-gold-light">
                  预置释文候选示例
                </h3>
              </div>
              <span className="text-[11px] font-mono text-celadon-light">
                DEMO ONLY
              </span>
            </div>

            {/* Selected Char Info Banner */}
            {activeChar && activeChar.inferred_candidates && activeChar.inferred_candidates.length > 0 ? (
              <div className="space-y-3.5">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-gold/25 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 rounded-xl bg-cinnabar/20 border-2 border-cinnabar flex items-center justify-center font-serif text-2xl font-bold text-cinnabar-light shadow-cinnabar-glow">
                      {activeChar.char}
                    </div>
                    <div>
                      <div className="font-serif font-bold text-sm text-slate-100 flex items-center gap-2">
                        <span>待释读漫漶残字 #{activeChar.id}</span>
                        <span className="text-[11px] font-mono text-cinnabar px-1.5 py-0.5 rounded bg-cinnabar/10 border border-cinnabar/20">
                          演示标签 · 未实测
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 font-sans mt-0.5">
                        这些候选来自项目预置案例，没有与当前选区进行笔画比对。
                      </p>
                    </div>
                  </div>
                </div>

                {/* Candidate List (Top 3) */}
                <div className="space-y-2">
                  <span className="text-[11px] font-serif text-slate-400">
                    预置候选排序（非概率）:
                  </span>
                  
                  {activeChar.inferred_candidates.map((cand, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-xl border transition-all ${
                        idx === 0
                          ? 'bg-gold/10 border-gold/50 shadow-gold-glow'
                          : 'bg-slate-900/40 border-slate-800'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center space-x-2">
                          <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-mono font-bold ${
                            idx === 0 ? 'bg-gold text-slate-950' : 'bg-slate-800 text-slate-400'
                          }`}>
                            {idx + 1}
                          </span>
                          <span className="font-serif text-lg font-bold text-white">
                            「{cand.glyph}」
                          </span>
                          <span className="text-[10px] font-serif text-slate-400 px-1.5 py-0.5 rounded bg-slate-800">
                            {cand.font_style}
                          </span>
                        </div>
                        <div className="flex items-center space-x-1.5">
                          <span className="text-xs font-mono font-bold text-gold-light">
                            演示顺序 {idx + 1}
                          </span>
                        </div>
                      </div>

                      <div className="text-[11px] text-slate-300 leading-relaxed font-sans">
                        <span className="text-gold/90 font-serif">考据依据: </span>
                        {cand.evidence}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono mt-1">
                        文献源: {cand.source}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Feedback Message */}
                {adoptionSuccessMsg && (
                  <div className="p-2.5 rounded-xl bg-celadon/20 border border-celadon/50 text-celadon-light text-xs font-serif flex items-center space-x-2 animate-fadeIn">
                    <Check className="w-4 h-4 flex-shrink-0" />
                    <span>{adoptionSuccessMsg}</span>
                  </div>
                )}

                <p className="text-xs text-slate-400">请在上方“实际残字推演”中框选图像，保存实际候选后再人工采纳。</p>
              </div>
            ) : (
              <div className="p-6 text-center text-slate-400 font-serif text-xs">
                当前选中的字符为标准完好字或俗异体字，请在上方古籍卷轴中点击带有虚线红框的漫漶残字进行推演。
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
