import React from 'react';
import { useExperience } from '../context/ExperienceContext';
import { SealStamp } from './SealStamp';

export const Footer: React.FC = () => {
  const { showcaseMode, setManifestoOpen } = useExperience();
  if (showcaseMode) return null;

  return (
    <footer className="w-full bg-[var(--rm-bg-footer)] border-t border-[var(--rm-border)] py-6 px-4 text-center select-none transition-colors duration-300">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between text-xs text-[var(--rm-ink-muted)] gap-4">
        {/* Left Info */}
        <div className="flex items-center space-x-2.5">
          <SealStamp text="金石" variant="zhuwen" size="xs" />
          <span className="font-serif text-[var(--rm-ink-primary)] font-semibold tracking-wider">
            墨韵智考 · RubbingMind
          </span>
          <button
            type="button"
            onClick={() => setManifestoOpen(true)}
            className="text-[11px] font-serif text-[var(--rm-gold)] hover:underline ml-1"
          >
            作品立意与技术图谱 ↗
          </button>
        </div>

        {/* Center Tech Stack */}
        <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-[11px] text-[var(--rm-ink-muted)] font-mono">
          <span>Blender 5.2.2 + Three.js PBR</span>
          <span>•</span>
          <span>2D-FFT 频空域自适应</span>
          <span>•</span>
          <span>DEM 三维舆图</span>
          <span>•</span>
          <span>有据史料检索</span>
        </div>

        {/* Right Epigraphic Colophon */}
        <div className="text-[11px] text-[var(--rm-ink-secondary)] font-serif">
          以当代数字媒体，守望千年贞石微痕 · 考据与推演边界明晰
        </div>
      </div>
    </footer>
  );
};
