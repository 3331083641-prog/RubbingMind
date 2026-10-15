import React, { useState } from 'react';
import { SteleItem } from '../types/stele';
import { RubbingArchiveViewer } from './RubbingArchiveViewer';
export const VerifiedMuseumGraph: React.FC<{stele: SteleItem; onNavigate: (tab: string) => void}> = ({stele, onNavigate}) => {
  const [viewer, setViewer] = useState<'readable' | 'archive' | null>(null);
  const [failedId, setFailedId] = useState<string | null>(null);
  return <div className="max-w-7xl mx-auto p-8 space-y-6">
  <h1 className="text-2xl font-serif text-gold">{stele.title} · 馆藏资料关联</h1>
  <section aria-label="真实文物影像" className="glass-panel rounded-xl p-6 space-y-4">
    <h2 className="text-lg font-serif text-gold">真实文物影像</h2>
    {failedId === stele.id ? <div role="status">本件图像加载失败。<button className="ml-3 text-gold" onClick={() => setFailedId(null)}>重试</button></div> :
      <button className="block w-full bg-black/40 rounded-lg" onClick={() => setViewer('readable')} aria-label="查看高清拓本">
        <img data-testid="graph-museum-image" src={stele.imageAssets?.cover} alt={`${stele.title} · 真实影像`} className="w-full h-96 object-contain" onError={() => setFailedId(stele.id)} />
      </button>}
    <p className="text-sm text-slate-400">{stele.attribution} · {stele.license}</p>
    <p className="text-xs text-slate-400">{stele.modifications}</p>
    <div className="flex gap-6 text-gold">
      <button onClick={() => setViewer('readable')}>查看高清拓本</button>
      <button onClick={() => setViewer('archive')}>查看完整档案</button>
      <a href={stele.sourceUrl} target="_blank" rel="noreferrer">查看馆藏来源</a>
    </div>
  </section>
  <div className="glass-panel rounded-xl p-6 grid md:grid-cols-2 gap-4">
    <p>原刻朝代：{stele.dynasty}</p><p>原刻年代：{stele.originalYear}</p>
    <p>撰文：{stele.inscriptionAuthor}</p><p>书丹：{stele.calligrapher}</p>
    <p>拓本现藏：{stele.collectionInstitution}</p><p>馆藏编号：{stele.collectionNumber}</p>
    <p>原碑所在地：{stele.originalLocation || '未核定'}</p><p>原石现藏机构：{stele.physicalCollectionInstitution || '未核定'}</p>
  </div>
  <p>{stele.description}</p><p className="text-slate-400">本馆藏尚无经过核验的 GIS 轨迹与 GraphRAG 推理记录。四件核心样本的时空图谱可从顶部选择器进入。</p>
  <a href={stele.sourceUrl} target="_blank" rel="noreferrer" className="text-gold underline">查看馆藏来源</a>
  <button onClick={() => onNavigate('museum')} className="ml-6 text-gold">返回典藏馆</button>
  {viewer && <RubbingArchiveViewer key={`${stele.id}-${viewer}`} stele={stele} mode={viewer} onClose={() => setViewer(null)} />}
</div>;
};
