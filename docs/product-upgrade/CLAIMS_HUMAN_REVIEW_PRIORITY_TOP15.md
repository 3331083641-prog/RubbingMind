# Claims 人工复核优先队列 Top15

- 作者：RM-金石史料
- 生成时间：2026-10-25 18:06 Asia/Shanghai
- 基于 tip：`e662631`（`e66263185036b18c45682d1b980ced73bcf61898`）
- 数据源：`docs/product-upgrade/CLAIMS_OPEN_ISSUES.md` + `scripts/check_claims_open_issues.py` 同源扫描
- **开项仍开**：本文仅排期提示，**不是**关闭声明；claim 文件 28/28 ≠ 开项关闭
- 铁律：不定论、不合并异文、不抬升 Verification、不改 claims JSON、不 C-08 --apply、不改正式馆藏/主库、不 push

## 排序说明（仅便于人工排期，非史实结论）

1. **conflict（异文并列）优先于**单纯 pending_review / cataloguePendingReview
2. **影响面大**者优先：分期/载体/历日交叉/现藏迁徙/书体归属（及带 reviewFlags 的载体鉴定）重于一般人物角色异文
3. **证据缺口/下一步可执行**者优先（馆方页、碑面纪年、URL、目录 Verification 对照等）
4. **同碑多条相邻列出**，但不合并异文、不合并开项

## 台账计数快照（生成时）

| 指标 | 数量 |
|---|---:|
| openRows | 36 |
| conflict | 20 |
| pendingHuman | 30 |
| reviewFlag | 1 |
| cataloguePendingReview | 13 |
| claimFiles | 28 |

## Top15 优先队列

| # | claimId | 题名/主题 | 开项类型 | 严重度分组 | 证据缺口 | 建议动作 | Q 队列 |
|---:|---|---|---|---|---|---|---|
| 1 | `ming_02_luxianzhi:work:objectNature` | ming_02_luxianzhi · work.objectNature | conflict | 高（影响分期/载体/历日/书体归属） | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；reviewFlags 待消解（载体性质待人工鉴定）；缺馆方／公开网页 URL 来源 | 先按 reviewFlags 目验 ming_02_luxianzhi 载体／鉴定，再决定是否维持 conflict | Q1 |
| 2 | `tang_01_duobao:date:dayCrossCheck` | tang_01_duobao · date.dayCrossCheck | conflict | 高（影响分期/载体/历日/书体归属） | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 | 打开 tang_01_duobao 馆方 Dates 与碑面纪年／干支，只核验两侧一致性并记录证据缺口 | Q1 |
| 3 | `tang_03_yanjiamiao:date:ce` | tang_03_yanjiamiao · date.ce | conflict | 高（影响分期/载体/历日/书体归属） | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺碑面／释文文件源做干支历表交叉 | 打开 tang_03_yanjiamiao 馆方 Dates 与碑面纪年／干支，只核验两侧一致性并记录证据缺口 | Q1 |
| 4 | `tang_03_yanjiamiao:date:yearCrossCheck` | tang_03_yanjiamiao · date.yearCrossCheck | conflict | 高（影响分期/载体/历日/书体归属） | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺碑面／释文文件源做干支历表交叉 | 打开 tang_03_yanjiamiao 馆方 Dates 与碑面纪年／干支，只核验两侧一致性并记录证据缺口 | Q1 |
| 5 | `wei_02_wugaoli:date:dayCrossCheck` | wei_02_wugaoli · date.dayCrossCheck | conflict | 高（影响分期/载体/历日/书体归属） | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 | 打开 wei_02_wugaoli 馆方 Dates 与碑面纪年／干支，只核验两侧一致性并记录证据缺口 | Q1 |
| 6 | `tang_04_xuanmita:style:script` | tang_04_xuanmita · script_style.script | conflict | 高（影响分期/载体/历日/书体归属） | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 | 打开 tang_04_xuanmita 馆方书体栏与目录 scriptType，两侧异文继续并列登记 | Q1 |
| 7 | `tang_04_xuanmita:stone:transfer` | tang_04_xuanmita · stone.transfer | conflict | 高（影响分期/载体/历日/书体归属） | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 | 核对 tang_04_xuanmita 现藏／迁徙／尺寸多家著录，异文并列不合并 | Q1 |
| 8 | `yuan_01_yufu:style:script` | yuan_01_yufu · script_style.script | conflict | 高（影响分期/载体/历日/书体归属） | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 | 打开 yuan_01_yufu 馆方书体栏与目录 scriptType，两侧异文继续并列登记 | Q1 |
| 9 | `qing_02_wushi_reerection:work:dynasty` | qing_02_wushi_reerection · work.dynasty | conflict | 高（影响分期/载体/历日/书体归属） | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 | 打开 qing_02_wushi_reerection 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | Q1 |
| 10 | `qing_02_wushi_reerection:person:engraver` | qing_02_wushi_reerection · person.engraver | conflict | 中（人物角色异文） | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 | 打开 qing_02_wushi_reerection 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | Q1 |
| 11 | `qing_02_wushi_reerection:person:author` | qing_02_wushi_reerection · person.author | pending_review+cataloguePendingReview | 中（待人工复核／未抬升） | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 authorVerification=pending_review，claims 未抬升为已验证 | 核目录 qing_02_wushi_reerection.author Verification=pending_review；无新证据勿抬升为已验证 | Q2+Q3 |
| 12 | `qing_02_wushi_reerection:person:calligrapher` | qing_02_wushi_reerection · person.calligrapher | pending_review+cataloguePendingReview | 中（待人工复核／未抬升） | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 | 核目录 qing_02_wushi_reerection.calligrapher Verification=pending_review；无新证据勿抬升为已验证 | Q2+Q3 |
| 13 | `song_01_yuanyou:script_style:script` | song_01_yuanyou · script_style.script | conflict | 高（影响分期/载体/历日/书体归属） | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 | 打开 song_01_yuanyou 馆方书体栏与目录 scriptType，两侧异文继续并列登记 | Q1 |
| 14 | `ming_03_wugou:script_style:script` | ming_03_wugou · script_style.script | conflict | 高（影响分期/载体/历日/书体归属） | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 | 打开 ming_03_wugou 馆方书体栏与目录 scriptType，两侧异文继续并列登记 | Q1 |
| 15 | `tang_02_jiucheng:stone:currentLocation` | tang_02_jiucheng · stone.currentLocation | conflict | 高（影响分期/载体/历日/书体归属） | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 | 核对 tang_02_jiucheng 现藏／迁徙／尺寸多家著录，异文并列不合并 | Q1 |

