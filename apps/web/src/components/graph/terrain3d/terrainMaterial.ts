import * as THREE from 'three';

/**
 * Hypsometric ramp in the 墨韵智考 palette: deep ink water, 青黛 lowland,
 * 岩石灰 mid-slope, 泥金 high ground, pale stone on the highest ridges.
 * Stops are authored in sRGB hex and baked to an 8-bit LUT.
 */
export const TERRAIN_RAMP: Array<[number, string]> = [
  [-400, '#0a1c26'],
  [0, '#1a3b45'],
  [90, '#1e3f42'],
  [300, '#24433f'],
  [650, '#2b4a3f'],
  [1100, '#375444'],
  [1700, '#454d3e'],
  [2400, '#545545'],
  [3100, '#66604b'],
  [3800, '#7d7154'],
  [4500, '#96855f'],
  [5200, '#b1a077'],
  [6000, '#ccbc96'],
  [6900, '#e2d8c0'],
  [8600, '#f4efe5'],
];

const RAMP_SIZE = 256;
const RAMP_MIN = -400;
const RAMP_MAX = 8600;

function buildRampTexture(): THREE.DataTexture {
  const data = new Uint8Array(RAMP_SIZE * 4);
  // Bytes are authored sRGB; the shader decodes them with pow(2.2). Do NOT route
  // the stops through THREE.Color here — three's colour management would already
  // convert them to linear and the shader would decode a second time.
  const parse = (hex: string): [number, number, number] => {
    const value = Number.parseInt(hex.slice(1), 16);
    return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
  };
  const stops = TERRAIN_RAMP.map(([height, hex]) => ({ height, rgb: parse(hex) }));
  for (let i = 0; i < RAMP_SIZE; i++) {
    const height = RAMP_MIN + ((RAMP_MAX - RAMP_MIN) * i) / (RAMP_SIZE - 1);
    let a = stops[0];
    let b = stops[stops.length - 1];
    for (let s = 0; s < stops.length - 1; s++) {
      if (height >= stops[s].height && height <= stops[s + 1].height) { a = stops[s]; b = stops[s + 1]; break; }
    }
    const span = b.height - a.height || 1;
    const t = Math.max(0, Math.min(1, (height - a.height) / span));
    data[i * 4] = Math.round(a.rgb[0] + (b.rgb[0] - a.rgb[0]) * t);
    data[i * 4 + 1] = Math.round(a.rgb[1] + (b.rgb[1] - a.rgb[1]) * t);
    data[i * 4 + 2] = Math.round(a.rgb[2] + (b.rgb[2] - a.rgb[2]) * t);
    data[i * 4 + 3] = 255;
  }
  const texture = new THREE.DataTexture(data, RAMP_SIZE, 1, THREE.RGBAFormat);
  texture.minFilter = THREE.LinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.wrapS = THREE.ClampToEdgeWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  texture.needsUpdate = true;
  return texture;
}

const vertexShader = /* glsl */ `
uniform mat4 u_mvp;
uniform vec2 u_origin;
uniform float u_heightScale;
uniform vec3 u_camera;
uniform float u_heightFactor;  // 1 = real relief, 0 = flat shaded-relief plate

attribute float aElev;
attribute vec2 aGrad;
attribute float aCurv;
attribute float aEdge;

varying float vElev;
varying vec2 vGrad;
varying float vCurv;
varying float vEdge;
varying float vDist;
varying vec3 vWorld;

void main() {
  vec3 p = vec3(position.xy + u_origin, 0.0);
  p.z = max(aElev, 0.0) * u_heightScale * u_heightFactor;
  vElev = aElev;
  vGrad = aGrad;
  vCurv = aCurv;
  vEdge = aEdge;
  vWorld = p;
  vDist = length(p - u_camera);
  gl_Position = u_mvp * vec4(p, 1.0);
}
`;

