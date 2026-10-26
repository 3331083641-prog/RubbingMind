# PHASE0_SUMMARY — Phase 0 审计汇总（跨审计去重）

- 作者：Green（Agent 01，总协调）
- 写入时间：2026-10-19 12:25（Asia/Shanghai，UTC+8）
- 基线：`feature/product-grade-upgrade` @ `f0c5886`
- 本文只汇总各审计文件里写了的内容，不新增结论。原文表述不清的地方直接引用原文。“红队复核”一栏只写 REVIEW_FINDINGS.md 里真实写了的结论；没写的一律为“待复核”。

## 0. 来源文件与编号约定

| 来源编号前缀 | 文件 | 作者 | 原文编号写法 |
|---|---|---|---|
| `E-xx` | AUDIT_EVALUATION.md | RM-评测科学家 | E-01 … E-25 |
| `F-P0-x` / `F-P1-x` / `F-P2-x` | AUDIT_FRONTEND.md | RM-报告前端 | 原文为 P0-1、P1-1、P2-1（本文加前缀 F- 区分） |
| `ENG:E-Pn-xx` | AUDIT_ENGINEERING.md | RM-架构后端 | 原文为 E-P0-01 等（本文加前缀 ENG: 以免与评测的 E-xx 混淆） |
| `C-xx` | AUDIT_CONTENT.md | RM-金石史料 | C-01 … C-23 |
| `RT-xxx` / `RV-Exx` / `BT-xx` | REVIEW_FINDINGS.md / BASELINE_TESTS.md | RM-红队QA | 原样 |
| ADR / R1-x | ARCHITECTURE_DECISIONS.md | RM-架构后端 | 原样 |
| SPEC §x | REPORT_DATA_SPEC.md | RM-评测科学家 | 原样 |

## 1. 各审计报告的条数（按文件原文）

| 文件 | P0 | P1 | P2 | 原文说明 |
|---|---|---|---|---|
| AUDIT_EVALUATION.md | 3 | 9 | 13 | “共 25 条（P0 3 条，P1 9 条，P2 13 条，其中 5 条是‘已验证’的正面结论）” |
| AUDIT_FRONTEND.md | 6 | 15 | 7 | “条数统计：P0 6 条，P1 15 条，P2 7 条” |
| AUDIT_ENGINEERING.md | 3 | 9 | 11 | E-P0-01~03 / E-P1-01~09 / E-P2-01~11 |
| AUDIT_CONTENT.md | 3 | 12 | 8 | C-01~03 / C-04~10、C-15、C-17、C-18、C-19、C-21 / 其余 |
| REVIEW_FINDINGS.md（红队） | 0 | 3 | 10 | “结论：本轮没有 P0”；RT-001~003 为 P1，RT-004~013 为 P2 |
| **合计（去重前）** | **15** | **48** | **49** | |
| **去重后（本文）** | **11** | 见 §3 | 见 §4 | P0 去重合并了 4 组重复：运行排序、runId、双 ID、原图当输出 |

另：ASSET_FREEZE.json（RM-金石史料）头部记录 `generated_at 2026-10-19T11:48:37+08:00`、`repo_head f0c5886…`；`museum_image_count.referenced=84 / expected=84`（cover/archive/readable 各 28）；11 个类别合计 4046 个文件（museum_metadata 129、museum_image 84、museum_source_original 28、museum_assessment_derived 84、demo_sample 21、homepage_video 1、homepage_poster 1、blender_model 28、terrain_dem 423、boundary 10、experiment_raw 3237）。文件 SHA-256 为 `82E940BD…AF86A01A`（Green 12:19 用 Get-FileHash 实测）。“591 项比对全部一致、discrepancies 为空”来自金石史料的汇报，Green 未逐项复核，红队抽样复核中（见 TASK_BOARD）。

## 2. P0 矩阵（去重后 11 条）