## 按优先级的 claimId 列表

1. `ming_02_luxianzhi:work:objectNature`
2. `tang_01_duobao:date:dayCrossCheck`
3. `tang_03_yanjiamiao:date:ce`
4. `tang_03_yanjiamiao:date:yearCrossCheck`
5. `wei_02_wugaoli:date:dayCrossCheck`
6. `tang_04_xuanmita:style:script`
7. `tang_04_xuanmita:stone:transfer`
8. `yuan_01_yufu:style:script`
9. `qing_02_wushi_reerection:work:dynasty`
10. `qing_02_wushi_reerection:person:engraver`
11. `qing_02_wushi_reerection:person:author`
12. `qing_02_wushi_reerection:person:calligrapher`
13. `song_01_yuanyou:script_style:script`
14. `ming_03_wugou:script_style:script`
15. `tang_02_jiucheng:stone:currentLocation`

## 同碑相邻说明

- `tang_03_yanjiamiao`：`tang_03_yanjiamiao:date:ce`；`tang_03_yanjiamiao:date:yearCrossCheck`（相邻列出，异文仍并列、不开项合并）
- `tang_04_xuanmita`：`tang_04_xuanmita:style:script`；`tang_04_xuanmita:stone:transfer`（相邻列出，异文仍并列、不开项合并）
- `qing_02_wushi_reerection`：`qing_02_wushi_reerection:work:dynasty`；`qing_02_wushi_reerection:person:engraver`；`qing_02_wushi_reerection:person:author`；`qing_02_wushi_reerection:person:calligrapher`（相邻列出，异文仍并列、不开项合并）

## 明确不做

- 不关闭任一开项；不改 `data/catalog/claims/*`
- 不抬升任何 `*Verification`
- 不执行 C-08 `--apply`；不改主库 28 件 / 馆藏原文影像 / 主库 SHA
- 不 push；不改 main

## 下一步（人工）

1. 按上表 #1 起逐条打开馆方页 / 碑面纪年 / 目录字段，只记录核对结果与证据缺口
2. 有足以定论的新证据后，再另案改对应 claims JSON（本文件不授权改库）
3. 关闭须同时满足：新证据入库 + 台账 `--check` 计数下降；仅本文档存在 ≠ 关闭
