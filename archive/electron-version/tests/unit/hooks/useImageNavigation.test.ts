import { useImageNavigation } from '@renderer/hooks/useImageNavigation'
import { useAppStore } from '@renderer/stores/appStore'
import { renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import type { FileEntry } from '@/types/ipc'

describe('useImageNavigation', () => {
  const mockFiles: FileEntry[] = [
    {
      name: 'photo1.jpg',
      path: '/photos/photo1.jpg',
      isDirectory: false,
      size: 1024000,
      modifiedTime: Date.now(),
    },
    {
      name: 'photo2.jpg',
      path: '/photos/photo2.jpg',
      isDirectory: false,
      size: 2048000,
      modifiedTime: Date.now(),
    },
    {
      name: 'photo3.jpg',
      path: '/photos/photo3.jpg',
      isDirectory: false,
      size: 1536000,
      modifiedTime: Date.now(),
    },
  ]

  beforeEach(() => {
    // Reset store before each test
    useAppStore.setState({
      selectedFiles: [],
    })
  })

  describe('selectNext', () => {
    it('should select first file when no file is selected', () => {
      const { result } = renderHook(() => useImageNavigation(mockFiles))

      result.current.selectNext()

      expect(useAppStore.getState().selectedFiles).toEqual(['/photos/photo1.jpg'])
    })

    it('should select next file in sequence', () => {
      useAppStore.setState({ selectedFiles: ['/photos/photo1.jpg'] })

      const { result } = renderHook(() => useImageNavigation(mockFiles))

      result.current.selectNext()

      expect(useAppStore.getState().selectedFiles).toEqual(['/photos/photo2.jpg'])
    })

    it('should wrap around to first file when at end', () => {
      useAppStore.setState({ selectedFiles: ['/photos/photo3.jpg'] })

      const { result } = renderHook(() => useImageNavigation(mockFiles))

      result.current.selectNext()

      expect(useAppStore.getState().selectedFiles).toEqual(['/photos/photo1.jpg'])
    })

    it('should select first file when current file not in list', () => {
      useAppStore.setState({ selectedFiles: ['/photos/not-in-list.jpg'] })

      const { result } = renderHook(() => useImageNavigation(mockFiles))

      result.current.selectNext()

      expect(useAppStore.getState().selectedFiles).toEqual(['/photos/photo1.jpg'])
    })

    it('should do nothing when files array is empty', () => {
      const { result } = renderHook(() => useImageNavigation([]))

      result.current.selectNext()

      expect(useAppStore.getState().selectedFiles).toEqual([])
    })
  })

  describe('selectPrevious', () => {
    it('should select last file when no file is selected', () => {
      const { result } = renderHook(() => useImageNavigation(mockFiles))

      result.current.selectPrevious()

      expect(useAppStore.getState().selectedFiles).toEqual(['/photos/photo3.jpg'])
    })

    it('should select previous file in sequence', () => {
      useAppStore.setState({ selectedFiles: ['/photos/photo2.jpg'] })

      const { result } = renderHook(() => useImageNavigation(mockFiles))

      result.current.selectPrevious()

      expect(useAppStore.getState().selectedFiles).toEqual(['/photos/photo1.jpg'])
    })

    it('should wrap around to last file when at start', () => {
      useAppStore.setState({ selectedFiles: ['/photos/photo1.jpg'] })

      const { result } = renderHook(() => useImageNavigation(mockFiles))

      result.current.selectPrevious()

      expect(useAppStore.getState().selectedFiles).toEqual(['/photos/photo3.jpg'])
    })

    it('should select last file when current file not in list', () => {
      useAppStore.setState({ selectedFiles: ['/photos/not-in-list.jpg'] })

      const { result } = renderHook(() => useImageNavigation(mockFiles))

      result.current.selectPrevious()

      expect(useAppStore.getState().selectedFiles).toEqual(['/photos/photo3.jpg'])
    })

    it('should do nothing when files array is empty', () => {
      const { result } = renderHook(() => useImageNavigation([]))

      result.current.selectPrevious()

      expect(useAppStore.getState().selectedFiles).toEqual([])
    })
  })

  describe('selectFirst', () => {
    it('should select first file', () => {
      const { result } = renderHook(() => useImageNavigation(mockFiles))

      result.current.selectFirst()

      expect(useAppStore.getState().selectedFiles).toEqual(['/photos/photo1.jpg'])
    })

    it('should select first file even when another is selected', () => {
      useAppStore.setState({ selectedFiles: ['/photos/photo3.jpg'] })

      const { result } = renderHook(() => useImageNavigation(mockFiles))

      result.current.selectFirst()

      expect(useAppStore.getState().selectedFiles).toEqual(['/photos/photo1.jpg'])
    })

    it('should do nothing when files array is empty', () => {
      const { result } = renderHook(() => useImageNavigation([]))

      result.current.selectFirst()

      expect(useAppStore.getState().selectedFiles).toEqual([])
    })
  })

  describe('selectLast', () => {
    it('should select last file', () => {
      const { result } = renderHook(() => useImageNavigation(mockFiles))

      result.current.selectLast()

      expect(useAppStore.getState().selectedFiles).toEqual(['/photos/photo3.jpg'])
    })

    it('should select last file even when another is selected', () => {
      useAppStore.setState({ selectedFiles: ['/photos/photo1.jpg'] })

      const { result } = renderHook(() => useImageNavigation(mockFiles))

      result.current.selectLast()

      expect(useAppStore.getState().selectedFiles).toEqual(['/photos/photo3.jpg'])
    })

    it('should do nothing when files array is empty', () => {
      const { result } = renderHook(() => useImageNavigation([]))

      result.current.selectLast()

      expect(useAppStore.getState().selectedFiles).toEqual([])
    })
  })

  describe('clearSelection', () => {
    it('should clear selected files', () => {
      useAppStore.setState({ selectedFiles: ['/photos/photo1.jpg', '/photos/photo2.jpg'] })

      const { result } = renderHook(() => useImageNavigation(mockFiles))

      result.current.clearSelection()

      expect(useAppStore.getState().selectedFiles).toEqual([])
    })

    it('should do nothing when no files are selected', () => {
      const { result } = renderHook(() => useImageNavigation(mockFiles))

      result.current.clearSelection()

      expect(useAppStore.getState().selectedFiles).toEqual([])
    })
  })

  describe('currentFile and currentIndex', () => {
    it('should return null and -1 when no file is selected', () => {
      const { result } = renderHook(() => useImageNavigation(mockFiles))

      expect(result.current.currentFile).toBeNull()
      expect(result.current.currentIndex).toBe(-1)
    })

    it('should return current file and index when file is selected', () => {
      useAppStore.setState({ selectedFiles: ['/photos/photo2.jpg'] })

      const { result } = renderHook(() => useImageNavigation(mockFiles))

      expect(result.current.currentFile).toBe('/photos/photo2.jpg')
      expect(result.current.currentIndex).toBe(1)
    })

    it('should return -1 when selected file not in list', () => {
      useAppStore.setState({ selectedFiles: ['/photos/not-in-list.jpg'] })

      const { result } = renderHook(() => useImageNavigation(mockFiles))

      expect(result.current.currentFile).toBe('/photos/not-in-list.jpg')
      expect(result.current.currentIndex).toBe(-1)
    })
  })

  describe('totalFiles', () => {
    it('should return total number of files', () => {
      const { result } = renderHook(() => useImageNavigation(mockFiles))

      expect(result.current.totalFiles).toBe(3)
    })

    it('should return 0 when no files', () => {
      const { result } = renderHook(() => useImageNavigation([]))

      expect(result.current.totalFiles).toBe(0)
    })
  })
})
