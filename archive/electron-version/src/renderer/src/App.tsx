import { ExifPanel } from '@renderer/components/exif/ExifPanel'
import { FileBrowser } from '@renderer/components/file-browser/FileBrowser'
import { MenuBar } from '@renderer/components/MenuBar'
import { PhotoMap } from '@renderer/components/map/PhotoMap'
import { ImagePreview } from '@renderer/components/preview/ImagePreview'
import { StatusBar } from '@renderer/components/StatusBar'
import { ThumbnailGrid } from '@renderer/components/thumbnail/ThumbnailGrid'
import { Toaster } from '@renderer/components/ui/sonner'
import { useImageNavigation } from '@renderer/hooks/useImageNavigation'
import { useKeyboardShortcuts } from '@renderer/hooks/useKeyboardShortcuts'
import { useAppStore } from '@renderer/stores/appStore'
import { useQuery } from '@tanstack/react-query'
import i18n from 'i18next'
import { Camera } from 'lucide-react'
import { useEffect, useMemo } from 'react'
import { Group, Panel, Separator } from 'react-resizable-panels'

function App() {
  const {
    selectedFiles,
    currentPath,
    panelVisibility,
    layoutPreset,
    language,
    initializeFromStore,
    setSelectedFiles,
    navigateToPath,
  } = useAppStore()

  // Layout sizes based on preset
  const layoutSizes = useMemo(() => {
    switch (layoutPreset) {
      case 'preview-focus':
        return { left: 20, right: 80, preview: 75, map: 25 }
      case 'map-focus':
        return { left: 20, right: 80, preview: 40, map: 60 }
      case 'compact':
        return { left: 30, right: 70, preview: 60, map: 40 }
      default:
        return { left: 25, right: 75, preview: 60, map: 40 }
    }
  }, [layoutPreset])
  // Get the first selected file for EXIF display
  const selectedFile = selectedFiles.length > 0 ? selectedFiles[0] : null

  // Sync i18n language with store
  useEffect(() => {
    if (language && i18n.language !== language) {
      i18n.changeLanguage(language)
    }
  }, [language])

  // Initialize store from persisted settings and handle initial file
  useEffect(() => {
    const init = async () => {
      await initializeFromStore()
      // Check for initial file from command line
      // biome-ignore lint/suspicious/noExplicitAny: Electron API
      const api = (window as any).api
      if (api) {
        const result = await api.getInitialFile()
        if (result.success && result.data) {
          navigateToPath(result.data.dirPath)
          setSelectedFiles([result.data.filePath])
        }
      }
    }
    init()
  }, [initializeFromStore, navigateToPath, setSelectedFiles])

  // Check if selected file is an image (simple extension check)
  const isImageFile = useMemo(() => {
    if (!selectedFile) return false
    const ext = selectedFile.split('.').pop()?.toLowerCase()
    return ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'tiff', 'tif'].includes(ext || '')
  }, [selectedFile])

  const previewFile = isImageFile ? selectedFile : null

  // Fetch directory contents for thumbnail grid
  // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
  const isElectron = !!(window as any).api

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
    queryKey: ['exif-for-map', previewFile],
    queryFn: async () => {
      if (!previewFile || !isElectron) return null
      // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
      return await (window as any).api.readExif({ path: previewFile })
    },
    enabled: !!previewFile && isElectron,
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
            <MenuBar />
          </div>
        </header>

        <main className="flex-1 overflow-hidden p-4">
          <Group
            id="main-layout"
            key={layoutPreset}
            orientation="horizontal"
            className="h-full gap-4"
          >
            {/* Left Panel: File Browser and Thumbnail Grid */}
            <Panel id="left-panel" defaultSize={layoutSizes.left} minSize={15}>
              <Group id="left-group" orientation="vertical" className="h-full gap-4">
                {/* Top: File Browser */}
                {panelVisibility.fileBrowser && (
                  <Panel
                    id="file-browser-panel"
                    defaultSize={40}
                    minSize={20}
                    collapsible
                    collapsedSize={5}
                  >
                    <FileBrowser />
                  </Panel>
                )}

                {/* Separator only if both panels are visible */}
                {panelVisibility.fileBrowser && panelVisibility.thumbnailGrid && (
                  <Separator
                    id="left-separator"
                    className="h-1 bg-border hover:bg-primary transition-colors"
                  />
                )}

                {/* Bottom: Thumbnail Grid */}
                {panelVisibility.thumbnailGrid && (
                  <Panel
                    id="thumbnail-panel"
                    defaultSize={60}
                    minSize={30}
                    collapsible
                    collapsedSize={5}
                  >
                    <ThumbnailGrid files={files} currentPath={currentPath} />
                  </Panel>
                )}
              </Group>
            </Panel>

            <Separator
              id="main-separator-1"
              className="w-1 bg-border hover:bg-primary transition-colors"
            />

            {/* Middle Panel: EXIF Info */}
            {panelVisibility.exifPanel && (
              <Panel id="exif-panel" defaultSize={20} minSize={15} collapsible collapsedSize={3}>
                <ExifPanel filePath={previewFile} />
              </Panel>
            )}

            {/* Separator between EXIF and Right panels, only if EXIF is visible */}
            {panelVisibility.exifPanel && (
              <Separator
                id="main-separator-2"
                className="w-1 bg-border hover:bg-primary transition-colors"
              />
            )}

            {/* Right Panel: Image Preview and Map */}
            <Panel id="right-panel" defaultSize={layoutSizes.right} minSize={30}>
              <Group id="right-group" orientation="vertical" className="h-full gap-4">
                {/* Top: Image Preview */}
                {panelVisibility.imagePreview && (
                  <Panel
                    id="image-preview-panel"
                    defaultSize={layoutSizes.preview}
                    minSize={20}
                    collapsible
                    collapsedSize={5}
                  >
                    <ImagePreview filePath={previewFile} />
                  </Panel>
                )}

                {/* Separator only if both panels are visible */}
                {panelVisibility.imagePreview && panelVisibility.mapView && (
                  <Separator
                    id="right-separator"
                    className="h-1 bg-border hover:bg-primary transition-colors"
                  />
                )}

                {/* Bottom: Map */}
                {panelVisibility.mapView && (
                  <Panel
                    id="map-panel"
                    defaultSize={layoutSizes.map}
                    minSize={20}
                    collapsible
                    collapsedSize={5}
                  >
                    <PhotoMap exifData={exifData} filePath={previewFile} />
                  </Panel>
                )}
              </Group>
            </Panel>
          </Group>
        </main>

        <StatusBar filePath={previewFile} />
      </div>
    </>
  )
}

export default App
