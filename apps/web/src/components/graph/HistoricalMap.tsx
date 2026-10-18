import React, { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Compass, MapPin } from 'lucide-react';
import type { HistoryDataset, HistoricalLocation } from '../../types/history';
import { chinaMapStyle } from './chinaMapStyle';
// Vite may inject helpers into MapLibre's inline worker serialization. Use the untransformed CSP worker.
maplibregl.setWorkerUrl(workerUrl);

export interface MapCommand { kind: 'national' | 'focus' | 'place'; placeId?: string; locationIds?:string[]; zoom?:number; serial: number }
export const NATIONAL_BOUNDS: [[number,number],[number,number]] = [[73,17],[135,54]];
const style = chinaMapStyle;

export function resolveMapPlace(data: HistoryDataset, id?: string | null): HistoricalLocation | undefined {
  const p = data.locations.find(l => l.id === id);
  return p && p.longitude !== null && p.latitude !== null ? p : data.locations.find(l => l.id === p?.regionLocationId);
}
interface Props { data: HistoryDataset; command: MapCommand; selectedIds: string[]; labels: boolean; boundaries: boolean; rivers: boolean; lines: boolean; effects: boolean; onSelect: (id: string, zoom?:number) => void }
export default function HistoricalMap({ data, command, selectedIds, labels, boundaries, rivers, lines, effects, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const insetContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markers = useRef<maplibregl.Marker[]>([]);
  const provinceMarkers = useRef<maplibregl.Marker[]>([]);
  const select = useRef(onSelect); select.current = onSelect;
  const [ready, setReady] = useState(false);
  const [error, setError] = useState('');
  const [camera, setCamera] = useState({ zoom: 0, longitude: 105, latitude: 35 });
  useEffect(() => {
    if (!container.current) return;
    let inset: maplibregl.Map | undefined;
    try {
      const m = new maplibregl.Map({ container: container.current, style: style(), center: [105,35], zoom:3, minZoom:1, maxZoom:15, renderWorldCopies:false, attributionControl:false });
      map.current = m;
      m.addControl(new maplibregl.NavigationControl({ showCompass:false }),'top-right');
      m.addControl(new maplibregl.ScaleControl({unit:'metric'}),'bottom-left');
      m.on('load', () => {
        m.fitBounds(NATIONAL_BOUNDS,{padding:45,duration:0}); setReady(true);
        fetch('/assets/gis/province-labels.json').then(r=>r.json()).then((places:{name:string;coordinates:[number,number]}[])=>{
          if(map.current!==m)return;
          places.forEach(p=>{const el=document.createElement('span');el.className='province-label';el.textContent=p.name.replace('维吾尔自治区','').replace('壮族自治区','').replace('回族自治区','').replace('自治区','');provinceMarkers.current.push(new maplibregl.Marker({element:el}).setLngLat(p.coordinates).addTo(m));});
        }).catch(()=>setError('现代地名标注未加载，可重开页面恢复。'));
      });
      m.on('error', e => setError(`地图资源加载失败：${e.error.message}`));
      m.on('moveend', () => { const p=m.getCenter(); setCamera({zoom:m.getZoom(),longitude:p.lng,latitude:p.lat}); });
      if (insetContainer.current) {
        inset=new maplibregl.Map({container:insetContainer.current,style:style(),interactive:false,attributionControl:false,renderWorldCopies:false});
        inset.on('load',()=>inset?.fitBounds([[105,3],[125,24]],{padding:4,duration:0}));
      }
      const resize = new ResizeObserver(() => { m.resize(); inset?.resize(); }); resize.observe(container.current);
      return () => { resize.disconnect(); markers.current.forEach(mk=>mk.remove()); markers.current=[]; provinceMarkers.current.forEach(mk=>mk.remove());provinceMarkers.current=[];inset?.remove(); m.remove(); map.current=null; };
    } catch { setError('浏览器暂不支持 WebGL，请使用支持硬件加速的浏览器。'); }
  }, []);

  useEffect(() => {
    const m=map.current; if (!ready || !m) return;
    markers.current.forEach(mk=>mk.remove()); markers.current=[];
    data.locations.filter(p=>p.longitude!==null && p.latitude!==null).forEach(p=>{
      const button=document.createElement('button');
      button.className=`historical-marker ${p.type==='current_collection' ? 'collection' : p.type==='historical_activity'||p.type==='ancestral_origin' ? 'activity' : 'original'} ${selectedIds.includes(p.id) ? 'selected' : ''} ${effects ? 'with-effects' : ''}`;
      button.setAttribute('aria-label',`地图地点：${p.name}`); button.setAttribute('data-place-id',p.id);
      const glyph=document.createElement('span'); glyph.className='marker-symbol'; glyph.textContent=p.type==='current_collection' ? '藏' : p.type==='ancestral_origin' ? '籍' : p.type==='historical_activity' ? '地' : '碑'; button.append(glyph);
      if(labels){ const name=document.createElement('span'); name.className='marker-label'; name.textContent=p.name; button.append(name); }
      button.addEventListener('click',e=>{e.stopPropagation();select.current(p.id);});
      button.addEventListener('dblclick',e=>{e.preventDefault();e.stopPropagation();select.current(p.id,11);});
      markers.current.push(new maplibregl.Marker({element:button}).setLngLat([p.longitude!,p.latitude!]).addTo(m));
    });
    // Every link is labelled as an association. It is never a transport itinerary.
    const features: GeoJSON.Feature[]=[];
    if(lines){
      const stone=data.locations.filter(l=>['original_site','current_collection'].includes(l.type) && l.longitude!==null);
      if(stone.length===2) features.push({type:'Feature',properties:{kind:'stone_transfer',meaning:'原石两端关联；路径未考'},geometry:{type:'LineString',coordinates:stone.map(l=>[l.longitude!,l.latitude!])}});
      const activity=data.locations.filter(l=>['ancestral_origin','historical_activity'].includes(l.type) && l.longitude!==null);
      const origin=data.locations.find(l=>l.type==='original_site'&&l.longitude!==null);
      if(origin) activity.forEach(l=>features.push({type:'Feature',properties:{kind:'person_activity',meaning:'人物与立碑地关联；不是旅行线路'},geometry:{type:'LineString',coordinates:[[origin.longitude!,origin.latitude!],[l.longitude!,l.latitude!]]}}));
    }
    (m.getSource('relations') as maplibregl.GeoJSONSource).setData({type:'FeatureCollection',features});
    for(const layer of ['region-fill','region-outline'])m.setFilter(layer,['in',['get','locationId'],['literal',data.locations.map(l=>l.id)]]);
  },[ready,data,labels,lines]);
  useEffect(()=>{
    markers.current.forEach(marker=>{
      const element=marker.getElement();
      element.classList.toggle('selected',selectedIds.includes(element.dataset.placeId!));
      element.classList.toggle('with-effects',effects);
    });
  },[ready,data,selectedIds,effects,labels,lines]);

  useEffect(()=>{
    const m=map.current; if(!ready||!m)return;
    for(const layer of ['province-outline','national-outline']) m.setLayoutProperty(layer,'visibility',boundaries?'visible':'none');
    m.setLayoutProperty('rivers','visibility',rivers?'visible':'none');
  },[ready,boundaries,rivers]);
  useEffect(()=>{provinceMarkers.current.forEach(marker=>marker.getElement().style.display=labels?'block':'none');},[labels]);
  useEffect(()=>{
    const m = map.current; if(!ready || !m) return;
    const visible = effects ? 'visible' : 'none';
    m.setLayoutProperty('terrain-shade','visibility', visible);
    if (m.getLayer('terrain-color')) m.setLayoutProperty('terrain-color','visibility', visible);
    m.setPaintProperty('land','fill-opacity', effects ? 0 : 0.94);
  },[ready,effects]);
  useEffect(()=>{
    const m=map.current; if(!ready||!m)return;
    if(command.kind==='national'){m.fitBounds(NATIONAL_BOUNDS,{padding:45,duration:650});return;}
    const p=resolveMapPlace(data,command.placeId);
    if(command.kind==='place'&&p){m.flyTo({center:[p.longitude!,p.latitude!],zoom:command.zoom??(p.precision==='regional'?5.3:6),duration:800});return;}
    const points=command.locationIds?.length
      ? command.locationIds.map(id=>resolveMapPlace(data,id)).filter((l):l is HistoricalLocation=>!!l&&l.longitude!==null&&l.latitude!==null)
      : data.locations.filter(l=>l.longitude!==null&&l.latitude!==null);
    if(!points.length){m.fitBounds(NATIONAL_BOUNDS,{padding:45,duration:650});return;}
    if(points.length===1){m.flyTo({center:[points[0].longitude!,points[0].latitude!],zoom:5.3,duration:750});return;}
    const b=new maplibregl.LngLatBounds(); points.forEach(l=>b.extend([l.longitude!,l.latitude!]));
    m.fitBounds(b,{padding:{top:75,bottom:75,left:95,right:95},maxZoom:8.2,duration:750});
  },[ready,command,data]);
  return <div className="historical-map" data-testid="historical-map" data-ready={ready} data-zoom={camera.zoom} data-center={`${camera.longitude},${camera.latitude}`}>
    <div className="map-canvas" ref={container}/>
    <div className="map-compass" aria-hidden="true"><span>北</span><Compass size={48} strokeWidth={.7}/></div>
    <div className="map-coordinate">{camera.longitude.toFixed(2)}° E · {camera.latitude.toFixed(2)}° N <span>WGS84 地望索引</span></div>
    {camera.zoom>=4&&<div className="region-legend">青绿虚线面：现代定位县区</div>}
    <div className="south-sea-inset"><div ref={insetContainer}/><span>南海诸岛 · 同源地理附图</span></div>
    <div className="map-key"><span><i className="red"/>立碑地望</span><span><i className="gold"/>原石保存</span><span><i className="green"/>人物关联地</span></div>
    {data.locations.length===0&&<div className="map-empty"><MapPin size={25}/><strong>地望待考</strong><span>本样本没有已核实地理点，保留全国底图。</span></div>}
    {error&&<div role="alert" className="map-error">{error}</div>}
  </div>;
}
