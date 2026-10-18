import React, { useEffect, useMemo, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Compass, MapPin, Mountain, RotateCw, Layers3, Eye } from 'lucide-react';
import type { HistoryDataset, HistoricalLocation } from '../../types/history';
import { chinaMapStyle } from './chinaMapStyle';
import { DemStore } from './terrain3d/dem';
import { Terrain3DScene, type TerrainStats } from './terrain3d/terrainLayer';
// Vite may inject helpers into MapLibre's inline worker serialization. Use the untransformed CSP worker.
maplibregl.setWorkerUrl(workerUrl);

export interface MapCommand { kind: 'national' | 'focus' | 'place'; placeId?: string; locationIds?: string[]; zoom?: number; serial: number }
export const NATIONAL_BOUNDS: [[number, number], [number, number]] = [[73, 17], [135, 54]];
const style = chinaMapStyle;

/** Layers owned by the 2D style. In 3D the same data is draped onto the DEM mesh. */
const STYLE_LAYERS = ['terrain-color', 'terrain-shade', 'land', 'province-outline', 'national-line', 'national-outline', 'rivers', 'rivers-case', 'region-fill', 'region-outline', 'stone-links', 'person-links'];

export function resolveMapPlace(data: HistoryDataset, id?: string | null): HistoricalLocation | undefined {
  const p = data.locations.find(l => l.id === id);
  return p && p.longitude !== null && p.latitude !== null ? p : data.locations.find(l => l.id === p?.regionLocationId);
}

interface MarkerRecord { id: string; el: HTMLButtonElement; lng: number; lat: number; priority: number; labelEl: HTMLElement | null; labelW: number; labelH: number }
interface LabelRecord { el: HTMLSpanElement; lng: number; lat: number; w: number; h: number }
interface ScreenBox { x0: number; y0: number; x1: number; y1: number }

interface Props {
  data: HistoryDataset;
  command: MapCommand;
  selectedIds: string[];
  labels: boolean;
  /** 中国国界（含海岸线）图层 */
  nationalBorder: boolean;
  /** 省级行政边界图层（省际共享边界去重后） */
  provinceBorder: boolean;
  rivers: boolean;
  lines: boolean;
  effects: boolean;
  onSelect: (id: string, zoom?: number) => void;
  /** 三维地形开关；false 时为原有二维 MapLibre 视图 */
  terrain3d: boolean;
  /** 垂直夸张倍数；null 表示按缩放自动 */
  exaggeration: number | null;
  /** 等高线（由同一 DEM 派生） */
  contours?: boolean;
  onTerrainStats?: (stats: TerrainStats) => void;
  onTerrainState?: (state: { ready: boolean; error: string; pitch: number; bearing: number; zoom: number }) => void;
}

