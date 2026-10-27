
---

# 修订 R2 — Green 后续裁定、实现结果与合并说明

- 修订时间：2026-10-19 12:58（Asia/Shanghai）；作者：RM-架构后端
- 分支：`agent/arch-backend`（worktree `D:\RubbingMind-wt\rm-arch-backend`，基于 feature@f0c5886）。没有 push，没有合并。合并顺序：等红队审完、Green 明确下令后再定。

## R2-0 本修订覆盖的 R1 条目
- R1-2 的判据名、旧运行处理方式、comparedImages 格式，由 R2-1 取代。
- R1-5 中“约定格式（待金石史料确认）”，由 R2-3 的实际格式取代。
- R1-8 第 d 步已提前完成（R2-2）。新增的 RT 项排期见 R2-7。

## R2-1 运行级改动判据（Green 2026-10-19 最终裁定）
- `passthroughCriterion` 一律为 `"pixel-equal-v1"`，运行级与实验级同名。定义：输入与输出解码后（`IMREAD_UNCHANGED`，原始分辨率、全部通道），数组形状与位深相同，并且每个值都相等。不转灰度，不缩放。
- 新增字段 `passthroughSource: "recorded" | "computed-on-read"`。
- **无法判定**时（缺图、解码失败、形状或位深不同、SHA 不符），`isPassthrough` 等数值字段、`passthroughCriterion`、`passthroughSource` 全部为 null，`passthroughUndeterminedReason` 写明原因。**不新增** `passthroughStatus`；SPEC v2 也没有这个字段。
- 旧运行：只有当 `outputSha256.original` 和 `outputSha256.restored` 都存在、两张图都在本地，且 SHA-256 与记录一致时，才在读取时计算（`computed-on-read`）。**任何文件都不回写**，测试校验了运行目录在读取前后逐字节相同。结果按 (路径, mtime, sha) 缓存。
- `comparedImages = ["original","restored"]`，与 SPEC §8 一致。
- `change_stats` 改用 int32 计算差值，修正 16 位 PNG 下 int16 溢出的问题。
- **与 SPEC v2 的出入（请评测科学家修改 SPEC）**：第 225 行仍写 `working-gray-pixel-equal-v1`，并且规定 criterion“不为 null”。按 Green 裁定，本分支以裁定为准。
- 实测提示：彩色原图（如 tang-duobao/072201）的输出是灰度复制成三通道，按全通道判据会得到改动比例 1.0，因为灰度化本身计为改动；灰度判据下是 2719 像素。是否接受这一点由 Green 定。详见 REVIEW_EVALSCI_SHARED_FILES_arch-backend.md。
- 提交：`53200d6`（第一版，原样搬入 eval-sci 实现），`4379827`（按 R2-1 修改）。

## R2-2 第 d 步提前：URL 状态与共享 runId（提交 `7c0e258`）
- URL 参数：`steleId`、`runId`、`experimentId`、`batch`，另有 `tab`。用 replaceState 写回，保留 hash。没有参数时行为不变。
- App 持有 activeRunId、experimentId、batch。WorkbenchPage 通过可选 `onRunChange` 上报；ReportsPage 新增可选 `runId`、`onRunChange`、`experimentId`、`batch`、`onExperimentChange`。
- api.ts 新增：类型 RunSelection、RunChangeStatus、ProcessingRunR1、ExperimentBatchMeta、ExperimentDiagnosis；函数 getReportSelection、listExperiments、getExperimentDiagnosis。`npm run build` 通过。
- 后续需要补：RunChangeStatus 加上 `passthroughSource`，comparedImages 类型收窄为 `string[]`；ExperimentExplorer 和 HeldoutComparison 的接入归报告前端。

## R2-3 ID 映射：实际格式与 BR-02 / BR-03 的处理（提交 `7af1497`、`9934438`）
- **实际格式**（agent/jinshi@c358724 的 draft-2026-10-19）：`{version, status, author, namespaces, entries:[{legacyId, newId, kind ∈ rubbing|demo_sample|review_alias|retired, title?, collectionNumber?, depictsSameWorkAs?:{relation, rubbingId, rubbingNewId, workId, evidenceGrade, basis, historySubject}, aliasOf?, recommendedId?, note?, textProvenance?}]}`。命名空间：`rm:rubbing:`、`rm:demo:`、`rm:retired:`、`rm:work:`。
- 本分支**不提交** id_mapping.json。读取是可选的：文件缺失时返回空映射，不报错；文件无法解析时返回空映射并在 `mappingError` 中说明。测试只用 fixture。
- **复核判定**：只有 `depictsSameWorkAs.reviewStatus == "human_reviewed"` 才算经过人工复核。草案中 `evidenceGrade="待人工复核"`，所以 `relationReviewed=false`。这个字段名请金石史料确认后写入 entries。
- **BR-02**（新旧 ID 都接受，旧响应逐字节不变）：用中间件把 `/api/steles/rm:<ns>:<id>/…` 改写为旧 ID，所有接口和存储继续使用旧 ID。命名空间与记录类型不匹配时返回 404（例如 `rm:rubbing:tang-duobao`），`rm:work:` 返回 404，`rm:retired:` 返回 410。实测 `/api/steles/tang-duobao` 与 `/api/steles/rm:demo:tang-duobao` 的响应逐字节相同。
- **BR-03**（entity 字段）：只在 `/api/steles/{id}/graph` 和 `/api/id-mapping[/{id}]` 中返回。馆藏图谱新增 `steleId`；`/api/steles/{id}` 不变（Green 已批准）。
- **不聚合**：runs、inferences、report 中的 inferenceRecords 都标注 `sourceSteleId`；默认运行只从本 ID 的运行中选。
- 下架记录：任何接口都不输出坐标或地点（Green 第 5 项）。扫描测试覆盖 61 个 GET 响应；id_mapping 会剥离下架条目中的地点类键。

