# 只读比对：后端 commit 8a97a12 与 C08_SYNC_SPEC（R1–R6 及 7 条验收）

- 比对人：RM-金石史料 · 2026-10-19（Asia/Shanghai）
- 对象：`8a97a12`（分支 `agent/arch-backend`）中的 `scripts/sync_catalog_db.py`、`tests/test_sync_catalog_db.py`。
- 方式：在笔记本上用 `git -C D:\RubbingMind show 8a97a12:<path>` 只读导出，没有 checkout。只在 box 上的数据库**副本**（SHA 8408dbc3…，与用户库一致）上调用了它的只读函数 `compute_diff()` 和 `confirmation_token()`，**没有运行 `--apply`，也没有运行 `--rollback`**。
- 比对基准：本分支 `c358724` 的 R1–R6，以及 2026-10-25 与后端对齐后的令牌规则（[:16]）。

## 1. 实测：差异是否一致

| 项 | 结果 |
|---|---|
| `operations` 与 `data/catalog/c08_sync_diff.json` 逐项相等 | **相等**（15 项） |
| `counts` | 相等：update 5 / hold 0 / set_null 5 / keep_row 5 / insert 0 |
| `basis` | 两个 SHA-256 和行数相同；本分支多一个 `catalogueFile` 字段。它的 `check_external_diff` 只比两个 SHA，不受影响 |
| 它的令牌 `32326a07b002522c` | 等于本分支 `diffDigestSha256` 的前 16 位，说明规范化 JSON 的写法一致 |

## 2. R1–R6

| 规则 | 8a97a12 | 结论 |
|---|---|---|
| R1 目录为准，COLUMN_MAP 九列 | 列映射与本分支相同；`verification in (None, 'verified')` 才 update | 一致 |
| R2 未核定不升级 | 写成 hold；hold 不执行（`_execute` 中跳过） | 一致 |
| R3 下架行保留并置空坐标 | 下架判定为 `replacement_mapping` **或** `museum_catalog_status=retired`，比本分支（只看 mapping）略宽 | 一致（更保守） |
| R4 活跃行坐标置空 | 有 | 一致 |
| R5 非目录、非下架行不动 | keep_row，不写 | 一致 |
| R6 缺行按目录插入 | 只插入 `id` 和 COLUMN_MAP 九列 | 基本一致。**风险**：如果真实库 `steles` 还有其他 NOT NULL 列，插入会失败，然后整笔回滚。当前差异中 insert 为 0，不影响本次 |

## 3. 7 条验收

| # | 要求 | 8a97a12 | 差异 / 建议 |
|---|---|---|---|
| 1 | 默认只预览 | 默认 dry-run，`mode=ro` | 无差异 |
| 2 | 前置校验 basis SHA | `--diff` 可选；给了才逐项比对 basis 和 operations | **差异**：不给 `--diff` 时不和已提交的差异清单比对，只靠令牌绑定当次重算结果。建议 `--apply` 必须带 `--diff`，并比对 `diffDigestSha256` |
| 3 | 先备份 | `<db>.<YYYYMMDD-HHMMSS>.bak`（Asia/Shanghai），校验副本 SHA，记入 `.bak.json`；存在 -wal/-journal 时拒绝 | 无差异 |
| 4 | 用户确认后写入，单事务 | 令牌是 sha256(basis+operations) 的**前 16 位**；`BEGIN IMMEDIATE` 单事务，失败 ROLLBACK，逐条检查 rowcount=1 | **已对齐**（Green 2026-10-25）：本分支令牌改为 `diffDigestSha256[:16]`，与后端一致；16 位截断不再算缺陷 |
| 5 | 只执行清单内操作，不执行 hold | 执行的是重算得到的 operations；hold、keep_row 跳过 | 无 `--diff` 时，执行的不是“清单中的”操作，而是重算结果（同第 2 条） |
| 6 | 写后复核 | 重算后要求 update、set_null、insert 都为 0 | **小差异**：没有核对 keep_row 行仍在（下架 5 行没被删）、总行数不变。建议补这两项断言，或直接调用 `check_catalog_governance.py --summary` 判断 |
| 7 | 可回滚 | `--rollback <bak>` 先校验 SHA，恢复后再校验一次 | 无差异 |

## 4. 测试（只读阅读，未运行）

- `test_sync_catalog_db.py` 共 4 条：dry-run 只读且不打印坐标；令牌错误或缺失时拒绝；写入后 hold 未写、下架行保留；回滚字节一致；外部差异的 basis 不符时拒绝；`--apply` 必须显式给出 `--db`。
- 缺少的测试：`--apply` 不带 `--diff`、真实库 schema（NOT NULL 列）下的插入。令牌 16 位截断已与后端对齐，不再单列缺陷。

## 5. 结论

8a97a12 的 R1–R6 与本分支一致，在库副本上重算出的 15 项操作与差异清单逐项相同。令牌 `diffDigestSha256[:16]` 已与本分支对齐（Green 2026-10-25），16 位截断不再算缺陷。仍需后端调整的有 2 处，写在 BR-10：

1. `--apply` 必须带 `--diff`，并比对 `diffDigestSha256`；
2. 写后复核补上“下架行仍在、总行数不变”。
