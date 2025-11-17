import type {
  GenerateThumbnailRequest,
  GenerateThumbnailResponse,
  ReadExifRequest,
  ReadExifResponse,
  Result,
  RotateImageRequest,
  RotateImageResponse,
} from '@/types/ipc'
import {
  ExifDataSchema,
  GenerateThumbnailRequestSchema,
  ReadExifRequestSchema,
  RotateImageRequestSchema,
  failure,
  success,
} from '@/types/ipc'
import ExifReader from 'exifreader'
import sharp from 'sharp'

/**
 * Generate a thumbnail for an image using sharp
 */
export async function generateThumbnail(
  request: GenerateThumbnailRequest
): Promise<Result<GenerateThumbnailResponse>> {
  try {
    const validated = GenerateThumbnailRequestSchema.parse(request)

    // Generate thumbnail using sharp
    const buffer = await sharp(validated.path)
      .resize(validated.width, validated.height, {
        fit: 'cover',
        position: 'center',
      })
      .jpeg({ quality: 80 })
      .toBuffer()

    // Convert to base64
    const thumbnail = buffer.toString('base64')

    // Get actual dimensions
    const metadata = await sharp(buffer).metadata()

    return success({
      path: validated.path,
      thumbnail: `data:image/jpeg;base64,${thumbnail}`,
      width: metadata.width || validated.width,
      height: metadata.height || validated.height,
    })
  } catch (error) {
    return failure(error instanceof Error ? error : new Error(String(error)))
  }
}

/**
 * Read EXIF data from an image file
 */
export async function readExif(request: ReadExifRequest): Promise<Result<ReadExifResponse>> {
  try {
    const validated = ReadExifRequestSchema.parse(request)

    // Read EXIF data using exifreader
    const tags = await ExifReader.load(validated.path)

    // Helper function to safely convert tag values to numbers
    const toNumber = (value: unknown): number | undefined => {
      if (typeof value === 'number') return value
      if (typeof value === 'string') {
        const parsed = Number.parseFloat(value)
        return Number.isNaN(parsed) ? undefined : parsed
      }
      return undefined
    }

    // Helper to extract GPS coordinates
    const getGPSCoordinate = (coordinate: unknown): number | undefined => {
      if (typeof coordinate === 'number') return coordinate
      if (typeof coordinate === 'object' && coordinate !== null && 'description' in coordinate) {
        const desc = (coordinate as { description?: unknown }).description
        if (typeof desc === 'number') return desc
      }
      return undefined
    }

    // Extract GPS data if available
    const latitude = getGPSCoordinate(tags.GPSLatitude)
    const longitude = getGPSCoordinate(tags.GPSLongitude)
    const hasGPS = latitude !== undefined && longitude !== undefined

    // Extract relevant EXIF data
    const exifData = {
      camera: {
        make: tags.Make?.description,
        model: tags.Model?.description,
        lens: tags.LensModel?.description,
      },
      exposure: {
        iso: toNumber(tags.ISOSpeedRatings?.value),
        aperture: toNumber(tags.FNumber?.value),
        shutterSpeed: tags.ExposureTime?.description,
        focalLength: toNumber(tags.FocalLength?.value),
      },
      gps:
        hasGPS && latitude !== undefined && longitude !== undefined
          ? {
              latitude,
              longitude,
              altitude: toNumber(tags.GPSAltitude?.value),
            }
          : undefined,
      timestamp: tags.DateTimeOriginal?.value
        ? new Date(
            String(tags.DateTimeOriginal.value).replace(/^(\d{4}):(\d{2}):(\d{2})/, '$1-$2-$3')
          ).getTime()
        : undefined,
      width: toNumber(tags['Image Width']?.value) || toNumber(tags.PixelXDimension?.value),
      height: toNumber(tags['Image Height']?.value) || toNumber(tags.PixelYDimension?.value),
    }

    // Validate the extracted data
    const validatedExif = ExifDataSchema.parse(exifData)

    return success({
      path: validated.path,
      exif: validatedExif,
    })
  } catch (error) {
    return failure(error instanceof Error ? error : new Error(String(error)))
  }
}

/**
 * Rotate an image by the specified angle (90, 180, 270, or -90 degrees)
 * This overwrites the original file with the rotated version
 * EXIF orientation is automatically handled by sharp - it will read the orientation,
 * apply the rotation, and reset the orientation tag to 1 (normal)
 */
export async function rotateImage(
  request: RotateImageRequest
): Promise<Result<RotateImageResponse>> {
  try {
    const validated = RotateImageRequestSchema.parse(request)

    // Read the image, apply EXIF orientation, then rotate
    // withMetadata() preserves EXIF data but updates orientation tag to 1
    await sharp(validated.path)
      .rotate(validated.angle)
      .withMetadata()
      .toFile(`${validated.path}.tmp`)

    // Replace the original file with the rotated version
    const fs = await import('node:fs/promises')
    await fs.rename(`${validated.path}.tmp`, validated.path)

    return success({
      path: validated.path,
      success: true,
    })
  } catch (error) {
    // Clean up temporary file if it exists
    try {
      const fs = await import('node:fs/promises')
      await fs.unlink(`${request.path}.tmp`)
    } catch {
      // Ignore cleanup errors
    }

    return failure(error instanceof Error ? error : new Error(String(error)))
  }
}