| ID | 标题 | 证据位置 | 来源 | 红队复核 | 负责人 | 阶段 |
|---|---|---|---|---|---|---|
| **P0-01** | 报告默认绑定 legacy-unverified 旧运行（`finishedAt` 字符串倒序，“未记录”排在 ISO 时间前） | `museum_processing.py:84,90-97`；`main.py:375-376`；`ReportsPage.tsx:19-20`。实测 tang-duobao 默认 `20261014T165542_5fc44fba`，应为 `20261018T072201_13772747` | F-P0-1、ENG:E-P0-01 | 待复核 | 架构后端（ADR R1-1 排序 + legacy + runSelection）；报告前端（默认选择与徽标） | Phase 1 |
| **P0-02** | 工作台与报告不共享 runId，没有 URL 状态，刷新丢失、不能深链 | `App.tsx:16-22,94,111`；`WorkbenchPage.tsx:45,146`；`ReportsPage.tsx:13-20,33` | F-P0-2、ENG:E-P0-02 | 待复核 | 架构后端（App.tsx/api.ts，ADR R1-6）；报告前端（报告组件内的 URL 参数） | Phase 1 → Phase 4 |
| **P0-03** | 同一作品两套 ID（核心演示 `tang-duobao`/`han-caoquan` 与馆藏 `tang_01_duobao`/`han_01_caoquan`），运行/推演/图谱按 ID 分裂；演示 ID 被隐式别名到真实馆藏，同一 ID 指两种东西 | `history_graph.py:9-10,17`；`evidence_retrieval.py:20-21,56-57`；`main.py:352-361`；`graphSelection.ts:2-16`；`services/history.ts:12-19`；`core_sample_links.json`（`same_work`，“不证明为同一馆藏拓本”）。实测 runs 4 条 vs 10 条、推演 0 vs 8；馆藏 ID 的 graph 无 steleId | ENG:E-P0-03、C-01；相关：E-21（原 P2）、F-P1-8、F-P1-15 | 待复核 | 金石史料（`rm:demo:` 命名空间 + `id_mapping.json` 内容与人工复核）；架构后端（映射接口，ADR R1-5） | Phase 1（接口）→ Phase 3/4 |
| **P0-04** | 单件报告把未改动的原图展示为“本次算法输出”，后端写“实际处理已执行” | `museum_processing.py:52-58,66`；`main.py:382`；`ReportsPage.tsx:99`；`WorkbenchPage.tsx:461`；`GlyphInferencePanel.tsx:126`。tang_01_duobao 10 次自适应运行像素改动 0 | E-03、F-P0-3（前半） | **成立**（RV-E03：主工作区 tang_01_duobao 10/10 次 0 像素改动；8740 上 `/report` 仍写“实际处理已执行”，restored SHA = original SHA `5532e851…`） | 架构后端（SPEC §8 字段 + `main.py:382` 文案，ADR R1-2）；报告前端（文案）；评测科学家（判据） | Phase 1 |
| **P0-05** | 实验层不区分“原图返回”与“实际处理”：identity/门控回退输出与输入逐字节相同，却记 `applied`/`candidate` 并计入均值（v2 55/140、v2-text 45/140、heldout v2.1 21/70；blur 全部原样返回） | `degradation_analysis.py:185-186,191-193,195,234`；`experiments/run_v2.py:108`；`compare_v21.py:110`；`ExperimentExplorer.tsx:16,40`；`HeldoutComparison.tsx:57-58` | E-02、F-P0-3（后半：not_applicable 行仍标“本方法输出”）；相关：E-05 | **成立**（RV-E02：v2 55 行、v2-text 45 行逐字节相同且全部 applied，计入 n=70；重算 v2-text test 26.798→28.466，47 行） | 评测科学家（agent/eval-sci 已实现判据与派生文件，待复核）；报告前端（显示） | Phase 1 |
| **P0-06** | 所谓“留出”批次不是留出：`2026-10-18-v21-heldout` 的 14 件与 `2026-10-17-v2-text` 完全同批（同 SHA，7 件是其 test），song_03 裁切重叠 100%、tang_04 79.5%；v2.1 在 v2-text 结果之后才写 | `experiments/compare_v21.py:1-6,46-64`（:49-51 只排除 v2）；`2026-10-18-v21-heldout/results.json` 的 `excludedFromPreviousBatch`；`HeldoutComparison.tsx:37-38,51,60`；`tests/test_heldout_v21.py:9-15`；提交 f9aebdb（10-17 18:13）→ ea5a67a（10-18 00:56）→ 59f9784（10-18 10:52） | E-01 | **成立**（RV-E01：“泄漏事实成立；‘看过结果之后才改 v2.1’只证明了时间先后，因果关系没有证明”） | 评测科学家（改名“同批复测 v2.1”、排除表）；报告前端（UI 不出现“留出”） | Phase 1 |
| **P0-07** | 没有 `split` 字段的批次（heldout 490 行、2026-10-15 80 行）被过滤器放行并显示为“test”；默认批次 `items.at(-1)` 选中 heldout | `ExperimentExplorer.tsx:10,12,15` | F-P0-4；相关：E-07（原 P1）、F-P1-13 | 待复核 | 架构后端（批次元数据 splitAvailable/status/defaultForReport，ADR R1-3）；报告前端（过滤器禁用与提示） | Phase 1 |
| **P0-08** | PDF/JSON 导出不含全局评测、不反映当前选择（两评测组件 `print:hidden`；实测 PDF 1 页 A4 只有单件 article） | `HeldoutComparison.tsx:51`；`ExperimentExplorer.tsx:21`；`ReportsPage.tsx:34-58,65,81` | F-P0-5；相关：E-23（原 P2） | 待复核 | 报告前端 | Phase 1 |
| **P0-09** | 比较只用绝对均值，没有按文物聚类 CI、相对输入 Δ、跨批次警告；error-analysis.md 中“独立测试组 SSIM 不优于输入”“遮挡 10/14 劣于输入”在 UI 上看不到；各批次汇总口径不同（2026-10-15 notch summary 41.364 dB n=2 vs 全行 27.813 dB n=10） | `HeldoutComparison.tsx:46,61-63`；`ExperimentExplorer.tsx:16,20,36-37`；`run_ablation.py:122` vs `run_v2.py:72`；`compare_v21.py:146-158` | F-P0-6；相关：E-06（原 P1）、E-24（原 P2）、F-P1-14 | 待复核 | 评测科学家（聚类 CI、口径、SPEC §1(c)）；报告前端（ECharts 呈现） | Phase 1 |
| **P0-10** | 核心演示样本元数据含无来源或与来源冲突的史实并直接上首页（如多宝塔“公元 752 年 5 月”“西安碑林博物馆第一室”未能核实；author 写成书丹者；元怀墓志现藏地多说并存） | `data/catalog/core_samples.json:6,10,13,294,301,606,610,613,894,901`；`apps/web/src/data/coreSamples.json`；`HomePage.tsx:239,280` | C-02 | 待复核 | 金石史料 | Phase 3（已在 agent/jinshi 起步） |
| **P0-11** | 北魏测试样本 wei-jianyi 的“释文”是 `sample_generator.py` 生成的合成文本，却以 transcript/translation 和逐字 `clear` 状态按已识读样式展示 | `sample_generator.py:89-97`；`core_samples.json:920,926`；`knowledge_agent.py:308-314`；`catalog.py:33-34`；`GET /api/steles/wei-jianyi/infer` | C-03 | 待复核 | 金石史料 | Phase 3（已在 agent/jinshi 起步） |

