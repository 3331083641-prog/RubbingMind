# 核对与同步方案（C-06 核验状态链 · C-08 SQLite 与目录）

> **决定（2026-10-19 12:35 Asia/Shanghai，用户经 Green 传达）**
> - **C-06 选方案 A**：已新增复核台账 `data/catalog/review_ledger.json`（由 `scripts/build_review_ledger.py` 生成，可 `--check`），原 28 份证据文件和 `approved_by_user` 都不改。批准人、日期、范围留空，标“待用户填写”。典藏馆卡片和拓本查看器同时显示“已批准（用户确认可用于项目）”和“证据待第三轮复核”。
> - **C-08 选方案 A**：同步脚本由架构后端实现（默认只预览、执行前备份、用户确认后写入）。本分支只交付差异清单 `data/catalog/c08_sync_diff.json` 和映射规则 `docs/product-upgrade/C08_SYNC_SPEC.md`；需求见 `JINSHI_BACKEND_REQUESTS.md` 的 BR-05。
> - 下架行坐标：只读校验脚本和差异清单都不再输出数值（任务 0 的一部分）；其余输出路径另行提交。


- 作者：RM-金石史料（Agent 03/06/07）· 2026-10-19（Asia/Shanghai）
- 本方案**不改** `approved_by_user`，**不改**用户 SQLite（`data/rubbingmind.sqlite`），也不改 `steles28.json` 的任何字段。
- 只读校验脚本：`python scripts/check_catalog_governance.py [--db PATH] [--summary] [--strict]`。SQLite 用 URI `mode=ro` 打开，结果只输出到 stdout；`tests/test_governance_check.py` 验证脚本不写文件。实测差异见本分支回报，复现命令见文末。

## 1. C-06 核验状态链

**现状（脚本实测）**
- 28/28 件：目录 `sourceVerification.status = approved_by_user`，但对应证据文件 `processing.human_review_status = pending_third_round_user_ChatGPT_review`，`quality_status = 通过制作核验，待第三轮独立复核`。
- 目录与证据文件的 `sourceSha256` 28/28 一致，所以影像身份链本身是完整的。
- `review_manifest.json` 的批准依据只有一句“用户明确确认第三轮28件可正式用于项目”，没有批准人、日期，也没有逐件范围。

**可选方案（请 Green 选一）**

| 方案 | 做法 | 优点 | 风险 |
|---|---|---|---|
| A（推荐） | 不改两边的旧值。新增 `data/catalog/review_ledger.json`，逐件记录批准范围（影像可用 / 许可 / 著录字段）、批准人、日期（Asia/Shanghai）、证据文件 SHA；`approved_by_user` 解释为“影像与许可已批准”，不代表著录史实已核 | 增量、可回滚，状态含义更清楚 | 需要用户补一次确认（批准人和日期不能由 Agent 代填） |
| B | 用户确认后，把 28 份证据的 `human_review_status` 更新为 `approved_by_user_<日期>` | 两边一致 | 改动原始审核包的派生文件；必须由用户本人确认 |
| C | 维持现状，只在 UI 和 API 标明“影像已批准；著录字段待独立复核” | 不改任何数据 | 状态矛盾仍然存在 |

**验收**：`check_catalog_governance.py --summary` 的 `C06_inconsistentRecords` 为 0（方案 B），或者 ledger 覆盖 28 件且检索和 UI 引用 ledger（方案 A）。

## 2. C-08 SQLite `steles` 表与目录

**现状（Phase 0 审计时的副本实测；回报中附本次用笔记本主库只读复跑的结果）**
- 行数 33，目录 28 件；目录里的 28 件在 SQLite 中都有。
- 多出 5 行，都是已下架的旧记录：`qing_01_shilang`、`qing_02_gaocheng`、`qing_03_yanjin`、`qing_04_gongchen`、`yuan_04_jiulao`。`museum_catalog_status` 已标 retired，但 `gis_lng/gis_lat` 仍有精确到 0.001° 的坐标，且没有坐标来源。
- 字段差异 5 处，都在 `author` 列：SQLite 为“未核定”，目录为已核定值。具体是 song_02（宋太宗）、yuan_01（赵世延）、yuan_03（王思廉）、ming_02（文徵明）、ming_04（王毓宗）。
- 比较范围：title、dynasty、dynasty_value、author、script_type、museum、source_url、license、attribution。

**可选方案**

| 方案 | 做法 | 说明 |
|---|---|---|
| A（推荐） | 目录 `steles28.json` 是唯一事实来源，SQLite 只作运行时缓存。由后端 Agent 写一个**显式、可预演**的同步脚本，默认 dry-run，需加 `--apply` 并先备份 `.bak`；用户确认后执行 | 用户 SQLite 由后端负责，不由本分支执行 |
| B | 不同步；后端读取时一律以目录为准，SQLite 中的 steles 列仅作历史保留 | 不碰用户数据库；需后端确认没有其他读取方 |
| 下架行坐标 | 无论选 A 还是 B，下架行的坐标都不应再被任何接口输出；建议同步时置空，或在读取层屏蔽 | 坐标没有来源，按铁律不能展示 |

**验收**：`check_catalog_governance.py --strict` 对 C-08 部分无差异，或者差异都在“历史保留、不输出”的白名单内并有记录。

## 3. C-05 目录 ↔ 史料图谱（附带）

脚本同时列出 3 处跨源差异：tang_01 原石现藏、tang_01 拓本年代、han_01 原石现藏。检索现在对这 3 处返回 `conflict`，两说并列。是否把碑林官网（原石现藏）和台北故宫品名（明拓）补录进目录，需要“金石学 + 数据治理”审议（BRIEF 第 3 节），本分支不改目录。

## 复现
```powershell
cd D:\RubbingMind-wt\rm-jinshi
python scripts\check_catalog_governance.py --db D:\RubbingMind\data\rubbingmind.sqlite --summary
python scripts\check_catalog_governance.py --db D:\RubbingMind\data\rubbingmind.sqlite > %TEMP%\gov.json
```
