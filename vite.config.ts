import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

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
