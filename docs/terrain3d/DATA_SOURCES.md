# 三维地貌数据来源与合规记录

本文件只记录**实际取得并已入库**的数据，以及明确**未取得**的数据。任何未下载的产品都在“未取得”一节列明，不以推测替代。

数据入库时间：2026-10-18（Asia/Shanghai）。校验值由 `scripts/fetch_terrain_dem.py` 在真实文件上重新扫描计算。

---

## 1. 数字高程（DEM）

| 项目 | 内容 |
| --- | --- |
| 数据名称 | AWS Open Data — Terrain Tiles（Mapzen terrarium 产品线） |
| 官方地址 | https://registry.opendata.aws/terrain-tiles/ |
| 瓦片直链 | `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png` |
| 提供服务方 | Amazon Web Services Open Data Program（原始产品由 Mapzen / Tilezen 整理） |
| 编码 | Terrarium：`elevation_m = R × 256 + G + B / 256 − 32768` |
| 覆盖与分辨率 | z0–z3 全球；z4–z5 中国及周边（60°E–150°E，0°N–60°N）；z6 中国（70°E–140°E，15°N–56°N） |
| 地面分辨率 | z5 约 4.4 km/像素，z6 约 2.2 km/像素（赤道附近估算，随纬度变化） |
| 坐标系 | EPSG:3857 瓦片网格；采样经纬度为 EPSG:4326 |
| 高程基准 | 随上游产品：SRTM / GMTED2010 / 3DEP 混合，垂直基准为 EGM96 大地水准面，**不是** WGS84 椭球高 |
| 授权 | 开放数据；按提供方要求署名，见 `apps/web/public/assets/gis/terrain/ATTRIBUTION.md` |
| 署名要求 | `Mapzen / USGS 3DEP / SRTM (NASA-NGA) / GMTED2010 / NOAA ETOPO1` |
| 取得日期 | 2026-10-18 |
| 入库文件数 | 325 块 PNG（z0–z6） |
| 入库总体积 | 26.2 MB |
| 校验值 | 见 `apps/web/public/assets/gis/terrain/manifest.json` 的 `sha256`；逐块清单见 `terrain/provenance.json` |
| 处理步骤 | **无重采样、无投影变换、无高程修改**。仅按 z/x/y 原样保存，运行时按 Terrarium 公式解码为 Float32 米。 |

### 实测高程核验（开发期探针，非推断）

| 位置 | 瓦片 | 最小值 / 最大值 / 均值（m） |
| --- | --- | --- |
| 珠峰 z5 | 23/13 | -1 / 7188 / 1960 |
| 珠峰 z7（仅本地验证，未入库） | 94/53 | 81 / 8317 / 3563 |
| 珠峰 z9（仅本地验证，未入库） | 379/214 | 2192 / 8704 / 5365 |
| 塔里木 z5 | 23/12 | 790 / 6473 / 3339 |
| 成都 z5 | 25/13 | -19 / 5851 / 1032 |
| 北京 z5 | 26/12 | -108 / 2586 / 187 |
| 上海 z5 | 26/13 | -6340 / 3075 / -46 |

海底为负值，说明数据保留了真实地形而非仅陆地裁切。

### 高分辨率数据的获取方式

z7–z9 不进入普通 Git 仓库（体积、许可与可复现性原因），提供脚本按需下载：

```powershell
cd D:\RubbingMind
python scripts/fetch_terrain_dem.py --zoom 7 9 --bbox 73 17 135 54 --workers 12
```

脚本会校验 PNG 尺寸、更新 `terrain/manifest.json` 与 `provenance.json`；前端按 manifest 自动使用已存在的最高层级，缺失层级向父级回退，不会请求 404 或伪造高程。

---

## 2. 中国行政区划与国界

