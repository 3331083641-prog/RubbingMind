import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { STELE_DIMENSIONS } from '../../config/steleDimensions';
import { buildSteleModel, SteleModelInstance, HotspotData } from './SteleModelBuilder';
import { Rotate3d, Maximize2, Scan, SunMedium, Flame, Moon, Sparkles, SlidersHorizontal } from 'lucide-react';
import { useExperience } from '../../context/ExperienceContext';

type CameraPresetKey = keyof typeof STELE_DIMENSIONS.cameraPresets;

export type RakingLightPreset = 'archaeology' | 'moonlight' | 'candle' | 'gallery';

const RAKING_PRESETS: Record<
  RakingLightPreset,
  {
    label: string;
    short: string;
    color: number;
    fillColor: number;
    rimColor: number;
    keyIntensity: number;
    ambientIntensity: number;
    hemiIntensity: number;
    fillIntensity: number;
    rimIntensity: number;
    defaultAzimuth: number;
    defaultElevation: number;
    kelvin: string;
  }
> = {
  archaeology: {
    label: '考古斜射光',
    short: '考古斜光',
    color: 0xffefd6,
    fillColor: 0x9bb2c9,
    rimColor: 0xe8c78a,
    keyIntensity: 3.4,
    ambientIntensity: 0.16,
    hemiIntensity: 0.34,
    fillIntensity: 0.42,
    rimIntensity: 1.85,
    defaultAzimuth: -56,
    defaultElevation: 22,
    kelvin: '4200K',
  },
  moonlight: {
    label: '冷月光',
    short: '冷月光',
    color: 0xcbe4ff,
    fillColor: 0x7699ba,
    rimColor: 0x98d8cf,
    keyIntensity: 3.05,
    ambientIntensity: 0.14,
    hemiIntensity: 0.36,
    fillIntensity: 0.48,
    rimIntensity: 2.1,
    defaultAzimuth: 52,
    defaultElevation: 32,
    kelvin: '6800K',
  },
  candle: {
    label: '暖烛火',
    short: '暖烛火',
    color: 0xffb76b,
    fillColor: 0x8f5b3c,
    rimColor: 0xff8c52,
    keyIntensity: 3.35,
    ambientIntensity: 0.15,
    hemiIntensity: 0.28,
    fillIntensity: 0.45,
    rimIntensity: 1.65,
    defaultAzimuth: -44,
    defaultElevation: 16,
    kelvin: '2600K',
  },
  gallery: {
    label: '展馆柔光',
    short: '展馆柔光',
    color: 0xfff3e8,
    fillColor: 0xe2ebf3,
    rimColor: 0xfff3e8,
    keyIntensity: 2.45,
    ambientIntensity: 0.32,
    hemiIntensity: 0.72,
    fillIntensity: 1.35,
    rimIntensity: 2.1,
    defaultAzimuth: 36,
    defaultElevation: 42,
    kelvin: '5000K',
  },
};

type SteleQAWindow = Window & {
  __steleQA?: Map<
    HTMLCanvasElement,
    { inspect: () => unknown; renderMode: (mode: string) => void; preset: (key: CameraPresetKey) => void }
  >;
  __steleDisposed?: { geometries: number; textures: number; disconnected: boolean }[];
};

interface SteleViewerProps {
  customRubbingUrl?: string;
  restoredRubbingUrl?: string;
  steleTitle?: string;
  onOpenWorkbench?: () => void;
  onToggleFullscreen?: () => void;
  isFullscreen?: boolean;
  className?: string;
  showControls?: boolean;
  externalRestorationRatio?: number;
  onHotspotClick?: (point: { title: string; desc: string }) => void;
}

