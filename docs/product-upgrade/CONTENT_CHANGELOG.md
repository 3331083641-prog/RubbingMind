# CONTENT_CHANGELOG — 金石内容修正记录

- 作者：RM-金石史料（Agent 03/06/07）
- 分支：`agent/jinshi`（基于 `feature/product-grade-upgrade@f0c5886`）
- 规则：每条史实修改都附来源 URL（真实打开过的页面）；查不到的写“未核实”，不补写。时间为 Asia/Shanghai。
- 对应审计：`docs/product-upgrade/AUDIT_CONTENT.md`（C-xx 编号）

## 2026-10-19 12:40 · C-03 合成测试文本标记（wei-jianyi）

| 位置 | 修改前 | 修改后 | 依据 |
|---|---|---|---|
| `data/catalog/core_samples.json` 与 `apps/web/src/data/coreSamples.json`（两份逐字节一致）· wei-jianyi | `translation`、`inferenceDemo.transcript` 是“夫人諱某，昌黎人也……”，无任何标记 | 文首加“【合成测试文本（sample_generator 生成，非真实释文）】”；新增 `textProvenance`（kind=`synthetic_test_text`，isAuthenticInscription=false）；`damaged_summary`、`summary` 开头加同一标签；35 个字符加 `textKind`；badges 加“合成测试文本” | `sample_generator.py` `SAMPLE_SOURCES["sample_4.png"].lines` 与该文本逐字相同（项目内部来源，不是史料）；审计 C-03 |
| `data/history/wei-jianyi.json` | `identity` 与主节点 `desc` 没有说明文本是合成的 | `identity`、主节点 `desc` 开头加标签；新增 `textProvenance` | 同上 |
| `evidence_retrieval.py` | wei-jianyi 的证据条目没有标记 | 条目 `text` 开头加标签，并带 `textProvenance`；回答中命中这类条目时，开头加“注意：检索结果含合成测试文本……不能作为史料证据”；响应新增 `contentWarnings`；索引版本升到 v2.4（指纹变化后自动重建，旧索引不受影响） | 同上 |
| 前端 `WorkbenchPage.tsx` / `HomePage.tsx` / `EvidenceSearch.tsx` / `types/stele.ts` | 没有标记 | 工作台顶部提示、字符区标题、首页卡片、检索证据标题和警示行都显示标签；类型只加可选字段 | 同上 |
| `sample_generator.py`、`knowledge_agent.py`（sample_4） | 没有标记 | 加常量 `SYNTHETIC_TEXT_LABEL` 和 `text_provenance` 字段；生成器逻辑不变，也没有删除 | 同上 |
