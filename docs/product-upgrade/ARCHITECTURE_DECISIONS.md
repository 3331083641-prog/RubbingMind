# ARCHITECTURE_DECISIONS（初稿）

- 作者：RM-架构后端
- 时间：2026-10-19 11:55（Asia/Shanghai）
- 修订记录：R1 2026-10-19 12:25（Asia/Shanghai），RM-架构后端：并入 AUDIT_FRONTEND 后端需求与 Green 决定，见文末“修订 R1”。被 R1 修订的条目已就地标注【R1 修订】。
- 状态：**Proposed（初稿）**。全部 ADR 都要按 BRIEF 第 3 节走"独立质疑"，由非实现者审查。ADR-001/002 中涉及文物同一性的映射，还必须经过金石学与数据治理审查，Green 确认后才能实施。本阶段一行代码都没有改。
- 证据来源：`docs/product-upgrade/AUDIT_ENGINEERING.md`（下文以 E-Pn-xx 引用）

---

## ADR-001 统一 ID 体系

**背景**：E-P0-03 的情况是同一作品同时存在 `tang-duobao`（核心样本）和 `tang_01_duobao`（馆藏）两套 ID。runId 有处理运行和归档评估两种格式。人工标注没有 ID。别名分散在 4 个文件里。

**决定**：现有 ID 字符串**一个都不改写**。在此基础上增加一层"类型化 ID"，以及 canonical 加 alias 的映射。

| 实体 | ID 字段 | 格式（沿用现有） | 来源 | 备注 |
|---|---|---|---|---|
| 作品 / 馆藏记录 | `steleId` | 现有 `id`，如 `tang_01_duobao` | steles28.json | 28 件的 canonical |
| 算法样本 | `sampleId` | 现有 `tang-duobao`、`han-caoquan`、`wei-yuanhuai`、`wei-jianyi`；【R1 修订】规范写法为 `rm:demo:<id>`，旧裸 ID 继续可用 | core_samples.json | **不再把它当作 steleId 使用**；【R1 修订】按 Green 决定不合并，只通过 `id_mapping.json` 中经人工复核的一条关系连接（见 R1-5） |
| 用户上传 | `uploadId`（同时作为 steleId 兼容） | `upload-<hex32>` | user_uploads | 与馆藏严格隔离 |
| 原刻载体 | `artifactId` | `stone:<steleId>` | 新登记（证据图谱已有 `<sid>:stone` 节点） | 作品 ≠ 原石 |
| 拓本 | `rubbingId` | `rubbing:<steleId>:<collectionNumber>` | steles28.collectionNumber | 作品 ≠ 拓本 |
| 图像 | `imageSha256` | 64 位 hex | sourceVerification.sourceSha256 / assessment / run / upload | 作为图像的主键；角色写在 `imageRole` |
| 处理运行 | `runId` | `YYYYMMDDTHHMMSS_hex8`；归档评估保留 `assess28-…`，并加 `runKind:'archived_assessment'` | static/results、assessments | legacy 标 `runKind:'legacy_unverified'` |
| 残字推演 | `inferenceId` | hex32 | glyph_inferences | – |
| 人工标注 | `annotationId` | `ann-<uuid>`（新增） | annotations.jsonl | 旧记录迁移时补 ID（追加式） |
| 实验 | `experimentId` | `config.experimentId`，否则用 `experimentId` | experiments/results | 由 registry 统一读取 |
| 来源 | `sourceId` | `catalog:<sid>[:transcript:n]`、`history:<core>:<src>` | evidence 表 | 两个命名空间保留，分别加前缀 |
| 地点 | `locationId` | 沿用 history `locations[].id`，加命名空间 `loc:<sampleId>:<id>` | data/history | 没有坐标时 `precision:'region'` |

**同一性规则**（遵守 BRIEF 第 2 节）：
- `id_alias.relation` 只有三种取值：`same_record_alias`（例如 qing_02_chongli_wushi）、`same_work_verified`（必须附证据和审核人）、`retired_recommendation`（**明确为不同文物**，只做推荐）。
- 建议候选：`tang-duobao↔tang_01_duobao`、`han-caoquan↔han_01_caoquan`。它们来自 history_graph.ALIASES 与 graphSelection.recordId，**还需要金石学审核**。【R1 修订】Green 已决定**不合并**；关系只能写在金石史料 Agent 产出的 `data/catalog/id_mapping.json`，并且必须经过人工复核。另外更正审计遗漏：仓库已有 `data/catalog/core_sample_links.json`（4 条，tang/han 为 `same_work`，备注“不证明为同一馆藏拓本”），它在 R1 中只作为“未复核的历史链接”展示，不参与聚合。`wei-yuanhuai`、`wei-jianyi` 不建立任何 same_work 关系。

