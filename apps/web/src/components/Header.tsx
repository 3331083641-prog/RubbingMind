import React, { useState } from 'react';
import { SteleItem } from '../types/stele';
import { Menu, X } from 'lucide-react';

interface HeaderProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
  steles: SteleItem[];
  selectedSteleId: string;
  onSelectStele: (id: string) => void;
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
}) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const choose = (id: string) => { onTabChange(id); setMenuOpen(false); };
  const selected = steles.find((item) => item.id === selectedSteleId);
  const selectedLabel = selected ? `[${selected.dynasty}] ${selected.title}` : '';

  return (
    <header className="sticky top-0 z-50 w-full bg-[#0C1113]/92 backdrop-blur-md border-b border-gold/20 shadow-card" data-testid="app-header">
      <div className="h-[68px] px-3 xl:px-5 grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-2">
        <div className="flex items-center gap-2 cursor-pointer group select-none" onClick={() => choose('home')}>
          <div className="w-10 h-10 shrink-0 rounded-lg bg-gradient-to-br from-cinnabar to-cinnabar-dark border border-cinnabar-light/60 flex items-center justify-center shadow-cinnabar-glow">
            <span className="text-paper-light font-serif font-black text-2xl tracking-tighter">墨</span>
          </div>
          <div className="flex flex-col min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-lg xl:text-xl font-serif font-bold text-white tracking-wider group-hover:text-gold">墨韵智考</span>
              <span className="text-[10px] font-sans font-medium px-1.5 py-0.5 rounded bg-gold/15 text-gold border border-gold/30">Pro 2.0</span>
            </div>
            <span className="hidden 2xl:inline text-[10px] text-slate-400 font-sans tracking-tight">金石碑拓频空域微痕修复与多模态考据平台</span>
          </div>
        </div>

        <nav className="hidden xl:flex items-center justify-center gap-0.5 min-w-0" aria-label="主导航" data-testid="primary-nav">
          {NAV_ITEMS.map((item) => {
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => choose(item.id)}
                className={`relative shrink-0 px-1.5 2xl:px-3 py-2 rounded-lg font-serif text-[13px] 2xl:text-sm whitespace-nowrap select-none ${isActive ? 'text-gold-light bg-gold/10 font-semibold' : 'text-slate-300 hover:text-white hover:bg-slate-800/40'}`}
              >
                <span className={`mr-1 text-xs ${isActive ? 'text-gold' : 'text-slate-500'}`}>{item.iconPrefix}</span>
                <span>{item.label}</span>
                {isActive && <span className="absolute bottom-0 left-2 right-2 h-[2px] bg-gradient-to-r from-transparent via-gold to-transparent rounded-full" />}
              </button>
            );
          })}
        </nav>

        <div className="flex items-center justify-end gap-2">
          <label className="relative hidden xl:flex items-center shrink-0 bg-xuan-panel/90 border border-gold/25 rounded-lg px-2 py-1.5 text-xs text-slate-300">
            <span className="hidden 2xl:inline text-slate-400 mr-2 text-[11px] shrink-0">当前碑刻</span>
            <span className="whitespace-nowrap font-serif text-xs text-gold-light pr-4">{selectedLabel}</span>
            <select aria-label="当前碑刻" value={selectedSteleId} onChange={(e) => onSelectStele(e.target.value)} className="absolute inset-0 cursor-pointer opacity-0">
              {steles.map((s) => <option key={s.id} value={s.id} className="bg-[#151C20] text-slate-200">[{s.dynasty}] {s.title}</option>)}
            </select>
          </label>
          <button type="button" className="xl:hidden p-2 rounded-lg border border-gold/30 text-gold" aria-expanded={menuOpen} aria-label={menuOpen ? '关闭主导航' : '打开主导航'} onClick={() => setMenuOpen((open) => !open)}>
            {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>
      {menuOpen && (
        <div className="xl:hidden border-t border-gold/20 bg-[#0C1113] px-3 py-3 flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <button key={item.id} onClick={() => choose(item.id)} className={`text-left px-3 py-2 rounded-lg font-serif text-sm ${currentTab === item.id ? 'text-gold-light bg-gold/10' : 'text-slate-300'}`}>
              {item.iconPrefix} {item.label}
            </button>
          ))}
          <label className="mt-2 text-xs text-slate-400">
            当前碑刻
            <select aria-label="当前碑刻" value={selectedSteleId} onChange={(e) => onSelectStele(e.target.value)} className="mt-1 w-full bg-[#151C20] text-gold-light border border-gold/25 rounded-lg px-2 py-2">
              {steles.map((s) => <option key={s.id} value={s.id}>[{s.dynasty}] {s.title}</option>)}
            </select>
          </label>
        </div>
      )}
    </header>
  );
};
