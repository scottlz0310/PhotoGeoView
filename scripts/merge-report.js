#!/usr/bin/env node
const fs = require('fs')
const path = require('path')
const libCoverage = require('istanbul-lib-coverage')
const libReport = require('istanbul-lib-report')
const reports = require('istanbul-reports')
const libSourceMaps = require('istanbul-lib-source-maps')

function normalizePath(p) {
  return p.replace(/\\/g, '/')
}

async function main() {
  const repoRoot = path.resolve(__dirname, '..')
  const nycDir = path.resolve('.nyc_output')

  if (!fs.existsSync(nycDir)) {
    console.error('.nyc_output directory not found. Run tests/e2e to generate coverage fragments first.')
    process.exitCode = 1
    return
  }

  const files = fs.readdirSync(nycDir).filter((f) => f.endsWith('.json'))

  const map = libCoverage.createCoverageMap({})
  if (files.length > 0) {
    for (const file of files) {
      const p = path.join(nycDir, file)
      try {
        const content = JSON.parse(fs.readFileSync(p, 'utf8'))
        map.merge(content)
      } catch (err) {
        console.error('Failed to merge', p, err)
        process.exitCode = 1
        return
      }
    }
    console.log('Merged E2E coverage fragments:', files.length)
  } else {
    console.warn('No .json coverage fragments found in .nyc_output; continuing to check for vitest coverage files')
  }

  // Also merge Vitest coverage if present (coverage/vitest/coverage-final.json or coverage/coverage-final.json)
  const vitestPaths = [
    path.resolve('coverage', 'vitest', 'coverage-final.json'),
    path.resolve('coverage', 'coverage-final.json'),
  ]
  for (const vp of vitestPaths) {
    if (fs.existsSync(vp)) {
      try {
        const content = JSON.parse(fs.readFileSync(vp, 'utf8'))
        map.merge(content)
        console.log('Merged vitest coverage from', vp)
      } catch (err) {
        console.error('Failed to merge vitest coverage', vp, err)
        process.exitCode = 1
        return
      }
    }
  }

  // Remap bundle coverage -> original sources using source maps (Vite)
  let remapped = map
  try {
    const sourceMapStore = libSourceMaps.createSourceMapStore()
    remapped = await sourceMapStore.transformCoverage(map)
  } catch (err) {
    console.warn('Failed to remap coverage via source maps; continuing without remap:', err?.message || err)
  }

  // Filter to application sources (avoid node_modules/vendor skewing summary)
  const includeRoots = [
    normalizePath(path.join(repoRoot, 'src', 'renderer', 'src')) + '/',
    normalizePath(path.join(repoRoot, 'src', 'types')) + '/',
    'src/renderer/src/',
    'src/types/',
  ]
  const filtered = libCoverage.createCoverageMap({})
  for (const file of remapped.files()) {
    const normalized = normalizePath(file)
    const shouldInclude = includeRoots.some((root) => normalized.includes(root))
    if (!shouldInclude) continue
    filtered.addFileCoverage(remapped.fileCoverageFor(file))
  }

  if (filtered.files().length === 0) {
    console.warn('No application source files matched after remap/filter; falling back to unfiltered coverage map.')
    for (const file of remapped.files()) {
      filtered.addFileCoverage(remapped.fileCoverageFor(file))
    }
  }

  fs.mkdirSync(path.resolve('coverage'), { recursive: true })
  const mergedPath = path.resolve('coverage', 'merged.json')
  fs.writeFileSync(mergedPath, JSON.stringify(filtered.toJSON(), null, 2), 'utf8')
  console.log('Wrote merged coverage to', mergedPath)

  const context = libReport.createContext({ coverageMap: filtered })
  const textSummaryReport = reports.create('text-summary', {})
  try {
    textSummaryReport.execute(context)
  } catch (err) {
    console.error('Failed to generate coverage summary', err)
    process.exitCode = 1
  }
}

main().catch((err) => {
  console.error(err)
  process.exitCode = 1
})
