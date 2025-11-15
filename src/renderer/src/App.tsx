import { ExifPanel } from '@renderer/components/exif/ExifPanel'
import { FileBrowser } from '@renderer/components/file-browser/FileBrowser'
import { PhotoMap } from '@renderer/components/map/PhotoMap'
import { ImagePreview } from '@renderer/components/preview/ImagePreview'
import { ThumbnailGrid } from '@renderer/components/thumbnail/ThumbnailGrid'
import { Toaster } from '@renderer/components/ui/sonner'
import { useAppStore } from '@renderer/stores/appStore'
import { useQuery } from '@tanstack/react-query'
import { Camera } from 'lucide-react'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'

function App(): JSX.Element {
  const { selectedFiles, currentPath } = useAppStore()
  // Get the first selected file for EXIF display
  const selectedFile = selectedFiles.length > 0 ? selectedFiles[0] : null

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

  // Fetch EXIF data for the selected file for PhotoMap
  const { data: exifResult } = useQuery({
    queryKey: ['exif-for-map', selectedFile],
    queryFn: async () => {
      if (!selectedFile || !isElectron) return null
      // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
      return await (window as any).api.readExif({ path: selectedFile })
    },
    enabled: !!selectedFile && isElectron,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const exifData = exifResult?.success ? exifResult.data.exif : null

  return (
    <>
      <Toaster />
      <div className="h-screen flex flex-col bg-background">
        <header className="flex-shrink-0 border-b bg-card px-6 py-4">
          <div className="flex items-center gap-3">
            <Camera className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-br from-purple-600 to-purple-900 bg-clip-text text-transparent">
                PhotoGeoView
              </h1>
              <p className="text-sm text-muted-foreground">Photo Geo-Tagging Application</p>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-hidden p-4">
          <PanelGroup direction="horizontal" className="h-full gap-4">
            {/* Left Panel: File Browser and Thumbnail Grid */}
            <Panel defaultSize={25} minSize={15}>
              <PanelGroup direction="vertical" className="gap-4">
                {/* Top: File Browser */}
                <Panel defaultSize={40} minSize={20}>
                  <FileBrowser />
                </Panel>

                <PanelResizeHandle className="h-1 bg-border hover:bg-primary transition-colors" />

                {/* Bottom: Thumbnail Grid */}
                <Panel defaultSize={60} minSize={30}>
                  <ThumbnailGrid files={files} currentPath={currentPath} />
                </Panel>
              </PanelGroup>
            </Panel>

            <PanelResizeHandle className="w-1 bg-border hover:bg-primary transition-colors" />

            {/* Middle Panel: EXIF Info */}
            <Panel defaultSize={20} minSize={15}>
              <ExifPanel filePath={selectedFile} />
            </Panel>

            <PanelResizeHandle className="w-1 bg-border hover:bg-primary transition-colors" />

            {/* Right Panel: Image Preview and Map */}
            <Panel defaultSize={55} minSize={30}>
              <PanelGroup direction="vertical" className="gap-4">
                {/* Top: Image Preview */}
                <Panel defaultSize={60} minSize={30}>
                  <ImagePreview filePath={selectedFile} />
                </Panel>

                <PanelResizeHandle className="h-1 bg-border hover:bg-primary transition-colors" />

                {/* Bottom: Map */}
                <Panel defaultSize={40} minSize={20}>
                  <PhotoMap exifData={exifData} filePath={selectedFile} />
                </Panel>
              </PanelGroup>
            </Panel>
          </PanelGroup>
        </main>
      </div>
    </>
  )
}

export default App
