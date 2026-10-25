# ES_EVAL_PROGRESS — 评测侧 ES-3/4/5 推进台账

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-25 16:46 Asia/Shanghai
- 分支 tip：agent/eval-sci（本 tip parent=19255db；feature 已 FF 合入 19255db）；R7 lag 见 MECHANISM_HEAD_NOTE §16；A24/R7 仍开勿假关
- 对齐基线：feature/product-grade-upgrade@19255dbff2fc9454c51904521aa01fffb61f0186（窄冒烟 747 passed / 1 xfailed）
- TASK_BOARD 真源：D:\RubbingMind\docs\product-upgrade\TASK_BOARD.md（worktree 外）；本文件为 worktree 内进度镜像，供 Green 监工。

## 状态（本提交）

| ID | TASK_BOARD 目标 | 本提交交付 | 状态 |
|---|---|---|---|
| ES-3 | 按文物聚类 bootstrap CI；CI 下界 >0 才能写“提升” | 既有 ci_by_artifact + may_claim_positive_lift / lift_claim_label / summarize_lift_claims + lift_claim_summary.json；**本轮**固化 bootstrap CI 口径说明（见下节；**不重算** bootstrap） | **进行中·可再门禁**（数据未重算） |
| ES-4 | 机制层代表案例图注「未记录」勿伪绿 | enrich_mechanism_captions.py 已挂；captionProvenance.pngBytesUntouched=true；**R7 未重跑**；本轮再核图注口径 | **进行中·图注 provenance 已挂** |
| ES-5 | 负提升原因改为测量量推导 | NLC + negative_lift_display.json（measured 主列 / ruleInferred 次列）；本轮再核负提升口径；**不伪绿** | **进行中·口径伴生已挂** |

## ES-3 bootstrap CI 口径（只读既有 derived；本轮不重算）

对 2026-10-17-v2 / 2026-10-17-v2-text 的 derived/ci_by_artifact.json 实读：

| 项 | 值 |
|---|---|
| bootstrap | 1000 |
| seed | 20261019 |
| artifactN | 14 |
| minReliableArtifacts | 3 |
| groups/批 | 324 |
| 写「提升」门槛 | psnrGainCI95Low > 0 且 ciReliable 且 rtifactN >= minReliable → liftClaimLabel=positive_lift_ci_excludes_zero |
| v2 claimCounts | positive_lift_ci_excludes_zero=35；no_positive_lift_claim=197；未评测=92 |
| v2-text claimCounts | positive_lift_ci_excludes_zero=35；no_positive_lift_claim=191；未评测=98 |

**禁令**：spans_zero / 
egative / 不可靠 CI / rtifactN < minReliable **不得**写成正提升；无配对参考不报 PSNR/SSIM 增益结论。

## ES-4 / ES-5 口径再核

- **ES-4**：images[] 须含 batch/caseId/derivedAt/headCommit/sourcePath/captionNote；缺图用「未记录」；captionProvenance.pngBytesUntouched=true 表示只改 JSON 图注、未碰 PNG 字节；机制 head 仍为 7623a52，报告不得声称与 tip 字节一致。
- **ES-5**：展示以 primaryMeasuredCauses / measuredEvidence 为主；
uleInferredCause 仅次列启发式；
egative_lift_display.json 保持 slim（不含 measuredEvidence 本体）。

## 导出标签契约（A24；勿假关）

- 产品/schema **仍无** label=candidate|human_accepted_glyph 导出字段（	est_a24_schema_still_absent_keep_xfail_evidence PASSED）。
- 	est_a24_export_label_recognized_forbidden_until_schema_exists **保持 xfail**；禁止伪绿 Top-1/Top-3/拒识率；无独立真值时上述指标保持「未评测」。

## R7 / A24 开项（勿谎关）

| ID | 状态 | 证据 |
|---|---|---|
| **R7 / G7** | 开 | 本 tip（parent=19255db）相对 mechanism head 7623a52 超前 **185** commits（见 MECHANISM_HEAD_NOTE §16）；只记账未假关；未跑 mechanism_cases.py |
| **A24** | xfail 保持（禁伪 Top-k） | test_a24_export_label_recognized_forbidden_until_schema_exists；schema 缺口未落地；另有 test_a24_schema_still_absent_keep_xfail_evidence |

## 明确未做

- mechanism 大重跑 / 重算（R7）
- 改 museum_processing.py
- 伪绿 Top-k / CI / 负提升指标
- push / 合 main / 改 TASK_BOARD 真源文件（worktree 外）
- 把 A24 改成正式 assert
- 基于已作废 tip（8178f46 / 109eec1 / c6de56e）

## 对齐 feature@19255db（2026-10-25 16:46 Asia/Shanghai）

- 对齐后 HEAD/feature/agent/eval-sci 曾均为 19255db；本 tip 叠文档续开项（parent=19255db）
- pytest：python -m pytest tests/ -q --tb=no → **747 passed / 1 xfailed / 0 failed**；XFAIL = A24 export label
- ES-3/4/5 契约测试仍绿；bootstrap **未**重算；R7/A24 **勿谎关**
