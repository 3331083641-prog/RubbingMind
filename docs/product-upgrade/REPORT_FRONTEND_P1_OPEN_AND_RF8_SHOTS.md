# 报告前端 P1 开项盘点 + RF-8 确认截图清单

> 作者：RM-报告前端执行器 · tip base `f27719c`（rebase 自 60f967c，旧 SHA 作废） · 2026-10-25 Asia/Shanghai  
> 性质：**docs-only**。不改 HomePage / App.tsx / api.ts / urlState.ts；**不自关 RF-8**；不 push。  
> 对照源：`phase1-frontend/slice10`–`slice15` 的 `p1-rf-open-inventory.txt`、`docs/product-upgrade/FRONTEND_INTEGRATION_CHECKLIST.md`（本分支）、`D:\RubbingMind\docs\product-upgrade\ACCEPTANCE_MATRIX.md` / `TASK_BOARD.md`（主库台账，本 worktree 未跟踪）、源码只读抽查。

---

## A. 除 RF-8 外的 P1 / RF 开项缺口（相对 tip@f27719c）

### A.1 已落地代码证据（≠ 产品关单）

下列项在 tip 上**有代码/导出证据**，但 `ACCEPTANCE_MATRIX` / 产品闸门仍记「开项仍开」——**证据 ≠ 关单，勿口头关闭 ACCEPTANCE Phase1**。

| 项 | tip 上证据摘要 | 产品闸门 |
|---|---|---|
| RF-2 上下文栏 / URL props 消费 | ReportsPage / Workbench 消费 props；URL 读写归 App（本 Agent 不改） | 仍开（产品级） |
| RF-3 全局 vs 单件分层 | ReportsPage 全局评测 disclaimer | 仍开 |
| RF-4 ECharts 分轴/负值/CI | `MethodComparisonChart.tsx` | 仍开 |
| RF-5 三联 + object-contain | `SyncedTriptych.tsx` | 仍开 |
| RF-6 失败案例入口 | `FailureCasesPanel.tsx` | 仍开 |
| RF-7 A4 打印/导出 | `reportPrint.css` + `ReportPrintLayout.tsx`；JSON 含 algorithmLayer | 仍开 |
| RF-9 页脚「增强与辅助释读」 | 先前 tip 文案 | 仍开 |
| RF-10 同批复测 v2.1 命名 | 先前 grep/文案 | 仍开 |
| RF-11 原图返回文案 | `runOutcome` / isPassthrough 展示 | 仍开 |
| P1-1 not_evaluated / glyph | `glyphEvaluationText`；禁伪 Top-k | 仍开 |
| P1-4 mechanism head lag | `MECHANISM_HEAD_NOTE` + captionNote | 仍开 |
| P1-5/6/7/8 打印局限 / DER | 打印局限文案 + DER v3.3 相关 | 仍开 |
| P1-9 报告首屏多分辨率 | slice7：1920×1080 / 1440×900；slice10：1366×768 / 390×844（报告页，非 RF-8 首页） | 仍开 |
| P1-11 空指标不拼单位 | 打印 PSNR 空值不带单位 | 仍开 |
| ES-3 liftClaim UI + 导出对齐 | GlobalEvaluation + export JSON liftClaims（21cb82b 系） | 仍开 |
| ES-5 NLC 列 | 先前 slice8 | 仍开 |
| BR-09 includeDemo | `EvidenceSearch.tsx` checkbox + warning/result banners；API 默认 false | CHECKLIST「待办」条目**过时** |
| reportStatus 全路径 | `reportData` stele_retired / run_not_found / stele_not_found | 仍开 |
| **algorithmOutputMode UI** | tip@5195b5b → feature@5a7b20c：`algorithmOutputModeView` / 决策链 / 打印 / 导出 `algorithmLayer`；契约来自 arch@847e7f1 | CHECKLIST §2「UI 未接」**过时**；产品闸门仍开 |
| AB-8 health samples_* | `App.tsx` 全局 banner `health-samples-banner`（架构侧）；报告页**不**重复做面板 | 本 Agent 范围外 |

### A.2 仍开 / blocked（除 RF-8）

