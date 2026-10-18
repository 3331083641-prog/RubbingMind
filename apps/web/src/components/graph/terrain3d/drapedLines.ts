import * as THREE from 'three';
import type { DemStore } from './dem';
import { mercatorX, mercatorY } from './projection';

export interface DrapeGroupSpec {
  id: string;
  /** polylines as [lng, lat][]; polygons are supplied as their rings */
  lines: number[][][];
  color: string;
  widthPx: number;
  opacity: number;
  /** metres above the DEM surface, so lines never sink into the mesh */
  lift: number;
  dash?: [number, number];
}

const vertexShader = /* glsl */ `
uniform mat4 u_mvp;
uniform vec2 u_origin;
uniform vec2 u_res;
uniform float u_width;
uniform float u_heightScale;

attribute vec3 aPrev;
attribute vec3 aNext;
attribute float aSide;
attribute float aDist;

varying float vSide;
varying float vDist;

vec3 worldOf(vec3 p) {
  return vec3(p.xy + u_origin, max(p.z, 0.0) * u_heightScale);
}

void main() {
  vec3 w = worldOf(position);
  vec3 wp = worldOf(aPrev);
  vec3 wn = worldOf(aNext);

  vec4 c = u_mvp * vec4(w, 1.0);
  vec4 cp = u_mvp * vec4(wp, 1.0);
  vec4 cn = u_mvp * vec4(wn, 1.0);

  vec2 s = c.xy / c.w * u_res;
  vec2 sp = (abs(cp.w) > 1e-5) ? cp.xy / cp.w * u_res : s;
  vec2 sn = (abs(cn.w) > 1e-5) ? cn.xy / cn.w * u_res : s;

  vec2 d0 = s - sp;
  vec2 d1 = sn - s;
  vec2 n0 = length(d0) > 1e-4 ? vec2(-d0.y, d0.x) / length(d0) : vec2(0.0);
  vec2 n1 = length(d1) > 1e-4 ? vec2(-d1.y, d1.x) / length(d1) : vec2(0.0);
  vec2 dir = n0 + n1;
  dir = length(dir) > 1e-4 ? normalize(dir) : vec2(0.0, 1.0);
  float miter = 1.0 / max(dot(dir, n0 + 1e-6), 0.35);

  c.xy += (dir * aSide * u_width * 0.5 * miter * 2.0 / u_res) * c.w;
  gl_Position = c;
  vSide = aSide;
  vDist = aDist;
}
`;

const fragmentShader = /* glsl */ `
uniform vec3 u_color;
uniform float u_opacity;
uniform vec2 u_dash;     // (period, duty); duty >= 1 disables dashing

varying float vSide;
varying float vDist;

void main() {
  float edge = 1.0 - smoothstep(0.62, 0.98, abs(vSide));
  float alpha = u_opacity * edge;
  if (u_dash.y < 0.999) {
    float phase = fract(vDist / max(u_dash.x, 1e-6));
    alpha *= step(phase, u_dash.y);
  }
  if (alpha <= 0.002) discard;
  gl_FragColor = vec4(u_color * alpha, alpha);
}
`;

interface GroupRecord {
  spec: DrapeGroupSpec;
  mesh: THREE.Mesh;
  material: THREE.ShaderMaterial;
  vertices: number;
  baseWidth: number;
}

export interface DrapeBuildStats {
  groups: number;
  vertices: number;
  points: number;
  buildMs: number;
}

/**
 * Vector overlays drawn on top of the terrain surface. Every vertex carries the
 * DEM height at its exact longitude/latitude, so borders and rivers follow the
 * same surface the terrain mesh renders instead of floating on a flat plane.
 */
export class DrapedLineLayer {
  readonly group = new THREE.Group();
  private records: GroupRecord[] = [];
  private matrices: Record<string, THREE.IUniform> | null = null;

  constructor() {
    this.group.name = 'draped-vectors';
  }

  empty() {
    return this.records.length === 0;
  }