const fragmentShader = /* glsl */ `
uniform sampler2D u_ramp;
uniform float u_rampMin;
uniform float u_rampMax;
uniform float u_heightScale;
uniform vec3 u_light;
uniform vec3 u_sunColor;
uniform vec3 u_skyColor;
uniform vec3 u_groundColor;
uniform vec3 u_rockColor;
uniform vec3 u_contourColor;
uniform vec3 u_fogColor;
uniform vec3 u_waterColor;
uniform vec3 u_coastColor;
uniform float u_contourInterval;
uniform float u_contourStrength;
uniform float u_fogNear;
uniform float u_fogFar;
uniform float u_aoStrength;
uniform float u_snowLine;

varying float vElev;
varying vec2 vGrad;
varying float vCurv;
varying float vEdge;
varying float vDist;
varying vec3 vWorld;

vec3 toLinear(vec3 srgb) { return pow(srgb, vec3(2.2)); }

void main() {
  float elevation = vElev;
  bool water = elevation <= 0.5;

  // Surface normal in mercator space, derived from the drawn geometry.
  vec2 grad = vGrad * u_heightScale;
  vec3 n = normalize(vec3(-grad.x, -grad.y, 1.0));
  float slope = clamp(1.0 - n.z, 0.0, 1.0);

  float t = clamp((elevation - u_rampMin) / (u_rampMax - u_rampMin), 0.0, 1.0);
  // LUT bytes are sRGB; every uniform colour below is already linear.
  vec3 base = toLinear(texture2D(u_ramp, vec2(t, 0.5)).rgb);

  if (water) {
    // Flat sea: real bathymetry sets the depth tint, but the surface stays flat.
    float depth = clamp(-elevation / 3500.0, 0.0, 1.0);
    base = mix(u_waterColor, u_waterColor * 0.35, depth);
    n = vec3(0.0, 0.0, 1.0);
    slope = 0.0;
  } else {
    // Exposed rock on steep faces, independent of altitude.
    base = mix(base, u_rockColor, smoothstep(0.30, 0.78, slope) * 0.5);
    // Aerial snow only where the DEM really is high.
    float snow = smoothstep(u_snowLine, u_snowLine + 700.0, elevation) * (1.0 - smoothstep(0.30, 0.62, slope));
    base = mix(base, vec3(0.86, 0.87, 0.85), snow * 0.55);
    // Valley concavity from the DEM (no invented detail).
    float ao = clamp(1.0 - max(vCurv, 0.0) / 900.0, 0.0, 1.0);
    base *= mix(1.0, ao, u_aoStrength);
    // Coast rim: a thin cartographic line where land meets sea.
    base = mix(base, u_coastColor, (1.0 - smoothstep(0.0, 55.0, elevation)) * 0.42);
  }

  float ndl = max(dot(n, u_light), 0.0);
  vec3 ambient = mix(u_groundColor, u_skyColor, n.z * 0.5 + 0.5);
  vec3 lit = base * (u_sunColor * ndl + ambient);

  // Gentle rim so ridge crests read against the plate.
  if (!water) {
    float rim = pow(1.0 - ndl, 3.0) * smoothstep(0.12, 0.5, slope);
    lit += vec3(0.62, 0.44, 0.17) * rim * 0.18;
  }

  // Contour lines every u_contourInterval metres, suppressed on cliffs and when
  // the bands would collapse into pixel-scale moire at national zoom.
  if (!water && u_contourStrength > 0.001) {
    float band = elevation / u_contourInterval;
    float fw = max(fwidth(band), 1e-5);
    float line = 1.0 - smoothstep(0.0, fw * 1.4, abs(fract(band + 0.5) - 0.5));
    float density = 1.0 - smoothstep(0.05, 0.16, fw);
    float strength = u_contourStrength * density * (1.0 - smoothstep(0.25, 0.65, slope));
    lit = mix(lit, u_contourColor, line * strength);
  }

  // The relief plate dissolves into the ink sheet instead of ending on a hard edge.
  lit = mix(u_fogColor, lit, smoothstep(0.0, 1.0, vEdge));

  // Aerial perspective keeps the far edge of the plate from ending abruptly.
  float fog = smoothstep(u_fogNear, u_fogFar, vDist);
  lit = mix(lit, u_fogColor, fog * 0.6);

  gl_FragColor = vec4(pow(clamp(lit, 0.0, 1.0), vec3(1.0 / 2.2)), 1.0);
}
`;

export interface TerrainUniforms {
  u_mvp: { value: THREE.Matrix4 };
  u_origin: { value: THREE.Vector2 };
  u_heightScale: { value: number };
  u_camera: { value: THREE.Vector3 };
  u_heightFactor: { value: number };
  u_light: { value: THREE.Vector3 };
  u_sunColor: { value: THREE.Color };
  u_skyColor: { value: THREE.Color };
  u_groundColor: { value: THREE.Color };
  u_rockColor: { value: THREE.Color };
  u_contourColor: { value: THREE.Color };
  u_fogColor: { value: THREE.Color };
  u_waterColor: { value: THREE.Color };
  u_coastColor: { value: THREE.Color };
  u_contourInterval: { value: number };
  u_contourStrength: { value: number };
  u_fogNear: { value: number };
  u_fogFar: { value: number };
  u_aoStrength: { value: number };
  u_snowLine: { value: number };
  u_ramp: { value: THREE.Texture };
  u_rampMin: { value: number };
  u_rampMax: { value: number };
}

export function createTerrainUniforms(): TerrainUniforms {
  return {
    u_mvp: { value: new THREE.Matrix4() },
    u_origin: { value: new THREE.Vector2() },
    u_heightScale: { value: 1 / 40075016.68557849 },
    u_camera: { value: new THREE.Vector3() },
    u_heightFactor: { value: 1 },
    u_light: { value: new THREE.Vector3(-0.55, -0.45, 0.7).normalize() },
    u_sunColor: { value: new THREE.Color('#fff0d0') },
    u_skyColor: { value: new THREE.Color('#44606c') },
    u_groundColor: { value: new THREE.Color('#0b1416') },
    u_rockColor: { value: new THREE.Color('#4a463a') },
    u_contourColor: { value: new THREE.Color('#d9c58c') },
    u_fogColor: { value: new THREE.Color('#061018') },
    u_waterColor: { value: new THREE.Color('#05121b') },
    u_coastColor: { value: new THREE.Color('#2f5a52') },
    u_contourInterval: { value: 800 },
    u_contourStrength: { value: 0.05 },
    u_fogNear: { value: 0.2 },
    u_fogFar: { value: 0.8 },
    u_aoStrength: { value: 0.7 },
    u_snowLine: { value: 6000 },
    u_ramp: { value: buildRampTexture() },
    u_rampMin: { value: RAMP_MIN },
    u_rampMax: { value: RAMP_MAX },
  };
}

export function createTerrainMaterial(uniforms: TerrainUniforms, flat = false): THREE.ShaderMaterial {
  return new THREE.ShaderMaterial({
    uniforms: uniforms as unknown as Record<string, THREE.IUniform>,
    vertexShader,
    fragmentShader,
    transparent: false,
    depthTest: true,
    depthWrite: true,
    side: THREE.FrontSide,
    polygonOffset: flat,
    polygonOffsetFactor: flat ? -1 : 0,
    polygonOffsetUnits: flat ? -2 : 0,
  });
}

/** Light rig used by the scene; exported so tests can assert it is real lighting. */
export function terrainLightDescription() {
  return {
    light: '方向光（西北偏上约 55°）+ 半球环境光（天空 / 地面双色）',
    sun: '#fff0d0',
    sky: '#44606c',
    ground: '#0b1416',
  };
}
