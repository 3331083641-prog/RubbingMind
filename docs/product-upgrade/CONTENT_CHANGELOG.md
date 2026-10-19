# CONTENT_CHANGELOG — 金石内容修正记录

- 作者：RM-金石史料（Agent 03/06/07）
- 分支：`agent/jinshi`（基于 `feature/product-grade-upgrade@f0c5886`）
- 规则：每条史实修改都附来源 URL（真实打开过的页面）；查不到的写“未核实”，不补写。时间为 Asia/Shanghai。
- 对应审计：`docs/product-upgrade/AUDIT_CONTENT.md`（C-xx 编号）

## 2026-10-19 12:40 · C-03 合成测试文本标记（wei-jianyi）

| 位置 | 修改前 | 修改后 | 依据 |
|---|---|---|---|
| `data/catalog/core_samples.json` 与 `apps/web/src/data/coreSamples.json`（两份逐字节一致）· wei-jianyi | `translation`、`inferenceDemo.transcript` 是“夫人諱某，昌黎人也……”，无任何标记 | 文首加“【合成测试文本（sample_generator 生成，非真实释文）】”；新增 `textProvenance`（kind=`synthetic_test_text`，isAuthenticInscription=false）；`damaged_summary`、`summary` 开头加同一标签；35 个字符加 `textKind`；badges 加“合成测试文本” | `sample_generator.py` `SAMPLE_SOURCES["sample_4.png"].lines` 与该文本逐字相同（项目内部来源，不是史料）；审计 C-03 |
| `data/history/wei-jianyi.json` | `identity` 与主节点 `desc` 没有说明文本是合成的 | `identity`、主节点 `desc` 开头加标签；新增 `textProvenance` | 同上 |
| `evidence_retrieval.py` | wei-jianyi 的证据条目没有标记 | 条目 `text` 开头加标签，并带 `textProvenance`；回答中命中这类条目时，开头加“注意：检索结果含合成测试文本……不能作为史料证据”；响应新增 `contentWarnings`；索引版本升到 v2.4（指纹变化后自动重建，旧索引不受影响） | 同上 |
| 前端 `WorkbenchPage.tsx` / `HomePage.tsx` / `EvidenceSearch.tsx` / `types/stele.ts` | 没有标记 | 工作台顶部提示、字符区标题、首页卡片、检索证据标题和警示行都显示标签；类型只加可选字段 | 同上 |
| `sample_generator.py`、`knowledge_agent.py`（sample_4） | 没有标记 | 加常量 `SYNTHETIC_TEXT_LABEL` 和 `text_provenance` 字段；生成器逻辑不变，也没有删除 | 同上 |

## 2026-10-19 · C-02 演示样本史实：改为来源支持、未核实或多说并列

本节所有修改同时作用于 `data/catalog/core_samples.json` 和 `apps/web/src/data/coreSamples.json`，两份保持逐字节一致。每件新增 `factSources`，列出字段、证据等级、URL、引文；没有来源的条目 URL 为 null，并写明原因。

| 样本 · 字段 | 修改前 | 修改后 | 来源 |
|---|---|---|---|
| tang-duobao · year/originalYear | 公元 752 年 5 月 | 752 年（天宝十一载；馆方记“四月建”，公历月日未核实） | 西安碑林博物馆“多宝塔感应碑”：“唐天宝十一载(752)四月建” https://www.beilin-museum.com/index.php?a=index&aid=147&c=View&m=home |
| tang-duobao · location | 西安碑林博物馆第一室 | 原石现藏西安碑林博物馆（陈列室号未核实） | 同上：“北宋崇宁二年（1103）移存西安碑林”；“第一室”无来源 |
| tang-duobao · author | 颜真卿（书丹，琅琊临沂） | 岑勋（撰文）；颜真卿（书丹）；徐浩（题额） | 同上：“岑勋撰文，徐浩题额，颜真卿……书丹” |
| han-caoquan · location | 西安碑林博物馆第三室 | 原石现藏西安碑林博物馆（陈列室号未核实） | 西安碑林博物馆“曹全碑”：“1956年移存西安碑林” https://www.beilin-museum.com/index.php?a=index&aid=145&c=View&m=home |
| han-caoquan · author/calligrapher | 汉代书吏（无名氏，典型东汉八分书） | 未核实（书写者未见馆方著录） | 无来源，不补写 |
| han-caoquan · translation 节录 | ……遷郃陽令。 | ……轉拜郃陽令。（**异文**：演示节录作“遷”，馆方释文作“轉拜”，按馆方释文改，两说都记在这里） | 台北故宫“汉曹全碑墨拓本（购拓000033）” https://digitalarchive.npm.gov.tw/Collection/Detail/34589?dep=P （本轮未能在线复核，依据仓库 `steles28.json` han_01_caoquan 的馆方释文抽取：“于時聖主諮諏。羣僚咸曰。君哉。轉拜郃陽令。”） |
| wei-yuanhuai · location | 开封市博物馆（1925年洛阳邙山出土） | 未核实，两说并列：现藏“开封市博物馆”／“河南博物院（1996年自开封市博物馆调拨）”；出土地“河南省孟津县张阳村”／“洛阳张羊村” | 百度百科“元怀”：“1925年3月，出土于河南省孟津县张阳村元怀墓中，现藏开封市博物馆。” https://baike.baidu.com/item/%E5%85%83%E6%80%80/10330461 ；搜狐转载：“原藏河南开封市博物馆……1996年河南博物院从开封市博物馆调去了10多件刻石精品，《元怀墓志》也在其中。” https://www.sohu.com/a/818047024_121124391 ；期刊网摘要：“1925年河南洛阳张羊村出土，原石现藏河南博物院” https://www.qikanchina.com/thesis/detail/1262393 （审计阶段打开过，本轮复查返回 403）。三者都是二手资料，等级为“有限支持”；河南博物院官方页面未能核实 |
| wei-yuanhuai · year/originalYear | 公元 517 年 4 月 27 日 | 517 年（熙平二年；志文记“三月廿六日丁亥薨”“秋八月廿日窆”，公历月日未核实） | 搜狐转载志文同上 URL。**异文**：原演示“517年4月27日”无来源；百度百科写逝世日期“517年5月2日”。两说均未核实 |
| wei-yuanhuai · author/calligrapher | 北魏宗室御用书家 | 未核实（二手资料称志石“无撰书人乡名”） | 搜狐转载同上 URL：“无撰书人乡名。” |
| wei-yuanhuai · 世次（只在 factSources 注明，志文不改） | — | 志文作“高祖孝文皇帝之第四子”；百度百科作“孝文帝元宏第五子”；刘军论文记“第四/第五子表述有异”。原样保留两说 | https://ygx.sxu.edu.cn/db/%E6%9C%9F%E5%88%8A/gdwm/gdwm2013/1304pdf/1304009.pdf ；百度百科同上 |
| wei-jianyi · author/location/year | 北朝民间刻工／洛阳古墓博物馆石刻馆／公元 528 年 | 无（合成测试样本，不对应真实文物）；年份改为“测试标签：528，非已核实文物纪年” | 合成测试样本，见 C-03 |
| `data/history/sources.json` | — | 新增 `baike-yuanhuai`、`sohu-yuanhuai`（status=`limited_support`） | 同上两个 URL |
| `data/history/wei-yuanhuai.json` | originalStoneCollection=待考；yuan-tomb 的 note 不列异文 | originalStoneCollection 两说并列；yuan-tomb 的 note 列出张阳村和张羊村两种写法，坐标仍为空；sourceIds 加入两个新来源 | 同上 |
