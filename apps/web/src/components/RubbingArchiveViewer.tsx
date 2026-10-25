import React, { useEffect, useRef, useState } from 'react';
import { SteleItem, roleText } from '../types/stele';

export const RubbingArchiveViewer: React.FC<{ stele: SteleItem; mode: 'readable' | 'archive'; onClose: () => void }> = ({ stele, mode, onClose }) => {
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const drag = useRef<{ x: number; y: number; ox: number; oy: number } | null>(null);
  const label = mode === 'archive' ? '完整馆藏档案' : '高清拓本';
  useEffect(() => {
    const handle = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    const original = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handle);
    return () => { document.body.style.overflow = original; window.removeEventListener('keydown', handle); };
  }, [onClose]);
  return <div role="dialog" aria-modal="true" aria-label={label} className="fixed inset-0 z-50 bg-[#080b0e]/95 flex flex-col p-4 text-slate-200">
    <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
      <div><h2 className="font-serif text-gold">{stele.title} · {label}</h2><p className="text-xs">{stele.collectionInstitution} · {stele.collectionNumber} · {stele.year}</p></div>
      <div className="flex gap-3 items-center">
        <button aria-label="缩小" onClick={() => setZoom(z => Math.max(.25, z / 1.25))}>−</button>
        <output data-testid="archive-zoom">{Math.round(zoom * 100)}%</output>
        <button aria-label="放大" onClick={() => setZoom(z => Math.min(12, z * 1.25))}>＋</button>
        <button onClick={() => { setZoom(1); setOffset({ x: 0, y: 0 }); }}>重置</button>
        <button onClick={onClose} aria-label="关闭档案">关闭 ×</button>
      </div>
    </div>
    <div className="flex-1 min-h-0 overflow-hidden flex items-center justify-center cursor-grab touch-none border border-gold/20" data-testid="archive-pan"
      onWheel={e => setZoom(z => Math.min(12, Math.max(.25, z * (e.deltaY < 0 ? 1.1 : 1 / 1.1))))}
      onPointerDown={e => { e.currentTarget.setPointerCapture(e.pointerId); drag.current = { x: e.clientX, y: e.clientY, ox: offset.x, oy: offset.y }; }}
      onPointerMove={e => { if (drag.current) setOffset({ x: drag.current.ox + e.clientX - drag.current.x, y: drag.current.oy + e.clientY - drag.current.y }); }}
      onPointerUp={() => { drag.current = null; }} onPointerCancel={() => { drag.current = null; }}>
      {failed ? <div>本件图像加载失败。<button onClick={() => { setFailed(false); setAttempt(n => n + 1); }}>重试</button></div> :
        <img key={attempt} data-testid="archive-image" src={stele.imageAssets?.[mode]} alt={`${stele.title} ${label}`} draggable={false} className="max-h-full max-w-full object-contain select-none" style={{ transform: `translate(${offset.x}px,${offset.y}px) scale(${zoom})` }} onError={() => setFailed(true)} />}
    </div>
    <div className="text-xs space-y-1 mt-3">
      <details><summary className="text-gold cursor-pointer">馆藏资料与年代说明</summary>
        <p>文物类型：{stele.artifactType} · 书体：{stele.script_type} · 撰文：{roleText(stele.inscriptionAuthor, stele.authorVerification)} · 书丹：{roleText(stele.calligrapher, stele.calligrapherVerification)} · 篆额：{roleText(stele.titleCalligrapher, stele.titleCalligrapherVerification)} · 刻工：{roleText(stele.engraver, stele.engraverVerification)} · 碑主/墓主：{roleText(stele.steleSubject, stele.steleSubjectVerification)}</p>
        <p>拓本影像损伤：{stele.imageCondition || '待人工复核'} · 原石风化：{stele.stoneWeathering || '无原石影像，不评定'} · 处理运行：{stele.assessmentRunId || '未记录'}</p>
        <p>原刻：{stele.originalYear} · 拓本：{stele.rubbingPeriod} · 原碑所在地：{stele.originalLocation || '未核定'} · 原石现藏机构：{stele.physicalCollectionInstitution || '未核定'}</p>
        <p>{stele.description}</p>
      </details>
      <p>{stele.attribution} · {stele.license} {stele.licenseUrl && <a className="text-gold underline" href={stele.licenseUrl} target="_blank" rel="noreferrer">许可证</a>}</p>
      <p>{stele.modifications}</p><p>档案版为审核包所选扫描画面；册页藏品的全册原始PDF保存在本地归档，来源见馆方记录。拖动可平移，滚轮可缩放。</p>
      <a className="text-gold underline" href={stele.sourceUrl} target="_blank" rel="noreferrer">查看馆藏来源</a>
    </div>
  </div>;
};
