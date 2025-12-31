import { Store } from '@tauri-apps/plugin-store'
import { create } from 'zustand'
import i18n from '@/i18n'
import { type AppSettings, DEFAULT_SETTINGS } from '@/types/settings'

interface SettingsState {
  // 設定データ
  settings: AppSettings
  // 初期化完了フラグ
  isLoaded: boolean

  // アクション
  loadSettings: () => Promise<void>
  updateSettings: (updates: Partial<AppSettings>) => Promise<void>
  resetSettings: () => Promise<void>
}

// Tauri Store インスタンス
let store: Store | null = null

// Store の初期化（遅延初期化）
async function getStore(): Promise<Store> {
  if (!store) {
    store = await Store.load('settings.json')
  }
  return store
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  settings: DEFAULT_SETTINGS,
  isLoaded: false,

  // 設定を読み込む
  loadSettings: async () => {
    try {
      const store = await getStore()

      // 各設定項目を読み込む
      const display = await store.get<AppSettings['display']>('display')
      const map = await store.get<AppSettings['map']>('map')
      const ui = await store.get<AppSettings['ui']>('ui')
      const lastOpenedFolder = await store.get<string | null>('lastOpenedFolder')
      const version = await store.get<number>('version')

      // 読み込んだ設定をマージ（存在しない項目はデフォルト値を使用）
      const loadedSettings: AppSettings = {
        display: display ?? DEFAULT_SETTINGS.display,
        map: map ?? DEFAULT_SETTINGS.map,
        ui: ui ?? DEFAULT_SETTINGS.ui,
        lastOpenedFolder: lastOpenedFolder ?? DEFAULT_SETTINGS.lastOpenedFolder,
        version: version ?? DEFAULT_SETTINGS.version,
      }

      // 言語設定を適用
      if (loadedSettings.ui.language) {
        i18n.changeLanguage(loadedSettings.ui.language)
      }

      set({ settings: loadedSettings, isLoaded: true })
    } catch (_error) {
      // エラー時はデフォルト設定を使用
      set({ settings: DEFAULT_SETTINGS, isLoaded: true })
    }
  },

  // 設定を更新
  updateSettings: async (updates: Partial<AppSettings>) => {
    const store = await getStore()
    const currentSettings = get().settings

    // 設定をマージ
    const newSettings: AppSettings = {
      ...currentSettings,
      ...updates,
      // ネストされたオブジェクトも正しくマージ
      display: { ...currentSettings.display, ...updates.display },
      map: { ...currentSettings.map, ...updates.map },
      ui: { ...currentSettings.ui, ...updates.ui },
    }

    // 言語設定が変更された場合は適用
    if (newSettings.ui.language !== currentSettings.ui.language) {
      i18n.changeLanguage(newSettings.ui.language)
    }

    // Store に保存
    await store.set('display', newSettings.display)
    await store.set('map', newSettings.map)
    await store.set('ui', newSettings.ui)
    await store.set('lastOpenedFolder', newSettings.lastOpenedFolder)
    await store.set('version', newSettings.version)
    await store.save()

    // 状態を更新
    set({ settings: newSettings })
  },

  // 設定をリセット
  resetSettings: async () => {
    const store = await getStore()

    // すべての設定をクリア
    await store.clear()
    await store.save()

    // デフォルト設定に戻す
    set({ settings: DEFAULT_SETTINGS })
  },
}))
