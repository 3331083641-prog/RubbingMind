# AUDIT_FRONTEND —— Phase 0 前端与 UI/UX 只读审计（重点：算法评测报告页）

- 作者：RM-报告前端（Agent 08+09）
- 审计时间：2026-10-19 11:38–12:02（Asia/Shanghai，UTC+8）
- 仓库：`D:\RubbingMind`，分支 `feature/product-grade-upgrade`，HEAD `f0c5886a9d4c8b47d64640e1f7eaeac44be3c388`（与任务指定的 f0c5886 一致，所以直接读工作区文件；源码另用 `git archive f0c5886` 导出副本读取）
- 性质：只读审计。没有改代码、没有建 worktree、没有提交/推送/切分支。只新写了本文件和 `screenshots/product-upgrade/phase0-frontend/` 下的截图。
- 证据等级：**已验证**（命令或截图实测）/ **代码证据**（只读源码得出，未在浏览器复现）/ **待核实**

---

## 0. 执行过的命令清单（真实执行，输出摘要）

| # | 命令（在笔记本 PowerShell 上执行，另注明的除外） | 输出摘要 |
|---|---|---|
| 1 | `git -C D:\RubbingMind rev-parse HEAD; branch --show-current; status --short` | `f0c5886a…`，`feature/product-grade-upgrade`；已跟踪文件无改动，只有 BRIEF 第 0 节列出的那些未跟踪文件，外加 `docs/product-upgrade/` |
| 2 | `git ls-files apps/web/src` 加逐文件行数统计 | 45 个文件；ReportsPage.tsx 110 行，ExperimentExplorer.tsx 45 行，HeldoutComparison.tsx 64 行，WorkbenchPage.tsx 806 行 |
| 3 | `git archive --format=zip f0c5886 apps/web/src main.py experiment_registry.py experiments/... data/catalog/glyph-benchmark-v2.json ...` → 临时目录 → CopyToBox | 用于逐行阅读的只读副本 |
| 4 | `Get-NetTCPConnection -State Listen`（端口 5180/8000/5720/8720） | 只有 **8000** 在监听（PID 30712，用户进程）；**5180 没有在跑** |
| 5 | `curl.exe -s http://127.0.0.1:8000<path>`（只发 GET，共 22 个端点，见 §2.6） | 除 `/api/experiments/controlled-rubbings-v2-2026-10-17/diagnosis` 返回 404 外，其余都是 200 |
| 6 | `python -m playwright --version` | `Version 1.63.0`；自带 chromium-headless-shell 不存在，退回 `channel="msedge"` |
| 7 | `node vite.js --config C:\Users\WPY11\rm-report-frontend-tmp\vite.audit.config.mjs`（root=apps/web，port 5720 strictPort，cacheDir 指向 tmp，/api 和 /static 代理到用户的 8000） | `VITE v5.4.21 ready`，PID **44980**；源码、package.json、lock 都没改 |
| 8 | `python C:\Users\WPY11\rm-report-frontend-tmp\capture.py`（Playwright + Edge headless） | 在 1920×1080 和 1440×900 两种分辨率下截图，生成 21 张 PNG 和 1 份打印 PDF，另记录 DOM 探针 JSON |
| 9 | `Stop-Process -Id 44980`（停止前核对过它的命令行确是自己起的 vite） | 5720 已释放，8000 仍在（未触碰） |
| 10 | 在 box 上执行 `pdfinfo/pdffonts/pdftotext 11_reports_print_tang-duobao_A4.pdf` | A4、**1 页**，嵌入 Noto Serif SC 和 PingFang SC，内容只有单次运行 article |
| 11 | `git grep -n -A12 "def list_runs" f0c5886 -- museum_processing.py` | 排序键 `finishedAt`，倒序（见 P0-1） |
| 12 | `git show f0c5886:data/catalog/core_sample_links.json` | tang-duobao↔tang_01_duobao 的关系是 `same_work`，备注写明“不证明为同一馆藏拓本” |

---

## 1. 结论速览

- 报告页现在是一条纵向长页（1920 下实测 docHeight≈3270px），顺序是：留出实验表 → 实验浏览器表 → 单件纸面报告。**没有用 ECharts，没有视觉对照的交互，没有机制层，没有失败案例入口。PDF 只包含单次运行那部分。**
- 现有文案对“无真值不报指标”总体比较守规矩：PSNR/SSIM 为空时显示“未评测”，OCR 写“未评测”，glyph-evaluation API 返回 `not_evaluated`。主要风险不在措辞，而在**数据绑定和统计呈现**：默认运行选错、全局与单件不分层、“test”分组名不副实、原图直出被当成“算法输出”、没有 CI 和 Δ。
- 条数统计：**P0 6 条，P1 15 条，P2 7 条**。

---

## 2. 五页现状：组件树、数据来源、ID 传递

### 2.1 全局壳（App.tsx）
- 组件树：`App` → `Header`（导航 + “当前碑刻”下拉）→ `main` 中按 `currentTab` 条件渲染五页 → `Footer` → `UploadModal`。
- **路由**：没有路由库，也没有 URL 状态。`currentTab` 和 `selectedSteleId` 都只是 React state（App.tsx:17、19）。全仓 `localStorage/sessionStorage/URLSearchParams/history.pushState` 的 grep 只命中一处 `SteleViewer.tsx:259 ?steleQA=1`（QA 开关）。**刷新会回到首页加默认文物，也无法深链到报告的某个运行或实验。**
- 默认文物：`'tang-duobao'`（核心演示样本，coreSamples.json），不是馆藏 `tang_01_duobao`（App.tsx:19）。
- 数据：`SteleService.getSteles()` 请求 `/api/steles`，失败时静默回退到 `data/steles28.json`（api.ts:36–38，`FALLBACK_STELES`）。实测后端返回 31 条（28 条 verified_review_v3 + 3 条 user_upload），`data-catalogue-status="ready"`。
- 页间唯一共享的 ID 是 `selectedSteleId`。工作台和报告都以 `key={currentStele.id}` 重新挂载（App.tsx:94、111）。**runId、experimentId、inferenceId 都不跨页传递。**

