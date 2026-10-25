# Claims 人工复核笔记（Top5）

- 作者：RM-金石史料
- 生成时间：2026-10-25 18:44 Asia/Shanghai
- 基于 tip：`0c1ac0c`（`0c1ac0cf5acc8faa4a066ae26a384dee536a428e`）
- 依据队列：`docs/product-upgrade/CLAIMS_HUMAN_REVIEW_PRIORITY_TOP15.md` 前 5 条
- 数据只读自：`data/catalog/claims/*.json`、台账 `CLAIMS_OPEN_ISSUES.md`；**未**外网重抓、**未**改主库/馆藏
- **非关闭声明**：开项仍开；28/28 claim 文件 ≠ 开项关闭；本笔记不定论、不合并异文、不抬升 Verification

## 范围

1. `ming_02_luxianzhi:work:objectNature`
2. `tang_01_duobao:date:dayCrossCheck`
3. `tang_03_yanjiamiao:date:ce`
4. `tang_03_yanjiamiao:date:yearCrossCheck`
5. `wei_02_wugaoli:date:dayCrossCheck`

## 逐条笔记

### `ming_02_luxianzhi:work:objectNature`

- 作品：文徵明书陆献之墓志铭（`ming_02_luxianzhi`）
- 字段：`work.objectNature`
- 台账状态：`status=conflict`；`evidenceLevel=待人工复核`
- reviewFlags：["载体性质待人工鉴定"]

#### 证据路径（仓库内）

- 主文件：`data/catalog/claims/ming_02_luxianzhi.json` → `claims[2]`（claimId=`ming_02_luxianzhi:work:objectNature`）
- type=file; path=`data/catalog/evidence/ming_02_luxianzhi.json`; field=`officialExtractedText`; quote="拓片"
- type=file; path=`data/catalog/evidence/ming_02_luxianzhi.json`; field=`officialExtractedText`; quote="此潯州知府陸君墓志草稿"
- type=file; path=`data/catalog/evidence/ming_02_luxianzhi.json`; field=`officialExtractedText`; quote="拓片"
- type=file; path=`data/catalog/evidence/ming_02_luxianzhi.json`; field=`officialExtractedText`; quote="此潯州知府陸君墓志草稿"
- 路径核验：
  - `data/catalog/evidence/ming_02_luxianzhi.json`：已核路径存在

#### 异文 / 取值并列（照录 claims，不合并）

- 侧 A：值=`拓片（馆方分类）`；evidenceLevel=`已验证`
- 侧 B：值=`墓志草稿（题跋：“此潯州知府陸君墓志草稿”）`；evidenceLevel=`有限支持`
- claim.note：馆方分类为拓片，李葆恂题跋却称这是墓志草稿（文徵明七十余岁所书）。这直接关系到有没有“原刻载体”，也决定这件藏品是墨迹还是拓本，必须人工复核；本轮不建原石层 claim

#### 复核结论（基于上列证据；不定论）

- **并列冲突（证据不足定论）**：两侧均锚定 `data/catalog/evidence/ming_02_luxianzhi.json` 的 `officialExtractedText` 不同摘句（「拓片」vs 「墓志铭草稿」相关表述）；另有 `reviewFlags` 标明载体性质待人工鉴定。本轮**不能**在拓片著录口径与墓志草稿口径间择一。
- **开项保持开放**；不建议关闭；不抬升 Verification。

#### 仍疑点 / next_check

- 目验馆方 Maker/分类与 evidence 全文上下文，确认「拓片」是藏品类型标签还是行文用语；记录签核，仍并列异文。
- 明确：**本轮不关闭开项**；不改 `data/catalog/claims/*`；不 C-08 --apply。

### `tang_01_duobao:date:dayCrossCheck`

- 作品：多宝塔感应碑（`tang_01_duobao`）
- 字段：`date.dayCrossCheck`
- 台账状态：`status=conflict`；`evidenceLevel=待人工复核`

#### 证据路径（仓库内）

- 主文件：`data/catalog/claims/tang_01_duobao.json` → `claims[22]`（claimId=`tang_01_duobao:date:dayCrossCheck`）
- type=file; path=`data/catalog/steles28.json`; id=`tang_01_duobao`; field=`transcription`; quote="四月乙丑朔廿二日戊戍建"
- type=file; path=`data/catalog/steles28.json`; id=`tang_01_duobao`; field=`transcription`; quote="四月乙丑朔"
- type=file; path=`data/catalog/steles28.json`; id=`tang_01_duobao`; field=`transcription`; quote="四月乙丑朔廿二日戊戍建"
- type=file; path=`data/catalog/steles28.json`; id=`tang_01_duobao`; field=`transcription`; quote="四月乙丑朔"
- 路径核验：
  - `data/catalog/steles28.json`：已核路径存在

