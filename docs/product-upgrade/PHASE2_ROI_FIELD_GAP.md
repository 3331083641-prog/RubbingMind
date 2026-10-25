# PHASE2_ROI_FIELD_GAP — ROI 局部对照字段清单与缺口

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-25（Asia/Shanghai）
- 分支：`agent/eval-sci` @ `65f7815`
- 范围：Phase 2 评测骨架 — 「ROI 局部对照」所需可追溯字段
- 只读对照：`main.py`、`museum_processing.py`（**未改**）、`glyph_inference.py`、`catalog_assessment.py`、`apps/web/src/services/api.ts`、`apps/web/src/types/stele.ts`
- 不删实验、不改 backend 处理内核

## 1. 目标字段（评测骨架要求）

| # | 字段 | 用途 |
|---|---|---|
| F1 | 文物 ID | 锚定碑刻 / 拓片实体 |
| F2 | 源 SHA | 对照所用源图（或选定图）字节身份 |
| F3 | runId | 绑定一次处理运行 |
| F4 | ROI | 局部框（坐标系、尺度、是否映射回源图） |
| F5 | 版本 | 算法 / 契约 / 评测版本 |
| F6 | 参数 | 实际生效参数（非仅请求参数） |
| F7 | 时间 | 推断 / 处理 / 评审发生时刻 |

以下「路径」以 API JSON 或持久化 record 为准；TS 类型为前端镜像。

## 2. 逐项对照

### F1 文物 ID

| 现有路径 | 类型 | 可追溯？ | 说明 |
|---|---|---|---|
| `ProcessingRun.steleId` / process 响应同名字段 | `string` | 是 | `museum_processing` 写入 run；`GET /api/steles/{id}/runs` |
| `GlyphInferenceRecord.steleId` | `string` | 是 | `POST /api/steles/{stele_id}/inferences` → `glyph_inference.infer` |
| catalog assessment 路径参数 `stele_id`；评审记录内嵌 | `string` | 是 | `GET/POST /api/catalog/{stele_id}/assessment*` |
| 实验机制 case：`mechanism.json` / `index.json` → `cases[].caseId`（含 batch 行键，**不是**博物馆 steleId） | `string` | 部分 | 批内可追溯；与产品 steleId 需另映射 |

**缺口：** 实验 caseId ↔ 产品 steleId 无统一对照表暴露给 ROI 评测；Phase 2 若跨「实验机制图 vs 产品 ROI」需显式 mapping 字段或禁止混用。

### F2 源 SHA

| 现有路径 | 类型 | 可追溯？ | 说明 |
|---|---|---|---|
| `ProcessingRun.inputImageSha256` | `string` | 是 | 处理输入 |
| `ProcessingRun.outputSha256`（按角色） | `Record<string,string>` | 是 | 输出角色摘要 |
| `GlyphInferenceRecord.inputImageSha256` | `string` | 是 | infer 持久化 |
| `GlyphInferenceRecord.selectedImageSha256` / `imageProvenance.selectedImageSha256` | `string` | 是 | 实际裁切图（original / restored） |
| `GlyphInferenceRecord.cropSha256` | `string` | 是 | ROI 裁切 PNG |
| `imageProvenance`：`imageSource`、`runOwnership`、宽高 | object | 是 | `api.ts` GlyphInferenceRecord |
| catalog：`sourceImageSha256` / `inputImageSha256` / `outputImageSha256` | `string` | 是 | assessment 资产校验 |
| glyph-benchmark 注解要求 `imageSha256` | `string` | 契约有 / 数据空 | `data/catalog/glyph-benchmark-v2.json` annotations=0 |

**缺口：** 前端 `GlyphInferenceRecord` 类型未显式列出 `inputImageSha256` / `cropSha256` / `roi`（后端有）；TypeScript 与后端漂移会导致评测脚本若只信 TS 漏字段。ROI 对照若需「工作图坐标 vs 源图像素」的成对 SHA，今日靠 provenance + cropSha256，缺独立「ROI 对照会话」聚合对象。

### F3 runId

| 现有路径 | 类型 | 可追溯？ | 说明 |
|---|---|---|---|
| `ProcessingResult.runId` / `ProcessingRun` | `string` | 是 | process / runs API |
| `GlyphInferenceRecord.runId` | `string | null` | 是 | 来自 provenance；original 图可为 null/无 run |
| `RunSelection.runId` | `string | null` | 是 | 报告选 run |
| catalog assessment | 视批次数据 | 部分 | 有 algorithmVersion/parameters；**不一定**有与 `ProcessingRun.runId` 同形的 id |

**缺口：** catalog assessment 与 processing run 的 runId 未强制同一命名空间；ROI 对照若跨 assessment 与 inference，需文档约定「以 inference.runId 或 assessment 自有 id 为准」并禁止静默混比。

### F4 ROI

| 现有路径 | 类型 | 可追溯？ | 说明 |
|---|---|---|---|
| `GlyphInferenceRecord.bbox` | `{x,y,w,h}` number | 是 | 请求坐标系 = 选定图像素 |
| 后端 `record.roi`（`_map_roi`） | `imageBBox` / `mappedSourceBBox` / `mappedInsideSource` / `cropWidth` / `cropHeight` / `scaleFromSource` | 是（持久化 JSON） | **TS 类型未声明 `roi`** |
| catalog review `roi`：`{x,y,width,height}` + 链接信息 | object | 是 | `save_review`；宽高字段名 `width`/`height`（非 w/h） |
| `GET .../assessment/region-crop` | 图像 | 是 | 依赖评审 ROI |
| `museum_processing` | — | 无 | **无 bbox/roi 字段**（整图处理） |

