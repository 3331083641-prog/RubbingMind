# 墨韵智考第二阶段技术实装与验收报告

日期：2026-10-17。基线、远程审查和问题清单见 [S0技术审计](technical-implementation-v2.md)。基线提交 `a7a6cb097699e44921d776ff0582f0fa4704ab31`；开发分支 `codex/technical-v2`。本报告仅将实际执行且保留证据的检查列为通过。

## 已完成代码

| 模块 | 实际实现与位置 |
|---|---|
| 自适应增强 | `degradation_analysis.py` 的 `AdaptiveRubbingRestorer`、`analyze_degradation`、`periodic_peaks`。输入图像高通MAD、孤立极值、频谱共轭峰/能量、梯度、对比度、薄笔画风险；选择窄陷波、局部中值、NLM或不处理。 |
| 保真门控 | 输入/输出强结构梯度、变化量、对比度放大诊断；不确定时回退原图。没有历史真值，不称质量准确率。未强制CLAHE、全图形态学或锐化。 |
| 旧算法对照 | `algorithm_engine.py` 保留原低通、NLM/形态学/CLAHE串联。`experiments/run_ablation.py` 取消 `degradation == periodic` 的标签选路；原2026-10-15数据不改写，注明其先验泄漏。 |
| 科研/艺术输出 | 引擎分别输出增强灰度、频谱、二值骨架、轮廓、骨架展陈和朱砂图。scikit-image骨架收敛至细化结果，不再限12次腐蚀或混入Canny。艺术纸纹/风化使用局部随机生成器和记录种子；艺术图不参加PSNR。 |
| 文物身份与运行 | `museum_processing.py` 拒绝真实ID搭配任意外部base64；外图先进入独立上传空间。记录源文件SHA、工作副本尺寸/比例、输出SHA、掩码SHA、种子、图像角色、算法版本和自适应决策。 |
| 真实残字分析 | `glyph_vision.py` 从实际ROI计算灰度、前景、噪点、连通区域、骨架、笔画分布、边界截断警示。`glyph_inference.py` 复用原SQLite记录与采纳/撤销，新增驳回；可选视觉模型链路保留。 |
| 本地字形检索 | 人工指定标签、标注者及依据后加入本地参考库；归一化形状的对称距离变换与投影距离进行排序，不称校准概率。不会将模型建议自动变成独立真值。 |
| 史料检索增强 | `evidence_retrieval.py`：规范证据记录、中文字符/二元词FTS5、BM25、实体消歧、来源支持的一跳扩展与重排。输出摘录、证据ID、原文位置、关系链、来源、已有核验地点。不调用模型生成未知史实。 |
| 28件统一入口 | 每件建立作品、原刻载体、具体拓本、藏所和纪年实体；有据人物才建立关系。沿用已有核心同作品映射，不把建义演示样本与王诵墓志合并。无坐标/路线时不补造。 |
| 释文展示修正 | `catalog.py` 和前端fallback派生读取过滤PDF目录头、馆藏代码及许可附录；原始馆藏清单不改写。修正将“文物统一编号”等当作碑文卷轴的错误。 |
| 实验UI | `experiment_registry.py` 只读文件接口与SHA校验；`ExperimentExplorer.tsx` 实际文件驱动筛选、表格/比较条、输入输出图、CSV/JSON导出、适用数量及限制。单次运行报告独立保留。 |
| 交互修正 | 残字弹窗通过portal挂到页面顶层，解决父级玻璃面板层叠遮挡；PDF修正整章禁止换页造成的大空白与单独页脚，实测当前报告一页可读。 |
| 资源界限 | 大图等比例生成至多160万像素、最长边1800的工作副本；原件只读。处理接口单任务锁，忙时429；请求体实际字节限制18MiB。远程私有数据及写接口管理员鉴权，未配置凭据拒绝。 |

## 新增接口

- `POST /api/research/query`：问题、可选当前文物范围，返回实际检索证据和关系；范围冲突或资料不足不补结论。
- `GET /api/research/steles/{id}`：28件及四核心的来源关系。
- `GET /api/experiments`、`GET /api/experiments/{id}`、`.../assets/{filename}`、`.../export/{kind}`。
- `GET /api/inferences/{id}/analysis/{gray|foreground|skeleton|noise}`；`POST .../template` 明确人工标注参考。
- 原有上传、运行历史、采纳/撤销和报告接口保留；决策新增 `reject`，处理方式新增 `adaptive`。