### 2.2 首页 HomePage.tsx
- 组件树：`HomeAmbientBackground`（视频）+ hero 文案 + 4 张统计卡 + `SteleViewer`（Three.js 碑模）/ `SteleFullscreenViewer` + 3 张能力卡 + “核心测试碑拓标本”4 卡。
- 数据：统计卡由 `steles` 实时计算（28 件、7 个时期、4 件核心样本、28 件有来源）；核心样本卡来自静态 `coreSamples.json`。
- 发现：核心样本卡的图片用了 `object-cover`（HomePage.tsx:249），并显示 `PSNR: {psnr ?? '未评测'} dB`（:269），实际会渲染成“PSNR: 未评测 dB”。见 P1-12、P2-1。

### 2.3 典藏馆 MuseumPage.tsx
- 组件树：banner（`bg_museum_hall_v2.webp`，background-size cover，装饰图）→ 朝代/损伤筛选 → 28 张卡（`museum-card`）→ `RubbingArchiveViewer` / `AssessmentViewer` / `SteleFullscreenViewer` 弹层。
- 数据：App 中 `steles.filter(source_kind==='verified_review_v3')`（App.tsx:85）；AssessmentViewer 调 `/api/catalog/{id}/assessment`。
- 实测：28 张卡，封面 `objectFit=contain`（DOM 探针已验证），PSNR 位置在 null 时显示“未评测”，不带单位（MuseumPage.tsx:322）。
- 跳转：“微痕修复”调用 `onSelectStele(id)` 后进入 workbench（:114–115）；“时空图谱”跳到 graph（:400–401）。只传 steleId。

### 2.4 工作台 WorkbenchPage.tsx
- 组件树：状态行 → 运行历史下拉（`选择运行记录`）→ 左栏图像画布（split/side/clean/cinnabar/skeleton 五种模式，金色激光扫描线）+ 指标条 + 参数面板 → 右栏 `GlyphInferencePanel`、自适应诊断 `<details><pre>JSON`、释文卷轴、候选面板。
- 数据：`/api/steles/{id}/infer`（失败时回退到预置释文，api.ts:49–51），`/api/steles/{id}/runs`，`POST /api/process`，以及残字相关 API。
- 运行 ID：`selectedRunId` 是页内 state（:45），处理成功后 `setSelectedRunId(result.runId)`（:146）。**不会回传给 App，也不会传到报告。**进入页面时默认不选任何运行（实测 tang_01_duobao 下 `runSelect=""`）。
- 指标条：`{psnr ?? '未评测'} dB`、`(+{snr_gain ?? '未评测'}dB)`、`{glyph_completeness ?? '未评测'}%`、“字符识别率: {character_accuracy ?? '未评测'}%”（:491–507）。见 P1-11。

### 2.5 图谱 GraphPage.tsx / VerifiedMuseumGraph.tsx
- 分支（App.tsx:100–107）：当前文物是 `verified_review_v3` 时渲染 `VerifiedMuseumGraph`，只有影像、著录和 EvidenceSearch，**没有 GIS 和 Three.js**；4 件核心样本渲染 `GraphPage`（MapLibre + Three.js 地形 + ECharts KnowledgeNetwork + 时间轴 + 纪年换算）。
- 数据：`loadHistory` 先请求 `/api/steles/{id}/graph`，失败时回退到 `data/history/*.json` 静态导入（services/history.ts:11–30）；EvidenceSearch 调 `/api/research/steles/{id}` 和 `POST /api/research/query`。
- 实测：tang-duobao 在 1920/1440 下 `canvas=2`（Three.js 地形渲染正常）；tang_01_duobao 进入的是 VerifiedMuseumGraph，`canvas=0`。
- ID：`resolveCoreId` 把 `tang_01_duobao` 映射为 `tang-duobao`（graphSelection.ts:2–9）。core_sample_links.json 标的是 `same_work`，备注“不证明为同一馆藏拓本”。截图 04 显示，核心样本的图谱右栏展示的是“数字拓本 台北故宫博物院 / 赠拓000365”的影像和编号。**这是作品层与拓本层的界线问题，待金石学和数据治理核实（P1-15）。**

### 2.6 报告页 ReportsPage.tsx（重点）
- 组件树（ReportsPage.tsx:59–112）：
  1. `header`：标题，“导出 JSON”（:64，前端拼装），“打印 / 保存 PDF”（:65，`window.print()`）
  2. 运行下拉 `选择报告运行记录`（:68–74），选项为“尚未执行”加 runs
  3. `<HeldoutComparison/>`（:76），全局，**带 print:hidden**
  4. `<ExperimentExplorer/>`（:77），全局，**带 print:hidden**
  5. `<article>` 单件纸面报告（:78–112）：馆藏身份与出处 → 处理与评测（参数用 `<pre>JSON`，诊断变化量也用 `<pre>JSON`，输出图 object-contain）→ 残字推演 → 古碑识别（硬编码“未评测”）→ footer
- 数据来源：

| 区块 | 来源 | 位置 |
|---|---|---|
| 运行列表 | GET `/api/steles/{id}/runs` | ReportsPage:19；main.py:387；museum_processing.py:90–97 |
| 单件报告 | GET `/api/steles/{id}/report?run_id=` | ReportsPage:26；main.py:371–384；后端不可用时回退到静态 steles28 拼装（api.ts:59） |
| 留出对比 | GET `/api/experiments/heldout-v20-v21-2026-10-18`、`/diagnosis`（ID **硬编码**） | HeldoutComparison:37–38；main.py:170、187 |
| 实验浏览器 | GET `/api/experiments` → `/api/experiments/{id}` → `/assets/{file}`、`/export/{kind}` | ExperimentExplorer:12、14、18、42；experiment_registry.py |
| OCR 状态 | **硬编码文案**，没有调用 `/api/glyph-evaluation` | ReportsPage:110 |
| glyph-benchmark-v2.json | 前端**没有任何引用**；只被 experiments/evaluate_glyphs.py 使用 | — |
| `report.ablation` | API 返回 `[]`，前端没有渲染 | api.ts:57 |

