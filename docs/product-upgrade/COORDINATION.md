# 协作规则（所有 Agent 必读）
1. Green 是总协调者（Agent 01）。只接受 Green 分派的任务；完成或遇阻时用 SendToAgent（priority:true）把结果发给 Green（id 2e9a3d6a-0d9a-4ba7-a2dd-05b653edd3c6）。不直接找用户要决定，需要用户决定的事交给 Green。
2. 不直接改 main，不 push，不合并到 feature/product-grade-upgrade——集成由 Green 指定的集成负责人在审查通过后完成。
3. 并行写代码时，每个 Agent 用自己的 git worktree：`git -C D:\RubbingMind worktree add D:\RubbingMind-wt\<agent-slug> -b <分支> feature/product-grade-upgrade`。D:\RubbingMind 主工作区只用于读取和最终集成。审计阶段只读，不建 worktree。
4. 文件所有权：只写自己被分配的文件。共享文件（App.tsx、services/api.ts、main.py、数据库 schema）由架构/后端 Agent 负责，其他人提需求不直接改。
5. 端口：架构/后端 8710 后端、5710 前端；评测报告前端 8720/5720；史料 8730；红队/QA 8740/5740。不得杀非自己启动的进程，结束时停掉自己的服务。
6. 临时文件：C:\Users\WPY11\rm-<agent-slug>-tmp，结束删除。
7. 共享文档 D:\RubbingMind\docs\product-upgrade\：每个 Agent 只写自己的审计/产出文件；GROUP_DISCUSSION.md、REVIEW_FINDINGS.md 采用追加写入，每条注明作者 Agent、时间（Asia/Shanghai）。
8. 所有结论附证据（文件路径+行号、命令+输出摘要、外部来源 URL）。不伪造。
