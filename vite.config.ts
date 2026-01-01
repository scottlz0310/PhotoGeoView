import { execSync } from 'child_process'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import istanbul from 'vite-plugin-istanbul'
import path from 'path'

const buildTime = new Date().toISOString()
const gitSha = (() => {
  const envSha = process.env.VITE_GIT_SHA ?? process.env.GIT_SHA
  if (envSha) {
    return envSha
  }
  try {
    return execSync('git rev-parse --short HEAD').toString().trim()
  } catch {
    return 'unknown'
  }
})()

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    istanbul({
      include: 'src/*',
      exclude: ['node_modules', 'test/', 'e2e/'],
      extension: ['.js', '.ts', '.tsx'],
      requireEnv: true,
    }),
  ],
  define: {
    'import.meta.env.VITE_BUILD_TIME': JSON.stringify(buildTime),
    'import.meta.env.VITE_GIT_SHA': JSON.stringify(gitSha),
  },

  // パスエイリアス
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  // 開発サーバー設定
  server: {
    port: 5173,
    strictPort: true,
  },

  // ビルド設定
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'map-vendor': ['leaflet', 'react-leaflet'],
          'ui-vendor': ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
        },
      },
    },
  },

  // 環境変数のプレフィックス
  envPrefix: 'VITE_',

  // 最適化設定
  optimizeDeps: {
    include: ['react', 'react-dom', 'leaflet', 'react-leaflet'],
    exclude: ['archive'],
    entries: ['src/**/*.tsx', 'src/**/*.ts'], // エントリーポイントを明示的に指定
  },
})
