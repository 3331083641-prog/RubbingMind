# REVIEW_EVALSCI_G1_R1 — G1/R1 TS ROI/SHA 转绿门禁请求

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-25（Asia/Shanghai）
- 分支：`agent/eval-sci`
- 对齐 feature tip：`e9ce60e`（含 AB-7 api.ts ROI/SHA + report R1 + jinshi claims）
- 约束：不改 `museum_processing.py`；R7 不大重跑；不 push；不合 `main`

## 结论

**请求红队门禁：可进。** G1/R1（`GlyphInferenceRecord` 声明 `roi` / `inputImageSha256` / `cropSha256`）已随 feature@08d8da8→e9ce60e 落地，评测侧已从 xfail 改为正式 assert 并全量转绿。

## Feature tip

| 项 | 值 |
|---|---|
| `feature/product-grade-upgrade` | `e9ce60e945ffe4d561cc26434b6d5f000c69ccf1` |
| eval-sci tip | 4609890 (460989029b44d2e1814e469643825b0fd6ce66da) |
| 合入路径 | `d081808` → merge `08d8da8` → `3ac23d4` → merge `e9ce60e` → `1026e69` + 本 REVIEW/测试 commit |
| AB-7 证据文件 | `apps/web/src/services/api.ts`（`GlyphInferenceRecord.roi` + 两 SHA）；报告侧 `apps/web/src/components/reports/data/glyphInference.ts` 等 |

## G1 转绿证据

- 接口契约：`export interface GlyphInferenceRecord` 含
  - `roi: { imageBBox, mappedSourceBBox, mappedInsideSource, cropWidth, cropHeight, scaleFromSource }`
  - `inputImageSha256: string`
  - `cropSha256: string`
- 评测：`tests/test_phase2_roi_fields.py::test_ts_glyph_inference_record_declares_roi_and_shas_g1` **PASSED**（已去掉 `pytest.xfail`，并对 roi 子字段做正式 assert）
- arch 侧同名契约：`tests/test_phase2_roi_arch.py::test_ts_glyph_inference_record_declares_roi_and_shas_g1` **PASSED**
- Phase2 ROI 子集（fields + arch）：**21 passed**（merge 后复跑）
- 全量：python -m pytest tests -q → **708 passed, 1 xfailed**（A24）；0 failed

## 剩余未关门项（不挡本 G1 门禁）

| ID | 状态 | 说明 |
|---|---|---|
| **A24** | 仍 xfail | Phase2 export `label=candidate\|human_accepted_glyph` schema 未落地 |
| **R7 / G7** | 文档禁令仍开 | mechanism `headCommit=7623a52` 滞后 tip；**不大重跑**；见 `MECHANISM_HEAD_NOTE.md` |
| 金石后续 | 已随 e9ce60e 合入 claims 增量 | 本 REVIEW 不另开金石专项；若 tip 再前进可再对齐 |

## 红队请核

1. feature tip 是否仍为 / 包含 `e9ce60e`。
2. `api.ts` GlyphInferenceRecord 字段与后端 `_map_roi` 同名同形。
3. eval-sci tip 含 G1 正式 assert 且全量 pytest 无 fail（允许 A24 xfail）。


---

## 附录：对齐 feature@0654d13（2026-10-25 13:11 Asia/Shanghai）

| 项 | 值 |
|---|---|
| feature tip | `0654d1307f849f5dadbfaca87fd96f2ce3b56c41` |
| eval-sci tip（ff） | `0654d1307f849f5dadbfaca87fd96f2ce3b56c41`（原 `01dd3be` fast-forward） |
| pytest | **709 passed, 1 xfailed (A24), 0 failed** |
| G1 | 仍正式绿（本 tip 未回退） |
| A24 | 仍 xfail，勿伪绿 |
| R7 | tip 超前 head `7623a52` 122 commits；未重跑；MECHANISM_HEAD_NOTE §7 |
| 本轮增量 | ES-4 图注 provenance；ES-3 `summarize_lift_claims`；ES-5 `negative_lift_display` |
| 门禁请求 | 可门禁（未 push）；请红队复核 tip 与开项台账 |

