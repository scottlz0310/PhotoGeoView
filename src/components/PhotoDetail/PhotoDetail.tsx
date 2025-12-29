import type React from 'react'

export function PhotoDetail(): React.ReactElement {
  return (
    <div className="h-full w-full overflow-y-auto bg-card p-4">
      <h2 className="mb-4 text-lg font-semibold text-card-foreground">Photo Details</h2>
      <div className="text-sm text-muted-foreground">
        Select a photo to view its details and EXIF information
      </div>
    </div>
  )
}
