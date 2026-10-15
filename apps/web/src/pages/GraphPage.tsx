import React, { lazy, Suspense, useEffect, useMemo, useRef, useState } from 'react';
import { Network, MapPin, CalendarDays, BookOpen, ExternalLink, Search, LocateFixed, RotateCcw, Play, Pause, SkipBack, Layers, UserRound } from 'lucide-react';
import type { SteleItem } from '../types/stele';
import type { HistoryDataset, Selection, HistoricalEvent } from '../types/history';
import { CORE_STELES, resolveCoreId } from '../data/graphSelection';
import { loadHistory, convertYear } from '../services/history';
import type { MapCommand } from '../components/graph/HistoricalMap';
import './GraphPage.css';
const HistoricalMap = lazy(() => import('../components/graph/HistoricalMap'));
const KnowledgeNetwork = lazy(() => import('../components/graph/KnowledgeNetwork'));
const TABS = ['文物影像','基础信息','人物关系','地理关联','史料来源'];
const PRECISION = { exact:'精确定位', approximate:'馆区近似', regional:'位置约略 · 区域索引', unknown:'坐标待考' };
const EVENT_TYPES:Record<string,string> = {stele_creation:'立碑',excavation:'出土',transfer:'原石移藏',collection:'典藏',person_activity:'人物活动',historical_context:'史事 / 标签'};
const sceneFor = (_e:HistoricalEvent) => '/assets/gis/timeline-shanshui-concept.png';
const SourceLink = ({url,children}:{url?:string;children:React.ReactNode}) => url ? <a href={url} target="_blank" rel="noopener noreferrer">{children}<ExternalLink size={12}/></a> : <span>{children}</span>;

