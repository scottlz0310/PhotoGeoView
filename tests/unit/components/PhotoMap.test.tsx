import type { ExifData } from '@/types/ipc'
import { PhotoMap } from '@renderer/components/map/PhotoMap'
import { useAppStore } from '@renderer/stores/appStore'
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Mock leaflet and react-leaflet
vi.mock('leaflet', () => ({
  default: {
    Icon: {
      Default: {
        prototype: {},
        mergeOptions: vi.fn(),
      },
    },
  },
}))

vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="map-container">{children}</div>
  ),
  TileLayer: () => <div data-testid="tile-layer" />,
  Marker: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="marker">{children}</div>
  ),
  Popup: ({ children }: { children: React.ReactNode }) => <div data-testid="popup">{children}</div>,
  useMap: () => ({
    setView: vi.fn(),
  }),
}))

describe('PhotoMap', () => {
  const mockExifDataWithGPS: ExifData = {
    camera: {
      make: 'Canon',
      model: 'EOS R5',
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

  const mockExifDataWithoutGPS: ExifData = {
    camera: {
      make: 'Canon',
      model: 'EOS R5',
    },
    timestamp: '2024-01-15T10:30:00Z',
    width: 8192,
    height: 5464,
  }

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

  describe('Empty States', () => {
    it('should display message when filePath is null', () => {
      render(<PhotoMap exifData={null} filePath={null} />)

      expect(screen.getByText('Map')).toBeInTheDocument()
      expect(
        screen.getByText('Select an image to view its location on the map')
      ).toBeInTheDocument()
    })

    it('should display message when GPS data is not available', () => {
      render(<PhotoMap exifData={mockExifDataWithoutGPS} filePath="/photos/test.jpg" />)

      expect(screen.getByText('Map')).toBeInTheDocument()
      expect(screen.getByText('This image does not contain GPS coordinates')).toBeInTheDocument()
    })

    it('should display message when exifData is null', () => {
      render(<PhotoMap exifData={null} filePath="/photos/test.jpg" />)

      expect(screen.getByText('This image does not contain GPS coordinates')).toBeInTheDocument()
    })

    it('should not display map when filePath is null', () => {
      const { container } = render(<PhotoMap exifData={mockExifDataWithGPS} filePath={null} />)

      expect(container.querySelector('[data-testid="map-container"]')).not.toBeInTheDocument()
    })

    it('should not display map when GPS data is missing', () => {
      const { container } = render(
        <PhotoMap exifData={mockExifDataWithoutGPS} filePath="/photos/test.jpg" />
      )

      expect(container.querySelector('[data-testid="map-container"]')).not.toBeInTheDocument()
    })
  })

  describe('GPS Data Display', () => {
    it('should display map title', () => {
      render(<PhotoMap exifData={mockExifDataWithGPS} filePath="/photos/test.jpg" />)

      expect(screen.getByText('Map')).toBeInTheDocument()
    })

    it('should accept exifData with GPS coordinates', () => {
      const { container } = render(
        <PhotoMap exifData={mockExifDataWithGPS} filePath="/photos/test.jpg" />
      )

      // Component should render without errors
      expect(container.querySelector('.h-full')).toBeInTheDocument()
    })

    it('should handle GPS data with altitude', () => {
      const exifWithAltitude: ExifData = {
        ...mockExifDataWithGPS,
        gps: {
          latitude: 35.6762,
          longitude: 139.6503,
          altitude: 100.5,
        },
      }

      render(<PhotoMap exifData={exifWithAltitude} filePath="/photos/test.jpg" />)

      expect(screen.getByText('Map')).toBeInTheDocument()
    })

    it('should handle GPS data without altitude', () => {
      const exifWithoutAltitude: ExifData = {
        ...mockExifDataWithGPS,
        gps: {
          latitude: 35.6762,
          longitude: 139.6503,
        },
      }

      render(<PhotoMap exifData={exifWithoutAltitude} filePath="/photos/test.jpg" />)

      expect(screen.getByText('Map')).toBeInTheDocument()
    })
  })

  describe('File Path Handling', () => {
    it('should accept different file paths', () => {
      const paths = ['/photos/vacation.jpg', '/images/2024/photo.jpg', 'C:\\Photos\\test.jpg']

      for (const path of paths) {
        const { unmount } = render(<PhotoMap exifData={mockExifDataWithGPS} filePath={path} />)
        expect(screen.getByText('Map')).toBeInTheDocument()
        unmount()
      }
    })

    it('should update when filePath changes', () => {
      const { rerender } = render(
        <PhotoMap exifData={mockExifDataWithGPS} filePath="/photos/photo1.jpg" />
      )

      expect(screen.getByText('Map')).toBeInTheDocument()

      rerender(<PhotoMap exifData={mockExifDataWithGPS} filePath="/photos/photo2.jpg" />)

      expect(screen.getByText('Map')).toBeInTheDocument()
    })

    it('should handle transition from GPS to no GPS', () => {
      const { rerender } = render(
        <PhotoMap exifData={mockExifDataWithGPS} filePath="/photos/photo1.jpg" />
      )

      expect(screen.getByText('Map')).toBeInTheDocument()

      rerender(<PhotoMap exifData={mockExifDataWithoutGPS} filePath="/photos/photo2.jpg" />)

      expect(screen.getByText('This image does not contain GPS coordinates')).toBeInTheDocument()
    })

    it('should handle transition from no GPS to GPS', () => {
      const { rerender } = render(
        <PhotoMap exifData={mockExifDataWithoutGPS} filePath="/photos/photo1.jpg" />
      )

      expect(screen.getByText('This image does not contain GPS coordinates')).toBeInTheDocument()

      rerender(<PhotoMap exifData={mockExifDataWithGPS} filePath="/photos/photo2.jpg" />)

      expect(screen.getByText('Map')).toBeInTheDocument()
    })
  })

  describe('GPS Coordinates', () => {
    it('should accept valid latitude and longitude', () => {
      const exifData: ExifData = {
        gps: {
          latitude: 0,
          longitude: 0,
        },
      }

      render(<PhotoMap exifData={exifData} filePath="/photos/test.jpg" />)

      expect(screen.getByText('Map')).toBeInTheDocument()
    })

    it('should accept negative coordinates', () => {
      const exifData: ExifData = {
        gps: {
          latitude: -33.8688,
          longitude: 151.2093,
        },
      }

      render(<PhotoMap exifData={exifData} filePath="/photos/test.jpg" />)

      expect(screen.getByText('Map')).toBeInTheDocument()
    })

    it('should accept extreme coordinates', () => {
      const exifData: ExifData = {
        gps: {
          latitude: 89.9,
          longitude: 179.9,
        },
      }

      render(<PhotoMap exifData={exifData} filePath="/photos/test.jpg" />)

      expect(screen.getByText('Map')).toBeInTheDocument()
    })
  })

  describe('Component Structure', () => {
    it('should render Card component', () => {
      const { container } = render(<PhotoMap exifData={null} filePath={null} />)

      const card = container.querySelector('.rounded-lg.border')
      expect(card).toBeInTheDocument()
    })

    it('should render CardHeader', () => {
      const { container } = render(<PhotoMap exifData={null} filePath={null} />)

      const header = container.querySelector('.flex.flex-col.space-y-1\\.5.p-6')
      expect(header).toBeInTheDocument()
    })

    it('should render CardContent', () => {
      const { container } = render(<PhotoMap exifData={null} filePath={null} />)

      const content = container.querySelector('.p-6')
      expect(content).toBeInTheDocument()
    })
  })
})
