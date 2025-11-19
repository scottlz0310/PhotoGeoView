import { ThumbnailGrid } from '@renderer/components/thumbnail/ThumbnailGrid'
import { useAppStore } from '@renderer/stores/appStore'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { FileEntry } from '@/types/ipc'

// Mock @tanstack/react-virtual
vi.mock('@tanstack/react-virtual', () => ({
  useVirtualizer: () => ({
    getTotalSize: () => 800,
    getVirtualItems: () => [
      { index: 0, key: 0, size: 200, start: 0 },
      { index: 1, key: 1, size: 200, start: 200 },
    ],
  }),
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

describe('ThumbnailGrid', () => {
  const mockImageFiles: FileEntry[] = [
    {
      name: 'photo1.jpg',
      path: '/photos/photo1.jpg',
      isDirectory: false,
      isImage: true,
      size: 1024000,
      modifiedTime: Date.now(),
    },
    {
      name: 'photo2.jpg',
      path: '/photos/photo2.jpg',
      isDirectory: false,
      isImage: true,
      size: 2048000,
      modifiedTime: Date.now(),
    },
    {
      name: 'photo3.jpg',
      path: '/photos/photo3.jpg',
      isDirectory: false,
      isImage: true,
      size: 1536000,
      modifiedTime: Date.now(),
    },
  ]

  const mockMixedFiles: FileEntry[] = [
    ...mockImageFiles,
    {
      name: 'document.pdf',
      path: '/photos/document.pdf',
      isDirectory: false,
      isImage: false,
      size: 512000,
      modifiedTime: Date.now(),
    },
    {
      name: 'folder',
      path: '/photos/folder',
      isDirectory: true,
      isImage: false,
      size: 0,
      modifiedTime: Date.now(),
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    useAppStore.setState({
      selectedFiles: [],
      panelVisibility: {
        fileBrowser: true,
        thumbnailGrid: true,
        exifPanel: true,
        imagePreview: true,
        mapView: true,
      },
    })

    // Mock generateThumbnail API
    vi.mocked(window.api.generateThumbnail).mockResolvedValue({
      success: true,
      data: { thumbnail: 'data:image/png;base64,mock' },
    } as any)
  })

  describe('Empty States', () => {
    it('should display message when currentPath is null', () => {
      render(<ThumbnailGrid files={[]} currentPath={null} />, { wrapper: createWrapper() })

      expect(screen.getByText('Thumbnails')).toBeInTheDocument()
      expect(screen.getByText('Select a folder to view thumbnails')).toBeInTheDocument()
    })

    it('should display message when no image files are found', () => {
      const nonImageFiles: FileEntry[] = [
        {
          name: 'document.pdf',
          path: '/files/document.pdf',
          isDirectory: false,
          isImage: false,
          size: 512000,
          modifiedTime: Date.now(),
        },
      ]

      render(<ThumbnailGrid files={nonImageFiles} currentPath="/files" />, {
        wrapper: createWrapper(),
      })

      expect(screen.getByText('No images found in this folder')).toBeInTheDocument()
    })

    it('should not display thumbnails when currentPath is null', () => {
      const { container } = render(<ThumbnailGrid files={mockImageFiles} currentPath={null} />, {
        wrapper: createWrapper(),
      })

      expect(container.querySelector('button[type="button"]')).toBeNull()
    })
  })

  describe('Image Filtering', () => {
    it('should filter and display only image files', async () => {
      render(<ThumbnailGrid files={mockMixedFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      // Should show count of only image files (3), not all files (5)
      await waitFor(() => {
        expect(screen.getByText(/Thumbnails \(3\)/)).toBeInTheDocument()
      })
    })

    it('should not display non-image files in grid', async () => {
      render(<ThumbnailGrid files={mockMixedFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.queryByText('document.pdf')).not.toBeInTheDocument()
        expect(screen.queryByText('folder')).not.toBeInTheDocument()
      })
    })

    it('should display image file names', async () => {
      render(<ThumbnailGrid files={mockImageFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
        expect(screen.getByText('photo2.jpg')).toBeInTheDocument()
      })
    })
  })

  describe('Thumbnail Display', () => {
    it('should display image count in header', async () => {
      render(<ThumbnailGrid files={mockImageFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByText('Thumbnails (3)')).toBeInTheDocument()
      })
    })

    it('should render thumbnail items as buttons', async () => {
      const { container } = render(<ThumbnailGrid files={mockImageFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        const buttons = container.querySelectorAll('button[type="button"]')
        // At least some buttons should be rendered (virtual scrolling may not show all)
        expect(buttons.length).toBeGreaterThan(0)
      })
    })

    it('should call generateThumbnail API for each image', async () => {
      render(<ThumbnailGrid files={mockImageFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(window.api.generateThumbnail).toHaveBeenCalled()
      })
    })

    it('should display thumbnails when API returns success', async () => {
      render(<ThumbnailGrid files={mockImageFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        const images = screen.getAllByRole('img')
        expect(images.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Selection Behavior', () => {
    it('should select thumbnail on click', async () => {
      render(<ThumbnailGrid files={mockImageFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
      })

      const thumbnail = screen.getByText('photo1.jpg').closest('button')
      fireEvent.click(thumbnail!)

      const state = useAppStore.getState()
      expect(state.selectedFiles).toContain('/photos/photo1.jpg')
    })

    it('should replace selection on normal click', async () => {
      useAppStore.setState({ selectedFiles: ['/photos/photo2.jpg'] })

      render(<ThumbnailGrid files={mockImageFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
      })

      const thumbnail = screen.getByText('photo1.jpg').closest('button')
      fireEvent.click(thumbnail!)

      const state = useAppStore.getState()
      expect(state.selectedFiles).toEqual(['/photos/photo1.jpg'])
    })

    it('should add to selection with Ctrl+click', async () => {
      useAppStore.setState({ selectedFiles: ['/photos/photo1.jpg'] })

      render(<ThumbnailGrid files={mockImageFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByText('photo2.jpg')).toBeInTheDocument()
      })

      const thumbnail = screen.getByText('photo2.jpg').closest('button')
      fireEvent.click(thumbnail!, { ctrlKey: true })

      const state = useAppStore.getState()
      expect(state.selectedFiles).toContain('/photos/photo1.jpg')
      expect(state.selectedFiles).toContain('/photos/photo2.jpg')
      expect(state.selectedFiles).toHaveLength(2)
    })

    it('should add to selection with Meta+click (Cmd on Mac)', async () => {
      useAppStore.setState({ selectedFiles: ['/photos/photo1.jpg'] })

      render(<ThumbnailGrid files={mockImageFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByText('photo2.jpg')).toBeInTheDocument()
      })

      const thumbnail = screen.getByText('photo2.jpg').closest('button')
      fireEvent.click(thumbnail!, { metaKey: true })

      const state = useAppStore.getState()
      expect(state.selectedFiles).toContain('/photos/photo1.jpg')
      expect(state.selectedFiles).toContain('/photos/photo2.jpg')
      expect(state.selectedFiles).toHaveLength(2)
    })

    it('should deselect with Ctrl+click when already selected', async () => {
      useAppStore.setState({ selectedFiles: ['/photos/photo1.jpg', '/photos/photo2.jpg'] })

      render(<ThumbnailGrid files={mockImageFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
      })

      const thumbnail = screen.getByText('photo1.jpg').closest('button')
      fireEvent.click(thumbnail!, { ctrlKey: true })

      const state = useAppStore.getState()
      expect(state.selectedFiles).not.toContain('/photos/photo1.jpg')
      expect(state.selectedFiles).toContain('/photos/photo2.jpg')
      expect(state.selectedFiles).toHaveLength(1)
    })

    it('should apply selected styling to selected thumbnails', async () => {
      useAppStore.setState({ selectedFiles: ['/photos/photo1.jpg'] })

      render(<ThumbnailGrid files={mockImageFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        const thumbnail = screen.getByText('photo1.jpg').closest('button')
        expect(thumbnail).toHaveClass('border-primary')
      })
    })

    it('should not apply selected styling to unselected thumbnails', async () => {
      useAppStore.setState({ selectedFiles: ['/photos/photo1.jpg'] })

      render(<ThumbnailGrid files={mockImageFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        const thumbnail = screen.getByText('photo2.jpg').closest('button')
        expect(thumbnail).not.toHaveClass('border-primary')
      })
    })
  })

  describe('Loading State', () => {
    it('should show loading state while thumbnail is generating', async () => {
      vi.mocked(window.api.generateThumbnail).mockImplementation(() => new Promise(() => {}) as any)

      const { container } = render(<ThumbnailGrid files={mockImageFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        const loader = container.querySelector('.animate-spin')
        expect(loader).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('should display fallback icon when thumbnail generation fails', async () => {
      vi.mocked(window.api.generateThumbnail).mockResolvedValue({
        success: false,
      } as any)

      const { container } = render(<ThumbnailGrid files={mockImageFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        // Should show ImageIcon when no thumbnail is available
        const icons = container.querySelectorAll('.lucide-image')
        expect(icons.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Virtual Scrolling', () => {
    it('should render virtual scroll container', () => {
      const { container } = render(<ThumbnailGrid files={mockImageFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      const scrollContainer = container.querySelector('.h-full.overflow-auto')
      expect(scrollContainer).toBeInTheDocument()
    })

    it('should use virtualization for large file lists', () => {
      const manyFiles: FileEntry[] = Array.from({ length: 100 }, (_, i) => ({
        name: `photo${i}.jpg`,
        path: `/photos/photo${i}.jpg`,
        isDirectory: false,
        isImage: true,
        size: 1024000,
        modifiedTime: Date.now(),
      }))

      render(<ThumbnailGrid files={manyFiles} currentPath="/photos" />, {
        wrapper: createWrapper(),
      })

      // Virtual scrolling should render container
      expect(screen.getByText('Thumbnails (100)')).toBeInTheDocument()
    })
  })
})