**影响**：各个 API 响应在保留旧字段（`id`、`stele_id`、`steleId`）的同时，增加一个 `ids:{steleId,sampleId?,artifactId?,rubbingId?,imageSha256?,runId?}` 块。

## ADR-002 存储、迁移与回滚

**决定**：只做增量迁移，不改写 record_json，不移动文件，不碰 28 件影像。

1. 新增表（放在 `rubbingmind.sqlite` 中）：
   - `schema_version(version INTEGER, applied_at, migration, sha256_before)`
   - `entity_registry(id TEXT PK, type TEXT, canonical_id TEXT, status TEXT, source_file TEXT, created_at)`
   - `id_alias(alias TEXT PK, canonical_id TEXT, relation TEXT, evidence_json TEXT, reviewed_by TEXT, reviewed_at)`
   - `run_index(run_id TEXT PK, owner_id TEXT, owner_type TEXT, run_kind TEXT, algorithm_version TEXT, input_sha256 TEXT, started_at, finished_at, sort_ts TEXT, path TEXT, deleted_at TEXT NULL)`，并在 `(owner_id, sort_ts)` 上建索引
   - `entity_link(from_id, to_id, relation, evidence_json, PRIMARY KEY(from_id,to_id,relation))`，用于 inference→run、annotation→inference 等
2. 迁移脚本 `scripts/migrate_ids_v1.py`（Phase 4 实现）：
   - `--dry-run`（默认）：只输出映射报告 `docs/product-upgrade/ID_MIGRATION_REPORT.json`，内容为每条旧 ID 对应的新登记，以及冲突和未映射项。
   - `--apply`：先把 DB 备份到 `data/runtime/backups/<ts>/rubbingmind.sqlite` 并记录 SHA，再在单个事务里建表和插入，最后写 `schema_version`。
   - 扫描 `static/results/*/*/processing.json`，建立 run_index。`sort_ts` 由 runId 前缀解析；legacy 也从 runId 前缀取时间，但 `run_kind='legacy_unverified'`，修复 E-P0-01。
3. 无损映射表：映射报告逐条列出旧 ID、新 ID 或类型、来源文件与行。验证"旧记录数等于登记数"：steles28 28、core 4、uploads N、runs = 文件数、inferences = 表行数。
4. 兼容：旧路由和旧字段原样保留至少一个大版本。新路由放在 `/api/v2/...`，或者通过增量字段提供。功能开关 `RUBBINGMIND_ID_V2=0` 可回到旧行为。
5. 回滚：(a) 关闭功能开关，立即回到旧逻辑；(b) 执行 `scripts/migrate_ids_v1.py --rollback`，在事务内 DROP 新增的 5 张表，并在 schema_version 记录回滚；(c) 最后手段：用备份覆盖，**必须先经 Green 和用户确认**，覆盖前再备份一次当前文件。文件系统没有任何改动，所以不需要回滚文件。
6. 验收：dry-run 报告没有未映射项；apply 前后 84 张正式影像 SHA 不变（对照 ASSET_FREEZE.json），`static/results` 文件数和 SHA 不变；原有 124 个 pytest 全部通过；回滚演练后 DB 的 SHA 与备份一致。

## ADR-003 五页闭环 API 契约

**决定**：
- 前端全局上下文为 `RMContext = {steleId, sampleId?, runId?, inferenceId?, experimentId?, imageSha256?}`，由 App 持有，并同步到 URL hash：`#/<tab>?steleId=&runId=&inferenceId=`（修复 E-P0-02）。默认选中馆藏 ID，不再默认 `tang-duobao`。
- 新接口（只读，增量）：
  - `GET /api/context?steleId=&runId=` 返回 `{ids, stele, aliases[], images[{imageSha256,role,url}], runs:{count, latestVerified}, selectedRun|null, inferences:{run[],original[]}, assessment|null, graph:{url,kind}, report:{url}}`
  - `GET /api/runs/{runId}` 返回 `{owner, run}`（修复 E-P1-02）
  - `GET /api/steles/{id}/graph` 统一为 `{steleId, kind:'catalog'|'history', nodes, links, places, sources, verification}`，只增加字段，旧字段保留
  - `GET /api/steles/{id}/report?run_id=` 增加 `runSelection:{rule:'explicit'|'latest_verified'|'none', runId}`、`runInferences`、`originalImageInferences`、`reportId`（只由后端生成）
