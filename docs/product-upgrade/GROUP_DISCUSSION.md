# GROUP_DISCUSSION — 决策日志

- 说明（如实交代）：**这不是会议纪要，也没有实时群聊。** 各智能体只与 Green 一对一收发消息，并通过本文件夹的共享文件交换产出。本文件记录的是 Green 做出的决定，以及各 Agent 经消息转达给 Green 的意见与证据。格式按 BRIEF 第 3 节：议题、观点、证据、反对意见、决定、责任人、验证方式。
- 写入方式：追加写入（COORDINATION 第 7 条）。每条注明作者与时间（Asia/Shanghai，UTC+8）。
- 时间说明：下列时间为 Green 做出决定或收到转达的大致时间（“约”），日期均为 2026-10-19。

---

## [约 12:04] 报告前端三项待决：首页样本卡显示方式、URL 状态归属、页脚措辞
- 作者：Green（Agent 01）
- 议题：AUDIT_FRONTEND §7.6 请 Green 决定：① 首页核心样本卡 `object-cover` 裁切拓本（受保护视觉）是否改；② App 层 URL/runId 状态（共享文件）由谁实现；③ Footer“复原”措辞。
- 观点（RM-报告前端，经消息）：P1-12 提出“改为 object-contain 加深色衬底，或保持现状并在卡片上注明‘局部裁切’”；P0-2 提出在 App 层加 `activeRunId` 与 URL 状态，“共享文件，交架构 Agent”。
- 证据：`HomePage.tsx:249,269-270`（object-cover、h-48、hover 放大）；BRIEF Phase 1“不得 object-fit cover 裁字”；`App.tsx:17-19`（无路由、无 URL 状态）；COORDINATION 第 4 条（App.tsx、services/api.ts 归架构/后端）；BRIEF 第 2 节“图像变清晰≠恢复原刻文字”。
- 反对意见：首页属于受保护视觉（BRIEF 第 1 节），改动有破坏现有观感的风险。
- 决定：
  1. 首页核心样本卡改为 `object-contain`，用纸色衬底保持观感；改前改后都截图，**交用户确认后才可合并**。
  2. URL 状态在报告页自己的组件里实现；涉及 `App.tsx` / `services/api.ts` 的改动由 RM-架构后端负责（已写入 ADR R1-6）。
  3. 页脚“复原”改为“增强与辅助释读”。
- 责任人：RM-报告前端（1、2 中报告组件部分、3）；RM-架构后端（2 中 App.tsx/api.ts 部分）。
- 验证方式：1920×1080 / 1440×900 改前改后截图交用户；红队验收 URL 深链（复制 URL 到新标签页打开同一文物/运行/批次）。

## [约 12:06] 紧急规则：所有 Agent 起前端必须显式设置 `RUBBINGMIND_API_TARGET`，后端一律用 DB 副本
- 作者：Green（Agent 01）
- 议题：Vite 代理默认指向用户的 8000，其他 Agent 起前端时若未设置变量，会把请求（包括写请求）发到用户的真实服务和数据库。
- 观点（RM-架构后端，经消息）：“Vite 代理默认指向用户的 8000——其他 Agent 起前端时如果没设 RUBBINGMIND_API_TARGET，就会写进用户的真实数据库。这一条建议你先提醒各个 Agent。”
- 证据：`apps/web/vite.config.ts:10-16`（`RUBBINGMIND_API_TARGET || 'http://127.0.0.1:8000'`）；AUDIT_ENGINEERING E-P1-06；REVIEW_FINDINGS RT-003（technical_v2 测试默认 5180 且会发 POST）。
- 决定：立即生效——所有 Agent 起前端一律设置 `RUBBINGMIND_API_TARGET` 指向自己的后端端口；后端从自己的 worktree 启动并使用 DB 副本；测前测后核对用户两个 DB 的 SHA。并要求 RM-架构后端把数据路径改为可配置（ADR-007 / R1-7）。
- 后续意见（RM-架构后端，ADR R1-7，12:12）：不设变量时 Vite **仍默认 `http://127.0.0.1:8000`**，只在终端打印醒目警告，理由是“用户的日常用法是 5180 → 8000，改默认会直接破坏它”。这与 E-P1-06 原修复建议（“未设置时报错，或要求显式指定”）不同，作为待复核的反对意见记录在此，由红队验收 AB-1 时评估。
- 各 Agent 回执：RM-报告前端确认已把“RUBBINGMIND_API_TARGET=8720 + db 副本 + 测前测后 SHA 核对”加入 Phase 1 硬约束，并如实报告 Phase 0 审计时曾起 vite PID 44980@5720 未设变量（代理到 8000），只发 GET，但图谱页会自动发 POST `/api/calendar`。RM-红队QA 报告其全部测试均已指向 8740/5740。
- 责任人：全部 Agent；RM-架构后端（代码层修复）。
- 验证方式：用户两个 DB 的 SHA-256 前后一致（见 12:07 条）；红队验收 AB-1。

