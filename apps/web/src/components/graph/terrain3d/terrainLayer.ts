import * as THREE from 'three';
import type * as maplibregl from 'maplibre-gl';
import { DemStore } from './dem';
import { buildCovers, buildTerrainPatch, disposeBuild, sampleBuildSurface, type TerrainBuild, type TerrainSpec } from './terrainMesh';
import { createTerrainMaterial, createTerrainUniforms, type TerrainUniforms } from './terrainMaterial';
import { DrapedLineLayer, geometriesToPolylines, type DrapeGroupSpec } from './drapedLines';
import { EARTH_CIRCUMFERENCE, mercatorToClip, mercatorX, mercatorY } from './projection';

/** Fixed scene origin (meridian of the national frame) keeps float32 positions accurate. */
const SCENE_ORIGIN = new THREE.Vector2(mercatorX(105), mercatorY(34));

export const NATIONAL_MERCATOR = {
  x0: mercatorX(58),
  y0: mercatorY(62),
  x1: mercatorX(152),
  y1: mercatorY(-2),
};

export interface TerrainLevel {
  id: string;
  label: string;
  minZoom: number;
  /** top zoom this level is expected to serve; drives vector decimation */
  maxZoom: number;
  /** longitude half-window in degrees; null means the fixed national frame */
  halfLon: number | null;
  demZoom: number;
  budget: number;
}

export const TERRAIN_LEVELS: TerrainLevel[] = [
  { id: 'national', label: '全国地貌', minZoom: 0, maxZoom: 5.4, halfLon: null, demZoom: 5, budget: 620000 },
  { id: 'regional', label: '区域地貌', minZoom: 5.4, maxZoom: 7.6, halfLon: 11, demZoom: 6, budget: 460000 },
  { id: 'local', label: '局地地貌', minZoom: 7.6, maxZoom: 10, halfLon: 4.2, demZoom: 8, budget: 360000 },
  { id: 'close', label: '近景地貌', minZoom: 10, maxZoom: 13, halfLon: 1.5, demZoom: 10, budget: 300000 },
];

export interface TerrainStats {
  ready: boolean;
  level: string;
  levelLabel: string;
  buildMs: number;
  vertices: number;
  triangles: number;
  demZoom: number;
  tiles: number;
  maxZoom: number;
  exaggeration: number;
  verticalScale: number;
  fps: number;
  drapedVertices: number;
  vectorGroups: string[];
  frames: number;
  dpr: number;
}

export interface VectorInput {
  provinces?: GeoJSON.FeatureCollection;
  /** province-to-province borders only (shared edges deduplicated) */
  provinceInternal?: GeoJSON.FeatureCollection;
  /** dissolved national boundary: land border + coastline + island rings */
  national?: GeoJSON.FeatureCollection;
  /** maritime line features carried by the province file */
  maritime?: GeoJSON.FeatureCollection;
  rivers?: GeoJSON.FeatureCollection;
  regions?: GeoJSON.FeatureCollection;
  relations?: GeoJSON.FeatureCollection;
}

export interface VectorVisibility {
  national: boolean;
  provinces: boolean;
  rivers: boolean;
  regions: boolean;
  relations: boolean;
}

type StatsListener = (stats: TerrainStats) => void;

/** Exaggeration law: full 1:1 at street zoom, gentle compensation at national scale. */
export function autoExaggeration(zoom: number): number {
  const raw = 6.0 * Math.pow(2, 5.2 - zoom);
  return Math.max(1, Math.min(34, raw));
}

