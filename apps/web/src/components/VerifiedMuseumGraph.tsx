import React from 'react';
import { SteleItem } from '../types/stele';
export const VerifiedMuseumGraph: React.FC<{stele: SteleItem; onNavigate: (tab: string) => void}> = ({stele, onNavigate}) => <div className="max-w-7xl mx-auto p-8 space-y-6">
  <h1 className="text-2xl font-serif text-gold">{stele.title} · 馆藏资料关联</h1>
  <div className="glass-panel rounded-xl p-6 grid md:grid-cols-2 gap-4">
    <p>原刻朝代：{stele.dynasty}</p><p>原刻年代：{stele.originalYear}</p>
    <p>撰文：{stele.inscriptionAuthor}</p><p>书丹：{stele.calligrapher}</p>
    <p>拓本现藏：{stele.collectionInstitution}</p><p>馆藏编号：{stele.collectionNumber}</p>
    <p>原碑所在地：{stele.originalLocation || '未核定'}</p><p>原石现藏机构：{stele.physicalCollectionInstitution || '未核定'}</p>
  </div>
  <p>{stele.description}</p><p className="text-slate-400">本馆藏尚无经过核验的 GIS 轨迹与 GraphRAG 推理记录。四件核心样本的时空图谱可从顶部选择器进入。</p>
  <a href={stele.sourceUrl} target="_blank" rel="noreferrer" className="text-gold underline">查看馆藏来源</a>
  <button onClick={() => onNavigate('museum')} className="ml-6 text-gold">返回典藏馆</button>
</div>;
