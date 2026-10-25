# 审查：agent/eval-sci 对共享文件的改动（RM-架构后端）

- 时间：2026-10-19 12:55（Asia/Shanghai）；审查人：RM-架构后端
- 方式：只读。用 `git archive` / `git diff` 读取 `f21ceaa`、`7623a52`、`d222fbc`，没有合并、cherry-pick 或修改 agent/eval-sci。
- 范围：`degradation_analysis.py` 和 `museum_processing.py`（Green 指定）。另外列出 7623a52 中与本分支有重叠的 `restoration_diagnosis.py` 和 `algorithm_engine.py`。
- 事实：
  - `f21ceaa` 改了 `degradation_analysis.py`（+45）和 `museum_processing.py`（+60）；
  - `7623a52` **没有**改这两个文件（`git diff --stat 7623a52~1 7623a52` 只列出 `algorithm_engine.py`、`restoration_diagnosis.py`、`restoration_measures.py` 和测试）；
  - `d222fbc` 没有改 `.py` 文件（实验目录除外）。
- 对照本分支：`agent/arch-backend` 的 `53200d6`（原样搬入）和 `4379827`（按 Green 新裁定修改）。

## 结论

| 文件 / 提交 | 结论 |
|---|---|
| degradation_analysis.py `change_stats`（f21ceaa） | **修改后签字**：见 D-1 |
| degradation_analysis.py `AdaptiveRubbingRestorer.restore`（f21ceaa） | **签字**（算法域，属评测科学家），附 D-2、D-3 两条意见 |
| museum_processing.py（f21ceaa） | **不按原样签字**，以本分支 4379827 的实现为准，见 M-1 至 M-6 |
| restoration_diagnosis.py（7623a52） | **签字**，合并时按 X-1 处理 |
| algorithm_engine.py（7623a52，E-05） | **签字**，附 X-2 |

## 逐条意见

| 编号 | 位置 | 问题 | 风险 | 建议 / 本分支处理 |
|---|---|---|---|---|
| D-1 | `degradation_analysis.py` `change_stats`：`diff = np.abs(a.astype(np.int16) - b.astype(np.int16))` | 16 位 PNG（最大 65535）转 int16 会溢出 | 16 位输入的改动量和 maxAbsDiff 算错，甚至把有改动误判为 0 | 改为 `int32`。本分支 4379827 已改，并有 16 位用例测试 |
| D-2 | `restore()`：`selectedOutput='original' if change['isPassthrough'] else 'candidate'` | 门控接受、但输出恰好与输入相同时，selectedOutput 改为 original，语义发生变化 | 依赖 selectedOutput 的旧报告和导出含义会变 | 可以接受；请在 SPEC §9 写明 selectedOutput 的新含义（已部分写明） |
| D-3 | `restore()` 和 V22 分支：`outputMode` 取值 `gate_fallback_original`、`identity_no_evidence`、`processed` | 与运行级 `outputMode ∈ {processed, passthrough, undetermined}` 同名但取值不同 | 前端可能把两个层级的 outputMode 混用 | 建议实验侧改名为 `algorithmOutputMode`，或在 SPEC 中区分层级。本分支不动 |
| M-1 | `museum_processing.py` `RUN_PASSTHROUGH_CRITERION='working-gray-pixel-equal-v1'` 与 `_decode_gray()` | Green 裁定判据统一为 `pixel-equal-v1`：按原始分辨率、保留全部通道比较，不转灰度 | 两条分支判据不一致；灰度比较会漏掉只在单一通道上的改动 | 本分支 4379827 用 `IMREAD_UNCHANGED`，形状和位深都相同才逐值比较。SPEC v2 第 225 行仍写 working-gray，需要评测科学家同步修改 |
| M-2 | `run_change_status()` 无法判定时返回 `passthroughCriterion=RUN_PASSTHROUGH_CRITERION` | Green 裁定：无法判定时 criterion 和 source 都为 null | 前端会误以为“已按判据判定” | 本分支：全部字段 null，新增 `passthroughSource`，**不**新增 passthroughStatus 字段。SPEC 中没有 passthroughStatus，与裁定一致 |
| M-3 | `comparedImages={'before':…,'after':…}` | SPEC §8 规定是数组 `[string, string]` | 前端按数组解析会出错 | 本分支改为 `['original','restored']` |
| M-4 | `read_run` 补字段：`isPassthrough=None…passthroughCriterion=None` | Green 新裁定：旧运行在两张图的 SHA 都校验通过时，读取时计算；不回写 | 旧运行一律为 null，E-03 的 10 次运行无法显示“未修改” | 本分支 `computed_on_read_status()`：两张图都在、SHA-256 与记录一致才计算，`passthroughSource='computed-on-read'`；有缓存，不写文件。原实现还漏了 `totalPixelCount` 和 `meanAbsDiff`，已补全 |
| M-5 | `process_verified_request` 中 `out=BASE/'static/results'/…` | 与本分支 R1-7 的 `results_root()`（RUBBINGMIND_RESULTS_DIR）在同一行重叠 | 合并冲突 | 按本 ADR 的合并说明手工解决：保留 `results_root()` 和 `raw_images` |
| M-6 | eval-sci 测试 `tests/test_applied_status.py::_run_processing` 只 patch 了 `museum_processing.BASE` | 设置了 RUBBINGMIND_RESULTS_DIR 时，结果会写到重定向目录，测试找不到文件 | 合并后在隔离环境中测试失败 | 合并时在该测试中加 `monkeypatch.setattr(museum_processing,'RESULTS_DIR',None)`；同时把判据断言改为 `pixel-equal-v1`、comparedImages 改为数组 |
| M-7 | `effective_parameters()` | 没有问题 | — | 签字，已原样搬入 |
| X-1 | `restoration_diagnosis.py`（7623a52）：重写了 `diagnose()`，加入 measuredCauses 和 displayName | 本分支 c4（b5370d1）在同一文件**末尾追加** `diagnose_batch()` / `_case_key()`，没有改 `diagnose()` | 末尾相邻区块会产生文本冲突，但没有语义冲突 | 合并时同时保留 7623a52 的 `diagnose()` 和本分支追加的函数。本分支 main.py 返回 `{**diagnose(),'diagnosisVersion':'heldout-legacy-heuristic'}`，测试与 `diagnose()` 本身比较，合并后仍成立 |
| X-2 | `algorithm_engine.py`（7623a52）：notch 没有检出峰对时原样返回输入 | 行为变化：避免 FFT 往返加 uint8 截断造成的 −1 偏移 | 历史结果不可比 | 签字；需在新批次中体现（SPEC 已说明） |

