import { resolve } from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/**/*.test.ts', 'tests/**/*.test.tsx'],
    exclude: ['node_modules/**', 'out/**', 'dist/**', 'tests/e2e/**'],
    coverage: {
      provider: 'istanbul',
      reporter: ['text-summary', 'json'],
      reportsDirectory: './coverage/vitest',
      include: ['src/renderer/src/**/*.{ts,tsx}', 'src/types/**/*.ts'],
      exclude: [
        'node_modules/**',
        'out/**',
        'dist/**',
        'tests/**',
        '**/*.d.ts',
        '**/*.config.*',
        '**/main.tsx',
        'src/main/**',
        'src/preload/**',
        'src/renderer/src/components/ui/**', // Exclude shadcn/ui components (3rd party)
      ],
      thresholds: {
        lines: 20,
        functions: 20,
        branches: 20,
        statements: 20,
      },
    },
  },
  resolve: {
    alias: {
      '@renderer': resolve(__dirname, './src/renderer/src'),
      '@': resolve(__dirname, './src'),
    },
  },
})
