import { z } from 'zod'

// ============================================================================
// IPC Channel Names
// ============================================================================

export const IPC_CHANNELS = {
  // File System
  GET_DIRECTORY_CONTENTS: 'fs:getDirectoryContents',
  GET_FILE_INFO: 'fs:getFileInfo',
  READ_IMAGE_METADATA: 'fs:readImageMetadata',
  SELECT_DIRECTORY: 'fs:selectDirectory',

  // Image Processing
  GENERATE_THUMBNAIL: 'image:generateThumbnail',
  READ_EXIF: 'image:readExif',
  ROTATE_IMAGE: 'image:rotateImage',

  // Window
  MINIMIZE_WINDOW: 'window:minimize',
  MAXIMIZE_WINDOW: 'window:maximize',
  CLOSE_WINDOW: 'window:close',

  // Theme
  GET_SYSTEM_THEME: 'theme:getSystemTheme',

  // App
  GET_INITIAL_FILE: 'app:getInitialFile',
  GET_APP_VERSION: 'app:getVersion',

  // Store
  GET_STORE_VALUE: 'store:get',
  SET_STORE_VALUE: 'store:set',

  // Updater
  CHECK_FOR_UPDATES: 'updater:checkForUpdates',
  DOWNLOAD_UPDATE: 'updater:downloadUpdate',
  QUIT_AND_INSTALL: 'updater:quitAndInstall',
  UPDATE_AVAILABLE: 'updater:updateAvailable',
  UPDATE_NOT_AVAILABLE: 'updater:updateNotAvailable',
  UPDATE_DOWNLOADED: 'updater:updateDownloaded',
  UPDATE_ERROR: 'updater:error',
  DOWNLOAD_PROGRESS: 'updater:downloadProgress',

  // Context Menu
  SHOW_CONTEXT_MENU: 'context-menu:show',
} as const

// ============================================================================
// Validation Schemas (Zod)
// ============================================================================

// File Entry Schema
export const FileEntrySchema = z.object({
  name: z.string(),
  path: z.string(),
  isDirectory: z.boolean(),
  size: z.number(),
  modifiedTime: z.number(), // Unix timestamp
  extension: z.string().optional(),
  isImage: z.boolean().optional(),
})

export type FileEntry = z.infer<typeof FileEntrySchema>

// Directory Contents Request
export const GetDirectoryContentsRequestSchema = z.object({
  path: z.string(),
  includeHidden: z.boolean().optional().default(false),
  imageOnly: z.boolean().optional().default(false),
})

export type GetDirectoryContentsRequest = z.infer<typeof GetDirectoryContentsRequestSchema>

// Directory Contents Response
export const GetDirectoryContentsResponseSchema = z.object({
  path: z.string(),
  entries: z.array(FileEntrySchema),
})

export type GetDirectoryContentsResponse = z.infer<typeof GetDirectoryContentsResponseSchema>

// File Info Request
export const GetFileInfoRequestSchema = z.object({
  path: z.string(),
})

export type GetFileInfoRequest = z.infer<typeof GetFileInfoRequestSchema>

// EXIF Data Schema
export const ExifDataSchema = z.object({
  camera: z
    .object({
      make: z.string().optional(),
      model: z.string().optional(),
      lens: z.string().optional(),
    })
    .optional(),
  exposure: z
    .object({
      iso: z.number().optional(),
      aperture: z.number().optional(),
      shutterSpeed: z.string().optional(),
      focalLength: z.number().optional(),
    })
    .optional(),
  gps: z
    .object({
      latitude: z.number(),
      longitude: z.number(),
      altitude: z.number().optional(),
    })
    .optional(),
  timestamp: z.number().optional(), // Unix timestamp
  width: z.number().optional(),
  height: z.number().optional(),
})

export type ExifData = z.infer<typeof ExifDataSchema>

// Image Metadata Request
export const ReadImageMetadataRequestSchema = z.object({
  path: z.string(),
})

export type ReadImageMetadataRequest = z.infer<typeof ReadImageMetadataRequestSchema>

// Image Metadata Response
export const ReadImageMetadataResponseSchema = z.object({
  path: z.string(),
  exif: ExifDataSchema.optional(),
})

export type ReadImageMetadataResponse = z.infer<typeof ReadImageMetadataResponseSchema>

// Thumbnail Generation Request
export const GenerateThumbnailRequestSchema = z.object({
  path: z.string(),
  width: z.number().optional().default(200),
  height: z.number().optional().default(200),
})

export type GenerateThumbnailRequest = z.infer<typeof GenerateThumbnailRequestSchema>