## R2-4 RT-014：/api/process 去掉默认文物（提交 `e551137`）
- 选择：`stele_id` 默认值改为 None；既没有 `stele_id` 也没有内置 `sample_id` 时返回 **422**，不写任何文件。
- 理由：
  - (1) 前端 `api.ts processStele` 的类型要求 `stele_id: string`，WorkbenchPage 总是传 `stele.id`，不受影响；
  - (2) 方案“未传时归入 `rm:upload:`”会凭空生成一个产物身份，违背“不自动替换样本”；
  - (3) 原来的默认值还让“只传 sample_id”的请求被悄悄改成处理 tang-duobao，本次一并修正。
- 回归测试覆盖：缺参时 422 且不写盘；前端的参数形状仍然正常处理；只传 sample_id 时使用该样本。

## R2-5 C-08 SQLite 同步脚本（提交 `8a97a12`）
- `scripts/sync_catalog_db.py`，规则 R1–R6 与 agent/jinshi 的 `C08_SYNC_SPEC.md`、`JINSHI_GOVERNANCE_PLAN.md` 一致。
- **默认 dry-run**：以 `mode=ro` 打开，打印操作清单和确认令牌。令牌是 basis 加 operations 的 SHA-256 前 16 位，即 Green 要求的“差异摘要哈希”；SPEC 原写的是“sqliteSha 前 8 位”，以 Green 为准。
- **写入条件**：显式 `--db`、`--apply`，再加 `--confirm <令牌>` 或交互输入令牌。检测到 `-wal` 或 `-journal` 时中止。写入前备份为 `<db>.<YYYYMMDD-HHMMSS>.bak`（Asia/Shanghai），校验并记录备份 SHA。整个写入在一个事务内完成，不执行 hold，写后复核。`--rollback` 会先校验备份 SHA 再恢复。
- **可选 `--diff`**：传入 `check_catalog_governance.py --emit-sync-diff` 生成的清单时，它必须与重算结果完全一致，否则中止。
- 对用户真实库只做过只读 dry-run（mode=ro），没有执行 --apply。

## R2-6 与 agent/eval-sci 的跨分支合并说明（由 RM-架构后端签字负责）
- **degradation_analysis.py**：本分支只引入 `PASSTHROUGH_CRITERION` 和 `change_stats`，并把差值改为 int32。合并时：
  - 保留 eval-sci 的 `restore()` 改动（算法域）；
  - `PASSTHROUGH_CRITERION='pixel-equal-v1'` 两边一致；
  - `change_stats` 采用本分支的 int32 版本。
- **museum_processing.py**：重叠冲突的手工解决方式如下。
  1. 导入行：保留 `from degradation_analysis import VERSION as ADAPTIVE_VERSION, change_stats` 和 `from runtime_paths import results_override`。
  2. `out=…` 行：采用 `out=results_root()/artifact_id/run_id`，不要用 `BASE/'static/results'`；同时保留 eval-sci 的 `saved={};hashes={};raw_images={}`。
  3. 判据相关函数（`RUN_PASSTHROUGH_CRITERION`、`_decode_gray`、`run_change_status`、`read_run` 补字段）：**采用本分支 4379827 的版本**（pixel-equal-v1 全通道、passthroughSource、computed-on-read、数组 comparedImages），删除 `_decode_gray`。
  4. `effective_parameters`：两边相同。
  5. eval-sci 的 `tests/test_applied_status.py`：加 `RESULTS_DIR=None` patch，并按 R2-1 更新判据和 comparedImages 的断言。
- **restoration_diagnosis.py**：采用 7623a52 的 `diagnose()`，保留本分支末尾追加的 `_case_key` 和 `diagnose_batch`。
- 每次合并后都要跑全量 pytest，并运行 `scripts/sync_catalog_db.py --db <副本>` 做 dry-run，作为冒烟检查。

## R2-7 实现计划更新（插入 R1-8）
| 顺序 | 内容 | 状态 |
|---|---|---|
| a、b、c1–c5、d | 见 R1；c2 已按 R2-1 修订（4379827） | 完成 |
| G5 / RT-014 / C-08 | R2-3、R2-4、R2-5 | 完成 |
| **RT（P0 之后、拆 router 之前）** | RT-002：样本下载禁用证书校验、用 http 下载、失败时用合成图冒充，改为默认不下载，缺样本时明确报错，或显式标为合成样本。RT-003：测试脚本默认端口不得指向 5180 或 8000，必须显式传入或使用项目测试端口。RT-004：pytest 不得改写已跟踪的 `screenshots/stele-final/asset-validation.json`（本轮已确认它每次都会被改写，目前靠测后 checkout 还原），不得使用 `data/` 下的真实 SQLite（用 tmp_path 或副本）。RT-005、RT-009：安全响应头、remote 模式下 /docs 需要鉴权、写操作校验 Host 和 Origin（与 P1 一起做）。RT-006：旧 `static/index.html` 用 localStorage 存 API Key、CDN 资源没有 SRI；没有 dist 时明确提示先构建。RT-013：删除运行改为软删除，或删前备份。 | 未实现（按指令） |
| RT-010 | CI 改为 PR 触发，并补上 GIS、graph、terrain 和移动端 technical_v2 | 只写方案，不改 workflow |
| e（P1） | 见 R1-8 | 未开始 |
| f | 拆分 router 和 api.ts | 等 P0、P1 完成 |
| Phase 5 | 受控演示（默认只绑 127.0.0.1） | 只写方案 |
