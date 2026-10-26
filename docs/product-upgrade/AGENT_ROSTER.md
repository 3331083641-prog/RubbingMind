# AGENT_ROSTER — 墨韵智考 RubbingMind 产品级升级 · 智能体名册

- 作者：Green（Agent 01，总协调）
- 写入时间：2026-10-19 12:25（Asia/Shanghai，UTC+8）
- 依据：BRIEF.md、COORDINATION.md、各 Agent 的审计/产出文件，以及各 Agent 发给 Green 的消息。

## 0. 先说清楚的几件事

1. **12 个角色映射到 5 个真实智能体 + 1 个总协调者。** BRIEF 里的 Agent 01–12 不是 12 个独立进程。Green 是 Agent 01，其余 11 个角色合并到下面 5 个 Grok Bot 智能体里，每个智能体承担 2–3 个角色。
2. **没有实时群聊。** 各智能体之间不直接对话，也没有“群组会议”。沟通方式只有两种：
   - 一对一消息：每个智能体只和 Green 收发消息（SendToAgent），Green 转达决定和需求；
   - 共享文件：`D:\RubbingMind\docs\product-upgrade\` 下的文档（各自只写自己的文件，GROUP_DISCUSSION.md、REVIEW_FINDINGS.md 采用追加写入）。
   `GROUP_DISCUSSION.md` 因此是 **Green 的决策日志 + 经消息转达的各 Agent 意见**，不是会议纪要。
3. **没有使用或控制 Cursor IDE。** 所有工作都是这些智能体通过用户笔记本（LAPTOP-TU4U942T）上的 PowerShell 和 git worktree 完成的。
4. **更早的隐藏审计员不计入。** 在本名册的 5 个智能体之前，曾启动过一批隐藏审计员，它们在产出任何文件或结论之前就已被停止，没有留下任何产出，本名册和所有阶段文档都不引用、不计入它们。
5. 所有 Agent 都受 COORDINATION.md 约束：不直接改 main、不 push、不合并到 `feature/product-grade-upgrade`；写代码只在自己的 worktree；不杀非自己启动的进程；用户的 8000（python，PID 30712）与 5180（Vite）不碰。

## 1. 名册

| 智能体 | 承担的 BRIEF 角色 | Grok Bot 智能体 ID | 分支 | worktree | 端口 | 临时目录 |
|---|---|---|---|---|---|---|
| **Green** | Agent 01 总协调 / 监工 | `2e9a3d6a-0d9a-4ba7-a2dd-05b653edd3c6`（COORDINATION.md 第 1 条） | — | 只读主工作区 `D:\RubbingMind` | — | `C:\Users\WPY11\rm-green-tmp`（用完即删） |
| **RM-评测科学家** | Agent 04 计算机视觉 + Agent 05 评测科学 | `00b7a173-5111-448e-bf74-3584fd3aca02` | `agent/eval-sci` | `D:\RubbingMind-wt\rm-eval-sci` | （本阶段未起常驻服务） | `C:\Users\WPY11\rm-eval-sci-tmp` |
| **RM-报告前端** | Agent 08 UI/UX + Agent 09 前端 | `e29a1c3f-e9d8-4959-b675-92389210f001` | `agent/report-frontend` | `D:\RubbingMind-wt\rm-report-frontend` | 8720 / 5720 | `C:\Users\WPY11\rm-report-frontend-tmp` |
| **RM-架构后端** | Agent 02 架构 + Agent 10 后端 + Git 集成负责人 | `92c46026-6a1f-47f0-9b85-6bde51ad0a0b` | `agent/arch-backend` | `D:\RubbingMind-wt\rm-arch-backend` | 8710 / 5710 | `C:\Users\WPY11\rm-arch-backend-tmp` |
| **RM-金石史料** | Agent 03 金石学 + Agent 06 数据治理 + Agent 07 知识检索 | `12139cd2-2965-438a-bac4-6f4a2ba8ef41` | `agent/jinshi` | `D:\RubbingMind-wt\rm-jinshi` | 8730 | `C:\Users\WPY11\rm-jinshi-tmp` |
| **RM-红队QA** | Agent 11 QA + Agent 12 红队 | `90f384c7-fac3-40fc-9f34-4ad67e6ab94c` | 无写分支（只读） | `D:\RubbingMind-wt\qa-baseline`（detached `f0c5886`，只读）；另有 `D:\RubbingMind-wt\qa-evalsci`（detached `f21ceaa`，用于复核 eval-sci 分支，12:19 观察到） | 8740 / 5740 | `C:\Users\WPY11\rm-redteam-qa-tmp` |

角色名称说明：各角色的具体称谓取自各 Agent 的自述和审计文件抬头（如 AUDIT_EVALUATION.md“Agent 04 计算机视觉 + Agent 05 评测科学”、AUDIT_CONTENT.md“金石内容、数据治理与知识检索”）。

## 2. 职责与文件所有权

| 智能体 | 主要职责 | 拥有/负责的文件（只写这些） |
|---|---|---|
| Green | 拆解任务、分派、监工（每半小时巡检）、复核交付、做决定或把需要用户拍板的事交给用户、写协调文档 | `AGENT_ROSTER.md`、`MASTER_PLAN.md`、`PHASE0_SUMMARY.md`、`TASK_BOARD.md`、`GROUP_DISCUSSION.md`（追加）、`PROGRESS.md` |
| RM-评测科学家 | 实验与统计口径、REPORT_DATA_SPEC、原图返回/实际处理判据、按文物聚类 CI、机制层真实数据、算法侧修正；科学结论的独立质疑人 | `AUDIT_EVALUATION.md`、`REPORT_DATA_SPEC.md`；代码：`experiments/`、`degradation_analysis.py`、`experiment_registry.py`（待红队复核，见 GROUP_DISCUSSION 12:09） |
| RM-报告前端 | 报告页六层重构的 UI/UX 与实现、五页闭环前端联动、截图、A4 打印 | `AUDIT_FRONTEND.md`、`screenshots/product-upgrade/phase0-frontend/`；代码：`ReportsPage.tsx`、`ExperimentExplorer.tsx`、`HeldoutComparison.tsx`、`components/reports/` |
| RM-架构后端 | 架构、后端 API、schema、共享文件、Git 集成（合并入 feature 分支的执行人） | `AUDIT_ENGINEERING.md`、`ARCHITECTURE_DECISIONS.md`；共享文件 `App.tsx`、`services/api.ts`、`main.py`、数据库 schema（COORDINATION 第 4 条） |
| RM-金石史料 | 28 件馆藏与演示样本的史实/来源、实体模型、ID 映射内容、检索质量、资产冻结；史实结论的独立质疑人 | `AUDIT_CONTENT.md`、`ASSET_FREEZE.json`；数据：`data/catalog/id_mapping.json`（agent/jinshi 产出）、演示样本元数据 |
| RM-红队QA | 基线测试、验收矩阵、红队探测、对其他 Agent 结论的独立复核、每次合并前的验收 | `BASELINE_TESTS.md`、`REVIEW_FINDINGS.md`（追加）、`ACCEPTANCE_MATRIX.md` |

## 3. 通信记录方式

- 每个 Agent 完成或遇阻时用 SendToAgent（priority:true）把结果发给 Green；需要用户决定的事由 Green 统一问用户。
- Green 发出的分派和决定，同时记录在 `TASK_BOARD.md` 和 `GROUP_DISCUSSION.md`。
- 任何结论都要附证据（文件路径+行号、命令+输出摘要、外部来源 URL），不伪造（COORDINATION 第 8 条）。
