# PHASE2_GLYPH_CANDIDATE_ASSERTIONS — 残字候选不得显示为已识读

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-25（Asia/Shanghai）
- 分支：`agent/eval-sci` @ `65f7815`
- 对照：`glyph_inference.py`、`GlyphInferencePanel.tsx`、`apps/web/src/services/api.ts`、`experiments/evaluate_glyphs.py`、`data/catalog/glyph-benchmark-v2.json`、`tests/test_glyph_*.py`、`main.py` glyph / glyph-evaluation 路由

## 0. 状态机（现网）

后端 `glyph_inference.decide` / `infer`：

| status | 含义 | 如何进入 |
|---|---|---|
| `pending_review` | 有候选，待人工 | infer 且 `candidates` 非空 |
| `no_candidate` | 无候选 | infer 且候选空（含视觉拒识等） |
| `human_accepted` | 人工采纳某一候选 | `action=accept` + glyph ∈ candidates |
| `human_rejected` | 人工驳回全部候选 | `action=reject` |
| （撤销） | 回到待审 | `action=revoke` → `pending_review`，`adoptedGlyph=null` |

`adoptedGlyph` 仅在 accept 非空；**不存在** `recognized` / `accepted`（无 human_ 前缀）等 API 状态值。

## 1. 可自动化断言草案

状态列：**已实现** = 已有代码或测试近似覆盖；**未实现** = Phase 2 待加断言/测试。

| # | 断言 | 层 | 状态 | 对照 |
|---|---|---|---|---|
| A1 | `status` 枚举 ⊆ `pending_review` | `no_candidate` | `human_accepted` | `human_rejected` | API | 部分已实现 | decide/infer 写入；缺 pytest 枚举锁死 |
| A2 | 禁止出现 `recognized` / `accepted` / `auto_accepted` / `ocr_accepted` 作为 `status` | API | 未实现 | 需负向测试 |
| A3 | `status=pending_review` ⇒ `adoptedGlyph is null` | API | 未实现 | infer 初值满足；缺回归 |
| A4 | `status=no_candidate` ⇒ `candidates==[]` 且 `adoptedGlyph is null` | API | 部分 | infer 逻辑；缺显式测试 |
| A5 | `status=human_accepted` ⇒ `adoptedGlyph` ∈ `candidates[].glyph` | API | 已实现 | `decide` 校验；`tests/test_glyph_inference.py` 有决策路径 |
| A6 | `status=human_rejected` ⇒ `adoptedGlyph is null` | API | 部分 | decide 行为；建议锁测试 |
| A7 | `accept` 的 glyph 必须来自当前 `candidates`，不可接受任意汉字 | API | 已实现 | `decide` ValueError |
| A8 | `revoke` 后 `status=pending_review` 且 `adoptedGlyph is null`，并追加 `decisions` | API | 已实现 | decide |
| A9 | `candidates` / `retrievalCandidates` 不得单独改变 `status` 为已采纳 | API | 已实现（设计） | 仅 decide 写 accepted |
| A10 | `ocrBaseline.countsAsAccuracy` 必须为 `false`（或等价：OCR 不计入准确率） | API | 部分 | 字段存在于类型与 UI；需断言永不 true 冒充识读 |
| A11 | `visualAnalysis.rejectRecognition` / source=`rejected` 时不得产生可采纳候选，或 status=`no_candidate` | API | 部分 | infer 分支；建议专项测试 |
| A12 | 模板注册不得把未人工确认的 inference 候选静默升格为真值 | API | 已实现（设计） | `register_template` 注释 + 需人工 basis/annotator |
| A13 | UI 展示候选时文案必须含「候选」语义，禁止「已识读 / 识别结果 / 碑文确定」等无 human_accepted 前提的措辞 | UI | 部分 | `GlyphInferencePanel` 用「候选」「人工采纳」；缺文案禁区测试 |
| A14 | UI 禁区词（无 `human_accepted` 时）：`已识读`、`识别完成`、`碑文为`（断言式）、`OCR 已确认`、`自动采纳` | UI | 未实现 | 需组件/快照或字符串扫描测试 |
| A15 | 仅 `human_accepted` 时可展示「人工采纳：…」类确定态；`pending_review`/`no_candidate`/`human_rejected` 不得展示 adopted 确定态 | UI | 部分 | Panel 以 `adoptedGlyph` 条件渲染 |
| A16 | 人工采纳 / 驳回 / 撤销按钮与 API action 一致：`accept`/`reject`/`revoke` | UI+API | 已实现 | Panel `decide(...)` |
| A17 | `decisions[]` 为 append-only 审计；每次 action 写 `at`+`actor` | API | 已实现 | decide |
| A18 | glyph-benchmark 无独立人工注解时，评测结果 `status` 必须为 `not_evaluated`（或清单 `awaiting_independent_human_annotations`），`top1`/`top3` 为 null | 评测 | 已实现 | `evaluate_glyphs.py` + 当前 `glyph-v2-evaluation.json` |
| A19 | 无真值时禁止把 Top-k 候选准确率写成已评测数值 | 评测 | 已实现 | annotations=[] → not_evaluated |
| A20 | 有真值评测时，拒绝阈值与 Top-k 分离；低分拒绝不得计为正确识读 | 评测 | 已实现（逻辑） | `rejected` + top1/top3；真值仍缺 |
| A21 | `GET /api/glyph-evaluation` 暴露的状态不得把 awaiting 说成已完成识读评测 | API | 部分 | 路由存在；需契约测试 |
| A22 | 报告页 `inferenceRecords` 列表不得因存在 candidates 而把整碑标为「已识读」 | UI/报告 | 未实现 | 需 Reports 文案审计 |
| A23 | `originalStatus`（目录字符 clear/damaged/…）不得映射为 inference `status` | API | 已实现（分离字段） | 两字段并存；缺「禁止拷贝」测试 |
| A24 | Phase 2 导出：候选行 `label=candidate`；仅 human_accepted 行 `label=human_accepted_glyph`；禁止 `label=recognized` | 评测导出 | 未实现 | 骨架草案 |

