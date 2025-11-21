import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@renderer/components/ui/dialog'
import { KeyboardShortcutsHelp } from '@renderer/components/ui/keyboard-hint'
import {
  Menubar,
  MenubarCheckboxItem,
  MenubarContent,
  MenubarItem,
  MenubarMenu,
  MenubarSeparator,
  MenubarShortcut,
  MenubarSub,
  MenubarSubContent,
  MenubarSubTrigger,
  MenubarTrigger,
} from '@renderer/components/ui/menubar'
import { useAppStore } from '@renderer/stores/appStore'
import i18n from 'i18next'
import { useTheme } from 'next-themes'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'

export function MenuBar() {
  const { t } = useTranslation()
  const {
    panelVisibility,
    togglePanel,
    statusBarItems,
    toggleStatusBarItem,
    layoutPreset,
    setLayoutPreset,
    language,
    setLanguage,
    navigateToPath,
    clearSelectedFiles,
  } = useAppStore()
  const { theme, setTheme } = useTheme()
  const [showShortcuts, setShowShortcuts] = useState(false)
  const [showAbout, setShowAbout] = useState(false)

  // biome-ignore lint/suspicious/noExplicitAny: Electron API
  const api = (window as any).api

  const handleOpenFolder = async () => {
    if (!api) return
    try {
      const result = await api.selectDirectory()
      if (result.success && result.data) {
        navigateToPath(result.data)
        clearSelectedFiles()
        toast.success('Folder Opened', {
          description: `Opened: ${result.data}`,
        })
      }
    } catch (error) {
      toast.error('Error', {
        description: error instanceof Error ? error.message : 'Failed to open folder',
      })
    }
  }

  const handleExit = () => {
    if (api) {
      api.closeWindow()
    }
  }

  const handleCheckUpdate = async () => {
    if (api) {
      await api.checkForUpdates()
    }
  }

  const handleLanguageChange = (lang: 'en' | 'ja') => {
    setLanguage(lang)
    i18n.changeLanguage(lang)
  }

  return (
    <>
      <Menubar className="border-none bg-transparent">
        {/* File Menu */}
        <MenubarMenu>
          <MenubarTrigger>{t('menu.file')}</MenubarTrigger>
          <MenubarContent>
            <MenubarItem onClick={handleOpenFolder}>
              {t('menu.openFolder')}
              <MenubarShortcut>Ctrl+O</MenubarShortcut>
            </MenubarItem>
            <MenubarSeparator />
            <MenubarItem onClick={handleExit}>
              {t('menu.exit')}
              <MenubarShortcut>Alt+F4</MenubarShortcut>
            </MenubarItem>
          </MenubarContent>
        </MenubarMenu>

        {/* View Menu */}
        <MenubarMenu>
          <MenubarTrigger>{t('menu.view')}</MenubarTrigger>
          <MenubarContent>
            <MenubarSub>
              <MenubarSubTrigger>{t('menu.theme')}</MenubarSubTrigger>
              <MenubarSubContent>
                <MenubarCheckboxItem checked={theme === 'light'} onClick={() => setTheme('light')}>
                  {t('menu.light')}
                </MenubarCheckboxItem>
                <MenubarCheckboxItem checked={theme === 'dark'} onClick={() => setTheme('dark')}>
                  {t('menu.dark')}
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={theme === 'system'}
                  onClick={() => setTheme('system')}
                >
                  {t('menu.system')}
                </MenubarCheckboxItem>
              </MenubarSubContent>
            </MenubarSub>
            <MenubarSeparator />
            <MenubarSub>
              <MenubarSubTrigger>{t('menu.panels')}</MenubarSubTrigger>
              <MenubarSubContent>
                <MenubarCheckboxItem
                  checked={panelVisibility.fileBrowser}
                  onClick={() => togglePanel('fileBrowser')}
                >
                  {t('menu.fileBrowser')}
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={panelVisibility.thumbnailGrid}
                  onClick={() => togglePanel('thumbnailGrid')}
                >
                  {t('menu.thumbnailGrid')}
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={panelVisibility.exifPanel}
                  onClick={() => togglePanel('exifPanel')}
                >
                  {t('menu.exifPanel')}
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={panelVisibility.imagePreview}
                  onClick={() => togglePanel('imagePreview')}
                >
                  {t('menu.imagePreview')}
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={panelVisibility.mapView}
                  onClick={() => togglePanel('mapView')}
                >
                  {t('menu.mapView')}
                </MenubarCheckboxItem>
              </MenubarSubContent>
            </MenubarSub>
            <MenubarSeparator />
            <MenubarSub>
              <MenubarSubTrigger>{t('menu.statusBarInfo')}</MenubarSubTrigger>
              <MenubarSubContent>
                <MenubarCheckboxItem
                  checked={statusBarItems.camera}
                  onClick={() => toggleStatusBarItem('camera')}
                >
                  {t('menu.camera')}
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={statusBarItems.exposure}
                  onClick={() => toggleStatusBarItem('exposure')}
                >
                  {t('menu.exposure')}
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={statusBarItems.gps}
                  onClick={() => toggleStatusBarItem('gps')}
                >
                  {t('menu.gps')}
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={statusBarItems.datetime}
                  onClick={() => toggleStatusBarItem('datetime')}
                >
                  {t('menu.datetime')}
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={statusBarItems.dimensions}
                  onClick={() => toggleStatusBarItem('dimensions')}
                >
                  {t('menu.dimensions')}
                </MenubarCheckboxItem>
              </MenubarSubContent>
            </MenubarSub>
          </MenubarContent>
        </MenubarMenu>

        {/* Settings Menu */}
        <MenubarMenu>
          <MenubarTrigger>{t('menu.settings')}</MenubarTrigger>
          <MenubarContent>
            <MenubarSub>
              <MenubarSubTrigger>{t('menu.layout')}</MenubarSubTrigger>
              <MenubarSubContent>
                <MenubarCheckboxItem
                  checked={layoutPreset === 'default'}
                  onClick={() => setLayoutPreset('default')}
                >
                  {t('menu.layoutDefault')}
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={layoutPreset === 'preview-focus'}
                  onClick={() => setLayoutPreset('preview-focus')}
                >
                  {t('menu.layoutPreviewFocus')}
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={layoutPreset === 'map-focus'}
                  onClick={() => setLayoutPreset('map-focus')}
                >
                  {t('menu.layoutMapFocus')}
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={layoutPreset === 'compact'}
                  onClick={() => setLayoutPreset('compact')}
                >
                  {t('menu.layoutCompact')}
                </MenubarCheckboxItem>
              </MenubarSubContent>
            </MenubarSub>
            <MenubarSeparator />
            <MenubarSub>
              <MenubarSubTrigger>Language / 言語</MenubarSubTrigger>
              <MenubarSubContent>
                <MenubarCheckboxItem
                  checked={language === 'en'}
                  onClick={() => handleLanguageChange('en')}
                >
                  English
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={language === 'ja'}
                  onClick={() => handleLanguageChange('ja')}
                >
                  日本語
                </MenubarCheckboxItem>
              </MenubarSubContent>
            </MenubarSub>
          </MenubarContent>
        </MenubarMenu>

        {/* Help Menu */}
        <MenubarMenu>
          <MenubarTrigger>{t('menu.help')}</MenubarTrigger>
          <MenubarContent>
            <MenubarItem onClick={() => setShowShortcuts(true)}>
              {t('menu.keyboardShortcuts')}
              <MenubarShortcut>?</MenubarShortcut>
            </MenubarItem>
            <MenubarSeparator />
            <MenubarItem onClick={handleCheckUpdate}>{t('menu.checkForUpdates')}</MenubarItem>
            <MenubarSeparator />
            <MenubarItem onClick={() => setShowAbout(true)}>{t('menu.about')}</MenubarItem>
          </MenubarContent>
        </MenubarMenu>
      </Menubar>

      {/* Shortcuts Dialog */}
      <Dialog open={showShortcuts} onOpenChange={setShowShortcuts}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('dialog.shortcuts')}</DialogTitle>
          </DialogHeader>
          <KeyboardShortcutsHelp />
        </DialogContent>
      </Dialog>

      {/* About Dialog */}
      <Dialog open={showAbout} onOpenChange={setShowAbout}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('dialog.aboutTitle')}</DialogTitle>
            <DialogDescription>{t('dialog.aboutDesc')}</DialogDescription>
          </DialogHeader>
          <div className="space-y-2 text-sm">
            <p>
              <strong>{t('dialog.version')}:</strong> 2.1.0
            </p>
            <p className="text-muted-foreground">{t('dialog.aboutDesc')}</p>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
