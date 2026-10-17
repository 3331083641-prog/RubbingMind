import React,{useEffect,useMemo,useState} from 'react';
type Row={sampleId:string;degradation:string;method:string;psnr:number|null;ssim:number|null;edgeF1:number|null;processingMs:number;applicability:string;split?:string;error?:string|null;output:string|null;input?:string;reference?:string;seed:number;strength?:number};
type Batch={id:string;rowCount:number;sampleCount:number;historicalWarning?:string|null;limitations:string[]};
type Detail={config:{referenceNote:string};registry:Batch;rows:Row[];summary:Record<string,unknown>[];sources:{id:string;sourceUrl:string;license:string;sourceSha256:string}[]};
const fmt=(n:number|null|undefined)=>n==null?'未评测':n.toFixed(3);

export const ExperimentExplorer:React.FC=()=>{
  const [batches,setBatches]=useState<Batch[]>([]);const [id,setId]=useState('');
  const [data,setData]=useState<Detail|null>(null);const [error,setError]=useState('');
  const [sample,setSample]=useState('');const [degradation,setDegradation]=useState('');const [method,setMethod]=useState('');const [split,setSplit]=useState('test');
  const [selected,setSelected]=useState(0);const [metric,setMetric]=useState<'psnr'|'ssim'|'edgeF1'|'processingMs'>('psnr');
  useEffect(()=>{let live=true;fetch('/api/experiments').then(async r=>{if(!r.ok)throw new Error('实验服务不可用');return r.json();}).then(items=>{if(live){setBatches(items);setId(items.at(-1)?.id||'');}}).catch(e=>{if(live)setError(String(e));});return()=>{live=false;};},[]);
  useEffect(()=>{if(!id)return;let live=true;setData(null);setError('');setSelected(0);setSample('');setDegradation('');setMethod('');
    fetch(`/api/experiments/${encodeURIComponent(id)}`).then(async r=>{if(!r.ok)throw new Error('实验批次读取失败');return r.json();}).then(d=>{if(live)setData(d);}).catch(e=>{if(live)setError(String(e));});return()=>{live=false;};},[id]);
  const rows=useMemo(()=>data?.rows.filter(r=>(!sample||r.sampleId===sample)&&(!degradation||r.degradation===degradation)&&(!method||r.method===method)&&(!split||!r.split||r.split===split))||[],[data,sample,degradation,method,split]);
  const group=useMemo(()=>Array.from(new Set(rows.map(r=>r.method))).map(m=>{const values=rows.filter(r=>r.method===m);const nums=values.map(r=>r[metric]).filter((n):n is number=>n!=null&&Number.isFinite(n));const mean=nums.length?nums.reduce((a,b)=>a+b,0)/nums.length:null;const std=nums.length>1?Math.sqrt(nums.reduce((a,b)=>a+(b-mean!)**2,0)/(nums.length-1)):0;return {method:m,n:values.length,valid:nums.length,applicable:values.filter(r=>r.applicability!=='not_applicable'&&!r.error).length,mean,std};}),[rows,metric]);
  const row=rows[Math.min(selected,Math.max(0,rows.length-1))];
  const asset=(filename:string)=>`/api/experiments/${encodeURIComponent(id)}/assets/${encodeURIComponent(filename)}`;
  const select=(label:string,value:string,set:(v:string)=>void,options:string[])=><label className="text-xs">{label}<select aria-label={label} value={value} onChange={e=>{set(e.target.value);setSelected(0);}} className="block p-2 bg-slate-950 border border-slate-700 rounded max-w-full"><option value="">全部</option>{options.map(v=><option key={v}>{v}</option>)}</select></label>;
  const max=Math.max(1,...group.map(r=>r.mean||0));
  return <section aria-label="算法实验与消融分析" className="glass-panel rounded-xl border border-gold/20 p-4 md:p-6 space-y-4 print:hidden">
    <h2 className="text-lg text-gold font-serif">算法实验与消融分析</h2>
    <p className="text-xs text-slate-400">仅对应受控退化实验，不代表28件历史拓本的无参考修复质量或识字准确率。</p>
    {error&&<p role="alert" className="text-cinnabar-light">{error}</p>}
    <label className="text-sm">实验批次<select aria-label="实验批次" value={id} onChange={e=>setId(e.target.value)} className="ml-2 bg-slate-950 p-2 rounded max-w-full">{batches.map(b=><option key={b.id} value={b.id}>{b.id} · {b.sampleCount}件 / {b.rowCount}输出</option>)}</select></label>
    {data&&<>
      <p className="text-xs text-slate-300">{data.config.referenceNote}</p>
      {data.registry.historicalWarning&&<p className="text-cinnabar-light">{data.registry.historicalWarning}</p>}
      <div className="flex flex-wrap gap-3">
        {select('实验样本',sample,setSample,Array.from(new Set(data.rows.map(r=>r.sampleId))))}
        {select('退化类型',degradation,setDegradation,Array.from(new Set(data.rows.map(r=>r.degradation))))}
        {select('处理方法',method,setMethod,Array.from(new Set(data.rows.map(r=>r.method))))}
        {select('数据分组',split,setSplit,['development','test'])}
        <label className="text-xs">对比指标<select aria-label="对比指标" value={metric} onChange={e=>setMetric(e.target.value as typeof metric)} className="block p-2 bg-slate-950 border border-slate-700 rounded">{['psnr','ssim','edgeF1','processingMs'].map(v=><option key={v}>{v}</option>)}</select></label>
      </div>
      <div className="overflow-x-auto"><table data-testid="experiment-table" className="w-full text-xs text-left"><thead><tr>{['方法','输入数','适用数','均值','标准差','比较条'].map(v=><th key={v} className="p-2">{v}</th>)}</tr></thead><tbody>{group.map(g=><tr key={g.method} className="border-t border-slate-700"><td className="p-2">{g.method}</td><td>{g.n}</td><td>{g.applicable}</td><td>{fmt(g.mean)}</td><td>{fmt(g.std)}</td><td className="w-1/4"><div className="h-3 bg-gold/60" style={{width:`${Math.max(0,(g.mean||0)/max*100)}%`}}/></td></tr>)}</tbody></table></div>
      <p className="text-xs text-slate-400">当前{rows.length}条；不适用陷波以原图计入全样本比较，适用数另列。标准差为记录间离散程度；按文物聚类的95%置信区间见导出summary。空值/失败保留，不改为0分。</p>
      {row&&<><label className="text-xs">单次实验记录<select aria-label="单次实验记录" value={Math.min(selected,rows.length-1)} onChange={e=>setSelected(Number(e.target.value))} className="block bg-slate-950 p-2 max-w-full">{rows.map((r,i)=><option key={i} value={i}>{r.sampleId} / {r.degradation} / {r.strength??'历史'} / {r.method}</option>)}</select></label>
        <p className="text-xs">PSNR {fmt(row.psnr)} dB · SSIM {fmt(row.ssim)} · edge F1 {fmt(row.edgeF1)} · {fmt(row.processingMs)} ms · seed {row.seed} · {row.error||row.applicability}</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">{[['受控参考',row.reference],['退化输入',row.input],['本方法输出',row.output]].map(([label,file])=>file&&<figure key={label}><img src={asset(file)} alt={label||''} loading="lazy" className="w-full max-h-72 object-contain bg-black"/><figcaption className="text-xs text-center">{label}</figcaption></figure>)}</div>
      </>}
      <div className="flex flex-wrap gap-4 text-xs text-gold">{['results.json','results.csv','summary.csv'].map(kind=><a key={kind} href={`/api/experiments/${encodeURIComponent(id)}/export/${kind}`} download>导出 {kind}</a>)}</div>
      <details className="text-xs"><summary>来源与实验限制</summary>{data.registry.limitations.map(t=><p key={t}>{t}</p>)}{data.sources.map(s=><p key={s.id}><a className="text-gold underline" href={s.sourceUrl} target="_blank" rel="noreferrer">{s.id}</a> · {s.license} · SHA {s.sourceSha256||'历史记录见原始文件'}</p>)}</details>
    </>}
  </section>;
};