- API 实测（GET，端口 8000）：

| 端点 | HTTP | 大小 | 摘要 |
|---|---|---|---|
| /api/health | 200 | 144B | `{"status":"healthy","version":"2.0.0"}` |
| /api/experiments | 200 | 36.9KB | 4 个批次：controlled-rubbings-2026-10-15（2 件/80 行，historicalWarning=先验泄漏），controlled-rubbings-v2-2026-10-17（14/1260），controlled-rubbings-v2-text-2026-10-17（14/1260），heldout-v20-v21-2026-10-18（14/490，**metricsOnly=true**） |
| /api/experiments/heldout-v20-v21-2026-10-18 | 200 | 390KB | 490 行，**所有行都没有 split 字段**；也都没有 input/output 图像；summary 有 42 组（7 方法×6 退化），**没有 CI**；带 baselineCommit/candidateCommit/environment |
| …/heldout…/diagnosis | 200 | 7.7KB | adaptive_v21：negativeLift 16，unchanged 21，causeCounts{本身信息不可恢复 9，算子或参数不适合 5，频谱检测不可靠 2}，含逐 case 列表 |
| /api/experiments/controlled-rubbings-v2-2026-10-17 | 200 | 1.49MB | 1260 行，split development 630 / test 630；applicability：applied 1016 / baseline 140 / not_applicable 104；全部行都有输出图和 SHA；summary 18 组，**带 psnrCI95 等** |
| …/v2-2026-10-17/diagnosis | **404** | 46B | “没有这份实验的失败诊断”（只有 heldout 有诊断） |
| /api/experiments/controlled-rubbings-2026-10-15 | 200 | 35.8KB | 80 行，没有 split；applicability 中有 `notch_applied` 2 条 |
| …/heldout…/export/summary.csv、results.csv；…/v2…/export/summary.csv | 200 | 5.8KB/204KB/6.5KB | text/csv |
| /api/glyph-evaluation | 200 | 229B | `status:not_evaluated, top1:null, top3:null, verifiedLabels:0` |
| /api/steles | 200 | 374KB | 31 条 |
| /api/steles/tang-duobao/runs | 200 | 12.6KB | 4 条；**前两条是 legacy-unverified，finishedAt="未记录"** |
| /api/steles/tang-duobao/report | 200 | 2.9KB | 默认 run=`20261014T165542_5fc44fba`（legacy），diagnosticMetrics `{}` |
| /api/steles/tang_01_duobao/runs | 200 | 54.8KB | 10 条 v2.0/v2.1；**每一条的 input_output_mean_absolute_difference 都是 0.0**，最新一条 decisions=`skip_notch, identity` |
| /api/steles/tang_01_duobao/report | 200 | 9.3KB | run=`20261018T082526_4728b9df`，inferenceRecords 1 条 |
| /api/steles/han_01_caoquan/report | 200 | 746B | run=null，“尚未执行处理；配对质量未评测。” |
| /api/catalog/tang_01_duobao/assessment | 200 | 10KB | 归档评估记录 |
| /api/steles/tang-duobao | 200 | 4.4KB | 核心样本存在于后端 |
| /api/steles/wei-jianyi/runs | 200 | 2KB | 1 条 legacy |
| /api/research/steles/tang_01_duobao | 200 | 17KB | 关系图 |

### 2.7 页间 ID 与“同一文物/同一运行”结论（专题 F）
- **同一文物**：五页共用 `selectedSteleId`，所以文物是一致的。但存在两套命名空间：核心样本 `tang-duobao` 与馆藏 `tang_01_duobao`。实验数据的 `sampleId` 用馆藏 ID；报告页**不会**把当前文物和它在实验批次中的行关联起来（比如 tang_01_duobao 在 v2 批次里有行，报告中看不到）。
- **同一运行**：**不共享。**工作台的 `selectedRunId` 是局部 state；报告页自己取 `runs[0]`。实测 tang-duobao：工作台未选运行，报告却默认选中 legacy 运行 `20261014T165542_5fc44fba`。

---

## 3. 发现清单

格式：位置 / 实测 / 缺陷 / 影响 / 修复路径 / 验收标准。

### P0（正确性 / 真实流程 / 可信交付）

**P0-1 报告默认绑定的是 legacy-unverified 旧运行，不是最新运行**
- 位置：ReportsPage.tsx:19–20（`setRunId(items[0]?.runId)`）；museum_processing.py:97（`sorted(key=finishedAt, reverse=True)`）；main.py:375（后端默认也取 `runs[0]`）
- 实测（已验证）：`/api/steles/tang-duobao/runs` 的顺序是 `20261014T165542(未记录)`、`20261015T013329(未记录)`、`20261018T072201(2026-10-18…)`、`20261017T093048(…)`。字符串“未记录”倒序时排在 ISO 时间前面，legacy 运行于是排到第一位。默认文物进入报告时，下拉值为 `20261014T165542_5fc44fba`，PDF 写的是“算法版本：legacy-unverified；开始：未记录；输入 SHA-256：未记录”。截图 05、10、11。
- 缺陷：排序键混用了字符串和时间，默认选择没有校验运行是否可信。
- 影响：用户打开“算法评测报告”看到并导出的，是一条没有 SHA、没有时间的旧记录，可信交付失败。
- 修复路径：后端按解析后的时间排序，无时间的记录排最后并标 `legacy`；前端默认选“最近一条 verified 运行”，或者来自工作台的 runId（见 P0-2）；legacy 运行加显式徽标“旧版未验证”，并禁止作为默认。需要后端 Agent 负责 museum_processing.py。
- 验收：对 tang-duobao，默认 runId 应为 `20261018T072201_13772747`，或者为空并提示“请选择”；legacy 只能手动选择，并带警示；补一条单元测试覆盖“未记录”排序。

