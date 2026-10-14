/**
 * 墨韵智考 - 金石碑刻高精度三维模型构建引擎 (Three.js)
 * 严格按照参考三视图与规制：
 * 1. SteleCrown: 圆拱形双龙盘顶高浮雕碑首 + 摩尼宝珠 + 祥云浪花
 * 2. SteleBody: 真实 0.24m 厚度深古青石碑身 + 回字雷纹装饰框 + 背部凿斧纹理
 * 3. StelePedestal: 三阶须弥座 (宽厚承重台 + 卷草回纹腰台 + 仰莲瓣承托层)
 * 4. InscriptionPanel: 内凹碑文面，支持动态激光扫描与前后修复材质混合
 * 5. 3D Local Hotspots: 绑定于碑面的局部三维热点，绝不产生屏幕漂移
 */

import * as THREE from 'three';
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
  hotspotMeshes: { core: THREE.Mesh; ring: THREE.Mesh; data: HotspotData }[];
  updateScan: (scanY: number, intensity: number) => void;
  setMixRatio: (ratio: number) => void;
  dispose: () => void;
}

export function buildSteleModel(
  textureLoader: THREE.TextureLoader,
  customRubbingUrl?: string
): SteleModelInstance {
  const group = new THREE.Group();
  const materials: THREE.Material[] = [];
  const textures: THREE.Texture[] = [];
  const hotspotMeshes: { core: THREE.Mesh; ring: THREE.Mesh; data: HotspotData }[] = [];

  // 1. 加载生成的 PBR 贴图套件
  const loadTex = (path: string, srgb = true, repeatX = 1, repeatY = 1): THREE.Texture => {
    const tex = textureLoader.load(path);
    if (srgb) tex.colorSpace = THREE.SRGBColorSpace;
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(repeatX, repeatY);
    textures.push(tex);
    return tex;
  };

  const crownDiff = loadTex('/assets/stele/model3d/crown_diffuse.png', true);
  const crownNorm = loadTex('/assets/stele/model3d/crown_normal.png', false);
  const crownRough = loadTex('/assets/stele/model3d/crown_roughness.png', false);

  const bodyDiff = loadTex('/assets/stele/model3d/body_diffuse.png', true);
  const bodyNorm = loadTex('/assets/stele/model3d/body_normal.png', false);
  const bodyRough = loadTex('/assets/stele/model3d/body_roughness.png', false);

  const pedDiff = loadTex('/assets/stele/model3d/pedestal_diffuse.png', true);
  const pedNorm = loadTex('/assets/stele/model3d/pedestal_normal.png', false);
  const pedRough = loadTex('/assets/stele/model3d/pedestal_roughness.png', false);

  const stoneSideDiff = loadTex('/assets/stele/model3d/stone_side_diffuse.png', true, 1, 2);
  const stoneSideNorm = loadTex('/assets/stele/model3d/stone_side_normal.png', false, 1, 2);

  const stoneSeamlessDiff = loadTex('/assets/stele/model3d/stone_seamless_diffuse.png', true, 2, 2);
  const stoneSeamlessNorm = loadTex('/assets/stele/model3d/stone_seamless_normal.png', false, 2, 2);
  const stoneSeamlessRough = loadTex('/assets/stele/model3d/stone_seamless_roughness.png', false, 2, 2);

  // 2. 基础石材材质 (明朗质感的唐代青石/灰岩，纹理真实丰富)
  const baseStoneMaterial = new THREE.MeshStandardMaterial({
    color: 0x6e7782, // 真实青石灰度
    map: stoneSeamlessDiff,
    normalMap: stoneSeamlessNorm,
    normalScale: new THREE.Vector2(2.2, 2.2),
    roughnessMap: stoneSeamlessRough,
    roughness: 0.85,
    metalness: 0.02,
  });
  materials.push(baseStoneMaterial);

  const sideStoneMaterial = new THREE.MeshStandardMaterial({
    color: 0x626b75,
    map: stoneSideDiff,
    normalMap: stoneSideNorm,
    normalScale: new THREE.Vector2(2.5, 2.5),
    roughness: 0.88,
    metalness: 0.02,
  });
  materials.push(sideStoneMaterial);

  // =========================================================================
  // 3. 构建三阶须弥座 (StelePedestal)
  // =========================================================================
  const pedCfg = STELE_DIMENSIONS.pedestal;
  const pedestalGroup = new THREE.Group();
  group.add(pedestalGroup);

  // --- Tier 1: 底层承重台基 (1.85m x 0.18m x 0.72m) ---
  const t1Geo = new THREE.BoxGeometry(
    pedCfg.tier1.width,
    pedCfg.tier1.height,
    pedCfg.tier1.depth,
    8, 2, 6
  );
  const t1Mat = new THREE.MeshStandardMaterial({
    color: 0x7c848d,
    map: pedDiff,
    normalMap: pedNorm,
    normalScale: new THREE.Vector2(1.8, 1.8),
    roughness: 0.90,
    metalness: 0.01,
  });
  materials.push(t1Mat);
  const t1Mesh = new THREE.Mesh(t1Geo, t1Mat);
  t1Mesh.position.set(0, pedCfg.tier1.yPos, 0);
  t1Mesh.castShadow = true;
  t1Mesh.receiveShadow = true;
  pedestalGroup.add(t1Mesh);

  // --- Tier 2: 中层卷草回纹基台 (1.68m x 0.18m x 0.60m) ---
  const t2Geo = new THREE.BoxGeometry(
    pedCfg.tier2.width,
    pedCfg.tier2.height,
    pedCfg.tier2.depth,
    6, 2, 4
  );
  const t2Mat = new THREE.MeshStandardMaterial({
    color: 0x828b94,
    map: pedDiff,
    normalMap: pedNorm,
    normalScale: new THREE.Vector2(2.2, 2.2),
    roughnessMap: pedRough,
    roughness: 0.85,
    metalness: 0.02,
  });
  materials.push(t2Mat);
  const t2Mesh = new THREE.Mesh(t2Geo, t2Mat);
  t2Mesh.position.set(0, pedCfg.tier2.yPos, 0);
  t2Mesh.castShadow = true;
  t2Mesh.receiveShadow = true;
  pedestalGroup.add(t2Mesh);

  // --- Tier 3: 上层仰莲瓣形承台 (1.48m x 0.19m x 0.46m) ---
  const t3Geo = new THREE.BoxGeometry(
    pedCfg.tier3.width,
    pedCfg.tier3.height,
    pedCfg.tier3.depth,
    8, 3, 4
  );
  const t3Mat = new THREE.MeshStandardMaterial({
    color: 0x8a939d,
    map: pedDiff,
    normalMap: pedNorm,
    normalScale: new THREE.Vector2(2.5, 2.5),
    roughnessMap: pedRough,
    roughness: 0.82,
    metalness: 0.02,
  });
  materials.push(t3Mat);
  const t3Mesh = new THREE.Mesh(t3Geo, t3Mat);
  t3Mesh.position.set(0, pedCfg.tier3.yPos, 0);
  t3Mesh.castShadow = true;
  t3Mesh.receiveShadow = true;
  pedestalGroup.add(t3Mesh);

  // 实体雕塑莲瓣环绕装饰条 (在 Tier 3 四周建立真实几何起伏)
  const petalCountX = 14;
  const petalGeo = new THREE.CylinderGeometry(0.048, 0.02, 0.16, 12, 1, false, 0, Math.PI);
  const petalMat = new THREE.MeshStandardMaterial({
    color: 0x939da8,
    roughness: 0.78,
    metalness: 0.02,
    normalMap: pedNorm,
  });
  materials.push(petalMat);

  // 前后莲瓣
  for (let i = 0; i < petalCountX; i++) {
    const x = -pedCfg.tier3.width / 2 + 0.06 + (i * (pedCfg.tier3.width - 0.12)) / (petalCountX - 1);
    
    // Front Petal
    const pFront = new THREE.Mesh(petalGeo, petalMat);
    pFront.position.set(x, pedCfg.tier3.yPos + 0.01, pedCfg.tier3.depth / 2 + 0.015);
    pFront.rotation.x = Math.PI / 2;
    pedestalGroup.add(pFront);

    // Back Petal
    const pBack = new THREE.Mesh(petalGeo, petalMat);
    pBack.position.set(x, pedCfg.tier3.yPos + 0.01, -pedCfg.tier3.depth / 2 - 0.015);
    pBack.rotation.x = -Math.PI / 2;
    pedestalGroup.add(pBack);
  }

  // =========================================================================
  // 4. 构建碑身主体 (SteleBody) - 真实 0.24m 厚度
  // =========================================================================
  const bodyCfg = STELE_DIMENSIONS.body;
  const bodyGroup = new THREE.Group();
  group.add(bodyGroup);

  // 碑身实体长方体 (带 6 面材质映射)
  const bodyGeo = new THREE.BoxGeometry(bodyCfg.width, bodyCfg.height, bodyCfg.depth, 6, 8, 4);

  const bodyFrontMat = new THREE.MeshStandardMaterial({
    color: 0x7c858e,
    map: bodyDiff,
    normalMap: bodyNorm,
    normalScale: new THREE.Vector2(2.0, 2.0),
    roughnessMap: bodyRough,
    roughness: 0.85,
    metalness: 0.01,
  });
  materials.push(bodyFrontMat);

  const bodyMaterials: THREE.Material[] = [
    sideStoneMaterial, // +X (右侧面)
    sideStoneMaterial, // -X (左侧面)
    baseStoneMaterial, // +Y (顶部与碑首连接)
    baseStoneMaterial, // -Y (底部插入底座)
    bodyFrontMat,      // +Z (正面带碑文与回纹)
    baseStoneMaterial, // -Z (背部自然风化青石)
  ];

  const bodyMesh = new THREE.Mesh(bodyGeo, bodyMaterials);
  bodyMesh.position.set(0, bodyCfg.yPos, 0);
  bodyMesh.castShadow = true;
  bodyMesh.receiveShadow = true;
  bodyGroup.add(bodyMesh);

  // 碑身正面凸起的回字雷纹立体装饰框 (立体浮雕几何)
  const borderThick = bodyCfg.borderThickness;
  const bw = bodyCfg.borderWidth;
  const frameMat = new THREE.MeshStandardMaterial({
    color: 0x8a949e,
    map: bodyDiff,
    normalMap: bodyNorm,
    normalScale: new THREE.Vector2(2.5, 2.5),
    roughness: 0.80,
  });
  materials.push(frameMat);

  // 左边框
  const leftBorder = new THREE.Mesh(
    new THREE.BoxGeometry(bw, bodyCfg.height, borderThick),
    frameMat
  );
  leftBorder.position.set(-bodyCfg.width / 2 + bw / 2, bodyCfg.yPos, bodyCfg.depth / 2 + borderThick / 2);
  bodyGroup.add(leftBorder);

  // 右边框
  const rightBorder = new THREE.Mesh(
    new THREE.BoxGeometry(bw, bodyCfg.height, borderThick),
    frameMat
  );
  rightBorder.position.set(bodyCfg.width / 2 - bw / 2, bodyCfg.yPos, bodyCfg.depth / 2 + borderThick / 2);
  bodyGroup.add(rightBorder);

  // 底部边框
  const bottomBorder = new THREE.Mesh(
    new THREE.BoxGeometry(bodyCfg.width, bw, borderThick),
    frameMat
  );
  bottomBorder.position.set(0, bodyCfg.yPos - bodyCfg.height / 2 + bw / 2, bodyCfg.depth / 2 + borderThick / 2);
  bodyGroup.add(bottomBorder);

  // =========================================================================
  // 5. 构建圆拱形双龙浮雕碑首 (SteleCrown)
  // =========================================================================
  const crownCfg = STELE_DIMENSIONS.crown;
  const crownGroup = new THREE.Group();
  group.add(crownGroup);

  // 拱形主体：半圆柱挤出几何体 (拱径 1.28m, 厚度 0.24m)
  const crownShape = new THREE.Shape();
  crownShape.moveTo(-crownCfg.archRadius, 0);
  crownShape.absarc(0, 0, crownCfg.archRadius, Math.PI, 0, true);
  crownShape.lineTo(crownCfg.archRadius, 0);
  crownShape.lineTo(-crownCfg.archRadius, 0);

  const crownExtrudeSettings: THREE.ExtrudeGeometryOptions = {
    depth: crownCfg.depth,
    bevelEnabled: true,
    bevelSegments: 4,
    steps: 1,
    bevelSize: 0.02,
    bevelThickness: 0.02,
    curveSegments: 32,
  };

  const crownGeo = new THREE.ExtrudeGeometry(crownShape, crownExtrudeSettings);
  // 修正 Extrude 中心点 (Extrude 从 Z=0 向 +Z 挤出)
  crownGeo.center();

  const crownMat = new THREE.MeshStandardMaterial({
    color: 0x8e97a1,
    map: crownDiff,
    normalMap: crownNorm,
    normalScale: new THREE.Vector2(3.0, 3.0),
    roughnessMap: crownRough,
    roughness: 0.80,
    metalness: 0.03,
  });
  materials.push(crownMat);

  const crownMesh = new THREE.Mesh(crownGeo, crownMat);
  crownMesh.position.set(0, crownCfg.yPos + crownCfg.archRadius * 0.45, 0);
  crownMesh.castShadow = true;
  crownMesh.receiveShadow = true;
  crownGroup.add(crownMesh);

  // 中央摩尼宝珠高浮雕 (圆形凸起球冠)
  const orbGeo = new THREE.SphereGeometry(crownCfg.centerOrbRadius, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2);
  const orbMat = new THREE.MeshStandardMaterial({
    color: 0xa8b2bd,
    roughness: 0.65,
    metalness: 0.08,
    bumpMap: crownNorm,
    bumpScale: 0.02,
  });
  materials.push(orbMat);

  // 正面宝珠
  const orbMeshFront = new THREE.Mesh(orbGeo, orbMat);
  orbMeshFront.position.set(crownCfg.orbPosition.x, crownCfg.orbPosition.y, crownCfg.depth / 2 + 0.02);
  orbMeshFront.rotation.x = Math.PI / 2;
  crownGroup.add(orbMeshFront);

  // 背面宝珠
  const orbMeshBack = new THREE.Mesh(orbGeo, orbMat);
  orbMeshBack.position.set(crownCfg.orbPosition.x, crownCfg.orbPosition.y, -crownCfg.depth / 2 - 0.02);
  orbMeshBack.rotation.x = -Math.PI / 2;
  crownGroup.add(orbMeshBack);

  // =========================================================================
  // 6. 构建内凹碑文雕刻面板 (InscriptionPanel & Shader)
  // =========================================================================
  const panelCfg = STELE_DIMENSIONS.panel;

  // 载入真实碑拓对比贴图
  const damagedRubbing = customRubbingUrl
    ? loadTex(customRubbingUrl, true)
    : loadTex('/assets/stele/rubbings/stele_tang_duobao_damaged.png', true);

  const cleanRubbing = loadTex('/assets/stele/rubbings/stele_tang_duobao_clean.png', true);

  // 编写高精度碑文微痕渲染 Shader (支持激光扫描带光晕 + 修复混合)
  const inscriptionShaderMaterial = new THREE.ShaderMaterial({
    uniforms: {
      uDamagedTex: { value: damagedRubbing },
      uRestoredTex: { value: cleanRubbing },
      uBodyDiff: { value: bodyDiff },
      uBodyNorm: { value: bodyNorm },
      uMixRatio: { value: 0.0 }, // 0.0 = 原始受损, 1.0 = 修复后
      uScanY: { value: 0.5 },    // 扫描在碑文面板中的归一化 Y (0.0 ~ 1.0)
      uScanActive: { value: 1.0 },
      uLaserColor: { value: new THREE.Color(0xd4af37) },
      uLaserIntensity: { value: 1.0 },
    },
    vertexShader: `
      varying vec2 vUv;
      varying vec3 vNormal;
      varying vec3 vWorldPos;

      void main() {
        vUv = uv;
        vNormal = normalize(normalMatrix * normal);
        vec4 worldP = modelMatrix * vec4(position, 1.0);
        vWorldPos = worldP.xyz;
        gl_Position = projectionMatrix * viewMatrix * worldP;
      }
    `,
    fragmentShader: `
      uniform sampler2D uDamagedTex;
      uniform sampler2D uRestoredTex;
      uniform sampler2D uBodyDiff;
      uniform sampler2D uBodyNorm;
      uniform float uMixRatio;
      uniform float uScanY;
      uniform float uScanActive;
      uniform vec3 uLaserColor;
      uniform float uLaserIntensity;

      varying vec2 vUv;
      varying vec3 vNormal;
      varying vec3 vWorldPos;

      void main() {
        // 采样原始拓片与修复拓片
        vec4 colDamaged = texture2D(uDamagedTex, vUv);
        vec4 colRestored = texture2D(uRestoredTex, vUv);
        vec4 stoneBase = texture2D(uBodyDiff, vUv);

        // 局部拓印混合：保持青石底材质感同时呈现清晰碑文字迹
        vec3 inkDamaged = mix(stoneBase.rgb * 0.75, colDamaged.rgb * 1.15, 0.85);
        vec3 inkRestored = mix(stoneBase.rgb * 0.75, colRestored.rgb * 1.15, 0.85);

        // 根据平滑混合系数过渡
        vec3 finalColor = mix(inkDamaged, inkRestored, clamp(uMixRatio, 0.0, 1.0));

        // 模拟基础 Lambert 光照让石材明暗自然
        vec3 lightDir = normalize(vec3(0.5, 0.8, 1.0));
        float diff = max(dot(vNormal, lightDir), 0.0) * 0.6 + 0.45;
        finalColor *= diff;

        // 激光扫描带 (在 uScanY 处产生泥金色柔和光带与光辉)
        if (uScanActive > 0.5) {
          float dist = abs(vUv.y - uScanY);
          float laserCore = smoothstep(0.012, 0.0, dist);
          float laserGlow = smoothstep(0.08, 0.0, dist) * 0.4;
          vec3 laserLight = uLaserColor * (laserCore * 1.6 + laserGlow) * uLaserIntensity;
          finalColor += laserLight;
        }

        gl_FragColor = vec4(finalColor, 1.0);
      }
    `,
    side: THREE.FrontSide,
  });
  materials.push(inscriptionShaderMaterial);

  // 碑文平面微嵌入碑面
  const inscriptionGeo = new THREE.PlaneGeometry(panelCfg.width, panelCfg.height, 32, 32);
  const inscriptionMesh = new THREE.Mesh(inscriptionGeo, inscriptionShaderMaterial);
  inscriptionMesh.position.set(0, panelCfg.yPos, panelCfg.zOffset);
  bodyGroup.add(inscriptionMesh);

  // =========================================================================
  // 7. 三维局部残字定位热点 (Dual-Ring 3D Breathing Hotspots)
  // 绑定于碑身局部坐标系，随石碑旋转平移完全保持精准对齐！
  // =========================================================================
  const hotspotsInfo: HotspotData[] = [
    {
      id: 'h-gan',
      title: '第2行第5字【感】',
      glyph: '感',
      desc: '心字底岩石层裂隙剥蚀严重，贝叶斯推演置信度 94.2%',
      localPos: new THREE.Vector3(0.24, 1.62, panelCfg.zOffset + 0.005),
      confidence: 0.942,
    },
    {
      id: 'h-cen',
      title: '第4行第3字【岑】',
      glyph: '岑',
      desc: '南阳岑勋署名处山冠磨灭，经骨架拓扑重构置信度 96.5%',
      localPos: new THREE.Vector3(-0.12, 1.82, panelCfg.zOffset + 0.005),
      confidence: 0.965,
    },
    {
      id: 'h-yong',
      title: '第5行第7字【湧】',
      glyph: '湧',
      desc: '多宝如来湧现空中，三点水旁被纸纹混叠剥蚀，置信度 92.8%',
      localPos: new THREE.Vector3(-0.30, 1.35, panelCfg.zOffset + 0.005),
      confidence: 0.928,
    },
  ];

  hotspotsInfo.forEach((h) => {
    // 红色内核心
    const coreGeo = new THREE.CircleGeometry(0.024, 20);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0xc83c23,
      depthTest: true,
      side: THREE.DoubleSide,
    });
    materials.push(coreMat);
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    coreMesh.position.copy(h.localPos);
    bodyGroup.add(coreMesh);

    // 泥金色外呼吸光圈
    const ringGeo = new THREE.RingGeometry(0.034, 0.046, 32);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0xd4af37,
      transparent: true,
      opacity: 0.85,
      depthTest: true,
      side: THREE.DoubleSide,
    });
    materials.push(ringMat);
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.position.copy(h.localPos);
    ringMesh.position.z += 0.002;
    bodyGroup.add(ringMesh);

    hotspotMeshes.push({ core: coreMesh, ring: ringMesh, data: h });
  });

  // 更新与生命周期控制函数
  const updateScan = (scanYNorm: number, intensity: number) => {
    inscriptionShaderMaterial.uniforms.uScanY.value = scanYNorm;
    inscriptionShaderMaterial.uniforms.uLaserIntensity.value = intensity;
  };

  const setMixRatio = (ratio: number) => {
    inscriptionShaderMaterial.uniforms.uMixRatio.value = ratio;
  };

  const dispose = () => {
    materials.forEach((m) => m.dispose());
    textures.forEach((t) => t.dispose());
  };

  return {
    group,
    materials,
    textures,
    hotspotMeshes,
    updateScan,
    setMixRatio,
    dispose,
  };
}
