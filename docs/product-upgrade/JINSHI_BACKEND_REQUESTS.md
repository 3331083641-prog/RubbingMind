# 金石史料 → 后端 / 架构 需求清单（RM-金石史料）

共享文件（`main.py`、`apps/web/src/services/api.ts`、`App.tsx`、数据库 schema）不由本分支修改。以下需求交给架构/后端 Agent，Green 决定是否排期。

| 编号 | 关联审计项 | 共享文件 | 需求 | 验收 |
|---|---|---|---|---|
| BR-01 | C-03 | `apps/web/src/services/api.ts:51` | 离线回退分支直接返回 `record.inferenceDemo`。数据里已带 `textProvenance`，前端类型也已加可选字段，所以只需确认回退时不丢弃该字段。如果日后改成重新构造对象，必须透传 `textProvenance`。 | 后端离线时，工作台仍显示“合成测试文本”提示 |
| BR-02 | C-01 | `main.py:338-345`（`get_stele`）、`museum_manager.get_stele_by_id` | 同时接受旧 ID 和新命名空间 ID：`rm:rubbing:<id>` 去掉前缀后等于现行 id；`rm:demo:<core id>` 只解析到演示样本；`rm:retired:<id>` 返回 410（与现有逻辑一致）。可以直接调用 `history_graph.resolve_id()` 和 `data/catalog/id_mapping.json`，不需要新表。 | `GET /api/steles/rm:demo:tang-duobao` 返回演示记录；`GET /api/steles/rm:rubbing:tang_01_duobao` 返回馆藏记录；两者 `id` 不同；旧 ID 的响应逐字节不变 |
| BR-03 | C-01 | `main.py:332-345`、`/api/steles/{id}/graph`（`main.py:352-361`） | 响应里增加只读字段 `entity`（即 `resolve_id()` 的结果：kind、newId、depictsSameWorkAs），前端据此区分“演示样本”和“馆藏拓本”，不再靠 id 字符串判断。馆藏 id 的 `/graph` 现在走 `catalog_graph`；如果要显示对应的演示样本，可以附上 `demoSamples`。 | 4 个演示 id 的响应 `entity.kind=demo_sample`；28 件馆藏为 `rubbing` |
| BR-04 | C-01 | `apps/web/src/data/graphSelection.ts`、`App.tsx` | 图谱页选择器用 `rm:demo:` 标出演示入口，并显示“对应馆藏 tang_01_duobao（同作品，待人工复核）”。`graphSelection.ts` 不属于共享文件，但它的选择逻辑与 `App.tsx` 耦合，请前端 Agent 一并处理 | 截图显示演示和馆藏两种入口有区别 |
