#!/usr/bin/env node
const { spawn } = require('node:child_process')
const path = require('node:path')
const fs = require('node:fs/promises')

async function run() {
  const repoRoot = path.join(__dirname, '..')
  const outRenderer = path.join(repoRoot, 'out', 'renderer')
  const tmpRoot = path.join(repoRoot, 'out-instrumented')
  const tmpRenderer = path.join(tmpRoot, 'renderer')

  // Clean tmp
  await fs.rm(tmpRoot, { recursive: true, force: true }).catch(() => {})

  // Ensure source exists
  try {
    await fs.access(outRenderer)
  } catch (e) {
    console.error('Expected built renderer at', outRenderer, 'but not found. Run `pnpm build` first.')
    process.exit(2)
  }

  const nycBin = path.join(repoRoot, 'node_modules', '.bin', process.platform === 'win32' ? 'nyc.cmd' : 'nyc')

  console.log('Running nyc instrument...')
  const inst = spawn(nycBin, ['instrument', outRenderer, tmpRenderer], { stdio: 'inherit' })

  inst.on('close', async (code) => {
    if (code !== 0) {
      console.error('nyc instrument failed with code', code)
      process.exit(code)
    }

    try {
      // Backup original just in case
      const backup = path.join(repoRoot, 'out-backup-renderer')
      await fs.rm(backup, { recursive: true, force: true }).catch(() => {})
      await fs.rename(outRenderer, backup)
      await fs.rename(tmpRenderer, outRenderer)
      // cleanup
      await fs.rm(backup, { recursive: true, force: true }).catch(() => {})
      await fs.rm(tmpRoot, { recursive: true, force: true }).catch(() => {})
      console.log('Instrumentation complete: out/renderer replaced with instrumented files')
      process.exit(0)
    } catch (err) {
      console.error('Failed to replace renderer with instrumented files:', err)
      process.exit(3)
    }
  })
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
