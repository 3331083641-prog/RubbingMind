import * as THREE from 'three';

/** WGS84 web-mercator circumference in metres (MapLibre's constant). */
export const EARTH_CIRCUMFERENCE = 40075016.68557849;
/** Metres of ground per unit of vertical mercator space (sea level). */
export const MERCATOR_Z_PER_METRE = 1 / EARTH_CIRCUMFERENCE;

export const TILE_SIZE = 512;

export function mercatorX(lon: number): number {
  return (lon + 180) / 360;
}

export function mercatorY(lat: number): number {
  const clamped = Math.max(-85.05112878, Math.min(85.05112878, lat));
  const rad = (clamped * Math.PI) / 180;
  return 0.5 - Math.log(Math.tan(Math.PI / 4 + rad / 2)) / (2 * Math.PI);
}

export function longitudeOf(x: number): number {
  return x * 360 - 180;
}

export function latitudeOf(y: number): number {
  return (Math.atan(Math.sinh(Math.PI * (1 - 2 * y))) * 180) / Math.PI;
}

/** Metres per mercator unit East-West at a latitude (used for true-slope math). */
export function groundMetresPerMercatorUnit(lat: number): number {
  return EARTH_CIRCUMFERENCE * Math.cos((lat * Math.PI) / 180);
}

/**
 * MapLibre v6 hands custom layers `modelViewProjectionMatrix`, which maps
 * *world pixel* space to clip space (`transform._viewProjMatrix`). Scaling it by
 * `worldSize` makes it map normalised web-mercator space ([0,1] in x/y, and
 * z/2πR in z) instead, which is the space this terrain is built in.
 *
 * Verified numerically against `map.project()` — see
 * docs/terrain3d/PROJECTION.md and scripts/test_terrain_projection_browser.py.
 */
export function mercatorToClip(mvp: ArrayLike<number>, worldSize: number, target: THREE.Matrix4): THREE.Matrix4 {
  target.fromArray(mvp as number[]);
  target.multiply(new THREE.Matrix4().makeScale(worldSize, worldSize, worldSize));
  return target;
}

export function worldSizeForZoom(zoom: number): number {
  return TILE_SIZE * Math.pow(2, zoom);
}

/** Screen position in CSS pixels of a mercator point, or null when behind the camera. */
export function projectToScreen(
  mvp: THREE.Matrix4,
  x: number,
  y: number,
  z: number,
  width: number,
  height: number,
): { x: number; y: number; visible: boolean } {
  const p = new THREE.Vector4(x, y, z, 1).applyMatrix4(mvp);
  const w = p.w;
  if (!Number.isFinite(w) || w <= 1e-9) return { x: 0, y: 0, visible: false };
  const ndcX = p.x / w;
  const ndcY = p.y / w;
  return {
    x: (ndcX * 0.5 + 0.5) * width,
    y: (1 - (ndcY * 0.5 + 0.5)) * height,
    visible: ndcX > -1.35 && ndcX < 1.35 && ndcY > -1.35 && ndcY < 1.35 && p.z / w > -1 && p.z / w < 1,
  };
}
