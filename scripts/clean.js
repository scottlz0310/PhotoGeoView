import fs from 'fs'
import path from 'path'

const targets = [
  'dist',
  'build',
  'out',
  'coverage',
  '.pwtest-cache',
  path.join('src-tauri', 'target'),
  path.join('src-tauri', 'gen'),
]

for (const relativePath of targets) {
  const targetPath = path.join(process.cwd(), relativePath)
  if (fs.existsSync(targetPath)) {
    fs.rmSync(targetPath, { recursive: true, force: true })
    console.log(`Removed: ${relativePath}`)
  }
}

const srcRoot = path.join(process.cwd(), 'src')

const removeGeneratedJs = (dirPath) => {
  if (!fs.existsSync(dirPath)) {
    return
  }

  const entries = fs.readdirSync(dirPath, { withFileTypes: true })
  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name)
    if (entry.isDirectory()) {
      removeGeneratedJs(fullPath)
      continue
    }

    if (!entry.isFile()) {
      continue
    }

    if (!fullPath.endsWith('.js') && !fullPath.endsWith('.jsx')) {
      continue
    }

    const basePath = fullPath.replace(/\.jsx?$/, '')
    const hasTsSource =
      fs.existsSync(`${basePath}.ts`) || fs.existsSync(`${basePath}.tsx`)
    if (hasTsSource) {
      fs.rmSync(fullPath, { force: true })
      console.log(`Removed: ${path.relative(process.cwd(), fullPath)}`)
    }
  }
}

removeGeneratedJs(srcRoot)
