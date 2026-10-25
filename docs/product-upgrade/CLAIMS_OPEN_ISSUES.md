# Claims 开项台账（冲突／待人工复核）

> **口径（Green 2026-10-25）：** claim 文件已齐 **28/28**，不等于开项关闭。
> 本文件只汇总 `conflict` 异文并列、`evidenceLevel=待人工复核`、`reviewFlags`、以及目录 `*Verification=pending_review` 且未抬升为「已验证」的条目。
> **不定论、不合并异文、不改写已审证据。** 建议动作仅为人工复核提示。

- 生成时间（Asia/Shanghai）：2026-10-25
- 扫描范围：`data/catalog/claims/*.json`（28 件作品文件）+ `steles28.json` Verification 字段
- 校验脚本：`scripts/check_claims_open_issues.py --check`

## 统计摘要

| 指标 | 数量 |
|---|---:|
| claim 文件 | 28/28 |
| 开项行（去重 claimId） | 36 |
| 其中 status=conflict | 20 |
| 其中 evidenceLevel=待人工复核 | 30 |
| 含 reviewFlags | 1 |
| 目录 pending_review 未抬升 | 13 |

### 按朝代（开项行）

| 朝代 | 开项行 |
|---|---:|
| 东汉 | 2 |
| 北魏 | 2 |
| 唐代 | 10 |
| 宋代 | 3 |
| 元代 | 6 |
| 明代 | 5 |
| 清代 | 8 |

### 按严重度分组（仅便于排期，非史实结论）

| 分组 | 开项行 |
|---|---:|
| 中（待人工复核／未抬升） | 16 |
| 高（影响分期/载体/历日/书体归属） | 12 |
| 中（人物角色异文） | 7 |
| 中（异文并列） | 1 |

### 冲突字段分布（status=conflict）

| property | 条数 |
|---|---:|
| script | 4 |
| calligrapher | 2 |
| engraver | 2 |
| dayCrossCheck | 2 |
| objectNature | 1 |
| dynasty | 1 |
| authorEraConflict | 1 |
| currentLocation | 1 |
| eventDate | 1 |
| ce | 1 |
| yearCrossCheck | 1 |
| transfer | 1 |
| authorDispute | 1 |
| authorFieldConflict | 1 |

## 人工复核提示（按核对队列）

> 仅排期提示：**不定论、不合并异文、不自动关闭开项、不 C-08 --apply**。
> 每条给出「下一步核对动作」与「证据缺口」；关闭须另有新证据并改对应 claims JSON。

### Q1 · conflict 异文并列（20）

| claimId | 作品 | 字段 | 下一步核对动作 | 证据缺口 |
|---|---|---|---|---|
| `han_02_yiying:person:calligrapher` | han_02_yiying | person.calligrapher | 打开 han_02_yiying 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `wei_02_wugaoli:date:dayCrossCheck` | wei_02_wugaoli | date.dayCrossCheck | 打开 wei_02_wugaoli 馆方 Dates 与碑面纪年／干支，只核验两侧一致性并记录证据缺口 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `tang_01_duobao:date:dayCrossCheck` | tang_01_duobao | date.dayCrossCheck | 打开 tang_01_duobao 馆方 Dates 与碑面纪年／干支，只核验两侧一致性并记录证据缺口 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 |
| `tang_02_jiucheng:date:visitYear` | tang_02_jiucheng | date.eventDate | 打开 tang_02_jiucheng 馆方 Dates 与碑面纪年／干支，只核验两侧一致性并记录证据缺口 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `tang_02_jiucheng:stone:currentLocation` | tang_02_jiucheng | stone.currentLocation | 核对 tang_02_jiucheng 现藏／迁徙／尺寸多家著录，异文并列不合并 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `tang_03_yanjiamiao:date:ce` | tang_03_yanjiamiao | date.ce | 打开 tang_03_yanjiamiao 馆方 Dates 与碑面纪年／干支，只核验两侧一致性并记录证据缺口 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺碑面／释文文件源做干支历表交叉 |
| `tang_03_yanjiamiao:date:yearCrossCheck` | tang_03_yanjiamiao | date.yearCrossCheck | 打开 tang_03_yanjiamiao 馆方 Dates 与碑面纪年／干支，只核验两侧一致性并记录证据缺口 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺碑面／释文文件源做干支历表交叉 |
| `tang_04_xuanmita:stone:transfer` | tang_04_xuanmita | stone.transfer | 核对 tang_04_xuanmita 现藏／迁徙／尺寸多家著录，异文并列不合并 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `tang_04_xuanmita:style:script` | tang_04_xuanmita | script_style.script | 打开 tang_04_xuanmita 馆方书体栏与目录 scriptType，两侧异文继续并列登记 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 |
| `song_01_yuanyou:script_style:script` | song_01_yuanyou | script_style.script | 打开 song_01_yuanyou 馆方书体栏与目录 scriptType，两侧异文继续并列登记 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `song_02_wenxuan:person:authorEraConflict` | song_02_wenxuan | person.authorEraConflict | 打开 song_02_wenxuan 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `yuan_01_yufu:style:script` | yuan_01_yufu | script_style.script | 打开 yuan_01_yufu 馆方书体栏与目录 scriptType，两侧异文继续并列登记 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 |
| `yuan_02_sundeyu:person:authorDispute` | yuan_02_sundeyu | person.authorDispute | 打开 yuan_02_sundeyu 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `yuan_03_shengzhu:bibliography:authorFieldConflict` | yuan_03_shengzhu | bibliography.authorFieldConflict | 打开 yuan_03_shengzhu 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺目录字段对照源 |
| `ming_02_luxianzhi:work:objectNature` | ming_02_luxianzhi | work.objectNature | 先按 reviewFlags 目验 ming_02_luxianzhi 载体／鉴定，再决定是否维持 conflict | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；reviewFlags 待消解（载体性质待人工鉴定）；缺馆方／公开网页 URL 来源 |
| `ming_03_wugou:script_style:script` | ming_03_wugou | script_style.script | 打开 ming_03_wugou 馆方书体栏与目录 scriptType，两侧异文继续并列登记 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `ming_04_tongdian:person:calligrapher` | ming_04_tongdian | person.calligrapher | 打开 ming_04_tongdian 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `qing_02_wushi_reerection:person:engraver` | qing_02_wushi_reerection | person.engraver | 打开 qing_02_wushi_reerection 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `qing_02_wushi_reerection:work:dynasty` | qing_02_wushi_reerection | work.dynasty | 打开 qing_02_wushi_reerection 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `qing_04_ayuwang_reliquary:person:engraver` | qing_04_ayuwang_reliquary | person.engraver | 打开 qing_04_ayuwang_reliquary 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |

### Q2 · 待人工复核（非 conflict）（10）

| claimId | 作品 | 字段 | 下一步核对动作 | 证据缺口 |
|---|---|---|---|---|
| `tang_02_jiucheng:stone:dimensions` | tang_02_jiucheng | stone.dimensions | 按「建议人工动作」复核 tang_02_jiucheng.dimensions，补证据后再议是否改 claims JSON | evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `tang_04_xuanmita:date:gregorianDay` | tang_04_xuanmita | date.gregorianDay | 按「建议人工动作」复核 tang_04_xuanmita.gregorianDay，补证据后再议是否改 claims JSON | evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 |
| `tang_04_xuanmita:rubbing:sourceStoneIdentity` | tang_04_xuanmita | rubbing.sourceStone | 按「建议人工动作」复核 tang_04_xuanmita.sourceStone，补证据后再议是否改 claims JSON | evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `yuan_04_jingyuanchang:person:calligrapher` | yuan_04_jingyuanchang | person.calligrapher | 核目录 yuan_04_jingyuanchang.calligrapher Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |
| `yuan_04_jingyuanchang:person:steleSubject` | yuan_04_jingyuanchang | person.steleSubject | 核目录 yuan_04_jingyuanchang.steleSubject Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 steleSubjectVerification=pending_review，claims 未抬升为已验证 |
| `qing_01_qianlong_heart_sutra:person:calligrapher` | qing_01_qianlong_heart_sutra | person.calligrapher | 核目录 qing_01_qianlong_heart_sutra.calligrapher Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |
| `qing_02_wushi_reerection:person:author` | qing_02_wushi_reerection | person.author | 核目录 qing_02_wushi_reerection.author Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 authorVerification=pending_review，claims 未抬升为已验证 |
| `qing_02_wushi_reerection:person:calligrapher` | qing_02_wushi_reerection | person.calligrapher | 核目录 qing_02_wushi_reerection.calligrapher Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |
| `qing_03_sanxitang_preface:person:author` | qing_03_sanxitang_preface | person.author | 核目录 qing_03_sanxitang_preface.author Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 authorVerification=pending_review，claims 未抬升为已验证 |
| `qing_03_sanxitang_preface:person:calligrapher` | qing_03_sanxitang_preface | person.calligrapher | 核目录 qing_03_sanxitang_preface.calligrapher Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |

### Q3 · 目录 pending_review 未抬升（无 conflict）（13）

| claimId | 作品 | 字段 | 下一步核对动作 | 证据缺口 |
|---|---|---|---|---|
| `han_02_yiying:person:steleSubject` | han_02_yiying | person.steleSubject | 核目录 han_02_yiying.steleSubject Verification=pending_review；无新证据勿抬升为已验证 | 目录 steleSubjectVerification=pending_review，claims 未抬升为已验证 |
| `wei_04_wangsong:person:author` | wei_04_wangsong | person.author | 核目录 wei_04_wangsong.author Verification=pending_review；无新证据勿抬升为已验证 | 目录 authorVerification=pending_review，claims 未抬升为已验证 |
| `song_03_daguan:person:author` | song_03_daguan | person.author | 核目录 song_03_daguan.author Verification=pending_review；无新证据勿抬升为已验证 | 目录 authorVerification=pending_review，claims 未抬升为已验证；缺馆方／公开网页 URL 来源 |
| `yuan_03_shengzhu:person:titleCalligrapher` | yuan_03_shengzhu | person.titleCalligrapher | 核目录 yuan_03_shengzhu.titleCalligrapher Verification=pending_review；无新证据勿抬升为已验证 | 目录 titleCalligrapherVerification=pending_review，claims 未抬升为已验证；缺馆方／公开网页 URL 来源 |
| `yuan_04_jingyuanchang:person:calligrapher` | yuan_04_jingyuanchang | person.calligrapher | 核目录 yuan_04_jingyuanchang.calligrapher Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |
| `yuan_04_jingyuanchang:person:steleSubject` | yuan_04_jingyuanchang | person.steleSubject | 核目录 yuan_04_jingyuanchang.steleSubject Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 steleSubjectVerification=pending_review，claims 未抬升为已验证 |
| `ming_03_wugou:person:steleSubject` | ming_03_wugou | person.steleSubject | 核目录 ming_03_wugou.steleSubject Verification=pending_review；无新证据勿抬升为已验证 | 目录 steleSubjectVerification=pending_review，claims 未抬升为已验证 |
| `ming_04_tongdian:person:engraver` | ming_04_tongdian | person.engraver | 核目录 ming_04_tongdian.engraver Verification=pending_review；无新证据勿抬升为已验证 | 目录 engraverVerification=pending_review，claims 未抬升为已验证 |
| `qing_01_qianlong_heart_sutra:person:calligrapher` | qing_01_qianlong_heart_sutra | person.calligrapher | 核目录 qing_01_qianlong_heart_sutra.calligrapher Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |
| `qing_02_wushi_reerection:person:author` | qing_02_wushi_reerection | person.author | 核目录 qing_02_wushi_reerection.author Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 authorVerification=pending_review，claims 未抬升为已验证 |
| `qing_02_wushi_reerection:person:calligrapher` | qing_02_wushi_reerection | person.calligrapher | 核目录 qing_02_wushi_reerection.calligrapher Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |
| `qing_03_sanxitang_preface:person:author` | qing_03_sanxitang_preface | person.author | 核目录 qing_03_sanxitang_preface.author Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 authorVerification=pending_review，claims 未抬升为已验证 |
| `qing_03_sanxitang_preface:person:calligrapher` | qing_03_sanxitang_preface | person.calligrapher | 核目录 qing_03_sanxitang_preface.calligrapher Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |

### Q4 · 含 reviewFlags（1）

| claimId | 作品 | 字段 | 下一步核对动作 | 证据缺口 |
|---|---|---|---|---|
| `ming_02_luxianzhi:work:objectNature` | ming_02_luxianzhi | work.objectNature | 先按 reviewFlags 目验 ming_02_luxianzhi 载体／鉴定，再决定是否维持 conflict | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；reviewFlags 待消解（载体性质待人工鉴定）；缺馆方／公开网页 URL 来源 |

## 冲突并列一览（JS-4 · status=conflict）

> 异文两侧并列，**不定论、不合并、不关闭**。共 **20** 条（与统计摘要 conflict 一致）。
> 用途：人工对照馆方页／碑面／目录时，一眼看到两侧主张；关闭须有新证据并改对应 claims JSON。

| # | claimId | 作品 | 字段 | 侧 A | 侧 B／更多 | 建议人工动作 | 证据缺口 |
|---:|---|---|---|---|---|---|---|
| 1 | `han_02_yiying:person:calligrapher` | han_02_yiying | person.calligrapher | 后汉钟太尉书（传统题记；张稚圭按图题记） | 未核定（目录 calligrapher） | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| 2 | `wei_02_wugaoli:date:dayCrossCheck` | wei_02_wugaoli | date.dayCrossCheck | 碑面作“癸申”（非六十甲子合法干支，疑泐误） | 若丙午朔第13日推算为 戊午 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| 3 | `tang_01_duobao:date:dayCrossCheck` | tang_01_duobao | date.dayCrossCheck | 廿二日戊戌（释文作“戊戍”） | 按“乙丑朔”顺推，廿二日应为丙戌 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 |
| 4 | `tang_02_jiucheng:date:visitYear` | tang_02_jiucheng | date.eventDate | 貞觀六年孟夏之月（碑文） | 贞观七年四月（故宫介绍文字） | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| 5 | `tang_02_jiucheng:stone:currentLocation` | tang_02_jiucheng | stone.currentLocation | 原石在陕西宝鸡麟游（九成宫原地） | 原碑今存于陕西省西安市碑林博物馆 | 对照多家馆方现藏／迁徙说明与尺寸著录；多源异文并列。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| 6 | `tang_03_yanjiamiao:date:ce` | tang_03_yanjiamiao | date.ce | 780 | 779 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺碑面／释文文件源做干支历表交叉 |
| 7 | `tang_03_yanjiamiao:date:yearCrossCheck` | tang_03_yanjiamiao | date.yearCrossCheck | 780 | 779 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺碑面／释文文件源做干支历表交叉 |
| 8 | `tang_04_xuanmita:stone:transfer` | tang_04_xuanmita | stone.transfer | 宋元祐年间移入碑林 | 1103 年西安碑林建立之初就移入碑林 | 对照多家馆方现藏／迁徙说明与尺寸著录；多源异文并列。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| 9 | `tang_04_xuanmita:style:script` | tang_04_xuanmita | script_style.script | 楷书 | 小楷书（台北故宫品名、封签） | 对照馆方书体栏、释文标注与目录 scriptType；异文保持并列。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 |
| 10 | `song_01_yuanyou:script_style:script` | song_01_yuanyou | script_style.script | 楷书（馆方书体栏；目录 scriptType） | 隶书（馆方释文对标题的书体标注） | 对照馆方书体栏、释文标注与目录 scriptType；异文保持并列。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| 11 | `song_02_wenxuan:person:authorEraConflict` | song_02_wenxuan | person.authorEraConflict | 宋太宗（馆方题名／目录） | 大中祥符诏令语境属真宗朝（释文） | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| 12 | `yuan_01_yufu:style:script` | yuan_01_yufu | script_style.script | 行楷书（目录、馆方书体栏） | 小楷书（馆方品名） | 对照馆方书体栏、释文标注与目录 scriptType；异文保持并列。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 |
| 13 | `yuan_02_sundeyu:person:authorDispute` | yuan_02_sundeyu | person.authorDispute | 赵文原撰（释文） | 赵孟頫（馆方作者栏，实为书者） ｜ 未核定／disputed（目录） | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| 14 | `yuan_03_shengzhu:bibliography:authorFieldConflict` | yuan_03_shengzhu | bibliography.authorFieldConflict | 赵孟頫（馆方作者栏） | 王思廉撰 / 赵孟頫书（释文） | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺目录字段对照源 |
| 15 | `ming_02_luxianzhi:work:objectNature` | ming_02_luxianzhi | work.objectNature | 拓片（馆方分类） | 墓志草稿（题跋：“此潯州知府陸君墓志草稿”） | 对照馆方分类与题跋原文，必要时目验拓本／墨迹载体；确认是否存在原刻层。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；reviewFlags 待消解（载体性质待人工鉴定）；缺馆方／公开网页 URL 来源 |
| 16 | `ming_03_wugou:script_style:script` | ming_03_wugou | script_style.script | 篆额 + 楷书正文（目录 scriptType） | 篆书（馆方书体栏单值） | 对照馆方书体栏、释文标注与目录 scriptType；异文保持并列。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| 17 | `ming_04_tongdian:person:calligrapher` | ming_04_tongdian | person.calligrapher | 集王羲之书（吴士瑞集字；非王羲之亲书） | 未核定（目录 calligrapher） | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| 18 | `qing_02_wushi_reerection:person:engraver` | qing_02_wushi_reerection | person.engraver | 郑之宗 / Zheng Zhizong（馆方 carver；目录说明亦称郑之宗刻） | 未核定（目录 engraver） | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| 19 | `qing_02_wushi_reerection:work:dynasty` | qing_02_wushi_reerection | work.dynasty | 清代（目录；1787年翁方纲新刻记文，非东汉画像石） | 东汉（馆方页面时期标签 Eastern Han dynasty, 25–220 CE） | 对照馆方 Period/Culture 标签与刻石纪年、作者生卒；区分遗迹语境标签与本件新刻朝代。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| 20 | `qing_04_ayuwang_reliquary:person:engraver` | qing_04_ayuwang_reliquary | person.engraver | 授轮、圆伦、谛受、道修（馆方 carving agent／碑阴署仝募刊；募刊≠传统刻工身份待复核） | 未核定（目录 engraver） | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |

## 待人工复核工作清单（JS-5）

> 供人工逐条勾选；**脚本与台账不自动关闭**。去重 claimId 共 **36** 条仍开放。
> 含 `evidenceLevel=待人工复核`、目录 `*Verification=pending_review` 未抬升、`reviewFlags`。勾选仅表示人工已看过，关闭开项仍须改 claims JSON 并有证据。

| ☐ | claimId | 作品 | 类型摘要 | 建议人工动作 | 下一步核对 | 证据缺口 |
|---|---|---|---|---|---|---|
| ☐ | `han_02_yiying:person:calligrapher` | han_02_yiying | conflict、待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 打开 han_02_yiying 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| ☐ | `han_02_yiying:person:steleSubject` | han_02_yiying | 目录pending_review未抬升 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 核目录 han_02_yiying.steleSubject Verification=pending_review；无新证据勿抬升为已验证 | 目录 steleSubjectVerification=pending_review，claims 未抬升为已验证 |
| ☐ | `wei_02_wugaoli:date:dayCrossCheck` | wei_02_wugaoli | conflict、待人工复核 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 打开 wei_02_wugaoli 馆方 Dates 与碑面纪年／干支，只核验两侧一致性并记录证据缺口 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| ☐ | `wei_04_wangsong:person:author` | wei_04_wangsong | 目录pending_review未抬升 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 核目录 wei_04_wangsong.author Verification=pending_review；无新证据勿抬升为已验证 | 目录 authorVerification=pending_review，claims 未抬升为已验证 |
| ☐ | `tang_01_duobao:date:dayCrossCheck` | tang_01_duobao | conflict、待人工复核 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 打开 tang_01_duobao 馆方 Dates 与碑面纪年／干支，只核验两侧一致性并记录证据缺口 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 |
| ☐ | `tang_02_jiucheng:date:visitYear` | tang_02_jiucheng | conflict、待人工复核 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 打开 tang_02_jiucheng 馆方 Dates 与碑面纪年／干支，只核验两侧一致性并记录证据缺口 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| ☐ | `tang_02_jiucheng:stone:currentLocation` | tang_02_jiucheng | conflict、待人工复核 | 对照多家馆方现藏／迁徙说明与尺寸著录；多源异文并列。 | 核对 tang_02_jiucheng 现藏／迁徙／尺寸多家著录，异文并列不合并 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| ☐ | `tang_03_yanjiamiao:date:ce` | tang_03_yanjiamiao | conflict、待人工复核 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 打开 tang_03_yanjiamiao 馆方 Dates 与碑面纪年／干支，只核验两侧一致性并记录证据缺口 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺碑面／释文文件源做干支历表交叉 |
| ☐ | `tang_03_yanjiamiao:date:yearCrossCheck` | tang_03_yanjiamiao | conflict、待人工复核 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 打开 tang_03_yanjiamiao 馆方 Dates 与碑面纪年／干支，只核验两侧一致性并记录证据缺口 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺碑面／释文文件源做干支历表交叉 |
| ☐ | `tang_04_xuanmita:stone:transfer` | tang_04_xuanmita | conflict、待人工复核 | 对照多家馆方现藏／迁徙说明与尺寸著录；多源异文并列。 | 核对 tang_04_xuanmita 现藏／迁徙／尺寸多家著录，异文并列不合并 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| ☐ | `tang_04_xuanmita:style:script` | tang_04_xuanmita | conflict、待人工复核 | 对照馆方书体栏、释文标注与目录 scriptType；异文保持并列。 | 打开 tang_04_xuanmita 馆方书体栏与目录 scriptType，两侧异文继续并列登记 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 |
| ☐ | `tang_02_jiucheng:stone:dimensions` | tang_02_jiucheng | 待人工复核 | 对照多家馆方现藏／迁徙说明与尺寸著录；多源异文并列。 | 按「建议人工动作」复核 tang_02_jiucheng.dimensions，补证据后再议是否改 claims JSON | evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| ☐ | `tang_04_xuanmita:date:gregorianDay` | tang_04_xuanmita | 待人工复核 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 按「建议人工动作」复核 tang_04_xuanmita.gregorianDay，补证据后再议是否改 claims JSON | evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 |
| ☐ | `tang_04_xuanmita:rubbing:sourceStoneIdentity` | tang_04_xuanmita | 待人工复核 | 对照多家馆方现藏／迁徙说明与尺寸著录；多源异文并列。 | 按「建议人工动作」复核 tang_04_xuanmita.sourceStone，补证据后再议是否改 claims JSON | evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| ☐ | `song_01_yuanyou:script_style:script` | song_01_yuanyou | conflict、待人工复核 | 对照馆方书体栏、释文标注与目录 scriptType；异文保持并列。 | 打开 song_01_yuanyou 馆方书体栏与目录 scriptType，两侧异文继续并列登记 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| ☐ | `song_02_wenxuan:person:authorEraConflict` | song_02_wenxuan | conflict、待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 打开 song_02_wenxuan 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| ☐ | `song_03_daguan:person:author` | song_03_daguan | 目录pending_review未抬升 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 核目录 song_03_daguan.author Verification=pending_review；无新证据勿抬升为已验证 | 目录 authorVerification=pending_review，claims 未抬升为已验证；缺馆方／公开网页 URL 来源 |
| ☐ | `yuan_01_yufu:style:script` | yuan_01_yufu | conflict、待人工复核 | 对照馆方书体栏、释文标注与目录 scriptType；异文保持并列。 | 打开 yuan_01_yufu 馆方书体栏与目录 scriptType，两侧异文继续并列登记 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 |
| ☐ | `yuan_02_sundeyu:person:authorDispute` | yuan_02_sundeyu | conflict、待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 打开 yuan_02_sundeyu 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| ☐ | `yuan_03_shengzhu:bibliography:authorFieldConflict` | yuan_03_shengzhu | conflict、待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 打开 yuan_03_shengzhu 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺目录字段对照源 |
| ☐ | `yuan_03_shengzhu:person:titleCalligrapher` | yuan_03_shengzhu | 目录pending_review未抬升 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 核目录 yuan_03_shengzhu.titleCalligrapher Verification=pending_review；无新证据勿抬升为已验证 | 目录 titleCalligrapherVerification=pending_review，claims 未抬升为已验证；缺馆方／公开网页 URL 来源 |
| ☐ | `yuan_04_jingyuanchang:person:calligrapher` | yuan_04_jingyuanchang | 目录pending_review未抬升、待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 核目录 yuan_04_jingyuanchang.calligrapher Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |
| ☐ | `yuan_04_jingyuanchang:person:steleSubject` | yuan_04_jingyuanchang | 目录pending_review未抬升、待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 核目录 yuan_04_jingyuanchang.steleSubject Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 steleSubjectVerification=pending_review，claims 未抬升为已验证 |
| ☐ | `ming_02_luxianzhi:work:objectNature` | ming_02_luxianzhi | conflict、待人工复核、reviewFlag（载体性质待人工鉴定） | 对照馆方分类与题跋原文，必要时目验拓本／墨迹载体；确认是否存在原刻层。 | 先按 reviewFlags 目验 ming_02_luxianzhi 载体／鉴定，再决定是否维持 conflict | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；reviewFlags 待消解（载体性质待人工鉴定）；缺馆方／公开网页 URL 来源 |
| ☐ | `ming_03_wugou:script_style:script` | ming_03_wugou | conflict、待人工复核 | 对照馆方书体栏、释文标注与目录 scriptType；异文保持并列。 | 打开 ming_03_wugou 馆方书体栏与目录 scriptType，两侧异文继续并列登记 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| ☐ | `ming_04_tongdian:person:calligrapher` | ming_04_tongdian | conflict、待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 打开 ming_04_tongdian 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| ☐ | `ming_03_wugou:person:steleSubject` | ming_03_wugou | 目录pending_review未抬升 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 核目录 ming_03_wugou.steleSubject Verification=pending_review；无新证据勿抬升为已验证 | 目录 steleSubjectVerification=pending_review，claims 未抬升为已验证 |
| ☐ | `ming_04_tongdian:person:engraver` | ming_04_tongdian | 目录pending_review未抬升 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 核目录 ming_04_tongdian.engraver Verification=pending_review；无新证据勿抬升为已验证 | 目录 engraverVerification=pending_review，claims 未抬升为已验证 |
| ☐ | `qing_02_wushi_reerection:person:engraver` | qing_02_wushi_reerection | conflict、待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 打开 qing_02_wushi_reerection 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| ☐ | `qing_02_wushi_reerection:work:dynasty` | qing_02_wushi_reerection | conflict、待人工复核 | 对照馆方 Period/Culture 标签与刻石纪年、作者生卒；区分遗迹语境标签与本件新刻朝代。 | 打开 qing_02_wushi_reerection 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| ☐ | `qing_04_ayuwang_reliquary:person:engraver` | qing_04_ayuwang_reliquary | conflict、待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 打开 qing_04_ayuwang_reliquary 馆方 Maker／分类页，对照目录角色字段；不定论、不升 Verification | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| ☐ | `qing_01_qianlong_heart_sutra:person:calligrapher` | qing_01_qianlong_heart_sutra | 目录pending_review未抬升、待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 核目录 qing_01_qianlong_heart_sutra.calligrapher Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |
| ☐ | `qing_02_wushi_reerection:person:author` | qing_02_wushi_reerection | 目录pending_review未抬升、待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 核目录 qing_02_wushi_reerection.author Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 authorVerification=pending_review，claims 未抬升为已验证 |
| ☐ | `qing_02_wushi_reerection:person:calligrapher` | qing_02_wushi_reerection | 目录pending_review未抬升、待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 核目录 qing_02_wushi_reerection.calligrapher Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |
| ☐ | `qing_03_sanxitang_preface:person:author` | qing_03_sanxitang_preface | 目录pending_review未抬升、待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 核目录 qing_03_sanxitang_preface.author Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 authorVerification=pending_review，claims 未抬升为已验证 |
| ☐ | `qing_03_sanxitang_preface:person:calligrapher` | qing_03_sanxitang_preface | 目录pending_review未抬升、待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 核目录 qing_03_sanxitang_preface.calligrapher Verification=pending_review；无新证据勿抬升为已验证 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |

## 明细

说明：同一 claim 可同时属于多种开项类型（如 conflict 且待人工复核）。

### han_02_yiying · 乙瑛碑（东汉）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `han_02_yiying:person:calligrapher` | person.calligrapher | conflict、待人工复核 | 「后汉钟太尉书（传统题记；张稚圭按图题记）」 ｜ 「未核定（目录 calligrapher）」 | file:data/catalog/steles28.json:transcription；cat:calligrapher；url:國立故宮博物院 | 待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `han_02_yiying:person:steleSubject` | person.steleSubject | 目录pending_review未抬升 | 主张：乙瑛（字少卿；鲁前相；平原高唐人）——请置卒史之主请人（目录 steleSubjectVerification=pending_review；claims 未抬升为已验证） | file:data/catalog/steles28.json:transcription；url:國立故宮博物院；cat:steleSubject | 有限支持 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 目录 steleSubjectVerification=pending_review，claims 未抬升为已验证 |

### wei_02_wugaoli · 吴高黎墓志（北魏）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `wei_02_wugaoli:date:dayCrossCheck` | date.dayCrossCheck | conflict、待人工复核 | 「碑面作“癸申”（非六十甲子合法干支，疑泐误）」 ｜ 「若丙午朔第13日推算为 戊午」 | file:data/catalog/steles28.json:transcription；url:國立故宮博物院 | 待人工复核 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |

### wei_04_wangsong · 建义元年王诵墓志（北魏）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `wei_04_wangsong:person:author` | person.author | 目录pending_review未抬升 | 主张：李奖（抚军将军顿丘；“辄凭以为铭”）（目录 authorVerification=pending_review；claims 未抬升为已验证） | file:data/catalog/steles28.json:transcription；url:國立故宮博物院；cat:author | 有限支持 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 目录 authorVerification=pending_review，claims 未抬升为已验证 |

### tang_01_duobao · 多宝塔感应碑（唐代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `tang_01_duobao:date:dayCrossCheck` | date.dayCrossCheck | conflict、待人工复核 | 「廿二日戊戌（释文作“戊戍”）」 ｜ 「按“乙丑朔”顺推，廿二日应为丙戌」 | file:data/catalog/steles28.json:transcription | 待人工复核 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 |

### tang_02_jiucheng · 九成宫醴泉铭（唐代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `tang_02_jiucheng:date:visitYear` | date.eventDate | conflict、待人工复核 | 「貞觀六年孟夏之月（碑文）」 ｜ 「贞观七年四月（故宫介绍文字）」 | file:data/catalog/steles28.json:transcription；url:故宫博物院 | 待人工复核 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `tang_02_jiucheng:stone:currentLocation` | stone.currentLocation | conflict、待人工复核 | 「原石在陕西宝鸡麟游（九成宫原地）」 ｜ 「原碑今存于陕西省西安市碑林博物馆」 | url:故宫博物院；url:宝鸡市文物局；url:中国国家博物馆 | 待人工复核 | 对照多家馆方现藏／迁徙说明与尺寸著录；多源异文并列。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `tang_02_jiucheng:stone:dimensions` | stone.dimensions | 待人工复核 | 主张：通高 326 厘米，上宽 89、下宽 98、厚 29 厘米（宝鸡市文物局）；故宫作“碑高2.44m，宽1.18m” | url:宝鸡市文物局；url:故宫博物院 | 待人工复核 | 对照多家馆方现藏／迁徙说明与尺寸著录；多源异文并列。 | evidenceLevel 仍为「待人工复核」，缺人工签核记录 |

### tang_03_yanjiamiao · 颜氏家庙碑（唐代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `tang_03_yanjiamiao:date:ce` | date.ce | conflict、待人工复核 | 「780」 ｜ 「779」 | cat:originalYearCE；cat:originalYear；url:國立故宮博物院 | 待人工复核 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺碑面／释文文件源做干支历表交叉 |
| `tang_03_yanjiamiao:date:yearCrossCheck` | date.yearCrossCheck | conflict、待人工复核 | 「780」 ｜ 「779」 | cat:originalYearCE；url:國立故宮博物院 | 待人工复核 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺碑面／释文文件源做干支历表交叉 |

### tang_04_xuanmita · 玄秘塔碑（唐代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `tang_04_xuanmita:stone:transfer` | stone.transfer | conflict、待人工复核 | 「宋元祐年间移入碑林」 ｜ 「1103 年西安碑林建立之初就移入碑林」 | url:西安碑林博物馆 | 待人工复核 | 对照多家馆方现藏／迁徙说明与尺寸著录；多源异文并列。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `tang_04_xuanmita:style:script` | script_style.script | conflict、待人工复核 | 「楷书」 ｜ 「小楷书（台北故宫品名、封签）」 | cat:scriptType；file:data/catalog/evidence/tang_04_xuanmita.json:officialExtractedText | 待人工复核 | 对照馆方书体栏、释文标注与目录 scriptType；异文保持并列。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 |
| `tang_04_xuanmita:date:gregorianDay` | date.gregorianDay | 待人工复核 | 主张：未换算 | file:data/catalog/steles28.json:transcription | 待人工复核 | 对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 |
| `tang_04_xuanmita:rubbing:sourceStoneIdentity` | rubbing.sourceStone | 待人工复核 | 主张：是否拓自西安碑林原石：未核实 | file:data/catalog/evidence/tang_04_xuanmita.json:officialExtractedText；url:西安碑林博物馆 | 待人工复核 | 对照多家馆方现藏／迁徙说明与尺寸著录；多源异文并列。 | evidenceLevel 仍为「待人工复核」，缺人工签核记录 |

