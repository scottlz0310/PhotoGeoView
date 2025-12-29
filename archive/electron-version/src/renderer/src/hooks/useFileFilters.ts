import type { FileFilters } from '@renderer/stores/appStore'
import { useCallback, useMemo } from 'react'
import type { FileEntry } from '../../../types/ipc'

interface ExifData {
  camera?: {
    make?: string
    model?: string
  }
  gps?: {
    latitude?: number
    longitude?: number
  }
  datetime?: {
    original?: string
  }
}

/**
 * Custom hook for filtering files based on filter criteria
 */
export function useFileFilters() {
  const applyFilters = useCallback(
    (files: FileEntry[], filters: FileFilters, exifDataMap: Map<string, ExifData>): FileEntry[] => {
      return files.filter((file) => {
        const exif = exifDataMap.get(file.path)

        // Date range filter
        if (filters.dateFrom || filters.dateTo) {
          const fileDate = file.modifiedTime ? new Date(file.modifiedTime) : null

          if (fileDate) {
            if (filters.dateFrom && fileDate < filters.dateFrom) {
              return false
            }
            if (filters.dateTo && fileDate > filters.dateTo) {
              return false
            }
          } else if (filters.dateFrom || filters.dateTo) {
            // If date filter is set but file has no date, exclude it
            return false
          }
        }

        // GPS filter
        if (filters.hasGPS !== null) {
          const hasGPSData = !!(exif?.gps?.latitude && exif?.gps?.longitude)
          if (filters.hasGPS !== hasGPSData) {
            return false
          }
        }

        // Camera model filter
        if (filters.cameraModels.length > 0) {
          const cameraModel = exif?.camera?.model || exif?.camera?.make
          if (!cameraModel || !filters.cameraModels.includes(cameraModel)) {
            return false
          }
        }

        return true
      })
    },
    []
  )

  return { applyFilters }
}

/**
 * Extract unique camera models from EXIF data
 */
export function useUniqueCameraModels(exifDataMap: Map<string, ExifData>): string[] {
  return useMemo(() => {
    const models = new Set<string>()

    for (const exif of exifDataMap.values()) {
      const model = exif?.camera?.model || exif?.camera?.make
      if (model) {
        models.add(model)
      }
    }

    return Array.from(models).sort()
  }, [exifDataMap])
}