**P0-2 工作台与报告不共享运行 ID，也没有可深链状态**
- 位置：App.tsx:17–19、94、111；WorkbenchPage.tsx:45、146；ReportsPage.tsx:13、20
- 实测（已验证）：tang_01_duobao 下工作台 `runSelect=""`，报告默认 `20261018T082526_4728b9df`；tang-duobao 下工作台为空，报告为 legacy。刷新后 `data-tab=home`。
- 缺陷：报告展示的运行不一定是用户刚在工作台执行的那条；URL 中没有 steleId/runId/experimentId。
- 影响：违背 Phase 4 和专题 F 的要求；跨页会串结果；评审无法复现链接。
- 修复路径：在 App 层（共享文件，交架构 Agent）加 `activeRunId` 和 URL hash/query，形如 `?tab=reports&stele=…&run=…&exp=…`；工作台处理成功或选择运行后回写；报告读这个值，没有时再用 P0-1 的规则。
- 验收：在工作台运行后点“报告”，下拉值等于新的 runId；复制 URL 到新标签页，打开的是同一文物、同一运行、同一实验批次；切换文物时 runId 清空，不串号。

**P0-3 “原图直出”被当成“算法输出”展示**
- 位置：ReportsPage.tsx:99（“本次算法输出；不作为原刻真值”）；ExperimentExplorer.tsx:40（not_applicable 的行仍标“本方法输出”）
- 实测（已验证）：tang_01_duobao 的 10 条运行，`input_output_mean_absolute_difference=0.0`、`tenengrad_change_percent=0`；最新运行 `decisions=[skip_notch, identity]`、`fidelityGate.meanAbsoluteChange=0`；截图 13 显示整幅输出图，看不出它和输入完全一样。实验浏览器截图 08 中 `han_02_yiying/gaussian/0.65/notch` 的 applicability=`not_applicable`，三联图仍标“本方法输出”。
- 缺陷：没有区分原图返回和实际处理，违反 BRIEF Phase 1 统计要求中的“区分原图返回与实际处理”。
- 影响：用户会以为算法对这件文物做了修复。
- 修复路径：报告读取 `adaptiveDiagnostics.decisions`、`fidelityGate`、`diagnosticMetrics.input_output_mean_absolute_difference`，为 0 时显示“算法判定不修改：输出与工作输入像素一致”（AssessmentViewer.tsx:110 已有同类文案可复用）；实验浏览器对 `not_applicable/baseline` 标“未处理（原图计入）”。
- 验收：tang_01_duobao 最新运行的报告和 PDF 都出现“未修改”标识；not_applicable 的行不再出现“本方法输出”。

**P0-4 留出批次“数据分组=test”名不副实**
- 位置：ExperimentExplorer.tsx:10（默认 `split='test'`）、:15（`(!split||!r.split||r.split===split)`）
- 实测（已验证）：heldout 的 490 行和 2026-10-15 的 80 行都没有 `split` 字段，过滤器让它们全部通过；界面默认显示“数据分组 test”，表中“输入数 70”。截图 06、09。
- 缺陷：没有 split 的批次被标成 test，会误导读者以为这是独立测试集。heldout 批次自己在 limitations 里写的是“仍是同一批 28 件阅读图，不是新的外部隐藏集”。
- 影响：dev/test 区分失真，违反统计铁律。
- 修复路径：批次没有 split 时禁用这个过滤器，显示“本批次未划分 dev/test（见限制）”；有 split 时列出两组，并默认 test，同时注明“阈值不得依此调参”。
- 验收：选 heldout 或 2026-10-15 时不再出现 test 标签；选 v2 时 test 行数为 630。

**P0-5 PDF/JSON 导出不包含全局评测，也不反映当前选择**
- 位置：HeldoutComparison.tsx:51、ExperimentExplorer.tsx:21（`print:hidden`）；ReportsPage.tsx:34–58（JSON 不含实验批次和过滤器）、:65（`window.print`）、:81（生成时间取 `new Date()`）
- 实测（已验证）：Edge headless 以 print media 输出 `11_reports_print_tang-duobao_A4.pdf`，**1 页 A4**，只有单件 article，没有任何算法比较、样本数、CI、限制、图题或编号；字体嵌入正常（Noto Serif SC、PingFang SC）。
- 缺陷：没有达到 BRIEF 的 PDF 要求（反映当前选择、图题、来源与局限）。
- 影响：交付件里看不到评测结论，或者被误当成完整评测报告。
- 修复路径：设计报告专用的打印布局（见 IA §6.6），把当前 experimentId、过滤条件、所选 runId、图表静态快照、图题、来源和局限都纳入；JSON 导出补 `experimentId/filters/split/summary 引用/exportedAt(+08:00)`。
- 验收：选定批次和过滤条件后打印，PDF 首页写明 experimentId、筛选、n/CI；图表带编号和图题；JSON 与 PDF 的数值一致，有自动比对脚本。

**P0-6 比较只用绝对均值，没有 CI 和相对输入 Δ，容易读成“普遍优势”**
- 位置：HeldoutComparison.tsx:46、61–63；ExperimentExplorer.tsx:16、20、36–37（“95% CI 见导出 summary”）
- 实测（已验证）：heldout 的“全部”视图中 adaptive_v21 的条最长（PSNR 28.98）。但 experiments/results/2026-10-17-v2/error-analysis.md 写的是“独立测试组 SSIM 不优于输入……不能宣布普遍优越”，test/gaussian 的 adaptive_joint ΔdB 为 −0.293 [−1.088, 0.373]，test/occlusion 为 −4.172，10/14 劣于输入。这些在 UI 里都看不到。实验浏览器的均值和标准差按行计算（每件文物 2 档强度、5 种退化），不是按文物聚类（ExperimentExplorer:16）。
- 缺陷：违反 BRIEF 统计要求（按文物分组 CI、样本数、正负提升都保留、不跨批次解读）。
- 影响：评审很可能得出没有被证据支持的结论。
- 修复路径：比较图默认展示“相对输入 ΔPSNR/ΔSSIM（按文物配对）+95% 聚类 CI + 负提升数”，绝对值作为次级视图；heldout summary 需要评测科学家补 CI（目前 API 没有）；把 error-analysis 的结论分级显示在研究总览。
- 验收：每个均值旁都有 n（文物数/记录数）和 CI；负 Δ 以朱砂色画在零线左侧；总览中的结论文字与 error-analysis.md 一致，并经评测科学家签字。

