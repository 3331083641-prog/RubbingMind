# MECHANISM_HEAD_NOTE — 机制层 headCommit 与 tip 关系（红队条件）

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-25（Asia/Shanghai）
- 分支：`agent/eval-sci`
- 当前 tip（写入时）：9eb8406ba1a788a20dc88035fe2eef314afc7b9d（短写 9eb8406）。对齐 feature@c761d54（含 AB-8）后 ES-3/5 续做；NLD slim。若后续仅 docs stamp 提交，门禁以本 ES 交付 tip 或最新 HEAD 为准（见 REVIEW）。
- 机制产物绑定 headCommit：`7623a52a3299b7c948031dfa1f79f04b8eb66d9e`（短写 `7623a52`）
- 关联：`REPRESENTATIVE_CASES.md`、`REPORT_DATA_SPEC.md` §MEC / E-18、`experiments/mechanism_cases.py`

## 1. 红队条件（有条件可合并）

红队对 tip `65f7815` 结论为「有条件可合并」。条件之一：

> 现有真实 cv2 机制层产物（`derived/mechanism/`）绑定的 `headCommit` 仍是旧 tip `7623a52`，已落后于当前 tip。

本文档将该条件固化为评测与报告约束，**只改文档 / 脚本注释**；不删实验原始数据，不擅自重跑大批量 mechanism。

## 2. 事实核对（2026-10-25）

| 批次 | `derived/mechanism/index.json` → `headCommit` | `baseCommit` | 与 tip `65f7815` |
|---|---|---|---|
| `2026-10-17-v2` | `7623a52a3299b7c948031dfa1f79f04b8eb66d9e` | `f0c5886a9d4c8b47d64640e1f7eaeac44be3c388` | **落后** |
| `2026-10-17-v2-text` | `7623a52a3299b7c948031dfa1f79f04b8eb66d9e` | 同上 | **落后** |

生成脚本：`experiments/mechanism_cases.py`（只读历史批次，只写 `derived/mechanism/`）。说明见 `REPRESENTATIVE_CASES.md`。

### appliedStatusSha256（红队非阻断建议）

对上述两批核对：`derived/applied_status.json` 的 `sourceResultsSha256` **等于** 对应 `results.json` 的 SHA-256（v2：`dd565cee…fc06131`；v2-text：`d70a821c…0c641b`）。行级 `shaMatchesRecord` 抽样为 true。

**结论：appliedStatus 未过期，本期不重生 derived。** 若日后 tip 前移导致 `results.json` 变更或 SHA 失配，再按红队非阻断建议重生 `applied_status` 并在本文件追加记录。

## 3. 报告与对外表述禁令（在重跑 mechanism 之前）

在 `derived/mechanism/index.json` 的 `headCommit` 更新为与当前 tip（或声明的 replay 提交）一致之前：

1. **不得**把机制 PNG / `mechanism.json` 宣称为「与当前 tip 字节一致」或「在 tip `65f7815`（或更新 tip）上重算」。
2. 允许表述：「机制图在 headCommit=`7623a52` 上由 `mechanism_cases.py` 生成；当前 tip 已前移，机制层尚未重跑。」
3. 前端 / 报告页若展示机制图，须保留「v2.1（head 重算）」标签中的 **head 含义 = 生成时 headCommit**，并链到本文或 `REPRESENTATIVE_CASES.md` 本节，避免读者误以为 head = 仓库 tip。
4. 合并或 tip 前移后：**必须**重跑 mechanism（两批），更新 `index.json` 的 `headCommit` / `environment`，再解除上述禁令。

## 4. 重跑门槛（本期不做）

- 重跑需可复现环境（Python / numpy / OpenCV / scipy / scikit-image 与 `index.json` → `environment` 对齐）。
- 只写 `derived/mechanism/`；不得改 `results.json`、不得删原始实验产物。
- 重跑完成后：更新本文件「事实核对」表、`REPRESENTATIVE_CASES.md` 文首 head、SPEC §MEC 交叉引用；可选再跑 pytest 相关只读服务测试。

## 5. 脚本注释

`experiments/mechanism_cases.py` 模块文档字符串已注明：产物 `headCommit` 以各批 `derived/mechanism/index.json` 为准；若落后于分支 tip，报告不得声称与 tip 字节一致（见本文件）。


## 6. tip 前移记录

| 日期 (Asia/Shanghai) | tip | 机制 headCommit | 动作 |
|---|---|---|---|
| 2026-10-25 | 65f7815 | 7623a52 | 初版禁令 |
| 2026-10-25 | 0f20bf1（7b54e2+） | 7623a52 | merge feature@9d8428e + ROI 核对文档；**仍不重跑** mechanism；禁令保持 |
| 2026-10-25 | 0654d13（fast-forward feature@0654d13） | 7623a52 | tip 超前 mechanism head **125** commits；**仍不重跑** mechanism；ES-4 仅 JSON 图注 enrichment（pngBytesUntouched） |

| 2026-10-25 | 9eb8406（FF feature@c761d54 + ES-3/5 续做） | 7623a52 | tip 超前 mechanism head **135** commits；**仍不重跑** mechanism；仅记证据 |

## 7. 对齐 feature@0654d13 后的开项证据（2026-10-25 13:11 Asia/Shanghai）

| 项 | 值 |
|---|---|
| 分支 tip | `3e085451373f8d1679ffd2d33a0af6405ab7dcdc` |
| mechanism `headCommit` | `7623a52a3299b7c948031dfa1f79f04b8eb66d9e` |
| tip 相对 head 超前 | **125** commits（`git rev-list --count 7623a52..0654d13`） |
| R7 / G7 | **仍开项** — 只记证据，不谎关；未重跑 `mechanism_cases.py` |
| ES-4 本轮 | `enrich_mechanism_captions.py` 只改 `mechanism.json` / `index.json` 图注字段；PNG SHA 未变 |
| 宣称禁令 | 报告不得宣称机制 PNG 与当前 tip 字节一致 |

## 8. 对齐 feature@c761d54 后的开项证据（2026-10-25 Asia/Shanghai）

| 项 | 值 |
| --- | --- |
| 分支 tip | 9eb8406ba1a788a20dc88035fe2eef314afc7b9d |
| 父提交 | c761d546794c428a29c1a1e0f73c55c464d092cf（feature tip / FF 点） |
| mechanism headCommit | 7623a52a3299b7c948031dfa1f79f04b8eb66d9e |
| tip 相对 head 超前 | **135** commits（git rev-list --count 7623a52..HEAD） |
| R7 / G7 | **仍开着** — 只记证据，勿谎关；未重跑 mechanism_cases.py |
| ES-3 | lift_claim_summary.json + CI annotate（may_claim_positive_lift / liftClaimLabel） |
| ES-5 | negative_lift_display.json（slim：无 measuredEvidence 复本；指向 NLC） |
| ES-4 提醒 | 图注 provenance 已挂；PNG 字节仍属旧 headCommit |
| A24 | 仍 xfail；Phase2 schema 缺口未落地 |