- 页面之间的契约：

| 跳转 | 携带 | 后端校验 |
|---|---|---|
| 首页 → 典藏馆 | – | – |
| 典藏馆 → 工作台 | steleId | 404/410 原样展示 |
| 工作台 → 图谱 | steleId（如有 sampleId 一并带上） | graph.kind |
| 工作台 → 报告 | steleId + runId | runId 必须属于 steleId（已实现），否则 404 |
| 报告 → 工作台 | steleId + runId | 回放该 run |

- "前端成功必须后端保存"：所有写操作只有在拿到 2xx 和服务端 ID 后，才在界面上显示成功。读接口回退时带 `origin:'offline_bundle'` 并显式提示（修复 E-P1-08）。
- 验收：以 Playwright 在 5710 前端跑 E2E（指向 8710 副本），完成一圈"典藏馆 → 工作台处理 → 图谱 → 报告"，四个页面上的 steleId/runId 一致，导出的 JSON 与界面一致；刷新后上下文恢复。

## ADR-004 运行记录与关联完整性
- run 以 run_index 为准，文件仍然是事实存储。排序用 `sort_ts`，legacy 永远排在最后，且不作为默认选择。
- 删除改成墓碑：设置 `deleted_at`，输出文件移到 `static/results/.trash/<runId>/`，而不是 rmtree（删除仍需二次确认）。关联推演标记 `runStatus:'deleted'`，报告不引用。是否真的物理删除，留给用户在界面上确认。
- 残字参考检索排除同一个 cropSha 或同一个 inference 的模板，评测按碑分组（修复 E-P1-04）。人工标注必须校验 steleId、imageSha256 和 bbox（修复 E-P1-03）。
- 验收：E-P1-01/03/04 的复现用例全部变成预期的拒绝或标记结果。

## ADR-005 共享文件修改策略
- 所有者：`main.py`、`apps/web/src/services/api.ts`、`apps/web/src/App.tsx`、DB schema 和迁移脚本，都归 RM-架构后端。其他 Agent 通过 TASK_BOARD 或 SendToAgent 提出接口需求，内容包括路由、请求、响应示例和验收用例。
- 第一步做**零行为变化的拆分 PR**：把 `main.py` 拆成 `routers/{catalog,steles,process,uploads,inferences,research,experiments,compat}.py`，`main.py` 只保留装配。`api.ts` 拆成 `services/{steles,runs,inferences,research,experiments}.ts`，由 `api.ts` 统一 re-export，保持原有 import 路径。验收：拆分前后 `/openapi.json` 的路径和方法集合完全一致（36 个操作），pytest 124 个全部通过，`npm run build` 通过。
- 拆分之后，各 Agent 在自己的 worktree 里只改自己的 router 或 service 文件。App.tsx 的上下文、路由部分仍由我负责合并。
- 契约测试：新增 `tests/test_api_contract.py`，对 36 个现有操作做形状快照，防止破坏兼容。

## ADR-006 安全加固（形态 A 本地研究产品；形态 B 受控演示）
1. `TrustedHostMiddleware`，允许 `127.0.0.1`、`localhost` 以及 `RUBBINGMIND_ALLOWED_HOSTS`（修复 E-P1-05 的 DNS rebinding）。
2. CSRF：对 unsafe 方法，要求 `Origin` 为空或在允许列表内，且 `Sec-Fetch-Site` 不是 `cross-site`；前端统一带 `X-RubbingMind-Client: web`（会触发预检）。
3. 错误结构统一为 `{error:{code,message,field?},detail}`（detail 保留以兼容），内部异常文本不外泄（E-P2-01/08）。
4. 参数校验：region-crop 要求 `gt=0` 并设上限；标注完整校验；上传加每日配额和磁盘余量检查。
5. CPU 密集路由改为同步 `def`，或放进线程池（E-P2-02）。
6. 外部模型：只读本机环境变量，只允许 HTTPS；timeout 拆成 connect 5s 和 read 30s；状态通过 `GET /api/model-status` 透明展示，返回 configured/unavailable，不返回密钥；没有模型时照常降级（这一点已经实现）。删除 `DeduceRequest` 死代码。`.env.example` 改成代码实际使用的变量名。
7. 形态 B：`RUBBINGMIND_DEPLOYMENT=demo`，配只读公开白名单（馆藏列表、档案、实验），关闭 `/docs` 和 `/openapi.json`，复核人姓名打码，所有写接口要求 token；**不开放公网**，只做局域网受控演示，开启前必须经过用户确认（BRIEF 第 7 节）。
- 验收：AUDIT 第 2 节中的负向用例全部复跑通过；E-P1-05 两条用例分别返回 403/400；形态 B 的白名单用例矩阵全部通过。

