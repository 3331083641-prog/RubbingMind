import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, Layers, Compass, Sparkles, ShieldCheck, Box, BookOpen, ArrowUpRight } from 'lucide-react';
import { SealStamp } from './SealStamp';

interface CuratorialManifestoModalProps {
  isOpen: boolean;
  onClose: () => void;
  verifiedCount: number;
  onNavigate?: (tab: string) => void;
}

const ARCH_PILLARS = [
  {
    code: 'LAYER 01',
    title: '三维金石质感重建',
    subtitle: 'Blender 5.2.2 程序化雕刻 · WebGL PBR · 考古侧光掠影',
    desc: '通过无头 Blender 脚本构建闭合流形石碑与风化倒角、法线/粗糙度/AO 贴图；前端支持实时斜射侧光方位、仰角与冷月/暖烛/考古光色温调节，再现碑刻微浮雕与阴刻刀锋。',
    badge: '空间与光影',
    icon: Box,
  },
  {
    code: 'LAYER 02',
    title: '频空域自适应微痕复原',
    subtitle: '2D-FFT 周期陷波 · Fast NLM 保边去噪 · 保真门控',
    desc: '针对拓片织纹周期噪点与漫漶斑驳，先做频谱峰检验与残差诊断，再决定陷波、孤立去噪、NLM 或原图直通；全部运行记录与 SHA-256 哈希可追溯，绝不伪造无参考评测数值。',
    badge: '视觉算法',
    icon: Layers,
  },
  {
    code: 'LAYER 03',
    title: '有据史料考据与时空舆图',
    subtitle: 'SQLite FTS5/BM25 · 真实 DEM 三维地形 · 四级证据链',
    desc: '整合台北故宫、大都会、普林斯顿 28 件跨七朝代真实馆藏与 4 件核心样本；检索回答严格绑定来源摘录与争议保留原则，清晰区分“史料著录”与“AI 辅助推演”。',
    badge: '数字人文',
    icon: Compass,
  },
  {
    code: 'LAYER 04',
    title: '当代美育与文化留痕闭环',
    subtitle: '拂尘显影序章 · 双栏白话译注 · 高清数字碑帖藏品卡',
    desc: '打破“工具型上传等待”壁垒，构建“观碑 · 复原 · 释读 · 留痕”策展动线；观众可摘选名句单字、落印定制竖排宣纸书签与当代海报并一键导出高清 PNG，让金石重回日常。',
    badge: '社会价值',
    icon: Sparkles,
  },
];

