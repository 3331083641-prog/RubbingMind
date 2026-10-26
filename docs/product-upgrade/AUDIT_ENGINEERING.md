# AUDIT_ENGINEERING — Phase 0 工程审计（架构 / 后端 / Git）

- 作者：RM-架构后端
- 时间：2026-10-19 11:38–11:55（Asia/Shanghai）
- 审计对象：`D:\RubbingMind`，分支 `feature/product-grade-upgrade` @ `f0c5886`（只读，未改任何业务代码，未 commit/push/切分支）
- 实测环境：Windows 笔记本 LAPTOP-TU4U942T，Python 3.12.4，SQLite 3.45.3
- 实测方式：`DB_PATH` 在 `database.py:12` 写死为 `BASE_DIR/data/rubbingmind.sqlite`，没有环境变量可以改。所以先用 robocopy 把整个后端（代码 + data + static + experiments + apps/web/public|dist，1.307 GB，不含 .git/node_modules/用户未跟踪目录）复制到 `C:\Users\WPY11\rm-arch-backend-tmp\app`，再在副本上启动 `python -m uvicorn main:app --app-dir <副本> --host 127.0.0.1 --port 8710`（PID 38508）。所有写库、写文件的测试都只落在副本里。测完按 PID 停掉，并核对了命令行。
- 用户数据未被改动（前后 SHA-256 一致）：`data\rubbingmind.sqlite` = `8408DBC3…0323D`（mtime 2026-10-18 16:25:27，测前测后一致）；`data\runtime\evidence-v2.sqlite` = `854DF859…BABD3`（一致）；`static\results` 216 个文件、`data\uploads` 3 个、`glyph-inferences` 47 个，测前测后一样。端口 8000 一直由他人进程 PID 30712 占用，我没有碰它。5180 测试期间没有监听。
- 证据分级：**已验证**（实际执行过）/ **代码确认**（读代码确认，没有运行）/ **未实测**。

## 0. 总览

| 级别 | 数量 | 编号 |
|---|---|---|
| P0 | 3 | E-P0-01 ~ 03 |
| P1 | 9 | E-P1-01 ~ 09 |
| P2 | 11 | E-P2-01 ~ 11 |

- API：`main.py` 定义了 **36 个操作**（没有 include 任何 router；另有 `/static`、`/assets` 两个 StaticFiles 挂载，以及 FastAPI 默认的 `/docs`、`/redoc`、`/openapi.json`）。36/36 的正常路径都实测返回 2xx。总共跑了 159 次 HTTP 检查（含负向、安全用例），154 次符合预期，5 次暴露缺陷（见 E-P1-01/03/05、E-P2-01）。另外做了 28 次进程内（ASGITransport 模拟远程 IP）鉴权检查，全部符合 fail-closed 预期。
- 基线测试：在副本上跑 `python -m pytest tests -q`，第一次 **3 failed / 121 passed**。原因：副本缺 `docs/`、`screenshots/` 下的已跟踪文件，有 2 个失败；我的审计复核写入改变了运行时状态，有 1 个失败（见 E-P2-06）。补齐已跟踪文件、移走审计写入后重跑，结果 **124 passed**。
- 原始测试记录（副本目录，审计结束会随临时目录一起删除）：`results_part1.json`（88 条）、`results_part2.json`（72 条）。本文摘录了关键输出。

---

## 1. Git 事实（已验证）

命令：`git status --short --branch`、`git branch -a -vv`、`git worktree list`、`git rev-list --left-right --count main...<b>`、`git ls-remote --heads origin`、`git stash list`

