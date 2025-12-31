import { Camera } from 'lucide-react'
import { useTheme } from 'next-themes'
import { useEffect, useState } from 'react'
import { Group, Panel, Separator } from 'react-resizable-panels'
import { AboutDialog } from './components/About/AboutDialog'
import { MapView } from './components/MapView'
import { PhotoDetail } from './components/PhotoDetail'
import { PhotoList } from './components/PhotoList'
import { Settings } from './components/Settings/Settings'
import { StatusBar } from './components/StatusBar/StatusBar'
import { usePhotoStore } from './stores/photoStore'
import { useSettingsStore } from './stores/settingsStore'

function App(): React.ReactElement {
  const { loadSettings, isLoaded, settings } = useSettingsStore()
  const { initializeViewMode } = usePhotoStore()
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [isAboutOpen, setIsAboutOpen] = useState(false)
  const { setTheme } = useTheme()

  // アプリ起動時に設定を読み込む
  useEffect(() => {
    loadSettings()
  }, [loadSettings])

  // 設定読み込み完了後にビューモードを初期化
  useEffect(() => {
    if (isLoaded) {
      initializeViewMode()
    }
  }, [isLoaded, initializeViewMode])

  useEffect(() => {
    if (isLoaded) {
      setTheme(settings.ui.theme)
    }
  }, [isLoaded, setTheme, settings.ui.theme])

  return (
    <div className="flex h-screen w-full flex-col bg-background">
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
          <div className="flex items-center gap-4">
            <button
              type="button"
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              ファイル
            </button>
            <button
              type="button"
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              表示
            </button>
            <button
              type="button"
              onClick={() => setIsSettingsOpen(true)}
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              設定
            </button>
            <button
              type="button"
              onClick={() => setIsAboutOpen(true)}
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              ヘルプ
            </button>
          </div>
        </div>
      </header>

      {/* 設定ダイアログ */}
      <Settings isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      <AboutDialog isOpen={isAboutOpen} onOpenChange={setIsAboutOpen} />

      <main className="flex-1 overflow-hidden p-4">
        <Group id="main-panel-group" orientation="horizontal" className="h-full gap-4">
          {/* Left Panel - Photo List */}
          <Panel
            id="photo-list-panel"
            defaultSize={30}
            minSize={20}
            className="flex flex-col rounded-lg border bg-card shadow-sm"
          >
            <div className="flex-1 overflow-hidden">
              <PhotoList />
            </div>
          </Panel>

          <Separator
            id="separator-horizontal"
            className="w-[2px] bg-border hover:bg-primary/50 transition-colors cursor-col-resize"
          />

          {/* Right Panel - Split vertically into Photo Preview (top) and Map (bottom) */}
          <Panel id="right-panel" defaultSize={70} minSize={30}>
            <Group id="right-panel-group" orientation="vertical" className="h-full gap-4">
              {/* Top: Photo Preview */}
              <Panel
                id="photo-detail-panel"
                defaultSize={60}
                minSize={20}
                className="flex flex-col rounded-lg border bg-card shadow-sm"
              >
                <div className="flex-1 overflow-hidden relative">
                  <PhotoDetail />
                </div>
              </Panel>

              <Separator
                id="separator-vertical"
                className="h-[2px] bg-border hover:bg-primary/50 transition-colors cursor-row-resize"
              />

              {/* Bottom: Map View */}
              <Panel
                id="map-view-panel"
                defaultSize={40}
                minSize={20}
                className="flex flex-col rounded-lg border bg-card shadow-sm"
              >
                <div className="flex-1 overflow-hidden relative">
                  <MapView />
                </div>
              </Panel>
            </Group>
          </Panel>
        </Group>
      </main>

      {/* Status Bar */}
      <StatusBar />
    </div>
  )
}

export default App
