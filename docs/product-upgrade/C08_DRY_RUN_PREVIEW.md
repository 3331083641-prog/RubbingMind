# C-08 Dry-run 预览（只读 · 主库禁止 --apply）

- 生成时间（Asia/Shanghai）：2026-10-25 11:03:21 CST
- 目标库：D:\RubbingMind\data\rubbingmind.sqlite（URI mode=ro）
- 生成器：scripts/check_catalog_governance.py --emit-sync-diff（金石分支）
- 令牌公式：sha256(C-08|diffDigest|dbSHA)[:16]（arch@a261ba0；**不是**仅 digest[:16]）
- **主库禁止 --apply**；本文件仅为预览。副本 dry-run 文档示例令牌 112ba2d3ebd14f2a 与本次用户库令牌无关。

## 令牌与摘要

| 字段 | 值 |
|---|---|
| confirmationToken（本次预览） | ef30c1d51053b8a8 |
| diffDigestSha256 | 32326a07b002522ce2855413b52bcd0161f3f4d9289af12cf0441037dc0674cb |
| dbSHA（basis.sqliteSha256） | 8408dbc36819efda512d392df69fd2b96d7b1469460fcba0bbee5aaad270323d |
| catalogueSha256 | 0bc28fe95fad15d8df42c89ec5f897d8f9f63fb97b3c71c3b16d48acd63ab1b2 |
| sqliteRows | 33 |
| catalogueRecords | 28 |
| 对照：digest[:16]（已撤回，勿用） | 32326a07b002522c |

## 操作摘要

counts = {"update": 5, "hold": 0, "set_null": 5, "keep_row": 5, "insert_from_catalogue": 0}

| rule | op | 条数 | 示例 id |
|---|---|---|---|
| R1 | update | 5 | ming_02_luxianzhi, ming_04_tongdian, song_02_wenxuan, yuan_01_yufu, yuan_03_shengzhu |
| R3 | keep_row,set_null | 10 | qing_01_shilang, qing_01_shilang, qing_02_gaocheng, qing_02_gaocheng, qing_03_yanjin …(+5) |

## 完整 operations（预览）

`json
[
  {
    "op": "update",
    "table": "steles",
    "id": "ming_02_luxianzhi",
    "column": "author",
    "from": "未核定",
    "to": "文徵明",
    "catalogueVerification": "verified",
    "rule": "R1"
  },
  {
    "op": "update",
    "table": "steles",
    "id": "ming_04_tongdian",
    "column": "author",
    "from": "未核定",
    "to": "王毓宗",
    "catalogueVerification": "verified",
    "rule": "R1"
  },
  {
    "op": "update",
    "table": "steles",
    "id": "song_02_wenxuan",
    "column": "author",
    "from": "未核定",
    "to": "宋太宗",
    "catalogueVerification": "verified",
    "rule": "R1"
  },
  {
    "op": "update",
    "table": "steles",
    "id": "yuan_01_yufu",
    "column": "author",
    "from": "未核定",
    "to": "赵世延",
    "catalogueVerification": "verified",
    "rule": "R1"
  },
  {
    "op": "update",
    "table": "steles",
    "id": "yuan_03_shengzhu",
    "column": "author",
    "from": "未核定",
    "to": "王思廉",
    "catalogueVerification": "verified",
    "rule": "R1"
  },
  {
    "op": "keep_row",
    "table": "steles",
    "id": "qing_01_shilang",
    "reason": "museum_catalog_status=retired；保留历史行，不删除",
    "rule": "R3"
  },
  {
    "op": "set_null",
    "table": "steles",
    "id": "qing_01_shilang",
    "columns": [
      "gis_lng",
      "gis_lat"
    ],
    "from": "已屏蔽：无来源坐标，不输出数值",
    "to": null,
    "rule": "R3"
  },
  {
    "op": "keep_row",
    "table": "steles",
    "id": "qing_02_gaocheng",
    "reason": "museum_catalog_status=retired；保留历史行，不删除",
    "rule": "R3"
  },
  {
    "op": "set_null",
    "table": "steles",
    "id": "qing_02_gaocheng",
    "columns": [
      "gis_lng",
      "gis_lat"
    ],
    "from": "已屏蔽：无来源坐标，不输出数值",
    "to": null,
    "rule": "R3"
  },
  {
    "op": "keep_row",
    "table": "steles",
    "id": "qing_03_yanjin",
    "reason": "museum_catalog_status=retired；保留历史行，不删除",
    "rule": "R3"
  },
  {
    "op": "set_null",
    "table": "steles",
    "id": "qing_03_yanjin",
    "columns": [
      "gis_lng",
      "gis_lat"
    ],
    "from": "已屏蔽：无来源坐标，不输出数值",
    "to": null,
    "rule": "R3"
  },
  {
    "op": "keep_row",
    "table": "steles",
    "id": "qing_04_gongchen",
    "reason": "museum_catalog_status=retired；保留历史行，不删除",
    "rule": "R3"
  },
  {
    "op": "set_null",
    "table": "steles",
    "id": "qing_04_gongchen",
    "columns": [
      "gis_lng",
      "gis_lat"
    ],
    "from": "已屏蔽：无来源坐标，不输出数值",
    "to": null,
    "rule": "R3"
  },
  {
    "op": "keep_row",
    "table": "steles",
    "id": "yuan_04_jiulao",
    "reason": "museum_catalog_status=retired；保留历史行，不删除",
    "rule": "R3"
  },
  {
    "op": "set_null",
    "table": "steles",
    "id": "yuan_04_jiulao",
    "columns": [
      "gis_lng",
      "gis_lat"
    ],
    "from": "已屏蔽：无来源坐标，不输出数值",
    "to": null,
    "rule": "R3"
  }
]
`

## 说明

- 本预览未写入任何数据库，未创建 .bak。
- 若日后在**副本**上 --apply，须同时提供 --diff 与 --confirm <令牌>，且令牌必须按 sha256(C-08|diffDigest|dbSHA)[:16] 重算。
- 合并时 evidence_retrieval / glyph_inference 的 include_demo 与演示隔离以金石分支为准；WorkbenchPage 冲突交报告前端（见 JINSHI_FRONTEND_REQUESTS.md）。