## ADR-007 可配置路径与一键启动
- 环境变量全部可选，默认值等于现状：`RUBBINGMIND_DATA_DIR`（DB、runtime、uploads）、`RUBBINGMIND_RESULTS_DIR`（static/results）、`RUBBINGMIND_PORT`、`RUBBINGMIND_HOST`（默认 127.0.0.1，非回环地址需要显式确认）。统一放在一个 `settings.py` 里，替换 database.py:12、upload_storage.py:15、glyph_inference.py:23、catalog_assessment.py:18、glyph_annotations.py:13、evidence_retrieval.py:16、museum_processing.py:35 这几处路径常量。
- `start.ps1`：增加 `-Port` 参数（默认 8000；被占用就报错并提示，不自动 +1，避免与 Agent 端口规划冲突），以及 `-DataDir` 参数。就绪检查依次为 `/api/health`（扩展为返回 DB 可读写、28 件计数、目录可写）和 `/api/steles` 计数为 28。显示访问地址。PID 记录与停止逻辑沿用现有实现，只停本项目进程。迁移前自动备份 DB。**不覆盖数据库。**
- `start.bat`：只作为 start.ps1 的薄包装，去掉自动从镜像 pip 安装的步骤，改为提示用户执行 `pip install -r requirements.txt`。
- `vite.config.ts`：`RUBBINGMIND_API_TARGET` 未设置时打印醒目警告。各 Agent 开发时必须显式指向自己的端口（修复 E-P1-06）。
- 测试：pytest 的 fixture 设置临时 `RUBBINGMIND_DATA_DIR`，让测试密闭（E-P2-06）。
- 验收：在干净 clone 中，`start.ps1 -Port 8710 -DataDir <tmp>` 启动后，用户 data 目录的 SHA 不变；`stop.ps1` 只停该 PID；health 能报告 28 件。

## 待决事项（交 Green）
【R1 修订】第 1–4 项已由 Green 答复，见 R1-0；下面保留原文备查。
1. `tang-duobao↔tang_01_duobao`、`han-caoquan↔han_01_caoquan` 是否建立 same_work_verified，需要金石学和数据治理审核。
2. `docs/product-upgrade/` 是否纳入版本库。
3. 3 个外部 worktree 中未提交的改动（4/198/204 处）怎么处理，由用户决定。
4. 形态 B 演示的范围与 token 分发方式。

---

# 修订 R1 — 并入报告前端后端需求与 Green 决定

- 修订时间：2026-10-19 12:25（Asia/Shanghai）；作者：RM-架构后端
- 依据（均已核对原文行号）：
  - `AUDIT_FRONTEND.md`（RM-报告前端）：§2.1 第 40–45 行（App 没有 URL 状态，只共享 selectedSteleId）；P0-1 第 125–131 行（默认运行是 legacy）；P0-2 第 133–139 行（runId 不跨页）；P0-4 第 149–154 行（没有 split 的批次被当成 test）；第 98 行（v2 批次 diagnosis 返回 404）；P1-4 第 180 行；P1-8 第 184 行；P1-13 第 189 行；§7.2 第 277–289 行（后端字段需求 1–9 与 URL 形式）；第 311 行（交后端/架构的清单）。
  - `AUDIT_EVALUATION.md`（RM-评测科学家）**E-03 第 90–100 行**：本机 12 次自适应运行中有 10 次改动 0 像素，报告仍显示“本次算法输出”；验收要求这 10 次显示“未修改”，`20261018T072201_13772747` 显示改动比例（644816 像素）。
  - `REPORT_DATA_SPEC.md` v1（RM-评测科学家，配套分支 `agent/eval-sci`@`f21ceaa`）：§1(a) 第 69 行（默认批次应为最新的有图像批次 BVT，禁止默认 BRT）；§2 第 135 行（没有 split 的行显示“本批未划分”）；§6 第 165 行（负提升全部列出）；**§8 第 180–202 行（运行级字段契约）**。
