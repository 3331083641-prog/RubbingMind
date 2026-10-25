# REPRESENTATIVE_CASES — 机制层代表样本（E-18）

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-19（Asia/Shanghai）
- 分支 / 代码：`agent/eval-sci`，机制图与 head 重算基于 commit `7623a52a3299b7c948031dfa1f79f04b8eb66d9e`；对照基线 `f0c5886a9d4c8b47d64640e1f7eaeac44be3c388`；**相对当前 tip 已落后，见 §7 与 MECHANISM_HEAD_NOTE.md**
- 生成脚本：`experiments/mechanism_cases.py`（只读历史结果，只写 `derived/mechanism/`）
- 运行环境：Python 3.12.4，numpy 2.4.4，OpenCV 5.0.0，scipy 1.18.0，scikit-image 0.26.0。与两批结果记录的 Python、numpy、OpenCV、scikit-image 版本一致
- 前端用途：报告第 4 层“消融与机制”和第 5 层“失败案例与不确定性”。字段契约见 `REPORT_DATA_SPEC.md` §5、§6

## 1. 为什么选这些样本（可复现规则，不按观感挑选）

对象是 `2026-10-17-v2` 和 `2026-10-17-v2-text` 两批，每批分 development 和 test 两个划分。只在 `adaptive_joint` 的已存行里挑选，每个划分 5 个类别，共 20 个样本。

| 类别 | 候选条件（用已存数据判断） | 排序键 | 取哪一个 |
|---|---|---|---|
| 提升 `improvement` | `derived/applied_status.json` 中 isPassthrough=false，且已存 ΔPSNR > 0 | (ΔPSNR, caseId) | 中位位次 `(n−1)//2` |
| 负提升 `negative` | isPassthrough=false，且 ΔPSNR < 0 | (ΔPSNR, caseId) | 中位位次 |
| 原图返回 `passthrough` | isPassthrough=true，且已存决策链中没有 `fallback_identity` | caseId | 中位位次 |
| 门控拒绝 `gate_reject` | 已存决策链中含有 `fallback_identity` | caseId | 中位位次 |
| 陷波执行 `notch` | 决策链含有 `notch`，且没有 `fallback_identity` | (ΔPSNR, caseId) | 中位位次 |

- ΔPSNR 定义为同一 caseId 下“输出 PSNR − degraded 行 PSNR”。
- 按上表顺序依次挑选。如果中位位次上的样本已被前一个类别选中，就改取最近的未选位次，先向上找，再向下找。
- 规则写在 `experiments/mechanism_cases.py` 的 docstring 和 `index.json` 的 `selectionRule` 字段里。
- 用中位数而不用极值，是为了不挑最好看的或最差的样本。每个样本的位次和候选数都记在 `selection.rank` 和 `selection.candidateN` 中（rank 从 0 开始，下表显示为 rank+1）。
- 本次 20 个样本没有触发重复回退，表中的位次都是中位位次。

### 1.1 与前端临时规则的关系（2026-10-19 补充）

前端目前用的临时规则是：**同一批次、划分、方法、退化类型下，从实际处理的记录里取 ΔPSNR 中位数和最小值各一条，再取一条原图返回。** 本文件的正式规则与它**不兼容**，二者是两套选法，用途不同，前端可以并存，但不能混称：

| 维度 | 正式规则（本文件，机制图用） | 前端临时规则 |
|---|---|---|
| 分组粒度 | 批次 × 划分（各退化合在一起） | 批次 × 划分 × 方法 × 退化 |
| 方法 | 只看 `adaptive_joint` | 8 个方法（degraded 基线除外） |
| 每组取几条 | 5 类各 1 条：提升 / 负提升 / 原图返回 / 门控拒绝 / 陷波执行 | 3 条：实际处理的中位数、实际处理的最小值、原图返回 1 条 |
| “负提升”怎么取 | 负提升行的中位位次（避开极端值） | 实际处理行的 ΔPSNR 最小值（就是最差的一条） |
| 原图返回 | 区分“原图返回”（无 `fallback_identity`）和“门控拒绝”（有 `fallback_identity`），各取中位位次 | 不区分，取一条 |
| 每批样本数 | 10 | 最多 80 组 × 3 条 |
| 是否有机制图 | 有（PNG + JSON，见 §4） | 没有，只是选样 |