function clampNumber(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

export class Terrain3DScene {
  readonly store: DemStore;
  readonly layer: maplibregl.CustomLayerInterface;
  readonly scene = new THREE.Scene();
  readonly camera = new THREE.PerspectiveCamera();
  readonly uniforms: TerrainUniforms = createTerrainUniforms();

  private map: maplibregl.Map;
  private renderer: THREE.WebGLRenderer | null = null;
  private material = createTerrainMaterial(this.uniforms);
  private nationalMesh: THREE.Mesh | null = null;
  private nationalBuild: TerrainBuild | null = null;
  private detailMesh: THREE.Mesh | null = null;
  private detailBuild: TerrainBuild | null = null;
  private drape = new DrapedLineLayer();
  private mvp = new THREE.Matrix4();
  private worldSize = 512;
  private visible = true;
  private exaggerationOverride: number | null = null;
  private level: TerrainLevel = TERRAIN_LEVELS[0];
  private vectors: VectorInput = {};
  private vectorVisibility: VectorVisibility = { national: true, provinces: true, rivers: true, regions: false, relations: false };
  private demZoom = 5;
  private frameCount = 0;
  private lastStats: TerrainStats | null = null;
  private statsListeners = new Set<StatsListener>();
  private buildToken = 0;
  private building = false;
  private dirty = true;
  private disposed = false;
  private failed = false;
  private errorListeners = new Set<(message: string) => void>();
  private frameTimes: number[] = [];
  private frameStamps: number[] = [];
  private lastFps = 0;
  private lastFrameAt = 0;
  private canvasSize = { width: 0, height: 0 };
  private lastDetailCenter = { x: 0, y: 0 };
  private rebuildTimer: number | null = null;
  private nationalAt: number | null = null;
  private vectorVersion = 0;
  private drapeKey = '';
  private heightScale = 1 / EARTH_CIRCUMFERENCE;
  private screenSize = new THREE.Vector2(1, 1);
  private flat = false;

  constructor(map: maplibregl.Map, store: DemStore) {
    this.map = map;
    this.store = store;
    this.scene.name = 'terrain3d';
    this.camera.fov = 36.87;
    this.camera.near = 1;
    this.camera.far = 1e9;

    const nationalMesh = new THREE.Mesh(new THREE.BufferGeometry(), this.material);
    nationalMesh.frustumCulled = false;
    nationalMesh.name = 'national-terrain';
    this.nationalMesh = nationalMesh;
    this.scene.add(nationalMesh);
    this.scene.add(this.drape.group);

    this.layer = {
      id: 'terrain-3d',
      type: 'custom',
      renderingMode: '3d',
      onAdd: (mapInstance: maplibregl.Map, gl: WebGL2RenderingContext) => {
        this.renderer = new THREE.WebGLRenderer({
          canvas: mapInstance.getCanvas(),
          context: gl,
          antialias: true,
          alpha: true,
        });
        this.renderer.autoClear = false;
        this.renderer.autoClearColor = false;
        this.renderer.autoClearDepth = false;
        this.renderer.setPixelRatio(1);
        this.lastDetailCenter = { x: -1, y: -1 };
        this.scheduleBuild(0);
      },
      render: (_gl: WebGL2RenderingContext, options: maplibregl.CustomRenderMethodInput) => {
        this.renderFrame(options);
      },
      onRemove: () => {
        this.dispose();
      },
    };
  }

  onStats(listener: StatsListener) {
    this.statsListeners.add(listener);
    if (this.lastStats) listener(this.lastStats);
    return () => this.statsListeners.delete(listener);
  }

  /** Notified when a WebGL failure forces the scene to stop drawing. */
  onError(listener: (message: string) => void) {
    this.errorListeners.add(listener);
    return () => this.errorListeners.delete(listener);
  }

  setVisible(visible: boolean) {
    this.visible = visible;
    if (visible) {
      this.dirty = true;
      this.map.triggerRepaint();
    }
  }

  setExaggeration(value: number | null) {
    this.exaggerationOverride = value;
    this.map.triggerRepaint();
    this.emitStats();
  }

  /** Cartographic contour lines are derived from the DEM, never from noise. */
  setContours(enabled: boolean) {
    this.uniforms.u_contourStrength.value = enabled ? 0.07 : 0;
    this.map.triggerRepaint();
  }

  /**
   * Flat mode keeps the DEM shading but removes the vertical displacement, which
   * is exactly a classic hypsometric hillshade plate — the "2D map" of the toggle.
   */
  setFlat(flat: boolean) {
    this.flat = flat;
    this.uniforms.u_heightFactor.value = flat ? 0 : 1;
    this.map.triggerRepaint();
  }

  get isFlat() {
    return this.flat;
  }

  get exaggeration(): number {
    return this.exaggerationOverride ?? autoExaggeration(this.map.getZoom());
  }

  setVectors(input: VectorInput) {
    this.vectors = input;
    this.vectorVersion++;
    this.dirty = true;
    this.drapeKey = '';
    if (this.nationalBuild) this.buildDrapes(true);
    this.scheduleBuild(30);
  }

  setVectorVisibility(visibility: Partial<VectorVisibility>) {
    this.vectorVisibility = { ...this.vectorVisibility, ...visibility };
    this.applyVectorVisibility();
    this.map.triggerRepaint();
  }

  /** DEM height in metres at a geographic position (data value, not the mesh). */
  heightAt(lng: number, lat: number): number {
    return Math.max(0, this.store.sample(mercatorX(lng), mercatorY(lat), this.demZoom));
  }

  /**
   * Height of the surface actually drawn at a mercator position. Falls back to
   * the national patch, then to a raw DEM sample outside every patch.
   */
  surfaceHeight(x: number, y: number): number {
    const detail = this.detailBuild;
    if (detail && buildCovers(detail, x, y)) return Math.max(0, sampleBuildSurface(detail, x, y));
    const national = this.nationalBuild;
    if (national && buildCovers(national, x, y)) return Math.max(0, sampleBuildSurface(national, x, y));
    return Math.max(0, this.store.sample(x, y, this.demZoom));
  }

  /** Project a geographic position onto the current viewport, honouring terrain height. */
  screenPosition(lng: number, lat: number, width: number, height: number, exaggerated = true) {
    const x = mercatorX(lng);
    const y = mercatorY(lat);
    const metres = this.surfaceHeight(x, y);
    const z = exaggerated && !this.flat ? (metres * this.exaggeration) / EARTH_CIRCUMFERENCE : 0;
    const vector = new THREE.Vector4(x, y, z, 1).applyMatrix4(this.mvp);
    const w = vector.w;
    if (!Number.isFinite(w) || w <= 1e-6) return { x: 0, y: 0, visible: false, height: metres };
    const ndcX = vector.x / w;
    const ndcY = vector.y / w;
    return {
      x: (ndcX * 0.5 + 0.5) * width,
      y: (1 - (ndcY * 0.5 + 0.5)) * height,
      visible: ndcX > -1.2 && ndcX < 1.2 && ndcY > -1.2 && ndcY < 1.2 && vector.z / w > -1 && vector.z / w < 1,
      height: metres,
    };
  }

  getMatrix(): THREE.Matrix4 {
    return this.mvp;
  }

  getStats(): TerrainStats | null {
    return this.lastStats;
  }

  /** ids of the draped vector groups currently built (for the HUD / tests) */
  get vectorGroups(): string[] {
    return this.drape.groupIds;
  }

  private applyVectorVisibility() {
    for (const id of ['national', 'national-halo', 'national-casing', 'maritime']) {
      this.drape.setGroupVisible(id, this.vectorVisibility.national);
    }
    for (const id of ['province']) {
      this.drape.setGroupVisible(id, this.vectorVisibility.provinces);
    }
    this.drape.setGroupVisible('rivers', this.vectorVisibility.rivers);
    this.drape.setGroupVisible('regions', this.vectorVisibility.regions);
    this.drape.setGroupVisible('relations', this.vectorVisibility.relations);
  }

  private scheduleBuild(delay: number) {
    if (this.rebuildTimer !== null) window.clearTimeout(this.rebuildTimer);
    this.rebuildTimer = window.setTimeout(() => {
      this.rebuildTimer = null;
      void this.rebuild();
    }, delay);
  }

  private levelForZoom(zoom: number): TerrainLevel {
    let chosen = TERRAIN_LEVELS[0];
    for (const level of TERRAIN_LEVELS) if (zoom >= level.minZoom) chosen = level;
    return chosen;
  }

  private specFor(level: TerrainLevel): TerrainSpec {
    let x0: number;
    let y0: number;
    let x1: number;
    let y1: number;
    let fadeEdge = false;
    if (level.halfLon === null) {
      ({ x0, y0, x1, y1 } = NATIONAL_MERCATOR);
      fadeEdge = true;
    } else {
      const center = this.map.getCenter();
      const cx = mercatorX(center.lng);
      const cy = mercatorY(center.lat);
      const halfX = level.halfLon / 360;
      const height = this.map.getCanvas().clientHeight || 720;
      const width = this.map.getCanvas().clientWidth || 960;
      const halfY = (halfX * height) / Math.max(width, 1) / Math.cos((center.lat * Math.PI) / 180);
      x0 = cx - halfX;
      x1 = cx + halfX;
      y0 = cy - halfY;
      y1 = cy + halfY;
    }
    const spanX = x1 - x0;
    const spanY = y1 - y0;
    const aspect = Math.max(0.2, spanX / spanY);
    let ny = Math.round(Math.sqrt(level.budget / aspect));
    let nx = Math.round(ny * aspect);
    nx = Math.max(64, Math.min(1800, nx));
    ny = Math.max(64, Math.min(1800, ny));
    return {
      x0, y0, x1, y1, nx, ny,
      demZoom: level.demZoom,
      originX: SCENE_ORIGIN.x,
      originY: SCENE_ORIGIN.y,
      label: level.label,
      fadeEdge,
    };
  }

  private async rebuild() {
    if (this.disposed || this.building) return;
    const token = ++this.buildToken;
    const zoom = this.map.getZoom();
    const level = this.levelForZoom(zoom);
    const spec = this.specFor(level);
    this.building = true;
    try {
      await this.store.ensureCoverage(spec.x0, spec.y0, spec.x1, spec.y1, spec.demZoom);
      if (token !== this.buildToken || this.disposed) return;
      const effective = this.store.availableZoom(spec.x0, spec.y0, spec.x1, spec.y1, spec.demZoom);
      spec.demZoom = Math.max(0, effective);
      this.demZoom = spec.demZoom;

      if (level.halfLon === null) {
        const build = buildTerrainPatch(this.store, spec);
        this.replaceNational(build);
      } else {
        const build = buildTerrainPatch(this.store, spec);
        this.replaceDetail(build);
        this.lastDetailCenter = { x: (spec.x0 + spec.x1) / 2, y: (spec.y0 + spec.y1) / 2 };
      }
      this.level = level;
      this.buildDrapes();
      this.dirty = false;
      this.map.triggerRepaint();
      this.emitStats();
    } catch (error) {
      console.warn('[terrain3d] build failed', error);
    } finally {
      this.building = false;
      if (this.levelForZoom(this.map.getZoom()) !== this.level) this.scheduleBuild(80);
    }
  }

  private replaceNational(build: TerrainBuild) {
    disposeBuild(this.nationalBuild);
    this.nationalBuild = build;
    if (this.nationalMesh) {
      this.nationalMesh.geometry = build.geometry;
      this.nationalMesh.visible = true;
    }
    this.nationalAt = performance.now();
  }

  private replaceDetail(build: TerrainBuild) {
    disposeBuild(this.detailBuild);
    this.detailBuild = build;
    if (!this.detailMesh) {
      const mesh = new THREE.Mesh(build.geometry, createTerrainMaterial(this.uniforms, true));
      mesh.frustumCulled = false;
      mesh.name = 'detail-terrain';
      mesh.renderOrder = 1;
      this.detailMesh = mesh;
      this.scene.add(mesh);
    } else {
      this.detailMesh.geometry = build.geometry;
    }
    // The detail patch is drawn with a depth bias so it wins over the coarse plate.
    const material = this.detailMesh.material as THREE.ShaderMaterial;
    material.polygonOffset = true;
    // The detail patch covers the viewport once it exists, so the coarse plate is
    // hidden instead of being depth-biased: a polygon offset large enough to beat
    // z-fighting also pushed the terrain in front of the draped borders.
    material.polygonOffsetFactor = 0;
    material.polygonOffsetUnits = 0;
    material.needsUpdate = true;
    this.detailMesh.visible = true;
  }

  private buildDrapes(force = false) {
    const key = `${this.demZoom}|${this.vectorVersion}`;
    if (!force && key === this.drapeKey) return;
    this.drapeKey = key;
    const groups: DrapeGroupSpec[] = [];
    const collect = (collection: GeoJSON.FeatureCollection | undefined, id: string, style: Omit<DrapeGroupSpec, 'id' | 'lines'>) => {
      if (!collection) return;
      const lines: number[][][] = [];
      for (const feature of collection.features) {
        if (!feature.geometry) continue;
        lines.push(...geometriesToPolylines(feature.geometry));
      }
      if (!lines.length) return;
      groups.push({ id, lines, ...style });
    };
    // `lift` is a relative depth rank, not metres: the per-frame lift below is
    // computed so every line stays ~0.8 screen px above the rendered surface at
    // any zoom or exaggeration.
    // Province borders carry no dark casing: with dense sub-pixel geometry the
    // many overlapping translucent quads accumulate, so even a 0.22-alpha casing
    // became an opaque band that hid the thin bronze core.
    collect(this.vectors.provinceInternal, 'province', { color: '#d4b177', widthPx: 1.3, opacity: 0.85, lift: 1.0 });
    collect(this.vectors.maritime, 'maritime', { color: '#e8c07a', widthPx: 1.15, opacity: 0.8, lift: 1.2 });
    // The national outline is drawn three times: a dark casing for contrast on
    // bright high ground, a soft gold halo, then the crisp core. No geometry is
    // invented to separate China from neighbouring territory.
    collect(this.vectors.national, 'national-casing', { color: '#170f04', widthPx: 4.6, opacity: 0.55, lift: 1.35 });
    collect(this.vectors.national, 'national-halo', { color: '#f3b95c', widthPx: 8.5, opacity: 0.2, lift: 1.5 });
    collect(this.vectors.national, 'national', { color: '#ffdc9a', widthPx: 2.7, opacity: 1, lift: 1.65 });
    collect(this.vectors.rivers, 'rivers', { color: '#8ef0dd', widthPx: 1.15, opacity: 0.85, lift: 0.7 });
    collect(this.vectors.regions, 'regions', { color: '#74ae96', widthPx: 1.0, opacity: 0.5, lift: 1.1, dash: [26000, 0.55] });
    collect(this.vectors.relations, 'relations', { color: '#dfb85e', widthPx: 1.15, opacity: 0.7, lift: 1.4, dash: [40000, 0.5] });
    // ~1.6 px at the top zoom of this LOD: enough to keep the ribbon continuous
    // without visibly cutting corners of the administrative boundary.
    const degreesPerPixel = 360 / (512 * Math.pow(2, this.level.maxZoom));
    const minSpacing = degreesPerPixel * 1.6;
    this.drape.build(groups, (x, y) => this.surfaceHeight(x, y), SCENE_ORIGIN.x, SCENE_ORIGIN.y, minSpacing);
    this.applyVectorVisibility();
  }

  private updateMatrices(options: maplibregl.CustomRenderMethodInput) {
    const canvas = this.map.getCanvas();
    const zoom = this.map.getZoom();
    this.worldSize = 512 * Math.pow(2, zoom);
    mercatorToClip(options.modelViewProjectionMatrix, this.worldSize, this.mvp);
    this.camera.projectionMatrix.fromArray(options.projectionMatrix as unknown as number[]);
    const center = this.map.getCenter();
    const camDist = (0.5 * canvas.clientHeight) / Math.tan(options.fov / 2);
    const camMercator = camDist / this.worldSize;
    this.uniforms.u_camera.value.set(mercatorX(center.lng), mercatorY(center.lat), camMercator);
    this.uniforms.u_fogNear.value = camMercator * 1.9;
    this.uniforms.u_fogFar.value = camMercator * 5.2;
    this.uniforms.u_mvp.value.copy(this.mvp);
    this.uniforms.u_origin.value.copy(SCENE_ORIGIN);
    this.heightScale = this.exaggeration / EARTH_CIRCUMFERENCE;
    this.uniforms.u_heightScale.value = this.heightScale;
    this.screenSize.set(canvas.clientWidth || 1, canvas.clientHeight || 1);
    // Line widths are authored in CSS pixels; the ribbon shader expands in CSS px
    // too, so device pixel ratio does not change the apparent weight. The gentle
    // ramp keeps province lines at 1.25-1.67 px from national to local zoom.
    const widthScale = clampNumber(1 + (zoom - 4.6) * 0.085, 1, 1.34);
    // Depth separation is solved in screen space: ~0.8 px converted to metres at
    // the current zoom, then divided by the exaggeration because the shader
    // multiplies it back. This keeps the border glued to the surface without
    // z-fighting at any zoom level.
    const metresPerPixel = (EARTH_CIRCUMFERENCE * Math.cos((center.lat * Math.PI) / 180)) / this.worldSize;
    const liftMetres = this.flat ? 0 : (1.2 * metresPerPixel) / Math.max(this.exaggeration, 0.35);
    this.drape.update(this.mvp, SCENE_ORIGIN, this.flat ? 0 : this.heightScale, this.screenSize, widthScale, liftMetres);
  }

  private renderFrame(options: maplibregl.CustomRenderMethodInput) {
    if (!this.visible || this.disposed || !this.renderer || this.failed) return;
    try {
      const canvas = this.map.getCanvas();
      if (!this.nationalBuild && !this.building) this.scheduleBuild(0);

      if (canvas.width !== this.canvasSize.width || canvas.height !== this.canvasSize.height) {
        this.canvasSize = { width: canvas.width, height: canvas.height };
        this.renderer.setSize(canvas.width, canvas.height, false);
      }

      this.updateMatrices(options);
      this.frameCount++;

      const now = performance.now();
      if (this.lastFrameAt) {
        this.frameTimes.push(now - this.lastFrameAt);
        if (this.frameTimes.length > 90) this.frameTimes.shift();
      }
      this.lastFrameAt = now;
      this.frameStamps.push(now);
      while (this.frameStamps.length && now - this.frameStamps[0] > 1000) this.frameStamps.shift();

      // The coarse plate is off-screen once the detail patch owns the viewport.
      // Once a detail patch exists it covers the viewport, so the coarse plate can be
    // hidden entirely — that removes the overlapping-surface z-fight which used to
    // require a depth bias big enough to occlude the draped borders.
    if (this.nationalMesh) this.nationalMesh.visible = !this.detailBuild || this.map.getZoom() < 5.5;

      this.renderer.render(this.scene, this.camera);
      this.renderer.resetState();

      if (this.frameCount % 30 === 0) this.emitStats();
      this.maybeRebuildForView();
    } catch (error) {
      // A driver/context failure must not break MapLibre's render loop or the page.
      this.failed = true;
      console.warn('[terrain3d] render failed; disabling the 3D layer', error);
      this.errorListeners.forEach((listener) => listener(error instanceof Error ? error.message : String(error)));
    }
  }

  private maybeRebuildForView() {
    if (this.building || this.rebuildTimer !== null) return;
    const zoom = this.map.getZoom();
    const level = this.levelForZoom(zoom);
    if (level !== this.level) {
      this.scheduleBuild(160);
      return;
    }
    if (level.halfLon === null) return;
    const center = this.map.getCenter();
    const cx = mercatorX(center.lng);
    const cy = mercatorY(center.lat);
    const halfX = level.halfLon / 360;
    const dx = Math.abs(cx - this.lastDetailCenter.x) / halfX;
    const dy = Math.abs(cy - this.lastDetailCenter.y) / halfX;
    if (!this.detailBuild || dx > 0.55 || dy > 0.55) this.scheduleBuild(220);
  }

  private emitStats() {
    const now = performance.now();
    while (this.frameStamps.length && now - this.frameStamps[0] > 1000) this.frameStamps.shift();
    const fps = this.frameStamps.length;
    if (fps >= 8) this.lastFps = fps;
    const build = this.detailBuild ?? this.nationalBuild;
    const stats: TerrainStats = {
      ready: Boolean(this.nationalBuild),
      level: this.level.id,
      levelLabel: this.level.label,
      buildMs: build?.buildMs ?? 0,
      vertices: (this.nationalBuild?.vertices ?? 0) + (this.detailBuild?.vertices ?? 0),
      triangles: (this.nationalBuild?.triangles ?? 0) + (this.detailBuild?.triangles ?? 0),
      demZoom: this.demZoom,
      tiles: this.store.tiles.size,
      maxZoom: this.store.maxZoom,
      exaggeration: Math.round(this.exaggeration * 10) / 10,
      verticalScale: Math.round((this.exaggeration * 1000) / 1000),
      fps: this.lastFps,
      drapedVertices: this.drape.vertexCount,
      vectorGroups: this.drape.groupIds,
      frames: this.frameCount,
      dpr: window.devicePixelRatio || 1,
    };
    this.lastStats = stats;
    this.statsListeners.forEach((listener) => listener(stats));
  }

  /** Called by the map after a move so vectors stay glued to the surface. */
  handleMapMove() {
    this.map.triggerRepaint();
  }

  dispose() {
    if (this.disposed) return;
    this.disposed = true;
    if (this.rebuildTimer !== null) window.clearTimeout(this.rebuildTimer);
    this.rebuildTimer = null;
    disposeBuild(this.nationalBuild);
    disposeBuild(this.detailBuild);
    this.nationalBuild = null;
    this.detailBuild = null;
    this.drape.dispose();
    this.material.dispose();
    if (this.detailMesh) {
      (this.detailMesh.material as THREE.Material).dispose();
      this.detailMesh = null;
    }
    this.renderer?.dispose();
    this.renderer = null;
    this.scene.clear();
    this.statsListeners.clear();
  }
}
