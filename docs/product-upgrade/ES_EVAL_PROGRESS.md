# ES_EVAL_PROGRESS — 评测侧 ES-3/4/5 推进台账

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-25 16:25 Asia/Shanghai
- 分支 tip：rebase on 7e080c5（AB-8 health samples）；R7 lag=184；A24/R7 仍开勿假关
- 对齐：fast-forward eature/product-grade-upgrade@c761d54（含 reports MechanismPanel / claims 台账）
- TASK_BOARD 真源：D:\RubbingMind\docs\product-upgrade\TASK_BOARD.md（worktree 外）；本文件为 worktree 内进度镜像，供 Green 监工。

## 状态（本提交）

| ID | TASK_BOARD 目标 | 本提交交付 | 状态 |
|---|---|---|---|
| ES-3 | 按文物聚类 bootstrap CI；CI 下界 >0 才能写“提升” | 既有 ci_by_artifact.json 契约 + may_claim_positive_lift / lift_claim_label / summarize_lift_claims；**新增** lift_claim_summary.json 导出 + API liftClaimLabel/liftClaimSummary 注解（不重算 bootstrap） | **进行中·可再门禁**（数据未重算） |
| ES-4 | 机制层代表案例图注「未记录」勿伪绿 | enrich_mechanism_captions.py（images[] 含 batch/caseId/derivedAt/headCommit/sourcePath/captionNote；index captionProvenance.pngBytesUntouched=true）；**R7 未重跑** | **进行中·图注 provenance 已挂** |
| ES-5 | 负提升原因改为测量量推导 | 既有 NLC 契约 + 
egative_lift_display；**新增** 
egative_lift_display.json 伴生导出（measured 主列 / ruleInferred 次列启发式标注） | **进行中·口径伴生已挂** |

## R7 / A24 开项（勿谎关）

| ID | 状态 | 证据 |
|---|---|---|
| **R7 / G7** | 开 | tip@7e080c5+stamp 超前 mechanism head 7623a52 **184** commits（见 MECHANISM_HEAD_NOTE §15）；只记账未假关 |
| **A24** | xfail 保持（禁伪 Top-k） | 	est_a24_export_label_recognized_forbidden_until_schema_exists；产品/schema 缺口（AB-8 未落地 export label）；勿伪绿；另有 	est_a24_schema_still_absent_keep_xfail_evidence |

## 明确未做

- mechanism 大重跑 / 重算（R7）
- 改 museum_processing.py
- 伪绿 Top-k / CI / 负提升指标
- push / 合 main / 改 TASK_BOARD 真源文件（worktree 外）
- 把 A24 改成正式 assert

## 对齐 feature@ed9f1a0（2026-10-25 15:43）

- FF 自 51fa1ba → ed9f1a0（含 report slice10；export JSON liftClaims 屏上对齐属报告侧）
- 评测侧 ES-3/4/5 契约与 derived 再核：仍绿；不伪绿 Top-k/CI
- R7 lag=169 / A24 xfail：**勿谎关**