临时规则本身没有写明并列和奇偶的处理。为了能对账，我在 `experiments/representative_temp_rule.py` 里把它固定为：

- ΔPSNR = 同一 caseId 下方法行 PSNR − degraded 行 PSNR（与正式规则相同）；
- “实际处理” = DER `appliedStatus == 'processed'`。notch 那些“标为不适用、只被 E-05 截断改了 1 级”的行（`appliedStatusDetail = not-applicable-but-modified-rounding`）不算实际处理；
- 按 (ΔPSNR, caseId) 排序，中位数取下中位 `(n−1)//2`，最小值取第 0 位；
- 原图返回取 caseId 排序后的第一条；
- 某一类没有行时输出 null。

输出文件：`experiments/results/<批次>/derived/representative_temp_rule.json`（两批各 80 组），里面还有 `mechanismCasesOverlap`，列出本文件 20 个样本是否也被临时规则选中（只比较 `adaptive_joint`）。

实测重合（2026-10-19 运行）：

- `2026-10-17-v2`：2 / 10。`ming_01_xianfu_salt_pepper_0`（dev，提升）和 `han_02_yiying_salt_pepper_0`（test，提升）恰好也是临时规则在 adaptive_joint × salt_pepper 组的中位数。
- `2026-10-17-v2-text`：0 / 10。
- 另外，`wei_02_wugaoli_periodic_1` 是本文件 v2 test 的“陷波执行”样本（adaptive_joint），也是临时规则在固定 notch 方法 × periodic 组的中位数。caseId 相同，但方法不同，不算重合。

前端使用要求：

- 机制图只对本文件的 20 个样本存在。临时规则选出的其他样本没有机制图，按 SPEC §5 显示“该样本未生成机制图”。
- 两套样本的标题要分开写：本文件的叫“机制代表样本（中位位次规则）”，临时规则的叫“分组代表记录（中位数 / 最小值 / 原图返回）”。
- 临时规则的“最小值”就是最差的一条，展示时必须写“该组 ΔPSNR 最小的一条”，不能叫“典型负提升”。
- 如果以后要把正式规则改成与临时规则兼容，可以在 `mechanism_cases.py` 里按临时规则选样再重算机制图。本轮没有这样做。

## 2. 重算用的代码版本

| 标签 | 代码 | 用途 |
|---|---|---|
| `historical` | `experiments/results/<批次>/source_snapshot/degradation_analysis.py`（SHA-256 `14f172c0…`，与 results.json 记录的 `codeSha256` 一致；版本串 `adaptive-rubbing-v2.0`） | 证明已存输出可复现 |
| `base` | `git f0c5886:degradation_analysis.py`（v2.1，本分支改动之前） | 衡量 v2.1 与已存 v2.0 输出的差别 |
| `head` | 工作树 `degradation_analysis.py` @ `7623a52`（含 f21ceaa 的状态字段和 E-05 修复） | 生成机制图；判断本分支改动是否改变了像素 |
| notch 基线 `historicalEngine` / `headEngine` | 批次快照 `algorithm_engine.py` / 工作树 `algorithm_engine.py`（E-05 修复） | 衡量 E-05 修复对固定陷波基线的影响 |

结论（20/20 个样本）：

