# TASK_BOARD — 当前任务分派

- 作者：Green（Agent 01，总协调）
- 快照时间：**2026-10-19 12:15（Asia/Shanghai，UTC+8）**；12:19 补充了 Git 观察（见 §6）
- 规则：每个 Agent 只在自己的 worktree/分支写代码；实测用自己的端口和 DB 副本，起前端必须设 `RUBBINGMIND_API_TARGET`；不 push、不合并；完成或遇阻用 SendToAgent（priority:true）报 Green。
- 状态取值：进行中 / 待开始 / 待复核 / 待用户决定 / 完成

## 1. RM-评测科学家（Agent 04+05）· 分支 `agent/eval-sci` · worktree `D:\RubbingMind-wt\rm-eval-sci`

| # | 任务 | 关联 | 状态 | 验收标准 |
|---|---|---|---|---|
| ES-1 | REPORT_DATA_SPEC v1（六层数据契约、四级结论分级、三项强制更正、§8 后端字段） | E-01/02/03、SPEC | 完成（待红队复核） | 已交 `REPORT_DATA_SPEC.md` |
| ES-2 | 原图返回/实际处理判据（pixel-equal-v1）、4 个批次 derived/applied_status、同批复测改名、compare_v21 排除表扫描全部历史批次 | P0-05、P0-06 | 完成，commit `f21ceaa`（待红队复核） | 红队复核通过；主工作区 `experiments/results` 哈希清单不变 |
| ES-3 | **按文物聚类 bootstrap CI**（每个方法 × 划分 × 退化），写入派生文件；配对增益 CI 下界 >0 才能写“提升” | P0-09、SPEC §0.3 | 进行中 | 派生文件含 artifactN、CI；与 v2 已有 psnrCI95 口径可对照 |
| ES-4 | **机制层代表案例**：挑选代表样本，给出真实的频谱、周期峰、陷波位置、二值前景、骨架、边缘、门控决策数据（只用真实执行步骤，缺的标“未记录”） | P1-07（E-18） | 进行中 | 每张图注明来源文件、批次、生成时间；不伪造 |
| ES-5 | **E-04 负提升原因改为测量量推导**（不再按退化标签套写） | P1-01 | 进行中 | 每条原因有测量依据；启发式归因显式标注 |
| ES-6 | **E-05 修正**：陷波“不适用”分支不得改像素（截断问题） | P1-02 | 进行中 | 单测：未检出峰时输出与输入逐像素相同；历史结果不覆盖，新数据用新批次目录 |
| ES-7 | `experiment_registry.py` 的改动（displayName、heldOut:false、派生导出）是否保留 | — | 待复核（先保留，等红队复核，见 GROUP_DISCUSSION 12:09） | 红队结论 |

## 2. RM-报告前端（Agent 08+09）· 分支 `agent/report-frontend` · worktree `D:\RubbingMind-wt\rm-report-frontend` · 端口 8720/5720

