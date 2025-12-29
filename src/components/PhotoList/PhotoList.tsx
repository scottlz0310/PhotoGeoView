import type React from 'react'

export function PhotoList(): React.ReactElement {
  return (
    <div className="h-full w-full overflow-y-auto bg-card p-4">
      <h2 className="mb-4 text-lg font-semibold text-card-foreground">Photo List</h2>
      <div className="text-sm text-muted-foreground">
        No photos loaded yet. Click &quot;Open Photos&quot; to get started.
      </div>
    </div>
  )
}
