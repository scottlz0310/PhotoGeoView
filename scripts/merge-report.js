#!/usr/bin/env node
const fs = require('fs')
const path = require('path')
const libCoverage = require('istanbul-lib-coverage')
const libReport = require('istanbul-lib-report')
const reports = require('istanbul-reports')

const nycDir = path.resolve('.nyc_output')
if (!fs.existsSync(nycDir)) {
  console.error('.nyc_output directory not found. Run tests/e2e to generate coverage fragments first.')
  process.exitCode = 1
  process.exit()
}

const files = fs.existsSync(nycDir) ? fs.readdirSync(nycDir).filter(f => f.endsWith('.json')) : []

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
      process.exit()
    }
  }
} else {
  console.warn('No .json coverage fragments found in .nyc_output; continuing to check for vitest coverage files')
}

// Also merge Vitest coverage if present (coverage/vitest/coverage-final.json or coverage/coverage-final.json)
const vitestPaths = [path.resolve('coverage', 'vitest', 'coverage-final.json'), path.resolve('coverage', 'coverage-final.json')]
for (const vp of vitestPaths) {
  if (fs.existsSync(vp)) {
    try {
      const content = JSON.parse(fs.readFileSync(vp, 'utf8'))
      map.merge(content)
      console.log('Merged vitest coverage from', vp)
    } catch (err) {
      console.error('Failed to merge vitest coverage', vp, err)
      process.exitCode = 1
      process.exit()
    }
  }
}

fs.mkdirSync(path.resolve('coverage'), { recursive: true })
const mergedPath = path.resolve('coverage', 'merged.json')
fs.writeFileSync(mergedPath, JSON.stringify(map.toJSON(), null, 2), 'utf8')
console.log('Wrote merged coverage to', mergedPath)

// Generate HTML report into coverage/combined
const reportDir = path.resolve('coverage', 'combined')
fs.mkdirSync(reportDir, { recursive: true })
const context = libReport.createContext({ dir: reportDir, coverageMap: map })
const htmlReport = reports.create('html', {})
try {
  htmlReport.execute(context)
  console.log('Wrote HTML report to', reportDir)
} catch (err) {
  console.error('Failed to generate HTML report', err)
  process.exitCode = 1
}
