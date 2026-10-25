# 合并说明（agent/arch-backend）：algorithmOutputMode 分层

- **运行级** `outputMode` ∈ {processed, passthrough, undetermined}：写在 `processing.json` 顶层，报告页“是否改动”只读此字段（本分支 `museum_processing.output_mode`）。
- **算法诊断层** 正式命名为 **`algorithmOutputMode`** ∈ {processed, identity_no_evidence, gate_fallback_original}（原 AdaptiveRubbingRestorer.restore / V22 早退里的同名 `outputMode`）。
- 两层同名不同义；本分支不改 eval-sci 大面积文件。合并前请 eval-sci 侧完成改名；本分支 ADR R2-12 与审查文档一律使用 `algorithmOutputMode`。
- 详见 `docs/product-upgrade/ADR_R2_SUPPLEMENT.md` R2-12、`REVIEW_EVALSCI_SHARED_FILES_arch-backend.md`。
