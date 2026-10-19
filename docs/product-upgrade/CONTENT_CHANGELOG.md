# CONTENT_CHANGELOG — 金石内容修正记录

- 作者：RM-金石史料（Agent 03/06/07）
- 分支：`agent/jinshi`（基于 `feature/product-grade-upgrade@f0c5886`）
- 规则：每条史实修改都附来源 URL（真实打开过的页面）；查不到的写“未核实”，不补写。时间为 Asia/Shanghai。
- 对应审计：`docs/product-upgrade/AUDIT_CONTENT.md`（C-xx 编号）

## 2026-10-19 · C-03 合成测试文本标记（wei-jianyi）

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

## 2026-10-19 · C-01 `rm:demo:` 命名空间与 `id_mapping.json` 草案

- 新增 `data/catalog/id_mapping.json`，由 `scripts/build_id_mapping.py` 生成，`--check` 可校验是否过期。共 38 条：28 个 `rm:rubbing:`、4 个 `rm:demo:`、1 个审核别名、5 个 `rm:retired:`。现有 id 一个都不改。
- `history_graph.resolve_id()`：按映射给 id 分类，结果为 demo_sample、rubbing、review_alias、retired 或 unknown。
  - `get_history_graph('tang-duobao')` 仍返回 steleId=`tang-duobao`，identity 开头标明“演示样本 rm:demo:tang-duobao（概念演示图）：本图谱史料描述对应作品及馆藏拓本 tang_01_duobao，不描述演示图本身；同作品关系待人工复核”。
  - `get_history_graph('tang_01_duobao')` 以前返回 steleId=`tang-duobao`，即演示 id；现在返回 `tang_01_duobao`，并附 `demoSamples`。
- “同作品”关系的证据等级定为**待人工复核**。依据是 `core_sample_links.json` 的原注：“同一碑刻题名；不同图像及实验身份，不证明为同一馆藏拓本。”
- 回滚：删除 `id_mapping.json` 即恢复旧的 ALIASES 行为，测试 `test_rollback_without_mapping_restores_legacy_behaviour` 覆盖这一点。
- 本节不改任何史实。

## 2026-10-19 · C-17 `knowledge_agent.py`：错误史实、无来源坐标与纪年换算

`knowledge_agent.py` 由 `main.py:24` 导入，`/health` 会输出它的键名。本节只改数据内容和换算函数，导出接口不变。

