# REPORT_DATA_SPEC — 评测报告六层数据契约

- 版本：v1（2026-10-19，RM-评测科学家）
- 基线：`feature/product-grade-upgrade` @ `f0c5886`。配套实现：分支 `agent/eval-sci`（未合并）
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
| DER | `experiments/results/<批次>/derived/applied_status.{csv,json}` | 派生标注（本次新增，由 `experiments/derive_applied_status.py` 生成） | 不适用 |
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
| 增益 | `ΔPSNR = PSNR(out, ref) − PSNR(in, ref)`，SSIM、edgeF1 同理；thinStrokeMae 用 `in − out`（越大越好） | 前端可算，DER/结果里已有 `psnr` |
| 差分热图 | `H = |out − in|`（不是 `out − ref`），显示时 `clip(H / max(1, P99(H)), 0, 1)` 映射到单色色带。另提供带符号图 `S = out − in`，用发散色带，0 为中性色。图上必须标注 `maxAbsDiff`、`changedPixelRatio` 和 P99 归一化常数 | 前端计算，或后端以后按需生成 |
| 误差图 | `E_x = |x − ref|`，x ∈ {in, out}；`ΔE = E_in − E_out`（正值表示更接近参考） | 前端 |
| 按文物聚类 CI | 对方法 m、退化 d、划分 s：先算每件文物的均值 `ā_k = mean_{strength} metric`；再对 K 件文物做 1000 次有放回重采样；CI = 第 2.5 和 97.5 百分位。与 `run_v2.grouped_summary` 一致。种子要固定并写进输出 | `experiments/run_v2.py: grouped_summary` |
| 配对增益 CI | 与上相同，但对象换成每件文物的 `mean(ΔPSNR)`。只有 CI 下界 > 0 才能写“提升” | 前端或后端（待实现，见 §8） |
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
  - 默认选中批次禁止是 BRT（E-07：`items.at(-1)` 会默认选中它）。默认应选最新的有图像批次（BVT）。
- 代码侧：`experiments/compare_v21.py` 的排除表现在扫描 `experiments/results/*/results.json`，包括 v2-text 和更早的批次。再遇到重叠时直接 `SystemExit`，除非显式传 `--allow-seen`；此时结果标记 `heldOut:false`。

### (b) “原图返回”与“实际处理”分开计数、分开求均值

- 判据：输出与输入逐像素相同（`pixel-equal-v1`）。字节相同另列 `byteIdentical`。实测 BV2 的 65 行、BVT 的 47 行原图返回全部字节相同。
- 每个方法 × 划分（× 退化）都必须同时显示：`n`、`processedN`、`passthroughN`、`undeterminedN`，以及三种均值。主数字用 `MeanProcessed`，并且必须旁注“另有 passthroughN 行原样返回，均值 x”。`MeanAll` 只放在“与历史 summary 对照”一栏。
- `appliedStatus` 枚举（DER 每行一个）：

| 值 | 含义 | 前端标签 |
|---|---|---|
| `baseline` | degraded 基线本身 | 输入基线 |
| `processed` | 改动 ≥1 像素 | 实际处理 |
| `passthrough` | 0 像素改动，且记录里标为 applicable | 原图返回（未处理） |
| `passthrough_not_applicable` | 0 像素改动，记录标 not_applicable | 原图返回（判定不适用） |
| `processed_not_applicable_label` | 记录标 not_applicable，但像素被改动了（E-05：notch 走 NA 分支时 astype(uint8) 截断） | 标为不适用但有改动（E-05） |
| `failed` | 运行出错 | 失败 |
| `undetermined` | 无图像或无法解码 | 无法判定 |

- E-05 只在本 SPEC 中记录，本次不修：notch 的 NA 分支平均绝对差 0.084（BV2）/ 0.161（BVT），符号为负。`ExperimentExplorer.tsx:37` 的“以原图计入”说法不成立。前端在 notch 卡片上必须显示“不适用分支仍有轻微像素改动（E-05，待修）”。
- BRT 没有图像，因此 `isPassthrough = null`，`undeterminedN = 70`（每个方法），不猜测。允许另列两个**指示量**，必须标“未经像素验证”：
  - `indicatorPsnrDeltaZeroN`：`psnrDeltaFromInput == 0` 的行数；
  - `indicatorCopyOnlyOperatorsN`：`diagnosticsOperators ⊆ {skip_notch, identity, preserve_missing, fallback_identity}` 的行数（按代码阅读，这些算子只复制输入）。
  - 实测：adaptive_v20 / v21 都是 21 / 19。两者不一致，正好说明不能当判据。

