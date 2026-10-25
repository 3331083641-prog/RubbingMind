
## R2-8 URL 与 experimentId（Green / 报告前端，2026-10-19）

- 参数：`tab` / `steleId` / `runId` / `experimentId` / `batch`。
- `experimentId` 权威；`batch`（结果目录名）仅作可读别名：解析后 `replaceState` 写回并去掉 `batch`；冲突以 experimentId 为准；未知 ID 为真实空状态，不回落 heldout / 同批复测。
- 默认批次用 `ExperimentBatchMeta.defaultForReport`（当前 BVT），不加 `isReportDefault`。
- 无 URL 参数时不改写地址；非法 `tab` / `runId` 从 URL 清除并提示；深链新标签页时 App 初始化读取 `tab+steleId`（及 runId/experimentId）。
- 写回一律 `replaceState`。ReportsPage 取 `items[0]` / 未调用 `getReportSelection` 归报告前端，本分支不改 ReportsPage。
- 提交：`dcdaac7`（及 api.ts 类型补齐）。

## R2-9 灰度口径 SPEC v3.1

- `grayCriterion = "gray-bt601-pixel-equal-v1"`；`cv2.cvtColor` BGR2GRAY / BGRA2GRAY；字段 `grayChangedPixelCount` / `grayChangedPixelRatio`。
- 本分支另附 `grayCriterionRule`、`graySource`（SPEC 未列，便于调试；不决定 isPassthrough）。
- 与 9ba3a57 初版差异：判据名从 `working-gray-pixel-equal-v1` 改为 `gray-bt601-pixel-equal-v1`；四通道改用 BGRA2GRAY。

## R2-5（续）C-08 令牌与验收

- 令牌 = SHA-256(`C-08|<diffDigest>|<targetDbSha256>`) 前 16 位；差异摘要或目标库任一变化即失效（旧令牌 `32326a07b002522c` 作废）。
- 输入改为读 `data/catalog/c08_sync_diff.json`；basis 两 SHA 与操作清单必须与重算一致。
- RV-AI01：rollback 前检查 WAL/journal + 排他锁，并先备份当前库 SHA；RV-AI04：帮助与文档写明 apply/rollback 前必须停后端。
- RV-AI02 / RV-AI03：P3，仅排期。

## R2-6（续）合并责任与 M-5

- `run_change_status`、`effective_parameters`、`change_stats`、灰度参考字段：**只由本分支实现**；eval-sci（含 `253c5e9`）删除副本，改为调用本分支，测试 patch `RESULTS_DIR=None`。
- `evidence_retrieval.include_demo`：**以 agent/jinshi 为准**。本分支 BR-08 在 API 层加 `includeDemo`（默认 false），若本分支 `query()` 尚无该参数则兼容调用并在 `demoScope.compatNote` 说明；合并时取 jinshi 实现。

## R2-10 实现计划补充（本轮不实现 / 仅排期）

| 项 | 说明 | 状态 |
|---|---|---|
| BR-06 | 可选：API 附只读 `reviewLedger` | 排期 |
| BR-07 | `query_steles(include_retired=True)` 退役坐标置空 | 本轮已做 |
| BR-08 / C-16 `includeDemo` | API + api.ts；检索逻辑合并取 jinshi | API 本轮；逻辑排期合并 |
| RV-AI02 / RV-AI03 | C-08 P3 | 排期 |
| RT-002..010 | 见 R2-7 | 方案 |

## R2-11 RV-AI05

- computed-on-read：像素上限默认 40MP / 张，两文件合计字节上限默认 128MiB；环境变量 `RUBBINGMIND_COMPUTED_ON_READ_MAX_PIXELS` / `_MAX_BYTES`。超限 → 全部判据字段 null + 原因。

## R2-12 算法层 algorithmOutputMode（Green 2026-10-19 定稿）

- 算法诊断层字段正式命名为 `algorithmOutputMode`，取值 `{processed, identity_no_evidence, gate_fallback_original}`（原 `AdaptiveRubbingRestorer.restore` / V22 早退里的同名 `outputMode`）。
- 运行级继续叫 `outputMode` ∈ `{processed, passthrough, undetermined}`，由 `isPassthrough` 导出。
- 两层同名不同义：报告页的“是否改动”只读运行级；算法层只用于决策链展示。本分支不改 eval-sci 大面积文件；合并说明要求 eval-sci 侧完成改名，本分支任何引用与 ADR/审查文档使用 `algorithmOutputMode`。
- 灰度判据最终名：`gray-bt601-pixel-equal-v1`（不要再用 working-gray-pixel-equal-v1）。