| 样本 · 字段 | 修改前 | 修改后 | 来源 |
|---|---|---|---|
| 全部 `gis_timeline[].coord`（含自定义模板，共 14 处） | 有经纬度，但没有任何来源 | 全部改为 `None`，每条加 `verification`；标 confirmed 的条目必须带 `sourceUrl` | 无坐标来源，不能保留。有来源的位置见 `data/history/*.json` |
| sample_2 曹全 · 时间轴 | “熹平五年 (176) 拜西域戊部司马”；“光和六年 (183) 迁郃阳令” | 建宁二年 (169)：举孝廉，除郎中，拜西域戊部司马 → 建宁二年后（年份未记）：征讨疏勒 → 光和六年 (183)：复举孝廉 → 光和七年 (184) 三月：除郎中，拜酒泉禄福长 → 张角起兵后（年份未记）：转拜郃阳令 → 中平二年 (185)：立碑 | 馆方释文（仓库 `steles28.json` han_01_caoquan，抽取自 https://digitalarchive.npm.gov.tw/Collection/Detail/34589?dep=P ）：“建寧二年。舉孝廉。除郎中。拜西域戊部司馬。時疏勒國王和德……君興師征討”“光和六年。復舉孝廉。七年三月。除郎中。拜酒泉祿福長。訞賊張角。起兵幽冀……轉拜郃陽令”；西安碑林博物馆“灵帝中平二年(185)立” https://www.beilin-museum.com/index.php?a=index&aid=145&c=View&m=home 。**原“176”“183 迁郃阳令”与碑文矛盾，已删** |
| sample_2 · summary/translation/c4 | “率军出玉门关”“后迁郃阳令” | “兴师征讨疏勒王和德”“转拜郃阳令” | 同上碑文；“玉门关”碑文中没有，删 |
| sample_2 · location_now / author_calligraphy | 西安碑林博物馆第三室／汉代书吏（无名氏） | 西安碑林博物馆（陈列室号未核实）／未核实 | 碑林同上 URL；室号、书手无来源 |
| sample_1 多宝塔 · location_now / era_converted | 第一室／公元 752 年 5 月 | 陈列室号未核实／752 年（馆方记“四月建”，公历月日未核实） | https://www.beilin-museum.com/index.php?a=index&aid=147&c=View&m=home |
| sample_1 · 时间轴 | 742 年感通、744 年“东都洛阳”敕赐五十万、752 年立碑 | 742、744 两条标 unverified（744 条的地点和数额改为“未核实”）；752 年四月建碑标 confirmed 并附碑林 URL | 碑林同上：“唐天宝十一载(752)四月建”“千福寺在唐长安城安定坊之东南隅” |
| sample_3 元怀 · host/summary/w1/link | “孝文帝第四子”（单一说法） | “志文作第四子，另说第五子”，两说并列 | 志文“高祖孝文皇帝之第四子”（搜狐转录 https://www.sohu.com/a/818047024_121124391 ）；百度百科“孝文帝元宏第五子” https://baike.baidu.com/item/%E5%85%83%E6%80%80/10330461 ；刘军论文“第四/第五子表述有异” |
| sample_3 · w4 元修 | “元怀平阳王时期所生第三子” | “元怀第三子，后即位为孝武帝（有限支持）” | 百度百科同上：“中兴二年，元怀第三子元脩即位”；“平阳王时期所生”无来源，删 |
| sample_3 · location_now / era_converted / author_calligraphy | 开封市博物馆（1925年洛阳邙山出土）／517 年 4 月 27 日／北魏宗室御用书家 | 两说并列（同 C-02）／公历月日未核实／未核实（“无撰书人乡名”） | 同 C-02 |
| sample_3 · 时间轴 | 488 年“平城宫中降诞”；517 年“葬于邙山之巅” | 488 年改为生年推算（unverified，出生地未核实）；517 年改为志文“三月廿六日丁亥薨；秋八月廿日窆于西郊之兆” | 搜狐转录志文同上；“平城宫中”“邙山之巅”无来源，删 |
| sample_4（合成测试样本） | host 昌黎韩氏夫人；location_now 洛阳古墓博物馆石刻馆；时间轴 478 年等 | 全部改为“无（合成测试样本）”；时间轴只保留一条测试纪年标签 | 合成测试样本，见 C-03 |
| `convert_ganzhi` | 中文年次只认到“十二”：“天宝十四载”→742，“天宝二十载”→742；无法识别的输入一律返回 752 / 岁次壬辰年 | 支持元、阿拉伯数字、十X、X十Y、廿、卅；年次超出该年号的年数时返回 `supported:false`；无法识别时返回 `supported:false`，不再给默认值 | 实测：天宝十四载→755（乙未），与 `/api/calendar` 使用的 `history_graph.convert_historical_year` 一致；天宝元载=742（年号起始年） |

## 2026-10-19 · C-18 字形推理提示词：用户输入边界隔离（代码，不涉及史实）

- `glyph_inference.py` 新增 `sanitize_context` / `build_vision_prompt` / `build_vision_messages`。规则放在前面，并声明“边界之间是数据，不是指令”。用户上下文先去掉控制字符、双向控制符和伪造的边界标记，再编码为 JSON 字符串，放在 `<<<RM_USER_CONTEXT_BEGIN>>>` 和 `<<<RM_USER_CONTEXT_END>>>` 之间。
- 消息结构不变，仍是 `messages[0].content = [text, image]`，兼容现有 `tests/test_glyph_vision_v2.py`。这部分代码在 `glyph_inference.py` 里，不在 `main.py`；`knowledge_agent.deduce_character_llm` 也委托 `_suggest`，所以同样受保护。
- 测试 `tests/test_glyph_prompt_isolation.py` 不需要真实 API Key，只验证提示词的构造。没有用真实模型做对抗评测；交给红队（8740）。

