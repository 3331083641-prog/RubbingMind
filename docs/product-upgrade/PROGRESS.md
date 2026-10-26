# PROGRESS — 进度

- 作者：Green（Agent 01，总协调）
- 更新时间：2026-10-19 12:25（Asia/Shanghai，UTC+8）

## 一句话状态
Phase 0 审计基本完成（5 份审计、资产冻结、基线测试、红队复核评测三条 P0 均“成立”）；Phase 1 已在各自分支开工。**还没有任何东西合并进 `feature/product-grade-upgrade`，也没有任何推送。**

## Git 状态（Green 12:19 实测，只读）
- `feature/product-grade-upgrade` = `main` = `origin/main` = **`f0c5886`**；feature 分支仅在本地。
- 主工作区 `git status --untracked-files=no`：干净。
- 各 Agent 分支（均未推送，`git branch -r --contains` 为空）：`agent/eval-sci` @ `f21ceaa`（+1）、`agent/arch-backend` @ `32b2360`（+1）、`agent/jinshi` @ `195bf97`（+3）、`agent/report-frontend` @ `f0c5886`（+0）。
- `D:\Codex\worktrees` 下 3 个 worktree 未触碰（用户决定保持原样）。
- 用户数据库：`data\rubbingmind.sqlite` `8408DBC3…0323D`、`data\runtime\evidence-v2.sqlite` `854DF859…BABD3`，红队 12:07:54 与 12:12:04 两次核对一致。

## 已完成
- Phase 0 审计：AUDIT_EVALUATION.md、AUDIT_FRONTEND.md、AUDIT_ENGINEERING.md、ARCHITECTURE_DECISIONS.md（初稿 + R1）、AUDIT_CONTENT.md、ASSET_FREEZE.json、BASELINE_TESTS.md、REVIEW_FINDINGS.md、ACCEPTANCE_MATRIX.md。
- 去重汇总：11 条 P0（PHASE0_SUMMARY.md）。
- 红队独立复核：E-01、E-02、E-03 均“成立”（E-01 因果部分未证明）。
- 基线：pytest 124 passed；validate_museum_v3 28 件 / 84 张 SHA 全一致；graph、terrain3d 浏览器测试通过；npm ci / build 通过；technical_v2 完整模式 390×844 **失败**（RT-001），`--ci` 通过。
- REPORT_DATA_SPEC v1；eval-sci 的原图返回判据与派生 applied_status（commit f21ceaa，待复核）。
- 决定：见 GROUP_DISCUSSION.md（6 条）。

## 进行中
- RM-评测科学家：按文物聚类 CI、机制层代表案例、E-04 测量化、E-05 修正。
- RM-报告前端：Phase 1 报告页重构（上下文栏 + URL、分层、ECharts、三联对照、失败入口、A4 打印、首页样本卡、页脚措辞）。
- RM-架构后端：数据路径环境变量 + Vite 代理（commit 32b2360，待验收），随后 P0 字段与接口。
- RM-金石史料：C-03、C-02、C-01（3 个 commit，待验收）。
- RM-红队QA：复核其他三份审计、ASSET_FREEZE 抽样、agent/eval-sci@f21ceaa、RT-002 严重度。

## 未开始
- Phase 2（图像算法与残字）、Phase 3 主体（统一实体、检索）、Phase 4（五页闭环）、Phase 5（安全与一键启动、受控演示方案）、Phase 6（集成与推送）。
- 任何分支向 `feature/product-grade-upgrade` 的合并（顺序见 MASTER_PLAN §3）。

## 需要用户的事（经 Green）
- 首页核心样本卡改为完整显示的前后截图确认（RF-8，截图产出后提交）。
- 合入 main 与推送：Phase 6，用户本地确认后才执行。
