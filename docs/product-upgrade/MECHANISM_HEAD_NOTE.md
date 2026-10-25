# MECHANISM_HEAD_NOTE — 机制层 headCommit 与 tip 关系（红队条件）

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-25（Asia/Shanghai）
- 分支：`agent/eval-sci`
- 当前 tip（写入时）：ed9f1a0b20978d5500453bdbbaa43505a6f9297d（短写 ed9f1a0；FF 对齐 feature 稳定 tip；含 report slice10 / liftClaims 屏上对齐；冒烟 747p/1xfail；R7/A24 仍开）
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

| 2026-10-25 | 4f57eb5（FF feature@4f57eb5） | 7623a52 | tip 超前 mechanism head **141** commits；**仍不重跑** mechanism；门禁合入后对齐 |

| 2026-10-25 | b60d556（FF feature@b60d556） | 7623a52 | tip 超前 mechanism head **145** commits；**仍不重跑** mechanism；89ff1db 已合入 |

| 2026-10-25 | e53929f（FF feature@e53929f） | 7623a52 | tip 超前 mechanism head **161** commits；**仍不重跑** mechanism；含 report slice8/9 |

| 2026-10-25 | ed9f1a0（FF feature@ed9f1a0） | 7623a52 | tip 超前 mechanism head **169** commits；**仍不重跑** mechanism；续 ES-3/4/5 契约核验 |

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

## 9. 对齐 feature@4f57eb5 后开项证据（2026-10-25 14:20 Asia/Shanghai）

| 项 | 值 |
| --- | --- |
| 分支 tip | 4f57eb5ef57cdcb702042ccaa23904dbafcf9648 |
| feature tip | 4f57eb5ef57cdcb702042ccaa23904dbafcf9648（对齐时相同） |
| mechanism headCommit | 7623a52a3299b7c948031dfa1f79f04b8eb66d9e |
| tip 相对 head 超前 | **141** commits（git rev-list --count 7623a52..HEAD） |
| R7 / G7 | **仍开项** — 只记证据，未谎关；未重跑 mechanism_cases.py |
| pytest | 742 passed / 1 xfailed / 0 failed |
| A24 | 仍 xfail（	est_a24_export_label_recognized_forbidden_until_schema_exists）；禁伪 Top-k；未改正式 assert |
| 铁律 | 未 push / 未合 main / 未改 museum_processing |

## 10. 对齐 feature@b60d556 后开项证据（2026-10-25 14:51 Asia/Shanghai）

| 项 | 值 |
| --- | --- |
| 分支 tip | b60d55697d741682d28af5f28319e2b84aca8230 |
| feature tip | b60d55697d741682d28af5f28319e2b84aca8230（对齐时相同） |
| mechanism headCommit | 7623a52a3299b7c948031dfa1f79f04b8eb66d9e |
| tip 相对 head 超前 | **145** commits（git rev-list --count 7623a52..HEAD） |
| R7 / G7 | **仍开项** — 只记证据，未谎关；未重跑 mechanism_cases.py；无空转宣称 |
| pytest | 747 passed / 1 xfailed / 0 failed |
| A24 | 仍 xfail；禁伪 Top-k / 无假 schema 前勿伪绿 |
| 铁律 | 未 push / 未合 main；FF 未改写 museum_processing（仅随 feature 带入） |

## 11. 对齐 feature@e53929f 后开项证据（2026-10-25 15:09 Asia/Shanghai）

| 项 | 值 |
| --- | --- |
| 分支 tip | e53929f1f5e9281427dc11d244f6c78bb0dde3a7 |
| feature tip | e53929f1f5e9281427dc11d244f6c78bb0dde3a7（对齐时相同；含 c027714 + ffb9138） |
| mechanism headCommit | 7623a52a3299b7c948031dfa1f79f04b8eb66d9e |
| tip 相对 head 超前 | **161** commits（git rev-list --count 7623a52..HEAD） |
| R7 / G7 | **仍开项** — 只记证据，未谎关；本期不重跑大批量 mechanism |
| pytest | 747 passed / 1 xfailed / 0 failed |
| A24 | 仍 xfail；禁伪 Top-k / 无假 schema 前勿伪绿 |
| ES-3/4/5 | 契约与 derived 证据维持；不伪绿 CI / Top-k |
| 铁律 | 未 push / 未合 main / 未改 museum_processing / 未把 A24 改正式 assert |

## 12. feature@3b0c47b 窄冒烟后开项核验（2026-10-25 15:24 Asia/Shanghai）

| 项 | 值 |
| --- | --- |
| 分支 tip / feature tip | 3b0c47bb41351d37fe77d125ca9b84b111e8e7e0（已对齐，无需再 FF） |
| mechanism index.json headCommit | 7623a52a3299b7c948031dfa1f79f04b8eb66d9e（v2 + v2-text 均同） |
| tip 相对 head 超前 | **162** commits（git rev-list --count 7623a52..HEAD；含本 tip 相对 e53929f +1） |
| R7 / G7 | **仍开项** — 只记证据，未谎关；本期不重跑大批量 mechanism |
| A24 | 	est_a24_export_label_recognized_forbidden_until_schema_exists 仍 xfail；	est_a24_schema_still_absent_keep_xfail_evidence PASSED；禁伪 Top-k |
| 铁律 | 未 push / 未合 main / 未改 museum_processing / 未把 A24 改正式 assert |

## 13. 对齐 feature@ed9f1a0 后 ES/R7 开项（2026-10-25 15:43 Asia/Shanghai）

| 项 | 值 |
| --- | --- |
| 分支 tip | ed9f1a0b20978d5500453bdbbaa43505a6f9297d |
| feature tip | ed9f1a0b20978d5500453bdbbaa43505a6f9297d（对齐时相同） |
| mechanism headCommit | 7623a52a3299b7c948031dfa1f79f04b8eb66d9e |
| tip 相对 head 超前 | **169** commits（git rev-list --count 7623a52..HEAD） |
| R7 / G7 | **仍开项** — 只记证据，未谎关；未重跑大批量 mechanism |
| A24 | 仍 xfail；禁伪 Top-k |
| ES-3 | lift_claim_summary.json + CI annotate 契约仍绿；报告侧 export JSON liftClaims 屏上对齐（report 合入） |
| ES-4 | captionProvenance.pngBytesUntouched=true；head 仍滞后 tip |
| ES-5 | 
egative_lift_display.json 仍在；规则次级口径维持 |
| pytest | 747 passed / 1 xfailed / 0 failed |
| 铁律 | 未 push / 未合 main / 未改 museum_processing；文件只写 D:\RubbingMind |
