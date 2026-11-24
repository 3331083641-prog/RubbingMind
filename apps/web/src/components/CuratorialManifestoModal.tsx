import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, Layers, Compass, Sparkles, ShieldCheck, Box, ArrowUpRight } from 'lucide-react';
import { SealStamp } from './SealStamp';

interface CuratorialManifestoModalProps {
  isOpen: boolean;
  onClose: () => void;
  verifiedCount: number;
  onNavigate?: (tab: string) => void;
}

const ARCH_PILLARS = [
  {
    code: '01',
    title: '三维侧光鉴刻',
    subtitle: 'Blender PBR · WebGL · Raking Light',
    desc: '高精雕刻唐风双龙青石碑，拖动斜射光角度重现千年刀锋。',
    icon: Box,
  },
  {
    code: '02',
    title: '频空域微痕复原',
    subtitle: '2D-FFT · Fast NLM · 保真门控',
    desc: '自适应频谱去噪并保留原图门控，全链路 SHA-256 可溯源。',
    icon: Layers,
  },
  {
    code: '03',
    title: '有据史料与舆图',
    subtitle: 'SQLite FTS5 · 真实 DEM · 四级证据',
    desc: '28 件七朝代授权馆藏实证检索，严格划清史实与推演边界。',
    icon: Compass,
  },
  {
    code: '04',
    title: '当代美育留痕',
    subtitle: '双栏释读 · 碑帖藏品卡 · 高清 PNG',
    desc: '摘句落印生成宣纸书签与当代海报，让古老碑刻重回日常。',
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
      <div className="relative w-full max-w-4xl rounded-2xl border border-[var(--rm-border-strong)] bg-[var(--rm-bg-elevated)] text-[var(--rm-ink-primary)] shadow-[var(--rm-shadow-float)] overflow-hidden my-auto rm-animate-unscroll">
        <div className="h-1 w-full bg-gradient-to-r from-transparent via-[var(--rm-cinnabar)] to-transparent opacity-80" />

        <div className="flex items-center justify-between gap-4 px-6 py-4 border-b border-[var(--rm-border)]">
          <div className="flex items-center gap-3.5">
            <SealStamp text="金石传拓" variant="baiwen" size="sm" />
            <div>
              <span className="text-[10px] rm-mono-metric tracking-[0.22em] uppercase text-[var(--rm-gold)] block">
                CURATORIAL MANIFESTO
              </span>
              <h2 className="text-lg md:text-xl font-serif font-bold tracking-wide">
                墨韵智考 · 作品立意与技术图谱
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

        <div className="p-6 space-y-6 max-h-[78vh] overflow-y-auto">
          {/* Core Mission & Key Figures */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-center">
            <div className="md:col-span-7 space-y-2">
              <h3 className="text-lg font-serif font-bold leading-snug">
                石刻风化不可逆，墨拓微痕待新生
              </h3>
              <p className="text-xs md:text-sm text-[var(--rm-ink-secondary)] leading-relaxed font-sans">
                以「保护 → 复原 → 释读 → 留痕」四重闭环，将计算机视觉、三维图形学与金石文献转化为可触摸的当代数字美育体验。
              </p>
            </div>
            <div className="md:col-span-5 grid grid-cols-3 gap-2.5 text-center">
              <div className="p-3 rounded-xl border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)]">
                <div className="text-xl rm-mono-metric font-bold text-[var(--rm-gold-light)]">{verifiedCount}</div>
                <span className="text-[10px] text-[var(--rm-ink-muted)] font-serif">授权馆藏</span>
              </div>
              <div className="p-3 rounded-xl border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)]">
                <div className="text-xl rm-mono-metric font-bold text-[var(--rm-celadon-light)]">2,520</div>
                <span className="text-[10px] text-[var(--rm-ink-muted)] font-serif">受控实验</span>
              </div>
              <div className="p-3 rounded-xl border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)]">
                <div className="text-xl rm-mono-metric font-bold text-[var(--rm-cinnabar-bright)]">PBR</div>
                <span className="text-[10px] text-[var(--rm-ink-muted)] font-serif">侧光碑刻</span>
              </div>
            </div>
          </div>

          {/* 4 Pillars */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {ARCH_PILLARS.map((pillar) => {
              const Icon = pillar.icon;
              return (
                <div
                  key={pillar.code}
                  className="p-4 rounded-xl border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)] space-y-2"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="w-8 h-8 rounded-lg bg-[var(--rm-gold-soft)] border border-[var(--rm-border-strong)] flex items-center justify-center text-[var(--rm-gold)]">
                      <Icon className="w-4 h-4" />
                    </span>
                    <div>
                      <h4 className="font-serif font-bold text-sm">{pillar.title}</h4>
                      <span className="text-[10px] rm-mono-metric text-[var(--rm-gold)]">{pillar.subtitle}</span>
                    </div>
                  </div>
                  <p className="text-xs text-[var(--rm-ink-secondary)] leading-relaxed font-sans">{pillar.desc}</p>
                </div>
              );
            })}
          </div>

          {/* Compact Integrity Strip */}
          <div className="px-4 py-3 rounded-xl border border-[var(--rm-celadon)]/35 bg-[var(--rm-celadon-soft)] flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[var(--rm-celadon-light)] shrink-0" />
              <span className="font-serif text-[var(--rm-ink-primary)]">
                实证底线：无真值不虚报指标 · 争议不选边 · 采纳须人工确认
              </span>
            </div>
            {onNavigate && (
              <button
                type="button"
                onClick={() => {
                  onClose();
                  onNavigate('workbench');
                }}
                className="px-3.5 py-1.5 rounded-lg text-xs font-serif font-bold bg-[var(--rm-cinnabar)] text-[#faf6ee] hover:brightness-110 inline-flex items-center gap-1 rm-keep-light-ink"
              >
                <span>步入工坊</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
};