**缺口：**

1. **坐标系分裂：** glyph 用 `w/h`，catalog review 用 `width/height`；评测断言需归一化 schema。
2. **TS 漏 `roi`：** 前端无法类型安全消费 `mappedSourceBBox` / `mappedInsideSource`。
3. **无「对照 ROI 对」：** 缺少成对字段如 `beforeRoi`/`afterRoi` 或同一 bbox 在 original vs restored 上的二次映射结果（今日仅单次选定图上的 bbox + 映射回 source）。
4. 整图 run（museum_processing）不产生 ROI；局部对照必须走 inference 或 assessment 评审链路。

### F5 版本

| 现有路径 | 类型 | 可追溯？ | 说明 |
|---|---|---|---|
| `ProcessingResult.algorithmVersion` | `string` | 是 | |
| `RunChangeStatus.passthroughCriterion` / `grayCriterion` | string | null | 是 | 判据版本（如 `pixel-equal-v1`、`gray-bt601-pixel-equal-v1`） |
| `visualAnalysis.version` | `string` | 是 | 字形视觉分析 |
| catalog `algorithmVersion` | string | 是 | assessment 载荷 |
| glyph-benchmark `version` / evaluation `status` | string | 是 | 清单级；非 per-ROI |
| mechanism `index.json` → `headCommit` | string | 是 | **落后 tip**（见 `MECHANISM_HEAD_NOTE.md`） |

**缺口：** 无统一 `evalSchemaVersion` 挂在每条 ROI 对照记录上；Phase 2 建议在评测导出中自管版本字段。mechanism headCommit ≠ tip 时不可把机制图版本等同产品 tip。

### F6 参数

| 现有路径 | 类型 | 可追溯？ | 说明 |
|---|---|---|---|
| `ProcessingRun.algorithmParameters` | `Record<string, string|number|null>` | 是 | 请求侧为主 |
| `RunChangeStatus.effectiveParameters` (+ Source / UnavailableReason) | object | null | 是 | **实际生效**；SPEC E-10 |
| catalog assessment `parameters` | object | 是 | |
| glyph infer：模型名 / source / scoreBasis；**无**完整 vision API 超参快照 | 部分 | 环境变量决定 endpoint；记录有 `model` |

**缺口：** inference 路径缺少与 process 同级的 `effectiveParameters`；OCR baseline 有 `countsAsAccuracy:false` 等，但未进入 ROI 对照参数袋。Phase 2 对照「同 ROI 不同参数」时只能依赖 run 级 effectiveParameters，不能依赖 inference 自身。

### F7 时间

| 现有路径 | 类型 | 可追溯？ | 说明 |
|---|---|---|---|
| `ProcessingRun.startedAt` / `finishedAt` | ISO string | 是 | |
| `GlyphInferenceRecord.createdAt` | ISO string | 是 | |
| `decisions[].at` | ISO string | 是 | 采纳/驳回/撤销 |
| catalog review 记录时间戳 | 有 | 是 | `save_review` 历史 |
| mechanism `derivedAt` | string | 是 | 派生时间，非 tip 时间 |

**缺口：** 时区未统一标注（多为 UTC ISO）；报告面向 Asia/Shanghai 时需转换。缺「对照会话开始/结束」时间（多条 inference 聚合）。

## 3. 缺口摘要（给 Phase 2 实现）

| ID | 缺口 | 严重度 | 建议 |
|---|---|---|---|
| G1 | TS `GlyphInferenceRecord` 缺少后端已有的 `roi` / `inputImageSha256` / `cropSha256` | 中 | 补类型；评测读后端 JSON |
| G2 | ROI 字段名 `w/h` vs `width/height` 不一致 | 中 | 评测归一化层 |
| G3 | 无成对 before/after ROI 对照对象 | 高（相对 Phase2 目标） | 新导出 schema，复用 bbox+双图 SHA |
| G4 | catalog assessment runId 与 processing runId 未统一 | 中 | 文档约定 + 可选外键 |
| G5 | inference 无 effectiveParameters | 中 | 对照时 join runId → run.effectiveParameters |
| G6 | 实验 caseId ≠ steleId | 低–中 | 禁止无 mapping 的跨域 ROI 声明 |
| G7 | mechanism headCommit 落后 tip | 文档阻断 | 见 `MECHANISM_HEAD_NOTE.md`；重跑前不宣称字节一致 |
| G8 | glyph-benchmark 无真值注解（n=0） | 高（识读评测） | Top-k 保持 `not_evaluated`（见断言文档） |

## 4. 可直接用于评测导出的最小字段袋（草案）

```text
steleId, inputImageSha256, selectedImageSha256, cropSha256,
runId, bbox, roi.mappedSourceBBox, roi.mappedInsideSource,
algorithmVersion, effectiveParameters (via runId join),
createdAt, inferenceId, status
```

缺 G3 成对结构时，局部对照仅支持「单图 ROI 可追溯」，不支持「同框双版本像素 diff 会话」的一等公民记录。
