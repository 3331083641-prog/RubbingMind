# REPORT_DATA_SPEC — 评测报告六层数据契约

- 版本：v3.3 定稿（2026-10-19，RM-评测科学家。**Green 定稿**：`grayCriterion = gray-bt601-pixel-equal-v1`（不要用 `working-gray-pixel-equal-v1`）；灰度字段集仍为后端五元组；算法/诊断层字段名定稿为 `algorithmOutputMode`，运行级仍为 `outputMode`。v3.2 → v3.3：落实上述定稿（废止 v3.2 中间稿的 working-gray 命名，以及「是否改名尚未确定」的措辞）。v3.1 → v3.2：Rule/Source、旧运行 effectiveParameters、museum_processing 归属后端。更早见 git 历史。）
- 机制层 headCommit 约束：MECHANISM_HEAD_NOTE.md（产物 headCommit=7623a52 落后 tip 时，报告不得宣称机制图与 tip 字节一致）
- 基线：`feature/product-grade-upgrade` @ `f0c5886`。配套实现：分支 `agent/eval-sci`（未合并），代码在 `f21ceaa`、`7623a52` 和其后的提交（`git log f0c5886..agent/eval-sci`），派生数据见同分支
- 依据：`docs/product-upgrade/AUDIT_EVALUATION.md`（E-01 … E-12）
- 适用对象：报告前端（ReportsPage / ExperimentExplorer 的继任页面）和架构后端（main.py / API）
- 本文件只定义数据与口径，不改 UI 和后端代码。凡是写“必须 / 禁止”的条目，前端验收按字面执行。

## 0. 总则

### 0.1 数据源（只读）

| 代号 | 路径 | 内容 | 是否有图像 |
|---|---|---|---|
| B15 | `experiments/results/2026-10-15/results.json` / `results.csv` / `summary.csv` | 第一批受控退化，10 行/方法 | 有。只有 `output` 字段；输入取同样本同退化的 `method='degraded'` 输出 `{sample}_{deg}_degraded.png` |
| BV2 | `experiments/results/2026-10-17-v2/…` | v2 受控退化，1260 行，带 development/test 划分 | 有。`reference/input/output` 和对应 `*Sha256` |
| BVT | `experiments/results/2026-10-17-v2-text/…` | v2-text，1260 行，划分同上 | 有 |
| BRT | `experiments/results/2026-10-18-v21-heldout/…` | v2.0/v2.1 同批复测，490 行 | **没有图像**，只有数值和 `diagnosticsOperators` |
| DER | `experiments/results/<批次>/derived/applied_status.{csv,json}` | 派生标注（由 `experiments/derive_applied_status.py` 生成；E-05 细分标签由 `experiments/notch_na_changes.py` 写入同一文件） | 不适用 |
| CI | `experiments/results/{2026-10-17-v2,2026-10-17-v2-text}/derived/ci_by_artifact.{csv,json}` | 按文物聚类 bootstrap CI（`experiments/ci_by_artifact.py`） | 不适用 |
| NLC | `experiments/results/{2026-10-15,2026-10-17-v2,2026-10-17-v2-text}/derived/negative_lift_causes.{csv,json}` | 负提升的测量原因（E-04，`experiments/derive_negative_lift_causes.py`） | 不适用 |
| MEC | `experiments/results/{2026-10-17-v2,2026-10-17-v2-text}/derived/mechanism/` | 机制层代表样本（E-18，`experiments/mechanism_cases.py`；说明见 `REPRESENTATIVE_CASES.md；headCommit 与 tip 关系见 MECHANISM_HEAD_NOTE.md`） | 派生 PNG |
| DGC | `experiments/results/{2026-10-15,2026-10-17-v2,2026-10-17-v2-text}/derived/degradation_check.json` | 退化生成器核对（`experiments/verify_degradation_params.py`） | 不适用 |
| RUN | `static/results/<stele>/<run>/processing.json` + PNG | 馆藏运行记录（本地，gitignore） | 有 |
| REG | `GET /api/experiments`（`experiment_registry.batches()`） | 批次清单、限制说明 | — |

历史 `results.json/csv/summary.csv` 和 PNG 一律不改。所有更正都通过 DER 或注册表的显示层实现。

### 0.2 分级规则（每个结论、每张卡片、每个数字都必须带一个等级）

| 等级 | 判定条件（全部满足） | UI 文案 |
|---|---|---|
| **已验证** | ① 来源是真实结果文件或 DER；② 已复算一致（AUDIT 已复算：summary 0 不一致，图像 SHA 0 不一致）；③ 样本没有参与过该方法的调参；④ 有按文物聚类的 95% CI，且 CI 不跨 0（只用于“提升”类结论） | 已验证 |
| **有限支持** | 有真实数据且复算一致，但满足任一：n_文物 < 10；没有 CI 或 CI 跨 0；样本参与过调参或误差分析（BRT 全部属此类）；只在受控退化上成立（参考图是可读 JPG 裁切，不是碑石真值） | 有限支持（附原因） |
| **未评测** | 数据里没有该方法、该退化或该指标；或 `isPassthrough` 无法判定而结论依赖它 | 未评测 |
| **待人工复核** | 需要人看图才能判断（释读、笔画是否被误补、V22 内部常数块 E-09、两个 glyph schema 不一致 E-12）；或自动判据与专家意见冲突 | 待人工复核 |

规则：

- 等级只能降，不能升。组合结论取组成部分中最低的等级。
- 受控退化结论最高只能是“已验证（受控退化）”。禁止写成“对真实碑拓有效”。
- 禁止使用的词：“留出”“held-out”“泛化到新文物”（BRT 不适用）；“修复成功”“恢复真迹”。

### 0.3 统一派生量

