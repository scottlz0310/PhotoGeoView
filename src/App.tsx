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

      <main className="flex-1 overflow-hidden">
        <Group id="main-panel-group" orientation="horizontal" className="flex h-full w-full">
          {/* Left Panel - Photo List */}
          <Panel id="photo-list-panel" defaultSize={25} minSize={15} maxSize={40}>
            <PhotoList />
          </Panel>

          <Separator
            id="separator-1"
            className="w-2 bg-border hover:bg-primary"
            style={{ cursor: 'col-resize' }}
          />

          {/* Center Panel - Map View */}
          <Panel id="map-view-panel" defaultSize={45} minSize={30}>
            <MapView />
          </Panel>

          <Separator
            id="separator-2"
            className="w-2 bg-border hover:bg-primary"
            style={{ cursor: 'col-resize' }}
          />

          {/* Right Panel - Photo Detail */}
          <Panel id="photo-detail-panel" defaultSize={30} minSize={20} maxSize={50}>
            <PhotoDetail />
          </Panel>
        </Group>
      </main>
    </div>
  )
}

export default App
