import { useEffect, useState } from 'react'
import { Group, Panel, Separator } from 'react-resizable-panels'
import { MapView } from './components/MapView'
import { PhotoDetail } from './components/PhotoDetail'
import { PhotoList } from './components/PhotoList'
import { Settings } from './components/Settings/Settings'
import { usePhotoStore } from './stores/photoStore'
import { useSettingsStore } from './stores/settingsStore'

function App(): React.ReactElement {
  const { loadSettings, isLoaded } = useSettingsStore()
  const { initializeViewMode } = usePhotoStore()
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)

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

  return (
    <div className="flex h-screen w-full flex-col bg-background">
      <header className="border-b border-border bg-card px-4 py-3">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-card-foreground">
            PhotoGeoView <span className="text-sm font-normal text-muted-foreground">v3.0.0</span>
          </h1>
          <button
            type="button"
            onClick={() => setIsSettingsOpen(true)}
            className="rounded bg-muted px-3 py-1.5 text-sm text-foreground hover:bg-muted/80 transition-colors"
          >
            ⚙️ 設定
          </button>
        </div>
      </header>

      {/* 設定ダイアログ */}
      <Settings isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />

      <main className="flex-1 overflow-hidden p-4">
        <Group id="main-panel-group" orientation="horizontal" className="h-full gap-4">
          {/* Left Panel - Photo List */}
          <Panel id="photo-list-panel" defaultSize={30} minSize={20}>
            <PhotoList />
          </Panel>

          <Separator
            id="separator-horizontal"
            className="w-[2px] bg-border/60 hover:bg-primary/80 transition-colors cursor-col-resize"
          />

          {/* Right Panel - Split vertically into Photo Preview (top) and Map (bottom) */}
          <Panel id="right-panel" defaultSize={70} minSize={30}>
            <Group id="right-panel-group" orientation="vertical" className="h-full gap-4">
              {/* Top: Photo Preview */}
              <Panel id="photo-detail-panel" defaultSize={60} minSize={20}>
                <PhotoDetail />
              </Panel>

              <Separator
                id="separator-vertical"
                className="h-[2px] bg-border/60 hover:bg-primary/80 transition-colors cursor-row-resize"
              />

              {/* Bottom: Map View */}
              <Panel id="map-view-panel" defaultSize={40} minSize={20}>
                <MapView />
              </Panel>
            </Group>
          </Panel>
        </Group>
      </main>
    </div>
  )
}

export default App