去重说明：F-P0-1 与 ENG:E-P0-01 → P0-01；F-P0-2 与 ENG:E-P0-02 → P0-02；ENG:E-P0-03 与 C-01 → P0-03；E-03 与 F-P0-3 → P0-04（F-P0-3 中关于实验浏览器的部分并入 P0-05）。其中 E-21 在评测审计中定为 P2、在工程审计中（E-P0-03）定为 P0，本文取较高级别 P0。

## 3. P1 矩阵（去重后）

| ID | 标题 | 证据位置 | 来源 | 红队复核 | 负责人 | 阶段 |
|---|---|---|---|---|---|---|
| P1-01 | 负提升原因按退化标签硬写，不是测量出来的；“14 件”硬编码 | `restoration_diagnosis.py:11-25,58`；`HeldoutComparison.tsx:58` | E-04 | 待复核 | 评测科学家 | Phase 1 |
| P1-02 | 陷波判“不适用”时仍改像素（全 1 mask 仍做 FFT→IFFT，`astype(np.uint8)` 截断） | `algorithm_engine.py:179-206`；`run_ablation.py:57-59`；`ExperimentExplorer.tsx:37` | E-05；SPEC §1(b)（“本次不修”） | 待复核 | 评测科学家 | Phase 1 |
| P1-03 | heldout 批次没有存任何图像（三联图、差分图无法提供），空状态不说明原因 | `compare_v21.py:85-173`；`experiment_registry.py:11,28-35`；`ExperimentExplorer.tsx:40` | E-08、F-P1-5 | 待复核 | 评测科学家（数据）；报告前端（SyncedTriptych、空状态） | Phase 1 |
| P1-04 | v2.2 候选门控按模拟器的遮挡生成方式定制，只在已见过的裁切上测过（未进生产） | `degradation_analysis.py:199-240`；`run_v2.py:60-62`；`2026-10-18-synthetic-v22-summary.json` | E-09 | 待复核 | 评测科学家 | Phase 2 |
| P1-05 | 运行记录的参数是原始请求，不是实际生效值（adaptive 模式忽略 filter_order 等） | `algorithm_engine.py:365`；`museum_processing.py:60` | E-10；SPEC §8 `effectiveParameters` | 待复核 | 架构后端（字段）；评测科学家（口径） | Phase 1 |
| P1-06 | 残字评测两套不兼容 schema；报告页“未评测”是写死文字，不绑定 `/api/glyph-evaluation` | `glyph-benchmark-v2.json:5`；`evaluate_glyphs.py:25`；`glyph_annotations.py:14-15,106-107,120-131`；`main.py:279-286`；`ReportsPage.tsx:110` | E-12、F-P1-10 | 待复核 | 评测科学家；报告前端 | Phase 2（绑定在 Phase 1） |
| P1-07 | 机制层没有数据和组件：实验批次没存频谱/陷波/二值前景/边缘；运行里已存的 frequency_spectrum、binary_skeleton、contour、decisions、fidelityGate 未被展示 | `run_ablation.py:58-59`；`run_v2.py:111-117`；`compare_v21.py:141`；全仓 tsx 中 `frequency_spectrum` 0 命中 | E-18、F-P1-3 | 待复核 | 评测科学家（代表案例真实数据）；报告前端（MechanismPipeline） | Phase 1 |
| P1-08 | 报告页没有 ECharts：手画条，负值被 `Math.max(0, …)` 截为 0，无指标方向 | `HeldoutComparison.tsx:46,63`；`ExperimentExplorer.tsx:20,36` | F-P1-1；相关：E-24（原 P2） | 待复核 | 报告前端 | Phase 1 |
| P1-09 | 首屏只有标题、运行下拉和 7×9 数字表，`<pre>JSON` 堆叠 | ReportsPage 首屏（截图 05） | F-P1-2 | 待复核 | 报告前端 | Phase 1 |
| P1-10 | 失败案例没有独立入口；v2/v2-text/2026-10-15 的 diagnosis 接口 404 | `HeldoutComparison.tsx:58`；`main.py:187-189`；`restoration_diagnosis.py:7` | F-P1-4；ADR R1-4 实测 | 待复核 | 架构后端（各批次诊断接口）；报告前端（FailureCasesPanel） | Phase 1 |
| P1-11 | 可复现信息缺失（commit、seed、config、source_snapshot 不展示；gitSha、代码 SHA 有缺口；运行目录被 gitignore） | heldout API 字段；`results.json` 的 `environment`；`compare_v21.py:35-43,163,170`；`.gitignore:64,79` | F-P1-6；相关：E-11（原 P2） | 待复核 | 报告前端；评测科学家 | Phase 1 |
| P1-12 | 全局评测与单件报告没有分层 | `ReportsPage.tsx:76-78` | F-P1-7 | 待复核 | 报告前端 | Phase 1 |
| P1-13 | 时间显示为 UTC ISO 原串，未统一为 Asia/Shanghai | `ReportsPage.tsx:71,93` | F-P1-9 | 待复核 | 报告前端 | Phase 1 |
| P1-14 | 工作台指标单位与空值拼接错误（“未评测 dB”“未评测%”，snr_gain 强制加 `+`） | `WorkbenchPage.tsx:491-507` | F-P1-11；相关：F-P2-1 | 待复核 | 报告前端 | Phase 1/2 |
| P1-15 | 首页核心样本卡 `object-cover` 裁切拓本（受保护视觉，需决策）；“PSNR: 未评测 dB” | `HomePage.tsx:249,269-270` | F-P1-12、F-P2-1 | 待复核 | 报告前端（决定见 GROUP_DISCUSSION 12:04，需用户确认截图） | Phase 1 |
| P1-16 | Explorer 统计口径：n=1 时标准差显示 0；均值按行而不是按文物聚类 | `ExperimentExplorer.tsx:16` | F-P1-14；相关：E-19 | 待复核 | 报告前端；评测科学家 | Phase 1 |
| P1-17 | 删除运行后引用它的推演变成悬挂引用，仍显示“已验证归属”；删除是物理删除、不可恢复 | `museum_processing.py:100-108`；`main.py:393-400`；`WorkbenchPage.tsx:168-169` | ENG:E-P1-01；相关：RT-013（P2） | 待复核 | 架构后端 | Phase 2/5 |
| P1-18 | `sample_id` 处理路径写入无归属的 `static/results/uploaded-image/` | `museum_processing.py:28-29,34-35` | ENG:E-P1-02 | 待复核 | 架构后端 | Phase 4 |
| P1-19 | 人工标注接口不校验文物、图像 SHA、坐标 | `glyph_annotations.py:60-99`；`main.py:289-299` | ENG:E-P1-03 | 待复核 | 架构后端 | Phase 2 |
| P1-20 | 参考字形检索自匹配（同一选区登记模板后再推演得 1.000） | `glyph_inference.py:278-296` | ENG:E-P1-04；相关：E-13（原 P2） | 待复核 | 架构后端；评测科学家 | Phase 2 |
| P1-21 | 跨站 multipart 写入（CSRF）、无 Host 校验（DNS rebinding）；本地模式按 loopback 放行写操作，反代/隧道可绕过 | `main.py:70-76`；`runtime_guard.py:17-26`；`catalog_assessment.py:90-95` | ENG:E-P1-05；相关：RT-009（P2） | 待复核（RT-009 为红队自身代码审查发现） | 架构后端；红队验收 | Phase 5 |
| P1-22 | 数据路径与端口写死；Vite 代理默认指向用户 8000；测试脚本默认连用户端口并会写数据；start.ps1 端口不可指定、start.bat 自动 pip（trusted-host）；pytest 改写已跟踪文件并在 data/ 建真实 SQLite；测试不密闭 | `database.py:11-12`；`catalog.py:5`；`upload_storage.py:15`；`glyph_inference.py:23`；`evidence_retrieval.py:16`；`main.py:542`；`vite.config.ts:10-16`；`scripts/test_technical_v2_browser.py:170`；`start.ps1:39-41`；`scripts/validate_stele_asset.py:55`；`tests/test_catalog_assessment_api.py:25` | ENG:E-P1-06、RT-003；相关：RT-004（P2）、ENG:E-P2-04、ENG:E-P2-06 | RT-003、RT-004 为红队自身发现（BT-01 实测副作用） | 架构后端（ADR-007 / R1-7） | Phase 1（路径变量）→ Phase 5（一键启动） |
| P1-23 | 持久化分裂：SQLite `steles` 33 行（含 5 行下架）与 steles28.json 双轨，无约束、无 schema 版本；5 处作者过时，5 条下架记录带无来源精确坐标；retired_steles.json 残留手写指标 | `database.py:23-96,102-103`；`museum_manager.py:8`；`data/rubbingmind.sqlite`；`data/catalog/retired_steles.json` | ENG:E-P1-07、C-08 | 待复核 | 架构后端（schema）；金石史料（只读一致性核对，不直接改用户库） | Phase 3 |
| P1-24 | 前端读接口静默回退到打包数据（404/410 也回退），用户看不出数据来源 | `services/api.ts:40-43,49-52,57-60`；`history.ts:21-26` | ENG:E-P1-08 | 待复核 | 架构后端（api.ts） | Phase 4 |
| P1-25 | 选中运行后，报告里的推演记录把原图推演过滤掉（8 条只显示 1 条） | `main.py:380` | ENG:E-P1-09、E-22（原 P2） | 待复核 | 架构后端 | Phase 1 |
| P1-26 | 检索 `status=insufficient_evidence` 与 `judgment=supported` 同时出现（碑主不在 supported_facets） | `evidence_retrieval.py:331-352`；`EvidenceSearch.tsx:38` | C-04 | 待复核 | 金石史料 | Phase 3 |
| P1-27 | 跨来源异文不检测：目录“原石现藏机构：未核定”与 history“西安碑林博物馆”同时返回、不标冲突 | `steles28.json`；`data/history/han-caoquan.json:12`；`tang-duobao.json:10,12`；`evidence_retrieval.py:37,61` | C-05 | 待复核 | 金石史料 | Phase 3 |
| P1-28 | 28 件目录 `approved_by_user`，28 份证据仍是“待第三轮复核”；review_manifest 无日期、确认人、逐件记录 | `steles28.json`；`data/catalog/evidence/*.json`；`review_manifest.json` | C-06 | 待复核 | 金石史料（只出核对方案，不改批准状态） | Phase 3 |
| P1-29 | 馆藏编号跨模块写法不一致（繁简、括注、空格），无规范化键 | `steles28.json`；`data/history/*.json:11` | C-07 | 待复核 | 金石史料 | Phase 3 |
| P1-30 | 核定状态无 schema 约束；三套状态词表未映射到四级证据 | `data/catalog/schema.json` | C-09 | 待复核 | 金石史料；架构后端 | Phase 3 |
| P1-31 | 作品、原刻载体、拓本只做到字段级区分；dimensions、carver/engraver、scriptType 语义混用 | `steles28.json`（如第 1605、1698、1700、1880 行）；`WorkbenchPage.tsx:213` | C-10 | 待复核 | 金石史料 | Phase 3 |
| P1-32 | 检索查询理解：简称（多宝塔、九成宫）被拒答，“魏征/魏徵”判 contradicted，别名 ID 查不到 | `evidence_retrieval.py:20-21,160-170,310-312`；`museum_manager.py:14` | C-15 | 待复核 | 金石史料 | Phase 3 |
| P1-33 | `knowledge_agent.py` 留有错误史实、无来源坐标、错误纪年换算（“天宝十四载”→742，应为 755）；当前 API `/api/calendar` 用的是 `history_graph.convert_historical_year`，实测正确 | `knowledge_agent.py:49,141,202-203,216,265,269,291,474-498,515-522`；`main.py:24` | C-17 | 待复核 | 金石史料（删除调用面需经 Green 和用户同意） | Phase 3 |
| P1-34 | 残字 LLM 提示把用户上下文直接拼进去，没有隔离（无 API Key，仅代码审查） | `glyph_inference.py:162-165`；`main.py:121,176-186` | C-18 | 待复核（未实测） | 金石史料（方案）；架构后端（实现）；红队（用例） | Phase 3/5 |
| P1-35 | 启动时样本回退：从未授权第三方站点下载（`verify=False`、伪造 Referer/UA），失败后本地合成“高仿真碑拓”写入 `static/samples` 冒充核心样本 | `main.py:49-57`；`sample_generator.py:6,47-89,119-135,301-305` | RT-002、C-19 | RT-002 为红队自身代码审查发现（基线未触发）；**严重度红队复审中** | 架构后端（实现）；金石史料（演示图 provenance） | Phase 5（严重度待定，可能提前） |
| P1-36 | 馆藏释文前 35 字被标为 `status:'clear'` 并排进人为行列网格 | `catalog.py:35-36`；`services/api.ts:51`；`WorkbenchPage.tsx:684-696` | C-21 | 待复核 | 金石史料；报告前端/架构后端（显示与接口） | Phase 2/3 |
| P1-37 | `test_technical_v2_browser.py` 完整模式在 390×844 移动端失败；CI 只跑 `--ci` | `scripts/test_technical_v2_browser.py:22,150-152`；`Header.tsx:74` | RT-001 | 红队自身发现（BT-06a 实测，退出码 1） | 红队QA（测试）；报告前端（若需改 UI） | Phase 1/5 |

