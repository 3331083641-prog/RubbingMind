# 2026-10-26 本地 / GitHub 同步审计

**2026-10-27 更正：** 历史报告把 A24 与完整 ROI 处理闭环混为一谈。A24 测试的准确缺口是候选 / 人工采纳字形的导出标签 schema；实际 ROI 局部处理的跨页闭环是另一个待办。两项均未在本次视觉重构中关闭，详见 [报告页审查](../report-redesign/DESIGN_AUDIT.md)。

- [LOCAL_REMOTE_DIFF.md](LOCAL_REMOTE_DIFF.md)：实际 fetch 后的远程基线、本地分支与主要功能差异。
- [CHANGE_INVENTORY.md](CHANGE_INVENTORY.md)：逐文件来源、状态、功能、测试与同步取舍。
- [WORKTREE_REVIEW.md](WORKTREE_REVIEW.md)：全部分支与 14 个登记工作树（含正式目录）。
- [SYNC_DECISIONS.md](SYNC_DECISIONS.md)：A–G 分类、兼容修复、保留的研究与产品限制。
- [EXPERIMENT_EVIDENCE.json](EXPERIMENT_EVIDENCE.json)：2520 条配对指标重算与 252 次历史源码像素重放。
- [VALIDATION_RESULTS.md](VALIDATION_RESULTS.md)：实际执行的本地检查、失败与修复后结果。
- [本次真实浏览器证据](../../screenshots/sync-verification/)：三个桌面画幅、五个页面及评测重要可视化。

`FINAL_SYNC_REPORT.md` 在本机完成 main 合并、GitHub Actions 以及本地最终 SHA 核对后生成。
它是包含最终提交 SHA 的事后核验记录，按忽略规则留在本目录；其余审计源码文档和验证证据受 Git 管理。
这样不会为了把报告自己的提交 SHA 写入报告而不断改变交付提交。最终 SHA 与 Actions 链接同时给到用户，并记录于合并 PR 的说明。

截图、示例 JSON 与 PDF 展示的是使用公开实验图像的本次本地审计运行；其中的运行 ID 不代表新克隆已包含本机数据库或私人处理历史。
