import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// ARCHITECTURE_DECISIONS R1-7: the default stays http://127.0.0.1:8000 so the
// established 5180 -> 8000 workflow keeps working. Any other instance (agent
// worktrees, tests, demos) MUST set RUBBINGMIND_API_TARGET explicitly; when it
// is missing we warn loudly instead of silently talking to the main backend.
const DEFAULT_API_TARGET = 'http://127.0.0.1:8000';
const explicitTarget = process.env.RUBBINGMIND_API_TARGET?.trim();
const apiTarget = explicitTarget || DEFAULT_API_TARGET;

function warnImplicitTarget() {
  if (explicitTarget) return;
  const line = '='.repeat(72);
  console.warn([
    '',
    line,
    '[RubbingMind] 警告：未设置 RUBBINGMIND_API_TARGET，/api 与 /static 代理到默认',
    `             ${DEFAULT_API_TARGET}（主工作区后端）。`,
    '             若这是 worktree / 测试 / 演示实例，请先显式设置，例如：',
    '             $env:RUBBINGMIND_API_TARGET="http://127.0.0.1:8710"',
    '             否则页面读写的是主后端及其数据库，而不是本实例。',
    line,
    '',
  ].join('\n'));
}

const proxy = {
  '/api': { target: apiTarget, changeOrigin: true },
  '/static': { target: apiTarget, changeOrigin: true },
};

export default defineConfig(({ command }) => {
  if (command === 'serve') warnImplicitTarget();
  return {
    plugins: [react()],
    optimizeDeps: {
      include: ['katex', 'maplibre-gl', 'echarts/core', 'echarts/charts', 'echarts/components', 'echarts/renderers'],
    },
    // RT-008: bind loopback only (dev-server vulns are localhost-scoped).
    server: {
      host: '127.0.0.1',
      port: 5173,
      proxy,
    },
    preview: {
      host: '127.0.0.1',
      port: 4173,
      proxy,
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: false
    }
  };
});
