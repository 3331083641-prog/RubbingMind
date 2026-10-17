# 第二阶段接续记录（实时状态：2026-10-17）

## 工作区与边界

- 根目录 `D:\RubbingMind`，仓库 `3331083641-prog/RubbingMind`，仍为Private。
- 本轮基线 `a7a6cb097699e44921d776ff0582f0fa4704ab31`；开发分支 `codex/technical-v2`，已正常快进合并main。
- 已推送main与开发分支：`f9aebdb` 后端/实验、`22762c6` 前端/CI、`98ffb280f20361deacb26aca9e5b20e39c926d5d` 文档/截图、`41ee69e2ff2bac2be4617bd243960085a907b632` pytest跨环境入口修复。
- **禁止覆盖**84张正式JPG、`data/catalog/steles28.json`、三维几何、地图素材及原有失败实验。不要提交用户原有未跟踪的建模文件、rubbings-review-v3、rubbings-workspace、旧截图或私有数据库。
- 备份/冻结SHA在Git忽略的 `data/runtime/technical-v2-backup/`，不包含密钥。不要读取、打印或上传环境密钥。

## 已完成并有证据

- 自适应增强、图像退化诊断、保真回退、确定性纸纹/风化、二值骨架与轮廓分离。
- 新增两批实验，共28个ID、280输入、2520输出；每批完整重跑1260次，输出SHA与指标一致。旧数据不改写，纸边失败批次保留。
- 正文批测试：输入24.705dB/SSIM0.704；固定联合18.829/0.485；自适应26.798/0.762；单陷波27.252/0.767，不声称全面胜出。
- 实际ROI前景、骨架、连通区域/边界警示；本地人工参考字形检索；视觉接口兼容、采纳/撤销/驳回持久化。
- FTS5/BM25+有来源实体一跳扩展，28件统一研究接口，原石/拓本分离，未知身份拒绝混用；已有GIS定位联动。
- 第五页真实实验API、筛选、数字/图像/CSV/JSON；报告仍按真实runId关联。
- 修正PDF目录/许可头误当碑文、框选弹窗层叠遮挡、打印空白分页。
- 本机90项Python测试、TypeScript/Vite构建、84图SHA、Windows三桌面尺寸及390px触屏浏览器、上传完整工作流通过。截图与JSON/PDF在 `screenshots/technical-v2/`。
- 主验收浏览器：`scripts/test_technical_v2_browser.py`。环境：后端8015、Vite5180，已运行；原8000/5173服务未误杀。

## 本轮工程验收状态

1. **CI导入失败已修复并复验通过**：首次运行 `39024429038` 的pytest入口未把根目录加入sys.path，添加`pytest.ini`后两种启动方式均90通过。提交`41ee69e`的[Actions 39041939971](https://github.com/3331083641-prog/RubbingMind/actions/runs/39041939971)四项作业全部成功，原失败记录保留。
2. **清洁克隆通过**：`D:\Codex\verification\rubbingmind-technical-v2-20261017` 从GitHub独立克隆并快进到`41ee69e`。新npm缓存、venv、数据库、45包依赖均独立安装，90项测试、28件/84图校验、前端构建及实际浏览器流程通过。首次镜像TLS错误后改用官方PyPI，不关闭证书校验。证据 `technical-v2-clean-clone.json`，含运行ID、版本、失败及成功日志位置。
3. 独立克隆8016/5181按health→generate→Vite→浏览器验收；原工作区8015/5180也重新启动并再次通过在线/fallback冒烟。只停止自己拥有的服务，不误杀其他Python/Node进程。
4. `technical-implementation-v2-report.md` 已补充实际CI与克隆结果；冻结资源证据为 `technical-v2-frozen-verification.json`，84图与主清单完全不变。
5. `technical-v2-change-manifest.json` 按Git的LF规范化文本和二进制原字节计算SHA，排除自身。最终纯文档提交后仍应检查远程main与本地一致及Actions成功，最新文档提交SHA以 `git log -1` 为准，不在文档中循环追写自身SHA。

## 后续研究与上线前待办（尚未实现或未核实）

1. **优先：建立独立人工字符真值**。填充 `data/catalog/glyph-benchmark-v2.json`：标注者、出处/许可、源图SHA、ROI、字符及不确定项。按文物划分参考/测试集，不用同字模板自匹配伪造识别率，再运行 `experiments/evaluate_glyphs.py`。当前n=0、指标null是正确状态。
2. **实际视觉模型验收**。用户自行配置兼容API后，再测真实碑刻ROI、服务失败、拒识、繁体/古字及来源可信度。现有受控mock只验证接口；不要输出密钥或将外部模型建议URL直接当正式证据。
3. **扩大独立增强评估**。保留两批原始失败和历史结果；另建新批次与预先确定的采样规则，加入跨机器/更多真实无真值样本及人工笔画评价。避免按测试PSNR调参；尤其分析自适应SSIM下降、石花误判与细笔画损失。源/输出SHA、种子、版本、聚类区间继续完整记录。
4. **史料与检索质量**。人工核对更多有权使用的原文位置、人物/地点关系与答案证据；35个外部URL中34个受403/429/TLS限制，需允许访问环境或馆方记录人工复核。只有增加独立标注后才报告检索质量指标，语义检索与生成式回答目前没有实现。
5. **公网部署前独立安全工程**。仍需账户与租户隔离、文件权限、存储配额、过期策略、强任务超时/队列、并发与大图压力测试。当前管理员鉴权与单任务锁不能当成多用户隔离；不要直接开放本地开发服务器。
6. **保留合规与性能待办**。全国地图正式审图许可尚未取得确认；不要改变仓库可见性。JS大块/模型首次加载仍可量测优化，不改几何或地图版图。现有RSS是单机单任务测量，不是并发结论。

## 接续执行入口

先 `git fetch --prune`、审查 `git status`、核对最新远程main；优先新建 `codex/` 分支。阅读S0/最终技术报告及本文件，再使用 `python -m pytest tests -q`、`python scripts/validate_museum_v3.py`、前端 `npm run build` 建立新基线。浏览器按 `/health`→`/generate`→前端启动→`scripts/test_technical_v2_browser.py` 顺序，Windows设置 `RUBBINGMIND_BROWSER_CHANNEL=msedge`。依赖/数据不从原工作区复制进清洁环境。每个未验证环节保持明确状态，不把待办变成成功文案。

## 必须如实保留的限制

- 没有独立人工逐字标签，没有真实外部视觉API识字效果验收；Top-1/Top-3/拒识率均null。`glyph-benchmark-v2.json`等待标注，不能用模板自匹配或模型百分数冒充准确率。
- 外部来源35个HTTP尝试只有1个可达，其余403/429/TLS失败，不宣称实时链接全部通过。
- 管理员单用户远程拒绝/鉴权边界已实现，未完成公网多用户隔离/存储配额/强任务超时或压力测试。
- JS大块、地图正式审图许可、古文字通用OCR仍有限制；不要扩大宣传。

主文档：`docs/audit/technical-implementation-v2.md`、`docs/audit/technical-implementation-v2-report.md`。完整修改文件清单见同目录 `technical-v2-change-manifest.json`；可复现实验及实际失败见 `experiments/results/2026-10-17-v2*`。
