import { resolve } from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import istanbul from 'vite-plugin-istanbul'

const isCoverage = process.env.VITE_COVERAGE === 'true'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin({ exclude: ['electron-store'] })],
    resolve: {
      alias: {
        '@main': resolve('src/main'),
        '@': resolve('src'),
      },
    },
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    resolve: {
      alias: {
        '@preload': resolve('src/preload'),
        '@': resolve('src'),
      },
    },
  },
  renderer: {
    build: {
      sourcemap: isCoverage,
      rollupOptions: {
        input: {
          index: resolve('src/renderer/index.html'),
          splash: resolve('src/renderer/splash.html'),
        },
      },
    },
    resolve: {
      alias: {
        '@renderer': resolve('src/renderer/src'),
        '@': resolve('src'),
      },
    },
    plugins: [
      react(),
      istanbul({
        include: 'src/renderer/src/**',
        exclude: ['node_modules', 'tests/**', '**/*.test.*'],
        extension: ['.ts', '.tsx', '.js', '.jsx'],
        requireEnv: true,
        forceBuildInstrument: true,
        cypress: false,
        checkProd: false,
      }),
    ],
  },
})
