import { ExifPanel } from '@renderer/components/exif/ExifPanel'
import { useAppStore } from '@renderer/stores/appStore'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Create a test QueryClient
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  })

// Wrapper component for React Query
const createWrapper = () => {
  const testQueryClient = createTestQueryClient()
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={testQueryClient}>{children}</QueryClientProvider>
  )
}

describe('ExifPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useAppStore.setState({
      panelVisibility: {
        fileBrowser: true,
        thumbnailGrid: true,
        exifPanel: true,
        imagePreview: true,
        mapView: true,
      },
    })
  })

  describe('Empty State', () => {
    it('should display message when filePath is null', () => {
      render(<ExifPanel filePath={null} />, { wrapper: createWrapper() })

      expect(screen.getByText('EXIF Information')).toBeInTheDocument()
      expect(screen.getByText('Select an image to view EXIF data')).toBeInTheDocument()
    })

    it('should not show loading state when filePath is null', () => {
      const { container } = render(<ExifPanel filePath={null} />, { wrapper: createWrapper() })

      const spinner = container.querySelector('.animate-spin')
      expect(spinner).not.toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    it('should display loading spinner while fetching EXIF data', async () => {
      // Mock readExif to return a pending promise
      const pendingPromise = new Promise(() => {})
      vi.mocked(window.api.readExif).mockReturnValue(pendingPromise as any)

      const { container } = render(<ExifPanel filePath="/photos/test.jpg" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        const spinner = container.querySelector('.animate-spin')
        expect(spinner).toBeInTheDocument()
      })
    })
  })

  describe('No EXIF Data', () => {
    it('should display message when EXIF data is not available', async () => {
      vi.mocked(window.api.readExif).mockResolvedValue({
        success: true,
        data: { exif: null },
      } as any)

      render(<ExifPanel filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('No EXIF data available')).toBeInTheDocument()
      })
    })
  })

  describe('EXIF Data Display', () => {
    const mockExifData = {
      camera: {
        make: 'Canon',
        model: 'EOS R5',
        lens: 'RF 24-105mm F4 L IS USM',
      },
      exposure: {
        iso: 100,
        aperture: 4.0,
        shutterSpeed: '1/125',
        focalLength: 50,
      },
      gps: {
        latitude: 35.6762,
        longitude: 139.6503,
        altitude: 40.5,
      },
      timestamp: '2024-01-15T10:30:00Z',
      width: 8192,
      height: 5464,
    }

    beforeEach(() => {
      vi.mocked(window.api.readExif).mockResolvedValue({
        success: true,
        data: { exif: mockExifData },
      } as any)
    })

    it('should display camera information when available', async () => {
      render(<ExifPanel filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('Camera')).toBeInTheDocument()
        expect(screen.getByText('Canon')).toBeInTheDocument()
        expect(screen.getByText('EOS R5')).toBeInTheDocument()
        expect(screen.getByText('RF 24-105mm F4 L IS USM')).toBeInTheDocument()
      })
    })

    it('should display exposure settings when available', async () => {
      render(<ExifPanel filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('Exposure')).toBeInTheDocument()
        expect(screen.getByText('100')).toBeInTheDocument() // ISO
        expect(screen.getByText('f/4')).toBeInTheDocument() // Aperture
        expect(screen.getByText('1/125')).toBeInTheDocument() // Shutter speed
        expect(screen.getByText('50mm')).toBeInTheDocument() // Focal length
      })
    })

    it('should display GPS location when available', async () => {
      render(<ExifPanel filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('Location')).toBeInTheDocument()
        expect(screen.getByText('35.676200')).toBeInTheDocument() // Latitude
        expect(screen.getByText('139.650300')).toBeInTheDocument() // Longitude
        expect(screen.getByText('40.5m')).toBeInTheDocument() // Altitude
      })
    })

    it('should display image dimensions when available', async () => {
      render(<ExifPanel filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('8192 × 5464')).toBeInTheDocument()
      })
    })

    it('should display date taken when timestamp is available', async () => {
      render(<ExifPanel filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('Date Taken')).toBeInTheDocument()
        // The date will be formatted based on locale, so we just check it exists
        const dateElement = screen.getByText(/2024|Jan|15/)
        expect(dateElement).toBeInTheDocument()
      })
    })
  })

  describe('Partial EXIF Data', () => {
    it('should display only camera info when other data is missing', async () => {
      vi.mocked(window.api.readExif).mockResolvedValue({
        success: true,
        data: {
          exif: {
            camera: {
              make: 'Sony',
              model: 'A7 III',
            },
          },
        },
      } as any)

      render(<ExifPanel filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('Camera')).toBeInTheDocument()
        expect(screen.getByText('Sony')).toBeInTheDocument()
        expect(screen.getByText('A7 III')).toBeInTheDocument()

        // Should not show sections without data
        expect(screen.queryByText('Exposure')).not.toBeInTheDocument()
        expect(screen.queryByText('Location')).not.toBeInTheDocument()
      })
    })

    it('should display only GPS info when other data is missing', async () => {
      vi.mocked(window.api.readExif).mockResolvedValue({
        success: true,
        data: {
          exif: {
            gps: {
              latitude: 40.7128,
              longitude: -74.006,
            },
          },
        },
      } as any)

      render(<ExifPanel filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('Location')).toBeInTheDocument()
        expect(screen.getByText('40.712800')).toBeInTheDocument()
        expect(screen.getByText('-74.006000')).toBeInTheDocument()

        // Should not show altitude when not available
        expect(screen.queryByText(/Altitude/)).not.toBeInTheDocument()

        // Should not show sections without data
        expect(screen.queryByText('Camera')).not.toBeInTheDocument()
        expect(screen.queryByText('Exposure')).not.toBeInTheDocument()
      })
    })

    it('should handle missing lens information in camera data', async () => {
      vi.mocked(window.api.readExif).mockResolvedValue({
        success: true,
        data: {
          exif: {
            camera: {
              make: 'Nikon',
              model: 'Z6',
              // lens is missing
            },
          },
        },
      } as any)

      render(<ExifPanel filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('Nikon')).toBeInTheDocument()
        expect(screen.getByText('Z6')).toBeInTheDocument()
        expect(screen.queryByText('Lens')).not.toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('should display error message when EXIF read fails', async () => {
      const error = new Error('Failed to read EXIF data')
      vi.mocked(window.api.readExif).mockRejectedValue(error)

      render(<ExifPanel filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText(/Error loading EXIF data/i)).toBeInTheDocument()
        expect(screen.getByText(/Failed to read EXIF data/i)).toBeInTheDocument()
      })
    })

    it('should display error when API returns unsuccessful result', async () => {
      vi.mocked(window.api.readExif).mockResolvedValue({
        success: false,
        error: { message: 'File not found' },
      } as any)

      render(<ExifPanel filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      await waitFor(() => {
        // When success is false but no error is thrown, should show no data
        expect(screen.getByText('No EXIF data available')).toBeInTheDocument()
      })
    })
  })

  describe('File Path Changes', () => {
    it('should refetch EXIF data when filePath changes', async () => {
      const mockExif1 = {
        camera: { make: 'Canon', model: 'EOS R5' },
      }
      const mockExif2 = {
        camera: { make: 'Sony', model: 'A7 III' },
      }

      vi.mocked(window.api.readExif)
        .mockResolvedValueOnce({
          success: true,
          data: { exif: mockExif1 },
        } as any)
        .mockResolvedValueOnce({
          success: true,
          data: { exif: mockExif2 },
        } as any)

      const { rerender } = render(<ExifPanel filePath="/photos/photo1.jpg" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByText('Canon')).toBeInTheDocument()
        expect(screen.getByText('EOS R5')).toBeInTheDocument()
      })

      rerender(<ExifPanel filePath="/photos/photo2.jpg" />)

      await waitFor(() => {
        expect(screen.getByText('Sony')).toBeInTheDocument()
        expect(screen.getByText('A7 III')).toBeInTheDocument()
        expect(screen.queryByText('Canon')).not.toBeInTheDocument()
      })
    })
  })
})