1. **historical 重算与已存输出逐像素一致，20/20**。重算的决策链也与已存 `diagnostics.decisions` 一致，20/20。
2. **base（v2.1）与已存（v2.0）输出：8/20 一致，12/20 不一致**，差异像素数从 422 到 60535 不等，见下表。原因是 v2.1 把 `nlm` 换成了 `thin_stroke_nlm`，并加了 `stop_after_notch` 和 `preserve_missing`。还有一例门控结论也变了：`2026-10-17-v2/song_02_wenxuan_gaussian_0` 在 v2.0 被门控拒绝、原样返回，在 v2.1 被接受。
3. **head 与 base 逐像素一致，20/20**。说明 f21ceaa（只加了状态字段）和本次 E-05 修复都没有改变 adaptive 输出，因为 E-05 修复只在 `algorithm_engine.apply_frequency_domain_filter` 的 notch 分支里，adaptive 路径不调用它。
4. **固定 notch 基线**：已存为 `not_applicable` 的 11 个样本，旧引擎都改动了像素（8 到 17127 px）；E-05 修复后都原样返回输入，因此与已存 PNG 不再一致。已存为 `applied` 的 9 个样本，修复前后都与已存一致。
5. **机制图描述的是 head（v2.1）的行为，不是已存 v2.0 输出的行为**。两者不一致时，目录里另有 `diff_head_vs_stored.png`。`mechanism.measuresStoredOutput` 给出了按已存输出计算的同一组测量量。前端必须同时显示“已存指标属于 v2.0，机制图属于 v2.1”。

## 3. 样本清单

### 2026-10-17-v2

| 划分 | 类别 | caseId（目录名） | 退化 / 强度 | 选取位次 | 已存 ΔPSNR (dB) | 已存决策链（v2.0） | head 决策链（v2.1） | 历史代码重算 = 已存 | f0c5886 = 已存（不同像素数） | head = f0c5886 | notch 基线：E-05 修复后 = 已存 | 图像数 / 字节 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| development | 提升 | `ming_01_xianfu_salt_pepper_0` | salt_pepper / 0.65 | 16/32（按 gain） | 5.245 | skip_notch → isolated_impulse_median → nlm | skip_notch → isolated_impulse_median → thin_stroke_nlm | 是 | 否（31656 px，最大差 61） | 是 | 否（已存为 not_applicable，旧代码改了 10393 px；修复后原样返回=是） | 13 / 480076 |
| development | 负提升 | `qing_01_qianlong_heart_sutra_occlusion_1` | occlusion / 1.3 | 7/14（按 gain） | -3.885 | skip_notch → nlm | skip_notch → thin_stroke_nlm | 是 | 否（40694 px，最大差 79） | 是 | 否（已存为 not_applicable，旧代码改了 4154 px；修复后原样返回=是） | 13 / 542984 |
| development | 原图返回（门控通过） | `song_01_yuanyou_blur_1` | blur / 1.3 | 10/20（按 caseId） | 0.000 | skip_notch → identity | skip_notch → identity | 是 | 是 | 是 | 否（已存为 not_applicable，旧代码改了 564 px；修复后原样返回=是） | 11 / 327363 |
| development | 门控拒绝 | `ming_01_xianfu_periodic_1` | periodic / 1.3 | 2/4（按 caseId） | 0.000 | notch → isolated_impulse_median → nlm → fallback_identity | notch → isolated_impulse_median → thin_stroke_nlm → fallback_identity | 是 | 是 | 是 | 是 | 12 / 349171 |
| development | 陷波执行 | `wei_01_zhangmenglong_periodic_1` | periodic / 1.3 | 4/7（按 gain） | 9.271 | notch → isolated_impulse_median → nlm | notch → isolated_impulse_median → thin_stroke_nlm | 是 | 否（41912 px，最大差 102） | 是 | 是 | 14 / 657490 |
| test | 提升 | `han_02_yiying_salt_pepper_0` | salt_pepper / 0.65 | 11/21（按 gain） | 1.831 | skip_notch → isolated_impulse_median → nlm | skip_notch → isolated_impulse_median → thin_stroke_nlm | 是 | 否（32916 px，最大差 132） | 是 | 否（已存为 not_applicable，旧代码改了 7921 px；修复后原样返回=是） | 13 / 533896 |
| test | 负提升 | `song_02_wenxuan_periodic_0` | periodic / 0.65 | 9/18（按 gain） | -2.612 | notch → nlm | notch → thin_stroke_nlm | 是 | 否（60535 px，最大差 98） | 是 | 是 | 14 / 731624 |
| test | 原图返回（门控通过） | `song_02_wenxuan_blur_0` | blur / 0.65 | 9/18（按 caseId） | 0.000 | skip_notch → identity | skip_notch → identity | 是 | 是 | 是 | 否（已存为 not_applicable，旧代码改了 8 px；修复后原样返回=是） | 11 / 356924 |
| test | 门控拒绝 | `song_02_wenxuan_gaussian_0` | gaussian / 0.65 | 7/13（按 caseId） | 0.000 | skip_notch → nlm → fallback_identity | skip_notch → thin_stroke_nlm | 是 | 否（422 px，最大差 7） | 是 | 否（已存为 not_applicable，旧代码改了 1103 px；修复后原样返回=是） | 13 / 459008 |
| test | 陷波执行 | `wei_02_wugaoli_periodic_1` | periodic / 1.3 | 4/7（按 gain） | 8.394 | notch → isolated_impulse_median → nlm | notch → isolated_impulse_median → thin_stroke_nlm | 是 | 否（38865 px，最大差 137） | 是 | 是 | 14 / 673131 |