| 名称 | 公式 / 定义 | 实现 |
|---|---|---|
| 逐行改动量 | `D = |int16(out) − int16(in)|`（灰度；3 通道时任一通道 ≠0 即算该像素改动）。`changedPixelCount = Σ[D>0]`，`changedPixelRatio = changedPixelCount / (H·W)`，`maxAbsDiff = max D`，`meanAbsDiff = mean D` | `degradation_analysis.change_stats` |
| isPassthrough | `changedPixelCount == 0`（判据 `pixel-equal-v1`）。`byteIdentical`（文件 SHA 相同）是充分非必要条件，另列 | 同上；DER 两项都给 |
| 增益 | `ΔPSNR = PSNR(out, ref) − PSNR(in, ref)`，SSIM、edgeF1 同理（输出减输入，越大越好）。thinStrokeMae 越小越好，统一写成“输出减输入”，负值表示改善；CI 文件中 v2 系列没有 thinStrokeMae | CI 文件中的 `*Gain*` 字段 |
| 差分热图 | `H = |out − in|`（不是 `out − ref`），显示时 `clip(H / max(1, P99(H)), 0, 1)` 映射到单色色带。另提供带符号图 `S = out − in`，用发散色带，0 为中性色。图上必须标注 `maxAbsDiff`、`changedPixelRatio` 和 P99 归一化常数 | 前端计算，或后端以后按需生成 |
| 误差图 | `E_x = |x − ref|`，x ∈ {in, out}；`ΔE = E_in − E_out`（正值表示更接近参考） | 前端 |
| 按文物聚类 CI | 对方法 m、退化 d、划分 s 和口径（全部 / 实际处理 / 原图返回）：先算每件文物的均值 `ā_k`；再对 K 件文物做 1000 次有放回重采样，取重采样均值的第 2.5 和 97.5 百分位。**已计算**：seed=20261019，每个 CI 都用新的 `numpy.random.default_rng(20261019)`，K<3 的组标 `ciReliable=false`，空组输出 null。**前后端对账**：前端临时实现用同样的参数（按文物聚类、seed=20261019、B=1000、分位 2.5% / 97.5%）。参数一致不保证端点逐位相同：只有用同一随机流（numpy `default_rng` 的 PCG64、文物按 `sampleId` 排序、`rng.choice(ā, (1000, K), replace=True)`、`np.percentile` 线性插值）才能逐位复现。前端应直接读 CI 文件显示；如果自己重算，对账时均值必须相等，端点允许有蒙特卡洛误差（参考量级：同参数不同随机流时，端点差最大约为 CI 宽度的 10%，见 §4） | `experiments/ci_by_artifact.py` → CI 文件 |
| 配对增益 CI | 与上相同，但对象换成每件文物的 `mean(输出 − 同 caseId 的 degraded 行)`。`*GainSign` 取值为 positive（下界 > 0）、negative（上界 < 0）、spans_zero、zero（上下界都正好是 0，即原图返回）。只有 positive 才能写“提升” | 已计算，同上 |
| 负提升计数 | `ΔPSNR < 0` 的行数；同时按处理/原图返回分开计数（`negativeLiftCountProcessed`） | `compare_v21` 新运行 |
| 分离均值 | 每个指标都给三种：`MeanAll`、`MeanProcessed`（isPassthrough=false）、`MeanPassthrough`（isPassthrough=true），并带 `processedN / passthroughN / undeterminedN` | `experiments/applied_status.split_means` |

## 1. 三条强制更正

### (a) BRT 改名为“同批复测 v2.1”，UI 不得出现“留出”

- 存储 ID `heldout-v20-v21-2026-10-18` 和目录名 `2026-10-18-v21-heldout` 是历史标识，不改。只改显示层。
- 显示名用 REG 新字段 `displayName = "同批复测 v2.1（v2.0 对照，2026-10-18）"`，并给 `heldOut: false`。限制说明第一条固定为注册表的 `protocolNote`。
- 理由（E-01 证据，全部是实测）：
  1. BRT 的 14 件文物就是 BVT 的 14 件（源图 SHA 相同；在 BVT 中是 7 件 development、7 件 test）；
  2. 裁切重叠：song_03_daguan 为 1.0，tang_04_xuanmita 为 0.795；
  3. BRT 每行 `excludedFromPreviousBatch=True`（14/14），与事实不符：当时的排除表漏了 v2-text；
  4. 时间线：BVT 在 f9aebdb（2026-10-17 18:13）；v2.1 改动在 ea5a67a（2026-10-18 00:56，preserve_missing / stop_after_notch / thin_stroke_nlm，针对 BVT 的误差分析）；BRT 在 59f9784（10:52）；
  5. BVT 的 error-analysis.md 自己写了：如果继续调参，需要新的、未用过的留出集。
- 前端规则：
  - 任何标题、图例、tooltip、导出文件名都不得出现“留出 / held-out / heldout”字样（目录名原样出现在“数据来源路径”里除外，需用等宽字体标为路径）。
  - BRT 的所有结论最高为“有限支持”，原因写“样本参与过 v2.1 的误差分析”。
  - **禁止**为 BRT（同批复测 v2.0 / v2.1）给出“有效处理率”“实际处理率”“原图返回率”或任何以 `processedN`、`passthroughN` 为分子的比例。原因：该批没有图像，DER 中除 baseline 外 420/420 行都是 `undetermined`，分子不存在。BRT 的这一栏只能显示“无法判定（本批次未保存图像）”和 `undeterminedN = 70`（每个方法）。两个指示量（见 §1(b)）不得改名、换算或合并成比例，也不得写进标题或结论卡。审计 E-02 验收标准里的“21（v2.1）”是指示量 `indicatorPsnrDeltaZeroN`，不是像素判定的原图返回数，同样不得按原图返回数显示。
  - 默认选中批次禁止是 BRT（E-07：`items.at(-1)` 会默认选中它）。默认应选最新的有图像批次（BVT）。
- 代码侧：`experiments/compare_v21.py` 的排除表现在扫描 `experiments/results/*/results.json`，包括 v2-text 和更早的批次。再遇到重叠时直接 `SystemExit`，除非显式传 `--allow-seen`；此时结果标记 `heldOut:false`。

### (b) “原图返回”与“实际处理”分开计数、分开求均值

- 判据 `pixel-equal-v1`（实验层和馆藏运行共用，`degradation_analysis.change_stats`）：两张图解码后的数组形状相同，并且全部通道逐像素相等。形状不同或任一张无法解码时不判定（null），不做缩放、裁切或灰度转换。字节相同另列 `byteIdentical`。
  - 实验批次的 PNG 全部是单通道灰度（PNG color type 0：B15 82 个、BV2 1414 个、BVT 1414 个），所以 DER 里已有的判定就是按全部通道计算的，不需要重算。
  - 实测 BV2 的 65 行、BVT 的 47 行原图返回全部字节相同。
- **原图返回按方法拆分**（DER `appliedStatus ∈ {passthrough, passthrough_not_applicable}`，分母 = 该方法该划分的行数，每格 70 行；baseline 不计）：

