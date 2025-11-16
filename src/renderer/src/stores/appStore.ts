import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export interface FileFilters {
  // Date range filter
  dateFrom: Date | null
  dateTo: Date | null

  // GPS filter
  hasGPS: boolean | null // null = all, true = with GPS, false = without GPS

  // Camera model filter
  cameraModels: string[] // empty = all models
}

interface AppState {
  // Current directory path
  currentPath: string
  setCurrentPath: (path: string) => void

  // Navigation history
  navigationHistory: string[]
  historyIndex: number
  navigateToPath: (path: string) => void
  canGoBack: () => boolean
  canGoForward: () => boolean
  goBack: () => void
  goForward: () => void

  // Selected files
  selectedFiles: string[]
  setSelectedFiles: (files: string[]) => void
  addSelectedFile: (file: string) => void
  removeSelectedFile: (file: string) => void
  clearSelectedFiles: () => void

  // Filters
  filters: FileFilters
  setDateFilter: (from: Date | null, to: Date | null) => void
  setGPSFilter: (hasGPS: boolean | null) => void
  toggleCameraModel: (model: string) => void
  clearCameraModels: () => void
  resetFilters: () => void

  // UI state
  isSidebarOpen: boolean
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void

  // Panel visibility state
  panelVisibility: {
    fileBrowser: boolean
    thumbnailGrid: boolean
    exifPanel: boolean
    imagePreview: boolean
    mapView: boolean
  }
  togglePanel: (panelId: keyof AppState['panelVisibility']) => void
  setPanelVisibility: (panelId: keyof AppState['panelVisibility'], visible: boolean) => void

  // Theme
  theme: 'light' | 'dark' | 'system'
  setTheme: (theme: 'light' | 'dark' | 'system') => void
}

export const useAppStore = create<AppState>()(
  devtools(
    (set, get) => ({
      // Initial state
      currentPath: '',
      navigationHistory: [],
      historyIndex: -1,
      selectedFiles: [],
      isSidebarOpen: true,
      theme: 'system',
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

      // Actions
      setCurrentPath: (path) => set({ currentPath: path }),

      // Navigation history actions
      navigateToPath: (path) =>
        set((state) => {
          // Don't add if it's the same as current path
          if (path === state.currentPath) return state

          // If we're not at the end of history, truncate forward history
          const newHistory =
            state.historyIndex < state.navigationHistory.length - 1
              ? state.navigationHistory.slice(0, state.historyIndex + 1)
              : [...state.navigationHistory]

          // Add new path to history
          newHistory.push(path)

          // Limit history to 50 entries
          const limitedHistory = newHistory.slice(-50)

          return {
            currentPath: path,
            navigationHistory: limitedHistory,
            historyIndex: limitedHistory.length - 1,
          }
        }),

      canGoBack: () => {
        const state = get()
        return state.historyIndex > 0
      },

      canGoForward: () => {
        const state = get()
        return state.historyIndex < state.navigationHistory.length - 1
      },

      goBack: () =>
        set((state) => {
          if (state.historyIndex > 0) {
            const newIndex = state.historyIndex - 1
            return {
              currentPath: state.navigationHistory[newIndex],
              historyIndex: newIndex,
            }
          }
          return state
        }),

      goForward: () =>
        set((state) => {
          if (state.historyIndex < state.navigationHistory.length - 1) {
            const newIndex = state.historyIndex + 1
            return {
              currentPath: state.navigationHistory[newIndex],
              historyIndex: newIndex,
            }
          }
          return state
        }),

      setSelectedFiles: (files) => set({ selectedFiles: files }),
      addSelectedFile: (file) =>
        set((state) => ({
          selectedFiles: [...state.selectedFiles, file],
        })),
      removeSelectedFile: (file) =>
        set((state) => ({
          selectedFiles: state.selectedFiles.filter((f) => f !== file),
        })),
      clearSelectedFiles: () => set({ selectedFiles: [] }),

      // Filter actions
      setDateFilter: (from, to) =>
        set((state) => ({
          filters: { ...state.filters, dateFrom: from, dateTo: to },
        })),

      setGPSFilter: (hasGPS) =>
        set((state) => ({
          filters: { ...state.filters, hasGPS },
        })),

      toggleCameraModel: (model) =>
        set((state) => {
          const models = state.filters.cameraModels
          const index = models.indexOf(model)
          const newModels = index === -1 ? [...models, model] : models.filter((m) => m !== model)
          return {
            filters: { ...state.filters, cameraModels: newModels },
          }
        }),

      clearCameraModels: () =>
        set((state) => ({
          filters: { ...state.filters, cameraModels: [] },
        })),

      resetFilters: () =>
        set({
          filters: {
            dateFrom: null,
            dateTo: null,
            hasGPS: null,
            cameraModels: [],
          },
        }),

      toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
      setSidebarOpen: (open) => set({ isSidebarOpen: open }),

      // Panel visibility actions
      togglePanel: (panelId) =>
        set((state) => ({
          panelVisibility: {
            ...state.panelVisibility,
            [panelId]: !state.panelVisibility[panelId],
          },
        })),

      setPanelVisibility: (panelId, visible) =>
        set((state) => ({
          panelVisibility: {
            ...state.panelVisibility,
            [panelId]: visible,
          },
        })),

      setTheme: (theme) => set({ theme }),
    }),
    { name: 'AppStore' }
  )
)
