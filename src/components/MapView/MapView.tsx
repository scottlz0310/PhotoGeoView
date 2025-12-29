import type React from 'react'

export function MapView(): React.ReactElement {
  return (
    <div className="relative h-full w-full bg-muted">
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <h2 className="mb-2 text-xl font-semibold text-foreground">Map View</h2>
          <p className="text-sm text-muted-foreground">
            Map will appear here when photos with GPS data are loaded
          </p>
        </div>
      </div>
    </div>
  )
}
