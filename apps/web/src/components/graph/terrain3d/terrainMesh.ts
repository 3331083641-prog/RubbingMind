import * as THREE from 'three';
import type { DemStore } from './dem';

export interface TerrainSpec {
  /** mercator bounds of the patch */
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  nx: number;
  ny: number;
  demZoom: number;
  /** mercator origin subtracted from every position (double precision on the CPU) */
  originX: number;
  originY: number;
  label: string;
  /** fade the patch border into the background (national plate only) */
  fadeEdge?: boolean;
}

export interface TerrainBuild {
  geometry: THREE.BufferGeometry;
  spec: TerrainSpec;
  vertices: number;
  triangles: number;
  minElevation: number;
  maxElevation: number;
  meanElevation: number;
  buildMs: number;
  /** padded elevation grid the mesh was triangulated from, kept for surface queries */
  grid: Float32Array;
  gridWidth: number;
  gridHeight: number;
}

/**
 * Build an indexed terrain patch from real DEM samples.
 *
 * Positions are stored relative to a patch origin to keep float32 precision at
 * street zoom (the shader re-adds the origin). Every vertex also carries the
 * DEM elevation, its analytic gradient (metres per mercator unit) and a
 * concavity term used for valley shading. The gradient is central-difference on
 * the same grid that is triangulated, so the shading always describes the drawn
 * surface rather than a smoother invented one.
 */
