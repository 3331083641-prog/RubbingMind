# 墨韵智考代码审计（2026-10-15）

审计基线：`3ab634502008811e5026dfd9af60f2ad32b69885`，远程 `main` 与本地一致。整改分支：`codex/remediation-2026-10-15`。原有未跟踪三维文件、审核包和工作资料保持原状。SQLite、馆藏 JSON、提交号和工作区清单已备份到 `data/runtime/remediation-backup-2026-10-15/`（运行数据，Git 忽略）。

## 已确认的事实与问题

| 优先级 | 代码位置 | 事实及风险 | 整改方向 |
| --- | --- | --- | --- |
| P0 | `algorithm_engine.py:105` | `compute_metrics` 把输入／输出比较的 PSNR 加 8.5 并裁剪，SSIM 裁剪；噪点和边缘增益也加常数、裁剪。这些数字不能作为修复质量结论。 | 有真值时计算标准 PSNR/SSIM；无真值返回未评测，仅报告明确命名的诊断量。 |
| P0 | `algorithm_engine.py:160`、`main.py:86`、`museum_processing.py` | 当前 FFT 路径是高斯或二阶 Butterworth **低通**；`filter_order` 从 UI 进入请求后未传入引擎。页面称“陷波”与实现不符。 | 保留低通对照，实装可检测对称峰且可选择跳过的陷波；传递并验证阶数。 |
| P0 | `main.py:258`、`UploadModal.tsx` | 服务端错误读取 `result.images`、使用重复 `custom-5`、未保存用户图与记录，填写虚构指标和史料；前端失败后创建假成功。 | 限额与格式校验、安全持久化、UUID、回滚；前端失败如实提示。 |
| P0 | `knowledge_agent.py`、`WorkbenchPage.tsx` | 多模态调用函数存在，但工作台采纳仅改内存字符；规则候选以未经校准的百分数表现，默认候选声称笔画证据，未与实际局部图对应。 | 以手动选区和上下文提交真实图像；模型可选，规则仅作无概率建议；保存候选、采纳、撤销和坐标。 |
| P1 | `museum_processing.py`、`ReportsPage.tsx` | 实际处理输出有独立文件夹，但没有可查询的运行索引；报告不关联运行、固定编号；消融为空且页面仍展示空的“性能图”。 | 建立运行记录 API 与选择器；区分运行诊断和配对评测，报告动态引用。 |
| P1 | `main.py:_format_stele_item`、`HomePage.tsx`、`ReportsPage.tsx` | 后端保留固定指标，首页 `+18.6 dB`、`97.4%`、`120通+`、`350个+` 无本轮可复核统计；报告有“国家级”“算法认证”和固定 `RM-EPIGRAPHY-752-01`。 | 移除无依据数字与机构称谓，使用可计算馆藏数、朝代数、核心样本数；报告基于真实状态。 |
| P1 | `start.ps1`、`stop.ps1`、`check.ps1` | 硬编码 `D:\RubbingMind`；按端口强杀进程；`dist` 只看是否存在；检查结果可能误报。 | 解析脚本目录，记录自身 PID，不杀外部服务；明确开发／构建模式。 |
| P1 | `README.md`、`docs/graph-history-audit.md` | README 后段保留过期 23+5 说明及未证实算法效果；地图审图许可仍待核。 | 与 28 件审核包及实际实验同步；保留合规待办。 |
| P2 | `SteleViewer.tsx`、`GraphPage.tsx`、大图片资源 | 三维模型与全国地图已运行，资源较大；首屏加载与卸载内存须测量。 | 在 P0/P1 稳定后仅做测量支持的按需加载和反馈。 |

## 当前可信边界

28 件馆藏图片和七朝代数据已由 `data/catalog/steles28.json` 与审核资源建立对应；本轮冻结图片字节与文物身份。`museum_manager.py` 不在启动时改写馆藏数据。四件核心样本独立于馆藏：其中两件与馆藏同作品，另两件仅作演示。`catalog.py` 对真实馆藏的 PSNR/SSIM 返回空值，这是正确方向。`data/history/` 的核心样本 GIS 使用静态史料关系；不能把静态关系自动称为完整 GraphRAG 推理。

当前可确认的实际算法输出是 `/api/process` 写入 `static/results/<stele>/<run>/` 的图像与处理参数。`processing.json` 的 `engineDiagnosticMetrics` 来自输入／输出比较，不是有真值质量评估。预置核心样本候选、首页性能数字、报告公式文字和旧上传成功记录均不能作为独立实验结果。受控退化数据、人工字形标注、模型校准、地图公开审图许可仍未完成。

## 依赖与兼容风险

`App.tsx`、`api.ts` 的离线馆藏 fallback 依赖现有 28 件 JSON；上传属于本机运行数据，应通过独立接口合并而不污染权威清单。`WorkbenchPage.tsx` 和 `ReportsPage.tsx` 目前按文物 ID 重置组件，后续运行 ID、推演记录必须也按文物隔离。数据库已有用户数据，新增运行／上传表须增量迁移，不能删除 `steles`、`restoration_logs`、`inference_records`。`history_graph.py` 与 `data/history/` 的两件“同作品”资料不等于同一拓本版本；不能自动替换核心样本身份。CI 目前仅运行 Python、前端构建和资产存在性检查，缺少浏览器业务冒烟。

## 修改范围与验收顺序

先修指标和参数链，建立公开可重跑的受控实验；再修上传持久化、实际选区推演、运行历史与报告；随后核正首页和文档、启动脚本；最后执行单元、API、构建和浏览器回归，在 GitHub Actions 通过后同步。对每个阶段记录已验证内容与未解决限制，实验不以预期数值代替实测结果。
