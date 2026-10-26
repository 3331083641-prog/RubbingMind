# 本地实际验证记录

本轮使用 `D:\RubbingMind` 正式源码。后端 8740、前端 5740；审计数据库、上传和处理输出重定向到 `data/runtime/sync-audit`，没有用本机私人处理记录冒充测试数据。按 `/health` → `/generate` → 前端 → 浏览器顺序启动。日志保存在 `D:\Codex\logs\RubbingMind-sync-20261026`，日志不提交。

| 检查 | 实际结果 | 证据或范围 |
|---|---|---|
| `python -m pytest tests -q` | **773 passed, 1 xfailed**，128.44 秒 | 完整后端、安全、算法、数据与接口测试；A24 预期失败保留 |
| `npm ci`、`npm run build` | 成功 | TypeScript 和 Vite；最终构建 41.82 秒 |
| `npm run test:url` | 13 项通过 | URL 跨页面状态契约；加入 CI |
| `npm audit` | 0 漏洞 | selector parser 最小覆盖升级，前后 CSS 哈希相同 |
| `validate_museum_v3.py` | 成功 | 28 件、84 张图、378 对重复比较；23 CC BY 4.0、2 CC0、3 Public Domain |
| `validate_history_gis.py` | 成功 | 地理与历史数据约束；无依据位置仍保留 null / text-only |
| `verify_experiment_evidence.py --replay` | 成功 | 两批 2520 条 PSNR / SSIM / edge F1 重算，最大差 0；2828 张结果图及 28 张来源图哈希核对；252 次确定性选样历史代码重放像素完全一致 |
| Windows PowerShell 5.1 `start.ps1` / `check.ps1` | 成功 | 实际健康端点与启动兼容，不只静态解析 |
| 浏览器 smoke | 成功 | 五页导航、正式馆藏与后端离线回退 |
| `test_technical_v2_browser.py --ci` | 成功 | 实际处理、残字选区、驳回落盘、真实史料检索、报告 API 数值一致、JSON / PDF |
| `test_museum_v3_browser.py` | 成功 | 28 件详情、原图、档案缩放拖动、工作台 / 图谱联动、在线 / 离线报告导出 |
| `test_graph_browser.py` | 成功 | 地点、图层、关系网络拖动缩放筛选、纪年和事件联动、卸载重载 |
| `test_terrain3d_browser.py` | 成功 | 2D / 3D 切换、DEM 探针、地形、边界和水系控件 |
| `test_terrain3d_v22_browser.py` | 成功 | V2.2 地形与 31 省名标注；本次画幅无标签重叠。单次 FPS 不作为普遍性能保证 |
| 首页 ambient media 专项 | 成功 | Edge 实际 H.264 播放、循环、GLB、StrictMode、回退与减弱动态效果 |
| `verify_sync_delivery.py` | 成功 | 五页 × 1920×1080 / 1440×900 / 1366×768，无全局横向溢出；390 手机首页；报告实图、图表、负提升、机制图和导出 |
| 真实 UI 上传与处理 | 成功 | 公开受控退化样图，原始字节 SHA 一致，真实后端执行，正式馆藏仍为 28 件；见 verification-upload.json |
| 保护资产检查 | 成功 | 528 个二进制资源与原 main 相同，含 84 张馆藏图；保护的地图与碑刻展示源码没有被本轮替换 |
| Git 对象连通性 | 成功 | `fsck --connectivity-only --no-reflogs`；预存 dangling / tmp 对象未清理 |

## 首轮失败、原因与修复

- 首轮 pytest 有 1 失败：导入时捕获的结果目录仍读取本机历史，测试隔离不完整。修复测试目录注入后完整通过，未放松报告运行筛选条件。
- 新报告请求的 `/derived/` 地址原先没有后端路由。补受限只读接口，验证批次、来源 SHA、登记案例与影像 SHA；过期统计返回 409，越界拒绝。新增四项回归测试通过。
- 老浏览器脚本使用旧报告标题、列顺序、重复的馆藏标识或过时水系控件名称。更新为当前可访问角色和精确定位，同时核对真实 API 值、离线状态及导出内容；专项重新运行通过。
- `start.ps1` 无 BOM，在系统 Windows PowerShell 5.1 解析中文失败；保存为 UTF-8 BOM 后真实启动通过。
- 原 npm audit 有 3 个中危项；最小依赖覆盖后为 0，没有升级 Tailwind 主版本或调整主题。
- 导出原先把无法加载记录也称为未运行。现区分 `not_run`、`not_loaded`、`unavailable`；浏览器验证离线导出，临时置信区间在页面和 JSON 明示来源。
- 两项新增安全扫描回归测试确认忽略私有缓存 / 工作树，同时拒绝待交付的秘密配置；输出仅包含位置，不含命中值。

## 保留的限制

A24 完整 ROI 对照闭环仍未交付；没有把预期失败删除。古碑残字没有独立人工标注准确率，未调用真实可选视觉服务；同批复测不是独立留出集。历史机制图保持历史 head，过期 CI 不篡改哈希，临时 bootstrap 明示来源。争议史料和专家复核状态保留。

构建仍有大包体积提示，pytest 有 Starlette / httpx 弃用提示；都不伪装成失败或已消除。重放验证不声称复现运行时间，也不把受控图像指标解释为古文字识别准确率。

当前候选文件与全部将推送的新增历史对象均执行密钥检查；提交前再次检查大文件、`git diff --check` 与候选清单。远程 CI 和最终 main SHA 在本机 `FINAL_SYNC_REPORT.md` 与合并 PR 中记录。