| 批次 | 方法 | development | test | 合计 | 其中 `passthrough_not_applicable` |
|---|---|---|---|---|---|
| BV2 | adaptive_joint | 24 / 70 | 31 / 70 | 55 / 140 | 0 |
| BV2 | fast_nlm | 3 / 70 | 1 / 70 | 4 / 140 | 0 |
| BV2 | notch | 0 / 70 | 6 / 70 | 6 / 140 | 6 |
| BV2 | gaussian_lowpass、butterworth_lowpass、morphology、nlm_clahe、joint | 0 | 0 | 0 / 700 | 0 |
| BV2 | **8 个方法合计** | 27 / 560 | 38 / 560 | **65 / 1120** | 6 |
| BVT | adaptive_joint | 22 / 70 | 23 / 70 | 45 / 140 | 0 |
| BVT | fast_nlm | 2 / 70 | 0 / 70 | 2 / 140 | 0 |
| BVT | notch | 0 / 70 | 0 / 70 | 0 / 140 | 0 |
| BVT | gaussian_lowpass、butterworth_lowpass、morphology、nlm_clahe、joint | 0 | 0 | 0 / 700 | 0 |
| BVT | **8 个方法合计** | 24 / 560 | 23 / 560 | **47 / 1120** | 0 |

  - 口径：本节旧版写的“65 / 47”是 8 个方法的合计；审计 E-02 的“55 / 45”只算 adaptive_joint。两者都对，口径不同，差额 10 / 2 来自 fast_nlm 和 notch。前端显示原图返回数时必须写明方法；不写方法时只允许按方法逐行列出，禁止只给一个合计数。
  - notch 另有 BV2 98 行、BVT 95 行“标为不适用却改了像素”，**不**计入原图返回，单独计数，见下文 E-05。
  - `experiments/results/<批次>/derived/applied_status.json` 的 `summaryBySplitMethod` 就是这张表的数据源，前端按 `method` 取，不要自己加总。
- 每个方法 × 划分（× 退化）都必须同时显示：`n`、`processedN`、`passthroughN`、`undeterminedN`，以及三种均值。主数字用 `MeanProcessed`，并且必须旁注“另有 passthroughN 行原样返回，均值 x”。`MeanAll` 只放在“与历史 summary 对照”一栏。
- `appliedStatus` 枚举（DER 每行一个）：

| 值 | 含义 | 前端标签 |
|---|---|---|
| `baseline` | degraded 基线本身 | 输入基线 |
| `processed` | 改动 ≥1 像素 | 实际处理 |
| `passthrough` | 0 像素改动，且记录里标为 applicable | 原图返回（未处理） |
| `passthrough_not_applicable` | 0 像素改动，记录标 not_applicable | 原图返回（判定不适用） |
| `processed_not_applicable_label` | 记录标 not_applicable，但像素被改动了（E-05：历史代码中 notch 走 NA 分支时，astype(uint8) 截断改了像素；`7623a52` 起的新代码已改为原样返回，新运行不再出现此状态）。细分见 `appliedStatusDetail` | 标为不适用但有改动（E-05，历史数据） |
| `failed` | 运行出错 | 失败 |
| `undetermined` | 无图像或无法解码 | 无法判定 |

- E-05：历史数据中，notch 的 NA 分支平均绝对差为 0.084（BV2）/ 0.161（BVT），符号为负；`ExperimentExplorer.tsx:37` 的“以原图计入”说法对历史批次不成立。
  - **逐行核实（已计算）**：对每一行 `processed_not_applicable_label` 做五项只读检查：(1) 输出 − 输入的非零差值只有 −1；(2) 该批次的历史引擎（`source_snapshot/algorithm_engine.py`；B15 没有快照，用 `git 10a63f4:algorithm_engine.py`）按 notch d0=48 重算，与存档输出逐像素相同；(3) 历史引擎没有检出峰对；(4) 修复后的引擎原样返回输入；(5) 改动像素恰好就是 `astype(uint8)` 截断后低于输入的像素（全 1 掩码 FFT 往返的最大浮点误差 4.6e-5）。五项都成立记 `not-applicable-but-modified-rounding`，否则记 `not-applicable-but-modified-other` 并列出不成立的检查项。
  - 结果：

| 批次 | 行数 | rounding | other | 差值取值 | 每行改动像素（最少 / 最多 / 合计，每张 65536） |
|---|---|---|---|---|---|
| BV2 | 98（dev 56 / test 42） | 98 | 0 | 只有 −1 | 8 / 11516 / 573508 |
| BVT | 95（dev 49 / test 46） | 95 | 0 | 只有 −1 | 34 / 17662 / 1001122 |
| B15 | 8 | 8 | 0 | 只有 −1 | 2708 / 13187 / 73816 |

  - 结论：三个批次的这类行全部是 E-05 浮点截断（最大绝对差 = 1，方向全部为 −1），没有其他原因。
  - DER 字段：`appliedStatusDetail`（上面两个取值之一；其他行为 null）和 `naChangeEvidence`（逐项检查值和 `failedChecks`）。`appliedStatus` 本身不变；汇总增加 `notApplicableModifiedRoundingN`、`notApplicableModifiedOtherN`。
  - 前端：rounding 行显示“不适用分支的 1 级截断（E-05），非算法处理”，不计入实际处理率，也不计入原图返回；other 行（目前 0 行）显示“标为不适用但有改动，原因未定，待人工复核”。
  - **新代码已修**（`agent/eval-sci` @ `7623a52`）：`algorithm_engine.apply_frequency_domain_filter` 在 notch 没有检出峰对时直接返回输入副本，`details.passthrough=true`。
  - 历史批次不重跑，只靠 DER 的 `processed_not_applicable_label` 和 `appliedStatusDetail` 标注。前端 notch 卡片上，历史批次显示“历史批次：不适用分支仍有轻微像素改动（E-05，已在新代码修复）”。
  - 对单次处理的影响见 §11。
- BRT 没有图像，因此 `isPassthrough = null`，`undeterminedN = 70`（每个方法），不猜测。允许另列两个**指示量**，必须标“未经像素验证”：
  - `indicatorPsnrDeltaZeroN`：`psnrDeltaFromInput == 0` 的行数；
  - `indicatorCopyOnlyOperatorsN`：`diagnosticsOperators ⊆ {skip_notch, identity, preserve_missing, fallback_identity}` 的行数（按代码阅读，这些算子只复制输入）。
  - 实测：adaptive_v20 / v21 都是 21 / 19。两者不一致，正好说明不能当判据。

### (c) 跨批次比较警告规则

只要比较的两个数字来自不同批次，就必须逐条检查下面四项，命中任一条就在比较处显示黄色警告条，并把该比较降为“有限支持”或更低：

