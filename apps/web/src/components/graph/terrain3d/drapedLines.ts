import * as THREE from 'three';
import { mercatorX, mercatorY } from './projection';

export interface DrapeGroupSpec {
  id: string;
  /** polylines as [lng, lat][]; polygons are supplied as their rings */
  lines: number[][][];
  color: string;
  widthPx: number;
  opacity: number;
  /**
   * Relative depth rank, not metres. The scene turns the current camera into a
   * screen-constant lift so lines never sink into the mesh when zooming, and
   * ranks keep casings below cores.
   */
  lift: number;
  dash?: [number, number];
}

const vertexShader = /* glsl */ `
uniform mat4 u_mvp;
uniform vec2 u_origin;
uniform vec2 u_res;
uniform float u_width;
uniform float u_heightScale;
uniform float u_lift;      // metres, recomputed per frame: ~0.8 screen px above the surface

attribute vec3 aStart;
attribute vec3 aEnd;
attribute float aSide;
attribute float aEndFlag;
attribute float aDist;

varying float vSide;
varying float vDist;

vec3 worldOf(vec3 p) {
  return vec3(p.xy + u_origin, (max(p.z, 0.0) + u_lift) * u_heightScale);
}

void main() {
  vec4 cs = u_mvp * vec4(worldOf(aStart), 1.0);
  vec4 ce = u_mvp * vec4(worldOf(aEnd), 1.0);

  // Work in CSS pixels measured from the viewport centre: NDC * resolution / 2.
  vec2 half_res = u_res * 0.5;
  vec2 ss = (abs(cs.w) > 1e-6) ? (cs.xy / cs.w) * half_res : vec2(0.0);
  vec2 se = (abs(ce.w) > 1e-6) ? (ce.xy / ce.w) * half_res : vec2(0.0);

  vec2 delta = se - ss;
  float len = length(delta);
  vec2 dir = len > 1e-4 ? delta / len : vec2(1.0, 0.0);
  vec2 nrm = vec2(-dir.y, dir.x);

  vec4 c = aEndFlag > 0.5 ? ce : cs;
  // Dense administrative data has vertices only a fraction of a pixel apart.
  // Stretching every quad to at least 1.5 px keeps the ribbon continuous instead
  // of leaving pixel-centre gaps (the "dotted border" artefact).
  float extend = max(0.0, (1.5 - len) * 0.5);
  float along = (aEndFlag > 0.5 ? extend : -extend);
  vec2 screenPx = (aEndFlag > 0.5 ? se : ss) + dir * along + nrm * (aSide * u_width * 0.5);

  c.xy = (screenPx / half_res) * c.w;
  gl_Position = c;
  vSide = aSide;
  vDist = aDist;
}
`;