### song_01_yuanyou · 元祐党籍碑（宋代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `song_01_yuanyou:script_style:script` | script_style.script | conflict、待人工复核 | 「楷书（馆方书体栏；目录 scriptType）」 ｜ 「隶书（馆方释文对标题的书体标注）」 | cat:scriptType；url:國立故宮博物院；file:data/catalog/steles28.json:transcription | 待人工复核 | 对照馆方书体栏、释文标注与目录 scriptType；异文保持并列。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |

### song_02_wenxuan · 宋太宗御制至圣文宣王赞碑（宋代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `song_02_wenxuan:person:authorEraConflict` | person.authorEraConflict | conflict、待人工复核 | 「宋太宗（馆方题名／目录）」 ｜ 「大中祥符诏令语境属真宗朝（释文）」 | cat:author；file:data/catalog/steles28.json:transcription；cat:description；url:國立故宮博物院 | 待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |

### song_03_daguan · 大观圣作碑（宋代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `song_03_daguan:person:author` | person.author | 目录pending_review未抬升 | 缺失：内容为御笔诏旨，目录 author 未核定／pending_review；不把“徽宗”或郑居中奏请升为已验证撰人（目录字段 pending_review 未抬升） | cat:author；cat:authorVerification；file:data/catalog/steles28.json:transcription | 未评测 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 目录 authorVerification=pending_review，claims 未抬升为已验证；缺馆方／公开网页 URL 来源 |

### yuan_01_yufu · 大元敕藏御服之碑（元代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `yuan_01_yufu:style:script` | script_style.script | conflict、待人工复核 | 「行楷书（目录、馆方书体栏）」 ｜ 「小楷书（馆方品名）」 | cat:scriptType；file:data/catalog/evidence/yuan_01_yufu.json:officialExtractedText | 待人工复核 | 对照馆方书体栏、释文标注与目录 scriptType；异文保持并列。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺馆方／公开网页 URL 来源 |

### yuan_02_sundeyu · 元重阳宫孙德彧道行碑（元代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `yuan_02_sundeyu:person:authorDispute` | person.authorDispute | conflict、待人工复核 | 「赵文原撰（释文）」 ｜ 「赵孟頫（馆方作者栏，实为书者）」 ｜ 「未核定／disputed（目录）」 | file:data/catalog/steles28.json:transcription；url:國立故宮博物院；cat:authorVerification | 待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |

### yuan_03_shengzhu · 圣主本命长生之碑（元代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `yuan_03_shengzhu:bibliography:authorFieldConflict` | bibliography.authorFieldConflict | conflict、待人工复核 | 「赵孟頫（馆方作者栏）」 ｜ 「王思廉撰 / 赵孟頫书（释文）」 | url:國立故宮博物院；file:data/catalog/steles28.json:transcription | 待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；缺目录字段对照源 |
| `yuan_03_shengzhu:person:titleCalligrapher` | person.titleCalligrapher | 目录pending_review未抬升 | 缺失：释文“書並□□（篆題）”两字残泐；目录标 pending_review／未核定，不升为已验证。赵孟頫兼篆题仅作有限线索，不作定论（目录字段 pending_review 未抬升） | cat:titleCalligrapher；cat:titleCalligrapherVerification；file:data/catalog/steles28.json:transcription | 未评测 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 目录 titleCalligrapherVerification=pending_review，claims 未抬升为已验证；缺馆方／公开网页 URL 来源 |

### yuan_04_jingyuanchang · 赵孟頫书敬元长墓碣铭（元代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `yuan_04_jingyuanchang:person:calligrapher` | person.calligrapher | 目录pending_review未抬升、待人工复核 | 主张：赵孟頫（馆方作者栏；目录 pending_review）（目录 calligrapherVerification=pending_review；claims 未抬升为已验证） | cat:calligrapher；cat:calligrapherVerification；url:國立故宮博物院 | 待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |
| `yuan_04_jingyuanchang:person:steleSubject` | person.steleSubject | 目录pending_review未抬升、待人工复核 | 主张：敬元长（元故太常博士；目录 pending_review）（目录 steleSubjectVerification=pending_review；claims 未抬升为已验证） | cat:steleSubject；cat:steleSubjectVerification；url:國立故宮博物院 | 待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 steleSubjectVerification=pending_review，claims 未抬升为已验证 |

### ming_02_luxianzhi · 文徵明书陆献之墓志铭（明代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `ming_02_luxianzhi:work:objectNature` | work.objectNature | conflict、待人工复核、reviewFlag（载体性质待人工鉴定） | 「拓片（馆方分类）」 ｜ 「墓志草稿（题跋：“此潯州知府陸君墓志草稿”）」 | file:data/catalog/evidence/ming_02_luxianzhi.json:officialExtractedText | 待人工复核 | 对照馆方分类与题跋原文，必要时目验拓本／墨迹载体；确认是否存在原刻层。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录；reviewFlags 待消解（载体性质待人工鉴定）；缺馆方／公开网页 URL 来源 |

### ming_03_wugou · 无垢子何君墓志铭（明代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `ming_03_wugou:script_style:script` | script_style.script | conflict、待人工复核 | 「篆额 + 楷书正文（目录 scriptType）」 ｜ 「篆书（馆方书体栏单值）」 | cat:scriptType；url:國立故宮博物院；file:data/catalog/steles28.json:transcription | 待人工复核 | 对照馆方书体栏、释文标注与目录 scriptType；异文保持并列。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `ming_03_wugou:person:steleSubject` | person.steleSubject | 目录pending_review未抬升 | 主张：何君／无垢子（道全；松浮道人；四明人）（目录 steleSubjectVerification=pending_review；claims 未抬升为已验证） | file:data/catalog/steles28.json:transcription；url:國立故宮博物院；cat:steleSubject | 有限支持 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 目录 steleSubjectVerification=pending_review，claims 未抬升为已验证 |

