import type { FileEntry } from '@/types/ipc'
import { useFileFilters, useUniqueCameraModels } from '@renderer/hooks/useFileFilters'
import type { FileFilters } from '@renderer/stores/appStore'
import { renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('useFileFilters', () => {
  const mockFiles: FileEntry[] = [
    {
      name: 'photo1.jpg',
      path: '/photos/photo1.jpg',
      isDirectory: false,
      size: 1024000,
      modifiedTime: new Date('2024-01-15').getTime(),
      extension: '.jpg',
      isImage: true,
    },
    {
      name: 'photo2.jpg',
      path: '/photos/photo2.jpg',
      isDirectory: false,
      size: 2048000,
      modifiedTime: new Date('2024-02-15').getTime(),
      extension: '.jpg',
      isImage: true,
    },
    {
      name: 'photo3.jpg',
      path: '/photos/photo3.jpg',
      isDirectory: false,
      size: 1536000,
      modifiedTime: new Date('2024-03-15').getTime(),
      extension: '.jpg',
      isImage: true,
    },
  ]

  const mockExifDataMap = new Map([
    [
      '/photos/photo1.jpg',
      {
        camera: { make: 'Canon', model: 'EOS 5D Mark IV' },
        gps: { latitude: 35.6762, longitude: 139.6503 },
      },
    ],
    [
      '/photos/photo2.jpg',
      {
        camera: { make: 'Nikon', model: 'D850' },
        gps: { latitude: 40.7128, longitude: -74.006 },
      },
    ],
    [
      '/photos/photo3.jpg',
      {
        camera: { make: 'Sony', model: 'A7R IV' },
        // No GPS data
      },
    ],
  ])

  describe('applyFilters', () => {
    it('should return all files when no filters are applied', () => {
      const { result } = renderHook(() => useFileFilters())
      const filters: FileFilters = {
        dateFrom: null,
        dateTo: null,
        hasGPS: null,
        cameraModels: [],
      }

      const filtered = result.current.applyFilters(mockFiles, filters, mockExifDataMap)
      expect(filtered).toHaveLength(3)
      expect(filtered).toEqual(mockFiles)
    })

    describe('Date Range Filter', () => {
      it('should filter files by dateFrom', () => {
        const { result } = renderHook(() => useFileFilters())
        const filters: FileFilters = {
          dateFrom: new Date('2024-02-01'),
          dateTo: null,
          hasGPS: null,
          cameraModels: [],
        }

        const filtered = result.current.applyFilters(mockFiles, filters, mockExifDataMap)
        expect(filtered).toHaveLength(2)
        expect(filtered.map((f) => f.name)).toEqual(['photo2.jpg', 'photo3.jpg'])
      })

      it('should filter files by dateTo', () => {
        const { result } = renderHook(() => useFileFilters())
        const filters: FileFilters = {
          dateFrom: null,
          dateTo: new Date('2024-02-01'),
          hasGPS: null,
          cameraModels: [],
        }

        const filtered = result.current.applyFilters(mockFiles, filters, mockExifDataMap)
        expect(filtered).toHaveLength(1)
        expect(filtered.map((f) => f.name)).toEqual(['photo1.jpg'])
      })

      it('should filter files by date range', () => {
        const { result } = renderHook(() => useFileFilters())
        const filters: FileFilters = {
          dateFrom: new Date('2024-02-01'),
          dateTo: new Date('2024-02-28'),
          hasGPS: null,
          cameraModels: [],
        }

        const filtered = result.current.applyFilters(mockFiles, filters, mockExifDataMap)
        expect(filtered).toHaveLength(1)
        expect(filtered.map((f) => f.name)).toEqual(['photo2.jpg'])
      })

      it('should exclude files without date when date filter is set', () => {
        const filesWithoutDate: FileEntry[] = [
          ...mockFiles,
          {
            name: 'no-date.jpg',
            path: '/photos/no-date.jpg',
            isDirectory: false,
            size: 1000,
            modifiedTime: 0,
            extension: '.jpg',
            isImage: true,
          },
        ]

        const { result } = renderHook(() => useFileFilters())
        const filters: FileFilters = {
          dateFrom: new Date('2024-01-01'),
          dateTo: null,
          hasGPS: null,
          cameraModels: [],
        }

        const filtered = result.current.applyFilters(filesWithoutDate, filters, mockExifDataMap)
        expect(filtered).toHaveLength(3)
        expect(filtered.every((f) => f.modifiedTime > 0)).toBe(true)
      })
    })

    describe('GPS Filter', () => {
      it('should filter files with GPS data', () => {
        const { result } = renderHook(() => useFileFilters())
        const filters: FileFilters = {
          dateFrom: null,
          dateTo: null,
          hasGPS: true,
          cameraModels: [],
        }

        const filtered = result.current.applyFilters(mockFiles, filters, mockExifDataMap)
        expect(filtered).toHaveLength(2)
        expect(filtered.map((f) => f.name)).toEqual(['photo1.jpg', 'photo2.jpg'])
      })

      it('should filter files without GPS data', () => {
        const { result } = renderHook(() => useFileFilters())
        const filters: FileFilters = {
          dateFrom: null,
          dateTo: null,
          hasGPS: false,
          cameraModels: [],
        }

        const filtered = result.current.applyFilters(mockFiles, filters, mockExifDataMap)
        expect(filtered).toHaveLength(1)
        expect(filtered.map((f) => f.name)).toEqual(['photo3.jpg'])
      })

      it('should return all files when hasGPS is null', () => {
        const { result } = renderHook(() => useFileFilters())
        const filters: FileFilters = {
          dateFrom: null,
          dateTo: null,
          hasGPS: null,
          cameraModels: [],
        }

        const filtered = result.current.applyFilters(mockFiles, filters, mockExifDataMap)
        expect(filtered).toHaveLength(3)
      })
    })

    describe('Camera Model Filter', () => {
      it('should filter by single camera model', () => {
        const { result } = renderHook(() => useFileFilters())
        const filters: FileFilters = {
          dateFrom: null,
          dateTo: null,
          hasGPS: null,
          cameraModels: ['EOS 5D Mark IV'],
        }

        const filtered = result.current.applyFilters(mockFiles, filters, mockExifDataMap)
        expect(filtered).toHaveLength(1)
        expect(filtered.map((f) => f.name)).toEqual(['photo1.jpg'])
      })

      it('should filter by multiple camera models', () => {
        const { result } = renderHook(() => useFileFilters())
        const filters: FileFilters = {
          dateFrom: null,
          dateTo: null,
          hasGPS: null,
          cameraModels: ['EOS 5D Mark IV', 'D850'],
        }

        const filtered = result.current.applyFilters(mockFiles, filters, mockExifDataMap)
        expect(filtered).toHaveLength(2)
        expect(filtered.map((f) => f.name)).toEqual(['photo1.jpg', 'photo2.jpg'])
      })

      it('should filter by camera make when model is not available', () => {
        const exifWithMakeOnly = new Map([['/photos/photo1.jpg', { camera: { make: 'Canon' } }]])

        const { result } = renderHook(() => useFileFilters())
        const filters: FileFilters = {
          dateFrom: null,
          dateTo: null,
          hasGPS: null,
          cameraModels: ['Canon'],
        }

        const filtered = result.current.applyFilters(mockFiles, filters, exifWithMakeOnly)
        expect(filtered).toHaveLength(1)
        expect(filtered.map((f) => f.name)).toEqual(['photo1.jpg'])
      })

      it('should exclude files without camera data when camera filter is set', () => {
        const { result } = renderHook(() => useFileFilters())
        const filters: FileFilters = {
          dateFrom: null,
          dateTo: null,
          hasGPS: null,
          cameraModels: ['NonExistent Camera'],
        }

        const filtered = result.current.applyFilters(mockFiles, filters, mockExifDataMap)
        expect(filtered).toHaveLength(0)
      })
    })

    describe('Combined Filters', () => {
      it('should apply multiple filters together', () => {
        const { result } = renderHook(() => useFileFilters())
        const filters: FileFilters = {
          dateFrom: new Date('2024-01-01'),
          dateTo: new Date('2024-02-28'),
          hasGPS: true,
          cameraModels: ['EOS 5D Mark IV', 'D850'],
        }

        const filtered = result.current.applyFilters(mockFiles, filters, mockExifDataMap)
        expect(filtered).toHaveLength(2)
        expect(filtered.map((f) => f.name)).toEqual(['photo1.jpg', 'photo2.jpg'])
      })

      it('should return empty array when no files match all criteria', () => {
        const { result } = renderHook(() => useFileFilters())
        const filters: FileFilters = {
          dateFrom: new Date('2024-01-01'),
          dateTo: new Date('2024-01-31'),
          hasGPS: false,
          cameraModels: [],
        }

        const filtered = result.current.applyFilters(mockFiles, filters, mockExifDataMap)
        expect(filtered).toHaveLength(0)
      })
    })
  })
})

describe('useUniqueCameraModels', () => {
  it('should extract unique camera models from EXIF data', () => {
    const exifDataMap = new Map([
      ['/photo1.jpg', { camera: { make: 'Canon', model: 'EOS 5D Mark IV' } }],
      ['/photo2.jpg', { camera: { make: 'Canon', model: 'EOS 5D Mark IV' } }], // Duplicate
      ['/photo3.jpg', { camera: { make: 'Nikon', model: 'D850' } }],
      ['/photo4.jpg', { camera: { make: 'Sony', model: 'A7R IV' } }],
    ])

    const { result } = renderHook(() => useUniqueCameraModels(exifDataMap))

    expect(result.current).toHaveLength(3)
    expect(result.current).toEqual(['A7R IV', 'D850', 'EOS 5D Mark IV'])
  })

  it('should use make when model is not available', () => {
    const exifDataMap = new Map([
      ['/photo1.jpg', { camera: { make: 'Canon' } }],
      ['/photo2.jpg', { camera: { make: 'Nikon', model: 'D850' } }],
    ])

    const { result } = renderHook(() => useUniqueCameraModels(exifDataMap))

    expect(result.current).toHaveLength(2)
    expect(result.current).toEqual(['Canon', 'D850'])
  })

  it('should return empty array when no camera data exists', () => {
    const exifDataMap = new Map([['/photo1.jpg', {}]])

    const { result } = renderHook(() => useUniqueCameraModels(exifDataMap))

    expect(result.current).toHaveLength(0)
    expect(result.current).toEqual([])
  })

  it('should return sorted camera models', () => {
    const exifDataMap = new Map([
      ['/photo1.jpg', { camera: { model: 'Z' } }],
      ['/photo2.jpg', { camera: { model: 'A' } }],
      ['/photo3.jpg', { camera: { model: 'M' } }],
    ])

    const { result } = renderHook(() => useUniqueCameraModels(exifDataMap))

    expect(result.current).toEqual(['A', 'M', 'Z'])
  })

  it('should handle empty map', () => {
    const exifDataMap = new Map()

    const { result } = renderHook(() => useUniqueCameraModels(exifDataMap))

    expect(result.current).toHaveLength(0)
    expect(result.current).toEqual([])
  })
})
