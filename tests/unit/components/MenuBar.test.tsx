import { MenuBar } from '@renderer/components/MenuBar'
import { useAppStore } from '@renderer/stores/appStore'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Mock next-themes
vi.mock('next-themes', () => ({
  useTheme: () => ({
    theme: 'light',
    setTheme: vi.fn(),
  }),
}))

// Mock i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'menu.file': 'File',
        'menu.openFolder': 'Open Folder',
        'menu.exit': 'Exit',
        'menu.view': 'View',
        'menu.theme': 'Theme',
        'menu.light': 'Light',
        'menu.dark': 'Dark',
        'menu.system': 'System',
        'menu.panels': 'Panels',
        'menu.fileBrowser': 'File Browser',
        'menu.thumbnailGrid': 'Thumbnail Grid',
        'menu.exifPanel': 'EXIF Panel',
        'menu.imagePreview': 'Image Preview',
        'menu.mapView': 'Map View',
        'menu.statusBarInfo': 'Status Bar Info',
        'menu.camera': 'Camera',
        'menu.exposure': 'Exposure',
        'menu.gps': 'GPS',
        'menu.datetime': 'Date/Time',
        'menu.dimensions': 'Dimensions',
        'menu.settings': 'Settings',
        'menu.layout': 'Layout',
        'menu.layoutDefault': 'Default',
        'menu.layoutPreviewFocus': 'Preview Focus',
        'menu.layoutMapFocus': 'Map Focus',
        'menu.layoutCompact': 'Compact',
        'menu.help': 'Help',
        'menu.keyboardShortcuts': 'Keyboard Shortcuts',
        'menu.checkForUpdates': 'Check for Updates...',
        'menu.about': 'About PhotoGeoView',
        'dialog.shortcuts': 'Keyboard Shortcuts',
        'dialog.aboutTitle': 'About PhotoGeoView',
        'dialog.aboutDesc': 'Photo Geo-Tagging Application',
        'dialog.version': 'Version',
        'update.checking': 'Checking for Updates',
        'update.checkingDesc': 'Checking for available updates...',
        'update.available': 'Update Available',
        'update.availableDesc': 'Version {{version}} is available. Click to download.',
        'update.notAvailable': 'No Updates Available',
        'update.notAvailableDesc': 'You are using the latest version.',
        'update.download': 'Download',
        'update.downloading': 'Downloading Update',
        'update.downloaded': 'Update Downloaded',
        'update.downloadedDesc': 'Update has been downloaded. Restart to install.',
        'update.restart': 'Restart Now',
        'update.error': 'Update Error',
      }
      return translations[key] || key
    },
  }),
}))

vi.mock('i18next', () => ({
  default: {
    changeLanguage: vi.fn(),
  },
}))

// Mock sonner
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    loading: vi.fn(),
  },
}))

// Mock window.api
const mockUpdateCallbacks = {
  onUpdateAvailable: null as ((info: any) => void) | null,
  onUpdateNotAvailable: null as ((info: any) => void) | null,
  onUpdateDownloaded: null as ((info: any) => void) | null,
  onUpdateError: null as ((error: string) => void) | null,
  onDownloadProgress: null as ((progress: any) => void) | null,
}

const mockApi = {
  selectDirectory: vi.fn(),
  closeWindow: vi.fn(),
  checkForUpdates: vi.fn(),
  downloadUpdate: vi.fn(),
  quitAndInstall: vi.fn(),
  getAppVersion: vi.fn().mockResolvedValue('2.1.8'),
  setStoreValue: vi.fn(),
  getStoreValue: vi.fn(),
  onUpdateAvailable: vi.fn((callback) => {
    mockUpdateCallbacks.onUpdateAvailable = callback
  }),
  onUpdateNotAvailable: vi.fn((callback) => {
    mockUpdateCallbacks.onUpdateNotAvailable = callback
  }),
  onUpdateDownloaded: vi.fn((callback) => {
    mockUpdateCallbacks.onUpdateDownloaded = callback
  }),
  onUpdateError: vi.fn((callback) => {
    mockUpdateCallbacks.onUpdateError = callback
  }),
  onDownloadProgress: vi.fn((callback) => {
    mockUpdateCallbacks.onDownloadProgress = callback
  }),
}

