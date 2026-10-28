import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-[#080B0F] border-t border-gold/15 py-6 px-4 text-center select-none">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between text-xs text-slate-400 gap-4">
        {/* Left Info */}
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-gold" />
          <span className="font-serif text-slate-300 font-medium">墨韵智考</span>
        </div>

        {/* Center Tech Stack */}
        <div className="flex items-center space-x-4 text-[11px] text-slate-500 font-mono">
          <span>FastAPI + OpenCV</span>
          <span>•</span>
          <span>Three.js 3D 孪生</span>
          <span>•</span>
          <span>频空域联合去噪</span>
          <span>•</span>
          <span>GraphRAG 时空图谱</span>
        </div>

        {/* Right Epigraphic Disclaimer */}
        <div className="text-[11px] text-slate-400">
          中华古籍碑刻微痕增强与辅助释读数字实验室 · 金石学与计算机视觉融合
        </div>
      </div>
    </footer>
  );
};