| # | 差异 | 检查方式 | 警告文案 |
|---|---|---|---|
| C1 | 样本集 | 比较两批的 `sampleId` 集合和源图 SHA；记 Jaccard。B15/BV2 与 BVT/BRT 的文物集合不同，BVT 与 BRT 相同 | “两批样本集不同（重合 x/y 件），差异可能来自样本而非算法。” 若完全相同但其中一批参与过调参：“同一批文物复测，不是独立验证。” |
| C2 | 退化生成器 | 比较 `config` 中退化类型、强度表、种子、生成代码提交。**B15 与 v2 系列已逐项核对，结论为“不同”**（§10）：强度、参数、种子公式、裁切区域、joint 方法定义都不同 | “退化生成方式不同，PSNR 绝对值不可直接比较，只比较同批内相对增益。” B15 与 v2 互比时必须显示 |
| C3 | 方法版本 | 比较 `VERSION`、`diagnostics.version` 与提交（v2.0 / v2.1） | “方法版本不同：A 为 v2.0，B 为 v2.1。” |
| C4 | 汇总口径 | 是否计入 not_applicable 行（`run_ablation.py:122` 排除，`run_v2.py:72` 包含）、是否计入原图返回行、是否按文物聚类。E-06 实例：B15 notch summary 为 n=2、41.364 dB，全行均值为 n=10、27.813 dB | “汇总口径不同（A 排除不适用行，B 全部计入）。已按统一口径重算：…” 前端必须用 DER 的统一口径重算后再显示，不能直接拿两批的 summary.csv 互比 |

额外规则：

- 禁止跨批次画在同一根数值轴上而不标批次。
- 禁止用 B15 的 summary 均值做“改进幅度”的分母。

## 2. 第 1 层：研究总览

| 项目 | 来源字段 | 派生 | 缺失时 |
|---|---|---|---|
| 批次列表 | REG：`id`、`displayName`、`heldOut`、`directory`、`createdAt/commit`（若有）、`metricsOnly`、`imageComparisonAvailable`、`limitations`、`appliedStatusAvailable` | 显示时一律用 `displayName` | 字段缺失就显示 ID，并标“未命名” |
| 规模 | 各批 `rows` 数、`sampleId` 去重数、方法数、退化数 | `n_artifact = |{sampleId}|` | — |
| 协议卡 | `config`（划分、退化、强度、种子） | — | 写“配置未记录”，并降为有限支持 |
| 参考图性质 | 固定文案：参考 = 可读 JPG 的 256×256 裁切，不是碑石真值 | — | 必显，不可隐藏 |
| 原图返回比例 | DER `summaryBySplitMethod` | **按方法**给 `passthroughN / n`（n 为该方法该划分的行数），口径见 §1(b) 按方法拆分表；不给跨方法的单一比例 | DER 不存在：显示“未做改动量判定”，等级“未评测”；BRT：禁止给比例（§1(a)） |

## 3. 第 2 层：修复效果视觉对照

| 项目 | 来源 | 派生 / 规则 | 缺失时 |
|---|---|---|---|
| 三联图 ref / in / out | BV2/BVT 行的 `reference`、`input`、`output`；B15 只有 `output`，in 取 degraded PNG | 加载前必须核对 `*Sha256`，不一致就不显示图并报错 | BRT：整层显示“本批次只保存了数值，没有图像”，不得用别批的图代替 |
| 差分热图 | 见 §0.3 `H = |out − in|` | 若 `isPassthrough=true`：不画热图，显示“本次未改动原图（0 像素）” | — |
| 改动量徽标 | DER `changedPixelRatio`、`maxAbsDiff` | 格式 `改动 12.3% 像素，最大差 37` | null 时显示“无法判定” |
| 标签 | DER `appliedStatus` | 原图返回的输出图标题必须是“原图返回（未处理）”，不得叫“算法输出” | — |
| 馆藏运行 | RUN `processing.json` 的字段，或读取时计算（§8） | 同上；见 §8 的文案规则。`passthroughSource='computed-on-read'` 时详情注明“读取时按 pixel-equal-v1 计算” | `isPassthrough=null`：显示“无法判定”和 `passthroughUndeterminedReason` |

## 4. 第 3 层：算法横向比较

| 项目 | 来源 | 派生 | 缺失时 |
|---|---|---|---|
| 主表 | DER `summaryBySplitMethod` + CI 文件（同一批次内，`degradation='ALL'` 行） | 每格：`MeanProcessed`［聚类 CI］、`processedN/n`；次行灰字：`MeanAll`、`MeanPassthrough` | CI 为 null 或 `ciReliable=false`：显示“CI 不可靠（文物数 K）”，等级降为有限支持 |
| 划分 | `split` ∈ {development, test} | 默认显示 **test**。行没有 split 字段（B15、BRT）时，必须显示“本批未划分”，**不得**像 E-07 那样把无 split 的行混进 test | — |
| 相对基线 | 同批 `degraded` | ΔPSNR 与配对增益 CI | — |
| 跨批对照 | — | 必须走 §1(c) | — |

当前实测（DER，test 划分，PSNR dB，均值 = 简单行均值）：

| 批次 | 方法 | n | 处理 / 原图返回 | MeanAll | MeanProcessed | MeanPassthrough |
|---|---|---|---|---|---|---|
| BV2 | adaptive_joint | 70 | 39 / 31 | 25.350 | 25.667 | 24.952 |
| BV2 | notch | 70 | 64 / 6 | 27.346 | 27.027 | 30.749 |
| BV2 | degraded | 70 | — | 25.117 | — | — |
| BVT | adaptive_joint | 70 | 47 / 23 | 26.798 | 28.466 | 23.388 |
| BVT | notch | 70 | 70 / 0 | 27.252 | 27.252 | — |
| BVT | degraded | 70 | — | 24.705 | — | — |

（以上为派生文件里的原始值，属于简单行均值。）

**按文物聚类的配对增益 CI（已计算，seed=20261019，1000 次，每组 K=7 件文物）**：下表为 ΔPSNR（dB），数值为文物均值的均值［95% CI］，`degradation='ALL'`。

