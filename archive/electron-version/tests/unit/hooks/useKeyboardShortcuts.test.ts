import {
  getShortcutDisplay,
  type KeyboardShortcut,
  useKeyboardShortcuts,
} from '@renderer/hooks/useKeyboardShortcuts'
import { renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

describe('useKeyboardShortcuts', () => {
  let mockHandlers: {
    handleSave: ReturnType<typeof vi.fn>
    handleOpen: ReturnType<typeof vi.fn>
    handleClose: ReturnType<typeof vi.fn>
  }

  beforeEach(() => {
    mockHandlers = {
      handleSave: vi.fn(),
      handleOpen: vi.fn(),
      handleClose: vi.fn(),
    }
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Single key shortcuts', () => {
    it('should trigger handler when matching key is pressed', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 'Escape', handler: mockHandlers.handleClose, description: 'Close' },
      ]

      renderHook(() => useKeyboardShortcuts(shortcuts))

      const event = new KeyboardEvent('keydown', { key: 'Escape' })
      window.dispatchEvent(event)

      expect(mockHandlers.handleClose).toHaveBeenCalledTimes(1)
    })

    it('should not trigger handler when different key is pressed', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 'Escape', handler: mockHandlers.handleClose, description: 'Close' },
      ]

      renderHook(() => useKeyboardShortcuts(shortcuts))

      const event = new KeyboardEvent('keydown', { key: 'Enter' })
      window.dispatchEvent(event)

      expect(mockHandlers.handleClose).not.toHaveBeenCalled()
    })
  })

  describe('Modifier key shortcuts', () => {
    it('should trigger handler for Ctrl+key shortcut', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 's', ctrlKey: true, handler: mockHandlers.handleSave, description: 'Save' },
      ]

      renderHook(() => useKeyboardShortcuts(shortcuts))

      const event = new KeyboardEvent('keydown', { key: 's', ctrlKey: true })
      window.dispatchEvent(event)

      expect(mockHandlers.handleSave).toHaveBeenCalledTimes(1)
    })

    it('should not trigger handler when Ctrl is not pressed', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 's', ctrlKey: true, handler: mockHandlers.handleSave, description: 'Save' },
      ]

      renderHook(() => useKeyboardShortcuts(shortcuts))

      const event = new KeyboardEvent('keydown', { key: 's' })
      window.dispatchEvent(event)

      expect(mockHandlers.handleSave).not.toHaveBeenCalled()
    })

    it('should trigger handler for Shift+key shortcut', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 'Tab', shiftKey: true, handler: mockHandlers.handleOpen, description: 'Open' },
      ]

      renderHook(() => useKeyboardShortcuts(shortcuts))

      const event = new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true })
      window.dispatchEvent(event)

      expect(mockHandlers.handleOpen).toHaveBeenCalledTimes(1)
    })

    it('should trigger handler for Alt+key shortcut', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 'f', altKey: true, handler: mockHandlers.handleOpen, description: 'File menu' },
      ]

      renderHook(() => useKeyboardShortcuts(shortcuts))

      const event = new KeyboardEvent('keydown', { key: 'f', altKey: true })
      window.dispatchEvent(event)

      expect(mockHandlers.handleOpen).toHaveBeenCalledTimes(1)
    })

    it('should trigger handler for Ctrl+Shift+key shortcut', () => {
      const shortcuts: KeyboardShortcut[] = [
        {
          key: 'p',
          ctrlKey: true,
          shiftKey: true,
          handler: mockHandlers.handleOpen,
          description: 'Command palette',
        },
      ]

      renderHook(() => useKeyboardShortcuts(shortcuts))

      const event = new KeyboardEvent('keydown', { key: 'p', ctrlKey: true, shiftKey: true })
      window.dispatchEvent(event)

      expect(mockHandlers.handleOpen).toHaveBeenCalledTimes(1)
    })

    it('should trigger handler for Ctrl+Alt+key shortcut', () => {
      const shortcuts: KeyboardShortcut[] = [
        {
          key: 'Delete',
          ctrlKey: true,
          altKey: true,
          handler: mockHandlers.handleClose,
          description: 'Force delete',
        },
      ]

      renderHook(() => useKeyboardShortcuts(shortcuts))

      const event = new KeyboardEvent('keydown', { key: 'Delete', ctrlKey: true, altKey: true })
      window.dispatchEvent(event)

      expect(mockHandlers.handleClose).toHaveBeenCalledTimes(1)
    })

    it('should not trigger when extra modifier is pressed', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 's', ctrlKey: true, handler: mockHandlers.handleSave, description: 'Save' },
      ]

      renderHook(() => useKeyboardShortcuts(shortcuts))

      const event = new KeyboardEvent('keydown', { key: 's', ctrlKey: true, shiftKey: true })
      window.dispatchEvent(event)

      expect(mockHandlers.handleSave).not.toHaveBeenCalled()
    })
  })

  describe('Multiple shortcuts', () => {
    it('should handle multiple shortcuts', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 's', ctrlKey: true, handler: mockHandlers.handleSave, description: 'Save' },
        { key: 'o', ctrlKey: true, handler: mockHandlers.handleOpen, description: 'Open' },
        { key: 'Escape', handler: mockHandlers.handleClose, description: 'Close' },
      ]

      renderHook(() => useKeyboardShortcuts(shortcuts))

      window.dispatchEvent(new KeyboardEvent('keydown', { key: 's', ctrlKey: true }))
      expect(mockHandlers.handleSave).toHaveBeenCalledTimes(1)

      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'o', ctrlKey: true }))
      expect(mockHandlers.handleOpen).toHaveBeenCalledTimes(1)

      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
      expect(mockHandlers.handleClose).toHaveBeenCalledTimes(1)
    })

    it('should only trigger the first matching shortcut', () => {
      const handler1 = vi.fn()
      const handler2 = vi.fn()

      const shortcuts: KeyboardShortcut[] = [
        { key: 's', handler: handler1, description: 'First' },
        { key: 's', handler: handler2, description: 'Second' },
      ]

      renderHook(() => useKeyboardShortcuts(shortcuts))

      window.dispatchEvent(new KeyboardEvent('keydown', { key: 's' }))

      expect(handler1).toHaveBeenCalledTimes(1)
      expect(handler2).not.toHaveBeenCalled()
    })
  })

  describe('Event prevention', () => {
    it('should prevent default event behavior', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 's', ctrlKey: true, handler: mockHandlers.handleSave, description: 'Save' },
      ]

      renderHook(() => useKeyboardShortcuts(shortcuts))

      const event = new KeyboardEvent('keydown', { key: 's', ctrlKey: true })
      const preventDefaultSpy = vi.spyOn(event, 'preventDefault')

      window.dispatchEvent(event)

      expect(preventDefaultSpy).toHaveBeenCalled()
    })
  })

  describe('Enabled/Disabled state', () => {
    it('should not trigger handlers when disabled', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 's', ctrlKey: true, handler: mockHandlers.handleSave, description: 'Save' },
      ]

      renderHook(() => useKeyboardShortcuts(shortcuts, false))

      window.dispatchEvent(new KeyboardEvent('keydown', { key: 's', ctrlKey: true }))

      expect(mockHandlers.handleSave).not.toHaveBeenCalled()
    })

    it('should trigger handlers when enabled (default)', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 's', ctrlKey: true, handler: mockHandlers.handleSave, description: 'Save' },
      ]

      renderHook(() => useKeyboardShortcuts(shortcuts))

      window.dispatchEvent(new KeyboardEvent('keydown', { key: 's', ctrlKey: true }))

      expect(mockHandlers.handleSave).toHaveBeenCalledTimes(1)
    })

    it('should re-enable shortcuts when enabled changes from false to true', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 's', ctrlKey: true, handler: mockHandlers.handleSave, description: 'Save' },
      ]

      const { rerender } = renderHook(({ enabled }) => useKeyboardShortcuts(shortcuts, enabled), {
        initialProps: { enabled: false },
      })

      window.dispatchEvent(new KeyboardEvent('keydown', { key: 's', ctrlKey: true }))
      expect(mockHandlers.handleSave).not.toHaveBeenCalled()

      rerender({ enabled: true })

      window.dispatchEvent(new KeyboardEvent('keydown', { key: 's', ctrlKey: true }))
      expect(mockHandlers.handleSave).toHaveBeenCalledTimes(1)
    })
  })

  describe('Cleanup', () => {
    it('should remove event listener on unmount', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 's', ctrlKey: true, handler: mockHandlers.handleSave, description: 'Save' },
      ]

      const { unmount } = renderHook(() => useKeyboardShortcuts(shortcuts))

      unmount()

      window.dispatchEvent(new KeyboardEvent('keydown', { key: 's', ctrlKey: true }))

      expect(mockHandlers.handleSave).not.toHaveBeenCalled()
    })
  })
})

