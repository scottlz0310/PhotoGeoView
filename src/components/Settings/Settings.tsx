import { ChevronDown } from 'lucide-react'
import type React from 'react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import type { ViewMode } from '@/stores/photoStore'
import { useSettingsStore } from '@/stores/settingsStore'
import type { Language, Theme, TileLayerType } from '@/types/settings'

interface SettingsProps {
  isOpen: boolean
  onClose: () => void
}

interface SelectOption<T extends string> {
  value: T
  label: string
}

interface SelectFieldProps<T extends string> {
  id: string
  label: string
  value: T
  options: SelectOption<T>[]
  onChange: (value: T) => void
}

function SelectField<T extends string>({
  id,
  label,
  value,
  options,
  onChange,
}: SelectFieldProps<T>): React.ReactElement {
  const labelId = `${id}-label`
  const selectedLabel = options.find((option) => option.value === value)?.label ?? value

  return (
    <div>
      <label id={labelId} htmlFor={id} className="mb-1 block text-sm font-medium text-foreground">
        {label}
      </label>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            id={id}
            type="button"
            variant="outline"
            className="w-full justify-between"
            aria-labelledby={labelId}
          >
            <span className="truncate">{selectedLabel}</span>
            <ChevronDown className="h-4 w-4 opacity-70" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="start"
          style={{ width: 'var(--radix-dropdown-menu-trigger-width)' }}
        >
          <DropdownMenuRadioGroup
            value={value}
            onValueChange={(nextValue) => onChange(nextValue as T)}
          >
            {options.map((option) => (
              <DropdownMenuRadioItem key={option.value} value={option.value}>
                {option.label}
              </DropdownMenuRadioItem>
            ))}
          </DropdownMenuRadioGroup>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}

export function Settings({ isOpen, onClose }: SettingsProps): React.ReactElement | null {
  const { t } = useTranslation()
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
    if (window.confirm(`${t('common.reset')}?`)) {
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
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-md"
      style={{
        // biome-ignore lint/style/useNamingConvention: WebKit prefix required for browser compatibility
        WebkitBackdropFilter: 'blur(12px)',
      }}
      onClick={handleCancel}
      onKeyDown={handleOverlayKeyDown}
      role="button"
      tabIndex={-1}
      aria-label={t('common.close')}
    >
      <div
        className="w-full max-w-2xl rounded-xl p-6 bg-card text-card-foreground border border-border shadow-2xl"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="settings-title"
      >
        {/* ヘッダー */}
        <div className="mb-6 flex items-center justify-between border-b border-border pb-4">
          <h2 id="settings-title" className="text-xl font-bold text-card-foreground">
            {t('settings.title')}
          </h2>
          <button
            type="button"
            onClick={handleCancel}
            className="text-muted-foreground hover:text-foreground"
            aria-label={t('common.close')}
          >
            ✕
          </button>
        </div>

        {/* 設定項目 */}
        <div className="space-y-6 overflow-y-auto" style={{ maxHeight: '60vh' }}>
          {/* 表示設定 */}
          <section>
            <h3 className="mb-3 text-lg font-semibold text-card-foreground">
              {t('settings.sections.display')}
            </h3>
            <div className="space-y-3">
              {/* デフォルトビューモード */}
              <SelectField<ViewMode>
                id="default-view-mode"
                label={t('settings.display.defaultViewMode')}
                value={localSettings.display.defaultViewMode}
                options={[
                  { value: 'list', label: t('photoList.viewMode.list') },
                  { value: 'detail', label: t('photoList.viewMode.detail') },
                  { value: 'grid', label: t('photoList.viewMode.grid') },
                ]}
                onChange={(value) => {
                  setLocalSettings({
                    ...localSettings,
                    display: {
                      ...localSettings.display,
                      defaultViewMode: value,
                    },
                  })
                  setHasChanges(true)
                }}
              />

              {/* グリッド列数 */}
              <div>
                <label
                  htmlFor="grid-columns"
                  className="mb-1 block text-sm font-medium text-foreground"
                >
                  {t('settings.display.gridColumns')}
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
                  {t('settings.display.showExif')}
                </label>
              </div>
            </div>
          </section>

          {/* 地図設定 */}
          <section>
            <h3 className="mb-3 text-lg font-semibold text-card-foreground">
              {t('settings.sections.map')}
            </h3>
            <div className="space-y-3">
              {/* デフォルトズーム */}
              <div>
                <label
                  htmlFor="default-zoom"
                  className="mb-1 block text-sm font-medium text-foreground"
                >
                  {t('settings.map.defaultZoom')} (1-18)
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
              <SelectField<TileLayerType>
                id="tile-layer"
                label={t('settings.map.tileLayer')}
                value={localSettings.map.tileLayer}
                options={[
                  { value: 'osm', label: t('map.layers.osm') },
                  { value: 'satellite', label: t('map.layers.satellite') },
                ]}
                onChange={(value) => {
                  setLocalSettings({
                    ...localSettings,
                    map: {
                      ...localSettings.map,
                      tileLayer: value,
                    },
                  })
                  setHasChanges(true)
                }}
              />

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
                  {t('settings.map.enableClustering')}
                </label>
              </div>
            </div>
          </section>

          {/* UI設定 */}
          <section>
            <h3 className="mb-3 text-lg font-semibold text-card-foreground">
              {t('settings.sections.ui')}
            </h3>
            <div className="space-y-3">
              {/* テーマ */}
              <SelectField<Theme>
                id="theme"
                label={t('settings.ui.theme')}
                value={localSettings.ui.theme}
                options={[
                  { value: 'light', label: t('settings.themes.light') },
                  { value: 'dark', label: t('settings.themes.dark') },
                  { value: 'system', label: t('settings.themes.system') },
                ]}
                onChange={(value) => {
                  setLocalSettings({
                    ...localSettings,
                    ui: {
                      ...localSettings.ui,
                      theme: value,
                    },
                  })
                  setHasChanges(true)
                }}
              />

              {/* 言語 */}
              <SelectField<Language>
                id="language"
                label={t('settings.ui.language')}
                value={localSettings.ui.language}
                options={[
                  { value: 'ja', label: t('settings.languages.ja') },
                  { value: 'en', label: t('settings.languages.en') },
                ]}
                onChange={(value) => {
                  setLocalSettings({
                    ...localSettings,
                    ui: {
                      ...localSettings.ui,
                      language: value,
                    },
                  })
                  setHasChanges(true)
                }}
              />
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
            {t('common.reset')}
          </button>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleCancel}
              className="rounded border border-border bg-background px-4 py-2 text-sm text-foreground hover:bg-muted"
            >
              {t('common.cancel')}
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={!hasChanges}
              className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {t('common.save')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
