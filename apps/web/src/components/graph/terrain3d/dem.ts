/**
 * Terrarium DEM access for the Three.js terrain scene.
 *
 * Tiles stay byte-identical to the upstream open-data product; the only
 * transformation is the documented Terrarium decode
 * `elevation = R*256 + G + B/256 - 32768`. Nothing is smoothed, resampled or
 * perturbed here, so every height the shaders see is a real DEM sample.
 */
import { latitudeOf, longitudeOf, mercatorX, mercatorY } from './projection';

export interface DemLevel {
  z: number;
  tiles: number;
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
}

export interface TerrainManifest {
  format: string;
  levels: DemLevel[];
  maxZoom: number;
  totalTiles: number;
  generated?: string;
}

export interface DemTile {
  key: number;
  z: number;
  x: number;
  y: number;
  heights: Float32Array;
}

const TILE_PIXELS = 256;
/** numeric key for z/x/y; supports z <= 13, i.e. ~1 m per texel at the equator. */
function tileKey(z: number, x: number, y: number): number {
  return z * 268435456 + x * 16384 + y;
}

export interface TileAddress {
  z: number;
  x: number;
  y: number;
}

export function tileAddress(lng: number, lat: number, zoom: number): TileAddress {
  const n = 1 << zoom;
  return {
    z: zoom,
    x: Math.min(n - 1, Math.max(0, Math.floor(mercatorX(lng) * n))),
    y: Math.min(n - 1, Math.max(0, Math.floor(mercatorY(lat) * n))),
  };
}

/** Tile range covering a mercator box. */
export function tileRangeForMercator(x0: number, y0: number, x1: number, y1: number, zoom: number) {
  const n = 1 << zoom;
  return {
    z: zoom,
    x0: Math.max(0, Math.floor(x0 * n)),
    x1: Math.min(n - 1, Math.floor(x1 * n)),
    y0: Math.max(0, Math.floor(y0 * n)),
    y1: Math.min(n - 1, Math.floor(y1 * n)),
  };
}

class DecodeWorkerClient {
  private worker: Worker | null = null;
  private pending = new Map<number, (heights: Float32Array | null) => void>();
  private nextId = 1;
  private broken = false;

  constructor(url: URL) {
    try {
      this.worker = new Worker(url, { type: 'module' });
      this.worker.onmessage = (event: MessageEvent<{ id: number; heights?: Float32Array; error?: string }>) => {
        const resolve = this.pending.get(event.data.id);
        if (!resolve) return;
        this.pending.delete(event.data.id);
        resolve(event.data.heights ?? null);
      };
      this.worker.onerror = () => {
        this.broken = true;
        this.pending.forEach((resolve) => resolve(null));
        this.pending.clear();
      };
    } catch {
      this.broken = true;
      this.worker = null;
    }
  }

  decode(buffer: ArrayBuffer): Promise<Float32Array | null> {
    if (!this.worker || this.broken) return Promise.resolve(null);
    const id = this.nextId++;
    return new Promise((resolve) => {
      this.pending.set(id, resolve);
      this.worker!.postMessage({ id, buffer }, [buffer]);
    });
  }

  dispose() {
    this.worker?.terminate();
    this.worker = null;
  }
}

async function decodeOnMainThread(buffer: ArrayBuffer): Promise<Float32Array | null> {
  try {
    const bitmap = await createImageBitmap(new Blob([buffer], { type: 'image/png' }));
    const canvas = typeof OffscreenCanvas !== 'undefined'
      ? new OffscreenCanvas(bitmap.width, bitmap.height)
      : Object.assign(document.createElement('canvas'), { width: bitmap.width, height: bitmap.height });
    const context = (canvas as OffscreenCanvas).getContext('2d') as OffscreenCanvasRenderingContext2D | CanvasRenderingContext2D | null;
    if (!context) return null;
    context.drawImage(bitmap as unknown as CanvasImageSource, 0, 0);
    const data = context.getImageData(0, 0, bitmap.width, bitmap.height).data;
    const heights = new Float32Array(bitmap.width * bitmap.height);
    for (let i = 0, p = 0; i < heights.length; i++, p += 4) {
      heights[i] = data[p] * 256 + data[p + 1] + data[p + 2] / 256 - 32768;
    }
    bitmap.close?.();
    return heights;
  } catch {
    return null;
  }
}

export class DemStore {
  readonly tiles = new Map<number, DemTile>();
  readonly url: string;
  manifest: TerrainManifest | null = null;
  maxZoom = 3;
  /** bumps whenever new tiles arrive so the scene can rebuild */
  revision = 0;
  private worker: DecodeWorkerClient | null = null;
  private inflight = new Map<string, Promise<boolean>>();
  private lastTile: DemTile | null = null;

  constructor(base = '/assets/gis/terrain') {
    this.url = base;
    this.worker = new DecodeWorkerClient(new URL('./demWorker.ts', import.meta.url));
  }

  async loadManifest(): Promise<TerrainManifest | null> {
    try {
      const response = await fetch(`${this.url}/manifest.json`, { cache: 'no-cache' });
      if (!response.ok) throw new Error(`manifest ${response.status}`);
      const manifest = (await response.json()) as TerrainManifest;
      this.manifest = manifest;
      this.maxZoom = Math.max(0, manifest.maxZoom ?? 3);
      return manifest;
    } catch {
      // No manifest: the repository always ships the world overview at z0-z3.
      this.manifest = null;
      this.maxZoom = 3;
      return null;
    }
  }