// Thumbnail Generation Response
export const GenerateThumbnailResponseSchema = z.object({
  path: z.string(),
  thumbnail: z.string(), // Base64 encoded image
  width: z.number(),
  height: z.number(),
})

export type GenerateThumbnailResponse = z.infer<typeof GenerateThumbnailResponseSchema>

// Read EXIF Request
export const ReadExifRequestSchema = z.object({
  path: z.string(),
})

export type ReadExifRequest = z.infer<typeof ReadExifRequestSchema>

// Read EXIF Response
export const ReadExifResponseSchema = z.object({
  path: z.string(),
  exif: ExifDataSchema,
})

export type ReadExifResponse = z.infer<typeof ReadExifResponseSchema>

// Rotate Image Request
export const RotateImageRequestSchema = z.object({
  path: z.string(),
  angle: z.number().refine((val) => [90, 180, 270, -90].includes(val), {
    message: 'Angle must be 90, 180, 270, or -90',
  }),
})

export type RotateImageRequest = z.infer<typeof RotateImageRequestSchema>

// Rotate Image Response
export const RotateImageResponseSchema = z.object({
  path: z.string(),
  success: z.boolean(),
})

export type RotateImageResponse = z.infer<typeof RotateImageResponseSchema>

// Context Menu Request
export const ShowContextMenuRequestSchema = z.object({
  type: z.enum(['file', 'folder', 'background']),
  path: z.string().optional(),
})

export type ShowContextMenuRequest = z.infer<typeof ShowContextMenuRequestSchema>

// ============================================================================
// Result Type Pattern for Error Handling
// ============================================================================

export type Result<T, E = Error> = { success: true; data: T } | { success: false; error: E }

// Helper functions to create Result types
export const success = <T>(data: T): Result<T> => ({
  success: true,
  data,
})

export const failure = <E = Error>(error: E): Result<never, E> => ({
  success: false,
  error,
})

// ============================================================================
// IPC API Type Definition (for preload script)
// ============================================================================

export interface SystemTheme {
  shouldUseDarkColors: boolean
  themeSource: 'system' | 'light' | 'dark'
}

export interface IpcApi {
  // File System
  getDirectoryContents: (
    request: GetDirectoryContentsRequest
  ) => Promise<Result<GetDirectoryContentsResponse>>
  getFileInfo: (request: GetFileInfoRequest) => Promise<Result<FileEntry>>
  readImageMetadata: (
    request: ReadImageMetadataRequest
  ) => Promise<Result<ReadImageMetadataResponse>>
  selectDirectory: () => Promise<Result<string | null>>

  // Image Processing
  generateThumbnail: (
    request: GenerateThumbnailRequest
  ) => Promise<Result<GenerateThumbnailResponse>>
  readExif: (request: ReadExifRequest) => Promise<Result<ReadExifResponse>>
  rotateImage: (request: RotateImageRequest) => Promise<Result<RotateImageResponse>>

  // Window
  minimizeWindow: () => void
  maximizeWindow: () => void
  closeWindow: () => void

  // Theme
  getSystemTheme: () => Promise<Result<SystemTheme>>

  // App
  getInitialFile: () => Promise<Result<{ filePath: string; dirPath: string } | null>>
  getAppVersion: () => Promise<string>

  // Store
  // biome-ignore lint/suspicious/noExplicitAny: Value can be any type
  getStoreValue: (key: string) => Promise<any>
  // biome-ignore lint/suspicious/noExplicitAny: Value can be any type
  setStoreValue: (key: string, value: any) => Promise<void>

  // Updater
  checkForUpdates: () => Promise<void>
  downloadUpdate: () => Promise<void>
  quitAndInstall: () => Promise<void>
  // biome-ignore lint/suspicious/noExplicitAny: Event callback types
  onUpdateAvailable: (callback: (info: any) => void) => void
  // biome-ignore lint/suspicious/noExplicitAny: Event callback types
  onUpdateNotAvailable: (callback: (info: any) => void) => void
  // biome-ignore lint/suspicious/noExplicitAny: Event callback types
  onUpdateDownloaded: (callback: (info: any) => void) => void
  // biome-ignore lint/suspicious/noExplicitAny: Event callback types
  onDownloadProgress: (callback: (progress: any) => void) => void
  onUpdateError: (callback: (error: string) => void) => void

  // Context Menu
  showContextMenu: (request: ShowContextMenuRequest) => Promise<Result<void>>
  onMenuRefresh: (callback: () => void) => void
  onMenuGoUp: (callback: () => void) => void
}
