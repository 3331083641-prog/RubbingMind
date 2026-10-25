# 合并说明（agent/arch-backend）：algorithmOutputMode 分层

- **运行级** `outputMode` ∈ {processed, passthrough, undetermined}：写在 `processing.json` 顶层，报告页“是否改动”只读此字段（本分支 `museum_processing.output_mode`）。
- **算法诊断层** 正式命名为 **`algorithmOutputMode`** ∈ {processed, identity_no_evidence, gate_fallback_original}（原 AdaptiveRubbingRestorer.restore / V22 早退里的同名 `outputMode`）。
- 两层同名不同义；本分支不改 eval-sci 大面积文件。合并前请 eval-sci 侧完成改名；本分支 ADR R2-12 与审查文档一律使用 `algorithmOutputMode`。
- 详见 `docs/product-upgrade/ADR_R2_SUPPLEMENT.md` R2-12、`REVIEW_EVALSCI_SHARED_FILES_arch-backend.md`。

## 前端契约（arch tip，相对 feature@ed9f1a0）

- pps/web/src/types/stele.ts：新增 AlgorithmOutputMode / AdaptiveDiagnostics；ProcessingResult.adaptiveDiagnostics 改为该类型（不再是 Record<string, unknown>）。
- pps/web/src/services/api.ts：再导出上述类型；ProcessingRunR1 经 AdaptiveRunFields 携带 daptiveDiagnostics / requencyDetails；run-level outputMode 注释标明勿与算法层混淆。
- **未做 UI**；报告侧 
eportData.ts RunExtras 可改为消费 AdaptiveDiagnostics（仍属 report）。
- 取值仍由 degradation_analysis → museum_processing.adaptiveDiagnostics 写入，本 tip 不改后端内核。
