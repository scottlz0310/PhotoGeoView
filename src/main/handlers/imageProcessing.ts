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

    // Read EXIF data using exifreader
    const tags = await ExifReader.load(validated.path, { expanded: true })

    // Extract relevant EXIF data
    const exifData: ReadExifResponse['exif'] = {
      camera: {
        make: tags.exif?.Make?.description,
        model: tags.exif?.Model?.description,
        lens: tags.exif?.LensModel?.description,
      },
      exposure: {
        iso: Array.isArray(tags.exif?.ISOSpeedRatings?.value)
          ? tags.exif?.ISOSpeedRatings?.value[0]
          : tags.exif?.ISOSpeedRatings?.value,
        aperture: Array.isArray(tags.exif?.FNumber?.value)
          ? tags.exif?.FNumber?.value[0]
          : tags.exif?.FNumber?.value,
        shutterSpeed: tags.exif?.ExposureTime?.description,
        focalLength: Array.isArray(tags.exif?.FocalLength?.value)
          ? tags.exif?.FocalLength?.value[0]
          : tags.exif?.FocalLength?.value,
      },
      gps:
        tags.gps?.Latitude !== undefined && tags.gps?.Longitude !== undefined
          ? {
              latitude: tags.gps.Latitude,
              longitude: tags.gps.Longitude,
              altitude: tags.gps.Altitude,
            }
          : undefined,
      timestamp: tags.exif?.DateTimeOriginal?.description
        ? new Date(tags.exif.DateTimeOriginal.description).getTime()
        : undefined,
      width: tags.file?.['Image Width']?.value,
      height: tags.file?.['Image Height']?.value,
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
