import React, { useRef, useState } from 'react';
import { CORE_SAMPLES } from '../data/catalogSelection';
import { SteleItem } from '../types/stele';
import { SteleViewer } from '../components/stele3d/SteleViewer';
import { SteleFullscreenViewer } from '../components/stele3d/SteleFullscreenViewer';
import { HomeAmbientBackground } from '../components/HomeAmbientBackground';
import { RubbingRevealCanvas } from '../components/RubbingRevealCanvas';
import { SealStamp } from '../components/SealStamp';
import { useExperience } from '../context/ExperienceContext';
import {
  ArrowRight,
  Layers,
  Network,
  Sparkles,
  BookOpen,
  ScrollText,
  Eye,
  Stamp,
  SunMedium,
} from 'lucide-react';

interface HomePageProps {
  steles: SteleItem[];
  onSelectStele: (id: string) => void;
  onNavigate: (tab: string) => void;
}

const CURATORIAL_MOVEMENTS = [
  {
    num: '壹',
    en: 'OBSERVE',
    title: '观碑 · 考古侧光掠影',
    desc: '基于 Blender 5.2.2 程序化雕刻的风化青石碑体，拖动斜射光束角度与冷月/暖烛色温，让千年阴刻刀锋在暗馆中苏醒。',
    icon: Eye,
    accent: 'text-[var(--rm-gold)]',
  },
  {
    num: '贰',
    en: 'RESTORE',
    title: '复原 · 频空域微痕重构',
    desc: '二维傅里叶自动陷波、Fast NLM 保边去噪与保真门控协同工作，支持卷轴分屏、朱拓模拟与骨架提取，拒绝无真值造假。',
    icon: Layers,
    accent: 'text-[var(--rm-cinnabar-bright)]',
  },
  {
    num: '叁',
    en: 'INTERPRET',
    title: '释读 · 有据史料与学伴',
    desc: '原碑文与白话译注双栏联动，结合 SQLite FTS5 有据文献检索与三维 DEM 时空舆图，严格划清史实著录与 AI 推演边界。',
    icon: Sparkles,
    accent: 'text-[var(--rm-celadon-light)]',
  },
  {
    num: '肆',
    en: 'PRESERVE',
    title: '留痕 · 当代碑帖美育卡',
    desc: '将喜爱的碑文名句与单字排版为数字藏品卡、竖排宣纸书签或当代极简海报，落印导出一键珍藏，完成文化传播闭环。',
    icon: Stamp,
    accent: 'text-[var(--rm-gold)]',
  },
];