| 批次 | 划分 | 方法 | 口径 | 行数 | ΔPSNR［95% CI］ | 判定 |
|---|---|---|---|---|---|---|
| BV2 | development | adaptive_joint | 全部 | 70 | 1.95［−0.01, 3.86］ | 跨 0 |
| BV2 | development | adaptive_joint | 实际处理 | 46 | 4.08［0.50, 7.67］ | 下界 > 0 |
| BV2 | test | adaptive_joint | 全部 | 70 | 0.23［−1.21, 1.47］ | 跨 0 |
| BV2 | test | adaptive_joint | 实际处理 | 39 | 5.35［−1.49, 13.67］ | 跨 0 |
| BV2 | test | notch | 全部 | 70 | 2.23［0.30, 3.55］ | 下界 > 0 |
| BVT | development | adaptive_joint | 全部 | 70 | 1.71［−0.03, 3.42］ | 跨 0 |
| BVT | development | adaptive_joint | 实际处理 | 48 | 3.09［0.06, 6.34］ | 下界 > 0 |
| BVT | test | adaptive_joint | 全部 | 70 | 2.09［0.78, 3.48］ | 下界 > 0 |
| BVT | test | adaptive_joint | 实际处理 | 47 | 3.53［1.11, 6.36］ | 下界 > 0 |
| BVT | test | notch | 全部 | 70 | 2.55［1.67, 3.22］ | 下界 > 0 |

- 两批的其余 6 种固定基线（gaussian_lowpass、butterworth_lowpass、fast_nlm、morphology、nlm_clahe、joint）在 development 和 test 上，“全部”口径的增益 CI 上界都 < 0。
- 按退化类型拆分时，adaptive_joint 在 occlusion 上，两批两个划分的“全部”和“实际处理”口径 CI 上界都 < 0；periodic、salt_pepper 下界 > 0；blur 全部原图返回（增益正好为 0，“实际处理”为空组 null）；gaussian 在 BV2 两个划分跨 0、在 BVT 两个划分下界 > 0。完整结果见 CI 文件。
- 注意：notch 在部分组的 CI 端点只有 ±0.00x dB，例如 BV2 development blur 判为 positive。这是 E-05 截断造成的极小差异，前端应同时显示数值，不要只显示判定。
- 与现有 `grouped_summary` 的对照：
  - 用 `run_v2.grouped_summary`（config seed、共享 rng）重放，复现的 CI 与 results.json 中的 `*CI95` 完全一致（split × method × 3 指标全部一致，atol=1e-12）。
  - 本文件“全部”口径的行均值与 summary 的 `*Mean` 完全一致，最大差 0.0。
  - CI 端点与 summary 不完全相同：BV2 最大差 0.427、BVT 最大差 0.279，约为 summary CI 宽度的 10% / 7.8%。原因只是随机流不同：summary 在所有组之间共用一个 rng，本文件每组用新的固定 seed。两者算法相同。
  - 报告以 CI 文件为准，因为只有它有分口径、分退化的结果和配对增益。

## 5. 第 4 层：消融与机制

| 项目 | 来源 | 规则 | 缺失时 |
|---|---|---|---|
| 决策链分布 | BV2/BVT `diagnostics.decisions`、`selectedOutput`、`fidelityGate`；BRT `diagnosticsOperators`、`fidelityAccepted` | 按算子组合计数。v2.1 新运行有 `outputMode`（`processed` / `identity_no_evidence` / `gate_fallback_original`）；历史行由 DER 的 `isPassthrough` 覆盖 `selectedOutput`（E-02：历史上 identity 分支即使输出等于输入也记为 `candidate`） | — |
| v2.0 → v2.1 | BRT | 只能写“同批复测下的差异”，等级 ≤ 有限支持 | — |
| 门控说明 | 固定文案：fidelity gate 是启发式规则，不是统计检验 | — | — |
| 机制样本（E-18） | MEC：`derived/mechanism/index.json` 和 `<caseId>/mechanism.json` + PNG，字段见 `REPRESENTATIVE_CASES.md；**headCommit 落后 tip 时不得宣称机制图与当前 tip 字节一致**（MECHANISM_HEAD_NOTE.md）` | 每批每个划分 5 类（提升 / 负提升 / 原图返回 / 门控拒绝 / 陷波），按中位位次选取。与前端临时规则（同批次、划分、方法、退化下取实际处理的 ΔPSNR 中位数和最小值各一条，再取一条原图返回）的差异和对照文件 `derived/representative_temp_rule.json` 见 `REPRESENTATIVE_CASES.md；**headCommit 落后 tip 时不得宣称机制图与当前 tip 字节一致**（MECHANISM_HEAD_NOTE.md）`。机制图属于 v2.1（head 重算），已存指标属于 v2.0，必须分别标注 | 目录或 PNG 不存在：显示“该样本未生成机制图”。当前 PNG 还没有 API 路由，需要后端补 |
| 参数机制 | §8 `effectiveParameters`（E-10） | 必须显示**实际生效**的参数；`ignoredRequestParameters` 里的参数要标“本路径未使用” | 旧运行：“未记录实际生效参数” |

## 6. 第 5 层：失败案例与不确定性

| 项目 | 来源 | 规则 |
|---|---|---|
| 负提升原因（E-04） | NLC 文件；BRT 用 `/api` 的 `restoration_diagnosis` 新字段 | 以 `measuredCauses` 为主，每条附 `value`/`threshold`；旧 `cause` 只放在“规则推断”一栏 |
| 负提升列表 | 各批 `ΔPSNR < 0` 的行；BRT `negativeLift` | 全部列出，不抽样，不删除。实测 BRT：v2.0 有 15/70，v2.1 有 16/70；occlusion 下 v2.1 为 35.415，degraded 为 35.886，负提升 9/14 |
| 原图返回 | DER `appliedStatus ∈ {passthrough, passthrough_not_applicable}` | 单独一栏“未处理”，不算成功也不算失败 |
| blur | BV2/BVT 中 adaptive 在 blur 上 28/28 原图返回；BRT 中 v2.0 = v2.1 = degraded = 20.97 | 必须写“该方法对模糊不做处理”，禁止计入提升 |
| 不确定性 | 聚类 CI；n_文物 | n_文物 < 10 时自动降级 |
| 待人工复核 | E-09（V22 interior_constant_block）、E-12（两个 glyph schema） | 挂“待人工复核”徽标 |

## 7. 第 6 层：科学结论与可复现性

| 项目 | 来源 | 规则 |
|---|---|---|
| 结论卡 | 由上面各层汇总 | 每张卡写明：等级、批次 `displayName`、n_文物、口径（Processed / All）、CI |
| 复现信息 | `config`、git 提交、`sourceResultsSha256`（DER）、图像 SHA | 提供 `results.json`、`summary.csv`、`applied_status.csv/json` 的下载（REG 导出已支持后两者） |
| 判据版本 | `passthroughCriterion` | 必显 |
| 已知问题 | E-05（历史批次存在，新代码已修）、E-06、E-07、E-08、E-10 | 列在页脚“已知限制” |

