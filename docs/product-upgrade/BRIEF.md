# 墨韵智考 RubbingMind —— 产品级升级总任务（用户原始要求的忠实摘要）

协调者（监工）：Green。各专业 Agent 由 Green 创建并分派任务，向 Green 汇报。
本文件是所有 Agent 的共享任务书（用户原文的忠实摘要，存疑时问 Green）。副本：D:\RubbingMind\docs\product-upgrade\BRIEF.md

## 0. 环境
- 用户 Windows 笔记本：LAPTOP-TU4U942T，machineId `d94338e4-3afa-4493-8a0e-c37f7470021f`（用 Shell/Read 传 machineId，PowerShell）。
- 本地正式项目：`D:\RubbingMind`；GitHub：https://github.com/3331083641-prog/RubbingMind（Private，禁止改可见性）。
- 当前集成分支：`feature/product-grade-upgrade`（基于 f0c5886，仅本地，尚未推送）。
- 用户可能开着 Vite 开发服务器 5180、python 8000：不得杀掉不是自己启动的进程。各 Agent 自己的服务端口见 COORDINATION.md。
- CopyFromBox/CopyToBox 只能写 C:\Users\WPY11；Shell 可读写 D:。笔记本没有 ffmpeg。
- 用户未跟踪文件（design/blender/*.blend/.npz、rubbings-review-v3/、rubbings-workspace/、screenshots/ 下多个旧目录、user_prompt_10.txt、墨韵智考_真实碑拓28件高清成品/）禁止删除、修改、提交。

## 1. 技术栈与受保护资产
React+TS+Vite、FastAPI、OpenCV/NumPy/scikit-image、频空域自适应处理、SQLite、FTS5/BM25、Three.js、MapLibre、ECharts、Blender 碑模、历史 GIS、28 件正式馆藏（84 张正式影像）+4 件核心演示样本、来源授权记录、自动化测试与 GitHub Actions。
严格保护：首页视频背景与视觉；典藏馆真实影像、卡片、Blender 模型几何/纹理/材质；时空图谱 Three.js 真实地形、国界省界、DEM、V2.2 视觉；文物身份/馆藏编号/来源；实验原始数据、失败实验和负提升样本；原图 SHA-256；用户上传数据。不得为了指标修改馆藏影像。发现错误先给证据与非破坏性方案。

## 2. 质量铁律
- 只报告真实执行过的命令和真实输出；不伪造指标、史料、Agent 记录、CI 状态。
- 无配对参考的真实拓本不得报告修复 PSNR/SSIM；无独立人工真值时 Top-1/Top-3/拒识率保持“未评测”。
- “未核定”不能自动变“已核定”；异文冲突保留；北魏测试样本不得与未证明同一性的真实墓志合并；作品≠拓本≠原石。
- 图像变清晰≠恢复原刻文字；候选字不能显示为已识读碑文；模型输出不能升级为权威事实；视觉模型不得改馆藏原文。
- 无坐标核验时只用区域定位，不造精确坐标。
- 证据分级：已验证 / 有限支持 / 未评测 / 待人工复核。

## 3. 每项重大修改的四环节
方案提出 → 独立质疑（非实现者；科学结论须评测科学家审；史实须金石学+数据治理审）→ 实现与测试 → QA+红队验收，Green 确认后合并。
关键专题：A 增强是否保护笔画；B 数据泄漏/不公平对照；C 候选是否被当作已识读；D 史料关系证据是否充分；E UI 是否误导；F 多页面是否共享同一文物与运行记录；G 干净环境能否运行；H 无法证明的功能宣传。每场记录：议题、观点、证据、反对意见、决定、责任人、验证方法 → `docs/product-upgrade/GROUP_DISCUSSION.md`。

## 4. 阶段
- Phase 0 审计：Git、资产 SHA 冻结、基线测试、全部 API 实测、六维评价（技术深度、功能价值、内容广度、真实性、模块连接、视觉交互），每项：位置、实测结果、已验证、未实现、缺陷、用户影响、风险、修复路径、验收标准；P0（正确性/安全/真实流程/可信交付）P1 P2。
- Phase 1（第一重点）算法评测报告重构：ReportsPage.tsx、ExperimentExplorer.tsx、HeldoutComparison.tsx、experiment_registry.py、experiments/、data/catalog/glyph-benchmark-v2.json。六层：研究总览（真实数据，无真值显示“未评测”）；修复效果视觉对照（参考/退化/输出三联、同步缩放拖动、ROI、滑杆、方法切换、实验 ID、真实差分热图，无图则说明，不得 object-fit cover 裁字）；算法横向比较（ECharts，不同量纲分轴，不截断坐标轴，正负提升都保留，筛选联动）；消融与算法机制（只展示真实执行步骤：频谱、周期峰、陷波位置、二值前景、骨架、边缘、门控决策，可点击阶段查看真实数据）；失败案例与不确定性（独立入口，真实失败图像，不伪造）；科学结论与可复现性（实验 ID、样本来源、划分、方法版本、种子、配置、CSV/JSON 导出、源码索引；结论分级）。全局评测与单次文物处理报告明确分层。统计：dev/test 区分、不得按测试集调参、保留失败与负提升与不适用、区分原图返回与实际处理、按文物分组置信区间、样本数、不得跨批次均值解读为进步。PDF：反映当前选择、中文字体、A4 纵版、图题、来源与局限。风格：深墨、暖金、低饱和青绿、朱砂警示；避免表格堆叠和数字卡片墙。1920×1080/1440×900 首屏即见核心结论与视觉对照。
- Phase 2 图像算法与残字：可解释自适应（决策变量来自真实算法）、ROI 局部对照（文物ID/源SHA/运行ID/ROI/版本/参数/时间关联，切换文物不串结果）、残字流程（ROI、来源、位置、候选依据、视觉/文献证据、不确定性、人工采纳/驳回/撤销、持久化）。
- Phase 3 史料与知识：统一实体（作品、原刻载体、拓本、馆藏机构、撰文/书丹/碑主、事件、纪年、历史地名、现代地理、书体、文献、字形选区、运行、实验），稳定 ID 与跨模块链接；28 件逐件深化（缺失保持缺失并说明原因）；跨文物对比；检索（查询理解、消歧、证据排序、多来源、冲突、证据不足拒答、定位到馆藏/图谱、防提示注入）。
- Phase 4 五页闭环：首页→典藏馆→工作台→图谱→报告，通过真实 ID 联动（steleId/artifactId/rubbingId/imageSha256/runId/inferenceId/experimentId/sourceId/locationId 为建议体系，先查现有字段，迁移需无损映射与回滚）。前端成功必须后端保存。
- Phase 5 安全与稳定：交付形态 A（单机本地研究产品）做可靠，B 受控演示提供安全路径，不开放公网。上传类型/大小、路径穿越、解码异常、大图内存、参数校验、敏感信息、前端注入、检索提示注入、外部模型失败/超时、并发、删除确认；无 API Key 入库；一键启动（相对路径、健康检查、显示地址、只停本项目进程、不覆盖数据库）；可选模型状态透明、无模型时正常降级不伪造。
- Phase 6 GitHub 集成：功能分支/worktree → 审查 → 合入 feature/product-grade-upgrade → 全量测试 → 正常合并 main → 推送 → 核对 CI → 本地与远程一致。禁止 force push、改写历史。

## 5. 测试
python -m pytest tests -q；scripts/validate_museum_v3.py；validate_history_gis.py；test_graph_browser.py；test_terrain3d_v22_browser.py；test_technical_v2_browser.py；其他专项；npm ci；npm run build。业务流程 A–F（真实文物研究、图像处理、残字研究、算法评测、史料证据、异常处理）。数据正确性（28 件无错位、84 张 SHA 不变、演示样本区分、运行 ID 对应、无真值指标为空、PDF/JSON/CSV 一致、失败实验未删）。截图尺寸 1920×1080、1440×900、1366×768、390×844。

## 6. 文件位置
文档：D:\RubbingMind\docs\product-upgrade\（MASTER_PLAN、AGENT_ROSTER、TASK_BOARD、GROUP_DISCUSSION、ARCHITECTURE_DECISIONS、REVIEW_FINDINGS、ACCEPTANCE_MATRIX、PROGRESS 等）
截图：D:\RubbingMind\screenshots\product-upgrade\
测试：tests\ 或 scripts\；报告组件可放 apps/web/src/components/reports/。新组件必须接入实际页面。

## 7. 必须先问用户（经 Green）
购买付费服务、需要私密账号/密钥、公开仓库、删除或覆盖真实馆藏/用户数据、重写 Git 历史、暴露公网、重大成本或不可逆操作。
