#!/usr/bin/env node
const path = require('node:path')
const fs = require('node:fs/promises')
const { createInstrumenter } = require('istanbul-lib-instrument')

async function instrumentDir(src, dest, instrumenter) {
  await fs.mkdir(dest, { recursive: true })
  const entries = await fs.readdir(src, { withFileTypes: true })
  for (const entry of entries) {
    const sPath = path.join(src, entry.name)
    const dPath = path.join(dest, entry.name)
    if (entry.isDirectory()) {
      await instrumentDir(sPath, dPath, instrumenter)
    } else if (entry.isFile()) {
      if (path.extname(entry.name) === '.js') {
        const code = await fs.readFile(sPath, 'utf8')
        const instrumented = instrumenter.instrumentSync(code, sPath)
        await fs.writeFile(dPath, instrumented, 'utf8')
      } else {
        await fs.copyFile(sPath, dPath)
      }
    }
  }
}

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

  console.log('Instrumenting JS files using istanbul-lib-instrument...')
  const instrumenter = createInstrumenter({ esModules: true, produceSourceMap: false })

  try {
    await instrumentDir(outRenderer, tmpRenderer, instrumenter)

    // Adjust index.html in instrumented output to allow 'unsafe-eval' for coverage code
    const indexPath = path.join(tmpRenderer, 'index.html')
    try {
      let indexHtml = await fs.readFile(indexPath, 'utf8')
      // Ensure CSP allows 'unsafe-eval' for script-src so coverage instrumentation can run
      if (/Content-Security-Policy/.test(indexHtml)) {
        indexHtml = indexHtml.replace(/(<meta[^>]+http-equiv=["']Content-Security-Policy["'][^>]*content=")([^"]+)("[^>]*>)/i, (m, p1, p2, p3) => {
          // Add unsafe-eval and unsafe-inline to script-src
          const newContent = p2.replace(/script-src\s+'self'([^;]*)/, (m2, p21) => {
            if (/unsafe-eval/.test(p21)) return m2
            return `script-src 'self' 'unsafe-eval' 'unsafe-inline'${p21 || ''}`
          })
          return p1 + newContent + p3
        })
        await fs.writeFile(indexPath, indexHtml, 'utf8')
        console.log('Patched existing CSP in instrumented index.html to allow unsafe-eval for coverage')
      } else {
        // insert CSP meta tag into <head>
        indexHtml = indexHtml.replace(/<head(.*?)>/i, (m) => `${m}\n  <meta http-equiv="Content-Security-Policy" content="script-src 'self' 'unsafe-eval' 'unsafe-inline';" />`)
        await fs.writeFile(indexPath, indexHtml, 'utf8')
        console.log('Inserted CSP meta tag in instrumented index.html to allow unsafe-eval for coverage')
      }
    } catch (e) {
      // ignore if index.html not found
      console.warn('Could not patch index.html for CSP:', (e && e.message) || e)
    }
  } catch (err) {
    console.error('Instrumentation error:', err)
    process.exit(1)
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
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
