# AB / RT 开项盘点（续 feature@bd15ce0，2026-10-25 19:06 Asia/Shanghai）

作者：RM-架构后端。未 push。

## 基线 tip

- `feature/product-grade-upgrade` = arch = **bd15ce01fe9467bf23124ca6a4335a987874bfe1**
- 近序：… → d376dbc（RT-010 draft + RT006 备忘）→ eba2faf（金石 NOTES）→ bd15ce0（报告 RF-8 1440 证据；**RF-8 仍开**）

## 已在 tip、无需再叠

- AB-8：`HealthResponse` / `getHealth` + `App.tsx` `data-testid=health-samples-banner`
- algorithmOutputMode 契约 + UI（arch@847e7f1 / report@5195b5b）
- RT-005 / RT-007 / RT-008（产品级 Vite+loopback；tailwind moderate 仍开）/ RT-009 / RT-013
- RT-010：正式 `ci.yml` 已含 `feature/**`；草稿 `ci-feature.draft.yml` 含 `draft-feature-gate` / GIS / eval-contracts / repo-validation / browser preview（**仍未迁入 .github/workflows/**）

## 仍等用户

| 项 | 状态 |
|---|---|
| RT-006 `static/index.html` A/B/C | 等用户 widget；见 `RT006_USER_DECISION_BRIEF.md`（备忘≠拍板） |
| RF-8 首页 object-contain | 等用户截图确认；报告 tip 仅补证据/清单，**勿假关** |

## 仍等 Green / 门禁

| 项 | 状态 |
|---|---|
| eval@4d93c78 | parent=bd15ce0；完整门禁中——**过闸后再 FF**；勿合旧 `43d77b1` / `6f42ab1` |
| RT-008 tailwind v4 | 暂缓 |
| RT-010 草稿迁入正式 workflow | 须 Green 再批；本侧只扩 draft |

## 铁律

未 push；勿推 main；勿 C-08 --apply；勿杀非本进程；勿碰 Codex worktrees；主库 SHA 8408DBC3… / 854DF859…。