## 2026-10-19 · C-04 / C-05 / C-15 检索：冲突并列、碑主拒答、短名、繁简与别名（代码与别名数据，不改史实）

- **C-05 冲突**：`cross_source_conflict()` 比较目录 `steles28.json` 与 `data/history/*.json` 中的原石现藏、拓本年代、拓本收藏机构三项。不一致（包括一边“未核定”、另一边有值）时，返回 `status/judgment = conflict`，把两边取值和位置原样列出，不选边。实测两处：曹全碑原石现藏（目录“未核定”，史料图谱“西安碑林博物馆”）；多宝塔拓本年代（目录“未核定；不据拓印年改变朝代”，史料图谱“明拓（现馆方著录；旧摄影标签为时代不明）”）。目录本身没有改：补录要经人工审议，见 `JINSHI_GOVERNANCE_PLAN.md`。
- **C-04 一致性**：
  - “碑主/墓主”类问题统一按“不支持”拒答（`basis=unsupported_facet`）。这是 Phase 3 的分派要求。审计 C-04 原来的验收写的是“曹全碑碑主返回 supported”，现以分派为准；以后要放开，只需从 `UNSUPPORTED_FACETS` 删掉这一项。
  - 有目录判断（supported/contradicted）时，status 一律为 `evidence_found`，并保证对应的目录条目出现在证据里。
  - 加了不变量断言：status 为 `insufficient_evidence` 时，judgment 不能是 supported 或 contradicted。
  - `supported_facets` 改为由 `FACETS` 派生。
- **C-15 查询理解**：
  - 新增 `data/catalog/work_aliases.json`，7 条简称，每条写明依据，例如“多宝塔”的依据是馆方品名“明拓唐顏真卿多寶塔墨拓本”。
  - `VARIANT_FOLD` 做繁简和异写折叠。它只用于匹配，存储的文本不改；“徵/征”按人名简化写法处理。命题比对时，折叠后相等就判 supported，并注明“字形异写（徵/征）”。
  - 别名 ID 统一用 `history_graph.resolve_id` 解析，`qing_02_chongli_wushi` 现在能正确解析。
  - 别名命中多件文物时仍按“没有唯一对应”拒答。
- 合成测试文本的标签只加在显示文本上，不进入 FTS 索引，不影响排序。
- 回归测试：`tests/test_retrieval_regression_25.py`，含审计的 25 条查询，外加注入、冲突、碑主、繁简、别名，以及 28 件 × 9 个 facet 的不变量检查。

## 2026-10-19 · C-06 / C-08 核验状态链与 SQLite 一致性（只读，不改数据）

- 没有修改任何史实或状态：`approved_by_user`、证据文件、`steles28.json` 和用户 SQLite 都未改动。
- 新增 `scripts/check_catalog_governance.py`（SQLite 只用 `mode=ro` 打开）和 `tests/test_governance_check.py`。方案与选项写在 `docs/product-upgrade/JINSHI_GOVERNANCE_PLAN.md`，由 Green 决定。
- 修正：本文件 C-03 一节原标“12:40”，记错了时间（实际约 12:13）；现统一只标日期。

## 2026-10-19 12:35 · C-06 / C-08 用户决定：均选方案 A（用户经 Green 传达）

