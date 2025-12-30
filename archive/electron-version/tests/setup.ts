import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'
import '@testing-library/jest-dom/vitest'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock window.api for Electron IPC tests
global.window = Object.create(window)
Object.defineProperty(window, 'api', {
  value: {
    getDirectoryContents: vi.fn(),
    selectDirectory: vi.fn(),
    getFileInfo: vi.fn(),
    generateThumbnail: vi.fn(),
    readExif: vi.fn(),
    minimize: vi.fn(),
    maximize: vi.fn(),
    close: vi.fn(),
    getStoreValue: vi.fn(),
    setStoreValue: vi.fn(),
    showContextMenu: vi.fn(),
    onMenuRefresh: vi.fn().mockImplementation(() => () => {}),
    onMenuGoUp: vi.fn().mockImplementation(() => () => {}),
  },
  writable: true,
})
