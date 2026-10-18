# 三维地貌重构 · 任务进度（PROGRESS）

> 本文件是跨会话恢复入口。每完成一个阶段立即更新。

## 0. 基线（开发前实测）

| 项目 | 实测结果 | 时间 |
| --- | --- | --- |
| 本地目录 | `D:\RubbingMind` 存在、可读写 | 2026-10-18 |
| Git 分支 / HEAD | `main` / `5525f01` | 2026-10-18 |
| 工作区 | 无已跟踪文件修改；仅有未跟踪的截图与工作目录 | 2026-10-18 |
| 远程 | `https://github.com/3331083641-prog/RubbingMind.git` | 2026-10-18 |
| Node / npm | v24.15.0 / 11.12.1 | 2026-10-18 |
| Python | 3.12.4（numpy 2.4.4 / Pillow 12.2.0 / opencv 5.0.0 / fastapi 0.141.1） | 2026-10-18 |
| 前端依赖 | `apps/web/node_modules` 已存在；maplibre-gl 6.14.0、three 0.163.0 | 2026-10-18 |
| 浏览器 | Microsoft Edge（Playwright `channel='msedge'`） | 2026-10-18 |
| Python 测试基线 | `python -m pytest tests -q` → **115 passed** | 2026-10-18 |
| 图形硬件 | ANGLE / NVIDIA RTX 4060 Laptop GPU / WebGL 2.0 | 2026-10-18 |

### 既有地图能力基线（修改前）

- `HistoricalMap.tsx`：单实例 MapLibre，全国 `fitBounds([[73,17],[135,54]])`，缩放 1–15，`data-ready`/`data-zoom`/`data-center` 供测试读取。
- `chinaMapStyle.ts`：背景 `#061018`；`relief` 栅格分层设色（z0–3，高饱和青绿）+ `hillshade`；省界/国界/水系/定位面/关联线共 9 个图层。
- DEM：`apps/web/public/assets/gis/terrain/{z}/{x}/{y}.png`，Mapzen Terrarium 编码，仅 z0–3（全球 85 块）。
- 山体阴影贴图：`assets/gis/relief/`，由 `scripts/build_china_relief.py` 离线生成。
- 南海诸岛：第二个 MapLibre 实例（不可交互）。
- 交互：滚轮缩放、拖拽、地点检索、单击/双击定位、图层开关、模式切换、时间轴联动。
- 浏览器回归：`scripts/test_graph_browser.py` 全绿（26 项检查，3 视口 × 4 碑）。

## 1. 阶段状态

| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| S0 基线与环境核查 | ✅ | 见上表 |
| S1 DEM 数据扩充 | ✅ | z0–z5 全球/中国+周边、z6 中国；334 块 26.8 MB；`manifest.json` + `provenance.json` |
| S2 Three.js 地形引擎 | ✅ | `CustomLayerInterface` + `BufferGeometry` + 索引网格 + Worker 解码 + 双线性采样 |
| S3 地形材质与光照 | ✅ | 分层设色 LUT、平滑梯度法线、方向光 + 半球光、坡度岩石混合、凹地压暗、等高线、空气透视 |
| S4 构图、相机与交互 | ✅ | 俯仰感知的全国取景（二分求解 + 投影重心校正），实测 69.9%–70.5% 画幅 |
| S5 矢量图层贴地 | ✅ | 省界/国界/水系/定位面/关联线逐点采样 DEM，屏幕空间 ribbon；DOM 标记按地形高度投影 |
| S6 测试与截图核验 | ✅ | `tests/test_terrain3d.py` 7 项；`scripts/test_terrain3d_browser.py` 21 项；截图 `screenshots/terrain3d-final/` |
| S7 文档、Git 提交与推送 | ⏳ | 见第 5 节 |

## 2. 已修改 / 新增文件

### 新增（前端引擎）

```
apps/web/src/components/graph/terrain3d/projection.ts      墨卡托 / 矩阵换算
apps/web/src/components/graph/terrain3d/dem.ts             manifest、瓦片抓取、Worker 解码、采样、层级回退
apps/web/src/components/graph/terrain3d/demWorker.ts       Terrarium PNG → Float32 米
apps/web/src/components/graph/terrain3d/terrainMesh.ts     索引网格 + 高程/梯度/凹度/边缘属性
apps/web/src/components/graph/terrain3d/terrainMaterial.ts 分层设色 + 光照 + 等高线着色器
apps/web/src/components/graph/terrain3d/drapedLines.ts     贴地折线 ribbon
apps/web/src/components/graph/terrain3d/terrainLayer.ts    场景编排 / LOD / 统计 / 释放
```