- 本修订只改本文件，不改代码。下列各项的实现进度见 R1-7。

## R1-0 Green 决定（2026-10-19 转达）
1. tang-duobao/tang_01_duobao、han 同理，**不合并**。演示样本归入 `rm:demo:` 命名空间，与真实作品只通过一条经人工复核的关系连接。映射文件 `id_mapping.json` 由金石史料 Agent 在 `agent/jinshi` 分支产出，后端不写它的内容：文件存在就加载，不存在就当作空映射。新旧 ID 都接受。图谱接口对馆藏 ID 也返回 steleId。运行和推演按映射聚合，但每条都标注来源 ID。
2. `docs/product-upgrade/` 纳入版本库，最后随 feature 分支一起提交（现在不提交）。
3. `D:/Codex/worktrees` 下的 3 个 worktree 不碰。
4. 受控演示放到 Phase 5，只写方案，默认只绑 127.0.0.1。
5. router 拆分批准，排在 P0、P1 之后（步骤 f）。

## R1-1 运行排序与 legacy 标记 —— P0（前端 P0-1、§7.2-4；工程 E-P0-01）
- 现状：`museum_processing.py:97` 按 `finishedAt` 字符串倒序排序；旧运行在 :84 被填成 `'未记录'`，码位大于数字，所以排到最前。实测 tang-duobao 默认取到 legacy 运行 `20261014T165542_5fc44fba`。
- 契约（`GET /api/steles/{id}/runs`，只增加字段）：每条增加 `legacy: bool`、`runKind: 'processing' | 'legacy_unverified'`、`sortTimestamp`（从 runId 前缀 `YYYYMMDDTHHMMSS` 解析出的 UTC ISO 时间，解析失败时为 null）。排序规则：非 legacy 按 sortTimestamp 倒序；legacy 一律排在后面，组内同样倒序；sortTimestamp 为 null 的排在最后。
- 契约（`GET /api/steles/{id}/report`）：没有 run_id 时，选最新的非 legacy 运行；只有 legacy 运行时 `run=null`。增加 `runSelection: {rule: 'explicit' | 'latest_non_legacy' | 'none', runId, legacyRunCount}`。显式传入 legacy 的 run_id 仍然可以打开（`rule='explicit'`，并带 `legacy:true`）。
- 兼容：原有字段与顺序语义（第一条为默认）保持不变，只是第一条不再可能是 legacy（除非全部都是 legacy）。前端仍然取 `items[0]` 也能得到正确结果。
- 验收：tang-duobao 的 `/runs` 第一条为 `20261018T072201_13772747`，`/report` 默认也是它，`runSelection.rule='latest_non_legacy'`；qing_01_qianlong_heart_sutra（只有 legacy）的 `/report` 中 `run=null`、`rule='none'`；pytest 覆盖“未记录”混排。