### P1

| 编号 | 位置 | 实测 | 缺陷与影响 | 修复路径 | 验收 |
|---|---|---|---|---|---|
| P1-1 | HeldoutComparison.tsx:63；ExperimentExplorer.tsx:36 | 报告页 `canvas=0`，比较条是 div 宽度 `Math.max(0, v/max*100)` | 没有 ECharts；**负值被截成 0**；“细笔画误差/耗时”越小越好，却没有方向提示；条从 0 起，不算截断，但做不了分轴和联动 | ECharts：每种量纲单独成 grid（dB / 0–1 / 像素误差 / ms），yAxis `min` 取数据和 0 的较小者，`scale:false`；负 Δ 保留 | 图上可见零线和负值；同一个轴上不出现两种量纲 |
| P1-2 | ReportsPage 首屏（截图 05，1920/1440） | 首屏只有标题、运行下拉和一张 7×9 的数字表 | 首屏没有核心结论和视觉对照；表格加 `<pre>JSON` 堆叠（参数、诊断都是原始 JSON） | 按 IA §6.4 首屏布局重排 | 1920×1080 和 1440×900 首屏都能看到结论卡、三联对照和 n/CI |
| P1-3 | 全仓 grep `frequency_spectrum` 在 tsx 中 0 处命中 | 运行里有 frequency_spectrum、binary_skeleton、contour、decisions、fidelityGate、features，报告都没有展示 | “消融与机制”层不存在；组件名叫“算法实验与消融分析”但没有消融（`report.ablation` 为空且没有渲染） | 新的 MechanismPipeline 组件，读真实的运行产物 | 点击每个阶段都能看到真实图像和数值，来源 runId 可见 |
| P1-4 | HeldoutComparison.tsx:58；main.py:187 | 诊断只是一行拼接文本；v2 批次 diagnosis 返回 404 | 失败案例没有独立入口；diagnosis 的 cases 列表和 error-analysis.md 都没有展示 | 加 FailureCasesPanel，后端提供各批次的诊断或 error-analysis 接口 | 每个批次都能看到失败或负提升列表及其图像（有图时） |
| P1-5 | ExperimentExplorer.tsx:40 | 三联图是静态 `<img>`，没有同步缩放、ROI、滑杆、差分热图；heldout 没图时三联区域直接消失，不说明原因 | 视觉对照层不达标；空状态不明确 | SyncedTriptych + 差分热图（只用真实像素差） | metricsOnly 批次显示“本批次只存数值，未保存图像”及原因 |
| P1-6 | heldout API 有 baselineCommit/candidateCommit/environment，但 UI 没展示 | — | 可复现性信息缺失：没有源码索引、配置、方法版本，结论也没分级 | 加 ReproducibilityPanel | 每个批次都能看到 commit、seed、config 和 source_snapshot 路径 |
| P1-7 | ReportsPage.tsx:76–78 | 全局实验区块不随文物变化，却放在“本件运行”下拉之后 | 全局评测和单件报告没有分层，用户会以为表格属于当前文物 | 分成两个 tab 或两个锚点区：“全局评测”与“本件处理报告” | 标题和背景色明确区分；切换文物时全局区块标“与当前文物无关” |
| P1-8 | App.tsx:19；core_sample_links.json | 默认是核心样本 tang-duobao；实验 sampleId 用馆藏 ID | 两套 ID，报告不能把“本件在哪些实验里出现”关联起来 | ID 映射表由后端提供；报告中“本件参与的实验”通过 sampleId 关联 | tang_01_duobao 报告能列出它在 v2 和 heldout 中的行 |
| P1-9 | ReportsPage.tsx:71、93；截图 13 | 时间显示为 `2026-10-18T08:25:26.553444+00:00` 原串 | 时区不统一，可读性差 | 统一格式化为 Asia/Shanghai，并保留 ISO 原值供悬停查看 | 页面和 PDF 显示 `2026-10-18 16:25:26 (UTC+8)` |
| P1-10 | ReportsPage.tsx:110 | OCR/Top-1 是硬编码“未评测” | 结论与 `/api/glyph-evaluation` 不联动，将来测出数值也不会显示 | 绑定 API，同时显示 verifiedLabels 数量 | 断网时显示“状态不可用”，不出现假的“未评测” |
| P1-11 | WorkbenchPage.tsx:491–507 | “未评测 dB”“(+未评测dB)”“未评测%”；“字符识别率”标签常驻；snr_gain 强制加 `+` 号 | 单位和空值拼接错误，负值会显示成 “+-x” | 空值不带单位；没有标注集时隐藏“字符识别率”，或改成“识字评测：未评测” | 截图里不再出现“未评测%” |
| P1-12 | HomePage.tsx:249、269–270 | 核心样本卡 `object-cover`（h-48）并 hover 放大 | 拓本被裁切；“PSNR: 未评测 dB”。（**首页属受保护视觉**，修改需 Green 决策） | 改为 object-contain 加深色衬底，或保持现状并在卡片上注明“局部裁切” | 由 Green 决定后验收 |
| P1-13 | ExperimentExplorer.tsx:12 | 默认批次取 `items.at(-1)`（依赖目录名排序）；有泄漏的 2026-10-15 批次排第一，只用一行朱砂字警告 | 历史或作废批次与有效批次并列 | 批次分级：有效 / 历史（有泄漏）/ 只有数值；默认批次由评测科学家指定 | 泄漏批次需要二次确认才能查看，并带水印 |
| P1-14 | ExperimentExplorer.tsx:16 | n=1 时标准差显示 0；均值按行算 | 统计口径错误 | n<2 时显示“—”；按文物聚类 | 单测覆盖 |
| P1-15 | GraphPage（截图 04）；core_sample_links.json | 核心样本 tang-duobao 的图谱展示馆藏拓本“赠拓000365”影像 | 作品、拓本、演示样本的界线**待核实** | 交金石学和数据治理审 | 由对应 Agent 给出结论 |

