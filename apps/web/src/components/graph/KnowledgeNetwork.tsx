import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts/core';
import { GraphChart } from 'echarts/charts';
import { TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { HistoryDataset } from '../../types/history';
echarts.use([GraphChart,TooltipComponent,CanvasRenderer]);
export const NODE_COLORS = { stele:'#c9452d',person:'#dbb35a',place:'#64b4a2',era:'#a290ba',document:'#a290ba',script:'#a290ba',office:'#dbb35a' };
const ICONS = {
  stele:'<path d="M31 66V29l17-8 17 8v37M25 70h46M38 34h20M38 43h20M38 52h20"/>',
  person:'<circle cx="48" cy="35" r="10"/><path d="M28 70v-6c0-12 9-19 20-19s20 7 20 19v6M40 47l8 10 8-10"/>',
  place:'<path d="M48 74s-20-20-20-34a20 20 0 0 1 40 0c0 14-20 34-20 34Z"/><circle cx="48" cy="40" r="7"/>',
  era:'<rect x="25" y="27" width="46" height="42" rx="4"/><path d="M35 22v12M61 22v12M25 40h46M35 50h9M52 50h9M35 60h9M52 60h9"/>',
  document:'<path d="M31 22h25l12 12v39H31ZM55 22v14h13M39 46h20M39 55h20M39 64h13"/>',
};
function symbol(category:string){
  const color=NODE_COLORS[category as keyof typeof NODE_COLORS]||NODE_COLORS.document;
  const icon=ICONS[category as keyof typeof ICONS]||ICONS.document;
  return 'image://data:image/svg+xml;base64,'+btoa(`<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96"><circle cx="48" cy="48" r="44" fill="${color}" fill-opacity=".86" stroke="#ead5a0" stroke-width="2"/><g fill="none" stroke="#fff1d2" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">${icon}</g></svg>`);
}
interface Props {data:HistoryDataset; selectedId:string; category:string; reset:number; onSelect:(id:string)=>void}
export default function KnowledgeNetwork({data,selectedId,category,reset,onSelect}:Props){
  const container=useRef<HTMLDivElement>(null);
  const instance=useRef<echarts.ECharts>();
  const [width,setWidth]=useState(900);
  const select=useRef(onSelect); select.current=onSelect;
  useEffect(()=>{
    if(!container.current)return;
    const chart=echarts.init(container.current);instance.current=chart;
    chart.on('click',(p:any)=>{if(p.dataType==='node')select.current(p.data.id);});
    const resize=new ResizeObserver(()=>{chart.resize();setWidth(Math.round(container.current?.clientWidth||900));});resize.observe(container.current);
    return ()=>{resize.disconnect();chart.dispose();instance.current=undefined;};
  },[]);
  useEffect(()=>{
    const nodes=data.nodes.filter(n=>category==='all'||n.category===category||n.category==='stele');
    const ids=new Set(nodes.map(n=>n.id));
    const compact=width<500;
    instance.current?.setOption({tooltip:{renderMode:'richText',formatter:(p:any)=>p.dataType==='node'?p.data.name:p.data.relation},series:[{
      type:'graph',layout:'force',roam:true,draggable:true,left:compact?55:90,right:compact?55:90,top:65,bottom:75,zoom:compact?.95:1,
      force:{repulsion:compact?450:550,edgeLength:compact?[75,110]:[100,160],gravity:compact?.12:.15},
      data:nodes.map(n=>({...n,symbol:symbol(n.category),symbolSize:n.category==='stele'?(compact?60:78):(compact?38:48),itemStyle:{color:NODE_COLORS[n.category],shadowBlur:n.category==='stele'?14:2,shadowColor:NODE_COLORS[n.category]},label:{show:true,position:'bottom',color:'#e9e3d6',fontFamily:'serif',fontSize:compact?11:12,distance:6,formatter:(p:any)=>{const line=compact?5:7;return p.name.length>line+1?p.name.slice(0,line)+'\n'+p.name.slice(line):p.name;}}})),
      links:data.links.filter(l=>ids.has(l.source)&&ids.has(l.target)).map(l=>({...l,label:{show:!compact,formatter:l.relation,color:'#c8b980',fontSize:10},emphasis:{label:{show:true,formatter:l.relation}},lineStyle:{color:l.verification==='unverified'?'#887592':'#997d44',width:1.4,curveness:.08,type:l.verification==='unverified'?'dashed':'solid'}})),
      emphasis:{focus:'adjacency',edgeLabel:{show:true},itemStyle:{borderWidth:3},lineStyle:{width:3,color:'#e8c273'}},
    }]},true);
  },[data,category,reset,width]);
  useEffect(()=>{instance.current?.dispatchAction({type:'downplay'});instance.current?.dispatchAction({type:'highlight',name:data.nodes.find(n=>n.id===selectedId)?.name});},[selectedId,data,category,reset,width]);
  return <div className="knowledge-network" data-testid="knowledge-network"><div ref={container}/><p>实体关系网络 · 可拖动节点 · 位置不表示经纬度</p></div>;
}