### 修改

```
apps/web/src/components/graph/HistoricalMap.tsx   三维图层接入、地形高度标记、俯仰感知取景、视角控件
apps/web/src/pages/GraphPage.tsx                  二维/三维切换、垂直夸张、等高线、地形 HUD
apps/web/src/pages/GraphPage.css                  标记 overlay、视角控件、HUD、图层面板样式
apps/web/src/main.tsx                             扩大 resource timing 缓冲（地形瓦片会挤掉默认 250 条）
```

### 数据与脚本

```
apps/web/public/assets/gis/terrain/**              新增 z4–z6 瓦片 + manifest.json + provenance.json
scripts/fetch_terrain_dem.py                       新增：下载 / 校验 / 生成 manifest 与 provenance
scripts/test_terrain3d_browser.py                  新增：三维地貌浏览器验收
tests/test_terrain3d.py                            新增：DEM 与色带的数据级校验
```

## 3. 已完成测试（实测）

| 测试 | 结果 |
| --- | --- |
| `python -m pytest tests -q` | 115 → **122 passed**（新增 7 项） |
| `python scripts/validate_history_gis.py` | 通过（4 碑地点均落在声明省份/区域内） |
| `python scripts/test_graph_browser.py` | **passed**，26 项检查，`browserErrors: []` |
| `python scripts/test_terrain3d_browser.py` | **passed**，21 项检查，3 视口 + 6 区域 + 交互 + 性能 |
| `npm run build`（apps/web） | 见 IMPLEMENTATION_REPORT |

### 实测关键数值

- 全国画幅占比：1920 视口 **69.9%**、1440 **70.5%**、1366 **70.4%**（要求 65%–80%）。
- 运行时高程（引擎自身 DEM 采样）：珠峰 6835 m、拉萨 3687 m、塔里木 1059 m、四川盆地 352 m、华北平原 71 m、黄海 0 m（海面）。
- 全国网格：620,964 顶点 / 1,238,770 三角面；局部层级合计约 98 万顶点。
- 网格构建耗时：约 84–186 ms（主线程，moveend 防抖后）。
- 交互帧率：**159 FPS**（1920×1080，1.5 s 内 240 帧，含拖拽与缩放）。

## 4. 剩余问题 / 风险

1. **审图合规**：未单独申请地图审图号；沿用天地图镜像（上游声明 GS(2024)0650）。已在页面出处栏与数据文档中明确声明。
2. **高分辨率 DEM 未入库**：z7–z9 需运行抓取脚本；未取时局部层级会自动降级到 z6，地形变平滑但不伪造。
3. **Copernicus DEM 未取得**：需账号，已在 `DATA_SOURCES.md` 记录为“未取得”。
4. **二维模式实现变更**：现与三维共用同一引擎（平面晕渲），MapLibre 样式图层仅作无 WebGL 回退；`chinaMapStyle` 中的 `relief` 栅格仍在仓库中作为回退资源。
5. **南海诸岛附图**仍为独立二维 MapLibre 实例（小尺寸定位图，不参与三维渲染）。
6. **海拔垂直基准**为上游 EGM96 大地水准面，非 WGS84 椭球高。

## 5. 交付状态（2026-10-18 完成）

| 项目 | 结果 |
| --- | --- |
| 本地目录 | `D:\RubbingMind`（正式成果，未迁移） |
| 功能分支 | `feature/threejs-real-terrain`（已推送） |
| 分支提交 | `f774951` feat(terrain3d) 主体；`4791e98` fix(terrain3d) 渲染失败保护 |
| 合并到 main | `2312638` Merge branch 'feature/threejs-real-terrain' |
| 远程 main | `2312638de83ef061c7a2b5322ca80a00f40c66d2`（与本地一致） |
| GitHub Actions | run 39140085182：4/4 成功（Backend / Frontend / Repository Validation / Browser smoke） |
| 仓库可见性 | Private |
| 浏览器验收 | `test_terrain3d_browser.py` 通过（20 项）；`test_graph_browser.py` 通过（26 项） |
| 未入库内容 | `screenshots/terrain3d-dev/`（开发期临时图，已写入 .gitignore）、z7–z9 DEM |

### 后续可做（非本次范围）

1. 申请地图审图号并替换为官方标准版图。
2. 取得 Copernicus GLO-30 或同等级 30 m DEM 后，把近景层级提升到 z10–z12。
3. 低端 GPU 的降级策略与实测。
4. 地形遮挡标记（当前 DOM 标记始终在最上层）。