- HEAD：`feature/product-grade-upgrade` = `main` = `origin/main` = `f0c5886`（2026-10-19 00:55:14 +0800，"Merge branch 'feature/terrain3d-v22-visual-refinement'…"）。feature 相对 main：ahead 0 / behind 0，**仅本地**。`git ls-remote` 显示远程没有这个分支。
- 远程：`origin https://github.com/3331083641-prog/RubbingMind.git`。`git ls-remote` 返回的 14 个 head 与本地 remote-tracking 引用完全一致（FETCH_HEAD 时间 2026-10-19 11:31:36）。
- 工作区：已跟踪文件没有修改（`git diff --stat` 为空），没有 stash，已跟踪文件 4509 个。
- 本地分支 18 个，均已并入 main（ahead=0），只有一个例外：`codex/museum-v3-release` ahead 1（`b0d17eb`，"feat(gis): rebuild China-wide historical map…" 2026-10-15 00:47）。它和已并入 main 的 `f2f1ce5`（同标题，00:55）是同一功能的早期版本，`git cherry` 显示补丁不同，判断为被取代的旧提交。
- 只在本地的分支（远程没有）：`codex/museum-v3`、`codex/museum-v3-release`、`codex/remediation-2026-10-15`、`codex/security-deps-2026-10-15`、`feature/product-grade-upgrade`。只在远程的分支：`origin/dev/home-ambient-video`（behind 24, ahead 0）。
- 远程分支相对 main 全部 ahead 0（都已合入）。behind 数：dev/* 8–38，feature/terrain3d-v22 1，feature/threejs-real-terrain 5，codex/technical-v2 40。
- 额外 worktree 3 个（不是本审计创建的）：`D:/Codex/worktrees/RubbingMind-gis-final`（detached f2f1ce5，4 处未提交改动）、`rubbingmind-museum-release`（codex/museum-v3-release，198 处）、`rubbingmind-museum-v3`（codex/museum-v3，204 处）。**这些未提交改动可能含有未保存的工作，禁止清理，需要 Green 或用户确认。**
- 未跟踪条目（只列出，没有动）：审计开始时 57 条，结束时 58 条。新增的 `screenshots/product-upgrade/` 是其他 Agent 产生的。清单：`design/blender/stele-final/sculpt_fields.npz`、`stele-final.blend`、`docs/product-upgrade/`、`graph-current-ui-2026-10-15.png`、`rubbings-review-v3/`、`rubbings-workspace/`、`screenshots/home-video-check/`、`screenshots/museum-banner-v2/*`（8 张）、`screenshots/remediation-2026-10-15/graph/`、`screenshots/remediation-2026-10-15/museum/*`（18 个文件）、`screenshots/technical-v2/*`（4 张）、`screenshots/terrain3d-final/*`（19 张）、`screenshots/product-upgrade/`、`user_prompt_10.txt`、`墨韵智考_真实碑拓28件高清成品/`。
- 注意：`docs/product-upgrade/` 本身未跟踪，本文件和 ADR 也在其中。合入时需要 Green 决定是否纳入版本库。

---

## 2. API 清单与实测（已验证，副本 127.0.0.1:8710）

说明：示例 ID 为 `tang_01_duobao`（馆藏）、`tang-duobao`（核心样本）。耗时为单次实测值。

| # | 方法 路由（main.py 行） | 参数 | 返回结构（摘要） | 实测 |
|---|---|---|---|---|
| 1 | POST /api/research/query（149） | body `{question 2–500, steleId?≤100}` | `query,scopeSteleId,status,judgment,claim,answer,answerMode,algorithmVersion,indexFingerprint,evidence[],entities,relations,places,generation` | 200（151ms，judgment=supported，12 条证据）；短问题 422；未知 steleId 404；注入问句 200，answerMode=extractive_evidence_only，judgment=None，没有采纳注入断言 ✅ |
| 2 | GET /api/research/steles/{id}（157） | path | `steleId,nodes,links,sources,places,routes,verification` | 200；未知 404 ✅ |
| 3 | GET /api/experiments（164） | – | list[4]：`id,directory,rowCount,sampleCount,summary,limitations,imageComparisonAvailable,metricsOnly,historicalWarning` | 200（694ms，首次读取） ✅ |
| 4 | GET /api/experiments/{eid}（170） | path | `config,sources,rows,summary,environment,registry` | 4 个批次均 200；未知 404 ✅ |
| 5 | GET /api/experiments/{eid}/assets/{filename}（178） | path | PNG（白名单 + SHA 校验） | 200；`..%2F..%2F..%2Fmain.py` 404；未登记文件 404 ✅ |
| 6 | GET /api/experiments/{eid}/diagnosis（187） | 仅 `heldout-v20-v21-2026-10-18` | `experimentId,method,negativeLiftCount,unchangedCount,causeCounts,cases,caveat,notRetuned` | 200；其他批次 404 ✅ |
| 7 | GET /api/experiments/{eid}/export/{kind}（195） | kind∈results.json/results.csv/summary.csv | 文件下载 | 12 次全部 200；非法 kind 404 ✅ |
| 8 | GET /api/catalog/{id}/assessment（231） | path（`^[a-z][a-z0-9_]*$` + 28 件白名单） | 40+ 字段，含 `runId,sourceImageSha256,fidelityGate,regionOverlays,reviewHistory,psnr:null` | 200；核心样本 ID 404；`..%2F` 404 ✅ |
| 9 | GET /api/catalog/{id}/assessment/assets/{kind}（242） | kind∈input-roi/output | PNG（SHA 校验） | 200/200；非法 404 ✅ |
| 10 | POST /api/catalog/{id}/assessment/review（253） | body `{reviewer,damageTypes[1–8],note,suggestedCondition?,roi?}` | `latest,history,expertReview` | 副本写入 200；非法类型 400；ROI 越界 400 ✅ |
| 11 | GET /api/catalog/{id}/assessment/region-crop（268） | query x,y,width,height | PNG | 200；越界、负数 400；**width=height=0 返回 400 并带出 PIL 内部错误**（E-P2-01）；整幅 1874×1646 → 2.99MB，659ms |
| 12 | GET /api/glyph-evaluation（279） | – | `status,top1,top3,verifiedLabels,recordedLabels,reason` | 200，status=not_evaluated ✅ |
| 13 | POST /api/glyph-annotations（289） | body `{steleId,inferenceId?,bbox{x,y,width,height},glyph,sourceCitation,annotator,damageLevel,variantNote,imageSha256}` | 已保存记录 | 副本写入 200；**steleId=`does-not-exist`、bbox 999999 也返回 200**（E-P1-03） |
| 14 | GET /（302） | – | dist/index.html | 200 ✅ |
| 15 | GET /api/health（315） | – | `status,system,version,samples_available` | 200 ✅（只报 4 个样本，不检查 DB 和目录，见 ADR-007） |
| 16 | GET /health（314） | – | 同上 | 200 ✅ |
| 17 | POST /generate（326） | – | `steleId,nodes,links,gis_route,verification`（固定 tang-duobao） | 200 |
| 18 | GET /generate（364） | query stele_id | 与 #22 相同；**和 POST 版结构不同**（E-P2-10） | 200 |
| 19 | GET /api/steles（331） | – | list[31]（28 件 verified_review_v3 + 3 件 user_upload） | 200 ✅ |
| 20 | GET /api/steles/{id}（337） | path | 馆藏 / 核心样本 / 上传记录 | 馆藏 200，核心 200，别名 `qing_02_chongli_wushi` 200，下架 `qing_01_shilang` 410（带 recommendedId），未知 404 ✅ |
| 21 | GET /api/steles/{id}/infer（347） | path | `transcript,characters[],damaged_summary(,demoMode)` | 200 ✅（核心样本返回 demoMode=True 并注明"非本次图像检测"） |
| 22 | GET /api/steles/{id}/graph（352） | path | 馆藏：`nodes,links,gis_route,verification`（**没有 steleId**）；核心：`steleId,formalName,…` | 200；**两种 schema 不一致**（E-P0-03） |
| 23 | GET /api/steles/{id}/report（371） | query run_id? | `ablation,evaluation_summary,…,run,inferenceRecords,sourceRecords,reportId` | 200；错误 run 404；`../../etc` 404；**默认运行选错**（E-P0-01） |
| 24 | GET /api/steles/{id}/runs（387） | path | list[ProcessingRun] | tang_01_duobao 10 条，tang-duobao 4 条 ✅ |
| 25 | DELETE /api/steles/{id}/runs/{run_id}（393） | query confirm | `{deleted,steleId}` | 不带 confirm 400；错误 ID 404；跨文物 404；副本删除 200；**关联推演没有处理**（E-P1-01） |
| 26 | POST /api/process（403） | body ProcessRequest（d0 1–500 等，有 Literal 校验） | `stele_id,restored_image,…,runId,algorithmVersion,evaluationStatus,outputImages,measurementBasis`，psnr/ssim 为 null | 副本 200（1436ms）；带 image_base64 422；未知 404；下架 410；越界参数 422；sample_id `../main.py` 400；3 个并发请求 → 1×200 + 2×429 ✅；**sample_id 路径产生无归属 run**（E-P1-02） |
| 27 | POST /api/upload（411） | multipart file,title,dynasty,author,script_type,weathering_level | `{success,stele}` | 合法 PNG 200；text/plain 415；MIME 与内容不符 415；损坏、截断 400；空文件 400；16×16 413；30000² 炸弹头 400；>12MiB 413；空标题 422；文件名 `../../evil name.png` 被忽略（使用 uuid 目录）✅；**跨站 multipart 上传成功**（E-P1-05） |
| 28 | GET /api/uploads/{upload_id}/image（457） | path | 图像 | 200；未知 404；`upload-..%2F` 404 ✅ |
| 29 | POST /api/steles/{id}/inferences（466） | body `{bbox{x,y,w16–1024,h16–1024},context≤1000,characterId?,originalGlyph?,originalStatus?,imageSource,runId?}` | 推演记录（含 imageProvenance、cropSha256、candidates、status） | 原图 200（source=unavailable，无候选，诚实）；修复图 + 本次 run 200（runOwnership=verified）；没有 run 422；跨文物 run 404；越界 422；过小 422；上下文过长 422 ✅ |
| 30 | GET /api/steles/{id}/inferences（481） | path | list | 200 ✅ |
| 31 | GET /api/inferences/{id}/crop（487） | path | PNG | 200；未知 404 ✅ |
| 32 | POST /api/inferences/{id}/decision（495） | body `{action accept/revoke/reject, glyph?}` | 推演记录 | 采纳非候选字 422；reject/revoke 200；accept 200（候选来自 E-P1-04 场景）；非法 action 422 ✅ |
| 33 | GET /api/inferences/{id}/analysis/{role}（505） | role∈gray/foreground/skeleton/noise | PNG | 4×200；非法 404 ✅ |
| 34 | POST /api/inferences/{id}/ocr-baseline（513） | – | 推演记录 + ocrBaseline | 200（2383ms，rapidocr_onnxruntime，countsAsAccuracy=false）✅ |
| 35 | POST /api/inferences/{id}/template（524） | body `{glyph 单字,basis,annotator}` | 模板记录 | 200；非汉字 422；未知 404 ✅ |
| 36 | POST /api/calendar（532） | body `{query}` | `supported,solar_year,ganzhi,zodiac,era,message` | 天宝十一载 → 752 壬辰 ✅；缺字段 422；10 万字 query 200（23ms） |

---

## 3. 数据层：SQLite schema、ID 字段、模块关联

### 3.1 SQLite（已验证，在副本上以 `mode=ro` 读取；`pragma integrity_check`=ok，`foreign_keys`=0，`journal_mode`=delete）

`data/rubbingmind.sqlite`：
| 表 | 行数 | 结构 | 实际用途 |
|---|---|---|---|
| steles | 33 | 26 列（id PK…metrics_json, translation） | **运行时不读**。`museum_manager` 读 JSON。只有 `database.query_steles` 与 scripts/init_db.py、migrate_museum_v3.py 在用。其中 5 行为已下架记录 |
| museum_catalog_status | 33 | id PK, status, recommended_id | 28 active / 5 retired，只被 `query_steles` 使用 |
| user_uploads | 3 | id PK, record_json, sha256, image_format, created_at | 上传（upload_storage.py:20） |
| glyph_inferences | 11 | id PK, stele_id, record_json, created_at | 残字推演（glyph_inference.py:35）。stele_id 分布：tang_01_duobao 8，3 个 upload 各 1 |
| glyph_templates | 0 | id PK, record_json | 参考字形 |
| restoration_logs | 0 | 旧表（FK→steles） | 未使用 |
| inference_records | 0 | 旧表（FK→steles） | 未使用 |
索引：只有各表主键自动索引，没有业务索引。`stele_id`、`runId` 都存放在 `record_json` 文本里，无法建立索引或约束。

`data/runtime/evidence-v2.sqlite`（FTS5）：`evidence`（source_id PK, stele_id, record_json）125 行；`evidence_fts` = `fts5(source_id UNINDEXED, title, body, tokenize="unicode61")` 125 行，中文按单字 + 双字 bigram 预切分（evidence_retrieval.py:24-26）；`metadata`（fingerprint, graph）。数据源指纹变化时会 DROP 后重建（evidence_retrieval.py:88-104）。

SQLite 之外的持久化（代码确认）：运行记录写在 `static/results/<artifactId>/<runId>/processing.json` 与 PNG（museum_processing.py:35-68）；复核写在 `data/runtime/condition-reviews/<id>.jsonl`；人工标注写在 `data/runtime/glyph-annotations/annotations.jsonl`；推演图像写在 `data/runtime/glyph-inferences/*.png`；28 件档案是 `data/catalog/steles28.json` 和 `assessments/*.json`；4 件核心样本是 `data/catalog/core_samples.json` 和 `data/history/*.json`。**一共 5 种存储机制，彼此之间没有外键。**

### 3.2 现有 ID 字段与建议体系的对应（已验证字段存在）

| 建议 ID | 现有对应 | 位置 / 格式 | 问题 |
|---|---|---|---|
| steleId | `id`（馆藏 `tang_01_duobao` 风格；核心样本 `tang-duobao` 风格；上传 `upload-<hex32>`） | steles28.json、core_samples.json、user_uploads | **同一作品有两套 ID**（E-P0-03） |
| artifactId（原石） | 只在证据图谱中生成节点 `<sid>:stone` | evidence_retrieval.py:41 | 不持久化；`museum_processing.py:34` 中的 `artifact_id` 其实是 steleId，或者是 `'uploaded-image'` |
| rubbingId（拓本） | `collectionNumber`（如 `購拓000033`），图谱节点 `<sid>:rubbing` | steles28.json | 不是独立实体 |
| imageSha256 | `sourceVerification.sourceSha256`；assessment `sourceImageSha256/inputImageSha256/outputImageSha256`；run `inputImageSha256/outputSha256{role}`；inference `inputImageSha256/selectedImageSha256/cropSha256`；upload `originalFileSha256` | 多处 | 字段名不统一 |
| runId | 处理运行 `YYYYMMDDTHHMMSS_hex8`（museum_processing.py:33，正则 :73）；归档评估 `assess28-20261018-<sid>`（steles28.assessmentRunId）；旧运行 `legacy-unverified` | 文件系统 | 两类 runId 格式不同，没有索引表 |
| inferenceId | uuid4 hex32 | glyph_inferences.id | – |
| experimentId | `config.experimentId`，或者顶层 `experimentId` | experiments/results/*/results.json | 两种取法（experiment_registry.py:23） |
| sourceId | `catalog:<sid>`、`catalog:<sid>:transcript:<offset>`、`history:<core>:<source>` | evidence 表 | 和 history/sources.json 的 `id` 是两个命名空间 |
| locationId | history `locations[].id` 与 `regionLocationId` | data/history/*.json | 只有 4 件核心样本有 |
| 其他 | templateId(uuid)、upload_id、review `version`（文物内序号）、annotation **没有 ID** | – | 人工标注无法被引用 |

别名与映射：`review_aliases.json`（qing_02_chongli_wushi→qing_02_wushi_reerection）；`replacement_mapping.json`（5 件下架，oldId→newId，明确标注为"不同文物"）；`history_graph.ALIASES`（tang_01_duobao→tang-duobao，han_01_caoquan→han-caoquan，history_graph.py:10）；前端 `graphSelection.CORE_STELES`（id↔recordId，graphSelection.ts:2-7）。**4 份映射分散在 4 个文件，口径也不一样。**

### 3.3 五页前后端关联（代码确认 + 部分实测）

- 全局状态只有 `App.tsx:19` 的 `selectedSteleId`（初始值 `'tang-duobao'`，是核心样本 ID，不是馆藏 ID）和 `currentTab`。**没有 URL 路由，没有 runId、inferenceId、experimentId 状态**，刷新或分享都会丢失上下文。
- 首页 → 典藏馆 / 工作台 / 图谱：`HomePage.tsx:89,123,141,289,300` 调用 `onSelectStele(id)` 和 `onNavigate(tab)`。
- 典藏馆：`App.tsx:85` 只传 `source_kind==='verified_review_v3'` 的记录；`MuseumPage.tsx:114,400,450` 选中后跳到工作台或图谱。
- 工作台：`WorkbenchPage.tsx:119` 调 `POST /api/process`，`:146` 把 runId 存进**页面内部状态**，`:665` 传给 GlyphInferencePanel。
- 图谱：馆藏走 `VerifiedMuseumGraph`（只用前端传入的记录，不请求后端）。核心样本走 `GraphPage` → `services/history.ts:16` 请求 `/api/steles/{canonical}/graph`，用 `resolveCoreId` 把 `tang_01_duobao` 转成 `tang-duobao`，失败时回退到打包的 JSON（:22-25）。`EvidenceSearch` 走 `/api/research/*`。
- 报告：`ReportsPage.tsx:19-20` 自己拉 runs，并取 `items[0]`；`:33` 在前端重新拼 reportId。工作台选中的 runId **不会传过来**。
- services/api.ts：17 个方法，其中 `getSteles/getSteleById/getInference/getReport` 出错时一律 `catch` 后回退到打包数据（:37-59）。

---

## 4. 发现明细

### P0

**E-P0-01 报告默认选中的运行是 legacy-unverified，而不是最新的真实运行**
- 位置：`museum_processing.py:90-97`（`list_runs` 按 `finishedAt` 字符串倒序；旧运行在 :84 被填成 `'未记录'`）；`main.py:375-376`（默认取 `runs[0]`）；`ReportsPage.tsx:20`（前端也取 `items[0]`）
- 实测：在副本上调 `list_runs('tang-duobao')`，顺序为 `20261014T165542_5fc44fba legacy-unverified 未记录`、`20261015T013329… legacy-unverified 未记录`、`20261018T072201_13772747 adaptive-rubbing-v2.1 2026-10-18T07:22:01Z`、`20261017T093048… frequency-spatial-v2.1`。`GET /api/steles/tang-duobao/report` 返回的 run = `20261014T165542_5fc44fba`，algorithmVersion=`legacy-unverified`。`qing_01_qianlong_heart_sutra` 同样排在前面。原因是 "未" 的码位大于数字，倒序后排到最前。
- 状态：已验证
- 缺陷：默认报告展示的是未经验证的旧运行，而且看起来像"最新一次处理"
- 用户影响：报告页、导出的 JSON 和 PDF 绑定到错误的运行，可信交付失真
- 修复路径：增加 run 索引（ADR-004）。排序键用 runId 内嵌的 UTC 时间戳，legacy 一律排在最后。报告不再隐式取默认运行：没有 run_id 时返回 `runSelection:{rule:'latest_verified', runId}`，并且不选 legacy。前端显式传 runId（见 E-P0-02）
- 验收：对 tang-duobao 调 `/report`，选中 `20261018T072201_13772747`；有 legacy 时 `runSelection.rule` 可见；新增 pytest 覆盖"legacy 和新运行混合排序"

**E-P0-02 五页之间不传运行上下文：工作台生成或选中的 runId 到报告页就丢了**
- 位置：`App.tsx:16-22`（只有 selectedSteleId）；`WorkbenchPage.tsx:45,146`（runId 是页面内部状态）；`ReportsPage.tsx:13-20,33`
- 实测：代码确认。和 E-P0-01 叠加后，副本上的 tang-duobao 报告指向 legacy run，而工作台最新的 run 是 2026-10-18 那次。
- 状态：代码确认 + 后端部分已验证
- 缺陷：报告描述的运行不一定是用户刚做的那次；切换 tab 会丢失上下文；没有 URL，无法复现或分享
- 用户影响："首页 → 典藏馆 → 工作台 → 图谱 → 报告"无法真实闭环（专题 F）
- 修复路径：ADR-003。App 层维护 `{steleId, runId, inferenceId, experimentId}`，并同步到 URL hash（`#/reports?steleId=…&runId=…`）。工作台跳报告时带上 runId。后端报告接口回显 runId；runId 不属于该文物时返回 404（这一点已经实现）
- 验收：E2E：在工作台处理得到 runId X，点"前往报告"，报告页的 runId 为 X，导出 JSON 中的 runId 也是 X；刷新后上下文还在

**E-P0-03 同一作品有两套 ID（核心样本和馆藏），运行、推演、报告、图谱按 ID 分裂，图谱接口 schema 也不一致**
- 位置：`data/catalog/core_samples.json`（tang-duobao、han-caoquan，`source_kind=core_demo`、`isDemo=True`）与 `steles28.json`（tang_01_duobao、han_01_caoquan）；`history_graph.py:9-10` ALIASES；`graphSelection.ts:2-8`；`main.py:352-361`（馆藏返回 `catalog_graph`，没有 steleId；核心样本返回 history graph，带 steleId）；`services/history.ts:12-19`（要求 `data.steleId===canonical`）；`App.tsx:19` 默认选中 `tang-duobao`
- 实测：`/api/steles/tang_01_duobao/runs` 返回 10 条，`/api/steles/tang-duobao/runs` 返回 4 条；推演 tang_01_duobao 8 条，tang-duobao 0 条。`/api/steles/tang_01_duobao/graph` 的键为 `nodes,links,gis_route,verification`（没有 steleId），`/api/steles/tang-duobao/graph` 的键为 `steleId,formalName,…`。`/api/steles/wei_02_wugaoli/graph` 返回 steleId=None。
- 状态：已验证
- 缺陷：同一作品（多宝塔碑）的处理记录和推演记录分散在两个 ID 下；默认入口是 demo 记录；同一路由在不同 ID 下 schema 不同。另一方面，wei-yuanhuai 和 wei-jianyi 的身份未核定，**不能**合并（BRIEF 第 2 节）
- 用户影响：跨页面看到的"同一件文物"实际是两条记录，统计与报告不一致；图谱页依赖前端的别名转换
- 修复路径：ADR-001/002。区分 `steleId`（作品/馆藏记录）与 `sampleId`（算法样本）。只有经过金石学和数据治理审核、证明同一性的，才写入 `id_alias(sampleId→steleId, relation='same_work_verified')`。旧 ID 保持可访问，响应同时带 `ids` 块。graph 接口统一为 `{steleId, kind, nodes, links, places, sources, verification}`
- 验收：映射表经金石学 + 数据治理签字；`/api/context?steleId=tang-duobao` 返回 canonical 与 alias 关系；两种 ID 的 graph 响应都有 steleId 且结构一致；wei-* 不出现在 same_work 映射里

### P1

**E-P1-01 删除运行后，引用它的推演记录变成悬挂引用**
- 位置：`museum_processing.py:100-108`（只 rmtree 输出目录）；`glyph_inference.py` 没有删除或标记逻辑
- 实测：副本上删除 run `20261019T034611_64772d96` 返回 200 后，`GET /api/steles/tang_01_duobao/inferences` 中仍有 `b087930a…` 的 runId 指向该运行，`GET /api/inferences/<该ID>/crop` 仍返回 200（8649B），记录里还写着 `runOwnership: verified`
- 影响：来源链断了，但记录仍显示"已验证归属"
- 修复：删除改为墓碑（`run_index.deleted_at`），关联推演标记 `runStatus:'deleted'`，界面提示；或者有关联时拒绝删除（409），并列出关联推演
- 验收：删除后，关联推演的 provenance 显示 deleted；报告不再引用；有 pytest

**E-P1-02 `sample_id` 处理路径写入无归属的 `uploaded-image` 目录**
- 位置：`museum_processing.py:28-29,34-35`
- 实测：`POST /api/process {stele_id:null, sample_id:'sample_1.png'}` 返回 200，输出写到 `static/results/uploaded-image/<runId>/`，任何 `/runs` 接口都查不到
- 修复：sample 1-4 映射到 sampleId，或者干脆关闭这个路径（前端已不用：api.ts:44 只传 stele_id）
- 验收：任何 run 都能通过 `/api/runs/{runId}` 查到，并有 owner

**E-P1-03 人工标注接口不校验文物、图像 SHA 和坐标**
- 位置：`glyph_annotations.py:60-99`；`main.py:289-299`
- 实测：`steleId:'does-not-exist'`、`bbox 999999×999999`、`imageSha256:'f'*32` 返回 200 并写入（副本）
- 影响：垃圾标注进入将来的人工真值池（专题 B、C 的风险）
- 修复：校验 steleId 存在；imageSha256 必须等于该文物某张已登记图像，或某个 inference 的 selectedImageSha256；bbox 必须在图像尺寸内；为标注生成 annotationId；加锁
- 验收：上述输入返回 404/422；有 pytest

**E-P1-04 参考字形检索会自匹配：同一选区登记模板后，再推演得到 1.000 的"候选"**
- 位置：`glyph_inference.py:278-296`（不排除同 cropSha、同 inference、同碑模板）
- 实测：副本上用 inference 74894b6f 登记模板"寶"，再对同一 bbox 推演，得到 `source=local_shape_retrieval cands=[('寶',1.0)] status=pending_review`，accept 后为 `human_accepted 寶`
- 影响：可能被误当成"识别成功"（专题 B 数据泄漏、专题 C 候选被当作已识读）
- 修复：检索时排除 cropSha256 相同、inferenceId 相同的模板；评测时按碑分组排除；把 `templateSteleId==当前碑` 的情况显式标出
- 验收：同 crop 不返回自身模板；有 pytest

**E-P1-05 跨站请求可以写入（multipart CSRF），也没有 Host 校验（DNS rebinding）**
- 位置：`main.py:70-76`（只配了 CORS）；`runtime_guard.py:17-26`（本机回环一律放行）；没有 TrustedHostMiddleware
- 实测：`POST /api/upload`（multipart，`Origin: http://evil.example`）返回 200 并创建上传（副本），响应没有 ACAO。`GET /api/steles`（`Host: attacker.example`）返回 200，列出 34 条（含用户上传）。另外，`text/plain` 的 JSON 请求被 FastAPI 以 422 拒绝 ✅
- 影响：用户开着本地服务时访问恶意网页，网页可以写入上传，最多 12MiB 一次、不限次数；DNS rebinding 还能读取私有上传。交付形态 B 前必须修复
- 修复：加 TrustedHost（127.0.0.1/localhost/配置值）；对 unsafe 方法校验 Origin/Sec-Fetch-Site，并要求自定义头 `X-RubbingMind-Client`（触发预检）；上传配额
- 验收：上面两条实测分别返回 403/400；同源前端正常

**E-P1-06 数据路径与端口写死，多 Agent 与测试无法隔离；Vite 代理默认指向用户的 8000**
- 位置：`database.py:11-12`；`catalog.py:5`；`upload_storage.py:15`；`glyph_inference.py:23`；`evidence_retrieval.py:16`；`main.py:542`（8000）；`vite.config.ts:10,13`（5173，`RUBBINGMIND_API_TARGET || 'http://127.0.0.1:8000'`）
- 实测：为了安全实测，只能复制 1.307GB 整个后端。8000 端口实测由 PID 30712 占用
- 影响：其他 Agent 在 5720/5740 起前端时，如果没设 `RUBBINGMIND_API_TARGET`，就会**写入用户的真实数据库**
- 修复：`RUBBINGMIND_DATA_DIR`、`RUBBINGMIND_RESULTS_DIR`、`RUBBINGMIND_PORT` 等环境变量（ADR-007），默认值保持现状；vite 代理在未设置时报错，或要求显式指定
- 验收：`RUBBINGMIND_DATA_DIR=<tmp>` 启动后，所有写入落在 tmp；用户目录 SHA 不变

**E-P1-07 持久化分裂，没有约束，没有 schema 版本**
- 位置：见 3.1；`database.py:23-96`（旧表）；`museum_manager.py:8`（运行时只读 JSON）
- 实测：SQLite steles 表 33 行（含 5 行已下架）与 steles28.json（28 条）双轨；`foreign_keys=0`；没有 `schema_version`
- 修复：ADR-002，只做增量：`schema_version`、`entity_registry`、`id_alias`、`run_index`、`entity_link`；旧表只读、标注 deprecated
- 验收：迁移脚本可以 dry-run 并输出映射报告；回滚演练通过

**E-P1-08 前端读接口静默回退到打包数据，404/410 也一样**
- 位置：`services/api.ts:40-43,49-52,57-60`；`history.ts:21-26`
- 实测：代码确认。后端返回 410（下架）时，`getSteleById` 会 catch 并回到本地数据。`resolveSelected` 找不到时会 throw（catalogSelection.ts:6），所以不会换成别的文物，但用户看不出数据来自哪里
- 影响：违反"前端成功必须后端保存"的透明性；报告回退文案可能被误认为后端结论
- 修复：只在网络错误时回退，并在返回中带 `origin:'offline_bundle'` 让界面显示；404/410 按原样展示
- 验收：后端返回 410 时界面显示"已下架 + 推荐 ID"；断网时有显式离线标识

**E-P1-09 选中运行后，报告里的推演记录排除了原图推演**
- 位置：`main.py:380`（`item.get('runId')==selected['runId']`）
- 实测：tang_01_duobao 共 8 条推演，报告 `inferenceRecords` 只有 1 条
- 修复：分为 `runInferences` 和 `originalImageInferences` 两组，分别展示
- 验收：报告两组数量之和等于该文物推演总数

### P2

- **E-P2-01** `region-crop` 没有 >0 校验，width=height=0 返回 400 `cannot write empty image`（PIL 内部信息外泄）。位置 `catalog_assessment.py:283-298`、`main.py:268-276`。修复：Query(gt=0, le=上限)；统一错误结构。验收：0 返回 422，并且是中文业务信息。
- **E-P2-02** async 路由里执行同步的 CPU 和 IO，阻塞事件循环。位置 `main.py:466-529`（`infer_crop`、`decide`、`attach_ocr_baseline` 等）。实测：1024² 推演期间，`/api/health` 第一次请求耗时 **1212ms**（之后约 220ms）。修复：改成 `def`，或用 `run_in_threadpool`。验收：推演期间 health 低于 100ms。
- **E-P2-03** remote 模式的鉴权面（进程内实测，客户端 IP 为 203.0.113.5，以及 `RUBBINGMIND_DEPLOYMENT=remote`）：`/api/steles`、写接口、`/api/research/query`（POST）返回 401，fail-closed ✅；但 `/docs`、`/openapi.json`、`/api/catalog/*/assessment`（含 reviewHistory 的复核人姓名）、`/api/research/steles/*`、`/api/experiments`、`/static/*` 都返回 200。演示形态 B 下主列表需要 token，典藏馆不可用。位置 `runtime_guard.py:17`。修复：形态 B 定义只读公开白名单，关闭 docs，对 reviewer 打码。
- **E-P2-04** 启动脚本。`start.ps1` ✅：用 `$PSScriptRoot` 相对路径，只绑 127.0.0.1，健康检查 `/health` 加 `POST /generate`，记录 PID，`stop.ps1` 按 PID 和命令行双重核对，只停本项目进程，不碰数据库（代码确认，未运行，以免影响用户的 8000）。缺陷：从 8000 开始自动找空闲端口，与 COORDINATION 端口规划冲突；`npm ci`/`npm run build` 会自动执行；就绪检查不验证 28 件馆藏与 DB 可写。`start.bat`：端口固定 8000（`python main.py`，main.py:542），会自动 `pip install -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host`（供应链风险，而且会修改用户环境），没有健康检查和 PID 记录。修复见 ADR-007。
- **E-P2-05** 敏感信息：已跟踪文件 `git grep` 只命中测试中的假 token（`tests/test_experiments_v2.py:74`，`fixture-admin-token-not-real`）。`.env` 不存在，`.gitignore` 已覆盖 `.env*`、`*.key`、`*.sqlite` ✅。`main.py:104-110` 的 `DeduceRequest` 是死代码，带 `api_key/base_url` 字段，以后接上路由会形成"客户端提供密钥 + 任意 URL"的 SSRF 风险，建议删除。`.env.example:17-20` 的 `LLM_*` 变量名与代码实际读取的 `RUBBINGMIND_VISION_API_KEY/BASE_URL/MODEL`（glyph_inference.py:154-157）不一致。**用户环境变量中设有 `DASHSCOPE_API_KEY`（长度 35，值未读取、未记录）和 `DASHSCOPE_HTTP_BASE_URL`**，代码不读取它们。外部模型：只允许 HTTPS，timeout 30s，异常一律降级为 `model_unavailable`，不记录密钥（glyph_inference.py:153-189，代码确认）；因为没有配置密钥，**外部模型调用未实测**。
- **E-P2-06** 测试不密闭：`tests/test_catalog_assessment_api.py:25` 依赖 `data/runtime/condition-reviews` 为空。实测：在副本上写入一条复核后，该测试失败（`'已保存复核意见，尚未作为正式鉴定' == '自动初筛，待人工复核'`）。用户在真实界面保存一条复核，CI 之外的本地测试就会失败。修复：测试使用临时 DATA_DIR（依赖 E-P1-06）。
- **E-P2-07** 并发：`PROCESS_LOCK` 实测有效（3 个并发 → 1×200 + 2×429）✅。证据索引 DROP/CREATE 重建没有进程锁（evidence_retrieval.py:88-104），标注 jsonl 追加没有锁（glyph_annotations.py:96-98），SQLite 没有设置 busy_timeout。**这几处竞态未实测。**
- **E-P2-08** 错误结构不统一，有内部异常文本外泄：`damage_mask` 非法时返回 base64 库原文 `Invalid base64-encoded string…`（museum_processing.py:65 → main.py:407）；detail 有时是字符串、有时是对象（main.py:343）、有时是 pydantic 列表。修复：统一为 `{error:{code,message,field?}}`，并兼容旧的 `detail`。
- **E-P2-09** `data/museum_database.json`（390KB）仍保留旧记录，含编造的消融指标（如"频空域联合算法 (Ours) psnr 33.15 ssim 0.948"，replacement_mapping.json 的 oldRecord 中也有）。`museum_manager.py:17-20` 留着回退读取的路径。实测：该 JSON 里不在 28 件、核心样本、下架名单中的 ID 有 0 个，路径当前不可达。建议删除回退分支，旧数据保留为归档但不再提供服务。
- **E-P2-10** 契约重复或不一致：reportId 在前端（ReportsPage.tsx:33）和后端（main.py:383）各算一次；`GET /generate` 与 `POST /generate` 结构不同；`/api/health` 不反映 DB 和目录状态。
- **E-P2-11** Git 卫生：`codex/museum-v3-release` 上有一个被取代的未合并提交 `b0d17eb`；3 个外部 worktree 分别有 4/198/204 处未提交改动；`feature/product-grade-upgrade` 还没推送。建议 Green 在 Phase 6 前确认，worktree 由用户决定是否保留，**不要删除**。

### 已验证无缺陷（正向证据）
- 上传：MIME 白名单、内容与格式一致性、空文件、损坏、截断、炸弹头、像素和尺寸限制、12MiB 限制、文件名被忽略（使用 uuid 目录），全部符合预期（`main.py:411-454`）。
- 请求体超过 18MiB 返回 413（runtime_guard.py:27-37）。
- 路径穿越：experiments 资源与导出、assessment、uploads、inferences 的 crop 与 analysis、`/static`、`/assets`、run_id，全部 404 或 405。
- 文物缺失时不替换样本：404/410（main.py:337-344，museum_processing.py:12-13）。
- 大图内存：4000×3000 上传后处理 1831ms，工作副本缩到 1460×1095（INTER_AREA），进程峰值工作集 354MB。
- 检索注入：只做抽取式回答，没有采纳注入问句里的断言。
- 无真值时 psnr/ssim 全为 null，并写明 `measurementBasis`。
- CORS：只允许 `http://(127.0.0.1|localhost):517x`，evil origin 的预检返回 400。注意：5180、5710 等端口不在正则范围内，只能走 Vite 代理。

---

## 5. 无法完成或未实测的部分
- 外部视觉模型的成功、失败、超时路径：没有配置 `RUBBINGMIND_VISION_API_KEY`（我也不应该使用用户的 DASHSCOPE 密钥），只做了代码确认。
- `start.ps1`/`stop.ps1` 没有实际运行：它们从 8000 开始找端口，会与规则冲突，也可能 `npm run build` 改写 dist。只做了代码确认。
- 前端没有起 5710 做 E2E：本阶段只做后端审计。五页联动结论基于代码，其中 E-P0-01、E-P0-03 有后端实测。
- 证据索引重建竞态、SQLite 锁竞争：未实测。

— RM-架构后端，2026-10-19（Asia/Shanghai）
