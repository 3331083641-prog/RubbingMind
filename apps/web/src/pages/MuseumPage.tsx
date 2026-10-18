import React, { useState, useMemo } from 'react';
import { SteleItem, DYNASTY_OPTIONS, roleText } from '../types/stele';
import { RubbingArchiveViewer } from '../components/RubbingArchiveViewer';
import { AssessmentViewer } from '../components/AssessmentViewer';
import { SteleFullscreenViewer } from '../components/stele3d/SteleFullscreenViewer';
import { 
  Search, 
  Filter, 
  Layers, 
  Network, 
  Upload, 
  MapPin, 
  Calendar, 
  ShieldAlert, 
  BookOpen, 
  Rotate3d, 
  ExternalLink, 
  FileText,
  AlertCircle
} from 'lucide-react';

interface MuseumPageProps {
  steles: SteleItem[];
  onSelectStele: (id: string) => void;
  onNavigate: (tab: string) => void;
  onOpenUpload: () => void;
}

export const MuseumPage: React.FC<MuseumPageProps> = ({
  steles,
  onSelectStele,
  onNavigate,
  onOpenUpload
}) => {
  const [selectedDynasty, setSelectedDynasty] = useState<string>('all');
  const [selectedWeathering, setSelectedWeathering] = useState<string>('全部');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [viewing3DStele, setViewing3DStele] = useState<SteleItem | null>(null);
  const [viewingArchive, setViewingArchive] = useState<{stele:SteleItem;mode:'readable'|'archive'} | null>(null);
  const [viewingAssessment, setViewingAssessment] = useState<string | null>(null);
  const [failedImages, setFailedImages] = useState<Record<string,boolean>>({});
  const [pendingNoticeStele, setPendingNoticeStele] = useState<SteleItem | null>(null);

  const conditionLevels = ['全部', '轻度影像损伤', '中度影像损伤', '重度影像损伤', '严重漫漶', '待人工复核'];

  // 动态统计各朝代实际馆藏数量
  const dynastyCounts = useMemo(() => {
    const counts: Record<string, number> = { all: steles.length };
    DYNASTY_OPTIONS.forEach((opt) => {
      if (opt.value !== 'all') counts[opt.value] = 0;
    });

    steles.forEach((s) => {
      const dVal = s.dynasty_value || (
        s.dynasty.includes('汉') ? 'eastern_han' :
        s.dynasty.includes('魏') ? 'northern_wei' :
        s.dynasty.includes('唐') ? 'tang' :
        s.dynasty.includes('宋') ? 'song' :
        s.dynasty.includes('元') ? 'yuan' :
        s.dynasty.includes('明') ? 'ming' :
        s.dynasty.includes('清') ? 'qing' : 'all'
      );
      if (counts[dVal] !== undefined) {
        counts[dVal]++;
      }
    });
    return counts;
  }, [steles]);

  // 朝代、风化等级与关键词联合筛选逻辑
  const filteredSteles = useMemo(() => {
    return steles.filter((s) => {
      // 1. 朝代筛选
      let matchDynasty = selectedDynasty === 'all';
      if (!matchDynasty) {
        const targetOpt = DYNASTY_OPTIONS.find((o) => o.value === selectedDynasty);
        const targetLabel = targetOpt ? targetOpt.label : '';
        matchDynasty = 
          s.dynasty_value === selectedDynasty || 
          s.dynasty === targetLabel || 
          (targetLabel === '北魏' && s.dynasty.includes('魏'));
      }

      // 2. 风化等级筛选
      const condition = s.imageCondition || '待人工复核';
      const matchWeathering = 
        selectedWeathering === '全部' || 
        condition === selectedWeathering;

      // 3. 关键词检索 (支持碑名、书家、撰文者、馆藏地、馆藏号、书体)
      const q = searchQuery.toLowerCase().trim();
      const matchQuery = 
        !q || 
        s.title.toLowerCase().includes(q) ||
        (s.author && s.author.toLowerCase().includes(q)) ||
        (s.calligrapher && s.calligrapher.toLowerCase().includes(q)) ||
        (s.inscriptionAuthor && s.inscriptionAuthor.toLowerCase().includes(q)) ||
        (s.museum && s.museum.toLowerCase().includes(q)) ||
        (s.collectionInstitution && s.collectionInstitution.toLowerCase().includes(q)) ||
        (s.collectionNumber && s.collectionNumber.toLowerCase().includes(q)) ||
        (s.location && s.location.toLowerCase().includes(q)) ||
        (s.script_type && s.script_type.toLowerCase().includes(q));

      return matchDynasty && matchWeathering && matchQuery;
    });
  }, [steles, selectedDynasty, selectedWeathering, searchQuery]);

  // 处理点击“微痕修复”
  const handleRepairClick = (stele: SteleItem) => {
    if (stele.imageStatus === '原图待授权或待获取' || !stele.raw_image) {
      setPendingNoticeStele(stele);
      return;
    }
    onSelectStele(stele.id);
    onNavigate('workbench');
  };

  return (
    <div className="min-h-screen bg-[#0A0D12] text-slate-100 px-4 lg:px-12 py-8 space-y-8 select-none" data-testid="museum-page" data-dynasty={selectedDynasty} data-visible-count={filteredSteles.length}>
      {/* 1. Header Banner */}
      <div className="relative rounded-2xl p-6 lg:p-8 overflow-hidden glass-panel border border-gold/30 bg-gradient-to-r from-[#12181F] via-[#0D1217] to-[#12181F] flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-2xl">
        <div
          className="absolute inset-0 pointer-events-none bg-cover bg-no-repeat bg-[position:30%_42%] md:bg-[position:center_28%] opacity-[0.55]"
          style={{ backgroundImage: "url('/assets/stele/backgrounds/bg_museum_hall_v2.webp')" }}
          data-testid="museum-banner-art"
          data-banner-src="/assets/stele/backgrounds/bg_museum_hall_v2.webp"
          aria-hidden="true"
        />
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: [
              'linear-gradient(90deg, rgba(10,13,18,0.72) 0%, rgba(10,13,18,0.42) 24%, rgba(13,18,23,0.12) 50%, rgba(13,18,23,0.22) 70%, rgba(10,13,18,0.68) 100%)',
              'linear-gradient(180deg, rgba(18,24,31,0.30) 0%, rgba(18,24,31,0) 34%, rgba(10,13,18,0.22) 100%)',
            ].join(', '),
          }}
          aria-hidden="true"
        />

        <div className="relative z-10 space-y-2 max-w-2xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-gold/15 border border-gold/40 text-gold-light text-xs font-serif">
            <BookOpen className="w-3.5 h-3.5 text-gold" />
            <span>墨韵智考 · 七朝代真实馆藏碑拓数字化工程</span>
          </div>
          <h1 className="text-3xl font-serif font-bold text-white tracking-wide flex items-center gap-3">
            <span>墨韵智考数字典藏馆</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-cinnabar/20 border border-cinnabar/40 text-cinnabar-light font-mono font-normal">
              已入库 {steles.length} 件真实馆藏
            </span>
          </h1>
          <p className="text-xs md:text-sm text-slate-300 leading-relaxed font-sans">
            汇聚七朝代 {steles.length} 件已审核馆藏影像。依据台北故宫博物院、美国大都会艺术博物馆及普林斯顿大学艺术博物馆著录，保留来源、许可与处理记录。
          </p>
        </div>

        <div className="relative z-10 flex flex-col sm:flex-row items-center gap-3">
          <button
            onClick={onOpenUpload}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl font-serif text-xs font-semibold bg-gradient-to-r from-cinnabar to-cinnabar-dark text-paper-light border border-cinnabar-light/50 shadow-cinnabar-glow hover:brightness-110 active:scale-95 transition-all flex items-center justify-center space-x-2"
          >
            <Upload className="w-4 h-4" />
            <span>上传新碑拓样本入馆</span>
          </button>
        </div>
      </div>

      {/* 2. Top Seven Dynasty Tabs (Strict 8-category filter) */}
      <div className="glass-panel p-4 rounded-xl border border-gold/25 space-y-3.5 shadow-card">
        {/* Row 1: Dynasty Classification (全部 | 东汉 | 北魏 | 唐代 | 宋代 | 元代 | 明代 | 清代) */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          <div className="flex items-center space-x-2 overflow-x-auto no-scrollbar py-1">
            <span className="text-xs font-serif text-gold-light/90 whitespace-nowrap flex items-center gap-1.5 mr-1 font-semibold">
              <Filter className="w-3.5 h-3.5 text-gold" /> 朝代分期:
            </span>
            {DYNASTY_OPTIONS.map((opt) => {
              const isActive = selectedDynasty === opt.value;
              const count = dynastyCounts[opt.value] || 0;
              return (
                <button
                  key={opt.value}
                  onClick={() => setSelectedDynasty(opt.value)}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-serif transition-all whitespace-nowrap flex items-center gap-1.5 ${
                    isActive
                      ? 'bg-gold text-slate-950 font-bold shadow-gold-glow scale-105'
                      : 'bg-slate-900/80 text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-700/60 hover:border-gold/30'
                  }`}
                >
                  <span>{opt.label}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                    isActive ? 'bg-slate-950/30 text-slate-950 font-bold' : 'bg-slate-800 text-gold-light/80'
                  }`}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Quick Counter */}
          <div className="text-xs font-serif text-slate-400 whitespace-nowrap hidden xl:block">
            当前筛选呈现 <span className="text-gold font-bold">{filteredSteles.length}</span> / {steles.length} 通金石碑拓
          </div>
        </div>

        {/* Row 2: Weathering Level & Keyword Search */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pt-3 border-t border-slate-800/80">
          {/* Weathering Level Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-serif text-slate-400 mr-1 flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5 text-cinnabar" /> 拓本影像损伤状况:
            </span>
            {conditionLevels.map((lvl) => {
              const isLvlActive = selectedWeathering === lvl;
              return (
                <button
                  key={lvl}
                  onClick={() => setSelectedWeathering(lvl)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-serif transition-all ${
                    isLvlActive
                      ? 'bg-cinnabar text-white font-bold shadow-cinnabar-glow'
                      : 'bg-slate-900/60 text-slate-300 hover:bg-slate-800 border border-slate-800'
                  }`}
                >
                  {lvl}
                </button>
              );
            })}
          </div>

          {/* Search Input */}
          <div className="relative min-w-[280px] lg:min-w-[340px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索碑名、书家、撰文者、馆藏号、地望..."
              className="w-full pl-9 pr-4 py-1.5 bg-slate-950/80 border border-slate-700/80 focus:border-gold rounded-lg text-xs text-slate-200 outline-none placeholder:text-slate-500 transition-colors"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white text-xs font-bold"
              >
                ×
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 3. Stele Grid View (4 columns responsive) */}
      {filteredSteles.length === 0 ? (
        <div className="py-24 text-center glass-panel rounded-2xl border border-gold/20 space-y-3">
          <BookOpen className="w-10 h-10 text-slate-600 mx-auto" />
          <p className="text-slate-400 font-serif text-base">未检索到符合当前组合条件的碑拓馆藏</p>
          <p className="text-xs text-slate-500 font-sans">请尝试更换朝代分类、重置风化筛选或清空检索关键词</p>
          <button
            onClick={() => {
              setSelectedDynasty('all');
              setSelectedWeathering('全部');
              setSearchQuery('');
            }}
            className="mt-2 px-4 py-1.5 rounded-lg bg-gold/15 text-gold text-xs border border-gold/30 hover:bg-gold/25 transition-all font-serif"
          >
            重置所有筛选条件
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {filteredSteles.map((stele) => {
            const hasGenuineImage = !!stele.imageAssets?.cover && !failedImages[stele.id];

            return (
              <div
                key={stele.id}
                data-testid="museum-card" data-stele-id={stele.id} data-image-condition={stele.imageCondition || '待人工复核'}
                className="glass-panel rounded-2xl overflow-hidden border border-gold/20 hover:border-gold/60 transition-all duration-300 flex flex-col group hover:-translate-y-1 shadow-lg bg-[#0E1319]/90"
              >
                {/* Image or Pending Placeholder Box */}
                <div className="relative h-60 w-full bg-[#080B0E] overflow-hidden flex items-center justify-center border-b border-gold/15">
                  {hasGenuineImage ? (
                    <img
                      src={stele.imageAssets?.cover} loading="lazy" decoding="async" data-testid="museum-cover"
                      alt={stele.title}
                      className="w-full h-full object-contain"
                      onError={() => setFailedImages(prev => ({...prev,[stele.id]:true}))}
                    />
                  ) : (
                    <div className="text-sm text-slate-300 text-center p-5">本件图像加载失败
                      <button className="block mx-auto text-gold underline mt-3" onClick={() => setFailedImages(prev => ({...prev,[stele.id]:false}))}>重试</button>
                      <a className="block text-gold mt-3" href={stele.sourceUrl} target="_blank" rel="noreferrer">查看馆藏来源</a>
                    </div>
                  )}
                  
                  {/* Gradient Mask for images */}
                  {hasGenuineImage && (
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0A0D12] via-transparent to-transparent opacity-80" />
                  )}

                  {/* Top Corner Badges */}
                  <div className="absolute top-2.5 left-2.5 flex flex-wrap gap-1.5 z-10">
                    <span className="px-2 py-0.5 rounded text-[10px] font-serif bg-gold/90 text-slate-950 font-bold shadow-md">
                      {stele.dynasty} · {stele.script_type}
                    </span>
                    <span data-testid="image-condition" className={`px-2 py-0.5 rounded text-[10px] font-serif ${
                      (stele.imageCondition || '').startsWith('严重')
                        ? 'bg-cinnabar text-white font-bold'
                        : (stele.imageCondition || '').startsWith('重度')
                        ? 'bg-amber-700/80 text-amber-100'
                        : stele.imageCondition === '待人工复核' || !stele.imageCondition
                        ? 'bg-slate-700 text-slate-200'
                        : 'bg-celadon text-white'
                    }`}>
                      {stele.imageCondition || '待人工复核'}
                    </span>
                  </div>

                  {/* Bottom HUD: PSNR / Image Status */}
                  <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between text-[11px] px-2 py-1 rounded bg-black/70 backdrop-blur-sm border border-slate-800 font-mono">
                    <span className="text-gold-light">
                      {stele.metrics?.psnr == null ? '未评测' : `PSNR: ${stele.metrics.psnr} dB`}
                    </span>
                    <span className={hasGenuineImage ? 'text-celadon-light' : 'text-amber-400'}>
                      {hasGenuineImage ? '真实影像' : '图像加载失败'}
                    </span>
                  </div>
                </div>

                {/* Card Meta Content */}
                <div className="p-4 flex-1 flex flex-col justify-between space-y-3.5">
                  <div className="space-y-2">
                    {/* Stele Title & Collection Number */}
                    <div className="flex items-start justify-between gap-1.5">
                      <h3 className="font-serif font-bold text-base text-slate-100 group-hover:text-gold transition-colors leading-snug">
                        {stele.title}
                      </h3>
                      {stele.collectionNumber && (
                        <span className="text-[10px] font-mono text-slate-500 border border-slate-800 px-1.5 py-0.5 rounded whitespace-nowrap">
                          {stele.collectionNumber}
                        </span>
                      )}
                    </div>

                    {/* Metadata Items */}
                    <div className="space-y-1 text-xs text-slate-400 font-sans">
                      <p className="flex items-center gap-1.5">
                        <span className="text-gold/80 font-serif">撰文:</span>
                        <span className="text-slate-300 truncate">{roleText(stele.inscriptionAuthor, stele.authorVerification)}</span>
                      </p>
                      <p className="flex items-center gap-1.5">
                        <span className="text-gold/80 font-serif">书丹:</span>
                        <span className="text-slate-300 truncate">{roleText(stele.calligrapher, stele.calligrapherVerification)}</span>
                      </p>
                      <p className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-slate-500" />
                        <span className="leading-relaxed">原刻：{stele.year}</span>
                      </p>
                      <p className="flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5 text-slate-500" />
                        <span className="line-clamp-1">{stele.collectionInstitution || stele.museum}</span>
                      </p>
                    </div>

                    <p className="text-xs text-slate-400">拓本：{stele.rubbingPeriod}</p><p className="text-xs text-slate-400">类型：{stele.artifactType}</p>
                    <p className="text-xs text-slate-400">篆额：{roleText(stele.titleCalligrapher, stele.titleCalligrapherVerification)} · 刻工：{roleText(stele.engraver, stele.engraverVerification)} · 碑主/墓主：{roleText(stele.steleSubject, stele.steleSubjectVerification)}</p>
                    <p className="text-xs text-slate-400">影像初筛：{stele.imageConditionReviewStatus || '自动初筛，待人工复核'}</p>
                    <p className="text-xs text-slate-400">原石风化：{stele.physicalStoneWeathering || stele.stoneWeathering || '无可靠原石证据，不评定'}</p>
                    {stele.assessmentRunId && <p className="text-[10px] text-slate-500 font-mono truncate">处理 {stele.assessmentRunId} · {stele.assessmentScope === 'partial_center_roi' ? '中心局部' : '全幅'}</p>}
                    {/* Academic Summary */}
                    <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed pt-0.5 font-sans">
                      {stele.summary}
                    </p>

                    {/* License / Attribution */}
                    <div className="text-[10px] text-slate-500 font-mono truncate pt-1 border-t border-slate-800/60">
                      许可: {stele.license || 'CC BY 4.0 / 馆藏著录公开'}
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 text-xs text-gold">
                    <button onClick={() => setViewingAssessment(stele.id)}>查看本件评估</button>
                    <button onClick={() => setViewingArchive({stele,mode:'readable'})}>查看高清拓本</button>
                    <button onClick={() => setViewingArchive({stele,mode:'archive'})}>查看完整档案</button>
                    <a href={stele.sourceUrl} target="_blank" rel="noreferrer">查看馆藏来源</a>
                  </div>
                  {/* Action Buttons */}
                  <div className="pt-2.5 border-t border-slate-800/80 flex items-center justify-between gap-1.5">
                    <button
                      onClick={() => handleRepairClick(stele)}
                      className="flex-1 py-1.5 px-2 rounded-xl font-serif text-xs font-semibold bg-gold/15 text-gold hover:bg-gold hover:text-slate-950 border border-gold/40 hover:border-gold transition-all flex items-center justify-center space-x-1"
                      title={hasGenuineImage ? '进入工作台执行微痕修复' : '查阅馆藏著录说明'}
                    >
                      <Layers className="w-3.5 h-3.5" />
                      <span>{hasGenuineImage ? '微痕修复' : '著录详情'}</span>
                    </button>

                    <button
                      onClick={() => {
                        onSelectStele(stele.id);
                        onNavigate('graph');
                      }}
                      className="py-1.5 px-2.5 rounded-xl font-serif text-xs font-medium text-slate-300 hover:text-celadon-light border border-slate-700 hover:border-celadon/50 transition-colors flex items-center space-x-1"
                      title="查看此碑时空图谱与历史地理轨迹"
                    >
                      <Network className="w-3.5 h-3.5" />
                      <span>时空图谱</span>
                    </button>

                    {hasGenuineImage && (
                      <button
                        onClick={() => setViewing3DStele(stele)}
                        className="py-1.5 px-2 rounded-xl font-serif text-xs font-medium text-slate-300 hover:text-gold border border-slate-700 hover:border-gold/50 transition-colors flex items-center space-x-1"
                        title="在 3D 展陈空间中查看此碑"
                      >
                        <Rotate3d className="w-3.5 h-3.5 text-gold" />
                        <span>3D</span>
                      </button>
                    )}

                    {stele.sourceUrl && (
                      <a
                        href={stele.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1.5 rounded-xl text-slate-400 hover:text-gold hover:bg-slate-800 border border-slate-800 hover:border-gold/40 transition-colors"
                        title="访问原始数字馆藏来源网页"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {viewingArchive && <RubbingArchiveViewer stele={viewingArchive.stele} mode={viewingArchive.mode} onClose={() => setViewingArchive(null)} />}
      {viewingAssessment && <AssessmentViewer steleId={viewingAssessment} onClose={() => setViewingAssessment(null)} />}
      {/* 3D Stele Viewer Modal */}
      {viewing3DStele && (
        <SteleFullscreenViewer
          isOpen={!!viewing3DStele}
          onClose={() => setViewing3DStele(null)}
          customRubbingUrl={viewing3DStele.imageAssets?.cover || viewing3DStele.raw_image}
          steleTitle={`${viewing3DStele.title} · 三维数字展陈`}
          onOpenWorkbench={() => {
            onSelectStele(viewing3DStele.id);
            setViewing3DStele(null);
            onNavigate('workbench');
          }}
        />
      )}

      {/* Pending Acquisition Notice Modal */}
      {pendingNoticeStele && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel p-6 rounded-2xl max-w-md w-full border border-gold/40 space-y-4 shadow-2xl bg-[#0D1217]">
            <div className="flex items-center space-x-2 text-cinnabar-light font-serif">
              <AlertCircle className="w-5 h-5 text-cinnabar" />
              <h3 className="text-base font-bold text-white">馆藏数字原件授权说明</h3>
            </div>
            
            <p className="text-xs text-slate-300 leading-relaxed font-sans">
              《<span className="text-gold font-serif font-bold">{pendingNoticeStele.title}</span>》（馆藏号: {pendingNoticeStele.collectionNumber}）属于已核验证书的<span className="text-paper-light font-semibold">{pendingNoticeStele.collectionInstitution}</span>正式馆藏著录。
            </p>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              根据数字人文规范，本系统严禁使用 AI 随机虚构图像伪造真实文物。当前该档案处于“馆藏记录已导入 · 原图待授权获取”状态，建议查阅官方著录链接或在典藏馆浏览已获取的 已审核馆藏图片。
            </p>

            <div className="pt-2 border-t border-slate-800 flex items-center justify-between gap-3">
              {pendingNoticeStele.sourceUrl && (
                <a
                  href={pendingNoticeStele.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3.5 py-1.5 rounded-lg text-xs font-serif bg-gold/15 text-gold border border-gold/40 hover:bg-gold hover:text-slate-950 transition-all flex items-center gap-1.5"
                >
                  <span>访问官方著录来源</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
              <button
                onClick={() => setPendingNoticeStele(null)}
                className="ml-auto px-4 py-1.5 rounded-lg text-xs font-serif bg-slate-800 text-slate-200 hover:bg-slate-700 transition-colors"
              >
                我知道了
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