  build(specs: DrapeGroupSpec[], store: DemStore, demZoom: number, originX: number, originY: number): DrapeBuildStats {
    const started = performance.now();
    this.dispose();
    let points = 0;
    let vertices = 0;
    const mvp = new THREE.Matrix4();
    const res = new THREE.Vector2(1, 1);
    const origin = new THREE.Vector2(originX, originY);
    const heightScale = { value: 1 / 40075016.68557849 };

    for (const spec of specs) {
      const positions: number[] = [];
      const prevs: number[] = [];
      const nexts: number[] = [];
      const sides: number[] = [];
      const dists: number[] = [];
      const indices: number[] = [];
      let base = 0;

      for (const line of spec.lines) {
        if (line.length < 2) continue;
        const px: number[] = [];
        const py: number[] = [];
        const pz: number[] = [];
        for (const [lng, lat] of line) {
          const x = mercatorX(lng);
          const y = mercatorY(lat);
          px.push(x - originX);
          py.push(y - originY);
          pz.push(store.sample(x, y, demZoom) + spec.lift);
          points++;
        }
        const n = px.length;
        let travelled = 0;
        for (let i = 0; i < n; i++) {
          const iPrev = i > 0 ? i - 1 : 0;
          const iNext = i < n - 1 ? i + 1 : n - 1;
          if (i > 0) {
            travelled += Math.hypot(px[i] - px[i - 1], py[i] - py[i - 1]) * 40075016.68557849;
          }
          for (const side of [-1, 1]) {
            positions.push(px[i], py[i], pz[i]);
            prevs.push(px[iPrev], py[iPrev], pz[iPrev]);
            nexts.push(px[iNext], py[iNext], pz[iNext]);
            sides.push(side);
            dists.push(travelled);
          }
        }
        for (let i = 0; i < n - 1; i++) {
          const a = base + i * 2;
          indices.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
        }
        base += n * 2;
      }

      if (!positions.length) continue;

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      geometry.setAttribute('aPrev', new THREE.Float32BufferAttribute(prevs, 3));
      geometry.setAttribute('aNext', new THREE.Float32BufferAttribute(nexts, 3));
      geometry.setAttribute('aSide', new THREE.Float32BufferAttribute(sides, 1));
      geometry.setAttribute('aDist', new THREE.Float32BufferAttribute(dists, 1));
      geometry.setIndex(indices);
      geometry.boundingSphere = new THREE.Sphere(new THREE.Vector3(0, 0, 0), 4);

      const material = new THREE.ShaderMaterial({
        uniforms: {
          u_mvp: { value: mvp },
          u_origin: { value: origin },
          u_res: { value: res },
          u_width: { value: spec.widthPx },
          u_heightScale: heightScale,
          u_color: { value: new THREE.Color(spec.color) },
          u_opacity: { value: spec.opacity },
          u_dash: {
            value: spec.dash
              ? new THREE.Vector2(Math.max(spec.dash[0], 1e-3), spec.dash[1])
              : new THREE.Vector2(1, 1),
          },
        },
        vertexShader,
        fragmentShader,
        transparent: true,
        depthTest: true,
        depthWrite: false,
        side: THREE.DoubleSide,
        polygonOffset: true,
        polygonOffsetFactor: -2,
        polygonOffsetUnits: -4,
      });

      const mesh = new THREE.Mesh(geometry, material);
      mesh.frustumCulled = false;
      mesh.renderOrder = 10;
      this.group.add(mesh);
      this.records.push({ spec, mesh, material, vertices: positions.length / 3, baseWidth: spec.widthPx });
      vertices += positions.length / 3;
    }

    const first = this.records[0];
    this.matrices = first ? first.material.uniforms : null;
    return { groups: this.records.length, vertices, points, buildMs: performance.now() - started };
  }

  /** Shared uniforms are per material, so keep every group in sync each frame. */
  update(mvp: THREE.Matrix4, origin: THREE.Vector2, heightScale: number, size: THREE.Vector2, widthScale = 1) {
    for (const record of this.records) {
      const uniforms = record.material.uniforms;
      (uniforms.u_mvp.value as THREE.Matrix4).copy(mvp);
      (uniforms.u_origin.value as THREE.Vector2).copy(origin);
      (uniforms.u_res.value as THREE.Vector2).copy(size);
      uniforms.u_heightScale.value = heightScale;
      uniforms.u_width.value = record.baseWidth * widthScale;
    }
  }

  setVisible(visible: boolean) {
    this.group.visible = visible;
  }

  setGroupVisible(id: string, visible: boolean) {
    for (const record of this.records) {
      if (record.spec.id === id) record.mesh.visible = visible;
    }
  }

  get vertexCount() {
    return this.records.reduce((total, record) => total + record.vertices, 0);
  }

  dispose() {
    for (const record of this.records) {
      record.mesh.geometry.dispose();
      record.material.dispose();
      this.group.remove(record.mesh);
    }
    this.records = [];
  }
}

/** Flatten GeoJSON geometries into polylines (polygon rings included). */
export function geometriesToPolylines(geometry: GeoJSON.Geometry): number[][][] {
  const out: number[][][] = [];
  switch (geometry.type) {
    case 'LineString':
      out.push(geometry.coordinates as unknown as number[][]);
      break;
    case 'MultiLineString':
      for (const line of geometry.coordinates) out.push(line as unknown as number[][]);
      break;
    case 'Polygon':
      for (const ring of geometry.coordinates) out.push(ring as unknown as number[][]);
      break;
    case 'MultiPolygon':
      for (const polygon of geometry.coordinates) for (const ring of polygon) out.push(ring as unknown as number[][]);
      break;
    case 'GeometryCollection':
      for (const child of geometry.geometries) out.push(...geometriesToPolylines(child));
      break;
    default:
      break;
  }
  return out;
}