| 缺口 | 状态 | blocked 原因 | 本 Agent 可否叠代码 |
|---|---|---|---|
| ACCEPTANCE Phase1 全组 P1-* | **仍开**（矩阵各次门禁均写「开项仍开」） | 产品验收未关单；证据≠通过 | 否（禁止把矩阵改成「通过」） |
| FRONTEND_INTEGRATION_CHECKLIST 陈旧表述 | 文档债 | §2 algorithmOutputMode「UI 未接」、§4 RF-8「用户已确认」与 tip+Green 不一致 | 可选后续 docs 纠偏；**本 tip 不改 CHECKLIST 正文以免抢合** |
| AB / RT 产品项（RT-006 等） | 仍开 | 归架构 / Green / 用户 widget（见 `AB_OPEN_AFTER_25aa898.md`） | 否 |
| 报告页可叠 feat | **无** | slice13–15 代码扫描：除 RF-8（用户）外无可叠报告前端代码 tip | — |

### A.3 源码只读抽查（f27719c）

- `HomePage.tsx` L245 注释 + L250 `object-contain`；L246 纸色衬底 `bg-[#eee4d2]`；**本轮未改**。
- `reportData.ts`：`AlgorithmOutputModeView` / `runAlgorithmOutputModeView` 与 `AdaptiveDiagnostics` 对齐。
- `ArtifactRunReport.tsx` / `ReportPrintLayout.tsx` / `ReportsPage.tsx` 导出 `algorithmLayer` 已接。
- 未改 `App.tsx` / `api.ts` / `urlState.ts`（本 tip）。

---

## B. RF-8 单独成节（状态 = **仍开**）

### B.1 状态

| 字段 | 值 |
|---|---|
| 票 | **RF-8**（TASK_BOARD ↔ P1-15） |
| 状态 | **仍开** — 等用户截图确认；**禁止自关**；**禁止改 HomePage** |
| 代码现状 | 核心样本卡已是 `object-contain` + 纸色衬底（见上）；无 `object-cover` 于核心卡 |
| CHECKLIST §4 | 写「用户已确认」——相对 Green/ACCEPTANCE **过时**；以本清单为准：**未确认** |
| 用户应确认什么 | 首页核心样本卡拓本为 **完整显示（object-contain）**，纸色衬底可见，**未被 cover 裁切字口**；改前/改后观感可接受 |

### B.2 TASK_BOARD / Green 点名分辨率

合并前用户确认需覆盖：

1. **1920×1080**
2. **1440×900**

### B.3 已有截图路径（如实；含磁盘存在性与像素）

