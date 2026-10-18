# 三维地貌引擎架构

## 1. 为什么是 MapLibre `CustomLayerInterface` + Three.js

候选方案：

| 方案 | 结论 | 依据 |
| --- | --- | --- |
| A. MapLibre 自定义图层内嵌 Three.js（采用） | ✅ | 相机、投影、缩放/平移/旋转、`flyTo`、`fitBounds`、比例尺、南海附图、DOM 标记全部沿用既有 MapLibre 行为；经纬度对齐由 MapLibre 的矩阵保证 |
| B. 独立 Three.js 场景（自建相机） | ✗ | 需要重写相机、交互、拾取、标注与投影，且 `HistoricalMap` 既有测试与行为会整体失效，回归风险过高 |
| C. 用 MapLibre 内置 `setTerrain` 代替真实网格 | ✗ | 只是栅格地形抬升，不满足“BufferGeometry 真实网格 + 法线 + LOD”的要求 |

方案 A 的关键验证：MapLibre v6 的 `render(gl, options)` 传入的 `options.modelViewProjectionMatrix` 映射的是**世界像素空间**（`transform._viewProjMatrix`），乘以 `worldSize = 512 × 2^zoom` 后即映射**归一化墨卡托空间**。该结论用数值方式与 `map.project()` 逐点比对，误差 < 1e-12 px（含 42° 俯仰）：见 `projection.ts` 注释与 `scripts/test_terrain_projection_browser.py`。

## 2. 坐标与高度

```
经度 → x = (lon + 180) / 360
纬度 → y = 0.5 − ln(tan(π/4 + φ/2)) / 2π
高度 → z = elevation_m × exaggeration / 40075016.68557849   （墨卡托 z 单位 = 2πR 米）
```

- 顶点位置以固定场景原点 `SCENE_ORIGIN = (105°E, 34°N)` 为基准存为相对值，避免 float32 在高缩放级别下的抖动；着色器再加回原点。
- **垂直夸张只影响 `u_heightScale` 这一个 uniform**，高程属性 `aElev` 始终是原始米值。
- 自动夸张规律：`clamp(6 × 2^(5.2 − zoom), 1, 34)`。全国视图约 ×30，街道级回到 1:1。用户可在图层面板固定倍率。

## 3. 模块

```
apps/web/src/components/graph/terrain3d/
  projection.ts     墨卡托/经纬度/矩阵换算（纯函数，可单测）
  dem.ts            manifest 读取、瓦片抓取、Web Worker 解码、双线性采样、覆盖率回退
  demWorker.ts      Terrarium PNG → Float32 米（OffscreenCanvas，离主线程）
  terrainMesh.ts    索引网格构建：位置/高程/梯度/凹度/边缘淡出 + 法线所需的平滑差分
  terrainMaterial.ts 分层设色 LUT、坡度岩石混合、方向光 + 半球光、等高线、雾
  drapedLines.ts    折线贴地：每点采样 DEM 高程，屏幕空间宽度 ribbon，虚线支持
  terrainLayer.ts   场景编排：层级 LOD、矩阵同步、构建调度、统计、资源释放
```

## 4. 地形网格与 LOD

| 层级 | 触发缩放 | 范围 | 顶点预算 | 目标 DEM 层级 |
| --- | --- | --- | --- | --- |
| 全国地貌 | < 5.4 | 62°E–148°E，0°N–58°N | 620k | z5 |
| 区域地貌 | 5.4 – 7.6 | 相机中心 ±11° | 560k | z6 |
| 局地地貌 | 7.6 – 10 | ±4.2° | 480k | z8 |
| 近景地貌 | ≥ 10 | ±1.5° | 420k | z10 |

- 全国网格常驻；区域/局地网格作为“细节补片”叠加，用 `polygonOffset` 保证细节片在重合处胜出，不会 z-fighting。
- 构建在 `moveend` 后延迟触发（160–220 ms 防抖）；构建期间旧网格继续渲染，不出现空洞。
- 网格分辨率按顶点预算与包围盒长宽比计算，保持单元近似正方形。
- 实际使用的 DEM 层级由 `DemStore.availableZoom()` 根据**磁盘上真实存在**的瓦片决定，缺失时自动降级并向父级瓦片回退，绝不请求不存在的层级。

## 5. 着色

- **高程色带**：15 段 sRGB 节点烘焙成 256×1 LUT（`TERRAIN_RAMP`），自深墨海面 → 青黛低地 → 岩石灰 → 泥金高地 → 浅色雪线。LUT 内是 sRGB 字节，着色器用 `pow(2.2)` 解码；UNIFORM 颜色由 three 传入已是线性值，**不再二次解码**（这是首轮调试中发现的真实缺陷）。
- **法线**：由网格高程的中央差分得到 `d(elev)/d(mercator)`，乘以 `u_heightScale` 得到绘制表面的真实梯度，因此夸张系数变化时光照自动同步，无需重建几何。差分前对高程做 5×5 二项式平滑（**仅用于着色导数**，绘制高度与高程值不变），消除纹理级噪点造成的砂砾感。
- **光照**：方向光（西北偏上，归一化 `(-0.55,-0.45,0.70)`）+ 半球环境光（天空 `#44606c` / 地面 `#0b1416`）+ 山脊轮廓光。
- **坡度混合**：陡坡混入岩石灰；雪线以上且坡度平缓处混入浅色。凹地由 DEM 的离散拉普拉斯（`aCurv`）压暗，形成沟谷层次。
- **等高线**：每 800 m 一条，`fwidth` 控制线宽；当等高线密度超过像素可分辨范围（全国视图下的高原）时自动淡出，避免摩尔纹。
- **雾与边缘淡出**：按到相机距离做空气透视；全国网格在包围盒边缘 12% 内淡出到页面底色，使地貌“融进墨色纸面”而不是以硬边结束。

## 6. 矢量贴地

省界、国界、水系、定位面、关联线全部转换成折线，**逐个经纬度采样同一 DEM** 得到高度，再抬高 40–120 m 避免与地表 z-fighting，最后用屏幕空间扩展的 ribbon 着色器绘制（宽度以 CSS 像素恒定，不受倾斜影响）。

由于地形网格与矢量都从同一个 `DemStore` 采样，二者严格共享同一高程面；差异仅来自网格线性插值与逐点采样之间的亚像元误差，由抬升量覆盖。

## 7. 标记与标注

`maplibregl.Marker` 只能把 DOM 放在海平面（z=0），在倾斜视角下会与地表错位。因此标记与省名改为自建 overlay：每帧用同一 `mvp` 把 `(x, y, height)` 投影到屏幕，得到**贴地**位置；2D 模式退回 `map.project()`。DOM 结构与既有 CSS/测试选择器保持一致（`.historical-marker`、`.marker-label`、`.province-label`）。

## 8. 资源与性能

- 单一 WebGL 上下文：Three.js 直接复用 MapLibre 的 `gl`，不新建 canvas（页面 canvas 数量仍为 2：主图 + 南海附图）。
- 瓦片解码在 Worker 中进行；`DemStore` 去重同一瓦片的并发请求。
- 几何/材质在层级切换与卸载时 `dispose()`；场景在组件卸载时整体释放。
- 帧率、顶点数、构建耗时、DEM 层级在页面右下角 HUD 实时显示，并写入 `data-*` 供测试读取。