## R1-2 运行级 isPassthrough / changedPixelRatio —— P0（评测 E-03、前端 §7.2-5）
- 口径**完全对齐 REPORT_DATA_SPEC §8（第 184–196 行）**。字段：`isPassthrough`、`changedPixelCount`、`totalPixelCount`、`changedPixelRatio`、`maxAbsDiff`、`meanAbsDiff`、`passthroughCriterion='working-gray-pixel-equal-v1'`、`passthroughUndeterminedReason`、`comparedImages`、`outputMode ∈ {processed, passthrough, undetermined}`、`effectiveParameters`。前端 §7.2-5 中的 `unchangedFromInput` 就是 `isPassthrough`，以 SPEC 的字段名为准，不另起别名。
- 实现方式：把 `agent/eval-sci`@`f21ceaa` 中 `museum_processing.py` 的改动，以及 `degradation_analysis.py` 中的 `change_stats` 函数**原样搬过来**，保证两条分支合并时是相同改动、不冲突。`AdaptiveRubbingRestorer.restore` 中 outputMode 和 selectedOutput 的语义改动（E-02）属于评测科学家，不在本分支实现。
- 写入时机：PNG 落盘之后，用落盘字节解码比较（SPEC 第 200 行）。
- 旧运行：读取时补 null，并带原因“该运行保存于判据引入前，未记录改动量”，不回写旧文件（SPEC 第 201 行）。
- 报告文案：`main.py:382` 的 `evaluation_summary` 分三种状态措辞：passthrough → “算法判定无需处理，输出与输入逐像素相同；无配对真值，配对质量未评测。”；processed → 原文；undetermined → “未能判定是否改动……”。
- **待对齐**：E-03 验收要求那 10 次旧运行显示“未修改”，SPEC §8 却规定旧运行为 null，两者冲突。提议另加 `GET /api/steles/{id}/runs/{runId}/change-status`：先用 `outputSha256` 校验文件，再在读取时现算，标注 `measuredAt:'read_time'`，不回写。是否采用由评测科学家决定，R1 不实现。
- 验收：新运行的 `processing.json` 与响应都带上述字段；对恒等输出的运行 `isPassthrough=true`、`changedPixelRatio=0`；旧运行为 null 并带原因；pytest 覆盖。

## R1-3 批次元数据 —— P0（前端 P0-4、P1-13、§7.2-1）
- 契约（`GET /api/experiments` 每个批次增加；`GET /api/experiments/{id}` 的 `registry` 同步增加）：
  - `splitAvailable: bool`，以及 `splits: {development: n, test: n, …}`（只统计有 split 字段的行），`rowsWithoutSplit: n`。
  - `status ∈ {'valid', 'historical-leakage', 'metrics-only'}` 与 `statusReasons: [..]`。规则：目录 `2026-10-15` → historical-leakage（沿用 `historicalWarning` 的证据）；没有图像（metricsOnly）→ metrics-only；其余 → valid。同批复测、不是留出集这一点，由 eval-sci 的 `heldOut:false`、`displayName` 表达，不在 status 里重复。
  - `defaultForReport: bool`（全局只有一个 true）与 `defaultForReportBasis`。当前取 `controlled-rubbings-v2-text-2026-10-17`，依据 REPORT_DATA_SPEC §1(a) 第 69 行。
- 兼容：只增加字段，不改 `_entry` 的返回行（eval-sci 改了那一行），而是在 `batches()` 中追加，避免合并冲突。
- 验收：4 个批次的 status 分别为 historical-leakage、valid、valid、metrics-only；只有 BVT 的 `defaultForReport=true`；2026-10-15 与 heldout 的 `splitAvailable=false`；pytest 覆盖。

## R1-4 各批次诊断接口 —— P1（前端 P1-4、§7.2-3，第 98 行）
- **实测（2026-10-19 12:10，Asia/Shanghai）**：在 `D:\RubbingMind-wt\rm-arch-backend`（f0c5886，改动前）用进程内 TestClient 发 GET。这个接口只读实验 JSON，不访问 DB，不写文件。结果：`/api/experiments/controlled-rubbings-2026-10-15/diagnosis` 404，`controlled-rubbings-v2-2026-10-17/diagnosis` 404，`controlled-rubbings-v2-text-2026-10-17/diagnosis` 404，三者都是 `{"detail":"没有这份实验的失败诊断"}`；`heldout-v20-v21-2026-10-18/diagnosis` 200。原因：`main.py:189` 硬编码只允许 heldout，`restoration_diagnosis.py:7` 也写死了 heldout 的路径。
- 契约：所有已登记批次都返回 200，未登记批次返回 404。heldout 保持现有字段不变，另加 `diagnosisVersion:'heldout-legacy-heuristic'`（其中的归因是启发式的，见 AUDIT_EVALUATION E-04）。其他批次使用通用诊断 `diagnosisVersion:'baseline-delta-v1'`：
  `{experimentId, diagnosisVersion, baselineMethod:'degraded', comparison:'psnr − 同 case 的 degraded psnr', negativeLiftCount, byMethod:{m:{n, negativeLift, byteIdenticalToInput}}, cases:[{caseId, sampleId, split, degradation, strength, method, psnr, baselinePsnr, psnrDeltaFromInput, negativeLift, byteIdenticalToInput, output, outputSha256}], causeCounts:null, causeBasis:'未做归因：通用诊断只报告事实，不推断原因', caveat}`。
  - `cases` 列出**所有**负提升行，不抽样（SPEC 第 165 行）。“原图返回”只用 `outputSha256==inputSha256` 作为充分条件（`byteIdenticalToInput`）；像素级 isPassthrough 以 eval-sci 的 DER 为准，通用诊断不去猜。
  - 2026-10-15 批次没有 caseId，用 `(sampleId, degradation, strength, seed)` 去配 baseline。