describe('getShortcutDisplay', () => {
  it('should display single key shortcut', () => {
    const shortcut: KeyboardShortcut = {
      key: 'Escape',
      handler: () => {},
      description: 'Close',
    }

    expect(getShortcutDisplay(shortcut)).toBe('Escape')
  })

  it('should display Ctrl+key shortcut', () => {
    const shortcut: KeyboardShortcut = {
      key: 's',
      ctrlKey: true,
      handler: () => {},
      description: 'Save',
    }

    expect(getShortcutDisplay(shortcut)).toBe('Ctrl+s')
  })

  it('should display Shift+key shortcut', () => {
    const shortcut: KeyboardShortcut = {
      key: 'Tab',
      shiftKey: true,
      handler: () => {},
      description: 'Reverse tab',
    }

    expect(getShortcutDisplay(shortcut)).toBe('Shift+Tab')
  })

  it('should display Alt+key shortcut', () => {
    const shortcut: KeyboardShortcut = {
      key: 'f',
      altKey: true,
      handler: () => {},
      description: 'File menu',
    }

    expect(getShortcutDisplay(shortcut)).toBe('Alt+f')
  })

  it('should display Ctrl+Shift+key shortcut', () => {
    const shortcut: KeyboardShortcut = {
      key: 'p',
      ctrlKey: true,
      shiftKey: true,
      handler: () => {},
      description: 'Command palette',
    }

    expect(getShortcutDisplay(shortcut)).toBe('Ctrl+Shift+p')
  })

  it('should display Ctrl+Alt+key shortcut', () => {
    const shortcut: KeyboardShortcut = {
      key: 'Delete',
      ctrlKey: true,
      altKey: true,
      handler: () => {},
      description: 'Force delete',
    }

    expect(getShortcutDisplay(shortcut)).toBe('Ctrl+Alt+Delete')
  })

  it('should display Ctrl+Shift+Alt+key shortcut', () => {
    const shortcut: KeyboardShortcut = {
      key: 'f12',
      ctrlKey: true,
      shiftKey: true,
      altKey: true,
      handler: () => {},
      description: 'Debug mode',
    }

    expect(getShortcutDisplay(shortcut)).toBe('Ctrl+Shift+Alt+f12')
  })
})
