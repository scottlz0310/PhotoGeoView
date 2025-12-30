import { Group, Panel, Separator } from 'react-resizable-panels'
import { MapView } from './components/MapView'
import { PhotoDetail } from './components/PhotoDetail'
import { PhotoList } from './components/PhotoList'

function App(): React.ReactElement {
  return (
    <div className="flex h-screen w-full flex-col bg-background">
      <header className="border-b border-border bg-card px-4 py-3">
        <h1 className="text-xl font-bold text-card-foreground">
          PhotoGeoView <span className="text-sm font-normal text-muted-foreground">v3.0.0</span>
        </h1>
      </header>

      <main className="flex-1 overflow-hidden p-4">
        <Group id="main-panel-group" orientation="horizontal" className="h-full gap-4">
          {/* Left Panel - Photo List */}
          <Panel id="photo-list-panel" defaultSize={30} minSize={20}>
            <PhotoList />
          </Panel>

          <Separator
            id="separator-horizontal"
            className="w-1 bg-border hover:bg-primary transition-colors"
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
                className="h-1 bg-border hover:bg-primary transition-colors"
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