根目录：`D:\RubbingMind\screenshots\product-upgrade\phase1-frontend\`

| 路径（相对上述根，或绝对） | 标称用途 | 磁盘 | 实测像素 | 是否满足 RF-8 分辨率要求 |
|---|---|---|---|---|
| `slice10\rf8_home_core_cards_1920x1080.png` | RF-8 首页核心卡审计（推荐主证据） | **存在** | **1920×1080** | ✅ 满足 1920×1080 |
| `slice7\rf8_home_core_cards_1920x1080.png` | 同主题较早审计 | **存在** | **1920×1080** | ✅ 满足 1920×1080 |
| `slice4\home_rf8_contain.png` | contain 取证 | **存在** | **1920×1080** | ✅ 满足 1920×1080 |
| `slice3\06_home_core_cards_regression_1920x1080.png` | 回归 | **存在** | **1920×1080** | ✅ 满足 1920×1080 |
| `home-core-cards_before_1920w.png` | CHECKLIST §4 改前 | **存在** | **1280×455**（非满屏 1920×1080） | ⚠ 文件名含 1920w，**实测非 1920×1080 满屏**；可作前后对比参考，**不能单独当作 1920×1080 验收帧** |
| `home-core-cards_after_1920w.png` | CHECKLIST §4 改后 | **存在** | **1280×455** | 同上 |
| `home-core-cards_before_390w.png` | 窄屏改前 | **存在** | **390×1570** | 移动参考；非 TASK 点名分辨率 |
| `home-core-cards_after_390w.png` | 窄屏改后 | **存在** | **390×1570** | 同上 |
| `slice3\06_home_core_cards_regression_390w.png` | 窄屏回归 | **存在** | （未再测；文件在） | 窄屏参考 |
| **任意 `*rf8*1440*` / `*home*core*1440*`（phase1-frontend）** | RF-8 @ 1440×900 | **不存在** | — | ❌ **待补** |
| `D:\RubbingMind\screenshots\product-upgrade\phase0-frontend\01_home_1440x900.png` | phase0 首页（非 RF-8 专项） | 存在 | （phase0，非本票证据） | ❌ **不可替代** RF-8 phase1 确认 |

### B.4 待补清单（不伪造文件）

| 待补文件（建议路径） | 分辨率 | 说明 |
|---|---|---|
| `...\phase1-frontend\slice16\rf8_home_core_cards_1440x900.png`（或同目录等价名） | **1440×900** | Green / TASK_BOARD 点名；**当前缺失** |
| （可选）满屏改前/改后各一帧若用户要「前后对比」满屏 | 1920×1080 与/或 1440×900 | 现有 `*_1920w` 仅 1280×455 裁切区 |

本 tip **不生成、不伪造**任何截图二进制。

### B.5 用户确认操作建议

1. 打开 tip 构建后的首页，查看「核心算法样本」卡片。  
2. 对照 `slice10\rf8_home_core_cards_1920x1080.png`（已有）与补拍的 **1440×900** 帧。  
3. 确认：字口未被裁切、纸色衬底 `bg-[#eee4d2]` 可见、无 cover 拉伸裁边。  
4. 书面回复 Green / 报告前端「RF-8 截图确认通过」后，再由 Green 关单——**执行器不得自关**。

---

## C. 本 tip 范围

- 仅新增本文件：`docs/product-upgrade/REPORT_FRONTEND_P1_OPEN_AND_RF8_SHOTS.md`
- 不修改 ACCEPTANCE 结论行、不改 HomePage、不 push、不合 main

## D. 建议门禁

- 窄门禁 / docs-only：核对本文件路径存在、声明 RF-8=仍开、1440×900 标「待补」、未改 `apps/web`。

---

## E. 续页（RM-报告前端 · tip after 0c1ac0c · 2026-10-25 18:48 Asia/Shanghai）

> **docs + 真实截图**。未改 HomePage / App.tsx / api.ts / urlState.ts。**未自关 RF-8**。未 push。未抬 verification / 未关 Phase1。

### E.1 本轮补拍：RF-8 首页核心卡 @ 1440×900

| 字段 | 值 |
|---|---|
| 绝对路径（证据台账） | D:\RubbingMind\screenshots\product-upgrade\phase1-frontend\slice16\rf8_home_core_cards_1440x900.png |
| 仓库相对路径（本 tip 入库） | screenshots/product-upgrade/phase1-frontend/slice16/rf8_home_core_cards_1440x900.png |
| 视口 / deviceScaleFactor | 1440×900 / **1** |
| **Pillow 实测像素** | **1440×900** |
| 文件大小 | 1197153 bytes |
| 拍摄时间（Asia/Shanghai） | 2026-10-25 18:47:32 +0800 |
| DOM 抽查（Playwright） | object-contain=4，object-cover=0，imgs=4（首页核心卡） |
| 1920 帧 | **已有，本轮不重拍**：slice10\rf8_home_core_cards_1920x1080.png（及 slice7 同名副本） |
| RF-8 状态 | **仍开 / 待用户确认**（禁止自关；禁止改 HomePage） |

校验旁证：screenshots/product-upgrade/phase1-frontend/slice16/slice16-rf8-verify.json（含 measured_px / captured_at）。

### E.2 B.3 / B.4 缺口关闭情况（截图层）

- ~~缺少 *rf8*1440* / *home*core*1440*~~ → **已补**（上表）。
- 产品闸门 / 用户确认仍未完成 → RF-8 **不得**标关闭。

### E.3 P1 开项轻量再盘点（相对 tip@0c1ac0c，docs-only）

| 项 | 状态 | 备注 |
|---|---|---|
| **RF-8** | **仍开** | 1920+1440 证据帧齐；待用户目视确认 contain/纸色底 |
| RF-2..7,9..11 / P1-1,4..9,11 | 仍开（产品闸门） | tip 上有代码证据 ≠ 关单 |
| algorithmOutputMode UI | CHECKLIST §2 文案仍可能偏旧 | tip 已接 algorithmLayer；不抬 verification |
| BR-09 includeDemo | CHECKLIST 临时 | 有既有截图/证据；非本轮 |
| AB-8 health banner | 非本 Agent 范围 | App.tsx |
| ACCEPTANCE Phase1 全表 | **仍开** | 证据 ≠ 口头关闭；本 tip 不声称 Phase1/六层关闭 |
| 可叠代码 tip | 无 | 扫描无新的可合入报告前端代码缺口（除 RF-8 用户确认外） |

### E.4 本 tip 范围

- 新增：screenshots/.../slice16/rf8_home_core_cards_1440x900.png + verify json
- 更新：本续页
- 不做：push、改 HomePage、关 RF-8、抬 verification
