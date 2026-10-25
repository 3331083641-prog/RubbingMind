# PHASE2_ROI_REQUESTS — ROI 局部对照请求清单（转发用）

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-25（Asia/Shanghai）
- 分支：`agent/eval-sci` @ `bdf08e4`+
- 依据：`PHASE2_ROI_FIELD_GAP.md` G1–G8
- 约束：不改 `museum_processing.py` 内核语义以外的历史批次；不删实验；机制重跑另议

每条可直接转发 arch-backend / 报告前端。验收以 pytest `tests/test_phase2_roi_fields.py` 与本清单为准。

---

## R1 ← G1　TS 补齐推理 ROI/SHA 字段

| 项 | 内容 |
|---|---|
| 字段名 | `roi`, `inputImageSha256`, `cropSha256`（及可选 `selectedImageSha256`） |
| 接口路径 | 类型：`apps/web/src/services/api.ts` → `GlyphInferenceRecord`；数据：`POST/GET /api/steles/{stele_id}/inferences` |
| 现状 | 后端 JSON **已有**上述字段；TS 接口未声明 → 前端/评测若只信类型会漏追溯 |
| 期望 | `GlyphInferenceRecord` 声明与后端同名同形：`roi: {imageBBox, mappedSourceBBox, mappedInsideSource, cropWidth, cropHeight, scaleFromSource}`；三 SHA 为 `string` |
| 验收 | TS 含字段名；报告/对照页可读取 `mappedSourceBBox` 而不用 `as any`；`test_phase2_roi_fields` 中 G1 相关 xfail 转绿 |
| 责任方 | **报告前端**（类型）；后端无需改（已具备） |

## R2 ← G2　ROI 宽高字段归一

| 项 | 内容 |
|---|---|
| 字段名 | glyph：`bbox.w`/`bbox.h`；catalog：`roi.width`/`roi.height` |
| 接口路径 | `GlyphBox`（`POST .../inferences`）；`ReviewBox`（`POST /api/catalog/{stele_id}/assessment/review`） |
| 现状 | 两套命名并存，评测无法同一 schema 断言 |
| 期望 | 对外契约增加归一层：导出/对照 API 统一为 `{x,y,w,h}` **或** 明确 `schema: 'glyph-bbox' | 'review-box'`；禁止静默混用 |
| 验收 | 文档 + 单一归一函数有单测；Phase2 导出只出现一种几何字段名 |
| 责任方 | **arch-backend**（契约/归一）；报告前端跟类型 |

## R3 ← G3　成对 before/after ROI 对照对象

| 项 | 内容 |
|---|---|
| 字段名 | 建议：`roiCompareSession` 含 `steleId`, `runId`, `bbox`, `beforeImageSha256`, `afterImageSha256`, `beforeCropSha256`, `afterCropSha256`, `algorithmVersion`, `effectiveParameters`, `createdAt` |
| 接口路径 | 新建导出或扩展报告：`GET /api/steles/{id}/report` / 专用 `.../roi-compare`（路径由 backend 定） |
| 现状 | 仅单次选定图上的 `bbox`+`roi`；无双图同框会话 |
| 期望 | 一等公民记录支持「同框 original vs restored」像素/裁切对照；缺图时显式 `unavailableReason`，不填假 SHA |
| 验收 | 有真实 run 时返回成对 SHA；无 run 时 reason 非空；禁止用单图字段冒充成对 |
| 责任方 | **arch-backend**（主）；报告前端展示 |

## R4 ← G4　assessment 与 processing 的 run 标识对齐

| 项 | 内容 |
|---|---|
| 字段名 | `runId`（与 `ProcessingRun.runId` 同命名空间）或显式 `processingRunId` |
| 接口路径 | `GET /api/catalog/{stele_id}/assessment`；`GET /api/steles/{id}/runs` |
| 现状 | 部分 assessment（如 tang_01）已有 `runId`，但未强制「有则命中 /runs，无则 null+reason」的全量契约 |
| 期望 | assessment 载荷可关联到具体 `ProcessingRun.runId`（可空，但空时写 `runLink: null` + reason） |
| 验收 | 有关联时 ID 能在 `/runs` 命中；无关联不静默 |
| 责任方 | **arch-backend** |

## R5 ← G5　inference 可追溯生效参数