## 4. P2 汇总（去重后，简表）

| 来源 | 标题（简） | 负责人 | 阶段 |
|---|---|---|---|
| E-11 | 可复现溯源缺口（并入 P1-11） | 评测科学家 | 1 |
| E-13 | 候选来源风险：5 条写死上下文规则；模板检索不排除同文物/同 crop（后半并入 P1-20） | 评测科学家 | 2 |
| E-14 | 指标定义与“真值”性质需在报告中披露（原文“已验证，需在报告中披露”） | 评测科学家；报告前端 | 1 |
| E-20 | 28 件归档评估中 7 件输入输出 SHA 相同，21 件平均改动 0.002–1.309 灰度级 | 评测科学家；报告前端 | 1 |
| E-21 / E-22 / E-23 / E-24 | 分别并入 P0-03 / P1-25 / P0-08 / P1-08 | — | — |
| F-P2-1 | “PSNR: 未评测 dB”单位拼接（并入 P1-15） | 报告前端 | 1 |
| F-P2-2 | `scripts/capture_five_pages.py` 用不存在的 hash 路由，已失效 | 红队QA | 1 |
| F-P2-3 | 1920 轮 console 3 次 404，具体 URL“待核实” | 红队QA | 1 |
| F-P2-4 | “生成”时间取浏览器打印时刻 | 报告前端 | 1 |
| F-P2-5 | `graphSelection.ts:19` 回退对象 `metrics:{psnr:0,…}` 应为 null（评测审计“待核”：可能渲染成“PSNR: 0 dB”，未起前端验证） | 报告前端 | 1 |
| F-P2-6 / F-P2-7 | 方法顺序不固定、英文 ID；单次实验下拉最多 630 项 | 报告前端 | 1 |
| ENG:E-P2-01 | region-crop 无 >0 校验，PIL 内部信息外泄 | 架构后端 | 5 |
| ENG:E-P2-02 | async 路由执行同步 CPU/IO，阻塞事件循环（health 首次 1212ms） | 架构后端 | 5 |
| ENG:E-P2-03 | remote 模式鉴权面：/docs、/openapi.json、assessment（含复核人姓名）等仍 200 | 架构后端 | 5 |
| ENG:E-P2-04 | 启动脚本端口与自动安装问题（并入 P1-22） | 架构后端 | 5 |
| ENG:E-P2-05 | 敏感信息：`DeduceRequest` 死代码（api_key/base_url）；`.env.example` 变量名与代码不一致；用户环境有 `DASHSCOPE_API_KEY`（值未读取） | 架构后端 | 5 |
| ENG:E-P2-06 | 测试不密闭（并入 P1-22） | 架构后端 | 1 |
| ENG:E-P2-07 | 证据索引重建、标注追加无锁；SQLite 无 busy_timeout（竞态未实测）；PROCESS_LOCK 实测有效 | 架构后端 | 5 |
| ENG:E-P2-08 | 错误结构不统一，内部异常文本外泄 | 架构后端 | 5 |
| ENG:E-P2-09 | `data/museum_database.json` 含编造的消融指标（如 psnr 33.15），回退路径当前不可达 | 架构后端；金石史料 | 3 |
| ENG:E-P2-10 | 契约重复/不一致（reportId 前后端各算一次等） | 架构后端 | 4 |
| ENG:E-P2-11 | Git 卫生：`b0d17eb` 被取代的未合并提交；3 个外部 worktree 4/198/204 处未提交改动（用户决定保持原样） | Green / 用户 | 6 |
| C-11 | 缺失原因没有单独字段；证据库已有馆方数据未进入目录 | 金石史料 | 3 |
| C-12 | qing_02 馆方 caption 与目录朝代异文未记录 | 金石史料 | 3 |
| C-13 | `transcription` 混入授权附录；`translation` 字段名误用 | 金石史料 | 3 |
| C-14 | 坐标覆盖率低；北魏洛阳区域代理点偏在隋唐以后城区 | 金石史料 | 3 |
| C-16 | 检索排序噪声、演示与馆藏证据混排、结果无跳转 | 金石史料；报告前端 | 3/4 |
| C-20 | 检索测试缺口 | 金石史料；红队QA | 3 |
| C-22 | 现行 ID 编码“朝代_槽位”，下架后槽位复用 | 金石史料；架构后端 | 3 |
| C-23 | 图谱页只覆盖 4 个入口 | 金石史料；报告前端 | 3/4 |
| RT-004 | pytest 副作用（并入 P1-22） | 架构后端 | 1 |
| RT-005 | 无安全响应头；remote 模式 /docs、/openapi.json 公开 | 架构后端 | 5 |
| RT-006 | 遗留 `static/index.html`：API Key 存 localStorage、CDN 无 SRI、dist 缺失时回退到它 | 架构后端（删除/归档需 Green 确认） | 5 |
| RT-007 | `.env.example` 变量名与代码不一致 | 架构后端 | 5 |
| RT-008 | 开发依赖 9 个漏洞（3 moderate、6 high），生产依赖 0 | 架构后端 | 5 |
| RT-009 | 本地模式 loopback 放行（并入 P1-21） | 架构后端 | 5 |
| RT-010 | CI 只在 main 触发，漏 GIS/graph/terrain | 架构后端；Green 决定 | 6 |
| RT-011 | start.ps1 用 POST /generate 做健康检查，remote 下 401 | 架构后端 | 5 |
| RT-012 | README 顶点数 620,964 vs 实测 1,081,476（口径待核） | 金石史料/图谱负责人；红队 | 5 |
| RT-013 | 删除运行仅靠 confirm 参数，物理删除不可恢复（并入 P1-17） | 架构后端 | 5 |

