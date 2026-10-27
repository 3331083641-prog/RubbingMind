# 本地与 GitHub 差异审计

审计日期：2026-10-26，Asia/Shanghai。正式交付目录始终为 `D:\RubbingMind`。

| 初始检查 | 实测值 |
|---|---|
| 本地分支 | `feature/product-grade-upgrade` |
| 本地 HEAD | `12cff65a9285ccac6c7756d83bbbd1070b2c3306` |
| fetch 后 GitHub main | `f0c5886a9d4c8b47d64640e1f7eaeac44be3c388` |
| origin/main...HEAD 提交差 | 0 / 197 |
| 已提交差异 | 578 文件，491608 行增加、915 行删除（含派生实验 JSON） |
| 正式目录未提交已跟踪修改 / 已暂存修改 | 均为 0；另有未跟踪资料，不能称整个目录干净 |
| 远程 | https://github.com/3331083641-prog/RubbingMind.git；private，默认分支 main |

先盘点工作区、分支、worktree、忽略规则与 LFS，再执行 `git fetch origin --prune`。
没有执行 pull、hard reset、clean、force push、stash 或历史重写。
初始远程没有独有提交；合并前须再次 fetch 确认没有并发远程更新。

## 成果分布

正式分支已经包含 197 个本地未推送提交。另检查了所有本地分支和 14 个登记工作树，
包括 `D:\Codex\worktrees` 中的旧工作树。Git 历史不能单独证明操作者身份，来源按提交记录表述。
`agent/eval-sci@68859a6` 与 `agent/report-frontend@0c583f7` 各有一个独有提交，已普通 merge 保留。
`codex/museum-v3-release@b0d17eb` 是较早 GIS 实现，不以此覆盖后续 V2.2；原分支和脏工作树保留。

## 恢复检查点

恢复分支：`codex/sync-checkpoint-20261026_202908`。
独立备份：`D:\Codex\backups\RubbingMind-sync-20261026_202908`，含 refs、状态、工作树清单、关键文件、初始未跟踪源码与技术文档，
以及脏工作树的二进制差异补丁。秘密配置、私人数据库、上传数据原地保留，不加入 Git 或报告正文。

## 主要功能差异

| 模块 | 本地有效成果 | 取舍 |
|---|---|---|
| 首页 | 空指标文案修正，保留既有视频和 Blender PBR 模型 | 保留原样式与资源 |
| 典藏馆 | 28 件 claims、复核状态、原刻载体标记、来源分域 | 保留；保护 84 张正式运行影像 |
| 工作台 | 命名空间、真实处理记录、像素未改动判据、ROI/SHA/参数追溯、URL 状态 | 保留后端与前端配套实现 |
| 图谱 | 有据检索、冲突并列、演示隔离、合成文本警示 | 保留；地形 / DEM / V2.2 边界不改 |
| 评测报告 | 分层报告、真实数据图表、三图同步、负提升、机制图、打印和 JSON | 重点保留；补只读派生接口缺口 |
| 算法 | 无峰陷波直接返回副本，自适应输出模式追溯 | 保留；不覆盖历史实验 |
| 工程 | 可重定向私有状态、代理目标、请求限制、软删除 | 保留，补测试和 Windows 启动兼容 |

逐文件清单见 CHANGE_INVENTORY.md；历史工作树见 WORKTREE_REVIEW.md；取舍见 SYNC_DECISIONS.md。