### 2026-10-17-v2-text

| 划分 | 类别 | caseId（目录名） | 退化 / 强度 | 选取位次 | 已存 ΔPSNR (dB) | 已存决策链（v2.0） | head 决策链（v2.1） | 历史代码重算 = 已存 | f0c5886 = 已存（不同像素数） | head = f0c5886 | notch 基线：E-05 修复后 = 已存 | 图像数 / 字节 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| development | 提升 | `ming_03_wugou_salt_pepper_1` | salt_pepper / 1.3 | 16/31（按 gain） | 4.208 | skip_notch → isolated_impulse_median → nlm | skip_notch → isolated_impulse_median → thin_stroke_nlm | 是 | 否（15302 px，最大差 105） | 是 | 否（已存为 not_applicable，旧代码改了 2282 px；修复后原样返回=是） | 13 / 487397 |
| development | 负提升 | `yuan_03_shengzhu_occlusion_1` | occlusion / 1.3 | 9/17（按 gain） | -3.003 | skip_notch → nlm | skip_notch → thin_stroke_nlm → preserve_missing | 是 | 否（13384 px，最大差 76） | 是 | 否（已存为 not_applicable，旧代码改了 13215 px；修复后原样返回=是） | 13 / 441053 |
| development | 原图返回（门控通过） | `qing_03_sanxitang_preface_occlusion_1` | occlusion / 1.3 | 8/16（按 caseId） | 0.000 | skip_notch → identity | skip_notch → identity | 是 | 是 | 是 | 否（已存为 not_applicable，旧代码改了 17127 px；修复后原样返回=是） | 11 / 285680 |
| development | 门控拒绝 | `qing_03_sanxitang_preface_periodic_1` | periodic / 1.3 | 3/6（按 caseId） | 0.000 | notch → identity → fallback_identity | notch → stop_after_notch → fallback_identity | 是 | 是 | 是 | 是 | 12 / 301225 |
| development | 陷波执行 | `yuan_03_shengzhu_periodic_1` | periodic / 1.3 | 3/5（按 gain） | 13.828 | notch → nlm | notch → thin_stroke_nlm | 是 | 否（16923 px，最大差 108） | 是 | 是 | 14 / 591652 |
| test | 提升 | `qing_04_ayuwang_reliquary_salt_pepper_1` | salt_pepper / 1.3 | 16/31（按 gain） | 4.743 | skip_notch → isolated_impulse_median → nlm | skip_notch → isolated_impulse_median → thin_stroke_nlm | 是 | 否（22247 px，最大差 44） | 是 | 否（已存为 not_applicable，旧代码改了 16453 px；修复后原样返回=是） | 13 / 465071 |
| test | 负提升 | `tang_04_xuanmita_occlusion_0` | occlusion / 0.65 | 8/16（按 gain） | -1.884 | skip_notch → nlm | skip_notch → nlm | 是 | 是 | 是 | 是 | 12 / 358233 |
| test | 原图返回（门控通过） | `song_04_mengying_blur_0` | blur / 0.65 | 9/17（按 caseId） | 0.000 | skip_notch → identity | skip_notch → identity | 是 | 是 | 是 | 否（已存为 not_applicable，旧代码改了 9595 px；修复后原样返回=是） | 11 / 342989 |
| test | 门控拒绝 | `qing_04_ayuwang_reliquary_periodic_1` | periodic / 1.3 | 3/6（按 caseId） | 0.000 | notch → isolated_impulse_median → nlm → fallback_identity | notch → isolated_impulse_median → thin_stroke_nlm → fallback_identity | 是 | 是 | 是 | 是 | 12 / 361736 |
| test | 陷波执行 | `song_04_mengying_periodic_1` | periodic / 1.3 | 3/5（按 gain） | 9.783 | notch → isolated_impulse_median → nlm | notch → isolated_impulse_median → thin_stroke_nlm | 是 | 否（18550 px，最大差 103） | 是 | 是 | 14 / 596590 |
- “选取位次”是 rank+1 / 候选数。
- 体量：v2 共 128 张 PNG，5,111,667 字节；v2-text 共 125 张 PNG，4,231,626 字节；合计约 9.3 MB，加上 JSON 约 9.6 MB。

