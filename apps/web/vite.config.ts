import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: ['katex', 'maplibre-gl', 'echarts/core', 'echarts/charts', 'echarts/components', 'echarts/renderers'],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.RUBBINGMIND_API_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/static': {
        target: process.env.RUBBINGMIND_API_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  },
  preview: {
    port: 4173,
    proxy: {
      '/api': {
        target: process.env.RUBBINGMIND_API_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/static': {
        target: process.env.RUBBINGMIND_API_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false
  }
});
