# 金石史料 · 前端需求清单（RM-金石史料）

共享前端文件冲突时由报告前端处理；金石不直接改 `WorkbenchPage`。


## 2026-10-25 · 合并冲突归属（WorkbenchPage）

| 编号 | 来源 | 涉及 | 需求 | 验收 |
|---|---|---|---|---|
| FR-WP-01 | 红队 / 合并 | `WorkbenchPage`（及与之冲突的报告前端改动） | **冲突交给报告前端处理**；金石分支不改 `WorkbenchPage`。演示隔离与 `includeDemo` 开关若需 UI，等报告前端按 BR-08/BR-09 接线。 | 合并后 WorkbenchPage 以报告前端版本为准，金石不覆盖 |