### P2

| 编号 | 位置 | 说明 | 修复与验收 |
|---|---|---|---|
| P2-1 | HomePage.tsx:269 | “PSNR: 未评测 dB” 单位拼接（与 P1-12 同处） | 空值不带单位 |
| P2-2 | scripts/capture_five_pages.py:15–47 | 使用 `#/museum` 等 hash 路由，但 App 没有路由，脚本已失效 | 改为点击导航；QA Agent 负责 |
| P2-3 | 浏览器 console（1920 轮） | 3 次 `404 (Not Found)` 资源错误，具体 URL **待核实** | QA 记录网络日志 |
| P2-4 | ReportsPage.tsx:81 | “生成”时间取浏览器打印时刻，与运行时间容易混淆 | 改为“导出于（UTC+8）”，并单独列运行时间 |
| P2-5 | graphSelection.ts:19 | 回退对象 `metrics: {psnr:0, ssim:0…}`，当前被去重所以没显示，但留有隐患 | 改为 null |
| P2-6 | ExperimentExplorer.tsx:16、30–32 | 方法顺序不固定，方法名全是英文 ID | 固定顺序，加中文名和字典 |
| P2-7 | ExperimentExplorer.tsx:38 | “单次实验记录”下拉最多 630 项 | 改为可筛选的列表或在图上点选 |

---

## 4. 对照 BRIEF Phase 1 的逐层现状与差距

| 层 / 要求 | 现状（证据） | 差距 |
|---|---|---|
| ① 研究总览 | 没有总览；heldout 段只有一行“样本 14 件·记录 490 条·负提升 15/70、16/70”（HeldoutComparison:57） | 缺核心结论（分级）、实验范围、n、CI、“未评测”项清单 |
| ② 修复效果视觉对照 | 实验浏览器有静态三联（参考/退化/输出，object-contain，截图 08）；单件报告只有输出图 | 缺同步缩放和拖动、ROI、滑杆、方法切换联动、真实差分热图、无图说明；还有原图直出未标注（P0-3） |
| ③ 算法横向比较 | div 条加表格（P1-1）；按退化筛选；每次只看一个指标 | 缺 ECharts、分轴、Δ/CI、负值、筛选联动、按文物聚类 |
| ④ 消融与机制 | 没有（P1-3）；工作台只有 `<details><pre>JSON`（WorkbenchPage:664） | 全部缺失；数据其实已存在于运行产物 |
| ⑤ 失败案例与不确定性 | 只有 heldout 一行诊断文字（P1-4） | 缺独立入口、失败图像、原因分布 |
| ⑥ 科学结论与可复现性 | 有 CSV/JSON 导出（已验证 200），有限制说明 `<details>` | 缺实验 ID 显著展示、commit、seed、config、源码索引、结论分级 |
| 全局 vs 单件分层 | 同一长页，没有分隔（P1-7） | 需要结构上分层 |
| 统计要求 | dev/test 有过滤，但对无 split 的批次失真（P0-4）；没有 CI（P0-6） | 见 P0-4、P0-6 |
| PDF | 1 页，只有单件，中文字体正常（P0-5） | 需反映当前选择，加图题、来源与局限 |
| 风格 | 深墨底 `#0A0D12`、gold、cinnabar、celadon 都在 tailwind 中（tailwind.config.js:18–40）；article 用纸色 `#eee4d2` | 方向一致；问题在表格堆叠和 JSON 原文 |
| 首屏 | 1920 和 1440 首屏只有表格（截图 05） | 见 P1-2 |
| object-fit cover 裁字 | 报告页实测所有 img 都是 `contain`；全仓 cover 只出现在：首页视频（受保护，预期）、首页核心样本卡（P1-12）、UploadModal 预览缩略图（80px，属于预览）、图谱时间轴装饰缩略图（标注“非历史建筑复原”的概念图）、首页/典藏馆背景装饰 | 报告页合规；首页卡片待决策 |
| 误导文案 | 没有发现“已识读/已修复”。“字符识别率”“字形骨架完整度”标签常驻（P1-11）；Footer 写“微痕复原数字实验室”（Footer.tsx:27，品牌语，待 Green 判断） | 低风险 |
| 无真值展示指标 | 28 件馆藏和 4 件核心样本的 metrics 都是 null（已验证，静态 JSON）；所有运行的 evaluationMetrics 都是 psnr/ssim null；受控实验的 PSNR/SSIM 有配对参考，合规 | 合规；呈现方式见 P0-6 |
| 空状态 | 运行为空时显示“尚未执行处理”（真实）；后端不可用时 getReport 回退到静态 steles28 拼装，不报错（api.ts:59），表现为“尚未执行”，**掩盖了后端故障** | 回退时应显示“后端不可用”，不应伪装成“未执行” |

---

## 5. 受保护资产基线（只记录，不评价改动）

| 资产 | 基线（已验证） | 截图 |
|---|---|---|
| 首页视频背景 | `<video>` src=`/assets/home/home-ambient-loop.mp4`，`paused=false`，`readyState=4`，`object-fit:cover`；1920/1440 都在正常播放；HomeAmbientBackground.tsx:158–164 | 01_home_1920x1080.png、01_home_1440x900.png |
| 首页 Three.js 碑模 | SteleViewer 渲染正常，视角按钮和“激光扫描”控件都在 | 01_* |
| 典藏馆影像卡片 | 28 张卡，cover `object-contain`，banner `bg_museum_hall_v2.webp`；“已入库 28 件真实馆藏” | 02_museum_*.png |
| 时空图谱 Three.js 地形 | tang-duobao：canvas=2，地形、国界、省界高亮、小地图、DEM 状态面板都显示；1440 同样正常 | 04_graph_*.png |
| 馆藏图谱（非核心） | tang_01_duobao 进入 VerifiedMuseumGraph，canvas=0（设计如此：不造坐标） | 15_graph_tang_01_duobao_verified_1920x1080.png |

