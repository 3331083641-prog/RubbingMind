# 墨韵智考 RubbingMind

金石碑拓数字典藏、图像处理与史料辅助检索的本地 Web 项目。系统包含 React/TypeScript 前端、FastAPI 后端、OpenCV 图像处理、四件核心演示样本、28 件第三轮审核馆藏、三维展陈和历史 GIS。

## 真实馆藏与授权

第三轮审核的 28 件真实影像已经入库，东汉、北魏、唐、宋、元、明、清各 4 件。标准数据位于 [data/catalog/steles28.json](data/catalog/steles28.json)；每件的封面、阅读图、档案图分开保存，名称、原刻年代、拓本年代、馆藏机构及编号按审核记录对应。旧 5 件记录独立归档，不作为新文物身份。四件核心算法样本与 28 件馆藏使用独立 ID。查看 [馆藏影像来源与许可](docs/museum-image-sources.md) 和 [入库说明](docs/museum-v3-integration.md)。各图像许可按逐件记录标示；文物本身与数字图像授权需分别判断。

## 现有功能与实验边界

- 工作台默认使用输入图像驱动的自适应处理：分析频谱、残差与字口风险，选择陷波、孤立噪点处理、NLM或保留原图，并记录保真门控原因。固定高斯/Butterworth、形态学、CLAHE流程保留为对照。每次处理保存独立运行ID、参数、输入/输出哈希、工作副本缩放和随机种子。
- 上传 PNG/JPEG 后，服务端验证并保存原件、生成唯一记录；上传属于用户私有数据，不进入 28 件权威馆藏。上传失败会显示错误，不生成假记录。
- 残字选区可查看前景、噪点、连通区域和真实二值骨架；可将人工确认的参考字形加入本地轮廓距离/投影检索库。可选视觉模型由用户自行配置；未配置或不可用时明确显示有限的模板/上下文建议或无候选。采纳、驳回、撤销均保存；没有独立人工标注集，不报告古碑识字准确率。
- 报告按当前文物及所选运行 ID 展示实际处理、出处和推演状态，支持 JSON 与浏览器打印 PDF。没有运行时显示“尚未执行”；没有配对真值时 PSNR、SSIM 为“未评测”。
- 图谱的“史料智能检索”使用本地SQLite FTS5/BM25、实体识别和有来源的一跳关系扩展，28件馆藏与四核心均可查询；答案为证据摘录，不调用模型补写未知历史。原石/原刻载体、拓本和藏所分开建档。已有核验地点可联动原GIS，不生成无据路线。地图公开使用与审图事项见 [历史图谱审计](docs/graph-history-audit.md)，尚未取得本应用正式审图许可。

## 三维真实地貌（时空图谱中心）

地图默认以三维形态打开：**真实 DEM + Three.js 网格 + MapLibre 投影**，而不是给二维底图叠加山体阴影。

- 高程来自 AWS Open Data Terrain Tiles（Mapzen terrarium，无需密钥），仓库内置 z0–z6（334 块、26.8 MB）；全国概览 z5 ≈ 4.4 km、区域 z6 ≈ 2.2 km。更高层级用 `python scripts/fetch_terrain_dem.py --zoom 7 9` 按需下载，不入普通 Git。
- 地形由 `BufferGeometry` 索引网格构建，顶点携带真实高程、梯度、凹度与边缘属性；法线在片元着色器中由梯度求得，垂直夸张只改一个 uniform，**不修改高程数据**。
- 通过 MapLibre `CustomLayerInterface` 与地图共用相机与投影；省界、国界、水系逐点采样同一 DEM 后贴地绘制，地点标记按地形高度投影。**国界由 34 个省级面拓扑并集求出**（不是把省界整体加粗），以「暗色衬底 + 金色光晕 + 亮金主线」三层描边；**省界另取省际共享边界去重后的独立数据**（相邻省份只画一次、不含国界与海岸线），暖古铜金细线并随缩放加粗，始终弱于国界。两层在图层面板中可独立开关，省名与碑刻标记做屏幕空间避让。
- 二维/三维同一引擎：三维为立体起伏，二维为同一 DEM 的平面晕渲；无 WebGL 时回退到既有 MapLibre 栅格样式。
- 实测：全国画幅占比 69.9%–70.5%，交互 152–162 FPS（1920×1080，RTX 4060 Laptop），全国网格 620,964 顶点。详细参数与前后对照见 [V2.2 视觉精修](docs/terrain3d/V22_VISUAL_REFINEMENT.md)。

