import React, { useState } from 'react';
import { CORE_SAMPLES } from '../data/catalogSelection';
import { SteleItem } from '../types/stele';
import { SteleViewer } from '../components/stele3d/SteleViewer';
import { SteleFullscreenViewer } from '../components/stele3d/SteleFullscreenViewer';
import { ArrowRight, Layers, Network, ShieldCheck, Compass, Sparkles, BookOpen, Award, BarChart3, ScanLine } from 'lucide-react';

interface HomePageProps {
  steles: SteleItem[];
  onSelectStele: (id: string) => void;
  onNavigate: (tab: string) => void;
}

export const HomePage: React.FC<HomePageProps> = ({ steles, onSelectStele, onNavigate }) => {
  const currentStele = CORE_SAMPLES[0];
  const [isFullscreen3D, setIsFullscreen3D] = useState(false);

  return (
    <div className="min-h-screen bg-[#0A0D12] text-slate-100 flex flex-col space-y-12 pb-16">
      {/* 1. Hero Section */}
      <section className="relative w-full pt-8 pb-12 px-4 lg:px-12 overflow-hidden bg-gradient-to-b from-[#0F1419] via-[#0A0D12] to-[#0A0D12] border-b border-gold/15">
        {/* Subtle Background Ink Mountains Texture */}
        <div 
          className="absolute inset-0 opacity-15 pointer-events-none bg-center bg-cover mix-blend-screen"
          style={{ backgroundImage: `url('/assets/stele/backgrounds/bg_home_ink_landscape.png')` }}
        />
        
        {/* Ambient Top Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[720px] h-[300px] bg-gradient-to-b from-gold/15 to-transparent blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
          {/* Left Text / Info (Col 7) */}
          <div className="lg:col-span-7 flex flex-col space-y-6">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-gold/10 border border-gold/30 text-gold-light text-xs font-serif w-fit">
              <span className="w-1.5 h-1.5 rounded-full bg-cinnabar animate-pulse" />
              <span>全球校园人工智能算法精英大赛 · 智能文化赛道</span>
            </div>

            <div className="space-y-3">
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-serif font-black tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-paper-light via-gold-light to-gold">
                墨韵智考
              </h1>
              <p className="text-lg md:text-xl font-serif text-gold/90 font-medium">
                基于频空域联合去噪与多模态智能体的金石碑拓微痕修复及史料考据系统
              </p>
            </div>

            <p className="text-slate-300 font-sans text-sm md:text-base leading-relaxed max-w-2xl text-justify">
              针对历代传世金石碑拓因自然风化、漫漶残缺、纸墨斑驳及拓工织纹干扰造成的字口微痕丢失难题，
              系统开创性融合 <span className="text-gold font-serif">二维傅里叶变换频域陷波</span> 与 <span className="text-gold font-serif">空域快速非局部均值保边滤波</span>，
              并构筑 <span className="text-celadon-light font-serif">GraphRAG 时空知识图谱</span> 与 <span className="text-celadon-light font-serif">贝叶斯字形残缺推演引擎</span>，
              实现从“物理微痕恢复”到“史实多源互勘”的全链条数字人文科研范式。
            </p>

            {/* 4 Stats Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
              <div className="glass-panel p-3.5 rounded-xl border border-gold/20 flex flex-col">
                <span className="text-[11px] text-slate-400 font-serif">去噪信噪比增益</span>
                <div className="text-2xl font-serif font-bold text-gold-light mt-1">+18.6 <span className="text-xs font-normal">dB</span></div>
                <span className="text-[10px] text-celadon-light mt-0.5">演示指标；不代表馆藏实测</span>
              </div>
              <div className="glass-panel p-3.5 rounded-xl border border-gold/20 flex flex-col">
                <span className="text-[11px] text-slate-400 font-serif">残字推演置信度</span>
                <div className="text-2xl font-serif font-bold text-cinnabar-light mt-1">97.4 <span className="text-xs font-normal">%</span></div>
                <span className="text-[10px] text-slate-400 mt-0.5">多模态字形拓扑对齐</span>
              </div>
              <div className="glass-panel p-3.5 rounded-xl border border-gold/20 flex flex-col">
                <span className="text-[11px] text-slate-400 font-serif">历代碑拓标本</span>
                <div className="text-2xl font-serif font-bold text-slate-100 mt-1">120 <span className="text-xs font-normal">通+</span></div>
                <span className="text-[10px] text-slate-400 mt-0.5">覆盖汉隶/魏碑/盛唐楷书</span>
              </div>
              <div className="glass-panel p-3.5 rounded-xl border border-gold/20 flex flex-col">
                <span className="text-[11px] text-slate-400 font-serif">金石时空实体</span>
                <div className="text-2xl font-serif font-bold text-celadon-light mt-1">350 <span className="text-xs font-normal">个+</span></div>
                <span className="text-[10px] text-slate-400 mt-0.5">GraphRAG 历史谱系网络</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <button
                onClick={() => {
                  onSelectStele(currentStele.id);
                  onNavigate('workbench');
                }}
                className="px-6 py-3 rounded-xl font-serif font-bold text-sm bg-gradient-to-r from-gold to-gold-dark text-slate-950 shadow-gold-glow hover:brightness-110 active:scale-95 transition-all flex items-center space-x-2"
              >
                <Layers className="w-4 h-4" />
                <span>进入智考修复工作台</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={() => onNavigate('museum')}
                className="px-6 py-3 rounded-xl font-serif font-medium text-sm glass-panel text-slate-200 hover:text-gold border border-gold/30 hover:border-gold/60 transition-all flex items-center space-x-2"
              >
                <BookOpen className="w-4 h-4 text-gold" />
                <span>浏览中华贞石典藏馆</span>
              </button>

              <button
                onClick={() => onNavigate('graph')}
                className="px-5 py-3 rounded-xl font-serif font-medium text-sm text-slate-300 hover:text-celadon-light transition-colors flex items-center space-x-1.5"
              >
                <Network className="w-4 h-4 text-celadon" />
                <span>时空图谱与 GIS 考据</span>
              </button>
            </div>
          </div>

          {/* Right 3D Stele Scene (Col 5) - Museum Grade High Fidelity 3D Showcase */}
          <div className="lg:col-span-5 relative h-[560px] rounded-2xl overflow-hidden border border-gold/30 glass-panel shadow-2xl flex flex-col">
            <SteleViewer
              customRubbingUrl={currentStele?.damaged_image}
              steleTitle="唐风龙纹石碑 · 三维数字展陈示意"
              onOpenWorkbench={() => {
                if (currentStele) onSelectStele(currentStele.id);
                onNavigate('workbench');
              }}
              onToggleFullscreen={() => setIsFullscreen3D(true)}
              isFullscreen={false}
              showControls={true}
            />
          </div>
        </div>

        {/* Fullscreen 3D Viewer Modal */}
        <SteleFullscreenViewer
          isOpen={isFullscreen3D}
          onClose={() => setIsFullscreen3D(false)}
          customRubbingUrl={currentStele?.damaged_image}
          steleTitle="唐风龙纹石碑 · 全屏沉浸式展陈"
          onOpenWorkbench={() => {
            setIsFullscreen3D(false);
            if (currentStele) onSelectStele(currentStele.id);
            onNavigate('workbench');
          }}
        />
      </section>

      {/* 2. Three-Stage Core Architecture */}
      <section className="max-w-7xl mx-auto px-4 lg:px-8 w-full">
        <div className="text-center space-y-2 mb-8">
          <span className="text-xs font-serif text-gold tracking-widest uppercase">Methodology & Architecture</span>
          <h2 className="text-2xl md:text-3xl font-serif font-bold text-slate-100">
            三阶智能微痕修复与考据系统架构
          </h2>
          <p className="text-slate-400 text-xs md:text-sm font-sans max-w-xl mx-auto">
            从数字信号频域去噪，到视觉拓扑骨架推演，再到历史文献网络大模型交叉校验
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="glass-panel p-6 rounded-2xl border border-gold/20 hover:border-gold/50 transition-all group relative overflow-hidden flex flex-col justify-between">
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-xl bg-gold/10 border border-gold/30 flex items-center justify-center text-gold group-hover:scale-110 transition-transform">
                <Layers className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[11px] font-mono text-gold/80">STAGE 01 · 信号重构</span>
                <h3 className="text-lg font-serif font-bold text-slate-100 mt-1">频空域联合滤波去噪</h3>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed text-justify">
                采用二维离散傅里叶变换（2D-FFT）提取频域频谱，利用高斯陷波滤波器精确压制拓布经纬纸纹；配合空域快速非局部均值（Fast NLM）和自适应直方图均衡化（CLAHE），在抑制杂波的同时锐化笔画边缘。
              </p>
            </div>
            <div className="pt-4 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
              <span>PSNR 提升 +11.1 dB</span>
              <span className="text-gold font-mono font-medium">SSIM 0.9482</span>
            </div>
          </div>

          {/* Card 2 */}
          <div className="glass-panel p-6 rounded-2xl border border-cinnabar/20 hover:border-cinnabar/50 transition-all group relative overflow-hidden flex flex-col justify-between">
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-xl bg-cinnabar/10 border border-cinnabar/30 flex items-center justify-center text-cinnabar group-hover:scale-110 transition-transform">
                <Sparkles className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[11px] font-mono text-cinnabar/80">STAGE 02 · 智能释读</span>
                <h3 className="text-lg font-serif font-bold text-slate-100 mt-1">字形拓扑与贝叶斯残字推演</h3>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed text-justify">
                抽取残损字符的细化骨架拓扑（Skeleton Topology），结合古籍语言模型先验概率与字形相似度似然度，通过贝叶斯公式计算 Top-3 残字候选集合，给出历史引证与置信度量化打分。
              </p>
            </div>
            <div className="pt-4 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
              <span>Top-1 置信度 97.4%</span>
              <span className="text-cinnabar-light font-mono font-medium">贝叶斯后验概率</span>
            </div>
          </div>

          {/* Card 3 */}
          <div className="glass-panel p-6 rounded-2xl border border-celadon/20 hover:border-celadon/50 transition-all group relative overflow-hidden flex flex-col justify-between">
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-xl bg-celadon/10 border border-celadon/30 flex items-center justify-center text-celadon group-hover:scale-110 transition-transform">
                <Network className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[11px] font-mono text-celadon/80">STAGE 03 · 史料互勘</span>
                <h3 className="text-lg font-serif font-bold text-slate-100 mt-1">GraphRAG 时空谱系与 GIS 舆图</h3>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed text-justify">
                自动构建金石人物、官职秩品、地理沿革与正史古籍的多层关联网络。配备天干地支历法换算引擎与历史 GIS 时空行旅轨迹，完成从单一字词到宏观历史脉络的闭环互证。
              </p>
            </div>
            <div className="pt-4 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
              <span>350+ 知识实体节点</span>
              <span className="text-celadon-light font-mono font-medium">多源史料互证</span>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Featured Stele Gallery */}
      <section className="max-w-7xl mx-auto px-4 lg:px-8 w-full">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-serif font-bold text-slate-100">核心测试碑拓标本</h2>
            <p className="text-xs text-slate-400 mt-1">涵盖汉隶、魏碑、盛唐楷书及极难漫漶断片</p>
          </div>
          <button 
            onClick={() => onNavigate('museum')}
            className="text-xs text-gold hover:underline flex items-center space-x-1 font-serif"
          >
            <span>查看典藏馆全部碑拓 ({steles.length})</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {CORE_SAMPLES.map((stele) => (
            <div
              key={stele.id}
              className="glass-panel rounded-xl overflow-hidden border border-gold/20 hover:border-gold/60 transition-all duration-300 flex flex-col group"
            >
              {/* Stele Image Window */}
              <div className="relative h-48 w-full bg-slate-950 overflow-hidden flex items-center justify-center">
                <img
                  src={stele.raw_image}
                  alt={stele.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 filter contrast-125"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/assets/stele/rubbings/stele_tang_duobao_damaged.png';
                  }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0A0D12] via-transparent to-transparent opacity-80" />
                
                {/* Dynasty & Weathering Badges */}
                <div className="absolute top-2 left-2 flex flex-col gap-1">
                  <span className="px-2 py-0.5 rounded text-[10px] font-serif bg-gold/90 text-slate-950 font-bold">
                    {stele.dynasty}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-serif ${
                    stele.weathering_level === '严重漫漶' ? 'bg-cinnabar text-white' : 'bg-slate-800/80 text-slate-300'
                  }`}>
                    {stele.weathering_level}
                  </span>
                </div>

                <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between text-[11px] text-slate-300">
                  <span className="font-mono text-gold-light">PSNR: {stele.metrics?.psnr ?? '未评测'} dB</span>
                  <span className="font-mono text-celadon-light">SSIM: {stele.metrics?.ssim ?? '未评测'}</span>
                </div>
              </div>

              {/* Stele Content */}
              <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                <div>
                  <h4 className="font-serif font-bold text-base text-slate-100 group-hover:text-gold transition-colors">
                    {stele.title}
                  </h4>
                  <p className="text-[11px] text-slate-400 mt-1 line-clamp-1">{stele.author}</p>
                  <p className="text-xs text-slate-300 mt-2 line-clamp-2 leading-relaxed">
                    {stele.summary}
                  </p>
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                  <button
                    onClick={() => {
                      onSelectStele(stele.id);
                      onNavigate('workbench');
                    }}
                    className="text-xs font-serif text-gold hover:text-gold-light font-medium flex items-center space-x-1"
                  >
                    <Layers className="w-3.5 h-3.5" />
                    <span>立即修复</span>
                  </button>

                  <button
                    onClick={() => {
                      onSelectStele(stele.id);
                      onNavigate('graph');
                    }}
                    className="text-xs font-serif text-slate-400 hover:text-celadon-light flex items-center space-x-1"
                  >
                    <Network className="w-3.5 h-3.5" />
                    <span>图谱考据</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