## [约 12:06] 架构后端五项待决：ID 合并、docs 是否入库、外部 worktree、受控演示、router 拆分
- 作者：Green（Agent 01）
- 议题：AUDIT_ENGINEERING 与 ARCHITECTURE_DECISIONS“待决事项（交 Green）”。
- 观点：RM-架构后端提出 `tang-duobao↔tang_01_duobao`、`han-caoquan↔han_01_caoquan` 是否建立 same_work_verified 需金石学和数据治理审核，北魏两件不合并；RM-金石史料（AUDIT_CONTENT C-01、§6）提出演示样本单独 `rm:demo:` 命名空间，“只经人工复核关系连到真实作品”，以 `id_mapping.json` 增量迁移，删映射即回滚。
- 证据：`core_sample_links.json`（`same_work`，“不证明为同一馆藏拓本”）；BRIEF 第 2 节“作品≠拓本≠原石”“北魏测试样本不得与未证明同一性的真实墓志合并”；E-P0-03、C-01 实测。
- 反对意见：合并为同一 ID 可以直接解决运行记录分裂（4 条 vs 10 条）——但会把演示图与真实拓本混为一谈，违反 BRIEF。
- 决定：
  1. **不合并** tang-duobao / tang_01_duobao（han 同理）。演示样本归入 `rm:demo:` 命名空间，与真实作品只通过一条经人工复核的关系连接；`id_mapping.json` 由 RM-金石史料产出，后端只读加载。
  2. `docs/product-upgrade/` 纳入版本库，最后随 feature 分支一起提交（现在不提交）。
  3. 外部 worktree 的处理交用户决定（见 12:07 条）。
  4. 受控演示（形态 B）推迟到 Phase 5，只写方案，默认只绑 127.0.0.1。
  5. 零行为变化的 router 拆分获批，排在 P0 之后。（ADR R1-0 第 5 条的记录为“排在 P0、P1 之后（步骤 f）”，两处表述不一致，以 Green 下次确认为准。）
- 责任人：RM-金石史料（映射内容）；RM-架构后端（映射接口、拆分）。
- 验证方式：ADR R1-0 / R1-5 已按此修订；红队验收映射接口在空映射下结果不变。

## [约 12:07] 用户决定：`D:\Codex\worktrees` 下 3 个 worktree 保持原样
- 作者：Green（Agent 01），记录用户决定
- 议题：AUDIT_ENGINEERING §1 / E-P2-11：`RubbingMind-gis-final`（4 处未提交改动）、`rubbingmind-museum-release`（198 处）、`rubbingmind-museum-v3`（204 处）怎么处理。
- 决定（用户原话）：“Codex 那 3 个 worktree 先别动，保持原样”。
- 责任人：全部 Agent 不碰这 3 个 worktree。
- 验证方式：`git worktree list` 中这 3 个 worktree 的 HEAD 不变（12:19 观察：f2f1ce5 detached、b0d17eb、aefb8e8）。

## [约 12:07] `/api/calendar` 是否写库；用户数据库是否被写过
- 作者：Green（Agent 01）
- 议题：RM-报告前端 Phase 0 审计时 vite 代理到用户 8000，图谱页会自动 POST `/api/calendar`，是否写入用户数据？
- 证据：
  - Green 读代码：`main.py:532` `@app.post("/api/calendar")` → `:535-536` `from history_graph import convert_historical_year; return convert_historical_year(req.query)`，纯计算，不写数据库、不写文件。（12:19 用 `git grep -n` 在 f0c5886 上再次确认行号。）
  - RM-红队QA（BASELINE_TESTS BT-00）：`data\rubbingmind.sqlite` `8408DBC3…0323D`、`data\runtime\evidence-v2.sqlite` `854DF859…BABD3`，12:07:54 与 12:12:04 两次 SHA 一致，mtime 均为 2026-10-18，无 -wal/-journal。原文如实说明没有测前哈希，以 mtime + 测后 SHA 作替代证据。
  - RM-架构后端：两个 DB 测前测后 SHA 一致（AUDIT_ENGINEERING 抬头）。
- 决定：认定用户数据库未被写入；不需要恢复操作。
- 责任人：Green。
- 验证方式：后续每次合并前红队重新核对这两个 SHA。

## [约 12:09] “留出”批次改名为“同批复测 v2.1”；eval-sci 的 experiment_registry.py 改动暂保留待复核
- 作者：Green（Agent 01）
- 议题：E-01（红队 RV-E01 复核“成立”）之后，heldout 批次怎么展示；RM-评测科学家问其在 `experiment_registry.py` 上的顺手改动（displayName、heldOut:false、派生导出）是否保留。
- 观点（RM-评测科学家，REPORT_DATA_SPEC §1(a)）：存储 ID 和目录名不改，只改显示层为“同批复测 v2.1（v2.0 对照，2026-10-18）”，`heldOut:false`；UI、导出文件名、tooltip 不得出现“留出/held-out”；结论最高“有限支持”；不得作为默认批次。
- 证据：RV-E01（14/14 同文物同 SHA，7 件为 v2-text 的 test；song_03 100%、tang_04 79.5% 裁切重叠；`compare_v21.py:49-51` 只排除了 v2 批次）。
- 反对意见：`experiment_registry.py` 不在最初点名给评测科学家的文件范围内，且 RM-架构后端的 R1-3 也要改该文件附近（批次元数据），存在合并冲突风险（ADR R1-3 已注明“不改 `_entry` 的返回行……在 `batches()` 中追加”）。
- 决定：采用“同批复测 v2.1”命名；`experiment_registry.py` 的改动**先保留在 agent/eval-sci**，等红队复核后再决定是否随分支合并。
- 责任人：RM-评测科学家；RM-报告前端（UI 文案）；RM-红队QA（复核）。
- 验证方式：红队复核 `agent/eval-sci@f21ceaa`；全仓 UI 文案 grep 无“留出/held-out”。
