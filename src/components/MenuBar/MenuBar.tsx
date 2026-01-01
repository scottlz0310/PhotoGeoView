import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { getCurrentWindow } from '@tauri-apps/api/window'
import type React from 'react'
import { useCallback, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
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

const menuEvents = {
  openFiles: 'menu-open-files',
  openFolder: 'menu-open-folder',
  openLastFolder: 'menu-open-last-folder',
  reloadFolder: 'menu-reload-folder',
  viewList: 'menu-view-list',
  viewDetail: 'menu-view-detail',
  viewGrid: 'menu-view-grid',
  openSettings: 'menu-open-settings',
  openAbout: 'menu-open-about',
} as const

export function MenuBar({ onOpenSettings, onOpenAbout }: MenuBarProps): React.ReactElement {
  const { t } = useTranslation()
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
  const satelliteLabel = hasMapboxToken
    ? `${t('map.layers.satellite')} (Mapbox)`
    : `${t('map.layers.satellite')} (Mapbox Token Missing)`

  const loadPhotos = useCallback(
    async (paths: string[]) => {
      setIsLoading(true)
      setLoadingStatus(t('photoList.loading'))
      try {
        const results: PhotoData[] = []
        for (const path of paths) {
          try {
            const photoData = await invoke<PhotoData>('get_photo_data', { path })
            results.push(photoData)
          } catch (error) {
            toast.error(t('common.error'), {
              description: String(error),
            })
          }
        }
        if (results.length > 0) {
          clearNavigation()
          addPhotos(results)
          selectPhoto(results[0]?.path ?? null)
          toast.success(t('menu.openFiles'), {
            description: `${results.length} photos added`,
          })
        }
      } finally {
        setIsLoading(false)
        setLoadingStatus('')
      }
    },
    [addPhotos, clearNavigation, selectPhoto, setIsLoading, setLoadingStatus, t],
  )

  const handleOpenFiles = useCallback(async () => {
    setIsLoading(true)
    setLoadingStatus(t('common.loading'))
    try {
      const filePaths = await invoke<string[]>('select_photo_files')
      if (filePaths.length > 0) {
        await loadPhotos(filePaths)
      }
    } catch (error) {
      toast.error(t('common.error'), {
        description: String(error),
      })
    } finally {
      setIsLoading(false)
      setLoadingStatus('')
    }
  }, [loadPhotos, setIsLoading, setLoadingStatus, t])

  const openFolder = useCallback(
    async (folderPath: string) => {
      setIsLoading(true)
      setLoadingStatus(t('common.loading'))
      try {
        await navigateToDirectory(folderPath)
        updateSettings({ lastOpenedFolder: folderPath })
        toast.success(t('menu.openFolder'))
      } catch (error) {
        toast.error(t('common.error'), {
          description: String(error),
        })
      } finally {
        setIsLoading(false)
        setLoadingStatus('')
      }
    },
    [navigateToDirectory, setIsLoading, setLoadingStatus, t, updateSettings],
  )

  const handleOpenFolder = useCallback(async () => {
    setIsLoading(true)
    setLoadingStatus(t('common.loading'))
    try {
      const folderPath = await invoke<string | null>('select_photo_folder')
      if (folderPath) {
        await openFolder(folderPath)
      }
    } catch (error) {
      toast.error(t('common.error'), {
        description: String(error),
      })
    } finally {
      setIsLoading(false)
      setLoadingStatus('')
    }
  }, [openFolder, setIsLoading, setLoadingStatus, t])

  const handleOpenLastFolder = useCallback(async () => {
    if (!settings.lastOpenedFolder) {
      return
    }
    await openFolder(settings.lastOpenedFolder)
  }, [openFolder, settings.lastOpenedFolder])

  const handleReloadFolder = useCallback(() => {
    if (!currentPath) {
      return
    }
    navigateToDirectory(currentPath).catch((error) => {
      toast.error(t('common.error'), {
        description: String(error),
      })
    })
  }, [currentPath, navigateToDirectory, t])

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
      toast.error('Mapbox API Token Missing', {
        description: 'Please set VITE_MAPBOX_TOKEN environment variable.',
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

  useEffect(() => {
    const unlisteners: Array<() => void> = []

    const register = async () => {
      unlisteners.push(await listen(menuEvents.openFiles, () => handleOpenFiles()))
      unlisteners.push(await listen(menuEvents.openFolder, () => handleOpenFolder()))
      unlisteners.push(await listen(menuEvents.openLastFolder, () => handleOpenLastFolder()))
      unlisteners.push(await listen(menuEvents.reloadFolder, () => handleReloadFolder()))
      unlisteners.push(await listen(menuEvents.viewList, () => setViewMode('list')))
      unlisteners.push(await listen(menuEvents.viewDetail, () => setViewMode('detail')))
      unlisteners.push(await listen(menuEvents.viewGrid, () => setViewMode('grid')))
      unlisteners.push(await listen(menuEvents.openSettings, () => onOpenSettings()))
      unlisteners.push(await listen(menuEvents.openAbout, () => onOpenAbout()))
    }

    register().catch((_error) => {
      // メニュー登録エラーは無視
    })

    return () => {
      for (const unlisten of unlisteners) {
        unlisten()
      }
    }
  }, [
    handleOpenFiles,
    handleOpenFolder,
    handleOpenLastFolder,
    handleReloadFolder,
    onOpenAbout,
    onOpenSettings,
    setViewMode,
  ])

  return (
    <div className="flex items-center gap-4">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button type="button" className={menuTriggerClassName}>
            {t('menu.file')}
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuItem onClick={handleOpenFiles} disabled={isLoading}>
            {t('menu.openFiles')}
            <DropdownMenuShortcut>Ctrl+O</DropdownMenuShortcut>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleOpenFolder} disabled={isLoading}>
            {t('menu.openFolder')}
            <DropdownMenuShortcut>Ctrl+Shift+O</DropdownMenuShortcut>
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={handleOpenLastFolder}
            disabled={!settings.lastOpenedFolder || isLoading}
          >
            {t('menu.openLastFolder')}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleExit}>{t('menu.exit')}</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button type="button" className={menuTriggerClassName}>
            {t('menu.view')}
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
            <DropdownMenuRadioItem value="list">
              {t('photoList.viewMode.list')}
            </DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="detail">
              {t('photoList.viewMode.detail')}
            </DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="grid">
              {t('photoList.viewMode.grid')}
            </DropdownMenuRadioItem>
          </DropdownMenuRadioGroup>
          {currentPath && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleReloadFolder}>
                {t('menu.reloadFolder')}
              </DropdownMenuItem>
            </>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>{t('menu.mapTiles')}</DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <DropdownMenuRadioGroup
                value={settings.map.tileLayer}
                onValueChange={handleTileLayerChange}
              >
                <DropdownMenuRadioItem value="osm">{t('map.layers.osm')}</DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="satellite" disabled={!hasMapboxToken}>
                  {satelliteLabel}
                </DropdownMenuRadioItem>
              </DropdownMenuRadioGroup>
            </DropdownMenuSubContent>
          </DropdownMenuSub>
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>{t('menu.theme')}</DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <DropdownMenuRadioGroup value={settings.ui.theme} onValueChange={handleThemeChange}>
                <DropdownMenuRadioItem value="system">
                  {t('settings.themes.system')}
                </DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="light">
                  {t('settings.themes.light')}
                </DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="dark">
                  {t('settings.themes.dark')}
                </DropdownMenuRadioItem>
              </DropdownMenuRadioGroup>
            </DropdownMenuSubContent>
          </DropdownMenuSub>
          <DropdownMenuSeparator />
          <DropdownMenuCheckboxItem
            checked={settings.display.showExifByDefault}
            onCheckedChange={(checked) => handleExifToggle(Boolean(checked))}
          >
            {t('settings.display.showExif')}
          </DropdownMenuCheckboxItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button type="button" className={menuTriggerClassName}>
            {t('menu.settings')}
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuItem onClick={onOpenSettings}>{t('menu.settings')}</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button type="button" className={menuTriggerClassName}>
            {t('menu.help')}
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuItem onClick={onOpenAbout}>{t('menu.version')}</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