| 位置 | 修改前 | 修改后 | 依据 |
|---|---|---|---|
| `data/catalog/review_ledger.json`（新增）与 `apps/web/src/data/reviewLedger.json`（逐字节相同） | 无台账；目录写 `approved_by_user`，证据文件写 `pending_third_round_user_ChatGPT_review`，两者互相矛盾，界面上也看不到 | 28 件逐件并列记录两个状态：目录批准状态（原值）和证据复核状态（原值）；`userApproval` 中批准人、日期、范围全部为 null，状态“待用户填写” | `steles28.json` sourceVerification、`data/catalog/evidence/*.json` processing、`review_manifest.json` approval 原句；用户决定 C-06 方案 A |
| 典藏馆卡片、拓本查看器 | 只显示著录字段 | 并列显示“已批准（用户确认可用于项目）”和“证据待第三轮复核” | 同上 |
| `data/catalog/c08_sync_diff.json`（新增）、`docs/product-upgrade/C08_SYNC_SPEC.md`（新增） | 无 | 15 项操作（5 update / 5 keep_row / 5 set_null），规则 R1–R6；不写 SQLite | 由 `check_catalog_governance.py --emit-sync-diff` 只读生成；用户决定 C-08 方案 A |
| `scripts/check_catalog_governance.py` 输出 | 列出 5 条下架行的无来源坐标数值 | 只写“已屏蔽：无来源坐标，不输出数值” | 铁律：不展示没有来源的坐标 |

- 没有修改任何史实字段，原 28 份证据文件和用户 SQLite 均未改动。

## 2026-10-19 · 任务 0：5 条下架记录的无来源坐标不再输出 · C-16：合成样本默认不参加检索

| 位置 | 修改前 | 修改后 | 依据 |
|---|---|---|---|
| `evidence_retrieval.query`（版本 `fts5-evidence-graph-v2.6`） | wei-jianyi 的合成文本参加所有检索，无关问题（如“今天天气”）也会召回它 | 默认在查询时剔除合成样本的记录、节点、关系和地点。只有三种情况才纳入：`include_demo=True`；范围 ID 是演示样本（`wei-jianyi` 或 `rm:demo:wei-jianyi`）；问题里写了 `rm:demo:` ID。只出现“样本/演示”字样不算选择演示。响应新增 `demoScope` | 审计 C-16；用户/Green 指定“显式选择演示才出现” |
| `history_graph.resolve_id` | `rm:demo:` / `rm:rubbing:` / `rm:retired:` 形式的 ID 解析为 unknown | 按 `id_mapping.json` 的 `newId` 反查原 ID，不跨类别合并 | C-01 命名空间的补充 |
| 测试 | 建义相关的检索测试不需要选择演示 | 改为显式 `include_demo=True`。新增 `tests/test_demo_scope.py`（7 条无关查询、5 条只含样本字样的查询、3 种显式选择方式、API）和 `tests/test_retired_coordinates.py` | — |
| 下架坐标 | API 410 响应本来只返回 ID；`database.query_steles(include_retired=True)` 会带出坐标 | API 路径用测试固定下来：`/api/steles/<下架ID>`、`/graph`、`/infer` 只返回 message/oldId/recommendedId，检索与列表都不含坐标；`database.py` 写成需求 BR-07 | 铁律：不展示没有来源的坐标 |

- 4 个归档 JSON（`replacement_mapping.json`、`retired_steles.json`、`retired_database_records.json`、`museum_database_backup.json`）**保留原值不改**。它们是下架和迁移的历史记录，API 和静态目录都不提供；测试确认这些文件不会被 `/api`、`/static`、`/assets` 或前端数据带出。
- 没有修改任何史实字段。

## 2026-10-19 · 逐件深化第 1 批：6 件 claim（只增不改）

- 新增 `data/catalog/claims/schema.json`、`index.json`，以及 6 份 claim 文件：tang_01_duobao、han_01_caoquan、tang_02_jiucheng、tang_04_xuanmita、yuan_01_yufu、ming_02_luxianzhi。`steles28.json`、证据文件和史料图谱**都没改**。
- 挑选依据见 `index.json` 的 `selectionRule`：tang_01、han_01 是必选；其余 4 件按目录 verified 角色字段数、馆方释文长度、可打开的官方来源数挑选。
- 来源：仓库文件（目录字段、台北故宫资料表、释文）的引文都经测试逐字核对。外部只引用本轮实际打开的 7 个页面（`index.json` 的 `openedUrls`）：西安碑林 4 页、故宫博物院、国家博物馆、宝鸡市文物局。陕西省文物局名录页返回 504，未引用。
- 本批发现的异文和互证问题（都已原样并列，**没有改任何字段**）：