interface Props {stele:SteleItem;onNavigate:(tab:string)=>void;onSelectStele:(id:string)=>void}
export const GraphPage:React.FC<Props> = ({stele,onSelectStele}) => {
  const [data,setData]=useState<HistoryDataset|null>(null);
  const [error,setError]=useState('');
  const [selection,setSelection]=useState<Selection>({kind:'node',id:resolveCoreId(stele.id)||stele.id});
  const [tab,setTab]=useState('文物影像');
  const [mode,setMode]=useState('全国视图');
  const [command,setCommand]=useState<MapCommand>({kind:'national',serial:0});
  const [category,setCategory]=useState('all');
  const [query,setQuery]=useState('');
  const [labels,setLabels]=useState(true);
  const [boundaries,setBoundaries]=useState(true);
  const [rivers,setRivers]=useState(true);
  const [lines,setLines]=useState(false);
  const [effects,setEffects]=useState(true);
  const [layersOpen,setLayersOpen]=useState(false);
  const [reset,setReset]=useState(0);
  const [playing,setPlaying]=useState(false);
  const [speed,setSpeed]=useState(1);
  const [eventIndex,setEventIndex]=useState(-1);
  const [range,setRange]=useState<[number,number]>([0,9999]);
  const [era,setEra]=useState('');
  const [calendar,setCalendar]=useState<Awaited<ReturnType<typeof convertYear>>|null>(null);
  const [calendarError,setCalendarError]=useState('');
  const [calendarBusy,setCalendarBusy]=useState(false);
  const canonical=resolveCoreId(stele.id)||stele.id;
  const identityRef=useRef(canonical);identityRef.current=canonical;

  useEffect(()=>{
    let active=true;setError('');setPlaying(false);setEventIndex(-1);setQuery('');setTab('文物影像');setCalendar(null);setCalendarError('');
    loadHistory(canonical).then(d=>{
      if(!active)return;setData(d);setSelection({kind:'node',id:d.steleId});setEra(d.eraName);setCategory('all');
      const years=d.events.flatMap(e=>e.yearCE===null?[]:[e.yearCE]);setRange([Math.min(...years,d.yearCE||9999),Math.max(...years,d.yearCE||0)]);
      setCommand(c=>({kind:c.serial===0?'national':'focus',serial:c.serial+1}));
      if(d.yearCE!==null)convertYear(d.eraName).then(result=>{if(active)setCalendar(result);}).catch(()=>{if(active)setCalendarError('纪年服务暂不可用');});
    }).catch(()=>{if(active){setData(null);setError('图谱资料未能加载，请重新选择碑刻。');}});
    return ()=>{active=false;};
  },[canonical]);
  const events=useMemo(()=>data?.events.filter(e=>e.yearCE===null||e.yearCE>=range[0]&&e.yearCE<=range[1]).sort((a,b)=>(a.yearCE??99999)-(b.yearCE??99999))||[],[data,range]);
  const selectedNode=data?.nodes.find(n=>selection.kind==='node'&&n.id===selection.id);
  const selectedPlace=data?.locations.find(p=>selection.kind==='place'&&p.id===selection.id);
  const selectedEvent=data?.events.find(e=>selection.kind==='event'&&e.id===selection.id);
  const selectedIds=useMemo(()=>selectedNode?.locationIds||(selectedPlace?[selectedPlace.id]:selectedEvent?.locationId?[selectedEvent.locationId]:[]),[selectedNode,selectedPlace,selectedEvent]);
  const highlightedPlaces=useMemo(()=>data?selectedIds.map(id=>{const p=data.locations.find(l=>l.id===id);return p?.longitude===null?p.regionLocationId||id:id;}):[],[selectedIds,data]);
  const selectedTitle=selectedNode?.name||selectedPlace?.name||selectedEvent?.title||data?.formalName||'';
  const selectedDescription=selectedNode?.desc||selectedPlace?.note||selectedEvent?.description||data?.identity||'';
  const selectedSource=selectedNode?.sourceUrl||selectedPlace?.sourceUrl||selectedEvent?.sourceUrl;
  const searchResults=data?.locations.filter(p=>`${p.name}${p.modernName}`.includes(query))||[];
  const visibleNodes=data?.nodes.filter(n=>category==='all'||n.category===category||n.category==='stele')||[];
  const visibleNodeIds=new Set(visibleNodes.map(n=>n.id));
  const visibleLinks=data?.links.filter(l=>visibleNodeIds.has(l.source)&&visibleNodeIds.has(l.target))||[];
  const issueCommand=(kind:MapCommand['kind'],placeId?:string,zoom?:number)=>setCommand(c=>({kind,placeId,zoom,serial:c.serial+1}));
  const selectPlace=(id:string,zoom?:number)=>{setPlaying(false);setSelection({kind:'place',id});setTab('地理关联');issueCommand('place',id,zoom);};
  const selectNode=(id:string)=>{setPlaying(false);setSelection({kind:'node',id});setTab(id===data?.steleId?'文物影像':'人物关系');const n=data?.nodes.find(n=>n.id===id);if(n?.category==='stele')issueCommand('focus');else if(n?.locationIds.length)setCommand(c=>({kind:'focus',locationIds:n.locationIds,serial:c.serial+1}));};
  const selectEvent=(event:HistoricalEvent,index:number)=>{setSelection({kind:'event',id:event.id});setEventIndex(index);setTab('基础信息');if(event.locationId)issueCommand('place',event.locationId);};
  useEffect(()=>{
    if(!playing||!events.length)return;
    const timer=window.setTimeout(()=>{
      const next=eventIndex+1;
      if(next>=events.length){setPlaying(false);return;}
      selectEvent(events[next],next);
    },2500/speed);
    return ()=>window.clearTimeout(timer);
  },[playing,eventIndex,speed,events]);
  useEffect(()=>{setPlaying(false);setEventIndex(-1);},[range]);
  const calculate=async()=>{
    const current=canonical;setCalendarBusy(true);setCalendarError('');
    try {const result=await convertYear(era);if(identityRef.current===current)setCalendar(result);}
    catch {if(identityRef.current===current){setCalendar(null);setCalendarError('纪年服务暂不可用，请确认后端连接。');}}
    finally {setCalendarBusy(false);}
  };
  const restore=()=>{setPlaying(false);setSpeed(1);setSelection({kind:'node',id:data!.steleId});setTab('文物影像');setCategory('all');setQuery('');setEventIndex(-1);setLabels(true);setBoundaries(true);setRivers(true);setLines(false);setEffects(true);setLayersOpen(false);setMode('全国视图');setReset(n=>n+1);setRange([Math.min(...data!.events.map(e=>e.yearCE??9999),data!.yearCE??9999),Math.max(...data!.events.map(e=>e.yearCE??0),data!.yearCE??0)]);setEra(data!.eraName);convertYear(data!.eraName).then(setCalendar).catch(()=>setCalendarError('纪年服务暂不可用'));issueCommand('national');};
  const currentData=data?.steleId===canonical?data:null;
  return <div className="graph-page">
    <div className="graph-heading"><div className="heading-emblem"><Network size={28}/></div><div><h1>{currentData?.formalName||stele.title} · 金石时空知识图谱与 GIS 舆图</h1><p>GraphRAG 实体网络 · 人物谱系 · 现代地理底图 · 历史地望互勘</p></div><span className="heading-seal">金石<br/>合参</span></div>
    <div className="core-stele-selector" aria-label="核心测试碑拓选择">{CORE_STELES.map(c=><button key={c.id} data-testid={`stele-${c.id}`} aria-pressed={canonical===c.id} onClick={()=>onSelectStele(c.id)}><span>{c.label.split('·')[0]}</span>{c.label.split('·')[1]}{c.id==='wei-jianyi'&&<small>身份待核</small>}</button>)}</div>
    {error?<div role="alert" className="graph-load">{error}</div>:!data?<div role="status" className="graph-load">正在载入碑刻史料与地望…</div>:<>
    <div className={`explorer-grid ${!currentData?'is-loading':''}`} aria-busy={!currentData}>
      <section className="explorer-panel" aria-label="地图与知识网络">
        <div className="mode-bar">{['全国视图','碑刻地理','人物关系','历史轨迹','地图与图谱联动'].map(m=><button key={m} aria-pressed={mode===m} onClick={()=>{setMode(m);if(m==='全国视图')issueCommand('national');if(m==='碑刻地理'||m==='历史轨迹')issueCommand('focus');}}>{m}</button>)}</div>
        <div className="explorer-tools"><div className="place-search"><Search size={15}/><input aria-label="检索历史地名" value={query} onChange={e=>setQuery(e.target.value)} placeholder="检索历史地名 / 现代地名" onKeyDown={e=>{if(e.key==='Enter'&&searchResults[0])selectPlace(searchResults[0].id);}}/></div><button onClick={()=>issueCommand('focus')} title="定位碑刻关联范围"><LocateFixed size={15}/>自动定位</button><button onClick={()=>setLayersOpen(!layersOpen)} aria-expanded={layersOpen}><Layers size={15}/>图层</button><button onClick={restore} title="恢复所有默认状态"><RotateCcw size={15}/><span>重置</span></button></div>
        {query&&<div className="search-results" role="listbox" aria-label="地名检索结果">{searchResults.length?searchResults.map(p=><button key={p.id} role="option" aria-selected={selectedIds.includes(p.id)} onClick={()=>{selectPlace(p.id);setQuery('');}}>{p.name}<small>{PRECISION[p.precision]}</small></button>):<p>未找到此碑刻的关联地名</p>}</div>}
        {layersOpen&&<div className="layer-controls">{[['地点标签',labels,setLabels],['现代省界与国界',boundaries,setBoundaries],['真实主要水系',rivers,setRivers],['历史关联虚线',lines,setLines],['节点光晕与地形阴影',effects,setEffects]].map(([name,checked,set])=><label key={String(name)}><input type="checkbox" checked={Boolean(checked)} onChange={e=>(set as React.Dispatch<React.SetStateAction<boolean>>)(e.target.checked)}/>{String(name)}</label>)}</div>}
        <div className={`explorer-stage ${mode==='地图与图谱联动'?'linked':''}`}>
          <div className="map-region" style={{display:mode==='人物关系'?'none':'block'}}><Suspense fallback={<div className="graph-load">正在载入 GIS 引擎…</div>}><HistoricalMap data={data} command={command} selectedIds={highlightedPlaces} labels={labels} boundaries={boundaries} rivers={rivers} lines={lines} effects={effects} onSelect={selectPlace}/></Suspense></div>
          {(mode==='人物关系'||mode==='地图与图谱联动')&&<div className="network-region"><Suspense fallback={<div className="graph-load">正在载入人物关系…</div>}><KnowledgeNetwork data={data} selectedId={selection.id} category={category} reset={reset} onSelect={selectNode}/></Suspense></div>}
          <button className="national-return" onClick={()=>{if(mode==='人物关系')setMode('全国视图');issueCommand('national');}}>返回全国视图</button>
          {mode==='人物关系'||mode==='地图与图谱联动'?<div className="node-filter"><select aria-label="筛选图谱节点" value={category} onChange={e=>setCategory(e.target.value)}><option value="all">全部实体</option><option value="person">金石人物</option><option value="place">历史地望</option><option value="era">金石纪年</option><option value="document">文献载体</option></select><span>{visibleNodes.length} 节点 · {visibleLinks.length} 关系</span></div>:null}
        </div>
        <div className="map-provenance"><SourceLink url="https://github.com/MisterChangRay/geodeparse">天地图行政区划镜像 · 上游声明 GS(2024)0650 · MIT</SourceLink><SourceLink url="https://www.naturalearthdata.com/about/terms-of-use/">水系 Natural Earth · 公有领域</SourceLink><SourceLink url="/assets/gis/terrain/ATTRIBUTION.md">地形 Mapzen · USGS / NOAA 等</SourceLink><span>现代省界；古址精度另注。应用未单独审图。</span></div>
        {lines&&<p className="association-note">泥金虚线：原石起讫关联；青绿点线：人物关联地。均不代表已考证的行进路线。</p>}
      </section>
      <aside className="research-sidebar">
        <section className="research-panel"><header><UserRound size={20}/><h2>实体考据详录</h2><span>{selection.kind==='event'?'EVENT':selection.kind==='place'?'PLACE':selectedNode?.category.toUpperCase()||'STELE'}</span></header>
          <div className="research-tabs" role="tablist" aria-label="考据资料">{TABS.map(t=><button key={t} role="tab" aria-selected={tab===t} onClick={()=>setTab(t)}>{t}</button>)}</div>
          <div className="research-content" role="tabpanel">
            <div className="selected-entity"><span className="entity-seal">{selection.kind==='place'?'地':selection.kind==='event'?'纪':selectedNode?.category==='person'?'人':'碑'}</span><div><h3>{selectedTitle}</h3><p>{selectedPlace?PRECISION[selectedPlace.precision]:selectedEvent?selectedEvent.eraName:data.eraName} {data.offline&&'· 本地离线史料'}</p></div></div>
            {tab==='文物影像'&&<><div className="artifact-archive"><a href={data.image} target="_blank" rel="noopener noreferrer"><img src={data.image} alt={`${data.formalName} — ${data.imageStatus}`} loading="lazy"/></a><dl><dt>正式名称</dt><dd>{data.formalName}</dd><dt>原刻 / 标签</dt><dd>{data.eraName}（{data.yearCE??'待考'}）</dd><dt>书体</dt><dd>{data.script}</dd><dt>原石保存</dt><dd>{data.originalStoneCollection}</dd><dt>数字拓本</dt><dd>{data.digitalRubbingCollection}</dd><dt>典藏号</dt><dd>{data.collectionNumber}</dd></dl></div><p className="image-caption">{data.imageStatus}{data.imageStatus.startsWith('真实')&&' · 国立故宫博物院，台北，CC BY 4.0'}</p><SourceLink url={data.image}>查看图像原文件</SourceLink></>}
            {tab==='基础信息'&&<><dl className="detail-list"><dt>原刻纪年 / 测试标签</dt><dd>{data.eraName} · {data.yearCE??'待考'}年</dd><dt>拓本年代</dt><dd>{data.rubbingPeriod}</dd><dt>撰文 / 书丹 / 碑主</dt><dd>{data.authors.join('；')||'尚未核验，不生成通用人物'}</dd><dt>原石保存地</dt><dd>{data.originalStoneCollection}</dd><dt>数字拓本馆藏</dt><dd>{data.digitalRubbingCollection}</dd></dl>{selectedEvent&&<div className="event-detail"><strong>{EVENT_TYPES[selectedEvent.eventType]}</strong><p>{selectedEvent.verification==='confirmed'?'有据':selectedEvent.verification==='approximate'?'区间 / 约略':'身份待核'}</p><p>{selectedEvent.description}</p></div>}</>}
            {tab==='人物关系'&&<div className="entity-list">{data.nodes.filter(n=>n.category==='person'||n.id===selection.id).map(n=><button key={n.id} className={selection.id===n.id?'active':''} onClick={()=>selectNode(n.id)}><UserRound size={15}/><span><b>{n.name}</b><small>{n.desc}</small></span></button>)}{!data.nodes.some(n=>n.category==='person')&&<p>没有已核实人物关系；身份待核样本不补造人物。</p>}{data.links.filter(l=>l.source===selection.id||l.target===selection.id).map(l=><p key={`${l.source}-${l.target}`} className="relation-evidence">{data.nodes.find(n=>n.id===l.source)?.name} → {l.relation} → {data.nodes.find(n=>n.id===l.target)?.name}<SourceLink url={l.sourceUrl}>关系证据</SourceLink></p>)}</div>}
            {tab==='地理关联'&&<><div className="entity-list">{data.locations.map(p=><button key={p.id} className={selectedIds.includes(p.id)?'active':''} onClick={()=>selectPlace(p.id)}><MapPin size={15}/><span><b>{p.name}</b><small>{p.modernName} · {PRECISION[p.precision]}</small></span></button>)}{!data.locations.length&&<p>暂无已核实地理点；地图不设置默认西安坐标。</p>}</div>{selectedPlace&&<div className="coordinate-detail"><p>{selectedPlace.longitude===null?'经纬度未核实；仅文字记录':`WGS84 [${selectedPlace.longitude}, ${selectedPlace.latitude}]`}</p><p>{selectedPlace.coordinateMethod}</p><p>{selectedPlace.note}</p><SourceLink url={selectedPlace.coordinateSourceUrl||undefined}>坐标数据来源</SourceLink></div>}</>}
            {tab==='史料来源'&&<div className="source-list">{data.sources.filter(s=>data.sourceIds.includes(s.id)||selectedIds.some(id=>data.locations.find(l=>l.id===id)?.sourceId===s.id)).map(s=><div key={s.id}><SourceLink url={s.url}>{s.title}</SourceLink><p>{s.institution} · {s.status==='confirmed'?'已核验':'待核 / 约略'}</p><small>{s.notes}</small></div>)}</div>}
            <div className="entity-evidence"><p>{selectedDescription}</p><SourceLink url={selectedSource}>查看本实体史料</SourceLink></div>
          </div>
        </section>
        <section className="calendar-panel" data-testid="calendar"><header><CalendarDays size={18}/><h2>干支历法与金石纪年换算器</h2></header><form onSubmit={e=>{e.preventDefault();calculate();}}><input aria-label="纪年输入" value={era} onChange={e=>setEra(e.target.value)} placeholder="年号与年次 / 公元年份"/><button disabled={calendarBusy} type="submit">{calendarBusy?'换算中':'换算'}</button></form>{calendar?.supported?<div className="calendar-result"><span>公元 <b>{calendar.solar_year}</b> 年</span><span><b>{calendar.ganzhi}</b>年 · 肖{calendar.zodiac}</span></div>:<p className="unsupported" role="status">{calendarError||calendar?.message||'等待纪年换算'}</p>}<small>年度干支 · 支持天宝、中平、熙平、建义年次。<br/>不推算古代朔闰及具体公历月日。</small></section>
      </aside>
    </div>
    <section className="history-timeline" aria-label="历史GIS动态时间轴"><header><MapPin size={21}/><h2>金石行旅与历史 GIS 时空轨迹</h2><p>{data.steleId==='wei-jianyi'?'样本标签待考 · 不绘历史迁移':`${events.length} 条史料事件 · 原石流转与人物生平分开标记`}</p><select aria-label="轨迹播放速度" value={speed} onChange={e=>setSpeed(Number(e.target.value))}><option value={.5}>0.5×</option><option value={1}>1×</option><option value={2}>2×</option></select></header>
      <div className="timeline-body"><div className="playback-controls"><button className="play-button" aria-label={playing?'暂停历史轨迹':'播放历史轨迹'} disabled={!events.length} onClick={()=>{if(!playing&&eventIndex>=events.length-1)setEventIndex(-1);setPlaying(!playing);}}>{playing?<Pause size={24}/>:<Play size={24}/>}</button><button aria-label="重新播放" onClick={()=>{setEventIndex(-1);setPlaying(true);}} disabled={!events.length}><SkipBack size={17}/></button></div><div className="timeline-track" style={{'--progress':eventIndex<0?0:(eventIndex+1)/Math.max(events.length,1)} as React.CSSProperties}>{events.map((e,index)=><article className={`timeline-event ${selection.id===e.id?'active':''} ${e.eventType==='person_activity'?'person-event':''}`} key={e.id}><button data-testid={`event-${e.id}`} onClick={()=>{setPlaying(false);selectEvent(e,index);}}><span className="timeline-dot"/><span className="event-year">{e.eraName}<b>{e.yearCE===null?'纪年待考':`${e.yearCE}年${e.verification==='approximate'?' 起（区间）':''}`}</b></span><span className="event-story"><span className="event-thumbnail" role="img" aria-label="山水建筑概念装饰（非历史建筑复原）" style={{backgroundImage: `url(${sceneFor(e)})`,backgroundPosition: `${[9,30,55,76,92][index%5]}% 92%`}}/><span><small>{EVENT_TYPES[e.eventType]} · {e.verification==='confirmed'?'有据':e.verification==='approximate'?'约略':'待核'}</small><strong>{e.title}</strong><span>{data.locations.find(p=>p.id===e.locationId)?.name||'地点未核 / 未定'}</span></span></span></button><SourceLink url={e.sourceUrl}>史料依据</SourceLink></article>)}</div></div>
      <div className="timeline-footer"><span>场景缩略图为概念装饰；地名与事件以来源为据。</span>{data.events.length>1&&<div className="year-range"><label>时间范围<input aria-label="时间范围起年" type="number" value={range[0]} min={1} max={range[1]} onChange={e=>setRange([Math.min(Number(e.target.value),range[1]),range[1]])}/></label><span>至</span><input aria-label="时间范围止年" type="number" value={range[1]} min={range[0]} max={9999} onChange={e=>setRange([range[0],Math.max(Number(e.target.value),range[0])])}/></div>}</div>
    </section>
    <div className="graph-footnote"><BookOpen size={14}/><span>史料可追溯 · 位置精度公开 · 原石与拓本独立建档</span><span>{data.locations.filter(l=>l.longitude!==null).length} 个空间索引 / {data.locations.length} 条地点记录</span></div>
    </>}
  </div>;
};
