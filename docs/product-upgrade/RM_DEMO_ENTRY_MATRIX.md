# rm:demo:* 入口矩阵（arch × jinshi@RV-AI06 / C-16）

对齐：`history_graph.resolve_id` + `id_mapping.json`；合成样本默认隔离，仅显式 opt-in 进入检索。

## 接受（解析到演示实体，不无故 404）

| 入口 | 行为 |
|------|------|
| `GET /api/steles/rm:demo:<legacy>` | `NamespacedSteleIdMiddleware` 改写为 legacy；`museum_manager` 查 core_samples |
| `GET /api/steles/{legacy}`（core 如 `wei-jianyi`） | 直接命中 core_samples |
| `POST /api/research/query` + `steleId=rm:demo:<legacy>` | `_lookup_stele_id` → legacy 存在性校验；原 id 传入 `query` 以触发 `demo_scope_id` opt-in |
| `POST /api/research/query` + `steleId=<demo legacy>` | 同上，`demo_opt_in` = `demo_scope_id` |
| `POST /api/research/query` + `includeDemo=true` | `include_demo` opt-in；可检出合成样本并带 `contentWarnings` |
| `POST /api/research/query` 问题正文含 `rm:demo:` | `rm_demo_id_in_question` opt-in |
| `GET /api/research/steles/rm:demo:<legacy>` | `_lookup_stele_id` 后 `artifact_graph`；证据按 demo id 归档（RV-AI06） |
| `history_graph.get_history_graph(rm:demo:…)` | `resolve_id` kind=`demo_sample`；图谱图用 core_samples，不塌缩为馆藏拓本影像 |

## 拒绝 / 隔离

| 入口或条件 | 行为 |
|------------|------|
| 默认 `POST /api/research/query`（无 opt-in） | 合成样本（`textProvenance.kind=synthetic_test_text`，现为 `wei-jianyi`）不参与检索；`demoScope.included=false` |
| 仅问题中出现「样本/演示」等词 | **不** opt-in |
| `rm:work:*` 当作 stele 路径 | `namespace_mismatch` → 404 |
| 错误 kind 前缀（如 `rm:rubbing:wei-jianyi`） | `namespace_mismatch` → 404 |
| `rm:demo:<非 core / 未映射 id>` | lookup 后 `museum_manager` 无记录 → 404 |
| C-08 主库 `--apply` | **禁止**（仅副本 dry-run；主库 apply 须用户批准并先停后端） |

## 与金石口径

- `include_demo` / `demo_opt_in` / `demoScope` / `contentWarnings`：以 jinshi `evidence_retrieval` 为准（本分支 merge 取 theirs，仅保留 `INDEX=runtime_dir()` 以适配 `RUBBINGMIND_RUNTIME_DIR`）。
- RV-AI06：demo 证据与图谱身份不塌缩到馆藏拓本 id。
- Workbench 页面：以 `agent/report-frontend` 为准，本分支不强留随手改动。
