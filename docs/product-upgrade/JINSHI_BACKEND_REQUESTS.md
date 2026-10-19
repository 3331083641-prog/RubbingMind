# 金石史料 → 后端 / 架构 需求清单（RM-金石史料）

共享文件（`main.py`、`apps/web/src/services/api.ts`、`App.tsx`、数据库 schema）不由本分支修改。以下需求交给架构/后端 Agent，Green 决定是否排期。

| 编号 | 关联审计项 | 共享文件 | 需求 | 验收 |
|---|---|---|---|---|
| BR-01 | C-03 | `apps/web/src/services/api.ts:51` | 离线回退分支直接返回 `record.inferenceDemo`。数据里已带 `textProvenance`，前端类型也已加可选字段，所以只需确认回退时不丢弃该字段。如果日后改成重新构造对象，必须透传 `textProvenance`。 | 后端离线时，工作台仍显示“合成测试文本”提示 |
