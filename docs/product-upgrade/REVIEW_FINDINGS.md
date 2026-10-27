# 审查发现（REVIEW_FINDINGS）

本文件采用追加写入，每条注明作者 Agent 与时间（Asia/Shanghai）。不修改他人条目。

---

## RM-红队QA（Agent 11+12）· Phase 0 基线与安全红队发现

- 作者：RM-红队QA（Agent 11+12）
- 时间：2026-10-19 12:07（Asia/Shanghai，笔记本时间）
- 范围：`f0c5886`（feature/product-grade-upgrade），在只读 worktree `D:\RubbingMind-wt\qa-baseline` 中执行；后端 127.0.0.1:8740，前端 127.0.0.1:5740。
- 分级：P0 = 正确性/安全/真实流程/可信交付受损；P1 = 重要缺陷或高风险；P2 = 改进项或低风险。
- 测试命令与输出见 `BASELINE_TESTS.md`（BT-xx）。
- 结论：本轮**没有 P0**。路径穿越、上传校验、FTS 注入、CORS、远程模式认证、密钥泄漏这几项探测都通过（见“已验证通过的安全项”）。

### RT-001 · P1 · `test_technical_v2_browser.py` 完整模式在 390×844 移动端失败（基线测试不绿）
- 作者：RM-红队QA（Agent 11+12）；时间：2026-10-19 12:07
- 位置：`scripts/test_technical_v2_browser.py:22`（`nav()` 直接点 `header` 里的按钮），`:150-152`（390×844 移动端分支）；`apps/web/src/components/Header.tsx:74`（主导航在 `xl` 以下改为汉堡按钮 `xl:hidden`，`aria-label="打开主导航"`）。
- 证据：BT-06a，`python scripts/test_technical_v2_browser.py --url http://127.0.0.1:5740` 的退出码为 1，报错 `TimeoutError: Locator.click: Timeout 30000ms exceeded ... waiting for locator("header").first.get_by_role("button", name="时空图谱中心")`，出错行 152。桌面三种分辨率的段落都已执行。`--ci` 模式不含移动端，退出码为 0（BT-06b）。
- 用户影响：BRIEF 第 5 节要求的 390×844 移动端检索流程在基线上没有自动化证据。CI 只跑 `--ci`，所以这个失败不会出现在 CI 里。目前无法判断移动端用户能否经汉堡菜单完成检索。
- 建议修复路径：由测试负责人修改 `nav()`：先检测是否有“打开主导航”按钮，有则先点开再选项目。若 UI 本应在移动端直接显示导航，则改 UI。两种做法选其一，经审查后再修改。
- 验收标准：`python scripts/test_technical_v2_browser.py --url <前端>` 在不带 `--ci` 时退出码为 0，`mobileOverflow=false`，且 `12-mobile-touch-retrieval.png` 已生成。

### RT-002 · P1 · 启动时样本回退：从未授权第三方站点下载图片，失败后本地合成“高仿真碑拓”，作为核心演示样本写入 `static/samples`
- 作者：RM-红队QA（Agent 11+12）；时间：2026-10-19 12:07
- 位置：`main.py:49-57`（lifespan 调用 `ensure_samples()`）；`sample_generator.py:47-89`（`REMOTE_SAMPLE_URLS`，其中 3 个为 `http://` 明文，来自 yueyaa.com、itc.cn、dengdingsheng.com、yac8.com 等站点）；`sample_generator.py:119-135`（`requests.get(..., verify=False)`，伪造 `Referer: https://www.google.com/`，把 JPEG 字节原样写成 `.png`）；`sample_generator.py:301-305`（“本地高仿真碑拓合成引擎”兜底）。
- 证据：只读代码审查。当前已跟踪的 `static/samples/sample_1..4.png` 都存在且大于 5 KB（149,829 / 236,484 / 183,224 / 199,685 字节），基线运行时没有触发回退。只要文件缺失或小于 5 KB，下次启动就会静默触发。
- 用户影响：可能违反真实性铁律（合成图冒充核心样本，“图像清晰≠恢复原刻”）和来源授权要求（第三方站点图片无授权记录）。关闭 TLS 校验后再写入静态目录，存在供应链和内容被篡改的风险。替换后原图 SHA 会改变，但不会给出任何告警。
- 建议修复路径：去掉网络下载和合成兜底。样本缺失时启动失败或显式降级，`/health` 报告 `samples_missing`，不生成替代图。若必须保留合成图，则写到独立目录并标“合成·非文物”，不得使用 `sample_N.png` 文件名。核心样本按 SHA-256 清单校验。
- 验收标准：删除任一 `sample_N.png` 后启动，没有网络请求，也没有生成新文件；`/health` 明确报告缺失；UI 不展示替代图。对已有样本做 SHA 校验，失败时有告警。

### RT-003 · P1 · 测试脚本与启动脚本默认指向用户端口（8000/5173/5180），并且会写数据
- 作者：RM-红队QA（Agent 11+12）；时间：2026-10-19 12:07
- 位置：`scripts/test_technical_v2_browser.py:170`（`--url` 默认 `http://127.0.0.1:5180`，即用户 Vite 端口）；`scripts/test_graph_browser.py:8-9`、`scripts/test_terrain3d_v22_browser.py:22-23`（默认 8000/5173，可用 `GRAPH_BACKEND_URL`/`GRAPH_FRONTEND_URL` 覆盖）；`apps/web/vite.config.ts:10-16`（代理默认 `http://127.0.0.1:8000`，可用 `RUBBINGMIND_API_TARGET` 覆盖）；`start.ps1:39-41`（端口从 8000 起递增，不能指定）；`start.bat`（固定 `python main.py`，即 `main.py:542` 的 8000，并且会 `pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com`）。
- 证据：代码审查。基线运行时，笔记本 8000 端口被用户进程 PID 30712 占用（`netstat -ano`）。本 Agent 全部改用环境变量或参数指向 8740/5740。
- 用户影响：technical_v2 测试会执行真实写操作：POST `/api/process`、`/inferences` 以及决策写入（脚本第 61、73 行）。按默认参数运行时，这些写入会经用户的 5180 开发服务器进入主工作区数据库和 `static/results`，污染用户数据。start.ps1 无法按 COORDINATION 分配的端口启动，多 Agent 并行时会抢占 8001 之后的端口。start.bat 会静默安装依赖，镜像源还被标为受信任。
- 建议修复路径：所有浏览器脚本都要求显式提供 `--url`/`--backend`，或者默认使用临时端口并拒绝连接 5180/8000。start.ps1 增加 `-Port` 参数。start.bat 去掉自动 pip 安装，或者改为提示。
- 验收标准：不带参数运行任一浏览器脚本时，不会访问 5180/8000，并给出明确提示；`start.ps1 -Port 8740` 可用。

### RT-004 · P2 · pytest 有副作用：改写已跟踪文件，并在项目 `data/` 下创建或使用真实 SQLite
- 作者：RM-红队QA（Agent 11+12）；时间：2026-10-19 12:07
- 位置：`scripts/validate_stele_asset.py:55`（写 `screenshots/stele-final/asset-validation.json`，由 `tests/test_stele_asset.py` 间接调用）；`database.py:12`（`DB_PATH=data/rubbingmind.sqlite`）。只有部分测试 monkeypatch 了 `DB_PATH`（test_glyph_*、test_upload_flow、test_museum_v3）。
- 证据：BT-01 之后，在全新 worktree 中执行 `git status --porcelain`，结果为 ` M screenshots/stele-final/asset-validation.json`（`git diff --stat` 为空，只有 CRLF/LF 行尾差异）；`git status --ignored` 出现 `data/rubbingmind.sqlite` 和 `data/runtime/evidence-v2.sqlite`，两者在 pytest 之前都不存在。
- 用户影响：在主工作区 `D:\RubbingMind` 跑 pytest 会改动已跟踪文件，还可能读写用户真实的 `data/rubbingmind.sqlite`（其中有 `user_uploads` 表）。是否真的写入还没有逐个测试确认。
- 建议修复路径：增加 `tests/conftest.py`，把 `DB_PATH`、`UPLOAD_DIR`、`museum_processing.BASE`、证据索引路径统一重定向到 `tmp_path`。`validate_stele_asset` 增加输出路径参数，测试时写入 tmp 目录。
- 验收标准：在全新 worktree 跑 `pytest` 之后，`git status --porcelain --ignored` 中没有新出现的 `data/*.sqlite`，也没有被修改的已跟踪文件。

### RT-005 · P2 · 没有安全响应头；remote 模式下 `/docs`、`/openapi.json` 仍然公开
- 作者：RM-红队QA（Agent 11+12）；时间：2026-10-19 12:07
- 位置：`main.py:62-80`（没有任何设置安全头的中间件）；`runtime_guard.py:17`（`sensitive` 判定不包含 `/docs`、`/openapi.json`）。
- 证据：BT-10，`GET /` 的响应头中只有 `server: uvicorn`，没有 CSP、`X-Content-Type-Options`、`X-Frame-Options`。BT-12，`RUBBINGMIND_DEPLOYMENT=remote` 时 `GET /docs`、`GET /openapi.json` 都返回 200。
- 用户影响：受控演示（B 模式）下可能被 iframe 嵌入（点击劫持），没有 MIME 嗅探防护，完整 API 结构也对外公开。
- 建议修复路径：增加安全头中间件（`nosniff`、`frame-ancestors 'self'`、适度的 CSP）。remote 模式下设置 `docs_url=None`、`openapi_url=None`，或者对这两个路径要求认证。
- 验收标准：remote 模式下 `/docs` 返回 401 或 404；所有响应都带有 `X-Content-Type-Options: nosniff` 和 `frame-ancestors`/`X-Frame-Options`。

### RT-006 · P2 · 遗留页面 `static/index.html`：API Key 存在 localStorage、CDN 脚本没有 SRI、调用已不存在的接口
- 作者：RM-红队QA（Agent 11+12）；时间：2026-10-19 12:07
- 位置：`static/index.html:8,10,12`（`cdn.tailwindcss.com`、`cdn.jsdelivr.net/npm/vue@3`、`echarts@5.5.0`，没有 `integrity`）；`:1312,1416,1737`（`localStorage.setItem('rm_api_key', ...)`）；`:1493`（`fetch('/api/samples')`，后端没有这个路由）。`main.py:308-310`：dist 缺失时 `/` 回退到这个页面。`main.py:104-109`：`DeduceRequest.api_key` 字段没有任何路由使用。
- 证据：BT-11 中的 git grep 输出；BT-13 干净克隆在没有 dist 时 `GET /` 返回 200，实测页面包含 `cdn.jsdelivr.net/npm/vue@3` 和 `rm_api_key`，说明跳过构建的用户实际会看到这个页面。
- 用户影响：前端构建缺失时，用户看到的是过时页面，并可能被引导把 API Key 存进浏览器。CDN 一旦被投毒就能读取这个 Key。
- 建议修复路径：删除或归档 `static/index.html` 和 `DeduceRequest`（需要先经 Green 确认）。dist 缺失时 `/` 返回明确的“请先构建前端”提示。
- 验收标准：`/static/index.html` 返回 404，或者页面不再含 API Key 输入；仓库中不再有 `rm_api_key`。

### RT-007 · P2 · `.env.example` 的变量名与代码不一致
- 作者：RM-红队QA（Agent 11+12）；时间：2026-10-19 12:07
- 位置：`.env.example:16-20`（`LLM_PROVIDER`/`LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL_NAME`）；代码读取的是 `RUBBINGMIND_VISION_API_KEY`/`_BASE_URL`/`_MODEL`（`glyph_inference.py:154-157`），README:49 与代码一致。
- 证据：BT-11，在已跟踪文本中搜索时 `LLM_API_KEY` 只出现在 `.env.example`。`git grep -i -E "dotenv|load_dotenv|env_file"` 无命中，`git grep -E "APP_PORT|DATABASE_URL|LLM_API_KEY|STATIC_STORAGE_DIR" -- "*.py"` 也无命中，即模板中的变量代码都不读取，也没有自动加载 `.env`。
- 用户影响：用户按模板配置后，模型始终是“未配置”，降级原因不透明。另外 `RUBBINGMIND_DEPLOYMENT`、`RUBBINGMIND_ADMIN_TOKEN`、`RUBBINGMIND_REVIEW_TOKEN` 都没有写进模板。
- 建议修复路径：按代码实际读取的变量重写 `.env.example`，并说明它不会被自动加载、需要设成环境变量。
- 验收标准：`.env.example` 中每个变量都能在代码里找到读取点，代码读取的 `RUBBINGMIND_*` 变量也都出现在模板中。

### RT-008 · P2 · 前端开发依赖有已知漏洞（生产依赖为 0）
- 作者：RM-红队QA（Agent 11+12）；时间：2026-10-19 12:07
- 位置：`apps/web/package.json` 中的 `vite@^5.1.6`（锁定 5.4.21）和 `tailwindcss`。
- 证据：BT-07，`npm audit`：9 个漏洞（3 moderate、6 high），涉及 vite（Optimized Deps `.map` 路径穿越、launch-editor NTLMv2 泄露）、esbuild（开发服务器可被任意网站跨站读取）、braces/micromatch/chokidar（ReDoS）。`npm audit --omit=dev` 结果为 `found 0 vulnerabilities`。
- 用户影响：只在运行 `npm run dev` 时暴露，影响本机开发服务器。Vite 默认只绑定 localhost，风险较低。
- 建议修复路径：评估升级 vite 到已修复版本，由架构 Agent 负责并做回归。开发服务器保持 `--host 127.0.0.1`。
- 验收标准：`npm audit` 中没有 high 级别项，或者每项都有书面接受理由。

### RT-009 · P2 · 本地模式按 loopback 地址放行写操作：经本机反向代理或隧道暴露时会被绕过
- 作者：RM-红队QA（Agent 11+12）；时间：2026-10-19 12:07
- 位置：`runtime_guard.py:18-22`（`local` 模式下，loopback 来源的写请求不需要 token）；`catalog_assessment.py:90-95`（`review_allowed` 按 host 放行）。
- 证据：代码审查。BT-12 证实 remote 模式在没有 token 时拒绝访问（fail-closed）。
- 用户影响：用户若用 frp/ngrok/IIS 等本机反代把 local 模式的服务对外暴露，所有请求的来源都会是 127.0.0.1，上传、删除、标注全部不需要认证。
- 建议修复路径：README 和启动日志中明确写出：对外暴露必须用 `RUBBINGMIND_DEPLOYMENT=remote`。检测到 `X-Forwarded-For`/`Forwarded` 头时按非本机处理。
- 验收标准：带 `X-Forwarded-For` 的 loopback 写请求在 local 模式下也返回 401。

### RT-010 · P2 · CI 覆盖与触发范围不足
- 作者：RM-红队QA（Agent 11+12）；时间：2026-10-19 12:07
- 位置：`.github/workflows/ci.yml:3-8`（只在 `main` 的 push/PR 上触发）；ci.yml 没有运行 `validate_history_gis.py`、`test_graph_browser.py`、`test_terrain3d_v22_browser.py`，`test_technical_v2_browser.py` 只跑 `--ci`。
- 证据：只读审查 ci.yml。
- 用户影响：集成分支 `feature/product-grade-upgrade` 没有 CI 证据。RT-001 这类失败不会在 CI 中出现。
- 建议修复路径：在 Phase 6 合入 main 之前，在本地按 BASELINE_TESTS 跑全量；或者把 workflow 的触发范围扩大到 `feature/**` 并加入 GIS 校验。由 Green 决定。
- 验收标准：合入前有全量本地测试记录，或者有 feature 分支的 CI 运行记录。

### RT-011 · P2 · `start.ps1` 用 POST `/generate` 做健康检查，remote 模式下必然失败
- 作者：RM-红队QA（Agent 11+12）；时间：2026-10-19 12:07
- 位置：`start.ps1:49-50`、`check.ps1:16`；`runtime_guard.py:17`（所有非 GET 请求都视为 sensitive）。
- 证据：BT-12，remote 模式下 `POST /generate` 返回 401。
- 用户影响：B 模式下无法用一键脚本启动，失败提示会误导用户以为服务没起来。
- 建议修复路径：健康检查改用 `GET /generate` 或 `GET /api/health`。
- 验收标准：`RUBBINGMIND_DEPLOYMENT=remote` 时 start.ps1 能完成启动检查。

### RT-012 · P2 · README 中的地形顶点数与 V2.2 测试实测值不一致（待核）
- 作者：RM-红队QA（Agent 11+12）；时间：2026-10-19 12:07
- 位置：README“三维真实地貌”一节写的是“全国网格 620,964 顶点”；`scripts/test_terrain3d_v22_browser.py` 本次输出为 `performance.vertices = 1081476`，`interactiveFps = 158.3`。
- 证据：BT-05。
- 用户影响：可能是统计口径不同（只算地形网格，还是包含叠加层），也可能是文档数字过时，属于专题 H“无法证明的宣传”的待核项。FPS 只是本机单次数值。
- 建议修复路径：由图谱 Agent 说明两个数的口径，README 写明口径、硬件和日期。
- 验收标准：README 中的数字能由脚本复现，并写明口径。

### RT-013 · P2 · 删除运行记录只靠 query 参数确认，没有撤销或回收
- 作者：RM-红队QA（Agent 11+12）；时间：2026-10-19 12:07
- 位置：`main.py:393-400`（`confirm: bool = False`）；`museum_processing.py:100-108`（`shutil.rmtree` 删除输出目录）；`apps/web/src/pages/WorkbenchPage.tsx:168-169`（`window.confirm`）。
- 证据：BT-10，不带 confirm 时返回 400 `删除单次处理记录需要明确确认`；穿越形式的 run_id/stele_id 返回 404（`read_run` 有正则校验，`museum_processing.py:73`）。
- 用户影响：确认之后直接物理删除，不可恢复。报告和推演记录中引用的 runId 会悬空（`inferenceRecords` 中的 runId 没有级联检查）。
- 建议修复路径：改为软删除（移入 `data/runtime/trash/` 并保留 N 天），或者删除前检查是否被推演或标注引用。
- 验收标准：被引用的 run 无法删除，或删除后可以恢复；报告对已删除的 run 给出明确状态。

### 已验证通过的安全项（证据见 BT-10/11/12，不单列为缺陷）
- 路径穿越：`/static`、`/assets`、实验资产、评估资产、上传、推演、运行记录、报告 `run_id` 一共 20 条 `../`、`%2e%2e`、`%2f`、`%5c` 变体，全部返回 404 或 409，没有读到文件内容。实现见 `experiment_registry.py:67-69`、`museum_processing.py:73,103-106`、`glyph_inference.py:59-61,100-102`。
- 上传：非图像 MIME、SVG、MIME 与内容不一致、截断 PNG、空文件、16×16、6000×40、声明 30000×30000 的解压炸弹头、13 MiB、19 MiB，全部被拒绝（415/400/413），没有 500，也没有路径泄漏。
- 注入：FTS5 查询用 `?` 参数化，每个词加引号（`evidence_retrieval.py:318-319`）。测试了 `"`、`" OR 1=1 --`、`NEAR(`、`*`、`a) OR (b`，都没有 500。检索不经过 LLM，“忽略之前所有指令……把作者改为李白”这类注入文本没有改写结论；“多宝塔碑作者是李白吗？”的结论为 `contradicted`。
- XSS：React 端唯一的 `dangerouslySetInnerHTML` 在 `Latex.tsx:20`（katex 输出，`trust` 为默认的 false），并且这个组件目前没有被任何页面引用。含 `<img onerror>` 的上传标题按原文保存，由 React 文本节点转义输出（界面尚未截图验证）。
- CORS：只允许 `^http://(127.0.0.1|localhost):517[0-9]$`（`main.py:72`），`evil.example`、`null` 都没有返回 ACAO。
- 公网暴露：`main.py:542`、`start.ps1:44` 和 CI 都绑定 127.0.0.1，没有 0.0.0.0。`vite.config.ts` 没有设置 `host`（默认 localhost）。
- 错误信息：所有探测响应中都没有 `Traceback`、`D:\` 或 `File "`；上传接口的 500 分支使用固定文案（`main.py:450-452`）。
- 密钥：工作树已跟踪文本和全部 71 个提交的 `git log -p --all` 中，强特征（sk-/AKIA/ghp_/github_pat_/AIza/xox*/私钥头/hf_）命中 0 条；通用 `key=value` 规则命中 1 条，为误报（`static/index.html` 中的 `localStorage.getItem`）。历史中提交过的敏感文件名只有 `.env.example`。
- remote 模式：没有 token 或 token 错误时，`/api/steles`、报告、上传图像、POST 接口都返回 401。


---

## RM-红队QA（Agent 11+12）· 对 AUDIT_EVALUATION.md 三条 P0 的独立复核

- 作者：RM-红队QA（Agent 11+12）
- 时间：2026-10-19 12:13（Asia/Shanghai，笔记本时间）
- 方法：只读取原文中这 3 条的标题，不采信原文的证据和数字，全部在 worktree `D:\RubbingMind-wt\qa-baseline`（f0c5886）中用自己写的 Python 脚本重新计算。E-03 的后端在 8740 启动，使用 worktree 自己的数据库与运行目录。主工作区 `static/results` 只做只读的哈希和像素统计，没有在主工作区上启动服务。

### RV-E01 · 复核结论：**成立**（泄漏事实成立；“看过结果之后才改 v2.1”只证明了时间先后，因果关系没有证明）
- 样本重叠：`experiments/results/2026-10-18-v21-heldout/results.json` 的 14 件 `samples` 与 `2026-10-17-v2-text/results.json` 的 14 件 `sources` **完全相同**（交集 14/14：han_03_liqi、han_04_shichen、wei_03_kouyan、wei_04_wangsong、tang_03_yanjiamiao、tang_04_xuanmita、song_03_daguan、song_04_mengying、yuan_03_shengzhu、yuan_04_jingyuanchang、ming_03_wugou、ming_04_tongdian、qing_03_sanxitang_preface、qing_04_ayuwang_reliquary）。与 `2026-10-17-v2` 的交集为 0。
- 图像 SHA：这 14 件在两个批次中的 `file` 相同，`sourceSha256` 相同，并且都与当前文件重新计算的 SHA-256 一致（14/14 为 True）。
- 裁切重叠（两个批次都是 256×256 裁切，按 [x0,y0,x1,y1] 计算交集）：`song_03_daguan` 两批裁切完全相同 [497,1328,753,1584]，重叠 65536 px，占 100%；`tang_04_xuanmita` 为 [896,768,1152,1024] 与 [850,760,1106,1016]，重叠 52080 px，占 79.5%。其余 12 件重叠为 0。
- 在 v2-text 中，这 14 件里有 7 件是 `split=test`（han_04、wei_04、tang_04、song_04、yuan_04、ming_04、qing_04），也就是说留出批次复用了上一批的测试集文物。
- 排除名单：`experiments/compare_v21.py:49-51` 中的 `previous` 集合是 2026-10-17-v2 那批的 14 件（每个朝代前两件）。脚本取每个朝代后两件（`:54` `group[-2:]`），`:61-63` 的检查只保证不与 `previous` 重叠，**没有把 v2-text 批次纳入排除**。docstring（`:3-4`）和结果字段 `notThePreviousBatch` 都只提到 2026-10-17 v2，没有提到 v2-text。不过 `notThePreviousBatch` 也写了“仍是同一批 28 件阅读图，不是新的外部隐藏集”。
- 时间线（`git log`）：v2-text 的 results.json 首次提交于 f9aebdb（2026-10-17 18:13:10 +0800）；baseline f97ffab（10-17 22:55）中 `VERSION='adaptive-rubbing-v2.0'`；`adaptive-rubbing-v2.1` 首次出现在 ea5a67a（10-18 00:56:59）；留出对比提交于 59f9784（10-18 10:52:59）。v2.1 确实是在 v2-text 结果存在之后才写的。
- 用户影响：“v2.1 在留出集上优于 v2.0”的说法不能成立为留出结论，最多只算 development 或复用数据上的结果。
- 建议与验收：把这次对比重新标为“非留出/复用 v2-text 文物”；真正的留出集必须排除所有已用于开发或测试的文物和裁切，并在计分前冻结名单与 SHA。验收标准：新留出集与所有既往批次的文物交集为 0，或者裁切重叠为 0 且有书面说明。

### RV-E02 · 复核结论：**成立**
- 方法：在两个 v2 批次的 `rows` 中，对每一行比较 `inputSha256` 与 `outputSha256`，并抽取文件逐字节比较。
- `2026-10-17-v2`：`adaptive_joint` 共 140 行，其中输出与输入 SHA 相同的有 **55 行**（38 行 `diagnostics.selectedOutput='candidate'`，17 行 `selectedOutput='original'`），**全部是 `applicability='applied'`**。抽样 `han_01_caoquan_periodic_1`：`..._input.png` 与 `..._adaptive_joint.png` 逐字节相同（SHA 前缀都是 c192197e03c9）。
- `2026-10-17-v2-text`：`adaptive_joint` 中相同的有 **45 行**（33 行 candidate，12 行 original），全部是 applied。抽样 `han_03_liqi_periodic_1` 逐字节相同（b28f3644b363）。
- 计入均值：summary 中 adaptive_joint 的 `n=70`、`applicableN=70`（两个 split 都是），说明 identity 行全部计入了均值。重算结果如下（psnr 不为空的行）：

| 批次 | split | 全部 n / 均值 | 其中 identity n | 只算实际改动的行 n / 均值 |
|---|---|---|---|---|
| v2 | development | 70 / 27.510 | 24 | 46 / 27.831 |
| v2 | test | 70 / 25.350 | 31 | 39 / 25.667 |
| v2-text | development | 70 / 27.159 | 22 | 48 / 28.619 |
| v2-text | test | 70 / 26.798 | 23 | 47 / 28.466 |

  重算的总均值与 summary 中的 psnrMean 一致（27.51、25.35、27.159、26.798），口径确认无误。
- 代码位置：`experiments/run_v2.py:108` 对自适应方法一律写 `applicability='applied'`；`degradation_analysis.py:195` 在 `gate['accepted']` 时写 `'candidate'`，`:234` 写 `'original'`。还有一点要注意：有 33–38 行虽然标为 `candidate`，输出却与输入逐字节相同（候选本身就是 identity）。其他方法也有少量 identity 行：fast_nlm 在 v2 中 4 行、在 v2-text 中 2 行与输入相同且标为 applied；notch 在 v2 中有 6 行与输入相同，标为 not_applicable。
- 用户影响：“自适应”方法的均值混入了 31%–44% 的原图返回行，无法区分“算法有效”和“没有处理”。
- 建议与验收：行级增加 `outputIdenticalToInput` 和 `effectiveApplicability`（applied/identity/gated_original）。summary 分别给出“全部”和“实际处理”两套统计，并给出 identity 数量。验收标准：任意一行若 SHA 相同，就不得出现 `applied` 加 `candidate` 的组合；summary 的 identity 计数与行级统计一致。

### RV-E03 · 复核结论：**成立**
- 主工作区只读统计（脚本读取各 run 的 `processing.json`，用 OpenCV 灰度读取 `outputImages.original` 与 `outputImages.restored`，统计逐像素差）：自适应运行共 12 次，即 `tang_01_duobao` 10 次（v2.0 6 次、v2.1 4 次）、`tang-duobao` 1 次（20261018T072201）、`upload-cf737e88…` 1 次。其中 **tang_01_duobao 的 10 次全部是 changedPx=0/1598565、maxAbs=0**，另外 2 次有改动（644816 px 和 24368 px）。10 次零改动的运行，诊断中都是 `selectedOutput='candidate'`、`fidelityGate.accepted=true`。
- 8740 复现：worktree 后端（PID 10124，worktree 自有数据库与 `static/results`）执行 `GET /api/steles/tang_01_duobao/report`，返回 200，`reportId=RM-tang_01_duobao-20261019T035008_2d99637c`（由本 Agent 的 technical_v2 测试生成），`evaluation_summary` 为 **“实际处理已执行，但没有配对真值；配对质量未评测。”**。同一个 run 中：`outputSha256.restored` 与 `outputSha256.original` 都是 `5532e851…c6c3`（相同），`fidelityGate.meanAbsoluteChange=0.0`，`decisions` 的 operator 为 `['skip_notch','identity']`，`selectedOutput='candidate'`。worktree 中的另一次运行 20261019T034806 同样是 0 像素改动。
- 代码位置：`main.py:382` 只要有 run 就写“实际处理已执行”，不看输出是否改动。`apps/web/src/pages/ReportsPage.tsx:99` 的 figcaption 固定写“本次算法输出；不作为原刻真值。”，没有零改动提示（另外 `WorkbenchPage.tsx:461` 也出现“算法输出”）。对照归档评估页 `AssessmentViewer.tsx:110`，那里在 `record.unchanged` 时会写“处理前后像素没有发生变化”。
- 用户影响：默认报告把未改动的原图展示成“本次算法输出”，后端还声称“实际处理已执行”，违反“区分原图返回与实际处理”的要求，属于可信交付问题。
- 建议与验收：后端在 run 中写入 `outputIdenticalToInput`（以 restored 与 original 的 SHA 比较）。`evaluation_summary` 在 identity 时改为“算法判定无需处理，输出与输入逐像素相同”。报告页相应改文案，并且不展示 restored 图，或者明确标注“未改动”。验收标准：对 tang_01_duobao 跑一次默认处理后，报告 JSON 与页面都显示“未改动”，且不再出现“实际处理已执行”和“本次算法输出”。

### 复核小结
| 原条目 | 复核结论 | 关键复现证据 |
|---|---|---|
| E-01 | 成立（因果部分未证明） | 14/14 同文物同 SHA；song_03 100%、tang_04 79.5% 裁切重叠；compare_v21.py:49-51 只排除了 v2 批次 |
| E-02 | 成立 | v2 有 55 行、v2-text 有 45 行输出与输入逐字节相同，却记为 applied 并计入 n=70 的均值 |
| E-03 | 成立 | 主工作区 tang_01_duobao 10/10 次为 0 像素改动；8740 上报告仍写“实际处理已执行”，restored SHA 等于 original SHA |

## RM-红队QA（Agent 11+12）— 第二轮：三份审计 P0 复核 · ASSET_FREEZE 抽检 · eval-sci 代码审查 · RT-002 升级评估

- 作者：RM-红队QA（Agent 11+12）
- 时间：2026-10-19 12:30（Asia/Shanghai，笔记本实测时间）
- 复现环境：
  - 与 run 无关的项：qa-baseline（D:\RubbingMind-wt\qa-baseline，f0c5886）后端 127.0.0.1:8740，本地模式，PID 35952，用完已停。
  - 依赖 run 的项（P0-1/P0-3/E-P0-01/E-P0-03 计数）：临时副本 C:\Users\WPY11\rm-redteam-qa-tmp\replica，用 `git clone --shared` 建立，检出 f0c5886。主工作区的 static/results、data/uploads、data/rubbingmind.sqlite、data/runtime/evidence-v2.sqlite 只读复制到该副本。后端 8740，PID 12212，已停。没有复制进任何 worktree。
  - 未触碰 D:\Codex\worktrees。
- 主工作区数据库 SHA-256：开始（12:16:46）与结束一致，结束值见本节末尾。

### 一、AUDIT_FRONTEND.md F-P0-1…6 复核 → 结论：**通过**（6 条均成立；P0-4 定级可商榷）

| 项 | 判定 | 我的证据 |
|---|---|---|
| F-P0-1 报告默认 legacy run | **成立** | 副本 8740 上 `GET /api/steles/tang-duobao/runs` 的顺序：20261014T165542_5fc44fba（未记录）→ 20261015T013329_809b9df4（未记录）→ 20261018T072201_13772747 → 20261017T093048_6fc67e99。`/report` 的 run.runId 为 20261014T165542_5fc44fba，而不是验收要求的 20261018T072201_13772747。han-caoquan 唯一的 run 也是 legacy。代码位置：ReportsPage.tsx:20 `setRunId(items[0]?.runId)`。 |
| F-P0-2 无共享 runId 和深链 | **成立** | App.tsx:17-19 只有 currentTab 和 selectedSteleId 两个状态，App.tsx 里没有 runId（git grep 无命中）。全前端没有 router、pushState 或 useSearchParams，唯一的 URLSearchParams 是 SteleViewer.tsx:259 的 steleQA 参数。WorkbenchPage.tsx:45、146 与 ReportsPage.tsx:13 各自维护 runId。 |
| F-P0-3 passthrough 被称为算法输出 | **成立** | tang_01_duobao 的默认报告 run 是 20261018T082526_4728b9df。其 original.png 与 restored.png 的 SHA 都是 5532e85185cb…，灰度差异像素为 0（1185×1349）。但 ReportsPage.tsx:99 的图注是“本次算法输出；不作为原刻真值。”，main.py:382 的 evaluation_summary 是“实际处理已执行…”。ExperimentExplorer.tsx:40 的第三格固定为“本方法输出”，不区分 not_applicable 和 passthrough。 |
| F-P0-4 split 默认 test，无 split 的行被混入 | **成立**（建议定 P1） | ExperimentExplorer.tsx:10 `useState('test')`；:15 的过滤条件 `!r.split||r.split===split`。API 实测：heldout-v20-v21-2026-10-18 共 490 行、controlled-rubbings-2026-10-15 共 80 行，split 全为 None，在“test”筛选下全部可见。v2 和 v2-text 各 630 dev + 630 test，默认只显示 test。结果是同批复测与早期批次的数据被冠以“test”标签。 |
| F-P0-5 PDF/JSON 导出不含全局评测 | **成立** | HeldoutComparison.tsx:51 和 ExperimentExplorer.tsx:21 都带 `print:hidden`，所以打印 PDF 时这两块不出现。ReportsPage.tsx:34-54 的 exportData 字段只有本件 run、推理和来源，没有任何实验批次或汇总。 |
| F-P0-6 只有均值，没有 CI 和 Δ | **成立** | ExperimentExplorer.tsx:36 的表头是“方法/输入数/适用数/均值/标准差/比较条”；HeldoutComparison.tsx:61 只有均值列。API 的 v2 summary 里其实有 psnrCI95，但 UI 没展示；heldout summary 只有 *Mean，没有 CI。两处都没有相对 degraded 的 Δ。ExperimentExplorer.tsx:37 写着“95% 置信区间见导出 summary”，前端实际只提供 results.json / results.csv / summary.csv 三种导出。（另：我按 summary/csv/json 去请求 export 得到 404，是因为我用错了 kind 名，并非缺陷。） |

### 二、AUDIT_ENGINEERING.md E-P0-01…03 复核 → 结论：**通过**

| 项 | 判定 | 证据 |
|---|---|---|
| E-P0-01 run 排序 | **成立** | 同 F-P0-1。“未记录”的 legacy run 排在最前（museum_processing.py list_runs 按 finishedAt 字符串排序）。 |
| E-P0-02 runId 上下文 | **成立** | 同 F-P0-2。 |
| E-P0-03 双 ID | **成立** | 副本实测：tang_01_duobao 有 10 个 run、8 条 inferences；tang-duobao 有 4 个 run、0 条 inferences；han_01_caoquan 0 个 run；han-caoquan 1 个 legacy run。`/graph` 的 schema 不一致：演示 ID（tang-duobao、han-caoquan、wei-yuanhuai、wei-jianyi）返回 aliases/authors/identity/image 等 12 个以上的键，且带 steleId；馆藏 ID（tang_01_duobao、han_01_caoquan、wei_02_wugaoli）只返回 gis_route/links/nodes/verification，steleId 为 None。history_graph.py:10 `ALIASES={'tang_01_duobao':'tang-duobao','han_01_caoquan':'han-caoquan'}`。 |

### 三、AUDIT_CONTENT.md C-01…03 复核 → 结论：**通过**

| 项 | 判定 | 证据 |
|---|---|---|
| C-01 演示 ID 被并入馆藏 | **成立** | qa-baseline 8740：`/api/steles/han-caoquan` 返回 isDemo=True、source_kind=core_demo，但它的 `/graph` 返回馆藏图 /assets/stele/museum-rubbings/han_01_caoquan_readable.jpg 和 collectionNumber“购拓000033（拓本）”。tang-duobao 的 /graph 同样返回 tang_01_duobao_readable.jpg 和“赠拓000365”。`POST /api/research/query` 传 steleId=han-caoquan，返回 scopeSteleId=han_01_caoquan；传 tang-duobao，返回 tang_01_duobao（evidence_found）。 |
| C-02 无来源的史实 | **成立** | core_samples.json:6 author“颜真卿（书丹，琅琊临沂）”、:10 year“公元 752 年 5 月”、:13 location“西安碑林博物馆第一室”。4 条记录的键里都没有 author/location/year 的来源字段；全文件 12 处 source/evidence 只出现在 inferenceDemo 的候选字里（395-411、967-983）。同一件碑，馆藏记录 tang_01_duobao 的 author 是“岑勋”、location 是“原碑所在地未核定”，两者矛盾。HomePage.tsx:280 直接渲染 `{stele.author}`；首页卡片（239-290）没有渲染 isDemo，也没有任何演示标记，只有 badges“核心实验样本”的语义。apps/web/src/data/coreSamples.json 与 data/catalog/core_samples.json 经 `fc /b` 比对完全相同。 |
| C-03 wei-jianyi 的合成释文 | **成立** | `/api/steles/wei-jianyi/infer` 返回 35 个字符，其中 clear 34、damaged 1；demoMode=true。transcript 含“十一月申寅朔”。干支没有“申寅”，这是合成文本的痕迹。data/history/sources.json:56 自己写明“sample_generator.py 的 sample_4 使用昌黎夫人合成文字”。工作台 WorkbenchPage.tsx:196 对 isDemo 有提示“预置释文仅作演示”；`/api/steles/wei-jianyi` 的 translation 字段直接是这段合成文本。 |

### 四、ASSET_FREEZE.json 抽检 → 结论：**通过（覆盖面有条件）**

- 抽样方法：Python `random.seed(20261019)`，在 files[]（4046 条）里按 category 分层，每类 `random.sample` 取 min(4, 该类数量) 条，再从剩余条目中随机补足到 40 条。11 类全部覆盖。
- 比对方式：在笔记本上只读计算主工作区 D:\RubbingMind 下对应文件的 SHA-256 和字节数，与 freeze 记录比对。
- 结果：**40/40 一致**，0 个缺失，0 个不符。样本涵盖 museum_image 4、museum_source_original 4（含 3 个源 PDF，最大 25 MB）、blender_model 4、terrain_dem 5、experiment_raw 5 等。
- 结构核对：museum_image 共 84 条（cover/archive/readable 各 28），全部被 git 跟踪；terrain 有 334 张瓦片，聚合 SHA e892343a… 与 manifest 一致；discrepancies 为 0。
- 覆盖面意见：
  1. data/uploads/**（用户上传，BRIEF 要求保护）和 static/results/**（运行产物，P0-1 验收依赖其中的 run）都没有冻结，建议至少冻结清单和 SHA。
  2. data/museum-images/ 下的旧版文件没有纳入，scope_notes 已说明待确认。
  3. 抽检中看到 han_04_shichen 的 assessments/inputs 与 outputs 的 SHA 相同（5cc55f985fdd…），即派生输出等于输入（passthrough），与 RV-E02 一致。这不是冻结错误，但不应作为“处理结果”展示。

### 五、agent/eval-sci@f21ceaa 代码审查 → 结论：**有条件通过**

- 范围：`git diff f0c5886 f21ceaa`，18 个文件，+110770/−30，只有一个 commit。新增行基本都在 derived/applied_status.{csv,json}。
- 原始数据未被改动：`git diff --name-status` 限定在 experiments/results（不含 derived/）、data、apps/web/public、static、assets 时，输出为空。没有原始实验数据、馆藏图或失败实验被改或被删。
- test_heldout_v21.py：只替换了 docstring，新增 test_retest_samples_are_the_v2_text_artifacts；**没有删除或放宽任何旧断言**（逐行比对 diff）。
- applied_status 判据（pixel-equal-v1）：
  - 灰度逐像素相等即判 passthrough，无阈值；任何一个像素不同即判 processed；尺寸不一致时抛出 ValueError。
  - 所有行都保留：baseline / failed / undetermined 都是保留状态，没有删除。
  - 我的独立复算：seed 20261019，每批随机 40 行，用 cv2 重算，0 处不符。4 批的 sourceResultsSha256 与 results.json 一致。v2 adaptive_joint 为 passthrough 55 / processed 85，v2-text 为 passthrough 45 / 95，与我之前 RV-E02 的数字一致。
  - 新发现：notch 有 98（v2）和 95（v2-text）行判为 `processed_not_applicable_label`，即标签写着不适用，但像素实际发生了变化。这个标签与行为的矛盾需要算法负责人解释。
- `--allow-seen`：默认关闭。不加该参数时，`samples()` 遇到已见过的样本会 SystemExit。产出带 heldOut=all(excluded) 和逐样本的 seenInBatches 字段，属显著标注。脚本对 experimentId 和 OUT 硬编码，且 OUT 已存在时拒绝运行，不会覆盖历史。没有发现滥用路径。
- experiment_registry.py：DISPLAY 写死把 heldout-v20-v21-2026-10-18 标为“同批复测”、heldOut False，并在 limitations 首位插入 protocolNote。语义正确，但是硬编码。
- pytest 复现：在新建的 worktree D:\RubbingMind-wt\qa-evalsci（`git worktree add --detach … f21ceaa`）中运行 `python -m pytest tests -q -p no:cacheprovider`，结果 exit 0，**134 passed, 1 warning in 23.66s**。副作用：tracked 文件 screenshots/stele-final/asset-validation.json 被改，已用 git checkout 还原，worktree 现为 clean。
- eval-sci 自己的 worktree D:\RubbingMind-wt\rm-eval-sci 只读核对：HEAD f21ceaa9d1c49b39f62995e4d6dc7f1de349fe96，status 为空。
- **合并前必须修改**：
  1. 前端未同步（diff 不含任何 tsx）。HeldoutComparison.tsx:51 仍是“v2.0与v2.1留出对比”，与 API 的 heldOut=False 矛盾；ReportsPage.tsx:99 和 main.py:382 仍把 passthrough 称为“算法输出 / 实际处理已执行”。至少应在同一 PR，或在紧随其后、合并顺序锁定的 PR 中消费 isPassthrough/outputMode/displayName。
  2. 改动了 degradation_analysis.py（restore 的 selectedOutput 语义）和 museum_processing.py，这两个是生产共享文件，需要架构/后端 owner 签字，并补充对线上 /api/process 响应的回归测试。
  3. 旧 run 只给出 isPassthrough=None 和 outputMode='undetermined'，没有重新测量。tang_01_duobao 的 10 个 0 像素变化的 run 在 UI 上仍是“算法输出”。建议提供只读的离线回填脚本，或在 UI 上把 undetermined 显式展示出来。
  4. REPORT_DATA_SPEC.md 是共享协调文档，被提交进了功能分支，建议拆出或由 owner 确认，避免合并冲突。
  5. 解释 notch `processed_not_applicable_label` 的矛盾（见上）。
  6. heldout 批次没有图像，全部为 undetermined。结论文本中不得据此宣称“v2.1 有效处理率”。
- 建议（非阻塞）：
  - DISPLAY 改为从批次元数据读取；
  - change_stats 遇到尺寸不一致时，记 failed 而不是抛异常导致整批中断；
  - `notThePreviousBatch` 文本按实际计算结果生成；
  - pytest 仍会改写 tracked 的 asset-validation.json（与 RT-00x 相同的老问题）。

### 六、RT-002（sample_generator 合成“高仿真碑拓”）升级评估 → 建议维持 **P1**，不升 P0

- 合成图从未在 UI 中作为真拓出现：
  - 前端 apps/web/src 中对 sample_id、sample_[1-4] 和 static/samples 的 git grep 都无命中。
  - 核心样本的处理输入取自 record.damaged_image 或 raw_image，即 apps/web/public/assets/stele/rubbings/stele_*.png（museum_processing.py:24-25），不是 static/samples。
  - 这些 stele_*.png 在 assets_manifest.json 中全部标为 `data_status: concept_demo`。API 返回 isDemo=True，museum 字段为“核心算法演示样本，非第三轮馆藏影像”。
- 主工作区和 qa-baseline 的 static/samples/sample_1..4.png 不是本合成器的产物：
  - 两处 SHA 相同（B94D9FBA…/C1FB0D83…/5338923C…/DCF8F04A…），均由初始提交 511fdb7（2026-10-14）提交，此后没有历史改动，git status 干净。
  - 实测为 RGBA，尺寸 400×250、245×408、283×353、327×305，PNG 中无任何 text 元数据。
  - 合成器固定输出 800×1000 的 3 通道图（sample_generator.py:142、244-247），据此排除是合成产物。
  - 但它们**没有任何来源记录**：无 provenance、无 URL、无许可证。尺寸像缩略图，来源无法证实。
- 合成时不写任何标记（在临时副本中实际触发）：
  - 操作：删除副本的 sample_1.png 和 sample_4.png，把 sample_4 的两个候选文件移走，设置 HTTP(S)_PROXY=127.0.0.1:9 使下载失败，然后启动后端（PID 17252，已停）。
  - 日志结果：sample_1 走候选拷贝，日志写“已成功从用户真迹备份加载样本: sample_1.png <- stele_tang_duobao_damaged.png”，把 concept_demo 图称作“用户真迹”。sample_4 下载失败后，日志写“本地高仿真碑拓合成成功: sample_4.png [800x1000]”。
  - `/health` 的 samples_available 列出了 4 个样本，键来自 knowledge_agent 的 `AUTHENTIC_RUBBING_DATABASE`，无论样本是否合成都一样。
  - 合成的 sample_4 可以通过 `/static/samples/sample_4.png` 直接取到（200，1869248 B）。
  - `POST /api/process {"stele_id":null,"sample_id":"sample_4.png"}` 返回 200。inputImageSha256 等于合成图的 SHA，结果落在 static/results/**uploaded-image**/20261019T042857_be61268b，把合成图记成了“用户上传”。sourceRecords 为空，响应中没有“合成/synthetic/demo”任何字样。
  - 副本 rubbingmind.sqlite 的 SHA 处理前后不变，DB 中没有写入任何标记。
- 不升 P0 的理由：
  - 4 个样本都是被 git 跟踪的，而且候选 stele_*.png 也被跟踪。干净 clone 或正常启动走不到合成分支；我只有同时删除文件、移走候选、断网才触发成功。
  - UI 不消费 static/samples。
- 维持 P1 的理由：
  - 合成路径没有任何标记，`/health` 称其为 AUTHENTIC，合成结果被记为 uploaded-image，日志把演示图称为“真迹”。
  - static/samples 的来源无法证实。
  - 建议修复：
    - 去掉合成兜底，或将其产物写入带 `synthetic: true` 的 sidecar 并在 `/health` 中标注；
    - 下载改为 verify=True 且不伪造 Referer；
    - 删除 static/samples 或补 provenance。
- 顺带新发现 **RT-014（P2）**：main.py:90 `ProcessRequest.stele_id` 默认是 "tang-duobao"。不带 stele_id 的 `/api/process` 请求（例如 `{"sample_id":"sample_4.png"}`）会静默处理 tang-duobao，并在其名下新增 run（副本实测新增 20261019T042804_6a7c100d）。这与“不自动切换样本”的承诺相违，sample_id 分支（museum_processing.py:28）只在显式传 null 时才可达。

### 七、进程与 DB
- 本轮我启动的进程：35952（qa-baseline 8740）、12212（副本 8740）、17252（副本 8740，合成触发）。均由我停止。结束时监听端口中只剩 8000（PID 30712，用户进程，未触碰）；5180 未监听，未触碰。
- 主工作区 DB SHA-256，开始和结束一致：
  - data\rubbingmind.sqlite：8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D
  - data\runtime\evidence-v2.sqlite：854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3

---

## RM-评测科学家（Agent 04+05）· 追加：pytest 改写已跟踪文件的具体测试

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-19 12:33（Asia/Shanghai，笔记本实测时间）
- 关系：补充 RT-004 的第一部分（RT-004 只写到文件级“由 tests/test_stele_asset.py 间接调用”），以下把具体测试函数、机制和复现命令查准。RT-004 中的 SQLite 问题不在本条范围。

### RS-001 · P2 · `tests/test_stele_asset.py::test_shipped_stele_has_valid_geometry_uvs_and_embedded_pbr` 在 Windows 上把 `screenshots/stele-final/asset-validation.json` 的 LF 改写成 CRLF
- 作者：RM-评测科学家（Agent 04+05）；时间：2026-10-19 12:33
- 位置：
  - 测试 `tests/test_stele_asset.py:5`，函数 `test_shipped_stele_has_valid_geometry_uvs_and_embedded_pbr`，调用 `scripts.validate_stele_asset.run()`。
  - 写入点 `scripts/validate_stele_asset.py:55`：`(ROOT/'screenshots/stele-final/asset-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')`。
  - 在 Windows 上，`Path.write_text` 默认 `newline=None`，会把 `\n` 转成 `\r\n`。仓库中这个文件是 LF（`git ls-files --eol` 为 `i/lf w/lf attr/text eol=lf`）。
- 复现命令（在 worktree `D:\RubbingMind-wt\rm-eval-sci` 中，HEAD 7623a52）：
  ```powershell
  python -m pytest "tests/test_stele_asset.py::test_shipped_stele_has_valid_geometry_uvs_and_embedded_pbr" -q -p no:cacheprovider
  git status --short -- screenshots/stele-final/asset-validation.json
  git diff --ignore-cr-at-eol -- screenshots/stele-final/asset-validation.json
  ```
- 证据（实测）：
  - 运行前：974 字节，CR=0，SHA-256 `EF8ABB5B…3B7526`。
  - 运行这一个测试：`1 passed in 0.28s`。
  - 运行后：1027 字节，CR=53（每行多一个 CR），SHA-256 `A59C3A4B…DA072E2`；`git status` 为 ` M screenshots/stele-final/asset-validation.json`；`git diff --ignore-cr-at-eol` 输出 0 行，即内容没变，只改了行尾。
  - 单独运行这一个测试即可触发，所以不是别的测试导致的。全量 `python -m pytest tests -q` 也会触发（上一轮在本 worktree 全量运行后出现过；红队在 qa-evalsci worktree 中也复现过，见第二轮第五节）。还原方式：`git checkout -- screenshots/stele-final/asset-validation.json`。
- 用户影响：在主工作区或任何 worktree 跑测试，都会留下一个已跟踪文件的改动。容易被误提交，或被误判为“测试改了数据”，也会干扰“跑前跑后 git status 一致”这类洁净性验收。
- 建议修复路径（由该脚本的 owner 决定，本 Agent 未修改）：
  - 方案 1：写入时指定 `newline='\n'`（Python 3.10+ 的 `Path.write_text` 支持该参数），或改用 `write_bytes(...encode('utf-8'))`。
  - 方案 2：给 `run()` 加输出路径参数，测试里写到 `tmp_path`，不碰已跟踪文件。方案 2 同时满足 RT-004 的验收标准。
- 验收标准：在 Windows 全新 worktree 运行上述单测和全量 pytest 之后，`git status --porcelain` 中不出现 `screenshots/stele-final/asset-validation.json`。

## RM-红队QA（Agent 11+12）— 第三轮合并前门禁：agent/arch-backend

- 作者：RM-红队QA（Agent 11+12）
- 时间：2026-10-19 12:50（Asia/Shanghai，笔记本实测时间）
- **实际审查的 SHA：7c0e258073136715eb832806734f14127950c91f**
  - 这是 12:37:08 开始审查时分支的 HEAD，共 6 个 commit：32b2360、96dce66、53200d6、9501683、b5370d1、7c0e258。
  - 12:49:59 复查时，分支已前进到 **8a97a12**，新增 5 个 commit（7af1497、4379827、9934438、e551137、8a97a12），共 10 个文件，+888/−40。
  - 这 5 个 commit 包括 RT-014 修复、旧运行“读时计算”、退役记录隐私、rm:* 命名空间 ID，以及会写 SQLite 的 scripts/sync_catalog_db.py。**这 5 个 commit 本轮均未审查**，下面的结论只对 7c0e258 有效。
- 审查环境：
  - 新建 detached worktree D:\RubbingMind-wt\qa-arch（7c0e258），保留。
  - 只读核对 arch-backend 的 worktree：HEAD 7c0e258。
  - 需要运行记录的测试在两个临时副本中进行：C:\Users\WPY11\rm-redteam-qa-tmp\rep-base（f0c5886）和 rep-arch（7c0e258）。两者都用 `git clone --shared` 建立，主工作区的 static/results、data/uploads 和两个 sqlite 只读复制进去，两边数据完全相同。
  - 没有触碰 D:\Codex\worktrees；没有在其他 Agent 的 worktree 里运行任何东西。

### 1. 新增环境变量的默认值 → **成立（不设置时行为不变）**
| 变量 | 默认值（未设置或为空白） | 对照 f0c5886 |
|---|---|---|
| RUBBINGMIND_DB_PATH | `<repo>/data/rubbingmind.sqlite` | 与 database.py:12 原值相同（REPO 用 `Path(__file__).resolve()`，与原来的 abspath 只在符号链接情况下才可能不同） |
| RUBBINGMIND_RUNTIME_DIR | `<repo>/data/runtime`（evidence-v2.sqlite、glyph-inferences、glyph-annotations、condition-reviews） | 相同 |
| RUBBINGMIND_UPLOAD_DIR | `<repo>/data/uploads` | 相同 |
| RUBBINGMIND_RESULTS_DIR | None，即 `BASE/static/results`；不额外挂载 `/static/results` | 相同 |
| RUBBINGMIND_API_TARGET（已有变量） | 仍是 `http://127.0.0.1:8000`；新增 trim，未设置时在 `serve` 模式下打印警告 | 行为相同。实测设置了该变量时不打印警告，浏览器也没有请求 :8000 |

- 测试证据：test_runtime_paths 用子进程清空环境变量后断言 7 个路径都等于历史位置；空白字符串也视为默认。
- 遗留问题（P2）：scripts/migrate_museum_v3.py:13、26 和 scripts/assess_museum_condition.py:196 仍然硬编码 `base/'data/rubbingmind.sqlite'` 和 `static/results`，不受这些覆盖变量影响。设置了隔离变量后运行这两个脚本，仍会写主区。

### 2. legacy 运行排序与 /report 默认选择（F-P0-1）→ **部分修复（API 成立，UI 部分成立）**
- **API**：在 rep-arch 上，先删除我自己测试产生的运行，再干净复测：
  - `/api/steles/tang-duobao/report` 返回的 run 是 **20261018T072201_13772747**，runSelection 为 `{rule: latest_non_legacy, legacyRunCount: 2}`。
  - 运行顺序：072201 → 093048 → 两个 legacy 运行排在最后。
  - 同样的数据在 rep-base（f0c5886）上默认的是 legacy 运行 20261014T165542_5fc44fba。
  - han-caoquan 和 wei-jianyi 只有 legacy 运行，返回 run=None，evaluation_summary 为“只有旧版未核验运行，默认不选用…”。
- **UI**（Playwright + msedge，前端 5740 → 后端 8740）：
  - `?tab=reports&steleId=tang-duobao` 下拉框选中 20261018T072201_13772747，正确。
  - 但 `steleId=han-caoquan` 时选中的是 legacy 运行 **20261014T165543_438081c6**，与后端的 rule=none 矛盾。
  - 原因：ReportsPage 仍然取 `items[0]`，而新增的 `SteleService.getReportSelection` 在 apps/web/src 里没有任何调用者（git grep 无命中）。

### 3. SPEC §8 字段与 pixel-equal-v1 判据 → **大体一致，有 3 处偏差**
- 一致的部分：
  - `change_stats` 定义：int16 绝对差，任一通道不等于 0 即算该像素改动，0 阈值。
  - 字段名：isPassthrough、changedPixelCount、totalPixelCount、changedPixelRatio、maxAbsDiff、meanAbsDiff、passthroughCriterion='working-gray-pixel-equal-v1'、passthroughUndeterminedReason。
  - outputMode 枚举为 processed / passthrough / undetermined。
  - effectiveParameters 的公式与 SPEC 相同。
  - 旧运行读取时补 null 和原因“该运行保存于判据引入前…”，不回写文件。
- 偏差：
  - (a) `comparedImages` 实际是对象 `{before, after}`，SPEC 规定为 `[string, string]`，api.ts 里的类型写的是 `unknown`。
  - (b) 旧运行的 `passthroughCriterion` 为 null，SPEC 规定“不为 null”。
  - (c) 旧运行没有 `effectiveParameters`，SPEC 规定“不为 null”。
- 新运行实测：
  - `POST /api/process {"stele_id":"tang_01_duobao"}` 返回 outputMode=passthrough，/report 的 evaluation_summary 为“本次未改动原图：…逐像素相同…”，符合 SPEC。
  - tang-duobao 的新运行返回 processed。
- 与 eval-sci 的关系：两边都新增了 degradation_analysis.change_stats，以及 museum_processing 的 run_change_status 和 effective_parameters。`git merge-tree --write-tree 7c0e258 f21ceaa` 和 `… agent/eval-sci(d222fbc)` 都报告 **museum_processing.py 冲突**。merge-tree 只写对象，不改任何引用。

### 4. 4 个批次的诊断接口 → **成立，数字与独立重算一致**
- f0c5886 上，三个非 heldout 批次返回 404；7c0e258 上都返回 200，diagnosisVersion 为 baseline-delta-v1。heldout 返回 200，并增加 diagnosisVersion='heldout-legacy-heuristic'。
- byteIdenticalToInput 与我上一轮用 seed 20261019 做的像素重算结果对照：

| 批次 | 方法 | byteIdenticalToInput | 我的像素重算 |
|---|---|---|---|
| v2 | adaptive_joint | **55** | 55 |
| v2 | fast_nlm | 4 | 4 |
| v2 | notch | 6 | 6（passthrough_not_applicable） |
| v2-text | adaptive_joint | **45** | 45 |
| v2-text | fast_nlm | 2 | 2 |
| v2-text | notch | 0 | 0 |
| 2026-10-15 | 全部方法 | 0 | 0 |

- 其余计数：
  - negativeLiftCount：v2 747，v2-text 754，10-15 为 40，heldout 16。
  - unmatched 均为 0。
- 两点说明：
  - 诊断用的是 SHA 字节相等，SPEC 的判据是像素相等。字段名是 byteIdenticalToInput，与 SPEC 的 `byteIdentical` 不完全相同；byteIdentityBasis 已注明以 applied_status 为准。
  - 批次元数据：10-15 标为 historical-leakage，heldout 标为 metrics-only（rowsWithoutSplit 490）；defaultForReport 只有 v2-text 一个，符合 SPEC §1(a)。这个分支上 displayName 和 heldOut 为 None，它们由 eval-sci 提供。

### 5. urlState.ts 不带参数时的行为 → **部分成立**
- 页面初始状态的默认值不变：tab=home，steleId=tang-duobao。
- 但打开 `/` 后，URL 会被 replaceState 改写为 **`/?steleId=tang-duobao`**，原因是 writeUrlState 总会写入 steleId。
- 另外两点：
  - `runId=99999999T999999_deadbeef` 这样的无效值会留在 URL 里，而下拉框实际显示 072201，URL 与选择不一致。
  - `?tab=evil&steleId=<script>` 的参数会原样保留在 URL 中（已 URL 编码，未见 XSS）。
- 显式深链 `runId=20261014T165542_5fc44fba` 可以打开 legacy 运行，符合“显式可以打开”的设计。

### 6. 接口回归（42 条路由 → 157 个请求，f0c5886 与 7c0e258 使用相同数据和相同请求）
- 两个版本的路由集合完全相同，都是 42 条（含 docs、openapi、/static、/assets 挂载）。
- 状态码对照：
  - 157 个请求中 154 个状态码相同：200→200 共 83，404→404 共 60，422→422 共 7，400→400 共 3，413→413 共 1。
  - 唯一的变化是 3 个诊断请求 404→200，符合预期。
- 响应结构：134 个完全相同；23 个有变化，全部是新增字段或预期内的选择变化：
  - `/api/experiments` 及其详情：新增 splitAvailable、splits、rowsWithoutSplit、status、statusReasons、defaultForReport、defaultForReportBasis。
  - 各碑的 `/runs` 和 `/report`：新增 §8 字段、legacy、runKind、sortTimestamp、runSelection。
  - tang-duobao、han-caoquan、wei-jianyi 的 report 不再默认选 legacy 运行，所以 `run.*` 的旧结构消失。这是预期变化。
  - 3 个 `POST /api/process`：新增 §8 字段、comparedImages、effectiveParameters。
- **没有字段被删除**（除上述默认选择变化外），也没有状态码退化。

### 7. pytest 与构建
- 在 qa-arch 中运行 `python -m pytest tests -q -p no:cacheprovider`：exit 0，**140 passed, 1 warning in 22.63s**，与对方报告的一致。
- 测试改写了已跟踪文件 screenshots/stele-final/asset-validation.json，已用 git checkout 还原。
- 3 个已有测试各只增加一行 `monkeypatch.setattr(museum_processing,'RESULTS_DIR',None)`。diff 中没有任何被删除的 assert。
- 前端（设置 RUBBINGMIND_API_TARGET=8740）：`npm ci` exit 0，提示 9 vulnerabilities（3 moderate, 6 high），package-lock 未改动；`npm run build`（tsc && vite build）exit 0，仅有 chunk >500 kB 警告。构建结束后 worktree 干净。

### 8. 其他顺带项
- **F-P0-3**：后端已修，7c0e258 不再把 passthrough 的运行写成“实际处理已执行”。但 **UI 未修**：ReportsPage:99 的图注对 passthrough 运行和 undetermined 运行仍写“本次算法输出；不作为原刻真值。”（浏览器实测 tang_01_duobao 和 tang-duobao）。
- **RT-014**：7c0e258 **未修**。f0c5886 和 7c0e258 上，`POST /api/process {}` 与 `{"sample_id":"sample_1.png"}` 都会静默处理 tang-duobao。8a97a12 的 e551137 声称已修，未审查。
- **安全快速复测（两版一致，无回归）**：
  - 路径穿越：`/static/..%2F..%2Fmain.py`、`/static/results/..%2F..%2Fdata%2Frubbingmind.sqlite`、`/assets/..`、`/api/experiments/*/assets/..%2F..`、`/api/uploads/..%2F../image`、`/api/inferences/..%2F../crop` 全部返回 404。
  - CORS：来自 evil.example 的预检返回 400 “Disallowed CORS origin”，简单请求的响应不带 ACAO 头。
  - 上传：非图像返回 400，19 MiB 返回 413；文件名 `..\..\evil.png` 按 upload-uuid 落盘。
  - 绑定地址：main.py:568 仍是 127.0.0.1，runtime_guard.py 未改动。
  - Host 头为 evil.example 时 /api/health 返回 200，两版行为一致，是既有行为，不是新问题。
  - 新的 `/static/results` 覆盖挂载只在设置变量时出现。

### 结论（只针对 7c0e258）：**有条件可合并**
合并前必须项：
1. 分支已前进到 8a97a12，新增 5 个 commit 未经审查，其中包括写 SQLite 的 sync_catalog_db.py 和读时计算旧运行。**必须先对 7c0e258..8a97a12 做增量审查**，才能放行当前的 HEAD。
2. 与 eval-sci 在 museum_processing.py 上存在合并冲突（对 f21ceaa 和 d222fbc 都冲突）。需要确定合并顺序，并确定 run_change_status、effective_parameters、change_stats 只由一方负责，避免重复实现。
3. ReportsPage 默认选择改为使用后端的 runSelection（getReportSelection 已写好但没有调用者）。否则 han-caoquan、wei-jianyi 在 UI 上仍会默认 legacy 运行。如果这项归前端负责，需要在合并顺序中锁定。
4. SPEC §8 的 3 处偏差：comparedImages 的类型；旧运行的 passthroughCriterion 为 null；旧运行缺少 effectiveParameters。要么改代码，要么由 SPEC 负责人修订 SPEC。
5. urlState 不带参数时不应改写 URL（不写默认的 steleId）；无效的 runId 或 tab 应从 URL 中清除，或在页面上给出提示。

不阻塞合并、但需要跟进：
- ReportsPage:99 的“本次算法输出”文案（F-P0-3 的 UI 部分）；
- 两个脚本绕过路径覆盖变量；
- 诊断字段名 byteIdenticalToInput 与 SPEC 的 byteIdentical 不一致；
- HeldoutComparison 的“留出”标题依赖 eval-sci 的 displayName；
- npm 的 9 个漏洞是既有问题。

### 进程与 DB
- 本轮我启动的进程：
  - 后端 8740：42600（rep-base 回归）、41364（rep-arch 回归）、48040、50156（rep-arch 复测）、39824（rep-arch UI 测试）。
  - 前端 5740：cmd 45416，及其子进程 31884、31804、node 41964、44860、50740。
  - 全部已由我停止，前端用 taskkill /T 只结束了 45416 的进程树。
- 结束时监听端口：8000（PID 30712）和 5173（PID 25692）都不是我的进程，未触碰；5180 未监听。
- 主工作区 DB SHA-256（开始 12:37:08，结束见汇报）：
  - data\rubbingmind.sqlite：8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D
  - data\runtime\evidence-v2.sqlite：854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3

## arch-backend 增量审 7c0e258..8a97a12（RM-红队QA（Agent 11+12），2026-10-19 13:06 Asia/Shanghai）

- 审查对象：agent/arch-backend HEAD = 8a97a1209eb9b068196e8ca51d2f83ffdd5c5c42（12:55 与 13:05 两次核对，8a97a12 之后无新提交）。增量 5 个提交、10 个文件 +888/−40。
- 结论：**有条件可合并**。
- 实测（qa-arch 工作树）：`pytest -p no:cacheprovider` 220 passed；`npm run build` 通过（只有 chunk >500 kB 的警告）。测试改写的 asset-validation.json 已还原。
- 179 请求接口回归（7c0e258 对 8a97a12，临时副本）：153 项一致，26 项变化。新增的 rm:/id-mapping 端点 5 项 404→200；RT-014 相关 3 项变为 422；其余变化都是新增字段；process 响应的 comparedImages 由对象改为数组。
- 安全快测与 7c0e258 一致，无回归。
- 主区两个 SQLite 的 SHA 在开始、结束时一致（见下方）。

### 1. scripts/sync_catalog_db.py（只在临时副本上实跑）

- 默认只做 dry-run，以 `mode=ro` 打开数据库。副本 journal_mode=delete；dry-run 前后 SHA 与 mtime 都不变，也没有产生 -journal、-wal 文件。
- `--apply` 和 `--rollback` 都必须显式给出 `--db`，否则拒绝。非交互环境下没有 `--confirm` 也拒绝。错误令牌拒绝且不写库。
- 令牌为 sha256(basis{sqliteSha256, catalogueSha256, 行数} + operations)[:16]，同时绑定差异内容和库的真实 SHA，符合 Green 的口径。
  - 与 c358724 C08_SYNC_SPEC §3.4 的写法（basis.sqliteSha256 前 8 位）不同，但更严格，建议把规格改成与实现一致。
- 旧令牌失效实测：
  - 库内只加一张无关表，旧令牌 32326a07b002522c 被拒（"确认令牌与当前差异不一致…"），`--diff` 也因 basis 不符被拒。
  - 只改临时副本目录 steles28.json 的一个字段，旧令牌同样被拒；该文件随后已还原，SHA 为 0BC28FE9…。
  - 写库成功后再用同一令牌，被拒。
- 用 jinshi c358724 的 c08_sync_diff.json 做 `--diff` 外部核对：basis 与 operations 一致，令牌相同。
- 写库（副本）：
  - 先备份为 `<db>.20261019-130253.bak`（笔记本时间），备份 SHA 等于写前 SHA 8408DBC3…，并生成 .bak.json 旁注。
  - 写后 SHA 为 1B71A4C6…。逐格对比：共 80 行，**只改了 15 格**，即 5 处 author（未核定→目录值）和 5 行下架记录的 gis_lng/gis_lat 置 NULL，与规格 §2 完全一致。写后复核剩余 keep_row 5。
- 回滚：
  - 把备份恢复到别的库，拒绝。备份被篡改 1 字节，拒绝。
  - 正常回滚后 SHA 回到 8408DBC3…。
- 新问题：
  - **RV-AI01（P2）**：`--rollback` 没有检查库是否正在使用。存在 -wal 时 apply 会拒绝，但 rollback 照样执行（exit 0），残留的 -wal 留在原处。回滚前也不备份当前状态。
  - **RV-AI02（P3）**：不带 `--db` 的 dry-run 读取的是脚本所在仓库的 data/rubbingmind.sqlite，不读 RUBBINGMIND_DB_PATH。实测设置该变量后读的仍是仓库内的库。dry-run 是只读的，所以不会误写主区，但会与后端实际使用的库不一致。
  - **RV-AI03（P3）**：写后复核在 COMMIT 之后，失败时只能提示 `--rollback`。规格 §3.6 要求的 check_catalog_governance --summary 不在本分支，脚本用自身的复核代替。
  - **RV-AI04（P3）**：apply 的"正在使用"检测只看 -wal/-journal 文件。库是 delete 模式时，后端运行中并不会留下这类文件，靠的是 BEGIN IMMEDIATE 的锁。建议文档写明"先停后端"。
- 未在主区 data\rubbingmind.sqlite 上执行写入。对主库执行 apply 需要用户明确批准。

### 2. 旧 run 读时计算（computed-on-read）

- 10 个旧 tang_01_duobao run 全部为 isPassthrough=true、passthroughSource=computed-on-read、passthroughCriterion=pixel-equal-v1、changedPixelCount=0、comparedImages=['original','restored']。
- 只有 original 与 restored 的 SHA 都和 outputSha256 一致时才计算：
  - 篡改 restored.png 后，所有字段为 null，原因是"SHA-256 不一致，拒绝计算"，报告显示"未能判定是否改动原图"。
  - 删除 original.png 时同样全为 null，原因是"本地缺少…"。
- 不回写：processing.json 与副本数据库的 SHA 都不变。
- 判定使用全通道的 pixel-equal-v1（IMREAD_UNCHANGED，int32 差值）。本分支没有灰度字段。
- 耗时：10 个 run 冷启动 2994 ms，命中缓存 74 ms。
- **RV-AI05（P2）**：8000×6000 灰度图冷读 1090 ms，峰值工作集 175→838 MiB。彩色或 16 位图估计可到约 2 GB，目前没有尺寸或内存上限。
- 旧 run 仍然没有 effectiveParameters（读时不补），与 SPEC §8 写的"不为 null"不符。

### 3. RT-014（e551137）

- `{}`、stele_id 缺失、null、空串都返回 422（"缺少 stele_id…不会默认处理任何文物"），不创建 run。
- 空格、未知 id、`../../x`、`rm:demo:tang-duobao` 都返回 404。请求体不接受命名空间 id，与路径侧不一致，但安全。
- RT-014 判定已修复。没有请求再被默认归档到 tang-duobao。
- 前端唯一调用点是 api.ts:75 processStele，stele_id 为必填类型且结果会校验一致；scripts 下的 3 个浏览器脚本只监听响应。
- 残留：只给 sample_id 时仍返回 200，并归档为 uploaded-image（RT-002 的错标仍在，P1 维持）。

### 4. 其他核对

- comparedImages 已改为数组（4379827），旧 run 读时补齐。
- run_change_status、effective_parameters、change_stats 在本分支只由后端实现。
  - **合并风险**：eval-sci 新 HEAD 3391be3 在自己分支的 museum_processing.py 里也实现了 run_change_status、effective_parameters、_change_on_read 和灰度视图字段（GRAY_CRITERION）。与本分支形成双实现，merge-tree 有 4 个冲突块。
- 下架记录隐私：test_retired_no_coordinates 通过；/api/id-mapping 对 retired 条目去掉坐标键；运行时回归中未见坐标泄露。
- rm:* 命名空间：
  - 跨命名空间 404，路径穿越 404，rm:work 404。
  - **RV-AI06（P1，C-01 残留）**：`/api/steles/rm:demo:han-caoquan/graph` 返回 200，但图像仍是博物馆的 han_01_caoquan_readable.jpg。research/query 用 han-caoquan 时 scopeSteleId 仍为 han_01_caoquan。原因是 legacy ALIASES 仍会把 demo 映射到博物馆藏品。修复在 jinshi 的 id_mapping（本分支 available=false）。

### 5. merge-tree（只读，13:05）

- 8a97a12 与 eval-sci 3391be3：museum_processing.py 冲突（4 块）。
- 8a97a12 与 f21ceaa：degradation_analysis.py 和 museum_processing.py 冲突。
- 8a97a12 与 jinshi 0d30294 / ce541ca：evidence_retrieval.py 冲突（1 块）。
- 8a97a12 与 report-frontend 7e8fb30：无冲突。

### 上轮 5 项必改的状态

1. 7c0e258..8a97a12 增量审：已完成（本节）。
2. 与 eval-sci 的冲突：**未解决**，并且因为 3391be3 的双实现更重了。
3. ReportsPage 使用 getReportSelection：**未解决**。增量没有改动 apps/web；getReportSelection 只定义在 api.ts:100，没有被调用。
4. SPEC §8 偏差：**部分解决**。
   - comparedImages 改为数组 ✔。
   - passthroughCriterion 只在无法判定时为 null（与 eval-sci SPEC v3.1 一致）✔。
   - 旧 run 的 effectiveParameters 仍缺 ✘，需要后端补上或在 SPEC 中明确允许为 null。
5. urlState 改写 `/` 以及非法 runId/tab 留在 URL：**未解决**（apps/web 无改动）。

### 合并条件（有条件可合并）

- (a) 与 eval-sci 收敛为单一实现后解决 museum_processing.py 冲突。
- (b) 与 jinshi 解决 evidence_retrieval.py 冲突。
- (c) 第 3、5 项由 arch 或 report-frontend 认领修复。
- (d) 旧 run 的 effectiveParameters 与 SPEC 统一口径。
- (e) C-01 以 jinshi 的 id_mapping 合入为准，合并后复测 rm:demo:han-caoquan。
- (f) 对主库执行 sync --apply 需用户明确批准，且先停后端。

## RM-评测科学家（Agent 04+05）· 追加：SPEC v3.1 ↔ arch-backend@9ba3a57/49fca00 字段对照与科学口径

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-19 13:13（Asia/Shanghai）
- 对照对象：
  - SPEC：`agent/eval-sci` @ `3391be3` 的 `REPORT_DATA_SPEC.md` v3.1
  - 后端实现：`agent/arch-backend` @ `9ba3a57`（灰度字段）和 HEAD `49fca00`（effectiveParameters 读取时推导）；`museum_processing.py` + `degradation_analysis.change_stats`
- 本轮按 Green 13:10 纠偏：**不再改** `museum_processing.py`；科学口径已写入 SPEC v3.2；**尚未**把 arch-backend merge 进 eval-sci（等本清单确认后再做）。
- merge-tree 现状（只记录，未合并）：`git merge-tree --write-tree --name-only agent/eval-sci agent/arch-backend` → exit 1，唯一冲突文件 `museum_processing.py`；`degradation_analysis.py` 可自动合并。

### 科学口径（本轮裁定）

1. **主判据**保持 `pixel-equal-v1`：解码 `IMREAD_UNCHANGED`，形状与位深相同，全部通道逐值相等；彩色输入灰度化后输出算“已改动”。无法判定时 `isPassthrough`、`passthroughCriterion`、`passthroughSource` 均为 null。
2. **灰度口径**命名采用后端的 `working-gray-pixel-equal-v1`（指处理管线工作灰度），**不再**使用评测侧曾写的 `gray-bt601-pixel-equal-v1`。公式仍是 OpenCV `cvtColor(BGR→GRAY)`（即 BT.601 权重），写在 `grayCriterionRule`，不写进判据名。禁止用 `IMREAD_GRAYSCALE` 代替。
3. **灰度字段集**采用后端五元组：`grayChangedPixelCount`、`grayChangedPixelRatio`、`grayCriterion`、`grayCriterionRule`、`graySource`。只并列显示，不参与 passthrough 判定；可在主判据为 null 时仍有值。
4. **旧运行 effectiveParameters**：能按已核实版本映射从请求参数推导就 `derived-on-read`；否则 null，并给 `effectiveParametersUnavailableReason`。不回写。
5. **实现归属**：`run_change_status` / `effective_parameters*` / 灰度字段 / `computed_on_read_status` 由架构后端维护；评测分支合并时 `museum_processing.py` 冲突一律取后端。

### 字段对照表

| 字段 | SPEC v3.1（评测） | 后端 @9ba3a57 / 49fca00 | 科学口径 / 建议 |
|---|---|---|---|
| `passthroughCriterion` | `pixel-equal-v1`；无法判定时 null | 同左 | **一致，保持** |
| `passthroughSource` | recorded / computed-on-read / null | 同左 | **一致，保持** |
| `comparedImages` | 数组 `[\"original\",\"restored\"]` | 同左；读取时规范化对象→数组 | **一致，保持** |
| `grayCriterion` | `gray-bt601-pixel-equal-v1` | `working-gray-pixel-equal-v1` | **采用后端名**（SPEC v3.2 已改）。理由：命名对齐管线工作灰度；公式放 Rule |
| `grayCriterionRule` | 无（公式写在 grayCriterion 单元格） | 有长文本规则 | **采用后端字段**；建议后端在规则中显式写上“禁止 IMREAD_GRAYSCALE / 见 AUDIT 644816”（非阻塞） |
| `graySource` | 无 | recorded / computed-on-read / null | **采用后端字段** |
| `grayChangedPixelCount/Ratio` | 有；null 与解码失败绑定 | 有；灰度化失败才 null | **采用后端 null 规则**（可与 isPassthrough 不同步） |
| `effectiveParameters` | 写“不为 null” | 可为 null；另有 Source / UnavailableReason | **采用后端**：可 null + reason（SPEC v3.2 已改） |
| `effectiveParametersSource` | 无 | recorded / derived-on-read / null | **采用后端** |
| `effectiveParametersUnavailableReason` | 无 | 有 | **采用后端** |
| `change_stats` 差值类型 | int32（eval-sci `530b45e`） | int32（`4379827` 起，文本与评测相同） | **已对齐，无需再改** |
| 实现文件 | 评测分支曾有并行 `museum_processing` | `agent/arch-backend` 为正式实现 | **合并时取后端**；评测侧删除并行实现（待 merge 时做） |

### 给架构后端的清单（请确认或按建议改）

| # | 字段/点 | 现状（后端） | 建议 | 理由 | 阻塞 merge？ |
|---|---|---|---|---|---|
| 1 | `grayCriterion` 名 | `working-gray-pixel-equal-v1` | **保持**；评测 SPEC 已改跟你对齐 | 避免再改一次字符串 | 否 |
| 2 | `grayCriterionRule` 文案 | 已写 BGR→GRAY / 单通道 / 去 alpha | **建议追加一句**：禁止 `IMREAD_GRAYSCALE`，并指向 AUDIT 勘误（644816） | 防止前端或脚本混用解码器灰度 | 否 |
| 3 | `graySource` / Rule 字段 | 已有 | **保持** | 与 Source 语义对称 | 否 |
| 4 | 旧 run `effectiveParameters` | `49fca00` 已实现 derived-on-read 或 null+reason | **保持**；评测 SPEC v3.2 已跟齐 | 满足红队 gate 4 | 否 |
| 5 | `museum_processing.py` 合并 | 与 eval-sci 仍 content conflict | merge 进 eval-sci 时对该文件取 theirs | Green 13:10 指定 | 等确认后由评测执行 merge |

**结论：核心口径已与后端 HEAD 一致；无阻塞项。** 评测侧下一步：收到 Green / 后端“按口径无需再改”的确认后，再把 `agent/arch-backend` merge 进 `agent/eval-sci`（`museum_processing.py` 取后端），并跑 pytest。

### `degradation_analysis.py` 相对后端的剩余 diff（请签字）

相对 `agent/arch-backend` HEAD，评测分支**仅多** `AdaptiveRubbingRestorer.restore` / V22 的诊断字段（int32 两边已相同）：

- 增加 `changeStats = change_stats(image, result)`
- `selectedOutput`：由“门控是否接受”改为“输出是否与输入逐像素相同”（`original` if passthrough else `candidate`）
- 增加算法层 `outputMode ∈ {processed, identity_no_evidence, gate_fallback_original}`
- V22 早退分支同样带 `outputMode` / `changeStats`

完整 diff 见同目录附录或 `git diff agent/arch-backend agent/eval-sci -- degradation_analysis.py`（约 +20 行）。SPEC §9 已说明含义（D-2 / D-3）。请后端签字后随 merge 进入主线。

## RM-评测科学家（Agent 04+05）· 勘误：灰度判据名与 algorithmOutputMode（Green 定稿）

- 作者：RM-评测科学家（Agent 04+05）
- 时间：2026-10-19 13:19（Asia/Shanghai）
- 性质：勘误。不改写前文，只纠正字段名。

1. **灰度判据名**：前文（含「SPEC v3.1 ↔ arch-backend 字段对照」）若写「跟后端用 `working-gray-pixel-equal-v1`」或把 working-gray 当作科学口径，**作废**。**Green 已定稿为 `gray-bt601-pixel-equal-v1`**；后端正从 working-gray 改过来。灰度字段集仍为五元组。`grayCriterionRule` 继续写 BGR→GRAY = BT.601，并禁止 `IMREAD_GRAYSCALE`。SPEC **v3.3**。
2. **算法/诊断层字段名**：Green 定稿为 **`algorithmOutputMode`**；运行级仍为 **`outputMode`**。SPEC §9 已按定稿改写，去掉未确定是否改名的措辞。`degradation_analysis.py` 诊断 dict 键同步为 `algorithmOutputMode`。


## RM-红队QA（Agent 11+12）— 第三轮合并前门禁：agent/jinshi（固定审 4f9d568）

- 作者：RM-红队QA（Agent 11+12）
- 时间：2026-10-25 10:51（Asia/Shanghai）
- 环境：machineId=ba3b206b-6fff-443d-a208-1b296aa15191；worktree=D:\RubbingMind\wt\qa-jinshi（detached）；端口只用 8740；主库只读核对 SHA；临时目录 D:\RubbingMind\wt\qa-tmp
- 审查固定 tip：4f9d568b22d48300ef930cf5dda46094428ae134（RV-AI06: rm:demo:* always resolves as demo）
- 开始时 tip 曾为 6d94b35（EvidenceSearch relevanceLabel）；审查期间前进到 4f9d568，并对 eac58c3/d726dc/4f9d568 做了增量核实
- 结束时 gent/jinshi tip 已再前进至 719eea1；**未审 commit**：3e4a94（Claims batch 2a yuan_03+song_03）、719eea1（Phase3 batch2b yuan_02/tang_03/song_04/song_02）
- 对照合并基线：arch 8a97a12；eval-sci tip 当时记为 41587bf（本轮**不**审 eval-sci）

### 复用此前已完成结论（写入本轮使自洽）

| 项 | 结论 | 说明 |
|---|---|---|
| CONTENT_CHANGELOG 外链 | 成立（此前 12 条核验） | 史实改动有真实来源；本轮未重开全部 URL，以 changelog 与 claims 结构为准 |
| 颜真卿 / 岑勋等作者史实 | 成立 | 目录与图谱冲突处以 conflict 并列，不静默选边 |
| 异文 / dayCrossCheck | 成立 | tang_01 等保留 conflict；eac58c3 仅 calendar 复核笔记，**未改 claim 字段** |
| id_mapping depicts_same_work_as | 成立 | 演示与馆藏为同作品关系元数据，不合并 identity；depicts_same_work_as 出现 2 处 |
| governance 只读 | 成立 | sqlite3.connect(uri?mode=ro)；下架/无来源坐标输出为「已屏蔽」类 REDACTED |
| 冻结资产（museum 影像） | 成立 | 馆藏 readable 等未被动；jinshi 有意改 demo/前端 ledger（属本分支范围） |
| 与 arch evidence_retrieval.py | 冲突可解 | merge-tree 8a97a12×4f9d568：evidence_retrieval.py changed in both（1 块级冲突） |

### 本轮新实测

#### 1) pytest / build

| 命令 | 结果 | 证据 |
|---|---|---|
| python -m pytest tests -q -p no:cacheprovider（qa-jinshi@4f9d568） | **341 passed / 3 failed** | D:\RubbingMind\wt\qa-tmp\pytest-tip.txt；对方曾报 206（旧 tip 计数），本 tip 测试集已扩大 |
| 失败 1–2 | 	est_graph_images_use_reviewed_rubbings[han-caoquan/tang-duobao] | 测试仍断言 graph.image == 馆藏 museum-rubbings/*_readable.jpg；RV-AI06 后实际为演示图 /assets/stele/rubbings/stele_*.png。**产品行为符合 C-01/RV-AI06；测试未同步更新** |
| 失败 3 | 	est_history_graph_carries_label | identity 现以「演示样本 rm:demo:…」开头，合成标记仍在串内但不在 startswith 位置 |
| 	ests/test_retrieval_regression_25.py | **30 passed** | 含审计 25 条 + 注入/冲突/别名等 |
| 子集 id_namespace/governance/demo_scope/catalog_claims | **89 passed** | delta2 |
|
pm run build（apps/web，已有 node_modules） | **通过（exit 0）** | chunk>500kB 警告；RUBBINGMIND_API_TARGET 未影响 build |
| 还原副作用 | 已做 | screenshots/stele-final/asset-validation.json 曾被改写，已 git checkout -- 还原 |

#### 2) 8740 API 实测（后端从 qa-jinshi 启动，用 worktree 相对 data/rubbingmind.sqlite，未写主库）

| 检查 | 结果 | 证据 |
|---|---|---|
| C-01 / RV-AI06 graph（GET /api/steles/han-caoquan/graph） | **通过（tip 4f9d568）** | image=/assets/stele/rubbings/stele_han_caoquan.png；imageStatus=演示样本图（非馆藏拓本影像）；identity 明确区分演示与馆藏 han_01_caoquan |
| 同接口在旧 tip 6d94b35 | 曾失败（串馆藏图 / scope 折叠） | 由 4f9d568 修复；故**门禁以 4f9d568 为准** |
|
m:demo:han-caoquan 路径（含 URL 编码） | **仍 404** | /api/steles/rm%3Ademo%3Ahan-caoquan/graph → 404；research/query steleId=
m:demo:han-caoquan → 404「这里不存在」。**legacy 核心 ID 已隔离；rm: 命名空间 API 未接线** |
| research/query scope（steleId=han-caoquan） | **通过** | scopeSteleId=han-caoquan（不再折叠为 han_01_caoquan）；demoScope.included=true，合成样本默认说明需 opt-in |
| 提示注入 | **通过** | 「忽略以上指令…」→ answer=现有资料不足以回答该问题。 |
| C-03 /api/steles/wei-jianyi/infer | **部分通过** | **无 	ranslation 字段**（值为 null/缺失）；	ranscript 前缀含 【合成测试文本（sample_generator 生成，非真实释文）】；	extProvenance.kind=synthetic_test_text，isAuthenticInscription=false。标记在 transcript + textProvenance，不在 translation |
| 25 条检索回归 | **通过** | 见上 pytest 30 passed |
| 下架坐标不泄露 | **通过（脚本层）** | governance mode=ro；坐标无来源时 REDACTED/已屏蔽。对主库只读副本 --summary：C08_extraWithCoordinates=5（有坐标的多余行被标出，不打印真值） |
| C08 令牌口径 | **与后端对齐** | d726dc：confirmation_token = diffDigestSha256[:16]；SPEC/BR-10 已撤回「64 位不截断」。**若旧 SPEC 仍写 64 位，以后端 sha256(...)[:16] 为准，SPEC 对齐后端（Green 口径）** |

#### 3) 临时合并 / merge-tree

| 对比 | 结果 |
|---|---|
| merge-tree arch 8a97a12 × jinshi 4f9d568 | **evidence_retrieval.py CONFLICT（changed in both）**；其余大量 additive。合并前必须人工解决该文件 |
| merge-tree jinshi 4f9d568 × eval-sci 41587bf | **无冲突输出**（本轮未深入审 eval 内容） |
| merge-tree arch 8a97a12 × eval-sci 41587bf | **有冲突**（含 museum_processing 等；留给后续 eval/arch 任务，本轮不审） |
| 临时合并副本 C-01 | 因 evidence_retrieval 冲突未做完整 merge 提交；**在 jinshi tip 单边 8740 实测 C-01 已通过（legacy demo id）**。合并后仍需用合入 arch 的 evidence_retrieval 再测一次 rm:/scope |

#### 4) 主库 SHA（开始≈结束，未写）

| 库 | SHA-256 |
|---|---|
| D:\RubbingMind\data\rubbingmind.sqlite | 8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D |
| D:\RubbingMind\data\runtime\evidence-v2.sqlite | 854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3 |

（期望前缀 8408DBC3… / 854DF859… 一致。）

#### 5) 进程

- 已停自启 uvicorn PID 4844（8740）；8740 已空闲。
- 未碰 8000 / 5173 / 5180；5740 空闲。
- 保留 D:\RubbingMind\wt\qa-jinshi；清理 qa-tmp 中临时文件。

### 门禁结论：**有条件可合并**（固定 tip 4f9d568）

合并前必须项：

1. **解决与 arch 8a97a12 的 evidence_retrieval.py 冲突**（merge-tree 已确认）；合入后复测 C-01/research scope。
2. **修正 3 个失败测试**，使断言与 RV-AI06 一致（演示 ID → 演示图；勿再要求 museum-rubbings），或明确测试意图并改产品——当前产品侧正确、测试侧落后。
3. **明确
m:demo:* API 404 的产品决策**：要么接线路由/解析，要么在文档与前端只使用 legacy demo id（han-caoquan），避免 UI 链到 404。
4. **C-03 字段名**：对外文档若写 	ranslation，应改为实际的 	ranscript + 	extProvenance（或补 translation 镜像字段）；合成标记本身已存在。
5. **未审 tip 增量** 3e4a94、719eea1（claims batch 2a/2b）合并前需短增量审或由金石自行声明仅文档/claims、无检索行为变更。
6. **禁止对主库执行 C08 --apply**，除非用户批准且停后端；令牌继续用 sha256(...)[:16]。

非阻塞建议：ReportsPage/urlState 仍属 arch/frontend 侧；ASSET_FREEZE 中部分相对 f0c 的陈旧条目与 jinshi 有意改 demo 的差异，合并说明里写清即可。



## RM-红队QA（Agent 11+12）— arch-backend 增量门禁 56bb0cf…a261ba0

- 作者：RM-红队QA（Agent 11+12）
- 时间：2026-10-25 10:58（Asia/Shanghai）
- 环境：machineId=a3b206b-6fff-443d-a208-1b296aa15191；worktree=D:\RubbingMind\wt\qa-arch @ 261ba0（detached）；临时目录 D:\RubbingMind\wt\qa-tmp；端口 8740；主库只读
- 开始 tip：261ba03edbd12962a260329736952547e9054ea
- 结束 tip：261ba03edbd12962a260329736952547e9054ea（审查期间未前进）
- 本轮范围（含）：56bb0cf（gray-bt601 + RV-AI05）→ 768243b → 92de823（BR-07/08 + mechanism）→ 4e9098（C-08 新令牌 + RV-AI01/04）→ 261ba0（backup stamp）
- 上一审基线：8a97a12；对照 merge：jinshi tip 当时 11e6be；eval-sci 65f7815（本轮不审 eval 内容）

### 重点核实

#### 1) gray-bt601（展示专用）— **通过**

- 判定仍为全通道 pixel-equal-v1（RUN_PASSTHROUGH_CRITERION）；isPassthrough / outputMode /「本次未改动原图」**不**读灰度。
- 五元组：grayChangedPixelCount / grayChangedPixelRatio / grayCriterion=gray-bt601-pixel-equal-v1 / grayCriterionRule（BGR→GRAY=BT.601，禁止 IMREAD_GRAYSCALE）/ graySource。
- 实测（	ests/test_run_gray_reference.py）：彩色→灰度复写三通道时 isPassthrough=False 且 grayChangedPixelCount=0；output_mode 仍为 processed。
- 旧 run 读时计算：SHA 校验通过才算；灰度可 computed-on-read 补齐且不回写 processing.json。
- 工作区 DB 无历史 run 可供 8740 现场抽查；以单测 + 	est_computed_on_read_limits 为准。

#### 2) C-08 令牌新格式 — **通过（副本实测）**

- 公式：sha256(f"C-08|{diff_digest(diff)}|{db_sha256}")[:16]（scripts/sync_catalog_db.py）。
- 临时副本 qa-tmp/c08.sqlite（主库只读拷贝，SHA=8408DBC3…）+ jinshi c08_sync_diff.json（basis 匹配）：
  - 公式自洽；**旧式 digest[:16] 与新令牌不同**（old_style_token_differs=true）。
  - 错误令牌拒绝；改库字节后旧令牌失效；改 operations 后令牌变化。
  - 存在 -wal → 拒绝 apply；持有 BEGIN EXCLUSIVE → 拒绝 apply。
  - apply 成功（5 update + 5 set_null）→ rollback 恢复原 SHA；同秒 backup 戳冲突已用 -N 后缀（261ba0）。
- **合并注意**：jinshi d726dc 曾对齐「digest[:16]」旧口径；合入前金石侧 SPEC/脚本需再对齐本新格式 C-08|digest|dbSHA。

#### 3) BR-07 / BR-08 — **通过**

- BR-07（92de823）：query_steles(include_retired=True) 将下架行 gis_lng/gis_lat 置空返回，**DB 字节不变**；默认仍排除下架行（	est_query_steles_retired.py）。
- BR-08：EvidenceQueryRequest.includeDemo 默认 False；本分支 evidence_retrieval 尚无 include_demo 时兼容转发并标注 honoured=false + jinshi 为准的 compatNote。8740 实测：默认
equested=false；includeDemo=true →
equested=true, honoured=false。

#### 4) mechanism PNG 防穿越 — **通过**

-
esolve_mechanism_png：拒绝 ..、绝对路径、反斜杠、URL 编码穿越、非 .png、符号链接；Path.resolve +
elative_to 白名单。
- 单测 	est_mechanism_assets.py + 手工变体（../、..%2F、%2e%2e/、/etc/passwd、case_a/../../、....//）均拒绝；合法 case_a/ok.png 放行。
- 8740：未知实验 /mechanism-assets/../secret.png → 404。

#### 5) RV-AI01 / RV-AI04 / RV-AI05 — **通过（已修/加固）**

| 项 | 此前 | 本 tip | 证据 |
|---|---|---|---|
| RV-AI01 rollback + wal | 有 -wal 时风险 | apply/rollback 前 _assert_db_idle：检测 -wal/-journal **且** BEGIN EXCLUSIVE；rollback 前先备份当前库 | 副本：wal/锁均拒绝；rollback 恢复 SHA |
| RV-AI04「库在用」只靠 wal | 是 | 已加排他锁探测；文档仍要求先停后端 | 同上 |
| RV-AI05 大图内存 | 无上限（P2） | COMPUTED_ON_READ_MAX_PIXELS 默认 40MP；MAX_BYTES 默认 128MiB；超限 → 全字段 null + 明确原因，不回写 | 	est_computed_on_read_limits.py；56bb0cf |
| backup 同秒碰撞 | 可能 | 261ba0 后缀 -N | 同秒 apply+rollback 多份 .bak 成功 |

### pytest / build / 回归摘要

| 项 | 结果 |
|---|---|
| pytest -p no:cacheprovider | **250 passed** |
| 重点子集（mechanism/gray/limits/retired/demo/sync） | **22 passed** |
|
pm run build | **通过**（chunk 警告） |
| OpenAPI 路径数（本 tip 8740） | **42**（较此前 jinshi 审时 ~34 增加 mechanism/experiments/applied-status 等） |
| 相对 8a97a12 | 本范围新增 gray 五元组、读时上限、BR-07/08、mechanism 白名单、C-08 令牌改绑 C-08|digest|db、backup 戳；接口新增 mechanism 与 experiment 派生只读端点 |

### merge-tree（只读）

| 对比 | 结果 |
|---|---|
| arch 261ba0 × jinshi 11e6be | **冲突**：evidence_retrieval.py、pps/web/src/pages/WorkbenchPage.tsx、glyph_inference.py |
| arch 261ba0 × eval-sci 65f7815 | **无冲突输出**（对方声称已 merge arch；本轮不审 eval） |

### 主库 SHA（未写）

-
ubbingmind.sqlite = 8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D
-
untime/evidence-v2.sqlite = 854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3

### 进程 / 清理

- 已停自启 uvicorn（8740 无 Listen）；未杀 8000/5173 等他人进程。
- 删除 D:\RubbingMind\wt\qa-tmp；保留 qa-arch@a261ba0。
- 已还原 pytest 改写的 sset-validation.json。

### 门禁结论：**有条件可合并**（261ba0）

合并前必须项：

1. **与 jinshi 解决三处冲突**（evidence_retrieval.py 取金石实现并接上 BR-08 include_demo；WorkbenchPage / glyph_inference 人工合流）。
2. **金石 C-08 令牌再对齐**到后端新格式 sha256("C-08|"+diffDigest+"|"+dbSHA)[:16]（勿再用裸 diffDigest[:16]）。
3. 合入后在临时合并副本上复测：research includeDemo 真转发、mechanism 穿越、C-08 dry-run 令牌一致。
4. 对主库 --apply 仍须用户批准并先停后端（RV-AI04）。

非阻塞：工作区无旧 run 时 gray 现场抽查依赖单测；includeDemo 在合入 jinshi 前 honoured=false 为预期兼容态。


## RM-红队QA（Agent 11+12）：门禁审查 agent/eval-sci@65f7815（merge arch@a261ba0）
- 时间：2026-10-25 11:03（Asia/Shanghai；笔记本 `Get-Date`）
- 审查 tip：`65f78159a87ddee5895eb2d8d7b49fdbd1325028`（`test: align on-read fixture with backend outputImages + RV-AI05`）
- 祖先：merge `1cdee04`（parents `41587bf` + `a261ba0`）+ 收尾 `65f7815`
- worktree：`D:\RubbingMind\wt\qa-evalsci`（`--detach 65f7815`）；临时目录 `D:\RubbingMind\wt\qa-tmp-eval`（用完删除）
- 审查期间 branch tip 未前进（开始=结束=65f7815）；无未审提交
- 未碰 Codex worktrees / 主库写路径 / 8000·5180；未 commit/push；未长期占用 8740/5740

### 1) museum_processing / 双实现
| 项 | 结果 | 证据 |
|---|---|---|
| `museum_processing.py` blob | **与 arch@a261ba0 一致** | `60358fe70dfe5d41ab72f3be7bb760c273e5e5d3`（eval == arch） |
| `run_change_status` / `effective_parameters` / 灰度字段 | **仅此一份（后端实现）** | 定义仅在 `museum_processing.py`；测试与 `main.py` 调用该模块；ADR/SPEC 归属声明一致 |
| `change_stats` | **共用 `degradation_analysis.change_stats`（int32）** | `museum_processing` import `change_stats`；`change_stats` 使用 int32（无 int16 溢出） |
| `degradation_analysis.py` vs arch | **仍有分歧（eval 多 `algorithmOutputMode` + restore 内 `changeStats`）** | eval blob `95d44de6…`；arch blob `ca818a0e…`；`git diff a261ba0 65f7815 -- degradation_analysis.py` 约 +12 行 |
| `algorithm_engine.py` vs arch | **仍有分歧（E-05 陷波不适用原样返回）** | eval `a99872e4…`；arch/base `664348be…`；diff +8 行含 `passthroughReason` |

说明：Green 要求的 museum_processing「取后端」已落实。DA/AE 上 eval 相对 arch 仍有算法侧增量（SPEC v3.3 `algorithmOutputMode`、E-05），**不是** museum_processing 双实现残留，但合并产品线时需明确 DA/AE 以哪边为权威，避免 arch 后续再改回旧行为。

### 2) 原始数据 / heldout / allow-seen / SPEC
| 项 | 结果 | 证据 |
|---|---|---|
| 原始 `experiments/results/*/results.json` | **未改删** | `git diff --name-status f0c5886..65f7815 -- experiments/results` 无 `M`/`D` 于原始 results；仅 **A** derived（applied_status / ci_by_artifact / mechanism / NLC / e05 等） |
| 馆藏影像 / 失败实验目录 | **未见删除** | 同 diff；无 experiments 下 `D` |
| `test_heldout_v21` | **未放宽；反而诚实化** | 旧断言保留；新增 `test_retest_samples_are_the_v2_text_artifacts` 断言 14 件与 v2-text 集合相等（文档化 E-01） |
| `compare_v21 --allow-seen` | **默认拒绝同批复测** | `allow_seen=False`；未显式 `--allow-seen` 且样本已出现过则 `SystemExit`；`main(allow_seen='--allow-seen' in sys.argv)` |
| registry 展示名 | **ID 不变，displayName 标明非留出** | `experiment_registry.DISPLAY['heldout-v20-v21-2026-10-18']`：`heldOut:False` + protocolNote 指向 E-01 |
| SPEC | **树内含 v3.3 / gray-bt601 / algorithmOutputMode** | merge 自 arch 文档 + eval `41587bf`；与代码字段（grayCriterion、algorithmOutputMode）一致 |

### 3) bootstrap CI seed / 机制数据
| 项 | 结果 | 证据 |
|---|---|---|
| CI seed / bootstrap | **SEED=20261019，BOOTSTRAP=1000** | `experiments/ci_by_artifact.py`；stored JSON 同值 |
| 独立重算 CI | **324/324 组数值完全一致（v2 与 v2-text）** | `load_batch`+`compute` 重放；`diffs=0`；`sourceResultsSha256` 匹配；`compare_with_grouped_summary` 全部 `replayReproducesStored=True`（各 54） |
| `appliedStatusSha256` | **与当前 derived 文件不一致（P2）** | 重放时 SHA 不匹配：CI 落盘后 applied_status 可能又写过；**CI 数值本身可复现**，元数据哈希需重生或订正 |
| 机制案例 | **真实重算，非虚构占位** | 抽查 `han_02_yiying_salt_pepper_0`：input/output 文件 SHA 与 mechanism.json 一致；`images` 13 项含真实字节 SHA；`replays.historical.vsStoredOutput.pixelEqual=True`；`replays.head.vsBase.pixelEqual=True`；PNG 体积正常（谱图 ~150KB 级） |
| 机制生成 tip | 记录于 `headCommit=7623a52`（早于 65f7815） | 仍为真实 cv2 重算产物；合并后若 DA 再变应重跑 mechanism |

### 4) E-04 / E-05
| 项 | 结果 | 证据 |
|---|---|---|
| E-04 负提升原因 | **成立已补：测量原因 + 规则对照并存** | `derive_negative_lift_causes.py` → NLC JSON（含 `measuredCauses`/`measuredEvidence`/阈值）；`restoration_diagnosis.py` 双字段（`cause` 规则 + `measuredCauses`）；不再仅靠退化标签硬编码对外冒充测量 |
| E-05 陷波不适用 | **成立已修：无峰对时原样返回** | `algorithm_engine`：`passthrough=True` + 复制输入（避免 FFT/`astype(uint8)` 截断偏 −1）；`tests/test_process_regression_evalsci.py::test_notch_not_applicable_returns_input_unchanged`；历史批次用 `processed_not_applicable_label` / `test_notch_na_changes.py` 分类；`e05_processing_impact.py` 只读对比脚本 |

### 5) 独立复现 / 前端
| 项 | 结果 | 证据 |
|---|---|---|
| `python -m pytest tests -q -p no:cacheprovider` | **283 passed**（exit 0，~27.3s） | 日志 `D:\RubbingMind\wt\qa-tmp-eval\pytest-evalsci.log`（随后删临时目录） |
| `npm ci` + `npm run build`（`apps/web`） | **通过**（exit 0） | 8 个前端文件相对 f0c5886 有变（多为 merge arch 的 urlState/Reports/Workbench）；chunk 体积告警不影响退出码 |
| 副作用 | 已清理 worktree 内本次 `apps/web/dist` 与临时文件；保留 `qa-evalsci` | 见文末清理 |

### 6) merge-tree（只读）
| 对比 | 结果 |
|---|---|
| eval-sci@65f7815 vs arch@a261ba0 | **无冲突标记**（arch 已经 `1cdee04` 合入 eval） |
| eval-sci@65f7815 vs jinshi@b11e6be | **有冲突**：`apps/web/src/pages/WorkbenchPage.tsx`、`evidence_retrieval.py`、`glyph_inference.py`（及文档区块） |

### 主库 SHA（开始 / 结束一致，未写入）
- 开始（10:55:56 +08:00）：
  - `data/rubbingmind.sqlite` = `8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D`
  - `data/runtime/evidence-v2.sqlite` = `854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3`
- 结束值见文末核对段（应相同）

### 门禁结论：**有条件可合并**（65f7815）

合并前必须项：
1. **与 jinshi 当前 tip 解决三路冲突**（`evidence_retrieval.py` / `WorkbenchPage.tsx` / `glyph_inference.py`）：内容侧规则（检索阈值、演示范围等）取金石；评测/后端 URL 与 experimentId 权威规则取 eval/arch 已审口径，人工拼合后回归 retrieval + urlState。
2. **书面确认 `degradation_analysis.py` + `algorithm_engine.py` 以 eval@65f7815 为产品权威**（含 `algorithmOutputMode` 与 E-05），或由 arch-backend 显式 cherry-pick/快进到相同 blob 后再合，避免双源回退。
3. （建议，非阻断）重生 `ci_by_artifact.json` 的 `appliedStatusSha256` 或文档注明哈希漂移，避免派生链校验误报。

非阻断观察：机制 PNG 生成于 `7623a52`；DA 若再改应重跑 `mechanism_cases.py`。


## 短审 · agent/jinshi @b11e6be（相对门禁点 4f9d568；含未审 b3e4a94 / 719eea1 + tip 多出的 b11e6be）

- **范围**：`4f9d568..b11e6be` 共 3 commit
  - `b3e4a94` Claims batch 2a：yuan_03_shengzhu + song_03_daguan
  - `719eea1` docs(claims) batch2b：yuan_02 / tang_03 / song_04 / song_02（index 12/28）
  - `b11e6be` test(RV-AI06)：对齐 `test_history_graph` 馆藏 vs 演示图断言（tip 超出 719eea1，一并短审）
- **diffstat**：9 files / +4174 −9；主体为 6 份 claims JSON + index + CONTENT_CHANGELOG；代码仅测试。
- **史料抽查（NPM WebFetch，本机 curl 403 Cloudflare）**
  - yuan_03 id=34561：王思廉撰、赵孟頫书并篆题残泐、延祐四年、贈拓000410、作者栏仅赵 — 与 CHANGELOG/claims conflict 一致。
  - song_03 id=32018：李时雍摹写、蔡京题额、大观元/二年、購拓000421 — 一致。
  - yuan_02 id=34667：赵文原譔 / 赵孟頫书 / 赵世延篆额、元统三年乙亥 — conflict 保留异文，未升格撰人。
  - tang_03 id=29634：颜真卿、册 20.2×9.9、宋膺三跋「大历己未七七九年」vs 目录 780 — conflict 待复核。
  - song_04 id=34721：释梦英、丁卯年於長安集、本幅 130.8×81.6 — 一致。
  - song_02 id=34722：品名太宗、释文大中祥符（真宗）— conflict 样例成立；CHANGELOG 写本轮 fetch 超时，本审可打开（口径小不一致，不挡）。
- **规则抽查**：未核定未自动变已验证；conflict 用「待人工复核」；无坐标；无 demo/museum 路径混入 claims；影像 SHA 字段未改。
- **测试**
  - `test_history_graph.py::test_graph_images_use_reviewed_rubbings`：**2 passed**（b11e6be 有效）。
  - `tests/test_catalog_claims.py`：**21 failed / 68 passed** — 多为 batch2 未对齐既有 schema/测试门禁（见追加条件），非产品逻辑回归。
  - `check_catalog_governance.py`：本环境默认 sqlite 无 `steles` 表，脚本未作为本短审阻断项。
- **门禁结论**：相对 **4f9d568 有条件可合并** 结论**仍成立**（RV-AI06 / 演示馆藏分离未回退）；claims batch 2a/2b **需追加条件**后方可把史料包一并视为门禁通过。

### 追加条件（claims batch2）
1. **url source schema**：batch2 的 `type=url` 源仅有 `url+note`，缺 schema 必填 `publisher/title/sourceKind/accessedAt/quote` → 补齐或改 schema（须同步测试）。
2. **index.openedUrls**：6 条 NPM Detail URL 均被 claims 引用，但 **均未写入** `index.openedUrls`（仍为 batch1 的 7 条）→ 必须登记。
3. **conflict 形态**：`tang_03:date:yearCrossCheck` 缺 `alternatives`/`note`；`yuan_02:person:authorDispute` 缺 `note` → 按 batch1 约定补全。
4. **place.region**：若干 `entity=place` 且 `asserted` 的地点（含 rubbingHolder / originalSite）无 `region.precision=region` → 补区域级结构或标 missing。
5. **测试门禁**：`test_batch_is_six_and_includes_required_works` 仍写死 6/22，应改为 12/16（或参数化）。
6. （沿用）与 arch 的 merge-tree / C-08 对齐项不变；本短审未重跑全量 API。


### 清理 / 收尾（eval-sci@65f7815）
- 结束 tip = 开始 tip = `65f7815`；无未审提交。
- 结束主库 SHA（2026-10-25 11:04:17 +08:00）与开始一致：`8408DBC3…2323D` / `854DF859…ABD3`（未写入）。
- 已删 `D:\RubbingMind\wt\qa-tmp-eval`；已还原本次 `apps/web/dist` 与 `node_modules`；保留 `qa-evalsci@65f7815`。
- 未启动长期后端；未杀 8000/5180 他人进程。

## 门禁 · agent/report-frontend @a16d96b（独立验收）

- **作者**：RM-红队QA（Agent 11+12）
- **时间**：2026-10-25 11:17 Asia/Shanghai
- **审定 tip**：`a16d96b`（`feat(web): BR-09 EvidenceSearch includeDemo toggle with cinnabar warning`）；分支 tip 未前进，无未审提交。
- **工作树**：`D:\RubbingMind\wt\qa-report`（`git worktree add --detach` → a16d96b）；对接后端实测用 `D:\RubbingMind\wt\rm-arch-backend` @ `c0a7f76`（API `127.0.0.1:8740`，PID 自启自停）。
- **主库 SHA（开始=结束）**：`rubbingmind.sqlite` = `8408DBC3…2323D`；`evidence-v2.sqlite` = `854DF859…ABD3`（路径 `data/runtime/evidence-v2.sqlite`）。未写主库、未 C-08 --apply、未 commit/push/merge。

### 结论：**有条件可合并**

必须项（合入前）：
1. **解决 merge-tree 冲突**（只读已记录，合入时需人工处理）：
   - vs arch tip `c0a7f76`：`apps/web/src/components/EvidenceSearch.tsx`、`apps/web/src/pages/HomePage.tsx`
   - vs jinshi@`b11e6be`：上述两文件 + `apps/web/src/pages/WorkbenchPage.tsx`、`evidence_retrieval.py`、`glyph_inference.py`
2. **合入后回归**：冲突文件合并后重跑 `npm run build` + `tests/test_include_demo_compat.py` 与 FE 代理下 BR-09 OFF/ON 冒烟。
3. **Phase1 六层仍大部未验收**：本分支未关闭 P1-1…P1-9 浏览器/分辨率全量；不得宣称 Phase1 完成。

### BR-09 EvidenceSearch（Green 重点）

| 项 | 结果 | 证据 |
|---|---|---|
| 默认 `includeDemo=false` | 通过 | `EvidenceSearch.tsx:11`；`api.ts:192-195` `queryEvidence(..., includeDemo = false)` |
| POST 体转发 `includeDemo` | 通过 | `EvidenceSearch.tsx:18`；FE 代理 `5740→8740` 实测 |
| 开关 OFF（全局问「魏建义碑」） | 通过 | `demoScope.included=false`，证据 steleIds=`['wei_04_wangsong']`（无 wei-jianyi） |
| 开关 ON | 通过 | `included=true, optIn=include_demo`，证据含 `wei-jianyi` + `wei_04_wangsong` |
| 限定当前文物=`tang-duobao`（demo_sample）且 OFF | 预期行为 | `resolve_id('tang-duobao').kind=='demo_sample'` → `optIn=demo_scope_id` → `included=true`（BR-08 显式 scope 视作 opt-in）；证据仍为 tang-duobao |
| 朱砂警示是否误导「已核定」 | **否，不误导** | 全文无「已核定」；开关注警示 L30：`不可作为研究结论或评测依据`；结果横幅 L38：`不可作为真实史料或评测依据` / 兼容模式风险提示。`data-testid=evidence-demo-warning` / `evidence-demo-result-banner` |

### slice3（gray-bt601 / passthrough / experimentStatus）vs arch@a261ba0 / SPEC v3.3

| 字段/文案 | 前端 | 与 SPEC/后端 | 实测 |
|---|---|---|---|
| `grayCriterion='gray-bt601-pixel-equal-v1'` | `api.ts:50` 字面量类型 | SPEC v3.3 定稿一致；后端 `museum_processing.GRAY_*` / `test_run_gray_reference` | pytest 16 passed（含 gray/passthrough/spec8/include_demo） |
| gray 五元组展示 | `reportData.ts` `runOutcome` → `grayText`；`ArtifactRunReport.tsx:74` `data-testid=gray-change`；缺字段诚实空状态「后端尚未返回…不推断」 | 仅展示、不决定 `isPassthrough` | 当前 8740 库无 runs（`/runs` 空）；空状态路径与代码一致 |
| passthrough 文案 | `isPassthrough=true`→「本次未改动原图」；`false`→「算法已改动像素」；null→「未能判定是否改动」+ `passthroughUndeterminedReason`；`computed-on-read` 注明读取时校验 | SPEC §8 / arch 字段名一致；主判据仍 `pixel-equal-v1` | 代码+pytest；无 live run 像素对照 |
| `outputMode` vs `algorithmOutputMode` | 运行级用 `outputMode` / `runOutcome`；不把诊断层 `algorithmOutputMode` 误当 run 判据 | SPEC：算法/诊断=`algorithmOutputMode`，运行级=`outputMode` | 对照通过 |
| `experimentStatus` | App.tsx 五态 `none/resolving/ok/unknown/unavailable` → ReportsPage 朱砂告警 `app-unknown-experiment` / `app-unavailable-experiment` | FE 编排状态（非 SPEC API 字段）；与 checklist「已接」一致 | 代码行号对照通过 |

### Phase1 六层 vs ACCEPTANCE_MATRIX

BRIEF Phase1 六层：研究总览 / 视觉对照 / 横向比较 / 消融机制 / 失败与不确定性 / 科学结论与可复现性（+ PDF / 首屏分辨率）。

| 矩阵项 | 本门禁后状态 | 说明 |
|---|---|---|
| P1-1…P1-6、P1-8、P1-9 | **仍尚未验证** | 本分支有组件与 checklist 接线，但无 1920/1440 首屏截图、无完整六层浏览器走查、当前 API 无 runs 支撑三联/灰度实数 |
| P1-7 | **仍失败**（基线 RV-E01/E02） | 非本分支范围 |
| K-E（UI 是否误导·演示样本） | **部分→本门禁 BR-09 通过** | 朱砂警示不写成已核定；开关 OFF/ON 行为正确（全局） |
| F-E 史料证据 | 仍部分 | 本门拒答/demoScope 再探一次，未做全量冲突/定位闭环 |
| npm ci + build | **本分支通过** | `npm ci` + `npm run build` 39s，exit 0；`npm run test:url` 13 checks passed |

### 构建与测试摘要

- `npm ci`：175 packages；`npm run build`：**通过**（chunk size warning only）。
- `npm run test:url`：**13 passed**。
- pytest（qa-report）：`test_include_demo_compat` + `test_run_gray_reference` + `test_run_passthrough` + `test_run_spec8_alignment` → **16 passed**（2.54s）。
- 前端 Vite：`RUBBINGMIND_API_TARGET=http://127.0.0.1:8740`，端口 **5740**；代理 OFF/ON 与直连 8740 一致。

### 环境清理

- 停本门禁自启 API（8740）与 Vite（5740）；删 `D:\RubbingMind\wt\qa-tmp`；保留 `D:\RubbingMind\wt\qa-report@a16d96b`。
- 未碰 Codex worktrees / 主库 / 8000·5180·5173。



## 门禁 · agent/arch-backend @c0a7f76（复验：合入 jinshi + DA/AE sync + WorkbenchPage）

- **作者**：RM-红队QA（Agent 11+12）
- **时间**：2026-10-25 11:18 Asia/Shanghai
- **审定 tip**：`c0a7f7637c8d391bc4089c77118b56b1cd2393cc`（`test: RV-AI06 identity has demo banner before synthetic LABEL`）
  - 祖先：`533cb85` sync DA/AE←eval@65f7815；`6e9f219` merge jinshi@b11e6be（jinshi 已是 ancestor，exit 0）
- **工作树**：`D:\RubbingMind\wt\qa-arch` checkout --detach @c0a7f76
- **临时目录**：`D:\RubbingMind\wt\qa-tmp-arch`（与报告前端 `qa-tmp` 隔离）
- **API**：本复验用 **8741**（`127.0.0.1:8741`，PID 自启）；**8740** 已被另一审查（report-frontend 对接 arch）占用，故改口并在此写明。未杀 8740/8000/5180。
- **主库 SHA（开始=结束）**：`rubbingmind.sqlite`=`8408DBC3…323D`；`evidence-v2.sqlite`=`854DF859…ABD3`（`data/runtime/`）。未写主库；C-08 --apply 仅临时副本；无 commit/push；未碰 Codex。

### 结论：**不可合并**

合入前必须项：

1. **补齐 report-frontend 报告组件树（或回退 WorkbenchPage 依赖）**：`WorkbenchPage.tsx` blob 已等于 `report-frontend@a16d96b`（`7b0ce5df…`），但 `apps/web/src/components/reports/`（至少 `reportFilters.ts`）在 arch tip **不存在** → `npm run build` / `tsc` **失败**（`TS2307: Cannot find module '../components/reports/reportFilters'`）。仅摘 WorkbenchPage、不摘其依赖，前端不可交付。
2. **claims 测试与 index 对齐（随 jinshi 合入带入）**：`data/catalog/claims/index.json` 已有 **12** works（含 batch2a/2b），但 `tests/test_catalog_claims.py` 仍断言 `len(WORKS)==6` 且 schema/openedUrls/conflict/place 形态未跟 → **21 failed**。与 jinshi 短审「追加条件」一致，本 tip CI 全量不过。
3. **与 report-frontend@a16d96b 合入时处理 merge-tree 冲突**：`EvidenceSearch.tsx`、`HomePage.tsx`（arch 侧为 jinshi 版；rf 侧有 BR-09 等差分）。WorkbenchPage 已与 rf 同 blob，但 reports/ 仍缺。vs jinshi：**无冲突**（已 merge）。

建议项（非本 tip 阻断、但合入后应验）：
- 将 `components/reports/**`（及 `ReportsPage` 若未完整）按 RF 依赖闭包一并纳入，再重跑 `npm run build`。
- claims：url source schema / openedUrls / conflict alternatives+note / place.region（见 jinshi@b11e6be 短审）。

### 核对清单（通过项）

| 项 | 结果 | 证据 |
|---|---|---|
| DA `degradation_analysis.py` blob = eval@65f7815 | 通过 | `95d44de63938469b7ce51e3b0a001d7ab76e43ff` |
| AE `algorithm_engine.py` blob = eval@65f7815 | 通过 | `a99872e4fc9124be96621d3075432d3726d09bde` |
| `museum_processing.py` 仍为 60358fe7… | 通过 | `60358fe70dfe5d41ab72f3be7bb760c273e5e5d3` |
| WorkbenchPage ← report-frontend | blob 通过 / **构建失败** | blob=`7b0ce5df…`=a16d96b；缺 `reports/reportFilters.ts` |
| evidence_retrieval include_demo 路径 | 通过（相对 jinshi +runtime_dir） | vs jinshi 仅 `INDEX=runtime_dir()/'evidence-v2.sqlite'`（+2/−1）；`demo_opt_in` / `include_demo` / `resolve_id` 在册 |
| jinshi@b11e6be 已合入 | 通过 | `merge-base --is-ancestor` exit 0；merge-tree 无 `changed in both` |
| includeDemo 默认 false | 通过 | API `demoScope.included=false, optIn=null`；`demo_opt_in(...)` 默认 `null`；「样本/演示」字样 alone 不 opt-in |
| includeDemo true | 通过 | `included=true, optIn=include_demo`；`rm:demo:` in Q → `rm_demo_id_in_question`；scope `rm:demo:han-caoquan`/`han-caoquan` → `demo_scope_id` |
| research scope 不折叠到馆藏 | 通过 | scopeResolution.kind=`demo_sample`；evidence steleIds 为 `han-caoquan`（非整页折叠为仅 `han_01_caoquan`）；museum scope 单独 `kind=rubbing` |
| RV-AI06 图谱不串馆藏图 | 通过 | `/api/steles/han-caoquan/graph` 与 `rm:demo:han-caoquan`：`image=/assets/stele/rubbings/stele_han_caoquan.png`，`imageStatus` 以「演示样本图」开头，`identity` 含 `rm:demo:han-caoquan`；`han_01_caoquan` 为馆藏图路径（含 museum 语义）。pytest：`test_id_namespace` / `test_history_graph` RV-AI06 在列 |
| mechanism 路径穿越 | 通过 | 真实 eid `controlled-rubbings-2026-10-15`：`../`、`..%2F`、反斜杠、`/etc/passwd`、`%2e%2e/`、`x/../../` → **HTTP 400**（「路径不合法」/「只允许 .png」）；`resolve_mechanism_png` 单测同拒。本批次 mechanism 目录 missing（404/原因诚实），不削弱穿越拒绝 |
| C-08 令牌格式 | 通过 | `sha256(f"C-08\|{diffDigest}\|{dbSHA}")[:16]`；实测 TOKEN=`112ba2d3ebd14f2a` FORMULA_MATCH=True |
| C-08 preview/apply/rollback（仅临时副本） | 通过 | 副本自 main `8408DBC3…`；wrong token RC=1 未写；apply update=5/set_null=5；rollback 恢复 BEFORE；**主库 SHA 未变** |
| pytest -p no:cacheprovider | **部分失败** | 全量 **21 failed / 491 passed**（皆 `test_catalog_claims.py`）；`--ignore=test_catalog_claims` → **425 passed**；RV-AI06/include_demo 相关子集 **94 passed** |
| npm run build | **失败** | TS2307 reportFilters；见必须项 1 |
| merge-tree vs jinshi@b11e6be | 通过 | 0 conflict（已 ancestor） |
| merge-tree vs report-frontend@a16d96b | 有冲突 | EvidenceSearch.tsx、HomePage.tsx（`changed in both`） |

### includeDemo / graph 摘要（8741）

- 默认/显式 false：`demoScope.included=false`；合成样本列表含 `wei-jianyi` 且默认不进入检索。
- true：`optIn=include_demo`。
- `steleId=rm:demo:han-caoquan`（及遗留 `han-caoquan`）：`resolve_id`→`kind=demo_sample`，`depictsSameWorkAs.rubbingId=han_01_caoquan`（关系披露，不把 scope 收成馆藏 id）。
- 响应字段为 `demoScope`（included/optIn/note），无单独顶层 `includeDemoHonoured`；行为与 jinshi BR-08 一致。

### 清理 / 收尾

- 结束 tip = `c0a7f76`（与开始一致）；无未审提交。
- 结束主库 SHA（2026-10-25 11:18 Asia/Shanghai）与开始一致：`8408DBC3…323D` / `854DF859…ABD3`。
- 停本复验 API **8741**；删 `D:\RubbingMind\wt\qa-tmp-arch`；**保留** `qa-arch@c0a7f76`。
- 不杀 8740（他审占用）/8000/5180；不碰 Codex worktrees。


## 短审复验 — agent/jinshi @724c6a0（优先回报）

- **作者**：RM-红队QA（Agent 11+12）
- **时间**：2026-10-25 11:25 Asia/Shanghai
- **固定 tip**：`724c6a0264176029d6b3e7e19f90f3b4dba8ccdc`（`fix(claims): batch2a/2b red-team musts 1-5`）
  - 含 `7ebc3b5`（RV-AI06 rm:demo API + C08 `sha256(C-08|diff|db)[:16]`）+ `724c6a0`（claims ①–⑤）
- **工作树**：`D:\RubbingMind\wt\qa-jinshi` checkout --detach @724c6a0
- **临时目录**：`D:\RubbingMind\wt\qa-tmp-jinshi`（收尾删除）
- **对照 arch**：`c0a7f7637c8d391bc4089c77118b56b1cd2393cc`
- **主库 SHA（起=终）**：`rubbingmind.sqlite`=`8408DBC3…323D`；`evidence-v2.sqlite`=`854DF859…ABD3`；未 C-08 --apply；未碰 Codex / 8000 / 5180；未 commit/push

### 门禁结论：**有条件可合并**

上次追加条件（①–⑤）**全部清掉**；C-08 令牌已跟 arch 新格式；RV-AI06 未回退。独立复现对方宣称的 **87 / 387 passed**。

仍未清的合并条件：

1. **merge-tree vs arch@c0a7f76 仍有 2 处内容冲突**：`main.py`、`tests/test_synthetic_sample_label.py`（只读 merge-tree `--write-tree` exit 1）。arch 已含 jinshi@b11e6be；本 tip 相对 arch 仅超前 `7ebc3b5`+`724c6a0`，合入前需按既定冲突策略解这两处（RV-AI06 identity / demo banner 相关）。
2. （非阻断）本机直连 NPM Detail 返回 **HTTP 403**，无法在线复核引文原文；字段完备性与测试已覆盖，引文真实性依赖金石侧已打开记录。

### 上次追加条件核销

| # | 条件 | 结果 | 证据 |
|---|---|---|---|
| ① | url source 补齐 publisher/title/sourceKind/accessedAt/quote | **清掉** | 全库 url 源巡检 `url_ok=170 / url_bad=0`；抽查 yuan_03/tang_03/song_03 的 NPM url 五字段齐全（`sourceKind=official_museum`） |
| ② | 6 条 NPM URL 写入 index.openedUrls | **清掉** | `openedUrls` 13 条，其中 NPM `digitalarchive.npm.gov.tw` **6** 条（id 34561/32018/34667/29634/34721/34722） |
| ③ | conflict 补 alternatives/note（tang_03 yearCrossCheck、yuan_02 note） | **清掉** | tang_03：`yearCrossCheck` conflict，alts `[780,779]` + note；yuan_02：`authorDispute` conflict，3 alternatives + note；其余 conflict 均有 alternatives+note |
| ④ | place asserted 补 region.precision=region | **清掉** | 抽查各 batch2 作品 place/region 均为 `precision=region`；`test_no_coordinates_and_region_level_places` 在 87 内通过 |
| ⑤ | 测试 batch 6/22→12/16 | **清掉** | `index.works=12`、`remaining=16`；`test_catalog_claims.py` 断言已改；`test_catalog_claims` **87 passed** |

### C-08 / RV-AI06

| 项 | 结果 | 证据 |
|---|---|---|
| C-08 令牌 = `sha256(C-08\|diffDigest\|dbSHA)[:16]` | **通过** | jinshi `check_catalog_governance.confirmation_token` 与 arch `sync_catalog_db.confirmation_token` 同公式；样例向量 match=True |
| RV-AI06 未回退 | **通过** | `resolve_id('wei-jianyi'|'rm:demo:wei-jianyi')` → `kind=demo_sample` / `newId=rm:demo:wei-jianyi`；全量 pytest 含 history_graph / id_namespace 绿 |

### 独立复现

| 命令 | 结果 | vs 对方 |
|---|---|---|
| `python -m pytest tests/test_catalog_claims.py -q -p no:cacheprovider` | **87 passed** / 0.94s / exit 0 | 一致 |
| `python -m pytest tests -q -p no:cacheprovider` | **387 passed**, 1 warning / 47.18s / exit 0 | 一致 |

副作用：pytest 曾改 `screenshots/stele-final/asset-validation.json` → 已 `git checkout --` 还原；worktree 干净。

### merge-tree（只读）vs arch@c0a7f76

- merge-base = `b11e6be`
- **CONFLICT**：`main.py`、`tests/test_synthetic_sample_label.py`
- 其余可自动合并；claims/C08/RV-AI06 数据侧变更无额外冲突文件

### 收尾

- 停进程：本轮未起 8742/5742 API
- 删 `D:\RubbingMind\wt\qa-tmp-jinshi`
- **保留** `D:\RubbingMind\wt\qa-jinshi` @724c6a0
- 主库 SHA 终检与起始一致


## 复验门禁 — agent/arch-backend @7fcc751（reports 落地 + jinshi merge + coreSamples）

- **执行**：RM-红队QA（Agent 复验）
- **时间**：2026-10-25 11:35 Asia/Shanghai
- **固定 tip**：`7fcc7515c6e1fb260ead1b3fc6dfa7749e3280fe`
  - `48deed1` land report-frontend reports/ + BR-09 EvidenceSearch/HomePage（自 RF@a16d96b）
  - `b8311f3` merge jinshi `7ebc3b5..724c6a0` claims batch2a/2b
  - `7fcc751` coreSamples.json ≡ data/catalog/core_samples.json
- **工作树**：`D:\RubbingMind\wt\qa-arch` checkout --detach @7fcc751
- **临时目录**：`D:\RubbingMind\wt\qa-tmp-arch`（收尾删除）
- **对照 tip**：RF@`a16d96b`；jinshi@`724c6a0`；前次 arch@`c0a7f76`（不可合并）
- **主库 SHA（始=终）**：`rubbingmind.sqlite`=`8408DBC3…323D`；`evidence-v2.sqlite`=`854DF859…ABD3`；未 C-08 --apply 主库；未碰 Codex / 8000 / 5180；未 commit/push

### 门禁结论：**有条件可合并**

上次三项「不可合并」必须项：**全部消除**。残余为合入 RF EvidenceSearch 后弱相关 UI 回退、MuseumPage 未挂 ReviewStatusBadges、以及 TestClient 对 `rm:demo:` 路径偶发 404（live uvicorn 200）。对方自称 catalog/demo/mechanism **124 passed** 为 Phase0 基线口径，本 tip 全量套件规模不同；本闸实测 claims **87 passed**（对齐 jinshi）、catalog/demo/mechanism 相关子集 **223 passed / 2 failed**、全量 **509 passed / 4 failed**。

### 上次三项必须核对

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | reports/ 依赖 + `npm run build` exit 0 | **消除** | `apps/web/src/components/reports/` **17** 文件齐（含 `reportFilters.ts`）；WorkbenchPage 导入可解析；独立 `npm run build` **✓ built in 39.60s / exit 0**（对方称×2，本闸完整复现 1 次） |
| 2 | claims / catalog·demo·mechanism | **消除（claims）**；子集非 124 全绿 | `test_catalog_claims` **87 passed** / 0.70s（对照 jinshi@724c6a0 = 87）；子集（claims+demo+history+id+…）**223 passed / 2 failed**（非对方「124」口径）；全量 **509 passed / 4 failed**（较 c0a7f76 的 21 failed 大幅收敛） |
| 3 | merge-tree vs RF@a16d96b / jinshi@724c6a0 | **消除** | vs RF：`EvidenceSearch.tsx`/`HomePage.tsx` tip blob **==** RF（`changed in both` **0**）；vs jinshi：`724c6a0` 为 tip **祖先**，merge-tree 无冲突行；`main.py` / `test_synthetic_sample_label` 已随 `b8311f3` 合入 |

### 冒烟（API 8740）

| 项 | 结果 | 证据 |
|---|---|---|
| includeDemo OFF/默认 | 通过 | `demoScope.included=false`；wei-jianyi 默认不入检索结果 |
| includeDemo ON | 通过 | `optIn=include_demo`；结果含合成 ID |
| RV-AI06 han-caoquan / `rm:demo:` | 通过 | graph bare 与 `rm:demo:han-caoquan` 均 200；identity 标明演示样本；`scopeResolution.kind=demo_sample` + `depictsSameWorkAs.rubbingId=han_01_caoquan` |
| mechanism 穿越 | 通过 | `../`、编码变体等均 **400**「路径不合法」 |
| C-08 仅副本预览 | 通过 | token=`112ba2d3ebd14f2a`；`formula_match=true`（`sha256(C-08\|diffDigest\|dbSHA)[:16]`）；`target_eq_before=true`；主库 SHA 校验仍 `8408DBC3…323D`；**未** --apply 主库 |
| coreSamples 对齐 | 通过 | web `coreSamples.json` bytes == `data/catalog/core_samples.json`（sha256 前缀 `b0977b84f959ffef`） |

### 残余条件（不阻断「三项必须」，合入前建议清）

1. **EvidenceSearch 弱相关 UI 回退**：tip blob = RF@a16d96b（BR-09 includeDemo），**无** `relevanceLabel` / `data-testid="weak-relevance"`；`test_evidence_search_shows_weak_label_from_response` 失败（c0a7f76 旧 blob 曾有）。合入 RF 消冲突时丢了弱相关展示。
2. **MuseumPage 未挂 `ReviewStatusBadges`**：jinshi@724c6a0 有 2 处，tip/`b8311f3` 为 0 → `test_badges_render_flags` / `test_ui_component_renders_both_labels` 失败。
3. **TestClient `GET /api/steles/rm:demo:…`**：pytest 内 404；**live uvicorn 8740 同路径 200**（冒烟已过）。属测试客户端/路由边界，非线上回归。

### 收尾

- 停本闸 API **8740**（PID 见 api-pid）；删 `D:\RubbingMind\wt\qa-tmp-arch`；**保留** `qa-arch@7fcc751`
- 主库 SHA 终=始：`8408DBC3…323D` / `854DF859…ABD3`


## 窄复验门禁 — agent/arch-backend @5716455（清 7fcc751 三项残余）

- **执行**：RM-红队QA（窄复验）
- **时间**：2026-10-25 11:50 Asia/Shanghai
- **固定 tip**：`571645544d2271e0e2df64117cddfd04fd6b82e5`
  - `fix(arch): EvidenceSearch weak-relevance + badges@55afba6 + rm:demo TestClient`
  - 相对 `7fcc751`：收回 RF@ee11125 EvidenceSearch；jinshi@55afba6 Museum/Viewer 徽章；`get_stele` 走 `_lookup_stele_id` + 新回归
- **工作树**：`D:\RubbingMind\wt\qa-arch` checkout --detach @5716455
- **临时目录**：`D:\RubbingMind\wt\qa-tmp-arch`（收尾删除）
- **主库 SHA（始=终）**：`rubbingmind.sqlite`=`8408DBC3…323D`；`evidence-v2.sqlite`=`854DF859…ABD3`；未 C-08 --apply 主库；未碰 Codex；未 commit/push

### 门禁结论：**可合并**

相对 `7fcc751`「有条件可合并」的 **3 个残余失败全部清除**。对方自称相关套件 **205 passed / 0 failed**：本闸用等价文件集精确复现 **205 collected / 205 passed / 0 failed**（exit 0）。更广相关子集 **227 passed / 0 failed**。`npm run build` exit 0。

### 三项残余核对

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | EvidenceSearch `relevanceLabel` / `weak-relevance` | **清除** | tip blob **==** RF@ee11125（`f2537025…`）；源码含 `relevanceLabel` + `data-testid="weak-relevance"`；`test_evidence_search_shows_weak_label_from_response` **PASSED** |
| 2 | MuseumPage `ReviewStatusBadges` | **清除** | tip blob **==** jinshi@55afba6（`d32237b6…`）；MuseumPage import + 挂载；`test_badges_render_flags_on_museum_card_and_viewer` / `test_ui_component_renders_both_labels` **PASSED** |
| 3 | TestClient `rm:demo:` / `_lookup_stele_id` | **清除** | `main.py` `get_stele`/`generate` 经 `_lookup_stele_id`；`test_rm_demo_path_query_api_match_bare_demo` + 新回归 `test_rm_demo_query_param_matches_path_via_testclient` **PASSED**；live `GET /api/steles/rm:demo:han-caoquan` **200** |

### 相关套件 vs 对方「205/0」

命令（本闸还原）：
`pytest tests/test_catalog_claims.py tests/test_relevance_threshold.py tests/test_history_graph.py tests/test_demo_scope.py tests/test_synthetic_sample_label.py tests/test_carrier_flag.py tests/test_review_ledger.py tests/test_mechanism_assets.py tests/test_include_demo_compat.py -q -p no:cacheprovider`

| 口径 | 结果 |
|---|---|
| 对方自称 | 205 passed / 0 failed |
| 本闸复现 | **205 passed / 0 failed**（14.75s） |
| 更广相关（+demo_facts/id_*/catalog_assessment_api） | **227 passed / 0 failed** |
| 上次 4 失败单测 | **4 passed** |

### 冒烟摘要（8740）

- includeDemo OFF→`included=false`；ON→`optIn=include_demo`
- `rm:demo:han-caoquan` stele **200**
- mechanism-assets：含 `..` 的编码路径 **400**「路径不合法含 ..」（部分未编码路径被路由层 404，未泄文件）
- C-08：`--json` dry-run 副本；token=`sha256(C-08|diffDigest|dbSHA)[:16]` 与 `dryRunExampleToken=112ba2d3ebd14f2a` **match**；主库 SHA 未变
- `npm run build` **✓ built ~42s / exit 0**

### 收尾

- 停 API **8740**；删 `qa-tmp-arch`；**保留** `qa-arch@5716455`
- 主库 SHA 终=始


## 合入后冒烟 — main @5716455（feature/product-grade-upgrade FF）

- **执行**：RM-红队QA
- **时间**：2026-10-25 12:00 Asia/Shanghai
- **工作区**：D:\RubbingMind（主区，非 worktree）
- **HEAD**：571645544d2271e0e2df64117cddfd04fd6b82e5（git rev-parse == 5716455）；分支 feature/product-grade-upgrade
- **主库 SHA（冒烟前后）**：
ubbingmind.sqlite=8408DBC3…323D；evidence-v2.sqlite=854DF859…ABD3（与期望一致，未写主库）
- **临时**：D:\RubbingMind\wt\qa-tmp（副本 DB + runtime；收尾删除）
- **端口**：自起 API **8740**（副本库）；未杀他人进程；未碰 Codex；未 commit/push/merge/C-08 --apply

### 结论：**通过**

| 项 | 结果 | 证据 |
|---|---|---|
| HEAD == 5716455 | 通过 | rev-parse 全长匹配 |
| 两库 SHA | 通过 | 8408DBC3… / 854DF859… |
| pps/web npm run build | 通过 | exit 0；✓ built ~17.5s |
| pytest 205 套件 -p no:cacheprovider | 通过 | **205 passed / 0 failed** / 14.45s |
| 还原已跟踪脏文件 | 通过 | asset-validation 等无残留 M |
| includeDemo OFF | 通过 | 8740：included=false |
| includeDemo ON | 通过 | included=true / optIn=include_demo |
| RV-AI06 han-caoquan / rm:demo | 通过 | stele+graph 均 200；steleId 分别为 bare /
m:demo:han-caoquan |
| 主库未变 | 通过 | SHA 冒烟后仍 8408DBC3… |

未启动 report@ee11125（等候 Green 下一步指派）。


## 独立门禁 — agent/report-frontend @ee11125（相对 a16d96b；含 weak-relevance）

- **执行**：RM-红队QA
- **时间**：2026-10-25 12:10 Asia/Shanghai
- **固定 tip**：ee111256975812aecd41d6850a01ea4d19ec67bd
  - 相对 16d96b：merge arch@7fcc751；EvidenceSearch 收回
elevanceLabel / weak-relevance（blob
2537025…，与 arch@5716455 相同）
  - 历史含 slice3（eb07479 gray-bt601 / passthrough / experimentStatus）及 reports 全栈
- **工作树**：D:\RubbingMind\wt\qa-report checkout --detach @ee11125
- **临时**：D:\RubbingMind\wt\qa-tmp（副本库）；后端对接主区 **5716455** API **8740**
- **对照**：a16d96b；arch/main@5716455；jinshi@55afba6
- **主库 SHA（始=终）**：8408DBC3…323D / 854DF859…ABD3；未 C-08 --apply；未碰 Codex；未 commit/push

### 门禁结论：**有条件可合并**

相对此前 a16d96b「有条件」：与 **arch@5716455 merge-tree 冲突已清零**；EvidenceSearch 弱相关已收回；reports/slice3 与 arch tip **blob 一致**；
pm run build exit 0。仍须在合入时处理 **Museum/Viewer 徽章挂载**（tip 未挂，与 jinshi@55afba6「changed in both」），Phase1 六层产品验收仍为开项。

### 重点核对

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | EvidenceSearch weak-relevance + BR-09 | **通过** | tip≠a16d96b；tip==5716455；含
elevanceLabel/data-testid=weak-relevance + includeDemo 朱砂警告；	est_evidence_search_shows_weak_label_from_response **PASSED** |
| 2 | slice3 / passthrough / gray 与 arch@5716455 | **通过** | reports 关键 blob（reportData/types/reportFilters/ArtifactRunReport/ReportsPage）**==571**；pi.ts 含 grayCriterion?: 'gray-bt601-pixel-equal-v1'；labels：原图返回（未处理）；ReportsPage/App experimentStatus 五态文案齐全 |
| 3 | npm build + 相关测试 | **部分** |
pm run build **exit 0**（~39s）；FE 相关 pytest **68 passed / 2 failed**（失败=Museum 未挂 ReviewStatusBadges） |
| 4 | merge-tree vs 5716455 / jinshi@55afba6 | **vs571 通过；vs jinshi 有冲突** | vs 5716455：mb=7fcc751，conflict markers **0**；vs 55afba6：**changed in both** MuseumPage.tsx、RubbingArchiveViewer.tsx（徽章挂载） |
| 5 | Phase1 / ACCEPTANCE 开项 | **无实质关闭** | P1-1～P1-6/P1-8/P1-9 仍「尚未验证」；K-E 维持 BR-09 部分通过口径 |

### tip 相对 main@5716455

- 5716455..ee11125：报告前端历史 merge 链（reports 已在主线）
- ee11125..5716455：仅 badges 挂载 + _lookup_stele_id + 测试硬化（**3 文件 FE/BE**）
- 合入策略建议：主线已 571 时以 571 的 Museum/Viewer/main.py 为准；report tip 的 ES/reports 已对齐

### 冒烟（后端 5716455 + 副本库 8740）

- includeDemo OFF（韦坚一）：included=false
- includeDemo ON：optIn=include_demo
- han-caoquan /
m:demo: scope：optIn=demo_scope_id（RV-AI06 预期）
- 主库 SHA 未变

### 必须项（合入前）

1. **MuseumPage + RubbingArchiveViewer** 挂上 ReviewStatusBadges（取 jinshi@55afba6 / arch@5716455 blob）；清除与 jinshi 的 merge-tree 冲突，并使 carrier/review_ledger UI 测通过。
2. Phase1 六层仍非本 tip 关闭条件；保持 ACCEPTANCE 开项，勿宣称 Phase1 全过。

### 收尾

- 停自起 API **8740**；删 qa-tmp；**保留** qa-report@ee11125

## report-frontend 窄复验 adfc6e0（基于 ee11125；徽章重挂）— RM-红队QA — 2026-10-25 12:11 Asia/Shanghai

**范围**：`agent/report-frontend@adfc6e0`（`adfc6e0cf0a57c7926fed929f4673cc0bc32a119`，父 ee11125）。对方声称 MuseumPage/RubbingArchiveViewer 已挂 ReviewStatusBadges(compact)，与 arch@5716455 两文件 diff 空；pytest review_ledger 4p + museum_v3 9p；npm build 过；此前 Museum 徽章 2 fail 清零；主库 SHA 未变。

环境：qa-report `checkout --detach adfc6e0`；临时 `D:\RubbingMind\wt\qa-tmp`；文件只写 `D:\RubbingMind`；不写主库、不 C-08 --apply、不碰 Codex、不 commit/push。端口 8740 本轮未起（无冒烟需求）。

### 窄门结论：**可合并**

ee11125 有条件项「Museum/Viewer 未挂 badges」已在本 tip 清零：两文件 blob **== arch@5716455**，`git diff` 空；挂载点为 `<ReviewStatusBadges steleId=… compact />`。merge-tree vs 5716455 / jinshi@55afba6 **markers 0**。Phase1 P1-* **仍开项**（无新证据关闭）。

### 重点核对

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | 徽章挂载 MuseumPage / RubbingArchiveViewer | **通过** | import ReviewStatusBadges；`<ReviewStatusBadges steleId={…} compact />`；blob tip==571（MuseumPage `d32237b6…` / Viewer `32fc0d11…`）；vs 571 `git diff` 两文件空 |
| 2 | 此前 2 fail 清零 + review_ledger / museum_v3 | **通过（计数勘误）** | prior2：`test_badges_render_flags_on_museum_card_and_viewer` + `test_ui_component_renders_both_labels` **2 passed**；`test_review_ledger` **4 passed**；`test_museum_v3` **collect=5 / 5 passed**（对方称 9p，本库仅 5 case，全部绿）；carrier_flag+review_ledger **7 passed** |
| 3 | npm run build | **通过** | exit 0，~16.5s（chunk size warning 无害） |
| 4 | merge-tree vs 5716455 / jinshi@55afba6 | **均无冲突** | vs 571：mb=`7fcc751…` markers **0**；vs 55afba6：mb=`724c6a0…` markers **0**（ee11125 时的 Museum/Viewer changed-in-both 已消） |
| 5 | Phase1 / ACCEPTANCE | **无实际关闭** | P1-* 保持开项；勿宣称 Phase1 全过 |
| 6 | 主库 SHA | **未变** | START=END rubbingmind `8408DBC3…323D` / evidence-v2 `854DF859…ABD3` |

### tip 相对 main@5716455

- `5716455..adfc6e0`：report 侧历史 merge/slice3/BR-09 等（tip 独有提交链）
- `adfc6e0..5716455`：arch tip 上其它小差（shortstat 5 files, 33+/97-）；**Museum/Viewer/ES/Reports/ReviewStatusBadges blob 已对齐**
- 合入建议：与 571 合时以已对齐 FE blob 为准；本 tip 不再阻塞徽章路径

### 对方声称勘误

- museum_v3：**本 tip 仅 5 个用例且全过**，非对方口述的 9p。不影响结论（无 fail）。

### 收尾

- 本轮未起 8740；删 qa-tmp；**保留** qa-report@adfc6e0

## 合入后冒烟 feature@9d8428e（FF 合入 report@adfc6e0）— RM-红队QA — 2026-10-25 12:20 Asia/Shanghai

**范围**：主工作区 `feature/product-grade-upgrade` tip `9d8428e5e51d8587ea7032540fbdebfa330efc14`（架构已 FF 合入 report@adfc6e0；0 冲突；徽章路径保留）。**未混入 Phase2 ROI**（arch@fa31279 未进 feature）。

环境：主区 `D:\RubbingMind`；临时副本 `D:\RubbingMind\wt\qa-tmp`；不 push/commit/merge、不 C-08 --apply、不写主库、不碰 Codex、不杀他人进程；API **8740**（副本库）。

### 结论：**通过**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | HEAD / status | **一致** | `HEAD==9d8428e`；branch=`feature/product-grade-upgrade`；docs 等仍为未跟踪（本冒烟未 commit） |
| 2 | `npm run build` | **通过** | apps/web exit 0，~15.6s |
| 3 | 相关 pytest | **通过** | review_ledger+carrier_flag+museum_v3 **12p**；扩展（含 include_demo_compat / relevance / demo_scope/facts）**81p**；history_graph+徽章核心 **89p**；**全量 tests 514 passed / 0 failed**（`-p no:cacheprovider`） |
| 4 | includeDemo OFF/ON live（8740 副本库） | **通过** | 魏荐一 OFF：`demoScope.included=false`；ON：`included=true, optIn=include_demo`；`steleId=han-caoquan` OFF 仍 `included=true, optIn=demo_scope_id`（RV-AI06）；`rm:demo:wei-jianyi` OFF 同理 |
| 5 | 徽章 / Museum 路径 | **通过** | MuseumPage / RubbingArchiveViewer 各 1× `<ReviewStatusBadges … compact />`；组件文件存在；`/api/steles` 31；graph `rm:demo:wei-jianyi` 200（演示样本 identity）；assessment 200 |
| 6 | 主库 SHA | **未变** | START=END `8408DBC3…323D` / `854DF859…ABD3` |
| 7 | Phase1 | **仍开项** | 勿宣称关闭；本冒烟无新产品级关闭证据 |

### 收尾

- 停自起 API **8740**（pid 2936）；删 qa-tmp；主区 HEAD 仍 `9d8428e`

## arch-backend 门禁 fa31279（Phase2 ROI；相对 feature@9d8428e）— RM-红队QA — 2026-10-25 12:25 Asia/Shanghai

**范围**：`agent/arch-backend@fa312799dd7af50b37dbb254f3da6a78cb76f6f8`（短 `fa31279`）相对 `feature@9d8428e`。先读评测纪要 `wt/rm-eval-sci/docs/product-upgrade/REVIEW_ARCH_PHASE2_ROI.md`（主树 docs 无此文件副本）。

环境：qa-arch `checkout --detach fa31279`；临时 `D:\RubbingMind\wt\qa-tmp`；不写主库、不 C-08 --apply、不碰 Codex、不 commit/push、不杀他人进程；API **8740**（副本库）。

### 门禁结论：**可合并**

口径：架构 Phase2 ROI **后端契约**（R2–R6/R8）合入 feature。merge-base **即** `9d8428e`（FF 可合）；conflict markers **0**；徽章/ES FE blob **未回退**。pytest 子集 **10p** + 全量 **524p** 与对方/评测纪要一致。**R1/R7 仍缺，同意不阻塞**本 arch 合入。Phase1 P1-* **仍开项**。

### 重点核对

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | merge-tree vs feature@9d8428e | **无冲突（FF）** | mb=`9d8428e…`；markers **0**；`feat..tip` = 6 commits（e17110e…fa31279）；11 files +1039/−4（后端 ROI 模块+测+docs） |
| 2 | 徽章路径误伤 | **无回退** | MuseumPage / RubbingArchiveViewer / ReviewStatusBadges / EvidenceSearch tip blob **==** 9d8428e；`apps/web` diff **空** |
| 3 | Phase2 ROI 测 | **通过** | `tests/test_phase2_roi_arch.py` **10 passed**（R2×3 R3×2 R4×1 R5×2 R6×1 R8×1）；全量 **524 passed / 0 failed**（`-p no:cacheprovider`） |
| 4 | npm run build | **通过** | exit 0（无 FE 改动，仍复跑） |
| 5 | includeDemo / 徽章冒烟 | **未破坏** | 8740 副本：魏荐一 OFF `included=false`；ON `included=true,optIn=include_demo`；Museum 仍挂 compact badges；新路由 `/api/roi-geometry/normalize`、`/api/case-stele-mapping`、`/api/glyph-evaluation` 200；assessment 含 `runLink`/`runLinkUnavailableReason` |
| 6 | R1 / G1 | **仍缺（不阻塞）** | tip+主树 `api.ts` `GlyphInferenceRecord` **无** `roi` / `inputImageSha256` / `cropSha256`；责任方报告前端 |
| 7 | R7 / G7 | **仍缺（不阻塞）** | `derived/mechanism/index.json` `headCommit=7623a52…` 落后 tip；`MECHANISM_HEAD_NOTE` 禁令仍有效；**勿**宣称与 tip 字节一致；责任方评测侧，非 arch |
| 8 | 主库 SHA | **未变** | START=END `8408DBC3…323D` / `854DF859…ABD3` |

### 合入建议

1. **允许** FF/merge `fa31279` → `feature/product-grade-upgrade@9d8428e`。
2. 合入后另开 **报告前端 R1**；**R7** 仍按 MECHANISM_HEAD_NOTE，稳定 tip 后再重跑 mechanism。
3. 勿把 R1/R7 缺项写成 arch 阻塞；勿宣称 Phase1 关闭。

### 收尾

- 停自起 API **8740**；删 qa-tmp；**保留** qa-arch@fa31279

## 合入后冒烟 feature@fa31279（Phase2 ROI 已进）— RM-红队QA — 2026-10-25 12:29 Asia/Shanghai

**范围**：主工作区 `feature/product-grade-upgrade` HEAD `fa312799dd7af50b37dbb254f3da6a78cb76f6f8`（FF 合入 arch Phase2 ROI）。

环境：临时副本 `D:\RubbingMind\wt\qa-tmp`；不 push/commit、不 C-08 --apply、不写主库、不碰 Codex、不杀他人进程；API **8740** + 副本库；`RUBBINGMIND_API_TARGET`。

### 结论：**通过**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | HEAD / status | **一致** | `HEAD==fa31279`；branch=`feature/product-grade-upgrade`；docs 等仍未跟踪 |
| 2 | `npm run build` | **通过** | apps/web exit 0，~16.3s |
| 3 | pytest | **通过** | `test_phase2_roi_arch` **10p**；全量 **524 passed / 0 failed**；徽章轻测 carrier+review_ledger **7p**；asset-validation 已还原 |
| 4 | includeDemo OFF/ON live | **通过** | OFF `included=false`；ON `included=true, optIn=include_demo` |
| 5 | ROI 路由抽样 | **通过** | normalize→glyph-bbox schema；case-stele-mapping available/version=1/silentEquateForbidden；glyph-evaluation `not_evaluated` + 指标 null；assessment 含 `runLink`/`runLinkUnavailableReason`（assess28 命名空间未命中 → runLink=null，符合契约） |
| 6 | 徽章路径 | **保留** | MuseumPage + RubbingArchiveViewer 仍挂 `ReviewStatusBadges`（compact） |
| 7 | 主库 SHA | **未变** | START=END `8408DBC3…323D` / `854DF859…ABD3` |
| 8 | Phase1 | **仍开项** | 勿宣称关闭 |

### 收尾

- 停自起 API **8740**（pid 60348）；删 qa-tmp；HEAD 仍 `fa31279`


## 门禁 report-frontend@35c856a（P1-7 / RF-6 / RF-10 / R1 批）— RM-红队QA · 2026-10-25 12:40 Asia/Shanghai

**范围**：qa-report detach 35c856a9c0f5ba24a4ba18a15a09c3ad0bd61251（4 commits：7e726cd P1-7 MeanProcessed；bf0db74 RF-6/P1-5 diagnosis；631b9bc RF-10 RETEST_TITLE；35c856a R1 本地 GlyphInferenceRecord）。对照 feature@fa312799dd7af50b37dbb254f3da6a78cb76f6f8；顺带对照 arch AB-7@c846d31442b3e34327c048a8a17ef9c9d3644af7。

环境：临时副本 D:\RubbingMind\wt\qa-tmp；不 push/commit、不 C-08 --apply、不写主库、不启 Codex、不杀他人进程；API **8740** + 副本库（feature@fa31279）。

### 结论：**有条件可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip / 四提交 | **确认** | HEAD=35c856a；含 7e726cd / bf0db74 / 631b9bc / 35c856a |
| 2 | merge-tree vs feature@fa31279 | **无冲突** | mb=adfc6e0cf0a57c7926fed929f4673cc0bc32a119；markers **0** |
| 3 | merge-tree vs arch AB-7@c846d31 | **无冲突** | mb=adfc6e0cf0a57c7926fed929f4673cc0bc32a119；markers **0**；tip 增 glyphInference.ts，AB-7 改 pi.ts（文件不重叠） |
| 4 | 徽章 / ES / api.ts 相对 feature | **未回退** | tip pi.ts blob == fa31279（73c3a39…）；Museum/Viewer/EvidenceSearch 未误伤 |
| 5 | npm run build | **通过** | apps/web exit 0 |
| 6 | 相关 pytest | **通过** | 报告侧相关 **15 passed**（先前闸）；本闸未宣称全量 |
| 7 | feature@8740 live 冒烟 | **通过** | 魏荐一 OFF included=false；ON included=true,optIn=include_demo；/api/glyph-evaluation 200；assessment 含
unLink |
| 8 | R1 本地类型（35c856a） | **落地（报告侧）** | 新增 pps/web/src/components/reports/data/glyphInference.ts 交叉类型；ArtifactRunReport 展示 mappedSourceBBox / inputImageSha256 / cropSha256 |
| 9 | G1（grep api.ts） | **仍 xfail（已知）** | 纯 report tip 的 pi.ts **无** roi/SHA 声明；**记为「待与 AB-7 同批合入后转绿」**；**不单独因此判不可合并**。AB-7@c846d31 已在 arch 声明
oi/inputImageSha256/cropSha256；arch 上 phase2_roi_arch 11p 已绿（对方纪要） |
| 10 | P1-7 / RF-6 / RF-10 | **有证据，不关闭** | MeanProcessed / diagnosisConsistency / RETEST_TITLE 源码与提交在 tip；**勿标 P1/RF 关闭**（可记「部分/证据」） |
| 11 | Phase2 后端 | **合入时由 feature 保留** | tip 相对 feature 缺 Phase2 后端文件属谱系预期；merge 后须保留 fa31279 侧 ROI 路由与测试 |
| 12 | 主库 SHA | **未变** | START=END 8408DBC3…323D / 854DF859…ABD3 |

### 必须项（合入前/合入时）

1. **与 AB-7@c846d31 同批（或紧随）合入**，使 pi.ts GlyphInferenceRecord 声明落地，G1 转绿；纯 tip 合入后 G1 仍可能 xfail，属预期。
2. **合入后保留 feature@fa31279 Phase2 后端**（roi / case-stele-mapping / glyph-evaluation / test_phase2_roi_arch 等），勿被 report tip 谱系删文件盖掉。
3. **P1-* / RF-* 保持开启**；本批仅记证据，不关单。
4. tip 本地 glyphInference.ts 与 AB-7 pi.ts 合入后可能字段重叠——属清理项，**不阻塞**；可后续收敛到单一类型源。

### 合入建议

- **允许** merge 35c856a → feature/product-grade-upgrade@fa31279（或先合 AB-7@c846d31 再合本 tip；merge-tree 两边均无冲突）。
- 推荐顺序：**AB-7（api.ts）与本 tip 同批**，避免窗口期 G1 持续 xfail 被误读为回归。
- 勿因纯 tip 上 G1 xfail 单独判不可合并。

### 收尾

- 停自启 API **8740**；清 qa-tmp；**保留** qa-report@35c856a


## 门禁 jinshi@43b873f（已 merge feature@fa31279；claims 24/28）— RM-红队QA @ 2026-10-25 12:38 Asia/Shanghai

**范围**：D:\RubbingMind\wt\qa-jinshi checkout --detach 43b873ff0a41716c00851fed2c2373b0b69bbb81；临时 D:\RubbingMind\wt\qa-tmp-jinshi（与报告审查隔离）。不写主库、不碰 Codex、不 commit/push；C-08 **仅 dry-run**（禁止 --apply 主库）。端口未起服务（本轮无 TestClient/脚本 API 需求）。

相对 tip 含：merge fa31279；claims 第3/4 批深化（c6e927f / b4cfc22）；此前 badges@55afba6 与 feature 对齐 merges。

### 结论：**有条件可合并**

| # | 项 | 判定 | 证据 |
|---|---|---|---|
| 1 | tip / 祖先关系 | **确认** | HEAD=43b873f；
a31279 **是** tip 祖先（merge-base --is-ancestor exit 0）；parents=
5593ff +
a31279 |
| 2 | merge-tree vs feature@fa31279 | **冲突 0** | merge-tree --write-tree exit 0 → tree 8c14425…；classic 扫描命中的 “conflict” 均来自 **claims 内容字段**（status=conflict），非 Git 冲突 |
| 3 | test_catalog_claims | **171 passed** | 与对方宣称一致；exit 0 |
| 4 | claims+museum_v3+phase2 | **186 passed** | 与对方宣称一致；exit 0（1 Starlette/httpx deprecation warning） |
| 5 | validate_museum_v3 | **84/84 SHA** | items=28, images=84, sha256Match=84, passed=true |
| 6 | claims 覆盖 24/28 | **确认** | index.batch=Phase 3 深化第 4 批（24/28…）；remaining=4；24 件 piece JSON 均已深化 |
| 7 | conflict / 异文并列 | **通过** | 全库 17 条 status=conflict **均**含 alternatives（≥2）+ note；证据级「待人工复核」未升「已验证」；BAD_CLOSE_OR_NO_ALTS=[]；CHANGELOG 第4批明确「并列待复核，不臆断」 |
| 8 | C-08 令牌 / dry-run | **通过（仅预览）** | confirmation_token = sha256(f"C-08|{diff_digest}|{db_sha}")[:16]；副本 dry-run token=112ba2d3ebd14f2a MATCH；副本 SHA 始=终=8408DBC3…；**未** --apply 主库 |
| 9 | CHANGELOG / 新 claims 史实 | **无明显无源** | 第3/4 批 CHANGELOG 均列 NPM/Met 实开 URL；batch4 asserted 无空 sources；「已验证」史实条目均挂馆方/NPM/目录源；meta 字段（sourceSha256/derivation）自引用属预期 |
| 10 | 主库 SHA | **未变** | START=END 8408DBC3…323D / 854DF859…ABD3 |

### 必须项（合并前/合并时）

1. **合入时保留 tip 相对 fa31279 的增量**（claims 第3/4 批 + index + tests）；因 tip 已含 fa31279，可 FF 或 merge tip→feature。
2. **C-08 仍禁止对主库 --apply**，直至用户明确批准 + 停后端；令牌口径维持 sha256(C-08|diffDigest|dbSHA)[:16]（与 arch 一致）。
3. **剩余 4/28 件**（第5批）与既有 conflict「待人工复核」**保持开项**，不得在合并说明中宣称 claims 完成或冲突已关闭。
4. 合并后冒烟：	est_catalog_claims +
alidate_museum_v3 + includeDemo/徽章路径（若 FE 已在 feature）。

### 非阻塞备注

- 本 tip 的 merge-tree classic 文本中出现的 “conflict” 字样均为著录异文状态，**不是**合并冲突。
- qa-jinshi **保留**于 43b873f；已清 qa-tmp-jinshi。


## 窄门禁 jinshi@8e4ee25（基于 43b873f + 第5批 28/28）— RM-红队QA @ 2026-10-25 12:40 Asia/Shanghai

**范围**：qa-jinshi detach 8e4ee25fc5a9a79604cbd8eac7eb7b2f74bc8ea5；临时 qa-tmp-jinshi。相对已审 43b873f 的窄复验；C-08 仅 dry-run；不写主库。

### 相对 43b873f 增量

- 单提交 parent=43b873f：8e4ee25 feat(claims): 第5批逐件深化 4件（28/28）qing_01/qing_02/qing_03/qing_04
- 文件：+qing_01..qing_04 claims；index.json；CONTENT_CHANGELOG.md；	ests/test_catalog_claims.py

### 结论：**可合并**（合入目标改为 **8e4ee25**；43b873f 门禁结论仍成立并被本 tip 覆盖）

| # | 项 | 判定 | 证据 |
|---|---|---|---|
| 1 | tip / 祖先 | **确认** | HEAD=8e4ee25；fa31279 仍为祖先；43b873f 为直接父提交 |
| 2 | merge-tree vs fa31279 | **冲突 0** | write-tree exit 0 → 705ba7e33c… |
| 3 | test_catalog_claims | **199 passed** | exit 0（较 43b873f 的 171 增加第5批用例） |
| 4 | claims+museum_v3+phase2 | **214 passed** | exit 0 |
| 5 | validate_museum_v3 | **84/84 SHA** | items=28（含清代 4）；passed=true |
| 6 | claims 覆盖 | **28/28** | index remaining=0；28 piece JSON；第5批 qing_01–04 |
| 7 | conflict / 待人工复核 | **仍开项** | 全库 20 conflict 均有 alternatives；BAD_CLOSE=0；未要求臆断关闭 |
| 8 | 第5批来源 | **有源** | CHANGELOG 列 Princeton/Met 实开 URL；4 件 unsourced_asserted=0 |
| 9 | C-08 | **未 apply 主库** | dry-run 令牌 sha256(C-08|diffDigest|dbSHA)[:16] MATCH=112ba2d3ebd14f2a；副本 SHA 未变 |
| 10 | 主库 SHA | **未变** | START=END 8408DBC3…323D / 854DF859…ABD3 |

### 合入说明（非阻塞，但必须遵守）

1. **合入目标用 8e4ee25**（含第5批），勿停在 43b873f。
2. C-08 仍禁止对主库 --apply，直至用户批准并停后端。
3. 既有 conflict /「待人工复核」保持开项，合并说明中不得宣称「冲突已关闭」或「全部史实已核定」。
4. 合并后冒烟：	est_catalog_claims +
alidate_museum_v3。

### 收尾

- 已清 qa-tmp-jinshi；**保留** qa-jinshi@8e4ee25；未起 8740/8742。

## 合入后冒烟 feature@e9ce60e（08d8da8 + jinshi@8e4ee25）— RM-红队QA @ 2026-10-25 12:46 Asia/Shanghai

**范围**：主仓 `feature/product-grade-upgrade` HEAD `e9ce60e945ffe4d561cc26434b6d5f000c69ccf1`；独立 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach 同 tip。只读验收；未 push/commit/merge；未写主库；未 C-08 --apply；未起常驻 8740（ROI 用 TestClient）。

**ancestry**：parents = `08d8da8` + `8e4ee25`；另含祖先 `c846d31`（AB-7）、`35c856a`（report）。`merge-base --is-ancestor` 对 08d8da8 / 8e4ee25 / c846d31 / 35c856a 均为 exit 0。

### 结论：**通过**

| # | 项 | 判断 | 证据 |
|---|---|---|---|
| 1 | tip / parents | **确认** | HEAD=`e9ce60e`；parents=`08d8da868a5654f43101e339b39997c526bb3a35` + `8e4ee25fc5a9a79604cbd8eac7eb7b2f74bc8ea5`；message=Merge jinshi@8e4ee25 into feature |
| 2 | 含 08d8da8 / 8e4ee25 | **是** | 二者均为 tip 直接 parent；08d8da8 自身 parents 为 c846d31 + 35c856a |
| 3 | 全量 pytest | **637 passed / 0 failed / 0 xfail** | `python -m pytest tests -q -p no:cacheprovider`；exit 0；53.63s；1 Starlette/httpx deprecation warning |
| 4 | G1 | **转绿** | `test_ts_glyph_inference_record_declares_roi_and_shas_g1` **PASSED**；`apps/web/src/services/api.ts` GlyphInferenceRecord 含 `roi` / `inputImageSha256` / `cropSha256` / `mappedSourceBBox` |
| 5 | Phase2 ROI | **通过** | `tests/test_phase2_roi_arch.py` 11 passed（含 G1）；TestClient：`GET /api/roi-geometry/normalize` **200**；`/api/case-stele-mapping` 200 available=true version=1；`/api/steles/.../roi-compare` 200；`/api/glyph-evaluation` 200 not_evaluated |
| 6 | claims / museum 抽样 | **通过** | targeted（phase2+claims+museum_v3+include_demo+demo_scope）**235 passed**；`validate_museum_v3.py` passed=true items=28 images=84 sha256Match=84；claims index works=28 remaining=0（第5批含 qing_01–04）；conflict=20 且全部带 alternatives（未强关） |
| 7 | npm run build | **通过** | `apps/web`：`npm ci` + `npm run build`（tsc && vite build）exit 0；built in 15.10s；已知 >500kB chunk 警告 |
| 8 | includeDemo / badges | **未破坏** | MuseumPage + RubbingArchiveViewer 仍 import/渲染 `<ReviewStatusBadges … compact />`；`test_include_demo_compat` + `test_demo_scope` 全绿 |
| 9 | 主库 SHA | **始=终不变** | PRE=POST `8408DBC3…323D`（rubbingmind.sqlite）/ `854DF859…ABD3`（evidence-v2.sqlite） |

### 相对此前闸口的关键点

- 纯 report@35c856a 上 G1 因缺 AB-7 `api.ts` 字段而预期 xfail；合入 AB-7@c846d31 + report@35c856a → 08d8da8 后，再合 jinshi@8e4ee25 → **e9ce60e**，G1 **已转绿**。
- claims 自 24/28 推进至 **28/28**（第5批 qing_*），与先前窄门禁 8e4ee25 一致。
- 全量用例规模 524 → **637**（claims 扩容 + Phase2/G1 等）。

### 无 blocker / 残留（非阻断）

1. C-08 **仍禁止 --apply**（本轮未触碰）。
2. conflict 异文并列（20 条均带 alternatives）保持开项，不要求关闭。
3. npm audit 仍有 moderate/high 提示（历史已知，非本轮回归）。
4. Phase1 产品向 P1-* 仍按既往「对产品开放」口径，本轮未重开浏览器全量。

### 收尾

- 保留 worktree `qa-feature-smoke@e9ce60e`；日志：`wt/qa-tmp/pytest-e9ce60e.txt`、`npm-build-e9ce60e.txt`、`validate-museum-e9ce60e.txt`、`pytest-targeted-e9ce60e.txt`。
- **未**改业务代码、**未**写主库、**未** push。

## jinshi 文档窄门禁 9c9fdf2（开项台账；对齐 e9ce60e；无史实改动）— RM-红队QA @ 2026-10-25 12:50 Asia/Shanghai

**范围**：`agent/jinshi` tip `9c9fdf272451a14b65ceac4d43e2fe2db2f55c1b`；worktree `D:\RubbingMind\wt\qa-jinshi` detach。只读验收；无 push/commit/merge；未写主库；未 C-08 --apply；未改业务代码。

**ancestry**：parents = `f0b698c1b00753e7bfd26c11a2a82e2e367f40f8`（docs 开项台账）+ `e9ce60e945ffe4d561cc26434b6d5f000c69ccf1`。`merge-base --is-ancestor e9ce60e HEAD` exit 0；merge-base = e9ce60e（已含）。`8e4ee25` 为 f0b698c 祖先。

### 结论：**可合并**

| # | 项 | 判断 | 证据 |
|---|---|---|---|
| 1 | tip / vs e9ce60e | **已含** | HEAD=`9c9fdf2`；e9ce60e 为 merge parent²；message=align agent/jinshi to tip |
| 2 | merge-tree vs e9ce60e | **冲突 0** | `git merge-tree --write-tree` exit 0 → tree `2bf9764b48402c61f9b73c31cbe957b959904c7e`；无 CONFLICT / changed-in-both |
| 3 | diff 性质 | **仅文档/台账/校验脚本** | `e9ce60e...HEAD` 仅 4 文件 +568 行：`CLAIMS_OPEN_ISSUES.md`、`CONTENT_CHANGELOG.md`、`scripts/check_claims_open_issues.py`、`tests/test_claims_open_issues.py` |
| 4 | 无史实改动 | **确认** | `data/catalog/claims` / museum / evidence 路径 **无 diff**；无 claims JSON / 图像 / 史实字段实质变更 |
| 5 | check_claims_open_issues --check | **ok** | `{"ok": true, "openRows": 36, "conflict": 20, "pendingHuman": 30, "reviewFlag": 1, "cataloguePendingReview": 13, "claimFiles": 28}` |
| 6 | 相关 pytest | **200 passed** | `tests/test_catalog_claims.py` + `tests/test_claims_open_issues.py`；独立复现，与对方宣称一致 |
| 7 | conflict / 待人工复核 | **仍开项** | 台账明确 conflict=20、待复核并列；口径「勿宣称开项收官关闭」；未要求关闭冲突 |
| 8 | C-08 | **禁 apply** | 台账写明主库禁止 `--apply`；本轮未触碰 C-08 |
| 9 | 主库 SHA | **未变** | rubbingmind.sqlite=`8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D`；evidence-v2.sqlite=`854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3` |

### 合入说明（非阻塞）

1. 合入目标 **9c9fdf2**（已对齐 e9ce60e 的文档增量）。
2. 不得在合并说明中宣称「开项已关闭」或「冲突已解决」。
3. C-08 仍禁止对主库 `--apply`。

### 收尾

- 保留 `qa-jinshi@9c9fdf2`；未启 8740；未碰 `D:\Codex\worktrees`。
- **无** blocker。

## 门禁：eval-sci@01dd3be（已 merge e9ce60e；G1 正式 assert）— RM-红队QA @ 2026-10-25 12:52 Asia/Shanghai

**环境**：worktree `D:\RubbingMind\wt\qa-evalsci` detach `01dd3be7c5a48e843a23a5480ff7168657ed2735`；只读；未 push/commit/merge；未 C-08 --apply；未写主库。

**ancestry**：`log -1` subject=`docs(eval-sci): record tip hash in REVIEW_EVALSCI_G1_R1`；parent=`460989029b44d2e1814e469643825b0fd6ce66da`。`merge-base --is-ancestor e9ce60e… HEAD` exit 0；merge `1026e69` parents=`3ac23d4` + `e9ce60e945ffe4d561cc26434b6d5f000c69ccf1`。相对 e9ce60e 超前 23 commits（含历史 eval-sci + 两次 feature merge + G1 转绿 + tip 记录）。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip / parents | **通过** | HEAD=`01dd3be`；实质测试 tip=`4609890`（纪要表内记录）；01dd3be 仅 +1 行 tip hash |
| 2 | vs e9ce60e | **已含** | e9ce60e 为祖先；merge-base = e9ce60e |
| 3 | merge-tree vs e9ce60e | **冲突 0** | `changed in both` = 0（快进子孙，无双向冲突） |
| 4 | G1 正式 assert | **PASSED（非 xfail）** | `test_phase2_roi_fields.py::test_ts_glyph_inference_record_declares_roi_and_shas_g1` + `test_phase2_roi_arch.py::…_g1` 均 PASSED |
| 5 | Phase2 ROI 子集 | **21 passed** | fields(10)+arch(11)；另 glyph A1–A23 全绿 |
| 6 | 全量 pytest | **708 passed / 1 xfailed / 0 failed** | `python -m pytest tests -q`；65.30s；唯一 xfail=`test_a24_…`（A24 schema 未落地） |
| 7 | museum_processing | **未改** | blob 双侧 `60358fe70dfe5d41ab72f3be7bb760c273e5e5d3`；`git diff --stat` 空 |
| 8 | 纪要 REVIEW_EVALSCI_G1_R1.md | **与实测一致** | 宣称 708p/1xfail=A24、ROI 21p、G1 PASSED — 独立复现吻合；无夸大。纪要 tip 写 4609890（实质），门禁 tip 01dd3be 为其 docs 后继 |
| 9 | R7 | **开项/已知** | mechanism `headCommit=7623a52` 落后；文档化禁重跑；不要求关闭 |
| 10 | 主库 SHA | **未变** | PRE=POST `8408DBC3…323D` / `854DF859…ABD3` |

### 与对方宣称核对

- 「已 merge e9ce60e」：成立（ancestry + merge commit 1026e69）。
- 「G1 正式 assert PASSED」：成立（两处 G1 测试均非 xfail）。
- 「全量 708p/1xfail=A24」：成立（独立复现）。
- 「ROI 子集 21p」：成立（fields+arch）。
- 「museum_processing 未改」：成立（同 blob）。
- 「R7 未重跑」：成立（开项保留）。

### 无 blocker

1. A24 保持 xfail（已知产品缺口，非本 tip 回归）。
2. R7/G7 mechanism head 滞后：开项，勿强关。
3. 纪要 tip 字段写 4609890 而非 01dd3be：可接受（01dd3be 仅记录 tip hash 的 meta commit）。

### 环境

- 日志：`wt/qa-tmp/pytest-roi-01dd3be.txt`、`pytest-full-01dd3be.txt`
- **未**改业务代码；**未**杀无关进程；**未** push。

## 报告前端门禁 tip@044b059（agent/report-frontend；相对 feature@e9ce60e）— RM-红队QA @ 2026-10-25 12:52 Asia/Shanghai

**范围**：独立 worktree `D:\RubbingMind\wt\qa-report` detach 于 tip `044b0597d6d72fe7842fe26a292bc44edb09be09`；只读验收；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程。

**ancestry**：`merge-base --is-ancestor e9ce60e HEAD` = exit 0；parent=`44b710c`；含 merge `79cd366`（e9ce60e）与 `5b16d39`（P1-4/P1-11）与 `44b710c`（R1 api 对齐）。

### 结论：**可合并**

| # | 项 | 判定 | 证据 |
|---|---|---|---|
| 1 | tip / log -1 | **确认** | HEAD=`044b0597d6d72fe7842fe26a292bc44edb09be09`；message=`feat(reports): 失败案例样例图 + JSON/打印保留负提升口径`；AuthorDate 2026-10-25 12:47 +0800 |
| 2 | 含 e9ce60e | **是** | ancestor；commits since：044b059 / 44b710c / 79cd366 / 520152e / 5b16d39 |
| 3 | merge-tree vs e9ce60e | **0 冲突** | merge-base=`e9ce60e945ffe4d561cc26434b6d5f000c69ccf1`（tip 已含 feature）；diff 9 files / +358 −37 |
| 4 | G1 / api.ts | **PASSED（非 xfail）** | `test_ts_glyph_inference_record_declares_roi_and_shas_g1` **1 passed**；`GlyphInferenceRecord` 含 `roi` / `mappedSourceBBox` / `inputImageSha256` / `cropSha256`（44b710c R1 对齐） |
| 5 | 最差 6 条 + failureRetention | **有代码证据** | `FailureCasesPanel`：`negatives.slice(0, 6)` + 标题「最差 Math.min(6,…) 条 · 仅本批资产」；`ReportsPage` exportJson `failureRetention.policy`（D-07/RF-6）；`ReportPrintLayout` `data-testid="print-failure-retention"` |
| 6 | P1-4 / P1-11 | **有改动证据；勿关单** | `5b16d39`：`MechanismPanel.tsx`（200 行）+ panel=mechanism；Workbench 改用 `num`/`signed`，空值不拼 dB/%，识字未评测文案。**Phase1 P1-* / RF-* 仍开**，本闸不宣称关闭 |
| 7 | npm run build | **通过** | `apps/web` `tsc && vite build` exit 0；built in 17.02s；已知 >500kB chunk 警告 |
| 8 | 相关 pytest | **通过** | related `-k g1/glyph/failure/report/phase2_roi/include_demo`：**34 passed**；phase2_roi_arch：**11 passed**；G1 单测：**1 passed** |
| 9 | 主库 SHA | **始=终不变** | PRE=POST `8408DBC3…323D`（rubbingmind.sqlite）/ `854DF859…ABD3`（evidence-v2.sqlite） |

### 无 blocker / 仍开项（合入条件说明）

1. **P1-4 / P1-11 / 其余 Phase1 P1-* / RF-***：本 tip 仅交付前端实现证据，**未独立验收关闭**；ACCEPTANCE_MATRIX 保持开项。
2. C-08 **仍禁止 --apply**（本闸未触碰）。
3. npm chunk >500kB 警告（历史已知，非本 tip 回退）。
4. 无前端单测文件专测 FailureCasesPanel / failureRetention（以代码审查 + build + 后端相关测为准）。

### 收尾

- 保留 worktree `qa-report@044b059`；日志：`wt/qa-tmp/pytest-044b059-*.txt`、`npm-build-044b059.txt`、`evidence-044b059.txt`、`sha-pre/post-044b059.txt`。
- **未**改业务代码、**未**写主库、**未** push。

## 合入后冒烟 feature@0654d13（jinshi台账9c9fdf2 + eval@01dd3be + report@044b059）— RM-红队QA @ 2026-10-25 13:01 Asia/Shanghai

**范围**：主仓 `feature/product-grade-upgrade` HEAD `0654d1307f849f5dadbfaca87fd96f2ce3b56c41`；只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach 同 tip。只读验收；未 push/commit/merge；未写主库；未 C-08 --apply；未常驻 8740（ROI 用 TestClient）。

**ancestry**：parents = `c635572c671b9de27a6234424c2eee8d0caad8a2`（Merge report@044b059；其 parents=`9c9fdf2`+`044b059`）+ `01dd3be7c5a48e843a23a5480ff7168657ed2735`。`merge-base --is-ancestor` 对 `9c9fdf2` / `01dd3be` / `044b059` / `e9ce60e` / `08d8da8` / `8e4ee25` 均为 exit 0。

### 结论：**通过**

| # | 项 | 判断 | 证据 |
|---|---|---|---|
| 1 | tip / parents | **确认** | HEAD=`0654d1307f849f5dadbfaca87fd96f2ce3b56c41`；parents=`c635572` + `01dd3be`；message=Merge eval@01dd3be into feature |
| 2 | 含关键 tip | **是** | 含 `9c9fdf2`（jinshi 台账）、`01dd3be`（eval G1）、`044b059`（report failureRetention）、先前 `e9ce60e` |
| 3 | 全量 pytest | **709 passed / 0 failed / 1 xfailed** | `python -m pytest tests -q -p no:cacheprovider`；exit 0；58.28s；xfail=`test_a24_export_label_recognized_forbidden_until_schema_exists`（A24 已知产品缺口） |
| 4 | G1 | **正式 PASSED** | `test_ts_glyph_inference_record_declares_roi_and_shas_g1`（fields + arch 双测）均 PASSED；非 xfail |
| 5 | Phase2 ROI | **通过** | `test_phase2_roi_fields`+`test_phase2_roi_arch` **21 passed**；TestClient：`GET /api/roi-geometry/normalize` **200**；`/api/case-stele-mapping` **200** available=true version=1；`/api/steles/tang_01_duobao/roi-compare` **200**；`/api/glyph-evaluation` **200** not_evaluated |
| 6 | claims / museum 抽样 | **通过** | claims index works=**28/28** remaining=0（含 qing_01–04）；`validate_museum_v3.py` passed=true items=28 images=84 sha256Match=84；`check_claims_open_issues.py --check` ok（openRows=36 conflict=20 claimFiles=28）；claims+museum+open+demo pytest **225 passed** |
| 7 | npm run build | **通过** | `apps/web` `tsc && vite build` exit 0；built in 15.57s；已知 >500kB chunk 警告 |
| 8 | 主库 SHA | **始=终不变** | PRE=POST `8408DBC3…323D`（rubbingmind.sqlite）/ `854DF859…ABD3`（evidence-v2.sqlite） |
| 9 | P1 / RF 关单 | **未关** | 本闸追加 FINDINGS/MATRIX **未**把未独立关闭的 Phase1 P1-* / RF-* 标关闭；仍为开项 |

### 相对前序 tip 的增量核对

- 相对 `e9ce60e`（637p）：合入 eval+report+jinshi 台账后全量升至 **709p / 1xfail(A24)**；G1 保持正式绿。
- 相对已闸 `01dd3be`（708p）：+1 来自 report 侧合入后的用例增量；A24 xfail 仍在。
- conflict 异文并列（20）与 C-08 禁 `--apply`：**仍开项**，本闸未要求关闭、未 apply。

### 无 blocker / 已知保留开项（非本 tip 回归）

1. A24 继续 xfail（schema 未落地产品缺口）。
2. C-08 **仍禁止 `--apply`**；conflict 异文并列仍开项。
3. Phase1 **P1-*** / **RF-***：**仍开**——本闸有 report 侧证据但不独立关单。
4. npm chunk >500kB 警告（历史已知）。

### 收尾

- 日志：`wt/qa-tmp/pytest-0654d13.txt`、`pytest-g1-phase2-0654d13.txt`、`pytest-claims-museum-0654d13.txt`、`validate-museum-0654d13.txt`、`claims-open-0654d13.txt`、`phase2-routes-0654d13.txt`、`npm-build-0654d13.txt`、`sha-pre/post-0654d13.txt`。
- **未**改业务代码、**未**写主库、**未** push、**未**杀非己进程。

## 金石文档窄门禁 tip@ec70f56（JS-4/JS-5 开项台账；对齐 feature@0654d13）— RM-红队QA @ 2026-10-25 13:16 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-jinshi` detach 于 tip `ec70f563b2e011e90017ca975fb98f8e9ddcf104`；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程。

**ancestry**：`merge-base --is-ancestor 0654d13 HEAD` = exit 0；`merge-base(0654d13, HEAD)` = `0654d13`（**快进**）；message=`docs(claims): JS-4 冲突并列一览 + JS-5 待人工复核清单（开项仍开放）`；AuthorDate 2026-10-25 13:13 +0800。

### 结论：**可合并**

| # | 项 | 判定 | 证据 |
|---|---|---|---|
| 1 | tip / log -1 | **确认** | HEAD=`ec70f563b2e011e90017ca975fb98f8e9ddcf104` |
| 2 | vs 0654d13 | **已含 / FF** | ancestor exit 0；commits since=仅 ec70f56 |
| 3 | merge-tree vs 0654d13 | **冲突 0** | `--write-tree` exit 0；conflict_markers=0；changed_in_both=0 |
| 4 | diff 性质 | **仅 docs/脚本/台账** | 3 files +161/−3：`CLAIMS_OPEN_ISSUES.md`、`CONTENT_CHANGELOG.md`、`scripts/check_claims_open_issues.py`；**无** claims JSON / museum 史实路径 |
| 5 | claims 树 | **未改** | `data/catalog/claims` blob 双 tip 同 `d7293fc214ee86c5a345bb9bf995a71c2d57e52b` |
| 6 | check_claims_open_issues --check | **ok** | claimFiles=**28**；openRows=36；**conflict=20（仍开）**；pendingHuman=30；reviewFlag=1；cataloguePendingReview=13 |
| 7 | 相关 pytest | **200 passed** | `tests/test_catalog_claims.py` + `tests/test_claims_open_issues.py`；0.86s；exit 0 |
| 8 | conflict / C-08 | **仍开 / 禁 apply** | 台账明示「不定论、不合并、不关闭」；本闸**未**跑 `--apply`；**未**要求关单 |
| 9 | 主库 SHA | **始=终不变** | PRE=POST `8408DBC3…323D`（rubbingmind.sqlite）/ `854DF859…ABD3`（evidence-v2.sqlite）；主库 HEAD 仍 `0654d13` |

### 无 blocker

1. 冲突异文并列（约 20）与待人工复核**仍开放**——符合门禁，勿关单。
2. C-08 **仍禁止 --apply**——本闸未触碰。
3. 史实判定未改（claims JSON / museum 路径 diff 为空）。

### 收尾

- 日志：`wt/qa-tmp/gate-ec70f56-diff.txt`、`claims-open-ec70f56.txt`、`pytest-ec70f56.txt`、`sha-pre-post-ec70f56.txt`
- **未**改业务代码、**未**写主库、**未** push、**未** C-08 --apply。


## 报告前端门禁 tip@b200567（agent/report-frontend；对齐 feature@0654d13）— RM-红队QA @ 2026-10-25 13:16 Asia/Shanghai

**范围**：独立 worktree `D:\RubbingMind\wt\qa-report` detach 至 tip `b200567e481c9b7259a73caee03efbbff642b2ba`；只读验收；未 push/commit/merge；未写主库；未 C-08 --apply；未改业务代码；未杀非己进程。

**ancestry**：`merge-base --is-ancestor 0654d1307f849f5dadbfaca87fd96f2ce3b56c41 HEAD` = exit 0（已含 / FF 对齐）；tip 之上增量 2 commit：`7c6826a`（MECHANISM_HEAD_NOTE）→ `b200567`（reportStatus + glyphEvaluationText）。

### 结论：**可合并**

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip SHA | b200567e481c9b7259a73caee03efbbff642b2ba | `agent/report-frontend`；parent=`7c6826a` |
| 2 | vs feature@0654d13 | **已含 / FF** | ancestor exit 0；`0654d13..HEAD` = 7c6826a + b200567 |
| 3 | merge-tree vs 0654d13 | **冲突 0** | `git merge-tree --write-tree` → `3614637a…` exit 0；markers=0 |
| 4 | MECHANISM_HEAD_NOTE（P1-4 落后 tip 提示） | **有代码证据** | `MechanismPanel.tsx`：`data-testid="mechanism-head-lag-note"`；有 headCommit 时明示「可能落后于当前分支 tip」「不得宣称…与当前 tip 字节一致」；无则 `mechanism-head-unrecorded` |
| 5 | reportStatus 全路径文案 | **有代码证据** | `reportData.ts` `ReportApi.report`：`backend_unavailable` / 410 `stele_retired` / 404 `run_not_found` / 404 `stele_not_found` / 通用 error；`ArtifactRunReport` `data-testid="artifact-report-status"` + `data-status` |
| 6 | glyphEvaluationText（not_evaluated 禁伪 Top-k） | **有代码+逻辑证据** | `reportData.ts` `glyphEvaluationText`：`status==='not_evaluated'` 优先返回「未评测」**不输出 Top-1/Top-3 数字**（即使 top1/top3 非空）；接入 `GlobalEvaluation` / `ArtifactRunReport` / `ReportPrintLayout`；node 隔离复现：not_evaluated+假 top1=0.99 → 仍仅「未评测」 |
| 7 | npm run build | **通过** | `apps/web`：`tsc && vite build` exit 0；`dist/index.html` 存在 |
| 8 | 相关 pytest | **通过** | 相关 20 passed / 1 xfailed（A24 类已知）；拓宽 report/glyph 15 passed / 1 xfailed |
| 9 | P1 / RF / RF-8 关单 | **未关** | 本闸仅记前端实现证据；**Phase1 P1-* / RF-* / RF-8 仍开**；MATRIX/FINDINGS **未**把未独立关闭项标关闭 |
| 10 | 主库 SHA | **始=终未变** | PRE=POST `rubbingmind.sqlite=8408DBC3…323D` / `evidence-v2.sqlite=854DF859…ABD3` |

### 无 blocker / 仍开项（符合门禁，勿关单）

1. **P1-4**：本 tip 有 MECHANISM_HEAD_NOTE UI 证据，**仍作「有证据、仍开」**——整项 Phase1 产品验收未全量关闭。
2. **RF-*** / **RF-8**（TASK_BOARD：合并前需用户确认截图）：**仍开**。
3. 其余 Phase1 **P1-***：**仍开**。
4. C-08 **仍禁止 --apply**（本闸未触碰）。

### 收尾

- worktree：`D:\RubbingMind\wt\qa-report` @ `b200567`（detach）
- **未**改业务代码、**未**写主库、**未** push、**未** C-08 --apply。


## 合入后冒烟 tip@00a5c85（含 jinshi@ec70f56 + report@b200567）— RM-红队QA @ 2026-10-25 13:25 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach 至 tip `00a5c8575854d2231fc3e0d1b3298723370c53c0`；主仓 HEAD 同 tip；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非本进程。

**ancestry**：parents=`ec70f563b2e011e90017ca975fb98f8e9ddcf104` + `b200567e481c9b7259a73caee03efbbff642b2ba`；`merge-base --is-ancestor` 两者均为 exit 0。实际 HEAD **=** 目标 tip `00a5c85`（未再前进）。

### 结论：**通过**

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip / parents | **确认** | HEAD=`00a5c8575854d2231fc3e0d1b3298723370c53c0`；P=`ec70f56` + `b200567`；含两批 |
| 2 | 全量 pytest | **709 passed / 1 xfailed** | A24 已知 xfail；exit 0；~68s |
| 3 | G1 + Phase2 ROI | **21 passed** | `test_phase2_roi_fields` + `test_phase2_roi_arch`；含 `test_ts_glyph_inference_record_declares_roi_and_shas_g1` **PASSED** |
| 4 | Phase2 路由 | **ALL_200** | normalize / case-stele-mapping / roi-compare / glyph-evaluation 均 200；glyph-evaluation `status=not_evaluated` |
| 5 | claims / museum 抽样 | **205 passed** | `test_catalog_claims` + `test_claims_open_issues` + `test_museum_v3` |
| 6 | open-issues --check | **ok** | claimFiles=**28**；openRows=36；**conflict=20 仍开**；pendingHuman=30 |
| 7 | validate_museum_v3 | **passed** | items=28；images=84；sha256Match=**84/84** |
| 8 | npm run build | **通过** | `apps/web` tsc && vite build exit 0；built ~42.6s；chunk>500kB 警告（历史已知） |
| 9 | glyphEvaluationText | **禁伪 Top-k 成立** | `not_evaluated`+top1=0.99/top3=0.95 → 仅「未评测…」；**无** Top-1/数值泄漏；MECHANISM_HEAD_NOTE + `mechanism-head-lag-note` **仍在** |
| 10 | P1 / RF 关单 | **未关** | MATRIX/FINDINGS 本日无 P1/RF 关闭记录；本闸只追加冒烟结论 |
| 11 | 主库 SHA | **始=终不变** | PRE=POST `rubbingmind.sqlite=8408DBC3…323D` / `evidence-v2.sqlite=854DF859…ABD3` |

### 无 blocker / 仍开项（非本 tip 回归）

1. A24 正式 xfail（schema 未绑产品缺口）。
2. C-08 **仍禁止 `--apply`**；conflict 异文并列仍开项。
3. Phase1 **P1-*** / **RF-***：**仍开**（本闸有证据不关单）。
4. npm chunk >500kB 警告（历史已知）。

### 收尾

- 日志：`wt/qa-tmp/pytest-00a5c85.txt`、`pytest-g1-phase2-00a5c85.txt`、`pytest-claims-museum-00a5c85.txt`、`claims-open-00a5c85.txt`、`validate-museum-00a5c85.txt`、`phase2-routes-00a5c85.txt`、`npm-build-00a5c85.txt`、`sha-pre/post-00a5c85.txt`
- **未**改业务代码、**未**写主库、**未** push、**未**杀非本进程。

## 评测 tip 门禁 tip@9aa52b6（agent/eval-sci；基线 feature@0654d13）— RM-红队QA @ 2026-10-25 13:27 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-evalsci` detach 于 tip `9aa52b677ad4e0690cdffe6fa8d5247671b24816`；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非本进程。

**ancestry**：`merge-base --is-ancestor 0654d13 HEAD` = exit 0；`merge-base(0654d13, HEAD)` = `0654d13`。自 0654d13 起 4 commit：`40883f2`（ES-4）→ `0d14129`（ES-3/ES-5）→ `3e08545`（R7 开项纪要）→ `9aa52b6`（tip 门禁纪要）。

**注**：验收时主仓 `feature/product-grade-upgrade` 已前进至 `00a5c85`（已合 ec70f56+b200567）。本闸仍以 vs **0654d13** 为主；vs `00a5c85` merge-tree 亦干净（见下）。合入序按 Green：排在 feature 合完 ec70f56+b200567 **之后**。

### 结论：**可合并**

| # | 项 | 判定 | 证据 |
|---|---|---|---|
| 1 | tip / log -1 | **确认** | HEAD=`9aa52b677ad4e0690cdffe6fa8d5247671b24816`；subj=`docs(eval-sci): tip 3e08545 lag=125 vs mechanism head (gateable)`；Date 2026-10-25 13:16 +0800 |
| 2 | vs 0654d13 | **已含 / FF 祖先** | ancestor exit 0；commits since = 40883f2 + 0d14129 + 3e08545 + 9aa52b6 |
| 3 | merge-tree vs 0654d13 | **冲突 0** | `--write-tree` → `8818f58c…` exit 0；旧式 markers=0 |
| 4 | merge-tree vs feature@00a5c85（附注） | **冲突 0** | `--write-tree` → `81969a5e…` exit 0；Auto-merging `MechanismPanel.tsx`；**无**真实冲突 |
| 5 | 全量 pytest | **712 passed / 1 xfailed** | `python -m pytest -q`；68.56s；exit 0；日志 `wt/qa-tmp/pytest-9aa52b6.txt` |
| 6 | xfail = A24 | **确认** | `tests/test_phase2_glyph_candidate_assertions.py::test_a24_export_label_recognized_forbidden_until_schema_exists` — A24 schema 未实现 |
| 7 | G1 | **仍绿** | `test_phase2_roi_fields` + `test_phase2_roi_arch`（-k g1/roi）**21 passed**；正式 assert 未回退 xfail |
| 8 | ES-3 | **有证据** | commit `0d14129`：`summarize_lift_claims` / `may_claim_positive_lift` / `lift_claim_label` in `eval_export_contract.py` + `test_es3_*`；**未**重算 bootstrap CI |
| 9 | ES-4 | **有证据** | commit `40883f2`：`enrich_mechanism_captions.py`；images[] 含 batch/caseId/derivedAt/headCommit/sourcePath/captionNote；index `captionProvenance.pngBytesUntouched=true`；**R7 未重跑** |
| 10 | ES-5 | **有证据** | commit `0d14129`：`negative_lift_display` + `test_es5_*`；NLC 契约；**未**改写 NLC derived 文件 |
| 11 | museum_processing | **未改** | blob `60358fe70dfe5d41ab72f3be7bb760c273e5e5d3` 双 tip 相同；`git diff --name-only` 无 `museum_processing` |
| 12 | R7 | **仍开 / 勿关** | `MECHANISM_HEAD_NOTE` §7：headCommit=`7623a52`；tip 相对 head 仍落后；`pngBytesUntouched=true`；本闸**未**要求关闭、**未**重跑 `mechanism_cases.py` |
| 13 | 主库 SHA | **始=终不变** | PRE=POST `rubbingmind.sqlite=8408DBC3…323D` / `evidence-v2.sqlite=854DF859…ABD3` |

### 无 blocker / 仍开项（本闸不关）

1. **R7 / G7**：mechanism head=`7623a52` 落后 tip；只挂证据，**仍开**。
2. **A24**：正式 xfail（schema 未绑）。
3. C-08 **仍禁止 `--apply`**；conflict 异文并列仍开。
4. Phase1 **P1-*** / **RF-***：**仍开**。

### 收尾

- 日志：`wt/qa-tmp/pytest-9aa52b6.txt`、`pytest-g1-9aa52b6.txt`、`merge-tree-9aa52b6-vs-0654d13.txt`、`merge-tree-9aa52b6-vs-00a5c85.txt`、`sha-pre/post-9aa52b6.txt`
- **未**改业务代码、**未**写主库、**未** push、**未** C-08 --apply、**未**杀非本进程。


## 架构 tip 门禁 tip@3d7239c（AB-8 / RT-002/003/004 + SPEC §12/§13；基于 feature@00a5c85）— RM-红队QA @ 2026-10-25 13:30 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-arch` detach 至 tip `3d7239cb60394cb3f9279c6b1ea86ceddb92c34f`；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非本进程。

**ancestry**：`merge-base --is-ancestor 00a5c8575854d2231fc3e0d1b3298723370c53c0 HEAD` = exit 0；增量 2 commit：`f894760`（AB-8 P1 backend + RT-002/003/004）→ `3d7239c`（SPEC Phase2 ROI field bag + AB-8 /health samples）。

### 结论：**可合并**

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip SHA | 3d7239cb60394cb3f9279c6b1ea86ceddb92c34f | docs(spec) + AB-8；parent=
894760 |
| 2 | vs feature@00a5c85 | **已含 / 基于** | ancestor exit 0；`00a5c85..HEAD` = f894760 + 3d7239c |
| 3 | merge-tree vs 00a5c85 | **冲突 0** | `git merge-tree --write-tree` → `aacd9705…` exit 0；conflict markers=0 |
| 4 | RT-002 samples/health | **有代码+测试证据** | `sample_generator.check_samples` 明确 Never download/synth/write；`ensure_samples` 只报 present；`main.py` `/health` 暴露 `status/samples_missing/samples_sha_mismatch`；`tests/test_rt002_samples.py` 4 测（含 health degraded） |
| 5 | RT-003 拒默认端口 + browser_target | **有代码+测试证据** | `scripts/browser_target.py` `FORBIDDEN_PORTS={8000,5180}`；`assert_safe_target` SystemExit(2)；browser 脚本已接入；`start.ps1 -Port` 可显式指定；`tests/test_rt003_browser_ports.py` 禁口拒 / 安全口过 |
| 6 | RT-004 conftest/tmp | **有代码+测试证据** | `tests/conftest.py` autouse 把 `RUBBINGMIND_*` 指到 pytest tmp；`validate_stele_asset.run(report_path=None)` 不写 tracked `asset-validation.json`；`tests/test_rt004_validate_no_tracked_write.py` 2 测 |
| 7 | SPEC §12 / §13 | **有文档证据** | `REPORT_DATA_SPEC.md` §12 Phase2 ROI 持久化字段袋（R2–R6/R8）；§13 `/health` 样本完整性字段（AB-8/RT-002）并交叉引用 RT-003/004 |
| 8 | Phase2+RT 子集 | **35 passed** | `test_rt002/003/004` + `test_phase2_roi_fields/arch`；RT 单独 collect=**14** |
| 9 | 全量 pytest | **723 passed / 1 xfailed** | 与声称一致；xfail=A24（export schema label 未实现，已知） |
| 10 | museum_processing / claims | **未改史实** | tip diff 无 museum_processing 内核 / claims JSON；仅 `scripts/test_museum_assessment_browser.py` 浏览器脚本改端口护栏 |
| 11 | C-08 | **未 apply** | 本闸未触碰 apply；仍禁 |
| 12 | 主库 SHA | **始=终不变** | PRE=POST `rubbingmind.sqlite=8408DBC3…323D` / `evidence-v2.sqlite=854DF859…ABD3` |

### 非 blocker / 仍开项（有证据可注明缓解，仍勿无依据关单）

1. **RT-002 / RT-003 / RT-004**：本 tip 有实现+测试证据 → 记「有证据缓解」；MATRIX 中与之关联的 D-03/P5-9 等历史行 **仍开**（整项产品验收未全关）。
2. **A24** 正式 xfail（schema 缺口）— 非本 tip 引入。
3. **C-08 仍禁 --apply**；conflict 异文并列仍开。
4. `start.bat` / `start.ps1` 无 `-Port` 时仍可落到用户默认 8000 段——**符合**「用户/开发默认口」语义；RT-003 护的是 **browser/smoke 脚本拒用** 这些口，已成立。

### 收尾

- 日志：`wt/qa-tmp/pytest-full-3d7239c.txt`、`pytest-phase2-rt-3d7239c.txt`、`spec-12-13-3d7239c.txt`、`sha-pre/post-3d7239c.txt`
- **未**改业务代码、**未**写主库、**未** push、**未** C-08 --apply、**未**杀非本进程。

## 合入后冒烟 tip@c761d54（feature = 8a266b4 + AB-8@3d7239c）—— RM-红队QA @ 2026-10-25 13:34 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach 至 tip `c761d546794c428a29c1a1e0f73c55c464d092cf`；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非本进程。

**ancestry**：parents = `8a266b450c0618530b4e9e716b2290f7022eb867` + `3d7239cb60394cb3f9279c6b1ea86ceddb92c34f`；`merge-base --is-ancestor` 对 8a266b4 / 3d7239c / 9aa52b6 均为 exit 0。subj=`Merge commit '3d7239c…' into feature/product-grade-upgrade`。**验的是 c761d54（含 AB-8）**。

### 结论：**通过**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip / parents | **确认** | HEAD=$tip；parents=8a266b4 + 3d7239c |
| 2 | 含 AB-8 | **是** | ancestor 3d7239c exit 0；/health 暴露 samples_missing / samples_sha_mismatch |
| 3 | 全量 pytest | **726 passed / 1 xfailed** | 63.62s；exit 0；日志 `wt/qa-tmp/pytest-c761d54.txt` |
| 4 | xfail = A24 | **确认** | `test_a24_export_label_recognized_forbidden_until_schema_exists`（schema 未实现，已知） |
| 5 | G1 | **正式绿** | `-k "roi or g1"` → **21 passed**；glyph assertions 14p+1xfail(A24) |
| 6 | Phase2 + RT | **49 passed / 1 xfailed** | ROI fields/arch + glyph + RT002/003/004 |
| 7 | RT-002/003/004 抽样 | **14 passed** | collect 4+8+2；health samples_* 字段存在且 status=healthy |
| 8 | ES-3/4/5 抽样 | **23 passed** | `-k "es3 or es4 or es5 or test_es"` |
| 9 | claims/museum | **通过** | pytest 205p；`check_claims_open_issues --check` ok（claimFiles **28/28**；**conflict 20 仍开**）；validate_museum_v3 **84/84** sha256Match |
| 10 | npm run build | **通过** | apps/web `tsc && vite build` exit 0（chunk>500kB 警告，历史已知） |
| 11 | Phase2 路由抽样 | **后端仍在** | /health 200；/api/glyph-evaluation 200；roi-geometry/normalize 无参 422（路由在）；roi-compare 模板 404 |
| 12 | P1/RF/R7/A24/conflict | **未关单** | conflict=20；A24 仍 xfail；MECHANISM_HEAD_NOTE headCommit=7623a52 仍落后（R7 仍开）；本闸未要求关闭 |
| 13 | 主库 SHA | **始=终不变** | PRE=POST `rubbingmind.sqlite=8408DBC3…323D` / `evidence-v2.sqlite=854DF859…ABD3` |

### 无 blocker / 仍开项（门禁不挡）

1. **A24** 正式 xfail（export schema 缺）。
2. **R7 / G7**：mechanism head=7623a52 落后 tip；只留证据，**仍开**。
3. **C-08** 仍禁止 `--apply`；conflict 异文并列仍开。
4. Phase1 **P1-*** / **RF-***：**仍开**（本闸未关单）。
5. npm chunk >500kB 警告（历史已知）。

### 收尾

- 日志：`wt/qa-tmp/pytest-c761d54.txt`、`pytest-g1-phase2-rt-c761d54.txt`、`pytest-es-c761d54.txt`、`pytest-claims-museum-c761d54.txt`、`claims-open-c761d54.txt`、`validate-museum-c761d54.txt`、`pytest-rt-c761d54.txt`、`phase2-routes-c761d54.txt`、`npm-build-c761d54.txt`、`sha-pre/post-c761d54.txt`
- **未**改业务代码、**未**写主库、**未** push、**未** C-08 --apply、**未**杀非本进程。


## 架构 tip 门禁 tip@12fc96e（RT-005/007/009/011 + RT-006 部分；相对 feature@c761d54）—— RM-红队QA @ 2026-10-25 13:54 Asia/Shanghai

**范围**：只读 worktree D:\RubbingMind\wt\qa-arch detach 到 tip 12fc96ee5d9b02965efd9f91a35aa6d454066b39（相对 feature@c761d546794c428a29c1a1e0f73c55c464d092cf）。**未**改业务代码；**未** push/commit/merge；**未**写主库；**未** C-08 --apply；**未**杀非本进程；**未**动 qa-report（并行审 0301aad）。

**ancestry**：merge-base --is-ancestor c761d54 tip exit 0；c761d54..tip = 单提交 12fc96e fix(security): RT-005/007/009/011 + RT-006 partial mitigations。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip | **确认** | HEAD=12fc96ee5d9b02965efd9f91a35aa6d454066b39 |
| 2 | merge-tree vs c761d54 | **冲突 0** | git merge-tree --write-tree → c8894c1892b2fbf99b1fa1e6904742cab02c270b；conflict markers=0 |
| 3 | museum_processing | **未改** | blob 同 c761d54：60358fe70dfe5d41ab72f3be7bb760c273e5e5d3 |
| 4 | 变更面 | **10 文件** | .env.example / catalog_assessment.py / check.ps1 / ADR_R2_SUPPLEMENT.md / main.py /
untime_guard.py / start.ps1 + 3 新测 |
| 5 | RT-005 | **有缓解证据；产品单仍开** | SecurityHeadersMiddleware（nosniff/XFO/CSP）；remote 关 docs/redoc/openapi |
| 6 | RT-006 | **仅部分缓解；勿标全关** | 无 dist 时 /→503
rontend_build_required，不再回退 static/index.html；CDN/SRI/localStorage 等仍开 |
| 7 | RT-007 | **有缓解证据；产品单仍开** | .env.example 对齐 RUBBINGMIND_* 实读键 |
| 8 | RT-009 | **有缓解证据；产品单仍开** | client_is_trusted_local 拒绝 XFF/Forwarded；
eview_allowed 传 headers |
| 9 | RT-011 | **有缓解证据；产品单仍开** | start.ps1/check.ps1 仅 GET /api/health（不再 POST /generate） |
| 10 | RT-008/010/013 | **仍开** | 本 tip 未触及 |
| 11 | 12p+17p 复验 | **12 passed + 17 passed** | 见下方命令 |
| 12 | npm build | **跳过** | tip diff 无 pps/web / 前端资产 |
| 13 | 启服 smoke | **跳过** | 127.0.0.1:8000 已被 PID 68284 占用；不杀他人进程；TestClient 已覆盖 |
| 14 | 主库 SHA | **始=终不变** | rubbingmind=8408DBC3…323D；evidence-v2=854DF859…ABD3 |
| 15 | 产品 RT 关单 | **未关** | RT-005/006/007/009/011 仅记缓解；008/010/013 仍开 |

### 12p+17p 复验命令与数字

- **12p（本 tip 新测）**：python -m pytest tests/test_rt005_security_headers.py tests/test_rt006_007_011_scripts_env.py tests/test_rt009_proxy_headers.py -v → **12 passed**（3.63s）。日志：wt/qa-tmp/qa-arch-tmp/rt-12p.log
- **17p（相关既有）**：	est_api::test_health_endpoint + 	est_history_graph::test_health_then_generate + 	est_retired_no_coordinates[/api/health] + 	est_rt002_samples + 	est_rt003_browser_ports + 	est_rt004_validate_no_tracked_write → **17 passed**（2.82s）。日志：wt/qa-tmp/qa-arch-tmp/rt-17p.log

### 无 blocker / 仍开项（不挡本闸可合并）

1. **RT-005/007/009/011**：有代码+测试缓解证据 → 「验证待回填」；**产品单仍开**。
2. **RT-006**：仅部分缓解（无 dist→503）；全删 static / CDN SRI / localStorage 等 **仍开**，**勿标全关**。
3. **RT-008 / RT-010 / RT-013**：**仍开**（本 tip 未改）。
4. **C-08**：仍禁止 --apply。

### 收尾

- 日志：wt/qa-tmp/qa-arch-tmp/rt-12p.log、
t-17p.log、sha-pre-post-12fc96e.txt
- **未**改业务代码、**未**写主库、**未** push、**未** C-08 --apply、**未**杀非本进程、**未**关产品 RT 单。
## 报告 tip 门禁 tip@0301aad（P1-4 MechanismPanel captionNote + slice7 证据）相对 feature@c761d54；作者 RM-红队QA @ 2026-10-25 13:56 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-report` detach → tip `0301aad3369a27ee27d31e17ebde90fc98c8b820`；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非本任务进程。

**ancestry**：`merge-base(c761d54, 0301aad)=c761d54` → **fast-forward**；subj=`feat(reports): P1-4 show mechanism image captionNote (ES-4)`；单文件 `apps/web/src/components/reports/MechanismPanel.tsx`。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip / 相对 c761d54 | **确认** | tip=`0301aad3369a27ee27d31e17ebde90fc98c8b820`；base=`c761d546794c428a29c1a1e0f73c55c464d092cf`；agent/report-frontend @ 0301aad |
| 2 | merge-tree | **冲突 0** | FF；figcaption +`{img.captionNote ? …}` |
| 3 | P1-4 captionNote | **有代码证据，未关单** | MechanismPanel.tsx L201；types.ts `captionNote?: string`；slice7 `p1-4-captionNote-evidence.txt` |
| 4 | slice7 / P1-9 Playwright 首屏 | **有路径证据，未重跑全量，未关单** | `D:\RubbingMind\screenshots\product-upgrade\phase1-frontend\slice7\p1-9_reports_firstscreen_1920x1080.png`（789166） / `_1440x900.png`（578028）；`slice7-verify.json` ok=true；笔记 `wt/rm-report-frontend/phase1-frontend/slice7/`（未跟踪） |
| 5 | RF-8 / Phase1 | **仍开** | inventory 明确 RF-8 待用户确认；门禁**未关** P1/RF |
| 6 | pytest ES-4 contracts | **17 passed** | `test_es_derived_contracts.py`；日志 `wt/qa-tmp/pytest-es-0301aad.txt` |
| 7 | pytest 窄抽样 | **254 passed** | `-k es3/es4/es5/test_es/caption/mechanism/claim/museum`；`wt/qa-tmp/pytest-narrow-0301aad.txt` |
| 8 | npm run build | **通过** | exit 0；`wt/qa-tmp/npm-build-0301aad.txt`；chunk>500kB 警告已知 |
| 9 | 主库 SHA | **始=终不变** | PRE=POST `8408DBC3…323D` / `854DF859…ABD3` |

### 无 blocker / 仍开项（门禁通过不关单）

1. **P1-4 / P1-9 / 其余 Phase1 P1-***：本 tip 仅补 captionNote 展示 + 首屏截图证据 → **有证据、仍开**。
2. **RF-8**：需用户截图确认 → **仍开**。
3. **R7 / A24 / C-08 / conflict**：与本 tip 无关，维持既有仍开/禁止项。
4. 本门禁**未**重跑 Playwright 全量（仅核对证据路径与 verify.json）。

### 收尾

- 日志：`wt/qa-tmp/pytest-es-0301aad.txt`、`pytest-narrow-0301aad.txt`、`npm-build-0301aad.txt`
- **未**改业务代码、**未**写主库、**未** push、**未** C-08 --apply、**未**关 RF-8/P1。

## 评测 tip 门禁 tip@5ba8bef（含交付 9eb8406；相对 feature@c761d54）· RM-红队QA @ 2026-10-25 13:59 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-evalsci` detach 到 tip `5ba8befd92f7507fcfcefba3e8f19a5992af99ae`；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非本进程。**未动**并行占用的 `qa-report` / `qa-arch`。

**ancestry**：`merge-base --is-ancestor 9eb8406 HEAD` = exit 0；`merge-base --is-ancestor c761d54 HEAD` = exit 0（FF 后代）。自 c761d54 起 2 commit：`9eb8406`（ES-3/5 交付）+ `5ba8bef`（docs stamp R7/ES tip）。

### 结论：**可合并**

| # | 项 | 判断 | 证据 |
|---|---|---|---|
| 1 | tip HEAD | **确认** | `5ba8befd92f7507fcfcefba3e8f19a5992af99ae`；subj=`docs(eval-sci): stamp R7/ES tip to 9eb8406 gate candidate` |
| 2 | 交付 tip 9eb8406 | **在 ancestry** | `9eb8406ba1a788a20dc88035fe2eef314afc7b9d`；feat ES-3 lift summary + ES-5 display companion |
| 3 | vs feature@c761d54 | **已含 / FF** | ancestor exit 0；log = 9eb8406 + 5ba8bef |
| 4 | merge-tree vs c761d54 | **冲突 0** | `--write-tree` → `4fccc2d3b356914dde3e7fb0c19ab6f2d9fd4b45` exit 0；trivial markers=0 |
| 5 | 全量 pytest | **730 passed / 1 xfailed** | `python -m pytest -q`；80.58s；exit 0；**对照其称 730p/1xfail 一致**；日志 `wt/qa-tmp/qa-eval-tmp/pytest-full-5ba8bef.txt` |
| 6 | xfail = A24 | **确认仍 xfail** | `tests/test_phase2_glyph_candidate_assertions.py::test_a24_export_label_recognized_forbidden_until_schema_exists` — schema 未实现；**未伪绿 / 未关单** |
| 7 | ES 子集 | **27 passed / 1 xfailed** | `-k "es3 or es4 or es5 or test_es or a24"`；日志 `pytest-es-5ba8bef.txt` |
| 8 | ES-3 | **有证据** | `export_lift_claim_summary.py` + `annotate_ci_lift_claims`（`eval_export_contract.py` / `experiment_derived.ci_by_artifact` API 注解 liftClaimLabel + liftClaimSummary）；产物 `experiments/results/2026-10-17-v2{,-text}/derived/lift_claim_summary.json`（claimCounts 含 positive_lift_ci_excludes_zero=35；**未重算 bootstrap**） |
| 9 | ES-5 | **有证据（slim）** | `export_negative_lift_display.py` + `negative_lift_display`；产物 `…/derived/negative_lift_display.json`（rowCount=747；行内无完整 measuredEvidence，仅 measuredEvidenceCount/triggeredMeasures/primaryMeasuredCauses；**未改写 NLC**） |
| 10 | ES-4 | **维持 / 未回退** | tip diff **未删** ES-4；`enrich_mechanism_captions.py` 仍在；mechanism `index.json` 仍有 `captionProvenance.pngBytesUntouched=true` + fields 含 `captionNote`；headCommit 仍 `7623a52` |
| 11 | docs stamp | **有** | `5ba8bef` 更新 `ES_EVAL_PROGRESS.md` / `MECHANISM_HEAD_NOTE.md` / `REVIEW_EVALSCI_ES_CONTINUATION.md`；注 tip→mechanism head **135** commits lag |
| 12 | museum_processing | **未改** | tip diff name-only 无 `museum_processing` |
| 13 | R7 / G7 | **仍开** | MECHANISM_HEAD_NOTE / ES_EVAL_PROGRESS：**仍开·勿关**；只挂证据；**未** replay `mechanism_cases.py`；**本门禁未关单** |
| 14 | 主库 SHA | **始=终不变** | PRE=POST `rubbingmind.sqlite=8408DBC3…323D` / `evidence-v2.sqlite=854DF859…ABD3` |

### 无 blocker / 仍开项（门禁不关）

1. **R7 / G7**：mechanism head=`7623a52` 落后 tip（文档记 135 commits）；只挂证据；**仍开**。
2. **A24**：正式 xfail（export schema 缺口）；**仍开 / 勿伪绿**。
3. C-08 **仍禁止 `--apply`**；conflict 人工项照常仍开。
4. Phase1 **P1-*** / **RF-***：本 tip 范围外；**仍开**（并行报告 tip 另审）。
5. worktree 预存脏文件 `screenshots/stele-final/asset-validation.json`（非 tip 内容；本门禁未改/未提交）。

### 收尾

- 日志：`wt/qa-tmp/qa-eval-tmp/pytest-full-5ba8bef.txt`、`pytest-es-5ba8bef.txt`、`pytest-a24-5ba8bef.txt`、`sha-pre/post-5ba8bef.txt`
- **未**改业务代码、**未**写主库、**未** push、**未** C-08 --apply、**未**杀非本进程、**未**关 R7/A24。



## 合入后冒烟 tip@4f57eb5（合入 arch@12fc96e + report@0301aad + eval@5ba8bef）—作者 RM-红队QA @ 2026-10-25 14:24 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach 于 tip `4f57eb5ef57cdcb702042ccaa23904dbafcf9648`；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非本进程。本条为前一执行器冒烟跑完后崩溃、未写文档的补写（以实测日志为准）。

**ancestry**：parents = `91aa16abb5b3f58680b80bbaf32b738a8b03fc05` + `5ba8befd92f7507fcfcefba3e8f19a5992af99ae`；`merge-base --is-ancestor` 对 12fc96e / 0301aad / 5ba8bef / 9eb8406 / 91aa16a 均为 exit 0。subj=`Merge commit '5ba8bef' into feature/product-grade-upgrade`。**验的是 4f57eb5（含 arch+report+eval）**。

### 结论：**通过**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip / parents | **确认** | HEAD=`4f57eb5ef57cdcb702042ccaa23904dbafcf9648`；parents=91aa16a + 5ba8bef |
| 2 | 含 arch/report/eval | **是** | ancestor 12fc96e / 0301aad / 5ba8bef / 9eb8406 均 exit 0 |
| 3 | 全量 pytest | **742 passed / 1 xfailed** | 163.88s；exit 0；日志 `wt/qa-tmp/qa-smoke-a7dc/pytest-full-4f57eb5.txt`；对照中间 tip 91aa16a 曾 738p/1xfail，合入 eval 后 +4 |
| 4 | xfail = A24 | **确认** | schema 未实现；**未伪绿 / 未关单** |
| 5 | G1 | **23 passed** | `pytest-g1-4f57eb5.txt` |
| 6 | RT-002..011 抽样 | **26 passed** | `pytest-rt-4f57eb5.txt` |
| 7 | Phase2+AB8 相关 | **36 passed / 1 xfailed** | `pytest-phase2-ab8-4f57eb5.txt` |
| 8 | ES 抽样 | **41 passed** | `pytest-es-4f57eb5.txt` |
| 9 | AB-8 /api/health | **通过** | status 200 healthy；keys 含 samples_missing / samples_sha_mismatch（皆 []）；samples_available 4；`ab8-health-4f57eb5.txt` |
| 10 | claims/museum | **通过** | `check_claims_open_issues --check` ok（claimFiles **28**；**conflict 20 仍开**）；validate_museum_v3 items **28** / images **84** / sha256Match **84** |
| 11 | npm run build | **通过** | exit 0；chunk>500kB 警告（历史已知）；`npm-build-4f57eb5.txt` |
| 12 | P1/RF/R7/A24/conflict/RT 产品单 | **仍开勿关** | 本闸未关单；A24 仍 xfail；conflict=20 |
| 13 | 主库 SHA | **始=终不变** | PRE=POST `rubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D` / `evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3`（终 SHA 复核一致） |

### 无 blocker / 仍开项（门禁不挡合）

1. **A24** 正式 xfail（export schema 缺）；**仍开 / 勿伪绿**。
2. **R7 / G7**：mechanism head 仍落后；只留证据，**仍开**。
3. **C-08** 仍禁止 `--apply`；conflict 异文并列仍开（20）。
4. Phase1 **P1-*** / **RF-***：**仍开**（本闸未关单）。
5. 产品 **RT-*** 单：**仍开**（缓解≠关单；RT-006 部分、RT-008/010/013 未解）。
6. npm chunk >500kB 警告（历史已知）。

### 收尾

- 日志：`wt/qa-tmp/qa-smoke-a7dc/pytest-full-4f57eb5.txt`、`pytest-g1-4f57eb5.txt`、`pytest-rt-4f57eb5.txt`、`pytest-phase2-ab8-4f57eb5.txt`、`pytest-es-4f57eb5.txt`、`ab8-health-4f57eb5.txt`、`validate-museum-4f57eb5.txt`、`claims-open-4f57eb5.*`、`npm-build-4f57eb5.txt`、`sha-post-4f57eb5.txt`
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未**杀非本进程；**未**关 P1/RF/R7/A24/conflict/RT 产品单。
## 评测 tip 门禁 tip@89ff1db（docs：R7 lag=141；相对 feature@4f57eb5）—— RM-红队QA @ 2026-10-25 14:33 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-evalsci` checkout tip `89ff1db7d066b3c6f49bf63729dbef08365d9f82`；相对 feature@4f57eb5。未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非本进程。

**宣称**：MECHANISM_HEAD_NOTE / ES_EVAL_PROGRESS 证据更新；未重跑机制；A24 仍 xfail；R7 lag=141。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip HEAD | **确认** | `89ff1db7d066b3c6f49bf63729dbef08365d9f82`；subj=`docs(eval-sci): stamp R7 lag=141 after FF feature@4f57eb5`；`4f57eb5..89ff1db` = **1** commit |
| 2 | vs feature@4f57eb5 | **已合 / FF** | merge-base = base；merge-tree 冲突 **0** |
| 3 | 是否仅文档 | **是** | 仅 `docs/product-upgrade/ES_EVAL_PROGRESS.md`、`docs/product-upgrade/MECHANISM_HEAD_NOTE.md`（2 files, +20/−5）；**无**非 docs / 无 test / 无业务代码变更 |
| 4 | R7 lag=141 | **有证据** | `git rev-list --count 7623a52..4f57eb5` = **141**（文档记 feature tip 滞后）；stamp tip HEAD 为 142（+1 docs commit，预期）；MECHANISM_HEAD_NOTE §9 / ES_EVAL_PROGRESS 表均写 **141** |
| 5 | R7 / G7 仍开 | **确认** | 文案「**仍开项** — 只记证据，未谎关；未重跑 mechanism_cases.py」；ES 表状态「开」；**无**伪绿/关单措辞 |
| 6 | A24 仍 xfail | **确认** | tip diff **无** test/xfail 变更；源码仍 `pytest.xfail("A24: ...")`；可选 `pytest -k a24` → **1 passed / 1 xfailed**（exit 0）；**未**把 xfail 改 pass |
| 7 | 全量 pytest | **跳过** | docs-only，未全量；记「docs-only，未全量」 |
| 8 | 主库 SHA | **始=终不变** | PRE=POST `rubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D` / `evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3` |

### 无 blocker / 仍开项（门禁不关单）

1. **R7 / G7** — mechanism head `7623a52` 滞后只记证据；**仍开 / 勿关单**。
2. **A24** — 正式 xfail；schema 缺口；**仍开 / 勿伪绿**。
3. 产品 RT / P1 / RF / conflict 等开项本 tip 未触及，**仍开**。

### 收尾

- 日志：`wt/qa-tmp/qa-eval-89ff1db/pytest-a24-89ff1db.txt`、`merge-tree.txt`
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未**关 R7/A24 产品单。

## 架构 tip 门禁 tip@7d5f333（RT-008/010/013 + RT-006 remaining；相对 feature@063e0e3）—— RM-红队QA @ 2026-10-25 14:39 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-arch` detach → tip `7d5f333c650fddbeced5cb9ddf63c3c0beae07a4`；相对 **feature@063e0e392d5c4b729d6152bbcee715ca2db02deb**（含已合入的 eval@89ff1db）。**未**改业务代码；**未** push/commit/merge；**未**写主库；**未** C-08 --apply；**未**杀非本进程；**未**关产品 RT 单；**未**动 `qa-evalsci`。

**范围摘要**：RT-008 vite/bind/audit；RT-010 CI 草案 + 正式 `ci.yml` 最小触发扩展；RT-013 `delete_run` soft-delete；RT-006 决策文档（仍留 `static/index.html`）。

### 结论：**有条件可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip HEAD | **确认** | `7d5f333c650fddbeced5cb9ddf63c3c0beae07a4`；subj=`fix(security): RT-008/010/013 mitigations + RT-006 remaining decision doc` |
| 2 | vs feature@063e0e3 | **可合 / 需 rebase 底** | ahead **1** / behind **2**（89ff1db + merge 063e0e3）；merge-base=`4f57eb5`；merge-tree 冲突 **0** |
| 3 | vs 4f57eb5（对照） | 冲突 **0** / ahead 1 | 原 base；museum_processing blob 与 063e0e3 相同（`60358fe`） |
| 4 | museum_processing | **仅 soft-delete 路径** | 新增 `trash_runs_root` / `_glyph_references_to_run` / `restore_run`；改写 `delete_run`（`shutil.rmtree`→`shutil.move` + trash marker）；**无**其它业务路径改动。`main.py` DELETE 路由配套 409 `run_referenced` |
| 5 | RT-008 | **有缓解证据；产品单仍开** | vite 锁 `6.4.5`；`server/preview.host=127.0.0.1` + npm scripts `--host 127.0.0.1`；`npm audit --omit=dev`=**0**；full audit **3 moderate**（tailwind/postcss-selector-parser，书面接受，见 `RT008_VITE_AUDIT.md`） |
| 6 | RT-010 | **有缓解证据；产品单仍开** | 草案 `ci-feature.draft.yml` **不在** `.github/workflows/`；正式 `ci.yml` **已**扩 `feature/**`（相对 Green「非正式 workflow」口径有正式改动→条件） |
| 7 | RT-013 | **有缓解证据；产品单仍开** | soft-delete→`runtime/trash/runs`；引用拒绝；`restore_run` 可恢复；文档写明未关单 |
| 8 | RT-006 | **有决策文档；仍留 static；产品单仍开** | `RT006_STATIC_INDEX_DECISION.md`；`static/index.html` **仍存在**（90717 bytes）；未全删 |
| 9 | pytest `test_rt008_010_013` | **5 passed** | 实测 exit 0；日志 `wt/qa-tmp/qa-arch-7d5f333/pytest_rt008_010_013.txt` |
| 10 | 既有 RT 回归 | **26 passed** | rt002/003/004/005/006_007_011/009；日志 `pytest_rt_prev_security.txt` |
| 11 | 全 `test_rt*` | **31 passed** | 日志 `pytest_all_rt.txt` |
| 12 | 声称 13p+28p | **未定位原文；按实测记** | tip 提交信息/决策文档未写「13p+28p」。实测：`npm run test:url`=**13 passed**；新测 5p；既有 RT 26p；全 RT 31p |
| 13 | npm 前端 | **通过（含已知 moderate）** | `test:url` 13p；audit omit=dev 0；3 moderate 与 RT008 文档一致 |
| 14 | 主库 SHA | **始=终不变** | `rubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D` / `evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3` |
| 15 | museum SHA | **只读未改库** | `museum_database.json=6F03EE46432E462EF0018C0CEACCD642D8F3306045E9F96525D59A46CF6E9B30`；processing tip blob `818065d` |

### 条件（合入前需 Green 拍板）

1. **正式 `.github/workflows/ci.yml`** 已改 `feature/**` 触发——相对派单「CI 草案 / 非正式 workflow」有正式 workflow 触达；ADR_R2_SUPPLEMENT 已自述「最小触发扩展」。需 Green 确认可接受，否则应回退正式 ci.yml、仅保留 docs 草案。
2. 合入前以 **feature@063e0e3** 为底 merge/rebase（behind 2，冲突 0；feature 侧 ES docs 与 tip 并存，merge-tree 干净）。

### 无 blocker 项（产品仍开，勿关单）

- 产品 **RT-008 / RT-010 / RT-013 / RT-006**：**仍开**（本 tip 仅缓解/决策文档）。
- RT-008 剩余 3 moderate（tailwind 链）：书面接受，待 tailwind v4 或 backport。
- RT-006 全删 `static/index.html`：等 Green 选 A/B/C。

### 收尾

- 日志：`wt/qa-tmp/qa-arch-7d5f333/`（pytest_rt008_010_013 / pytest_rt_prev_security / pytest_all_rt / npm_audit_* / npm_test_url）
- **未**改业务代码、**未**写主库、**未** push、**未** C-08 --apply、**未**关产品 RT 单。


## 合入后冒烟 tip@063e0e3（合入 eval@89ff1db docs stamp）—作者 RM-红队QA @ 2026-10-25 14:41 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach 到 tip `063e0e392d5c4b729d6152bbcee715ca2db02deb`；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非本进程；**未动** `qa-arch`（并行门禁 7d5f333）。相对 `4f57eb5` 仅 docs 2 files（MECHANISM_HEAD_NOTE / ES_EVAL_PROGRESS），窄冒烟：全量 pytest + claims/museum/health/SHA。

**ancestry**：parents = `4f57eb5ef57cdcb702042ccaa23904dbafcf9648` + `89ff1db7d066b3c6f49bf63729dbef08365d9f82`；`merge-base --is-ancestor 89ff1db` exit 0。subj=`Merge commit '89ff1db' into feature/product-grade-upgrade`。**验的是 063e0e3（含 eval docs stamp）**。

### 结论：**通过**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip / parents | **确认** | HEAD=`063e0e392d5c4b729d6152bbcee715ca2db02deb`；parents=4f57eb5 + 89ff1db |
| 2 | 含 89ff1db | **是** | ancestor exit 0；diff vs 4f57eb5 = 仅 2 docs files +20/−5 |
| 3 | 全量 pytest | **742 passed / 1 xfailed** | 71.16s；exit 0；对照 tip@4f57eb5 **同量级**（742p/1xfail）；日志 `wt/qa-tmp/qa-smoke-063e0e3/pytest-full-063e0e3.txt` |
| 4 | xfail = A24 | **确认** | `pytest -k a24` → 1 passed / 1 xfailed；**未伪绿 / 未关单** |
| 5 | AB-8 /api/health | **通过** | status 200 healthy；samples_missing=[]；samples_sha_mismatch=[]；samples_available 4；`ab8-health-063e0e3.txt` |
| 6 | claims/museum | **通过** | `check_claims_open_issues --check` ok（claimFiles **28**；**conflict 20 仍开**；openRows=36）；validate_museum_v3 items **28** / images **84** / sha256Match **84** |
| 7 | G1 / RT / ES / npm | **本轮窄冒烟跳过** | docs-only 合入；全量已与 4f57eb5 同量级；前一 tip@4f57eb5 已绿（G1 23p / RT 26p / ES 41p / npm build ok） |
| 8 | P1/RF/R7/A24/conflict/RT 产品单 | **仍开勿关** | MECHANISM_HEAD_NOTE / ES_EVAL_PROGRESS 文案「仍开·勿关」；A24 仍 xfail；conflict=20 |
| 9 | 主库 SHA | **始=终不变** | PRE=POST `rubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D` / `evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3` |

### 无 blocker / 仍开项（门禁不挡合）

1. **A24** 正式 xfail（export schema 缺）；**仍开 / 勿伪绿**。
2. **R7 / G7**：mechanism head 仍落后；只留证据；**仍开**。
3. **C-08** 仍禁止 `--apply`；conflict 异文并列仍开（20）。
4. Phase1 **P1-*** / **RF-***：**仍开**（本闸未关单）。
5. 产品 **RT-*** 单：**仍开**（缓解≠关单）。

### 收尾

- 日志：`wt/qa-tmp/qa-smoke-063e0e3/pytest-full-063e0e3.txt`、`pytest-a24-063e0e3.txt`、`ab8-health-063e0e3.txt`、`claims-check-063e0e3.txt`、`claims-open-063e0e3.json`、`validate-museum-063e0e3.txt`、`sha-pre/post-063e0e3.txt`
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未**杀非本进程；**未**关 P1/RF/R7/A24/conflict/RT 产品单；**未动** qa-arch。

## 合入后冒烟 tip@b60d556（合入 arch@7d5f333；含 RT-008/010/013）—作者 RM-红队QA @ 2026-10-25 14:49 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach 到 tip `b60d55697d741682d28af5f28319e2b84aca8230`；未改业务代码；无 push/commit/merge；未写主库；无 C-08 --apply；未杀非本进程。

**ancestry**：parents = `063e0e392d5c4b729d6152bbcee715ca2db02deb` + `7d5f333c650fddbeced5cb9ddf63c3c0beae07a4`；`merge-base --is-ancestor 7d5f333` / `063e0e3` exit 0。subj=`Merge commit '7d5f333c650fddbeced5cb9ddf63c3c0beae07a4' into feature/product-grade-upgrade`。相对 063e0e3：12 files / +657/-147（ci.yml / vite / RT docs / main.py soft-delete / museum_processing / test_rt008_010_013）。

### 结论：**通过**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip / parents | **确认** | HEAD=`b60d55697d741682d28af5f28319e2b84aca8230`；parents=063e0e3 + 7d5f333 |
| 2 | 含 7d5f333 | **是** | ancestor exit 0 |
| 3 | 全量 pytest | **747 passed / 1 xfailed** | 75.62s；exit 0；对照 tip@063e0e3 的 742p/1xfail，**+5** = `test_rt008_010_013`；日志 `wt/qa-tmp/qa-smoke-b60d556/pytest-full-b60d556.txt` |
| 4 | xfail = A24 | **确认** | `pytest -k a24` → 1 passed / 1 xfailed；**未伪绿 / 未关单** |
| 5 | G1 | **23 passed** | `-k "roi or g1"`；`pytest-g1-b60d556.txt` |
| 6 | RT（含 008/010/013） | **31 passed** | rt002..009 + `test_rt008_010_013`（5p）；对照前 tip 26p；产品 RT 单**仍开** |
| 7 | Phase2+AB8 | **36p / 1xfail** | `-k "phase2 or ab8 or a24"`；A24 仍 xfail |
| 8 | ES 抽样 | **39 passed** | `-k "es3/es4/es5/es_derived/lift_claim/negative_lift/caption/mechanism_*"`（ES-3/4/5 主题；selector 略窄于历史 41，全量已覆盖） |
| 9 | claims/museum | **通过** | `check_claims_open_issues --check` ok（claimFiles **28**；**conflict 20 仍开**；openRows=36）；validate_museum_v3 items **28** / images **84** / sha256Match **84** |
| 10 | npm build | **通过** | `apps/web` `npm run build` exit 0（chunk>500kB 警告，同既往）；vite **^6.4.5** |
| 11 | /health AB-8 | **通过** | status 200 healthy；samples_missing=[]；samples_sha_mismatch=[]；samples_available 4 |
| 12 | RT-006 static/index.html | **仍留** | `static/index.html` **EXISTS** size=90717；未全删（决策文档口径） |
| 13 | P1/RF/R7/A24/conflict/RT 产品单 | **仍开勿关** | A24 仍 xfail；conflict=20；产品 RT-006/008/010/013 缓解≠关单 |
| 14 | 主库 SHA | **始=终不变** | PRE=POST `rubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D` / `evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3` |

### 无 blocker / 仍开项（门禁不挡合）

1. **A24** 正式 xfail（export schema 缺）；**仍开 / 勿伪绿**。
2. **R7 / G7**：mechanism head 仍落后；只留证据；**仍开**。
3. **C-08** 仍禁 `--apply`；conflict 异文并列仍开（20）。
4. Phase1 **P1-*** / **RF-***：**仍开**（本闸未关单）。
5. 产品 **RT-006/008/010/013** 等：**仍开**（本 tip 仅缓解/决策文档；static/index.html 仍留）。
6. 正式 `ci.yml` 已含 `feature/**`（合入自 7d5f333；产品 RT-010 仍开）。

### 收尾

- 日志：`wt/qa-tmp/qa-smoke-b60d556/`（pytest-full / g1 / rt / phase2-ab8 / es / a24 / ab8-health / claims-check / validate-museum / npm-build / sha-pre/post）
- **无**改业务代码；**无**写主库；**无** push；**无** C-08 --apply；**无**杀非本进程；**未关** P1/RF/R7/A24/conflict/RT 产品单。


## 报告 tip 门禁 tip@be5e43d（merge feature@b60d556 atop 32195ce ES-3/5 UI）—作者 RM-红队QA @ 2026-10-25 14:58 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-report` detach 到 tip `be5e43d4d2b7f7366027860086554d7a510a95b1`；相对 **feature@b60d556**；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非本进程；**未关** RF-8/P1。

**改派说明**：原派单 tip `32195ce`（相对 4f57eb5）已审半（7 commits / merge-tree vs 4f57eb5=0 / vs b60d556=0 / 证据与 testid 已核）；Green 改派后以 **be5e43d** 最终数字为准。

**ancestry**：parents = `32195ce0584bb63c9fd862c90802689d3bebf9c1` + `b60d55697d741682d28af5f28319e2b84aca8230`；subj=`merge(feature): product-grade-upgrade@b60d556 into report-frontend`；`merge-base --is-ancestor b60d556` exit 0；vs b60d556 ahead **8** / behind **0**（merge + 7 report commits：6ec5723…32195ce）。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip / parents | **确认** | HEAD=`be5e43d4d2b7f7366027860086554d7a510a95b1`；parents=32195ce + b60d556 |
| 2 | commits 范围（原批次） | **7 commits** | `6ec5723..32195ce`：types → ReportApi annotated → GlobalEvaluation → Chart → Print → ES-5 NLC → slice8 docs |
| 3 | merge-tree vs **4f57eb5**（原基线） | 冲突 **0** | exit 0；tree `f2c0735a…` |
| 4 | merge-tree vs **b60d556**（当前 feature） | 冲突 **0** | exit 0；tree `f2c0735a…`；已含 merge commit |
| 5 | 相对 b60d556 变更 | **7 files / +161/-24** | FailureCasesPanel / GlobalEvaluation / MethodComparisonChart / ReportPrintLayout / reportData.ts / types.ts / `phase1-frontend/slice8/evidence.txt` |
| 6 | annotated → 禁伪「提升」 | **有证据** | `reportData.ts` prefer `GET /api/experiments/{id}/ci-by-artifact`；`mayClaimPositiveLift`：仅 `positive_lift_ci_excludes_zero` 或（无禁标时 CI 下界>0 ∧ reliable ∧ n≥3）；`no_positive_lift_claim`/未评估 → false；pos/neg 结论与图表色/打印均经该门禁；`liftClaimDisplay`/`gainWord` 非门禁不得写「提升」 |
| 7 | testid lift-claim-* / nlc-* | **存在** | `lift-claim-label` / `lift-claim-summary` / `lift-claim-count-*` / `lift-claim-rule`；`nlc-source` / `nlc-measured-primary` / `nlc-rule-inferred` |
| 8 | slice8 证据 | **存在** | `phase1-frontend/slice8/evidence.txt`（2657 bytes）；无独立截图目录（证据为路径+字段对照；可选 curl 本轮跳过） |
| 9 | RF-8 | **仍开 · 勿关** | HomePage / api.ts / App.tsx / urlState.ts **相对 b60d556 未改**；`object-contain` 仍在 HomePage L245/L250；TASK_BOARD RF-8=进行中（合并前等用户确认截图） |
| 10 | npm build | **通过** | `apps/web` `npm run build` exit 0（~52s）；ReportsPage chunk `ReportsPage-jCRIk9pL.js`；chunk>500kB 警告同既往 |
| 11 | npm test:url | **13 passed** | exit 0 |
| 12 | ES pytest 抽样 | **12 passed** | `tests/test_es_derived_contracts.py` -k es3/es5/lift_claim/negative_lift/annotate；0.39s |
| 13 | 主库 SHA | **始=终不变** | PRE=POST `rubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D` / `evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3` |

### 非 blocker / 仍开项（门禁不挡合）

1. **RF-8** / Phase1 **P1-***：**仍开**（本 tip 明确未改 HomePage；勿关单）。
2. slice8 **无截图文件**（仅 `evidence.txt`）；UI 回归依赖 testid + 代码门禁 + 后端 ES 契约测。
3. ES-5 GAP（证据自述）：无独立 `negative_lift_display` HTTP 路由；UI 经既有 NLC derived 字段镜像（与 feature 契约一致）。
4. 产品 **RT-*** / **R7** / **A24** / **conflict**：**仍开**（本闸未触）。

### 收尾

- 日志：`wt/qa-tmp/qa-report-32195ce/`（npm-build-be5e43d / npm-test-url-be5e43d / pytest-es-be5e43d / sha-be5e43d）
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未**关 RF-8/P1。

## 评测 tip 门禁 tip@cc1e1da（docs：R7 lag=145；相对 feature@b60d556）—— RM-红队QA @ 2026-10-25 14:59 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-evalsci` detach 到 tip `cc1e1dadc679b87a64034b6d4fbf2b2559cc46b2`；相对 feature@b60d556；**未动** `qa-report`（并行审 be5e43d）；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非自己进程。

**宣称**：MECHANISM_HEAD_NOTE / ES_EVAL_PROGRESS 证据更新（§10 / R7 开项表）；**未重跑** mechanism；A24 仍 xfail；R7 lag=145。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip HEAD | **确认** | `cc1e1dadc679b87a64034b6d4fbf2b2559cc46b2`；subj=`docs(eval-sci): stamp R7 lag=145 after FF feature@b60d556`；parent=`b60d55697d741682d28af5f28319e2b84aca8230`；`b60d556..cc1e1da` = **1** commit（ahead 0/1） |
| 2 | vs feature@b60d556 | **已合 / FF 可合** | merge-base = base；`merge-tree --write-tree` 冲突 **0**（tree `1d87889e80bb11a3d448b64e69d6527f1d5193d2`） |
| 3 | 是否仅文档 | **是** | 仅 `docs/product-upgrade/ES_EVAL_PROGRESS.md`、`docs/product-upgrade/MECHANISM_HEAD_NOTE.md`（2 files, +19/-4）；**无** 非 docs / 无 test / 无业务代码 / 无 museum_processing |
| 4 | R7 lag=145 | **有证据** | `git rev-list --count 7623a52..b60d556` = **145**；MECHANISM_HEAD_NOTE §6/§10 与 ES_EVAL_PROGRESS「R7 / A24 开项」均记 **145** 且文案 **仍开·勿谎关**；**未重跑** `mechanism_cases.py` |
| 5 | A24 | **仍 xfail / 勿伪绿** | 源码 `test_a24_export_label_recognized_forbidden_until_schema_exists` 仍 `pytest.xfail(...)`；抽样 `pytest` → **1 passed / 1 xfailed**（`test_a24_schema_still_absent_keep_xfail_evidence` passed）；日志 `wt/qa-tmp/qa-eval-cc1e1da/pytest-a24.txt` |
| 6 | 全量 pytest | **跳过（docs-only）** | 与 tip@b60d556 冒烟同基线（747p/1xfail）；本 tip 无代码/测试改动 |
| 7 | R7 / A24 产品单 | **仍开 / 未关** | 文档明确「仍开」「xfail 保持」「勿谎关」「勿把 A24 改成正式 assert」 |
| 8 | 主库 SHA | **始=终不变** | `rubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D` / `evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3`（与期望 8408DBC3…323D / 854DF859…BABD3 一致） |

### 无 blocker / 开项（门禁结论之上）

1. **R7 / G7**：mechanism head 仍绑 `7623a52`，tip 超前 **145**；只记证据，**勿关单**。
2. **A24**：正式 xfail；export schema 缺口；**勿伪绿 / 勿关单**。
3. 本 tip **无** 产品行为变更；合入后冒烟可窄（docs-only）。

### 收尾

- 日志：`wt/qa-tmp/qa-eval-cc1e1da/`（merge-tree-raw / r7-lag / pytest-a24 / sha-post / tip docs 摘录）。
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未**杀非自己进程；**未关** R7/A24；**未动** `qa-report`。

## 报告 tip 门禁 tip@ffb9138（相对 be5e43d：P1-11/P1-8/DER 文案 + slice9；vs feature@c027714）—— RM-红队QA @ 2026-10-25 15:05 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-report` detach 到 tip `ffb913844222a73ad6a9265cf940ea2079fc5d7e`；相对已过闸 **be5e43d**；merge-tree vs **当前 feature tip `c027714`**（合入 eval@cc1e1da；parents 7b3864a+cc1e1da；含 report@be5e43d）。未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非自己进程；**未关** RF-8/P1。

**ancestry**：`be5e43d..ffb9138` = **4** commits；`merge-base --is-ancestor be5e43d ffb9138` exit 0；`be5e43d` 已在 feature@c027714 祖先链。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip HEAD | **确认** | `ffb913844222a73ad6a9265cf940ea2079fc5d7e`；subj=`docs(report): phase1 slice9 evidence for print empty DER口径` |
| 2 | 当前 feature tip | **确认** | `c027714204ff562e7de5ba4d3e08b88ee27ee549`（合入 eval@cc1e1da；**不再用**约 7b3864a 作 base） |
| 3 | commits 范围（相对 be5e43d） | **4 commits** | `8626c64` print PSNR empty without unit splice（P1-11）；`da7f4bf` print interactive limitations（P1-8）；`8da414c` DER criterion → REPORT_DATA_SPEC **v3.3**；`ffb9138` slice9 docs |
| 4 | 文件范围 | **6 files / +70/-4** | `GlobalEvaluation.tsx`；`ReportPrintLayout.tsx`；`phase1-frontend/slice9/{evidence,batch-tips,rf8-audit-evidence,algorithmOutputMode-gap}.txt` |
| 5 | merge-tree vs **feature@c027714** | 冲突 **0** | `merge-tree --write-tree` exit 0；tree `99bf2519b94da1e9ac0b36b8b584e8468ba70359`；无 CONFLICT / changed in both |
| 6 | merge-tree vs **be5e43d**（批次基线，可选） | 冲突 **0** | exit 0；tree `8f62b4f29a003ba364ea56597d994f654c16dadb` |
| 7 | P1-11 打印空值不拼单位 | **有证据** | `ReportPrintLayout` case figcaption：`num(model.caseRow.psnr, 2, 'dB')` / `num(...baseline..., '—')`；`format.ts` `num(..., empty='未评测')` → null 不残留 ` dB` |
| 8 | P1-8 打印交互局限声明 | **有证据** | `data-testid=print-limitations-interactive`：滑块/缩放/ROI/差分热图仅屏幕可用；PDF/打印为静态 |
| 9 | DER 口径文案 v3.3 | **有证据** | `data-testid=der-criterion-note`（GlobalEvaluation）+ `print-der-criterion`（Print）；文案由 v2 → **REPORT_DATA_SPEC v3.3**（与 docs 现行版本一致） |
| 10 | slice9 证据路径 | **存在** | `phase1-frontend/slice9/evidence.txt`（2123B）；`batch-tips.txt`；`rf8-audit-evidence.txt`；`algorithmOutputMode-gap.txt`（明确跳过 algorithmOutputMode UI） |
| 11 | RF-8 | **仍开 / 勿关** | HomePage / App.tsx / api.ts / urlState.ts **相对 be5e43d 未改**；`object-cover=0` / `object-contain=2`（L245/L250）；TASK_BOARD=进行中（合并前须用户确认截图）；截图四件仍存在于 `screenshots/product-upgrade/phase1-frontend/` |
| 12 | npm build | **通过** | `apps/web` `npm run build` exit 0；ReportsPage chunk `ReportsPage-B9rDsmzj.js`；chunk>500kB 警告同前 |
| 13 | npm test:url | **13 passed** | exit 0 |
| 14 | 主库 SHA | **始=终不变** | PRE=POST `rubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D` / `evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3` |

### 无 blocker / 仍开项（门禁结论之上）

1. **RF-8** / Phase1 **P1-***：**仍开**（本 tip 明确未改 HomePage；截图待用户确认）。
2. **algorithmOutputMode** UI：本批跳过（api.ts 仍无该字段；见 `algorithmOutputMode-gap.txt`）——非本 tip blocker。
3. 产品 **RT-*** / **R7** / **A24** / **conflict**：**仍开**（本门禁未关单）。

### 收尾

- 日志：`wt/qa-tmp/qa-report-ffb9138/`（npm-build / npm-test-url / sha-ffb9138）。
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未关** RF-8/P1。

## 合入后冒烟 tip@c027714（合入 eval@cc1e1da；含 report@be5e43d）——作者 RM-红队QA @ 2026-10-25 15:09 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach 到 tip `c027714204ff562e7de5ba4d3e08b88ee27ee549`；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非自己进程。

**ancestry**：parents = `7b3864a1c9ef92c64cf2e75c5e5127594841d313` + `cc1e1dadc679b87a64034b6d4fbf2b2559cc46b2`；subj=`merge(eval): cc1e1da into feature/product-grade-upgrade (after report@be5e43d)`；`merge-base --is-ancestor be5e43d` / `cc1e1da` / `7b3864a` exit 0。

### 结论：**通过**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip / parents | **确认** | HEAD=`c027714204ff562e7de5ba4d3e08b88ee27ee549`；parents=7b3864a + cc1e1da |
| 2 | 含 be5e43d / cc1e1da | **是** | ancestor exit 0 |
| 3 | 全量 pytest | **747 passed / 1 xfailed** | 81.91s；exit 0；与 tip@b60d556 同数；日志 `wt/qa-tmp/qa-smoke-c027714/pytest-full-c027714.txt` |
| 4 | xfail = A24 | **确认** | `pytest -k a24` → 1 passed / 1 xfailed；**勿伪绿 / 未关单** |
| 5 | G1 | **23 passed** | `-k "roi or g1"`；`pytest-g1-c027714.txt` |
| 6 | RT（含 008/010/013） | **31 passed** | rt002..009 + `test_rt008_010_013`；产品 RT 单**仍开** |
| 7 | Phase2+AB8 | **36p / 1xfail** | `-k "phase2 or ab8 or a24"`；A24 仍 xfail |
| 8 | ES 抽样 | **41 passed** | `-k "es3 or es4 or es5 or es_derived or lift_claim or negative_lift or caption or mechanism"`；ES-3/4/5 主题 |
| 9 | claims/museum | **通过** | `check_claims_open_issues --check` ok；claimFiles **28**；**conflict 20 仍开**；openRows=36；validate_museum_v3 items **28** / images **84** / sha256Match **84** |
| 10 | npm build | **通过** | `apps/web` `npm run build` exit 0；chunk>500kB 警告同既往；vite **5.4.21** |
| 11 | /health AB-8 | **通过** | status 200 healthy；samples_missing=[]；samples_sha_mismatch=[]；samples_available 4 |
| 12 | RT-006 static/index.html | **仍留** | `static/index.html` **EXISTS** size=90717；未全删 |
| 13 | P1/RF/R7/A24/conflict/RT 产品单 | **仍开勿关** | A24 仍 xfail；conflict=20；本闸未关单 |
| 14 | 主库 SHA | **始=终不变** | PRE=POST `rubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D` / `evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3` |

### 无 blocker / 仍开项（冒烟结论之上）

1. **A24** 正式 xfail；export schema 缺口；**仍开 / 勿伪绿**。
2. **R7 / G7**：mechanism head 滞后只记证据；**仍开**。
3. **C-08** 禁 `--apply`；conflict 人工表仍开（20）。
4. Phase1 **P1-*** / **RF-***：**仍开**（本闸未关单）。
5. 产品 **RT-006/008/010/013** 等：**仍开**；static/index.html 仍留。
6. 冒烟期间 feature 已前移至 `e53929f`（合入 report@ffb9138）；本段仅记 tip@c027714；最终 tip 冒烟另段。

### 收尾

- 日志：`wt/qa-tmp/qa-smoke-c027714/`（pytest-full / g1 / rt / phase2-ab8 / es / a24 / ab8-health / claims-check / validate-museum / npm-build / sha-pre/post / SUMMARY）。
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未**杀非自己进程；**未关** P1/RF/R7/A24/conflict/RT 产品单。


## 合入后冒烟 tip@e53929f（合入 report@ffb9138；parents c027714+ffb9138）——作者 RM-红队QA @ 2026-10-25 15:13 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach 到 tip `e53929f1f5e9281427dc11d244f6c78bb0dde3a7`；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非自己进程。

**ancestry**：parents = `c027714204ff562e7de5ba4d3e08b88ee27ee549` + `ffb913844222a73ad6a9265cf940ea2079fc5d7e`；subj=`merge(report): ffb9138 into feature/product-grade-upgrade (vs c027714)`；`merge-base --is-ancestor c027714` / `ffb9138` exit 0。相对 c027714：**6 files / +70/-4**（GlobalEvaluation / ReportPrintLayout / slice9/*）。

### 结论：**通过**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip / parents | **确认** | HEAD=`e53929f1f5e9281427dc11d244f6c78bb0dde3a7`；parents=c027714 + ffb9138 |
| 2 | 含 c027714 / ffb9138 | **是** | ancestor exit 0 |
| 3 | 全量 pytest | **747 passed / 1 xfailed** | 73.32s；exit 0；与 tip@c027714 同数；日志 `wt/qa-tmp/qa-smoke-e53929f/pytest-full-e53929f.txt` |
| 4 | xfail = A24 | **确认** | `pytest -k a24` → 1 passed / 1 xfailed；**勿伪绿 / 未关单** |
| 5 | G1 | **23 passed** | `-k "roi or g1"` |
| 6 | RT（含 008/010/013） | **31 passed** | rt002..009 + `test_rt008_010_013`；产品 RT 单**仍开** |
| 7 | Phase2+AB8 | **36p / 1xfail** | `-k "phase2 or ab8 or a24"`；A24 仍 xfail |
| 8 | ES 抽样 | **41 passed** | ES-3/4/5 主题 |
| 9 | claims/museum | **通过** | claimFiles **28**；**conflict 20 仍开**；openRows=36；museum items **28** / images **84** / sha256Match **84** |
| 10 | npm build | **通过** | exit 0；ReportsPage-B9rDsmzj.js；chunk>500kB 警告；vite **5.4.21** |
| 11 | /health AB-8 | **通过** | 200 healthy；samples_missing=[]；samples_sha_mismatch=[]；samples_available 4 |
| 12 | RT-006 static/index.html | **仍留** | EXISTS size=90717 |
| 13 | P1/RF/R7/A24/conflict/RT | **仍开勿关** | RF-8 HomePage 未改；A24 仍 xfail；conflict=20 |
| 14 | 主库 SHA | **始=终不变** | PRE=POST `8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D` / `854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3` |

### 无 blocker / 仍开项（冒烟结论之上）

1. **A24** 正式 xfail；**仍开 / 勿伪绿**。
2. **R7 / G7**：mechanism head 滞后只记证据；**仍开**。
3. **C-08** 禁 `--apply`；conflict=20 **仍开**。
4. Phase1 **P1-*** / **RF-8**：**仍开**（本 tip 合入 slice9 明确未改 HomePage；截图仍待用户确认）。
5. 产品 **RT-006/008/010/013** 等：**仍开**；static/index.html 仍留。

### 收尾

- 日志：`wt/qa-tmp/qa-smoke-e53929f/`（pytest-full / g1 / rt / phase2-ab8 / es / a24 / ab8-health / claims-check / validate-museum / npm-build / sha-pre/post / SUMMARY）。
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未**杀非自己进程；**未关** P1/RF/R7/A24/conflict/RT 产品单。

## 评测 tip 门禁 tip@3b0c47b（docs；R7 lag=161；相对 feature@e53929f）—— RM-红队QA @ 2026-10-25 15:15 Asia/Shanghai

**范围**：只读 worktree D:\RubbingMind\wt\qa-evalsci detach 到 tip 3b0c47bb41351d37fe77d125ca9b84b111e8e7e0；相对 feature@e53929f；**未动** qa-feature-smoke / qa-report；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非自己进程。

**性质**：MECHANISM_HEAD_NOTE / ES_EVAL_PROGRESS / REVIEW_EVALSCI_ALIGN_e53929f 证据更新（§11 / R7 开项表）；**未重跑** mechanism；A24 仍 xfail；R7 lag=161。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip HEAD | **确认** | 3b0c47bb41351d37fe77d125ca9b84b111e8e7e0；subj=docs(eval-sci): stamp R7 lag=161 after FF feature@e53929f；parent=e53929f1f5e9281427dc11d244f6c78bb0dde3a7；e53929f..3b0c47b = **1** commit（ahead 0/1） |
| 2 | vs feature@e53929f | **干净 / FF 可合** | merge-base = base；merge-tree --write-tree 冲突 **0**；tree 8564a1fe0333029c506b9d0498c46cdf8d766e92 |
| 3 | 是否纯文档 | **是** | 仅 docs/product-upgrade/ES_EVAL_PROGRESS.md、MECHANISM_HEAD_NOTE.md、REVIEW_EVALSCI_ALIGN_e53929f.md（3 files, +33/-4）；**无** 非 docs / 无 test / 无业务代码 / 无 museum_processing |
| 4 | R7 lag=161 | **已验证** | git rev-list --count 7623a52..e53929f = **161**（stamp HEAD 本身=162，与既有惯例一致）；MECHANISM_HEAD_NOTE §6/§11 与 ES_EVAL_PROGRESS「R7 / A24 开项」均写 **161**；文案 **仍开未谎关**；**未重跑** mechanism_cases.py |
| 5 | A24 | **仍 xfail / 未伪绿** | 窄抽样 pytest -k a24 → **1 passed / 1 xfailed**；日志 wt/qa-tmp/qa-eval-3b0c47b/pytest-a24.txt；未关单 |
| 6 | 全量 pytest | **跳过（docs-only）** | 父 tip@e53929f 冒烟同口径（747p/1xfail）；本 tip 无代码/测试改动 |
| 7 | R7 / A24 产品项 | **仍开 / 未关** | 文档明确仍开项、xfail 保持、不谎关；未把 A24 改正式 assert |
| 8 | 主库 SHA | **始=终不变** | rubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D / evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3（期望 8408DBC3…323D / 854DF859…BABD3 一致） |

### 无 blocker / 开项（门禁结论之外）

1. **R7 / G7**：mechanism head 仍绑 7623a52；相对 feature tip 超前 **161**；只记证据；**勿关单**。
2. **A24**：正式 xfail；export schema 缺口；**勿伪绿 / 勿关单**。
3. 本 tip **非** 产品行为变更；合入后冒烟可窄（docs-only）。

### 收尾

- 日志：wt/qa-tmp/qa-eval-3b0c47b/（tip-meta / diffstat / name-status / merge-tree-* / r7-lag / pytest-a24 / sha-post）。
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未关** R7/A24/P1/RF/conflict/产品 RT。

## 合入后窄冒烟 tip@3b0c47b（FF 合入 docs；parent e53929f）——作者 RM-红队QA @ 2026-10-25 15:23 Asia/Shanghai

**范围**：只读 worktree D:\RubbingMind\wt\qa-feature-smoke detach @ tip 3b0c47bb41351d37fe77d125ca9b84b111e8e7e0；窄冒烟（DB SHA / A24 仍 xfail / 开项未关；全量对照父 tip 跳过 + G1 抽检）。

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip / parent | **确认** | HEAD=3b0c47bb41351d37fe77d125ca9b84b111e8e7e0；parent=e53929f1f5e9281427dc11d244f6c78bb0dde3a7；subj=docs(eval-sci): stamp R7 lag=161 after FF feature@e53929f |
| 2 | docs-only vs parent | **是** | 3 files / +33/-4：ES_EVAL_PROGRESS.md / MECHANISM_HEAD_NOTE.md / REVIEW_EVALSCI_ALIGN_e53929f.md（均 docs/product-upgrade） |
| 3 | A24 | **仍 1p/1xfail / 未伪绿** | pytest -k a24 → **1 passed / 1 xfailed**（3.02s）；日志 wt/qa-tmp/qa-smoke-3b0c47b/pytest-a24-3b0c47b.txt |
| 4 | G1 抽检 | **23 passed** | pytest -k "roi or g1" → 23 passed（2.16s）；全量跳过（父 tip@e53929f = 747p/1xfail） |
| 5 | 主库 SHA | **始=终不变** | PRE=POST
ubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D / evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3（期望一致） |
| 6 | 开项 P1/RF-8/R7/A24/conflict/产品 RT | **仍开 / 未关** | 本闸未关单；A24 保持 xfail；R7 lag=161 证据仍开；conflict=20 仍开 |

### 结论

- **窄冒烟结论：通过**（无 blocker；docs-only；A24 未伪绿；主库 SHA 未变）。
- 全量 pytest 对照父 tip@e53929f（747p/1xfail）跳过；本 tip 无代码/测试改动。

### 收尾

- 日志：wt/qa-tmp/qa-smoke-3b0c47b/（tip-meta / pytest-a24 / pytest-g1 / sha-pre/post / SUMMARY）。
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

## 评测 tip 门禁 tip@51fa1ba（docs §12 核验；R7 lag=162；相对 feature@3b0c47b）—— RM-红队QA @ 2026-10-25 15:30 Asia/Shanghai

**范围**：只读 worktree D:\RubbingMind\wt\qa-evalsci detach @ tip 51fa1bacc7a35ba46c9d2848d765bbff58cae834；相对 feature@3b0c47bb41351d37fe77d125ca9b84b111e8e7e0；**未动** qa-feature-smoke；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非自己进程。

**性质**：MECHANISM_HEAD_NOTE §12 + ES_EVAL_PROGRESS 开项核验（feature@3b0c47b 窄冒烟后）；**未重跑** mechanism；A24 仍 xfail；R7 仍开。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip HEAD | **确认** | 51fa1bacc7a35ba46c9d2848d765bbff58cae834；subj=docs(eval-sci): verify A24/R7 open after feature@3b0c47b smoke；parent=3b0c47bb41351d37fe77d125ca9b84b111e8e7e0；3b0c47b..51fa1ba = **1** commit |
| 2 | vs feature@3b0c47b | **干净 / 可合** | merge-base = feature；merge-tree --write-tree 冲突 **0**；tree 56ad85152691f38db74be0d83985820cc1515aad |
| 3 | 是否纯文档 | **是** | 仅 docs/product-upgrade/ES_EVAL_PROGRESS.md、MECHANISM_HEAD_NOTE.md（2 files, +15/-4）；**无** 非 docs / 无 test / 无业务代码 / 无 museum_processing |
| 4 | §12 / R7 lag=162 | **已核验仍开** | MECHANISM_HEAD_NOTE §12 存在；git rev-list --count 7623a52..3b0c47b = **162**（docs 宣称值；feature tip）；7623a52..51fa1ba=163（本评测 tip 自身 +1 docs）；正文 **仍开未关单**；**未重跑** mechanism_cases.py |
| 5 | A24 | **仍 xfail / 未伪绿** | 窄抽样 pytest -k a24 → **1 passed / 1 xfailed**（日志 wt/qa-tmp/qa-eval-51fa1ba/pytest-a24.txt）；未关单；未改正式 assert |
| 6 | 全量 pytest | **跳过（docs-only）** | 与 tip@3b0c47b / e53929f 同口径（父 tip 窄冒烟通过；e53929f=747p/1xfail）；本 tip 无代码/测试改动 |
| 7 | R7 / A24 产品单 | **仍开 / 未关** | 文档明确仍开项、xfail 保持、未谎关；未把 A24 改正式 assert |
| 8 | 主库 SHA | **始=终不变** | rubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D / evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3（期望 8408DBC3…323D / 854DF859…BABD3 一致） |

### 无 blocker / 开项（门禁结论之外）

1. **R7 / G7**：mechanism head 锚定 7623a52；相对 feature tip 超前 **162**；只记证据；**勿关单**。
2. **A24**：正式 xfail（export schema 缺口）；**勿伪绿 / 勿关单**。
3. 本 tip **无** 产品行为变更；合入后冒烟可窄（docs-only）。

### 收尾

- 日志：wt/qa-tmp/qa-eval-51fa1ba/（tip-meta / diffstat / name-status / merge-tree-* / r7-lag / pytest-a24 / sha-post / SUMMARY）。
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未关** R7/A24/P1/RF/conflict/产品 RT。

## 报告 tip 门禁 tip@49002cc（含 21cb82b export liftClaims、slice10、merge 3b0c47b；vs feature@3b0c47b）—— RM-红队QA @ 2026-10-25 15:32 Asia/Shanghai

**范围**：只读 worktree D:\RubbingMind\wt\qa-report detach @ tip 49002ccdf0d777cba66fc5587612032db13215f2；相对 **feature@3b0c47bb41351d37fe77d125ca9b84b111e8e7e0**；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非自己进程；**未关** RF-8/P1。

**ancestry**：merge-base --is-ancestor 21cb82b 49002cc exit 0；merge-base --is-ancestor 3b0c47b 49002cc exit 0；3b0c47b..49002cc = **5** commits（含 c8e52ef merge feature@3b0c47b、21cb82b liftClaims、732ef69/dde2f9e/49002cc slice10）。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip HEAD | **确认** | 49002ccdf0d777cba66fc5587612032db13215f2；subj=docs(report): slice10 tips drop self-SHA churn；parent=dde2f9e |
| 2 | feature base | **确认** | 3b0c47bb41351d37fe77d125ca9b84b111e8e7e0 |
| 3 | ancestry | **齐** | 含 21cb82b export liftClaims；732ef69 slice10 evidence；c8e52ef merge(feature)@3b0c47b；dde2f9e/49002cc slice10 tips |
| 4 | 文件范围 | **9 files / +203/-2** | ReportsPage.tsx（+8/-2 liftClaims）；phase1-frontend/slice10/ 8 个证据文件（evidence / batch-tips / rf8-audit / p1-9 / p1-rf-open / c1-c4 / algorithmOutputMode-gap / slice10-verify.json） |
| 5 | merge-tree vs **feature@3b0c47b** | 冲突 **0** | merge-tree --write-tree exit 0；tree d7be42dcf0c77a4425fefa19b948ed82fbfd66d1；无 CONFLICT / changed in both |
| 6 | export liftClaims（ES-3） | **有证据** | ReportsPage exportJson 含 experiment.liftClaims.{summary,rule,primaryScopeLabel,note}；strip() 带 liftClaimLabel；note 对齐屏上 lift-claim badges；commit 21cb82b |
| 7 | slice10 证据目录 | **存在** | phase1-frontend/slice10/*；截图 EXISTS：p1-9_reports_firstscreen_1366x768.png(498572)、p1-9_reports_firstscreen_390x844.png(116073)、
f8_home_core_cards_1920x1080.png(2020748)；slice10-verify.json ok=true |
| 8 | RF-8 | **仍开 / 未关** | HomePage / App.tsx / api.ts / urlState.ts **相对 base 未改**；HomePage object-cover=0 / object-contain@L245/L250；TASK_BOARD=进行中（合并前需用户确认截图）；证据明确 NOT self-closed |
| 9 | algorithmOutputMode | **gap only / 非 blocker** | api.ts 仍无字段；lgorithmOutputMode-gap.txt；未伪 UI |
| 10 | npm build | **通过** | pps/web
pm run build exit 0；chunk ReportsPage-e8S6O9Um.js（与 evidence 一致）；chunk>500kB 警告同前 |
| 11 | npm test:url | **13 passed** | exit 0 |
| 12 | 主库 SHA | **始=终未变** | PRE=POST
ubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D / evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3（期望 8408DBC3…323D / 854DF859…BABD3 一致） |

### 无 blocker / 仍开项（门禁结论之外）

1. **RF-8** / Phase1 **P1-***：**仍开**（本 tip 明确未改 HomePage；截图待用户确认）。
2. **algorithmOutputMode** UI：上游缺口（非本 tip blocker）。
3. 产品 **RT-*** / **R7** / **A24** / **conflict**：**仍开**（本门禁未关单）。

### 收尾

- 日志：wt/qa-tmp/qa-report-49002cc/（tip-meta / name-status / mergetree / npm-build / npm-test-url / sha-post）。
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未关** RF-8/P1。

## 合入后冒烟 tip@ed9f1a0（合入 report@49002cc；parents 51fa1ba+49002cc；含 eval docs）—— RM-红队QA @ 2026-10-25 15:42 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach @ tip `ed9f1a0b20978d5500453bdbbaa43505a6f9297d`。**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非自己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

**ancestry**：parents=`51fa1bacc7a35ba46c9d2848d765bbff58cae834` + `49002ccdf0d777cba66fc5587612032db13215f2`；含 21cb82b liftClaims、3b0c47b/51fa1ba eval docs、slice10。vs 51fa1ba = 9 files / +203/-2（ReportsPage + phase1-frontend/slice10/*）。

### 结论：**通过**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip HEAD / parents | **确认** | ed9f1a0；parents 51fa1ba+49002cc；subj=merge(report): 49002cc into feature |
| 2 | 全量 pytest | **747 passed / 1 xfailed** | A24 仍 xfail；~73.97s；日志 pytest-full-ed9f1a0.txt |
| 3 | G1 | **23 passed** | -k "process_regression or mechanism or change_stats" |
| 4 | RT | **31 passed** | 含 test_rt008_010_013；未关产品 RT 单 |
| 5 | Phase2+AB8 | **36 passed / 1 xfailed** | A24 仍 xfail |
| 6 | ES | **41 passed** | ES-3/4/5 合约 + evidence/experiment_derived + 弱相关/回归探针 |
| 7 | claims | **ok / 仍开** | claimFiles=28；conflict=**20 仍开**；openRows=36；pendingHuman=30 |
| 8 | museum | **通过** | items=28；images=84；sha256Match=84 |
| 9 | /api/health AB-8 | **通过** | 200 healthy；samples_missing=[]；samples_sha_mismatch=[]；samples_available=4 |
| 10 | npm build | **通过** | vite 5.4.21；ReportsPage-e8S6O9Um.js；chunk>500kB 警告同前 |
| 11 | RT-006 static/index.html | **仍在** | size=90717（产品单仍开） |
| 12 | 主库 SHA | **始=终未变** | PRE=POST rubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D / evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3（期望 8408DBC3…323D / 854DF859…BABD3 一致） |
| 13 | 开项 P1/RF-8/R7/A24/conflict/产品 RT | **仍开 / 未关** | 门禁未关单；A24 保持 xfail；RF-8/P1 仍开；conflict=20 仍开 |

### 无 blocker

- **冒烟结论：通过**（无 blocker；开项不关）。
- 相对父 tip@51fa1ba / e53929f 口径数字一致（747p/1xfail；G1 23；RT 31；Phase2 36p/1xfail；ES 41；claims/museum/SHA 同前）。

### 收尾

- 日志：`wt/qa-tmp/qa-smoke-ed9f1a0/`（tip-meta / pytest-* / claims / museum / ab8-health / npm-build / sha-pre/post / SUMMARY）。
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply；**未关** P1/RF-8/R7/A24/conflict/产品 RT。
## 评测 tip 门禁 tip@2a553f9（ES-3/4/5 再核 + R7 lag=169；相对 feature@ed9f1a0）——作者 RM-红队QA @ 2026-10-25 15:48 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-evalsci` detach @ tip `2a553f9574f176e1db5df63b15657b86cdf230ef`；相对 **feature@ed9f1a0b20978d5500453bdbbaa43505a6f9297d**；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非自己进程；**未关** A24/R7/P1/RF-8/conflict/产品 RT。

**ancestry**：parent=ed9f1a0；merge-base --is-ancestor ed9f1a0 2a553f9 exit 0；ed9f1a0..2a553f9 = **1** commit（docs-only）。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip HEAD | **确认** | 2a553f9574f176e1db5df63b15657b86cdf230ef；subj=docs(eval-sci): ES-3/4/5 recheck + R7 lag=169 after FF feature@ed9f1a0；parent=ed9f1a0 |
| 2 | feature base | **确认** | ed9f1a0b20978d5500453bdbbaa43505a6f9297d |
| 3 | 文件范围 | **docs-only 3 files / +41/-4** | ES_EVAL_PROGRESS.md；MECHANISM_HEAD_NOTE.md §13；REVIEW_EVALSCI_ALIGN_ed9f1a0.md（新增） |
| 4 | merge-tree vs **feature@ed9f1a0** | 冲突 **0** | merge-tree --write-tree exit 0；tree 9627111fa637a5f10b19f7fad2dfb68231a3bcfc；无 CONFLICT |
| 5 | ES-3/4/5 再核 | **有证据** | REVIEW_EVALSCI_ALIGN + ES_EVAL_PROGRESS 续核；§13 ES-3 lift_claim_summary / ES-4 captionProvenance / ES-5 negative_lift_display；未伪绿 Top-k/CI |
| 6 | R7 lag=169 | **已核验仍开** | git rev-list --count 7623a52..ed9f1a0 = **169**；MECHANISM_HEAD_NOTE §13 正文一致；**未重跑** mechanism；**勿关单** |
| 7 | A24 | **仍 xfail / 未关** | 窄抽样 pytest -k a24 → **1 passed / 1 xfailed**；日志 wt/qa-tmp/qa-eval-2a553f9/pytest-a24.txt；未伪绿；未改正式 assert |
| 8 | museum_processing / 业务代码 | **未改** | name-status 无非 docs/ 路径 |
| 9 | 全量 pytest | **跳过（docs-only）** | 父 tip@ed9f1a0 冒烟 = 747p/1xfail |
| 10 | 主库 SHA | **始=终未变** | PRE=POST rubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D / evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3（期望 8408DBC3…323D / 854DF859…BABD3 一致） |

### 无 blocker / 仍开项（门禁结论之外）

1. **R7 / G7**：mechanism head 锚定 7623a52；相对 feature tip 超前 **169**；只记证据；**勿关单**。
2. **A24**：正式 xfail（export schema 缺口）；**勿伪绿 / 勿关单**。
3. 本 tip **无** 产品行为变更；合入后冒烟可窄（docs-only）。

### 收尾

- 日志：wt/qa-tmp/qa-eval-2a553f9/（tip-meta / diffstat / name-status / merge-tree / r7-lag / pytest-a24 / sha-post / SUMMARY）。
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未关** R7/A24/P1/RF/conflict/产品 RT。
## 报告 tip 窄门禁 tip@12e8ce6（docs-only slice11 inventory；无可叠 feat）相对 feature@ed9f1a0；作者 RM-红队QA @ 2026-10-25 15:52 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-report` detach @ tip `12e8ce6acea0394edfb7d3c6b0579965e3e4f2bc`；相对 **feature@ed9f1a0b20978d5500453bdbbaa43505a6f9297d**；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非本任务进程；**未关** RF-8/P1/R7/A24/conflict/产品 RT。

**ancestry**：parent=`ed9f1a0`；`merge-base --is-ancestor ed9f1a0 12e8ce6` exit 0；ed9f1a0..12e8ce6 = **1** commit（docs-only）；feature tip 当前仍 = ed9f1a0（2a553f9 尚未合入，故仅报 vs ed9f1a0）。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip HEAD | **确认** | `12e8ce6acea0394edfb7d3c6b0579965e3e4f2bc`；subj=`docs(report): slice11 FF ed9f1a0 无可叠代码项 inventory`；parent=ed9f1a0 |
| 2 | feature base | **确认** | `ed9f1a0b20978d5500453bdbbaa43505a6f9297d`（feature tip 未前移） |
| 3 | 文件范围 | **docs-only 5 files / +98** | `phase1-frontend/slice11/`：algorithmOutputMode-gap / batch-tips / evidence / p1-rf-open-inventory / rf8-audit-evidence；**0** 非 docs；**无** apps/web / TSX |
| 4 | 无可叠 feat | **确认** | inventory：可代码化 P1 已落地至 slice10；余 RF-8（等用户）+ algorithmOutputMode（arch 字段缺） |
| 5 | merge-tree vs **feature@ed9f1a0** | 冲突 **0** | `merge-tree --write-tree` exit 0；tree `148a06fdad7a15aa5f309fef4fbc6c51f7a9e31c`；无 CONFLICT |
| 6 | RF-8 | **仍开 / 未自关** | rf8-audit-evidence：HomePage 未改；object-contain@L245/L250；等用户截图确认；**门禁未关单** |
| 7 | algorithmOutputMode | **缺口仅记录** | api.ts 字段 present=False；非本 tip blocker；交 arch |
| 8 | npm build | **跳过（无前端改动）** | 父 tip@ed9f1a0 smoke 已绿（ReportsPage-e8S6O9Um.js） |
| 9 | 全量 pytest | **跳过（docs-only）** | 父 tip@ed9f1a0 冒烟 = 747p/1xfail |
| 10 | 主库 SHA | **始=终不变** | PRE=POST rubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D / evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3（期望 8408DBC3…323D / 854DF859…BABD3 一致） |

### 无 blocker / 仍开项（门禁通过之外）

1. **RF-8** / Phase1 **P1-***：**仍开**（本 tip 明确未改 HomePage；截图等用户确认）。
2. **algorithmOutputMode** UI：契约缺口；非本 tip blocker。
3. 产品 **RT-*** / **R7** / **A24** / **conflict**：**仍开**（本闸未关单）。

### 收尾

- 日志：`wt/qa-tmp/qa-report-12e8ce6/`（tip-meta / name-status / diffstat / merge-tree / merge-tree-write / sha-post / SUMMARY）。
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未关** RF-8/P1。
## 金石 tip 窄门禁 tip@5bf3836（人工复核提示按核对队列 + 证据缺口；相对 feature@ed9f1a0）——作者 RM-红队QA @ 2026-10-25 15:52 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-jinshi` detach @ tip `5bf383631bc3184bf1f446c890c6c05ffcdb0070`；相对 **feature@ed9f1a0b20978d5500453bdbbaa43505a6f9297d**；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非自己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

**ancestry**：parent=ed9f1a0；merge-base --is-ancestor ed9f1a0 5bf3836 exit 0；ed9f1a0..5bf3836 = **1** commit；ahead/behind vs feature = **0/1**（FF child）。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip HEAD | **确认** | `5bf383631bc3184bf1f446c890c6c05ffcdb0070`；subj=docs(claims): 人工复核提示按核对队列 + 证据缺口（开项仍开放）；parent=ed9f1a0 |
| 2 | feature base | **确认** | `ed9f1a0b20978d5500453bdbbaa43505a6f9297d` |
| 3 | 文件范围 | **docs + ledger 脚本 2 files / +341/-147** | `docs/product-upgrade/CLAIMS_OPEN_ISSUES.md`；`scripts/check_claims_open_issues.py`（新增 evidence_gap / next_check / Q1–Q4 队列渲染） |
| 4 | claims/* 数据文件 | **未改** | `git diff --name-only` 无 `claims/`、无 museum/sqlite/static；claimFiles 仍 28 |
| 5 | merge-tree vs **feature@ed9f1a0** | 冲突 **0** | merge-tree --write-tree exit 0；tree `b94e481d46c73bea234d01180c0fbea285a96d67`；conflict markers=0 |
| 6 | 人工复核提示 / 证据缺口 | **有证据** | 台账新增「人工复核提示（按核对队列）」Q1 conflict=20 / Q2 pending_human / Q3 catalogue pending_review / Q4 reviewFlags；JS-4/JS-5 表增「证据缺口」列；脚本明确 **不定论、不合并异文、不自动关闭开项、不 C-08 --apply** |
| 7 | claims --check | **ok / 仍开** | `{"ok": true, "openRows": 36, "conflict": 20, "pendingHuman": 30, "reviewFlag": 1, "cataloguePendingReview": 13, "claimFiles": 28}`；日志 `wt/qa-tmp/qa-jinshi-5bf3836/claims-check.txt` |
| 8 | conflict / 开项 | **20 仍开 / 未关** | 统计摘要 + Q1 均 conflict=20；门禁**未关单** |
| 9 | 业务代码 / 主库 | **未改 / 未写** | 仅 docs+ledger 脚本；无 C-08 --apply |
| 10 | 主库 SHA | **始=终不变** | PRE=POST rubbingmind.sqlite=`8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D` / evidence-v2.sqlite=`854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3`（期望 8408DBC3…323D / 854DF859…BABD3 一致） |

### 无 blocker / 仍开项（门禁结论之外）

1. **conflict=20** / openRows=36 / pendingHuman=30 / cataloguePendingReview=13 / reviewFlag=1 → **仍开**（本 tip 仅排期提示与证据缺口列，明确不关闭）。
2. **P1 / RF-8 / R7 / A24 / 产品 RT** → **仍开**（本门禁未关单）。
3. 非纯 docs-only（含 `scripts/check_claims_open_issues.py` ledger 生成器增强），但**非业务路径**；与既有金石台账脚本同口径。

### 收尾

- 日志：`wt/qa-tmp/qa-jinshi-5bf3836/`（tip-meta / name-status / diffstat / merge-tree* / claims-check / sha-post / SUMMARY）
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未关** conflict/P1/RF-8/R7/A24/产品 RT。
## 金石 tip 窄门禁 tip@5bf3836 · feature base 更新补记（vs feature@2a553f9）——作者 RM-红队QA @ 2026-10-25 15:53 Asia/Shanghai

**背景**：feature HEAD 已 FF 至 `2a553f9574f176e1db5df63b15657b86cdf230ef`（合入 eval docs；parent ed9f1a0）。merge-tree 主口径改 vs **2a553f9**；附带 vs ed9f1a0。

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| A | tip / feature@2a553f9 关系 | **同父兄弟** | tip parent=ed9f1a0；2a553f9 parent=ed9f1a0；merge-base=`ed9f1a0b20978d5500453bdbbaa43505a6f9297d` |
| B | merge-tree vs **feature@2a553f9** | 冲突 **0** | merge-tree --write-tree exit 0；tree `4eb45cf125522623d22c4796c077bcee96a44fb2`；conflict markers=0；日志 `merge-tree-vs-2a553f9.txt` |
| C | 文件重叠 tip∩2a553f9（各相对 ed9f1a0） | **无** | tip: CLAIMS_OPEN_ISSUES.md + check_claims_open_issues.py；2a553f9: ES_EVAL_PROGRESS / MECHANISM_HEAD_NOTE / REVIEW_EVALSCI_ALIGN_ed9f1a0.md |
| D | merge-tree vs ed9f1a0（附） | 冲突 **0** | tree `b94e481d46c73bea234d01180c0fbea285a96d67`（先跑口径仍有效） |
| E | claims --check / conflict | **ok / 20 仍开** | 未重关；开项勿关 |
| F | 主库 SHA | **始=终不变** | `8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D` / `854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3` |

### 结论（更新后）：**可合并**

- 相对新 feature@2a553f9：**无冲突、无文件重叠**；claims/* 未改；conflict=20 等开项**仍开**。
- blockers: **none**。
### 补记：feature tip 前移 @ 2026-10-25 15:53 Asia/Shanghai

- feature HEAD 已至 2a553f9574f176e1db5df63b15657b86cdf230ef（FF eval docs；parent=ed9f1a0）。
- **merge-tree tip@12e8ce6 vs feature@2a553f9**：冲突 **0**；--write-tree exit 0；tree 982b17c03ee81ade4aeface666155af3ba312ca7。
- 与 tip@ed9f1a0 关系：兄弟分叉（rev-list left-right **1/1**）；两侧均为 docs-only（report slice11 vs eval ES/R7），路径不重叠。
- 附带 vs ed9f1a0：冲突 0；tree 148a06fdad7a15aa5f309fef4fbc6c51f7a9e31c（先前已报）。
- **结论不变：可合并**；**RF-8 仍开未关**。

## 合入后窄冒烟 tip@2a553f9（FF 合入 eval docs；parent ed9f1a0）—— RM-红队QA @ 2026-10-25 15:55 Asia/Shanghai

**范围**：只读 worktree D:\RubbingMind\wt\qa-feature-smoke detach @ tip 2a553f9574f176e1db5df63b15657b86cdf230ef；窄冒烟（DB SHA / A24 仍 xfail / 开项勿关；全量对照父 tip 跳过 + G1 抽检）。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **确认** | HEAD=2a553f9574f176e1db5df63b15657b86cdf230ef；parent=ed9f1a0b20978d5500453bdbbaa43505a6f9297d；subj=docs(eval-sci): ES-3/4/5 recheck + R7 lag=169 after FF feature@ed9f1a0 |
| 2 | docs-only vs parent | **是** | 3 files / +41/-4：ES_EVAL_PROGRESS.md / MECHANISM_HEAD_NOTE.md / REVIEW_EVALSCI_ALIGN_ed9f1a0.md（均 docs/product-upgrade） |
| 3 | A24 | **仍 1p/1xfail / 未假绿** | pytest -k a24 → **1 passed / 1 xfailed**（2.59s）；日志 wt/qa-tmp/qa-smoke-2a553f9/pytest-a24-2a553f9.txt |
| 4 | G1 抽检 | **23 passed** | pytest -k "roi or g1" → 23 passed（2.48s）；全量对照父 tip@ed9f1a0 = 747p/1xfail |
| 5 | 主库 SHA | **始=终未变** | PRE=POST rubbingmind.sqlite=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D / evidence-v2.sqlite=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3 |

- **窄冒烟结论：通过**（无 blocker；docs-only；A24 未假绿；主库 SHA 未变）。
- 全量 pytest 对照父 tip@ed9f1a0（747p/1xfail）跳过；本 tip 无代码/测试改动。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**（未关）。
- 日志：wt/qa-tmp/qa-smoke-2a553f9/（tip-meta / pytest-a24 / pytest-g1 / sha-pre/post / SUMMARY）。
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

## 架构 tip 门禁 tip@847e7f1（algorithmOutputMode / AdaptiveDiagnostics 契约；相对 feature@ac8f83c）——红队QA @ 2026-10-25 15:56 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-arch` detach @ tip `847e7f166ae3f6bc25a9fc8f0c801d0bf8438f2f`；门禁 base **feature@ac8f83c7852419633b4ea12927fec6d75b12baba**（parents f7a1d72+12e8ce6）；附带 vs f7a1d72 / 2a553f9 / ed9f1a0。未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非自己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

**ancestry**：parent=ed9f1a0；merge-base(ac8f83c,847e7f1)=ed9f1a0；与 feature 分叉（非 FF）；合入需 merge commit。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip HEAD | **确认** | `847e7f166ae3f6bc25a9fc8f0c801d0bf8438f2f`；subj=feat(arch): type algorithmOutputMode on adaptiveDiagnostics (ADR R2-12)；parent=ed9f1a0 |
| 2 | feature base | **确认** | `ac8f83c7852419633b4ea12927fec6d75b12baba`（合入 report@12e8ce6 after jinshi@5bf3836） |
| 3 | 文件范围 | **4 files / +39/-5** | `apps/web/src/types/stele.ts`、`services/api.ts`、`pages/WorkbenchPage.tsx`、`docs/product-upgrade/MERGE_NOTE_algorithmOutputMode.md` |
| 4 | merge-tree vs **feature@ac8f83c** | 冲突 **0** | merge-tree --write-tree exit 0；tree `deeab238446ec8f6e09141b3f84c27ad10e278be`；messages 空；与 feature 文件 **无重叠** |
| 5 | 附带 merge-tree | 冲突 **0** | vs f7a1d72 tree `bb501f53…`；vs 2a553f9 tree `2d627927…`；vs ed9f1a0 tree `412f1ebd…` |
| 6 | AlgorithmOutputMode 契约 | **有证据** | stele.ts：`type AlgorithmOutputMode = 'processed' \| 'identity_no_evidence' \| 'gate_fallback_original'`；`AdaptiveDiagnostics.algorithmOutputMode?` |
| 7 | AdaptiveDiagnostics / api.ts | **有证据** | api.ts 再导出类型；`AdaptiveRunFields`；`ProcessingRunR1` 携带 adaptiveDiagnostics；run-level `outputMode` 注释标明勿与算法层混淆（ADR R2-12） |
| 8 | WorkbenchPage 类型 | **有证据** | `useState<AdaptiveDiagnostics\|null>`（原 `Record<string,unknown>`）；ProcessingResult.adaptiveDiagnostics 收窄为同类型 |
| 9 | museum_processing / claims / 硬删 | **未改** | name-only 无 museum_processing / claims / sqlite；本 tip 不改后端内核 |
| 10 | npm build | **通过** | `tsc && vite build` exit 0；vite 5.4.21；WorkbenchPage-CfM8fqt2.js；ReportsPage-e8S6O9Um.js |
| 11 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3` |
| 12 | 开项 | **仍开** | P1/RF-8/R7/A24/conflict/产品 RT 本闸未关单 |

### 无 blocker / 开项（门禁范围之外）

1. **algorithmOutputMode UI** 仍缺（本 tip 仅类型契约；UI 非本 tip blocker）。
2. **P1 / RF-8 / R7 / A24 / conflict / 产品 RT** — **仍开**（本闸未关单）。
3. 合入方式：**非 FF**（相对 ac8f83c 分叉）；架构侧需 merge commit（冲突预期 0）。

### 收尾

- 日志：`wt/qa-tmp/qa-arch-847e7f1/`（tip-meta / name-status / diffstat / full-diff / contract-evidence / merge-tree-vs-* / npm-build / sha-pre / sha-post / SUMMARY）。
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未关** RF-8/P1/R7/A24/conflict/产品 RT。

## 合入后窄冒烟 tip@ac8f83c（合入 report@12e8ce6；parents f7a1d72+12e8ce6；含 eval@2a553f9 + jinshi@5bf3836）—— RM-红队QA @ 2026-10-25 15:57 Asia/Shanghai

**范围**：只读 worktree D:\RubbingMind\wt\qa-feature-smoke detach @ tip ac8f83c7852419633b4ea12927fec6d75b12baba；窄冒烟（DB SHA / A24 仍 xfail / claims+museum 抽检 / 开项勿关；全量对照父 tip@ed9f1a0 跳过 + G1 抽检）。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parents | **确认** | HEAD=ac8f83c7852419633b4ea12927fec6d75b12baba；parents=f7a1d722… + 12e8ce6a…；含 2a553f9/5bf3836/12e8ce6/f7a1d72 |
| 2 | 变更范围 vs ed9f1a0 | **docs/台账/脚本** | 10 files / +480/-151：eval docs + CLAIMS_OPEN_ISSUES + check_claims_open_issues.py + phase1-frontend/slice11/*（无 apps/web） |
| 3 | A24 | **仍 1p/1xfail / 未假绿** | pytest -k a24 → **1 passed / 1 xfailed**（2.24s）；日志 qa-tmp/qa-smoke-ac8f83c/pytest-a24-ac8f83c.txt |
| 4 | G1 抽检 | **23 passed** | pytest -k "roi or g1"（2.12s） |
| 5 | claims | **ok / conflict 仍开** | --json + --check → ok；claimFiles=28 conflict=20 openRows=36 pendingHuman=30；ledger 与扫描一致；**未** --write |
| 6 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 7 | 主库 SHA | **始=终未变** | 8408DBC3…323D / 854DF859…BABD3 |

- **窄冒烟结论：通过**（无 blocker；A24 未假绿；claims/museum 绿；主库 SHA 未变；conflict=20 仍开）。
- 全量 pytest 对照父 tip@ed9f1a0（747p/1xfail）跳过。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**（未关）。
- 日志：wt/qa-tmp/qa-smoke-ac8f83c/。
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。

## 合入后冒烟 tip@25aa898（合入 arch@847e7f1；parents ac8f83c+847e7f1；含 eval/jinshi/report + algorithmOutputMode 契约）—— RM-红队QA @ 2026-10-25 16:02 Asia/Shanghai

**范围**：只读 worktree D:\RubbingMind\wt\qa-feature-smoke detach @ tip 25aa898ee882221bbd5affbdda20deceeb7058bc；合入后冒烟（DB SHA / A24 仍 xfail / G1+RT+Phase2+ES 抽检 / claims+museum / **npm build=tsc&&vite 必跑** / 开项勿关）。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parents | **确认** | HEAD=25aa898ee882221bbd5affbdda20deceeb7058bc；parents=ac8f83c7852419633b4ea12927fec6d75b12baba + 847e7f166ae3f6bc25a9fc8f0c801d0bf8438f2f；含 847e7f1 / ac8f83c / 2a553f9 / 5bf3836 / 12e8ce6 |
| 2 | vs ac8f83c | **4 files / +39/-5** | apps/web：api.ts + stele.ts + WorkbenchPage.tsx；docs MERGE_NOTE_algorithmOutputMode.md（类型契约 algorithmOutputMode / AdaptiveDiagnostics） |
| 3 | A24 | **仍 1p/1xfail / 未假绿** | pytest -k a24 → **1 passed / 1 xfailed**（3.92s）；qa-tmp/qa-smoke-25aa898/pytest-a24-25aa898.txt |
| 4 | G1 | **23 passed** | pytest -k "roi or g1"（2.57s） |
| 5 | RT | **31 passed** | 全部 test_rt*.py（4.21s）；含 test_rt008_010_013 |
| 6 | Phase2/AB8 | **35p / 1xfail** | -k "phase2 or ab8"（4.53s）；A24 相关 xfail 仍在 |
| 7 | ES 抽检 | **45 passed** | -k "es_derived or mechanism or evalsci or ES3 or ES4 or ES5"（6.59s） |
| 8 | claims | **ok / conflict 仍开** | --check → ok；claimFiles=28 conflict=20 openRows=36；**未** --write |
| 9 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 10 | **npm build（tsc+vite）** | **passed** |
pm run build = tsc && vite build；vite 5.4.21；exit 0；built in 15.66s；WorkbenchPage-CfM8fqt2.js / ReportsPage-e8S6O9Um.js；chunk>500kB warn only |
| 11 | static/index.html | **仍在** | size=90717 |
| 12 | 主库 SHA | **始=终未变** | rubbingmind=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D / evidence-v2=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3 |

- **合入后冒烟结论：通过**（无 blocker；tsc 绿；A24 未假绿；主库 SHA 未变；conflict=20 仍开）。
- 全量 pytest 对照父 tip@ed9f1a0（747p/1xfail）+ 本 tip 为前端类型契约，已用 G1/RT/Phase2/ES+A24 抽检覆盖。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**（未关）。
- 日志：wt/qa-tmp/qa-smoke-25aa898/。
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。


## 评测 tip 门禁 tip@b3452d2（R7 lag=177 证据戳；rebase 取代 a1ae0cc）相对 feature@25aa898；作者 RM-红队QA @ 2026-10-25 16:05 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-evalsci` detach @ tip `b3452d21bf4b8119466fcb546711acc49294f8da`；相对 **feature@25aa898ee882221bbd5affbdda20deceeb7058bc**；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非本任务进程；**未关** A24/R7/P1/RF-8/conflict/产品 RT。

**ancestry**：parent=`25aa898`；ahead/behind vs feature = **1/0**（FF 子提交）；`a1ae0cc`（旧 lag=174 @ac8f83c）已被 rebase 取代（本 tip 直接挂在 25aa898 上）。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip HEAD | **确认** | `b3452d21bf4b8119466fcb546711acc49294f8da`；subj=`docs(eval-sci): stamp R7 lag=177 after rebase onto feature@25aa898`；parent=25aa898 |
| 2 | feature base | **确认** | `25aa898ee882221bbd5affbdda20deceeb7058bc`（含 arch@847e7f1） |
| 3 | 文件范围 | **docs-only 2 files / +16/-4** | `ES_EVAL_PROGRESS.md` + `MECHANISM_HEAD_NOTE.md`（§14）；**0** museum_processing / 业务代码 |
| 4 | merge-tree vs **feature@25aa898** | 冲突 **0** | `merge-tree --write-tree` exit 0；tree `37fabca33bb36a2f3d86f05fc59024a134af2a5a`；changed in both=0 |
| 5 | 取代 a1ae0cc | **确认** | object 仍在；本 tip parent=25aa898（非 a1ae0cc）；MECHANISM §14 写明 rebase 取代 |
| 6 | R7 lag 证据 | **有戳 / 仍开** | `rev-list 7623a52..25aa898`=**176**（feature-base 惯例）；`7623a52..b3452d2`=**177**（tip-inclusive，与戳文 lag=177 一致）；**未**重跑 mechanism；**未关** R7 |
| 7 | A24 | **仍开 / xfail** | 全量跳过（纯 docs）；对照并行冒烟 tip@25aa898：`pytest -k a24` → **1 passed / 1 xfailed**；**门禁未关单** |
| 8 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3` |
| 9 | 开项 | **仍开** | A24/R7/P1/RF-8/conflict/产品 RT 本闸未关单 |

### 无 blocker

1. lag 戳文 177 = tip-inclusive；feature-base 惯例为 176（与 tip@2a553f9「feature lag + tip+1」记法一致）。非合入 blocker。
2. A24/R7 **仍开**；docs-only 证据戳，不关闭开项。

### 收尾

- 日志：`wt/qa-tmp/qa-eval-b3452d2/`（tip-meta / name-status / diffstat / merge-tree-* / r7-lag / a1ae0cc-superseded / sha-post / sha-match / SUMMARY）
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未关** A24/R7/P1/RF-8/conflict/产品 RT。
## 合入后窄冒烟 tip@b3452d2（FF 合入 eval docs；parent 25aa898；R7 lag=177 证据戳）—— RM-红队QA @ 2026-10-25 16:09 Asia/Shanghai

**范围**：只读 worktree D:\RubbingMind\wt\qa-feature-smoke detach @ tip b3452d21bf4b8119466fcb546711acc49294f8da；窄冒烟（DB SHA / A24 仍 xfail / claims+museum 抽检 / 开项勿关；全量对照父 tip@25aa898 跳过）。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **确认** | HEAD=b3452d21bf4b8119466fcb546711acc49294f8da；parent=25aa898ee882221bbd5affbdda20deceeb7058bc；FF 合入 eval@b3452d2 |
| 2 | 变更范围 vs 25aa898 | **docs-only** | 2 files / +16/-4：ES_EVAL_PROGRESS.md + MECHANISM_HEAD_NOTE.md（无业务代码 / museum_processing） |
| 3 | A24 | **仍 1p/1xfail / 未假绿** | pytest -k a24 → **1 passed / 1 xfailed**（3.07s）；日志 qa-tmp/qa-smoke-post-b3452d2/pytest-a24-b3452d2.txt |
| 4 | claims | **ok / conflict 仍开** | --json + --check → ok；claimFiles=28 conflict=20 openRows=36 pendingHuman=30；**未** --write |
| 5 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 6 | 主库 SHA | **始=终未变** | rubbingmind=8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D / evidence-v2=854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3 |

- **窄冒烟结论：通过**（无 blocker；A24 未假绿；claims/museum 绿；主库 SHA 未变；conflict=20 仍开）。
- 全量 pytest 对照父 tip@25aa898（抽检绿 / 父全量口径）跳过；本 tip 纯 docs。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**（未关）。
- 日志：wt/qa-tmp/qa-smoke-post-b3452d2/
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。


## 架构 tip 门禁 tip@89a3f6e（HealthResponse/getHealth samples_* + reportData algorithmOutputMode + AB 开项盘点）相对 feature@b3452d2；作者 RM-红队QA @ 2026-10-25 16:10 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-arch` detach @ tip `89a3f6e8318a959be7fc15c2af68025f88b50f96`；相对 **feature@b3452d21bf4b8119466fcb546711acc49294f8da**（附带 vs `25aa898ee882221bbd5affbdda20deceeb7058bc`）；未改业务内核；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非本任务进程；**未关** A24/R7/P1/RF-8/conflict/产品 RT。

**ancestry**：parent=`25aa898`；与 eval@`b3452d2` 为兄弟分叉（均挂 25aa898）；合入当前 feature 需 **merge（非 FF）**。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip HEAD | **确认** | `89a3f6e8318a959be7fc15c2af68025f88b50f96`；subj=`feat(arch): HealthResponse getHealth + sync algorithmOutputMode on reportData`；parent=25aa898 |
| 2 | feature base | **确认** | `b3452d21bf4b8119466fcb546711acc49294f8da`（FF 已含 eval docs；parent 25aa898） |
| 3 | 文件范围 vs 25aa898 | **3 files / +53/-1** | `api.ts` + `reportData.ts` + `AB_OPEN_AFTER_25aa898.md`；**0** museum_processing / claims |
| 4 | merge-tree vs **feature@b3452d2** | 冲突 **0** | `merge-tree --write-tree` exit 0；tree `f356913defb5a220f2e8a69536900d3f1b0371ec` |
| 5 | 附带 vs 25aa898 | 冲突 **0** | tree `8b55ea11877ce0ccee4c309ca548390e9dc84911` |
| 6 | HealthResponse / getHealth samples_* | **有证据 / 契约对齐** | `api.ts` 声明 `samples_available` / `samples_missing` / `samples_sha_mismatch`；`SteleService.getHealth()` → `/api/health`；与 `main.py` health_check 同名字段一致 |
| 7 | reportData algorithmOutputMode | **有证据** | `adaptiveDiagnostics.algorithmOutputMode` 三值字面量与 `stele.ts` AlgorithmOutputMode / ADR R2-12 对齐；另补 `changeStats` |
| 8 | AB 开项盘点 | **有文档 / 未关开项** | `AB_OPEN_AFTER_25aa898.md` 列 RT-006/RF-8/UI/CI 等仍开；本闸未关 |
| 9 | npm build | **通过** | `npm run build`（tsc+vite）exit 0；~14.91s；chunk warn only |
| 10 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3` |
| 11 | 开项 | **仍开** | A24/R7/P1/RF-8/conflict/产品 RT 本闸未关闭 |

### 非 blocker

1. `reportData.ts` 使用内联字面量联合，未 `import type { AlgorithmOutputMode } from …/stele`；取值与 `stele.ts` 一致，非合入 blocker。
2. `getHealth` / `samples_*` 类型已就绪，UI 消费仍属后续（AB 文档已记）；非 blocker。
3. 合入 feature@b3452d2 需 merge commit（兄弟分叉），非 FF。

### 收尾

- 日志：`wt/qa-tmp/qa-arch-89a3f6e/`（tip-meta / name-status / diffstat / merge-tree-* / sha-post / sha-match / npm-build.log / SUMMARY）
- **未**改业务内核；**未**写主库；**未** push；**未** C-08 --apply；**未关** A24/R7/P1/RF-8/conflict/产品 RT。


## 报告 tip 门禁 tip@5195b5b（algorithmOutputMode UI；相对 feature@b3452d2；附带 vs 25aa898）—— RM-红队QA @ 2026-10-25 16:11 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-report` detach @ tip `5195b5b79670d2bbf32ddd4f76e3944b30f66a89`；相对 **feature@b3452d21bf4b8119466fcb546711acc49294f8da**（FF 合入 eval docs 后最终 tip）；附带 vs `25aa898`。未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非本进程；**未关** RF-8/P1/R7/A24/conflict/产品 RT。

**ancestry**：parent=`25aa898`；vs feature@b3452d2 left-right=`1/1`（双方各 1 独有提交，需 merge 非 FF）；含 25aa898。

### 结论：**可合并**

| # | 项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tip HEAD | **确认** | `5195b5b79670d2bbf32ddd4f76e3944b30f66a89`；subj=`feat(report): 消费 algorithmOutputMode 决策链展示（ADR R2-12）`；parent=25aa898 |
| 2 | feature base | **确认** | 主 base=`b3452d2`（含 eval R7 lag=177）；附带 vs `25aa898` |
| 3 | 文件范围 vs b3452d2 | **7 UI/证据 + 2 docs 差** | tip 自身相对 25aa898：4 apps/web reports/* + 3 phase1-frontend/slice12/*（+110/-6）。vs b3452d2 另见 docs ES/MECHANISM 差（因 tip 未含 eval@b3452d2；三方合并 tip 未改 docs → 无冲突） |
| 4 | merge-tree vs **feature@b3452d2** | 冲突 **0** | `merge-tree --write-tree` exit 0；tree `cb2001190a0e3115638d4aa661ae69fa485de842` |
| 5 | merge-tree vs 25aa898 | 冲突 **0** | tree `1496850fbfc5b2618dad6c155914f99ff2c39893` |
| 6 | algorithmOutputMode UI | **有证据** | `reportData.ts`：`algorithmOutputModeView` / modes processed\|identity_no_evidence\|gate_fallback_original\|missing；`ArtifactRunReport` `data-testid=algorithm-output-mode`；`ReportPrintLayout` `print-algorithm-output-mode`；`ReportsPage` export `algorithmLayer`；slice12 evidence + ui txt |
| 7 | api.ts / stele.ts / HomePage | **未改** | vs b3452d2 与 vs 25aa898：`apps/web/src/services/api.ts` / `types/stele.ts` / `pages/HomePage.tsx` **diff 空** |
| 8 | npm build | **通过** | `tsc && vite build` vite 5.4.21 exit 0；built in 38.02s；ReportsPage-CyF6rdsH.js；chunk>500kB warn only |
| 9 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH=True |
| 10 | RF-8 | **仍开** | inventory 明示 awaiting user screenshot；本闸**未关**；HomePage 未改 |

### 无 blocker

1. RF-8 / P1 / R7 / A24 / conflict / 产品 RT **仍开**（本闸不关）。
2. vs b3452d2 非 FF（1/1），合入需 merge；冲突 0，非 blocker。

### 收尾

- 日志：`wt/qa-tmp/qa-report-5195b5b/`（tip-meta / name-status / merge-tree-write-tree / npm-build / sha-post / protected / slice12 副本 / SUMMARY）
- **未**改业务代码；**未**写主库；**未** push；**未** C-08 --apply；**未关** RF-8/P1/R7/A24/conflict/产品 RT。
## 合入后冒烟 tip@5a7b20c（merge report@5195b5b into feature；parents 9de0bab+5195b5b；含 algoMode UI + getHealth/samples_*）—— RM-红队QA @ 2026-10-25 16:20 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach @ tip `5a7b20c4f8f024a9c68adfb1799bc0399519d3b1`。tip-chase：相对起点 9de0bab 已前进（合入 report）；对**最终 tip** 做完整合入后冒烟。未改业务源码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

**vs 9de0bab**：2 commits（`5a7b20c` merge + `5195b5b` feat(report)）；7 files / +110/-6（ArtifactRunReport / ReportPrintLayout / reportData / ReportsPage + phase1-frontend/slice12/*）。合入时 reportData 冲突已解（AdaptiveDiagnostics + UI helpers）。含 report UI。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parents | **确认** | HEAD=`5a7b20c4f8f024a9c68adfb1799bc0399519d3b1`；parents=`9de0bab40ca3b05ba59cbb5b67405be94f4073af` + `5195b5b79670d2bbf32ddd4f76e3944b30f66a89`；subj=`merge(report): 5195b5b into feature/product-grade-upgrade (vs 9de0bab)` |
| 2 | ancestry | **确认** | 含 9de0bab / 5195b5b / 89a3f6e / b3452d2 |
| 3 | A24 | **仍 1p/1xfail / 未关** | `pytest -k a24` → **1 passed / 1 xfailed**（~84s）；未假绿 |
| 4 | G1 / Phase2 ROI | **通过** | `test_phase2_roi_fields.py`+`test_phase2_roi_arch.py` → **21 passed**；`-k g1` 3p；`-k "g1..g8"` 9p |
| 5 | Phase2+AB8 | **通过** | `-k "phase2 or ab8 or AB8"` → **35 passed / 1 xfailed** |
| 6 | ES spot | **通过** | `-k "es_derived or mechanism or evalsci or ES3/4/5"` → **45 passed** |
| 7 | claims | **ok / conflict 仍开** | `--check --json` ok；claimFiles=28 conflict=20 openRows=36 pendingHuman=30；**未** `--write` |
| 8 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 9 | algoMode UI | **有证据** | `data-testid=algorithm-output-mode` / `print-algorithm-output-mode`；`runAlgorithmOutputModeView`；ReportsPage `algorithmLayer`；reportData 导入 `AdaptiveDiagnostics`+`AlgorithmOutputMode`；slice12 evidence |
| 10 | samples_*/getHealth | **有证据（静态）** | `api.ts` HealthResponse=`samples_available/missing/sha_mismatch` + `SteleService.getHealth()`；`main.py` `/api/health` 同键；未起后端（端口未占，静态合同足够） |
| 11 | npm/tsc build | **通过** | `npm run build`（tsc+vite 5.4.21）exit 0；built in 42.63s；chunk>500kB warn only |
| 12 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH_PRE=True / MATCH_EXPECTED=True |

- **合入后冒烟结论：通过**。无 blocker；A24 仍 xfail；conflict=20 仍开；主库未写。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**（未关）。
- 日志：`wt/qa-tmp/qa-smoke-post-5a7b20c/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。

## 评测 tip 门禁 tip@c6de56e（R7 lag=182 证据戳；rebase 取代 802d51d）相对 feature@5a7b20c—— RM-红队QA @ 2026-10-25 16:21 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-evalsci` detach @ tip `c6de56ec77bcc9be6149e95fb3b51c7cd639c3b2`。门禁以 commit hash `5a7b20c` / `c6de56e` 为准（不盲信分支名 HEAD）。未改业务源码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip 存在 | **确认** | `git cat-file -t` = commit；HEAD=`c6de56ec77bcc9be6149e95fb3b51c7cd639c3b2`；parent=`5a7b20c4f8f024a9c68adfb1799bc0399519d3b1`；subj=`docs(eval-sci): stamp R7 lag=182 after rebase onto feature@5a7b20c`；author 2026-10-25 16:17 +0800 |
| 2 | vs 旧 802d51d | **rebase 取代** | 旧 `802d51d`（parent=9de0bab；lag=179）；与 c6de56e **互非祖先**；rev-list 802d51d..c6de56e=3 / 反向=1；已由本 tip 取代，勿用旧 tip |
| 3 | vs feature@5a7b20c merge-tree | **冲突 0** | merge-base=5a7b20c；left-right **0 behind / 1 ahead**（FF 子提交）；conflict_markers=0；tree=`4904557a991a4c7fc483f6f68c71cdacb9d503c2` |
| 4 | feature 分支 tip | **=5a7b20c** | `feature/product-grade-upgrade` 当前即 5a7b20c（本机未滞后；仍按 commit hash 门禁） |
| 5 | docs-only | **是** | 2 files / +20/-7：`ES_EVAL_PROGRESS.md` + `MECHANISM_HEAD_NOTE.md`；无 `.py/.ts/.tsx/.js`；**museum_processing 未改** |
| 6 | R7 lag=182 | **证据有 / 仍开** | `git rev-list --count 7623a52..c6de56e` = **182**；ES_EVAL_PROGRESS / MECHANISM_HEAD_NOTE §15 戳文 lag=182；台账写「仍开 / 只记账未假关」；**未关 R7** |
| 7 | A24 | **仍开 / xfail 未假绿** | `pytest -k a24` → **1 passed / 1 xfailed**（3.86s）；**未关 A24** |
| 8 | npm/tsc | **跳过** | docs-only 门禁，非必须 |
| 9 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；PRE=POST=MATCH |
| 10 | 开项 | **仍开** | P1 / RF-8 / R7 / A24 / conflict / 产品 RT 本闸未关单 |

- **门禁结论：可合并**。无 blocker；纯 docs 证据戳；FF 可合入 feature@5a7b20c。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**（未关）。
- 日志：`wt/qa-tmp/qa-eval-c6de56e/`（fetch / merge-tree / pytest-a24 / sha-pre/post / gate-summary）
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
## 合入后冒烟 tip@7e080c5（merge AB-8 arch@12f8883 into feature；parents 5a7b20c+12f8883；含 health-samples-banner）—— RM-红队QA @ 2026-10-25 16:29 Asia/Shanghai

**范围**：只读 worktree D:\RubbingMind\wt\qa-feature-smoke detach @ tip 7e080c5d670af123408b34a17bc072984e93fb5d。**最终 tip 锁定**（8178f46/109eec1/c6de56e 单独路径作废勿验）。未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

**vs 5a7b20c**：2 files / +42/-15（App.tsx + AB_OPEN_AFTER_25aa898.md）。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parents | **确认** | HEAD=7e080c5d670af123408b34a17bc072984e93fb5d；parents=5a7b20c4f8f024a9c68adfb1799bc0399519d3b1 + 12f8883cf30c99d11dbf741eba6400d6db142372；subj=merge: AB-8 health samples banner (arch) |
| 2 | AB-8 banner | **有证据** | data-testid=health-samples-banner；SteleService.getHealth() 读 samples_missing / samples_sha_mismatch；status==='degraded' 非阻断横幅；pi.ts HealthResponse 含 samples_available/missing/sha_mismatch；	est_rt002_samples.py health 报 missing |
| 3 | A24 | **仍 1p/1xfail / 未关** | pytest -k a24 → **1 passed / 1 xfailed**（~4s）；未伪绿 |
| 4 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 5 | npm/tsc build | **通过** |
pm run build（tsc+vite 5.4.21）exit 0；built in 14.99s；chunk>500kB warn only |
| 6 | 主库 SHA | **始=终未变** | rubbingmind=8408DBC3…323D / evidence-v2=854DF859…BABD3；MATCH_PRE=True / MATCH_EXPECTED=True |

- **合入后冒烟结论：通过**。无 blocker；A24 仍 xfail；开项未关。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**（未关单）。
- 日志：wt/qa-tmp/qa-smoke-post-7e080c5/
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。

## 评测 tip 门禁 tip@19255db（R7 lag=184 证据戳；rebase 取代 c6de56e/802d51d；相对 feature@7e080c5）—— RM-红队QA @ 2026-10-25 16:35 Asia/Shanghai

**范围**：只读 worktree D:\RubbingMind\wt\qa-evalsci detach @ tip 19255dbff2fc9454c51904521aa01fffb61f0186（以 commit hash 7e080c5 / 19255db 为准；**勿用** 8178f46/c6de56e/802d51d/109eec1）。未改业务源码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip 身份 | **确认** | git cat-file -t = commit；HEAD=19255dbff2fc9454c51904521aa01fffb61f0186；parent=7e080c5d670af123408b34a17bc072984e93fb5d；subj=docs(eval-sci): stamp R7 lag=184 after rebase onto feature@7e080c5 |
| 2 | vs 旧 tip | **rebase 取代** | 旧 c6de56e(parent=5a7b20c；lag=182) / 802d51d / 8178f46 / 109eec1 **均勿用**；本 tip parent=7e080c5 为当前可合 tip |
| 3 | vs feature@7e080c5 merge-tree | **冲突 0** | merge-base=7e080c5；left-right **0 behind / 1 ahead**；FF 单提交；conflict_markers=0；--write-tree=f4ebd44e10acfc66fd4975443f80fc8e52ba2a7c exit 0 |
| 4 | feature 分支 tip | **=7e080c5** | feature/product-grade-upgrade 当前即 7e080c5；与 tip parent 一致 |
| 5 | docs-only | **是** | 2 files / +20/-7：ES_EVAL_PROGRESS.md + MECHANISM_HEAD_NOTE.md；无 .py/.ts/.tsx/.js；**museum_processing 未改** |
| 6 | R7 lag=184 | **证据齐 / 仍开** | git rev-list --count 7623a52..19255db = **184**；ES_EVAL_PROGRESS / MECHANISM_HEAD_NOTE §15 声称 lag=184、台账写明仍开 / 只记账未假关。**未关 R7** |
| 7 | A24 | **仍开 / xfail 未伪绿** | pytest -k a24 → **1 passed / 1 xfailed**（3.85s）。**未关 A24** |
| 8 | npm/tsc | **跳过** | docs-only 门禁非必需 |
| 9 | 主库 SHA | **始=终未变** | rubbingmind=8408DBC3…323D / evidence-v2=854DF859…BABD3；PRE=POST=MATCH |
| 10 | 开项 | **仍开** | P1 / RF-8 / R7 / A24 / conflict / 产品 RT 门禁未关单 |

- **门禁结论：可合并**。无 blocker；纯 docs 证据戳；FF 可合入 feature@7e080c5。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**（未关单）。
- 日志：wt/qa-tmp/qa-eval-19255db/（merge-tree / pytest-a24 / sha / gate-summary）。
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
## 合入后窄冒烟 tip@19255db（ff-only eval docs onto feature@7e080c5；parent=7e080c5；docs-only +20/-7）—— RM-红队QA @ 2026-10-25 16:36 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach @ tip `19255dbff2fc9454c51904521aa01fffb61f0186`。**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

**vs 7e080c5**：2 files / +20/-7（`ES_EVAL_PROGRESS.md` + `MECHANISM_HEAD_NOTE.md`）docs-only。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **确认** | HEAD=`19255dbff2fc9454c51904521aa01fffb61f0186`；parent=`7e080c5d670af123408b34a17bc072984e93fb5d`；subj=`docs(eval-sci): stamp R7 lag=184 after rebase onto feature@7e080c5`；feature tip 同步锁定 |
| 2 | docs 合入 | **已进** | ES_EVAL_PROGRESS + MECHANISM_HEAD_NOTE（R7 lag=184 戳）；无业务代码 diff |
| 3 | AB-8 仍在 | **验证静** | `data-testid=health-samples-banner`；`getHealth` + `samples_missing`/`samples_sha_mismatch`；`degraded` 非阻断；`api.ts` HealthResponse；`main.py` /api/health samples_* |
| 4 | A24 | **仍 1p/1xfail / 未关** | `pytest -k a24` → **1 passed / 1 xfailed**（~4s）；未假绿 |
| 5 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 6 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH_PRE=True / MATCH_EXPECTED=True |

- **合入后窄冒烟结论：通过**（无 blocker；A24 仍 xfail，开项未关）。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**，未关台账。
- 日志：`wt/qa-tmp/qa-smoke-post-19255db/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。

## 报告 tip 门禁 tip@21a3dc7（slice13 inventory docs-only；相对 feature@19255db）—— RM-红队QA @ 2026-10-25 16:45 Asia/Shanghai

**范围**：只读 worktree D:\\RubbingMind\\wt\\qa-report detach @ tip 21a3dc7b92ad25460febd44b74e8f32240aea407；相对 feature@19255dbff2fc9454c51904521aa01fffb61f0186。未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **确认** | HEAD=21a3dc7b92ad25460febd44b74e8f32240aea407；parent=19255dbff2fc9454c51904521aa01fffb61f0186；subj=docs(report): slice13 对齐 19255db 开项盘点（无可叠 feat；RF-8 仍开）；author 2026-10-25 16:40 +0800 |
| 2 | vs feature@19255db merge-tree | **冲突 0** | merge-base=19255db；left-right **0 behind / 1 ahead**（FF 单提交）；conflict_markers=0；--write-tree=518515cb3ecec69c290389110df4b2c2b7603d58 exit 0 |
| 3 | docs-only | **是** | 2 files / +43：phase1-frontend/slice13/evidence.txt + p1-rf-open-inventory.txt；无 .py/.ts/.tsx/.js；**museum_processing 未改**；api.ts / stele.ts / HomePage / App.tsx **UNCHANGED** |
| 4 | 证据目录 slice13 | **有** | tip 内 phase1-frontend/slice13/：ALIGN HEAD=19255db；AB-8 / algoMode 已在 tip；扫描无可叠 report-page 代码 tip；明示 RF-8 still open（user confirm） |
| 5 | RF-8 | **仍开 / 未假关** | inventory：waiting user screenshot confirm；HomePage NOT modified；本闸**未关** RF-8 |
| 6 | npm/tsc | **跳过** | docs-only 窄门禁不要求 |
| 7 | museum | **passed** | validate_museum_v3.py items=28 images=84 sha256Match=84 |
| 8 | 主库 SHA | **始=终未变** | rubbingmind=8408DBC3…323D / evidence-v2=854DF859…BABD3；MATCH_EXPECTED=True |
| 9 | 开项 | **仍开** | P1 / RF-8 / R7 / A24 / conflict / 产品 RT 本闸未关单 |

- **门禁结论：可合并**（无 blocker；纯 docs 证据盘点；FF 可合入 feature@19255db）。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**（未关单）。
- 日志：wt/qa-tmp/qa-report-21a3dc7/（tip-meta / name-status / merge-tree-write-tree / validate-museum / sha-post / slice13 副本 / SUMMARY）
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。


## 评测 tip 门禁 tip@6f25bfc（R7 lag=185 证据戳；docs-only；相对 feature@19255db）— @ RM-红队QA @ 2026-10-25 16:50 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-evalsci` detach @ tip `6f25bfc897f5b3c1c444e52b0e384bda84c11d83`；以 commit hash `19255db` / `6f25bfc` 为准。未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程。**未关** P1/RF-8/R7/A24/conflict/产品 RT。与 report@21a3dc7 门禁并行。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **确认** | HEAD=`6f25bfc897f5b3c1c444e52b0e384bda84c11d83`；parent=`19255dbff2fc9454c51904521aa01fffb61f0186`；subj=`docs(eval-sci): ES-3 bootstrap CI 口径 + R7 lag stamp after feature@19255db` |
| 2 | vs feature@19255db merge-tree | **冲突 0** | merge-base=19255db；left-right **0 behind / 1 ahead**（FF 单提交）；conflict_markers=0；`--write-tree`=`97a6d6f3554b96e8126596dfb54f7e10677abd08` exit 0 |
| 3 | docs-only | **是** | 2 files / +63/-15：`ES_EVAL_PROGRESS.md` + `MECHANISM_HEAD_NOTE.md`；无 `.py/.ts/.tsx/.js`；**museum_processing 未改** |
| 4 | R7 lag=185 | **证据齐 / 仍开** | `git rev-list --count 7623a52..6f25bfc` = **185**；ES_EVAL_PROGRESS / MECHANISM_HEAD_NOTE §16 明示 lag=185、仍开 / 只记账未假关；**未关 R7**；文档无「已关」伪关闭 |
| 5 | A24 | **仍开 / xfail 未伪绿** | `pytest -k a24` → **1 passed / 1 xfailed**（7.23s）；**未关 A24** |
| 6 | museum | **passed** | `validate_museum_v3.py` items=28 images=84 sha256Match=84 |
| 7 | 主库 SHA | **始=终未动** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH_EXPECTED pre=post=True |
| 8 | 开项 | **仍开** | P1 / RF-8 / R7 / A24 / conflict / 产品 RT 本闸未关单 |
| 9 | npm/tsc | **跳过** | docs-only 窄门禁不要求 |

- **门禁结论：可合并**（无 blocker；纯 docs R7 证据戳；FF 可合入 feature@19255db）。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**（未关单）。
- 日志：`wt/qa-tmp/qa-eval-6f25bfc/`（tip-meta / name-status / merge-tree-write-tree / pytest-a24 / validate-museum / sha-pre/post / r7-lag / SUMMARY）。
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
## 合入后窄冒烟 tip@6f25bfc（ff-only eval docs onto feature@19255db；parent=19255db；docs-only +63/-15）—— RM-红队QA @ 2026-10-25 16:56 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach @ tip `6f25bfc897f5b3c1c444e52b0e384bda84c11d83`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

**vs 19255db**：2 files / +63/-15（`ES_EVAL_PROGRESS.md` + `MECHANISM_HEAD_NOTE.md`）docs-only。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **确认** | HEAD=`6f25bfc897f5b3c1c444e52b0e384bda84c11d83`；parent=`19255dbff2fc9454c51904521aa01fffb61f0186`；subj=`docs(eval-sci): ES-3 bootstrap CI 口径 + R7 lag stamp after feature@19255db`；feature tip 同步锁定 |
| 2 | docs 合入 | **已进** | ES_EVAL_PROGRESS + MECHANISM_HEAD_NOTE；R7 lag=185 仍开；无业务代码 diff |
| 3 | AB-8 抽检 | **仍在** | `data-testid=health-samples-banner`；`getHealth` + `samples_missing`/`samples_sha_mismatch`/`degraded`；`api.ts` HealthResponse；`main.py` /api/health samples_* |
| 4 | A24 | **仍开 1p/1xfail / 未关** | `pytest -k a24` → **1 passed / 1 xfailed**；未假绿 |
| 5 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 6 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH_PRE=True / MATCH_EXPECTED=True |

- **合入后窄冒烟结论：通过**（无 blocker；A24 仍 xfail，开项未关）。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**，未改台账关闭态。
- 日志：`wt/qa-tmp/qa-smoke-post-6f25bfc/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。

## 报告 tip 门禁 tip@bd7303e（slice13 inventory docs-only rebase；取代 21a3dc7；相对 feature@6f25bfc）—— RM-红队QA @ 2026-10-25 17:00 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-report` detach @ tip `bd7303e828c8e18988872712765b5c1dcfff6711`；相对 feature@`6f25bfc897f5b3c1c444e52b0e384bda84c11d83`。未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。旧 tip `21a3dc7` **作废勿用**。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **确认** | HEAD=`bd7303e828c8e18988872712765b5c1dcfff6711`；parent=`6f25bfc897f5b3c1c444e52b0e384bda84c11d83`；subj=`docs(report): slice13 对齐 6f25bfc 开项盘点（无可叠 feat；RF-8 仍开）` |
| 2 | vs feature@6f25bfc merge-tree | **冲突 0** | merge-base=6f25bfc；left-right **0 behind / 1 ahead**（FF 单提交）；conflict_markers=0；`--write-tree`=`d9175962620ffc705eafa96a3d4472f9c18cf450` exit 0 |
| 3 | docs-only | **是** | 2 files / +45：`phase1-frontend/slice13/evidence.txt` + `p1-rf-open-inventory.txt`；无 `.py/.ts/.tsx/.js`；**museum_processing / api / App / HomePage 未改** |
| 4 | 证据目录 slice13 | **有** | ALIGN HEAD=6f25bfc；明示 RF-8 still open（user confirm）；无可叠 report-page 代码 tip；AB-8/algoMode 已在 tip 祖先 |
| 5 | RF-8 | **仍开 / 未假关** | inventory：awaiting user screenshot confirm；HomePage NOT modified；本闸**未关** RF-8；checklist「用户已确认」视为 STALE |
| 6 | npm/tsc | **跳过** | docs-only 窄门禁；本 tip 无 apps/web 变更 |
| 7 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH_PRE=True / MATCH_EXPECTED=True |
| 8 | 开项 | **仍开** | P1 / RF-8 / R7 / A24 / conflict / 产品 RT 本闸未关单 |
| 9 | 旧 tip | **作废** | `21a3dc7`（base 19255db）已被 rebase 取代；勿再当可合 tip |

- **门禁结论：可合并**（无 blocker；纯 docs slice13；FF 可合入 feature@6f25bfc）。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**（未关单）。
- 日志：`wt/qa-tmp/qa-report-bd7303e/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
## 合入后窄冒烟 tip@bd7303e（ff-only report docs onto feature@6f25bfc；parent=6f25bfc；docs-only slice13 +45）—— RM-红队QA @ 2026-10-25 17:04 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach @ tip `bd7303e828c8e18988872712765b5c1dcfff6711`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

**vs 6f25bfc**：2 files / +45（`phase1-frontend/slice13/evidence.txt` + `p1-rf-open-inventory.txt`）docs-only。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **确认** | HEAD=`bd7303e828c8e18988872712765b5c1dcfff6711`；parent=`6f25bfc897f5b3c1c444e52b0e384bda84c11d83`；subj=`docs(report): slice13 对齐 6f25bfc 开项盘点（无可叠 feat；RF-8 仍开）`；feature tip 同步锁定 |
| 2 | docs 路径 | **已进** | slice13 evidence + p1-rf-open-inventory；RF-8 仍开写明；无业务代码 diff |
| 3 | AB-8 横幅 | **仍在** | `data-testid=health-samples-banner`；`getHealth` + `samples_missing`/`samples_sha_mismatch`/`degraded`；`api.ts` HealthResponse；`main.py` /api/health samples_* |
| 4 | A24 | **仍开 1p/1xfail / 未绿** | `pytest -k a24` → **1 passed / 1 xfailed**；未假关 |
| 5 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 6 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH_PRE=True / MATCH_EXPECTED=True |
| 7 | RF-8 | **仍开 / 未自关** | inventory：awaiting user screenshot confirm；HomePage NOT modified；门禁**未关** RF-8 |
| 8 | R7 | **仍开** | lag=`186`（rev-list 7623a52..HEAD）；未关 R7 |

- **合入后窄冒烟结论：通过**（无 blocker；A24 仍 xfail，开项未关）。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**；未在台账关闭态。
- 日志：`wt/qa-tmp/qa-smoke-post-bd7303e/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
## 评测 tip 门禁 tip@fa5bf1c（R7 lag stamp docs-only；对照 feature@bd7303e）— @ RM-红队QA @ 2026-10-25 17:19 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-evalsci` detach @ tip `fa5bf1c4a50a984ffb993a8f7a9787c07cb15e4e`；以 commit hash `bd7303e` / `fa5bf1c` 为准；未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程。**未关** P1/RF-8/R7/A24/conflict/产品 RT。主仓 feature tip 当时=`bd7303e828c8e18988872712765b5c1dcfff6711`（期望仍为 bd7303e；若漂移只记实）。

| # | 项 | 结论 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **确认** | HEAD=`fa5bf1c4a50a984ffb993a8f7a9787c07cb15e4e`；parent=`bd7303e828c8e18988872712765b5c1dcfff6711`；subj=`docs(eval-sci): R7 lag=186 stamp after feature@bd7303e + ES-3/4/5 续开项` |
| 2 | vs feature@bd7303e merge-tree | **冲突 0** | merge-base=bd7303e；left-right **0 behind / 1 ahead**；FF 单提交；`--write-tree`=`1dc8b66fffb07d9328926293d4bb339caa57162e` exit 0；无冲突消息 |
| 3 | docs-only | **是** | 2 files / +34/-18：`ES_EVAL_PROGRESS.md` + `MECHANISM_HEAD_NOTE.md`；无 `.py/.ts/.tsx/.js`；**museum_processing 未改** |
| 4 | R7 lag | **有条件 / 仍开** | 实测 `rev-list 7623a52..fa5bf1c`=**187**；`..bd7303e`=**186**。tip 正文自称 `rev-list ..HEAD`=186 且「相对 bd7303e 为 186」——与 tip HEAD 计数 **187** 差 1（把 parent lag 写成了 HEAD lag）。R7 **仍开** / 只举证未假关；**未关 R7**；文档无「已关闭」伪绿 |
| 5 | A24 | **仍开 / xfail 未伪绿** | `pytest -k a24` → **1 passed / 1 xfailed**（3.94s）；**未关 A24** |
| 6 | museum | **passed** | `validate_museum_v3.py` items=28 images=84 sha256Match=84 |
| 7 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH_EXPECTED=True |
| 8 | 开项 | **仍开** | P1 / RF-8 / R7 / A24 / conflict / 产品 RT 闸门未收口 |
| 9 | npm/tsc | **跳过** | docs-only 窄门禁不要求 |

- **门禁结论：有条件可合并**（无业务 blocker；FF docs-only；条件见下）。
- **条件**：合入前将 MECHANISM_HEAD_NOTE / ES_EVAL_PROGRESS 中「`rev-list 7623a52..HEAD`=186」改为与 tip HEAD 实测 **187** 一致，或删掉「..=HEAD」措辞、明确写「相对 feature@bd7303e lag=186」。否则 stamp 自述与 git 计数矛盾。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**；未收口、未假关。
- 日志：`wt/qa-tmp/qa-eval-fa5bf1c/`（diff-name-status / merge-tree / validate-museum / pytest-a24 / sha-check / r7 / SUMMARY）。
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
## 评测 tip 窄门禁 tip@46c7ded（R7 lag stamp 校正 docs-only；取代 fa5bf1c；对齐 feature@bd7303e）— @ RM-红队QA @ 2026-10-25 17:31 Asia/Shanghai

**范围**：只读 worktree D:\RubbingMind\wt\qa-evalsci detach @ tip 46c7ded94c7244a8fd410501a672f9a7c28cc963。以 commit hash bd7303e / 46c7ded 为准。未改业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程。**未关** P1/RF-8/R7/A24/conflict/产品 RT。门禁时 feature tip=bd7303e828c8e18988872712765b5c1dcfff6711（期望 bd7303e）。旧 tip fa5bf1c **作废勿用**。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **确认** | HEAD=46c7ded94c7244a8fd410501a672f9a7c28cc963；parent=bd7303e828c8e18988872712765b5c1dcfff6711；subj=docs(eval-sci): fix R7 lag stamp to measured HEAD rev-list (replace fa5bf1c) |
| 2 | vs feature@bd7303e merge-tree | **冲突 0** | merge-base=bd7303e；left-right **0 behind / 1 ahead**；FF 单提交；--write-tree=1928ab326b12f51248ff2cc8d92eace378d4655b；冲突行数=0 |
| 3 | docs-only | **是** | 2 files / +34/-18：ES_EVAL_PROGRESS.md + MECHANISM_HEAD_NOTE.md；无 .py/.ts/.tsx/.js；**museum_processing 未动** |
| 4 | R7 lag | **一致 / 仍开** | 实测
ev-list 7623a52..46c7ded=**187**；..bd7303e=**186**；MECHANISM §17 + ES_EVAL 正文 stamp=**187**，与 tip HEAD 实测一致（已取代 fa5bf1c 误标 186）；R7 **仍开** / 只记证未假关；**未关 R7** |
| 5 | A24 | **仍开 / xfail 未伪关** | pytest -k a24 → **1 passed / 1 xfailed**；**未关 A24** |
| 6 | museum | **passed** | validate_museum_v3.py items=28 images=84 sha256Match=84 |
| 7 | 主库 SHA | **始=末未变** | rubbingmind=8408DBC3…323D / evidence-v2=854DF859…BABD3；MATCH_EXPECTED=True |
| 8 | 开项 | **仍开** | P1 / RF-8 / R7 / A24 / conflict / 产品 RT 栅栏未收口 |
| 9 | npm/tsc | **跳过** | docs-only 窄门禁不要求 |

- **门禁结论：可合并**（业务无 blocker；FF docs-only；stamp 与实测一致为 187）。
- 旧 tip fa5bf1c 因 stamp 186≠实测 187 已作废；本 tip 校正后一致。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**，未假关、未改关。
- 日志：wt/qa-tmp/qa-eval-46c7ded/（diff-name-status / merge-tree / validate-museum / pytest-a24 / sha-check / r7 / stamp-check / SUMMARY）。
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
## 合入后窄冒烟 tip@46c7ded（ff-only eval docs onto feature@bd7303e；parent=bd7303e；docs-only lag stamp=187）—— RM-红队QA @ 2026-10-25 17:39 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach @ tip `46c7ded94c7244a8fd410501a672f9a7c28cc963`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

**vs bd7303e**：2 files — `docs/product-upgrade/ES_EVAL_PROGRESS.md` + `MECHANISM_HEAD_NOTE.md`（docs-only；stamp 与实测 rev-list=**187** 一致；取代 fa5bf1c）。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=`46c7ded94c7244a8fd410501a672f9a7c28cc963`；parent=`bd7303e828c8e18988872712765b5c1dcfff6711`；subj=`docs(eval-sci): fix R7 lag stamp to measured HEAD rev-list (replace fa5bf1c)`；feature tip 同 tip 锁定 |
| 2 | docs 边界 | **已核** | 仅 ES_EVAL_PROGRESS + MECHANISM_HEAD_NOTE；无业务代码 diff |
| 3 | lag stamp | **一致** | 实测 `git rev-list --count 7623a52..HEAD` = **187**；正文 stamp=187 |
| 4 | AB-8 横幅 | **仍在** | `data-testid=health-samples-banner`；`getHealth` + `samples_missing`/`samples_sha_mismatch`/`degraded`；`api.ts` HealthResponse；`main.py` /api/health samples_* |
| 5 | A24 | **仍开 1p/1xfail / 未关** | `pytest -k a24` → **1 passed / 1 xfailed**；未假绿 |
| 6 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 7 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH_PRE=True / MATCH_EXPECTED=True |
| 8 | RF-8 | **仍开 / 未假关** | inventory「awaiting user screenshot confirm；HomePage NOT modified」；本轮**未关** RF-8 |
| 9 | R7 | **仍开** | lag=`187`（rev-list 7623a52..HEAD）；未关 R7 |

- **合入后窄冒烟结论：通过**（无 blocker；A24 仍 xfail，开项未关）。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**（未在台账关闭态）。
- 日志：`wt/qa-tmp/qa-smoke-post-46c7ded/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。

## 完整门禁 tip@e662631（ES-3/4/5 paired-ref + caption/NLC；非窄 docs；parent=46c7ded）— 作者 RM-红队QA @ 2026-10-25 17:49 Asia/Shanghai

**范围**：worktree D:\RubbingMind\wt\qa-evalsci detach @ tip e66263185036b18c45682d1b980ced73bcf61898。**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

**声称核对**：4 files +207/−2 = eval_export_contract.py + 	est_es_derived_contracts.py + ES_EVAL_PROGRESS.md + MECHANISM_HEAD_NOTE.md（与 diff 一致）；**museum_processing 未改**。

| # | 项 | 结论 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **确认** | HEAD=e66263185036b18c45682d1b980ced73bcf61898；parent=46c7ded94c7244a8fd410501a672f9a7c28cc963；subj=docs/test(eval-sci): ES-3/4/5 paired-ref gate + full caption/NLC asserts；主仓 feature tip 门禁时=46c7ded94c7244a8fd410501a672f9a7c28cc963 |
| 2 | vs feature@46c7ded merge-tree | **冲突 0 / FF** | merge-base=46c7ded；ancestor OK；--write-tree=164a106758e7613da415aa97f06675972cd2473f；冲突消息=0；ahead=1 behind=0 |
| 3 | 变更面 | **符合声称** | 4 files / +207/−2；无 .ts/.tsx 无关扩大；**museum_processing 未改** |
| 4 | ES-3 证据 | **成立** | has_paired_reference；lift_claim_label 无配对先返未评价；liftClaimMetric=psnr；测试 	est_es3_unpaired_* / 	est_es3_export_summary_is_psnr_primary_* / frozen claimCounts |
| 5 | ES-4 证据 | **成立** | 	est_es4_all_mechanism_cases_have_caption_fields 全量 case 图注字段 + PNG 存在；pngBytesUntouched |
| 6 | ES-5 证据 | **成立** | 	est_es5_display_rows_align_one_to_one_with_nlc display↔NLC 1:1（caseId/method/split/degradation/psnrDelta/primaryMeasuredCauses） |
| 7 | pytest | **756 passed / 1 xfailed** | python -m pytest tests/ -q --tb=line @ tip；exit=0；相对 46c7ded 全集 +9（新 ES-3/4/5 门禁测）与声称一致 |
| 8 | A24 | **仍开 1p/1xfail / 未假绿** | pytest -k a24 → **1 passed / 1 xfailed**；**未关 A24** |
| 9 | R7 lag | **一致 / 仍开** | 实测
ev-list 7623a52..e662631=**188**；MECHANISM §18 + ES_EVAL 新段 stamp=188；**未关 R7** / 未重跑 mechanism |
| 10 | museum | **passed** | validate_museum_v3.py items=28 images=84 sha256Match=84 |
| 11 | 主库 SHA | **始=终未变** | rubbingmind=8408DBC3…323D / evidence-v2=854DF859…BABD3；PRE=POST=EXPECTED |
| 12 | 开项 | **仍开** | P1 / RF-8 / R7 / A24 / conflict / 产品 RT 栅栏未改关 |

- **门禁结论：可合并**（非窄 docs；契约测实跑通过；ES-3/4/5 有代码+测试证据；无业务 blocker）。
- 宣传与实现一致：配对参考门禁 / PSNR 主口径 / 全量图注 / display↔NLC 1:1 均有测覆盖；**未**发现需降级的空宣传。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**，未假关。
- 日志：wt/qa-tmp/qa-eval-e662631/（diff-stat / full-diff / pytest-full / pytest-a24 / validate-museum / sha-pre/post / SUMMARY）。
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
## 合入后冒烟 tip@e662631（ff-only eval@e662631 onto feature@46c7ded；parent=46c7ded；非窄 docs：契约+测试+2 docs；lag stamp=188）—— RM-红队QA @ 2026-10-25 17:56 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach @ tip `e66263185036b18c45682d1b980ced73bcf61898`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

**vs 46c7ded**：4 files · `experiments/eval_export_contract.py` + `tests/test_es_derived_contracts.py` + `ES_EVAL_PROGRESS.md` + `MECHANISM_HEAD_NOTE.md`（+207/−2）；stamp 与实测 rev-list=**188** 一致。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=`e66263185036b18c45682d1b980ced73bcf61898`；parent=`46c7ded94c7244a8fd410501a672f9a7c28cc963`；subj=`docs/test(eval-sci): ES-3/4/5 paired-ref gate + full caption/NLC asserts`；feature tip 同 tip 锁定 |
| 2 | diff 边界 | **吻合** | 恰 4 files（contract + tests + 2 docs）；无其它路径 |
| 3 | 契约测抽检 | **通过** | `pytest tests/test_es_derived_contracts.py -q` → **30 passed** |
| 4 | 全量 pytest | **通过** | `pytest tests/ -q` → **756 passed / 0 failed / 1 xfailed** |
| 5 | lag stamp | **一致** | 实测 `git rev-list --count 7623a52..HEAD` = **188**；文档 stamp=188 |
| 6 | AB-8 横幅 | **仍在** | `data-testid=health-samples-banner`；`getHealth` + `samples_missing`/`samples_sha_mismatch`/`degraded`；`api.ts` HealthResponse；`main.py` /api/health samples_* |
| 7 | A24 | **仍开 1p/1xfail / 未关** | `pytest -k a24` → **1 passed / 1 xfailed**；未假绿 |
| 8 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 9 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH_PRE=True / MATCH_EXPECTED=True |
| 10 | RF-8 | **仍开 / 未假关** | inventory 仍含 RF-8（awaiting user screenshot；HomePage NOT modified）；**未关** RF-8 |
| 11 | R7 | **仍开** | lag=`188`（rev-list 7623a52..HEAD）；未关 R7 |

- **合入后冒烟结论：通过**（无 blocker；A24 仍 xfail，开项未关）。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**（未在台账关闭状态）。
- 日志：`wt/qa-tmp/qa-smoke-post-e662631/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。


## 窄门禁 tip@7e99080（jinshi Claims 人工复核 Top15；parent=e662631；docs-only；与 arch@d6f434d 并行）—— RM-红队QA @ 2026-10-25 18:11 Asia/Shanghai

**范围**：只读 worktree D:\RubbingMind\wt\qa-jinshi detach @ 7e9908042811f4a8ace880ced8190687abb7c1ff；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。feature tip 仍=e66263185036b18c45682d1b980ced73bcf61898（尚未 FF；与 arch@d6f434d 并行）。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=7e9908042811f4a8ace880ced8190687abb7c1ff；parent=e66263185036b18c45682d1b980ced73bcf61898；subj=docs(jinshi): claims human-review priority top15 queue；ahead=1 behind=0 |
| 2 | merge-tree vs e662631 | **冲突 0 / 可 FF** | changed_in_both=0；<<<<<< =0；base=e662631 |
| 3 | diff 边界 | **docs-only 吻合** | 仅 docs/product-upgrade/CLAIMS_HUMAN_REVIEW_PRIORITY_TOP15.md（A +83）；无 claims DB / museum / 业务代码 / ci.yml |
| 4 | Top15 文档抽样 | **优先级清单非关单** | 明示不算关单；禁写 claims JSON；禁抬升 Verification；禁 C-08 --apply；异文并列不合并；表内 ≥15 行（conflict 为主 + pending_review）；**无假关/已关闭措辞** |
| 5 | 开项栅栏 | **仍开 / 未假关** | FINDINGS+MATRIX 仍含 RF-8/R7/A24/conflict/P1；文档本身亦声明不关闭 claims 28/28 与 conflict 开项 |
| 6 | 主库 SHA | **始=终未变** | rubbingmind=8408DBC3…323D / evidence-v2=854DF859…BABD3；MATCH_EXPECTED=True |

- **窄门禁结论：可合并**（docs-only；可 FF；无 blocker；开项未假关）。
- 合入顺序提醒：与 arch@d6f434d 并行不同文件；先过先 FF；若 feature tip 已动则对方需 rebase 后再窄核。
- 日志：wt/qa-tmp/qa-jinshi-7e99080/
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。

## 窄门禁 tip@d6f434d（arch RT-010 CI draft；parent=e662631；docs-only draft）—— RM-红队QA @ 2026-10-25 18:12 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-arch` detach @ tip `d6f434dd62938b95187da5877875f7cdcd55b2bd`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT（含 **RT-010 仍开**，draft≠关单）。

**vs feature@e662631**：docs-only 2 files · `docs/product-upgrade/ci-feature.draft.yml` + `docs/product-upgrade/RT010_CI_DRAFT.md`（+58）；**未**改 `.github/workflows/ci.yml`。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=`d6f434dd62938b95187da5877875f7cdcd55b2bd`；parent=`e66263185036b18c45682d1b980ced73bcf61898`；subj=`docs(ci): RT-010 draft-feature-gate (pytest + museum_v3 + npm build)`；feature tip=`e66263185036b18c45682d1b980ced73bcf61898` |
| 2 | ahead/behind | **1/0** | `git rev-list --left-right --count e662631...d6f434d` → `0\t1`（tip ahead=1 / behind=0） |
| 3 | merge-tree | **冲突 0 / 可 FF** | merge-tree vs e662631 无 CONFLICT/<<<<<<；可快进 |
| 4 | 变更面 | **docs-only +58** | 恰 2 files：`RT010_CI_DRAFT.md` + `ci-feature.draft.yml`；无其它路径 |
| 5 | 生效 ci.yml | **未碰** | name-status 无 `.github/workflows/ci.yml`；parent/tip blob=`56f507bcdc7069868fd92f3305df78a2c8804322` 相同 |
| 6 | draft 性质 | **草稿非生效** | `ci-feature.draft.yml` 位于 `docs/product-upgrade/`；头注释 `DRAFT ONLY — not under .github/workflows/`；新增 job `draft-feature-gate`（pytest + validate_museum_v3 + npm ci/build） |
| 7 | RT-006 / RF-8 / Tailwind | **未碰生效配置** | diff 仅 docs；正文写明暂缓 RT-008 tailwind v4；RT-006 / RF-8 仍等用户；无 Tailwind/RF-8/RT-006 生效面改动 |
| 8 | RT-010 产品单 | **仍开 / 未假关** | MD 声明「草案 / 产品 RT-010 保持开项」；draft 迁入 workflows 须 Green 再批；**本 tip 不关 RT-010** |
| 9 | museum / 主库 SHA | **可选核：未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；RM_MATCH=True / EV_MATCH=True（只读核，未写库） |
| 10 | 开项栅栏 | **仍开** | P1 / RF-8 / R7 / A24 / conflict / 产品 RT（含 RT-010）未假关 |

- **门禁结论：可合并**（窄门禁；docs-only draft；可 FF；未碰生效 ci.yml / RT-006 / RF-8 / Tailwind）。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT（**RT-010 仍开**）**仍开**，draft≠关单。
- 日志：`wt/qa-tmp/qa-arch-d6f434d/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
## 窄门禁 tip@4ef251e（report P1 开项+RF-8 截图清单；parent=e662631；docs-only；并行 arch@d6f434d / jinshi@7e99080）—— RM-红队QA @ 2026-10-25 18:13 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-report` detach @ tip `4ef251eaeea5e933df72fd19070a13352e28c8d0`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。feature tip 仍=`e66263185036b18c45682d1b980ced73bcf61898`（尚未 FF）。与 arch@d6f434d、jinshi@7e99080 并行（文件互不重叠）。

**vs feature@e662631**：docs-only 1 file → `docs/product-upgrade/REPORT_FRONTEND_P1_OPEN_AND_RF8_SHOTS.md`（+118）；**未**改 HomePage / apps/web。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=`4ef251eaeea5e933df72fd19070a13352e28c8d0`；parent=`e66263185036b18c45682d1b980ced73bcf61898`；subj=`docs(report): P1 开项盘点 + RF-8 确认截图清单（1920/1440；RF-8 仍开）`；feature tip=`e66263185036b18c45682d1b980ced73bcf61898` |
| 2 | ahead/behind | **1/0** | `git rev-list --left-right --count e662631...4ef251e` → `0\t1` |
| 3 | merge-tree | **冲突 0 / 可 FF** | `--write-tree`=`7de89f340c2dd1e4612c24936c8607d5ca5771d1`；无 CONFLICT/<<<<<<；ancestor OK |
| 4 | 变更面 | **docs-only +118** | 仅 `REPORT_FRONTEND_P1_OPEN_AND_RF8_SHOTS.md`（A）；无 HomePage / apps/web / ci.yml / museum_processing |
| 5 | RF-8 状态 | **仍开 / 未自关** | 文档 §B 明示 RF-8=仍开；禁止自关；禁止改 HomePage；CHECKLIST「用户已确认」标为过时 |
| 6 | 1440 证据 | **待补 / 未伪造** | phase1-frontend 下无 `*rf8*1440*` / `*home*core*1440*`；slice16 建议路径缺失；**未生成任何截图二进制**；phase0 `01_home_1440x900.png` 明示不可替代 |
| 7 | 1920 截图声明 | **与磁盘一致** | slice10/7/4/3 主证据均为实测 **1920×1080**；`*_1920w` before/after 实测 **1280×455**（文档如实写「不能单独当 1920 验收」） |
| 8 | P1 开项 | **仍开 / 未假关** | §A 表：RF-2..RF-11、P1-*、ES-3/5、algorithmOutputMode 等产品闸门均「仍开」；强调证据≠关单 |
| 9 | 主库 SHA | **始=末未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；RM_MATCH=True / EV_MATCH=True |
| 10 | 开项栅栏 | **仍开** | P1 / RF-8 / R7 / A24 / conflict / 产品 RT 未假关 |

- **窄门禁结论：可合并**（docs-only；可 FF；无业务 blocker；RF-8 仍开且 1440 待补未伪造）。
- 合入顺序提醒：与 arch@d6f434d / jinshi@7e99080 并行不同文件；先过先 FF；后过若 tip 已动则令对方 rebase 再窄核。
- 日志：`wt/qa-tmp/qa-report-4ef251e/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
## 合入后窄冒烟 tip@d6f434d（ff-only arch RT-010 CI draft onto feature@e662631；parent=e662631；docs-only）— ✓ RM-红队QA @ 2026-10-25 18:17 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach @ tip `d6f434dd62938b95187da5877875f7cdcd55b2bd`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/RT-010/conflict/产品 RT。

**vs e662631**：2 files → `docs/product-upgrade/RT010_CI_DRAFT.md` + `docs/product-upgrade/ci-feature.draft.yml`（docs-only；**未碰** `.github/workflows/ci.yml`）。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=`d6f434dd62938b95187da5877875f7cdcd55b2bd`；parent=`e66263185036b18c45682d1b980ced73bcf61898`；subj=`docs(ci): RT-010 draft-feature-gate (pytest + museum_v3 + npm build)`；feature tip = tip 锁定 |
| 2 | docs 边界 | **已核** | 仅 RT010_CI_DRAFT + ci-feature.draft.yml；无业务代码 diff |
| 3 | 生效 ci.yml | **未碰** | `.github/workflows/ci.yml` 不在 diff；name-only 空 |
| 4 | AB-8 横幅 | **仍在** | `data-testid=health-samples-banner`；`getHealth` + `samples_missing`/`samples_sha_mismatch`/`degraded` |
| 5 | A24 | **仍开 1p/1xfail / 未关** | `pytest -k a24` → **1 passed / 1 xfailed**；未假绿 |
| 6 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 7 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH_PRE=True / MATCH_EXPECTED=True |
| 8 | RF-8 | **仍开 / 未假关** | inventory/evidence 仍列 RF-8；本轮**未关** RF-8 |
| 9 | R7 | **仍开** | lag=`189`（rev-list 7623a52..HEAD）；未关 R7 |
| 10 | RT-010 | **仍开（仅 draft）** | 仅 docs 草案；生效 workflows 未改；未关 RT-010 |

- **合入后窄冒烟结论：通过**（无 blocker；A24 仍 xfail，开项未关）。
- 开项 P1 / RF-8 / R7 / A24 / RT-010 / conflict / 产品 RT **仍开**（未在台账关闭态）。
- 日志：`wt/qa-tmp/qa-smoke-post-d6f434d/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。

## 完整门禁 tip@8e72315（eval ES-3 dry-run + ES-6 E-05 草案；parent=e662631；含代码）— RM-红队QA @ 2026-10-25 18:19 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-evalsci` detach @ tip `8e7231572229999da5a50fe22eb93666acc0d3c0`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。

**vs parent@e662631**：8 files +412（docs×4 + experiments×2 + tests×2）；**非窄 docs**；merge-tree 冲突 0 / 可 FF。

**feature 现状提示**：门禁期间 feature 已 FF 至 `d6f434dd62938b95187da5877875f7cdcd55b2bd`（arch RT-010 draft）。旧 tip@8e72315 相对新 tip **diverged 1/1**（共同祖先 e662631；文件无重叠；merge-tree vs d6f434d 亦干净）。**合入前须 rebase 到 d6f434d 后再窄核/FF**；QA **未**自行 merge。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=`8e7231572229999da5a50fe22eb93666acc0d3c0`；parent=`e66263185036b18c45682d1b980ced73bcf61898`；subj=`docs/test(eval-sci): ES-3 bootstrap dry-run + ES-6 E-05 gate draft`；门禁时 feature=`d6f434dd62938b95187da5877875f7cdcd55b2bd` |
| 2 | ahead/behind vs e662631 | **1/0** | `git rev-list --left-right --count e662631...8e72315` → `0\t1` |
| 3 | merge-tree vs e662631 | **冲突 0 / 可 FF** | `--write-tree`=`98604554b928bbdf0d7a75a5f5f5e9bd9c905a3b`；无 CONFLICT |
| 4 | vs feature@d6f434d | **diverged 1/1；冲突 0** | MB=e662631；merge-tree=`313af0d70fa27a8995d615537d17cefedc7089bb`；文件与 RT-010 draft **无重叠**；**须 rebase 后再窄核** |
| 5 | 变更面 | **8 files +412** | ES3_BOOTSTRAP_DRY_RUN / ES6_E05_GATE_DRAFT / ES_EVAL_PROGRESS / MECHANISM_HEAD_NOTE / ci_bootstrap_dry_run.py / eval_export_contract.py / test_es3_es6_gate_skeletons.py / test_es_derived_contracts.py；**无** museum_processing / 主库路径 / 生效 ci.yml |
| 6 | dry-run 只读 | **通过** | `ci_bootstrap_dry_run.py`：`wroteDerived=False` / `recomputedBootstrap=False` / openFindings 保留 appliedStatusSha256 漂移；**不写 derived、不重算 bootstrap、不伪绿** |
| 7 | ES-6 骨架 | **仍开** | 草案文案含「未关/仍进行中」；G1 像素相等断言 **不**关 ES-6；TASK_BOARD 未关 |
| 8 | pytest 全量 | **763 passed / 1 xfailed / 0 failed** | `python -m pytest tests/ -q --tb=line` EXIT=0；约 67s；相对 e662631 的 756p **+7** |
| 9 | 契约/骨架抽检 | **37 passed** | test_es_derived_contracts + test_es3_es6_gate_skeletons |
| 10 | A24 | **仍开 3p/1xfail** | `-k a24`：3 passed / 1 xfailed（含 Top-k 未评测伴生）；**未关**伪报 Top-k |
| 11 | R7 lag | **189=stamp；仍开** | `git rev-list --count 7623a52..HEAD`=189；与 MECHANISM_HEAD_NOTE §19 / ES_EVAL_PROGRESS 一致；未跑 mechanism_cases.py |
| 12 | museum | **passed 28/84** | validate_museum_v3：items=28 images=84 sha256Match=84 |
| 13 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；PRE=POST=EXPECTED |
| 14 | 开项栅栏 | **仍开** | P1 / RF-8 / R7 / A24 / conflict / 产品 RT 未假关 |

- **完整门禁结论：可合并（相对 parent=e662631）**；证据齐；未伪绿。
- **合入前置**：feature 已在 d6f434d → **先 rebase 到 d6f434d，再窄核/FF**；旧 8e72315 勿直接 FF 到当前 tip。
- 日志：`wt/qa-tmp/qa-eval-8e72315/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。

## 红队窄核 tip@f27719c（jinshi Top15 rebase←d6f434d；取代旧 tip 7e99080）— RM-红队QA @ 2026-10-25 18:19 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-jinshi` detach @ tip `f27719cc64c3b4683af54bdcb67583cbed69c887`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/conflict/产品 RT。旧 tip `7e99080` **作废勿合**。

**vs feature@d6f434d**：1 file 仅 `docs/product-upgrade/CLAIMS_HUMAN_REVIEW_PRIORITY_TOP15.md`（+83）；docs-only；blob 与旧 tip `7e99080` **相同**（纯 rebase）。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent / feature | **锁定** | tip=`f27719cc64c3b4683af54bdcb67583cbed69c887`；parent=`d6f434dd62938b95187da5877875f7cdcd55b2bd`；feature HEAD=`d6f434dd62938b95187da5877875f7cdcd55b2bd`；subj=`docs(jinshi): claims human-review priority top15 queue` |
| 2 | ahead/behind | **可 FF** | ahead=1 behind=0 |
| 3 | merge-tree | **干净** | struct_conflicts=0；`merge-tree --write-tree` 成功；仅 `added in remote` 新 docs |
| 4 | 变更边界 | **docs-only** | 仅 CLAIMS_HUMAN_REVIEW_PRIORITY_TOP15.md +83；无 claims/主库/馆藏/museum_processing |
| 5 | Top15 抽样 | **优先队列非关单** | 明示「开项仍开 / 不是关闭声明」；不定论/不合并异文/不抬升 Verification/不 C-08；conflict 表行≥10；无关单/假关用语 |
| 6 | 开项栅栏 | **仍开 / 未假关** | P1/RF-8/R7/A24/conflict 台账仍开 |
| 7 | 主库 SHA | **未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH_EXPECTED=True |

- **红队窄核结论：可合并**（可 FF；无 blocker）。
- 开项 P1 / RF-8 / R7 / A24 / conflict / 产品 RT **仍开**（未在台账关闭态）。
- 日志：`wt/qa-tmp/qa-jinshi-f27719c/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。

## 红队窄核 report@60f967c（RF-8 清单 rebase←d6f434d）— 2026-10-25 18:21 Asia/Shanghai

- **判决：可合并（相对 d6f434d）**；**合入条件**：若 feature 已/将到 `f27719c`，须 **rebase 新 tip 后再合**（勿直接 FF 本 tip）。
- tip=`60f967cec58c0cd9315aa8967eec2c649da47d0c` parent=`d6f434dd62938b95187da5877875f7cdcd55b2bd`
- 主仓 tip@核时=`f27719cc64c3b4683af54bdcb67583cbed69c887`；qa-feature-smoke=`d6f434dd62938b95187da5877875f7cdcd55b2bd`
- merge-tree vs d6f434d：**CLEAN**；ahead/behind=**1/0**；可 FF vs d6f434d
- 变更：**docs-only** 1 file +118：`docs/product-upgrade/REPORT_FRONTEND_P1_OPEN_AND_RF8_SHOTS.md`
- **未改** HomePage / apps/web / 生效 ci.yml
- **RF-8 仍开**；1440×900 **待补/缺失未伪造**；P1 开项仍开（盘点文档，非关票）
- 旧 tip `4ef251e` **作废勿合**
- 主库 SHA 未变：8408DBC3…323D / 854DF859…BABD3（MATCH）
- 开项勿假关：RF-8/R7/A24/P1/conflict 仍开
- 日志：`wt/qa-tmp/qa-report-60f967c/`
- STOP=否（窄核完成）；未 push / 未 commit / 未 merge
## 合入后窄冒烟 tip@f27719c（ff-only jinshi Claims Top15 onto feature@d6f434d；parent=d6f434d；docs-only） · RM-红队QA @ 2026-10-25 18:24 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach @ tip `f27719cc64c3b4683af54bdcb67583cbed69c887`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/RT-010/conflict/产品 RT。

**vs d6f434d**：1 file → `docs/product-upgrade/CLAIMS_HUMAN_REVIEW_PRIORITY_TOP15.md`（docs-only；+83；优先级队列，非关单）。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=`f27719cc64c3b4683af54bdcb67583cbed69c887`；parent=`d6f434dd62938b95187da5877875f7cdcd55b2bd`；subj=`docs(jinshi): claims human-review priority top15 queue`；feature tip = tip 锁定 |
| 2 | docs 边界 | **已核** | 仅 CLAIMS_HUMAN_REVIEW_PRIORITY_TOP15.md；无业务代码 diff；未改 HomePage / claims 数据 |
| 3 | AB-8 横幅 | **仍在** | `data-testid=health-samples-banner`；`getHealth` + `samples_missing`/`samples_sha_mismatch`/`degraded` |
| 4 | A24 | **仍开 1p/1xfail / 未关** | `pytest -k a24` → **1 passed / 1 xfailed**；未假绿 |
| 5 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 6 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH_PRE=True / MATCH_EXPECTED=True |
| 7 | RF-8 | **仍开 / 未假关** | inventory/evidence 仍列 RF-8；本 tip **未关** RF-8 |
| 8 | R7 | **仍开** | lag=`190`（rev-list 7623a52..HEAD）；未关 R7 |
| 9 | RT-010 | **仍开（draft 仍在）** | 本 tip 未碰；先前 draft 合入后生效 workflows 仍未改 |
| 10 | conflict / 产品 RT | **仍开** | Top15 为人工复核优先级队列，明确非关单 / 非抬 verification / 非 C-08 |

- **合入后窄冒烟结论：通过**（无 blocker；A24 仍 xfail，开项未假关）。
- 开项 P1 / RF-8 / R7 / A24 / RT-010 / conflict / 产品 RT **仍开**（未在台账关闭态）。
- 日志：`wt/qa-tmp/qa-smoke-post-f27719c/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。


## 窄核 report@0c1ac0c（RF-8 清单 rebase←f27719c）· RM-红队QA @ 2026-10-25 18:31 Asia/Shanghai

- **判决：可合并**（相对 feature@f27719c；可 FF；docs-only）
- tip=`0c1ac0cf5acc8faa4a066ae26a384dee536a428e` parent=`f27719cc64c3b4683af54bdcb67583cbed69c887`
- 主仓 tip@核验时=`f27719cc64c3b4683af54bdcb67583cbed69c887`；qa-feature-smoke=`f27719cc64c3b4683af54bdcb67583cbed69c887`；qa-report detach=`0c1ac0cf5acc8faa4a066ae26a384dee536a428e`
- merge-tree vs f27719c：**CLEAN**；ahead/behind=**1/0** → 可 FF
- 变更：**docs-only** 1 file +118：`docs/product-upgrade/REPORT_FRONTEND_P1_OPEN_AND_RF8_SHOTS.md`
- **未改** HomePage / apps/web / 生效 ci.yml
- **RF-8 仍开**；1440×900 **待补/缺失未伪造**；P1 开项仍开（盘点文档，非关单）
- 旧 tip `60f967c` / `4ef251e` **作废勿合**
- 主库 SHA 未变：8408DBC3…323D / 854DF859…BABD3（MATCH）
- 开项未假关：RF-8/R7/A24/P1/conflict 仍开
- 日志：`wt/qa-tmp/qa-report-0c1ac0c/`
- STOP=否（窄核完成；未 push / 未 commit / 未 merge）

## 红队门禁 tip@40acb18（eval ES-3 dry-run + ES-6 E-05；rebase←f27719c；旧 tip 作废）· RM-红队QA @ 2026-10-25 18:34 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-evalsci` detach @ tip `40acb18ab934d406dd3e00dbb1cbd731ab86786d`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未假关** P1/RF-8/R7/A24/ES-6/conflict/产品 RT。

**vs parent@f27719c**：8 files +419/−1（docs×4 + experiments×2 + tests×2）；**非窄 docs**；merge-tree 冲突 0 / 可 FF。

**合入前提（tip 可能再动）**：门禁相对 parent=`f27719cc64c3b4683af54bdcb67583cbed69c887`（f27719c）**可合并 / 可 FF**。 Green 已令架构 FF report@`0c1ac0cf5acc8faa4a066ae26a384dee536a428e`；**若 feature 已到 / 将到 `0c1ac0c`，本 tip@40acb18 须 rebase 后再合**（文件与 RF-8 清单不重叠，但 parent 链会变）。**勿**直接 FF 旧 tip；**QA 未**自行 merge。门禁当时 feature=`0c1ac0cf5acc8faa4a066ae26a384dee536a428e`。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **通过** | HEAD=`40acb18ab934d406dd3e00dbb1cbd731ab86786d`；parent=`f27719cc64c3b4683af54bdcb67583cbed69c887`；subj=`docs/test(eval-sci): ES-3 bootstrap dry-run + ES-6 E-05 gate draft`；门禁时 feature=`0c1ac0cf5acc8faa4a066ae26a384dee536a428e` |
| 2 | ahead/behind vs f27719c | **1/0** | `git rev-list --left-right --count f27719c...40acb18` → `0\t1` |
| 3 | merge-tree vs f27719c | **冲突 0 / 可 FF** | `--write-tree`=`e9340a8d25d5d445524849bed2e4d1a78ea5a683`；无 CONFLICT |
| 4 | 变更集 | **8 files +419/−1** | ES3_BOOTSTRAP_DRY_RUN / ES6_E05_GATE_DRAFT / ES_EVAL_PROGRESS / MECHANISM_HEAD_NOTE / ci_bootstrap_dry_run.py / eval_export_contract.py / test_es3_es6_gate_skeletons.py / test_es_derived_contracts.py；**无** museum_processing / 馆藏路径 / 生效 ci.yml / HomePage |
| 5 | 旧 tip | **作废勿合** | `dfbf8f0` / `8e72315` 明确作废；本 tip 为 rebase←f27719c |
| 6 | dry-run 只读 | **通过** | 实跑 `python -m experiments.ci_bootstrap_dry_run`：`wroteDerived=false` / `recomputedBootstrap=false` / `hasOpenFindings=true`（appliedStatusSha256 漂移记开项）；**未写 derived、未重算 bootstrap、未伪绿** |
| 7 | ES-6 草案 | **仍开** | `ES6_E05_GATE_DRAFT.md` 标明进行中/未关/勿伪绿；G1 引擎单测≠关 ES-6；TASK_BOARD 未关 |
| 8 | pytest 全量 | **763 passed / 1 xfailed / 0 failed** | `python -m pytest tests/ -q --tb=line` EXIT=0 |
| 9 | 契约/骨架抽检 | **37 passed** | test_es_derived_contracts + test_es3_es6_gate_skeletons |
| 10 | A24 | **仍开** | `-k a24` 含 xfail；Top-k 未落地；**未**伪绿 Top-k |
| 11 | R7 lag | **191=stamp；仍开** | `git rev-list --count 7623a52..HEAD`=191；与 MECHANISM_HEAD_NOTE §20 / ES_EVAL_PROGRESS 一致；未跑 mechanism_cases.py |
| 12 | museum | **passed 28/84** | validate_museum_v3：items=28 images=84 sha256Match=84 |
| 13 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；PRE=POST=EXPECTED |
| 14 | 开项栅栏 | **仍开** | P1 / RF-8 / R7 / A24 / ES-6 / conflict / 产品 RT 未假关 |

- **红队门禁结论：相对 f27719c 可合并（可 FF）**；证据齐；未伪绿。
- **若 feature 已到 / 将到 report@0c1ac0c：须 rebase 后再合**（勿合旧 tip；QA 未自行 merge）。
- 日志：`wt/qa-tmp/qa-eval-40acb18/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
## 合入后窄冒烟 tip@0c1ac0c（ff-only report P1开项+RF-8截图清单 onto feature@f27719c；parent=f27719c；docs-only） · RM-红队QA @ 2026-10-25 18:39 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach @ tip `0c1ac0cf5acc8faa4a066ae26a384dee536a428e`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/RT-010/conflict/红队 RT。

**vs f27719c**：1 file → `docs/product-upgrade/REPORT_FRONTEND_P1_OPEN_AND_RF8_SHOTS.md`（docs-only；+118；开项盘点+截图清单，非关单）。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=`0c1ac0cf5acc8faa4a066ae26a384dee536a428e`；parent=`f27719cc64c3b4683af54bdcb67583cbed69c887`；subj=`docs(report): P1 开项盘点 + RF-8 确认截图清单（1920/1440；RF-8 仍开）`；feature tip = tip 一致 |
| 2 | docs 边界 | **守住** | 仅 REPORT_FRONTEND_P1_OPEN_AND_RF8_SHOTS.md；无业务代码 diff；**未改** HomePage / apps/web |
| 3 | AB-8 横幅 | **仍在** | `data-testid=health-samples-banner`；`getHealth` + `samples_missing`/`samples_sha_mismatch`/`degraded` |
| 4 | A24 | **仍开 1p/1xfail / 未伪绿** | `pytest -k a24` → **1 passed / 1 xfailed**；未强关 |
| 5 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 6 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH_PRE=True / MATCH_EXPECTED=True |
| 7 | RF-8 | **仍开 / 未假关** | inventory/evidence 仍列 RF-8；本 tip 清单写明 1440 待补；**未改** RF-8 / HomePage |
| 8 | R7 | **仍开** | lag=`191`（rev-list 7623a52..HEAD）；未关 R7 |
| 9 | RT-010 | **仍开（draft 仍在）** | 本 tip 未碰；先前 draft 仍在；生效 workflows 仍未改 |
| 10 | conflict / 红队 RT | **仍开** | 清单为开项盘点+截图待补，明确非关单 / 不抬 verification / 无 C-08 |

- **合入后窄冒烟结论：通过**（无 blocker；A24 仍 xfail；开项未假关）。
- 开项 P1 / RF-8 / R7 / A24 / RT-010 / conflict / 红队 RT **仍开**（未在台账关闭态）。
- 日志：`wt/qa-tmp/qa-smoke-post-0c1ac0c/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
## 窄门禁 tip@d376dbc（arch CI draft 扩展 + RT-006 决策备忘；parent=0c1ac0c；docs-only）— RM-红队QA @ 2026-10-25 18:47 Asia/Shanghai

**范围**：只读 worktree D:\RubbingMind\wt\qa-arch detach @ tip d376dbcabced081da22619dbe5a459a5520440df；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未假关** RT-006/RT-010/P1/RF-8/R7/A24/conflict。

**vs 0c1ac0c**：3 files +114/−5，全部 docs/product-upgrade（RT006_USER_DECISION_BRIEF.md 新增、RT010_CI_DRAFT.md / ci-feature.draft.yml 扩展）；**未碰** .github/workflows/ci.yml（blob 前后相同）；**未碰** DeduceRequest / static/ 业务路径。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent / feature | **锁定** | HEAD=d376dbcabced081da22619dbe5a459a5520440df；parent=0c1ac0cf5acc8faa4a066ae26a384dee536a428e；feature/product-grade-upgrade=0c1ac0cf5acc8faa4a066ae26a384dee536a428e；ahead=1 behind=0 |
| 2 | merge-tree | **CLEAN / 可 FF** | conflicts=0；parent==base → fast-forward |
| 3 | docs-only 边界 | **守住** | 仅 3 个 docs 路径；无生效 ci.yml；无 DeduceRequest/static 业务改动 |
| 4 | RT006 brief | **备忘非关闭** | 标题含「备忘」；状态「等用户 widget 拍板」；「不自选执行」；列 A/B/C 待选；**未**自选/未声称已决定；约束：仅 widget 明确或 Green 下令后才改文件 |
| 5 | RT-006 | **仍开 / 未假关** | brief 本身声明待拍板；台账不关闭 |
| 6 | RT-010 | **仍开（draft 扩展）** | 仅扩展 ci-feature.draft.yml + RT010 说明；生效 workflows 未改；开项仍开 |
| 7 | 主库 SHA | **未变** | rubbingmind=8408DBC3…323D / evidence-v2=854DF859…BABD3；MATCH_EXPECTED=True |
| 8 | 并行 | **知情** | 与 eval@4b17bc5 并行；本 tip 未 FF eval；若本 tip 先合入则 eval 需 rebase |

- **窄门禁判决：可合并**（docs-only；可 FF；无 blocker）。
- 开项 P1 / RF-8 / R7 / A24 / **RT-006** / **RT-010** / conflict **仍开**（未由台账关闭态）。
- 日志：wt/qa-tmp/qa-arch-d376dbc/
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。

## 红队门禁 tip@4b17bc5（eval ES-3 dry-run + ES-6 E-05；rebase←0c1ac0c）— RM-红队QA @ 2026-10-25 18:48 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-evalsci` detach @ tip `4b17bc5556e0eceff6f603465bbf37ba77934c34`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非已进程；**未假关** P1/RF-8/R7/A24/ES-6/conflict/产品 RT。

**vs parent@0c1ac0c**：8 files +419/−1（docs×4 + experiments×2 + tests×2）；**非窄 docs**；merge-tree 冲突 0 / 可 FF。

**合入条件**：门禁相对 parent=`0c1ac0cf5acc8faa4a066ae26a384dee536a428e`（0c1ac0c）**可合并 / 可 FF**；结案时 feature 仍锁 parent。并行 Green 派 arch@d376dbc 窄门禁——若 FF 前 tip 被动到该 tip，则本 tip 须 rebase。旧 tip `40acb18`/`dfbf8f0`/`8e72315` **作废勿合**。**QA 未**自行 merge/push。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **通过** | HEAD=`4b17bc5556e0eceff6f603465bbf37ba77934c34`；parent=`0c1ac0cf5acc8faa4a066ae26a384dee536a428e`；subj=`docs/test(eval-sci): ES-3 bootstrap dry-run + ES-6 E-05 gate draft`；结案 feature=`0c1ac0cf5acc8faa4a066ae26a384dee536a428e` |
| 2 | ahead/behind vs 0c1ac0c | **1/0** | `git rev-list --left-right --count 0c1ac0c...4b17bc5` → `0\t1` |
| 3 | merge-tree vs 0c1ac0c | **冲突 0 / 可 FF** | `--write-tree`=`5ec0b37646db66f102bbef74e6ecee408620636a`；无 CONFLICT |
| 4 | 变更集 | **8 files +419/−1** | ES3_BOOTSTRAP_DRY_RUN / ES6_E05_GATE_DRAFT / ES_EVAL_PROGRESS / MECHANISM_HEAD_NOTE / ci_bootstrap_dry_run.py / eval_export_contract.py / test_es3_es6_gate_skeletons.py / test_es_derived_contracts.py；**无** museum_processing / 馆藏路径 / 生效 ci.yml / HomePage |
| 5 | 旧 tip | **作废勿合** | `40acb18` / `dfbf8f0` / `8e72315` 明确作废；本 tip 为 rebase←0c1ac0c |
| 6 | dry-run 只读 | **通过** | 实跑 `python -m experiments.ci_bootstrap_dry_run`：`wroteDerived=false` / `recomputedBootstrap=false` / `hasOpenFindings=true`（appliedStatusSha256 漂移记开项）；**未写 derived、未重算 bootstrap、未伪绿** |
| 7 | ES-6 草案 | **仍开** | `ES6_E05_GATE_DRAFT.md` 草案/进行中/不伪绿；G1 通过不假关 ES-6；TASK_BOARD 未关 |
| 8 | pytest 全量 | **763 passed / 1 xfailed / 0 failed** | `python -m pytest tests/ -q --tb=line` EXIT=0 |
| 9 | 契约/骨架抽检 | **37 passed** | test_es_derived_contracts + test_es3_es6_gate_skeletons |
| 10 | A24 | **仍开** | `-k a24` 含 xfail；Top-k 未闭环；**未**伪绿 Top-k |
| 11 | R7 lag | **192=stamp；仍开** | `git rev-list --count 7623a52..HEAD`=192，与 MECHANISM_HEAD_NOTE §20 / ES_EVAL_PROGRESS 一致；未改 mechanism_cases.py |
| 12 | museum | **passed 28/84** | validate_museum_v3：items=28 images=84 sha256Match=84 |
| 13 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；PRE=POST=EXPECTED |
| 14 | 开项栅栏 | **仍开** | P1 / RF-8 / R7 / A24 / ES-6 / conflict / 产品 RT 未假关 |

- **红队门禁结论：可合并 / 可 FF（相对 0c1ac0c）。** 证据齐；未伪绿。
- 日志：`wt/qa-tmp/qa-eval-4b17bc5/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。

## 附注 tip@4b17bc5 REBASE_REQUIRED — RM-红队QA @ 2026-10-25 18:49 Asia/Shanghai

门禁结案后 feature 已 FF 到 arch@d376dbcabced081da22619dbe5a459a5520440df（d376dbc）；与 tip@4b17bc5 **diverged 1/1**；文件与 arch **不重叠**。
**最终判决：有条件可合并**——相对 parent@0c1ac0c 证据齐（763p/1xfail；dry-run 只读；lag=192；museum 28/84；SHA 未变；A24/R7/ES-6 仍开）；**合入前须 rebase←d376dbc 再窄核/FF**。**勿合旧 tip**；QA **未**自行 merge/push。

## 窄门禁 tip@b16c756（jinshi Top5 复核笔记；parent=0c1ac0c；docs-only） — RM-红队QA @ 2026-10-25 18:52 Asia/Shanghai

**范围**：只读核 tip `b16c756e0cfc6954b583d4130669686ec107d5e0`（相对当时 feature@`0c1ac0c`）；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未假关**开项。

**合入条件（REBASE_REQUIRED）**：相对 parent@`0c1ac0c` 证据齐（docs-only / merge-tree 干净 / 可 FF）。但 feature **已到** `d376dbcabced081da22619dbe5a459a5520440df`，`d376dbc...b16c756` = **1/1 diverged** → **判决：REBASE_REQUIRED ← d376dbc**；**勿合**旧 tip@b16c756。金石 rebase 出新 tip 后再窄核。QA **未**自行 merge。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **通过** | tip=`b16c756e0cfc6954b583d4130669686ec107d5e0`；parent=`0c1ac0cf5acc8faa4a066ae26a384dee536a428e`；subj=`docs(jinshi): human review notes for Top5 priority claims`；门禁开始 feature=`0c1ac0c`；结束 feature=`d376dbc` |
| 2 | ahead/behind vs 0c1ac0c | **1/0** | rev-list left-right → 0/1；ancestor_ok |
| 3 | merge-tree vs 0c1ac0c | **冲突 0 / 可 FF** | write-tree=`31b6227970bdae1711f57bb3da8c2b449762492a`；无 CONFLICT；exit=0 |
| 4 | 变更面 | **docs-only 2 files +191** | A NOTES_TOP5(+187)；M Top15(+4 指针)；**未改** claims JSON / museum / 主库 / apps / 生效 ci.yml |
| 5 | NOTES 抽样 | **并列冲突非关单** | status=conflict×5；结论均为并列冲突+开项保持开放/不建议关闭；文首非关闭声明；假关/已关闭/关单=0；未抬升 Verification |
| 6 | Top15 指针 | **通过** | 仅追加后续文档指针；关闭条件仍要求新证据入库+台账 --check 下降 |
| 7 | 主库 SHA | **始=末未变** | rubbingmind=`8408DBC3…323D`；evidence-v2=`854DF859…BABD3`；MATCH |
| 8 | 开项栅栏 | **仍开** | conflict×5 仍开；P1/RF-8/R7/A24/RT-006/RT-010/ES-6 **未假关** |
| 9 | vs feature@d376dbc | **diverged 1/1** | **REBASE_REQUIRED ← d376dbc**；旧 tip 作废勿 FF |

- **红队窄门禁结论：相对 0c1ac0c 证据齐可 FF；因 tip 已动 → REBASE_REQUIRED ← d376dbc；勿合 b16c756。**
- 日志：`wt/qa-tmp/qa-jinshi-b16c756/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply；STOP=否（窄门禁完成）。
## 合入后窄冒烟 tip@d376dbc（ff-only arch CI draft 扩展 + RT-006 决策备忘 onto feature@0c1ac0c；parent=0c1ac0c；docs-only） · RM-红队QA @ 2026-10-25 18:52 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach @ tip `d376dbcabced081da22619dbe5a459a5520440df`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未关** P1/RF-8/R7/A24/RT-006/RT-010/conflict。

**vs 0c1ac0c**：3 files · `RT006_USER_DECISION_BRIEF.md`（新建备忘）+ `RT010_CI_DRAFT.md` / `ci-feature.draft.yml`（扩展）；docs-only +114/-5；**未碰** `.github/workflows/ci.yml`；**未碰** DeduceRequest / static / HomePage。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=`d376dbcabced081da22619dbe5a459a5520440df`；parent=`0c1ac0cf5acc8faa4a066ae26a384dee536a428e`；subj=`docs(ci,rt006): extend feature CI draft + user A/B/C brief`；feature tip = tip 一致 |
| 2 | docs 边界 | **守住** | 仅 3 个 docs/product-upgrade 路径；无业务代码 diff |
| 3 | 生效 ci.yml | **未碰** | name-only diff 空；blob HEAD==parent；见 ci-yml-untouched.txt |
| 4 | RT-006 brief | **备忘非关闭** | 含 A/B/C 选项说明；**未**自选/未执行落地；DeduceRequest/static 未改 |
| 5 | AB-8 横幅 | **仍在** | `data-testid=health-samples-banner`；`getHealth` + `samples_missing`/`samples_sha_mismatch`/`degraded` |
| 6 | A24 | **仍开 1p/1xfail / 未伪绿** | `pytest -k a24` → **1 passed / 1 xfailed**；未强绿 |
| 7 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 8 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH_PRE=True / MATCH_EXPECTED=True |
| 9 | RF-8 | **仍开 / 未假关** | inventory/evidence 仍列 RF-8；本 tip 未改 HomePage |
| 10 | R7 | **仍开** | lag=`192`（rev-list 7623a52..HEAD）；未关 R7 |
| 11 | RT-006 | **仍开 / 未假关** | brief 仅为用户决策备忘；台账不关闭 |
| 12 | RT-010 | **仍开（draft 扩展）** | 仅扩展 draft；生效 workflows 仍未改 |
| 13 | conflict / 其余 | **仍开** | 未抬 verification；未 C-08 |

- **合入后窄冒烟结论：通过**（无 blocker；A24 仍 xfail；开项未假关）。
- 开项 P1 / RF-8 / R7 / A24 / **RT-006** / **RT-010** / conflict **仍开**（未在台账关闭态）。
- 日志：`wt/qa-tmp/qa-smoke-post-d376dbc/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
## 窄核 tip@eba2faf（jinshi Top5 复核笔记 rebase←d376dbc；parent=d376dbc；docs-only） · RM-红队QA @ 2026-10-25 18:55 Asia/Shanghai

**范围**：只读核 tip `eba2faf505dfa4f79f0fae523d00cc5dadbc6823`（相对 feature@`d376dbc`）；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未假关**开项。旧 tip `b16c756e0cfc6954b583d4130669686ec107d5e0` **作废勿合**。

**判决：可合并（可 FF）**。parent 恰为当前 feature tip；merge-tree 无冲突；docs-only +191；NOTES 五条均为并列冲突+开项保持开；主库 SHA 未变。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **通过** | tip=`eba2faf505dfa4f79f0fae523d00cc5dadbc6823`；parent=`d376dbcabced081da22619dbe5a459a5520440df`；subj=`docs(jinshi): human review notes for Top5 priority claims`；主仓 feature HEAD=`d376dbcabced081da22619dbe5a459a5520440df` 一致 |
| 2 | ahead/behind vs d376dbc | **1/0** | rev-list；ancestor_ok；可 FF |
| 3 | merge-tree vs d376dbc | **冲突 0 / 可 FF** | write-tree=`2ec791f0058f3090c913e74217c391a2120d7230`；无 CONFLICT；exit=0 |
| 4 | 变更面 | **docs-only 2 files +191** | A `CLAIMS_HUMAN_REVIEW_NOTES_TOP5.md`(+187)；M `CLAIMS_HUMAN_REVIEW_PRIORITY_TOP15.md`(+4 指针)；**未改** claims JSON / museum / 主库 / apps / 生效 ci.yml |
| 5 | NOTES 抽样 | **并列冲突非关单** | 5/5：`status=conflict` +「并列冲突」+「开项保持开」+「本轮不关闭开项」；文首「非关闭声明」；未抬升 Verification；关单/已关闭/假关=0 |
| 6 | Top15 指针 | **通过** | 仅追加后续文档指针；关闭条件仍要求新证据入库+台账 `--check` 下降；标明「开项仍开」 |
| 7 | CLAIMS_OPEN_ISSUES | **仍开** | Top5 五条 claimId 仍在台账；未改该文件 |
| 8 | 主库 SHA | **始=末未变** | rubbingmind=`8408DBC3…323D`；evidence-v2=`854DF859…BABD3`；MATCH |
| 9 | museum 边界 | **未碰** | tip 无 museum/主库路径；steles28 仍 28（只读核） |
| 10 | 开项栅栏 | **仍开** | conflict×5 仍开；P1/RF-8/R7/A24/RT-006/RT-010/ES-6 **未假关** |

- **红队窄核结论：可合并**（请架构 ff-only；合入后窄冒烟）。
- 日志：`wt/qa-tmp/qa-jinshi-eba2faf/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply；STOP=否（窄核完成）。

## 完整门禁 tip@6f42ab1（eval@6f42ab1；ES-3/ES-6；rebase←d376dbc；vs feature@eba2faf） — RM-红队QA @ 2026-10-25 18:59 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-evalsci` tip `6f42ab1ab2922e9b8344a72d0a138900d8e05130`；相对当时 feature@`d376dbc` 完整门禁；**事后** feature 已 FF 至 `eba2faf`（jinshi）。**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程。旧 tip `4b17bc5`/`40acb18`/`8e72315`/`dfbf8f0` **作废勿合**。

**独立核验 vs Green 宣称**：feature 当时=`d376dbc` ✓；parent=`d376dbc` ✓；ahead1 ✓；lag 实测 tip=`193` ✓（stamp 正文=`192` **不一致**）；9 files +554/-1（含代码）✓；可 FF **仅相对 d376dbc**。相对当前 feature@`eba2faf`：**diverged 1/1，REBASE_REQUIRED**。

**红队裁决：有条件可合并（REBASE_REQUIRED ←eba2faf）**。条件：(1) 必须 rebase 到当前 feature tip `eba2faf` 后再窄核/FF，**勿**对旧 tip 直接 FF；(2) R7 stamp=192 ≠ 实测 tip lag=193，只记证据勿假关；(3) A24/R7/ES-6/RF-8/P1/conflict/RT-006/RT-010 **仍开**；(4) ES-3 dry-run 有证据但 `hasOpenFindings=true`（appliedStatusSha256 drift），ES-3 **未关**。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=`6f42ab1ab2922e9b8344a72d0a138900d8e05130`；parent=`d376dbcabced081da22619dbe5a459a5520440df`；subj=`docs/test(eval-sci): ES-3 dry-run + ES-6 E-05 gate draft evidence` |
| 2 | vs d376dbc | **ahead1/behind0 / 可 FF** | merge-base=is-ancestor；merge-tree 冲突标记=0 |
| 3 | vs eba2faf（当前 feature） | **diverged 1/1 / 不可 FF** | eba 非 HEAD 祖先；HEAD 非 eba 祖先；merge-base=`d376dbc`；merge-tree 冲突=0 但仍需 rebase |
| 4 | diff 规模 | **9 files +554/-1（含代码）** | docs ES3/ES6/PROGRESS/MECHANISM + experiments ci_bootstrap_dry_run/es6_e05/eval_export_contract + tests skeletons/contracts；**非** docs-only |
| 5 | pytest 全量 | **766 passed / 1 xfailed** | `python -m pytest tests/ -q --tb=line` EXIT=0；XFAIL=A24 |
| 6 | A24 | **仍开 1p/1xfail** | `pytest -k a24` → 3 passed / 1 xfailed（含相关）；未强绿 |
| 7 | ES contracts / skeletons | **40 passed** | test_es_derived_contracts + test_es3_es6_gate_skeletons |
| 8 | ES-3 dry-run | **只读通过 / 未伪绿 / 未写库** | `wroteDerived=false` `recomputedBootstrap=false` `ok=true` `hasOpenFindings=true`（appliedStatusSha256 drift）；derived 无新写；ES-3 **仍开** |
| 9 | ES-6 | **仍开** | gate_verdict 骨架永不 closed；缺 close evidence → blocked_missing_evidence；草稿证据成立但不关单 |
| 10 | R7 lag | **仍开 / stamp≠实测** | 实测 `git rev-list --count 7623a52..HEAD`=**193**；NOTE stamp R7 lag=**192**（header 仍写 parent=0c1ac0c，实际 parent=d376dbc）；Green 宣称 193=实测；**勿假关** |
| 11 | museum | **passed 28/84** | validate_museum_v3 items=28 images=84 sha256Match=84；museum_processing 未入 diff |
| 12 | 主库 SHA | **始=终 MATCH** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3` |
| 13 | 开项 | **仍开** | A24 / R7 / ES-6 / ES-3(openFindings) / RF-8 / P1 / conflict / RT-006 / RT-010 |

- **结论：有条件可合并** — 相对 d376dbc 拓扑干净且 pytest/dry-run/museum/主库通过；**相对当前 feature@eba2faf 必须 REBASE_REQUIRED**，先过先 FF 由 Green 决定，QA 不 merge。
- marker：`eval@6f42ab1`
- 日志：`wt/qa-tmp/qa-eval-6f42ab1/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
## 合入后窄冒烟 tip@eba2faf（ff-only 架构合入 jinshi Top5 NOTES onto feature@d376dbc；parent=d376dbc；docs-only）— RM-红队QA @ 2026-10-25 19:01 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-feature-smoke` detach @ tip `eba2faf505dfa4f79f0fae523d00cc5dadbc6823`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未假关** P1/RF-8/R7/A24/RT-006/RT-010/NOTES conflict/ES-6。

**vs d376dbc**：2 files → `CLAIMS_HUMAN_REVIEW_NOTES_TOP5.md`（新增）+ `CLAIMS_HUMAN_REVIEW_PRIORITY_TOP15.md`（指针）；docs-only +191；**未碰** `.github/workflows/ci.yml`；**未碰** claims JSON / museum 数据 / 业务代码。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=`eba2faf505dfa4f79f0fae523d00cc5dadbc6823`；parent=`d376dbcabced081da22619dbe5a459a5520440df`；subj=`docs(jinshi): human review notes for Top5 priority claims`；feature tip = tip 一致 |
| 2 | docs 边界 | **守住** | 仅 2 个 docs/product-upgrade 路径；无业务代码 diff |
| 3 | 生效 ci.yml | **未碰** | name-only diff 空；blob HEAD==parent；见 ci-yml-untouched.txt |
| 4 | NOTES conflict | **仍开/不假关** | status=conflict ×5；保持开放用语在；未抬 verification；未关闭 |
| 5 | AB-8 横幅 | **仍在** | `data-testid=health-samples-banner`；`getHealth` + `samples_missing`/`samples_sha_mismatch`/`degraded` |
| 6 | A24 | **仍开 1p/1xfail / 未伪绿** | `pytest -k a24` → **1 passed / 1 xfailed**；未强绿 |
| 7 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 8 | 主库 SHA | **始=终未变** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；MATCH_PRE=True / MATCH_EXPECTED=True |
| 9 | RF-8 | **仍开 / 未假关** | inventory/evidence 仍列 RF-8；本 tip 未改 HomePage |
| 10 | R7 | **仍开** | lag=`193`（rev-list 7623a52..HEAD）；未关 R7 |
| 11 | RT-006 | **仍开 / 未假关** | 本 tip 未触 |
| 12 | RT-010 | **仍开（draft 未生效）** | 生效 workflows 仍未碰 |
| 13 | conflict / 其余 | **仍开** | 未抬 verification；未 C-08；ES-6 仍开 |

- **合入后窄冒烟结论：通过**（无 blocker；A24 仍 xfail；开项未假关）。
- 开项 P1 / RF-8 / R7 / A24 / **RT-006** / **RT-010** / **NOTES conflict** / ES-6 **仍开**（未在台账关闭态）。
- 日志：`wt/qa-tmp/qa-smoke-post-eba2faf/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。

## 窄核 tip@bd15ce0（report@bd15ce0；RF-8 1440×900 证据续页；vs feature@eba2faf）· RM-红队QA @ 2026-10-25 19:01 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-report` tip `bd15ce01fe9467bf23124ca6a4335a987874bfe1`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程。旧 tip `492d48c`/`1c0673b`/`60f967c`/`4ef251e` **作废勿合**。

**独立核验 vs Green 宣称**：parent=`eba2faf`=当前 feature HEAD ✓；ahead1/behind0 ✓；docs-only 3files +95/-1 ✓；未改 HomePage ✓；RF-8 仍开勿假关 ✓；清单§E + verify json 仅证据补充 ✓。

**红队裁决：可合并（可 FF）**。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=`bd15ce01fe9467bf23124ca6a4335a987874bfe1`；parent=`eba2faf505dfa4f79f0fae523d00cc5dadbc6823`；subj=`docs(report): RF-8 home core cards 1440x900 shot + checklist续页 (RF-8 still open)` |
| 2 | vs feature@eba2faf | **ahead1/behind0 / 可 FF** | merge-base=eba2faf；is-ancestor；merge-tree 冲突标记=0 |
| 3 | diff | **docs-only 3 files +95/-1** | md 清单§E；png 1440×900；slice16-rf8-verify.json；**未碰** HomePage/apps/web/生效 ci.yml |
| 4 | HomePage | **未改** | name-status 无 `HomePage` / `.tsx` / `.ts` / `.py` |
| 5 | RF-8 | **仍开** | §E 状态=待开/待用户确认；禁止自关/禁止改 HomePage；未抬 verification；未关 Phase1；FINDINGS/MATRIX 无本 tip 关单 |
| 6 | 1440 证据 | **成立（不关单）** | Pillow (1440,900)；verify contain=4 cover=0；1920 未重拍（沿用既有） |
| 7 | 主库 SHA | **始=末 MATCH** | rubbingmind=`8408DBC36819EFDA512D392DF69FD2B96D7B1469460FCBA0BBEE5AAAD270323D`；evidence-v2=`854DF859CF2FB7A72C52694D0CF2E1955A028CC3496B9F8C72F01E36645BABD3` |
| 8 | 开项栅栏 | **仍开** | P1/RF-8/R7/A24/RT-006/RT-010/conflict **未假关** |

- **结论：可合并** — 请架构 ff-only；合入后窄冒烟（本 tip 不关 RF-8）。
- marker：`report@bd15ce0`
- 日志：`wt/qa-tmp/qa-report-bd15ce0/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
## 合入后窄冒烟 tip@bd15ce0（ff-only 架构合入 report RF-8 1440 onto feature@eba2faf；parent=eba2faf；docs-only）— RM-红队QA @ 2026-10-25 19:10 Asia/Shanghai

**范围**：只读 worktree D:\RubbingMind\wt\qa-feature-smoke detach @ tip bd15ce01fe9467bf23124ca6a4335a987874bfe1；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未假关** P1/RF-8/R7/A24/RT-006/RT-010/NOTES conflict/ES-6。合入时未跟踪 slice16 挡道备份 _merge_bak_slice16_20261025190355/ **仅磁盘备份、未入库**（冒烟以 tip 内已跟踪文件为准）。

**vs eba2faf**：3 files → REPORT_FRONTEND_P1_OPEN_AND_RF8_SHOTS.md（§E 续）+
f8_home_core_cards_1440x900.png + slice16-rf8-verify.json；docs-only +95/−1；**未改** HomePage；**未碰** .github/workflows/ci.yml；**未改** claims JSON / museum 数据 / 业务代码。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=bd15ce01fe9467bf23124ca6a4335a987874bfe1；parent=eba2faf505dfa4f79f0fae523d00cc5dadbc6823；subj=docs(report): RF-8 home core cards 1440x900 shot + checklist续页 (RF-8 still open)；feature tip = tip 一致 |
| 2 | docs 边界 | **守住** | 仅 3 个 docs/screenshots 路径；无业务代码 diff |
| 3 | HomePage | **未改** | name-only / HomePage* diff 空 |
| 4 | 生效 ci.yml | **未碰** | name-only diff 空；blob HEAD==parent |
| 5 | _merge_bak_slice16_* | **未入库** | git ls-files 无命中；磁盘备份存在于 D:\RubbingMind\_merge_bak_slice16_20261025190355（勿 add） |
| 6 | RF-8 | **仍开 / 未假关** | inventory/evidence/report 仍列 RF-8；本 tip 仅补 1440 截图+清单§E，未改 HomePage |
| 7 | museum | **passed** | items=28 images=84 sha256Match=84 |
| 8 | 主库 SHA | **始=终 MATCH** | rubbingmind=8408DBC3…323D / evidence-v2=854DF859…BABD3；MATCH_PRE=True / MATCH_EXPECTED=True |
| 9 | R7 | **仍开** | lag=194（rev-list 7623a52..HEAD）；未关 R7 |
| 10 | A24 | **仍开 1p/1xfail / 未伪绿** | pytest -k a24 → **1 passed / 1 xfailed** |
| 11 | RT-006 | **仍开 / 未假关** | 本 tip 未碰 |
| 12 | RT-010 | **仍开（draft 未生效）** | 生效 workflows 仍未改 |
| 13 | NOTES conflict / ES-6 | **仍开** | 本 tip 未碰；未抬 verification；未 C-08 |

- **合入后窄冒烟结论：通过**（无 blocker；开项未假关）。
- 开项 P1 / RF-8 / R7 / A24 / **RT-006** / **RT-010** / **NOTES conflict** / ES-6 **仍开**（未在台账关单态）。
- 日志：wt/qa-tmp/qa-smoke-post-bd15ce0/
- **未改**业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply；**未**将 _merge_bak_slice16_* 入库。

## 窄核 arch@12cff65（RT-010 draft permissions + open inventory；parent=bd15ce0；docs-only）· RM-红队QA @ 2026-10-25 19:12 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-arch` detach @ tip `12cff65a9285ccac6c7756d83bbbd1070b2c3306`；**未改**业务代码；未 push/commit/merge；未写主库；无 C-08 --apply；未杀非己进程。**未假关** P1/RF-8/R7/A24/RT-006/RT-010/NOTES conflict/ES-6。

**独立核验 vs Green 宣称**：parent=`bd15ce0`=当前 feature HEAD 通过；ahead1/behind0 通过；docs-only 3files +44/-20 通过；**未碰**生效 `.github/workflows/ci.yml` 通过；未自选 RT-006 A/B/C 通过；开项仍开 通过。

**红队裁决：可合并（可 FF）**。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=`12cff65a9285ccac6c7756d83bbbd1070b2c3306`；parent=`bd15ce01fe9467bf23124ca6a4335a987874bfe1`；subj=`docs(ci,ab): RT-010 draft permissions + open inventory @bd15ce0`；feature HEAD=`bd15ce01fe9467bf23124ca6a4335a987874bfe1` |
| 2 | vs feature@bd15ce0 | **ahead1/behind0 / 可 FF** | merge-base=bd15ce0；is-ancestor exit=0；merge-tree write-tree=`d2ef09ed26a1ff2bfcc739b13998e8cefc21310c`；CONFLICT=0 |
| 3 | diff | **docs-only 3 files +44/-20** | M AB_OPEN_AFTER_25aa898.md；M RT010_CI_DRAFT.md；M ci-feature.draft.yml |
| 4 | 生效 ci.yml | **未碰** | name-only 无 `.github/**`；blob parent==tip=`56f507bcdc7069868fd92f3305df78a2c8804322` |
| 5 | RT-006 | **仍开 / 未自选** | `static/index.html` 仍在；`RT006_USER_DECISION_BRIEF.md` 仍在；AB_OPEN「备忘≠拍板 / 等用户 widget」 |
| 6 | RT-010 | **仍为 draft / 未上线** | draft 仍在 `docs/product-upgrade/`；未迁入 `.github/workflows/`；文案「未关单 / 须 Green 再批」 |
| 7 | 开项栅栏 | **仍开** | P1/RF-8/R7/A24/RT-006/RT-010/NOTES conflict/ES-6 **未假关** |
| 8 | 主库 SHA | **始=终 MATCH** | rubbingmind=`8408DBC3…323D`；evidence-v2=`854DF859…BABD3` |
| 9 | 并行提示 | **先过先 FF** | 与 eval@4d93c78 同 parent=bd15ce0；另一路合入后或需 rebase |

- **结论：可合并** — 请架构 ff-only；合入后窄冒烟；**勿**假关 RT-010/RT-006/RF-8。
- marker：`arch@12cff65`
- 日志：`wt/qa-tmp/qa-arch-12cff65/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。

## 完整门禁 tip@4d93c78（eval@4d93c78；ES-3 dry-run + ES-6 E-05；rebase←bd15ce0；vs feature@bd15ce0）— RM-红队QA @ 2026-10-25 19:12 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\rm-eval-sci` @ tip `4d93c787d02859eb8248f2e1728296019ccb10ff`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程；**未假关** A24/R7/ES-6/ES-3 openFindings/RF-8/P1/conflict/RT-006/RT-010。**旧 tip `43d77b1`（及更早 `6f42ab1`/`4b17bc5` 等）作废勿合**。

**独立核验 vs Green 宣称**：parent=`bd15ce0`=当前 feature HEAD ✓；is-ancestor bd15ce0→4d93c78 ✓；ahead1/behind0 ✓；9 files +554/−1（含代码）✓；可 FF ✓。

**红队裁决：可合并（可 FF）**。

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=`4d93c787d02859eb8248f2e1728296019ccb10ff`；parent=`bd15ce01fe9467bf23124ca6a4335a987874bfe1`；subj=`docs/test(eval-sci): ES-3 dry-run + ES-6 E-05 gate draft evidence`；feature HEAD=parent |
| 2 | vs feature@bd15ce0 | **ahead1/behind0 / 可 FF** | merge-base=bd15ce0；merge-tree --write-tree=`676f9a08abc99c545657e23cfd51e3c10f09807a`；CONFLICT=0 |
| 3 | diff | **9 files +554/−1（含代码）** | A ES3_BOOTSTRAP_DRY_RUN.md / ES6_E05_GATE_DRAFT.md；M ES_EVAL_PROGRESS.md / MECHANISM_HEAD_NOTE.md；A ci_bootstrap_dry_run.py / es6_e05_gate_evidence.py；M eval_export_contract.py；A test_es3_es6_gate_skeletons.py；M test_es_derived_contracts.py |
| 4 | museum_processing / 生效 ci.yml / HomePage | **未碰** | name-status 无命中；FORBIDDEN_HITS=none |
| 5 | pytest 全量 | **766 passed / 1 xfailed / 0 failed** | EXIT=0；约 70s；A24 仍 xfail |
| 6 | ES contracts / skeletons | **40 passed** | test_es_derived_contracts + test_es3_es6_gate_skeletons |
| 7 | A24 | **仍开 1xfail / 未伪绿** | `pytest -k a24` 含 xfailed；未强关 |
| 8 | ES-3 dry-run | **只读通过 / 未伪绿 / 未写库** | `wroteDerived=false`；`recomputedBootstrap=false`；`ok=true`；`hasOpenFindings=true`（appliedStatusSha256 drift）；derived 快照前后一致 DERIVED_CHANGED=0；ES-3 **仍开** |
| 9 | ES-6 | **仍开** | E-05 gate draft / evidence 模块在；未抬 close evidence；未假关 |
| 10 | R7 lag | **仍开 / 勿假关** | 实测 tip `git rev-list --count 7623a52..HEAD`=**195**；parent@bd15ce0=**194**；NOTE header R7 lag 仍写 **194**（rebase 后 tip+1 漂移）；**不关 R7** |
| 11 | museum | **passed 28/84** | validate_museum_v3 items=28 images=84 sha256Match=84 |
| 12 | 主库 SHA | **始=终 MATCH** | rubbingmind=`8408DBC3…323D` / evidence-v2=`854DF859…BABD3`；PRE=POST |
| 13 | 开项 | **仍开** | A24 / R7 / ES-6 / ES-3(openFindings) / RF-8 / P1 / conflict / RT-006 / RT-010 |
| 14 | 并行 | **先过先 FF** | 同 parent 另有 arch@12cff65 已窄核可合并；若 arch 先 FF 则本 tip 或需 rebase |
| 15 | 旧 tip | **作废勿合** | `43d77b1`（parent=eba2faf；vs bd15ce0 曾 diverged/REBASE_REQUIRED）及更早同族 tip |

- **结论：可合并** — 请架构 ff-only；合入后窄冒烟；**勿**假关 A24/R7/ES-6/ES-3/RF-8。
- marker：`eval@4d93c78`
- 日志：`wt/qa-tmp/qa-eval-4d93c78/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。


## 窄核 tip@04f207e（report@04f207e·P1 开项盘点续页 F vs feature@bd15ce0）· RM-红队QA @ 2026-10-25 19:13 Asia/Shanghai

**范围**：只读 worktree `D:\RubbingMind\wt\qa-report` tip `04f207e8c2f13b760fcc94506b43f656ef9e8c6f`；**未改**业务代码；未 push/commit/merge；未写主库；未 C-08 --apply；未杀非己进程。

**独立核验 vs Green 声称**：parent=`bd15ce0`=当前 feature HEAD ✅；ahead1/behind0 ✅；docs-only 1file +45 ✅；未改 HomePage ✅；RF-8 仍开勿假关 ✅；续页 F ✅。

**红队裁决：可合并（可 FF）。**

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | tip / parent | **锁定** | HEAD=`04f207e8c2f13b760fcc94506b43f656ef9e8c6f`；parent=`bd15ce01fe9467bf23124ca6a4335a987874bfe1`；subj=`docs(report): P1 open inventory续页 F vs feature@bd15ce0 (RF-8 still open, 无可叠 feat)` |
| 2 | vs feature@bd15ce0 | **ahead1/behind0 / 可 FF** | merge-base=bd15ce0；is-ancestor exit=0；merge-tree --write-tree=`a7cd011ad4fb830427f7fa4f21271f7de77c75d3`；CONFLICT=0 |
| 3 | diff | **docs-only 1 file +45** | M `docs/product-upgrade/REPORT_FRONTEND_P1_OPEN_AND_RF8_SHOTS.md`（续页 F）；**未改** HomePage / apps/web / 生效 `.github/workflows/ci.yml` |
| 4 | HomePage | **未改** | name-only 无 `HomePage` / `.tsx` / `.ts` / `.py` / apps/web / 生效 ci.yml |
| 5 | RF-8 | **仍开** | 续页 F.1 状态=**仍开**（等用户截图确认）；禁止自关/改 HomePage；未抬 verification；未关 Phase1；无可叠 feat |
| 6 | 主库 SHA | **始=终 MATCH** | rubbingmind=`8408DBC3…323D`；evidence-v2=`854DF859…BABD3` |
| 7 | 开项闸门 | **仍开** | P1/RF-8/R7/A24/RT-006/RT-010/NOTES conflict/ES-6 **未假关** |
| 8 | 并行提示 | **先过先 FF** | 同 parent 还有 arch@12cff65 / eval@4d93c78；结束时 feature HEAD 仍=bd15ce0 → 未 diverged |

- **裁决：可合并** → 待架构 ff-only；合入后窄冒烟；**勿**假关 RF-8。
- marker：`report@04f207e`
- 日志：`wt/qa-tmp/qa-report-04f207e/`
- **未**改业务代码；**未**写主库；**未** push/commit/merge；**未** C-08 --apply。
