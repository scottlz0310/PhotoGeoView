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
            className="relative flex w-2 items-center justify-center bg-border after:absolute after:inset-y-0 after:left-1/2 after:w-1 after:-translate-x-1/2 after:bg-border hover:bg-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring data-[panel-group-direction=vertical]:h-2 data-[panel-group-direction=vertical]:w-full"
          >
            <div className="z-10 flex h-4 w-3 items-center justify-center rounded-sm border bg-border">
              <svg
                className="h-2.5 w-2.5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-label="Resize handle"
              >
                <title>Resize handle</title>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </div>
          </Separator>

          {/* Center Panel - Map View */}
          <Panel id="map-view-panel" defaultSize={45} minSize={25} maxSize={60}>
            <MapView />
          </Panel>

          <Separator
            id="separator-2"
            className="relative flex w-2 items-center justify-center bg-border after:absolute after:inset-y-0 after:left-1/2 after:w-1 after:-translate-x-1/2 after:bg-border hover:bg-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring data-[panel-group-direction=vertical]:h-2 data-[panel-group-direction=vertical]:w-full"
          >
            <div className="z-10 flex h-4 w-3 items-center justify-center rounded-sm border bg-border">
              <svg
                className="h-2.5 w-2.5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-label="Resize handle"
              >
                <title>Resize handle</title>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </div>
          </Separator>

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