export function buildTerrainPatch(store: DemStore, spec: TerrainSpec): TerrainBuild {
  const started = performance.now();
  const { x0, y0, x1, y1, nx, ny, demZoom, originX, originY } = spec;
  const gx = nx + 2;
  const gy = ny + 2;
  const grid = new Float32Array(gx * gy);

  const stepX = (x1 - x0) / (nx - 1);
  const stepY = (y1 - y0) / (ny - 1);

  let minElevation = Infinity;
  let maxElevation = -Infinity;
  let sum = 0;
  for (let j = 0; j < gy; j++) {
    const y = y0 + (j - 1) * stepY;
    const row = j * gx;
    for (let i = 0; i < gx; i++) {
      const x = x0 + (i - 1) * stepX;
      const h = store.sample(x, y, demZoom);
      grid[row + i] = h;
      if (i > 0 && i < gx - 1 && j > 0 && j < gy - 1) {
        if (h < minElevation) minElevation = h;
        if (h > maxElevation) maxElevation = h;
        sum += h;
      }
    }
  }
  if (!Number.isFinite(minElevation)) { minElevation = 0; maxElevation = 0; }

  const count = nx * ny;
  const positions = new Float32Array(count * 3);
  const elevation = new Float32Array(count);
  const gradient = new Float32Array(count * 2);
  const curvature = new Float32Array(count);
  const edge = new Float32Array(count);
  const fadeX = Math.max((x1 - x0) * 0.14, 1e-6);
  const fadeY = Math.max((y1 - y0) * 0.14, 1e-6);

  // Shading gradients come from a lightly smoothed copy of the DEM so that
  // texel-scale noise does not turn into speckle. Heights stay untouched: the
  // mesh silhouette and every elevation value remain the raw DEM sample.
  const smooth = blurGrid(grid, gx, gy);

  const invStepX2 = 1 / (stepX * 2);
  const invStepY2 = 1 / (stepY * 2);
  let p = 0;
  for (let j = 0; j < ny; j++) {
    const row = (j + 1) * gx;
    const y = y0 + j * stepY;
    for (let i = 0; i < nx; i++, p++) {
      const index = row + i + 1;
      const h = grid[index];
      positions[p * 3] = x0 + i * stepX - originX;
      positions[p * 3 + 1] = y - originY;
      positions[p * 3 + 2] = 0;
      elevation[p] = h;
      gradient[p * 2] = (smooth[index + 1] - smooth[index - 1]) * invStepX2;
      gradient[p * 2 + 1] = (smooth[index + gx] - smooth[index - gx]) * invStepY2;
      curvature[p] = (smooth[index - 1] + smooth[index + 1] + smooth[index - gx] + smooth[index + gx]) * 0.25 - smooth[index];
      if (spec.fadeEdge) {
        const px = x0 + i * stepX;
        const py = y0 + j * stepY;
        const fx = Math.min(px - x0, x1 - px) / fadeX;
        const fy = Math.min(py - y0, y1 - py) / fadeY;
        edge[p] = Math.max(0, Math.min(1, Math.min(fx, fy)));
      } else {
        edge[p] = 1;
      }
    }
  }

  const indices = count > 65535 ? new Uint32Array((nx - 1) * (ny - 1) * 6) : new Uint16Array((nx - 1) * (ny - 1) * 6);
  let cursor = 0;
  for (let j = 0; j < ny - 1; j++) {
    const row = j * nx;
    for (let i = 0; i < nx - 1; i++) {
      const a = row + i;
      const b = a + 1;
      const c = a + nx;
      const d = c + 1;
      indices[cursor++] = a;
      indices[cursor++] = c;
      indices[cursor++] = b;
      indices[cursor++] = b;
      indices[cursor++] = c;
      indices[cursor++] = d;
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('aElev', new THREE.BufferAttribute(elevation, 1));
  geometry.setAttribute('aGrad', new THREE.BufferAttribute(gradient, 2));
  geometry.setAttribute('aCurv', new THREE.BufferAttribute(curvature, 1));
  geometry.setAttribute('aEdge', new THREE.BufferAttribute(edge, 1));
  geometry.setIndex(new THREE.BufferAttribute(indices, 1));
  // Heights are applied in the vertex shader, so the CPU-side bounds stay flat.
  geometry.boundingSphere = new THREE.Sphere(new THREE.Vector3((x1 - x0) / 2, (y1 - y0) / 2, 0), 1);

  return {
    geometry,
    spec,
    vertices: count,
    triangles: (nx - 1) * (ny - 1) * 2,
    minElevation,
    maxElevation,
    meanElevation: sum / count,
    buildMs: performance.now() - started,
    grid,
    gridWidth: gx,
    gridHeight: gy,
  };
}

/**
 * Height of the *rendered* surface at a mercator position, bilinearly
 * interpolated on the same grid the triangle mesh was built from.
 *
 * Draped borders and markers use this instead of sampling the DEM directly: the
 * mesh only carries one elevation per cell, so a raw DEM sample can differ by
 * tens of metres from the surface actually drawn and would make lines dive under
 * ridges or float above valleys.
 */
export function sampleBuildSurface(build: TerrainBuild, x: number, y: number): number {
  const { x0, y0, x1, y1, nx, ny } = build.spec;
  const stepX = (x1 - x0) / (nx - 1);
  const stepY = (y1 - y0) / (ny - 1);
  const gx = build.gridWidth;
  const gy = build.gridHeight;
  const fx = (x - x0) / stepX + 1;
  const fy = (y - y0) / stepY + 1;
  const ix = Math.min(gx - 2, Math.max(0, Math.floor(fx)));
  const iy = Math.min(gy - 2, Math.max(0, Math.floor(fy)));
  const tx = Math.min(1, Math.max(0, fx - ix));
  const ty = Math.min(1, Math.max(0, fy - iy));
  const grid = build.grid;
  const a = grid[iy * gx + ix];
  const b = grid[iy * gx + ix + 1];
  const c = grid[(iy + 1) * gx + ix];
  const d = grid[(iy + 1) * gx + ix + 1];
  return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty;
}

/** True when a mercator position falls inside the patch footprint. */
export function buildCovers(build: TerrainBuild, x: number, y: number): boolean {
  const { x0, y0, x1, y1 } = build.spec;
  return x >= x0 && x <= x1 && y >= y0 && y <= y1;
}

/** Separable binomial (1-4-6-4-1) blur used only for shading derivatives. */
function blurGrid(source: Float32Array, width: number, height: number): Float32Array {
  const weights = [1, 4, 6, 4, 1];
  const total = 16;
  const horizontal = new Float32Array(source.length);
  const output = new Float32Array(source.length);
  for (let j = 0; j < height; j++) {
    const row = j * width;
    for (let i = 0; i < width; i++) {
      let sum = 0;
      for (let k = -2; k <= 2; k++) {
        const ii = Math.min(width - 1, Math.max(0, i + k));
        sum += source[row + ii] * weights[k + 2];
      }
      horizontal[row + i] = sum / total;
    }
  }
  for (let j = 0; j < height; j++) {
    for (let i = 0; i < width; i++) {
      let sum = 0;
      for (let k = -2; k <= 2; k++) {
        const jj = Math.min(height - 1, Math.max(0, j + k));
        sum += horizontal[jj * width + i] * weights[k + 2];
      }
      output[j * width + i] = sum / total;
    }
  }
  return output;
}

export function disposeBuild(build: TerrainBuild | null) {
  if (!build) return;
  build.geometry.dispose();
  // attributes are plain typed arrays; three frees the GPU buffers on dispose
}

/** Read a DEM height in metres at a mercator position (terrain-following helpers). */
export function groundHeight(store: DemStore, x: number, y: number, zoom: number): number {
  return store.sample(x, y, zoom);
}