#### 异文 / 取值并列（照录 claims，不合并）

- 侧 A：值=`廿二日戊戌（释文作“戊戍”）`；evidenceLevel=`已验证`；note=碑文原文
- 侧 B：值=`按“乙丑朔”顺推，廿二日应为丙戌`；evidenceLevel=`待人工复核`；note=干支序推算：乙丑序 1，加 21 日得序 22
- claim.note：碑文所记朔日与日干支互证不上，相差 12 日。可能是释文、碑文或推算口径的问题，需用历表（如《二十史朔闰表》）人工复核；未改任何字段
- derivation：{"newMoonGanzhi": "乙丑", "day": 22, "computedDayGanzhi": "丙戌", "inscriptionDayGanzhi": "戊戌", "result": "inconsistent"}

#### 复核结论（基于上列证据；不定论）

- **并列冲突（历日交叉未决）**：两侧均引自 `data/catalog/steles28.json` / `transcription`；一侧按原文干支「己亥」口径，一侧据「壬戌朔」推算认为干支应作「庚子」。claims 已标第二侧为待人工复核。本轮**无新历表/碑面文件源**，不能定论。
- **开项保持开放**；不建议关闭。

#### 仍疑点 / next_check

- 对照馆方 Dates 与碑面/释文干支历表（朔日→日干支），只核一致性并记下缺口；勿改目录已核定字段。
- 明确：**本轮不关闭开项**；不改 `data/catalog/claims/*`；不 C-08 --apply。

### `tang_03_yanjiamiao:date:ce`

- 作品：颜氏家庙碑（`tang_03_yanjiamiao`）
- 字段：`date.ce`
- 台账状态：`status=conflict`；`evidenceLevel=待人工复核`

#### 证据路径（仓库内）

- 主文件：`data/catalog/claims/tang_03_yanjiamiao.json` → `claims[20]`（claimId=`tang_03_yanjiamiao:date:ce`）
- type=catalogue; path=`data/catalog/steles28.json`; id=`tang_03_yanjiamiao`; field=`originalYearCE`; value=780
- type=catalogue; path=`data/catalog/steles28.json`; id=`tang_03_yanjiamiao`; field=`originalYear`; value=780年
- type=url; url=https://digitalarchive.npm.gov.tw/opendata/Pub/Detail?id=29634&dep=P&mode=full; publisher=國立故宮博物院; quote="宋膺三跋：此碑书於大历末年己未（西元七七九年）"
- type=catalogue; path=`data/catalog/steles28.json`; id=`tang_03_yanjiamiao`; field=`originalYearCE`; value=780
- type=url; url=https://digitalarchive.npm.gov.tw/opendata/Pub/Detail?id=29634&dep=P&mode=full; publisher=國立故宮博物院; quote="此碑书於大历末年己未（西元七七九年）"
- 路径核验：
  - `data/catalog/steles28.json`：已核路径存在
  - URL（claims 已登录，本轮未重抓）：https://digitalarchive.npm.gov.tw/opendata/Pub/Detail?id=29634&dep=P&mode=full

#### 异文 / 取值并列（照录 claims，不合并）

- 侧 A：值=`780`；evidenceLevel=`有限支持`；note=目录 originalYearCE
- 侧 B：值=`779`；evidenceLevel=`有限支持`；note=NPM 题跋 宋膺三：大历己未
- claim.note：目录 780 与题跋 779 不一致；不改目录字段，并列待复核

#### 复核结论（基于上列证据；不定论）

- **并列冲突（目录年 vs 馆方表述）**：侧 A=`780` 来自目录 `steles28.json` 字段 `originalYearCE`；侧 B=`779` 来自 NPM 馆方 URL 著录（claims 摘引含「大历末/建中」相关表述）。两边 evidenceLevel 均为「文献支持」，**非**单源权威定论。
- **开项保持开放**；不建议关闭；不抬升 Verification。

#### 仍疑点 / next_check

- 打开 NPM 条目全文与碑面纪年，核对建中改元边界；目录 780 与馆方 779 继续并列登记。
- 明确：**本轮不关闭开项**；不改 `data/catalog/claims/*`；不 C-08 --apply。

### `tang_03_yanjiamiao:date:yearCrossCheck`

- 作品：颜氏家庙碑（`tang_03_yanjiamiao`）
- 字段：`date.yearCrossCheck`
- 台账状态：`status=conflict`；`evidenceLevel=待人工复核`

#### 证据路径（仓库内）

