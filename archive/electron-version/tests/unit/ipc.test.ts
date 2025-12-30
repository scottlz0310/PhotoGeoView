import { describe, expect, it } from 'vitest'
import {
  ExifDataSchema,
  FileEntrySchema,
  failure,
  GenerateThumbnailRequestSchema,
  GenerateThumbnailResponseSchema,
  GetDirectoryContentsRequestSchema,
  GetDirectoryContentsResponseSchema,
  GetFileInfoRequestSchema,
  ReadExifRequestSchema,
  ReadExifResponseSchema,
  ReadImageMetadataRequestSchema,
  ReadImageMetadataResponseSchema,
  RotateImageRequestSchema,
  RotateImageResponseSchema,
  success,
} from '@/types/ipc'

describe('IPC Type Validation', () => {
  describe('FileEntrySchema', () => {
    it('should validate a complete file entry', () => {
      const validEntry = {
        name: 'photo.jpg',
        path: '/path/to/photo.jpg',
        isDirectory: false,
        size: 1024000,
        modifiedTime: 1640995200000,
        extension: '.jpg',
        isImage: true,
      }

      const result = FileEntrySchema.safeParse(validEntry)
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data).toEqual(validEntry)
      }
    })

    it('should validate a minimal file entry', () => {
      const minimalEntry = {
        name: 'file.txt',
        path: '/path/to/file.txt',
        isDirectory: false,
        size: 500,
        modifiedTime: 1640995200000,
      }

      const result = FileEntrySchema.safeParse(minimalEntry)
      expect(result.success).toBe(true)
    })

    it('should reject missing required fields', () => {
      const invalidEntry = {
        name: 'file.txt',
        path: '/path/to/file.txt',
        // Missing isDirectory, size, modifiedTime
      }

      const result = FileEntrySchema.safeParse(invalidEntry)
      expect(result.success).toBe(false)
    })

    it('should reject invalid field types', () => {
      const invalidEntry = {
        name: 'file.txt',
        path: '/path/to/file.txt',
        isDirectory: 'not a boolean',
        size: '1000',
        modifiedTime: 1640995200000,
      }

      const result = FileEntrySchema.safeParse(invalidEntry)
      expect(result.success).toBe(false)
    })
  })

  describe('GetDirectoryContentsRequestSchema', () => {
    it('should validate a complete request', () => {
      const request = {
        path: '/path/to/directory',
        includeHidden: true,
        imageOnly: true,
      }

      const result = GetDirectoryContentsRequestSchema.safeParse(request)
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data).toEqual(request)
      }
    })

    it('should apply default values for optional fields', () => {
      const request = {
        path: '/path/to/directory',
      }

      const result = GetDirectoryContentsRequestSchema.safeParse(request)
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data.includeHidden).toBe(false)
        expect(result.data.imageOnly).toBe(false)
      }
    })

    it('should reject missing path', () => {
      const request = {
        includeHidden: true,
      }

      const result = GetDirectoryContentsRequestSchema.safeParse(request)
      expect(result.success).toBe(false)
    })
  })

  describe('GetDirectoryContentsResponseSchema', () => {
    it('should validate a valid response', () => {
      const response = {
        path: '/path/to/directory',
        entries: [
          {
            name: 'photo.jpg',
            path: '/path/to/directory/photo.jpg',
            isDirectory: false,
            size: 1024000,
            modifiedTime: 1640995200000,
            extension: '.jpg',
            isImage: true,
          },
        ],
      }

      const result = GetDirectoryContentsResponseSchema.safeParse(response)
      expect(result.success).toBe(true)
    })

    it('should validate an empty entries array', () => {
      const response = {
        path: '/path/to/empty',
        entries: [],
      }

      const result = GetDirectoryContentsResponseSchema.safeParse(response)
      expect(result.success).toBe(true)
    })

    it('should reject invalid entries', () => {
      const response = {
        path: '/path/to/directory',
        entries: [{ name: 'invalid' }],
      }

      const result = GetDirectoryContentsResponseSchema.safeParse(response)
      expect(result.success).toBe(false)
    })
  })

  describe('GetFileInfoRequestSchema', () => {
    it('should validate a valid request', () => {
      const request = { path: '/path/to/file.jpg' }

      const result = GetFileInfoRequestSchema.safeParse(request)
      expect(result.success).toBe(true)
    })

    it('should reject missing path', () => {
      const request = {}

      const result = GetFileInfoRequestSchema.safeParse(request)
      expect(result.success).toBe(false)
    })
  })

  describe('ExifDataSchema', () => {
    it('should validate complete EXIF data', () => {
      const exifData = {
        camera: {
          make: 'Canon',
          model: 'EOS 5D Mark IV',
          lens: 'EF 24-70mm f/2.8L II USM',
        },
        exposure: {
          iso: 800,
          aperture: 2.8,
          shutterSpeed: '1/250',
          focalLength: 50,
        },
        gps: {
          latitude: 35.6762,
          longitude: 139.6503,
          altitude: 40,
        },
        timestamp: 1640995200000,
        width: 6720,
        height: 4480,
      }

      const result = ExifDataSchema.safeParse(exifData)
      expect(result.success).toBe(true)
    })

    it('should validate minimal EXIF data', () => {
      const minimalExif = {}

      const result = ExifDataSchema.safeParse(minimalExif)
      expect(result.success).toBe(true)
    })

    it('should validate GPS data without altitude', () => {
      const exifData = {
        gps: {
          latitude: 35.6762,
          longitude: 139.6503,
        },
      }

      const result = ExifDataSchema.safeParse(exifData)
      expect(result.success).toBe(true)
    })

    it('should reject GPS data without required latitude', () => {
      const exifData = {
        gps: {
          longitude: 139.6503,
        },
      }

      const result = ExifDataSchema.safeParse(exifData)
      expect(result.success).toBe(false)
    })

    it('should reject GPS data without required longitude', () => {
      const exifData = {
        gps: {
          latitude: 35.6762,
        },
      }

      const result = ExifDataSchema.safeParse(exifData)
      expect(result.success).toBe(false)
    })

    it('should validate partial camera data', () => {
      const exifData = {
        camera: {
          make: 'Canon',
        },
      }

      const result = ExifDataSchema.safeParse(exifData)
      expect(result.success).toBe(true)
    })

    it('should validate partial exposure data', () => {
      const exifData = {
        exposure: {
          iso: 800,
          aperture: 2.8,
        },
      }

      const result = ExifDataSchema.safeParse(exifData)
      expect(result.success).toBe(true)
    })
  })

  describe('ReadImageMetadataRequestSchema', () => {
    it('should validate a valid request', () => {
      const request = { path: '/path/to/image.jpg' }

      const result = ReadImageMetadataRequestSchema.safeParse(request)
      expect(result.success).toBe(true)
    })

    it('should reject missing path', () => {
      const request = {}

      const result = ReadImageMetadataRequestSchema.safeParse(request)
      expect(result.success).toBe(false)
    })
  })

  describe('ReadImageMetadataResponseSchema', () => {
    it('should validate response with EXIF data', () => {
      const response = {
        path: '/path/to/image.jpg',
        exif: {
          camera: {
            make: 'Canon',
            model: 'EOS 5D',
          },
        },
      }

      const result = ReadImageMetadataResponseSchema.safeParse(response)
      expect(result.success).toBe(true)
    })

    it('should validate response without EXIF data', () => {
      const response = {
        path: '/path/to/image.jpg',
      }

      const result = ReadImageMetadataResponseSchema.safeParse(response)
      expect(result.success).toBe(true)
    })
  })

  describe('GenerateThumbnailRequestSchema', () => {
    it('should validate a complete request', () => {
      const request = {
        path: '/path/to/image.jpg',
        width: 300,
        height: 300,
      }

      const result = GenerateThumbnailRequestSchema.safeParse(request)
      expect(result.success).toBe(true)
    })

    it('should apply default width and height', () => {
      const request = {
        path: '/path/to/image.jpg',
      }

      const result = GenerateThumbnailRequestSchema.safeParse(request)
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data.width).toBe(200)
        expect(result.data.height).toBe(200)
      }
    })

    it('should reject missing path', () => {
      const request = {
        width: 300,
      }

      const result = GenerateThumbnailRequestSchema.safeParse(request)
      expect(result.success).toBe(false)
    })
  })

  describe('GenerateThumbnailResponseSchema', () => {
    it('should validate a valid response', () => {
      const response = {
        path: '/path/to/image.jpg',
        thumbnail: 'base64encodedstring==',
        width: 200,
        height: 200,
      }

      const result = GenerateThumbnailResponseSchema.safeParse(response)
      expect(result.success).toBe(true)
    })

    it('should reject missing required fields', () => {
      const response = {
        path: '/path/to/image.jpg',
        thumbnail: 'base64encodedstring==',
      }

      const result = GenerateThumbnailResponseSchema.safeParse(response)
      expect(result.success).toBe(false)
    })
  })

  describe('ReadExifRequestSchema', () => {
    it('should validate a valid request', () => {
      const request = { path: '/path/to/image.jpg' }

      const result = ReadExifRequestSchema.safeParse(request)
      expect(result.success).toBe(true)
    })

    it('should reject missing path', () => {
      const request = {}

      const result = ReadExifRequestSchema.safeParse(request)
      expect(result.success).toBe(false)
    })
  })

  describe('ReadExifResponseSchema', () => {
    it('should validate a valid response', () => {
      const response = {
        path: '/path/to/image.jpg',
        exif: {
          camera: {
            make: 'Canon',
          },
        },
      }

      const result = ReadExifResponseSchema.safeParse(response)
      expect(result.success).toBe(true)
    })

    it('should reject missing required exif field', () => {
      const response = {
        path: '/path/to/image.jpg',
      }

      const result = ReadExifResponseSchema.safeParse(response)
      expect(result.success).toBe(false)
    })
  })

  describe('RotateImageRequestSchema', () => {
    it('should validate valid rotation angles', () => {
      const validAngles = [90, 180, 270, -90]

      for (const angle of validAngles) {
        const request = {
          path: '/path/to/image.jpg',
          angle,
        }

        const result = RotateImageRequestSchema.safeParse(request)
        expect(result.success).toBe(true)
      }
    })

    it('should reject invalid rotation angles', () => {
      const invalidAngles = [0, 45, 135, 360, -180]

      for (const angle of invalidAngles) {
        const request = {
          path: '/path/to/image.jpg',
          angle,
        }

        const result = RotateImageRequestSchema.safeParse(request)
        expect(result.success).toBe(false)
      }
    })

    it('should reject missing path', () => {
      const request = {
        angle: 90,
      }

      const result = RotateImageRequestSchema.safeParse(request)
      expect(result.success).toBe(false)
    })

    it('should reject missing angle', () => {
      const request = {
        path: '/path/to/image.jpg',
      }

      const result = RotateImageRequestSchema.safeParse(request)
      expect(result.success).toBe(false)
    })
  })

  describe('RotateImageResponseSchema', () => {
    it('should validate a valid response', () => {
      const response = {
        path: '/path/to/image.jpg',
        success: true,
      }

      const result = RotateImageResponseSchema.safeParse(response)
      expect(result.success).toBe(true)
    })

    it('should validate a failure response', () => {
      const response = {
        path: '/path/to/image.jpg',
        success: false,
      }

      const result = RotateImageResponseSchema.safeParse(response)
      expect(result.success).toBe(true)
    })
  })

  describe('Result Helper Functions', () => {
    it('should create a successful result', () => {
      const data = { value: 'test' }
      const result = success(data)

      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data).toEqual(data)
      }
    })

    it('should create a failure result', () => {
      const error = new Error('Test error')
      const result = failure(error)

      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error).toBe(error)
      }
    })

    it('should create a failure result with custom error type', () => {
      const customError = { code: 'ERR_001', message: 'Custom error' }
      const result = failure(customError)

      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error).toEqual(customError)
      }
    })

    it('should type-guard successful results', () => {
      const result = success({ value: 42 })

      if (result.success) {
        // TypeScript should know result.data exists
        expect(result.data.value).toBe(42)
        // @ts-expect-error error should not exist on success
        expect(result.error).toBeUndefined()
      }
    })

    it('should type-guard failure results', () => {
      const result = failure(new Error('fail'))

      if (!result.success) {
        // TypeScript should know result.error exists
        expect(result.error).toBeInstanceOf(Error)
        // @ts-expect-error data should not exist on failure
        expect(result.data).toBeUndefined()
      }
    })
  })
})
