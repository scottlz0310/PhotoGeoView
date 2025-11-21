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
import { useTheme } from 'next-themes'
import { useState } from 'react'
import { toast } from 'sonner'

export function MenuBar() {
  const { panelVisibility, togglePanel, navigateToPath, clearSelectedFiles } = useAppStore()
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

  return (
    <>
      <Menubar className="border-none bg-transparent">
        {/* File Menu */}
        <MenubarMenu>
          <MenubarTrigger>File</MenubarTrigger>
          <MenubarContent>
            <MenubarItem onClick={handleOpenFolder}>
              Open Folder
              <MenubarShortcut>Ctrl+O</MenubarShortcut>
            </MenubarItem>
            <MenubarSeparator />
            <MenubarItem onClick={handleExit}>
              Exit
              <MenubarShortcut>Alt+F4</MenubarShortcut>
            </MenubarItem>
          </MenubarContent>
        </MenubarMenu>

        {/* View Menu */}
        <MenubarMenu>
          <MenubarTrigger>View</MenubarTrigger>
          <MenubarContent>
            <MenubarSub>
              <MenubarSubTrigger>Theme</MenubarSubTrigger>
              <MenubarSubContent>
                <MenubarCheckboxItem checked={theme === 'light'} onClick={() => setTheme('light')}>
                  Light
                </MenubarCheckboxItem>
                <MenubarCheckboxItem checked={theme === 'dark'} onClick={() => setTheme('dark')}>
                  Dark
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={theme === 'system'}
                  onClick={() => setTheme('system')}
                >
                  System
                </MenubarCheckboxItem>
              </MenubarSubContent>
            </MenubarSub>
            <MenubarSeparator />
            <MenubarSub>
              <MenubarSubTrigger>Panels</MenubarSubTrigger>
              <MenubarSubContent>
                <MenubarCheckboxItem
                  checked={panelVisibility.fileBrowser}
                  onClick={() => togglePanel('fileBrowser')}
                >
                  File Browser
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={panelVisibility.thumbnailGrid}
                  onClick={() => togglePanel('thumbnailGrid')}
                >
                  Thumbnail Grid
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={panelVisibility.exifPanel}
                  onClick={() => togglePanel('exifPanel')}
                >
                  EXIF Panel
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={panelVisibility.imagePreview}
                  onClick={() => togglePanel('imagePreview')}
                >
                  Image Preview
                </MenubarCheckboxItem>
                <MenubarCheckboxItem
                  checked={panelVisibility.mapView}
                  onClick={() => togglePanel('mapView')}
                >
                  Map View
                </MenubarCheckboxItem>
              </MenubarSubContent>
            </MenubarSub>
          </MenubarContent>
        </MenubarMenu>

        {/* Settings Menu */}
        <MenubarMenu>
          <MenubarTrigger>Settings</MenubarTrigger>
          <MenubarContent>
            <MenubarItem disabled>Panel Layout...</MenubarItem>
            <MenubarItem disabled>File Associations...</MenubarItem>
          </MenubarContent>
        </MenubarMenu>

        {/* Help Menu */}
        <MenubarMenu>
          <MenubarTrigger>Help</MenubarTrigger>
          <MenubarContent>
            <MenubarItem onClick={() => setShowShortcuts(true)}>
              Keyboard Shortcuts
              <MenubarShortcut>?</MenubarShortcut>
            </MenubarItem>
            <MenubarSeparator />
            <MenubarItem onClick={handleCheckUpdate}>Check for Updates...</MenubarItem>
            <MenubarSeparator />
            <MenubarItem onClick={() => setShowAbout(true)}>About PhotoGeoView</MenubarItem>
          </MenubarContent>
        </MenubarMenu>
      </Menubar>

      {/* Shortcuts Dialog */}
      <Dialog open={showShortcuts} onOpenChange={setShowShortcuts}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Keyboard Shortcuts</DialogTitle>
          </DialogHeader>
          <KeyboardShortcutsHelp />
        </DialogContent>
      </Dialog>

      {/* About Dialog */}
      <Dialog open={showAbout} onOpenChange={setShowAbout}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>About PhotoGeoView</DialogTitle>
            <DialogDescription>Photo Geo-Tagging Application</DialogDescription>
          </DialogHeader>
          <div className="space-y-2 text-sm">
            <p>
              <strong>Version:</strong> 2.1.0
            </p>
            <p className="text-muted-foreground">
              A desktop application for viewing photos with their geographic information.
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