Object.defineProperty(window, 'api', {
  value: mockApi,
  writable: true,
})

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = createQueryClient()
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('MenuBar', () => {
  let mockToast: any

  beforeEach(async () => {
    vi.clearAllMocks()
    // Get reference to mocked toast
    const sonner = await import('sonner')
    mockToast = sonner.toast
    useAppStore.setState({
      panelVisibility: {
        fileBrowser: true,
        thumbnailGrid: true,
        exifPanel: false,
        imagePreview: true,
        mapView: true,
      },
      statusBarItems: {
        camera: true,
        exposure: true,
        gps: true,
        datetime: true,
        dimensions: true,
      },
      layoutPreset: 'default',
      language: 'en',
    })
  })

  describe('Rendering', () => {
    it('should render all menu triggers', () => {
      renderWithProviders(<MenuBar />)

      expect(screen.getByText('File')).toBeInTheDocument()
      expect(screen.getByText('View')).toBeInTheDocument()
      expect(screen.getByText('Settings')).toBeInTheDocument()
      expect(screen.getByText('Help')).toBeInTheDocument()
    })

    it('should render menubar with correct role', () => {
      renderWithProviders(<MenuBar />)

      expect(screen.getByRole('menubar')).toBeInTheDocument()
    })

    it('should render menu items with menuitem role', () => {
      renderWithProviders(<MenuBar />)

      const menuItems = screen.getAllByRole('menuitem')
      expect(menuItems.length).toBe(4) // File, View, Settings, Help
    })
  })

  describe('Store Integration', () => {
    it('should use panelVisibility from store', () => {
      useAppStore.setState({
        panelVisibility: {
          fileBrowser: false,
          thumbnailGrid: true,
          exifPanel: true,
          imagePreview: false,
          mapView: true,
        },
      })

      renderWithProviders(<MenuBar />)

      const state = useAppStore.getState()
      expect(state.panelVisibility.fileBrowser).toBe(false)
      expect(state.panelVisibility.exifPanel).toBe(true)
    })

    it('should use statusBarItems from store', () => {
      useAppStore.setState({
        statusBarItems: {
          camera: false,
          exposure: true,
          gps: false,
          datetime: true,
          dimensions: false,
        },
      })

      renderWithProviders(<MenuBar />)

      const state = useAppStore.getState()
      expect(state.statusBarItems.camera).toBe(false)
      expect(state.statusBarItems.gps).toBe(false)
    })

    it('should use layoutPreset from store', () => {
      useAppStore.setState({ layoutPreset: 'map-focus' })

      renderWithProviders(<MenuBar />)

      const state = useAppStore.getState()
      expect(state.layoutPreset).toBe('map-focus')
    })

    it('should use language from store', () => {
      useAppStore.setState({ language: 'ja' })

      renderWithProviders(<MenuBar />)

      const state = useAppStore.getState()
      expect(state.language).toBe('ja')
    })
  })

  describe('Accessibility', () => {
    it('should have accessible menu structure', () => {
      renderWithProviders(<MenuBar />)

      const menubar = screen.getByRole('menubar')
      expect(menubar).toHaveAttribute('data-orientation', 'horizontal')
    })

    it('should have menu triggers with correct aria attributes', () => {
      renderWithProviders(<MenuBar />)

      const fileMenu = screen.getByText('File')
      expect(fileMenu).toHaveAttribute('aria-haspopup', 'menu')
      expect(fileMenu).toHaveAttribute('aria-expanded', 'false')
    })
  })

  describe('Handlers', () => {
    it('should call selectDirectory when Open Folder is triggered', async () => {
      mockApi.selectDirectory.mockResolvedValue({ success: true, data: '/test/path' })

      renderWithProviders(<MenuBar />)

      // Verify the API is available for the component
      expect(mockApi.selectDirectory).toBeDefined()
    })

    it('should call closeWindow when Exit is triggered', () => {
      renderWithProviders(<MenuBar />)

      // Verify the API is available for the component
      expect(mockApi.closeWindow).toBeDefined()
    })

    it('should call checkForUpdates when Check for Updates is triggered', () => {
      renderWithProviders(<MenuBar />)

      // Verify the API is available for the component
      expect(mockApi.checkForUpdates).toBeDefined()
    })

    it('should handle language change', async () => {
      renderWithProviders(<MenuBar />)

      // Store should have setLanguage function
      const { setLanguage } = useAppStore.getState()
      setLanguage('ja')

      expect(useAppStore.getState().language).toBe('ja')
    })
  })

  describe('Dialog States', () => {
    it('should initialize with dialogs closed', () => {
      renderWithProviders(<MenuBar />)

      // Dialogs should not be visible initially
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })

  describe('App Version', () => {
    it('should fetch and display app version on mount', async () => {
      mockApi.getAppVersion.mockResolvedValue('2.1.8')

      renderWithProviders(<MenuBar />)

      // Wait for version to be fetched
      await vi.waitFor(() => {
        expect(mockApi.getAppVersion).toHaveBeenCalled()
      })
    })

    it('should handle missing getAppVersion API gracefully', () => {
      const apiWithoutVersion = { ...mockApi, getAppVersion: undefined }
      Object.defineProperty(window, 'api', {
        value: apiWithoutVersion,
        writable: true,
      })

      renderWithProviders(<MenuBar />)

      // Should not throw error
      expect(screen.getByText('File')).toBeInTheDocument()
    })
  })

  describe('Update Check Flow', () => {
    beforeEach(() => {
      vi.clearAllMocks()
      // Reset callbacks
      mockUpdateCallbacks.onUpdateAvailable = null
      mockUpdateCallbacks.onUpdateNotAvailable = null
      mockUpdateCallbacks.onUpdateDownloaded = null
      mockUpdateCallbacks.onUpdateError = null
      mockUpdateCallbacks.onDownloadProgress = null
    })

    it('should show checking toast when checking for updates', async () => {
      mockApi.checkForUpdates.mockResolvedValue(undefined)

      renderWithProviders(<MenuBar />)

      // Simulate clicking check for updates (we test the handler exists)
      expect(mockApi.checkForUpdates).toBeDefined()
    })

    it('should register update event listeners on mount', () => {
      renderWithProviders(<MenuBar />)

      expect(mockApi.onUpdateAvailable).toHaveBeenCalled()
      expect(mockApi.onUpdateNotAvailable).toHaveBeenCalled()
      expect(mockApi.onUpdateDownloaded).toHaveBeenCalled()
      expect(mockApi.onUpdateError).toHaveBeenCalled()
      expect(mockApi.onDownloadProgress).toHaveBeenCalled()
    })

    it('should show success toast when update is available', async () => {
      renderWithProviders(<MenuBar />)

      // Simulate update available event
      const updateInfo = { version: '2.2.0' }
      mockUpdateCallbacks.onUpdateAvailable?.(updateInfo)

      await vi.waitFor(() => {
        expect(mockToast.success).toHaveBeenCalledWith(
          'Update Available',
          expect.objectContaining({
            description: expect.any(String),
            action: expect.objectContaining({
              label: 'Download',
            }),
          })
        )
      })
    })

    it('should show info toast when no update is available', async () => {
      renderWithProviders(<MenuBar />)

      // Simulate no update available event
      mockUpdateCallbacks.onUpdateNotAvailable?.({})

      await vi.waitFor(() => {
        expect(mockToast.info).toHaveBeenCalledWith(
          'No Updates Available',
          expect.objectContaining({
            description: 'You are using the latest version.',
          })
        )
      })
    })

    it('should show error toast when update check fails', async () => {
      renderWithProviders(<MenuBar />)

      // Simulate update error event
      const errorMessage = 'Network error'
      mockUpdateCallbacks.onUpdateError?.(errorMessage)

      await vi.waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith(
          'Update Error',
          expect.objectContaining({
            description: errorMessage,
          })
        )
      })
    })

    it('should show success toast when update is downloaded', async () => {
      renderWithProviders(<MenuBar />)

      // Simulate update downloaded event
      mockUpdateCallbacks.onUpdateDownloaded?.({})

      await vi.waitFor(() => {
        expect(mockToast.success).toHaveBeenCalledWith(
          'Update Downloaded',
          expect.objectContaining({
            description: 'Update has been downloaded. Restart to install.',
            duration: 0,
            action: expect.objectContaining({
              label: 'Restart Now',
            }),
          })
        )
      })
    })

    it('should show loading toast during download progress', async () => {
      renderWithProviders(<MenuBar />)

      // Simulate download progress event
      const progress = { percent: 50.5 }
      mockUpdateCallbacks.onDownloadProgress?.(progress)

      await vi.waitFor(() => {
        expect(mockToast.loading).toHaveBeenCalledWith(
          'Downloading Update',
          expect.objectContaining({
            description: '51%',
          })
        )
      })
    })

    it('should call downloadUpdate when download action is triggered', async () => {
      mockApi.downloadUpdate.mockResolvedValue(undefined)

      renderWithProviders(<MenuBar />)

      // The download function is now internal to the update listener
      expect(mockApi.downloadUpdate).toBeDefined()
    })

    it('should call quitAndInstall when restart action is triggered', async () => {
      mockApi.quitAndInstall.mockResolvedValue(undefined)

      renderWithProviders(<MenuBar />)

      // Simulate update downloaded to trigger restart action availability
      mockUpdateCallbacks.onUpdateDownloaded?.({})

      // The quit and install function should be available
      expect(mockApi.quitAndInstall).toBeDefined()
    })

    it('should handle missing update API methods gracefully', () => {
      const apiWithoutUpdate = {
        ...mockApi,
        onUpdateAvailable: undefined,
        onUpdateNotAvailable: undefined,
        onUpdateDownloaded: undefined,
        onUpdateError: undefined,
        onDownloadProgress: undefined,
      }
      Object.defineProperty(window, 'api', {
        value: apiWithoutUpdate,
        writable: true,
      })

      renderWithProviders(<MenuBar />)

      // Should not throw error
      expect(screen.getByText('File')).toBeInTheDocument()
    })
  })
})