export const SteleViewer: React.FC<SteleViewerProps> = ({
  customRubbingUrl,
  restoredRubbingUrl,
  steleTitle = '唐风龙纹石碑 · 三维数字展陈',
  onOpenWorkbench,
  onToggleFullscreen,
  isFullscreen = false,
  className = '',
  showControls = true,
  externalRestorationRatio,
  onHotspotClick,
}) => {
  const { theme, prefersReducedMotion } = useExperience();
  const qaEnabled =
    typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('steleQA') === '1';

  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const modelInstanceRef = useRef<SteleModelInstance | null>(null);
  const fitCameraRef = useRef<((key: CameraPresetKey, instant?: boolean) => void) | null>(null);
  const presetRef = useRef<CameraPresetKey>('perspective');
  const sceneRef = useRef<THREE.Scene | null>(null);
  const lightsRef = useRef<{
    key: THREE.DirectionalLight;
    ambient: THREE.AmbientLight;
    hemi: THREE.HemisphereLight;
    fill: THREE.DirectionalLight;
    rim: THREE.DirectionalLight;
  } | null>(null);

  const [isLoaded, setIsLoaded] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Interactive states
  const [isAutoRotate, setIsAutoRotate] = useState<boolean>(!prefersReducedMotion);
  const [isLaserScanning, setIsLaserScanning] = useState<boolean>(!prefersReducedMotion);
  const [restorationRatio, setRestorationRatio] = useState<number>(externalRestorationRatio ?? 0.0);
  const [activePreset, setActivePreset] = useState<string>('perspective');
  const [selectedHotspot, setSelectedHotspot] = useState<HotspotData | null>(null);
  const [popupPos, setPopupPos] = useState<{ x: number; y: number } | null>(null);

  // Raking Light Studio state (考古侧光掠影)
  const [rakingPreset, setRakingPreset] = useState<RakingLightPreset>(qaEnabled ? 'gallery' : 'archaeology');
  const [rakingAzimuth, setRakingAzimuth] = useState<number>(qaEnabled ? 36 : -56);
  const [rakingElevation, setRakingElevation] = useState<number>(qaEnabled ? 42 : 22);
  const [rakingDrawerOpen, setRakingDrawerOpen] = useState<boolean>(false);

  const selectedHotspotRef = useRef<HotspotData | null>(null);
  selectedHotspotRef.current = selectedHotspot;
  const isLaserScanningRef = useRef(isLaserScanning);
  isLaserScanningRef.current = isLaserScanning;
  const isAutoRotateRef = useRef(isAutoRotate);
  isAutoRotateRef.current = isAutoRotate;
  const rakingRef = useRef({ preset: rakingPreset, azimuth: rakingAzimuth, elevation: rakingElevation });
  rakingRef.current = { preset: rakingPreset, azimuth: rakingAzimuth, elevation: rakingElevation };
  const themeRef = useRef(theme);
  themeRef.current = theme;
  const reducedMotionRef = useRef(prefersReducedMotion);
  reducedMotionRef.current = prefersReducedMotion;

  const targetCamPos = useRef<THREE.Vector3 | null>(null);
  const targetLookAt = useRef<THREE.Vector3 | null>(null);

  // Sync external restoration ratio if driven by Workbench slider
  useEffect(() => {
    if (typeof externalRestorationRatio === 'number') {
      setRestorationRatio(externalRestorationRatio);
      modelInstanceRef.current?.setMixRatio(externalRestorationRatio);
    }
  }, [externalRestorationRatio]);

  // Update scene background live when theme switches
  useEffect(() => {
    if (!sceneRef.current || qaEnabled) return;
    sceneRef.current.background = new THREE.Color(theme === 'xuan' ? 0xe7dfd0 : 0x0b0e13);
  }, [theme, qaEnabled]);

  // Apply Raking Light parameters live without re-initializing WebGL
  const syncRakingLight = useCallback(
    (presetKey: RakingLightPreset, azimuthDeg: number, elevationDeg: number, flicker = 1.0) => {
      const lights = lightsRef.current;
      if (!lights) return;
      const cfg = RAKING_PRESETS[presetKey];
      const az = THREE.MathUtils.degToRad(azimuthDeg);
      const el = THREE.MathUtils.degToRad(elevationDeg);
      const dist = 5.4;
      const x = Math.sin(az) * Math.cos(el) * dist;
      const y = 1.65 + Math.sin(el) * dist;
      const z = Math.cos(az) * Math.cos(el) * dist;

      lights.key.position.set(x, y, Math.max(0.85, z));
      lights.key.color.setHex(cfg.color);
      lights.key.intensity = cfg.keyIntensity * flicker;

      lights.ambient.intensity = cfg.ambientIntensity;
      lights.hemi.intensity = cfg.hemiIntensity;
      lights.fill.color.setHex(cfg.fillColor);
      lights.fill.intensity = cfg.fillIntensity;
      lights.rim.color.setHex(cfg.rimColor);
      lights.rim.intensity = cfg.rimIntensity;
    },
    [],
  );

  useEffect(() => {
    syncRakingLight(rakingPreset, rakingAzimuth, rakingElevation);
  }, [rakingPreset, rakingAzimuth, rakingElevation, syncRakingLight]);

  // Initialize Three.js Scene
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    let cancelled = false;
    let suspended = false;
    const handleFullscreen = (event: Event) => {
      suspended = !isFullscreen && Boolean((event as CustomEvent<boolean>).detail);
    };
    window.addEventListener('stele-fullscreen', handleFullscreen);
    setIsLoaded(false);
    setLoadError(null);
    targetCamPos.current = targetLookAt.current = null;

    let animFrameId: number;
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 560;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: false,
        powerPreference: 'high-performance',
      });
    } catch {
      setLoadError('当前设备暂不支持 WebGL 3D 渲染，已切换至静帧鉴赏模式。');
      return () => {
        window.removeEventListener('stele-fullscreen', handleFullscreen);
      };
    }

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(
      qaEnabled ? 0x0c1015 : themeRef.current === 'xuan' ? 0xe7dfd0 : 0x0b0e13,
    );
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100);
    const initCam = STELE_DIMENSIONS.cameraPresets.perspective;
    camera.position.set(initCam.position[0], initCam.position[1], initCam.position[2]);
    cameraRef.current = camera;

    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.08;
    rendererRef.current = renderer;

    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.minDistance = 1.5;
    controls.maxDistance = 16;
    controls.target.set(initCam.target[0], initCam.target[1], initCam.target[2]);
    controls.autoRotate = isAutoRotateRef.current;
    controls.autoRotateSpeed = 0.55;
    controlsRef.current = controls;

    controls.addEventListener('start', () => {
      setIsAutoRotate(false);
      targetCamPos.current = targetLookAt.current = null;
    });

    // Museum & Archaeological Raking Light Rig
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.25);
    scene.add(ambientLight);

    const hemiLight = new THREE.HemisphereLight(0xedf2f7, 0x8e867c, 0.55);
    hemiLight.position.set(0, 10, 0);
    scene.add(hemiLight);

    const keyLight = new THREE.DirectionalLight(0xffefd6, 3.0);
    keyLight.position.set(-4.2, 3.5, 3.6);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 1024;
    keyLight.shadow.mapSize.height = 1024;
    keyLight.shadow.bias = -0.0005;
    keyLight.shadow.normalBias = 0.008;
    keyLight.target.position.set(0, 1.65, 0);
    scene.add(keyLight.target);
    Object.assign(keyLight.shadow.camera, { left: -2.2, right: 2.2, top: 2.2, bottom: -2.2 });
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0xcfdce8, 0.85);
    fillLight.position.set(4.5, 3.2, 3.8);
    scene.add(fillLight);

    const rimLight = new THREE.DirectionalLight(0xf3dfc1, 2.0);
    rimLight.position.set(0, 5.2, -4.5);
    scene.add(rimLight);

    const undersideLight = new THREE.DirectionalLight(0xe8edf2, 0.65);
    undersideLight.position.set(-2, -4, 3);
    scene.add(undersideLight);

    lightsRef.current = {
      key: keyLight,
      ambient: ambientLight,
      hemi: hemiLight,
      fill: fillLight,
      rim: rimLight,
    };
    syncRakingLight(rakingRef.current.preset, rakingRef.current.azimuth, rakingRef.current.elevation);

    // Load Authored Tang Twin-Dragon Stele Model (stele-final.glb)
    const textureLoader = new THREE.TextureLoader();
    const steleInstance = buildSteleModel(textureLoader, customRubbingUrl, restoredRubbingUrl);
    modelInstanceRef.current = steleInstance;
    scene.add(steleInstance.group);

    const fitCamera = (key: CameraPresetKey, instant = false) => {
      if (steleInstance.bounds.isEmpty()) return;
      const preset = STELE_DIMENSIONS.cameraPresets[key];
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.fov = preset.fov;
      camera.aspect = w / h;

      // Close-up cinematic presets target the exact carved inscription panel directly
      if (key === 'inscription' || key === 'raking') {
        camera.clearViewOffset();
        camera.updateProjectionMatrix();
        const pos = new THREE.Vector3(...(preset.position as [number, number, number]));
        const tgt = new THREE.Vector3(...(preset.target as [number, number, number]));
        if (instant) {
          targetCamPos.current = targetLookAt.current = null;
          camera.position.copy(pos);
          controls.target.copy(tgt);
          controls.update();
        } else {
          targetCamPos.current = pos;
          targetLookAt.current = tgt;
        }
        return;
      }

      const center = steleInstance.bounds.getCenter(new THREE.Vector3());
      const direction = new THREE.Vector3(...(preset.position as [number, number, number]))
        .sub(new THREE.Vector3(...(preset.target as [number, number, number])))
        .normalize();
      const right = new THREE.Vector3().crossVectors(camera.up, direction).normalize();
      const up = new THREE.Vector3().crossVectors(direction, right).normalize();
      const topMargin = isFullscreen ? 105 : 68;
      const bottomMargin = showControls ? (w < 700 ? 132 : 76) : 24;
      const safeHeight = Math.max(120, h - topMargin - bottomMargin);
      camera.setViewOffset(w, h, 0, (bottomMargin - topMargin) / 2, w, h);
      camera.updateProjectionMatrix();
      const tan = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
      let distance = 2;
      const { min, max } = steleInstance.bounds;
      for (const x of [min.x, max.x]) {
        for (const y of [min.y, max.y]) {
          for (const z of [min.z, max.z]) {
            const delta = new THREE.Vector3(x, y, z).sub(center);
            const depth = delta.dot(direction);
            distance = Math.max(
              distance,
              depth + Math.abs(delta.dot(up)) / ((tan * safeHeight) / h * 0.94),
              depth + Math.abs(delta.dot(right)) / (tan * camera.aspect * 0.88),
            );
          }
        }
      }
      const position = center.clone().addScaledVector(direction, distance);
      if (instant) {
        targetCamPos.current = targetLookAt.current = null;
        camera.position.copy(position);
        controls.target.copy(center);
        controls.update();
      } else {
        targetCamPos.current = position;
        targetLookAt.current = center;
      }
    };
    fitCameraRef.current = fitCamera;

    steleInstance.ready
      .then(() => {
        if (cancelled) return;
        steleInstance.setMixRatio(restorationRatio);
        fitCamera(presetRef.current, true);
        renderer.domElement.dataset.steleReady = 'true';
        setIsLoaded(true);
      })
      .catch((error) => {
        if (!cancelled) setLoadError(error instanceof Error ? error.message : '石碑模型加载失败');
      });

    // Raycaster for 3D Hotspots
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    const handlePointerDown = (event: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -(((event.clientY - rect.top) / rect.height) * 2 - 1);
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster
        .intersectObject(steleInstance.group, true)
        .filter((hit) => !hit.object.name.endsWith('-ring'));

      if (intersects.length > 0) {
        const found = steleInstance.hotspotMeshes.find((h) => h.core === intersects[0].object);
        if (found) {
          setSelectedHotspot(found.data);
          onHotspotClick?.({ title: found.data.title, desc: found.data.desc });
          setPopupPos({ x: event.clientX - rect.left, y: event.clientY - rect.top });
          return;
        }
      }
      setSelectedHotspot(null);
    };
    renderer.domElement.addEventListener('pointerdown', handlePointerDown);

    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      if (renderer.domElement.dataset.steleReady === 'true') fitCamera(presetRef.current, true);
    };
    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    // Render Loop & QA Bridge
    const clock = new THREE.Clock();
    let frames = 0;
    let fps = 0;
    let fpsStart = performance.now();
    const qaWindow = window as SteleQAWindow;
    const clay = new THREE.MeshStandardMaterial({ color: 0x909090, roughness: 0.95, metalness: 0 });
    let qaMode = 'web';

    if (qaEnabled) {
      qaWindow.__steleQA ??= new Map();
      qaWindow.__steleQA.set(renderer.domElement, {
        preset: (key) => {
          setIsAutoRotate(false);
          controls.autoRotate = false;
          presetRef.current = key;
          fitCamera(key, true);
        },
        renderMode: (mode) => {
          qaMode = mode;
          scene.background = new THREE.Color(mode === 'web' ? 0x0c1015 : 0xffffff);
          scene.overrideMaterial = mode === 'clay' ? clay : null;
          steleInstance.hotspotMeshes.forEach((h) => {
            h.core.visible = h.ring.visible = mode === 'web';
          });
        },
        inspect: () => {
          const gl = renderer.getContext();
          const debug = gl.getExtension('WEBGL_debug_renderer_info');
          const points: number[][] = [];
          if (!steleInstance.bounds.isEmpty()) {
            const { min, max } = steleInstance.bounds;
            for (const x of [min.x, max.x]) {
              for (const y of [min.y, max.y]) {
                for (const z of [min.z, max.z]) {
                  const p = new THREE.Vector3(x, y, z).project(camera);
                  points.push([p.x, p.y, p.z]);
                }
              }
            }
          }
          return {
            ready: renderer.domElement.dataset.steleReady === 'true',
            fps,
            transitioning: !!targetCamPos.current,
            interaction: steleInstance.interactionState(),
            position: camera.position.toArray(),
            target: controls.target.toArray(),
            bounds: points,
            triangles: renderer.info.render.triangles,
            calls: renderer.info.render.calls,
            gpu: debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER),
            drawingBuffer: [renderer.domElement.width, renderer.domElement.height],
            pixelRatio: renderer.getPixelRatio(),
            memory: { ...renderer.info.memory },
            modelBounds: {
              min: steleInstance.bounds.min.toArray(),
              max: steleInstance.bounds.max.toArray(),
            },
            meshes: steleInstance.group.children.filter((o) => o.name !== 'SteleFinal').length,
            hotspots: steleInstance.hotspotMeshes.map((h) => {
              const p = h.core.position.clone().project(camera);
              return {
                id: h.data.id,
                x: ((p.x + 1) * container.clientWidth) / 2,
                y: ((1 - p.y) * container.clientHeight) / 2,
              };
            }),
            materials: steleInstance.materials
              .filter((m) => m instanceof THREE.MeshStandardMaterial)
              .map((m) => {
                const s = m as THREE.MeshStandardMaterial;
                return {
                  map: !!s.map,
                  normal: !!s.normalMap,
                  roughness: !!s.roughnessMap,
                  ao: !!s.aoMap,
                  metalness: s.metalness,
                  transparent: s.transparent,
                  colorSpace: s.map?.colorSpace,
                };
              }),
          };
        },
      });
    }

    const animate = () => {
      animFrameId = requestAnimationFrame(animate);
      if (suspended || document.hidden) return;
      const delta = clock.getDelta();
      const elapsed = clock.elapsedTime;
      frames++;
      const now = performance.now();
      if (now - fpsStart >= 1000) {
        fps = (frames * 1000) / (now - fpsStart);
        frames = 0;
        fpsStart = now;
      }

      if (targetCamPos.current && targetLookAt.current) {
        const alpha = 1 - Math.exp(-Math.min(delta, 0.2) * 8.5);
        const offset = camera.position.clone().sub(controls.target);
        const desired = targetCamPos.current.clone().sub(targetLookAt.current);
        const radius = THREE.MathUtils.lerp(offset.length(), desired.length(), alpha);
        const direction = offset.normalize();
        const rotation = new THREE.Quaternion().setFromUnitVectors(direction, desired.normalize());
        direction.applyQuaternion(new THREE.Quaternion().slerp(rotation, alpha));
        controls.target.lerp(targetLookAt.current, alpha);
        camera.position.copy(controls.target).addScaledVector(direction, radius);
        if (camera.position.distanceTo(targetCamPos.current) < 0.002) {
          camera.position.copy(targetCamPos.current);
          controls.target.copy(targetLookAt.current);
          targetCamPos.current = null;
          targetLookAt.current = null;
        }
      }

      controls.autoRotate = isAutoRotateRef.current && !reducedMotionRef.current;
      controls.update();

      // Gentle candle flame shimmer when candle preset active
      if (rakingRef.current.preset === 'candle' && !reducedMotionRef.current && qaMode === 'web') {
        const flicker = 0.94 + Math.sin(elapsed * 7.2) * 0.04 + Math.sin(elapsed * 13.7) * 0.025;
        keyLight.intensity = RAKING_PRESETS.candle.keyIntensity * flicker;
      }

      if (qaMode !== 'web') {
        steleInstance.updateScan(0.5, 0);
      } else if (isLaserScanningRef.current && !reducedMotionRef.current) {
        const scanNormY = Math.sin(elapsed * 1.5) * 0.45 + 0.5;
        steleInstance.updateScan(scanNormY, 1.15);
      } else {
        steleInstance.updateScan(0.5, 0.0);
      }

      steleInstance.hotspotMeshes.forEach((h, idx) => {
        const scale = reducedMotionRef.current ? 1.0 : 1.0 + Math.sin(elapsed * 3.2 + idx * 1.5) * 0.24;
        h.ring.scale.set(scale, scale, 1);
        (h.ring.material as THREE.MeshBasicMaterial).opacity = reducedMotionRef.current
          ? 0.72
          : 0.5 + Math.cos(elapsed * 3.2 + idx * 1.5) * 0.32;
      });

      if (selectedHotspotRef.current) {
        const p = selectedHotspotRef.current.localPos.clone().project(camera);
        const next = {
          x: ((p.x + 1) * container.clientWidth) / 2,
          y: ((1 - p.y) * container.clientHeight) / 2,
        };
        setPopupPos((prev) =>
          prev && Math.abs(prev.x - next.x) < 1 && Math.abs(prev.y - next.y) < 1 ? prev : next,
        );
      }

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelled = true;
      window.removeEventListener('stele-fullscreen', handleFullscreen);
      cancelAnimationFrame(animFrameId);
      resizeObserver.disconnect();
      renderer.domElement.removeEventListener('pointerdown', handlePointerDown);
      controls.dispose();
      steleInstance.dispose();
      keyLight.shadow.map?.dispose();
      clay.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
      fitCameraRef.current = null;
      modelInstanceRef.current = null;
      sceneRef.current = null;
      lightsRef.current = null;
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      if (qaEnabled) {
        qaWindow.__steleQA?.delete(renderer.domElement);
        (qaWindow.__steleDisposed ??= []).push({
          geometries: renderer.info.memory.geometries,
          textures: renderer.info.memory.textures,
          disconnected: !renderer.domElement.isConnected,
        });
      }
    };
  }, [customRubbingUrl, restoredRubbingUrl, isFullscreen, showControls, qaEnabled, syncRakingLight]);

  const toggleAutoRotate = useCallback(() => {
    setIsAutoRotate((prev) => {
      const next = !prev;
      if (controlsRef.current) controlsRef.current.autoRotate = next;
      return next;
    });
  }, []);

  const switchPreset = useCallback((presetKey: CameraPresetKey) => {
    setActivePreset(presetKey);
    setIsAutoRotate(false);
    if (controlsRef.current) controlsRef.current.autoRotate = false;
    presetRef.current = presetKey;
    setSelectedHotspot(null);
    if (presetKey === 'raking') {
      const cfg = RAKING_PRESETS.archaeology;
      setRakingPreset('archaeology');
      setRakingAzimuth(cfg.defaultAzimuth);
      setRakingElevation(cfg.defaultElevation);
    }
    fitCameraRef.current?.(presetKey);
  }, []);

  const selectRakingPreset = (key: RakingLightPreset) => {
    const cfg = RAKING_PRESETS[key];
    setRakingPreset(key);
    setRakingAzimuth(cfg.defaultAzimuth);
    setRakingElevation(cfg.defaultElevation);
  };

  const handleRestorationChange = (ratio: number) => {
    setRestorationRatio(ratio);
    modelInstanceRef.current?.setMixRatio(ratio);
  };

  const activeLightMeta = RAKING_PRESETS[rakingPreset];

  return (
    <div
      data-stele-viewer
      className={`rm-dark-stage relative w-full h-full select-none overflow-hidden ${
        theme === 'xuan' && !qaEnabled ? 'bg-[#e7dfd0]' : 'bg-[#0B0E13]'
      } ${className}`}
    >
      {/* 3D WebGL Canvas Container */}
      <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Loading / Graceful Low-End WebGL Fallback */}
      {!isLoaded && (
        <div
          role="status"
          className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-6 text-center bg-[#0B0E13]/85 text-slate-200 pointer-events-none"
        >
          {loadError ? (
            <>
              <img
                src={customRubbingUrl || '/assets/stele/rubbings/stele_tang_duobao_damaged.png'}
                alt={steleTitle}
                className="max-h-[65%] max-w-[80%] object-contain rounded border border-gold/30 opacity-90"
              />
              <span className="text-xs font-serif text-gold-light">{loadError}</span>
            </>
          ) : (
            <>
              <span className="w-7 h-7 rounded-full border-2 border-gold/30 border-t-gold animate-spin" />
              <span className="text-xs font-serif tracking-widest text-gold-light">
                正在凝石布光 · 载入三维碑刻…
              </span>
            </>
          )}
        </div>
      )}

      {/* Top Banner Tag & Model Switcher */}
      {!isFullscreen && (
        <div className="absolute top-3 left-3.5 right-3.5 z-20 flex items-center justify-between gap-2 pointer-events-none">
          <div
            style={{ backgroundColor: 'rgba(13, 17, 23, 0.92)' }}
            className="px-3 py-1.5 rounded-full border border-gold/40 text-xs font-serif text-[#f2ece1] backdrop-blur-md shadow-card flex items-center gap-2 pointer-events-auto min-w-0 max-w-[56%]"
          >
            <span className="w-2 h-2 rounded-full bg-[#c33927] shrink-0" />
            <span className="font-semibold truncate text-[#f2ece1]">{steleTitle}</span>
            <span className="hidden xl:inline text-[10px] text-[#e5cb98] rm-mono-metric border-l border-white/15 pl-2 shrink-0 whitespace-nowrap">
              {activeLightMeta.short} · {rakingAzimuth}°
            </span>
          </div>

          <div className="flex items-center gap-1.5 pointer-events-auto shrink-0">
            {/* Raking Light Studio Toggle */}
            <button
              type="button"
              data-testid="raking-light-toggle"
              onClick={() => setRakingDrawerOpen((open) => !open)}
              style={rakingDrawerOpen ? undefined : { backgroundColor: 'rgba(13, 17, 23, 0.92)' }}
              className={`px-2.5 py-1.5 rounded-xl text-[11px] font-serif border backdrop-blur-md shadow-card flex items-center gap-1 transition-all whitespace-nowrap ${
                rakingDrawerOpen
                  ? 'bg-[#c33927] border-[#e05d44] text-[#faf6ee] rm-keep-light-ink'
                  : 'border-gold/40 text-[#e5cb98] hover:border-gold'
              }`}
              title="调节考古侧光掠影（方位角、掠射仰角、色温）"
            >
              <SlidersHorizontal className="w-3.5 h-3.5 shrink-0" />
              <span>侧光掠影</span>
            </button>

            {onToggleFullscreen && (
              <button
                type="button"
                onClick={onToggleFullscreen}
                style={{ backgroundColor: 'rgba(13, 17, 23, 0.92)' }}
                className="p-1.5 rounded-xl hover:bg-gold/25 text-[#f2ece1] hover:text-gold border border-gold/35 hover:border-gold transition-all backdrop-blur-md shadow-card"
                title="全屏沉浸式展陈"
                aria-label="全屏沉浸式展陈"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Fullscreen Raking Light Trigger */}
      {isFullscreen && (
        <div className="absolute top-20 right-6 z-30 flex items-center gap-2">
          <button
            type="button"
            data-testid="raking-light-toggle"
            onClick={() => setRakingDrawerOpen((open) => !open)}
            className={`px-3 py-1.5 rounded-xl text-xs font-serif border backdrop-blur-md flex items-center gap-1.5 transition-all ${
              rakingDrawerOpen
                ? 'bg-[#c33927] border-[#e05d44] text-[#faf6ee]'
                : 'bg-[#0d1117]/88 border-gold/35 text-[#e5cb98] hover:border-gold'
            }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>考古侧光掠影</span>
          </button>
        </div>
      )}

      {/* Collapsible Raking Light Floating Control Panel (考古侧光掠影控制台) */}
      {rakingDrawerOpen && (
        <div
          data-testid="raking-light-panel"
          style={{ backgroundColor: 'rgba(13, 17, 23, 0.95)' }}
          className={`absolute ${isFullscreen ? 'top-32 right-6' : 'top-14 right-3.5'} z-30 w-68 max-w-[272px] p-3.5 rounded-2xl border border-gold/45 backdrop-blur-xl shadow-2xl text-xs text-[#f2ece1] space-y-3 rm-animate-unscroll`}
        >
          <div className="flex items-center justify-between border-b border-white/10 pb-2">
            <div>
              <span className="font-serif font-bold text-[#e5cb98] block">考古侧光掠影 · Raking Light</span>
              <span className="text-[10px] text-slate-400">斜射光束掠过石面，凸显阴刻刀锋与微痕</span>
            </div>
            <button
              type="button"
              onClick={() => setRakingDrawerOpen(false)}
              className="text-slate-400 hover:text-white px-1 text-sm"
              aria-label="收起侧光面板"
            >
              ×
            </button>
          </div>

          {/* 3+1 Color Temperature Presets */}
          <div className="grid grid-cols-2 gap-1.5">
            {(
              [
                { key: 'archaeology', label: '考古斜射光', icon: Sparkles },
                { key: 'moonlight', label: '冷月光', icon: Moon },
                { key: 'candle', label: '暖烛火', icon: Flame },
                { key: 'gallery', label: '展馆柔光', icon: SunMedium },
              ] as const
            ).map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                type="button"
                onClick={() => selectRakingPreset(key)}
                className={`px-2 py-1.5 rounded-lg font-serif text-[11px] flex items-center gap-1.5 border transition-all ${
                  rakingPreset === key
                    ? 'bg-gold text-slate-950 border-gold font-bold'
                    : 'bg-white/5 text-slate-200 border-white/10 hover:border-gold/50'
                }`}
              >
                <Icon className="w-3.5 h-3.5 shrink-0" />
                <span>{label}</span>
              </button>
            ))}
          </div>

          {/* Azimuth & Elevation Controls */}
          <div className="space-y-2 pt-1">
            <div className="space-y-1">
              <div className="flex justify-between text-[11px]">
                <span className="font-serif text-slate-300">侧光方位角</span>
                <span className="rm-mono-metric text-[#e5cb98]">{rakingAzimuth}°</span>
              </div>
              <input
                type="range"
                aria-label="侧光方位角"
                min={-78}
                max={78}
                step={2}
                value={rakingAzimuth}
                onChange={(e) => setRakingAzimuth(Number(e.target.value))}
                className="w-full accent-[#C9A66B] cursor-pointer h-1.5 bg-slate-700 rounded-lg"
              />
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-[11px]">
                <span className="font-serif text-slate-300">掠射仰角（越低凹凸越显）</span>
                <span className="rm-mono-metric text-[#e5cb98]">{rakingElevation}°</span>
              </div>
              <input
                type="range"
                aria-label="侧光掠射仰角"
                min={8}
                max={64}
                step={2}
                value={rakingElevation}
                onChange={(e) => setRakingElevation(Number(e.target.value))}
                className="w-full accent-[#C9A66B] cursor-pointer h-1.5 bg-slate-700 rounded-lg"
              />
            </div>
          </div>

          {/* Curatorial Camera Framing Presets */}
          <div className="pt-2 border-t border-white/10 space-y-1.5">
            <span className="text-[10px] text-slate-400 font-serif block">运镜机位预设</span>
            <div className="grid grid-cols-3 gap-1">
              {(
                [
                  { key: 'perspective', label: '全景瞻仰' },
                  { key: 'inscription', label: '铭文细察' },
                  { key: 'raking', label: '斜光鉴刻' },
                ] as const
              ).map((cam) => (
                <button
                  key={cam.key}
                  type="button"
                  onClick={() => switchPreset(cam.key)}
                  className={`py-1 rounded-md text-[11px] font-serif border transition-all ${
                    activePreset === cam.key
                      ? 'bg-[#c33927] border-[#e05d44] text-[#faf6ee] font-semibold'
                      : 'bg-white/5 border-white/10 text-slate-200 hover:border-gold/50'
                  }`}
                >
                  {cam.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Interactive 3D Hotspot Detail Popover */}
      {selectedHotspot && popupPos && (
        <div
          className="absolute z-30 max-w-xs p-4 rounded-xl bg-[#10151c]/95 border border-gold/55 shadow-2xl backdrop-blur-md text-xs text-[#f2ece1] pointer-events-auto"
          style={{
            left: Math.min(popupPos.x + 15, (containerRef.current?.clientWidth || 500) - 280),
            top: Math.max(popupPos.y - 60, 20),
          }}
        >
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-gold/20">
            <span className="font-serif font-bold text-sm text-[#e5cb98] flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#c33927]" />
              {selectedHotspot.title}
            </span>
            <button
              type="button"
              onClick={() => setSelectedHotspot(null)}
              className="text-slate-400 hover:text-white px-1 text-sm font-bold"
            >
              ×
            </button>
          </div>
          <p className="text-slate-200 leading-relaxed font-sans">{selectedHotspot.desc}</p>
          <div className="mt-2.5 pt-2 border-t border-white/10 flex items-center justify-between">
            <span className="text-[11px] rm-mono-metric text-[#df5440]">
              后验概率: {(selectedHotspot.confidence * 100).toFixed(1)}%（交互演示值）
            </span>
            {onOpenWorkbench && (
              <button
                type="button"
                onClick={onOpenWorkbench}
                className="text-[11px] font-serif text-[#e5cb98] hover:underline flex items-center gap-1"
              >
                <span>工作台推演 →</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Bottom Compact Museum Control Bar */}
      {showControls && (
        <div className="absolute bottom-3 left-3.5 right-3.5 z-20 flex flex-wrap items-center justify-between gap-2 pointer-events-none">
          {/* Left: View Preset Switcher (Preserves exact 6 orthographic + perspective labels + adds cinematic quick picks) */}
          <div className="flex flex-wrap items-center gap-0.5 bg-[#0d1117]/90 backdrop-blur-md border border-gold/30 rounded-xl p-1 pointer-events-auto shadow-card">
            {(
              [
                { key: 'front', label: '正面' },
                { key: 'left', label: '左侧' },
                { key: 'right', label: '右侧' },
                { key: 'top', label: '俯视' },
                { key: 'bottom', label: '仰视' },
                { key: 'back', label: '背面' },
                { key: 'perspective', label: '透视' },
              ] as const
            ).map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => switchPreset(item.key)}
                className={`px-2 py-1 rounded-lg text-[11px] font-serif transition-all ${
                  activePreset === item.key
                    ? 'bg-gold text-slate-950 font-bold shadow-gold-glow'
                    : 'text-slate-200 hover:text-white hover:bg-white/10'
                }`}
              >
                {item.label}
              </button>
            ))}

            <span className="hidden sm:inline-block h-4 w-px bg-white/15 mx-1" />

            <button
              type="button"
              onClick={() => switchPreset('inscription')}
              className={`hidden sm:inline-flex px-2 py-1 rounded-lg text-[11px] font-serif transition-all ${
                activePreset === 'inscription'
                  ? 'bg-[#c33927] text-[#faf6ee] font-semibold'
                  : 'text-[#e5cb98] hover:bg-white/10'
              }`}
              title="平滑推近至碑面铭文细察"
            >
              铭文细察
            </button>
            <button
              type="button"
              onClick={() => switchPreset('raking')}
              className={`hidden sm:inline-flex px-2 py-1 rounded-lg text-[11px] font-serif transition-all ${
                activePreset === 'raking'
                  ? 'bg-[#c33927] text-[#faf6ee] font-semibold'
                  : 'text-[#e5cb98] hover:bg-white/10'
              }`}
              title="切换斜光鉴刻视角并启用考古斜射光"
            >
              斜光鉴刻
            </button>

            <button
              type="button"
              onClick={toggleAutoRotate}
              className={`p-1.5 rounded-lg text-xs transition-all border-l border-white/15 ml-0.5 pl-2 ${
                isAutoRotate ? 'text-gold' : 'text-slate-400 hover:text-white'
              }`}
              title={isAutoRotate ? '暂停自由旋转' : '开启自由缓慢旋转'}
            >
              <Rotate3d className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Right: Laser Scan & Restoration Blend Slider (kept as last slider in viewer for QA compatibility) */}
          <div className="flex items-center space-x-2.5 bg-[#0d1117]/90 backdrop-blur-md border border-gold/30 rounded-xl px-2.5 py-1.5 pointer-events-auto shadow-card">
            <button
              type="button"
              onClick={() => setIsLaserScanning(!isLaserScanning)}
              className={`flex items-center space-x-1 text-[11px] font-serif px-2 py-1 rounded-lg border transition-all ${
                isLaserScanning
                  ? 'bg-gold/20 border-gold text-[#e5cb98]'
                  : 'bg-white/5 border-white/15 text-slate-400'
              }`}
            >
              <Scan className="w-3.5 h-3.5" />
              <span>激光扫描: {isLaserScanning ? '开' : '关'}</span>
            </button>

            <div className="flex items-center space-x-2 text-xs">
              <span className="text-slate-400 font-serif text-[11px]">原拓</span>
              <input
                type="range"
                min="0"
                max="1"
                step="0.02"
                value={restorationRatio}
                onChange={(e) => handleRestorationChange(parseFloat(e.target.value))}
                className="w-20 accent-[#C9A66B] cursor-pointer h-1.5 bg-slate-700 rounded-lg"
                title={`修复对比混合度: ${(restorationRatio * 100).toFixed(0)}%`}
              />
              <span className="text-[#e5cb98] font-serif text-[11px]">复原</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
