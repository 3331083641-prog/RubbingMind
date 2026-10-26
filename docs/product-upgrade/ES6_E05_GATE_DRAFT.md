# ES-6 · E-05 闸门草案（勿伪绿）

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-25 18:45 Asia/Shanghai
- 状态：**草案 / 测骨架** — TASK_BOARD ES-6 **仍进行中**；本 tip **不**关闭 ES-6 / E-05
- 关联：TASK_BOARD ES-6；REPORT_DATA_SPEC E-05；`experiments/notch_na_changes.py`；`experiments/e05_processing_impact.py`；`experiments/es6_e05_gate_evidence.py`

## TASK_BOARD 目标（摘录）

> ES-6 **E-05 修正**：陷波“不适用”分支不得改像素（截断问题）。验收：单测未检出峰时输出与输入逐像素相同；历史结果不覆盖，新数据用新批次目录。

真源路径（worktree 外，只读对照，**本 tip 不改**）：`D:\RubbingMind\docs\product-upgrade\TASK_BOARD.md` — ES-6 状态列须仍为「进行中」。任何「已完成 / 关闭 / ✅」写回真源均属伪绿，禁止。

## 闸门准则（草案）

| # | 准则 | 本期状态 |
|---|---|---|
| G1 | HEAD `algorithm_engine`：notch 未检出峰 → `passthrough=true` 且输出与输入 **uint8 逐像素相等**（`np.array_equal`；`maxAbsDiff==0`；`changedPixelCount==0`） | 已有单测 `test_notch_not_applicable_returns_input_unchanged` + 本 tip 边界骨架（**不等于**关 ES-6） |
| G2 | 历史批次不重跑、不覆盖 `results.json`；E-05 只靠 DER `processed_not_applicable_label` + `appliedStatusDetail` | 仍开（报告/前端文案与 DER 伴生） |
| G3 | 新数据必须新批次目录；禁止把历史 notch NA 截断行改写成“已处理提升” | 仍开（流程约束） |
| G4 | 评测侧 **不**改 `museum_processing.py`（架构后端真源）；单次处理影响以 `e05_processing_impact` 只读证据为准 | 维持 |
| G5 | 关闭 ES-6 需：G1–G4 证据齐 + Green/红队确认；禁止本 tip 伪绿勾完 | **未关** |

## G1 像素相等边界（验收细化）

**算通过（仅频域阶段 / HEAD）**

1. `filter_type='notch'` 且未检出共轭峰对：`details.notchApplied is False`、`details.passthrough is True`。
2. 返回值是输入的 **副本**（`out is not gray`），且 `np.array_equal(out, gray)`。
3. `int(np.count_nonzero(out.astype(np.int16) - gray.astype(np.int16))) == 0`。

**不算 G1 通过 / 反例**

| 反例 | 为何不算过闸 |
|---|---|
| 旧引擎全 1 掩码 FFT 往返 + `astype(uint8)`（差值多为 −1） | 这是 E-05 历史截断病症本身；HEAD 不得再走此路径 |
| `process_rubbing(notch)` 的 `restored` 与输入不同 | 频域 NA 后仍会跑空域增强；G1 只约束频域 `apply_frequency_domain_filter` 身份返回，**不**要求整管线 restored==input |
| 仅有「引擎单测绿」无 DER/批次/Green 确认 | G5：缺证据不得标「ES-6 关闭」 |
| 把 BV2/BVT 历史 `processed_not_applicable_label` 行改写成 passthrough 并覆盖 `results.json` | 违反 G2/G3 |

## 缺证据时不得标通过

关闭 ES-6 所需证据键（骨架；缺任一 → 判定 **仍开 / blocked_missing_evidence**，**永不**由本模块自动标 `closed`）：

1. `g1_pixel_equal_head` — HEAD 无峰路径逐像素相等证据（单测或只读复现）
2. `g2_history_untouched` — 历史 `results.json` 未覆盖声明
3. `g3_new_batch_policy` — 新数据新批次目录约束声明
4. `g4_no_museum_processing_edit` — 本分支未改 `museum_processing.py`
5. `green_red_ack` — Green/红队关单确认

实现：`experiments/es6_e05_gate_evidence.py` → `gate_verdict(evidence)` 只返回 `open` 或 `blocked_missing_evidence`；**不提供** `closed` 返回值（防伪绿）。

## 明确非目标（本 tip）

- 不重跑历史批次；不改馆藏原始数据；不跑 mechanism 大重算（R7 仍开）。
- 不把引擎单测绿当成 TASK_BOARD ES-6 已完成；不改 TASK_BOARD 真源状态列。
- 不 push；不合 main；A24 保持 xfail。

## 测骨架

- `tests/test_es3_es6_gate_skeletons.py`：草案存在；G1 边界（副本 + 逐像素相等）；旧截断路径为反例；缺证据不得标通过；台账/草案仍为进行中/未关（非关闭）。
- 既有：`tests/test_notch_na_changes.py`、`tests/test_process_regression_evalsci.py`（E-05 回归，不升级为关单）。
