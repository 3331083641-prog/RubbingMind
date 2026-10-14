import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

interface HeroSteleSceneProps {
  onHotspotClick?: (point: { title: string; desc: string }) => void;
  className?: string;
}

export const HeroSteleScene: React.FC<HeroSteleSceneProps> = ({ onHotspotClick, className = '' }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeAnnotation, setActiveAnnotation] = useState<{ title: string; desc: string; x: number; y: number } | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let animationFrameId: number;
    const width = container.clientWidth || 600;
    const height = container.clientHeight || 500;

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x0a0d12, 0.04);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0.5, 6.2);

    // 2. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // 3. Lighting
    const ambientLight = new THREE.AmbientLight(0xd4af37, 0.35);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xf5d46e, 1.8);
    keyLight.position.set(4, 5, 5);
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0x3e8e7e, 1.2);
    rimLight.position.set(-4, 3, -3);
    scene.add(rimLight);

    const scanPointLight = new THREE.PointLight(0xf5d46e, 2.5, 3.5);
    scene.add(scanPointLight);

    // 4. Stele Geometry & Procedural Stone Material
    // Generate procedural stone normal/noise texture using canvas
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d')!;
    ctx.fillStyle = '#181f26';
    ctx.fillRect(0, 0, 512, 1024);

    // Add noise grain & micro-cracks
    for (let i = 0; i < 45000; i++) {
      const x = Math.random() * 512;
      const y = Math.random() * 1024;
      const gray = Math.floor(Math.random() * 60) + 20;
      ctx.fillStyle = `rgb(${gray},${gray + 4},${gray + 8})`;
      ctx.fillRect(x, y, 1, 1);
    }
    // Subtle stele boundary inscriptions line
    ctx.strokeStyle = 'rgba(212, 175, 55, 0.35)';
    ctx.lineWidth = 2;
    ctx.strokeRect(32, 48, 448, 928);
    ctx.strokeRect(40, 56, 432, 912);

    // Faux Chinese character grid lines
    ctx.strokeStyle = 'rgba(212, 175, 55, 0.08)';
    ctx.lineWidth = 1;
    for (let c = 1; c < 8; c++) {
      ctx.beginPath();
      ctx.moveTo(40 + c * 54, 56);
      ctx.lineTo(40 + c * 54, 968);
      ctx.stroke();
    }
    for (let r = 1; r < 20; r++) {
      ctx.beginPath();
      ctx.moveTo(40, 56 + r * 45.6);
      ctx.lineTo(472, 56 + r * 45.6);
      ctx.stroke();
    }

    const stoneTexture = new THREE.CanvasTexture(canvas);
    stoneTexture.wrapS = THREE.RepeatWrapping;
    stoneTexture.wrapT = THREE.RepeatWrapping;

    // Stele Group
    const steleGroup = new THREE.Group();
    scene.add(steleGroup);

    // Stele Slab (Main Body)
    const steleGeometry = new THREE.BoxGeometry(2.1, 3.8, 0.32, 16, 32, 4);
    const steleMaterial = new THREE.MeshStandardMaterial({
      map: stoneTexture,
      roughness: 0.78,
      metalness: 0.22,
      color: 0x222a30,
    });
    const steleMesh = new THREE.Mesh(steleGeometry, steleMaterial);
    steleMesh.position.y = 0.2;
    steleGroup.add(steleMesh);

    // Stele Top (Forehead / 碑额 rounded arch)
    const topGeometry = new THREE.CylinderGeometry(1.05, 1.05, 0.32, 32, 1, false, 0, Math.PI);
    const topMesh = new THREE.Mesh(topGeometry, steleMaterial);
    topMesh.rotation.z = Math.PI / 2;
    topMesh.rotation.y = Math.PI / 2;
    topMesh.position.set(0, 2.1, 0);
    steleGroup.add(topMesh);

    // Stele Base (Pedestal / 趺座)
    const baseGeometry = new THREE.BoxGeometry(2.6, 0.45, 1.1);
    const baseMaterial = new THREE.MeshStandardMaterial({
      color: 0x141a20,
      roughness: 0.85,
      metalness: 0.15,
    });
    const baseMesh = new THREE.Mesh(baseGeometry, baseMaterial);
    baseMesh.position.y = -1.9;
    steleGroup.add(baseMesh);

    // 5. Golden Laser Scanning Plane
    const scanGeo = new THREE.PlaneGeometry(2.4, 0.08);
    const scanMat = new THREE.MeshBasicMaterial({
      color: 0xf5d46e,
      transparent: true,
      opacity: 0.85,
      side: THREE.DoubleSide,
    });
    const scanMesh = new THREE.Mesh(scanGeo, scanMat);
    scanMesh.position.z = 0.18;
    steleGroup.add(scanMesh);

    // Laser Light Sheet Beam
    const beamGeo = new THREE.PlaneGeometry(2.4, 0.6);
    const beamMat = new THREE.MeshBasicMaterial({
      color: 0xd4af37,
      transparent: true,
      opacity: 0.22,
      side: THREE.DoubleSide,
    });
    const beamMesh = new THREE.Mesh(beamGeo, beamMat);
    beamMesh.position.z = 0.17;
    steleGroup.add(beamMesh);

    // 6. Dual-Ring Breathing Hotspots
    const hotspotData = [
      { id: 'h1', pos: new THREE.Vector3(-0.45, 0.85, 0.18), title: '天宝纪年篆额区', desc: '碑首六字篆额《大唐多宝佛塔感应碑》，双龙盘顶螭首深浮雕。' },
      { id: 'h2', pos: new THREE.Vector3(0.35, 0.1, 0.18), title: '【感】字残损漫漶区', desc: '心字底岩石层裂隙剥蚀，经频域高斯陷波与非局部均值成功提取隐痕。' },
      { id: 'h3', pos: new THREE.Vector3(-0.25, -0.7, 0.18), title: '【岑勋】撰文署名处', desc: '石花微粒与拓布纸纹混叠，骨架拓扑分析重构岑字横折山形。' }
    ];

    const hotspotMeshes: { outerRing: THREE.Mesh; innerCore: THREE.Mesh; data: typeof hotspotData[0] }[] = [];

    hotspotData.forEach((h) => {
      // Inner solid core
      const coreGeo = new THREE.CircleGeometry(0.045, 24);
      const coreMat = new THREE.MeshBasicMaterial({ color: 0xc83c23, side: THREE.DoubleSide });
      const coreMesh = new THREE.Mesh(coreGeo, coreMat);
      coreMesh.position.copy(h.pos);
      steleGroup.add(coreMesh);

      // Outer breathing ring
      const ringGeo = new THREE.RingGeometry(0.065, 0.085, 32);
      const ringMat = new THREE.MeshBasicMaterial({ color: 0xd4af37, transparent: true, opacity: 0.8, side: THREE.DoubleSide });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.position.copy(h.pos);
      ringMesh.position.z += 0.005;
      steleGroup.add(ringMesh);

      hotspotMeshes.push({ innerCore: coreMesh, outerRing: ringMesh, data: h });
    });

    // 7. Mouse Parallax Interaction
    let mouseX = 0;
    let mouseY = 0;
    let targetRotationX = 0;
    let targetRotationY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      mouseX = x;
      mouseY = y;
      targetRotationY = x * 0.45;
      targetRotationX = -y * 0.25;
    };

    container.addEventListener('mousemove', handleMouseMove);

    // 8. Raycaster for Hotspot Clicking
    const raycaster = new THREE.Raycaster();
    const mouseVec = new THREE.Vector2();

    const handleClick = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      mouseVec.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouseVec.y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);

      raycaster.setFromCamera(mouseVec, camera);
      const intersects = raycaster.intersectObjects(hotspotMeshes.map(h => h.innerCore));

      if (intersects.length > 0) {
        const clicked = hotspotMeshes.find(h => h.innerCore === intersects[0].object);
        if (clicked) {
          setActiveAnnotation({
            title: clicked.data.title,
            desc: clicked.data.desc,
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
          });
          if (onHotspotClick) {
            onHotspotClick(clicked.data);
          }
        }
      } else {
        setActiveAnnotation(null);
      }
    };

    container.addEventListener('click', handleClick);

    // 9. Resize Handling
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    // 10. Animation Loop
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Smooth Parallax Lerp
      steleGroup.rotation.y += (targetRotationY - steleGroup.rotation.y) * 0.05;
      steleGroup.rotation.x += (targetRotationX - steleGroup.rotation.x) * 0.05;

      // Laser scanning line translation
      const scanY = Math.sin(elapsedTime * 1.6) * 1.6 + 0.2;
      scanMesh.position.y = scanY;
      beamMesh.position.y = scanY - 0.28;
      scanPointLight.position.set(0, scanY, 0.6);

      // Hotspots breathing pulsing
      hotspotMeshes.forEach((h, idx) => {
        const scale = 1 + Math.sin(elapsedTime * 3 + idx) * 0.28;
        h.outerRing.scale.set(scale, scale, scale);
        (h.outerRing.material as THREE.MeshBasicMaterial).opacity = 0.5 + Math.cos(elapsedTime * 3 + idx) * 0.35;
      });

      renderer.render(scene, camera);
    };

    animate();

    // Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      container.removeEventListener('mousemove', handleMouseMove);
      container.removeEventListener('click', handleClick);

      // Dispose three.js resources
      steleGeometry.dispose();
      topGeometry.dispose();
      baseGeometry.dispose();
      scanGeo.dispose();
      beamGeo.dispose();
      stoneTexture.dispose();
      steleMaterial.dispose();
      baseMaterial.dispose();
      scanMat.dispose();
      beamMat.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div className={`relative w-full h-full min-h-[460px] overflow-hidden select-none cursor-grab active:cursor-grabbing ${className}`}>
      <div ref={containerRef} className="w-full h-full" />

      {/* Floating 3D Control Hints */}
      <div className="absolute top-4 left-4 pointer-events-none z-10 flex items-center space-x-2 bg-xuan-panel/80 px-3 py-1.5 rounded-full border border-gold/30 text-xs text-slate-300 backdrop-blur-md">
        <span className="w-2 h-2 rounded-full bg-gold animate-ping" />
        <span>Three.js 碑石数字孪生 · 支持鼠标视差交互与热点触控</span>
      </div>

      {/* Hotspot Annotation Popup */}
      {activeAnnotation && (
        <div 
          className="absolute z-20 max-w-xs p-3.5 rounded-xl bg-xuan-card/95 border border-gold/60 shadow-gold-glow backdrop-blur-md text-xs animate-fadeIn pointer-events-auto"
          style={{ 
            left: Math.min(activeAnnotation.x + 12, (containerRef.current?.clientWidth || 400) - 260), 
            top: Math.max(activeAnnotation.y - 40, 20) 
          }}
        >
          <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-gold/20">
            <span className="font-semibold text-gold-light flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cinnabar" />
              {activeAnnotation.title}
            </span>
            <button 
              onClick={() => setActiveAnnotation(null)}
              className="text-slate-400 hover:text-white px-1"
            >
              ×
            </button>
          </div>
          <p className="text-slate-200 leading-relaxed font-sans">{activeAnnotation.desc}</p>
        </div>
      )}
    </div>
  );
};