export const HomePage: React.FC<HomePageProps> = ({ steles, onSelectStele, onNavigate }) => {
  const heroSectionRef = useRef<HTMLElement | null>(null);
  const { setManifestoOpen } = useExperience();
  const [heroSampleIndex, setHeroSampleIndex] = useState(0);
  const currentStele = CORE_SAMPLES[heroSampleIndex] || CORE_SAMPLES[0];
  const verifiedSteles = steles.filter((item) => item.source_kind === 'verified_review_v3');
  const dynastyCount = new Set(verifiedSteles.map((item) => item.dynasty_value)).size;
  const [isFullscreen3D, setIsFullscreen3D] = useState(false);

  return (
    <div className="min-h-screen bg-[var(--rm-bg-canvas)] text-[var(--rm-ink-primary)] flex flex-col space-y-14 pb-20 transition-colors duration-300">
      {/* 1. Immersive Prologue Hero: "拂尘见字 / 数字传拓" */}
      <section
        ref={heroSectionRef}
        className="home-ambient-hero relative w-full min-h-[calc(100vh-68px)] flex flex-col justify-center pt-8 pb-12 px-4 lg:px-12 overflow-hidden bg-gradient-to-b from-[#0E1218] via-[#0A0C10] to-[#0A0C10] border-b border-[var(--rm-border)]"
      >
        {/* Preserved ambient video background (exact geometry & CI test contract kept) */}
        <HomeAmbientBackground />

        {/* Interactive Ink-Dabber / Raking-Light Calligraphy Reveal Canvas (pointer-events: none) */}
        <RubbingRevealCanvas hostRef={heroSectionRef} />

        {/* Subtle Background Ink Mountains Texture */}
        <div
          className="absolute inset-0 opacity-[0.03] pointer-events-none bg-center bg-cover mix-blend-screen"
          style={{ backgroundImage: `url('/assets/stele/backgrounds/bg_home_ink_landscape.png')` }}
        />

        {/* Vertical Editorial Colophon Rail (Desktop Accent) */}
        <div
          aria-hidden="true"
          className="hidden 2xl:flex flex-col items-center gap-4 absolute right-5 top-1/2 -translate-y-1/2 z-10 pointer-events-none opacity-65"
        >
          <span className="h-12 w-px bg-gradient-to-b from-transparent via-[var(--rm-gold)] to-transparent" />
          <span className="rm-colophon text-[11px] text-[var(--rm-gold)]">
            拂塵見字 · 貞石長存
          </span>
          <SealStamp text="传拓" variant="zhuwen" size="xs" />
        </div>

        <div className="w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
          {/* Left Narrative & Actions (Col 7) */}
          <div className="home-hero-copy lg:col-span-7 flex flex-col space-y-6 rm-animate-unscroll">
            <div className="flex flex-wrap items-center gap-2.5">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[var(--rm-gold-soft)] border border-[var(--rm-border-strong)] text-[var(--rm-gold-light)] text-xs font-serif w-fit backdrop-blur-md">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--rm-cinnabar)] animate-pulse" />
                <span>拂尘见字 · 移动指针以光墨拂过千年碑面</span>
              </div>
              <button
                type="button"
                onClick={() => setManifestoOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--rm-bg-surface)] border border-[var(--rm-border)] hover:border-[var(--rm-cinnabar)] text-[11px] font-serif text-[var(--rm-ink-secondary)] hover:text-[var(--rm-cinnabar-bright)] transition-colors"
              >
                <ScrollText className="w-3 h-3" />
                <span>作品立意与技术图谱</span>
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-4">
                <h1 className="text-4xl md:text-5xl lg:text-6xl font-serif font-black tracking-[0.08em] text-transparent bg-clip-text bg-gradient-to-r from-[#faf6ee] via-[#e5cb98] to-[#c9a66b]">
                  墨韵智考
                </h1>
                <SealStamp text="金石传拓" variant="baiwen" size="md" className="rm-animate-seal" />
              </div>
              <p className="text-lg md:text-xl font-serif text-[var(--rm-gold-light)] font-medium tracking-wide">
                千年金石 × 当代数字媒体 · 碑拓微痕重构、三维侧光鉴刻与人文考据
              </p>
            </div>

            <p className="text-slate-300 font-sans text-sm md:text-base leading-relaxed max-w-2xl text-justify">
              面对石刻文物不可逆的风化漫漶与公众阅读门槛，系统融汇
              <strong className="text-[var(--rm-ink-primary)] font-serif"> Blender 5.2.2 三维金石重建</strong>、
              <strong className="text-[var(--rm-ink-primary)] font-serif">2D-FFT 频空域自适应微痕复原</strong>、
              <strong className="text-[var(--rm-ink-primary)] font-serif">真实 DEM 时空舆图</strong>与
              <strong className="text-[var(--rm-ink-primary)] font-serif">有据史料检索</strong>，
              以“观碑 · 复原 · 释读 · 留痕”四重策展体验，让沉睡的贞石字口重焕温度。无真值拓片绝不虚报指标。
            </p>

            {/* 4 Museum Metric Plaques */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
              <div className="rm-book-frame p-3.5 rounded-xl flex flex-col">
                <span className="text-[11px] text-[var(--rm-ink-muted)] font-serif">真实授权馆藏</span>
                <div className="text-2xl rm-mono-metric font-bold text-[var(--rm-gold-light)] mt-1">
                  {verifiedSteles.length} <span className="text-xs font-serif font-normal">通</span>
                </div>
                <span className="text-[10px] text-[var(--rm-celadon-light)] mt-0.5">84 幅独立高清影像</span>
              </div>
              <div className="rm-book-frame p-3.5 rounded-xl flex flex-col">
                <span className="text-[11px] text-[var(--rm-ink-muted)] font-serif">跨越历史朝代</span>
                <div className="text-2xl rm-mono-metric font-bold text-[var(--rm-cinnabar-bright)] mt-1">
                  {dynastyCount} <span className="text-xs font-serif font-normal">朝</span>
                </div>
                <span className="text-[10px] text-[var(--rm-ink-muted)] mt-0.5">东汉至清逐件著录</span>
              </div>
              <div className="rm-book-frame p-3.5 rounded-xl flex flex-col">
                <span className="text-[11px] text-[var(--rm-ink-muted)] font-serif">受控算法实证</span>
                <div className="text-2xl rm-mono-metric font-bold text-[var(--rm-ink-primary)] mt-1">
                  2,520 <span className="text-xs font-serif font-normal">组</span>
                </div>
                <span className="text-[10px] text-[var(--rm-ink-muted)] mt-0.5">9 种方法可复现对比</span>
              </div>
              <div className="rm-book-frame p-3.5 rounded-xl flex flex-col">
                <span className="text-[11px] text-[var(--rm-ink-muted)] font-serif">实时 3D 鉴刻</span>
                <div className="text-2xl rm-mono-metric font-bold text-[var(--rm-celadon-light)] mt-1">
                  PBR <span className="text-xs font-serif font-normal">侧光</span>
                </div>
                <span className="text-[10px] text-[var(--rm-ink-muted)] mt-0.5">3.8MB 轻量化秒开</span>
              </div>
            </div>

            {/* Primary Action Buttons (Exact accessible labels preserved for CI) */}
            <div className="flex flex-wrap items-center gap-3.5 pt-2">
              <button
                onClick={() => {
                  onSelectStele(currentStele.id);
                  onNavigate('workbench');
                }}
                className="px-6 py-3 rounded-xl font-serif font-bold text-sm bg-gradient-to-r from-[#c33927] to-[#9b2517] text-[#faf6ee] shadow-cinnabar-glow hover:brightness-110 active:scale-95 transition-all flex items-center space-x-2 rm-keep-light-ink"
              >
                <Layers className="w-4 h-4" />
                <span>进入智考修复工作台</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={() => onNavigate('museum')}
                className="px-6 py-3 rounded-xl font-serif font-semibold text-sm glass-panel text-[var(--rm-ink-primary)] hover:text-[var(--rm-gold-light)] border border-[var(--rm-border-strong)] hover:border-[var(--rm-gold)] transition-all flex items-center space-x-2"
              >
                <BookOpen className="w-4 h-4 text-[var(--rm-gold)]" />
                <span>浏览中华贞石典藏馆</span>
              </button>

              <button
                onClick={() => onNavigate('graph')}
                className="px-5 py-3 rounded-xl font-serif font-medium text-sm text-[var(--rm-ink-secondary)] hover:text-[var(--rm-celadon-light)] transition-colors flex items-center space-x-1.5"
              >
                <Network className="w-4 h-4 text-[var(--rm-celadon)]" />
                <span>时空图谱与 GIS 考据</span>
              </button>
            </div>
          </div>

          {/* Right 3D Raking-Light Exhibition Stage (Col 5) */}
          <div className="lg:col-span-5 flex flex-col space-y-2.5">
            <div className="relative h-[540px] rounded-2xl overflow-hidden border border-[var(--rm-border-strong)] shadow-[var(--rm-shadow-float)] flex flex-col">
              <SteleViewer
                customRubbingUrl={currentStele?.damaged_image || currentStele?.raw_image}
                steleTitle={`${currentStele.title.replace(/（核心实验样本）/, '')} · 三维侧光鉴刻`}
                onOpenWorkbench={() => {
                  if (currentStele) onSelectStele(currentStele.id);
                  onNavigate('workbench');
                }}
                onToggleFullscreen={() => setIsFullscreen3D(true)}
                isFullscreen={false}
                showControls={true}
              />
            </div>

            {/* Instant 3D Stele Rubbing Switcher Bar */}
            <div className="flex items-center justify-between gap-2 px-3 py-2 rounded-xl glass-panel border border-[var(--rm-border)] text-[11px]">
              <span className="font-serif text-[var(--rm-ink-muted)] inline-flex items-center gap-1 shrink-0">
                <SunMedium className="w-3.5 h-3.5 text-[var(--rm-gold)]" />
                切换展台碑拓：
              </span>
              <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
                {CORE_SAMPLES.map((sample, idx) => (
                  <button
                    key={sample.id}
                    type="button"
                    onClick={() => setHeroSampleIndex(idx)}
                    className={`px-2 py-1 rounded-md font-serif whitespace-nowrap transition-all ${
                      idx === heroSampleIndex
                        ? 'bg-[var(--rm-gold)] text-[#14110f] font-bold'
                        : 'text-[var(--rm-ink-secondary)] hover:bg-[var(--rm-bg-subtle)]'
                    }`}
                  >
                    {sample.title.split('·')[1]?.split('（')[0] || sample.title.slice(0, 5)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Fullscreen 3D Viewer Modal */}
        <SteleFullscreenViewer
          isOpen={isFullscreen3D}
          onClose={() => setIsFullscreen3D(false)}
          customRubbingUrl={currentStele?.damaged_image || currentStele?.raw_image}
          steleTitle={`${currentStele.title} · 全屏考古侧光展陈`}
          onOpenWorkbench={() => {
            setIsFullscreen3D(false);
            if (currentStele) onSelectStele(currentStele.id);
            onNavigate('workbench');
          }}
        />
      </section>

      {/* 2. Four-Fold Curatorial Narrative: 观碑 · 复原 · 释读 · 留痕 */}
      <section className="max-w-7xl mx-auto px-4 lg:px-8 w-full space-y-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="space-y-2">
            <span className="text-[11px] rm-mono-metric text-[var(--rm-gold)] tracking-[0.26em] uppercase">
              CURATORIAL EXPERIENCE · FOUR MOVEMENTS
            </span>
            <h2 className="text-2xl md:text-3xl font-serif font-bold text-[var(--rm-ink-primary)] tracking-wide">
              起承转合 · 四重沉浸式数字金石策展动线
            </h2>
          </div>
          <p className="text-xs md:text-sm text-[var(--rm-ink-muted)] font-sans max-w-md">
            告别“上传即等待”的工具逻辑，以观碑、复原、释读、留痕重构文物数字化与公众美育链路。
          </p>
        </div>

        <div className="rm-hairline-divider" />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {CURATORIAL_MOVEMENTS.map((step) => {
            const Icon = step.icon;
            return (
              <div
                key={step.num}
                className="rm-book-frame p-5 rounded-2xl hover:-translate-y-1 flex flex-col justify-between space-y-4 group"
              >
                <div className="space-y-3.5">
                  <div className="flex items-center justify-between">
                    <span className="w-10 h-10 rounded-xl bg-[var(--rm-bg-subtle)] border border-[var(--rm-border-strong)] flex items-center justify-center group-hover:scale-105 transition-transform">
                      <Icon className={`w-5 h-5 ${step.accent}`} />
                    </span>
                    <span className="font-serif text-2xl font-black text-[var(--rm-border-strong)] group-hover:text-[var(--rm-cinnabar)] transition-colors">
                      {step.num}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] rm-mono-metric text-[var(--rm-ink-muted)] tracking-widest">
                      {step.en}
                    </span>
                    <h3 className="text-base font-serif font-bold text-[var(--rm-ink-primary)] mt-0.5">
                      {step.title}
                    </h3>
                  </div>
                  <p className="text-xs text-[var(--rm-ink-secondary)] leading-relaxed text-justify font-sans">
                    {step.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 3. Curated Archive Preview (零门槛秒级体验) */}
      <section className="max-w-7xl mx-auto px-4 lg:px-8 w-full">
        <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
          <div>
            <span className="text-[11px] rm-mono-metric text-[var(--rm-cinnabar-bright)] tracking-[0.22em] uppercase">
              CURATED SPECIMENS · ZERO-FRICTION ENTRY
            </span>
            <h2 className="text-2xl font-serif font-bold text-[var(--rm-ink-primary)] mt-1">
              典藏碑林精选 · 跨朝代书体标本
            </h2>
            <p className="text-xs text-[var(--rm-ink-muted)] mt-1">
              无需自备图片，涵盖汉隶、北魏墓志、盛唐颜楷与极端漫漶残片，点击即刻步入四重工坊
            </p>
          </div>
          <button
            onClick={() => onNavigate('museum')}
            className="text-xs text-[var(--rm-gold)] hover:underline flex items-center space-x-1 font-serif"
          >
            <span>步入典藏馆浏览全部 {verifiedSteles.length} 通真实馆藏</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {CORE_SAMPLES.map((stele) => (
            <div
              key={stele.id}
              className="rm-book-frame rounded-2xl overflow-hidden flex flex-col group hover:-translate-y-1"
            >
              {/* Stele Image Window (object-contain preserved, never crops glyphs) */}
              <div
                className="relative h-48 w-full bg-[#e9dfd0] overflow-hidden flex items-center justify-center"
                data-testid="core-sample-image-frame"
              >
                <img
                  src={stele.raw_image}
                  alt={stele.title}
                  className="w-full h-full object-contain p-1.5 group-hover:scale-[1.03] transition duration-500 filter contrast-125"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/assets/stele/rubbings/stele_tang_duobao_damaged.png';
                  }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0A0C10]/85 via-transparent to-transparent" />

                {/* Dynasty & Condition Badges */}
                <div className="absolute top-2.5 left-2.5 flex flex-col gap-1">
                  <span className="px-2 py-0.5 rounded text-[10px] font-serif bg-[#c9a66b] text-[#14110f] font-bold">
                    {stele.dynasty.split('·')[0]}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-serif rm-keep-light-ink ${
                      stele.imageCondition === '严重漫漶'
                        ? 'bg-[#c33927] text-[#faf6ee]'
                        : 'bg-[#12161c]/85 text-[#f2ece1]'
                    }`}
                  >
                    {stele.script_type?.split('（')[0] || '金石拓本'}
                  </span>
                </div>

                <div className="absolute bottom-2 left-2.5 right-2.5 flex items-center justify-between text-[10px] text-[#e5cb98] rm-mono-metric">
                  <span>PSNR: {stele.metrics?.psnr != null ? `${stele.metrics.psnr} dB` : '未评测'}</span>
                  <span>SSIM: {stele.metrics?.ssim ?? '未评测'}</span>
                </div>
              </div>

              {/* Stele Content */}
              <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                <div>
                  <h4 className="font-serif font-bold text-base text-[var(--rm-ink-primary)] group-hover:text-[var(--rm-gold)] transition-colors">
                    {stele.title}
                  </h4>
                  <p className="text-[11px] text-[var(--rm-ink-muted)] mt-1 line-clamp-1">{stele.author}</p>
                  <p className="text-xs text-[var(--rm-ink-secondary)] mt-2 line-clamp-2 leading-relaxed font-sans">
                    {stele.summary}
                  </p>
                </div>

                <div className="pt-2.5 border-t border-[var(--rm-border)] flex items-center justify-between">
                  <button
                    onClick={() => {
                      onSelectStele(stele.id);
                      onNavigate('workbench');
                    }}
                    className="text-xs font-serif text-[var(--rm-cinnabar-bright)] hover:underline font-semibold flex items-center space-x-1"
                  >
                    <Layers className="w-3.5 h-3.5" />
                    <span>步入工坊</span>
                  </button>

                  <button
                    onClick={() => {
                      onSelectStele(stele.id);
                      onNavigate('graph');
                    }}
                    className="text-xs font-serif text-[var(--rm-ink-secondary)] hover:text-[var(--rm-celadon-light)] flex items-center space-x-1"
                  >
                    <Network className="w-3.5 h-3.5" />
                    <span>时空图谱</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
