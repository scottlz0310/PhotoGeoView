import type {
  GenerateThumbnailRequest,
  GenerateThumbnailResponse,
  ReadExifRequest,
  ReadExifResponse,
  Result,
} from '@/types/ipc'
import {
  ExifDataSchema,
  GenerateThumbnailRequestSchema,
  ReadExifRequestSchema,
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
 * Read EXIF data from an image using exifreader
 */
export async function readExif(request: ReadExifRequest): Promise<Result<ReadExifResponse>> {
  try {
    const validated = ReadExifRequestSchema.parse(request)

    // Read EXIF data using exifreader (without expanded mode for better compatibility)
    const tags = await ExifReader.load(validated.path)

    // Helper function to safely convert to number
    const toNumber = (val: unknown): number | undefined => {
      if (typeof val === 'number') return val
      if (typeof val === 'string') {
        const num = Number.parseFloat(val)
        return Number.isNaN(num) ? undefined : num
      }
      return undefined
    }

    // Extract relevant EXIF data
    const exifData: ReadExifResponse['exif'] = {
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
        tags.GPSLatitude !== undefined && tags.GPSLongitude !== undefined
          ? {
              latitude: toNumber(tags.GPSLatitude.description) || 0,
              longitude: toNumber(tags.GPSLongitude.description) || 0,
              altitude: toNumber(tags.GPSAltitude?.description),
            }
          : undefined,
      timestamp: tags.DateTimeOriginal?.description
        ? new Date(
            String(tags.DateTimeOriginal.description).replace(
              /^(\d{4}):(\d{2}):(\d{2})/,
              '$1-$2-$3'
            )
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
