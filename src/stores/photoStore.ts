import { create } from 'zustand'
import type { PhotoData, PhotoFilter } from '@/types/photo'

interface PhotoState {
  // 写真データ
  photos: PhotoData[]
  selectedPhoto: PhotoData | null

  // フィルター
  filter: PhotoFilter

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
}))