## 实测补充（8710，DB 副本，2026-10-19 12:47–12:49）

本机 13 次 adaptive 运行，用 pixel-equal-v1（全通道）和旧的工作灰度判据对比：
- `tang_01_duobao` 的 10 次：两种判据都是 0 像素改动，读取时计算后为 passthrough，满足 E-03 验收。
- `tang-duobao/20261018T072201_13772747`：原图是彩色，输出是灰度复制成三通道。灰度判据下改动 2719 像素；全通道判据下 1,507,328 像素（比例 1.0），因为灰度化本身就计为改动。
- 一次上传运行的情况相同。
- **请 Green / 评测科学家确认**：彩色输入的灰度化是否应算作“改动”。按当前裁定是算的。
- 另外，E-03 记载该运行的改动量为 644816 像素，这与上面两种判据的结果都不一致，需要评测科学家核对当时的口径。


## Green 已采纳（2026-10-19 13:10 Asia/Shanghai）

- **degradation_analysis.change_stats**：本分支 int32 差值（D-1）已采纳；eval-sci 侧应删除重复实现，改调本分支。
- **museum_processing.run_change_status / effective_parameters / 灰度参考字段**：只保留本分支一份。评测科学家已停改该文件；定稿后把 `agent/arch-backend` merge 进 `agent/eval-sci`，冲突全取本分支。权威提交：`4379827`（pixel-equal-v1）及其后的灰度 / SPEC 对齐修订。
- **判据 (a)**：全通道 `pixel-equal-v1` 决定 isPassthrough；灰度口径仅并列显示，名称为 SPEC v3.1 的 `gray-bt601-pixel-equal-v1`。
- **M-5**：museum_processing 合并冲突按 ADR R2-6 手工解决；eval-sci 的 `253c5e9` 应改为调用本分支函数并删除自有副本。


## 对照 DA_DIFF_FOR_BACKEND.md（评测科学家，merge 前签字）

来源：`/workspace/rm-eval/docs/DA_DIFF_FOR_BACKEND.md`（`git diff agent/arch-backend agent/eval-sci -- degradation_analysis.py`；int32 已一致，不在 diff 内）。

| 改动 | 结论 |
|---|---|
| `restore()` 末尾 `changeStats=change_stats(image,result)` | **签字** |
| `selectedOutput = 'original' if isPassthrough else 'candidate'`（按像素是否相等，不再按门控是否接受） | **签字**（D-2） |
| 算法层原字段 `outputMode` ∈ {processed, identity_no_evidence, gate_fallback_original} | **有条件签字**：Green 定稿要求正式命名为 **`algorithmOutputMode`**；运行级保留 `outputMode`。请 eval-sci 在 merge 前改名；本分支 ADR R2-12 与合并说明写明，不大面积改 eval-sci 文件 |
| V22 平坦块早退同样带 `changeStats` + `selectedOutput` +（改名后的）`algorithmOutputMode='gate_fallback_original'` | **签字**（字段齐全前提下） |

Gray 判据最终名（Green）：`gray-bt601-pixel-equal-v1`。
