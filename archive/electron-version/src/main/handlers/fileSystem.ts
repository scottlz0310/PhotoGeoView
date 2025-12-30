import fs from 'node:fs/promises'
import path from 'node:path'
import { dialog } from 'electron'
import {
  type FileEntry,
  failure,
  type GetDirectoryContentsRequest,
  GetDirectoryContentsRequestSchema,
  type GetDirectoryContentsResponse,
  type GetFileInfoRequest,
  GetFileInfoRequestSchema,
  type Result,
  success,
} from '../../types/ipc'

// Image file extensions
const IMAGE_EXTENSIONS = new Set([
  '.jpg',
  '.jpeg',
  '.png',
  '.gif',
  '.bmp',
  '.webp',
  '.tiff',
  '.tif',
  '.heic',
  '.heif',
  '.raw',
  '.cr2',
  '.nef',
  '.arw',
  '.dng',
])

/**
 * Check if a file is an image based on its extension
 */
function isImageFile(filename: string): boolean {
  const ext = path.extname(filename).toLowerCase()
  return IMAGE_EXTENSIONS.has(ext)
}

/**
 * Get file information
 */
export async function getFileInfo(request: GetFileInfoRequest): Promise<Result<FileEntry>> {
  try {
    // Validate request
    const validated = GetFileInfoRequestSchema.parse(request)

    const stats = await fs.stat(validated.path)
    const filename = path.basename(validated.path)
    const ext = path.extname(filename)

    const fileEntry: FileEntry = {
      name: filename,
      path: validated.path,
      isDirectory: stats.isDirectory(),
      size: stats.size,
      modifiedTime: stats.mtimeMs,
      extension: ext || undefined,
      isImage: !stats.isDirectory() && isImageFile(filename),
    }

    return success(fileEntry)
  } catch (error) {
    return failure(error instanceof Error ? error : new Error(String(error)))
  }
}

/**
 * Get directory contents
 */
export async function getDirectoryContents(
  request: GetDirectoryContentsRequest
): Promise<Result<GetDirectoryContentsResponse>> {
  try {
    // Validate request
    const validated = GetDirectoryContentsRequestSchema.parse(request)

    // Read directory
    const dirEntries = await fs.readdir(validated.path, { withFileTypes: true })

    // Process entries
    const entries: FileEntry[] = []

    for (const entry of dirEntries) {
      // Skip hidden files if not requested
      if (!validated.includeHidden && entry.name.startsWith('.')) {
        continue
      }

      const fullPath = path.join(validated.path, entry.name)

      try {
        const stats = await fs.stat(fullPath)
        const ext = path.extname(entry.name)
        const isImage = !entry.isDirectory() && isImageFile(entry.name)

        // Skip non-image files if imageOnly is true
        if (validated.imageOnly && !isImage && !entry.isDirectory()) {
          continue
        }

        entries.push({
          name: entry.name,
          path: fullPath,
          isDirectory: entry.isDirectory(),
          size: stats.size,
          modifiedTime: stats.mtimeMs,
          extension: ext || undefined,
          isImage,
        })
      } catch (error) {
        // Skip files we can't read
        console.warn(`Failed to read file ${fullPath}:`, error)
      }
    }

    // Sort: directories first, then by name
    entries.sort((a, b) => {
      if (a.isDirectory !== b.isDirectory) {
        return a.isDirectory ? -1 : 1
      }
      return a.name.localeCompare(b.name)
    })

    return success({
      path: validated.path,
      entries,
    })
  } catch (error) {
    return failure(error instanceof Error ? error : new Error(String(error)))
  }
}

/**
 * Open directory selection dialog
 */
export async function selectDirectory(): Promise<Result<string | null>> {
  try {
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory'],
    })

    if (result.canceled || result.filePaths.length === 0) {
      return success(null)
    }

    return success(result.filePaths[0])
  } catch (error) {
    return failure(error instanceof Error ? error : new Error(String(error)))
  }
}