| # | 任务 | 关联 | 状态 | 验收标准 |
|---|---|---|---|---|
| RF-1 | Phase 1 报告页重构（在自己的 worktree） | Phase 1 | 进行中 | ACCEPTANCE_MATRIX P1-1~P1-9 |
| RF-2 | 上下文栏 + URL 参数 `steleId` / `runId` / `experimentId` / `batch`（在报告组件内实现；App.tsx 接入点归架构后端） | P0-02 | 进行中 | 复制 URL 到新标签页打开同一文物、运行、批次；切换文物清空 runId |
| RF-3 | 全局评测 与 单件报告 分层 | P1-12 | 进行中 | 标题与背景明确区分；全局区块标“与当前文物无关” |
| RF-4 | ECharts 横向比较（分轴、不截断、负值保留、指标方向、n 与 CI） | P1-08、P0-09 | 进行中 | 图上可见零线和负值；同轴不混量纲 |
| RF-5 | 同步缩放/拖动的三联对照（参考/退化/输出），差分热图只用真实像素差；无图批次说明原因 | P1-03 | 进行中 | metricsOnly 批次显示“本批次只存数值，未保存图像” |
| RF-6 | 失败案例独立入口 | P1-10 | 进行中 | 每个批次能看到全部负提升行 |
| RF-7 | A4 纵版打印/导出：反映当前选择、图题、来源与局限；JSON 与 PDF 数值一致 | P0-08 | 进行中 | PDF 首页写明 experimentId、筛选、n/CI |
| RF-8 | 首页核心样本卡 `object-cover` → `object-contain` + 纸色衬底；改前改后截图交用户确认 | P1-15 | 进行中（**合并前需用户确认截图**） | 截图 1920×1080 / 1440×900 |
| RF-9 | 页脚“复原”改为“增强与辅助释读” | 专题 H | 进行中 | 截图核对 |
| RF-10 | “同批复测 v2.1”命名：UI、导出文件名、tooltip 不出现“留出/held-out” | P0-06、SPEC §1(a) | 进行中 | 全仓 UI 文案 grep |
| RF-11 | 原图返回的显示文案（`isPassthrough=true` → “本次未改动原图”） | P0-04、SPEC §8 | 进行中（依赖架构后端字段） | tang_01_duobao 最新运行报告与 PDF 出现“未修改” |

## 3. RM-架构后端（Agent 02+10 + Git 集成）· 分支 `agent/arch-backend` · worktree `D:\RubbingMind-wt\rm-arch-backend` · 端口 8710/5710

| # | 任务 | 关联 | 状态 | 验收标准 |
|---|---|---|---|---|
| AB-1 | 数据路径环境变量（`RUBBINGMIND_DB_PATH`、`_RUNTIME_DIR`、`_UPLOAD_DIR`、`_RESULTS_DIR`）+ 安全的 Vite 代理 | P1-22、ADR R1-7 | 进行中（12:19 观察到 commit `32b2360`，待红队验收） | 不设变量时 pytest 原样通过；设变量时写入只落指定目录、用户两个 DB SHA 不变 |
| AB-2 | P0：运行排序 + legacy 标记 + `runSelection` | P0-01、ADR R1-1 | 待开始 | tang-duobao 默认 `20261018T072201_13772747` |
| AB-3 | P0：SPEC §8 的 `isPassthrough` 等字段 + `main.py:382` 文案三态 | P0-04、ADR R1-2 | 待开始 | 恒等输出 `isPassthrough=true`、`changedPixelRatio=0` |
| AB-4 | P0：批次元数据（splitAvailable、status、defaultForReport） | P0-07、ADR R1-3 | 待开始 | 4 个批次 status 依次为 historical-leakage、valid、valid、metrics-only |
| AB-5 | 各批次诊断接口 | P1-10、ADR R1-4 | 待开始 | 4 个批次 diagnosis 均 200 |
| AB-6 | ID 映射接口（`rm:demo:`、`id_mapping.json` 只读加载、馆藏 graph 返回 steleId、聚合带 `sourceSteleId`） | P0-03、ADR R1-5 | 待开始（映射内容由金石史料产出） | 空映射下结果与改动前相同（加 sourceSteleId 除外） |
| AB-7 | App.tsx URL / runId 接入点、api.ts 接入点 | P0-02、ADR R1-6 | 待开始（ADR R1-8 步骤 d 原记为“暂不做（等 Green 指令）”；按 Green 当前分派列入） | 前端 P0-2 验收 |
| AB-8 | 之后：P1（P1-17~P1-25 中归后端的项）+ RT-002/003/004/005/006/009/010/013 | §3 P1、§4 P2 | 待开始 | 各条验收标准 |
| AB-9 | 最后：零行为变化的 router 拆分（main.py → routers，api.ts → services），36 个操作不变 | 已批准 | 待开始（P0 之后；ADR 记为 P0、P1 之后） | openapi 前后一致；全量测试通过 |