## 2. 条数统计

- 草案断言总数：**24**
- 已实现（含设计已落地、评测脚本已遵守）：**10**（A5, A7, A8, A9, A12, A16, A17, A18, A19, A23）
- 部分已实现：**8**（A1, A4, A6, A10, A11, A13, A15, A21）
- 未实现：**6**（A2, A3, A14, A22, A24 + 计 A20 逻辑已有但真值数据未落地 → 归「部分」已在上表；未实现严格为 A2, A3, A14, A22, A24 及可再拆的枚举锁）

更干净计数：**24 条草案**；其中测试/代码可宣称「已实现」约 10，「部分」8，「未实现」6。

## 3. UI 文案禁区（评测清单）

在 `status ∈ {pending_review, no_candidate, human_rejected}` 或仅有 candidates 时，下列中文（及同义）不得作为**确定态**标题或徽章：

- 已识读 / 识别完成 / 识别成功
- 碑文（断言式结论，无「候选」修饰）
- 自动确认 / 模型已确认 / OCR 已确认

允许：候选、待人工复核、人工采纳、人工驳回、未评测、不计入准确率。

## 4. 与 ROI 缺口文档的衔接

候选断言消费的追溯字段见 `PHASE2_ROI_FIELD_GAP.md`（steleId、SHA、runId、bbox/roi、时间）。无 G3 成对 ROI 时，仍可对**单条 inference** 做 A1–A24；不可宣称「双版本局部识读对照已闭环」。

## 5. 建议的下一步测试文件（不在本期强制提交）

- `tests/test_glyph_candidate_status_contract.py`：A1–A8, A23
- UI 字符串扫描或 Playwright：A13–A15, A22
- `tests/test_glyph_evaluation_not_evaluated.py`：A18–A21（可薄包装现有 evaluate_glyphs）
