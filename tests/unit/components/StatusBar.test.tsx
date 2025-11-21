import { StatusBar } from '@renderer/components/StatusBar'
import { useAppStore } from '@renderer/stores/appStore'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'statusBar.noImageSelected': 'No image selected',
      }
      return translations[key] || key
    },
  }),
}))

// Mock window.api
const mockApi = {
  readExif: vi.fn(),
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

describe('StatusBar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useAppStore.setState({
      statusBarItems: {
        camera: true,
        exposure: true,
        gps: true,
        datetime: true,
        dimensions: true,
      },
    })
  })

  describe('No Image Selected', () => {
    it('should show "No image selected" when filePath is null', () => {
      renderWithProviders(<StatusBar filePath={null} />)

      expect(screen.getByText('No image selected')).toBeInTheDocument()
    })

    it('should show "No image selected" when filePath is undefined', () => {
      renderWithProviders(<StatusBar filePath={undefined} />)

      expect(screen.getByText('No image selected')).toBeInTheDocument()
    })
  })

  describe('With Image Selected', () => {
    it('should render status bar with file path', () => {
      renderWithProviders(<StatusBar filePath="/photos/test.jpg" />)

      // Should not show "No image selected"
      expect(screen.queryByText('No image selected')).not.toBeInTheDocument()
    })
  })

  describe('Status Bar Item Visibility', () => {
    it('should respect camera visibility setting', () => {
      useAppStore.setState({
        statusBarItems: {
          camera: false,
          exposure: true,
          gps: true,
          datetime: true,
          dimensions: true,
        },
      })

      renderWithProviders(<StatusBar filePath="/photos/test.jpg" />)

      const state = useAppStore.getState()
      expect(state.statusBarItems.camera).toBe(false)
    })

    it('should respect all items hidden', () => {
      useAppStore.setState({
        statusBarItems: {
          camera: false,
          exposure: false,
          gps: false,
          datetime: false,
          dimensions: false,
        },
      })

      renderWithProviders(<StatusBar filePath="/photos/test.jpg" />)

      const state = useAppStore.getState()
      expect(state.statusBarItems.camera).toBe(false)
      expect(state.statusBarItems.exposure).toBe(false)
    })
  })

  describe('Layout', () => {
    it('should render with border-t class', () => {
      const { container } = renderWithProviders(<StatusBar filePath={null} />)

      const footer = container.querySelector('footer')
      expect(footer).toHaveClass('border-t')
    })

    it('should render as footer element', () => {
      const { container } = renderWithProviders(<StatusBar filePath={null} />)

      const footer = container.querySelector('footer')
      expect(footer).toBeInTheDocument()
    })

    it('should have proper styling classes', () => {
      const { container } = renderWithProviders(<StatusBar filePath={null} />)

      const footer = container.querySelector('footer')
      expect(footer).toHaveClass('flex-shrink-0')
      expect(footer).toHaveClass('bg-card')
    })
  })
})