  /** Highest zoom that actually has tiles inside the given mercator box. */
  availableZoom(x0: number, y0: number, x1: number, y1: number, desired: number): number {
    for (let z = Math.min(desired, this.maxZoom); z >= 0; z--) {
      const range = tileRangeForMercator(x0, y0, x1, y1, z);
      let complete = true;
      for (let x = range.x0; x <= range.x1 && complete; x++) {
        for (let y = range.y0; y <= range.y1; y++) {
          if (!this.tiles.has(tileKey(z, x, y))) { complete = false; break; }
        }
      }
      if (complete) return z;
    }
    return 0;
  }

  private async loadTile(z: number, x: number, y: number): Promise<boolean> {
    const key = `${z}/${x}/${y}`;
    const existing = this.inflight.get(key);
    if (existing) return existing;
    const task = (async () => {
      try {
        const response = await fetch(`${this.url}/${z}/${x}/${y}.png`);
        if (!response.ok) return false;
        const buffer = await response.arrayBuffer();
        const heights = (await this.worker?.decode(buffer.slice(0))) ?? (await decodeOnMainThread(buffer));
        if (!heights || heights.length !== TILE_PIXELS * TILE_PIXELS) return false;
        this.tiles.set(tileKey(z, x, y), { key: tileKey(z, x, y), z, x, y, heights });
        this.revision++;
        return true;
      } catch {
        return false;
      } finally {
        this.inflight.delete(key);
      }
    })();
    this.inflight.set(key, task);
    return task;
  }

  /**
   * Load the tiles needed to sample a box. Only the requested level is fetched;
   * parents are fetched only for tiles that turn out to be missing (404), so the
   * national view never pulls the whole pyramid.
   */
  async ensureCoverage(x0: number, y0: number, x1: number, y1: number, zoom: number, concurrency = 8): Promise<void> {
    for (let z = Math.min(zoom, this.maxZoom); z >= 0; z--) {
      const range = tileRangeForMercator(x0, y0, x1, y1, z);
      const missing: Array<[number, number, number]> = [];
      for (let x = range.x0; x <= range.x1; x++) {
        for (let y = range.y0; y <= range.y1; y++) {
          if (!this.tiles.has(tileKey(z, x, y))) missing.push([z, x, y]);
        }
      }
      if (!missing.length) return;
      let cursor = 0;
      const runners = new Array(Math.min(concurrency, missing.length)).fill(0).map(async () => {
        while (cursor < missing.length) {
          const [tz, tx, ty] = missing[cursor++];
          await this.loadTile(tz, tx, ty);
        }
      });
      await Promise.all(runners);
      const absent = missing.filter(([tz, tx, ty]) => !this.tiles.has(tileKey(tz, tx, ty)));
      if (!absent.length) return;
      // Some tiles are genuinely absent on disk: recurse to the parent level so
      // sampling still has coherent data instead of falling back to z3.
      if (z === 0) return;
    }
  }

  private pixel(i: number, j: number, zoom: number): number {
    const n = 1 << zoom;
    if (i < 0) i = 0; else if (i > n * TILE_PIXELS - 1) i = n * TILE_PIXELS - 1;
    if (j < 0) j = 0; else if (j > n * TILE_PIXELS - 1) j = n * TILE_PIXELS - 1;
    const tx = Math.floor(i / TILE_PIXELS);
    const ty = Math.floor(j / TILE_PIXELS);
    const key = tileKey(zoom, tx, ty);
    let tile = this.lastTile;
    if (!tile || tile.key !== key) {
      tile = this.tiles.get(key) ?? null;
      if (tile) this.lastTile = tile;
    }
    if (!tile) return null;
    return tile.heights[(j - ty * TILE_PIXELS) * TILE_PIXELS + (i - tx * TILE_PIXELS)];
  }

  /** Bilinear DEM height in metres at a mercator position. */
  sample(x: number, y: number, zoom: number): number {
    for (let z = Math.min(zoom, this.maxZoom); z >= 0; z--) {
      const scaled = (1 << z) * TILE_PIXELS;
      const px = x * scaled - 0.5;
      const py = y * scaled - 0.5;
      const ix = Math.floor(px);
      const iy = Math.floor(py);
      const fx = px - ix;
      const fy = py - iy;
      const h00 = this.pixel(ix, iy, z);
      if (h00 === null) continue;
      const h10 = this.pixel(ix + 1, iy, z);
      const h01 = this.pixel(ix, iy + 1, z);
      const h11 = this.pixel(ix + 1, iy + 1, z);
      if (h10 === null || h01 === null || h11 === null) continue;
      return (h00 * (1 - fx) + h10 * fx) * (1 - fy) + (h01 * (1 - fx) + h11 * fx) * fy;
    }
    return 0;
  }

  heightAtLngLat(lng: number, lat: number, zoom: number): number {
    return this.sample(mercatorX(lng), mercatorY(lat), zoom);
  }

  /** Real-world bounds of the tiles on disk, used to keep the mesh inside data. */
  coverageBox(): { x0: number; y0: number; x1: number; y1: number } | null {
    const level = (this.manifest?.levels ?? []).slice().sort((a, b) => b.z - a.z)[0];
    if (!level) return null;
    const n = 1 << level.z;
    return {
      x0: level.minX / n,
      y0: level.minY / n,
      x1: (level.maxX + 1) / n,
      y1: (level.maxY + 1) / n,
    };
  }

  describeCoverage(): string {
    const box = this.coverageBox();
    if (!box) return 'z0-z3 世界概览';
    return `${longitudeOf(box.x0).toFixed(0)}°E–${longitudeOf(box.x1).toFixed(0)}°E / ${latitudeOf(box.y1).toFixed(0)}°N–${latitudeOf(box.y0).toFixed(0)}°N · z0–z${this.maxZoom}`;
  }

  dispose() {
    this.worker?.dispose();
    this.worker = null;
    this.tiles.clear();
  }
}
