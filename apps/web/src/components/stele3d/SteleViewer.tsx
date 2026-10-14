import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { STELE_DIMENSIONS } from '../../config/steleDimensions';
import { buildSteleModel, SteleModelInstance, HotspotData } from './SteleModelBuilder';
import { Rotate3d, Maximize2, Minimize2, Scan } from 'lucide-react';

// Opt-in inspection bridge for the dedicated browser acceptance script.
// It is absent in normal use and never changes non-stele application state.
type SteleQAWindow = Window & {
  __steleQA?: Map<HTMLCanvasElement, {inspect: () => unknown; renderMode: (mode: string) => void; preset: (key: keyof typeof STELE_DIMENSIONS.cameraPresets) => void}>;
  __steleDisposed?: {geometries: number; textures: number; disconnected: boolean}[];
};

interface SteleViewerProps {
  customRubbingUrl?: string;
  steleTitle?: string;
  onOpenWorkbench?: () => void;
  onToggleFullscreen?: () => void;
  isFullscreen?: boolean;
  className?: string;
  showControls?: boolean;
  onHotspotClick?: (point: { title: string; desc: string }) => void;
}

export const SteleViewer: React.FC<SteleViewerProps> = ({
  customRubbingUrl,
  steleTitle = '唐风龙纹石碑 · 三维数字展陈模型',
  onOpenWorkbench,
  onToggleFullscreen,
  isFullscreen = false,
  className = '',
  showControls = true,
  onHotspotClick,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const modelInstanceRef = useRef<SteleModelInstance | null>(null);
  const fitCameraRef = useRef<((key: keyof typeof STELE_DIMENSIONS.cameraPresets, instant?: boolean) => void) | null>(null);
  const presetRef = useRef<keyof typeof STELE_DIMENSIONS.cameraPresets>('perspective');
  const [isLoaded, setIsLoaded] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  // States
  const [isAutoRotate, setIsAutoRotate] = useState<boolean>(true);
  const [isLaserScanning, setIsLaserScanning] = useState<boolean>(true);
  const [restorationRatio, setRestorationRatio] = useState<number>(0.0); // 0 = damaged, 1 = restored
  const [activePreset, setActivePreset] = useState<string>('perspective');
  const [selectedHotspot, setSelectedHotspot] = useState<HotspotData | null>(null);
  const [popupPos, setPopupPos] = useState<{ x: number; y: number } | null>(null);
  const selectedHotspotRef = useRef<HotspotData | null>(null);
  selectedHotspotRef.current = selectedHotspot;

  // Synced refs for animation loop to avoid stale closure
  const isLaserScanningRef = useRef(isLaserScanning);
  isLaserScanningRef.current = isLaserScanning;
  const isAutoRotateRef = useRef(isAutoRotate);
  isAutoRotateRef.current = isAutoRotate;

  // Smooth camera tween targets
  const targetCamPos = useRef<THREE.Vector3 | null>(null);
  const targetLookAt = useRef<THREE.Vector3 | null>(null);

  // Initialize Three.js Scene
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    let cancelled = false;
    let suspended = false;
    const handleFullscreen = (event: Event) => { suspended = !isFullscreen && Boolean((event as CustomEvent<boolean>).detail); };
    window.addEventListener('stele-fullscreen', handleFullscreen);
    setIsLoaded(false);
    setLoadError(null);
    targetCamPos.current = targetLookAt.current = null;

    let animFrameId: number;
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 560;

    // 1. Scene & Fog (深墨色与暖灰渐变空间)
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0c1015);

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(44, width / height, 0.1, 100);
    const initCam = STELE_DIMENSIONS.cameraPresets.perspective;
    camera.position.set(initCam.position[0], initCam.position[1], initCam.position[2]);
    cameraRef.current = camera;

    // 3. High Performance Renderer with Museum Color Grading
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
    });
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

    // 4. OrbitControls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 2.0;
    controls.maxDistance = 18;
    controls.target.set(initCam.target[0], initCam.target[1], initCam.target[2]);
    controls.autoRotate = isAutoRotate;
    controls.autoRotateSpeed = 0.8;
    controlsRef.current = controls;

    // 用户交互时自动暂停旋转
    controls.addEventListener('start', () => {
      setIsAutoRotate(false);
      targetCamPos.current = targetLookAt.current = null;
    });

    // 5. 博物馆级专业展览布光体系 (彻底照亮石雕细节)
    // 5.1 环境全局光 (充足底光)
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.32);
    scene.add(ambientLight);

    const hemiLight = new THREE.HemisphereLight(0xedf2f7, 0x98918a, 0.72);
    hemiLight.position.set(0, 10, 0);
    scene.add(hemiLight);

    // 5.2 主方向光 (Key Light - 暖白偏右上方)
    const keyLight = new THREE.DirectionalLight(0xfff3e8, 2.4);
    keyLight.position.set(4.5, 6.0, 5.0);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 1024;
    keyLight.shadow.mapSize.height = 1024;
    keyLight.shadow.bias = -0.0005;
    keyLight.shadow.normalBias = 0.008;
    keyLight.target.position.set(0, 1.65, 0);
    scene.add(keyLight.target);
    Object.assign(keyLight.shadow.camera, { left: -2.2, right: 2.2, top: 2.2, bottom: -2.2 });
    scene.add(keyLight);

    // 5.3 辅助填充光 (Fill Light - 柔和偏左前方，消除深部死阴影)
    const fillLight = new THREE.DirectionalLight(0xe2ebf3, 1.4);
    fillLight.position.set(-4.5, 3.5, 4.0);
    scene.add(fillLight);

    // 5.4 背部金色轮廓光 (Rim Light - 勾勒碑首双龙飞扬剪影)
    const rimLight = new THREE.DirectionalLight(0xfff3e8, 2.2);
    rimLight.position.set(0, 5.5, -4.5);
    scene.add(rimLight);

    const undersideLight = new THREE.DirectionalLight(0xe8edf2, 0.75);
    undersideLight.position.set(-2, -4, 3);
    scene.add(undersideLight);

    // Empty exhibition space: no floor or halo can occlude the underside.

    // 6. 构建高精度三维碑刻模型实例
    const textureLoader = new THREE.TextureLoader();
    const steleInstance = buildSteleModel(textureLoader, customRubbingUrl);
    modelInstanceRef.current = steleInstance;
    scene.add(steleInstance.group);

    const fitCamera = (key: keyof typeof STELE_DIMENSIONS.cameraPresets, instant = false) => {
      if (steleInstance.bounds.isEmpty()) return;
      const preset = STELE_DIMENSIONS.cameraPresets[key];
      const center = steleInstance.bounds.getCenter(new THREE.Vector3());
      const direction = new THREE.Vector3(...preset.position as [number, number, number])
        .sub(new THREE.Vector3(...preset.target as [number, number, number])).normalize();
      const right = new THREE.Vector3().crossVectors(camera.up, direction).normalize();
      const up = new THREE.Vector3().crossVectors(direction, right).normalize();
      const w = container.clientWidth, h = container.clientHeight;
      // Reserve real overlay area. Narrow exhibition window wraps its controls.
      const topMargin = isFullscreen ? 105 : 65;
      const bottomMargin = showControls ? (w < 700 ? 132 : 65) : 24;
      const safeHeight = Math.max(120, h - topMargin - bottomMargin);
      camera.fov = preset.fov;
      camera.aspect = w / h;
      camera.setViewOffset(w, h, 0, (bottomMargin - topMargin) / 2, w, h);
      camera.updateProjectionMatrix();
      const tan = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
      let distance = 2;
      const { min, max } = steleInstance.bounds;
      for (const x of [min.x,max.x]) for (const y of [min.y,max.y]) for (const z of [min.z,max.z]) {
        const delta = new THREE.Vector3(x,y,z).sub(center);
        const depth = delta.dot(direction);
        distance = Math.max(distance, depth + Math.abs(delta.dot(up)) / (tan * safeHeight / h * .94),
          depth + Math.abs(delta.dot(right)) / (tan * camera.aspect * .88));
      }
      const position = center.clone().addScaledVector(direction, distance);
      if (instant) {
        targetCamPos.current = targetLookAt.current = null;
        camera.position.copy(position); controls.target.copy(center); controls.update();
      } else { targetCamPos.current = position; targetLookAt.current = center; }
    };
    fitCameraRef.current = fitCamera;
    steleInstance.ready.then(() => {
      if (cancelled) return;
      steleInstance.setMixRatio(restorationRatio);
      fitCamera(presetRef.current, true);
      renderer.domElement.dataset.steleReady = 'true';
      setIsLoaded(true);
    }).catch(error => {
      if (!cancelled) setLoadError(error instanceof Error ? error.message : '石碑模型加载失败');
    });

    // 7. Raycaster 拾取 3D 局部残字热点
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const handlePointerDown = (event: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -(((event.clientY - rect.top) / rect.height) * 2 - 1);

      raycaster.setFromCamera(mouse, camera);
      // Test the actual stone too; back-facing/occluded hotspots cannot be picked.
      const intersects = raycaster.intersectObject(steleInstance.group, true)
        .filter(hit => !hit.object.name.endsWith('-ring'));

      if (intersects.length > 0) {
        const found = steleInstance.hotspotMeshes.find((h) => h.core === intersects[0].object);
        if (found) {
          setSelectedHotspot(found.data);
          onHotspotClick?.({title: found.data.title, desc: found.data.desc});
          setPopupPos({ x: event.clientX - rect.left, y: event.clientY - rect.top });
          return;
        }
      }
      setSelectedHotspot(null);
    };

    renderer.domElement.addEventListener('pointerdown', handlePointerDown);

    // 8. 窗口尺寸自适应
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

    // 9. 渲染与动画循环 (60 FPS)
    const clock = new THREE.Clock();
    let frames = 0, fps = 0, fpsStart = performance.now();
    const qaWindow = window as SteleQAWindow;
    const qaEnabled = new URLSearchParams(window.location.search).get('steleQA') === '1';
    const clay = new THREE.MeshStandardMaterial({color:0x909090, roughness:.95, metalness:0});
    let qaMode = 'web';
    if (qaEnabled) {
      qaWindow.__steleQA ??= new Map();
      qaWindow.__steleQA.set(renderer.domElement, {
        preset: key => { setIsAutoRotate(false); controls.autoRotate=false; presetRef.current=key; fitCamera(key,true); },
        renderMode: mode => {
          qaMode=mode;
          scene.background=new THREE.Color(mode==='web' ? 0x0c1015 : 0xffffff);
          scene.overrideMaterial=mode==='clay' ? clay : null;
          steleInstance.hotspotMeshes.forEach(h => {h.core.visible=h.ring.visible=mode==='web';});
        },
        inspect: () => {
          const gl=renderer.getContext();
          const debug=gl.getExtension('WEBGL_debug_renderer_info');
          const points: number[][]=[];
          if (!steleInstance.bounds.isEmpty()) {
            const {min,max}=steleInstance.bounds;
            for (const x of [min.x,max.x]) for (const y of [min.y,max.y]) for (const z of [min.z,max.z]) {
              const p=new THREE.Vector3(x,y,z).project(camera); points.push([p.x,p.y,p.z]);
            }
          }
          return {ready:renderer.domElement.dataset.steleReady==='true',fps,transitioning:!!targetCamPos.current,interaction:steleInstance.interactionState(),
            position:camera.position.toArray(),target:controls.target.toArray(),bounds:points,
            triangles:renderer.info.render.triangles,calls:renderer.info.render.calls,
            gpu:debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER),
            drawingBuffer:[renderer.domElement.width,renderer.domElement.height],pixelRatio:renderer.getPixelRatio(),
            memory:{...renderer.info.memory},modelBounds:{min:steleInstance.bounds.min.toArray(),max:steleInstance.bounds.max.toArray()},
            meshes:steleInstance.group.children.filter(o=>o.name!=='SteleFinal').length,
            hotspots:steleInstance.hotspotMeshes.map(h=> {
              const p=h.core.position.clone().project(camera);
              return {id:h.data.id,x:(p.x+1)*container.clientWidth/2,y:(1-p.y)*container.clientHeight/2};
            }),
            materials:steleInstance.materials.filter(m=>m instanceof THREE.MeshStandardMaterial).map(m=> {
              const s=m as THREE.MeshStandardMaterial;
              return {map:!!s.map,normal:!!s.normalMap,roughness:!!s.roughnessMap,ao:!!s.aoMap,metalness:s.metalness,transparent:s.transparent,colorSpace:s.map?.colorSpace};
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
      const now=performance.now();
      if (now-fpsStart>=1000) {fps=frames*1000/(now-fpsStart);frames=0;fpsStart=now;}

      // 相机平滑插值到预设目标 (Tween Lerp)
      if (targetCamPos.current && targetLookAt.current) {
        // Rotate around the stone at a safe radius instead of interpolating
        // through it when switching from front to back or top to underside.
        const alpha=1-Math.exp(-Math.min(delta,.2)*9);
        const offset=camera.position.clone().sub(controls.target);
        const desired=targetCamPos.current.clone().sub(targetLookAt.current);
        const radius=THREE.MathUtils.lerp(offset.length(),desired.length(),alpha);
        const direction=offset.normalize();
        const rotation=new THREE.Quaternion().setFromUnitVectors(direction,desired.normalize());
        direction.applyQuaternion(new THREE.Quaternion().slerp(rotation,alpha));
        controls.target.lerp(targetLookAt.current,alpha);
        camera.position.copy(controls.target).addScaledVector(direction,radius);
        if (camera.position.distanceTo(targetCamPos.current) < 0.002) {
          camera.position.copy(targetCamPos.current);
          controls.target.copy(targetLookAt.current);
          targetCamPos.current = null;
          targetLookAt.current = null;
        }
      }

      // 控制器更新
      controls.autoRotate = isAutoRotateRef.current;
      controls.update();

      // 激光扫描上下循环 (0.05 ~ 0.95 归一化 UV)
      if (qaMode !== 'web') {
        steleInstance.updateScan(0.5, 0);
      } else if (isLaserScanningRef.current) {
        const scanNormY = Math.sin(elapsed * 1.8) * 0.45 + 0.5;
        steleInstance.updateScan(scanNormY, 1.2);
      } else {
        steleInstance.updateScan(0.5, 0.0);
      }

      // 残字热点双环呼吸动画
      steleInstance.hotspotMeshes.forEach((h, idx) => {
        const scale = 1.0 + Math.sin(elapsed * 3.5 + idx * 1.5) * 0.28;
        h.ring.scale.set(scale, scale, 1);
        (h.ring.material as THREE.MeshBasicMaterial).opacity =
          0.5 + Math.cos(elapsed * 3.5 + idx * 1.5) * 0.35;
      });

      if (selectedHotspotRef.current) {
        const p = selectedHotspotRef.current.localPos.clone().project(camera);
        const next = {x:(p.x+1)*container.clientWidth/2, y:(1-p.y)*container.clientHeight/2};
        setPopupPos(prev => prev && Math.abs(prev.x-next.x)<1 && Math.abs(prev.y-next.y)<1 ? prev : next);
      }

      renderer.render(scene, camera);
    };

    animate();

    // 10. 资源安全清理
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
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      if (qaEnabled) {
        qaWindow.__steleQA?.delete(renderer.domElement);
        (qaWindow.__steleDisposed ??= []).push({geometries:renderer.info.memory.geometries,textures:renderer.info.memory.textures,disconnected:!renderer.domElement.isConnected});
      }
    };
  }, [customRubbingUrl, isFullscreen, showControls]);

  // 控制自动旋转开关
  const toggleAutoRotate = useCallback(() => {
    setIsAutoRotate((prev) => {
      const next = !prev;
      if (controlsRef.current) controlsRef.current.autoRotate = next;
      return next;
    });
  }, []);

  // 视角平滑切换
  const switchPreset = useCallback((presetKey: keyof typeof STELE_DIMENSIONS.cameraPresets) => {
    setActivePreset(presetKey);
    setIsAutoRotate(false);
    if (controlsRef.current) controlsRef.current.autoRotate = false;

    presetRef.current = presetKey;
    setSelectedHotspot(null);
    fitCameraRef.current?.(presetKey);
  }, []);

  // 修复混合度滑块更新
  const handleRestorationChange = (ratio: number) => {
    setRestorationRatio(ratio);
    if (modelInstanceRef.current) {
      modelInstanceRef.current.setMixRatio(ratio);
    }
  };

  return (
    <div data-stele-viewer className={`relative w-full h-full select-none overflow-hidden bg-[#0C1015] ${className}`}>
      {/* 3D WebGL Canvas Container */}
      <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />
      {!isLoaded && (
        <div role="status" className="absolute inset-0 flex items-center justify-center text-xs text-slate-300 pointer-events-none">
          {loadError || '正在加载石碑三维模型…'}
        </div>
      )}

      {/* Top Banner Tag */}
      {!isFullscreen && <div className="absolute top-3.5 left-4 z-20 pointer-events-none flex items-center space-x-2.5">
        <div className="px-3 py-1.5 rounded-full bg-slate-900/85 border border-gold/40 text-xs font-serif text-gold-light backdrop-blur-md shadow-card flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-cinnabar animate-pulse" />
          <span className="font-semibold">{steleTitle}</span>
          <span className="text-[10px] text-slate-400 font-sans border-l border-slate-700 pl-2">
            PBR 仿古青石 · 双龙浮雕 · 概念铭文
          </span>
        </div>
      </div>}

      {/* Top Right Tool Action: Fullscreen */}
      {onToggleFullscreen && !isFullscreen && (
        <div className="absolute top-3.5 right-4 z-20">
          <button
            onClick={onToggleFullscreen}
            className="p-2 rounded-xl bg-slate-900/80 hover:bg-gold/20 text-slate-300 hover:text-gold border border-gold/30 hover:border-gold transition-all backdrop-blur-md shadow-card"
            title={isFullscreen ? '退出全屏' : '全屏沉浸式展陈'}
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      )}

      {/* Interactive 3D Hotspot Detail Popover */}
      {selectedHotspot && popupPos && (
        <div
          className="absolute z-30 max-w-xs p-4 rounded-xl bg-[#121820]/95 border border-gold/60 shadow-gold-glow backdrop-blur-md text-xs animate-fadeIn pointer-events-auto"
          style={{
            left: Math.min(popupPos.x + 15, (containerRef.current?.clientWidth || 500) - 280),
            top: Math.max(popupPos.y - 60, 20),
          }}
        >
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-gold/20">
            <span className="font-serif font-bold text-sm text-gold-light flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cinnabar" />
              {selectedHotspot.title}
            </span>
            <button
              onClick={() => setSelectedHotspot(null)}
              className="text-slate-400 hover:text-white px-1 text-sm font-bold"
            >
              ×
            </button>
          </div>
          <p className="text-slate-200 leading-relaxed font-sans">{selectedHotspot.desc}</p>
          <div className="mt-2.5 pt-2 border-t border-slate-800 flex items-center justify-between">
            <span className="text-[11px] font-mono text-cinnabar-light">
              后验概率: {(selectedHotspot.confidence * 100).toFixed(1)}%
            </span>
            {onOpenWorkbench && (
              <button
                onClick={onOpenWorkbench}
                className="text-[11px] font-serif text-gold hover:underline flex items-center gap-1"
              >
                <span>工作台推演</span>
                <span>→</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Bottom Compact Museum Control Bar */}
      {showControls && (
        <div className="absolute bottom-3.5 left-4 right-4 z-20 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
          {/* Left: View Preset Switcher */}
          <div className="flex items-center space-x-1 bg-slate-900/90 backdrop-blur-md border border-gold/30 rounded-xl p-1 pointer-events-auto shadow-card">
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
                onClick={() => switchPreset(item.key)}
                className={`px-2.5 py-1 rounded-lg text-xs font-serif transition-all ${
                  activePreset === item.key
                    ? 'bg-gold text-slate-950 font-bold shadow-gold-glow'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                {item.label}
              </button>
            ))}

            {/* Auto Rotate Toggle */}
            <button
              onClick={toggleAutoRotate}
              className={`p-1.5 rounded-lg text-xs transition-all border-l border-slate-800 ml-1 pl-2 ${
                isAutoRotate ? 'text-gold' : 'text-slate-400 hover:text-white'
              }`}
              title={isAutoRotate ? '暂停自由旋转' : '开启自由缓慢旋转'}
            >
              <Rotate3d className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Right: Laser Scan & Restoration Slider */}
          <div className="flex items-center space-x-3 bg-slate-900/90 backdrop-blur-md border border-gold/30 rounded-xl px-3 py-1.5 pointer-events-auto shadow-card">
            {/* Laser Scan Toggle */}
            <button
              onClick={() => setIsLaserScanning(!isLaserScanning)}
              className={`flex items-center space-x-1.5 text-xs font-serif px-2.5 py-1 rounded-lg border transition-all ${
                isLaserScanning
                  ? 'bg-gold/20 border-gold text-gold-light shadow-gold-glow'
                  : 'bg-slate-800/60 border-slate-700 text-slate-400'
              }`}
            >
              <Scan className="w-3.5 h-3.5" />
              <span>激光扫描: {isLaserScanning ? '开' : '关'}</span>
            </button>

            {/* Restoration Blend Slider */}
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-slate-400 font-serif text-[11px]">退化原拓</span>
              <input
                type="range"
                min="0"
                max="1"
                step="0.02"
                value={restorationRatio}
                onChange={(e) => handleRestorationChange(parseFloat(e.target.value))}
                className="w-24 accent-[#D4AF37] cursor-pointer h-1.5 bg-slate-700 rounded-lg"
                title={`修复对比混合度: ${(restorationRatio * 100).toFixed(0)}%`}
              />
              <span className="text-gold-light font-serif text-[11px]">频空域修复</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
