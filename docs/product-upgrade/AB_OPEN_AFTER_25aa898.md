# AB 开项盘点（相对 feature@25aa898，2026-10-25 Asia/Shanghai）

作者：RM-架构后端。未 push。

## 本 tip 落地

- `api.ts`：`HealthResponse` + `SteleService.getHealth()`（RT-002 `samples_*` 契约；UI 可后续消费）
- `reportData.ts`：`adaptiveDiagnostics.algorithmOutputMode` 与 ADR R2-12 / arch@847e7f1 对齐

## 已在 tip 内、无需再做代码的 RT/AB

- RT-005 安全头 + remote 关闭 docs/openapi
- RT-007 `.env.example` 键名对齐
- RT-008 Vite 6.4.5 + loopback（产品仍开：tailwind moderate）
- RT-009 可信 loopback（拒代理头绕过）
- RT-010 `ci.yml` 已含 `feature/**` + `ci-feature.draft.yml` 草稿（产品仍开：完整 job 扩展）
- RT-013 soft-delete trash
- algorithmOutputMode **类型契约**（847e7f1）；**UI 展示**仍属 report

## 仍等用户 / Green

| 项 | 状态 |
|---|---|
| RT-006 `static/index.html` 全删 A/B/C | 等用户 widget |
| RF-8 首页 object-contain 截图确认 | 等用户；勿自关 |
| algorithmOutputMode UI | report；类型已就绪 |
| RT-008 tailwind v4 / RT-010 完整 CI | 需 Green 扩 scope |

## 禁令

不 push、不合 main、不 C-08 --apply、不杀非本进程。
