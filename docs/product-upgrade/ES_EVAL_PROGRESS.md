# ES_EVAL_PROGRESS — 评测侧 ES-3/4/5 推进记录

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-25 13:11 Asia/Shanghai
- 分支 tip：0654d13（0654d1307f849f5dadbfaca87fd96f2ce3b56c41）
- 对齐：fast-forward `feature/product-grade-upgrade@0654d13`（含 reports MechanismPanel / claims 台账）
- TASK_BOARD 本体在 D:\RubbingMind\docs\product-upgrade\TASK_BOARD.md（worktree 外）；本文件为 worktree 内进度镜像，供 Green 勾板。

## 状态（本提交）

| ID | TASK_BOARD 目标 | 本提交落地 | 状态 |
|---|---|---|---|
| ES-3 | 按文物聚类 bootstrap CI；CI 下界 >0 才能写「提升」 | 既有 `ci_by_artifact.json` 契约 + `may_claim_positive_lift` / `lift_claim_label` + 新增 `summarize_lift_claims`（不重算 bootstrap） | **进行中→门禁加固**（派生未重算） |
| ES-4 | 机制层代表案例；缺标「未记录」；不伪造 | `enrich_mechanism_captions.py`：images[] 补 batch/caseId/derivedAt/headCommit/sourcePath/captionNote；index `captionProvenance.pngBytesUntouched=true`；**R7 未重跑** | **进行中→图注 provenance 已挂** |
| ES-5 | 负提升原因改为测量量推导 | 既有 NLC 契约 + 新增 `negative_lift_display`（measured 主栏 / ruleInferred 次栏显式标注） | **进行中→口径辅助已挂** |

## R7 / A24 开项（勿谎关）

| ID | 状态 | 证据 |
|---|---|---|
| **R7 / G7** | 开 | tip `0654d13` 超前 mechanism head `7623a52` **122** commits；见 MECHANISM_HEAD_NOTE §7 |
| **A24** | xfail 保留 | `test_a24_export_label_recognized_forbidden_until_schema_exists`；产品缺口，勿伪绿 |

## 明确未做

- mechanism 大批量重跑（R7）
- 改 museum_processing.py
- 伪造 Top-k / CI / 机制指标
- push / 合 main / 改 TASK_BOARD 主文件（worktree 外）
- 把 A24 改成正式 assert
