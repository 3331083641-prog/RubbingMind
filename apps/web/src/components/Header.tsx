import React, { useState } from 'react';
import { SteleItem } from '../types/stele';
import { Menu, X, Sun, Moon, MonitorPlay, ScrollText } from 'lucide-react';
import { useExperience } from '../context/ExperienceContext';
import { SealStamp } from './SealStamp';

interface HeaderProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
  steles: SteleItem[];
  selectedSteleId: string;
  onSelectStele: (id: string) => void;
  isBackendConnected?: boolean;
  catalogueStatus?: 'loading' | 'ready' | 'fallback';
}

const NAV_ITEMS = [
  { id: 'home', label: '首页门户', iconPrefix: '◈' },
  { id: 'museum', label: '贞石典藏馆', iconPrefix: '❖' },
  { id: 'workbench', label: '智考工作台', iconPrefix: '✦' },
  { id: 'graph', label: '时空图谱中心', iconPrefix: '◎' },
  { id: 'reports', label: '算法评测报告', iconPrefix: '▤' },
];

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  onTabChange,
  steles,
  selectedSteleId,
  onSelectStele,
  catalogueStatus = 'ready',
}) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const { theme, toggleTheme, showcaseMode, toggleShowcaseMode, setManifestoOpen } = useExperience();
  const choose = (id: string) => {
    onTabChange(id);
    setMenuOpen(false);
  };
  const selected = steles.find((item) => item.id === selectedSteleId);
  const selectedLabel = selected ? `[${selected.dynasty}] ${selected.title}` : '';

  if (showcaseMode) {
    return null;
  }

  return (
    <header
      className="sticky top-0 z-50 w-full bg-[var(--rm-bg-header)] backdrop-blur-xl border-b border-[var(--rm-border)] shadow-card transition-colors duration-300"
      data-testid="app-header"
    >
      <div className="h-[68px] px-3 xl:px-5 grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-2">
        {/* Brand Emblem */}
        <div
          className="flex items-center gap-2.5 cursor-pointer group select-none"
          onClick={() => choose('home')}
        >
          <SealStamp
            text="墨"
            variant="baiwen"
            size="md"
            className="group-hover:scale-105 transition-transform duration-300"
            title="墨韵智考"
          />
          <div className="flex flex-col min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-lg xl:text-xl font-serif font-bold text-[var(--rm-ink-primary)] tracking-[0.08em] group-hover:text-[var(--rm-gold)] transition-colors">
                墨韵智考
              </span>
              {catalogueStatus === 'fallback' ? (
                <span
                  data-testid="demo-seal-badge"
                  title="后端未连接，已启用本地典藏演示态"
                  className="text-[10px] font-serif px-1.5 py-0.5 rounded-[3px] bg-[var(--rm-cinnabar-soft)] text-[var(--rm-cinnabar-bright)] border border-[var(--rm-cinnabar)]/45 whitespace-nowrap"
                >
                  演示态
                </span>
              ) : null}
            </div>
          </div>
        </div>

        {/* Center Navigation (Exact accessible button labels preserved for CI) */}
        <nav
          className="hidden xl:flex items-center justify-center gap-1 min-w-0"
          aria-label="主导航"
          data-testid="primary-nav"
        >
          {NAV_ITEMS.map((item) => {
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => choose(item.id)}
                className={`relative shrink-0 px-2.5 2xl:px-3.5 py-2 rounded-lg font-serif text-[13px] 2xl:text-sm whitespace-nowrap select-none transition-all duration-200 ${
                  isActive
                    ? 'text-[var(--rm-gold-light)] bg-[var(--rm-gold-soft)] font-semibold'
                    : 'text-[var(--rm-ink-secondary)] hover:text-[var(--rm-ink-primary)] hover:bg-[var(--rm-bg-subtle)]'
                }`}
              >
                <span
                  className={`mr-1 text-[11px] ${
                    isActive ? 'text-[var(--rm-cinnabar-bright)]' : 'text-[var(--rm-ink-muted)]'
                  }`}
                >
                  {item.iconPrefix}
                </span>
                <span>{item.label}</span>
                {isActive && (
                  <span className="absolute bottom-0.5 left-3 right-3 h-[2px] bg-gradient-to-r from-transparent via-[var(--rm-cinnabar)] to-transparent rounded-full" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Right Utility Cluster: Stele Picker + Dual Theme + Manifesto + Showcase */}
        <div className="flex items-center justify-end gap-1.5">
          <label className="relative hidden xl:flex items-center shrink-0 bg-[var(--rm-bg-surface)] border border-[var(--rm-border)] hover:border-[var(--rm-border-strong)] rounded-lg px-2.5 py-1.5 text-xs transition-colors">
            <span className="hidden 2xl:inline text-[var(--rm-ink-muted)] mr-2 text-[11px] shrink-0 font-serif">
              当前碑刻
            </span>
            <span className="whitespace-nowrap font-serif text-xs text-[var(--rm-gold-light)] max-w-[175px] truncate pr-3">
              {selectedLabel}
            </span>
            <select
              aria-label="当前碑刻"
              value={selectedSteleId}
              onChange={(e) => onSelectStele(e.target.value)}
              className="absolute inset-0 cursor-pointer opacity-0"
            >
              {steles.map((s) => (
                <option key={s.id} value={s.id} className="bg-[#151C20] text-slate-200">
                  [{s.dynasty}] {s.title}
                </option>
              ))}
            </select>
          </label>

          {/* Theme Switcher: 玄石暗馆 <-> 素宣书斋 */}
          <button
            type="button"
            data-testid="theme-toggle"
            onClick={toggleTheme}
            title={theme === 'obsidian' ? '切换至素宣书斋（浅色宣纸主题）' : '切换至玄石暗馆（深色青石主题）'}
            className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[var(--rm-border)] hover:border-[var(--rm-gold)] bg-[var(--rm-bg-surface)] text-xs font-serif text-[var(--rm-ink-secondary)] hover:text-[var(--rm-gold-light)] transition-colors"
          >
            {theme === 'obsidian' ? (
              <>
                <Sun className="w-3.5 h-3.5 text-[var(--rm-gold)]" />
                <span className="hidden 2xl:inline">素宣</span>
              </>
            ) : (
              <>
                <Moon className="w-3.5 h-3.5 text-[var(--rm-cinnabar)]" />
                <span className="hidden 2xl:inline">玄石</span>
              </>
            )}
          </button>

          {/* Curatorial Manifesto & Tech Graph */}
          <button
            type="button"
            data-testid="manifesto-button"
            onClick={() => setManifestoOpen(true)}
            title="查看作品立意与全栈技术图谱"
            className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[var(--rm-border)] hover:border-[var(--rm-cinnabar)] bg-[var(--rm-bg-surface)] text-xs font-serif text-[var(--rm-ink-secondary)] hover:text-[var(--rm-cinnabar-bright)] transition-colors"
          >
            <ScrollText className="w-3.5 h-3.5 text-[var(--rm-cinnabar-bright)]" />
            <span className="hidden 2xl:inline">立意图谱</span>
          </button>

          {/* Competition 16:9 Showcase Mode */}
          <button
            type="button"
            data-testid="showcase-toggle"
            onClick={toggleShowcaseMode}
            title="开启 16:9 纯净展演模式（适配录屏与展板截图，按 Esc 退出）"
            className="hidden lg:inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[var(--rm-cinnabar)]/40 bg-[var(--rm-cinnabar-soft)] text-xs font-serif text-[var(--rm-cinnabar-bright)] hover:bg-[var(--rm-cinnabar)] hover:text-[#faf6ee] transition-all"
          >
            <MonitorPlay className="w-3.5 h-3.5" />
            <span className="hidden 2xl:inline">展演</span>
          </button>

          <button
            type="button"
            className="xl:hidden p-2 rounded-lg border border-[var(--rm-border-strong)] text-[var(--rm-gold)]"
            aria-expanded={menuOpen}
            aria-label={menuOpen ? '关闭主导航' : '打开主导航'}
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Responsive Mobile Drawer */}
      {menuOpen && (
        <div className="xl:hidden border-t border-[var(--rm-border)] bg-[var(--rm-bg-elevated)] px-4 py-3 flex flex-col gap-1.5">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => choose(item.id)}
              className={`text-left px-3 py-2 rounded-lg font-serif text-sm ${
                currentTab === item.id
                  ? 'text-[var(--rm-gold-light)] bg-[var(--rm-gold-soft)] font-semibold'
                  : 'text-[var(--rm-ink-secondary)]'
              }`}
            >
              {item.iconPrefix} {item.label}
            </button>
          ))}
          <label className="mt-2 text-xs text-[var(--rm-ink-muted)] font-serif">
            当前碑刻
            <select
              aria-label="当前碑刻"
              value={selectedSteleId}
              onChange={(e) => onSelectStele(e.target.value)}
              className="mt-1 w-full bg-[var(--rm-bg-surface)] text-[var(--rm-gold-light)] border border-[var(--rm-border)] rounded-lg px-2 py-2"
            >
              {steles.map((s) => (
                <option key={s.id} value={s.id}>
                  [{s.dynasty}] {s.title}
                </option>
              ))}
            </select>
          </label>
          <div className="mt-2 pt-2 border-t border-[var(--rm-border)] flex flex-wrap gap-2">
            <button
              type="button"
              onClick={toggleTheme}
              className="px-3 py-1.5 rounded-lg border border-[var(--rm-border)] text-xs font-serif flex items-center gap-1.5"
            >
              {theme === 'obsidian' ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
              <span>{theme === 'obsidian' ? '切换素宣书斋' : '切换玄石暗馆'}</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setMenuOpen(false);
                setManifestoOpen(true);
              }}
              className="px-3 py-1.5 rounded-lg border border-[var(--rm-border)] text-xs font-serif flex items-center gap-1.5"
            >
              <ScrollText className="w-3.5 h-3.5 text-[var(--rm-cinnabar-bright)]" />
              <span>作品立意与技术图谱</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setMenuOpen(false);
                toggleShowcaseMode();
              }}
              className="px-3 py-1.5 rounded-lg bg-[var(--rm-cinnabar-soft)] border border-[var(--rm-cinnabar)]/40 text-[var(--rm-cinnabar-bright)] text-xs font-serif flex items-center gap-1.5"
            >
              <MonitorPlay className="w-3.5 h-3.5" />
              <span>纯净展演模式</span>
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
