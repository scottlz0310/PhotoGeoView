import { ExifPanel } from '@renderer/components/exif/ExifPanel'
import { FileBrowser } from '@renderer/components/file-browser/FileBrowser'
import { ThumbnailGrid } from '@renderer/components/thumbnail/ThumbnailGrid'
import { useAppStore } from '@renderer/stores/appStore'
import { useQuery } from '@tanstack/react-query'
import { Camera } from 'lucide-react'

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

  return (
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
        <div className="h-full grid grid-cols-3 gap-4">
          <FileBrowser />
          <ThumbnailGrid files={files} currentPath={currentPath} />
          <ExifPanel filePath={selectedFile} />
        </div>
      </main>
    </div>
  )
}

export default App
