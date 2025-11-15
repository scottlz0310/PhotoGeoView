import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

interface AppState {
  // Current directory path
  currentPath: string
  setCurrentPath: (path: string) => void

  // Selected files
  selectedFiles: string[]
  setSelectedFiles: (files: string[]) => void
  addSelectedFile: (file: string) => void
  removeSelectedFile: (file: string) => void
  clearSelectedFiles: () => void

  // UI state
  isSidebarOpen: boolean
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void

  // Theme
  theme: 'light' | 'dark' | 'system'
  setTheme: (theme: 'light' | 'dark' | 'system') => void
}

export const useAppStore = create<AppState>()(
  devtools(
    (set) => ({
      // Initial state
      currentPath: '',
      selectedFiles: [],
      isSidebarOpen: true,
      theme: 'system',

      // Actions
      setCurrentPath: (path) => set({ currentPath: path }),

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

      toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
      setSidebarOpen: (open) => set({ isSidebarOpen: open }),

      setTheme: (theme) => set({ theme }),
    }),
    { name: 'AppStore' }
  )
)
