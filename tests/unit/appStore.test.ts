import { useAppStore } from '@renderer/stores/appStore'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

describe('AppStore', () => {
  beforeEach(() => {
    // Reset store before each test
    const { setState } = useAppStore
    setState({
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
    })
  })

  afterEach(() => {
    // Clean up - reset to initial state
    const { setState } = useAppStore
    setState({
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
    })
  })

  describe('Path Management', () => {
    it('should set current path', () => {
      const { setCurrentPath, currentPath } = useAppStore.getState()
      setCurrentPath('/test/path')
      expect(useAppStore.getState().currentPath).toBe('/test/path')
    })
  })

  describe('Navigation History', () => {
    it('should navigate to path and update history', () => {
      const { navigateToPath } = useAppStore.getState()

      navigateToPath('/path1')
      expect(useAppStore.getState().currentPath).toBe('/path1')
      expect(useAppStore.getState().navigationHistory).toEqual(['/path1'])
      expect(useAppStore.getState().historyIndex).toBe(0)
    })

    it('should not add duplicate paths', () => {
      const { navigateToPath } = useAppStore.getState()

      navigateToPath('/path1')
      navigateToPath('/path1')

      expect(useAppStore.getState().navigationHistory).toEqual(['/path1'])
    })

    it('should allow going back and forward', () => {
      const { navigateToPath, goBack, goForward, canGoBack, canGoForward } = useAppStore.getState()

      navigateToPath('/path1')
      navigateToPath('/path2')
      navigateToPath('/path3')

      expect(useAppStore.getState().canGoBack()).toBe(true)
      expect(useAppStore.getState().canGoForward()).toBe(false)

      useAppStore.getState().goBack()
      expect(useAppStore.getState().currentPath).toBe('/path2')
      expect(useAppStore.getState().canGoForward()).toBe(true)

      useAppStore.getState().goForward()
      expect(useAppStore.getState().currentPath).toBe('/path3')
    })

    it('should limit history to 50 entries', () => {
      const { navigateToPath } = useAppStore.getState()

      // Add 60 paths
      for (let i = 0; i < 60; i++) {
        navigateToPath(`/path${i}`)
      }

      const { navigationHistory } = useAppStore.getState()
      expect(navigationHistory.length).toBeLessThanOrEqual(50)
    })
  })

  describe('File Selection', () => {
    it('should set selected files', () => {
      const { setSelectedFiles } = useAppStore.getState()

      setSelectedFiles(['file1.jpg', 'file2.jpg'])
      expect(useAppStore.getState().selectedFiles).toEqual(['file1.jpg', 'file2.jpg'])
    })

    it('should add file to selection', () => {
      const { addSelectedFile } = useAppStore.getState()

      addSelectedFile('file1.jpg')
      addSelectedFile('file2.jpg')

      expect(useAppStore.getState().selectedFiles).toEqual(['file1.jpg', 'file2.jpg'])
    })

    it('should remove file from selection', () => {
      const { setSelectedFiles, removeSelectedFile } = useAppStore.getState()

      setSelectedFiles(['file1.jpg', 'file2.jpg', 'file3.jpg'])
      removeSelectedFile('file2.jpg')

      expect(useAppStore.getState().selectedFiles).toEqual(['file1.jpg', 'file3.jpg'])
    })

    it('should clear all selected files', () => {
      const { setSelectedFiles, clearSelectedFiles } = useAppStore.getState()

      setSelectedFiles(['file1.jpg', 'file2.jpg'])
      clearSelectedFiles()

      expect(useAppStore.getState().selectedFiles).toEqual([])
    })
  })

  describe('Filters', () => {
    it('should set date filter', () => {
      const { setDateFilter } = useAppStore.getState()
      const from = new Date('2024-01-01')
      const to = new Date('2024-12-31')

      setDateFilter(from, to)

      const { filters } = useAppStore.getState()
      expect(filters.dateFrom).toEqual(from)
      expect(filters.dateTo).toEqual(to)
    })

    it('should set GPS filter', () => {
      const { setGPSFilter } = useAppStore.getState()

      setGPSFilter(true)
      expect(useAppStore.getState().filters.hasGPS).toBe(true)

      setGPSFilter(false)
      expect(useAppStore.getState().filters.hasGPS).toBe(false)

      setGPSFilter(null)
      expect(useAppStore.getState().filters.hasGPS).toBe(null)
    })

    it('should toggle camera model', () => {
      const { toggleCameraModel } = useAppStore.getState()

      toggleCameraModel('Canon EOS 5D')
      expect(useAppStore.getState().filters.cameraModels).toContain('Canon EOS 5D')

      toggleCameraModel('Canon EOS 5D')
      expect(useAppStore.getState().filters.cameraModels).not.toContain('Canon EOS 5D')
    })

    it('should clear camera models', () => {
      const { toggleCameraModel, clearCameraModels } = useAppStore.getState()

      toggleCameraModel('Canon EOS 5D')
      toggleCameraModel('Nikon D850')
      clearCameraModels()

      expect(useAppStore.getState().filters.cameraModels).toEqual([])
    })

    it('should reset all filters', () => {
      const { setDateFilter, setGPSFilter, toggleCameraModel, resetFilters } =
        useAppStore.getState()

      setDateFilter(new Date(), new Date())
      setGPSFilter(true)
      toggleCameraModel('Canon EOS 5D')

      resetFilters()

      const { filters } = useAppStore.getState()
      expect(filters.dateFrom).toBe(null)
      expect(filters.dateTo).toBe(null)
      expect(filters.hasGPS).toBe(null)
      expect(filters.cameraModels).toEqual([])
    })
  })

  describe('UI State', () => {
    it('should toggle sidebar', () => {
      const { toggleSidebar } = useAppStore.getState()

      expect(useAppStore.getState().isSidebarOpen).toBe(true)
      toggleSidebar()
      expect(useAppStore.getState().isSidebarOpen).toBe(false)
      toggleSidebar()
      expect(useAppStore.getState().isSidebarOpen).toBe(true)
    })

    it('should set sidebar state', () => {
      const { setSidebarOpen } = useAppStore.getState()

      setSidebarOpen(false)
      expect(useAppStore.getState().isSidebarOpen).toBe(false)

      setSidebarOpen(true)
      expect(useAppStore.getState().isSidebarOpen).toBe(true)
    })
  })

  describe('Panel Visibility', () => {
    it('should toggle panel visibility', () => {
      const { togglePanel } = useAppStore.getState()

      expect(useAppStore.getState().panelVisibility.exifPanel).toBe(true)
      togglePanel('exifPanel')
      expect(useAppStore.getState().panelVisibility.exifPanel).toBe(false)
      togglePanel('exifPanel')
      expect(useAppStore.getState().panelVisibility.exifPanel).toBe(true)
    })

    it('should set panel visibility', () => {
      const { setPanelVisibility } = useAppStore.getState()

      setPanelVisibility('mapView', false)
      expect(useAppStore.getState().panelVisibility.mapView).toBe(false)

      setPanelVisibility('mapView', true)
      expect(useAppStore.getState().panelVisibility.mapView).toBe(true)
    })
  })

  describe('Theme', () => {
    it('should set theme', () => {
      const { setTheme } = useAppStore.getState()

      setTheme('dark')
      expect(useAppStore.getState().theme).toBe('dark')

      setTheme('light')
      expect(useAppStore.getState().theme).toBe('light')

      setTheme('system')
      expect(useAppStore.getState().theme).toBe('system')
    })
  })
})