## 5. 基线测试结果（照录 BASELINE_TESTS.md“汇总”表）

被测提交 `f0c5886a9d4c8b47d64640e1f7eaeac44be3c388`，在只读 worktree `D:\RubbingMind-wt\qa-baseline` 执行；后端 127.0.0.1:8740，前端 127.0.0.1:5740。

| 编号 | 测试 | 退出码 | 结论 |
|---|---|---|---|
| BT-01 | `python -m pytest tests -q -p no:cacheprovider` | 0 | 通过：124 passed, 1 warning（22.31s） |
| BT-02 | `python scripts/validate_museum_v3.py` | 0 | 通过：passed=true，28 件，84 张，sha256Match=84 |
| BT-03 | `python scripts/validate_history_gis.py` | 0 | 通过（脚本只输出逐点状态，没有总体 passed 字段） |
| BT-04 | `python scripts/test_graph_browser.py`（8740/5740） | 0 | 通过：status=passed，3 个视口，24 项检查，browserErrors=[] |
| BT-05 | `python scripts/test_terrain3d_v22_browser.py`（8740/5740） | 0 | 通过：status=passed，可见省名 31 个，labelOverlaps=0 |
| BT-06a | `python scripts/test_technical_v2_browser.py --url http://127.0.0.1:5740`（完整模式） | 1 | **失败**：390×844 移动端导航超时（RT-001） |
| BT-06b | `python scripts/test_technical_v2_browser.py --ci --url http://127.0.0.1:5740`（CI 模式） | 0 | 通过：6 项检查，pageErrors=[] |
| BT-07 | `npm ci`（apps/web） | 0 | 通过：added 175 packages；audit 显示 9 个漏洞，均为开发依赖（RT-008） |
| BT-08 | `npm run build`（apps/web，`tsc && vite build`） | 0 | 通过：built in 15.64s，有 >500 kB chunk 警告 |
| BT-09 | 后端 8740 启动与主要 API | — | 通过（见下） |
| BT-10 | 安全探测（本机 8740 实例，无破坏） | 0 | 通过，没有发现可利用缺陷；改进项见 REVIEW_FINDINGS |
| BT-11 | 密钥扫描（工作树 + 全部 git 历史） | 0 | 通过：强特征命中 0 条 |
| BT-12 | remote 模式认证探测 | 0 | 通过：fail-closed |
| BT-13 | 干净克隆可运行性 | 见下 | 可运行：后端在 8740 启动，主要 API 全部 200；前端可构建；init_db 重复执行安全。dist 缺失时根路径回退到遗留页面（RT-006）；一键脚本未实测（RT-003） |