export default function HistoricalMap({ data, command, selectedIds, labels, nationalBorder, provinceBorder, rivers, lines, effects, onSelect, terrain3d, exaggeration, contours = true, onTerrainStats, onTerrainState }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const insetContainer = useRef<HTMLDivElement>(null);
  const overlay = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const inset = useRef<maplibregl.Map | null>(null);
  const scene = useRef<Terrain3DScene | null>(null);
  const store = useRef<DemStore | null>(null);
  const terrainLoading = useRef(false);
  const lastLayoutAt = useRef(0);
  const markers = useRef<MarkerRecord[]>([]);
  const provinceLabels = useRef<LabelRecord[]>([]);
  const select = useRef(onSelect); select.current = onSelect;
  const statsHandler = useRef(onTerrainStats); statsHandler.current = onTerrainStats;
  const stateHandler = useRef(onTerrainState); stateHandler.current = onTerrainState;
  const mode3d = useRef(terrain3d); mode3d.current = terrain3d;
  const exaggerationRef = useRef(exaggeration); exaggerationRef.current = exaggeration;
  const flags = useRef({ nationalBorder, provinceBorder, rivers, lines, effects, labels, terrainReady: false });
  flags.current = { ...flags.current, nationalBorder, provinceBorder, rivers, lines, effects, labels };
  const vectorsRef = useRef<{ provinces?: GeoJSON.FeatureCollection; provinceInternal?: GeoJSON.FeatureCollection; national?: GeoJSON.FeatureCollection; maritime?: GeoJSON.FeatureCollection; rivers?: GeoJSON.FeatureCollection; regions?: GeoJSON.FeatureCollection }>({});
  const [ready, setReady] = useState(false);
  const [error, setError] = useState('');
  const [terrain, setTerrain] = useState<{ ready: boolean; error: string; pitch: number; bearing: number }>({ ready: false, error: '', pitch: 0, bearing: 0 });
  const [camera, setCamera] = useState({ zoom: 0, longitude: 105, latitude: 35, bearing: 0 });
  const [pitch, setPitch] = useState(0);
  const [frame, setFrame] = useState({ width: 0, height: 0 });
  flags.current.terrainReady = terrain.ready;

  const nationalPadding = (m: maplibregl.Map, is3d: boolean) => {
    const { clientWidth: width, clientHeight: height } = m.getContainer();
    const side = Math.max(26, width * 0.14);
    return {
      top: Math.max(46, height * (is3d ? 0.17 : 0.08)),
      bottom: Math.max(46, height * (is3d ? 0.16 : 0.09)),
      left: side,
      right: side,
    };
  };

  /** Projected pixel box of the national extent in the current camera. */
  const projectedNationalBox = (m: maplibregl.Map) => {
    const [west, south] = NATIONAL_BOUNDS[0];
    const [east, north] = NATIONAL_BOUNDS[1];
    const points: [number, number][] = [];
    for (let i = 0; i <= 8; i++) {
      const t = i / 8;
      points.push([west + (east - west) * t, south], [west + (east - west) * t, north], [west, south + (north - south) * t], [east, south + (north - south) * t]);
    }
    let x0 = Infinity; let x1 = -Infinity; let y0 = Infinity; let y1 = -Infinity;
    for (const [lng, lat] of points) {
      const p = m.project([lng, lat]);
      x0 = Math.min(x0, p.x); x1 = Math.max(x1, p.x);
      y0 = Math.min(y0, p.y); y1 = Math.max(y1, p.y);
    }
    return { x0, x1, y0, y1 };
  };

  /**
   * Fit China into the viewport while the camera is pitched. `fitBounds` assumes
   * a top-down camera, so the national frame is solved here by bisecting zoom
   * against the projected extent and then re-centring the projected box.
   */
  const frameNational = (m: maplibregl.Map, duration = 0, is3d = mode3d.current) => {
    const { clientWidth: width, clientHeight: height } = m.getContainer();
    const pad = nationalPadding(m, is3d);
    if (!is3d) {
      m.easeTo({ pitch: 0, bearing: 0, duration });
      m.fitBounds(NATIONAL_BOUNDS, { padding: pad, duration });
      return;
    }
    const pitch = 44;
    m.jumpTo({ center: [104.5, 35.5], pitch, bearing: m.getBearing() });
    let lo = 1.1;
    let hi = 6.6;
    for (let i = 0; i < 22; i++) {
      const mid = (lo + hi) / 2;
      m.jumpTo({ zoom: mid });
      const box = projectedNationalBox(m);
      const fits = box.x0 >= pad.left && box.x1 <= width - pad.right && box.y0 >= pad.top && box.y1 <= height - pad.bottom;
      if (fits) { lo = mid; } else { hi = mid; }
    }
    m.jumpTo({ zoom: lo });
    const box = projectedNationalBox(m);
    const targetX = pad.left + (width - pad.left - pad.right) / 2;
    const targetY = pad.top + (height - pad.top - pad.bottom) / 2;
    const dx = targetX - (box.x0 + box.x1) / 2;
    const dy = targetY - (box.y0 + box.y1) / 2;
    if (Math.abs(dx) > 0.5 || Math.abs(dy) > 0.5) m.panBy([-dx, -dy], { duration: 0 });
    m.triggerRepaint();
    if (duration > 0) m.easeTo({ duration, pitch, bearing: m.getBearing() });
    updateFrameMetric(m);
  };

  const updateFrameMetric = (m: maplibregl.Map) => {
    const box = projectedNationalBox(m);
    const width = m.getContainer().clientWidth || 1;
    const height = m.getContainer().clientHeight || 1;
    setFrame({ width: Number(((box.x1 - box.x0) / width).toFixed(3)), height: Number(((box.y1 - box.y0) / height).toFixed(3)) });
  };

  const syncOverlay = () => {
    const layer = overlay.current;
    const m = map.current;
    if (!layer || !m) return;
    const width = layer.clientWidth;
    const height = layer.clientHeight;
    const active = mode3d.current && scene.current && flags.current.terrainReady;
    const zoom = m.getZoom();

    const markerScreen: Array<{ record: MarkerRecord; x: number; y: number; onScreen: boolean }> = [];
    for (const marker of markers.current) {
      let x = 0; let y = 0; let visible = true;
      if (active && scene.current) {
        const projected = scene.current.screenPosition(marker.lng, marker.lat, width, height);
        x = projected.x; y = projected.y; visible = projected.visible;
      } else {
        const projected = m.project([marker.lng, marker.lat]);
        x = projected.x; y = projected.y;
        visible = x > -80 && x < width + 80 && y > -80 && y < height + 80;
      }
      marker.el.style.transform = `translate(-50%,-50%) translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
      marker.el.style.visibility = visible ? 'visible' : 'hidden';
      markerScreen.push({ record: marker, x, y, onScreen: visible });
    }

    const labelScreen: Array<{ record: LabelRecord; x: number; y: number; onScreen: boolean }> = [];
    for (const label of provinceLabels.current) {
      let x = 0; let y = 0; let visible = true;
      if (active && scene.current) {
        const projected = scene.current.screenPosition(label.lng, label.lat, width, height);
        x = projected.x; y = projected.y; visible = projected.visible;
      } else {
        const projected = m.project([label.lng, label.lat]);
        x = projected.x; y = projected.y;
      }
      label.el.style.transform = `translate(-50%,-50%) translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
      label.el.style.visibility = visible ? 'visible' : 'hidden';
      labelScreen.push({ record: label, x, y, onScreen: visible });
    }

    // Label layout runs every frame with cached sizes, so the last frame always
    // matches the final camera; collisions are resolved deterministically, which
    // keeps labels from flickering while panning.
    layoutLabels(markerScreen, labelScreen, width, height, zoom);
  };

  /**
   * Greedy screen-space collision layout. Markers always keep their dot; their
   * text and the province names compete for space with national border priority:
   * selected marker > stele marker > province name > secondary place label.
   */
  const layoutLabels = (
    markerScreen: Array<{ record: MarkerRecord; x: number; y: number; onScreen: boolean }>,
    labelScreen: Array<{ record: LabelRecord; x: number; y: number; onScreen: boolean }>,
    width: number,
    height: number,
    zoom: number,
  ) => {
    const placed: ScreenBox[] = [];
    const margin = 2;
    const fits = (box: ScreenBox) => {
      if (box.x1 < -40 || box.x0 > width + 40 || box.y1 < -40 || box.y0 > height + 40) return false;
      for (const other of placed) {
        if (box.x0 < other.x1 + margin && box.x1 > other.x0 - margin && box.y0 < other.y1 + margin && box.y1 > other.y0 - margin) return false;
      }
      return true;
    };
    const add = (box: ScreenBox) => placed.push(box);

    const labelsOn = flags.current.labels;
    // Dots first: they are the geographic anchor and must never be hidden.
    const ordered = [...markerScreen].sort((a, b) => a.record.priority - b.record.priority);
    for (const item of ordered) {
      if (!item.onScreen) continue;
      const size = item.record.el.offsetWidth || 29;
      add({ x0: item.x - size / 2, y0: item.y - size / 2, x1: item.x + size / 2, y1: item.y + size / 2 });
    }

    // Marker text: the selected marker wins, then stele markers.
    for (const item of ordered) {
      const label = item.record.labelEl;
      if (!label) continue;
      if (!item.onScreen || !labelsOn) { label.style.visibility = 'hidden'; continue; }
      const showAtThisZoom = item.record.priority <= 1 || zoom >= 4.6;
      if (!showAtThisZoom) { label.style.visibility = 'hidden'; continue; }
      const w = item.record.labelW || 90;
      const h = item.record.labelH || 18;
      const box = { x0: item.x - w / 2, y0: item.y + 15, x1: item.x + w / 2, y1: item.y + 15 + h };
      if (fits(box)) { label.style.visibility = 'visible'; add(box); } else { label.style.visibility = 'hidden'; }
    }

    // Province names fill the remaining space. The anchor stays at the true
    // coordinate; only the text is nudged (right/left/above/below) until it fits,
    // which keeps dense eastern provinces labelled without moving any geography.
    for (const item of labelScreen) {
      const el = item.record.el;
      if (!item.onScreen || !labelsOn) { el.style.visibility = 'hidden'; el.style.marginLeft = '0px'; el.style.marginTop = '0px'; continue; }
      const w = item.record.w || 40;
      const h = item.record.h || 17;
      const candidates: Array<[number, number]> = [
        [0, 0],
        [w * 0.62, 0],
        [-w * 0.62, 0],
        [0, -h - 3],
        [0, h + 3],
        [w * 0.55, -h - 2],
        [-w * 0.55, -h - 2],
        [w * 0.7, h * 0.9],
        [-w * 0.7, h * 0.9],
        [w * 0.7, -h * 0.9],
        [-w * 0.7, -h * 0.9],
        [w * 0.95, 0],
        [-w * 0.95, 0],
      ];
      let placedBox: ScreenBox | null = null;
      let chosen: [number, number] = [0, 0];
      for (const [dx, dy] of candidates) {
        const cx = item.x + dx;
        const cy = item.y + dy;
        const box = { x0: cx - w / 2, y0: cy - h / 2, x1: cx + w / 2, y1: cy + h / 2 };
        if (fits(box)) { placedBox = box; chosen = [dx, dy]; break; }
      }
      if (placedBox) {
        el.style.marginLeft = `${chosen[0].toFixed(1)}px`;
        el.style.marginTop = `${chosen[1].toFixed(1)}px`;
        el.style.visibility = 'visible';
        add(placedBox);
      } else {
        el.style.visibility = 'hidden';
      }
    }
  };

  const reportState = () => {
    const m = map.current;
    if (!m) return;
    const state = { ready: Boolean(scene.current && flags.current.terrainReady), error: terrain.error, pitch: m.getPitch(), bearing: m.getBearing(), zoom: m.getZoom() };
    setPitch(m.getPitch());
    stateHandler.current?.(state);
  };

  const applyLayerMode = () => {
    const m = map.current;
    if (!m) return;
    const is3d = mode3d.current;
    const { nationalBorder: showNational, provinceBorder: showProvinces, rivers: showRivers, lines: showLines, effects: showEffects } = flags.current;
    const engine = scene.current;
    const engineReady = Boolean(engine && flags.current.terrainReady);
    // The terrain engine draws the surface plus the draped vectors in both modes;
    // the styled layers stay as the no-WebGL / engine-failure fallback.
    for (const id of STYLE_LAYERS) {
      if (!m.getLayer(id)) continue;
      m.setLayoutProperty(id, 'visibility', engineReady ? 'none' : 'visible');
    }
    if (!engineReady) {
      for (const id of ['national-outline', 'national-line']) if (m.getLayer(id)) m.setLayoutProperty(id, 'visibility', showNational ? 'visible' : 'none');
      for (const id of ['province-outline', 'province-casing']) if (m.getLayer(id)) m.setLayoutProperty(id, 'visibility', showProvinces ? 'visible' : 'none');
      for (const id of ['rivers', 'rivers-case']) if (m.getLayer(id)) m.setLayoutProperty(id, 'visibility', showRivers ? 'visible' : 'none');
      if (m.getLayer('terrain-shade')) m.setLayoutProperty('terrain-shade', 'visibility', showEffects ? 'visible' : 'none');
      if (m.getLayer('terrain-color')) m.setLayoutProperty('terrain-color', 'visibility', showEffects ? 'visible' : 'none');
      if (m.getLayer('land')) m.setPaintProperty('land', 'fill-opacity', showEffects ? 0 : 0.94);
    }
    if (engine) {
      engine.setVisible(engineReady);
      engine.setFlat(!is3d);
      engine.setVectorVisibility({
        national: showNational,
        provinces: showProvinces,
        rivers: showRivers,
        regions: m.getZoom() >= 4.2,
        relations: showLines,
      });
    }
    m.triggerRepaint();
  };

  const ensureTerrain = async () => {
    const m = map.current;
    if (!m || scene.current || terrainLoading.current) return;
    terrainLoading.current = true;
    try {
      setTerrain(t => ({ ...t, error: '' }));
      const demStore = new DemStore();
      store.current = demStore;
      await demStore.loadManifest();
      const engine = new Terrain3DScene(m, demStore);
      m.addLayer(engine.layer);
      scene.current = engine;
      if ((import.meta as unknown as { env?: { DEV?: boolean } }).env?.DEV) (window as unknown as { __terrain3d?: unknown }).__terrain3d = engine;
      engine.onStats(stats => statsHandler.current?.(stats));
      engine.onError(message => {
        flags.current.terrainReady = false;
        setTerrain(t => ({ ...t, ready: false, error: `三维地形中断：${message}；已回退到二维底图。` }));
        applyLayerMode();
      });
      m.setMaxPitch(72);
      const [provinces, riversData, regions, nationalBoundary, provinceInternal] = await Promise.all([
        fetch('/assets/gis/china-provinces.cgcs2000.geojson').then(r => r.json()),
        fetch('/assets/gis/rivers.geojson').then(r => r.json()),
        fetch('/assets/gis/coordinate-regions.geojson').then(r => r.json()),
        fetch('/assets/gis/china-national-boundary.geojson').then(r => r.json()),
        fetch('/assets/gis/china-province-internal-boundaries.geojson').then(r => r.json()),
      ]);
      const maritime: GeoJSON.FeatureCollection = {
        type: 'FeatureCollection',
        features: provinces.features.filter((f: GeoJSON.Feature) => f.geometry?.type === 'MultiLineString' || f.geometry?.type === 'LineString'),
      };
      const provinceShapes: GeoJSON.FeatureCollection = {
        type: 'FeatureCollection',
        features: provinces.features.filter((f: GeoJSON.Feature) => f.geometry?.type === 'MultiPolygon' || f.geometry?.type === 'Polygon'),
      };
      vectorsRef.current = { provinces: provinceShapes, provinceInternal, national: nationalBoundary, maritime, rivers: riversData, regions };
      engine.setVectors(vectorsRef.current);
      engine.setExaggeration(exaggerationRef.current);
      applyLayerMode();
      flags.current.terrainReady = true;
      setTerrain(t => ({ ...t, ready: true, error: '' }));
      applyLayerMode();
      reportState();
    } catch (reason) {
      setTerrain(t => ({ ...t, ready: false, error: `三维地形未能初始化：${reason instanceof Error ? reason.message : String(reason)}` }));
    } finally {
      terrainLoading.current = false;
    }
  };

  useEffect(() => {
    if (!container.current) return;
    let disposed = false;
    try {
      const m = new maplibregl.Map({ container: container.current, style: style(), center: [105, 35], zoom: 3, minZoom: 1, maxZoom: 15, renderWorldCopies: false, attributionControl: false, pitch: terrain3d ? 38 : 0 });
      map.current = m;
      if ((import.meta as unknown as { env?: { DEV?: boolean } }).env?.DEV) (window as unknown as { __historicalMap?: unknown }).__historicalMap = m;
      m.addControl(new maplibregl.NavigationControl({ showCompass: true, visualizePitch: true }), 'top-right');
      m.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-left');
      m.on('load', () => {
        frameNational(m, 0);
        setReady(true);
        if (mode3d.current) void ensureTerrain();
        const prefix = (name: string) => name.replace('维吾尔自治区', '').replace('壮族自治区', '').replace('回族自治区', '').replace('自治区', '').replace('特别行政区', '');
        fetch('/assets/gis/province-labels.json').then(r => r.json()).then((places: { name: string; coordinates: [number, number] }[]) => {
          if (map.current !== m) return;
          places.forEach(p => {
            const el = document.createElement('span');
            el.className = 'province-label';
            el.textContent = prefix(p.name);
            overlay.current?.appendChild(el);
            // Measure once: the text never changes, so collision tests can stay cheap.
            provinceLabels.current.push({ el, lng: p.coordinates[0], lat: p.coordinates[1], w: el.offsetWidth || 40, h: el.offsetHeight || 16 });
          });
          syncOverlay();
        }).catch(() => setError('现代地名标注未加载，可重开页面恢复。'));
      });
      m.on('error', e => setError(`地图资源加载失败：${e.error.message}`));
      m.on('moveend', () => {
        const p = m.getCenter();
        setCamera({ zoom: m.getZoom(), longitude: p.lng, latitude: p.lat, bearing: m.getBearing() });
        updateFrameMetric(m);
        reportState();
        // Final label layout must run after the camera stops, otherwise the last
        // throttled pass can leave labels overlapping.
        lastLayoutAt.current = 0;
        syncOverlay();
      });
      m.on('pitch', () => setPitch(m.getPitch()));
      m.on('render', syncOverlay);
      m.on('resize', syncOverlay);
      if (insetContainer.current) {
        const insetMap = new maplibregl.Map({ container: insetContainer.current, style: style(), interactive: false, attributionControl: false, renderWorldCopies: false });
        inset.current = insetMap;
        insetMap.on('load', () => insetMap.fitBounds([[105, 3], [125, 24]], { padding: 4, duration: 0 }));
        insetMap.on('error', () => undefined);
      }
      const resize = new ResizeObserver(() => {
        m.resize();
        inset.current?.resize();
        syncOverlay();
        // Keep the national composition calibrated when the viewport changes.
        if (mode3d.current && m.getZoom() < 4.9) frameNational(m, 0);
      });
      resize.observe(container.current);
      return () => {
        disposed = true;
        resize.disconnect();
        markers.current.forEach(mk => mk.el.remove()); markers.current = [];
        provinceLabels.current.forEach(l => l.el.remove()); provinceLabels.current = [];
        scene.current?.dispose(); scene.current = null;
        store.current?.dispose(); store.current = null;
        inset.current?.remove(); inset.current = null;
        m.remove(); map.current = null;
        void disposed;
      };
    } catch {
      setError('浏览器暂不支持 WebGL，请使用支持硬件加速的浏览器。');
      return;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 3D switch: enable the engine lazily, restore the style layers when going back to 2D.
  useEffect(() => {
    const m = map.current;
    if (!m || !ready) return;
    if (terrain3d && !scene.current) {
      void ensureTerrain();
      m.easeTo({ pitch: 38, bearing: 0, duration: 600 });
      frameNational(m, 700, true);
    } else {
      applyLayerMode();
      if (!terrain3d) m.easeTo({ pitch: 0, bearing: 0, duration: 550 });
      else m.easeTo({ pitch: 38, duration: 500 });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [terrain3d, ready]);

  useEffect(() => {
    scene.current?.setExaggeration(exaggeration);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [exaggeration]);

  useEffect(() => {
    scene.current?.setContours(contours);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contours]);

  useEffect(() => {
    applyLayerMode();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nationalBorder, provinceBorder, rivers, lines, effects, ready]);

  useEffect(() => {
    const m = map.current;
    if (!ready || !m) return;
    markers.current.forEach(mk => mk.el.remove()); markers.current = [];
    const host = overlay.current;
    if (!host) return;
    data.locations.filter(p => p.longitude !== null && p.latitude !== null).forEach(p => {
      const button = document.createElement('button');
      const selected = selectedIds.includes(p.id);
      button.className = `historical-marker ${p.type === 'current_collection' ? 'collection' : p.type === 'historical_activity' || p.type === 'ancestral_origin' ? 'activity' : 'original'} ${selected ? 'selected' : ''} ${effects ? 'with-effects' : ''}`;
      button.setAttribute('aria-label', `地图地点：${p.name}`);
      button.setAttribute('data-place-id', p.id);
      const glyph = document.createElement('span');
      glyph.className = 'marker-symbol';
      glyph.textContent = p.type === 'current_collection' ? '藏' : p.type === 'ancestral_origin' ? '籍' : p.type === 'historical_activity' ? '地' : '碑';
      button.append(glyph);
      let labelEl: HTMLElement | null = null;
      if (labels) { const name = document.createElement('span'); name.className = 'marker-label'; name.textContent = p.name; button.append(name); labelEl = name; }
      button.addEventListener('click', e => { e.stopPropagation(); select.current(p.id); });
      button.addEventListener('dblclick', e => { e.preventDefault(); e.stopPropagation(); select.current(p.id, 11); });
      host.appendChild(button);
      // Priority drives the label layout: selected first, then stele markers,
      // then secondary historical activity.
      const priority = selected ? 0 : (p.type === 'current_collection' || p.type === 'original_site') ? 1 : 2;
      const labelW = labelEl ? (labelEl.offsetWidth || 90) : 0;
      const labelH = labelEl ? (labelEl.offsetHeight || 18) : 0;
      markers.current.push({ id: p.id, el: button, lng: p.longitude!, lat: p.latitude!, priority, labelEl, labelW, labelH });
    });
    syncOverlay();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, data, labels]);

  useEffect(() => {
    const m = map.current;
    if (!ready || !m) return;
    // Every link is labelled as an association. It is never a transport itinerary.
    const features: GeoJSON.Feature[] = [];
    if (lines) {
      const stone = data.locations.filter(l => ['original_site', 'current_collection'].includes(l.type) && l.longitude !== null);
      if (stone.length === 2) features.push({ type: 'Feature', properties: { kind: 'stone_transfer', meaning: '原石两端关联；路径未考' }, geometry: { type: 'LineString', coordinates: stone.map(l => [l.longitude!, l.latitude!]) } });
      const activity = data.locations.filter(l => ['ancestral_origin', 'historical_activity'].includes(l.type) && l.longitude !== null);
      const origin = data.locations.find(l => l.type === 'original_site' && l.longitude !== null);
      if (origin) activity.forEach(l => features.push({ type: 'Feature', properties: { kind: 'person_activity', meaning: '人物与立碑地关联；不是旅行线路' }, geometry: { type: 'LineString', coordinates: [[origin.longitude!, origin.latitude!], [l.longitude!, l.latitude!]] } }));
    }
    const relations: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features };
    (m.getSource('relations') as maplibregl.GeoJSONSource)?.setData(relations);
    for (const layer of ['region-fill', 'region-outline']) m.setFilter(layer, ['in', ['get', 'locationId'], ['literal', data.locations.map(l => l.id)]]);
    scene.current?.setVectors({ ...vectorsRef.current, relations });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, data, lines]);

  useEffect(() => {
    markers.current.forEach(marker => {
      const element = marker.el;
      element.classList.toggle('selected', selectedIds.includes(element.dataset.placeId!));
      element.classList.toggle('with-effects', effects);
    });
  }, [ready, data, selectedIds, effects, labels, lines]);

  useEffect(() => {
    provinceLabels.current.forEach(label => { label.el.style.display = labels ? 'block' : 'none'; });
    syncOverlay();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [labels]);

  useEffect(() => {
    const m = map.current;
    if (!ready || !m) return;
    if (command.kind === 'national') { frameNational(m, 650); return; }
    const p = resolveMapPlace(data, command.placeId);
    if (command.kind === 'place' && p) { m.flyTo({ center: [p.longitude!, p.latitude!], zoom: command.zoom ?? (p.precision === 'regional' ? 5.3 : 6), duration: 800 }); return; }
    const points = command.locationIds?.length
      ? command.locationIds.map(id => resolveMapPlace(data, id)).filter((l): l is HistoricalLocation => !!l && l.longitude !== null && l.latitude !== null)
      : data.locations.filter(l => l.longitude !== null && l.latitude !== null);
    if (!points.length) { frameNational(m, 650); return; }
    if (points.length === 1) { m.flyTo({ center: [points[0].longitude!, points[0].latitude!], zoom: 5.3, duration: 750 }); return; }
    const b = new maplibregl.LngLatBounds(); points.forEach(l => b.extend([l.longitude!, l.latitude!]));
    m.fitBounds(b, { padding: { top: 75, bottom: 75, left: 95, right: 95 }, maxZoom: 8.2, duration: 750 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, command, data]);

  const viewAction = (action: 'top' | 'national' | 'spin-left' | 'spin-right' | 'tilt') => {
    const m = map.current;
    if (!m) return;
    if (action === 'top') m.easeTo({ pitch: 0, bearing: 0, duration: 650 });
    if (action === 'tilt') m.easeTo({ pitch: 42, duration: 650 });
    if (action === 'national') { m.easeTo({ bearing: 0, duration: 500 }); frameNational(m, 700); }
    if (action === 'spin-left') m.easeTo({ bearing: m.getBearing() - 30, duration: 450 });
    if (action === 'spin-right') m.easeTo({ bearing: m.getBearing() + 30, duration: 450 });
  };

  const modeLabel = terrain3d ? '二维地图' : '三维地形';

  return <div className="historical-map" data-testid="historical-map" data-ready={ready} data-zoom={camera.zoom} data-center={`${camera.longitude},${camera.latitude}`} data-terrain={terrain3d ? '3d' : '2d'} data-terrain-ready={terrain.ready} data-pitch={pitch.toFixed(1)} data-bearing={camera.bearing.toFixed(1)} data-terrain-mode={modeLabel} data-frame-width={frame.width} data-frame-height={frame.height}>
    <div className="map-canvas" ref={container}/>
    <div className="marker-overlay" ref={overlay} aria-live="off"/>
    <div className="map-compass" aria-hidden="true"><span>北</span><Compass size={44} strokeWidth={.7}/></div>
    <div className="map-view-controls" role="group" aria-label="地图视角控制">
      <button onClick={() => viewAction('top')} title="一键俯视（正射）"><Eye size={14}/><span>俯视</span></button>
      <button onClick={() => viewAction('tilt')} title="倾斜到三维视角"><Mountain size={14}/><span>倾斜</span></button>
      <button onClick={() => viewAction('spin-left')} title="逆时针旋转视角"><RotateCw size={14} style={{ transform: 'scaleX(-1)' }}/></button>
      <button onClick={() => viewAction('spin-right')} title="顺时针旋转视角"><RotateCw size={14}/></button>
      <button onClick={() => viewAction('national')} title="恢复中国全国构图"><Layers3 size={14}/><span>全国</span></button>
    </div>
    <div className="map-coordinate">{camera.longitude.toFixed(2)}° E · {camera.latitude.toFixed(2)}° N <span>WGS84 地望索引</span></div>
    {camera.zoom >= 4 && <div className="region-legend">青绿虚线面：现代定位县区</div>}
    <div className="south-sea-inset"><div ref={insetContainer}/><span>南海诸岛 · 同源地理附图</span></div>
    <div className="map-key"><span><i className="red"/>立碑地望</span><span><i className="gold"/>原石保存</span><span><i className="green"/>人物关联地</span></div>
    {data.locations.length === 0 && <div className="map-empty"><MapPin size={25}/><strong>地望待考</strong><span>本样本没有已核实地理点，保留全国底图。</span></div>}
    {error && <div role="alert" className="map-error">{error}</div>}
    {terrain.error && <div role="alert" className="map-error map-error-terrain">{terrain.error}</div>}
  </div>;
}
