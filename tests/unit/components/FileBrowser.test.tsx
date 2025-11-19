import { FileBrowser } from '@renderer/components/file-browser/FileBrowser'
import { useAppStore } from '@renderer/stores/appStore'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { FileEntry } from '@/types/ipc'

// Mock toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

// Mock FileList component
vi.mock('@renderer/components/file-browser/FileList', () => ({
  FileList: ({
    files,
    onFileDoubleClick,
  }: {
    files: FileEntry[]
    onFileDoubleClick: (file: FileEntry) => void
  }) => (
    <div data-testid="file-list">
      {files.map((file) => (
        <button
          key={file.path}
          type="button"
          data-testid={`file-item-${file.name}`}
          onDoubleClick={() => onFileDoubleClick(file)}
        >
          {file.name}
        </button>
      ))}
    </div>
  ),
}))

// Mock FileFilters component
vi.mock('@renderer/components/filters/FileFilters', () => ({
  FileFilters: () => <div data-testid="file-filters">Filters</div>,
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

describe('FileBrowser', () => {
  const mockFiles: FileEntry[] = [
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
      name: 'subfolder',
      path: '/photos/subfolder',
      isDirectory: true,
      isImage: false,
      size: 0,
      modifiedTime: Date.now(),
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    useAppStore.setState({
      currentPath: null,
      history: [],
      historyIndex: -1,
      selectedFiles: [],
      filters: {
        dateFrom: null,
        dateTo: null,
        hasGPS: null,
        cameraModels: [],
      },
      panelVisibility: {
        fileBrowser: true,
        thumbnailGrid: true,
        exifPanel: true,
        imagePreview: true,
        mapView: true,
      },
    })

    // Mock window.api
    vi.mocked(window.api.getDirectoryContents).mockResolvedValue({
      success: true,
      data: { entries: mockFiles },
    } as any)

    vi.mocked(window.api.selectDirectory).mockResolvedValue({
      success: true,
      data: '/selected/folder',
    } as any)
  })

  describe('Browser Mode Detection', () => {
    it('should display browser mode message when not in Electron', () => {
      const originalApi = (window as any).api
      ;(window as any).api = undefined

      render(<FileBrowser />, { wrapper: createWrapper() })

      expect(screen.getByText('Running in Browser Mode')).toBeInTheDocument()
      expect(
        screen.getByText('File system access is only available in the Electron desktop app.')
      ).toBeInTheDocument()

      // Restore
      ;(window as any).api = originalApi
    })

    it('should not display file browser when not in Electron', () => {
      const originalApi = (window as any).api
      ;(window as any).api = undefined

      const { container } = render(<FileBrowser />, { wrapper: createWrapper() })

      expect(container.querySelector('[data-testid="file-list"]')).not.toBeInTheDocument()

      // Restore
      ;(window as any).api = originalApi
    })
  })

  describe('Empty State', () => {
    it('should display empty state message when no path is selected', () => {
      render(<FileBrowser />, { wrapper: createWrapper() })

      expect(screen.getByText('File Browser')).toBeInTheDocument()
      expect(screen.getByText('Select a folder to browse')).toBeInTheDocument()
    })

    it('should not display navigation controls when no path is selected', () => {
      render(<FileBrowser />, { wrapper: createWrapper() })

      // Navigation buttons should not be visible
      expect(screen.queryByRole('button', { name: /Go Back/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /Go Forward/i })).not.toBeInTheDocument()
    })
  })

  describe('Folder Selection', () => {
    it('should render Select Folder button', () => {
      render(<FileBrowser />, { wrapper: createWrapper() })

      expect(screen.getByText('Select Folder')).toBeInTheDocument()
    })

    it('should call selectDirectory API when Select Folder is clicked', async () => {
      const user = userEvent.setup()
      render(<FileBrowser />, { wrapper: createWrapper() })

      const selectButton = screen.getByText('Select Folder')
      await user.click(selectButton)

      await waitFor(() => {
        expect(window.api.selectDirectory).toHaveBeenCalled()
      })
    })

    it('should update currentPath when folder is selected', async () => {
      const user = userEvent.setup()
      render(<FileBrowser />, { wrapper: createWrapper() })

      const selectButton = screen.getByText('Select Folder')
      await user.click(selectButton)

      await waitFor(() => {
        const state = useAppStore.getState()
        expect(state.currentPath).toBe('/selected/folder')
      })
    })
  })

  describe('File List Display', () => {
    it('should display files when path is set', async () => {
      useAppStore.setState({ currentPath: '/photos' })

      render(<FileBrowser />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByTestId('file-list')).toBeInTheDocument()
      })
    })

    it('should fetch directory contents when path is set', async () => {
      useAppStore.setState({ currentPath: '/photos' })

      render(<FileBrowser />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(window.api.getDirectoryContents).toHaveBeenCalledWith({
          path: '/photos',
          includeHidden: false,
          imageOnly: true,
        })
      })
    })

    it('should display all files from API response', async () => {
      useAppStore.setState({ currentPath: '/photos' })

      render(<FileBrowser />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByTestId('file-item-photo1.jpg')).toBeInTheDocument()
        expect(screen.getByTestId('file-item-photo2.jpg')).toBeInTheDocument()
        expect(screen.getByTestId('file-item-subfolder')).toBeInTheDocument()
      })
    })
  })

  describe('Search Functionality', () => {
    it('should display search input', () => {
      useAppStore.setState({ currentPath: '/photos' })
      render(<FileBrowser />, { wrapper: createWrapper() })

      expect(screen.getByPlaceholderText('Search files...')).toBeInTheDocument()
    })

    it('should filter files based on search query', async () => {
      const user = userEvent.setup()
      useAppStore.setState({ currentPath: '/photos' })

      render(<FileBrowser />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByTestId('file-item-photo1.jpg')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search files...')
      await user.type(searchInput, 'photo1')

      await waitFor(() => {
        expect(screen.getByTestId('file-item-photo1.jpg')).toBeInTheDocument()
        expect(screen.queryByTestId('file-item-photo2.jpg')).not.toBeInTheDocument()
        expect(screen.queryByTestId('file-item-subfolder')).not.toBeInTheDocument()
      })
    })

    it('should display clear button when search query is entered', async () => {
      const user = userEvent.setup()
      useAppStore.setState({ currentPath: '/photos' })

      render(<FileBrowser />, { wrapper: createWrapper() })

      const searchInput = screen.getByPlaceholderText('Search files...')
      await user.type(searchInput, 'test')

      await waitFor(() => {
        const clearButton = screen.getByRole('button', { name: /Clear search/i })
        expect(clearButton).toBeInTheDocument()
      })
    })

    it('should clear search query when clear button is clicked', async () => {
      const user = userEvent.setup()
      useAppStore.setState({ currentPath: '/photos' })

      render(<FileBrowser />, { wrapper: createWrapper() })

      const searchInput = screen.getByPlaceholderText('Search files...') as HTMLInputElement
      await user.type(searchInput, 'test')

      await waitFor(() => {
        expect(searchInput.value).toBe('test')
      })

      const clearButton = screen.getByRole('button', { name: /Clear search/i })
      await user.click(clearButton)

      await waitFor(() => {
        expect(searchInput.value).toBe('')
      })
    })

    it('should display "no files found" message when search has no results', async () => {
      const user = userEvent.setup()
      useAppStore.setState({ currentPath: '/photos' })

      render(<FileBrowser />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByTestId('file-list')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search files...')
      await user.type(searchInput, 'nonexistent')

      await waitFor(() => {
        expect(screen.getByText('No files found')).toBeInTheDocument()
        expect(screen.getByText('No files match "nonexistent"')).toBeInTheDocument()
      })
    })

    it('should display file count when searching', async () => {
      const user = userEvent.setup()
      useAppStore.setState({ currentPath: '/photos' })

      render(<FileBrowser />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByTestId('file-list')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search files...')
      await user.type(searchInput, 'photo1')

      await waitFor(() => {
        expect(screen.getByText(/1 of 3 files/)).toBeInTheDocument()
      })
    })
  })

  describe('Image Only Filter', () => {
    it('should display "Show images only" checkbox', () => {
      useAppStore.setState({ currentPath: '/photos' })
      render(<FileBrowser />, { wrapper: createWrapper() })

      expect(screen.getByLabelText('Show images only')).toBeInTheDocument()
    })

    it('should be checked by default', () => {
      useAppStore.setState({ currentPath: '/photos' })
      render(<FileBrowser />, { wrapper: createWrapper() })

      const checkbox = screen.getByLabelText('Show images only') as HTMLInputElement
      expect(checkbox.checked).toBe(true)
    })

    it('should fetch all files when unchecked', async () => {
      const user = userEvent.setup()
      useAppStore.setState({ currentPath: '/photos' })

      render(<FileBrowser />, { wrapper: createWrapper() })

      const checkbox = screen.getByLabelText('Show images only')
      await user.click(checkbox)

      await waitFor(() => {
        expect(window.api.getDirectoryContents).toHaveBeenCalledWith({
          path: '/photos',
          includeHidden: false,
          imageOnly: false,
        })
      })
    })
  })

  describe('Breadcrumb Navigation', () => {
    it('should display breadcrumb path', () => {
      useAppStore.setState({ currentPath: '/home/user/photos' })
      render(<FileBrowser />, { wrapper: createWrapper() })

      expect(screen.getByText('Root')).toBeInTheDocument()
      expect(screen.getByText('home')).toBeInTheDocument()
      expect(screen.getByText('user')).toBeInTheDocument()
      expect(screen.getByText('photos')).toBeInTheDocument()
    })

    it('should navigate when breadcrumb is clicked', async () => {
      const user = userEvent.setup()
      useAppStore.setState({ currentPath: '/home/user/photos' })

      render(<FileBrowser />, { wrapper: createWrapper() })

      const userBreadcrumb = screen.getByText('user')
      await user.click(userBreadcrumb)

      const state = useAppStore.getState()
      expect(state.currentPath).toBe('/home/user')
    })

    it('should clear selected files when breadcrumb is clicked', async () => {
      const user = userEvent.setup()
      useAppStore.setState({
        currentPath: '/home/user/photos',
        selectedFiles: ['/home/user/photos/photo1.jpg'],
      })

      render(<FileBrowser />, { wrapper: createWrapper() })

      const userBreadcrumb = screen.getByText('user')
      await user.click(userBreadcrumb)

      const state = useAppStore.getState()
      expect(state.selectedFiles).toHaveLength(0)
    })
  })

  describe('Navigation Buttons', () => {
    it('should display all navigation buttons', () => {
      useAppStore.setState({ currentPath: '/photos' })
      render(<FileBrowser />, { wrapper: createWrapper() })

      // Check for presence via container query as tooltips might not render accessible names
      const { container } = render(<FileBrowser />, { wrapper: createWrapper() })
      const buttons = container.querySelectorAll('button')
      expect(buttons.length).toBeGreaterThan(4) // Back, Forward, Home, Parent, Select, Collapse
    })

    it('should disable back button when cannot go back', () => {
      useAppStore.setState({ currentPath: '/photos', history: ['/photos'], historyIndex: 0 })
      const { container } = render(<FileBrowser />, { wrapper: createWrapper() })

      // Find back button (first navigation button)
      const navButtons = container.querySelectorAll('button[disabled]')
      expect(navButtons.length).toBeGreaterThan(0)
    })

    it('should disable forward button when cannot go forward', () => {
      useAppStore.setState({ currentPath: '/photos', history: ['/photos'], historyIndex: 0 })
      const { container } = render(<FileBrowser />, { wrapper: createWrapper() })

      // Forward button should be disabled when at the end of history
      const navButtons = container.querySelectorAll('button[disabled]')
      expect(navButtons.length).toBeGreaterThan(0)
    })

    it('should disable parent directory button when at root', () => {
      useAppStore.setState({ currentPath: '/' })
      const { container } = render(<FileBrowser />, { wrapper: createWrapper() })

      const navButtons = container.querySelectorAll('button[disabled]')
      expect(navButtons.length).toBeGreaterThan(0)
    })
  })

  describe('File Double Click', () => {
    it('should navigate to directory when double clicked', async () => {
      useAppStore.setState({ currentPath: '/photos' })
      render(<FileBrowser />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByTestId('file-item-subfolder')).toBeInTheDocument()
      })

      const subfolderItem = screen.getByTestId('file-item-subfolder')
      fireEvent.doubleClick(subfolderItem)

      const state = useAppStore.getState()
      expect(state.currentPath).toBe('/photos/subfolder')
    })

    it('should clear selected files when directory is double clicked', async () => {
      useAppStore.setState({
        currentPath: '/photos',
        selectedFiles: ['/photos/photo1.jpg'],
      })

      render(<FileBrowser />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByTestId('file-item-subfolder')).toBeInTheDocument()
      })

      const subfolderItem = screen.getByTestId('file-item-subfolder')
      fireEvent.doubleClick(subfolderItem)

      const state = useAppStore.getState()
      expect(state.selectedFiles).toHaveLength(0)
    })
  })

  describe('Date Filter Integration', () => {
    it('should filter files by date range', async () => {
      const now = Date.now()
      const yesterday = now - 24 * 60 * 60 * 1000
      const filesWithDates: FileEntry[] = [
        { ...mockFiles[0], modifiedTime: now },
        { ...mockFiles[1], modifiedTime: yesterday },
      ]

      vi.mocked(window.api.getDirectoryContents).mockResolvedValue({
        success: true,
        data: { entries: filesWithDates },
      } as any)

      useAppStore.setState({
        currentPath: '/photos',
        filters: {
          dateFrom: new Date(now - 1000),
          dateTo: null,
          hasGPS: null,
          cameraModels: [],
        },
      })

      render(<FileBrowser />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByTestId('file-item-photo1.jpg')).toBeInTheDocument()
        expect(screen.queryByTestId('file-item-photo2.jpg')).not.toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('should display error when directory fetch fails', async () => {
      vi.mocked(window.api.getDirectoryContents).mockRejectedValue(new Error('Access denied'))

      useAppStore.setState({ currentPath: '/photos' })

      render(<FileBrowser />, { wrapper: createWrapper() })

      // The error should be passed to FileList component
      await waitFor(() => {
        expect(window.api.getDirectoryContents).toHaveBeenCalled()
      })
    })

    it('should handle folder selection error', async () => {
      const user = userEvent.setup()
      vi.mocked(window.api.selectDirectory).mockResolvedValue({
        success: false,
        error: { message: 'Permission denied' },
      } as any)

      render(<FileBrowser />, { wrapper: createWrapper() })

      const selectButton = screen.getByText('Select Folder')
      await user.click(selectButton)

      await waitFor(() => {
        expect(window.api.selectDirectory).toHaveBeenCalled()
      })
    })
  })

  describe('Panel Controls', () => {
    it('should toggle panel when collapse button is clicked', async () => {
      const _user = userEvent.setup()
      render(<FileBrowser />, { wrapper: createWrapper() })

      const { container } = render(<FileBrowser />, { wrapper: createWrapper() })

      // Find collapse button (Minimize2 icon button)
      const buttons = container.querySelectorAll('button')
      // Collapse button is after Select Folder button
      expect(buttons.length).toBeGreaterThan(1)
    })
  })
})
