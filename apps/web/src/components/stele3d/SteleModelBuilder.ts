import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { STELE_DIMENSIONS } from '../../config/steleDimensions';

export interface HotspotData {
  id: string;
  title: string;
  desc: string;
  localPos: THREE.Vector3;
  glyph: string;
  confidence: number;
}

export interface SteleModelInstance {
  group: THREE.Group;
  materials: THREE.Material[];
  textures: THREE.Texture[];
  bounds: THREE.Box3;
  ready: Promise<void>;
  hotspotMeshes: { core: THREE.Mesh; ring: THREE.Mesh; data: HotspotData }[];
  updateScan: (scanY: number, intensity: number) => void;
  setMixRatio: (ratio: number) => void;
  dispose: () => void;
  interactionState: () => { scanY: number; intensity: number; ratio: number };
}

/**
 * One authored GLB (stele-final.glb) for homepage, fullscreen, museum and workbench 3D views.
 * Inscription is part of the closed stone skin, never a floating plane.
 */
export function buildSteleModel(
  textureLoader: THREE.TextureLoader,
  customRubbingUrl?: string,
  restoredRubbingUrl?: string,
): SteleModelInstance {
  const group = new THREE.Group();
  group.name = 'SteleFinal';
  const materials: THREE.Material[] = [];
  const textures: THREE.Texture[] = [];
  const hotspotMeshes: SteleModelInstance['hotspotMeshes'] = [];
  const bounds = new THREE.Box3();
  let disposed = false;

  const uniforms = {
    uScanY: { value: 0.5 },
    uLaserIntensity: { value: 0 },
    uMixRatio: { value: 0 },
    uDamagedTex: { value: null as THREE.Texture | null },
    uRestoredTex: { value: null as THREE.Texture | null },
    uPanel: {
      value: new THREE.Vector4(
        STELE_DIMENSIONS.panel.width,
        STELE_DIMENSIONS.panel.height,
        STELE_DIMENSIONS.panel.yPos,
        0,
      ),
    },
  };

  const disposeObject = (root: THREE.Object3D) => {
    const geos = new Set<THREE.BufferGeometry>();
    const mats = new Set<THREE.Material>(materials);
    const texs = new Set<THREE.Texture>(textures);
    root.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        geos.add(obj.geometry);
        (Array.isArray(obj.material) ? obj.material : [obj.material]).forEach((mat) => mats.add(mat));
      }
    });
    mats.forEach((mat) => {
      Object.values(mat).forEach((value) => {
        if (value instanceof THREE.Texture) texs.add(value);
      });
      mat.dispose();
    });
    const bitmaps = new Set<ImageBitmap>();
    texs.forEach((tex) => {
      if (typeof ImageBitmap !== 'undefined' && tex.source.data instanceof ImageBitmap) {
        bitmaps.add(tex.source.data);
      }
      tex.dispose();
    });
    bitmaps.forEach((bitmap) => bitmap.close());
    geos.forEach((geo) => geo.dispose());
    root.clear();
  };

  const damagedUrl = customRubbingUrl || '/assets/stele/rubbings/stele_tang_duobao_damaged.png';
  const restoredUrl =
    restoredRubbingUrl ||
    (damagedUrl.includes('stele_tang_duobao_damaged')
      ? '/assets/stele/rubbings/stele_tang_duobao_clean.png'
      : damagedUrl);

  const loadRubbing = async (url: string) => {
    const tex = await textureLoader.loadAsync(url);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.anisotropy = 4;
    textures.push(tex);
    return tex;
  };

  const ready = Promise.allSettled([
    new GLTFLoader().loadAsync('/assets/stele/model3d/final/stele-final.glb'),
    loadRubbing(damagedUrl),
    loadRubbing(restoredUrl),
  ]).then((results) => {
    const model = results[0];
    if (model.status === 'rejected') {
      disposeObject(group);
      throw new Error('石碑 GLB 加载失败，请检查模型资源路径。');
    }
    const gltf = model.value;
    if (disposed) {
      disposeObject(gltf.scene);
      return;
    }
    const damaged = results[1];
    const restored = results[2];
    if (damaged.status === 'rejected' || restored.status === 'rejected') {
      disposeObject(gltf.scene);
      throw new Error('碑面修复纹理加载失败。');
    }
    uniforms.uDamagedTex.value = damaged.value;
    uniforms.uRestoredTex.value = restored.value;

    gltf.scene.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh)) return;
      obj.castShadow = obj.receiveShadow = true;
      (Array.isArray(obj.material) ? obj.material : [obj.material]).forEach(
        (mat: THREE.MeshStandardMaterial) => {
          materials.push(mat);
          mat.metalness = 0;
          mat.side = THREE.FrontSide;
          mat.aoMapIntensity = 0.7;
          mat.normalScale.set(0.65, 0.65);
          Object.values(mat).forEach((value) => {
            if (value instanceof THREE.Texture && !textures.includes(value)) {
              value.anisotropy = 4;
              textures.push(value);
            }
          });

          mat.onBeforeCompile = (shader) => {
            Object.assign(shader.uniforms, uniforms);
            shader.vertexShader = shader.vertexShader
              .replace(
                '#include <common>',
                `
            #include <common>
            varying vec3 vStelePosition;
            varying vec3 vSteleNormal;
          `,
              )
              .replace(
                '#include <begin_vertex>',
                `
            #include <begin_vertex>
            vStelePosition = position;
            vSteleNormal = normal;
          `,
              );
            shader.fragmentShader = shader.fragmentShader
              .replace(
                '#include <common>',
                `
            #include <common>
            varying vec3 vStelePosition;
            varying vec3 vSteleNormal;
            uniform sampler2D uDamagedTex;
            uniform sampler2D uRestoredTex;
            uniform float uMixRatio;
            uniform float uScanY;
            uniform float uLaserIntensity;
            uniform vec4 uPanel;
          `,
              )
              .replace(
                '#include <map_fragment>',
                `
            #include <map_fragment>
            vec2 panelUv = vec2(vStelePosition.x / uPanel.x + 0.5, (vStelePosition.y - uPanel.z) / uPanel.y + 0.5);
            float panelMask = step(0.0, panelUv.x) * step(panelUv.x, 1.0) * step(0.0, panelUv.y) * step(panelUv.y, 1.0)
              * step(0.08, vStelePosition.z) * step(0.65, vSteleNormal.z);
            vec3 damaged = texture2D(uDamagedTex, panelUv).rgb;
            vec3 restored = texture2D(uRestoredTex, panelUv).rgb;
            float trace = dot(mix(damaged, restored, uMixRatio), vec3(0.2126, 0.7152, 0.0722));
            diffuseColor.rgb *= 1.0 + panelMask * uMixRatio * (0.16 + trace * 0.26);
          `,
              )
              .replace(
                '#include <emissivemap_fragment>',
                `
            #include <emissivemap_fragment>
            float scanDistance = abs(panelUv.y - uScanY);
            float scan = (1.0 - smoothstep(0.0, 0.004, scanDistance)) + (1.0 - smoothstep(0.0, 0.035, scanDistance)) * 0.15;
            totalEmissiveRadiance += vec3(0.66, 0.38, 0.06) * scan * uLaserIntensity * panelMask;
          `,
              );
          };
          mat.customProgramCacheKey = () => 'stele-pbr-scan-repair-v2';
          mat.needsUpdate = true;
        },
      );
    });

    group.add(gltf.scene);
    bounds.setFromObject(gltf.scene);

    const positions = [
      [0.72, 0.52],
      [0.39, 0.63],
      [0.22, 0.38],
    ];
    const ids = ['h-gan', 'h-cen', 'h-yong'];
    positions.forEach(([u, v], i) => {
      const p = STELE_DIMENSIONS.panel;
      const localPos = new THREE.Vector3((u - 0.5) * p.width, p.yPos + (v - 0.5) * p.height, p.zOffset + 0.004);
      const data: HotspotData = {
        id: ids[i],
        title: `概念铭文 · 残损区域 ${String.fromCharCode(65 + i)}`,
        glyph: '',
        localPos,
        confidence: [0.942, 0.965, 0.928][i],
        desc: '碑面微痕与侧光鉴刻演示热点；所示评分为交互演示值，真实残字释读须进入工作台结合选区考据。',
      };
      const cm = new THREE.MeshBasicMaterial({ color: 0xc33927, depthTest: true, side: THREE.FrontSide });
      const rm = new THREE.MeshBasicMaterial({
        color: 0xc9a66b,
        transparent: true,
        opacity: 0.72,
        depthWrite: false,
        side: THREE.FrontSide,
      });
      materials.push(cm, rm);
      const core = new THREE.Mesh(new THREE.CircleGeometry(0.014, 20), cm);
      const ring = new THREE.Mesh(new THREE.RingGeometry(0.022, 0.028, 32), rm);
      core.position.copy(localPos);
      ring.position.copy(localPos);
      ring.position.z += 0.001;
      core.name = data.id;
      ring.name = `${data.id}-ring`;
      group.add(core, ring);
      hotspotMeshes.push({ core, ring, data });
    });
  });

  return {
    group,
    materials,
    textures,
    hotspotMeshes,
    bounds,
    ready,
    interactionState: () => ({
      scanY: uniforms.uScanY.value,
      intensity: uniforms.uLaserIntensity.value,
      ratio: uniforms.uMixRatio.value,
    }),
    updateScan: (y, intensity) => {
      uniforms.uScanY.value = THREE.MathUtils.clamp(y, 0, 1);
      uniforms.uLaserIntensity.value = intensity;
    },
    setMixRatio: (ratio) => {
      uniforms.uMixRatio.value = THREE.MathUtils.clamp(ratio, 0, 1);
    },
    dispose: () => {
      if (disposed) return;
      disposed = true;
      disposeObject(group);
    },
  };
}