---

## 6. 六维评价（审计者判断，1–5）

| 维度 | 分 | 依据 |
|---|---|---|
| 技术深度 | 3 | 后端实验登记、SHA 校验、受控退化、CI 计算（v2 summary）、诊断 API 都是真实的；前端只把它们呈现为表格 |
| 功能价值 | 2 | 报告页能看数和导出，但看不到机制、失败和对照，也不能把文物与运行闭环 |
| 内容广度 | 3 | 4 个批次、7–9 种方法、5 种退化、14 件文物都有数据；error-analysis、diagnosis、运行中间产物都没接入 |
| 真实性 | 4 | 指标为空就写“未评测”，警告文案到位，限制说明齐全；扣分在 P0-1、P0-3、P0-4 |
| 模块连接 | 2 | 只共享 steleId；runId 和 experimentId 断链，没有 URL 状态，ID 有两套 |
| 视觉交互 | 2 | 配色统一；但表格和 JSON 堆叠，首屏没有结论，没有图表交互 |

---

## 7. 报告页重构信息架构草案（**提案，未实现**）

> 以下只是提案，需经 Green 分派，并由评测科学家和红队质疑后才能实施。组件建议放在 `apps/web/src/components/reports/`，ReportsPage.tsx 只负责组装。

### 7.1 顶层结构
```
ReportsPage
├─ ReportContextBar        当前文物 / 运行 / 实验批次 / 筛选条件（URL 同步），分层切换：[全局评测] [本件报告]
├─ 全局评测 GlobalEvaluation（experimentId 驱动，与当前文物无关，背景深墨）
│  ├─ L1 ResearchOverview       结论卡（分级：已验证/有限支持/未评测/待人工复核）+ 范围 + n/CI + 未评测项
│  ├─ L2 VisualComparison       SyncedTriptych（参考/退化/输出）+ ROI + 滑杆 + 方法切换 + DiffHeatmap + 无图说明
│  ├─ L3 MethodComparison       ECharts：Δ 指标分面（dB / SSIM / F1 / 误差 / ms 各一轴）、负提升、筛选联动
│  ├─ L4 AblationMechanism      阶段条：频谱 → 周期峰 → 陷波位置 → 二值前景 → 骨架 → 边缘 → 门控决策（真实产物）
│  ├─ L5 FailureUncertainty     失败/负提升/原图返回列表 + 原因分布 + 真实失败图像
│  └─ L6 ConclusionReproducibility 实验 ID、样本来源、划分、方法版本/commit、seed、config、导出、source_snapshot 索引
└─ 本件报告 ArtifactRunReport（steleId+runId 驱动，纸色背景）
   ├─ 身份与出处（作品/拓本/原石分层）
   ├─ 本次运行：决策链 + 是否原图返回 + 中间产物
   ├─ 残字推演与人工决策
   └─ 本件参与的全局实验（按 sampleId 关联）
```
组件文件：`ReportContextBar.tsx`、`ResearchOverview.tsx`、`SyncedTriptych.tsx`、`DiffHeatmap.tsx`、`MethodComparisonChart.tsx`（ECharts）、`MechanismPipeline.tsx`、`FailureCasesPanel.tsx`、`ReproducibilityPanel.tsx`、`ArtifactRunReport.tsx`、`ReportPrintLayout.tsx`、`useReportState.ts`（URL 同步）、`format.ts`（时间统一 UTC+8，空值不带单位）。

### 7.2 数据/API 字段需求
- 已有可直接用的：`/api/experiments*`（rows：sampleId/split/degradation/strength/seed/method/applicability/psnr/ssim/edgeF1/input/reference/output+Sha256；v2 summary 的 *CI95；heldout 的 baselineCommit/candidateCommit/environment/psnrDeltaFromInput/negativeLift/fidelityAccepted）；runs（outputImages.frequency_spectrum/binary_skeleton/contour/character_skeleton、adaptiveDiagnostics.features/decisions/fidelityGate、diagnosticMetrics、imageRoles、workingImage、randomSeed）。
- 需要后端或评测科学家补充：
  1. 每个批次的 `splitAvailable`、`status`（valid / historical-leakage / metrics-only）、`defaultForReport`
  2. heldout summary 的按文物聚类 CI 和 Δ（相对输入）
  3. 各批次的 diagnosis 或 error-analysis 结构化接口（目前只有 heldout，v2 返回 404）
  4. 运行列表正确排序，加 `legacy` 标记（P0-1）
  5. 运行级 `unchangedFromInput: bool`（目前只能用 MAD=0 推断）
  6. 机制阶段的数值：周期峰坐标、陷波掩膜图（目前只有 `periodicPeaks` 数组，**没有陷波位置图**，需确认）
  7. ID 映射接口：coreSampleId ↔ museumSteleId ↔ 实验 sampleId（core_sample_links.json 已有，需要 API 化）
  8. 差分热图：由前端基于同尺寸的 reference/output 计算 |Δ|，或者后端提供；**只能用真实像素**
  9. 源码索引：source_snapshot 路径和 commit
- ID 体系（沿用现有字段，只做映射不改名）：`steleId`（含 core/museum 两类）、`runId`、`experimentId`、`sampleId`(=museum steleId)、`caseId`、`inferenceId`、`sourceSha256/inputImageSha256/outputSha256`。URL 形如：`?tab=reports&view=global|artifact&stele=&run=&exp=&split=&deg=&method=&case=`。

