# REVIEW_EVALSCI_ES_CONTINUATION — ES-3/5 续做 + R7 证据门禁请求

## 元信息
- **门禁 / ES 交付 tip**：9eb8406ba1a788a20dc88035fe2eef314afc7b9d（短写 9eb8406）
- 父：c761d546794c428a29c1a1e0f73c55c464d092cf（feature@c761d54，含 AB-8）
- mechanism headCommit：7623a52a3299b7c948031dfa1f79f04b8eb66d9e
- tip 相对 head 超前：**135** commits（git rev-list --count 7623a52..9eb8406）
- 约束：不改 museum_processing.py；R7 不大重跑；不 push；不合 main；A24 勿伪绿

## 本 tip 交付
1. **对齐**：FF gent/eval-sci → feature@c761d54（含 AB-8）
2. **ES-3**：export_lift_claim_summary.py → derived/lift_claim_summary.json；ci_by_artifact 注解 liftClaimLabel / liftClaimSummary
3. **ES-5**：export_negative_lift_display.py → derived/negative_lift_display.json（measured 主列 / rule 次列；**slim**：无 measuredEvidence 复本）
4. **R7**：MECHANISM_HEAD_NOTE §8 记 lag；未重跑 mechanism_cases.py
5. **A24**：保持 xfail + schema 缺口证据；勿伪绿

## 门禁请求表
| 项 | 状态 |
| --- | --- |
| tip | 9eb8406ba1a788a20dc88035fe2eef314afc7b9d |
| pytest | 见冒烟（目标 ~730 passed / 1 xfailed） |
| R7 | 开；lag 135；未重跑 |
| A24 | 开 / xfail |
| ES-3/5 | 已落地 |
| push / main | **否** |
| 可请求红队门禁 | **是** |
