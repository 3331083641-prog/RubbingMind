import React from 'react';
import { useExperience } from '../context/ExperienceContext';
import { SealStamp } from './SealStamp';

export const Footer: React.FC = () => {
  const { showcaseMode, setManifestoOpen } = useExperience();
  if (showcaseMode) return null;

  return (
    <footer className="w-full bg-[var(--rm-bg-footer)] border-t border-[var(--rm-border)] py-5 px-4 select-none transition-colors duration-300">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between text-xs text-[var(--rm-ink-muted)] gap-3">
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
            作品立意 ↗
          </button>
        </div>

        <div className="flex items-center gap-3 text-[11px] font-mono text-[var(--rm-ink-muted)]">
          <span>Blender 5.2.2 · Three.js</span>
          <span>·</span>
          <span>2D-FFT · DEM · FTS5</span>
        </div>

        <div className="text-[11px] text-[var(--rm-ink-secondary)] font-serif">
          守望千年金石微痕
        </div>
      </div>
    </footer>
  );
};