- 验收：四个批次都返回 200；v2 的 `negativeLiftCount` 等于对 results.json 独立重算的值；heldout 响应与改动前逐字段一致（加 diagnosisVersion 除外）；pytest 覆盖。

## R1-5 核心样本 ID ↔ 馆藏 ID 映射 —— P0（前端 P1-8、P1-15、§7.2-7；工程 E-P0-03）【待金石史料审核】
- 命名空间：`rm:demo:<sampleId>`（tang-duobao、han-caoquan、wei-yuanhuai、wei-jianyi）。馆藏 ID 保持裸 ID（如 `tang_01_duobao`）。上传 ID 保持 `upload-<hex>`。
- 输入兼容：所有 `/api/steles/{id}…` 都接受裸 ID 和 `rm:demo:<id>`，规范化后一律按原 ID 读写存储，存储层不改名。
- 映射文件：`data/catalog/id_mapping.json`，由 agent/jinshi 产出。**本分支不创建也不写入它的内容。** 约定格式（待金石史料确认）：
  `{"version":1, "relations":[{"from":"rm:demo:tang-duobao","to":"tang_01_duobao","relation":"same_work","reviewStatus":"human_reviewed","reviewer":"…","reviewedAt":"…","evidence":[…],"aggregate":true}]}`
  只有 `reviewStatus=='human_reviewed'` 的关系参与聚合。文件不存在 → 空映射；格式错误 → 空映射，并在 `mappingError` 中说明原因，服务不崩溃。
- 接口：
  - `GET /api/id-mapping` → `{version, source, mappingError, namespaces, relations, unreviewedLegacyLinks}`。`unreviewedLegacyLinks` 来自 `core_sample_links.json`，只读展示，标为 unreviewed，不参与聚合。
  - `GET /api/id-mapping/{id}` → `{input, canonicalId, namespace, kind:'museum'|'demo'|'upload'|'unknown', relations:[…]}`。
- 图谱：`/api/steles/{馆藏 ID}/graph` 的响应增加 `steleId`（当前缺失），已有字段不变。
- 聚合：`/runs`、`/inferences` 的每条都增加 `sourceSteleId`。只有存在经过复核且 `aggregate:true` 的关系时，才合并对方 ID 的记录，并增加 `aggregatedFrom:[ids]`。映射为空时，结果和现在一样，只多一个 `sourceSteleId`。report 的默认运行只从**本 ID** 的运行里选，不跨 ID 自动选择，避免演示运行被当作馆藏报告。
- 验收：空映射下各接口结果与改动前相同（加 sourceSteleId 除外）；用临时映射文件（只在测试 fixture 中）验证聚合与来源标注；`rm:demo:tang-duobao` 与 `tang-duobao` 返回同一条记录；馆藏 graph 带 steleId；wei-* 在任何映射缺失时都不和馆藏关联。

## R1-6 App.tsx 的 URL 状态与共享 runId 接入点 —— P0（前端 P0-2、§2.1、§7.2 第 289 行）
- 契约（与前端 §7.2 第 289 行一致）：URL 查询串 `?tab=<home|museum|workbench|graph|reports>&stele=<id>&run=<runId>&exp=<experimentId>&view=<global|artifact>&split=&deg=&method=&case=`，用 `history.replaceState` 写入。FastAPI 的 `/` 会忽略查询串，所以不需要改后端。
- App 层状态：`{tab, steleId, runId, experimentId}`。接入点：
  - `WorkbenchPage` 新增 prop `onRunChange(runId|null)`：处理成功（WorkbenchPage.tsx:146）、选择历史运行（:159）、删除运行（:173）时回调。
  - `ReportsPage` 新增 prop `runId?` 与 `onRunChange`：有值时 `getReport(stele.id, runId)`，没有时用后端的 `runSelection`（R1-1），不再在前端自选 `items[0]`；`reportId` 改用后端返回的值。
  - `ExperimentExplorer` 与 `HeldoutComparison` 新增 prop `experimentId?`，不再硬编码；默认值取 R1-3 的 `defaultForReport`。
  - 切换文物时清空 runId（防止串号）。默认文物从 `'tang-duobao'` 改为馆藏 ID 还是保持不变，属于受保护的首页视觉与内容范围，交 Green 定，本修订不改。
