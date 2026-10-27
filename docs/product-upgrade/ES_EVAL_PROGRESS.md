# ES_EVAL_PROGRESS — 评测侧 ES-3/4/5 推进台账

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-25 17:10 Asia/Shanghai
- 分支 tip：agent/eval-sci（本 tip parent=bd7303e；feature 已 FF 合入 bd7303e）；R7 lag 见 MECHANISM_HEAD_NOTE §17；A24/R7 仍开勿假关
- 对齐基线：feature/product-grade-upgrade@bd7303e828c8e18988872712765b5c1dcfff6711（窄冒烟绿后 FF；pytest 747 passed / 1 xfailed）
- TASK_BOARD 真源：D:\RubbingMind\docs\product-upgrade\TASK_BOARD.md（worktree 外）；本文件为 worktree 内进度镜像，供 Green 监工。

## 状态（本提交）

| ID | TASK_BOARD 目标 | 本提交交付 | 状态 |
|---|---|---|---|
| ES-3 | 按文物聚类 bootstrap CI；CI 下界 >0 才能写“提升” | 既有 ci_by_artifact + may_claim_positive_lift / lift_claim_label / summarize_lift_claims + lift_claim_summary.json；**本轮**续记对齐戳与 bootstrap CI 口径（见下节）；**不重算** bootstrap | **进行中·可再门禁**（数据未重算） |
| ES-4 | 机制层代表案例图注「未记录」勿伪绿 | enrich_mechanism_captions.py 已挂；captionProvenance.pngBytesUntouched=true；**R7 未重跑**；本轮再核图注口径 | **进行中·图注 provenance 已挂** |
| ES-5 | 负提升原因改为测量量推导 | NLC + negative_lift_display.json（measured 主列 / ruleInferred 次列）；本轮再核负提升口径；**不伪绿** | **进行中·口径伴生已挂** |

## ES-3 bootstrap CI 口径（只读既有 derived；本轮不重算）

对 2026-10-17-v2 / 2026-10-17-v2-text 的 derived/ci_by_artifact.json 实读：

| 项 | 值 |
|---|---|
| bootstrap | 1000 |
| seed | 20261019 |
| artifactN | 14 |
| minReliableArtifacts | 3 |
| groups/批 | 324 |
| 写「提升」门槛 | psnrGainCI95Low > 0 ∧ ciReliable ∧ artifactN >= minReliable ∧ liftClaimLabel=positive_lift_ci_excludes_zero |
| v2 claimCounts | positive_lift_ci_excludes_zero=35；no_positive_lift_claim=197；未评测=92 |
| v2-text claimCounts | positive_lift_ci_excludes_zero=35；no_positive_lift_claim=191；未评测=98 |

**禁令**：spans_zero / negative / 不可靠 CI / artifactN < minReliable **不得**写成正提升；无配对参考不报 PSNR/SSIM 增益结论。

## ES-4 / ES-5 口径再核

- **ES-4**：images[] 须含 batch/caseId/derivedAt/headCommit/sourcePath/captionNote；缺图用「未记录」；captionProvenance.pngBytesUntouched=true 表示只改 JSON 图注、未改 PNG 字节；机制 head 仍为 7623a52，报告不得声称与 tip 字节一致。
- **ES-5**：展示以 primaryMeasuredCauses / measuredEvidence 为主列；ruleInferredCause 仅次列启发式；negative_lift_display.json 保持 slim（不含 measuredEvidence 本体）。

## 导出标签契约（A24；勿假关）

- 产品/schema **仍无** label=candidate|human_accepted_glyph 导出字段（test_a24_schema_still_absent_keep_xfail_evidence PASSED）。
- test_a24_export_label_recognized_forbidden_until_schema_exists **保持 xfail**；禁止伪绿 Top-1/Top-3/拒识率；无独立真值时上述指标保持「未评测」。

## R7 / A24 开项（勿谎关）

| ID | 状态 | 证据 |
|---|---|---|
| **R7 / G7** | 开 | 本 tip（parent=bd7303e）相对 mechanism head 7623a52 超前 **187** commits（见 MECHANISM_HEAD_NOTE §17）；只记账未假关；未跑 mechanism_cases.py |
| **A24** | xfail 保持（禁伪 Top-k） | test_a24_export_label_recognized_forbidden_until_schema_exists；schema 缺口未落地；另有 test_a24_schema_still_absent_keep_xfail_evidence |

## 明确未做

- mechanism 大重跑 / 重算（R7）
- 改 museum_processing.py
- 伪绿 Top-k / CI / 负提升指标
- push / 合 main / 改 TASK_BOARD 真源文件（worktree 外）
- 把 A24 改成正式 assert
- 基于已作废 tip（8178f46 / 109eec1 / c6de56e）

