import React from 'react';
import { MonitorPlay, X, ChevronLeft, ChevronRight, Sun, Moon } from 'lucide-react';
import { useExperience } from '../context/ExperienceContext';
import { SealStamp } from './SealStamp';

interface ShowcaseGuideBarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
}

const CHAPTERS = [
  { id: 'home', index: '壹', label: '拂尘见字 · 序章' },
  { id: 'museum', index: '贰', label: '贞石典藏 · 碑林' },
  { id: 'workbench', index: '叁', label: '观复释留 · 工坊' },
  { id: 'graph', index: '肆', label: '山河金石 · 舆图' },
  { id: 'reports', index: '伍', label: '算法实证 · 评测' },
];

/**
 * 16:9 1080P 纯净展演模式导览条（支持平滑导览切换与 Esc 退出）
 */
export const ShowcaseGuideBar: React.FC<ShowcaseGuideBarProps> = ({ currentTab, onTabChange }) => {
  const { showcaseMode, setShowcaseMode, theme, toggleTheme } = useExperience();

  if (!showcaseMode) return null;

  const activeIdx = Math.max(0, CHAPTERS.findIndex((c) => c.id === currentTab));
  const goPrev = () => onTabChange(CHAPTERS[(activeIdx - 1 + CHAPTERS.length) % CHAPTERS.length].id);
  const goNext = () => onTabChange(CHAPTERS[(activeIdx + 1) % CHAPTERS.length].id);

  return (
    <div
      data-testid="showcase-guide-bar"
      className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[95] flex items-center gap-2 px-3 py-2 rounded-full border border-[var(--rm-border-strong)] bg-[var(--rm-bg-surface-strong)] backdrop-blur-xl shadow-[var(--rm-shadow-float)] text-xs"
    >
      <div className="flex items-center gap-2 pr-2 border-r border-[var(--rm-border)]">
        <SealStamp text="展演" variant="baiwen" size="xs" />
        <span className="hidden sm:inline font-serif font-semibold text-[var(--rm-gold)] whitespace-nowrap flex items-center gap-1">
          <MonitorPlay className="w-3.5 h-3.5" />
          纯净展演
        </span>
      </div>

      <button
        type="button"
        onClick={goPrev}
        aria-label="上一展演章节"
        className="p-1.5 rounded-full hover:bg-[var(--rm-gold-soft)] text-[var(--rm-ink-secondary)] hover:text-[var(--rm-ink-primary)] transition-colors"
      >
        <ChevronLeft className="w-4 h-4" />
      </button>

      <div className="flex items-center gap-1">
        {CHAPTERS.map((chap) => {
          const active = chap.id === currentTab;
          return (
            <button
              key={chap.id}
              type="button"
              onClick={() => onTabChange(chap.id)}
              className={`px-2.5 py-1 rounded-full font-serif transition-all whitespace-nowrap ${
                active
                  ? 'bg-[var(--rm-cinnabar)] text-[#faf6ee] font-semibold rm-keep-light-ink shadow-sm'
                  : 'text-[var(--rm-ink-secondary)] hover:text-[var(--rm-ink-primary)] hover:bg-[var(--rm-bg-subtle)]'
              }`}
            >
              <span className="opacity-70 mr-1">{chap.index}</span>
              <span className="hidden md:inline">{chap.label}</span>
            </button>
          );
        })}
      </div>

      <button
        type="button"
        onClick={goNext}
        aria-label="下一展演章节"
        className="p-1.5 rounded-full hover:bg-[var(--rm-gold-soft)] text-[var(--rm-ink-secondary)] hover:text-[var(--rm-ink-primary)] transition-colors"
      >
        <ChevronRight className="w-4 h-4" />
      </button>

      <div className="flex items-center gap-1 pl-2 border-l border-[var(--rm-border)]">
        <button
          type="button"
          onClick={toggleTheme}
          title={theme === 'obsidian' ? '切换至素宣书斋浅色主题' : '切换至玄石暗馆深色主题'}
          className="p-1.5 rounded-full hover:bg-[var(--rm-gold-soft)] text-[var(--rm-gold)] transition-colors"
        >
          {theme === 'obsidian' ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
        </button>
        <button
          type="button"
          onClick={() => setShowcaseMode(false)}
          title="退出纯净展演模式 (Esc)"
          className="px-2.5 py-1 rounded-full border border-[var(--rm-border)] hover:border-[var(--rm-cinnabar)] text-[var(--rm-ink-secondary)] hover:text-[var(--rm-cinnabar-bright)] transition-colors inline-flex items-center gap-1 font-serif"
        >
          <X className="w-3.5 h-3.5" />
          <span>退出</span>
        </button>
      </div>
    </div>
  );
};
