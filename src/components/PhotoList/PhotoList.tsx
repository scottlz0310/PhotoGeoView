import { invoke } from '@tauri-apps/api/core'
import type React from 'react'
import { useState } from 'react'

export function PhotoList(): React.ReactElement {
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const handleOpenFile = async () => {
    setIsLoading(true)
    try {
      const filePath = await invoke<string | null>('select_photo_file')
      if (filePath) {
        setSelectedFiles([filePath])
      }
    } catch (_error) {
      // Failed to open file
    } finally {
      setIsLoading(false)
    }
  }

  const handleOpenFiles = async () => {
    setIsLoading(true)
    try {
      const filePaths = await invoke<string[]>('select_photo_files')
      if (filePaths.length > 0) {
        setSelectedFiles(filePaths)
      }
    } catch (_error) {
      // Failed to open files
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-full w-full flex-col bg-card p-4">
      <h2 className="mb-4 text-lg font-semibold text-card-foreground">Photo List</h2>

      {/* File selection buttons */}
      <div className="mb-4 flex gap-2">
        <button
          type="button"
          onClick={handleOpenFile}
          disabled={isLoading}
          className="rounded bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
        >
          Open Photo
        </button>
        <button
          type="button"
          onClick={handleOpenFiles}
          disabled={isLoading}
          className="rounded bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
        >
          Open Photos
        </button>
      </div>

      {/* File list */}
      <div className="flex-1 overflow-y-auto">
        {selectedFiles.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No photos loaded yet. Click &quot;Open Photo(s)&quot; to get started.
          </div>
        ) : (
          <div className="space-y-2">
            {selectedFiles.map((file) => (
              <div key={file} className="rounded bg-muted p-2 text-sm">
                <div className="truncate font-medium text-foreground">
                  {file.split('/').pop() || file.split('\\').pop()}
                </div>
                <div className="truncate text-xs text-muted-foreground">{file}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
