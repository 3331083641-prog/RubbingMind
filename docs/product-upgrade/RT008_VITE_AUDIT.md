# RT-008 Vite / npm audit（未关单）

## 本 tip 落地

- `apps/web` `vite` 升至 `^6.4.5`（锁文件实测 `6.4.5`），清除 audit **high**（`<=6.4.3` 一组）
- `vite.config.ts` 与 `npm run dev` / `preview` 均绑定 `127.0.0.1`
- `npm audit --omit=dev`：**0** vulnerabilities（生产依赖链干净）

## 书面接受的剩余 moderate（仅 dev）

升级后仍剩 **3 moderate**，均来自 **tailwindcss@3 → postcss-nested → postcss-selector-parser<7.1.6**（CPU ReDoS）。

| 项 | 理由 |
|---|---|
| 影响面 | 仅本地 `npm run dev` / 构建工具链；生产 bundle 不含该解析器攻击面 |
| 修复成本 | `npm audit fix --force` 会升到 **tailwindcss@4**（breaking），超出本 tip 范围 |
| 缓解 | loopback bind（本 tip）+ 不把 Vite 暴露到非本机 |

产品 RT-008 **保持开项**，直至 tailwind v4 迁移或官方 backport 被接受。
