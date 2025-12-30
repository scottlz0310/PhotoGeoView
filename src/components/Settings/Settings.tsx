import type React from 'react'
import { useEffect, useState } from 'react'
import type { ViewMode } from '@/stores/photoStore'
import { useSettingsStore } from '@/stores/settingsStore'
import type { Language, Theme, TileLayerType } from '@/types/settings'

interface SettingsProps {
  isOpen: boolean
  onClose: () => void
}

export function Settings({ isOpen, onClose }: SettingsProps): React.ReactElement | null {
  const { settings, updateSettings, resetSettings } = useSettingsStore()
  const [hasChanges, setHasChanges] = useState(false)

  // ローカル状態（編集中の設定）
  const [localSettings, setLocalSettings] = useState(settings)

  // ダイアログが開いた時に現在の設定を同期
  useEffect(() => {
    if (isOpen) {
      setLocalSettings(settings)
      setHasChanges(false)
    }
  }, [isOpen, settings])

  if (!isOpen) {
    return null
  }

  const handleSave = async () => {
    try {
      await updateSettings(localSettings)
      setHasChanges(false)
      onClose()
    } catch {
      // エラーハンドリングは上位層で行う
    }
  }

  const handleReset = async () => {
    if (window.confirm('すべての設定をデフォルトに戻しますか？')) {
      await resetSettings()
      setLocalSettings(settings)
      setHasChanges(false)
    }
  }

  const handleCancel = () => {
    setLocalSettings(settings)
    setHasChanges(false)
    onClose()
  }

  const handleOverlayKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleCancel()
    }
  }

  return (
    // biome-ignore lint/a11y/useSemanticElements: Overlay backdrop must be a div for proper full-screen styling
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{
        background: 'rgba(255, 255, 255, 0.85)',
        backdropFilter: 'blur(12px)',
        // biome-ignore lint/style/useNamingConvention: WebKit prefix required for browser compatibility
        WebkitBackdropFilter: 'blur(12px)',
      }}
      onClick={handleCancel}
      onKeyDown={handleOverlayKeyDown}
      role="button"
      tabIndex={-1}
      aria-label="設定を閉じる"
    >
      <div
        className="w-full max-w-2xl rounded-xl p-6"
        style={{
          background: '#ffffff',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.2)',
          border: '1px solid rgba(0, 0, 0, 0.1)',
        }}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="settings-title"
      >
        {/* ヘッダー */}
        <div className="mb-6 flex items-center justify-between border-b border-border pb-4">
          <h2 id="settings-title" className="text-xl font-bold text-card-foreground">
            設定
          </h2>
          <button
            type="button"
            onClick={handleCancel}
            className="text-muted-foreground hover:text-foreground"
            aria-label="閉じる"
          >
            ✕
          </button>
        </div>

        {/* 設定項目 */}
        <div className="space-y-6 overflow-y-auto" style={{ maxHeight: '60vh' }}>
          {/* 表示設定 */}
          <section>
            <h3 className="mb-3 text-lg font-semibold text-card-foreground">表示設定</h3>
            <div className="space-y-3">
              {/* デフォルトビューモード */}
              <div>
                <label
                  htmlFor="default-view-mode"
                  className="mb-1 block text-sm font-medium text-foreground"
                >
                  デフォルトビューモード
                </label>
                <select
                  id="default-view-mode"
                  value={localSettings.display.defaultViewMode}
                  onChange={(e) => {
                    setLocalSettings({
                      ...localSettings,
                      display: {
                        ...localSettings.display,
                        defaultViewMode: e.target.value as ViewMode,
                      },
                    })
                    setHasChanges(true)
                  }}
                  className="w-full rounded border border-border bg-background px-3 py-2 text-sm text-foreground"
                >
                  <option value="list">リスト表示</option>
                  <option value="detail">詳細表示</option>
                  <option value="grid">グリッド表示</option>
                </select>
              </div>

              {/* グリッド列数 */}
              <div>
                <label
                  htmlFor="grid-columns"
                  className="mb-1 block text-sm font-medium text-foreground"
                >
                  グリッド表示の列数
                </label>
                <input
                  id="grid-columns"
                  type="number"
                  min="1"
                  max="6"
                  value={localSettings.display.gridColumns}
                  onChange={(e) => {
                    setLocalSettings({
                      ...localSettings,
                      display: {
                        ...localSettings.display,
                        gridColumns: Number.parseInt(e.target.value, 10),
                      },
                    })
                    setHasChanges(true)
                  }}
                  className="w-full rounded border border-border bg-background px-3 py-2 text-sm text-foreground"
                />
              </div>

              {/* EXIF表示 */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="showExif"
                  checked={localSettings.display.showExifByDefault}
                  onChange={(e) => {
                    setLocalSettings({
                      ...localSettings,
                      display: {
                        ...localSettings.display,
                        showExifByDefault: e.target.checked,
                      },
                    })
                    setHasChanges(true)
                  }}
                  className="mr-2"
                />
                <label htmlFor="showExif" className="text-sm text-foreground">
                  EXIF情報を常に表示
                </label>
              </div>
            </div>
          </section>

          {/* 地図設定 */}
          <section>
            <h3 className="mb-3 text-lg font-semibold text-card-foreground">地図設定</h3>
            <div className="space-y-3">
              {/* デフォルトズーム */}
              <div>
                <label
                  htmlFor="default-zoom"
                  className="mb-1 block text-sm font-medium text-foreground"
                >
                  デフォルトズームレベル (1-18)
                </label>
                <input
                  id="default-zoom"
                  type="number"
                  min="1"
                  max="18"
                  value={localSettings.map.defaultZoom}
                  onChange={(e) => {
                    setLocalSettings({
                      ...localSettings,
                      map: {
                        ...localSettings.map,
                        defaultZoom: Number.parseInt(e.target.value, 10),
                      },
                    })
                    setHasChanges(true)
                  }}
                  className="w-full rounded border border-border bg-background px-3 py-2 text-sm text-foreground"
                />
              </div>

              {/* タイルレイヤー */}
              <div>
                <label
                  htmlFor="tile-layer"
                  className="mb-1 block text-sm font-medium text-foreground"
                >
                  地図タイルレイヤー
                </label>
                <select
                  id="tile-layer"
                  value={localSettings.map.tileLayer}
                  onChange={(e) => {
                    setLocalSettings({
                      ...localSettings,
                      map: {
                        ...localSettings.map,
                        tileLayer: e.target.value as TileLayerType,
                      },
                    })
                    setHasChanges(true)
                  }}
                  className="w-full rounded border border-border bg-background px-3 py-2 text-sm text-foreground"
                >
                  <option value="osm">OpenStreetMap</option>
                  <option value="satellite">衛星画像</option>
                </select>
              </div>

              {/* クラスタリング */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="clustering"
                  checked={localSettings.map.enableClustering}
                  onChange={(e) => {
                    setLocalSettings({
                      ...localSettings,
                      map: {
                        ...localSettings.map,
                        enableClustering: e.target.checked,
                      },
                    })
                    setHasChanges(true)
                  }}
                  className="mr-2"
                />
                <label htmlFor="clustering" className="text-sm text-foreground">
                  マーカークラスタリングを有効化
                </label>
              </div>
            </div>
          </section>

          {/* UI設定 */}
          <section>
            <h3 className="mb-3 text-lg font-semibold text-card-foreground">UI設定</h3>
            <div className="space-y-3">
              {/* テーマ */}
              <div>
                <label htmlFor="theme" className="mb-1 block text-sm font-medium text-foreground">
                  テーマ
                </label>
                <select
                  id="theme"
                  value={localSettings.ui.theme}
                  onChange={(e) => {
                    setLocalSettings({
                      ...localSettings,
                      ui: {
                        ...localSettings.ui,
                        theme: e.target.value as Theme,
                      },
                    })
                    setHasChanges(true)
                  }}
                  className="w-full rounded border border-border bg-background px-3 py-2 text-sm text-foreground"
                >
                  <option value="light">ライト</option>
                  <option value="dark">ダーク</option>
                  <option value="system">システムに従う</option>
                </select>
              </div>

              {/* 言語 */}
              <div>
                <label
                  htmlFor="language"
                  className="mb-1 block text-sm font-medium text-foreground"
                >
                  言語
                </label>
                <select
                  id="language"
                  value={localSettings.ui.language}
                  onChange={(e) => {
                    setLocalSettings({
                      ...localSettings,
                      ui: {
                        ...localSettings.ui,
                        language: e.target.value as Language,
                      },
                    })
                    setHasChanges(true)
                  }}
                  className="w-full rounded border border-border bg-background px-3 py-2 text-sm text-foreground"
                >
                  <option value="ja">日本語</option>
                  <option value="en">English</option>
                </select>
              </div>
            </div>
          </section>
        </div>

        {/* フッター（ボタン） */}
        <div className="mt-6 flex justify-between border-t border-border pt-4">
          <button
            type="button"
            onClick={handleReset}
            className="rounded bg-muted px-4 py-2 text-sm text-muted-foreground hover:bg-muted/80"
          >
            デフォルトに戻す
          </button>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleCancel}
              className="rounded border border-border bg-background px-4 py-2 text-sm text-foreground hover:bg-muted"
            >
              キャンセル
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={!hasChanges}
              className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              保存
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