- 分工：App.tsx 与 services/api.ts 归 RM-架构后端（ADR-005）；ReportsPage、ExperimentExplorer 归报告前端，在 `agent/report-frontend` 中按上面的 prop 契约接入。
- 兼容：没有查询串时行为和现在一样（首页 + 默认文物）；旧的截图脚本使用 `#/museum`（前端 P2-2），不在兼容范围内。
- 验收：前端 P0-2 的验收（第 139 行）：工作台运行后进报告，下拉值等于新 runId；复制 URL 到新标签页，文物、运行、批次都一致；切换文物后 runId 清空。

## R1-7 ADR-007 补充：数据路径环境变量与 Vite 代理默认值（步骤 b）
- 新增环境变量，默认值等于现状：`RUBBINGMIND_DB_PATH`（默认 `<repo>/data/rubbingmind.sqlite`）、`RUBBINGMIND_RUNTIME_DIR`（默认 `<repo>/data/runtime`，包括推演图、复核、标注、证据索引）、`RUBBINGMIND_UPLOAD_DIR`（默认 `<repo>/data/uploads`）、`RUBBINGMIND_RESULTS_DIR`（默认 `<repo>/static/results`，`/static/results` 的 URL 不变）。`data/catalog` 等受版本控制的权威数据**不可**改路径。
- Vite：未设置 `RUBBINGMIND_API_TARGET` 时，**仍然默认 `http://127.0.0.1:8000`**，同时在终端打印醒目警告。理由：用户的日常用法是 5180 → 8000，改默认会直接破坏它；风险来自其他 Agent 忘记设置，警告加上 COORDINATION 规则就能覆盖。Phase 5 一键启动脚本会显式设置这个变量。
- 验收：不设任何变量时，所有路径与改动前相同（pytest 原样通过）；设置变量时，所有写入都落在指定目录，用户的两个 DB 的 SHA 不变。

## R1-8 实现计划（分支 `agent/arch-backend`，worktree `D:\RubbingMind-wt\rm-arch-backend`，基于 feature@f0c5886）
| 步骤 | 内容 | 优先级 | 依赖与协调 | 提交 |
|---|---|---|---|---|
| a | 建 worktree | – | – | 无 |
| b | R1-7 路径环境变量 + Vite 警告 | P1（测试隔离前提） | – | 单独 commit |
| c1 | R1-1 运行排序 + legacy + runSelection | P0 | – | 单独 commit + 测试 |
| c2 | R1-2 isPassthrough 等（搬入 eval-sci 的原样代码 + 报告文案） | P0 | 与 `agent/eval-sci` 保持相同代码 | 单独 commit + 测试 |
| c3 | R1-3 批次元数据 | P0 | 与 eval-sci 的 experiment_registry 改动错开位置 | 单独 commit + 测试 |
| c4 | R1-4 各批次诊断 | P1 | – | 单独 commit + 测试 |
| c5 | R1-5 ID 映射接口、rm:demo、graph steleId、聚合与来源标注 | P0 | id_mapping.json 等金石史料产出 | 单独 commit + 测试 |
| d | R1-6 App.tsx URL 状态 + api.ts 接入点 | P0 | 与 report-frontend 对齐 prop | 暂不做（等 Green 指令） |
| e | P1：运行墓碑与关联推演、标注校验、模板自匹配、TrustedHost/CSRF、前端回退透明、报告推演分组、region-crop 校验、事件循环 | P1 | – | 暂不做 |
| f | router 与 api.ts 拆分（零行为变化，36 个操作的 openapi 一致） | P2 | P0、P1 合入后 | 暂不做 |
| Phase 5 | 受控演示方案（默认只绑 127.0.0.1）、一键启动 | – | – | 只写方案 |
- 每步都跑 `python -m pytest tests -q`。实测一律使用 DB 副本（RUBBINGMIND_DB_PATH 等指向 `C:\Users\WPY11\rm-arch-backend-tmp`）、端口 8710、绑定 127.0.0.1。不 push，不合并。