| 项 | 内容 |
|---|---|
| 字段名 | `effectiveParameters`（可 join）或 inference 内嵌 `runEffectiveParameters` |
| 接口路径 | `POST/GET .../inferences`；join `GET .../runs` → run.`effectiveParameters` |
| 现状 | inference **无** `algorithmVersion` / `effectiveParameters`；仅有 `runId`（original 常为 null） |
| 期望 | `runId` 非空时响应带 `effectiveParameters`（recorded/derived）与 `algorithmVersion`；`runId` 空时 `effectiveParameters: null` + `effectiveParametersUnavailableReason` |
| 验收 | 契约字段稳定；pytest 对「有 run / 无 run」两分支断言 |
| 责任方 | **arch-backend** |

## R6 ← G6　实验 caseId ↔ 产品 steleId 映射

| 项 | 内容 |
|---|---|
| 字段名 | `steleId` 或 `caseIdToSteleId` 对照表 |
| 接口路径 | 机制/实验只读 API 与产品 stele API 之间；文档或 `data/` 映射文件 |
| 现状 | `derived/mechanism` 用 batch caseId，与博物馆 steleId 不同域 |
| 期望 | 跨域 ROI/机制图引用必须带 mapping；无 mapping 时 UI/报告禁止并排「同一文物」声明 |
| 验收 | 无 mapping 的混用被测试或门禁拒绝 |
| 责任方 | **arch-backend**（映射源）；报告前端（禁混用） |

## R7 ← G7　机制 headCommit 与 tip 声明（文档门禁，非本周实现）

| 项 | 内容 |
|---|---|
| 字段名 | `headCommit`（`derived/mechanism/index.json`） |
| 接口路径 | `GET /api/experiments/{id}/mechanism`；文档 `MECHANISM_HEAD_NOTE.md` |
| 现状 | headCommit=`7623a52` 落后 tip；已文档禁令 |
| 期望 | tip 前移后重跑 mechanism 并更新 headCommit；此前报告不得宣称与 tip 字节一致 |
| 验收 | 重跑后 index.headCommit == 声明 tip；重跑前文案门禁保持 |
| 责任方 | **RM-评测科学家**（重跑/文档）；报告前端遵守禁令 |

## R8 ← G8　无真值时 Top-k 保持未评测

| 项 | 内容 |
|---|---|
| 字段名 | glyph-evaluation：`status`, `top1`, `top3`, `rejectionRate` |
| 接口路径 | `GET /api/glyph-evaluation`；`data/catalog/glyph-benchmark-v2.json`；`experiments/evaluate_glyphs.py` |
| 现状 | annotations=0 → `not_evaluated` / null 指标（已正确） |
| 期望 | **保持**；禁止在无独立人工注解时写入数值准确率；UI 不得显示伪造 Top-k |
| 验收 | `test_phase2_glyph_candidate_assertions` 绿；有注解后另开评测任务 |
| 责任方 | **arch-backend**（保持契约）；报告前端（未评测文案）；评测科学家（真值采集另项） |

---

## 汇总

| ID | 缺口 | 责任方 |
|---|---|---|
| R1/G1 | TS 补 `roi`/SHA | 报告前端 |
| R2/G2 | ROI 字段归一 | arch-backend + 前端 |
| R3/G3 | 成对 ROI 会话 | arch-backend + 前端 |
| R4/G4 | runId 对齐 | arch-backend |
| R5/G5 | inference 生效参数 | arch-backend |
| R6/G6 | caseId↔steleId | arch-backend + 前端 |
| R7/G7 | mechanism head 重跑 | 评测科学家（后续） |
| R8/G8 | 未评测契约保持 | backend + 前端 |

条目数：**8**（R1–R8）。

---

## 落地跟踪（评测侧 0f20bf1）

- 2026-10-25：REVIEW_ARCH_PHASE2_ROI.md — arch@fa31279 对 R2–R6/R8 **可进门禁**；feature 仍 9d8428e 未含 ROI。
- R1（TS）/ R7（mechanism head）仍开；R7 **不大重跑**，禁令见 MECHANISM_HEAD_NOTE.md。
- 评测侧 ES-3/4/5 契约见 ES_EVAL_PROGRESS.md 与 	ests/test_es_derived_contracts.py。
