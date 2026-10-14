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
    height: 2.00,         // 碑身直立段高度 (不含碑首)
    depth: 0.24,          // 碑身物理厚度 (避免纸片感)
    yPos: 1.55,           // 中心 Y = 0.55 + 2.00/2 = 1.55 (0.55 ~ 2.55)
    borderWidth: 0.08,    // 边缘回字雷纹边框宽度
    borderThickness: 0.015,// 边缘边框相对内凹字面的凸出高度
  },

  // 碑首 (Stele Crown)
  crown: {
    archRadius: 0.64,     // 圆拱半径 (外宽 1.28m 的一半)
    height: 0.75,         // 碑首总高 (拱顶最高点达 Y = 0.55 + 2.00 + 0.75 = 3.30m)
    depth: 0.24,          // 碑首物理厚度 (与碑身一致并稍带弧形收敛)
    yPos: 2.55,           // 拱底起始高度 Y = 2.55
    centerOrbRadius: 0.10,// 宝珠半径
    orbPosition: { x: 0, y: 2.95, z: 0.125 }, // 宝珠三维位置
  },

  // 碑文刻字凹槽面板 (Inscription Panel)
  panel: {
    width: 1.08,          // 碑文可视宽度 (1.28 - 2 * 0.10)
    height: 1.65,         // 碑文可视高度
    yPos: 1.55,           // 中心 Y
    zOffset: 0.121,       // 位于碑身表面 (+0.120 + 0.001 避免 Z-fighting)
    recessDepth: 0.012,   // 内凹深度
  },

  // 六方向正交与45度透视摄像机预设标定
  cameraPresets: {
    front: { position: [0, 1.85, 4.6], target: [0, 1.85, 0], fov: 42, up: [0, 1, 0] },
    back: { position: [0, 1.85, -4.6], target: [0, 1.85, 0], fov: 42, up: [0, 1, 0] },
    left: { position: [-4.6, 1.85, 0], target: [0, 1.85, 0], fov: 42, up: [0, 1, 0] },
    right: { position: [4.6, 1.85, 0], target: [0, 1.85, 0], fov: 42, up: [0, 1, 0] },
    top: { position: [0, 6.2, 0.001], target: [0, 1.85, 0], fov: 44, up: [0, 0, -1] },
    bottom: { position: [0, -2.6, 0.001], target: [0, 0.6, 0], fov: 44, up: [0, 0, 1] },
    perspective: { position: [3.0, 2.8, 3.8], target: [0, 1.80, 0], fov: 44, up: [0, 1, 0] },
  }
};