## 受控实验与真实结果

原2026-10-15：两件、10输入、80输出，历史均值不改写。首个扩展批次 `2026-10-17-v2` 为14件中心区域，140输入/1260输出，发现部分纸边，原始失败数据完整保留。补充 `2026-10-17-v2-text` 使用另外14件，依输入图像字迹条件和固定随机采样选区；七朝代各两件，ID分开发/测试，测试文物未用于调参。满幅石花的宋碑保留困难例外。没有按性能选取区域或去除负提升。

两批新增合计 **28件、280输入、2520输出**。相对参考仍含历史石花/纸纹，不能称为历史无损真值；遮挡没有凭空恢复。两批协议/文物不同，不应将均值差解释为算法迭代效果。

正文区域批次独立测试：7件文物×5退化×2强度，各方法70输入。表内陷波含不适用时的原图返回，适用数在CSV/API另列。

| 方法 | PSNR dB | SSIM | 边缘F1 |
|---|---:|---:|---:|
| 不处理 | 24.705 | 0.704 | 0.620 |
| 高斯低通 | 23.320 | 0.680 | 0.567 |
| Butterworth低通 | 22.754 | 0.655 | 0.535 |
| 自动陷波 | 27.252 | 0.767 | 0.686 |
| Fast NLM | 23.802 | 0.647 | 0.600 |
| 形态学开运算 | 18.617 | 0.471 | 0.377 |
| NLM+CLAHE | 16.956 | 0.563 | 0.520 |
| 固定联合 | 18.829 | 0.485 | 0.336 |
| 新自适应联合 | 26.798 | 0.762 | 0.696 |

新方法改善固定联合，仍不是所有指标最佳；周期陷波在本批PSNR/SSIM更高。中心批次测试自适应SSIM 0.689低于输入0.729，同样保留。CLAHE改变局部亮度、锐化/形态学损伤细节、NLM将原有纹理当噪声等边界在逐退化表说明，不能用视觉更“鲜明”代替接近参考。

两个批次均保存源图SHA、裁切、退化参数/种子、算法源快照SHA、输入和输出PNG SHA、代码版本、环境、耗时、原始指标。各批完整重跑1260次，图像哈希和PSNR/SSIM/边缘值精确一致，耗时不要求一致。`summary.csv` 为记录标准差和按文物聚类重采样的95%区间；`by-degradation.csv` 给出相对输入差值区间和负提升数量。异常与失败案例不删除。

## 残字识读的真实支持范围

真实馆藏ROI已在浏览器保存并显示分析图、坐标、SHA、警示及人工驳回记录。单元测试验证实际裁切哈希、模板检索、视觉请求中的实际PNG、外部服务失败、缺少上下文、采纳/撤销/驳回、不同文物隔离。

**没有配置外部视觉服务进行实际识字测评，也没有独立人工逐字真值。** 接口测试使用受控响应验证传参和失效行为，不当作真实识字效果。`data/catalog/glyph-benchmark-v2.json` 明确待标注；`experiments/evaluate_glyphs.py` 实际输出 `not_evaluated`、n=0、Top-1/Top-3/拒识率=null。本地参考库可用，但不等于通用古文字OCR。规则未读取笔画时继续明确标示。模型建议URL不作为已核验文献引用。

## GraphRAG实际查询与证据

`data/catalog/research-evaluation-v2.json`、`scripts/evaluate_research_v2.py` 和 `technical-v2-research-evaluation.json` 保留六个工程回归实例及实际摘录，不报告虚构准确率：

1. 多宝塔撰文/书丹：岑勋、颜真卿；证据 `history:tang-duobao:relation:0/1`。
2. 曹全原刻：185年；证据 `catalog:han_01_caoquan`。
3. 多宝塔原石/拓本：西安碑林原石与台北故宫具体拓本独立；关系证据 `history:tang-duobao:relation:7`。
4. 原刻/拓印年代：752原刻、明拓著录分别保留。
5. 建义演示样本：证据为本地审计 `history:wei-jianyi:local-audit`，明确未确认真实文物身份，不借528标签归并王诵。
6. 资料外问题：`insufficient_evidence`，不生成史实。

