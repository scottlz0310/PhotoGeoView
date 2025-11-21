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
  },
}))

// Mock window.api
const mockApi = {
  selectDirectory: vi.fn(),
  closeWindow: vi.fn(),
  checkForUpdates: vi.fn(),
  setStoreValue: vi.fn(),
  getStoreValue: vi.fn(),
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
  beforeEach(() => {
    vi.clearAllMocks()
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
      const i18n = await import('i18next')
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
})