## 4. 每个样本目录的文件

路径：`experiments/results/<批次>/derived/mechanism/<caseId>/`。批次级索引是 `experiments/results/<批次>/derived/mechanism/index.json`。

| 文件 | 何时存在 | 内容 |
|---|---|---|
| `mechanism.json` | 总是 | 见 §5 |
| `spectrum_input.png` | 总是 | 输入的 log 幅度谱：`log1p(|fftshift(fft2(x − mean x))|)`，min-max 映射到 0..255，VIRIDIS 色带；红圈为 head 检出的共轭周期峰 |
| `spectrum_output.png` | 总是 | head 输出的 log 幅度谱，红圈为残留峰 |
| `notch_mask.png` | 只在 head 执行 notch 时 | 陷波掩膜，fftshift 坐标；白色为保留，黑色为抑制；宽度为 notch_width=0.8 |
| `foreground_{reference,input,output}.png` | 总是 | Otsu 二值前景（少数类，与 `analyze_degradation` 相同），255 = 前景 |
| `skeleton_{reference,input,output}.png` | 总是 | `RubbingAlgorithmEngine.extract_stroke_skeleton`（Otsu + skimage skeletonize） |
| `edges_{reference,input,output}.png` | 总是 | Canny(80,160)，与 edgeF1 指标的定义相同 |
| `diff_output_input.png` | 只在 head 输出 ≠ 输入时 | `|head 输出 − 输入|`，按 max(1, P99) 归一，INFERNO 色带；归一常数见 `mechanism.diffScaleP99` |
| `diff_head_vs_stored.png` | 只在 head 输出 ≠ 已存输出时 | `|head 输出 − 已存输出|`；归一常数见 `mechanism.headVsStoredScaleP99` |

- 原图、输入、已存输出**没有复制**，以 `storedFiles` 中的相对文件名引用同一批次目录下的原始 PNG。
- 当前 `experiment_registry.asset()` 只服务批次根目录里的文件，`derived/mechanism/` 下的 PNG 还没有 API 路由。这一项需要架构后端补，本分支没有改 main.py。

## 5. `mechanism.json` 字段

