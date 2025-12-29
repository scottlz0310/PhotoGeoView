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
        <Group orientation="horizontal">
          {/* Left Panel - Photo List */}
          <Panel defaultSize={20} minSize={15} maxSize={40}>
            <PhotoList />
          </Panel>

          <Separator className="w-1 bg-border transition-colors hover:bg-primary" />

          {/* Center Panel - Map View */}
          <Panel defaultSize={50} minSize={30}>
            <MapView />
          </Panel>

          <Separator className="w-1 bg-border transition-colors hover:bg-primary" />

          {/* Right Panel - Photo Detail */}
          <Panel defaultSize={30} minSize={20} maxSize={50}>
            <PhotoDetail />
          </Panel>
        </Group>
      </main>
    </div>
  )
}

export default App
