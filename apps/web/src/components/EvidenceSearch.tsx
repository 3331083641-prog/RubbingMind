import React,{useEffect,useState} from 'react';

type Evidence={sourceId:string;steleId:string;title:string;text:string;url:string;originalPosition:string;evidenceLevel:string;textProvenance?:{kind:string;label:string};relevance?:string;relevanceLabel?:string};
type Relation={source:string;target:string;relation:string;sourceIds:string[];sourceUrl:string};
type Place={id:string;name:string;longitude:number|null;latitude:number|null;coreSampleId:string;precision:string};
type ClaimSource={source?:string;url?:string;quote?:string;location?:string;status?:string};
type DemoScope={included?:boolean;requested?:boolean;honoured?:boolean;optIn?:string|null;compatNote?:string};
type SearchResult={answer:string;status:string;judgment?:string|null;claim?:{sources?:ClaimSource[]}|null;algorithmVersion:string;evidence:Evidence[];relations:Relation[];entities:{id:string;name:string}[];places:Place[];limitations:string;demoScope?:DemoScope;contentWarnings?:string[]};

export const EvidenceSearch:React.FC<{steleId:string;onLocate?:(id:string)=>void}>=({steleId,onLocate})=>{
  const [question,setQuestion]=useState('');const [scope,setScope]=useState(true);const [includeDemo,setIncludeDemo]=useState(false);
  const [result,setResult]=useState<SearchResult|null>(null);const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  const [graph,setGraph]=useState<{nodes:{id:string;name:string;category:string}[];links:Relation[];sources:Evidence[]}|null>(null);
  useEffect(()=>{let active=true;setResult(null);setError('');setGraph(null);
    fetch(`/api/research/steles/${encodeURIComponent(steleId)}`).then(async r=>{if(!r.ok)throw new Error('馆藏关系接口暂不可用');return r.json();}).then(d=>{if(active)setGraph(d);}).catch(e=>{if(active)setError(String(e));});
    return()=>{active=false;};},[steleId]);
  const search=async()=>{setBusy(true);setError('');setResult(null);try{
    const response=await fetch('/api/research/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question,steleId:scope?steleId:null,includeDemo})});
    if(!response.ok)throw new Error(`史料检索未成功（${response.status}）`);setResult(await response.json());
  }catch(e){setError(String(e));}finally{setBusy(false);}};
  const names=Object.fromEntries([...(graph?.nodes||[]),...(result?.entities||[])].map(n=>[n.id,n.name]));
  return <section aria-label="史料智能检索" className="glass-panel p-4 md:p-6 rounded-xl border border-gold/20 my-4 text-slate-200">
    <h2 className="text-lg font-serif text-gold">史料智能检索</h2>
    <p className="text-xs text-slate-400 mb-3">本地有据全文检索与关系扩展，资料不足时拒绝补写。</p>
    <div className="grid lg:grid-cols-3 gap-4">
      <form onSubmit={e=>{e.preventDefault();search();}} className="space-y-3">
        <textarea aria-label="史料问题" value={question} onChange={e=>setQuestion(e.target.value)} maxLength={500} placeholder="如：多宝塔碑的撰文者与书丹者是谁？" className="w-full bg-slate-950 border border-slate-700 p-3 rounded min-h-24"/>
        <label className="block text-xs"><input type="checkbox" checked={scope} onChange={e=>setScope(e.target.checked)} data-testid="evidence-scope"/> 限定当前文物；取消后检索全库</label>
        <label className="block text-xs"><input type="checkbox" checked={includeDemo} onChange={e=>setIncludeDemo(e.target.checked)} data-testid="evidence-include-demo"/> 包含演示样本</label>
        {includeDemo && <div role="alert" data-testid="evidence-demo-warning" className="p-2.5 rounded-lg bg-cinnabar/20 border border-cinnabar/40 text-cinnabar-light text-xs">警示：开启后，检索结果将包含合成演示数据（非真实史料/非实测运行），仅供界面演示与联调，不可作为研究结论或评测依据。</div>}
        <button disabled={busy||question.trim().length<2} className="bg-gold text-black rounded px-4 py-2 disabled:opacity-40">{busy?'检索中…':'检索史料'}</button>
        {graph && <details className="text-xs"><summary>本件 {graph.nodes.length} 个有据实体 / {graph.links.length} 条关系</summary>
          {graph.links.map((edge,i)=><p key={i} className="my-2">{names[edge.source]||edge.source} → {edge.relation} → {names[edge.target]||edge.target}<a className="text-gold ml-1" href={edge.sourceUrl} target="_blank" rel="noreferrer">依据</a></p>)}
        </details>}
      </form>
      <div className="lg:col-span-2 text-sm space-y-3 min-w-0" aria-live="polite">
        {error && <p role="alert" className="text-cinnabar-light">{error}</p>}
        {result ? <>{(includeDemo || result.demoScope?.included || result.demoScope?.requested) && <div role="alert" data-testid="evidence-demo-result-banner" className="p-2.5 rounded-lg bg-cinnabar/20 border border-cinnabar/40 text-cinnabar-light text-xs">{result.demoScope?.included ? "本次结果含合成演示数据，不可作为真实史料或评测依据。" : result.demoScope?.requested && result.demoScope?.honoured === false ? "已请求包含演示样本，但当前后端尚未落实 include_demo（兼容模式）；仍按合成演示数据风险读待。" : "已开启「包含演示样本」：结果可含合成演示数据，不可作为研究结论或评测依据。"}</div>}{result.contentWarnings?.map(w=><p key={w} role="note" data-testid="research-content-warning" className="text-xs text-cinnabar-light">注意：结果含{w}，不能作为史料证据。</p>)}<p data-testid="research-answer" className="whitespace-pre-wrap max-h-72 overflow-auto">{result.answer}</p>
          {result.judgment==='disputed' && <p>状态：存在争议。系统保留互相冲突的著录，不按来源排序选边。</p>}
          {result.judgment==='conflict' && <p data-testid="research-conflict">状态：来源冲突。馆藏目录与史料图谱取值不同，以下原样并列，待人工复核。</p>}
          {result.claim?.sources?.map(item => <p key={(item.source || '') + (item.quote || '')} className="text-xs">{item.status} · {item.quote} {item.url && <a className="text-gold underline" href={item.url} target="_blank" rel="noreferrer">{item.source || '查看来源'}</a>}</p>)}
          <p className="text-xs text-slate-400">{result.algorithmVersion} · 检索 {result.status}{result.judgment ? ` · 判断 ${result.judgment==='supported'?'支持':result.judgment==='contradicted'?'反驳':result.judgment==='conflict'?'来源冲突':result.judgment==='disputed'?'存在争议':'证据不足'}` : ''}</p>
          {result.evidence.map((e,i)=><details key={e.sourceId} className="rounded border border-slate-700 p-2"><summary>[{i+1}] {e.title} · {e.evidenceLevel}{e.textProvenance?.kind==='synthetic_test_text'?` · ${e.textProvenance.label}`:''}{e.relevanceLabel&&<span data-testid="weak-relevance" className="ml-1 text-xs text-slate-400">· {e.relevanceLabel}</span>}</summary><p className="whitespace-pre-wrap mt-2">{e.text}</p><p className="text-xs break-all">证据ID：{e.sourceId} · 关联文物：{e.steleId} · 位置：{e.originalPosition}</p><a className="text-gold underline" href={e.url} target="_blank" rel="noreferrer">查看原始来源</a></details>)}
          <details><summary>检索扩展的证据关系（{result.relations.length}）</summary>{result.relations.map((r,i)=><p key={i}>{names[r.source]||r.source} → {r.relation} → {names[r.target]||r.target} <a href={r.sourceUrl} target="_blank" rel="noreferrer" className="text-gold">关系来源</a></p>)}</details>
          {result.places.map(p=><p key={`${p.coreSampleId}-${p.id}`}>地点：{p.name} · {p.precision} {p.longitude!==null&&p.coreSampleId===steleId&&onLocate&&<button className="text-gold underline" onClick={()=>onLocate(p.id)}>在现有GIS中定位</button>}</p>)}
          <p className="text-xs text-slate-500">{result.limitations}</p>
        </> : <p className="text-slate-400">输入文物、人物、纪年或馆藏关系问题。未检索前没有新增考据结论。</p>}
      </div>
    </div>
  </section>;
};
