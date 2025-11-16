import { ExifPanel } from '@renderer/components/exif/ExifPanel'
import { FileBrowser } from '@renderer/components/file-browser/FileBrowser'
import { PhotoMap } from '@renderer/components/map/PhotoMap'
import { ImagePreview } from '@renderer/components/preview/ImagePreview'
import { ThumbnailGrid } from '@renderer/components/thumbnail/ThumbnailGrid'
import { Button } from '@renderer/components/ui/button'
import { KeyboardShortcutsHelp } from '@renderer/components/ui/keyboard-hint'
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@renderer/components/ui/dropdown-menu'
import { Popover, PopoverContent, PopoverTrigger } from '@renderer/components/ui/popover'
import { Toaster } from '@renderer/components/ui/sonner'
import { useImageNavigation } from '@renderer/hooks/useImageNavigation'
import { useKeyboardShortcuts } from '@renderer/hooks/useKeyboardShortcuts'
import { useAppStore } from '@renderer/stores/appStore'
import { useQuery } from '@tanstack/react-query'
import { Camera, Eye, Keyboard } from 'lucide-react'
import { useEffect, useMemo } from 'react'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'

function App(): JSX.Element {
  const { selectedFiles, currentPath, panelVisibility, togglePanel } = useAppStore()
  // Get the first selected file for EXIF display
  const selectedFile = selectedFiles.length > 0 ? selectedFiles[0] : null

  // Fetch directory contents for thumbnail grid
  // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
  const isElectron = !!(window as any).api

  // Apply system theme on mount and watch for changes
  useEffect(() => {
    const applySystemTheme = () => {
      // Use browser's matchMedia instead of Electron's nativeTheme
      // This works correctly even in WSL2 environment
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches

      // Apply theme based on system preference
      document.documentElement.classList.toggle('dark', isDark)
    }

    // Apply on mount
    applySystemTheme()

    // Watch for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleThemeChange = () => applySystemTheme()

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleThemeChange)
      return () => mediaQuery.removeEventListener('change', handleThemeChange)
    }
    // Legacy browsers
    mediaQuery.addListener(handleThemeChange)
    return () => mediaQuery.removeListener(handleThemeChange)
  }, [])

  const { data: result } = useQuery({
    queryKey: ['directory-contents-for-thumbnails', currentPath],
    queryFn: async () => {
      if (!currentPath || !isElectron) return null
      // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
      return await (window as any).api.getDirectoryContents({
        path: currentPath,
        includeHidden: false,
        imageOnly: true,
      })
    },
    enabled: !!currentPath && isElectron,
  })

  const files = result?.success ? result.data.entries : []

  // Image navigation with keyboard shortcuts
  const { selectNext, selectPrevious, selectFirst, selectLast, clearSelection } =
    useImageNavigation(files)

  // Define keyboard shortcuts
  const shortcuts = useMemo(
    () => [
      {
        key: 'ArrowRight',
        handler: selectNext,
        description: 'Next image',
      },
      {
        key: 'ArrowLeft',
        handler: selectPrevious,
        description: 'Previous image',
      },
      {
        key: 'Home',
        handler: selectFirst,
        description: 'First image',
      },
      {
        key: 'End',
        handler: selectLast,
        description: 'Last image',
      },
      {
        key: 'Escape',
        handler: clearSelection,
        description: 'Clear selection',
      },
    ],
    [selectNext, selectPrevious, selectFirst, selectLast, clearSelection]
  )

  // Register keyboard shortcuts
  useKeyboardShortcuts(shortcuts, files.length > 0)

  // Fetch EXIF data for the selected file for PhotoMap
  // Note: staleTime removed to ensure fresh data after image rotation
  const { data: exifResult } = useQuery({
    queryKey: ['exif-for-map', selectedFile],
    queryFn: async () => {
      if (!selectedFile || !isElectron) return null
      // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
      return await (window as any).api.readExif({ path: selectedFile })
    },
    enabled: !!selectedFile && isElectron,
  })

  const exifData = exifResult?.success ? exifResult.data.exif : null

  return (
    <>
      <Toaster />
      <div className="h-screen flex flex-col bg-background">
        <header className="flex-shrink-0 border-b bg-card px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Camera className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-br from-purple-600 to-purple-900 bg-clip-text text-transparent">
                  PhotoGeoView
                </h1>
                <p className="text-sm text-muted-foreground">Photo Geo-Tagging Application</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="gap-2">
                    <Eye className="h-4 w-4" />
                    Panels
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>Toggle Panels</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuCheckboxItem
                    checked={panelVisibility.fileBrowser}
                    onCheckedChange={() => togglePanel('fileBrowser')}
                  >
                    File Browser
                  </DropdownMenuCheckboxItem>
                  <DropdownMenuCheckboxItem
                    checked={panelVisibility.thumbnailGrid}
                    onCheckedChange={() => togglePanel('thumbnailGrid')}
                  >
                    Thumbnail Grid
                  </DropdownMenuCheckboxItem>
                  <DropdownMenuCheckboxItem
                    checked={panelVisibility.exifPanel}
                    onCheckedChange={() => togglePanel('exifPanel')}
                  >
                    EXIF Panel
                  </DropdownMenuCheckboxItem>
                  <DropdownMenuCheckboxItem
                    checked={panelVisibility.imagePreview}
                    onCheckedChange={() => togglePanel('imagePreview')}
                  >
                    Image Preview
                  </DropdownMenuCheckboxItem>
                  <DropdownMenuCheckboxItem
                    checked={panelVisibility.mapView}
                    onCheckedChange={() => togglePanel('mapView')}
                  >
                    Map View
                  </DropdownMenuCheckboxItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" size="sm" className="gap-2">
                    <Keyboard className="h-4 w-4" />
                    Shortcuts
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-80">
                  <KeyboardShortcutsHelp />
                </PopoverContent>
              </Popover>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-hidden p-4">
          <PanelGroup direction="horizontal" className="h-full gap-4">
            {/* Left Panel: File Browser and Thumbnail Grid */}
            <Panel defaultSize={25} minSize={15}>
              <PanelGroup direction="vertical" className="gap-4">
                {/* Top: File Browser */}
                {panelVisibility.fileBrowser && (
                  <>
                    <Panel defaultSize={40} minSize={20} collapsible collapsedSize={5}>
                      <FileBrowser />
                    </Panel>
                    <PanelResizeHandle className="h-1 bg-border hover:bg-primary transition-colors" />
                  </>
                )}

                {/* Bottom: Thumbnail Grid */}
                {panelVisibility.thumbnailGrid && (
                  <Panel defaultSize={60} minSize={30} collapsible collapsedSize={5}>
                    <ThumbnailGrid files={files} currentPath={currentPath} />
                  </Panel>
                )}
              </PanelGroup>
            </Panel>

            <PanelResizeHandle className="w-1 bg-border hover:bg-primary transition-colors" />

            {/* Middle Panel: EXIF Info */}
            {panelVisibility.exifPanel && (
              <>
                <Panel defaultSize={20} minSize={15} collapsible collapsedSize={3}>
                  <ExifPanel filePath={selectedFile} />
                </Panel>
                <PanelResizeHandle className="w-1 bg-border hover:bg-primary transition-colors" />
              </>
            )}

            {/* Right Panel: Image Preview and Map */}
            <Panel defaultSize={55} minSize={30}>
              <PanelGroup direction="vertical" className="gap-4">
                {/* Top: Image Preview */}
                {panelVisibility.imagePreview && (
                  <>
                    <Panel defaultSize={60} minSize={30} collapsible collapsedSize={5}>
                      <ImagePreview filePath={selectedFile} />
                    </Panel>
                    <PanelResizeHandle className="h-1 bg-border hover:bg-primary transition-colors" />
                  </>
                )}

                {/* Bottom: Map */}
                {panelVisibility.mapView && (
                  <Panel defaultSize={40} minSize={20} collapsible collapsedSize={5}>
                    <PhotoMap exifData={exifData} filePath={selectedFile} />
                  </Panel>
                )}
              </PanelGroup>
            </Panel>
          </PanelGroup>
        </main>
      </div>
    </>
  )
}

export default App
