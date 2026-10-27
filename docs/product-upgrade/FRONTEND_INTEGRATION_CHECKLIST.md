# 前端对接清单（RM-报告前端 / slice3）

> 日期：2026-10-25（Asia/Shanghai）  
> 分支：`agent/report-frontend`  
> 相对 tip：`f11eb1f` → merge `agent/arch-backend@84c31ee` → **再 merge `agent/arch-backend@a261ba0`**  
> 本 Agent **不直接改** `App.tsx` / `api.ts` / `urlState.ts`（URL 层归架构后端）；通过 merge 合入其后端提交。

## 1. 分支 tip 与合入关系

| 分支 | tip（查本地） | 说明 |
|------|---------------|------|
| `agent/arch-backend` | `a261ba0` | gray-bt601、includeDemo BR-08、algorithmOutputMode ADR、C-08 |
| `agent/report-frontend`（本 worktree） | merge → `a261ba0` | 无冲突；`apps/web/src/services/api.ts` 取 arch-backend 版本 |
| `feature/product-grade-upgrade` | （集成分支） | 本 Agent 不 push |

本轮相对 `84c31ee` 新合入：`56bb0cf` gray-bt601 五元组 → `768243b` algorithmOutputMode ADR → `92de823` includeDemo → `a4e9098`/`a261ba0` C-08。

## 2. 已接字段 / 行为（证据：文件+行号）

### URL / 选择契约（RF-2）

| 项 | 状态 | 证据 |
|----|------|------|
| ReportsPage props：`runId`/`onRunChange`/`experimentId`/`batch`/`onExperimentChange`/`experimentStatus` | 已接 | `ReportsPage.tsx` Props；App 传入（merge 自 arch，本 Agent 不改 App） |
| 页内筛选不改 URL | 已接 | `reportFilters.ts` |
| 默认运行走 `getReportSelection`，禁止 `items[0]` | 已接 | `ReportsPage.tsx` + `ReportApi.selection` → `SteleService.getReportSelection`（`api.ts` ~155） |
| `experimentId` 权威；默认只认 `defaultForReport` | 已接 | `reportData.ts` `resolveBatch`/`defaultBatchId`/`classifyBatch` |
| App 层 `experimentStatus` 空状态 | 已接 | `data-testid="app-unknown-experiment"` / `app-unavailable-experiment` |

### RF-11 文案

| 项 | 状态 | 证据 |
|----|------|------|
| `isPassthrough=true` →「本次未改动原图」 | 已接 | `reportData.ts` `runOutcome` |
| `passthroughSource=computed-on-read` →「读取时校验」 | 已接 | `ArtifactRunReport.tsx` badge `data-testid="computed-on-read"` |
| 无残留「本次算法输出」/ UI「算法输出」 | 已扫 | UI 改为「算法已改动像素」（含 `ReportPrintLayout.tsx`）；仅注释提及旧文案 |
| 工作台朱砂标签 | 已接 | WorkbenchPage：「算法处理结果 · 朱砂…」 |

### RF-3/4/5/6

| 项 | 状态 | 证据 |
|----|------|------|
| ECharts 负值不截断、分轴 | 已接 | `MethodComparisonChart.tsx`：`scale: false`，`min/max` 含 0 与 CI |
| 三联同步缩放/滑杆/ROI/`object-contain` | 已接 | `SyncedTriptych.tsx` |
| 失败案例入口 | 已接 | `FailureCasesPanel.tsx` + ContextBar tab |
| A4 打印 | 已接 | `reportPrint.css` `@page { size: A4 portrait }` + `ReportPrintLayout.tsx` |

### gray* / comparedImages / effectiveParameters / includeDemo

| 字段 | 状态 | 证据 |
|------|------|------|
| `grayChangedPixelCount` →「灰度域改动 N 像素」 | 已接 | `runOutcome.grayText` + `data-testid="gray-change"` |
| `grayCriterion='gray-bt601-pixel-equal-v1'` | **已合入类型** | merge `a261ba0` → `api.ts`；前端原样展示 |
| `graySource` recorded / computed-on-read | 已接 | grayText 注明「读取时校验，仅参考，不决定 isPassthrough」 |
| `comparedImages: string[]` | 已接 | ArtifactRunReport 判据行；JSON 导出 |
| `effectiveParametersUnavailableReason` | 已接 | `data-testid="eff-params-unavailable"` |
| `includeDemo`（BR-08 API） | **API 已接** | `SteleService.queryEvidence(..., includeDemo=false)`（`api.ts`）；UI 开关 = BR-09，本轮不做 |
| `outputMode` run-level | 类型已在 api | 展示仍以 `isPassthrough`/`runOutcome` 为准 |
| `algorithmOutputMode`（ADR R2-12） | **文档已合入，UI 未接** | `MERGE_NOTE_algorithmOutputMode.md` / `ADR_R2_SUPPLEMENT.md`；属算法/诊断层，等 eval-sci 共享文件落地后再接 |

## 3. 待办 / 下一切片

1. **BR-09** EvidenceSearch「包含演示样本」开关（默认关 + 合成数据提示）—— Green：RF 做完有余力再做；本轮列入下一切片。  
2. **algorithmOutputMode** 展示（与 run-level `outputMode` 并列说明）—— 等后端字段出现在 run/diagnosis payload。  
3. **reportStatus** 全链路文案（stele_retired / run_not_found）—— 可选小改 `ReportApi.report`。  
4. derived CI 改走只读 HTTP 端点（可选）。

## 4. RF-8 首页样本卡

用户已确认。截图仍有效（未重做样式、未 push）：

- `D:\RubbingMind\screenshots\product-upgrade\phase1-frontend\home-core-cards_before_1920w.png`
- `D:\RubbingMind\screenshots\product-upgrade\phase1-frontend\home-core-cards_before_390w.png`
- `D:\RubbingMind\screenshots\product-upgrade\phase1-frontend\home-core-cards_after_1920w.png`
- `D:\RubbingMind\screenshots\product-upgrade\phase1-frontend\home-core-cards_after_390w.png`

## 5. Props 契约（ReportsPage / Workbench）

```
ReportsPage {
  stele, onNavigate,
  runId?, onRunChange?,
  experimentId?, batch?, onExperimentChange?,
  experimentStatus?: 'none'|'resolving'|'ok'|'unknown'|'unavailable'
}
WorkbenchPage { stele, onNavigate, runId?, onRunChange? }
```

URL 读写仅在 App/urlState（本 Agent 不改）；组件只消费 props。
