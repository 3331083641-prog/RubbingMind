import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import type { SteleItem, CharacterItem } from '../types/stele';
import { SteleService, type GlyphInferenceRecord } from '../services/api';

type Box = { x: number; y: number; w: number; h: number };

export const GlyphInferencePanel: React.FC<{
  stele: SteleItem;
  activeChar?: CharacterItem;
  runId?: string;
  onDecision: (record: GlyphInferenceRecord) => void;
}> = ({ stele, activeChar, runId, onDecision }) => {
  const [open, setOpen] = useState(false);
  const [box, setBox] = useState<Box | null>(null);
  const [context, setContext] = useState('');
  const [records, setRecords] = useState<GlyphInferenceRecord[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [referenceGlyph,setReferenceGlyph]=useState('');
  const [annotationBasis,setAnnotationBasis]=useState('');
  const [annotator,setAnnotator]=useState('');
  const image = useRef<HTMLImageElement>(null);
  const start = useRef<{x:number;y:number} | null>(null);
  const source = stele.imageAssets?.readable || stele.raw_image;

  useEffect(() => {
    let live = true;
    setRecords([]);setBox(null);setContext('');setOpen(false);
    SteleService.listGlyphInferences(stele.id).then(items => { if (live) setRecords(items); })
      .catch(() => { if (live) setMessage('推演记录暂不可用，请检查后端服务。'); });
    return () => { live = false; };
  }, [stele.id]);

  const point = (event: React.PointerEvent<HTMLImageElement>) => {
    const element = image.current!;
    const rect = element.getBoundingClientRect();
    return {
      x: Math.max(0, Math.min(element.naturalWidth, Math.round((event.clientX - rect.left) * element.naturalWidth / rect.width))),
      y: Math.max(0, Math.min(element.naturalHeight, Math.round((event.clientY - rect.top) * element.naturalHeight / rect.height)))
    };
  };
  const updateBox = (end:{x:number;y:number}) => {
    if (!start.current) return;
    const first = start.current;
    setBox({x:Math.min(first.x,end.x),y:Math.min(first.y,end.y),w:Math.abs(end.x-first.x),h:Math.abs(end.y-first.y)});
  };
  const submit = async () => {
    if (!box || box.w < 16 || box.h < 16) { setMessage('请在图像上框选至少 16×16 像素的残字区域。'); return; }
    setBusy(true); setMessage('');
    try {
      const item = await SteleService.inferGlyph(stele.id, {
        bbox:box, context, characterId:activeChar?.id,
        originalGlyph:activeChar?.char, originalStatus:activeChar?.status, runId
      });
      setRecords(items => [item, ...items]);
      setOpen(false);
      setMessage(item.note);
    } catch (error) { setMessage(error instanceof Error ? error.message : '推演失败'); }
    finally { setBusy(false); }
  };
  const decide = async (record:GlyphInferenceRecord, action:'accept'|'revoke'|'reject', glyph?:string) => {
    setBusy(true); setMessage('');
    try {
      const saved = await SteleService.decideGlyph(record.inferenceId, action, glyph);
      setRecords(items => items.map(item => item.inferenceId===saved.inferenceId?saved:item));
      onDecision(saved);
      setMessage(action==='accept'?'人工采纳已保存；原图未改变。':action==='reject'?'本次候选已人工驳回；操作已保存。':'采纳已撤销，保留操作记录。');
    } catch (error) { setMessage(error instanceof Error ? error.message : '记录保存失败'); }
    finally { setBusy(false); }
  };
  const latest = records[0];
  return <section className="glass-panel rounded-2xl border border-gold/30 p-5 space-y-3" aria-label="实际残字推演">
    <h3 className="font-serif text-gold-light font-bold">实际残字推演</h3>
    <p className="text-xs text-slate-400">框选只读阅读原图并填写相邻文字。可查看实际前景和骨架，检索已人工标注的本地参考；无模型、无参考时仅给有限上下文建议或无候选。预置释文不代表自动检测。</p>
    <button onClick={() => { setOpen(true); setBox(null); setMessage(''); }} className="text-xs text-gold border border-gold/40 rounded px-3 py-2">框选残字区域</button>
    {message && <p role="status" className="text-xs text-celadon-light">{message}</p>}
    {latest ? <div className="space-y-2 text-xs text-slate-300">
      <p>最近记录 {latest.inferenceId.slice(0,8)} · {latest.source==='vision_model'?'视觉模型输出（待人工核验）':latest.source==='context_rule'?'仅上下文规则':latest.source==='local_shape_retrieval'?'本地人工参考字形检索（待核验）':'无可靠候选'} · {latest.status}</p>
      <p>选区 x={latest.bbox.x}, y={latest.bbox.y}, {latest.bbox.w}×{latest.bbox.h} 像素 · 上下文：{latest.context || '未提供'}</p>
      <img src={latest.cropUrl} alt="实际提交的残字局部" className="max-w-44 max-h-36 object-contain" />
      {latest.visualAnalysis && <details open className="space-y-2"><summary>真实选区图像分析 · {latest.visualAnalysis.version}</summary>
        <p>前景：{latest.visualAnalysis.foregroundPolarity}；连通区域 {latest.visualAnalysis.componentCount}；骨架像素 {latest.visualAnalysis.skeletonPixels}。</p>
        <p>{latest.visualAnalysis.identityStatus}</p>
        {latest.visualAnalysis.warnings.map(w=><p key={w} className="text-cinnabar-light">{w}</p>)}
        <div className="flex flex-wrap gap-2">{Object.entries(latest.analysisImages||{}).map(([role,url])=><figure key={role}><img src={url} alt={`残字分析 ${role}`} className="w-24 h-24 object-contain bg-black"/><figcaption>{role}</figcaption></figure>)}</div>
      </details>}
      {latest.candidates.map((candidate,index) => <div key={index} className="rounded border border-slate-700 p-2">
        <p>候选 {index+1}：「{candidate.glyph}」 · {candidate.scoreBasis}</p>
        <p>字形依据：{candidate.visualEvidence || '未给出'}</p>
        <p>上下文依据：{candidate.contextEvidence || '未给出'}</p>
        {candidate.sourceUrls.map(url => <a key={url} href={url} target="_blank" rel="noreferrer" className="text-gold underline block">候选建议来源（须人工核验）</a>)}
        <button disabled={busy} onClick={() => decide(latest,'accept',candidate.glyph)} className="text-gold mt-1">人工采纳此字</button>
      </div>)}
      {!!latest.retrievalCandidates?.length && <details><summary>本地字形检索证据</summary>{latest.retrievalCandidates.map((c,i)=><p key={i}>「{c.glyph}」{c.visualEvidence}；{c.scoreBasis}</p>)}</details>}
      {latest.adoptedGlyph && <div>人工采纳：{latest.originalGlyph || '原字未录入'} → {latest.adoptedGlyph} <button disabled={busy} onClick={() => decide(latest,'revoke')} className="text-gold ml-2">撤销采纳</button></div>}
      <button disabled={busy} onClick={()=>decide(latest,'reject')} className="text-cinnabar-light">驳回本次候选</button>
      <p>本碑已保存 {records.length} 次推演；候选未经过概率校准。</p>
      <details className="border-t border-slate-700 pt-2"><summary>人工标注参考字形（可选）</summary>
        <p>仅将你能够确认的单字选区加入本地参考库。此标签不自动成为独立识字评测真值。</p>
        <input aria-label="参考汉字" maxLength={1} value={referenceGlyph} onChange={e=>setReferenceGlyph(e.target.value)} placeholder="单字" className="bg-slate-900 p-2 w-16"/>
        <input aria-label="标注者" value={annotator} onChange={e=>setAnnotator(e.target.value)} placeholder="标注者" className="bg-slate-900 p-2 max-w-full"/>
        <textarea aria-label="人工标注依据" value={annotationBasis} onChange={e=>setAnnotationBasis(e.target.value)} placeholder="核验依据与释文位置" className="bg-slate-900 p-2 w-full"/>
        <button disabled={busy||!referenceGlyph||!annotationBasis||!annotator} className="text-gold disabled:opacity-40" onClick={async()=>{setBusy(true);try{await SteleService.saveGlyphTemplate(latest.inferenceId,referenceGlyph,annotationBasis,annotator);setMessage('人工参考已保存；后续选区可以执行本地字形检索。');}catch(e){setMessage(String(e));}finally{setBusy(false);}}}>保存人工参考字形</button>
      </details>
    </div> : <p className="text-xs text-slate-500">尚未完成实际图像推演。</p>}
    {open && createPortal(<div role="dialog" aria-modal="true" aria-label="框选残字" className="fixed inset-0 z-[100] bg-black/95 overflow-auto p-6 text-slate-200">
      <div className="max-w-5xl mx-auto space-y-4">
        <div className="flex justify-between"><h2 className="text-gold">{stele.title} · 手动框选残字</h2><button onClick={() => setOpen(false)}>关闭</button></div>
        <p className="text-xs">拖动选取图像上的实际残字。坐标按原始像素保存；无人工确认前不更改释文。</p>
        <div className="overflow-auto"><div className="relative inline-block max-w-full">
          <img ref={image} src={source} alt={stele.title} draggable={false} className="block max-w-full max-h-[58vh] h-auto w-auto touch-none cursor-crosshair"
            onPointerDown={event => { if (!image.current?.naturalWidth) return; event.currentTarget.setPointerCapture(event.pointerId); start.current=point(event); setBox(null); }}
            onPointerMove={event => { if (start.current) updateBox(point(event)); }}
            onPointerUp={event => { updateBox(point(event)); start.current=null; }} />
          {box && image.current && <div className="absolute border-2 border-cinnabar pointer-events-none bg-cinnabar/10" style={{left:`${box.x/image.current.naturalWidth*100}%`,top:`${box.y/image.current.naturalHeight*100}%`,width:`${box.w/image.current.naturalWidth*100}%`,height:`${box.h/image.current.naturalHeight*100}%`}} />}
        </div></div>
        <label className="block text-sm">相邻碑文上下文（如未核实请留空）<textarea value={context} onChange={event => setContext(event.target.value)} maxLength={1000} className="block w-full min-h-20 mt-2 bg-slate-900 border border-slate-700 rounded p-2" /></label>
        <p className="text-xs">选区：{box ? `${box.x}, ${box.y}, ${box.w}×${box.h}` : '未选择'}</p>
        {message && <p role="alert" className="text-cinnabar-light">{message}</p>}
        <button disabled={busy || !box} onClick={submit} className="bg-gold text-black rounded px-4 py-2 disabled:opacity-50">{busy?'推演中…':'提交实际选区'}</button>
      </div>
    </div>,document.body)}
  </section>;
};
