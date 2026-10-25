# ES_EVAL_PROGRESS — 评测侧 ES-3/4/5 推进记录

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-25（Asia/Shanghai）
- 分支 tip：0f20bf1（0f20bf1928c97d0e15add82066efcfb07805faa2）
- TASK_BOARD 本体在 D:\\RubbingMind\\docs\\product-upgrade\\TASK_BOARD.md（worktree 外）；本文件为 worktree 内进度镜像，供 Green 勾板。

## 状态（本提交）

| ID | TASK_BOARD 目标 | 本提交落地 | 状态 |
|---|---|---|---|
| ES-3 | 按文物聚类 bootstrap CI；CI 下界 >0 才能写「提升」 | 既有 derived/ci_by_artifact.json 契约测 + may_claim_positive_lift / lift_claim_label 门禁（experiments/eval_export_contract.py，	ests/test_es_derived_contracts.py） | **进行中→契约门禁已挂**（派生文件沿用既有批次，未重算） |
| ES-4 | 机制层代表案例；缺标「未记录」；不伪造 | index/case 溯源断言；tip≠headCommit；MECHANISM_HEAD_NOTE tip 更新；**R7 不大重跑** | **进行中→禁令+溯源加固** |
| ES-5 | 负提升原因改为测量量推导 | 
egative_lift_causes.json 抽样契约：measuredEvidence + ruleInferredBasis 启发式标注 + unavailableReason | **进行中→导出契约已挂** |

## 附带（ROI / 导出）

- R3 会话形状校验（评测侧，不复制 arch 实现）：experiments/roi_compare_session_contract.py
- 无真值 glyph：
ot_evaluated + 禁止数值指标（
equire_unevaluated_metrics）
- arch R2–R8：见 REVIEW_ARCH_PHASE2_ROI.md（可进门禁，尚未进 feature）；**本侧不抢改**

## 明确未做

- mechanism 大批量重跑（R7）
- 改 museum_processing.py
- 伪造 Top-k / CI / 机制指标
- push / 合 main / 改 TASK_BOARD 主文件（worktree 外）
