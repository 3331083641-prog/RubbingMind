# RT-006 剩余：`static/index.html` 全删决策（待 Green）

> 产品 RT-006 **保持开项**。本 tip 不删除、不归档 `static/index.html`。

## 已落地（此前 tip@12fc96e）

- 无 `apps/web/dist/index.html` 时，`GET /` 返回 **503** `frontend_build_required`
- **不再**回退到 `static/index.html`（含 Vue CDN / `rm_api_key` localStorage 的旧壳）

## 仍开：全删 / 归档

REVIEW_FINDINGS 建议删除或归档：

- `static/index.html`（CDN 无 SRI、API Key 进 localStorage、调用已不存在的 `/api/samples`）
- 未使用的 `DeduceRequest.api_key` 字段

**需 Green 拍板后再做**，原因：

1. 可能仍有书签 / 离线演示直接打开 `/static/index.html`（静态挂载仍可能 200）
2. 全删属于对外可观察行为变化，超出「无 dist→503」缓解范围
3. Green 曾禁止对共享表面擅自大改

## 建议决策选项

| 选项 | 动作 | 风险 |
|---|---|---|
| A | 删除 `static/index.html` + 相关死代码 | 书签 404 |
| B | 移到 `docs/legacy/` 或 `archive/` 并从 StaticFiles 排除 | 保留考古 |
| C | 保留文件但加醒目「已废弃」横幅且不挂 API Key | 半吊子 |

本 tip 默认：**等 Green 选 A/B/C**；架构侧仅保持 503 不回退。
