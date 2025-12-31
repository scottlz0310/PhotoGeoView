import { invoke } from '@tauri-apps/api/core'
import { create } from 'zustand'
import type { DirectoryContent, DirectoryEntry, PhotoData, PhotoFilter } from '@/types/photo'
import { useSettingsStore } from './settingsStore'

export type ViewMode = 'list' | 'detail' | 'grid'

interface PhotoState {
  // 写真データ
  photos: PhotoData[]
  selectedPhoto: PhotoData | null

  // フィルター
  filter: PhotoFilter

  // ビューモード
  viewMode: ViewMode

  // ナビゲーション
  currentPath: string | null
  directoryEntries: DirectoryEntry[]

  // ローディング状態
  isLoading: boolean
  loadingStatus: string

  // アクション
  addPhotos: (photos: PhotoData[]) => void
  setPhotos: (photos: PhotoData[]) => void
  selectPhoto: (path: string | null) => void
  removePhoto: (path: string) => void
  clearPhotos: () => void

  // フィルター操作
  setFilter: (filter: Partial<PhotoFilter>) => void
  clearFilter: () => void

  // フィルター済み写真取得
  getFilteredPhotos: () => PhotoData[]

  // ビューモード操作
  setViewMode: (mode: ViewMode) => void
  // 設定から初期ビューモードを読み込む
  initializeViewMode: () => void

  // ナビゲーション操作
  navigateToDirectory: (path: string) => Promise<void>
  clearNavigation: () => void

  // ローディング操作
  setIsLoading: (isLoading: boolean) => void
  setLoadingStatus: (status: string) => void
}

const defaultFilter: PhotoFilter = {
  dateFrom: null,
  dateTo: null,
  hasGps: null,
}

export const usePhotoStore = create<PhotoState>((set, get) => ({
  // 初期状態
  photos: [],
  selectedPhoto: null,
  filter: defaultFilter,
  viewMode: 'list',
  currentPath: null,
  directoryEntries: [],
  isLoading: false,
  loadingStatus: '',

  // 写真追加（重複なし）
  addPhotos: (newPhotos) =>
    set((state) => {
      const existingPaths = new Set(state.photos.map((p) => p.path))
      const uniquePhotos = newPhotos.filter((p) => !existingPaths.has(p.path))
      return { photos: [...state.photos, ...uniquePhotos] }
    }),

  // 写真リスト置き換え
  setPhotos: (photos) => set({ photos }),

  // 写真選択
  selectPhoto: (path) =>
    set((state) => {
      if (path === null) {
        return { selectedPhoto: null }
      }
      const photo = state.photos.find((p) => p.path === path)
      return { selectedPhoto: photo || null }
    }),

  // 写真削除
  removePhoto: (path) =>
    set((state) => ({
      photos: state.photos.filter((p) => p.path !== path),
      selectedPhoto: state.selectedPhoto?.path === path ? null : state.selectedPhoto,
    })),

  // 全写真クリア
  clearPhotos: () => set({ photos: [], selectedPhoto: null }),

  // フィルター設定
  setFilter: (partialFilter) =>
    set((state) => ({
      filter: { ...state.filter, ...partialFilter },
    })),

  // フィルタークリア
  clearFilter: () => set({ filter: defaultFilter }),

  // フィルター済み写真取得
  getFilteredPhotos: () => {
    const { photos, filter } = get()

    return photos.filter((photo) => {
      // 日付フィルター
      if (filter.dateFrom || filter.dateTo) {
        const photoDate = photo.exif?.datetime
        if (!photoDate) {
          return false
        }

        const date = new Date(photoDate)

        if (filter.dateFrom && date < filter.dateFrom) {
          return false
        }

        if (filter.dateTo) {
          const endOfDay = new Date(filter.dateTo)
          endOfDay.setHours(23, 59, 59, 999)
          if (date > endOfDay) {
            return false
          }
        }
      }

      // GPS有無フィルター
      if (filter.hasGps !== null) {
        const hasGps = photo.exif?.gps !== null
        if (hasGps !== filter.hasGps) {
          return false
        }
      }

      return true
    })
  },

  // ビューモード変更（設定にも保存）
  setViewMode: (mode) => {
    set({ viewMode: mode })
    // 設定に保存
    const settingsStore = useSettingsStore.getState()
    settingsStore.updateSettings({
      display: { ...settingsStore.settings.display, defaultViewMode: mode },
    })
  },

  // 設定から初期ビューモードを読み込む
  initializeViewMode: () => {
    const settingsStore = useSettingsStore.getState()
    if (settingsStore.isLoaded) {
      set({ viewMode: settingsStore.settings.display.defaultViewMode })
    }
  },

  // ディレクトリに移動
  navigateToDirectory: async (path: string) => {
    const content = await invoke<DirectoryContent>('read_directory', { path })
    set({
      currentPath: content.currentPath,
      directoryEntries: content.entries,
    })
  },

  // ナビゲーション状態をクリア
  clearNavigation: () => {
    set({
      currentPath: null,
      directoryEntries: [],
    })
  },

  // ローディング状態を更新
  setIsLoading: (isLoading) => set({ isLoading }),
  setLoadingStatus: (status) => set({ loadingStatus: status }),
}))