| 文物 | 问题 | 来源 |
|---|---|---|
| tang_01 | 碑文“四月乙丑朔廿二日戊戌”：按乙丑朔顺推，廿二日应为丙戌，相差 12 日，待用历表复核；释文作“戊戍” | 台北故宫释文；干支序推算 |
| tang_02 | 原石现藏地：故宫“立于麟游……今石尚存”、宝鸡市文物局列为本市碑刻 vs 国家博物馆“原碑今存于陕西省西安市碑林博物馆” | https://www.dpm.org.cn/collection/impres/234546.html ；http://wwj.baoji.gov.cn/col1896/col1884/202308/t20230801_824609.html ；https://www.chnmuseum.cn/zp/zpml/gjwxbt/201912/t20191211_179521.shtml |
| tang_02 | 太宗驾临年：碑文“貞觀六年孟夏” vs 故宫介绍“贞观七年四月”；碑高：宝鸡“通高326厘米” vs 故宫“碑高2.44m” | 同上 |
| tang_04 | 移入碑林时间：碑林两条目分别作“宋元祐年间”和“1103年”；台北故宫品名、封签都作“小楷”，与碑林原石（高 386 厘米）是否同石未核实 | https://www.beilin-museum.com/index.php?a=index&aid=2998&c=View&lang=en&m=home ；https://www.beilin-museum.com/index.php?a=index&aid=148&c=View&m=home ；台北故宫资料表 |
| yuan_01 | 书体：馆方书体栏“行楷書” vs 品名“小楷書” | 台北故宫资料表 |
| ming_02 | 作品性质：馆方分类“拓片” vs 李葆恂题跋“此潯州知府陸君墓志草稿”，关系到是否存在原刻载体 | 台北故宫资料表 |

- 目录中未核定的字段（如 tang_01、han_01 的原石现藏地、tang_01 的拓本年代），claim 最高只到“有限支持”，由测试强制。

## 2026-10-19 · C-08 确认令牌规则统一（Green）

| 位置 | 修改前 | 修改后 | 依据 |
|---|---|---|---|
| `C08_SYNC_SPEC.md` 第 3 节第 4 条 | `--confirm <basis.sqliteSha256 前 8 位>` | 令牌同时绑定差异摘要哈希和真实库完整 SHA-256，任一变化即失效；64 位十六进制，不截断；文件里不存令牌 | Green 的要求 |
| `c08_sync_diff.json` | 无摘要字段 | 新增 `diffDigestSha256` 和 `confirmation`（规则、公式、绑定项）。操作本身未变（仍是 15 项） | 同上 |
| `scripts/check_catalog_governance.py` | — | 新增 `diff_digest()`、`confirmation_token()` 参考实现；测试覆盖“任一位变化即失效” | 同上 |
| `C08_BACKEND_REVIEW_8a97a12.md`（新增） | — | 只读比对后端 8a97a12：15 项操作逐项相同；需调整 3 处（BR-10） | `git show` 只读查看；只在库副本上调用了只读函数 |

## 2026-10-19 13:06（Asia/Shanghai）· 跨作品比较分组数据（RM-金石史料）

| 位置 | 修改前 | 修改后 | 依据 |
|---|---|---|---|
| `data/catalog/comparison_dimensions.json`（新增） | — | 定义 4 个分组维度：同书家、同朝代、同书体、同收藏机构（拓本）。字段、核定规则、归并规则都写在数据里，界面不写死 | 目录 `steles28.json` |
| `scripts/build_comparison_groups.py`（新增，支持 `--check`） | — | 生成 `data/catalog/comparison_groups.json`。28 件作品每个维度都覆盖到：要么进组，要么列入 excluded 并写明原因 | 同上 |
| 书家分组 | — | 只用 `calligrapherVerification=verified` 的 10 件，分 7 组，其中可比较的（2 件及以上）有 2 组：赵孟頫 3 件、颜真卿 2 件。其余 18 件排除（unknown、pending_review、disputed 或“未核定”） | 不把未核定写成已核定 |
| 书体分组 | — | 三条带括注的原值归入“楷书”，原值保留在 rawValue；“行楷书”单独成组 | 归并规则写在 normalizeBasis |
| 机构分组 | — | 比较的是拓本收藏机构，不是原石现藏地 | 作品 ≠ 原石 ≠ 拓本 |

