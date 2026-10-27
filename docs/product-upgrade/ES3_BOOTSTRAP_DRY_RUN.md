# ES-3 bootstrap 只读 dry-run 核对方案

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-25 18:05 Asia/Shanghai
- 状态：**方案 + 测骨架**（进行中；**未**重算落盘；**未**关 ES-3 数据层）
- 关联：TASK_BOARD ES-3；`experiments/ci_by_artifact.py`；`experiments/ci_bootstrap_dry_run.py`

## 目标

在不改写 `derived/ci_by_artifact.*`、不重跑大批量 bootstrap 落盘的前提下，核对既有派生与口径是否仍自洽，为日后授权重算准备可重复的只读步骤。

## 硬禁令

1. **不写** `derived/`（无 json/csv 覆盖）。
2. **不**把 dry-run 结果当成“已重算 CI”对外宣称。
3. 无配对参考不报 PSNR/SSIM 增益；`spans_zero` / negative / 不可靠 CI 不得写成正提升。
4. 不改 `museum_processing.py`、馆藏与实验原始数据；不 push；不合 main。

## 本期只读核对（已落地骨架）

入口：`python -m experiments.ci_bootstrap_dry_run`（默认两批；只打印报告）。

对每个批次读取既有 `derived/ci_by_artifact.json` 与 `lift_claim_summary.json`，检查：

| 项 | 期望 |
|---|---|
| bootstrap | 1000 |
| seed | 20261019 |
| artifactN | 14 |
| minReliableArtifacts | 3 |
| groups 长度 | 324 |
| sourceResultsSha256 | 等于当前 `results.json` 字节 SHA-256 |
| appliedStatusSha256 | 等于当前 `derived/applied_status.json` 字节 SHA-256 |
| claimCounts（PSNR 门禁） | 与 `summarize_lift_claims` / `lift_claim_summary.json` 一致 |
| wroteDerived | 必须为 false |

冻结对照（来自既有 derived，非本轮重算）：

- v2 claimCounts：positive_lift_ci_excludes_zero=35；no_positive_lift_claim=197；未评测=92
- v2-text claimCounts：positive_lift_ci_excludes_zero=35；no_positive_lift_claim=191；未评测=98

## 下一步（未做；需 Green/红队授权后另 tip）

1. 在内存中调用 `ci_by_artifact.compute` 对单组或全量重放 bootstrap，**只比**端点与冻结 JSON（atol 待定），仍不写盘。
2. 若 SHA 失配或端点漂移：记开项，**禁止**静默覆盖 derived。
3. 全量重算落盘仅在授权 tip 执行，并更新 MECHANISM/ES 台账。

## 与 R7 / A24

- R7 机制未重跑仍开；本方案不触及 `mechanism_cases.py`。
- A24 保持 xfail；Top-k/拒识无真值保持未评测。

## 本期实测开项（只记账，不改写 derived）

- 两批 `ci_by_artifact.json` 内嵌 `appliedStatusSha256` **与当前** `derived/applied_status.json` **不一致**（`sourceResultsSha256` 仍匹配）。
- dry-run 将此记为 `openFindings`；**禁止**为对齐 SHA 静默重写 `ci_by_artifact.*`。
- ES-3 数据层因此 **仍开**；全量 bootstrap 重算落盘需另授权 tip。