### ming_04_tongdian · 大峨山永明华藏寺新建铜殿记碑（明代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `ming_04_tongdian:person:calligrapher` | person.calligrapher | conflict、待人工复核 | 「集王羲之书（吴士瑞集字；非王羲之亲书）」 ｜ 「未核定（目录 calligrapher）」 | file:data/catalog/steles28.json:transcription；cat:calligrapher；url:國立故宮博物院 | 待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `ming_04_tongdian:person:engraver` | person.engraver | 目录pending_review未抬升 | 主张：朱廷□（云中；末字泐）（目录 engraverVerification=pending_review；claims 未抬升为已验证） | file:data/catalog/steles28.json:transcription；url:國立故宮博物院；cat:engraver | 有限支持 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 目录 engraverVerification=pending_review，claims 未抬升为已验证 |

### qing_01_qianlong_heart_sutra · 乾隆御书般若波罗蜜多心经（清代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `qing_01_qianlong_heart_sutra:person:calligrapher` | person.calligrapher | 目录pending_review未抬升、待人工复核 | 主张：弘历（乾隆帝；馆方 Maker：Hongli 弘曆, calligrapher；目录 pending_review）（目录 calligrapherVerification=pending_review；claims 未抬升为已验证） | cat:calligrapher；cat:calligrapherVerification；url:Princeton University Art Museum | 待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |

### qing_02_wushi_reerection · 重立武氏祠石记（清代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `qing_02_wushi_reerection:person:engraver` | person.engraver | conflict、待人工复核 | 「郑之宗 / Zheng Zhizong（馆方 carver；目录说明亦称郑之宗刻）」 ｜ 「未核定（目录 engraver）」 | cat:engraver；url:Princeton University Art Museum；file:data/catalog/steles28.json:description | 待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `qing_02_wushi_reerection:work:dynasty` | work.dynasty | conflict、待人工复核 | 「清代（目录；1787年翁方纲新刻记文，非东汉画像石）」 ｜ 「东汉（馆方页面时期标签 Eastern Han dynasty, 25–220 CE）」 | cat:dynasty；file:data/catalog/steles28.json:description；url:Princeton University Art Museum | 待人工复核 | 对照馆方 Period/Culture 标签与刻石纪年、作者生卒；区分遗迹语境标签与本件新刻朝代。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |
| `qing_02_wushi_reerection:person:author` | person.author | 目录pending_review未抬升、待人工复核 | 主张：翁方纲（馆方 author and calligrapher；目录 pending_review）（目录 authorVerification=pending_review；claims 未抬升为已验证） | cat:author；cat:authorVerification；url:Princeton University Art Museum | 待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 authorVerification=pending_review，claims 未抬升为已验证 |
| `qing_02_wushi_reerection:person:calligrapher` | person.calligrapher | 目录pending_review未抬升、待人工复核 | 主张：翁方纲（馆方 author and calligrapher；目录 pending_review）（目录 calligrapherVerification=pending_review；claims 未抬升为已验证） | cat:calligrapher；cat:calligrapherVerification；url:Princeton University Art Museum | 待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |

### qing_03_sanxitang_preface · 御刻三希堂石渠宝笈法帖·乾隆御序（清代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `qing_03_sanxitang_preface:person:author` | person.author | 目录pending_review未抬升、待人工复核 | 主张：弘历（乾隆帝；目录 pending_review；Met 全套署 Various artists，不否定御序作者栏）（目录 authorVerification=pending_review；claims 未抬升为已验证） | cat:author；cat:authorVerification；url:The Metropolitan Museum of Art | 待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 authorVerification=pending_review，claims 未抬升为已验证 |
| `qing_03_sanxitang_preface:person:calligrapher` | person.calligrapher | 目录pending_review未抬升、待人工复核 | 主张：弘历（乾隆帝；目录 pending_review）（目录 calligrapherVerification=pending_review；claims 未抬升为已验证） | cat:calligrapher；cat:calligrapherVerification；url:The Metropolitan Museum of Art | 待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | evidenceLevel 仍为「待人工复核」，缺人工签核记录；目录 calligrapherVerification=pending_review，claims 未抬升为已验证 |

### qing_04_ayuwang_reliquary · 阿育王寺舍利塔碑（清代）

| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 | 证据缺口 |
|---|---|---|---|---|---|---|---|
| `qing_04_ayuwang_reliquary:person:engraver` | person.engraver | conflict、待人工复核 | 「授轮、圆伦、谛受、道修（馆方 carving agent／碑阴署仝募刊；募刊≠传统刻工身份待复核）」 ｜ 「未核定（目录 engraver）」 | cat:engraver；url:Princeton University Art Museum | 待人工复核 | 对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。 | 异文并存，尚无足以定论的单源权威；evidenceLevel 仍为「待人工复核」，缺人工签核记录 |

## 维护约定

1. 新增／关闭开项时：先改对应 `data/catalog/claims/<id>.json`，再运行 `python scripts/check_claims_open_issues.py --check`（或 `--write` 重生成本文件）。
2. 关闭条件须人工确认；脚本不自动消除 conflict／待人工复核。
3. C-08 主库禁止 `--apply`；本台账不触发目录或 SQLite 写回。
4. 用语：写「claim 文件 28/28，开项 N 条」；勿写「收官关闭／冲突全部关闭」。
5. JS-4／JS-5：本文件「冲突并列一览」与「待人工复核工作清单」为呈现与人工排期用；claim 文件 28/28 + 开项台账/--check 已闭环功能，但开项仍开放（不等于史实定论关闭）。
6. 「人工复核提示（按核对队列）」为排期队列（Q1–Q4）：只提示下一步核对与证据缺口，不关闭、不定论、不合并异文。

