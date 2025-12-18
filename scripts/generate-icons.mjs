import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import path from 'node:path'
import sharp from 'sharp'
import pngToIco from 'png-to-ico'

const rootDir = process.cwd()
const sourcePng = path.join(rootDir, 'assets', 'icon.png')
const buildDir = path.join(rootDir, 'build')
const outIco = path.join(buildDir, 'icon.ico')
const outPng = path.join(buildDir, 'icon.png')

if (!existsSync(sourcePng)) {
  console.error(`Missing source icon: ${sourcePng}`)
  process.exit(1)
}

await mkdir(buildDir, { recursive: true })

// Keep build/icon.png in sync for electron-builder's mac/linux icon generation.
await writeFile(outPng, await readFile(sourcePng))

// ICO: include multiple PNG sizes (with alpha) for best Windows results.
const sizes = [16, 24, 32, 48, 64, 128, 256]
const pngBuffers = await Promise.all(
  sizes.map((size) =>
    sharp(sourcePng)
      .resize(size, size, { fit: 'contain' })
      .png({ compressionLevel: 9 })
      .toBuffer(),
  ),
)

const icoBuffer = await pngToIco(pngBuffers)
await writeFile(outIco, icoBuffer)

console.log(`Wrote ${outIco}`)
