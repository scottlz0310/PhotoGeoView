import { Button } from '@renderer/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@renderer/components/ui/card'
import { Input } from '@renderer/components/ui/input'
import { Separator } from '@renderer/components/ui/separator'
import { useAppStore } from '@renderer/stores/appStore'
import { Camera, FolderOpen, Image as ImageIcon, MapPin } from 'lucide-react'
import { useState } from 'react'

function App(): JSX.Element {
  const [count, setCount] = useState(0)
  const { isSidebarOpen, toggleSidebar, theme, setTheme } = useAppStore()

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8 bg-background">
      <header className="mb-12 text-center">
        <div className="flex items-center justify-center gap-3 mb-4">
          <Camera className="h-12 w-12 text-primary" />
          <h1 className="text-5xl font-bold bg-gradient-to-br from-purple-600 to-purple-900 bg-clip-text text-transparent">
            PhotoGeoView
          </h1>
        </div>
        <p className="text-xl text-muted-foreground">Modern Photo Geo-Tagging Application</p>
      </header>

      <main className="w-full max-w-4xl space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-3xl">Welcome to PhotoGeoView 2.0</CardTitle>
            <CardDescription>Built with modern web technologies</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <p className="text-foreground mb-4 font-medium">Tech Stack:</p>
              <ul className="space-y-2 text-muted-foreground">
                <li className="text-lg">⚡ Electron</li>
                <li className="text-lg">⚛️ React 19</li>
                <li className="text-lg">🔷 TypeScript 5.7+</li>
                <li className="text-lg">🚀 Vite 6</li>
                <li className="text-lg">🎨 TailwindCSS v4</li>
                <li className="text-lg">🧩 shadcn/ui</li>
              </ul>
            </div>

            <Separator />

            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Component Demo</h3>
              <div className="flex gap-3 flex-wrap">
                <Button variant="default" onClick={() => setCount((count) => count + 1)}>
                  Count is {count}
                </Button>
                <Button variant="outline" onClick={toggleSidebar}>
                  <FolderOpen className="h-4 w-4 mr-2" />
                  Toggle Sidebar: {isSidebarOpen ? 'Open' : 'Closed'}
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                >
                  <MapPin className="h-4 w-4 mr-2" />
                  Theme: {theme}
                </Button>
              </div>

              <Input placeholder="Search photos..." className="max-w-sm" />
              <p className="text-sm text-muted-foreground">
                State management demo using Zustand - try clicking the buttons above!
              </p>
            </div>

            <Separator />

            <div className="bg-muted rounded-lg p-4 text-center">
              <p className="text-lg font-medium text-muted-foreground">
                ✨ Ready for AI-driven development with TypeScript
              </p>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ImageIcon className="h-5 w-5" />
                Photos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Browse and manage your photo collection
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="h-5 w-5" />
                Geolocation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">View photos on an interactive map</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Camera className="h-5 w-5" />
                EXIF Data
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">Explore detailed photo metadata</p>
            </CardContent>
          </Card>
        </div>
      </main>

      <footer className="mt-12 text-sm text-muted-foreground">
        <p>Built with modern tech stack</p>
      </footer>
    </div>
  )
}

export default App
