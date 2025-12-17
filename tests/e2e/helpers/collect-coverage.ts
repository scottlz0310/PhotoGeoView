import fs from 'node:fs'
import path from 'node:path'
import type { Page } from '@playwright/test'

export async function saveRendererCoverage(page: Page) {
  try {
    const coverage = await page.evaluate(() => (globalThis as any).__coverage__)
    if (!coverage) {
      if (process.env.VITE_COVERAGE === 'true') {
        // eslint-disable-next-line no-console
        console.warn(
          'Renderer coverage not found on globalThis.__coverage__ (instrumentation may be missing).'
        )
      }
      return
    }
    fs.mkdirSync('.nyc_output', { recursive: true })
    const file = path.join('.nyc_output', `renderer-${Date.now()}.json`)
    fs.writeFileSync(file, JSON.stringify(coverage))
  } catch (e) {
    // swallow errors to avoid breaking e2e cleanup
    // but log to console for CI visibility
    // eslint-disable-next-line no-console
    console.warn('Failed to save renderer coverage:', (e as Error).message)
  }
}