实现、数据与限制见 [实施报告](docs/terrain3d/IMPLEMENTATION_REPORT.md)、[数据来源与合规](docs/terrain3d/DATA_SOURCES.md)、[引擎架构](docs/terrain3d/ARCHITECTURE.md)。数据只覆盖真实获取的部分：Copernicus DEM、USGS/NASA 原生产品与自然资源部标准图幅本次**未取得**，已在数据文档中列明；本应用仍未单独审图。

受控退化实验位于 [experiments/](experiments/)。第二阶段有中心采样、正文区域两批，共28件、280个退化输入、9种方法、2520次输出，各批按文物ID分开发/独立测试。正文批次独立测试均值：输入24.705 dB/0.704 SSIM；固定联合18.829/0.485；自适应26.798/0.762；单独陷波27.252/0.767。自适应并非所有指标或个例最佳；首批中心采样落到纸边的失败结果完整保留。报告页可筛选真实批次并查看图表、前后图和导出。旧实验使用退化标签选joint陷波的问题已记录；新实验与生产决策不接收标签或参考图。

## 安装与运行

建议 Python 3.10–3.12、Node.js 18+。在仓库根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/init_db.py
cd apps/web
npm ci
npm run build
cd ../..
.\start.ps1
```

`start.ps1` 使用脚本所在目录，必要时重建前端，启动 FastAPI 并记录本项目 PID；`stop.ps1` 仅停止它启动的进程。也可分别运行 `python -m uvicorn main:app --host 127.0.0.1 --port 8000` 与在 `apps/web` 运行 `npm run dev`。先检查 `/health`，再检查 `/generate`，然后打开 Vite 页面或构建后的服务页面。API 文档在 `/docs`。自检运行 `.\check.ps1`。

可选视觉模型通过环境变量 `RUBBINGMIND_VISION_API_KEY`、`RUBBINGMIND_VISION_BASE_URL` 和 `RUBBINGMIND_VISION_MODEL` 配置；请勿提交密钥。调用外部模型可能产生费用。

## 验证

```powershell
python -m pytest tests -q
python scripts/validate_museum_v3.py
python scripts/validate_history_gis.py
python experiments/run_ablation.py
# 扩展批次（已有目录不覆盖，使用新输出名）
python experiments/run_v2.py --output data/runtime/my-v2-experiment
python experiments/run_v2.py --config experiments/config-v2-text.json --output data/runtime/my-v2-text-experiment
python experiments/evaluate_glyphs.py
cd apps/web
npm run build
```

三维地貌的浏览器验收（需后端 8000 与 Vite 5173 同时运行）：

```powershell
python scripts/test_terrain3d_browser.py   # 截图写入 screenshots/terrain3d-final/
python scripts/test_graph_browser.py       # 原有图谱回归
```

浏览器验收步骤和实际结果见 [整改报告](docs/audit/2026-10-15-remediation-report.md)。自动化通过不等于文物学术结论已获专家认证。地图、未标注残字和无真值历史拓本仍有明确的验证边界。

第二阶段代码、评测与复现说明见 [技术实装记录](docs/audit/technical-implementation-v2.md) 和 [技术验收报告](docs/audit/technical-implementation-v2-report.md)。真实模型接入须用户自行配置，当前验收不包含未配置外部服务的识字效果。所有84张正式馆藏影像保持原始校验值。

本地默认绑定127.0.0.1。远程模式 `RUBBINGMIND_DEPLOYMENT=remote` 对私有数据及写接口要求管理员Bearer凭据（`RUBBINGMIND_ADMIN_TOKEN`），未配置则拒绝。它是管理员单用户模式，不提供多租户隔离；公网多用户服务仍需独立身份、配额、超时与文件归属系统，勿直接开放本机服务。
