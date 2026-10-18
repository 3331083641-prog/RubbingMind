# 仓库体积保留方案（2026-10-18）

本文件只记录体积和保留决定。没有删除文件。

本地目录体积（不含 `node_modules` 和 `__pycache__`）：

| 目录 | 大约体积 | 处理 |
| --- | --- | --- |
| `rubbings-review-v3/` | 1.6 GB | 未跟踪的审核工作区。不提交。 |
| `rubbings-workspace/` | 518 MB | 未跟踪的实验素材。不提交。 |
| `apps/` | 466 MB | 网站运行需要的前端和 28 件正式图片。保留。 |
| `data/` | 358 MB | 馆藏清单、评估归档和实验输入。保留。 |
| `static/` | 217 MB | 含可再生成的运行结果。正式图片不在这里替换。 |
| `experiments/` | 210 MB | 已提交的 v2.0/v2.1 结果和源码快照。不覆盖、不删除。 |
| `screenshots/` | 161 MB | 已提交的验收图保留。新的失败转储 `screenshots/ci-smoke/` 不入库，由 CI 作为产物上传。 |
| 成品目录与 `design/` | 未跟踪 | 不提交，不移动。 |

克隆后仍可运行：28 件阅读图、封面和评估 ROI 都在已跟踪路径里。`data/runtime/` 和 `static/results/` 继续被忽略，评估接口读取 `data/catalog/assessments/`。