export const CuratorialManifestoModal: React.FC<CuratorialManifestoModalProps> = ({
  isOpen,
  onClose,
  verifiedCount,
  onNavigate,
}) => {
  useEffect(() => {
    if (!isOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-label="作品立意与技术图谱"
      className="fixed inset-0 z-[110] flex items-center justify-center bg-black/80 backdrop-blur-md p-4 md:p-6 overflow-y-auto"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="relative w-full max-w-5xl rounded-2xl border border-[var(--rm-border-strong)] bg-[var(--rm-bg-elevated)] text-[var(--rm-ink-primary)] shadow-[var(--rm-shadow-float)] overflow-hidden my-auto rm-animate-unscroll">
        {/* Top Ornamental Rule */}
        <div className="h-1 w-full bg-gradient-to-r from-transparent via-[var(--rm-cinnabar)] to-transparent opacity-80" />

        {/* Header */}
        <div className="flex items-start justify-between gap-4 px-6 py-5 border-b border-[var(--rm-border)]">
          <div className="flex items-center gap-4">
            <SealStamp text="金石传拓" variant="baiwen" size="md" />
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[11px] rm-mono-metric tracking-[0.22em] uppercase text-[var(--rm-gold)]">
                  CURATORIAL MANIFESTO & ARCHITECTURE
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-serif bg-[var(--rm-cinnabar-soft)] text-[var(--rm-cinnabar-bright)] border border-[var(--rm-cinnabar)]/30">
                  数字媒体策展白皮书
                </span>
              </div>
              <h2 className="text-xl md:text-2xl font-serif font-bold mt-1 tracking-wide">
                墨韵智考 · 作品立意与全栈技术图谱
              </h2>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="关闭作品立意面板"
            className="p-2 rounded-lg border border-[var(--rm-border)] text-[var(--rm-ink-secondary)] hover:text-[var(--rm-ink-primary)] hover:border-[var(--rm-gold)] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 md:p-8 space-y-7 max-h-[78vh] overflow-y-auto">
          {/* Section 1: Problem & Mission */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-stretch">
            <div className="md:col-span-7 p-5 rounded-xl border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)] space-y-3">
              <div className="flex items-center gap-2 text-xs font-serif text-[var(--rm-cinnabar-bright)] tracking-widest">
                <BookOpen className="w-4 h-4" />
                <span>时代痛点与文化使命</span>
              </div>
              <h3 className="text-lg font-serif font-bold leading-snug">
                石刻风化不可逆，墨拓残痕待新生；<br />
                以当代数字媒体，搭起千年金石与公众美育之桥。
              </h3>
              <p className="text-xs md:text-sm text-[var(--rm-ink-secondary)] leading-relaxed text-justify font-sans">
                历代石刻碑碣历经风雨剥蚀、锤拓磨损与纸墨斑驳，大量珍贵书法与史料正陷入不可逆的漫漶消逝；
                与此同时，繁难的繁体异体字、缺乏语境的冷冰冰馆藏图录，使普通公众望而却步。
                《墨韵智考》尝试以<strong className="text-[var(--rm-ink-primary)]">“抢救性数字保护 → 可验证算法复原 → 学术严谨释读 → 当代生活传播”</strong>
                四重闭环，将严肃的计算机视觉、三维图形学与金石文献学转化为可触摸、可共情、可带走的东方数字媒体体验。
              </p>
            </div>

            <div className="md:col-span-5 grid grid-cols-2 gap-3">
              <div className="p-4 rounded-xl border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)] flex flex-col justify-between">
                <span className="text-[11px] text-[var(--rm-ink-muted)] font-serif">跨七朝代真实馆藏</span>
                <div className="text-2xl rm-mono-metric font-bold text-[var(--rm-gold-light)] mt-2">
                  {verifiedCount} <span className="text-xs font-serif font-normal">通</span>
                </div>
                <span className="text-[10px] text-[var(--rm-ink-muted)] mt-1">84 幅独立授权影像 · 东汉至清</span>
              </div>
              <div className="p-4 rounded-xl border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)] flex flex-col justify-between">
                <span className="text-[11px] text-[var(--rm-ink-muted)] font-serif">可复现算法实证</span>
                <div className="text-2xl rm-mono-metric font-bold text-[var(--rm-celadon-light)] mt-2">
                  2,520 <span className="text-xs font-serif font-normal">条</span>
                </div>
                <span className="text-[10px] text-[var(--rm-ink-muted)] mt-1">9 种方法 × 280 退化受控实验</span>
              </div>
              <div className="p-4 rounded-xl border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)] flex flex-col justify-between">
                <span className="text-[11px] text-[var(--rm-ink-muted)] font-serif">三维金石与地形</span>
                <div className="text-2xl rm-mono-metric font-bold text-[var(--rm-cinnabar-bright)] mt-2">
                  3D <span className="text-xs font-serif font-normal">双引擎</span>
                </div>
                <span className="text-[10px] text-[var(--rm-ink-muted)] mt-1">Blender PBR 侧光碑刻 + 真实 DEM</span>
              </div>
              <div className="p-4 rounded-xl border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)] flex flex-col justify-between">
                <span className="text-[11px] text-[var(--rm-ink-muted)] font-serif">学术严谨底线</span>
                <div className="text-lg font-serif font-bold text-[var(--rm-ink-primary)] mt-2">
                  考据不臆造
                </div>
                <span className="text-[10px] text-[var(--rm-ink-muted)] mt-1">明确区分馆藏史料与 AI 推演边界</span>
              </div>
            </div>
          </div>

          {/* Section 2: 4-Layer Technical & Curatorial Graph */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-serif font-bold tracking-wider text-[var(--rm-gold)]">
                四维融合架构 · 视觉 × 3D × 史料 × 文创传播
              </h3>
              <span className="text-[11px] rm-mono-metric text-[var(--rm-ink-muted)]">
                React 18 · Three.js · Blender 5.2.2 · MapLibre · FastAPI · OpenCV · SQLite FTS5
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {ARCH_PILLARS.map((pillar) => {
                const Icon = pillar.icon;
                return (
                  <div
                    key={pillar.code}
                    className="p-4 rounded-xl border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)] hover:border-[var(--rm-border-strong)] transition-colors space-y-2.5"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <span className="w-8 h-8 rounded-lg bg-[var(--rm-gold-soft)] border border-[var(--rm-border-strong)] flex items-center justify-center text-[var(--rm-gold)]">
                          <Icon className="w-4 h-4" />
                        </span>
                        <div>
                          <span className="text-[10px] rm-mono-metric text-[var(--rm-ink-muted)] block">
                            {pillar.code}
                          </span>
                          <h4 className="font-serif font-bold text-sm">{pillar.title}</h4>
                        </div>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-serif border border-[var(--rm-border)] text-[var(--rm-ink-secondary)]">
                        {pillar.badge}
                      </span>
                    </div>
                    <p className="text-[11px] rm-mono-metric text-[var(--rm-gold)]">{pillar.subtitle}</p>
                    <p className="text-xs text-[var(--rm-ink-secondary)] leading-relaxed font-sans">
                      {pillar.desc}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Section 3: Academic Integrity Charter & Quick Jump */}
          <div className="p-4 rounded-xl border border-[var(--rm-celadon)]/35 bg-[var(--rm-celadon-soft)] flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-[var(--rm-celadon-light)] shrink-0 mt-0.5" />
              <div className="text-xs space-y-1">
                <p className="font-serif font-bold text-[var(--rm-ink-primary)]">
                  数字人文实证宣言：真实影像、可查出处、边界透明
                </p>
                <p className="text-[var(--rm-ink-secondary)] font-sans leading-relaxed">
                  无配对真值的古碑原拓不虚报 PSNR/SSIM；争议史料保留多方著录不武断选边；残字候选须经人工审定采纳并支持撤销。
                </p>
              </div>
            </div>
            {onNavigate && (
              <div className="flex flex-wrap gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onNavigate('workbench');
                  }}
                  className="px-3.5 py-2 rounded-lg text-xs font-serif font-bold bg-[var(--rm-cinnabar)] text-[#faf6ee] hover:brightness-110 transition-all inline-flex items-center gap-1 rm-keep-light-ink"
                >
                  <span>步入四重工坊</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onNavigate('reports');
                  }}
                  className="px-3.5 py-2 rounded-lg text-xs font-serif border border-[var(--rm-border-strong)] hover:border-[var(--rm-gold)] transition-colors"
                >
                  查看评测实证
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
};