浏览器实测问题检索→证据展开→已有GIS定位，并切换清代新馆藏查询1787原刻著录。检索是FTS/BM25+有据关系扩展，回答是抽取式摘录；未实现或声称神经语义检索、全网实时考据或生成结论独立验证。

35个来源URL进行了真实HTTP访问尝试，**1个可达、34个403/429/TLS失败**，详见 `technical-v2-source-link-check.json`。原审核记录仍可追溯，不能将本次受限链接标为实时通过，也不为了绕过限制更换文物身份。

## 实测性能与安全边界

`performance.json`：新进程整体流水线峰值RSS包含导入、工作数组、PNG与Base64。512×768约0.39秒/124MiB；1024×1536约1.35秒/249MiB；2000×2400生成1154×1385工作副本，约1.42秒/254MiB。单机单次合成噪声输入，不是并发负载结论。第一次Windows内存探针句柄错误得0，保留为invalid记录，未作为有效指标。

本地默认绑定回环地址。远程模式只提供管理员单用户拒绝/鉴权边界，CORS不等于认证。尚无多用户租户隔离、每用户存储额度、自动过期清理、强制任务终止、外部任务队列或并发压力测试；**不可将其宣称为已验收公网多用户服务**。已有用户文件、记录和实验不清理；运行数据库已备份，测试fixture使用隔离数据库。

## 实际验证

- Python：**90 passed**，较基线新增24项；1条现有Starlette/httpx弃用警告。
- TypeScript/Vite构建通过；仍有大JS块警告，未重做模型或地图。
- 馆藏验证：28件、七朝代各4、84张SHA一致。与本次开始快照逐字节比较，正式图和 `data/catalog/steles28.json` 均不变；三维模型和地图素材不改写。
- 安全扫描通过；未纳入用户的未跟踪建模、审核工作区、旧截图或私有数据库。
- 两批各1260行完整重跑，输出和数值无差异。
- 真实Edge/Chromium浏览器：1920×1080、1440×900、1366×768；390×844触屏；五页、六方向、28封面/筛选、处理、原图ROI分析/驳回、史料查询/GIS、清代馆藏、实验筛选/图像与API数值、JSON/PDF、API断开fallback，页面脚本错误0。
- 原上传工作流另外回归：上传→刷新→实际处理→框选→运行关联→JSON/PDF成功。测试上传标为验收私有样本，不属于权威馆藏。
- 浏览器发现并修复弹窗层叠遮挡；两次测试脚本选择器/相对URL错误修正后重跑；PDF通过文字提取及渲染检查，当前文物/运行一致、没有错误认证表述。

真实页面图与记录在 `screenshots/technical-v2/`；`browser-result.json`、`actual-run-report.json/pdf`、`actual-research-query.json` 和上传回归子目录对应实际运行。原3页PDF的大空白不作为最终版，最终打印样例为一页。

## 复现

```powershell
python -m pip install -r requirements.txt
python scripts/init_db.py
python -m pytest tests -q
python scripts/validate_museum_v3.py
python scripts/evaluate_research_v2.py
python experiments/run_v2.py --config experiments/config-v2-text.json --output data/runtime/replay-text
python experiments/evaluate_glyphs.py
cd apps/web
npm ci
npm run build
```

先启动后端并验证 `/health`、`/generate`，再运行 `npm run dev`。浏览器依赖见 `requirements-browser.txt`；`python scripts/test_technical_v2_browser.py --url http://127.0.0.1:5173`，Windows可设 `RUBBINGMIND_BROWSER_CHANNEL=msedge`。CI新增该脚本的`--ci`模式；原在线/fallback冒烟保留。

## GitHub与清洁克隆

待本地最终文件审查后分批正常提交。完成推送、Actions和临时克隆检查后，在本节追加实际SHA、链接及结果；在此之前不将其标为通过。仓库保持原有Private状态，不强推、不清理历史。
