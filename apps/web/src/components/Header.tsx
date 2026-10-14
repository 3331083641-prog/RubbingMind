import React from 'react';
import { SteleItem } from '../types/stele';
import { Sparkles, Layers, BookOpen, Network, FileBarChart2, Upload, RefreshCw, CheckCircle2 } from 'lucide-react';

interface HeaderProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
  steles: SteleItem[];
  selectedSteleId: string;
  onSelectStele: (id: string) => void;
  onOpenUpload: () => void;
  isBackendConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  onTabChange,
  steles,
  selectedSteleId,
  onSelectStele,
  onOpenUpload,
  isBackendConnected
}) => {
  const navItems = [
    { id: 'home', label: '首页门户', icon: Sparkles, iconPrefix: '◈' },
    { id: 'museum', label: '贞石典藏馆', icon: BookOpen, iconPrefix: '❖' },
    { id: 'workbench', label: '智考工作台', icon: Layers, iconPrefix: '✦' },
    { id: 'graph', label: '时空图谱中心', icon: Network, iconPrefix: '◎' },
    { id: 'reports', label: '算法评测报告', icon: FileBarChart2, iconPrefix: '▤' },
  ];

  return (
    <header className="sticky top-0 z-50 h-[68px] w-full bg-[#0C1113]/90 backdrop-blur-md border-b border-gold/20 px-4 lg:px-8 flex items-center justify-between shadow-card">
      {/* Brand Identity */}
      <div 
        className="flex items-center space-x-3 cursor-pointer group select-none whitespace-nowrap"
        onClick={() => onTabChange('home')}
      >
        {/* Red Cinnabar Square Seal Logo */}
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cinnabar to-cinnabar-dark border border-cinnabar-light/60 flex items-center justify-center shadow-cinnabar-glow transition-transform duration-300 group-hover:scale-105">
          <span className="text-paper-light font-serif font-black text-2xl tracking-tighter">墨</span>
        </div>
        
        {/* Title */}
        <div className="flex flex-col">
          <div className="flex items-center space-x-2">
            <span className="text-xl font-serif font-bold text-white tracking-wider group-hover:text-gold transition-colors">
              墨韵智考
            </span>
            <span className="text-[11px] font-sans font-medium px-2 py-0.5 rounded bg-gold/15 text-gold border border-gold/30">
              Pro 2.0
            </span>
          </div>
          <span className="text-[10px] text-slate-400 font-sans tracking-tight hidden sm:inline">
            金石碑拓频空域微痕修复与多模态考据平台
          </span>
        </div>
      </div>

      {/* Main Tab Navigation */}
      <nav className="flex items-center space-x-1 lg:space-x-2 overflow-x-auto no-scrollbar py-1">
        {navItems.map((item) => {
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`relative px-3.5 py-2 rounded-lg font-serif text-sm transition-all duration-300 flex items-center space-x-1.5 whitespace-nowrap select-none ${
                isActive
                  ? 'text-gold-light bg-gold/10 font-semibold shadow-gold-glow'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <span className={`text-xs ${isActive ? 'text-gold' : 'text-slate-500'}`}>
                {item.iconPrefix}
              </span>
              <span>{item.label}</span>
              {isActive && (
                <span className="absolute bottom-0 left-2 right-2 h-[2px] bg-gradient-to-r from-transparent via-gold to-transparent rounded-full shadow-[0_0_8px_#D4AF37]" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Right Controls */}
      <div className="flex items-center space-x-3 whitespace-nowrap">
        {/* Stele Quick Switcher */}
        <div className="hidden md:flex items-center bg-xuan-panel/90 border border-gold/25 rounded-lg px-2.5 py-1.5 text-xs text-slate-300">
          <span className="text-slate-400 mr-2 text-[11px]">当前碑刻:</span>
          <select
            value={selectedSteleId}
            onChange={(e) => onSelectStele(e.target.value)}
            className="bg-transparent text-gold-light font-serif text-xs outline-none cursor-pointer pr-1"
          >
            {steles.map((s) => (
              <option key={s.id} value={s.id} className="bg-[#151C20] text-slate-200">
                [{s.dynasty}] {s.title}
              </option>
            ))}
          </select>
        </div>

        {/* Upload Button */}
        <button
          onClick={onOpenUpload}
          className="px-3.5 py-1.5 rounded-lg text-xs font-serif font-medium bg-gradient-to-r from-cinnabar to-cinnabar-dark text-paper-light border border-cinnabar-light/40 shadow-cinnabar-glow hover:brightness-110 active:scale-95 transition-all flex items-center space-x-1.5"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>上传拓片</span>
        </button>

        {/* Backend Online Indicator */}
        <div 
          className="hidden xl:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-900/60 border border-slate-700/60 text-[11px] text-slate-400"
          title={isBackendConnected ? "后端 FastAPI 运行于 http://127.0.0.1:8000" : "使用本地双保险数据"}
        >
          <span className={`w-2 h-2 rounded-full ${isBackendConnected ? 'bg-celadon-light animate-pulse' : 'bg-gold'}`} />
          <span className="font-sans font-mono">{isBackendConnected ? 'FastAPI 在线' : '本地离线'}</span>
        </div>
      </div>
    </header>
  );
};
