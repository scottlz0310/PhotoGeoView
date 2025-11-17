import { ImagePreview } from '@renderer/components/preview/ImagePreview'
import { useAppStore } from '@renderer/stores/appStore'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Mock react-zoom-pan-pinch
vi.mock('react-zoom-pan-pinch', () => ({
  TransformWrapper: ({ children }: { children: any }) => {
    const mockMethods = {
      zoomIn: vi.fn(),
      zoomOut: vi.fn(),
      resetTransform: vi.fn(),
    }
    return <div data-testid="transform-wrapper">{children(mockMethods)}</div>
  },
  TransformComponent: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="transform-component">{children}</div>
  ),
}))

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  })

const createWrapper = () => {
  const testQueryClient = createTestQueryClient()
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={testQueryClient}>{children}</QueryClientProvider>
  )
}

describe('ImagePreview', () => {
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
      render(<ImagePreview filePath={null} />, { wrapper: createWrapper() })

      expect(screen.getByText('Image Preview')).toBeInTheDocument()
      expect(screen.getByText('Select an image to preview')).toBeInTheDocument()
    })

    it('should not display image controls when filePath is null', () => {
      const { container } = render(<ImagePreview filePath={null} />, { wrapper: createWrapper() })

      expect(screen.queryByTestId('transform-wrapper')).not.toBeInTheDocument()
      expect(container.querySelector('img')).not.toBeInTheDocument()
    })
  })

  describe('Image Display', () => {
    it('should display image when filePath is provided', () => {
      render(<ImagePreview filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      const image = screen.getByRole('img')
      expect(image).toBeInTheDocument()
    })

    it('should use correct image URL for Unix paths', () => {
      render(<ImagePreview filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      const image = screen.getByRole('img') as HTMLImageElement
      expect(image.src).toContain('local-file:///photos/test.jpg')
    })

    it('should use correct image URL for Windows paths', () => {
      render(<ImagePreview filePath="C:\\Photos\\test.jpg" />, { wrapper: createWrapper() })

      const image = screen.getByRole('img') as HTMLImageElement
      // Windows paths are converted to forward slashes
      expect(image.src).toMatch(/local-file:\/\/\/C:\/+Photos\/+test\.jpg/)
    })

    it('should display correct alt text from file name', () => {
      render(<ImagePreview filePath="/photos/vacation.jpg" />, { wrapper: createWrapper() })

      const image = screen.getByAltText('vacation.jpg')
      expect(image).toBeInTheDocument()
    })

    it('should include cache-busting timestamp in image URL', () => {
      render(<ImagePreview filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      const image = screen.getByRole('img') as HTMLImageElement
      expect(image.src).toMatch(/\?t=\d+/)
    })
  })

  describe('Error Handling', () => {
    it('should hide failed image element on error', async () => {
      render(<ImagePreview filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      const image = screen.getByRole('img') as HTMLImageElement
      fireEvent.error(image)

      await waitFor(() => {
        expect(image.style.display).toBe('none')
      })
    })
  })

  describe('Control Buttons', () => {
    it('should render control buttons when image is displayed', () => {
      const { container } = render(<ImagePreview filePath="/photos/test.jpg" />, {
        wrapper: createWrapper(),
      })

      // Count all buttons (there should be 7: collapse, zoom in, zoom out, reset, fit, rotate left, rotate right)
      const buttons = container.querySelectorAll('button')
      expect(buttons.length).toBeGreaterThan(5)
    })
  })

  describe('File Path Changes', () => {
    it('should update image when filePath changes', () => {
      const { rerender } = render(<ImagePreview filePath="/photos/photo1.jpg" />, {
        wrapper: createWrapper(),
      })

      let image = screen.getByRole('img') as HTMLImageElement
      expect(image.src).toContain('photo1.jpg')

      rerender(<ImagePreview filePath="/photos/photo2.jpg" />)

      image = screen.getByRole('img') as HTMLImageElement
      expect(image.src).toContain('photo2.jpg')
    })

    it('should reset to empty state when filePath becomes null', () => {
      const { rerender } = render(<ImagePreview filePath="/photos/photo1.jpg" />, {
        wrapper: createWrapper(),
      })

      expect(screen.getByRole('img')).toBeInTheDocument()

      rerender(<ImagePreview filePath={null} />)

      expect(screen.queryByRole('img')).not.toBeInTheDocument()
      expect(screen.getByText('Select an image to preview')).toBeInTheDocument()
    })
  })

  describe('Transform Wrapper Integration', () => {
    it('should render TransformWrapper component', () => {
      render(<ImagePreview filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      expect(screen.getByTestId('transform-wrapper')).toBeInTheDocument()
    })

    it('should render TransformComponent for image container', () => {
      render(<ImagePreview filePath="/photos/test.jpg" />, { wrapper: createWrapper() })

      expect(screen.getByTestId('transform-component')).toBeInTheDocument()
    })
  })
})