## 对齐 feature@bd7303e（2026-10-25 17:10 Asia/Shanghai）

- 对齐后 HEAD/feature/agent/eval-sci 均为 bd7303e（ALIGNED_EQUAL）；本 tip 叠文档续开项（parent=bd7303e）
- pytest：python -m pytest tests/ -q --tb=no → **747 passed / 1 xfailed / 0 failed**；XFAIL = A24 export label
- ES-3/4/5 契约测试仍绿；bootstrap **未**重算；R7/A24 **勿谎关**
- slice13 随 feature 带入（evidence + p1-rf-open-inventory；RF-8 仍开，评测侧不关）


## 对齐 feature@46c7ded 后 ES-3/4/5 实质续做（2026-10-25 17:40 Asia/Shanghai）

- 对齐基线：feature/product-grade-upgrade@46c7ded94c7244a8fd410501a672f9a7c28cc963（窄冒烟绿；本 tip parent=46c7ded）
- 本 tip 相对 mechanism head `7623a52` 超前：**188** commits（`git rev-list --count 7623a52..HEAD` = tip HEAD 实测；与文档一致）
- **非 stamp**：契约/测试实质改动，非纯 lag 续记

### 本轮落地

| ID | 本轮 | 仍开 |
|---|---|---|
| ES-3 | `has_paired_reference`；无配对参考不得报 PSNR/SSIM 正提升；`lift_claim_label` 先查配对；`annotate_ci_lift_claims` 记 `liftClaimMetric=psnr`；冻结 claimCounts（v2: 35/197/92；v2-text: 35/191/98）与 bootstrap=1000/seed=20261019/artifactN=14/groups=324；summary 必须等于 PSNR 计数且 **≠** SSIM 计数（禁 SSIM 顶替提升口径） | bootstrap **未**重算；数据层仍进行中 |
| ES-4 | 全量 case（非抽样）图注字段 + PNG 存在性断言；`captionProvenance.pngBytesUntouched=true` 再核 | R7 机制未重跑；head 仍 7623a52 |
| ES-5 | display 行与 NLC **1:1**（caseId/method/split/degradation/psnrDelta/primaryMeasuredCauses）；rule 仅次列；slim 无 measuredEvidence 本体 | 口径伴生已挂；不伪关 |
| A24 | 仍 xfail + schema 缺口证据测试 | **勿假关**；禁伪绿 Top-k/拒识 |
| R7 | 只记账 lag=188；未重跑 `mechanism_cases.py` | **仍开** |

### 禁令（维持）

- 无配对参考不报 PSNR/SSIM 增益结论；spans_zero/negative/不可靠 CI 不得写成正提升
- 不改 museum_processing / 馆藏与实验原始数据；不 push；不合 main；不作废 tip 续写

## rebase 到 feature@eba2faf 续开（2026-10-25 18:55 Asia/Shanghai）

- 对齐分支：feature/product-grade-upgrade@eba2faf505dfa4f79f0fae523d00cc5dadbc6823（金石；本 tip parent=eba2faf）
- rebase --onto eba2faf d376dbc 后收束为 **单 tip**；**作废** 6f42ab1ab2922e9b8344a72d0a138900d8e05130 / 4b17bc5556e0eceff6f603465bbf37ba77934c34 / 46eb4d2cf172573b0f788b31dfa9a7d24d7f7d89 / 788a17f6ce04adc07ed747bb1a6d81eec96a7657 / eb1847f401e77692ad06149199fd3ea5df9d237c
- 本 tip 相对 mechanism head 7623a52：**194** commits（git rev-list --count 7623a52..HEAD = tip HEAD 实测；与文档一致）
- 内容：ES-3 bootstrap 只读 dry-run + ES-6 E-05 闸门草案 + G1 边界/反例/缺证据不得通过强化；**不**伪绿关 ES-6；A24/R7 仍开

### 本轮交付

| ID | 交付 | 仍开 |
|---|---|---|
| ES-3 | ES3_BOOTSTRAP_DRY_RUN.md + ci_bootstrap_dry_run.py 只读核对；不写 derived、不重算 | SHA 飘移仍开 |
| ES-6 | ES6_E05_GATE_DRAFT.md + es6_e05_gate_evidence.py + 测骨架（G1 副本相等/旧截断反例/缺证据 blocked；TASK_BOARD 只读仍「进行中」） | **仍进行中 / 未关** |
| A24 | xfail 保持 | **勿假关** |
| R7 | lag=**194** 只记账；未重跑 mechanism | **仍开** |

### 禁令（维持）

- 不伪绿关 ES-6/E-05；不改 TASK_BOARD 真源；不碰 museum_processing / 馆藏与实验原始数据；未 push；不合 main；不对作废 tip 强推