| 字段 | 类型 | 含义 |
|---|---|---|
| `batch`、`split`、`sampleId`、`caseId`、`degradation`、`strength` | string / number | 样本身份 |
| `category` | enum `improvement` / `negative` / `passthrough` / `gate_reject` / `notch` | 选取类别 |
| `selection` | `{rank, candidateN, sortKey}` | 选取位次（rank 从 0 开始） |
| `storedFiles` | `{reference, input, output, notchOutput}` | 同一批次目录下的原始文件名 |
| `inputSha256` / `inputSha256Recorded` / `inputShaMatches` | string / string / bool | 实际输入 SHA 与记录的 SHA，20/20 一致 |
| `storedOutputSha256` / `storedOutputShaMatches` | string / bool | 已存输出 SHA 校验，20/20 一致 |
| `storedMetrics` | `{psnrInput, psnrOutput, psnrGain, ssimGain, edgeF1Gain}` | 来自 results.json，属于 v2.0 |
| `storedDiagnostics` | `{algorithmVersion, operators, decisions, fidelityGate, selectedOutput}` | 已存的 v2.0 诊断。`selectedOutput` 是历史值，含 E-02 的错误标注 |
| `headCommit` | string | 生成本文件时的 HEAD |
| `parameters` | object | strength=1.0、notch_width=0.8、Canny、频谱、前景、骨架、差分图的定义 |
| `replays.{historical,base,head}` | object | `code`（来源、SHA，head 另有 `uncommittedChanges`，本次均为 false）、`operators`、`gateAccepted`、`versionString`、`vsStoredOutput{pixelEqual, changedPixelCount, maxAbsDiff, meanAbsDiff}`、`vsInput{…}`；`historical.operatorsMatchStored`；`head.vsBase` |
| `notchBaselineReplay` | object | `storedApplicability`；`historicalEngine` / `headEngine` 各有 `{code, applicability, vsStoredNotch, vsInput}` |
| `mechanism.features` | object | head 的 `noiseSigmaMAD`、`impulseFraction`、`periodicPeaks`（位置、幅值、能量占比、log 显著度）、`thinStrokeRisk`、`highFrequencyEnergyFraction` |
| `mechanism.decisions` / `fidelityGate` / `outputMode` / `changeStats` | object | head 的门控决策链和改动量 |
| `mechanism.notchApplied`、`peaksOutput` | bool / array | head 是否执行陷波；输出上的残留峰 |
| `mechanism.measures` | object | head 输出的测量量（定义见 `restoration_measures.measure_case`）：改动像素比例、平均和最大改动、输入平均误差、改动与输入误差之比、PSNR 输入/输出/差、edgeF1 输入/输出/差、细笔画 MAE 输入/输出/差、前景损失输入/输出/差、周期峰能量与峰数（输入/输出/比值）、缺失掩膜像素数、改动落在缺失区的比例、强边缘保持率、对比度比 |
| `mechanism.measuresStoredOutput` | object | 同一组测量量，按已存（v2.0）输出计算 |
| `images` | array `{file, description, shape, bytes, sha256}` | 本目录下的 PNG 清单 |

`index.json`（每批一个）包含 `selectionRule`、`headCommit`、`baseCommit`、`environment`、`recordedEnvironment`，以及 `cases` 摘要：类别、caseId、ΔPSNR、各版本是否一致、图像字节数和目录。

## 6. 前端展示约束

- 每张机制图都要标“v2.1（head 重算）”，已存指标要标“v2.0 已存”。
- 原图返回和门控拒绝两类样本，标题必须是“原图返回（未处理）”或“门控拒绝，原样返回”，不得叫“算法输出”。
- 本样本集只用于说明机制，不用于统计结论。统计结论用 `derived/ci_by_artifact.json`。
- v2-text 的 14 件文物与“同批复测 v2.1”相同（E-01），v2-text 中的机制样本不能当作独立验证。

## 7. headCommit 与分支 tip（2026-10-25）

- 机制产物生成时写入的 headCommit 仍为 7623a52a3299b7c948031dfa1f79f04b8eb66d9e。
- 当前分支 tip 已前移（写作时 65f78159a87ddee5895eb2d8d7b49fdbd1325028）。**在重跑 mechanism_cases.py 并更新 derived/mechanism/index.json 之前，报告不得宣称机制 PNG 与当前 tip 字节一致。**
- 约束全文：MECHANISM_HEAD_NOTE.md。pplied_status.json 的 sourceResultsSha256 与各批 
esults.json 仍一致，本期不重生 derived。

