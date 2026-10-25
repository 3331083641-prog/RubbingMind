# REVIEW_ARCH_PHASE2_ROI — 架构 Phase2 ROI 核对（转 Green）

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-25（Asia/Shanghai）
- 核对对象：`agent/arch-backend` @ `fa312799dd7af50b37dbb254f3da6a78cb76f6f8`（短写 `fa31279`）
- feature 实测 tip：`9d8428e5e51d8587ea7032540fbdebfa330efc14`（短写 `9d8428e`；含 5716455 + report@adfc6e0；**尚未含** arch Phase2 ROI）
- 评测侧对照基线：`PHASE2_ROI_REQUESTS.md`（R1–R8）、`PHASE2_ROI_FIELD_GAP.md`（G1–G8）、`PHASE2_GLYPH_CANDIDATE_ASSERTIONS.md`、`REPORT_DATA_SPEC.md`、`MECHANISM_HEAD_NOTE.md`
- 约束：只读核 arch；未改 arch 分支；未 push

---

## 0. 结论（二选一）

### **可进门禁**（针对 arch-backend R2–R6/R8 合入 feature）

arch@fa31279 的 Phase2 ROI **后端契约**（R2 几何归一、R3 成对对照会话、R4 assessment runLink、R5 inference 生效参数 join、R6 case↔stele 映射门禁、R8 无真值不造指标）与 `PHASE2_ROI_REQUESTS` 对齐；评测在 arch worktree **实测**全量 pytest **524 passed / 0 failed**，Phase2 子集 `tests/test_phase2_roi_arch.py` **10 passed**。

**不在本次 arch 门禁范围内、仍须跟踪的缺口：**

| 缺口 | 级别 | 说明 |
|---|---|---|
| **R1 / G1** | 中（前端类型） | 各树 `GlyphInferenceRecord` 仍缺 `roi` / `inputImageSha256` / `cropSha256`；责任方报告前端，**不阻塞** arch 后端合入 |
| **R7 / G7** | 报告表述禁令 | mechanism `headCommit=7623a52` 仍落后 tip；责任方评测科学家；**禁止**宣称与 tip 字节一致；**不阻塞** arch ROI 合入 |

若门禁定义为「端到端 Phase2 ROI（含 TS + 机制重跑）」→ 则因 R1/R7 仍开，应标 **有缺口**；本次按 Green 核 **架构落地** 口径，结论为 **可进门禁**。

---

## 1. 落地提交对照

| 请求 | 声称提交 | 实测短哈希/题注 | 评测判定 |
|---|---|---|---|
| R2 | e17110e `roi_geometry` | `e17110e` feat(phase2-r2): canonicalize ROI geometry… | **对齐** |
| R3 | f20a7bb `roi_compare` | `f20a7bb` feat(phase2-r3): paired before/after… | **对齐** |
| R4 | 8f504e9 assessment runLink | `8f504e9` feat(phase2-r4): assessment runLink… | **对齐** |
| R5 | 01149b0 `inference_trace` | `01149b0` feat(phase2-r5): join inference… | **对齐** |
| R6 | a7fdcf0 `case_stele_mapping` | `a7fdcf0` feat(phase2-r6): caseId↔steleId… | **对齐** |
| wire+R8 | fa31279 | `fa31279` feat(phase2): wire R2–R6/R8 routes… | **对齐** |
| R1 | （未声称） | 各 worktree `api.ts` 仍缺字段 | **缺 — 前端** |
| R7 | （未声称；arch 测试注明 owned elsewhere） | mechanism index 仍 `7623a52` | **缺 — 评测侧后续** |

---

## 2. 分项核对（字段 / 接口 / null 规则 / 验收）

### R2 ← G2　ROI 宽高归一 — PASS

- 模块：`roi_geometry.py`（`normalize_roi` / `to_review_box` / `export_geometry`）
- 规范：导出统一 `glyph-bbox` `{x,y,w,h,schema,sourceSchema}`；混用 `w/h`+`width/height` → `RoiGeometryError`
- 接口：`GET /api/roi-geometry/normalize`
- 与 REQUESTS「单一归一 + 禁止静默混用」一致

### R3 ← G3　成对 ROI 会话 — PASS（契约）

- 模块：`roi_compare.py` → `build_roi_compare_session` / `report_roi_compare_stub`
- 字段与 REQUESTS 建议一致：`steleId, runId, bbox, beforeImageSha256, afterImageSha256, beforeCropSha256, afterCropSha256, algorithmVersion, effectiveParameters, createdAt, unavailableReason`（另有 `cropUnavailableReason` 在图像对已齐但裁切失败时）
- 接口：`GET /api/steles/{id}/roi-compare`；报告载荷挂 `roiCompareSession`
- null 规则：无 runId / run 不存在 / 缺 original·restored SHA → SHA 全 null + 非空 `unavailableReason`；**不伪造 SHA**
- 备注：验收测覆盖「无 run / 假 runId」路径；成对 crop SHA 依赖本地角色图存在，属 best-effort，未用真实 fixture 做正向绿测（非契约缺口，建议后续补）

### R4 ← G4　assessment runLink — PASS

- `catalog_assessment.attach_processing_run_link`：有 `runId`/`processingRunId` 则 `read_run`；命中 → `runLink={processingRunId,matched,algorithmVersion}`；未命中或空 → `runLink=null` + `runLinkUnavailableReason`
- 明确区分 assess28-* 与 live `ProcessingRun` 命名空间（不静默等同）
- 接口：`GET /api/catalog/{stele_id}/assessment` 返回带 `runLink`

