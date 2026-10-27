# 报告页审查 · 2026-10-27

基线 fetch 后 main 为 `1dd8c47d80035c5477a82c7c4eb7c8fadf3b7865`，工作区干净；分支 `feature/report-visual-redesign`。修改前源码备份在 `D:\Codex\backups\RubbingMind-report-redesign-20261027`。

P0：首屏文字、三联图、多轴小图争夺注意力；主图在首屏下方；数据探索分散；强边框与小字遮盖主要结论。Taste 实际浏览器 baseline 检查为 3 FAIL / 10 WARN，包括无 h1、数字未对齐、无 tabular 数字。优先改报告结构与真实数据呈现。

P1：实验／文物／运行 URL 状态与导出保持一致；异常态和失败样例必须保留。A24 精确缺口见 `test_a24_export_label_recognized_forbidden_until_schema_exists`：尚无 candidate / human_accepted_glyph 导出标签 schema。它不是完整 ROI 局部修复流程；实际选区已有裁切、SHA、推演与人工操作记录，局部算法处理属于另外的工程范围。不能仅靠 UI 改动撤掉 xfail。

P1：历史机制图绑定 `7623a52`，未按最新代码重跑；过期 CI 拒绝机制继续保留。残字没有独立人工真值；争议 claims 和待复核项不升级认证。公网部署仍为单管理员工具，限制保留。

P2：首页核心样本完整性、跨页返回、移动端和异常提示做回归检查；视频、模型、地图与馆藏资产不重新设计。

原版真实运行与 Taste 检查证据：`D:\Codex\logs\RubbingMind-report-redesign-20261027\baseline-inspect`。三轮新设计复查与结果在 IMPLEMENTATION_REPORT.md 补齐。