## 8. 后端字段需求（交架构后端实现）

范围：`POST /api/process`（main.py）的响应、`processing.json`、`GET` 运行详情。参考实现在 `agent/arch-backend` 的 `museum_processing.py`（`4379827` 起的 pixel-equal-v1 与读取时计算；`9ba3a57` 灰度参考字段；`49fca00` comparedImages 规范化与 effectiveParameters 读取时推导）。**评测科学家分支不再维护该文件的并行实现**；合并时 `museum_processing.py` 冲突一律取后端版本。main.py 由后端接入。E-03 实测：本地 12 次 adaptive 运行中有 10 次改动 0 像素，界面仍显示“本次算法输出”，`main.py:382` 写的是“实际处理已执行”。

| 字段 | 类型 | 含义 | null 规则 | 前端文案 |
|---|---|---|---|---|
| `isPassthrough` | `bool \| null` | 按 `pixel-equal-v1`：`original.png` 与 `restored.png` 按存储分辨率解码（`IMREAD_UNCHANGED`，不缩放、不裁切、不转灰度），数组形状和位深都相同，且全部通道逐像素相等。**彩色输入经灰度化后输出，算“已改动”**（裁定 F，后端 `4379827` 同此实现） | 图像缺失、解码失败、形状不同；旧运行另有 SHA 规则（见下）：null | true → 标题“本次未改动原图”，副标“算法判断无需处理，输出与输入逐像素相同”，**不得**显示“算法输出”或“实际处理已执行”；false → “算法输出”；null → “未能判定是否改动” |
| `changedPixelCount` | `int \| null` | 改动像素数（任一通道） | 同上 | “改动 N 像素” |
| `totalPixelCount` | `int \| null` | H·W | 同上 | — |
| `changedPixelRatio` | `float \| null`，范围 [0, 1] | 改动像素比例 | 同上 | 百分比，保留 2 位；如果 > 0 但 < 0.01%，显示“<0.01%” |
| `maxAbsDiff` | `int \| null`，8 位图范围 0–255（16 位图 0–65535；差值按 int32 计算，不溢出） | 最大绝对差（任一通道） | 同上 | “最大差 x” |
| `meanAbsDiff` | `float \| null` | 平均绝对差，按全部元素（H·W·通道数）平均 | 同上 | 仅放在详情里 |
| `passthroughCriterion` | `string \| null` | 判据版本，统一为 `pixel-equal-v1`（与实验侧相同） | 无法判定时（`isPassthrough=null`）为 null | 详情：“判据：pixel-equal-v1”；null 时显示“无法判定” |
| `passthroughSource` | `"recorded" \| "computed-on-read" \| null` | `recorded`：处理时计算并写入 `processing.json`；`computed-on-read`：旧运行没有该字段，后端读取时按 `pixel-equal-v1` 当场计算，不回写 | 无法判定时为 null | 详情：“来源：运行时记录 / 读取时计算”；null 时显示“无法判定” |
| `passthroughUndeterminedReason` | `string \| null` | 为什么是 null | 只有 `isPassthrough=null` 时非空 | 原样显示 |
| `grayChangedPixelCount` | `int \| null` | **灰度口径**，只用于并列显示，**不参与** passthrough 判定：两张图按处理管线同一方式灰度化后，值不同的像素数（H·W） | 两张图任一缺失、无法解码或灰度化后形状/位深不同时为 null。**可以**在 `isPassthrough=null`（例如全通道形状不同）时仍有值 | 与 `changedPixelCount` 并列：“灰度口径：改动 N 像素” |
| `grayChangedPixelRatio` | `float \| null`，范围 [0, 1] | `grayChangedPixelCount / (H·W)` | 同上 | 百分比 |
| `grayCriterion` | `string \| null` | **Green 定稿**：`gray-bt601-pixel-equal-v1`（不要用 `working-gray-pixel-equal-v1`；后端正从 working-gray 改过来） | 同上 | 详情：“灰度口径：gray-bt601-pixel-equal-v1” |
| `grayCriterionRule` | `string \| null` | 人读规则，与实现一致：两张图各自按 `algorithm_engine.process_rubbing` 的灰度化——`cv2.cvtColor(BGR→GRAY)`（单通道不转换；四通道先去掉 alpha）；形状相同则逐像素比较。OpenCV 该转换的权重即 BT.601（Y≈0.299R+0.587G+0.114B，定点四舍五入）。**禁止**用 `IMREAD_GRAYSCALE` 代替（解码器灰度与 cvtColor 不同，见 AUDIT 勘误 644816） | 与 `grayCriterion` 同生同灭 | 详情展示规则原文 |
| `graySource` | `"recorded" \| "computed-on-read" \| null` | 与 `passthroughSource` 同语义，但只描述灰度字段的来源 | 灰度字段无法计算时为 null | 详情：“灰度来源：运行时记录 / 读取时计算” |
| `comparedImages` | `string[]`（数组，当前固定为 `["original", "restored"]`） | 参与比较的图像角色，顺序为 [比较前, 比较后]；`original` 是工作输入（有风化掩码时为合成退化图），`restored` 是算法输出 | 不为 null。旧版本写成对象 `{before, after}` 的记录，读取时规范为数组 | 详情 |
| `outputMode` | `"processed" \| "passthrough" \| "undetermined"` | 由 `isPassthrough` 导出，便于前端分支 | — | 同 isPassthrough |
| `effectiveParameters` | `object \| null` | E-10：实际生效的参数。adaptive：`strength = max(0.1, h_nlm / 10)`、`notchWidth = max(0.5, d0 / 60)`、`derivedFrom`、`ignoredRequestParameters = ["filter_order", "clahe_clip", "morph_kernel"]`；固定路径：`d0`、`filterOrder`、`nlmH`、`claheClip`、`morphKernel` | 新运行不为 null。旧运行见下：推导不出时为 null | 有值：参数面板显示“实际生效参数”；null：显示“无法确定实际生效参数”和 reason |
| `effectiveParametersSource` | `"recorded" \| "derived-on-read" \| null` | `recorded`：处理时写入；`derived-on-read`：旧运行缺失该字段时，后端按已核实的版本映射从 `algorithmParameters` 推导，**不回写** | `effectiveParameters=null` 时为 null | 详情 |
| `effectiveParametersUnavailableReason` | `string \| null` | 为什么无法给出 `effectiveParameters` | 仅 `effectiveParameters=null` 时非空 | 原样显示 |

实现约定：