BT-00（主工作区数据库完整性）：`data\rubbingmind.sqlite` SHA-256 `8408DBC3…0323D`、`data\runtime\evidence-v2.sqlite` `854DF859…BABD3`，12:07:54 与 12:12:04 两次一致，mtime 均为 2026-10-18。原文如实说明：“没有‘测前哈希’……以 mtime + 测后 SHA 作替代证据”。

补充：AUDIT_ENGINEERING 在后端副本上首次跑 pytest 为“3 failed / 121 passed”（副本缺已跟踪文件 2 个、审计写入 1 个），补齐后“124 passed”。RM-评测科学家汇报其 worktree（agent/eval-sci）上 `134 passed, 1 warning in 15.60s`（来自消息，未写入本文件夹的任何文件；红队复核中）。

## 6. 已验证的正面结论（照各文件原文，不计入缺陷）

- **评测（AUDIT_EVALUATION）**：E-15 无配对参考的真实拓本没有报 PSNR/SSIM；E-16 Top-1/Top-3/拒识率保持“未评测”，没有伪造；E-17 页面上的实验数字从原始 JSON/CSV 重算 0 处不一致，登记影像 SHA 全部一致；E-19 批次内 dev/test 按文物划分、没有重叠（每组 7 件，原文提示统计效力有限）；E-25 失败与负提升都保留着，没有删除，也没有改成 0。
- **工程（AUDIT_ENGINEERING“已验证无缺陷”）**：上传校验全部符合预期；请求体 >18MiB 返回 413；路径穿越全部 404/405；文物缺失时不替换样本（404/410）；4000×3000 大图处理 1831ms、峰值 354MB；检索只做抽取式回答，不采纳注入断言；无真值时 psnr/ssim 全为 null 并写明 `measurementBasis`；CORS 只允许 `http://(127.0.0.1|localhost):517x`；PROCESS_LOCK 3 个并发 → 1×200 + 2×429；36/36 接口正常路径 2xx；28 次模拟远程 IP 鉴权检查 fail-closed；用户两个 DB 测前测后 SHA 一致。
- **红队（REVIEW_FINDINGS“已验证通过的安全项”）**：路径穿越 20 条变体全部 404/409；上传 8 类以上异常全部拒绝、无 500；FTS5 参数化，注入文本未改写结论（“多宝塔碑作者是李白吗？”→ contradicted）；React 端唯一的 `dangerouslySetInnerHTML` 在未被引用的 `Latex.tsx`；全部绑定 127.0.0.1；错误响应无 Traceback/路径；密钥：工作树 + 71 个提交强特征 0 命中；remote 模式无 token 时 401。
- **内容（AUDIT_CONTENT“做得好的地方”）**：目录层保守，28 件没有把“未核定”写成“已核定”，异文（赵文原/邓文原）两说保留；`id`、`collectionNumber`、`sourceUrl`、`sourceSha256` 在 28 件中各自唯一；检索不调用语言模型，未核定/待复核/争议字段强制拒答；吴高黎、王诵两件真实馆藏与演示样本 wei-yuanhuai、wei-jianyi 显式隔离（`demo_only`）。
- **资产**：BT-02 `sha256Match=84`；ASSET_FREEZE.json `museum_image_count.referenced=84 / expected=84`。

## 7. 未完成或未实测的部分（各文件自述）

- 外部视觉模型成功/失败/超时路径：未配置密钥，未实测（ENG §5、C-18、ACCEPTANCE P5-6）。
- start.ps1 / start.bat 未实跑（端口从 8000 起、不可指定）。
- 全新 venv 安装 requirements.txt 未验证（BT-13）。
- PDF/JSON/CSV 一致性、并发 429 之外的竞态、移动端检索流程尚未验证。
- v2.1 改动是否“按测试集数值调参”：只证明了时间先后，因果未证（E-01、RV-E01）。
- 台北故宫页面超时/403，相关著录“未能核实”（AUDIT_CONTENT §0）。
- 评测审计“待核”：`graphSelection.ts:19` 的 0 值是否会渲染成“PSNR: 0 dB”（未起前端验证）。
