# REVIEW_EVALSCI_ES_CONTINUATION — ES-3/5 续做 + R7 证据门禁请求

## 元信息
- tip：9782d42e9d7ad6a52536e48759a065fd9e043f08（短写 9782d42）
- 父：c761d546794c428a29c1a1e0f73c55c464d092cf（feature@c761d54）
- 约束：不改 museum_processing.py；R7 不大重跑；不 push；不合 main；A24 勿伪绿

## 本 tip 交付
1. **对齐**：FF agent/eval-sci → feature@c761d54（含 AB-8）
2. **ES-3**：experiments/export_lift_claim_summary.py → derived/lift_claim_summary.json；experiment_derived.ci_by_artifact 注解 liftClaimLabel / liftClaimSummary（只读）
3. **ES-5**：experiments/export_negative_lift_display.py → derived/negative_lift_display.json（measured 主列 / rule 次列；**slim**：不含 measuredEvidence 数组复本，evidence 仍在 NLC）
4. **R7**：MECHANISM_HEAD_NOTE §8 记录 tip 超前 head **135** commits；未重跑 mechanism
5. **A24**：保持 xfail + schema 缺口证据测试；勿伪绿

## 门禁请求表
| 项 | 状态 |
| --- | --- |
| tip | 9782d42e9d7ad6a52536e48759a065fd9e043f08 |
| pytest | 见本机冒烟（预期 ~730 passed / 1 xfailed） |
| R7 | tip 超前 head 7623a52 135 commits；未重跑 |
| A24 | 仍开 / xfail |
| ES-3/5 | 已落地 companion + 契约测 |
| push / main | **否** |
| 可请求红队门禁 | **是**（在 tip 文档与冒烟一致后） |
