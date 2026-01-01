import { act } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DEFAULT_SETTINGS } from '../types/settings'
import { useSettingsStore } from './settingsStore'

// モックのセットアップ
const { mockStore } = vi.hoisted(() => ({
  mockStore: {
    get: vi.fn(),
    set: vi.fn(),
    save: vi.fn(),
    clear: vi.fn(),
  },
}))

vi.mock('@tauri-apps/plugin-store', () => ({
  // biome-ignore lint/style/useNamingConvention: Mocking external library
  Store: {
    load: vi.fn().mockResolvedValue(mockStore),
  },
}))

vi.mock('@/i18n', () => ({
  default: {
    changeLanguage: vi.fn(),
  },
}))

describe('settingsStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockStore.get.mockReset()
    mockStore.set.mockReset()
    mockStore.save.mockReset()
    mockStore.clear.mockReset()

    act(() => {
      useSettingsStore.setState({
        settings: DEFAULT_SETTINGS,
        isLoaded: false,
      })
    })
  })

  it('should initialize with default settings', () => {
    const state = useSettingsStore.getState()
    expect(state.settings).toEqual(DEFAULT_SETTINGS)
    expect(state.isLoaded).toBe(false)
  })

  it('should load settings from store', async () => {
    // モックの戻り値を設定
    mockStore.get.mockImplementation((key) => {
      if (key === 'display') {
        return Promise.resolve({ defaultViewMode: 'grid' })
      }
      if (key === 'ui') {
        return Promise.resolve({ theme: 'dark' })
      }
      return Promise.resolve(null)
    })

    await act(async () => {
      await useSettingsStore.getState().loadSettings()
    })

    const state = useSettingsStore.getState()
    expect(state.isLoaded).toBe(true)
    expect(state.settings.display.defaultViewMode).toBe('grid')
    expect(state.settings.ui.theme).toBe('dark')
    // マージされたデフォルト値
    expect(state.settings.map.defaultZoom).toBe(DEFAULT_SETTINGS.map.defaultZoom)
  })

  it('should handle load error gracefully', async () => {
    // エラーを発生させる
    const { Store } = await import('@tauri-apps/plugin-store')
    vi.mocked(Store.load).mockRejectedValueOnce(new Error('Load failed'))

    await act(async () => {
      await useSettingsStore.getState().loadSettings()
    })

    const state = useSettingsStore.getState()
    expect(state.isLoaded).toBe(true)
    expect(state.settings).toEqual(DEFAULT_SETTINGS)
  })

  it('should update settings', async () => {
    await act(async () => {
      await useSettingsStore.getState().updateSettings({
        display: { ...DEFAULT_SETTINGS.display, defaultViewMode: 'detail' },
      })
    })

    const state = useSettingsStore.getState()
    expect(state.settings.display.defaultViewMode).toBe('detail')
    expect(mockStore.set).toHaveBeenCalledWith(
      'display',
      expect.objectContaining({ defaultViewMode: 'detail' }),
    )
    expect(mockStore.save).toHaveBeenCalled()
  })

  it('should reset settings', async () => {
    // まず設定を変更
    await act(async () => {
      await useSettingsStore.getState().updateSettings({
        display: { ...DEFAULT_SETTINGS.display, defaultViewMode: 'detail' },
      })
    })

    // リセット
    await act(async () => {
      await useSettingsStore.getState().resetSettings()
    })

    const state = useSettingsStore.getState()
    expect(state.settings).toEqual(DEFAULT_SETTINGS)
    expect(mockStore.clear).toHaveBeenCalled()
    expect(mockStore.save).toHaveBeenCalled()
  })
})