### (c) 跨批次比较警告规则

只要比较的两个数字来自不同批次，就必须逐条检查下面四项，命中任一条就在比较处显示黄色警告条，并把该比较降为“有限支持”或更低：

| # | 差异 | 检查方式 | 警告文案 |
|---|---|---|---|
| C1 | 样本集 | 比较两批的 `sampleId` 集合和源图 SHA；记 Jaccard。B15/BV2 与 BVT/BRT 的文物集合不同，BVT 与 BRT 相同 | “两批样本集不同（重合 x/y 件），差异可能来自样本而非算法。” 若完全相同但其中一批参与过调参：“同一批文物复测，不是独立验证。” |
| C2 | 退化生成器 | 比较 `config` 中退化类型、强度表、种子、生成代码提交。B15 与 v2 系列退化参数是否相同：待核（逐项比对 config 后填写） | “退化生成方式不同，PSNR 绝对值不可直接比较，只比较同批内相对增益。” |
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
| 原图返回比例 | DER `summaryBySplitMethod` | `passthroughN / (n − baseline)` | DER 不存在：显示“未做改动量判定”，等级“未评测” |

## 3. 第 2 层：修复效果视觉对照

| 项目 | 来源 | 派生 / 规则 | 缺失时 |
|---|---|---|---|
| 三联图 ref / in / out | BV2/BVT 行的 `reference`、`input`、`output`；B15 只有 `output`，in 取 degraded PNG | 加载前必须核对 `*Sha256`，不一致就不显示图并报错 | BRT：整层显示“本批次只保存了数值，没有图像”，不得用别批的图代替 |
| 差分热图 | 见 §0.3 `H = |out − in|` | 若 `isPassthrough=true`：不画热图，显示“本次未改动原图（0 像素）” | — |
| 改动量徽标 | DER `changedPixelRatio`、`maxAbsDiff` | 格式 `改动 12.3% 像素，最大差 37` | null 时显示“无法判定” |
| 标签 | DER `appliedStatus` | 原图返回的输出图标题必须是“原图返回（未处理）”，不得叫“算法输出” | — |
| 馆藏运行 | RUN `processing.json` 的新字段（§8） | 同上；见 §8 的文案规则 | 旧运行没有字段：显示“该运行保存于判据引入前，未记录改动量” |

## 4. 第 3 层：算法横向比较

| 项目 | 来源 | 派生 | 缺失时 |
|---|---|---|---|
| 主表 | DER `summaryBySplitMethod`（同一批次内） | 每格：`MeanProcessed`［聚类 CI］、`processedN/n`；次行灰字：`MeanAll`、`MeanPassthrough` | CI 未算：显示“无 CI”，等级降为有限支持 |
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

（以上为派生文件里的原始值。聚类 CI 未在派生文件中重算，标“待核”。）

## 5. 第 4 层：消融与机制

| 项目 | 来源 | 规则 | 缺失时 |
|---|---|---|---|
| 决策链分布 | BV2/BVT `diagnostics.decisions`、`selectedOutput`、`fidelityGate`；BRT `diagnosticsOperators`、`fidelityAccepted` | 按算子组合计数。v2.1 新运行有 `outputMode`（`processed` / `identity_no_evidence` / `gate_fallback_original`）；历史行由 DER 的 `isPassthrough` 覆盖 `selectedOutput`（E-02：历史上 identity 分支即使输出等于输入也记为 `candidate`） | — |
| v2.0 → v2.1 | BRT | 只能写“同批复测下的差异”，等级 ≤ 有限支持 | — |
| 门控说明 | 固定文案：fidelity gate 是启发式规则，不是统计检验 | — | — |
| 参数机制 | §8 `effectiveParameters`（E-10） | 必须显示**实际生效**的参数；`ignoredRequestParameters` 里的参数要标“本路径未使用” | 旧运行：“未记录实际生效参数” |

