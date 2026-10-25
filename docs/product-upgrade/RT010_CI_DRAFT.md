# RT-010 CI 草案（未关单）

> 状态：**草案 / 可部分落地**。产品 RT-010 保持开项。ADR_R2 曾要求「只写草案，不改正式 workflow」；本 tip 按 Green 授权写草案，并对正式 `ci.yml` 仅做**最小触发扩展**（见下）。不 push、不合 main。

## 现状缺口（REVIEW_FINDINGS RT-010）

- `.github/workflows/ci.yml` 的 `on.push/pull_request.branches` **仅 `main`**
- 未覆盖：`validate_history_gis.py`、`test_graph_browser.py`、`test_terrain3d_v22_browser.py`
- `test_technical_v2_browser.py` 仅以 `--ci` 跑，移动端失败（RT-001）不会在 feature CI 暴露

## 验收口径

- 合入前有完整本地回归记录；或 feature 分支有 CI 运行记录
- 本 tip **不**宣称 RT-010 关闭

## 本 tip 已做

1. 正式 `ci.yml`：`push` / `pull_request` 增加 `feature/**`（最小触发扩展，便于 feature 分支有证据）
2. 草案工作流全文：`docs/product-upgrade/ci-feature.draft.yml`（**不**放在 `.github/workflows/`，避免误触发；待 Green 批准后再迁入）

## 建议正式启用顺序（需 Green 拍板）

1. 将 `ci-feature.draft.yml` 迁入 `.github/workflows/` 或合并进 `ci.yml`
2. 新增 job：`validate_history_gis.py`、graph / terrain3d browser、technical_v2 非 `--ci` 或显式 mobile viewport
3. 与 RT-001（technical_v2 移动导航）一并修，避免 feature CI 红灯无人认领

## Green scope 2026-10-25 18:01（Asia/Shanghai）

授权：仅扩展 `docs/product-upgrade/ci-feature.draft.yml`，**禁止**改 `.github/workflows/ci.yml` 生效面。

本 tip：

- 新增草稿 job `draft-feature-gate`：串联 `pytest tests/ -v` + `python scripts/validate_museum_v3.py` + `apps/web` 的 `npm ci` / `npm run build`（含 security_scan + init_db 前置）
- 保留原 `backend-test` / `frontend-build` / `browser-extended-draft`（含 history GIS / browser 提案步骤，`continue-on-error`）
- 仍为草稿；迁入 `.github/workflows/` 须 Green 再批

暂缓：RT-008 tailwind v4；RT-006 / RF-8 仍等用户。

## Green scope 2026-10-25 18:40（Asia/Shanghai）

空档续做：仅扩 `ci-feature.draft.yml`；仍禁改 `.github/workflows/ci.yml`。

本 tip 相对 `d6f434d` / `0c1ac0c` 基线新增草稿 job：

- `draft-catalogue-gis`：`validate_history_gis.py` **硬门**（无 `continue-on-error`）
- `draft-eval-contracts`：`pytest tests/test_es_derived_contracts.py -v`
- `draft-repository-validation`：关键产物存在性检查（含 draft 自身与 validate 脚本）
- `browser-extended-draft`：增加 loopback `vite preview :4173` 就绪等待后再跑 browser 脚本
- `concurrency` 组：同 ref 取消进行中的草稿 run

并行：`RT006_USER_DECISION_BRIEF.md` docs-only，供用户 A/B/C widget；**不执行**删除/归档。