| 项目 | 内容 |
| --- | --- |
| 数据 | `apps/web/public/assets/gis/china-provinces.cgcs2000.geojson` |
| 上游 | 天地图行政区划（镜像仓库 `MisterChangRay/geodeparse`，MIT） |
| 上游声明审图号 | GS(2024)0650（**上游镜像的声明，不是本应用的审图证明**） |
| 坐标系 | EPSG:4490 / CGCS2000（镜像原始数据），页面显示用 EPSG:3857 |
| 要素数 | 42（34 个面 + 8 条线，含海岸线与南海断续线等线要素） |
| 取得日期 | 2026-10-14（项目既有） |
| 校验值 | `sha256 = 841622088aff1f8126cbb8f1c0c855c50bc66cbd857d24e7162426d3ff3456da` |
| 处理 | 未修改几何；仅按要素类型拆分用于三维贴地绘制 |

### 2.1 国界与海岸线（由省级面派生）

| 项目 | 内容 |
| --- | --- |
| 数据 | `apps/web/public/assets/gis/china-national-boundary.geojson` |
| 生成脚本 | `scripts/build_national_boundary.py` |
| 方法 | 对 34 个省级面做**拓扑并集**（shapely `unary_union`），只保留并集边界。内部省界在并集中消失，剩下的是真实国界 + 海岸线 + 各岛屿外环 |
| 简化 | `simplify(0.002°, preserve_topology=True)`（约 200 m，远低于 z6 的 2.2 km 采样间距），拓扑保持，不移动国界走向 |
| 规模 | 437 个环、15,472 个点、约 370 KB |
| 坐标 | 完全沿用上游 CGCS2000 坐标，未重投影、未手工描边 |
| 内容 | 含台湾岛、海南岛、南海诸岛各岛环；仅剔除跨度 < 0.02° 的极小礁环 80 个 |
| 校验 | `tests/test_terrain3d.py::test_national_boundary_is_a_dissolved_outline` 校验要素数、环数、点数与经纬度范围 |

渲染采用三层描边：暗色衬底（在高原亮面保持对比）+ 金色光晕 + 亮金主线；省界单独弱化为低透明度细线。中国版图与邻国领土在深色海面与浅色高原上都能一眼区分。

**合规状态：本应用未单独申请地图审核号。** 项目沿用既有天地图镜像数据，并把上游审图号声明如实展示在页面出处栏；不得把上游审图号当作本应用的审图证明。

## 3. 水系

| 项目 | 内容 |
| --- | --- |
| 数据 | `apps/web/public/assets/gis/rivers.geojson`（5 条 MultiLineString，577 个坐标点） |
| 来源 | Natural Earth（公有领域） |
| 处理 | 保留原始几何与标识，未做平滑或改线 |

## 4. 现代定位县区面

| 项目 | 内容 |
| --- | --- |
| 数据 | `apps/web/public/assets/gis/coordinate-regions.geojson`（6 个面） |
| 用途 | 仅表示“位置约略 / 区域索引”的行政范围，不表示考古精确点 |

---

## 5. 未取得的数据（明确记录）

| 数据 | 原因 | 影响 |
| --- | --- | --- |
| Copernicus DEM GLO-30 / GLO-90 | 需要 Copernicus Data Space 账号与下载配额，本次未注册取得 | 全国概览分辨率停留在 z5/z6（4.4 km / 2.2 km），未达到 GLO-30 的 30 m |
| USGS EarthExplorer / NASA Earthdata 原生产品 | 同样需要账号，且单幅数据体积远超普通仓库 | 未使用；改用以 SRTM/GMTED 为源、无需密钥的 Terrarium 瓦片 |
| 自然资源部标准地图服务（bzdt.ch.mnr.gov.cn）标准图幅 | 需人工申请审图与下载授权 | 未使用；国界表达沿用天地图镜像，审图状态见上 |
| 天地图官方 API 底图 | 需要 `tk` 密钥 | 未使用；不使用密钥也保证项目可启动 |
| 高精度全国 30 m DEM | 体积与许可 | 不入库；通过脚本按需获取 |

---

## 6. 免责与表达约定

- 三维地形只由上述 DEM 高程驱动，**不存在随机噪声、AI 生成山体或图像贴图伪造**。
- 垂直夸张是独立显示参数（`autoExaggeration` / 用户倍数），只缩放显示高度，不写入高程数组。
- 行政边界与国界来自独立矢量数据，**不从未经核验的高程派生政治边界**。
- 海域仅为按 DEM 负值判定的平坦海面，不表示领海基线或任何法律主张。
