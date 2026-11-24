/**
 * 墨韵智考 - 金石碑刻三维模型统一工程尺寸与空间参数配置
 * 统一坐标系:
 * - X: 左右宽度方向 (0 为碑石中心)
 * - Y: 上下高度方向 (0 为地面基底)
 * - Z: 前后深度方向 (+Z 为正面，-Z 为背面)
 */

export const STELE_DIMENSIONS = {
  // 模型总体
  totalHeight: 3.30,      // 模型总高度 (米)
  originY: 0.0,           // 基准地坪位于 Y = 0

  // 底座 (三阶须弥座)
  pedestal: {
    totalHeight: 0.55,    // 底座总高度
    tier1: {              // 下层：宽厚承重台基 (Base Plinth)
      width: 1.85,
      height: 0.18,
      depth: 0.72,
      yPos: 0.09,         // 中心 Y = 0.09 (0 ~ 0.18)
    },
    tier2: {              // 中层：卷草回纹基台 (Meander Waist)
      width: 1.68,
      height: 0.18,
      depth: 0.60,
      yPos: 0.27,         // 中心 Y = 0.27 (0.18 ~ 0.36)
    },
    tier3: {              // 上层：仰莲瓣形承台 (Lotus Tier)
      width: 1.48,
      height: 0.19,
      depth: 0.46,
      yPos: 0.455,        // 中心 Y = 0.455 (0.36 ~ 0.55)
    },
    slotDepth: 0.04,      // 碑身插入槽深
  },

  // 碑身主体 (Stele Body)
  body: {
    width: 1.28,          // 碑身外宽
    height: 2.15,         // 碑身直立段高度 (不含碑首)
    depth: 0.24,          // 碑身物理厚度 (避免纸片感)
    yPos: 1.585,          // 中心 Y，含 0.04m 插入段 (0.51 ~ 2.66)
    borderWidth: 0.08,    // 边缘回字雷纹边框宽度
    borderThickness: 0.015,// 边缘边框相对内凹字面的凸出高度
  },

  // 碑首 (Stele Crown)
  crown: {
    archRadius: 0.64,     // 圆拱半径 (外宽 1.28m 的一半)
    height: 0.64,         // 碑首总高 (拱顶最高点达 Y = 2.66 + 0.64 = 3.30m)
    depth: 0.24,          // 碑首物理厚度 (与碑身一致并稍带弧形收敛)
    yPos: 2.66,           // 拱底起始高度 Y = 2.66
    centerOrbRadius: 0.10,// 宝珠半径
    orbPosition: { x: 0, y: 3.06, z: 0.125 }, // 宝珠三维位置
  },

  // 碑文刻字凹槽面板 (Inscription Panel)
  panel: {
    width: 1.08,          // 碑文可视宽度 (1.28 - 2 * 0.10)
    height: 1.98,         // 碑文可视高度
    yPos: 1.60,           // 中心 Y
    zOffset: 0.114,       // 位于碑身表面 (闭合碑体的内凹字面，Z = 0.114)
    recessDepth: 0.006,   // 内凹深度，与闭合碑身雕刻面保持一致
  },

  // 摄像机预设位点
  cameraPresets: {
    front: { position: [0, 1.65, 4.8], target: [0, 1.65, 0], fov: 42 },
    left: { position: [-4.5, 1.65, 0], target: [0, 1.65, 0], fov: 42 },
    right: { position: [4.5, 1.65, 0], target: [0, 1.65, 0], fov: 42 },
    top: { position: [0, 6.0, 1.4], target: [0, 1.65, 0], fov: 42 },
    bottom: { position: [0, -4.0, 0.001], target: [0, 1.65, 0], fov: 42 },
    back: { position: [0, 1.65, -4.8], target: [0, 1.65, 0], fov: 42 },
    perspective: { position: [3.2, 2.35, 3.8], target: [0, 1.52, 0], fov: 42 },
    inscription: { position: [0.18, 1.72, 2.15], target: [0, 1.64, 0.12], fov: 34 },
    raking: { position: [2.45, 1.78, 2.05], target: [0, 1.62, 0.08], fov: 38 },
  }
};