## 6. 第 5 层：失败案例与不确定性

| 项目 | 来源 | 规则 |
|---|---|---|
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
| 已知问题 | E-05（未修）、E-06、E-07、E-08、E-10 | 列在页脚“已知限制” |

## 8. 后端字段需求（交架构后端实现）

范围：`POST /api/process`（main.py）的响应、`processing.json`、`GET` 运行详情。参考实现在 `agent/eval-sci` 的 `museum_processing.py`（已在 `process_verified_request` 和 `read_run` 中实现。main.py 本身不改，由后端评审后接入）。E-03 实测：本地 12 次 adaptive 运行中有 10 次改动 0 像素，界面仍显示“本次算法输出”，`main.py:382` 写的是“实际处理已执行”。

| 字段 | 类型 | 含义 | null 规则 | 前端文案 |
|---|---|---|---|---|
| `isPassthrough` | `bool \| null` | 工作灰度图上，restored 与 original 逐像素相等 | 图像缺失、解码失败、尺寸不同，或旧运行：null | true → 标题“本次未改动原图”，副标“算法判断无需处理，输出与输入逐像素相同”，**不得**显示“算法输出”或“实际处理已执行”；false → “算法输出”；null → “未能判定是否改动” |
| `changedPixelCount` | `int \| null` | 改动像素数（任一通道） | 同上 | “改动 N 像素” |
| `totalPixelCount` | `int \| null` | H·W | 同上 | — |
| `changedPixelRatio` | `float \| null`，范围 [0, 1] | 改动像素比例 | 同上 | 百分比，保留 2 位；如果 > 0 但 < 0.01%，显示“<0.01%” |
| `maxAbsDiff` | `int \| null`，范围 0–255 | 最大绝对差 | 同上 | “最大灰度差 x” |
| `meanAbsDiff` | `float \| null` | 平均绝对差 | 同上 | 仅放在详情里 |
| `passthroughCriterion` | `string` | 判据版本，当前为 `working-gray-pixel-equal-v1`（实验侧为 `pixel-equal-v1`） | 不为 null | 详情：“判据：working-gray-pixel-equal-v1” |
| `passthroughUndeterminedReason` | `string \| null` | 为什么是 null | 只有 `isPassthrough=null` 时非空 | 原样显示 |
| `comparedImages` | `[string, string]` | 比较的两张图的角色，例如 `["original", "restored"]` | — | 详情 |
| `outputMode` | `"processed" \| "passthrough" \| "undetermined"` | 由 `isPassthrough` 导出，便于前端分支 | — | 同 isPassthrough |
| `effectiveParameters` | `object` | E-10：实际生效的参数。adaptive 路径给 `strength = max(0.1, h_nlm / 10)`、`notchWidth = max(0.5, d0 / 60)`、`derivedFrom`（公式）、`ignoredRequestParameters = ["filter_order", "clahe_clip", "morph_kernel"]`；固定路径给 `d0`、`filterOrder`、`nlmH`、`claheClip`、`morphKernel` | 不为 null | 参数面板显示“实际生效参数”，被忽略的参数灰显，并注明“自适应路径未使用” |

实现约定：

- 计算位置在 PNG 落盘之后，用落盘字节解码比较，避免内存图与文件不一致。
- 旧运行读取时补 `null` 和原因“该运行保存于判据引入前，未记录改动量”，不回写旧文件。
- ReportsPage 的修改归前端负责；本 SPEC 只规定文案。

## 9. 实验侧新运行的字段（已在 agent/eval-sci 实现）

- `run_v2.py` 和 `compare_v21.py` 的每行增加 `isPassthrough`、`changedPixelCount`、`changedPixelRatio`、`maxAbsDiff`、`passthroughCriterion`；输出未改动时，`applicability` 记为 `passthrough`，不再记为 applicable。
- summary 增加 `processedN`、`passthroughN`、`undeterminedN` 和 `*MeanProcessed`、`*MeanPassthrough`；`applicableN` 不再计入原图返回行。
- `AdaptiveRubbingRestorer.restore` 的诊断增加 `changeStats` 和 `outputMode`；输出未改动时，`selectedOutput` 为 `original`。`VERSION` 未改（仍为 v2.1）。新数据要用新批次目录，不要覆盖历史结果。
