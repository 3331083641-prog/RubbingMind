# RT-006 用户决策备忘：`static/index.html` A / B / C

> 状态：**等用户 widget 拍板**。本文仅汇总事实与选项，**不自选执行**。  
> 作者：RM-架构后端 · 2026-10-25 18:40 Asia/Shanghai · tip 基线 `0c1ac0c`（出 tip 时以 arch tip 为准）  
> 未 push；不改代码路径下的 `static/index.html` / `DeduceRequest`，直至 widget 选定。

## 现状（已核）

| 项 | 事实 |
|---|---|
| 产品主页 `GET /` | 有 `apps/web/dist/index.html` → 返回 React；**无 dist → HTTP 503** `frontend_build_required`，**不会**再回退渲染 `static/index.html` |
| `static/index.html` | 仍存在于仓库（约 90KB）；经 `StaticFiles` 挂在 `/static/`，故 **`/static/index.html` 仍可 200** |
| 旧页风险 | Vue CDN、无 SRI；`localStorage` 键 `rm_api_key` / `rm_base_url` / `rm_model`；调用已不存在的 `/api/samples` 等旧接口 |
| `DeduceRequest.api_key` | `main.py` 中仍有未使用可选字段；与静态页一并列入 REVIEW，**删除字段可与 A/B/C 同批或随后单独授权** |

相关旧说明：`docs/product-upgrade/RT006_STATIC_INDEX_DECISION.md`。

## 选项（请选一）

| 选项 | 动作 | 用户可见变化 | 风险 / 收益 |
|---|---|---|---|
| **A** | 删除 `static/index.html`（建议同时去掉未用 `DeduceRequest.api_key`） | 书签 `/static/index.html` → **404**；`GET /` 行为不变（仍靠 dist / 503） | 最干净；去掉 API Key 进 localStorage 的旧入口 |
| **B** | 移到 `docs/legacy/` 或 `archive/`，并从 StaticFiles 暴露路径排除 | 线上不再 200；仓库仍留档可查 | 可回溯；需改挂载/目录约定 |
| **C** | 保留文件 | `/static/index.html` 继续 200 | 零操作；旧钥匙页与死接口提示仍在 |

## 建议阅读顺序（给拍板用）

1. 是否还有人依赖书签打开 `/static/index.html`？（有 → 偏 B 或先公告再 A；无 → A）
2. 是否接受「仓库留档、线上不可达」？（是 → B）
3. 是否暂时什么都不动？（C；安全债保留）

## 执行约束（选定后）

- 仅在用户 widget 明确 A/B/C 且 Green 下令后，架构才改文件
- 禁止在未授权时自选删除或归档
- 不 push；不改 main；不动 Codex worktrees
