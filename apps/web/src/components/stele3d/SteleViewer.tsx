import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { STELE_DIMENSIONS } from '../../config/steleDimensions';
import { buildSteleModel, SteleModelInstance, HotspotData } from './SteleModelBuilder';
import { 
  Rotate3d, 
  Eye, 
  Maximize2, 
  Minimize2, 
  Scan, 
  Sparkles, 
  RotateCcw, 
  Layers, 
  SlidersHorizontal,
  Info,
  CheckCircle2,
  Compass
} from 'lucide-react';

interface SteleViewerProps {
  customRubbingUrl?: string;
  steleTitle?: string;
  onOpenWorkbench?: () => void;
  onToggleFullscreen?: () => void;
  isFullscreen?: boolean;
  className?: string;
  showControls?: boolean;
}

export const SteleViewer: React.FC<SteleViewerProps> = ({
  customRubbingUrl,
  steleTitle = '唐风龙纹石碑 · 三维数字展陈模型',
  onOpenWorkbench,
  onToggleFullscreen,
  isFullscreen = false,
  className = '',
  showControls = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const modelInstanceRef = useRef<SteleModelInstance | null>(null);

  // States
  const [isAutoRotate, setIsAutoRotate] = useState<boolean>(true);
  const [isLaserScanning, setIsLaserScanning] = useState<boolean>(true);
  const [restorationRatio, setRestorationRatio] = useState<number>(0.0); // 0 = damaged, 1 = restored
  const [activePreset, setActivePreset] = useState<string>('perspective');
  const [selectedHotspot, setSelectedHotspot] = useState<HotspotData | null>(null);
  const [popupPos, setPopupPos] = useState<{ x: number; y: number } | null>(null);

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

    let animFrameId: number;
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 560;

    // 1. Scene & Fog (深墨色与暖灰渐变空间)
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0c1015);
    scene.fog = new THREE.FogExp2(0x0c1015, 0.035);

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
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.32; // 充足曝光，告别死黑！
    rendererRef.current = renderer;

    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 4. OrbitControls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 1.6;
    controls.maxDistance = 8.5;
    controls.target.set(initCam.target[0], initCam.target[1], initCam.target[2]);
    controls.autoRotate = isAutoRotate;
    controls.autoRotateSpeed = 0.8;
    controlsRef.current = controls;

    // 用户交互时自动暂停旋转
    controls.addEventListener('start', () => {
      setIsAutoRotate(false);
    });

    // 5. 博物馆级专业展览布光体系 (彻底照亮石雕细节)
    // 5.1 环境全局光 (充足底光)
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
    scene.add(ambientLight);

    const hemiLight = new THREE.HemisphereLight(0xedf2f7, 0x1a222a, 0.65);
    hemiLight.position.set(0, 10, 0);
    scene.add(hemiLight);

    // 5.2 主方向光 (Key Light - 暖白偏右上方)
    const keyLight = new THREE.DirectionalLight(0xffeedd, 2.0);
    keyLight.position.set(4.5, 6.0, 5.0);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 1024;
    keyLight.shadow.mapSize.height = 1024;
    keyLight.shadow.bias = -0.0005;
    scene.add(keyLight);

    // 5.3 辅助填充光 (Fill Light - 柔和偏左前方，消除深部死阴影)
    const fillLight = new THREE.DirectionalLight(0x99ccdd, 1.1);
    fillLight.position.set(-4.5, 3.5, 4.0);
    scene.add(fillLight);

    // 5.4 背部金色轮廓光 (Rim Light - 勾勒碑首双龙飞扬剪影)
    const rimLight = new THREE.DirectionalLight(0xf5d46e, 1.8);
    rimLight.position.set(0, 5.5, -4.5);
    scene.add(rimLight);

    // 5.5 地面接触阴影与光环微光 (Ground Contact Shadow & Pedestal Glow)
    const groundGeo = new THREE.PlaneGeometry(12, 12);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x090c0f,
      roughness: 0.88,
      metalness: 0.1,
    });
    const groundMesh = new THREE.Mesh(groundGeo, groundMat);
    groundMesh.rotation.x = -Math.PI / 2;
    groundMesh.position.y = -0.005;
    groundMesh.receiveShadow = true;
    scene.add(groundMesh);

    // 地面泥金微光光圈
    const haloGeo = new THREE.RingGeometry(1.2, 2.6, 64);
    const haloMat = new THREE.MeshBasicMaterial({
      color: 0xd4af37,
      transparent: true,
      opacity: 0.08,
      side: THREE.DoubleSide,
    });
    const haloMesh = new THREE.Mesh(haloGeo, haloMat);
    haloMesh.rotation.x = -Math.PI / 2;
    haloMesh.position.y = 0.001;
    scene.add(haloMesh);

    // 6. 构建高精度三维碑刻模型实例
    const textureLoader = new THREE.TextureLoader();
    const steleInstance = buildSteleModel(textureLoader, customRubbingUrl);
    modelInstanceRef.current = steleInstance;
    scene.add(steleInstance.group);

    // 7. Raycaster 拾取 3D 局部残字热点
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const handlePointerDown = (event: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -(((event.clientY - rect.top) / rect.height) * 2 - 1);

      raycaster.setFromCamera(mouse, camera);
      const targetCores = steleInstance.hotspotMeshes.map((h) => h.core);
      const intersects = raycaster.intersectObjects(targetCores);

      if (intersects.length > 0) {
        const found = steleInstance.hotspotMeshes.find((h) => h.core === intersects[0].object);
        if (found) {
          setSelectedHotspot(found.data);
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
    };
    window.addEventListener('resize', handleResize);

    // 9. 渲染与动画循环 (60 FPS)
    const clock = new THREE.Clock();

    const animate = () => {
      animFrameId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      // 相机平滑插值到预设目标 (Tween Lerp)
      if (targetCamPos.current && targetLookAt.current) {
        camera.position.lerp(targetCamPos.current, 0.06);
        controls.target.lerp(targetLookAt.current, 0.06);
        if (camera.position.distanceTo(targetCamPos.current) < 0.02) {
          targetCamPos.current = null;
          targetLookAt.current = null;
        }
      }

      // 控制器更新
      controls.autoRotate = isAutoRotateRef.current;
      controls.update();

      // 激光扫描上下循环 (0.05 ~ 0.95 归一化 UV)
      if (isLaserScanningRef.current) {
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

      renderer.render(scene, camera);
    };

    animate();

    // 10. 资源安全清理
    return () => {
      cancelAnimationFrame(animFrameId);
      window.removeEventListener('resize', handleResize);
      renderer.domElement.removeEventListener('pointerdown', handlePointerDown);
      controls.dispose();
      steleInstance.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [customRubbingUrl]);

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

    const preset = STELE_DIMENSIONS.cameraPresets[presetKey];
    if (preset) {
      targetCamPos.current = new THREE.Vector3(preset.position[0], preset.position[1], preset.position[2]);
      targetLookAt.current = new THREE.Vector3(preset.target[0], preset.target[1], preset.target[2]);
    }
  }, []);

  // 修复混合度滑块更新
  const handleRestorationChange = (ratio: number) => {
    setRestorationRatio(ratio);
    if (modelInstanceRef.current) {
      modelInstanceRef.current.setMixRatio(ratio);
    }
  };

  return (
    <div className={`relative w-full h-full select-none overflow-hidden bg-[#0C1015] ${className}`}>
      {/* 3D WebGL Canvas Container */}
      <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Top Banner Tag */}
      <div className="absolute top-3.5 left-4 z-20 pointer-events-none flex items-center space-x-2.5">
        <div className="px-3 py-1.5 rounded-full bg-slate-900/85 border border-gold/40 text-xs font-serif text-gold-light backdrop-blur-md shadow-card flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-cinnabar animate-pulse" />
          <span className="font-semibold">{steleTitle}</span>
          <span className="text-[10px] text-slate-400 font-sans border-l border-slate-700 pl-2">
            PBR 仿古青石 · 双龙浮雕 · 仰莲须弥座
          </span>
        </div>
      </div>

      {/* Top Right Tool Action: Fullscreen */}
      {onToggleFullscreen && (
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
