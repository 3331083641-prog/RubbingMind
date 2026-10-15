import React, { useEffect, useRef, useState } from 'react';
import type { SteleItem, CharacterItem } from '../types/stele';
import { SteleService, type GlyphInferenceRecord } from '../services/api';

type Box = { x: number; y: number; w: number; h: number };

export const GlyphInferencePanel: React.FC<{
  stele: SteleItem;
  activeChar?: CharacterItem;
  onDecision: (record: GlyphInferenceRecord) => void;
}> = ({ stele, activeChar, onDecision }) => {
  const [open, setOpen] = useState(false);
  const [box, setBox] = useState<Box | null>(null);
  const [context, setContext] = useState('');
  const [records, setRecords] = useState<GlyphInferenceRecord[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const image = useRef<HTMLImageElement>(null);
  const start = useRef<{x:number;y:number} | null>(null);
  const source = stele.imageAssets?.readable || stele.raw_image;

  useEffect(() => {
    let live = true;
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
        originalGlyph:activeChar?.char, originalStatus:activeChar?.status
      });
      setRecords(items => [item, ...items]);
      setOpen(false);
      setMessage(item.note);
    } catch (error) { setMessage(error instanceof Error ? error.message : '推演失败'); }
    finally { setBusy(false); }
  };
  const decide = async (record:GlyphInferenceRecord, action:'accept'|'revoke', glyph?:string) => {
    setBusy(true); setMessage('');
    try {
      const saved = await SteleService.decideGlyph(record.inferenceId, action, glyph);
      setRecords(items => items.map(item => item.inferenceId===saved.inferenceId?saved:item));
      onDecision(saved);
      setMessage(action==='accept'?'人工采纳已保存；原图未改变。':'采纳已撤销，保留操作记录。');
    } catch (error) { setMessage(error instanceof Error ? error.message : '记录保存失败'); }
    finally { setBusy(false); }
  };
  const latest = records[0];
  return <section className="glass-panel rounded-2xl border border-gold/30 p-5 space-y-3" aria-label="实际残字推演">
    <h3 className="font-serif text-gold-light font-bold">实际残字推演</h3>
    <p className="text-xs text-slate-400">手动框选真实图像局部，填写相邻文字后提交。预置释文不代表自动检测结果；模型未配置时只可能给出上下文规则建议。</p>
    <button onClick={() => { setOpen(true); setBox(null); setMessage(''); }} className="text-xs text-gold border border-gold/40 rounded px-3 py-2">框选残字区域</button>
    {message && <p role="status" className="text-xs text-celadon-light">{message}</p>}
    {latest ? <div className="space-y-2 text-xs text-slate-300">
      <p>最近记录 {latest.inferenceId.slice(0,8)} · {latest.source==='vision_model'?'视觉模型输出（待人工核验）':latest.source==='context_rule'?'仅上下文规则':'无可靠候选'} · {latest.status}</p>
      <p>选区 x={latest.bbox.x}, y={latest.bbox.y}, {latest.bbox.w}×{latest.bbox.h} 像素 · 上下文：{latest.context || '未提供'}</p>
      <img src={latest.cropUrl} alt="实际提交的残字局部" className="max-w-44 max-h-36 object-contain" />
      {latest.candidates.map((candidate,index) => <div key={index} className="rounded border border-slate-700 p-2">
        <p>候选 {index+1}：「{candidate.glyph}」 · {candidate.scoreBasis}</p>
        <p>字形依据：{candidate.visualEvidence || '未给出'}</p>
        <p>上下文依据：{candidate.contextEvidence || '未给出'}</p>
        {candidate.sourceUrls.map(url => <a key={url} href={url} target="_blank" rel="noreferrer" className="text-gold underline block">候选来源链接</a>)}
        <button disabled={busy} onClick={() => decide(latest,'accept',candidate.glyph)} className="text-gold mt-1">人工采纳此字</button>
      </div>)}
      {latest.adoptedGlyph && <div>人工采纳：{latest.originalGlyph || '原字未录入'} → {latest.adoptedGlyph} <button disabled={busy} onClick={() => decide(latest,'revoke')} className="text-gold ml-2">撤销采纳</button></div>}
      <p>本碑已保存 {records.length} 次推演；候选未经过概率校准。</p>
    </div> : <p className="text-xs text-slate-500">尚未完成实际图像推演。</p>}
    {open && <div role="dialog" aria-modal="true" aria-label="框选残字" className="fixed inset-0 z-50 bg-black/95 overflow-auto p-6 text-slate-200">
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
    </div>}
  </section>;
};