const fragmentShader = /* glsl */ `
uniform vec3 u_color;
uniform float u_opacity;
uniform vec2 u_dash;     // (period, duty); duty >= 1 disables dashing
uniform float u_width;

varying float vSide;
varying float vDist;

void main() {
  // Feather measured in CSS pixels from the centre line, not as a fraction of
  // the ribbon: a 1.3 px border must stay solid instead of fading to a ghost.
  // The 0.55 px ramp keeps a hard core with one pixel of anti-aliasing.
  float halfWidth = max(u_width * 0.5, 0.45);
  float coverage = clamp((halfWidth - abs(vSide) * halfWidth) / 0.55, 0.0, 1.0);
  float alpha = u_opacity * coverage;
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

/** Distance filter that keeps the first and last vertex of every polyline. */
function decimate(line: number[][], minSpacingDegrees: number): number[][] {
  const out: number[][] = [line[0]];
  let last = line[0];
  for (let i = 1; i < line.length - 1; i++) {
    const point = line[i];
    if (Math.abs(point[0] - last[0]) + Math.abs(point[1] - last[1]) >= minSpacingDegrees) {
      out.push(point);
      last = point;
    }
  }
  out.push(line[line.length - 1]);
  return out;
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

  /**
   * @param sampleHeight height of the rendered surface in metres at a mercator
   *   position. Callers pass the terrain build's own interpolator so vectors sit
   *   exactly on the triangles that are drawn, not on a finer DEM sample.
   */
  build(
    specs: DrapeGroupSpec[],
    sampleHeight: (x: number, y: number) => number,
    originX: number,
    originY: number,
    /** minimum spacing in degrees between kept vertices (~1.5 px at this LOD) */
    minSpacingDegrees = 0,
  ): DrapeBuildStats {
    const started = performance.now();
    this.dispose();
    let points = 0;
    let vertices = 0;
    const mvp = new THREE.Matrix4();
    const res = new THREE.Vector2(1, 1);
    const origin = new THREE.Vector2(originX, originY);
    const heightScale = { value: 1 / 40075016.68557849 };

    for (const spec of specs) {
      // One quad per segment (4 vertices) instead of a per-point strip: a segment
      // quad can be stretched to a minimum screen length in the shader, which is
      // what keeps sub-pixel administrative data continuous.
      const positions: number[] = [];
      const starts: number[] = [];
      const ends: number[] = [];
      const sides: number[] = [];
      const endFlags: number[] = [];
      const dists: number[] = [];
      const indices: number[] = [];
      let base = 0;

      for (const raw of spec.lines) {
        if (raw.length < 2) continue;
        // Decimate to roughly 1.5 px at the top zoom of this LOD. Vector data is
        // far denser than pixels here; keeping every vertex produced sub-pixel
        // quads that rasterised as dots instead of a continuous border.
        const line = minSpacingDegrees > 0 ? decimate(raw, minSpacingDegrees) : raw;
        if (line.length < 2) continue;
        const px: number[] = [];
        const py: number[] = [];
        const pz: number[] = [];
        for (const [lng, lat] of line) {
          const x = mercatorX(lng);
          const y = mercatorY(lat);
          px.push(x - originX);
          py.push(y - originY);
          pz.push(sampleHeight(x, y));
          points++;
        }
        const n = px.length;
        let travelled = 0;
        for (let i = 0; i < n - 1; i++) {
          const dx = px[i + 1] - px[i];
          const dy = py[i + 1] - py[i];
          const metres = Math.hypot(dx, dy) * 40075016.68557849;
          if (metres < 0.5) continue; // duplicate vertex, contributes nothing
          for (const side of [-1, 1]) {
            for (const endFlag of [0, 1]) {
              positions.push(px[i], py[i], pz[i]);
              starts.push(px[i], py[i], pz[i]);
              ends.push(px[i + 1], py[i + 1], pz[i + 1]);
              sides.push(side);
              endFlags.push(endFlag);
              dists.push(travelled + (endFlag ? metres : 0));
            }
          }
          indices.push(base, base + 1, base + 2, base + 1, base + 3, base + 2);
          base += 4;
          travelled += metres;
        }
      }

      if (!positions.length) continue;

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      geometry.setAttribute('aStart', new THREE.Float32BufferAttribute(starts, 3));
      geometry.setAttribute('aEnd', new THREE.Float32BufferAttribute(ends, 3));
      geometry.setAttribute('aSide', new THREE.Float32BufferAttribute(sides, 1));
      geometry.setAttribute('aEndFlag', new THREE.Float32BufferAttribute(endFlags, 1));
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
          u_lift: { value: 0 },
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

  /**
   * Shared uniforms are per material, so keep every group in sync each frame.
   * `liftMetres` is the depth separation in metres for a rank-1 group; groups
   * multiply it by their own rank so casings sit under cores without touching
   * the geography.
   */
  update(mvp: THREE.Matrix4, origin: THREE.Vector2, heightScale: number, size: THREE.Vector2, widthScale = 1, liftMetres = 60) {
    for (const record of this.records) {
      const uniforms = record.material.uniforms;
      (uniforms.u_mvp.value as THREE.Matrix4).copy(mvp);
      (uniforms.u_origin.value as THREE.Vector2).copy(origin);
      (uniforms.u_res.value as THREE.Vector2).copy(size);
      uniforms.u_heightScale.value = heightScale;
      uniforms.u_width.value = record.baseWidth * widthScale;
      uniforms.u_lift.value = Math.max(0, liftMetres * (record.spec.lift || 1));
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

  /** ids of the drawn vector groups, exposed for the stats HUD and tests */
  get groupIds(): string[] {
    return this.records.map((record) => record.spec.id);
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
