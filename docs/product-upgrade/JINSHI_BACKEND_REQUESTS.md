# 金石史料 → 后端 / 架构 需求清单（RM-金石史料）

共享文件（`main.py`、`apps/web/src/services/api.ts`、`App.tsx`、数据库 schema）不由本分支修改。以下需求交给架构/后端 Agent，Green 决定是否排期。

| 编号 | 关联审计项 | 共享文件 | 需求 | 验收 |
|---|---|---|---|---|
| BR-01 | C-03 | `apps/web/src/services/api.ts:51` | 离线回退分支直接返回 `record.inferenceDemo`。数据里已带 `textProvenance`，前端类型也已加可选字段，所以只需确认回退时不丢弃该字段。如果日后改成重新构造对象，必须透传 `textProvenance`。 | 后端离线时，工作台仍显示“合成测试文本”提示 |
| BR-02 | C-01 | `main.py:338-345`（`get_stele`）、`museum_manager.get_stele_by_id` | 同时接受旧 ID 和新命名空间 ID：`rm:rubbing:<id>` 去掉前缀后等于现行 id；`rm:demo:<core id>` 只解析到演示样本；`rm:retired:<id>` 返回 410（与现有逻辑一致）。可以直接调用 `history_graph.resolve_id()` 和 `data/catalog/id_mapping.json`，不需要新表。 | `GET /api/steles/rm:demo:tang-duobao` 返回演示记录；`GET /api/steles/rm:rubbing:tang_01_duobao` 返回馆藏记录；两者 `id` 不同；旧 ID 的响应逐字节不变 |
| BR-03 | C-01 | `main.py:332-345`、`/api/steles/{id}/graph`（`main.py:352-361`） | 响应里增加只读字段 `entity`（即 `resolve_id()` 的结果：kind、newId、depictsSameWorkAs），前端据此区分“演示样本”和“馆藏拓本”，不再靠 id 字符串判断。馆藏 id 的 `/graph` 现在走 `catalog_graph`；如果要显示对应的演示样本，可以附上 `demoSamples`。 | 4 个演示 id 的响应 `entity.kind=demo_sample`；28 件馆藏为 `rubbing` |
| BR-04 | C-01 | `apps/web/src/data/graphSelection.ts`、`App.tsx` | 图谱页选择器用 `rm:demo:` 标出演示入口，并显示“对应馆藏 tang_01_duobao（同作品，待人工复核）”。`graphSelection.ts` 不属于共享文件，但它的选择逻辑与 `App.tsx` 耦合，请前端 Agent 一并处理 | 截图显示演示和馆藏两种入口有区别 |

## 2026-10-19 · C-06 / C-08 方案 A（用户经 Green 决定）

| 编号 | 来源 | 涉及 | 需求 | 验收 |
|---|---|---|---|---|
| BR-05 | C-08 | 新的后端同步脚本（例如 `scripts/sync_sqlite_from_catalog.py`），由架构后端负责，可能涉及 `database.py` | 按 `docs/product-upgrade/C08_SYNC_SPEC.md` 执行 `data/catalog/c08_sync_diff.json`：默认只预览；校验 basis SHA；先备份 `.bak`；用户确认后在单个事务里写入；不执行 `hold`；不删行；不改 schema | 规格第 3 节的 7 条；写后 `check_catalog_governance.py --summary` 中 `C08_fieldDiffs=0`、`C08_extraWithCoordinates=0` |
| BR-06 | C-06 | `main.py` `/api/steles`、`/api/steles/{id}`（可选） | 目前前端从静态复本 `apps/web/src/data/reviewLedger.json` 读取台账，不需要后端改动。如果希望 API 用户也能看到，可在记录里附只读字段 `reviewLedger`（取 `data/catalog/review_ledger.json` 对应条目），不要合并成单一状态 | API 响应里同时出现 `catalogueApproval` 和 `evidenceReview` |

## 2026-10-19 · 任务 0 / C-16

| 编号 | 来源 | 涉及 | 需求 | 验收 |
|---|---|---|---|---|
| BR-07 | 任务 0 | `database.py:157-165` `query_steles(include_retired=True)` | 返回下架行（`museum_catalog_status.status='retired'`）时，把 `gis_lng/gis_lat` 置为 None 再返回，不改库。目前只有 `scripts/init_db.py` 调用它，且用的是默认值 False；这一条是防御性需求 | 用含下架行的库调用 `query_steles(include_retired=True)`，5 条下架记录的坐标都是 None |
| BR-08 | C-16 | `main.py:144-154`（`EvidenceQueryRequest`、`/api/research/query`）、`apps/web/src/services/api.ts` | 请求体增加 `includeDemo: bool = False`，透传为 `evidence_retrieval.query(..., include_demo=...)`；`steleId` 允许 `rm:demo:<id>`（与 BR-02 一致，目前 `museum_manager` 会对它返回 404）。api.ts 的检索函数增加同名可选参数 | 默认请求的 `demoScope.included=false`；`includeDemo=true` 或 `steleId=rm:demo:wei-jianyi` 时为 true，证据带合成文本标签 |
| BR-09 | C-16 | 前端 `EvidenceSearch.tsx`（依赖 BR-08 的 api.ts 参数） | BR-08 完成后加一个“包含演示样本（含合成测试文本）”开关，默认关闭；打开时显示 `demoScope.note` | 截图显示开关关闭时没有合成文本，打开时出现标签 |

## 2026-10-19 · C-08 令牌规则（Green）与 8a97a12 只读比对

| 编号 | 来源 | 涉及 | 需求 | 验收 |
|---|---|---|---|---|
| BR-10 | C-08 | `agent/arch-backend` `scripts/sync_catalog_db.py`（8a97a12） | 令牌已与本分支对齐为 `diffDigestSha256[:16]`（即 `sha256(库SHA+目录SHA+行数+操作清单)[:16]`），16 位截断不再算缺陷。仍需：① `--apply` 必须带 `--diff`，并比对 `diffDigestSha256`；② 写后复核补上“下架行仍在、总行数不变”。详见 `C08_BACKEND_REVIEW_8a97a12.md` | `--apply` 无 `--diff` 被拒绝；写后下架 5 行仍在、总行数不变 |