### R5 ← G5　inference 生效参数 — PASS

- 模块：`inference_trace.enrich_inference_traceability`
- `runId` 空 → `effectiveParameters=null` + `effectiveParametersUnavailableReason`
- `runId` 非空 join `ProcessingRun` → `algorithmVersion` / `effectiveParameters` / `Source`；参数仍空则保留/补 reason
- 挂载：`POST/GET .../inferences`

### R6 ← G6　caseId↔steleId — PASS（API+门禁）

- 模块：`case_stele_mapping.py` + `data/catalog/case_stele_mapping.json`（version=1, status=`partial-unreviewed`, 4 条；2 条有 steleId 但均为 `unreviewed`；2 条 steleId=null）
- 接口：`GET /api/case-stele-mapping`（含 `policy.silentEquateForbidden=true`）、`.../{case_id}`、`.../{case_id}/claim/{stele_id}`（未复核 → **409**）
- `sameArtifactClaimAllowed` 仅 `mapped && human_reviewed` — 符合「无 mapping / 未复核禁止并排同一文物」

### R8 ← G8　无真值保持未评测 — PASS（真做到）

- `glyph_annotations.evaluate()`：`evaluationStatus=unassessed`，`top1/top3/rejectionRate=null`，`verifiedLabels=0`，`reason` 非空（benchmark `annotations=[]`）
- API：`GET /api/glyph-evaluation` → `status=not_evaluated`，三指标 null
- 验收测：`test_r8_glyph_evaluation_stays_not_evaluated_without_truth` 断言 null + reason
- **结论：无独立人工真值时不造数值准确率**

### R1 ← G1　前端 TS — **缺**

- 抽查 `rm-report-frontend` / `rm-arch-backend` / `rm-eval-sci` / 主树 `apps/web/src/services/api.ts`：`GlyphInferenceRecord` **均无**顶层 `roi`、`inputImageSha256`、`cropSha256`（仅 `imageProvenance.selectedImageSha256` 等）
- 与 REQUESTS R1 验收「TS 含字段名；G1 xfail 转绿」不符
- 责任方：**报告前端**（arch 未声称落地，正确）

### R7 ← G7　mechanism headCommit — **缺（非 arch）**

- arch 测试文件头注明 R1/R7 owned elsewhere — 正确未抢做
- 评测侧：`derived/mechanism/index.json` headCommit 仍 `7623a52`；tip 已前移；`MECHANISM_HEAD_NOTE` 禁令仍有效
- **本期不要求 arch 重跑机制**

---

## 3. Pytest 实测（评测在 arch worktree 复跑）

### 3.1 Phase2 子集

```
cd D:\RubbingMind\wt\rm-arch-backend   # HEAD=fa31279
python -m pytest tests/test_phase2_roi_arch.py -v --tb=short
→ 10 passed, 1 warning in 2.07s
```

用例：R2×3、R3×2、R4×1、R5×2、R6×1、R8×1。  
**更正：** 早前口头「相关 pytest 16 passed」与本文件 **10** 条不符；以本实测为准。

### 3.2 全量（回应 Green：架构报 524）

```
python -m pytest -q --tb=line
→ 524 passed, 1 warning in 50.68s
```

与架构声称 **一致**（评测已复跑，非「未复跑」）。  
日志副本：`D:\RubbingMind\wt\rm-arch-backend-tmp\full_pytest_fa31279.txt`、`phase2_roi_arch_pytest.txt`。  
跑测后若 `asset-validation.json` 因 CRLF 变脏，已 `git checkout` 还原，未提交。

---

## 4. 文档 / 指标是否需补

| 项 | 建议 |
|---|---|
| 本文件 | 已写入；供 Green / 合入门禁引用 |
| `PHASE2_ROI_REQUESTS.md` | 可在合入后把 R2–R6/R8 标「arch@fa31279 已落地」；R1/R7 保持开 |
| `REPORT_DATA_SPEC` | 建议 arch/报告在合入后补一小节：`roiCompareSession`、`runLink`、`case-stele-mapping` 字段（非阻塞；评测侧可随后补契约测） |
| `MECHANISM_HEAD_NOTE` | tip 前移后更新「当前 tip」叙述；**仍禁止**字节一致宣称（R7 未重跑） |
| 指标 | **无需**、也 **不得** 因本次 ROI 接线伪造 glyph Top-k / 机制新指标 |

---

## 5. 给 Green 的合入建议

1. **允许** `agent/arch-backend@fa31279` 按既有流程 merge 进 `feature/product-grade-upgrade`（当前 feature=`9d8428e`），就 Phase2 ROI 后端契约而言 **可进门禁**。
2. 合入后开 **报告前端 R1** 工单：补 `GlyphInferenceRecord.roi` + 三 SHA；评测侧对应 G1 xfail 转绿。
3. **R7** 仍由评测科学家门禁文档约束；稳定 tip + 环境对齐前 **不大重跑** mechanism。
4. 口头「16 passed」改为以 **`test_phase2_roi_arch.py` = 10 passed** + 全量 **524 passed** 为准。

---

## 6. 评测侧状态附注（非本核范围）

- `agent/eval-sci` 已 merge feature@9d8428e → tip `a7b54e2`（merge 清洁；双方改动的 `algorithm_engine.py`/`degradation_analysis.py` 补丁相同；无共享冲突需 Green 裁决；`museum_processing` 无冲突）。
- 本插队任务完成后可恢复 ES-3/4/5 评测侧推进（derived ROI 会话契约测、mechanism tip 禁令加固、未记录/未评测导出测）；**不**抢改 arch 已落地的 R2–R8 实现。
