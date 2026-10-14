import React from 'react';
import { SteleViewer } from './SteleViewer';
import { X, Layers, Sparkles } from 'lucide-react';

interface SteleFullscreenViewerProps {
  isOpen: boolean;
  onClose: () => void;
  customRubbingUrl?: string;
  steleTitle?: string;
  onOpenWorkbench?: () => void;
}

export const SteleFullscreenViewer: React.FC<SteleFullscreenViewerProps> = ({
  isOpen,
  onClose,
  customRubbingUrl,
  steleTitle = '金石碑刻 · 三维数字孪生大屏',
  onOpenWorkbench,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md animate-fadeIn">
      {/* Top Floating Controls */}
      <div className="absolute top-4 left-6 right-6 z-40 flex items-center justify-between pointer-events-none">
        <div className="flex items-center space-x-3 pointer-events-auto bg-slate-900/90 border border-gold/40 px-4 py-2 rounded-2xl shadow-2xl backdrop-blur-md">
          <div className="w-7 h-7 rounded-lg bg-cinnabar flex items-center justify-center font-serif text-white font-bold text-sm">
            墨
          </div>
          <div>
            <h3 className="text-sm font-serif font-bold text-gold-light">{steleTitle}</h3>
            <p className="text-[10px] text-slate-400 font-sans">
              鼠标左键自由旋转 · 滚轮远近缩放 · 右键平移视野 · 视角快速归位
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 pointer-events-auto">
          {onOpenWorkbench && (
            <button
              onClick={() => {
                onClose();
                onOpenWorkbench();
              }}
              className="px-4 py-2 rounded-xl bg-gold text-slate-950 font-serif font-bold text-xs shadow-gold-glow hover:brightness-110 active:scale-95 transition-all flex items-center space-x-1.5"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>载入工作台深度微痕修复</span>
            </button>
          )}

          <button
            onClick={onClose}
            className="p-2.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 transition-all shadow-card"
            title="退出全屏"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Main 3D Canvas */}
      <div className="w-full h-full">
        <SteleViewer
          customRubbingUrl={customRubbingUrl}
          steleTitle={steleTitle}
          onOpenWorkbench={() => {
            onClose();
            if (onOpenWorkbench) onOpenWorkbench();
          }}
          onToggleFullscreen={onClose}
          isFullscreen={true}
          showControls={true}
        />
      </div>
    </div>
  );
};
