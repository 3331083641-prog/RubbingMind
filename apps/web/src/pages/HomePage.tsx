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
    title: '观碑 · 侧光掠影',
    desc: 'Blender 三维青石与实时斜射光，重现阴刻刀锋。',
    icon: Eye,
    accent: 'text-[var(--rm-gold)]',
  },
  {
    num: '贰',
    en: 'RESTORE',
    title: '复原 · 频空去噪',
    desc: '2D-FFT 自适应门控重构微痕，无真值不虚报。',
    icon: Layers,
    accent: 'text-[var(--rm-cinnabar-bright)]',
  },
  {
    num: '叁',
    en: 'INTERPRET',
    title: '释读 · 史料学伴',
    desc: '双栏译注、DEM 舆图与有据检索，考据边界明晰。',
    icon: Sparkles,
    accent: 'text-[var(--rm-celadon-light)]',
  },
  {
    num: '肆',
    en: 'PRESERVE',
    title: '留痕 · 碑帖文创',
    desc: '摘句落印，一键导出高清藏品卡、书签与海报。',
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
    <div className="min-h-screen bg-[var(--rm-bg-canvas)] text-[var(--rm-ink-primary)] flex flex-col space-y-12 pb-16 transition-colors duration-300">
      {/* 1. Immersive Prologue Hero */}
      <section
        ref={heroSectionRef}
        className="home-ambient-hero relative w-full min-h-[calc(100vh-68px)] flex flex-col justify-center pt-6 pb-10 px-4 lg:px-12 overflow-hidden bg-gradient-to-b from-[#0E1218] via-[#0A0C10] to-[#0A0C10] border-b border-[var(--rm-border)]"
      >
        <HomeAmbientBackground />
        <RubbingRevealCanvas hostRef={heroSectionRef} />

        <div
          className="absolute inset-0 opacity-[0.03] pointer-events-none bg-center bg-cover mix-blend-screen"
          style={{ backgroundImage: `url('/assets/stele/backgrounds/bg_home_ink_landscape.png')` }}
        />

        {/* Vertical Editorial Colophon Rail */}
        <div
          aria-hidden="true"
          className="hidden 2xl:flex flex-col items-center gap-4 absolute right-5 top-1/2 -translate-y-1/2 z-10 pointer-events-none opacity-65"
        >
          <span className="h-12 w-px bg-gradient-to-b from-transparent via-[var(--rm-gold)] to-transparent" />
          <span className="rm-colophon text-[11px] text-[var(--rm-gold)]">拂塵見字 · 貞石長存</span>
          <SealStamp text="传拓" variant="zhuwen" size="xs" />
        </div>

        <div className="w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
          {/* Left Minimalist Editorial Copy (Col 7) */}
          <div className="home-hero-copy lg:col-span-7 flex flex-col space-y-6 rm-animate-unscroll">
            <div className="flex flex-wrap items-center gap-2.5">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[var(--rm-gold-soft)] border border-[var(--rm-border-strong)] text-[var(--rm-gold-light)] text-xs font-serif w-fit backdrop-blur-md">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--rm-cinnabar)] animate-pulse" />
                <span>拂尘见字 · 移动指针显影碑文</span>
              </div>
              <button
                type="button"
                onClick={() => setManifestoOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--rm-bg-surface)] border border-[var(--rm-border)] hover:border-[var(--rm-cinnabar)] text-[11px] font-serif text-[var(--rm-ink-secondary)] hover:text-[var(--rm-cinnabar-bright)] transition-colors"
              >
                <ScrollText className="w-3 h-3" />
                <span>立意图谱</span>
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-4">
                <h1 className="text-5xl md:text-6xl font-serif font-black tracking-[0.08em] text-transparent bg-clip-text bg-gradient-to-r from-[#faf6ee] via-[#e5cb98] to-[#c9a66b]">
                  墨韵智考
                </h1>
                <SealStamp text="金石传拓" variant="baiwen" size="md" className="rm-animate-seal" />
              </div>
              <p className="text-lg md:text-xl font-serif text-[var(--rm-gold-light)] font-medium tracking-wide">
                千年金石 · 三维侧光鉴刻 · 微痕重构与有据考据
              </p>
            </div>

            <p className="text-slate-300 font-sans text-sm md:text-base leading-relaxed max-w-xl">
              以三维光影与频空域算法抢救石刻漫漶微痕，联结真实馆藏考据与当代美育留痕。
            </p>

            {/* 4 Clean Museum Metric Plaques */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
              <div className="rm-book-frame px-3.5 py-3 rounded-xl flex flex-col">
                <span className="text-[11px] text-[var(--rm-ink-muted)] font-serif">授权馆藏</span>
                <div className="text-2xl rm-mono-metric font-bold text-[var(--rm-gold-light)] mt-0.5">
                  {verifiedSteles.length} <span className="text-xs font-serif font-normal">通</span>
                </div>
              </div>
              <div className="rm-book-frame px-3.5 py-3 rounded-xl flex flex-col">
                <span className="text-[11px] text-[var(--rm-ink-muted)] font-serif">跨越朝代</span>
                <div className="text-2xl rm-mono-metric font-bold text-[var(--rm-cinnabar-bright)] mt-0.5">
                  {dynastyCount} <span className="text-xs font-serif font-normal">朝</span>
                </div>
              </div>
              <div className="rm-book-frame px-3.5 py-3 rounded-xl flex flex-col">
                <span className="text-[11px] text-[var(--rm-ink-muted)] font-serif">受控实证</span>
                <div className="text-2xl rm-mono-metric font-bold text-[var(--rm-ink-primary)] mt-0.5">
                  2,520 <span className="text-xs font-serif font-normal">组</span>
                </div>
              </div>
              <div className="rm-book-frame px-3.5 py-3 rounded-xl flex flex-col">
                <span className="text-[11px] text-[var(--rm-ink-muted)] font-serif">三维鉴刻</span>
                <div className="text-2xl rm-mono-metric font-bold text-[var(--rm-celadon-light)] mt-0.5">
                  PBR <span className="text-xs font-serif font-normal">侧光</span>
                </div>
              </div>
            </div>

            {/* Primary Action Buttons (Exact CI labels preserved) */}
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
                className="px-4 py-3 rounded-xl font-serif font-medium text-sm text-[var(--rm-ink-secondary)] hover:text-[var(--rm-celadon-light)] transition-colors flex items-center space-x-1.5"
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
                steleTitle={currentStele.title.replace(/（核心实验样本）/, '')}
                onOpenWorkbench={() => {
                  if (currentStele) onSelectStele(currentStele.id);
                  onNavigate('workbench');
                }}
                onToggleFullscreen={() => setIsFullscreen3D(true)}
                isFullscreen={false}
                showControls={true}
              />
            </div>

            <div className="flex items-center justify-between gap-2 px-3 py-2 rounded-xl glass-panel border border-[var(--rm-border)] text-[11px]">
              <span className="font-serif text-[var(--rm-ink-muted)] inline-flex items-center gap-1 shrink-0">
                <SunMedium className="w-3.5 h-3.5 text-[var(--rm-gold)]" />
                展台碑拓
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

        <SteleFullscreenViewer
          isOpen={isFullscreen3D}
          onClose={() => setIsFullscreen3D(false)}
          customRubbingUrl={currentStele?.damaged_image || currentStele?.raw_image}
          steleTitle={`${currentStele.title.replace(/（核心实验样本）/, '')} · 全屏侧光鉴刻`}
          onOpenWorkbench={() => {
            setIsFullscreen3D(false);
            if (currentStele) onSelectStele(currentStele.id);
            onNavigate('workbench');
          }}
        />
      </section>

      {/* 2. Four-Fold Curatorial Narrative */}
      <section className="max-w-7xl mx-auto px-4 lg:px-8 w-full space-y-6">
        <div className="flex items-baseline justify-between gap-4">
          <h2 className="text-2xl font-serif font-bold text-[var(--rm-ink-primary)] tracking-wide">
            观碑 · 复原 · 释读 · 留痕
          </h2>
          <span className="text-[11px] rm-mono-metric text-[var(--rm-gold)] tracking-[0.22em] uppercase">
            FOUR CURATORIAL MOVEMENTS
          </span>
        </div>

        <div className="rm-hairline-divider" />

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {CURATORIAL_MOVEMENTS.map((step) => {
            const Icon = step.icon;
            return (
              <div
                key={step.num}
                className="rm-book-frame p-5 rounded-2xl hover:-translate-y-1 flex flex-col space-y-3 group"
              >
                <div className="flex items-center justify-between">
                  <span className="w-9 h-9 rounded-xl bg-[var(--rm-bg-subtle)] border border-[var(--rm-border-strong)] flex items-center justify-center">
                    <Icon className={`w-4 h-4 ${step.accent}`} />
                  </span>
                  <span className="font-serif text-xl font-black text-[var(--rm-border-strong)] group-hover:text-[var(--rm-cinnabar)] transition-colors">
                    {step.num}
                  </span>
                </div>
                <h3 className="text-base font-serif font-bold text-[var(--rm-ink-primary)]">{step.title}</h3>
                <p className="text-xs text-[var(--rm-ink-secondary)] leading-relaxed font-sans">{step.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* 3. Curated Archive Preview */}
      <section className="max-w-7xl mx-auto px-4 lg:px-8 w-full">
        <div className="flex flex-wrap items-baseline justify-between gap-4 mb-5">
          <h2 className="text-2xl font-serif font-bold text-[var(--rm-ink-primary)]">典藏碑林精选</h2>
          <button
            onClick={() => onNavigate('museum')}
            className="text-xs text-[var(--rm-gold)] hover:underline flex items-center space-x-1 font-serif"
          >
            <span>全部 {verifiedSteles.length} 通真实馆藏</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {CORE_SAMPLES.map((stele) => (
            <div
              key={stele.id}
              className="rm-book-frame rounded-2xl overflow-hidden flex flex-col group hover:-translate-y-1"
            >
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
                <div className="absolute inset-0 bg-gradient-to-t from-[#0A0C10]/80 via-transparent to-transparent" />
                <div className="absolute top-2.5 left-2.5 flex gap-1.5">
                  <span className="px-2 py-0.5 rounded text-[10px] font-serif bg-[#c9a66b] text-[#14110f] font-bold">
                    {stele.dynasty.split('·')[0]}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-serif bg-[#12161c]/85 text-[#f2ece1] rm-keep-light-ink">
                    {stele.script_type?.split('（')[0] || '石刻'}
                  </span>
                </div>
              </div>

              <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                <div>
                  <h4 className="font-serif font-bold text-base text-[var(--rm-ink-primary)] group-hover:text-[var(--rm-gold)] transition-colors line-clamp-1">
                    {stele.title.replace(/（核心实验样本）/, '')}
                  </h4>
                  <p className="text-[11px] text-[var(--rm-ink-muted)] mt-1 line-clamp-1">
                    {stele.year.split('（')[0]}
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