### 7.3 首屏布局
- **1920×1080**（除去 68px 页头，约 1012px 可用）：顶部 ContextBar 56px；左 7 列为 L1 结论卡（3 条分级结论，每条带 n/CI、来源批次）；右 5 列为 L2 SyncedTriptych 精简版（默认显示评测科学家指定的代表 case，标注 caseId）；下方一条 L3 Δ 迷你图（ECharts，零线可见）。不放数字卡片墙，最多 3 个关键数，且必须带 CI。
- **1440×900**（约 832px 可用）：结论卡和三联改为上下两段，三联高度约 360px；迷你图下移到首屏底部，只露出可见部分。
- 1366×768 / 390×844：单列，三联可左右滑动。

### 7.4 空状态规则
- 批次只有数值：“本批次只保存数值，未保存对比图像（registry.metricsOnly）”，不显示占位图。
- 没有 split：禁用分组过滤，并注明原因。
- 没有运行：“本件尚未执行处理”；后端不可用时显示“后端不可用，无法读取运行记录”（**不得**回退成“未执行”）。
- 没有真值：指标显示“未评测”，不带单位，并说明原因。
- 原图返回：显示“算法判定不修改”标识，指标 Δ=0 照实显示。
- 没有诊断：“该批次没有失败诊断”（404 照实呈现）。

### 7.5 导出方案
- JSON：`{exportedAt(+08:00), view, steleId, runId, experimentId, filters, summaryRows(当前筛选), caseIds, limitations, sources, appCommit}`
- CSV：沿用后端 `/export/*`，另加一份“当前筛选”的前端导出，文件名带 experimentId 和 filters hash。
- PDF：独立的 `ReportPrintLayout`，A4 纵版，中文衬线字体；第 1 页为结论、范围和局限，后面依次为图（ECharts 用 `getDataURL` 生成静态图，带图号和图题）、三联（标 caseId/SHA）、可复现性信息；页脚写来源和局限。用自动化比对 PDF、JSON、CSV 的数值。

### 7.6 需要谁提供或决策
- **Green**：首页核心样本卡 object-cover 是否修改（受保护视觉）；App.tsx URL 状态由谁实现；Footer“复原”措辞。
- **后端/架构**：P0-1 排序；P0-2 App 层状态；§7.2 第 1、3、4、5、7 项。
- **评测科学家**：报告默认批次与代表 case；heldout 的 CI 和 Δ；结论分级文字；2026-10-15 泄漏批次的展示策略；机制层要展示的数值是否真实可得（陷波掩膜）。
- **金石学/数据治理**：P1-15 核心样本与馆藏拓本的身份展示边界。

---

## 8. 截图与产物清单（`D:\RubbingMind\screenshots\product-upgrade\phase0-frontend\`）
01_home_1920x1080.png，01_home_1440x900.png，02_museum_1920x1080.png，02_museum_1440x900.png，03_workbench_1920x1080.png，03_workbench_1440x900.png，04_graph_1920x1080.png，04_graph_1440x900.png，05_reports_firstscreen_tang-duobao_1920x1080.png，05_reports_firstscreen_tang-duobao_1440x900.png，05_reports_fullpage_tang-duobao_1920x1080.png，06_reports_explorer_heldout_default_1920x1080.png，07_reports_explorer_v2-2026-10-17_1920x1080.png，08_reports_explorer_triptych_v2_1920x1080.png，09_reports_explorer_2026-10-15_leakage_1920x1080.png，10_reports_article_tang-duobao_1920x1080.png，11_reports_print_tang-duobao_A4.pdf，12_reports_firstscreen_tang_01_duobao_1920x1080.png，12_reports_firstscreen_tang_01_duobao_1440x900.png，13_reports_article_tang_01_duobao_1920x1080.png，14_workbench_tang_01_duobao_1920x1080.png，15_graph_tang_01_duobao_verified_1920x1080.png

浏览器：Microsoft Edge headless（Playwright 1.63 channel=msedge；自带的 chromium-headless-shell 没装，没有执行 `playwright install`）。前端由自己起的 vite 5720 提供（PID 44980，已停止），API 走用户的 8000。没有点击任何处理、上传、删除、推演或标注按钮。注意：图谱页加载时前端会自动发出 1 次 `POST /api/calendar`（services/history.ts:33；main.py:532–536 只调用 `convert_historical_year` 做纪年换算，代码里看不到写库，是否完全无副作用**待核实**），除此之外页面加载只发 GET。

---

## 9. 收尾记录（2026-10-19 12:02 Asia/Shanghai）
- 自己启动的进程：只有 vite PID 44980（5720），已停止。之后复查监听端口：8000（PID 30712，用户进程，未触碰）、5740/8740（其他 Agent 的进程，未触碰）；5720 和 8720 都没有在监听。Playwright 的 Edge headless 已随 browser.close() 退出。复查时看到的 msedge 进程是用户 Edge 的渲染进程，其余 node 进程是 MCP 服务或 5740 vite，都不是我启动的。
- 临时目录 C:\Users\WPY11\rm-report-frontend-tmp 已删除（Test-Path=False: True）。
- git：HEAD f0c5886，分支 feature/product-grade-upgrade；`git status --short --untracked-files=no` 输出为空（已跟踪文件 0 改动）；未跟踪条目共 58 条。相比审计前，只多了 screenshots/product-upgrade/ 目录；docs/product-upgrade/ 本来就是未跟踪目录，本次只往里新增了本文件。

## 修订记录 · 2026-10-19 13:15（UTC+8）· RM-报告前端切片 2

### `/api/calendar` 写操作核实（追加）

Green 已核实：`main.py:532` 的 calendar 路由只调用 `convert_historical_year`，无数据库写入、无文件系统写入。本轮结论：**已核实只读**。切片 2 验收期间未对该路由发出任何非 GET 请求（见 acceptance_log.nonGet=[]）。

### BR-09（只记不做）

等后端 BR-08 `includeDemo` 完成后，在 EvidenceSearch 加「包含演示样本」开关（默认关；开启时明确提示含合成演示数据）。切片 2 不实现。