- 计算位置在 PNG 落盘之后，用落盘字节解码比较，避免内存图与文件不一致。
- 旧运行（`processing.json` 没有 `isPassthrough`）：后端读取时当场计算，**不回写**任何文件。条件：运行目录里 `original.png` 和 `restored.png` 都存在，并且两者的 SHA-256 与 `processing.json.outputSha256` 中的记录一致。满足时按 `pixel-equal-v1` 计算全部改动量字段，`passthroughSource='computed-on-read'`。任一图缺失、未记录 SHA 或 SHA 不符时，所有改动量字段为 null，`passthroughSource=null`，`passthroughUndeterminedReason` 写明哪张图、哪种原因；前端显示“无法判定”。
- 本地实测（只读，`D:\RubbingMind\static\results`，24 个 `processing.json`，读取前后哈希不变）：22 个按读取时计算判定（10 个原图返回、12 个实际处理），2 个缺少 `original.png` 判为 null。10 个原图返回均为 `tang_01_duobao` 的 adaptive 运行，与审计 E-03“12 次 adaptive 中 10 次改动 0 像素”一致。
- 彩色输入（裁定 F）：源图是彩色时，`original.png` 是彩色，`restored.png` 是灰度复制成三通道，二者在全部通道上不会相等，所以按裁定判为“已改动”，`changedPixelCount` 通常等于全图。灰度口径字段同时给出灰度化之后的改动量，供并列显示。本地实测 `tang-duobao/20261018T072201_13772747`：全通道 1,507,328 / 1,507,328 px（比例 1.0）；灰度口径 2,719 px（0.18%）。本地 22 个可判定运行里，全通道与灰度口径的真假结论没有分歧。前端规则：`isPassthrough=false` 且 `grayChangedPixelCount` 远小于 `changedPixelCount` 时，在改动比例旁注明“含彩色转灰度，灰度口径改动 N 像素”。
- 无法判定时：`isPassthrough`、`passthroughCriterion`、`passthroughSource` 和全通道改动量字段都为 null，`outputMode='undetermined'`，界面显示“无法判定”和原因。灰度字段按上面的独立 null 规则，不强制与 `isPassthrough` 同为 null。
- 旧运行的 `effectiveParameters`：若记录里没有该字段，后端读取时按 `algorithmVersion` + `algorithmParameters.filter_type` 推导。仅当版本落在已核实映射（adaptive：`adaptive-rubbing-v2.0` / `v2.1`；固定路径：`frequency-spatial-v2.1` / `fixed-frequency-spatial-v2.2`）且所需请求参数齐全时给出对象，`effectiveParametersSource='derived-on-read'`；否则 `effectiveParameters=null`，`effectiveParametersSource=null`，`effectiveParametersUnavailableReason` 写明原因（缺 filter_type、版本未核实、缺请求参数、legacy-unverified 等）。**不回写**。
- 实现归属：`run_change_status`、`effective_parameters` / `effective_parameters_on_read`、`gray_change_status` / 灰度字段、`computed_on_read_status`、`change_stats`（`degradation_analysis`，与后端共用）由**架构后端**在 `agent/arch-backend` 维护。本 SPEC 只定口径；评测科学家分支的实验脚本只消费这些字段，不并行实现。
- ReportsPage 的修改归前端负责；本 SPEC 只规定文案。

## 9. 实验侧新运行的字段（已在 agent/eval-sci 实现）

- `run_v2.py` 和 `compare_v21.py` 的每行增加 `isPassthrough`、`changedPixelCount`、`changedPixelRatio`、`maxAbsDiff`、`passthroughCriterion`；输出未改动时，`applicability` 记为 `passthrough`，不再记为 applicable。
- summary 增加 `processedN`、`passthroughN`、`undeterminedN` 和 `*MeanProcessed`、`*MeanPassthrough`；`applicableN` 不再计入原图返回行。
- `AdaptiveRubbingRestorer.restore` 的诊断增加 `changeStats` 和 `algorithmOutputMode`；输出未改动时，`selectedOutput` 为 `original`。
  - `selectedOutput` 的新含义（架构后端 D-2）：`original` = 最终输出与输入逐像素相同（门控拒绝回退，或门控接受但候选恰好等于输入）；`candidate` = 最终输出至少有 1 个像素不同于输入。旧含义（“门控是否接受了候选”）不再成立。需要门控结论时读 `fidelityGate.accepted`，不要用 `selectedOutput` 推断。历史批次的 `selectedOutput` 仍是旧含义，由 DER 的 `isPassthrough` 覆盖显示。
  - **Green 定稿（D-3）**：算法/诊断层字段名为 `algorithmOutputMode ∈ {processed, identity_no_evidence, gate_fallback_original}`（`AdaptiveRubbingRestorer` 诊断 dict、实验行 `diagnostics` / `adaptiveDiagnostics`）；运行级仍为 `outputMode ∈ {processed, passthrough, undetermined}`（`processing.json` 顶层，§8）。前端按路径区分：报告页“是否改动”只读顶层 `outputMode`；决策链读 `algorithmOutputMode`。历史批次若仍写 `diagnostics.outputMode`，视为 `algorithmOutputMode` 旧名（只读兼容），新运行不得再写旧名。`VERSION` 未改（仍为 v2.1）。新数据要用新批次目录，不要覆盖历史结果。

## 10. B15（2026-10-15）与 v2 系列的退化参数逐项核对

核对方法：`experiments/verify_degradation_params.py`。对每个已存的 degraded 输入，用该批次自己的 `degrade()` 从已存 reference PNG 重新生成，再逐像素比较。

- B15 的 degrade 取自 `git 10a63f4:experiments/run_ablation.py`。
- v2 和 v2-text 的 degrade 取自各自的 `source_snapshot/experiments/run_v2.py`。
- 结果：B15 10/10、BV2 140/140、BVT 140/140 逐像素一致。BV2/BVT 的 `degradationParameters` 与重算一致，140/140。B15 的行没有记录参数，只有 seed。

