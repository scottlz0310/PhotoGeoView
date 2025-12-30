import { useAppStore } from '@renderer/stores/appStore'
import { useCallback } from 'react'
import type { FileEntry } from '../../../types/ipc'

/**
 * Custom hook for navigating between images using arrow keys
 * @param files - Array of file entries
 * @returns Navigation functions
 */
export function useImageNavigation(files: FileEntry[]) {
  const { selectedFiles, setSelectedFiles } = useAppStore()
  const currentFile = selectedFiles.length > 0 ? selectedFiles[0] : null

  const selectNext = useCallback(() => {
    if (files.length === 0) return

    if (!currentFile) {
      // No selection, select first file
      setSelectedFiles([files[0].path])
      return
    }

    const currentIndex = files.findIndex((f) => f.path === currentFile)
    if (currentIndex === -1) {
      // Current file not in list, select first
      setSelectedFiles([files[0].path])
      return
    }

    // Select next file (wrap around to first if at end)
    const nextIndex = (currentIndex + 1) % files.length
    setSelectedFiles([files[nextIndex].path])
  }, [files, currentFile, setSelectedFiles])

  const selectPrevious = useCallback(() => {
    if (files.length === 0) return

    if (!currentFile) {
      // No selection, select last file
      setSelectedFiles([files[files.length - 1].path])
      return
    }

    const currentIndex = files.findIndex((f) => f.path === currentFile)
    if (currentIndex === -1) {
      // Current file not in list, select last
      setSelectedFiles([files[files.length - 1].path])
      return
    }

    // Select previous file (wrap around to last if at start)
    const prevIndex = currentIndex === 0 ? files.length - 1 : currentIndex - 1
    setSelectedFiles([files[prevIndex].path])
  }, [files, currentFile, setSelectedFiles])

  const selectFirst = useCallback(() => {
    if (files.length > 0) {
      setSelectedFiles([files[0].path])
    }
  }, [files, setSelectedFiles])

  const selectLast = useCallback(() => {
    if (files.length > 0) {
      setSelectedFiles([files[files.length - 1].path])
    }
  }, [files, setSelectedFiles])

  const clearSelection = useCallback(() => {
    setSelectedFiles([])
  }, [setSelectedFiles])

  return {
    selectNext,
    selectPrevious,
    selectFirst,
    selectLast,
    clearSelection,
    currentFile,
    currentIndex: currentFile ? files.findIndex((f) => f.path === currentFile) : -1,
    totalFiles: files.length,
  }
}
