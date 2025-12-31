import { invoke } from '@tauri-apps/api/core'
import { getCurrentWindow } from '@tauri-apps/api/window'
import type React from 'react'
import { toast } from 'sonner'
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { usePhotoStore } from '@/stores/photoStore'
import { useSettingsStore } from '@/stores/settingsStore'
import type { PhotoData } from '@/types/photo'
import type { Theme, TileLayerType } from '@/types/settings'

interface MenuBarProps {
  onOpenSettings: () => void
  onOpenAbout: () => void
}

const menuTriggerClassName =
  'text-sm font-medium text-muted-foreground hover:text-foreground transition-colors data-[state=open]:text-foreground'

export function MenuBar({ onOpenSettings, onOpenAbout }: MenuBarProps): React.ReactElement {
  const {
    viewMode,
    currentPath,
    addPhotos,
    selectPhoto,
    setViewMode,
    navigateToDirectory,
    clearNavigation,
    setIsLoading,
    setLoadingStatus,
    isLoading,
  } = usePhotoStore()
  const { settings, updateSettings } = useSettingsStore()
  const hasMapboxToken = Boolean(import.meta.env.VITE_MAPBOX_TOKEN)
  const satelliteLabel = hasMapboxToken ? '衛星画像 (Mapbox)' : '衛星画像 (Mapboxキー未設定)'

  const loadPhotos = async (paths: string[]) => {
    setIsLoading(true)
    setLoadingStatus('写真データを読み込み中...')
    try {
      const results: PhotoData[] = []
      for (const path of paths) {
        try {
          const photoData = await invoke<PhotoData>('get_photo_data', { path })
          results.push(photoData)
        } catch (error) {
          toast.error('写真の読み込みに失敗しました', {
            description: String(error),
          })
        }
      }
      if (results.length > 0) {
        clearNavigation()
        addPhotos(results)
        selectPhoto(results[0]?.path ?? null)
        toast.success('写真を読み込みました', {
          description: `${results.length}件の写真を追加しました`,
        })
      }
    } finally {
      setIsLoading(false)
      setLoadingStatus('')
    }
  }

  const handleOpenFiles = async () => {
    setIsLoading(true)
    setLoadingStatus('ファイルを選択中...')
    try {
      const filePaths = await invoke<string[]>('select_photo_files')
      if (filePaths.length > 0) {
        await loadPhotos(filePaths)
      }
    } catch (error) {
      toast.error('ファイル選択に失敗しました', {
        description: String(error),
      })
    } finally {
      setIsLoading(false)
      setLoadingStatus('')
    }
  }

  const openFolder = async (folderPath: string) => {
    setIsLoading(true)
    setLoadingStatus('フォルダを読み込み中...')
    try {
      await navigateToDirectory(folderPath)
      updateSettings({ lastOpenedFolder: folderPath })
      toast.success('フォルダを開きました')
    } catch (error) {
      toast.error('フォルダの読み込みに失敗しました', {
        description: String(error),
      })
    } finally {
      setIsLoading(false)
      setLoadingStatus('')
    }
  }

  const handleOpenFolder = async () => {
    setIsLoading(true)
    setLoadingStatus('フォルダを選択中...')
    try {
      const folderPath = await invoke<string | null>('select_photo_folder')
      if (folderPath) {
        await openFolder(folderPath)
      }
    } catch (error) {
      toast.error('フォルダ選択に失敗しました', {
        description: String(error),
      })
    } finally {
      setIsLoading(false)
      setLoadingStatus('')
    }
  }

  const handleOpenLastFolder = async () => {
    if (!settings.lastOpenedFolder) {
      return
    }
    await openFolder(settings.lastOpenedFolder)
  }

  const handleExit = async () => {
    try {
      await getCurrentWindow().close()
    } catch {
      // ignore
    }
  }

  const handleThemeChange = (value: string) => {
    if (value === 'light' || value === 'dark' || value === 'system') {
      updateSettings({ ui: { ...settings.ui, theme: value as Theme } })
    }
  }

  const handleTileLayerChange = (value: string) => {
    if (value === 'satellite' && !hasMapboxToken) {
      toast.error('Mapbox APIキーが設定されていません', {
        description: '環境変数 VITE_MAPBOX_TOKEN を設定してください。',
      })
      return
    }
    if (value === 'osm' || value === 'satellite') {
      updateSettings({ map: { ...settings.map, tileLayer: value as TileLayerType } })
    }
  }

  const handleExifToggle = (checked: boolean) => {
    updateSettings({
      display: { ...settings.display, showExifByDefault: checked },
    })
  }

  return (
    <div className="flex items-center gap-4">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button type="button" className={menuTriggerClassName}>
            ファイル
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuItem onClick={handleOpenFiles} disabled={isLoading}>
            写真を開く
            <DropdownMenuShortcut>Ctrl+O</DropdownMenuShortcut>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleOpenFolder} disabled={isLoading}>
            フォルダを開く
            <DropdownMenuShortcut>Ctrl+Shift+O</DropdownMenuShortcut>
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={handleOpenLastFolder}
            disabled={!settings.lastOpenedFolder || isLoading}
          >
            最後に開いたフォルダ
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleExit}>終了</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button type="button" className={menuTriggerClassName}>
            表示
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuRadioGroup
            value={viewMode}
            onValueChange={(value) => {
              if (value === 'list' || value === 'detail' || value === 'grid') {
                setViewMode(value)
              }
            }}
          >
            <DropdownMenuRadioItem value="list">リスト表示</DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="detail">詳細表示</DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="grid">グリッド表示</DropdownMenuRadioItem>
          </DropdownMenuRadioGroup>
          {currentPath && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigateToDirectory(currentPath)}>
                フォルダを再読み込み
              </DropdownMenuItem>
            </>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>地図タイル</DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <DropdownMenuRadioGroup
                value={settings.map.tileLayer}
                onValueChange={handleTileLayerChange}
              >
                <DropdownMenuRadioItem value="osm">OpenStreetMap</DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="satellite" disabled={!hasMapboxToken}>
                  {satelliteLabel}
                </DropdownMenuRadioItem>
              </DropdownMenuRadioGroup>
            </DropdownMenuSubContent>
          </DropdownMenuSub>
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>テーマ</DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <DropdownMenuRadioGroup value={settings.ui.theme} onValueChange={handleThemeChange}>
                <DropdownMenuRadioItem value="system">システム</DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="light">ライト</DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="dark">ダーク</DropdownMenuRadioItem>
              </DropdownMenuRadioGroup>
            </DropdownMenuSubContent>
          </DropdownMenuSub>
          <DropdownMenuSeparator />
          <DropdownMenuCheckboxItem
            checked={settings.display.showExifByDefault}
            onCheckedChange={(checked) => handleExifToggle(Boolean(checked))}
          >
            EXIF情報を表示
          </DropdownMenuCheckboxItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button type="button" className={menuTriggerClassName}>
            設定
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuItem onClick={onOpenSettings}>設定を開く</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button type="button" className={menuTriggerClassName}>
            ヘルプ
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuItem onClick={onOpenAbout}>バージョン情報</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