| 项目 | B15（2026-10-15） | BV2（2026-10-17-v2） | BVT（2026-10-17-v2-text） | 是否相同 |
|---|---|---|---|---|
| 生成代码 | `run_ablation.degrade(reference, mode, seed)` @ 10a63f4 | `run_v2.degrade(reference, mode, seed, strength)`（快照 `6fea1321…`） | 同 BV2 的函数（快照 `8d804230…`，degrade 部分与 BV2 逐行相同） | B15 ≠ v2；BV2 = BVT |
| 退化类型 | gaussian、salt_pepper、periodic、blur、occlusion | 同左 | 同左 | 相同 |
| 强度 | 单一强度，等价于 strength = 1.0 | strengths = [0.65, 1.3] | 同 BV2 | 不同 |
| gaussian | σ = 18；`reference.astype(float)` 为 float64 再加噪声 | σ = 18·s = 11.7 / 23.4；float32 | 同 BV2 | 不同 |
| salt_pepper | 每侧概率 0.018 | 0.018·s = 0.0117 / 0.0234 | 同 BV2 | 不同 |
| periodic | 水平正弦，幅值 27，周期 8 px，相位 0 | 幅值 27·s = 17.55 / 35.1，周期 8，相位 0 | 同 BV2 | 幅值不同 |
| blur | GaussianBlur σ = 1.5 | σ = 1.5·s = 0.975 / 1.95 | 同 BV2 | 不同 |
| occlusion | 在 (w//3, h//3) 处填 28×45 的中值块 | 位置相同，尺寸为 int(28·s)×int(45·s) = 18×29 / 36×58 | 同 BV2 | 尺寸不同 |
| 种子 | 20261015 + 100·i + j（i = 样本序号，j = 退化序号） | 20261017 + 100·i + 10·j + k（k = 强度序号） | 20261018 + 100·i + 10·j + k | 不同 |
| 样本 | 2 件：han_01_caoquan、tang_01_duobao | 14 件（每朝代前 2 件），其中包括 B15 的这 2 件 | 14 件（id 为 *_03 / *_04），与 B15、BV2 都不重合 | B15 ⊂ BV2（按文物） |
| 裁切 | han_01 [300,400,556,656]；tang_01 [250,250,506,506] | han_01 [486,1282,742,1538]；tang_01 [809,695,1065,951]（中心裁切） | — | 同一源图（SHA 相同），但裁切区域重叠为 0 |
| 方法差异 | `joint` 按退化标签选择：periodic 时用 notch，否则用 butterworth（**使用了退化标签**）；没有 adaptive_joint | `joint` 一律用 butterworth（不看标签）；有 adaptive_joint | 同 BV2 | 不同 |
| 汇总口径 | summary 排除 not_applicable（`run_ablation.py:122`） | summary 计入全部行（`run_v2.py:72`） | 同 BV2 | 不同（E-06） |

结论：
- B15 与 v2 系列的退化生成器、强度、种子、裁切和 joint 定义都不同，只有退化类型名称相同。
- 跨批比较必须同时触发 C1（裁切不同）、C2、C3（joint 定义不同）、C4 四条警告。
- B15 的 `joint` 在 periodic 上使用了退化标签，不能作为“免标签”方法与 v2 的 `joint` 比较。

## 11. E-04 负提升原因（测量量推导）与 E-05 对单次处理的影响

**E-04**：`restoration_diagnosis.diagnose()` 保留旧字段，同时新增测量原因字段。

- 旧字段 `cause` 保留，新增 `causeBasis='规则推断（按退化类型）'`。
- 新增 `measuredCauses`（触发的原因列表）、`measuredEvidence`（每条判据的 `measure`、`value`、`comparator`、`threshold`、`available`、`triggered`、`unavailableReason`）、`measures`，以及顶层的 `measuredCauseCounts`、`measuredCriteria`、`measuredCriteriaVersion='measured-causes-v1'`。
- 判据是事先声明的常数，没有按结果调整：

| 原因 | 测量量 | 阈值 |
|---|---|---|
| 笔画前景损失 | `foregroundLossDelta`（参考图前景中，输出丢失的比例减去输入丢失的比例） | > 0.02 |
| 边缘保真下降 | `edgeF1Delta` | < −0.02 |
| 细笔画误差增大 | `thinStrokeMaeDelta`（参考 Canny 像素上的 MAE，输出减输入） | > 0.5 |
| 结构相似度下降 | `ssimDelta` | < −0.01 |
| 周期干扰残留 | `periodicEnergyRatio`（输出周期峰能量 / 输入周期峰能量） | ≥ 0.5 |
| 引入新的周期峰 | 输入没有峰时，输出的周期峰能量 | > 0 |
| 改动幅度超过输入误差 | `changeToInputErrorRatio` = mean\|out−in\| / mean\|in−ref\| | > 1.0 |
| 改动落在缺失/平坦区域 | `changedInMissingFraction`（改动像素中，落在 `missing_information_mask(input)` 内的比例） | > 0.2 |
| 强边缘被削弱 | `strongEdgeRetention` | < 0.85 |
| 对比度被放大 | `contrastRatio` | > 1.10 |

- 一个案例可以触发多条原因；没有任何判据触发时记为“未定位到测量原因（待人工复核）”。
- 同批复测批次没有图像，像素级量标为 `available=false`。实测该批 16 个负提升中，13 个“未定位”，3 个“结构相似度下降”。旧规则把 9 个归为“本身信息不可恢复”。
- 有图像的历史批次写在 NLC 文件里，覆盖全部方法：B15 40 行，BV2 747 行，BVT 754 行。adaptive_joint 的负提升 BV2 有 32 行、BVT 有 33 行，最常触发的是“结构相似度下降”和“边缘保真下降 / 细笔画误差增大 / 前景损失 / 改动超过输入误差”。notch 的负提升多数“未定位”（BV2 46 行、BVT 44 行），与 E-05 的极小截断差异一致。
- 前端：失败层以 `measuredCauses` 为主，每条附测量值和阈值；`cause` 只能放在“旧规则推断”一栏，并标明。

**E-05 对单次处理（museum_processing）的影响**：用 `experiments/e05_processing_impact.py` 在 `static/samples/sample_1..4.png` 上比较 f0c5886 与 7623a52 两版引擎的 `process_rubbing` 输出。

- `filter_type='adaptive'`（默认）：4/4 restored 逐像素相同，不受影响。
- `gaussian`、`butterworth`：4/4 相同。
- `notch` 且未检出峰（sample_1、2、4）：restored 改变，改动 65869 / 84412 / 69501 px（共约 10 万 px），最大差 37 / 31 / 96。原因是旧代码的 1 级截断经过后续空域增强（含 CLAHE）后被放大。
- `notch` 且检出峰（sample_3）：相同。
- 因此，`museum_processing.process_verified_request` 只在用户选择 `filter_type='notch'` 且图像没有周期峰时，输出会变。这时新输出更接近“陷波不适用、直接做空域增强”的本意。旧运行的输出图不会被重算；只有改动量字段在读取时计算（§8）。
