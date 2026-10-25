# C-08 同步规格（方案 A）· 交架构后端实现

- 决定：用户经 Green 传达，选 C-08 方案 A（2026-10-19 12:35 Asia/Shanghai 收到）。
- 作者：RM-金石史料。本规格只给出差异清单和映射规则，**本分支不写用户 SQLite**；同步脚本由架构后端实现。
- 差异清单：`data/catalog/c08_sync_diff.json`，由只读校验脚本生成：
  `python scripts/check_catalog_governance.py --db <sqlite> --emit-sync-diff data/catalog/c08_sync_diff.json`
  （SQLite 以 `mode=ro` 打开）。核对差异清单是否过期：`--check-sync-diff data/catalog/c08_sync_diff.json`。
- 本次生成依据：`sqliteSha256 = 8408dbc3…270323d`（与笔记本 `D:\RubbingMind\data\rubbingmind.sqlite` 只读计算的 SHA 一致），`catalogueSha256 = 0bc28fe9…63ab1b2`（`steles28.json`）。

## 1. 映射规则

| 规则 | 适用对象 | 动作 |
|---|---|---|
| R1 | 目录中的 28 件，`COLUMN_MAP` 内的列（title、dynasty、dynasty_value、author、script_type、museum←rubbingCollectionInstitution、source_url、license、attribution） | 以 `steles28.json` 为唯一事实来源，SQLite 值改为目录值（`op=update`）。前提是目录字段的 `*Verification` 为 `verified`，或该字段没有核验状态 |
| R2 | 同上，但目录字段的核验状态不是 `verified` | 不写入（`op=hold`），列出来交人工处理。永远不把未核定升级为已核定 |
| R3 | `museum_catalog_status=retired` 的旧行（5 行） | 保留行，不删除（`op=keep_row`）；`gis_lng/gis_lat` 置 NULL（`op=set_null`），因为坐标没有来源 |
| R4 | 目录中的 28 件，若 SQLite 带坐标 | 置 NULL：目录没有坐标来源字段，`catalog.py` 也不输出坐标。当前 0 处 |
| R5 | 不在目录、也未下架的行（如用户记录） | 不动（`op=keep_row`） |
| R6 | 目录中有、SQLite 中缺的记录 | 按目录插入（`op=insert_from_catalogue`）。当前 0 处 |

- 不新增列，不删列，不改 schema；`museum_catalog_status` 表不动。
- 差异清单里**不出现无来源坐标的数值**，`from` 只写“已屏蔽：无来源坐标，不输出数值”。

## 2. 本次差异（15 项操作）

- `update` 5 项（R1，都是 `author` 列，SQLite“未核定” → 目录已核定值）：ming_02_luxianzhi 文徵明、ming_04_tongdian 王毓宗、song_02_wenxuan 宋太宗、yuan_01_yufu 赵世延、yuan_03_shengzhu 王思廉。
- `keep_row` 5 项 + `set_null` 5 项（R3）：qing_01_shilang、qing_02_gaocheng、qing_03_yanjin、qing_04_gongchen、yuan_04_jiulao。
- `hold`、`insert_from_catalogue` 各 0 项。

## 3. 后端同步脚本的必需行为（验收条件）

1. **默认只预览**：不加参数时只打印将执行的操作，不写库。
2. **前置校验**：重新计算 SQLite 和 `steles28.json` 的 SHA-256，必须与 `basis` 一致，否则中止，并提示重新生成差异清单。
3. **先备份**：写入前把 SQLite 复制为 `rubbingmind.sqlite.<YYYYMMDD-HHMMSS>.bak`（Asia/Shanghai 时间），记录备份的 SHA-256，校验通过后再继续。
4. **用户确认后写入**：需同时给出 `--apply` 和用户的明确确认（交互输入令牌，或 `--confirm <令牌>`），并在单个事务里执行；任何一步失败就回滚。**确认令牌规则**（Green，2026-10-25，与后端 arch@a261ba0 对齐）：令牌为 `sha256(C-08|diffDigest|dbSHA)[:16]`（与后端 arch@a261ba0 一致；**不是**仅 `digest[:16]`）十六进制。
   - `diffDigestSha256 = sha256(canonical_json({"basis": {sqliteSha256, catalogueSha256, sqliteRows, catalogueRecords}, "operations": [...]}))`。canonical_json 的参数是 `sort_keys=True, separators=(',', ':'), ensure_ascii=False`，编码 UTF-8。这个值写在 `c08_sync_diff.json` 的 `diffDigestSha256` 字段里，后端须重算并比对。
   - `token = sha256(C-08|diffDigestSha256|dbSHA)[:16]`（16 位十六进制）。`diffDigest` 为完整 `diffDigestSha256`；`dbSHA` 为目标库完整 SHA-256。二者任一变化，令牌即失效。旧公式（仅 `diffDigestSha256[:16]`、或 `sha256(库SHA+目录SHA+行数+操作清单)[:16]`）**已撤回**。参考实现：`scripts/check_catalog_governance.py` 中的 `diff_digest()`、`confirmation_token()`。dry-run 示例令牌（**仅副本**）：`112ba2d3ebd14f2a`。**主库禁止** C08 `--apply`。
5. **只执行清单中的操作**：不做清单之外的修改，不执行 `hold`。
6. **写后复核**：运行 `check_catalog_governance.py --summary`，`C08_fieldDiffs` 应为 0，`C08_extraWithCoordinates` 应为 0，`C08_extraInSqlite` 仍为 5（保留的下架行）。
7. **可回滚**：提供把 `.bak` 恢复回原位的命令。

## 4. 不在本规格内

- 归档 JSON 保留原值：`data/catalog/replacement_mapping.json`、`retired_steles.json`、`retired_database_records.json`、`data/museum_database_backup.json` 记录下架和迁移的历史，其中有 5 条下架记录的原坐标数值。它们不是输出路径：没有 API 读取并返回坐标，`/static` 和 `/assets` 也不挂载 `data/`，`tests/test_retired_coordinates.py` 会检查这一点。同步时不要改这几个文件；以后若有代码要读取它们并对外输出，必须先屏蔽坐标。

- 用户上传记录、`data/runtime/**`、证据文件、`approved_by_user` 都不动。
- 活跃 28 件的坐标：目录没有坐标来源，不补写。