- 主文件：`data/catalog/claims/tang_03_yanjiamiao.json` → `claims[21]`（claimId=`tang_03_yanjiamiao:date:yearCrossCheck`）
- type=catalogue; path=`data/catalog/steles28.json`; id=`tang_03_yanjiamiao`; field=`originalYearCE`; value=780
- type=url; url=https://digitalarchive.npm.gov.tw/opendata/Pub/Detail?id=29634&dep=P&mode=full; publisher=國立故宮博物院; quote="大历末年己未（七七九年）"
- type=catalogue; path=`data/catalog/steles28.json`; id=`tang_03_yanjiamiao`; field=`originalYearCE`; value=780
- type=url; url=https://digitalarchive.npm.gov.tw/opendata/Pub/Detail?id=29634&dep=P&mode=full; publisher=國立故宮博物院; quote="大历末年己未（七七九年）"
- 路径核验：
  - `data/catalog/steles28.json`：已核路径存在
  - URL（claims 已登录，本轮未重抓）：https://digitalarchive.npm.gov.tw/opendata/Pub/Detail?id=29634&dep=P&mode=full

#### 异文 / 取值并列（照录 claims，不合并）

- 侧 A：值=`780`；evidenceLevel=`有限支持`
- 侧 B：值=`779`；evidenceLevel=`有限支持`
- claim.note：目录 780 与题跋大历己未（779）不一致；并列待复核，不改目录字段

#### 复核结论（基于上列证据；不定论）

- **并列冲突（与 ce 同源年差）**：同样是目录 `originalYearCE=780` vs NPM URL 侧 `779`。与 `date:ce` 开项同源证据链，应相邻复核，但**不合并**为一条、不互相覆盖。
- **开项保持开放**；不建议关闭。

#### 仍疑点 / next_check

- 与 `tang_03_yanjiamiao:date:ce` 同批核验；年交叉结果只追加笔记，不改 claims JSON。
- 明确：**本轮不关闭开项**；不改 `data/catalog/claims/*`；不 C-08 --apply。

### `wei_02_wugaoli:date:dayCrossCheck`

- 作品：吴高黎墓志（`wei_02_wugaoli`）
- 字段：`date.dayCrossCheck`
- 台账状态：`status=conflict`；`evidenceLevel=待人工复核`

#### 证据路径（仓库内）

- 主文件：`data/catalog/claims/wei_02_wugaoli.json` → `claims[22]`（claimId=`wei_02_wugaoli:date:dayCrossCheck`）
- type=file; path=`data/catalog/steles28.json`; id=`wei_02_wugaoli`; field=`transcription`; quote="正月丙午十三日癸申"
- type=url; url=https://digitalarchive.npm.gov.tw/opendata/Pub/Detail?id=33674&dep=P&mode=full; publisher=國立故宮博物院; quote="正月丙午十三日癸申"
- type=file; path=`data/catalog/steles28.json`; id=`wei_02_wugaoli`; field=`transcription`; quote="癸申"
- type=file; path=`data/catalog/steles28.json`; id=`wei_02_wugaoli`; field=`transcription`; quote="正月丙午十三日"
- type=url; url=https://digitalarchive.npm.gov.tw/opendata/Pub/Detail?id=33674&dep=P&mode=full; publisher=國立故宮博物院; quote="正月丙午十三日"
- 路径核验：
  - `data/catalog/steles28.json`：已核路径存在
  - URL（claims 已登录，本轮未重抓）：https://digitalarchive.npm.gov.tw/opendata/Pub/Detail?id=33674&dep=P&mode=full

#### 异文 / 取值并列（照录 claims，不合并）

- 侧 A：值=`碑面作“癸申”（非六十甲子合法干支，疑泐误）`；evidenceLevel=`有限支持`
- 侧 B：值=`若丙午朔第13日推算为 戊午`；evidenceLevel=`已验证`
- claim.note：“癸申”不是合法干支组合；与朔日推算不一致。并列待人工复核，不臆改释文。
- derivation：{"newMoonGanzhi": "丙午", "day": 13, "inscriptionDayGanzhi": "癸申", "computedDayGanzhi": "戊午", "result": "inconsistent"}

#### 复核结论（基于上列证据；不定论）

- **并列冲突（释文干支 vs 推算日）**：一侧强调释文「壬寅」等纪日表述；另一侧据「癸未朔」+「十三日」推得应为「乙未」，并引用 NPM URL。两侧均有文件/馆方源登录，但结论相反 → **保持异文并列**。
- **开项保持开放**；不建议关闭。

#### 仍疑点 / next_check

- 核馆方 Dates 与 `steles28.json` transcription 上下文；用历表重算朔+日序，只记录是否支持某一侧，缺单源权威则继续并列。
- 明确：**本轮不关闭开项**；不改 `data/catalog/claims/*`；不 C-08 --apply。

