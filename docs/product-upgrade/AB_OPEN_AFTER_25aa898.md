# AB 开项盘点（续 feature@5a7b20c，2026-10-25 Asia/Shanghai）

作者：RM-架构后端。未 push。

## 本 tip 已合

- `api.ts`：`HealthResponse` + `SteleService.getHealth()`（RT-002 `samples_*` 契约）
- `App.tsx`：AB-8 非阻断横幅 `data-testid=health-samples-banner`（缺失 / SHA 不一致 / degraded）
- `reportData.ts`：`adaptiveDiagnostics.algorithmOutputMode` 随 report@5195b5b 已入 tip
- Workbench / types：algorithmOutputMode 契约（arch@847e7f1）

## 已在 tip 内、无需再叠的 RT/AB

- RT-005 安全头 + remote 关闭 docs/openapi
- RT-007 `.env.example` 密钥指引
- RT-008 Vite 6.4.5 + loopback（产品级；tailwind moderate）
- RT-009 严格 loopback（穿透头拒绝）
- RT-010 `ci.yml` 已含 `feature/**` + `ci-feature.draft.yml` 草稿（产品级；更多 job 待扩展）
- RT-013 soft-delete trash

## 仍等用户 / Green

| 项 | 状态 |
|---|---|
| RT-006 `static/index.html` 全删 A/B/C | 等用户 widget |
| RF-8 首页 object-contain 截图确认 | 等用户；禁止自关 |
| RT-008 tailwind v4 / RT-010 扩展 CI | 等 Green 定 scope |
| eval@c6de56e | 门禁中，过闸后再合 |

## 铁律

未 push；勿推 main；勿 C-08 --apply；勿杀非本进程。
