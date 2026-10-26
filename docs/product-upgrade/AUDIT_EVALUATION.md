# AUDIT_EVALUATION —— 评测与图像算法只读审计（Phase 0）

- 作者：RM-评测科学家（Agent 04 计算机视觉 + Agent 05 评测科学）
- 时间：2026-10-19 11:50（Asia/Shanghai）
- 仓库：`D:\RubbingMind`，分支 `feature/product-grade-upgrade`，HEAD `f0c5886a9d4c8b47d64640e1f7eaeac44be3c388`
- 性质：只读审计。没有改代码、数据、影像，没有建 worktree，没有切分支，没有启动或停止服务。唯一写入的仓库文件是本文。临时文件放在 `C:\Users\WPY11\rm-eval-sci-tmp`，结束后已删除。
- 证据分级：已验证 / 未实现 / 缺陷；不确定的写“待核”。

## 0. 方法与环境核对

| 步骤 | 命令（摘要） | 输出摘要 |
|---|---|---|
| Git 状态 | `git -C D:\RubbingMind rev-parse HEAD` / `branch --show-current` / `status --short` | `f0c5886a…`，`feature/product-grade-upgrade`；只有用户未跟踪文件（design/blender、rubbings-*、screenshots/*、user_prompt_10.txt、墨韵智考_真实碑拓28件高清成品/、docs/product-upgrade/），没有已跟踪文件被修改 |
| 本文是否已存在 | `Test-Path …\AUDIT_EVALUATION.md` | `False`（新建，没有覆盖） |
| 源码读取 | 用 python `zipfile` 把 `git ls-files` 中 421 个文本文件打包到临时目录，再复制到审计沙箱逐行阅读 | 读取的是 HEAD 工作区里的字节，未修改 |
| 数值复算 | python 只读脚本读取 `experiments/results/*/results.json|csv`、`static/results/*/*/processing.json`、`data/catalog/assessments/*.json`，SQLite 用 `mode=ro` | 见各条 |
| 运行中 API | 只对用户已经在跑的 `127.0.0.1:8000` 发 GET：`/api/experiments`、`/api/experiments/heldout-v20-v21-2026-10-18[/diagnosis]`、`/api/steles`、`/api/glyph-evaluation`、`/api/steles/tang_01_duobao/report`、一张实验资产图 | 全部 200；没有发 POST/DELETE |

审计范围内的真实路径：
- 实验注册：`experiment_registry.py`（仓库根目录，不在 experiments/ 下），API 在 `main.py:164-201`
- 实验脚本：`experiments/run_ablation.py`、`run_v2.py`、`compare_v21.py`、`synthetic_v22.py`、`evaluate_glyphs.py`、`analyze_v2.py`、`benchmark_v2.py`、`prepare_text_v2.py`
- 实验批次：`experiments/results/2026-10-15/`、`2026-10-17-v2/`、`2026-10-17-v2-text/`、`2026-10-18-v21-heldout/`、`2026-10-18-rapidocr-probe/`、`2026-10-18-synthetic-v22-summary.json`、`glyph-v2-evaluation.json`
- 前端：`apps/web/src/pages/ReportsPage.tsx`（114 行）、`components/ExperimentExplorer.tsx`（46 行）、`components/HeldoutComparison.tsx`（67 行）、`components/GlyphInferencePanel.tsx`
- 图像算法：`algorithm_engine.py`、`degradation_analysis.py`（自适应 v2.1 与保真门控、v2.2 候选）、`museum_processing.py`（单次运行持久化）、`restoration_diagnosis.py`
- 残字：`glyph_inference.py`、`glyph_vision.py`、`glyph_annotations.py`、`glyph_ocr.py`、`data/catalog/glyph-benchmark-v2.json`

## 1. 发现汇总

共 25 条：P0 3 条，P1 9 条，P2 13 条（其中 5 条是“已验证、需要保持”的正面结论）。

| 编号 | 优先级 | 状态 | 一句话 |
|---|---|---|---|
| E-01 | P0 | 缺陷 | 标为“留出”的 v2.0/v2.1 对比用的是 v2-text 批次已经用过的同 14 件文物（同 SHA，其中 2 个裁切重叠），v2.1 是看过 v2-text 失败结果之后才改的 |
| E-02 | P0 | 缺陷 | 实验层没有区分“原图返回”和“实际处理”：identity 路径输出与输入逐字节相同，却记成 `selectedOutput:'candidate'`、`applicability:'applied'` 计入均值 |
| E-03 | P0 | 缺陷 | 单次文物处理报告：本机 12 次自适应运行里 10 次改动像素为 0，报告页仍然显示“本次算法输出”，后端写“实际处理已执行” |
| E-04 | P1 | 缺陷 | 负提升“原因”是按退化标签套规则写出来的，没有测量依据，却在 UI 上作为原因统计展示 |
| E-05 | P1 | 缺陷 | 陷波标 `not_applicable` 时仍会改像素（浮点截断偏 −1），UI 却写“不适用陷波以原图计入” |
| E-06 | P1 | 缺陷 | 各批次汇总口径不同，跨批次比较没有防护（2026-10-15 notch 汇总 41.364 dB 与 Explorer 现算的 27.813 dB 不一致） |
| E-07 | P1 | 缺陷 | Explorer 的 dev/test 过滤对没有 split 字段的批次不起作用；默认打开的批次是 heldout，没有图、没有 split、没有 CI，与页面文案矛盾 |
| E-08 | P1 | 未实现 | heldout 批次一张输出图都没有，三联图和差分图无法提供 |
| E-09 | P1 | 缺陷（风险） | v2.2 候选门控按模拟器遮挡（精确常数块）定制，只在已见过的 14 个裁切上测过 |
| E-10 | P1 | 缺陷 | 单次运行记录的参数不是实际生效的参数（adaptive 模式把 h、d0 换算成 strength、notch_width，其余参数被忽略但仍记录） |
| E-11 | P2 | 缺陷 | 可复现溯源有缺口：gitSha 相同但代码 SHA 不同；heldout 没有 codeSha256；单次运行都在 gitignore 目录里 |
| E-12 | P1 | 未实现 | 残字评测有两套互不兼容的 schema 和链路，即使有真值也算不出 Top-k；报告页“未评测”是写死的文字 |
| E-13 | P2 | 缺陷（风险） | 上下文规则候选是 5 条硬编码规则；模板检索不做文物隔离 |
| E-14 | P2 | 已验证+注意 | PSNR 的“配对参考”是经过对比度处理、缩放、JPEG 的阅读图局部；edgeF1 是不带容差的 Canny Dice |
| E-15 | P2 | 已验证 | 无配对参考的真实拓本没有报告修复 PSNR/SSIM（有一处潜在的 0 值隐患） |
| E-16 | P2 | 已验证 | Top-1/Top-3/拒识率保持“未评测”，没有伪造 |
| E-17 | P2 | 已验证 | 报告上的实验数字能从原始 JSON/CSV 复算出来（0 不一致）；影像 SHA 全部一致；列出硬编码常量 |
| E-18 | P1 | 未实现 | 机制层可视化（频谱、陷波位置、二值前景、边缘）在实验批次里没有落盘；单次运行的图只存在本机 |
| E-19 | P2 | 已验证+注意 | 批次内 dev/test 按文物划分、没有重叠；但每组只有 7 件，UI 标准差没按文物聚类 |
| E-20 | P2 | 缺陷 | 28 件归档评估里 7 件输出与输入完全相同（UI 已标明），另外 21 件平均改动 ≤1.31 灰度级，仍标“processed” |
| E-21 | P2 | 缺陷 | 同一文物有 `tang-duobao` 和 `tang_01_duobao` 两个 ID，运行记录被拆开（4 次 / 10 次） |
| E-22 | P2 | 缺陷 | 报告页选中某次运行后，基于原图的残字推演（runId=None）会被过滤掉 |
| E-23 | P2 | 未实现 | 打印 PDF 不含全局评测（HeldoutComparison、Explorer 都设了 print:hidden） |
| E-24 | P2 | 缺陷 | 条形图混用“越大越好/越小越好”的指标却不标方向；Explorer 表格不显示“原图返回”数 |
| E-25 | P2 | 已验证 | 失败与负提升都保留着，没有删除，也没有改成 0 分 |

---

## 2. 逐条发现

### E-01 【P0】“留出”批次与已用文物重叠，且算法是看过这些文物的结果之后才修改的（测试集泄漏 / 按测试集调参）
- 位置：`experiments/compare_v21.py:1-6, 46-64`（第 49-51 行的 `previous` 只列了 2026-10-17-v2 的 14 件）；`experiments/results/2026-10-18-v21-heldout/results.json` 中的 `samples[*].excludedFromPreviousBatch`、`notThePreviousBatch`；`apps/web/src/components/HeldoutComparison.tsx:37-38, 51, 60`（ID、aria-label、标签都叫“留出”）；`tests/test_heldout_v21.py:9-15` 把这份样本清单写成了断言。
- 实测：
  - python 读两份 results.json，比对文物 ID 和 SHA：heldout 的 14 件**全部**在 `2026-10-17-v2-text` 里出现过，`sourceSha256` 全部相同（`same sha True`）。在 v2-text 里，其中 7 件是 development，7 件是 test。
  - 裁切重叠：`song_03_daguan` 两批裁切都是 `[497,1328,753,1584]`，重叠 1.0；`tang_04_xuanmita` 重叠 0.795；其余 12 件重叠 0。
  - `excludedFromPreviousBatch` 14/14 为 True，但它只和 v2（01/02 号）比，没有和 v2-text（03/04 号）比。
  - 时间线：`git log --date=iso`：v2-text 结果在 `f9aebdb 2026-10-17 18:13` 入库；它的 `error-analysis.md` 记录了 adaptive_joint 在 occlusion 上 dev 12/14、test 11/14 劣于输入，在 periodic 上明显不如单独陷波。随后 `ea5a67a 2026-10-18 00:56` 把 VERSION 改成 `adaptive-rubbing-v2.1`，新增 `missing_information_mask/preserve_missing_regions`（针对遮挡）、`stop_after_notch`（针对周期）、`thin_stroke_nlm`；`15dc6c0 09:59` 又调了“页面底色空白不算缺损”；`59f9784 10:52` 才在同一批 14 件上跑出“留出”结果。
  - v2-text 的 `error-analysis.md` 自己写着“后续若继续调参，应另设未使用的文物留出集”，这条没有被执行。
- 状态：缺陷。v2.1 的改动是否“依据测试组数值”无法从代码直接证明（待核），但改动对准了 v2-text 记录的失败类型，而且用的是同一批文物，按 BRIEF“不得按测试集调参”的标准，这批结果不能叫留出验证。
- 用户影响：报告页把 v2.1 的提升（全退化平均 PSNR 27.343→28.981，periodic 32.989→39.645）当作留出证据展示，研究结论被高估。
- 风险：科学结论失真，答辩或评审时被质疑数据泄漏。
- 修复路径：①把这批改名为“已见文物上的回归对比（non-held-out）”，在 UI、API 注册信息和 limitations 里写明与 v2-text 重叠的 14 件、2 个重叠裁切；②修正 `excludedFromPreviousBatch` 的判定，要排除所有历史批次的 ID 和 SHA；③28 件已经全部用于实验，真正的留出需要新的授权文物或新的独立来源，而且要先登记清单、冻结代码 SHA 再计分；④在 `tests/test_heldout_v21.py` 加一条“与所有历史批次文物不重叠”的断言，当前清单应该让这条测试失败。
- 验收标准：`/api/experiments` 里不再有名字带 heldout、但与历史批次有文物重叠的批次；有一个单元测试按文物 ID 和 SHA 检查与全部历史批次不相交；UI 文案里不再出现“留出”二字，除非这条测试通过。

### E-02 【P0】实验层没有区分“原图返回（identity 或门控跳过）”与“实际处理”
- 位置：`degradation_analysis.py:185-186`（identity 分支）、`:191-193`（fallback_identity）、`:195`（`selectedOutput` 只有门控拒绝时才是 `original`）；`experiments/run_v2.py:108`（adaptive 一律记 `applicability='applied'`）；`experiments/compare_v21.py:110`；`apps/web/src/components/ExperimentExplorer.tsx:16`（“适用数”把 identity 也算进去）；`HeldoutComparison.tsx:57-58`（只显示负提升，不显示 unchangedCount）。
- 实测（python 只读复算，对比 `outputSha256==inputSha256`）：
  - `2026-10-17-v2` adaptive_joint 140 行：`('candidate', 输出=输入, 'identity')` 38 行，`('original', 输出=输入, 'fallback_identity')` 17 行，合计 55/140 原样返回；其中 blur 28/28。
  - `2026-10-17-v2-text`：candidate+identity 33 行，fallback 12 行，合计 45/140；blur 28/28。
  - `2026-10-18-v21-heldout` adaptive_v21：`psnrDeltaFromInput==0` 有 21/70（blur 14、occlusion 5、salt_pepper 2）；v2.0 也是 21/70。这些行都记 `applicability:'applied'`。blur 下 v2.1 的“负提升 0/14”其实是 14/14 没动像素。
  - API `/diagnosis` 返回 `unchangedCount: 21`，但 HeldoutComparison 第 58 行没有展示它。
- 状态：缺陷。
- 用户影响：“适用数”“负提升 0/14”“平均 PSNR”把“什么也没做”混成“处理有效或无害”，blur 的结论尤其误导。
- 风险：违反 BRIEF“区分原图返回与实际处理”；放大自适应方法看起来的稳健性。
- 修复路径：①在 `restore()` 输出里加 `outputMode ∈ {processed, identity_no_evidence, gate_fallback_original}`，判定依据是像素是否相同，而不是只看门控；`selectedOutput` 在 identity 分支设成 `original`；②实验行加 `unchangedFromInput: bool`（按 SHA 判定）；③汇总表分三栏：实际处理 n / 原图返回 n / 门控回退 n，负提升率只在“实际处理”子集上算，同时报告全样本口径；④历史批次不重写原文件，由 registry 读取时根据 `outputSha256==inputSha256` 派生出这个字段。
- 验收标准：对 v2、v2-text、heldout，UI 显示的原图返回数分别是 55、45、21（v2.1），并按退化类型拆分；blur 一行显示“14/14 未修改”，不显示“0 负提升”；有单元测试覆盖 identity 分支不再标 `candidate`。

### E-03 【P0】单次文物处理报告把“未修改的原图”展示成“本次算法输出”
- 位置：`museum_processing.py:52-58, 66`（`imageRoles.restored='algorithm_output'`，没有顶层 unchanged 字段）；`main.py:382`（`evaluation_summary='实际处理已执行，但没有配对真值…'`）；`apps/web/src/pages/ReportsPage.tsx:99`（图注“本次算法输出”）、`:32,20`（默认选最新一次运行）；`GlyphInferencePanel.tsx:126`（可以在这类“修复结果”上做残字推演）。
- 实测：
  - 只读读取本机 `static/results/*/*/processing.json`，共 24 个：自适应 12 个、固定频域 3 个、旧版（无 runId）9 个。用 cv2 逐像素比对 `original.png` 和 `restored.png` 的灰度：**10/12** 次自适应运行 `changedPixels 0`、`MAC 0.000`（tang_01_duobao 的 v2.0 6 次、v2.1 4 次），`selectedOutput` 都是 `candidate`，决策链 `['skip_notch','identity']`。
  - GET `/api/steles/tang_01_duobao/report`：默认运行 `20261018T082526_4728b9df`，`selectedOutput: candidate`，`evaluation_summary` 是“实际处理已执行…”。这次运行的像素改动为 0。
  - SQLite（只读）`glyph_inferences` 共 11 条，其中 3 条 `imageSource='restored'` 都在 tang_01_duobao 上，也就是在“与原图相同的修复结果”上做的推演。
- 状态：缺陷。
- 用户影响：用户以为算法处理过这件拓片，PDF 和 JSON 导出也会带着“算法输出”的说法。
- 风险：可信交付、真实流程层面的 P0；与归档评估页的做法不一致（`AssessmentViewer.tsx:110` 已经会写“处理前后像素没有发生变化”）。
- 修复路径：①`process_verified_request` 计算 `unchangedFromInput`（工作灰度图逐像素比较）和 `changedPixelFraction`，写进 processing.json；②报告页和工作台在 unchanged 时把图注改成“算法判定无需处理，输出与输入相同”，并显示决策链和门控理由；③`evaluation_summary` 按三种状态分别措辞；④残字推演选“修复结果”时，如果 unchanged，就提示它等同于原图。
- 验收标准：对上面 10 次运行，报告页和导出的 JSON 都显示“未修改”；changedPixels>0 的运行（如 `20261018T072201_13772747`，644816 像素，MAC 0.274）显示改动比例；有 e2e 或单元测试覆盖。

### E-04 【P1】负提升原因按退化标签硬写，不是测量出来的
- 位置：`restoration_diagnosis.py:11-25`（occlusion 写成“本身信息不可恢复”、periodic 写成“频谱检测不可靠”等）、`:58`（“14 件”硬编码）；展示在 `HeldoutComparison.tsx:58`。
- 实测：GET `/diagnosis` 返回 `causeCounts` 3 类：occlusion 9、gaussian 5、periodic 2；cases 共 37 条（21 条“算法没有修改像素”）。函数只看 `row.degradation` 和 `fidelityAccepted`，没有读任何图像或特征。
- 状态：缺陷。
- 用户影响：规则推断被当作原因分析展示。例如 occlusion 负提升 9 条实际都是 `thin_stroke_nlm` 改了像素（`yuan_04` −1.82 dB、`qing_04` −2.50 dB），根子是算法在遮挡块外做了 NLM，而不只是“信息不可恢复”。
- 风险：失败分析失真，误导下一步算法方向。
- 修复路径：改名为“按退化类型的启发式归因（未经验证）”，并给每条附上实际决策链（`diagnosticsOperators`）和 Δ；或者做真实的分区误差分析（遮挡区内、遮挡区外、边缘区的 MAE）。
- 验收标准：UI 上“原因”字段标注证据等级；每条负提升都能链接到它的 operator 列表和 Δ 数值。

### E-05 【P1】“陷波不适用”时仍会改像素
- 位置：`algorithm_engine.py:179-206`（未检出峰时 mask 全是 1，仍然做 FFT→IFFT，第 206 行 `astype(np.uint8)` 直接截断而不是四舍五入）；`experiments/run_ablation.py:57-59`；UI 文案在 `ExperimentExplorer.tsx:37`。
- 实测：只读 cv2 读 PNG 计算：v2 批次 notch NA 104 行，平均绝对差 0.084（最大 0.176），平均有符号差 −0.084，约 8.4% 像素被减 1；v2-text 95 行，平均绝对差 0.161、有符号差 −0.161。NA 行 `outputSha256==degraded` 只有 6/104 和 0/95；heldout 47 行 NA 的 PSNR 与 degraded 相同的是 0/47。
- 状态：缺陷（数值影响小，但标签与事实不符）。
- 用户影响：“以原图计入”这句话不成立；notch 在非周期退化上的“负提升”（例如 heldout occlusion 14/14）有一部分来自截断偏差。
- 修复路径：未检出峰时直接 `return image.copy()`；或者统一用 `np.rint`；历史结果保持不动，在 registry 里注明这一点。
- 验收标准：新批次 NA 行 `outputSha256 == inputSha256` 达到 100%；单元测试覆盖。

### E-06 【P1】各批次口径不一致，跨批次均值会被误读
- 位置：`experiments/run_ablation.py:122`（2026-10-15 汇总排除 NA）与 `run_v2.py:72`（v2 汇总包含 NA）；`compare_v21.py:146-158`（没有 split，也没有 CI）；`experiment_registry.py:39`（只有 2026-10-15 有 historicalWarning）；`ExperimentExplorer.tsx:16`（前端按全部行重新算）。
- 实测：2026-10-15 notch 的 `summary.csv` 是 `n=2, psnrMean=41.364`，Explorer 式全行平均是 `n=10, 27.813`；同一页的导出文件和表格数字对不上。v2 与 v2-text 的 test adaptive 分别是 25.350 和 26.798，两批是不同采样协议、不同文物（README 自己写了“不能称为迭代提升”），但 UI 没有警告。heldout 的 v2.1 全样本 28.981 dB 与 v2-text 的 26.798 dB 是不同文物、不同强度、不同裁切的数字。
- 状态：缺陷。
- 用户影响：切换批次时数字可以被直接拿来比较，很容易读成“算法进步了”。
- 修复路径：registry 给每个批次加 `protocolId`（采样规则、强度、裁切规则、NA 口径），不同 protocol 的批次在 UI 上禁止放进同一张图比较，或强制显示警告；汇总统一在后端用同一个函数算，前端不再自己算。
- 验收标准：Explorer 表格数字与导出的 summary 一致，或者明确标注口径差异；跨 protocol 比较时出现警告。

### E-07 【P1】Explorer 的 dev/test 过滤与默认批次问题
- 位置：`ExperimentExplorer.tsx:10`（默认 `split='test'`）、`:12`（默认选 `items.at(-1)`）、`:15`（`!r.split` 时直接放行）、`:37`（文案“按文物聚类的95%置信区间见导出summary”）。
- 实测：GET `/api/experiments` 的顺序是 `[2026-10-15, v2, v2-text, heldout]`，默认打开 heldout（`metricsOnly: True`）。heldout 和 2026-10-15 的行都没有 `split` 字段，在“test”过滤下会显示全部行。heldout 的 summary 字段里没有任何 CI95（字段：method, degradation, n, failed, *Mean, negativeLift*, fidelityRejected）。
- 状态：缺陷。
- 用户影响：界面写着“数据分组：test”，实际显示的是没有划分的数据；CI 的说法对默认批次不成立。
- 修复路径：没有 split 的批次把分组选择器禁用，并显示“本批未划分”；默认批次选“有图像、有划分”的最新批次，或者由用户明确选择；文案按批次能力动态生成。
- 验收标准：选 heldout 或 2026-10-15 时分组控件显示“未划分”；CI 文案只在 summary 有 CI 时出现。

### E-08 【P1】heldout 批次没有任何图像
- 位置：`experiments/compare_v21.py:85-173`（全程没有 imwrite）；`experiment_registry.py:11, 28-35`（`METRICS_NOTE='本批次已保留真实数值，部分图像对比不可用'`）。
- 实测：`git ls-files experiments/results/2026-10-18-v21-heldout` 只有 1 个文件（results.json）；rows 里没有 input、reference、output 字段。
- 状态：未实现。文案“部分不可用”应该是“全部不可用”。
- 用户影响：v2.0/v2.1 对比没有任何三联图、差分图或失败案例图。
- 修复路径：在独立目录按记录的种子、裁切和代码重跑，生成图像和 SHA（v2.0 需要从 `f97ffab` 取源码快照），新目录登记成新批次，原批次不改；在此之前文案改成“本批次只有数值，没有图像”。
- 验收标准：新批次每行都有 input、reference、output 及 SHA，并且数值与原批次逐条一致（像 replay-validation.json 那样记录）。

### E-09 【P1】v2.2 候选门控按模拟器定制（基准过拟合风险）
- 位置：`degradation_analysis.py:199-240`（`interior_constant_block` 只匹配方差<1e-6 的常数块，这正是 `run_v2.py:60-62` 遮挡的生成方式）；`experiments/results/2026-10-18-synthetic-v22-summary.json` 的 `seenOcclusionGate`（“在已经用过的 14 件留出裁切上 … 14/14 会触发”）。
- 实测：读 JSON：rows 6 条，都来自一张程序生成图；`resultNote` 写“v2.2 没有额外提高 PSNR，默认仍是 v2.1”。`AdaptiveRubbingRestorerV22` 没有出现在生产路径（`algorithm_engine.py:365` 用的是 `AdaptiveRubbingRestorer`）。
- 状态：缺陷（风险）。当前没有进入生产，文档也如实写了。
- 用户影响：目前没有直接影响。如果以后被提升为默认版本，会形成“针对模拟器的作弊式门控”。
- 修复路径：遮挡模拟改成带纹理或带噪声的填充（不再是精确常数），v2.2 在新的未见文物上评测；Phase 1 报告里把它放在“候选/未采用”分区。
- 验收标准：任何门控在新遮挡模拟器下仍然报告真实触发率；不在已见数据上宣称有效。

### E-10 【P1】单次运行记录的参数不等于实际生效的参数
- 位置：`algorithm_engine.py:365`（adaptive 模式：`strength=max(.1,nlm_h/10)`、`notch_width=max(.5,d0/60)`；`filter_order`、`clahe_clip`、`morph_kernel` 被忽略）；`museum_processing.py:60`（`algorithmParameters=req.model_dump(...)` 记录的是原始请求）。
- 实测：代码阅读。processing.json 的 `algorithmParameters` 里有 d0、h_nlm、clahe_clip 等字段，生效值只能从 `adaptiveDiagnostics.decisions[*].h/width` 间接看出来。
- 状态：缺陷。
- 用户影响：报告上的“参数”与实际算法不对应，复现时会用错参数。
- 修复路径：processing.json 加 `effectiveParameters`（strength、notch_width 及各算子的实际 h），把被忽略的参数标为 `ignoredInAdaptiveMode`。
- 验收标准：报告页参数区分“请求参数”和“生效参数”；按生效参数重跑可以得到相同的输出 SHA。

### E-11 【P2】可复现溯源有缺口
- 位置：`experiments/results/2026-10-17-v2*/results.json` 的 `environment`；`compare_v21.py:35-43, 163, 170`；`.gitignore:64, 79`。
- 实测：v2 与 v2-text 的 `gitSha` 都是 `a7a6cb0`，但 `codeSha256['algorithm_engine.py']` 分别是 `0ce77c1e…` 和 `4790aced…`（`diff` 只差 2000 万像素上限检查那 2 行），说明运行时工作区不干净；好在两批都有 `source_snapshot/`，且 `replay-validation.json` 记录 1260 行 0 不一致。heldout 没有 codeSha256 和源码快照，`candidateCommit` 是合并提交 `4d96e8e`，v2.0 是运行时用 `git show f97ffab:degradation_analysis.py` 写到 `data/runtime/` 再加载的。`git check-ignore` 显示 `static/results/`、`data/runtime/`、`*.db` 都被忽略，24 次单次运行和推演记录只在本机。
- 状态：缺陷。
- 修复路径：实验脚本在工作区不干净时拒绝运行，或强制记录 diff；heldout 补一份源码 SHA 说明（只追加）；Phase 1 的“可复现性”层把单次运行标为“本机记录，不随仓库分发”。
- 验收标准：每个批次都有 codeSha256 和快照；UI 能显示“工作区是否干净”。

### E-12 【P1】残字评测链路未打通，schema 不一致
- 位置：`data/catalog/glyph-benchmark-v2.json:5`（`humanVerified`、split 字段）+ `experiments/evaluate_glyphs.py:25`（split 取值 `reference/test`）与 `glyph_annotations.py:14-15, 106-107`（`reviewStatus='human_verified'`、split 取值 `train/test`）；`main.py:279-286`（`/api/glyph-evaluation` 只调 `glyph_annotations.evaluate()`，不传 predictions）；`glyph_annotations.py:120-131`（要求 `annotationId` 对上，而推演记录 `glyph_inference.py:246-258` 没有 annotationId 字段）；`ReportsPage.tsx:110` 把“古碑 OCR 准确率：未评测”写成了固定文字。
- 实测：GET `/api/glyph-evaluation` 返回 `status not_evaluated, top1 None, verifiedLabels 0, recordedLabels 0`；SQLite 只读：`glyph_templates` 0 条，没有 `annotations.jsonl`，也没有 `data/catalog/glyph-annotations/`。
- 状态：未实现。当前“未评测”是正确的，但即使将来有了真值，这条链路也算不出数字，两套 schema 还可能各算出不同结果。
- 修复路径：统一一份 schema（建议以 glyph-benchmark-v2 的 requiredFields 为准，再加 reviewStatus），只保留一条评测入口；推演记录关联 annotationId；报告页从 API 读状态，不写死文字。
- 验收标准：用合成的“链路测试”标注（明确标注“不计入准确率”）跑通 Top-1、Top-3、拒识的计算；真实状态在 API 和 UI 上一致。

### E-13 【P2】候选来源的风险
- 位置：`glyph_inference.py:24-30`（5 条写死的上下文规则，例如“慶歸法→胤”）、`:190-198`；`:278-296`（模板检索不排除同一文物或同一个 crop）。
- 实测：SQLite 只读，11 条推演：来源都是 `unavailable`，0 条有候选，0 条被采纳，9 条带 visualAnalysis，拒识 0 条；`/api/glyph-evaluation` 显示 0 标注。规则候选在代码里写了 `visualEvidence='规则未分析图像笔画'`、`scoreBasis='上下文规则排序，非概率'`（已验证有披露）。
- 状态：缺陷（风险）。目前没有造成错误展示。
- 修复路径：规则表移到带来源引用的数据文件里，UI 标“规则建议”；模板检索加 `excludeSteleId` 选项，评测模式下强制按文物隔离。
- 验收标准：评测模式下检索不会返回同一文物的模板；规则候选在 UI 上和图像证据分开展示。

### E-14 【P2】指标定义与“真值”的性质（已验证，需在报告中披露）
- 位置：`algorithm_engine.py:106-116`（PSNR 峰值 255，SSIM 用 skimage，`data_range=255`）；`run_v2.py:113-114`、`compare_v21.py:67-77`（edgeF1 = Canny(80,160) 边缘图的 Dice，不带位置容差；thinStrokeMae = 参考图 Canny 像素上的 MAE）；`data/catalog/processing/han_03_liqi.json`（阅读图做过灰度化+全局自动对比度混合（blend 0.1）、等比缩放 0.5055、存成 JPEG）。
- 实测：上述字段已读取。所有批次的“参考”都是阅读图的 256×256 局部（run_v2.py:95），各批 `referenceNote` 和 `pairedReference` 都写明“不是原石真值”。
- 状态：已验证（定义清楚，局限已披露）。
- 风险：参考图本身带石花和 JPEG 块效应；edgeF1 对 1 像素偏移很敏感。
- 修复路径：Phase 1 的“指标定义”卡片逐条列出这些定义和局限；考虑加一个带容差的边缘 F1（例如 2 像素）作为补充。
- 验收标准：报告页每个指标都有定义和真值来源说明。

### E-15 【P2】没有在无配对参考的情况下报告 PSNR/SSIM（已验证）
- 位置：`museum_processing.py:48, 57, 62`（`METRIC_KEYS` 全是 None，`evaluationStatus='unassessed'`，`evaluationMetrics={'psnr':None,'ssim':None}`）；`algorithm_engine.py:385-388`（只有传入 reference 才算，而 ProcessRequest 不传）；`ReportsPage.tsx:96-97`（只有 `paired_reference` 时才显示）；`catalog_assessment.py:196`、`AssessmentViewer.tsx:166`（“PSNR、SSIM 不报告”）。
- 实测：GET `/api/steles`：31 条记录的 `metrics` 没有一个非空值；28 份 assessments 的 `evaluationStatus` 都是“未评测”；report API 的 `metrics` 全是 None。
- 注意：`apps/web/src/data/graphSelection.ts:19` 给不在记录里的核心样本兜底时写的是 `metrics: {psnr: 0, …, character_accuracy: 0}`，用 0 而不是 null。实测 API 不返回 `wei-yuanhuai`、`wei-jianyi`，所以兜底会被触发；它只用在图谱页头部的列表（`App.tsx:47-49`），是否会在某处渲染成“PSNR: 0 dB”待核。工作台 `WorkbenchPage.tsx:491-507` 在空值时会拼出“未评测 dB”“(+未评测dB)”“未评测%”。
- 状态：已验证；有 1 个潜在隐患。
- 修复路径：0 改成 null；空值时不拼单位。
- 验收标准：全前端 grep 不再有 `psnr: 0` 之类的兜底；空值显示不带单位。

### E-16 【P2】Top-1/Top-3/拒识率保持“未评测”（已验证）
- 位置：`experiments/results/glyph-v2-evaluation.json`（`status not_evaluated, n 0`）；`experiments/results/2026-10-18-rapidocr-probe/result.json`（`countsAsAccuracy:false`，并注明“输出不能当作释文”）；`glyph_annotations.py:110-118`。
- 实测：见 E-12 的 API 和 SQLite 输出。RapidOCR 在曹全碑局部上输出“雨親民廣振王未”等字符串，文件里标为“未与释文核对”。
- 状态：已验证。
- 修复路径：保持现状；Phase 1 研究总览把这一项显示为“未评测”，并写明原因（0 条人工核验标注）。
- 验收标准：UI 上 Top-k 和拒识率显示“未评测”，并且来自 API 字段。

### E-17 【P2】报告数字的溯源链路（已验证）与硬编码清单
- 链路：
  - HeldoutComparison：`fetch /api/experiments/heldout-v20-v21-2026-10-18`（第 38 行）→ `main.py:170-175` → `experiment_registry.batch()`（第 52-61 行）→ `experiments/results/2026-10-18-v21-heldout/results.json` 的 `summary[*]`（method, degradation, n, failed, psnrMean, ssimMean, edgeF1Mean, thinStrokeMaeMean, processingMsMean, negativeLiftCount）以及 `registry.sampleCount/rowCount`。诊断：第 37 行 → `main.py:187-192` → `restoration_diagnosis.diagnose()` → 同一个 results.json 的 rows。
  - ExperimentExplorer：`/api/experiments`（第 12 行）→ `batches()`；`/api/experiments/{id}`（第 14 行）→ `rows[*]`（psnr, ssim, edgeF1, processingMs, applicability, split, seed, input, reference, output）。表格里的均值和标准差是**前端现算的**（第 16 行），不是读 summary；图片 `/assets/{filename}`（第 18 行）→ `experiment_registry.asset()` 校验 SHA；导出（第 42 行）→ `export_payload()` 直接返回原始文件字节。
  - ReportsPage：`/api/steles/{id}/runs`、`/report`（第 19、26 行）→ `main.py:371-390` → `static/results/{id}/{runId}/processing.json`。
- 实测复算（python 只读）：heldout 42 行 summary 按 rows 重算 n、failed、各项均值、negativeLiftCount、fidelityRejected，**0 处不一致**；v2 和 v2-text 各 18 行 summary（n、psnrMean、psnrStd、applicableN、artifactN）**0 处不一致**；results.csv 与 results.json 1260 行 × 2 批 0 处不一致，summary.csv 与 JSON 也 0 处不一致；影像 SHA：2026-10-15 有 80 个、v2 有 1414 个、v2-text 有 1414 个登记文件，**缺失 0、SHA 不符 0**；GET 一张资产图返回 200。UI 显示的 v2.0 负提升 15/70、v2.1 16/70、occlusion 两版都是 9/14，与文件一致。
- 硬编码：`HeldoutComparison.tsx:24`（METHODS）、`:37-38, 64`（实验 ID）、`:25-26`（退化标签）；`ExperimentExplorer.tsx:23`（“28件”）、`:33`（分组选项）、`:37`（口径文案）；`ReportsPage.tsx:110`（OCR 状态文字）；`restoration_diagnosis.py:8, 58`（caveat、“14 件”）；`experiment_registry.py:39`（historicalWarning 只对 2026-10-15）。没有发现硬编码的指标数值。
- 状态：已验证。
- 修复路径：Phase 1 把实验 ID 和方法列表改为从 registry 读取；汇总统一用后端结果（见 E-06）。
- 验收标准：页面上每个数字旁边都能导出对应的文件路径和字段（tooltip 或“来源”链接）。

### E-18 【P1】机制层可视化缺数据
- 位置：`experiments/run_ablation.py:58-59`（固定陷波的 `details.detectedPairs` 被丢掉）；`run_v2.py:111-117`（只存输出图）；`compare_v21.py:141`（只存 operator 名称）；`museum_processing.py:37`（单次运行存 original、restored、frequency_spectrum、character_skeleton、binary_skeleton、contour、cinnabar_rubbing）；`glyph_inference.py:263-266`（残字选区存 gray、foreground、skeleton、noise）。
- 实测：v2 和 v2-text 的 adaptive 行里有 `diagnostics.features.periodicPeaks[*].positions`（各 21/140 行非空，例如 `[[128,96],[128,160]]`）、`decisions`、`fidelityGate`（accepted, strongEdgeRetention, meanAbsoluteChange, contrastRatio, reasons）；实验批次里**没有**频谱图、差分图、二值前景、骨架、边缘图。单次运行的 12 个自适应目录里都有 frequency_spectrum、binary_skeleton、contour 的 PNG（只在本机，gitignore）；注意 adaptive 模式下的频谱是**输入图**的频谱（`algorithm_engine.py:366`），不是陷波后的频谱。
- 状态：未实现（部分）。
- 修复路径：差分热图可以直接从已有的 reference、input、output PNG 现算（不需要新实验）；频谱和陷波 mask 要么前端从 input PNG 现算，要么新开一批把 mask 存下来；二值前景、边缘在实验层要新生成。
- 验收标准：每张机制图都标明“由哪个文件、哪个函数在何时生成”；没有数据的阶段显示“未记录”，不用示意图代替。

### E-19 【P2】批次内 dev/test 划分（已验证）与统计效力
- 位置：`run_v2.py:33-38`（每朝代第 1 件做 development、第 2 件做 test）；`config-v2-text.json`（第 3 件 / 第 4 件）；`run_v2.py:67-82`（按文物 bootstrap 1000 次）；`ExperimentExplorer.tsx:16`（标准差没按文物聚类）。
- 实测：两批 split 各 630/630 行；`sources` 中 dev 和 test 的文物 ID 不相交；每组 `artifactN=7`。CI 示例：v2-text test adaptive_joint 的 psnrCI95 是 `[24.70, 29.26]`。
- 状态：已验证（批次内没有泄漏）；跨批次泄漏见 E-01。
- 风险：7 件文物的 bootstrap 区间不稳定；同一件文物的 10 个输入不独立。
- 修复路径：UI 显示 artifactN 和聚类 CI，不显示逐记录标准差，或明确标注它的含义。
- 验收标准：每个均值旁边都有 n（输入数）/ k（文物数）/ 聚类 CI。

### E-20 【P2】28 件归档评估的“处理”大多接近原图
- 位置：`data/catalog/assessments/*.json`；`catalog_assessment.py:155, 192-193`；`AssessmentViewer.tsx:110`。
- 实测：python 只读：28 件都是 `assessmentStatus: processed`；其中 7 件 `inputImageSha256==outputImageSha256`（决策链 `skip_notch, identity`），UI 会显示“像素没有发生变化”（已验证）；另外 21 件 `meanAbsoluteChange` 在 0.002 到 1.309 之间（例如 qing_01 0.002、song_03 0.004、yuan_01 1.309）。决策链：thin_stroke_nlm 12 件、identity 7 件、impulse+thin_stroke_nlm 6 件、nlm 3 件。
- 状态：缺陷（轻度）。
- 修复路径：显示 MAC 和改动像素比例；低于阈值时提示“改动极小，肉眼通常不可见”。
- 验收标准：评估卡片显示改动量。

### E-21 【P2】同一文物两个 ID，运行记录被拆开
- 位置：`apps/web/src/data/graphSelection.ts:3-4`（`tang-duobao`↔`tang_01_duobao`）；`static/results/tang-duobao/`（4 个）与 `static/results/tang_01_duobao/`（10 个）。
- 实测：见 E-03 的目录统计。
- 状态：缺陷。属于 F 专题（多页面共享同一文物），需要交架构/后端 Agent。
- 修复路径：建无损别名映射，报告页按规范 ID 汇总运行；不迁移文件。
- 验收标准：两个 ID 打开的报告页显示同一组运行。

### E-22 【P2】报告页的推演过滤
- 位置：`main.py:380`（`item.get('runId')==selected['runId']`）。
- 实测：代码阅读。基于原图的推演 `runId=None`，选中任何一次运行时都会被隐藏；不选运行时又显示全部。
- 修复路径：分成两组展示：“本运行的推演”和“基于原图的推演”。
- 验收标准：两类推演都能在报告里看到，并有标注。

### E-23 【P2】PDF 不含全局评测
- 位置：`HeldoutComparison.tsx:51`、`ExperimentExplorer.tsx:21`（`print:hidden`）；`ReportsPage.tsx:65`（`window.print()`）。
- 实测：代码阅读，没有生成 PDF 验证（本阶段不启动前端，待核）。
- 修复路径：Phase 1 按 BRIEF 做 PDF 版式（A4 纵版，包含当前选择的批次和方法、图题、来源与局限）。
- 验收标准：PDF 中包含当前选择的实验 ID、样本数、局限说明。

### E-24 【P2】可视化表达问题
- 位置：`HeldoutComparison.tsx:46, 63`（`max` 用绝对值，条宽从 0 起算；thinStrokeMae 和耗时是越小越好，却与 PSNR 用同一种条，不标方向）；`ExperimentExplorer.tsx:20, 36`。
- 状态：缺陷（轻度）。坐标从 0 开始，没有截断（已验证）。
- 修复路径：Phase 1 改用 ECharts，不同量纲分轴，标注指标方向，相对输入的 Δ 用正负双向条。
- 验收标准：每张图都有指标方向说明，零轴可见。

### E-25 【P2】失败与负提升都保留着（已验证）
- 位置：`run_v2.py:72, 86, 118-120`（保留出错行和 NA，拒绝覆盖已有目录）；`compare_v21.py:86-87, 125-129`；`experiments/README.md`。
- 实测：v2、v2-text、heldout 的 `error` 非空行都是 0（没有运行失败）；负提升行全部保留：v2 adaptive_joint dev 14 / test 18，v2-text dev 17 / test 16，heldout v2.1 16/70；`error-analysis.md` 和 `by-degradation.csv` 列出了 worseThanInputN；2026-10-15 的标签泄漏批次保留，并带 historicalWarning；`performance-invalid-memory-probe.json` 作为无效探针保留。
- 状态：已验证。
- 修复路径：Phase 1 的“失败案例”入口直接读这些行。
- 验收标准：失败入口里的条数与文件里的条数一致。

---

## 3. Phase 1 报告重构可用的真实数据清单

图例：配对参考 = 有受控退化前的局部图（不是原石真值）；真值 = 独立人工标注。

| # | 文件路径 | 关键字段 | 样本数 | 真值/配对参考 | 可支撑的可视化层 | 备注 |
|---|---|---|---|---|---|---|
| D1 | `experiments/results/2026-10-17-v2/results.json`（以及同目录的 results.csv、summary.csv） | rows：sampleId, dynasty, split, caseId, degradation, strength, seed, degradationParameters, method, applicability, psnr, ssim, edgeF1, processingMs, error, reference/input/output 及其 Sha256, algorithmVersion, diagnostics{features.periodicPeaks, decisions, fidelityGate, selectedOutput}；summary：split×method 的 n, applicableN, artifactN, *Mean, *Std, *CI95 | 14 件文物（dev 7 / test 7），140 个输入，1260 行，9 种方法 | 有配对参考（中心 256 局部）；无真值 | L1 总览（区分 dev/test）；L2 三联图（1414 张 PNG，SHA 0 不符）+ 由 PNG 现算差分图；L3 横向比较（含 CI）；L4 门控决策、周期峰位置（21/140 行）；L5 负提升行 | 有 5 个中心区域落在纸边（README）；adaptive 55/140 原样返回（E-02） |
| D2 | `experiments/results/2026-10-17-v2/{by-degradation.csv, error-analysis.md, historical-by-degradation.json, replay-validation.json, performance.json, source_snapshot/}` | deltaPSNRvsInput, deltaPSNRClusterCI95, worseThanInputN；重跑 1260 行 0 不一致；峰值 RSS | 同 D1 | 同 D1 | L3 相对输入 Δ 与聚类 CI；L5；L6 可复现性 | performance-invalid-memory-probe.json 是无效探针，只作记录 |
| D3 | `experiments/results/2026-10-17-v2-text/`（结构同 D1+D2，另有 samplingDiagnostics 和 algorithmParameters） | 同 D1；sources[*].samplingDiagnostics（eligibleRegionCount, dynamicP90P10 等）；config.algorithmParameters | 14 件（03/04 号），140 个输入，1260 行 | 有配对参考（按字迹阈值抽样的局部）；无真值 | L1–L6，同 D1；L6 可以展示抽样规则和例外（song_03_daguan） | 这 14 件同时被 heldout 使用（E-01）；原样返回 45/140 |
| D4 | `experiments/results/2026-10-18-v21-heldout/results.json` | rows：sampleId, degradation, method, inputPsnr, inputSsim, psnrDeltaFromInput, negativeLift, fidelityAccepted, diagnosticsOperators, psnr, ssim, edgeF1, thinStrokeMae；summary：method×degradation | 14 件，70 个输入，490 行，7 种方法 | 有配对参考；无真值；**不是留出集** | L3 v2.0/v2.1 配对 Δ（同一输入）；L5 负提升 16 条和原样返回 21 条；**没有图像** | 必须改名（E-01）；没有 split，没有 CI |
| D5 | `experiments/results/2026-10-15/results.json`、results.csv、summary.csv | rows：sampleId, degradation, seed, method, applicability, psnr, ssim, edgeF1, output(+Sha256)；summary 口径排除 NA | 2 件，10 个输入，80 行 | 有配对参考 | 只放 L5/L6“历史记录”；有 80 张输出、2 张参考图、10 张对比图 | joint 用了退化标签（先验泄漏），只能作为历史展示，不进入横向比较 |
| D6 | `experiments/results/*/comparison_*.jpg` | 拼图：reference、input + 各方法输出 | v2 140 张、v2-text 140 张、2026-10-15 10 张 | 同所属批次 | L2 的快速浏览图（同步缩放应改用单张 PNG） | 是 JPEG 压缩后的拼图，不适合像素级差分 |
| D7 | `experiments/results/2026-10-18-synthetic-v22-summary.json` | rows：degradation, method, version, selectedOutput, operators, inputPsnr, psnr, ssim, negativeLift, unchanged | 1 张生成图 × 3 种退化 × 2 版本 = 6 行 | 参考是生成图 | 只放 L4/L5“候选未采用”；不进入总览 | 参见 E-09 |
| D8 | `experiments/results/glyph-v2-evaluation.json`、`data/catalog/glyph-benchmark-v2.json`、`GET /api/glyph-evaluation` | status, n, top1, top3, rejectionRate, reason；verifiedLabels, recordedLabels | 0 条标注 | 无真值 | L1 显示“未评测”及原因 | 两套 schema 待统一（E-12） |
| D9 | `experiments/results/2026-10-18-rapidocr-probe/result.json` | engine, countsAsAccuracy:false, rubbingCrop.texts[*].text/score, limitation | 1 个局部 + 1 个印刷体“十” | 无真值 | L5“基线探针（不计准确率）” | 不能显示为释文 |
| D10 | `data/catalog/assessments/{id}.json` 以及 inputs/、outputs/、regions/ 下的 PNG | runId, sourceImageSha256, cropBox, algorithmVersion, adaptiveDecisions, fidelityGate, input/outputImageSha256, readableMetrics, archiveMetrics, gradeReasons, evaluationStatus | 28 件，每件 1 个 512×512 中心 ROI | 无配对参考（不报 PSNR） | 单次文物层：处理前后对照、门控决策、改动量；**不进全局评测** | 7 件原样返回，21 件改动 ≤1.31 灰度级（E-20） |
| D11 | `static/results/{steleId}/{runId}/processing.json` 及各 PNG（本机，gitignore） | runId, algorithmVersion, algorithmParameters, inputImageSha256, outputSha256{role}, adaptiveDiagnostics{features, decisions, fidelityGate, selectedOutput}, workingImage, diagnosticMetrics；PNG：original, restored, frequency_spectrum, character_skeleton, binary_skeleton, contour, cinnabar_rubbing | 24 个目录（自适应 12 个，其中 10 个像素没变；固定频域 3 个；旧版 9 个） | 无配对参考 | 单次文物层的骨架、边缘、频谱（输入的）、门控；**不随仓库分发** | E-03、E-10、E-21 |
| D12 | SQLite `data/rubbingmind.sqlite` 的 `glyph_inferences`、`glyph_templates`；`data/runtime/glyph-inferences/*_{gray,foreground,skeleton,noise}.png` | inferenceId, steleId, runId, bbox, roi, imageProvenance, cropSha256, source, candidates, status, decisions, visualAnalysis | 11 条推演（0 候选，0 采纳），0 个模板 | 无真值 | 残字层（Phase 2）：选区的二值前景、骨架、噪声；人工驳回记录 | 只在本机 |
| D13 | `data/catalog/processing/{id}.json`（28 个） | readable_bbox, isotropic_scale_factor, contrast{method, blend, cutoff}, sharpen, output_sha256{readable, archive, cover}, source_sha256 | 28 件 | 不适用 | L6：说明配对参考图本身是怎么做出来的 | 参见 E-14 |

各可视化层的数据可得性：

| 可视化 | 有真实数据可用？ | 来源 |
|---|---|---|
| 三联对照（参考/退化/输出） | 有：D1、D3（各 1414 张带 SHA 的 PNG）；D5 只有输出和参考，没有逐行 input 字段；**D4 没有** | `/api/experiments/{id}/assets/{file}` |
| 差分热图 | 原始数据有（由 reference、input、output 现算），目前没有生成好的文件 | D1、D3 |
| 频谱 | 实验层没有落盘，可以从 input PNG 现算；单次运行有输入图的频谱 PNG（D11） | D1、D3、D11 |
| 周期峰 / 陷波位置 | 自适应：有（features.periodicPeaks.positions，v2 和 v2-text 各 21 行）；固定陷波：没有（detectedPairs 被丢掉）；heldout：只有 operator 名称 | D1、D3 |
| 二值前景 | 实验层：没有；残字选区：有（D12，只在本机） | D12 |
| 骨架 | 单次运行：有（binary_skeleton，D11）；残字选区：有（D12）；实验层：没有 | D11、D12 |
| 边缘 | 单次运行：有（contour = Canny 50/150）；实验层：没有边缘图，只有 edgeF1 数值 | D11 |
| 门控决策 | 有：D1、D3（decisions + fidelityGate）、D10、D11；D4 只有 fidelityAccepted 和 operators | D1、D3、D4、D10、D11 |

## 4. 阻碍与未能核实的项
- v2.1 的修改是否“直接依据 v2-text 测试组数值”：只能证明时间先后和改动目标一致，因果关系待核（E-01）。
- `graphSelection.ts` 的 0 值兜底是否真的渲染成“PSNR: 0 dB”：没有启动前端，待核（E-15）。
- PDF 实际版式：没有生成 PDF，待核（E-23）。
- 本阶段没有运行 pytest 或任何实验脚本（实验脚本会写 experiments/ 或 data/runtime/，这是被禁止的）；所有数值都来自对已有文件的只读复算。

## 勘误 / 口径补充：E-02 原图返回数（追加）

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-19 12:50（Asia/Shanghai）
- 依据：`experiments/results/<批次>/derived/applied_status.json`（`experiments/derive_applied_status.py`，判据 `pixel-equal-v1`），分支 `agent/eval-sci`
- 本节只补充口径，不改前文结论。E-02 的结论（实验层没有区分原图返回与实际处理）和其中的数字都成立。

E-02 写的“55 / 45”只统计 `adaptive_joint`；`REPORT_DATA_SPEC.md` §1(b) 写的“65 / 47”是 8 个方法（degraded 基线除外）的合计。两处口径不同，数字都对。按方法拆分如下（每格分母 70 行）：

| 批次 | 方法 | development | test | 合计 |
|---|---|---|---|---|
| 2026-10-17-v2 | adaptive_joint | 24 | 31 | 55 / 140 |
| 2026-10-17-v2 | fast_nlm | 3 | 1 | 4 / 140 |
| 2026-10-17-v2 | notch（均为 `passthrough_not_applicable`） | 0 | 6 | 6 / 140 |
| 2026-10-17-v2 | 其余 5 个方法 | 0 | 0 | 0 / 700 |
| 2026-10-17-v2 | 合计 | 27 | 38 | 65 / 1120 |
| 2026-10-17-v2-text | adaptive_joint | 22 | 23 | 45 / 140 |
| 2026-10-17-v2-text | fast_nlm | 2 | 0 | 2 / 140 |
| 2026-10-17-v2-text | notch | 0 | 0 | 0 / 140 |
| 2026-10-17-v2-text | 其余 5 个方法 | 0 | 0 | 0 / 700 |
| 2026-10-17-v2-text | 合计 | 24 | 23 | 47 / 1120 |

- “其余 5 个方法”指 gaussian_lowpass、butterworth_lowpass、morphology、nlm_clahe、joint。
- notch 另有 98 行（v2）/ 95 行（v2-text）标为不适用但像素被改动，不计入原图返回。逐行核实全部是 E-05 的 1 级截断（差值只有 −1），见 SPEC §1(b)。
- E-02 验收标准中的“21（v2.1）”不是原图返回数：同批复测批次没有图像，像素判定全部是 undetermined，21 是指示量 `indicatorPsnrDeltaZeroN`（ΔPSNR 恰为 0 的行数）。按 SPEC §1(a)，报告不得把它显示为原图返回数或原图返回率。
- 同一张表已写入 `REPORT_DATA_SPEC.md` §1(b)，两处数字一致。

## 勘误 / 口径补充：E-03 中 644816 像素的来源（追加）

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-19 13:00（Asia/Shanghai）
- 本节只补充来源和修正值，不改前文。E-03 的结论（单次处理报告把未改动的原图展示成“本次算法输出”）成立。
- 对象：`static/results/tang-duobao/20261018T072201_13772747/`（adaptive）。输入 `original.png`、输出 `restored.png` 的 SHA-256 都与 `processing.json.outputSha256` 一致。两张图都是 1472×1024×3、uint8，`workingImage.scale = 1.0`，没有缩放或裁切。`original.png` 是彩色（三个通道不相等）；`restored.png` 是灰度复制成三个相等的通道。

E-03 写的“644816 像素，MAC 0.274”，两个数来自两种不同的灰度读法：

| 口径 | 怎么算 | 改动像素 | 平均绝对差 | 最大差 |
|---|---|---|---|---|
| 全通道 `pixel-equal-v1`（现行判据） | `IMREAD_UNCHANGED` 解码，任一通道不同即算一个像素 | **1,507,328 / 1,507,328**（比例 1.0）；按元素计 3,214,171 / 4,521,984 | 3.409（按元素） | — |
| 灰度口径 `gray-bt601-pixel-equal-v1` | 两张图各自 `cv2.cvtColor(BGR2GRAY)` 后比较 | **2,719**（0.18%） | **0.274** | 156 |
| 解码器灰度 | 两张图都用 `cv2.imdecode(..., IMREAD_GRAYSCALE)` 读入后比较 | **644,816** | 0.700 | 156 |

- 结论：644816 可以用“`IMREAD_GRAYSCALE` 读两张图”逐位复现；0.274 可以用“`cvtColor` 灰度化”逐位复现。E-03 的这两个数分别来自这两种读法。OpenCV 解码器对彩色 PNG 的灰度转换与 `cvtColor` 的结果不同，仅 `original.png` 一张图上就有 642,097 个像素不一致；`restored.png` 三通道相等，两种读法结果相同。所以 644816 里绝大部分是读法差异，不是算法改动。当时的审计脚本没有留存，“分别用了哪种读法”是按复现结果推断的。
- 修正值：该运行按现行判据记 **1,507,328 像素（全图，比例 1.0），原因是彩色输入被灰度化**；灰度口径并列记 **2,719 像素，MAC 0.274**。644816 作废，不再引用。

**复核“12 次 adaptive 运行中 10 次改动为 0”（全通道 pixel-equal-v1）**：只读计算，读取前后 `static/results` 下 216 个文件哈希不变。

| 运行 | 次数 | 全通道改动像素 | 灰度口径 | 解码器灰度 |
|---|---|---|---|---|
| `tang_01_duobao`（10 次：20261017T095714 … 20261018T082526） | 10 | 0 / 1,598,565（每次） | 0 | 0 |
| `tang-duobao/20261018T072201_13772747` | 1 | 1,507,328 / 1,507,328 | 2,719 | 644,816 |
| `upload-cf737e88…/20261017T100420_297da746` | 1 | 25,600 / 25,600 | 24,222 | 24,368 |

- 结论仍然成立：全通道判据下仍是 10/12 次改动为 0。原因是 `tang_01_duobao` 的 `original.png` 三个通道本来就相等（灰度源图），灰度化不产生改动。另外 2 次在三种口径下都是“已改动”。
- 这 10 次在读取时按 SHA 校验后计算，`passthroughSource = computed-on-read`，`isPassthrough = true`（分支 `agent/eval-sci` 的 `museum_processing.read_run`）。