## 2026-10-19 13:08（Asia/Shanghai）· A：检索相关性阈值（RM-金石史料，Green 要求）

**问题。** “资料不足”的结果里仍带着弱相关的 BM25 条目（例如“今天天气怎么样”返回 8 条）。

**方法。**
1. 给每条证据记录拆分后的得分：`bm25Score`（只算 BM25）和 `entityMatched`（是否命中实体、图谱一跳或作品范围加分）。
2. 关闭过滤，跑 25 条审计探针和 15 条无关问题，统计 BM25 分布。
3. 按统计结果定阈值。

**数据。** 命令：`python scripts/measure_relevance_scores.py`，算法 v2.7，临时索引。

| 分组 | n | min | p50 | p90 | max |
|---|---|---|---|---|---|
| 审计·有结论·命中实体 | 166 | 0.000 | 21.348 | 30.591 | 63.509 |
| 审计·有结论·仅关键词 | 0 | — | — | — | — |
| 审计·资料不足·命中实体 | 36 | 0.938 | 16.337 | 21.265 | 55.698 |
| 审计·资料不足·仅关键词 | 24 | 2.292 | 5.415 | 10.520 | 23.055 |
| 无关问题·全部 | 147 | 0.871 | 3.213 | 5.381 | **9.647** |

**结论与阈值。**
- 所有“有结论”的结果，证据都命中实体，阈值对它们没有影响。
- 无关问题的条目都没有命中实体，BM25 最高 9.647。
- 阈值取 `WEAK_BM25_THRESHOLD = 10.0`：略高于无关问题的最大值，并取整。

**规则。**
- 没有命中实体，且 BM25 < 10.0 的条目：不返回。
- 没有命中实体，但 BM25 ≥ 10.0 的条目：返回，并标 `relevance=weak_keyword`、`relevanceLabel=“弱相关，仅供参考”`。
- 响应里新增 `relevanceFilter`，写明阈值、丢弃条数和规则。
- 算法版本 v2.6 → v2.7。

**效果。**
- 15 条无关问题的证据全部为空，回答只剩“现有资料不足以回答该问题。”
- “建义元年墓志的墓主是谁？”保留 4 条关键词条目（BM25 10.5–23.1），都标为弱相关，另有 4 条被丢弃。
- 25 条审计探针的状态和判断都没有变化。

**测试。** 新增 `tests/test_relevance_threshold.py`。其中一条会关闭过滤重新统计；如果语料变化，使无关问题的最高分达到或超过 10，测试就会失败，提醒重新标定。

**局限。** BM25 的绝对分值依赖语料规模。语料有增删时，需要重跑上面的命令并核对阈值。

## 2026-10-19 13:09（Asia/Shanghai）· C：ming_02 载体性质提示（RM-金石史料，Green 要求）

| 位置 | 修改前 | 修改后 | 依据 |
|---|---|---|---|
| `claims/ming_02_luxianzhi.json` 中的 `work:objectNature` | conflict / 待人工复核，没有提示 | 加上 `reviewFlags: ["载体性质待人工鉴定"]`。status、evidenceLevel、value(null) 和两种说法都不变 | 馆方分类“拓片”与李葆恂题跋“此潯州知府陸君墓志草稿”冲突 |
| `claims/schema.json` | — | claim 增加可选字段 `reviewFlags`（只作提示，不改变证据等级） | — |
| `review_ledger.json` 及前端副本 | — | 每条记录新增 `contentFlags`，从 claims 原样传入；目前只有 ming_02 一条 | — |
| `ReviewStatusBadges.tsx`（博物馆卡片和查看器共用） | 两枚徽章 | 有 contentFlags 时，再加一枚红色徽章（`data-testid="content-flag"`），文字来自数据 | — |
| `tests/test_carrier_flag.py` | — | 3 条测试 | — |

