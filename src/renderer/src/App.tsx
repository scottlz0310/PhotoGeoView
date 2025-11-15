import { FileBrowser } from '@renderer/components/file-browser/FileBrowser'
import { Camera } from 'lucide-react'

function App(): JSX.Element {
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
        <FileBrowser />
      </main>
    </div>
  )
}

export default App
