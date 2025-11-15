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

  // Window
  MINIMIZE_WINDOW: 'window:minimize',
  MAXIMIZE_WINDOW: 'window:maximize',
  CLOSE_WINDOW: 'window:close',
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

  // Window
  minimizeWindow: () => void
  maximizeWindow: () => void
  closeWindow: () => void
}