## 2026-10-19 13:13（Asia/Shanghai）· A 补充：界面显示弱相关标签（RM-金石史料）

| 位置 | 修改前 | 修改后 | 依据 |
|---|---|---|---|
| `EvidenceSearch.tsx` 证据条目标题 | 不显示相关性 | 后端返回 `relevanceLabel` 时，在条目标题后显示“· 弱相关，仅供参考”（`data-testid="weak-relevance"`），文字来自接口 | 阈值规则见上一节；本文件不在共享文件清单内 |

## 2026-10-19 13:40（Asia/Shanghai）· B：历日核对（RM-金石史料，Green 要求）

**来源。** 中央研究院“兩千年中西曆轉換”（https://sinocal.sinica.edu.tw/，查询提交到 `luso.php`，参数 lstype=2、swDate=1582/10/15，所以 1582 年以前的西历日期是儒略历）。只引用实际打开的结果页。每次查询的参数、时间、HTTP 状态和读到的原文，都记录在 `data/catalog/calendar_check_B.json`。

**方法。** 先核对释文中的年和月，再查该月的朔日干支，然后逐日推算。结论分三种情况：碑文本身有误、释文有误、我们算错。

**tang_01 多宝塔“四月乙丑朔廿二日戊戌”：待复核，字段不改。**

| 步骤 | 读到的内容 |
|---|---|
| 释文的年和月 | “天寳十一載……歲次壬辰。四月乙丑朔廿二日戊戍建”。历表：天寶11年歲次壬辰；该年有閏3月，没有閏4月，因此“四月”所指的月份没有歧义 |
| 该月朔日 | 历表 4 月一行为“4 丁丑 18 … 丁亥 28 … 丁酉 7 …”，即四月初一是**丁丑**，不是乙丑。单日查询：天寶11年4月22日 = 西元752年6月8日 |
| 我们的计算 | 没有算错：从“乙丑朔”推，廿二日确为丙戌 |
| 碑文与历表 | 日干支“戊戌”与历表相合（释文作“戊戍”，“戍/戌”字形相近）；朔日干支“乙丑”与历表的“丁丑”不合 |
| 是碑文错还是释文错 | **待复核**：需要人工对照拓本影像中“四月□丑朔”一处 |

**各作品的年号年份。**

| 作品 | 查询 | 结果 | 结论 |
|---|---|---|---|
| han_01 | 中平2年10月1日 | 185年11月10日，歲次乙丑；10 月朔丙申，“丙辰”是廿一日（185年11月30日） | 年份一致；“十月丙辰”与历表不矛盾（碑文没有写日序），dayCrossCheck 仍是待复核 |
| han_01 | 中平元年1月1日 | “日期超出範圍” | 记录原文，不作推断 |
| tang_01 | 天寶元年1月1日 | 连续返回 401、401、403，没有打开 | 元年一页未能核实；只能由“11 年=752”推得 |
| tang_02 | 貞觀元年1月1日；貞觀6年6月1日 | 627年1月23日；632年6月23日，歲次壬辰 | 一致 |
| tang_04 | 會昌元年12月28日 | 西元**842年2月12日**；该年歲次辛酉，起于841年1月27日 | 年号年份一致。立碑日已跨入西历 842 年；gregorianDay 现为“未换算”，建议人工确认后再补 |
| tang_04 | 開成元年6月1日 | 836年7月17日，歲次丙辰 | 一致 |
| yuan_01 | 延祐元年1月1日；延祐2年3月3日 | 1314年1月17日（甲寅）；1315年4月7日（乙卯） | 一致 |
| ming_02 | 嘉靖元年1月1日；嘉靖5年8月21日 | 1522年1月28日（壬午）；1526年9月27日，歲次丙戌 | 一致。原先“嘉靖元年=1522 取通行年表”一句现在有了中研院查询结果 |

**字段修改。** 本轮 claims 字段改动为 0。升级建议都写在 JSON 的 `findings[].suggestion/conclusion` 中，等人工确认。