## 4. RM-金石史料（Agent 03+06+07）· 分支 `agent/jinshi` · worktree `D:\RubbingMind-wt\rm-jinshi` · 端口 8730

| # | 任务 | 关联 | 状态 | 验收标准 |
|---|---|---|---|---|
| JS-1 | C-03：wei-jianyi 合成文本标为合成测试文本（数据、API、检索、UI） | P0-11 | 进行中（12:19 观察到 commit `b5c5d9a`，待红队验收） | `/api/steles/wei-jianyi/infer` 无 `clear`/`transcript` |
| JS-2 | C-02：演示样本无来源史实改为有来源/未核定/异文并列 | P0-10 | 进行中（commit `d1f9654`，待红队验收） | `core_samples.json` 无缺 sourceId 的史实字段 |
| JS-3 | C-01：`rm:demo:` 命名空间 + `id_mapping.json`（关系需人工复核才参与聚合） | P0-03 | 进行中（commit `195bf97`，内容为草案，待审核） | 演示 ID 响应不出现馆藏影像路径与编号 |
| JS-4 | C-17 / C-18：knowledge_agent 错误史实与纪年换算；残字提示词隔离方案 | P1-33、P1-34 | 待开始 | 纪年换算只有一个实现；注入用例在 mock 模型下无伪链接 |
| JS-5 | 检索冲突（C-05）、别名/简繁/简称（C-15）、status 与 judgment 一致（C-04） | P1-26、P1-27、P1-32 | 待开始 | 回归集 #2 #3 #4 #5 |
| JS-6 | SQLite 与目录只读一致性核对（C-08），出差异核对方案交用户决定；**不直接改用户数据库，不改 28 件“已批准”状态** | P1-23、P1-28 | 待开始 | 核对报告 |

## 5. RM-红队QA（Agent 11+12）· 只读 worktree `D:\RubbingMind-wt\qa-baseline` · 端口 8740/5740

| # | 任务 | 关联 | 状态 | 验收标准 |
|---|---|---|---|---|
| QA-1 | 独立复核其他三份审计的 P0：AUDIT_FRONTEND、AUDIT_ENGINEERING、AUDIT_CONTENT | P0-01/02/03/07/08/09/10/11 | 进行中 | REVIEW_FINDINGS 追加 RV-F*/RV-ENG*/RV-C* 条目 |
| QA-2 | ASSET_FREEZE.json 抽样复核（重新计算一部分 SHA-256） | §1 | 进行中 | 抽样不一致数为 0，或列出不一致项 |
| QA-3 | 复核 `agent/eval-sci@f21ceaa`（含 experiment_registry.py 改动、134 passed 的复现） | ES-2、ES-7 | 进行中（12:19 观察到 worktree `D:\RubbingMind-wt\qa-evalsci` @ f21ceaa） | 复核结论写入 REVIEW_FINDINGS |
| QA-4 | RT-002 严重度复审（P1 还是 P0） | P1-35 | 进行中 | 结论与理由 |

## 6. Git 观察（Green 12:19 实测，只读）

| 分支 | 提交 | 相对 feature 领先 | 远程是否包含 |
|---|---|---|---|
| `agent/eval-sci` | `f21ceaa`（12:07:25）“eval-sci: separate passthrough from processing, derived applied status, same-batch retest naming” | 1 | 否 |
| `agent/arch-backend` | `32b2360`（12:18:10）“feat(runtime): RUBBINGMIND_* data path overrides and loud Vite proxy default warning” | 1 | 否 |
| `agent/jinshi` | `b5c5d9a` C-03、`d1f9654` C-02、`195bf97` C-01（均 12:17） | 3 | 否 |
| `agent/report-frontend` | `f0c5886` | 0 | — |
| `feature/product-grade-upgrade` / `main` / `origin/main` | `f0c5886` | — | — |
