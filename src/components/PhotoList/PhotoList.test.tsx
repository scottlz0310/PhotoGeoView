import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { usePhotoStore } from '@/stores/photoStore'
import { useSettingsStore } from '@/stores/settingsStore'
import type { PhotoData } from '@/types/photo'
import { PhotoList } from './PhotoList'

// モック
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}))

const { mockUsePhotoStore, mockUseVirtualizer } = vi.hoisted(() => ({
  mockUsePhotoStore: vi.fn(),
  mockUseVirtualizer: vi.fn(({ count }) => ({
    getVirtualItems: () => {
      return Array.from({ length: Math.min(count, 5) }).map((_, i) => ({
        index: i,
        start: i * 64,
        size: 64,
        key: String(i),
        measureElement: vi.fn(),
      }))
    },
    scrollToIndex: vi.fn(),
    getTotalSize: () => count * 64,
    measure: vi.fn(),
  })),
}))

vi.mock('@tanstack/react-virtual', () => ({
  useVirtualizer: mockUseVirtualizer,
}))

vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}))

// const { mockUsePhotoStore } = vi.hoisted(() => ({
//   mockUsePhotoStore: vi.fn(),
// }))

vi.mock('@/stores/photoStore', () => ({
  usePhotoStore: mockUsePhotoStore,
}))

vi.mock('@/stores/settingsStore', () => ({
  useSettingsStore: vi.fn(),
}))

// ResizeObserverのモック
globalThis.ResizeObserver = class ResizeObserver {
  observe() {
    // mock
  }
  unobserve() {
    // mock
  }
  disconnect() {
    // mock
  }
}

const mockPhotos: PhotoData[] = [
  {
    path: '/path/to/photo1.jpg',
    filename: 'photo1.jpg',
    fileSize: 1024 * 1024,
    modifiedTime: '2023-01-01T00:00:00',
    thumbnail: '',
    exif: {
      gps: { lat: 0, lng: 0 },
      datetime: '2023-01-01T00:00:00',
      camera: { make: 'Sony', model: 'Alpha' },
      width: 1000,
      height: 1000,
      iso: 100,
      aperture: 2.8,
      shutterSpeed: 0.01,
      focalLength: 50,
    },
  },
]

const defaultPhotoStoreState = {
  photos: [],
  selectedPhoto: null,
  selectedEntryPath: null,
  viewMode: 'list',
  currentPath: null,
  directoryEntries: [],
  isLoading: false,
  addPhotos: vi.fn(),
  selectPhoto: vi.fn(),
  setSelectedEntryPath: vi.fn(),
  setViewMode: vi.fn(),
  setIsLoading: vi.fn(),
  setLoadingStatus: vi.fn(),
  navigateToDirectory: vi.fn(),
}

describe('PhotoList', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useSettingsStore).mockReturnValue({
      settings: {
        display: { viewMode: 'list' },
      },
      updateSettings: vi.fn(),
    } as any)
  })

  it('should use mocked store', () => {
    expect(usePhotoStore).toBe(mockUsePhotoStore)
  })

  it('should render empty state when no photos', () => {
    mockUsePhotoStore.mockReturnValue(defaultPhotoStoreState)
    render(<PhotoList />)
    expect(mockUsePhotoStore).toHaveBeenCalled()
    // ツールバーが表示されていることを確認
    const backButtons = screen.getAllByTitle('common.back')
    expect(backButtons.length).toBeGreaterThan(0)
  })

  it('should call useVirtualizer with correct count', () => {
    mockUsePhotoStore.mockReturnValue({
      ...defaultPhotoStoreState,
      photos: mockPhotos,
      directoryEntries: [],
      currentPath: null,
    })

    render(<PhotoList />)
    expect(mockUseVirtualizer).toHaveBeenCalledWith(
      expect.objectContaining({
        count: 1,
      }),
    )
  })

  it('should render photos in list mode', async () => {
    mockUsePhotoStore.mockReturnValue({
      ...defaultPhotoStoreState,
      photos: mockPhotos,
      // isDirectoryView: false の場合、photos が使われる
      directoryEntries: [],
      currentPath: null,
    })

    render(<PhotoList />)
    expect(await screen.findByText('photo1.jpg')).toBeInTheDocument()
  })

  it('should render toolbar buttons', () => {
    render(<PhotoList />)
    const backButtons = screen.getAllByTitle('common.back')
    expect(backButtons.length).toBeGreaterThan(0)
  })
})
