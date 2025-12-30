import { invoke } from '@tauri-apps/api/core'
import type React from 'react'
import { useState } from 'react'
import { usePhotoStore } from '@/stores/photoStore'
import type { PhotoData } from '@/types/photo'

export function PhotoList(): React.ReactElement {
  const { photos, selectedPhoto, addPhotos, selectPhoto } = usePhotoStore()
  const [isLoading, setIsLoading] = useState(false)

  const handleOpenFile = async () => {
    setIsLoading(true)
    try {
      const filePath = await invoke<string | null>('select_photo_file')
      if (filePath) {
        const photoData = await invoke<PhotoData>('get_photo_data', { path: filePath })
        addPhotos([photoData])
        selectPhoto(photoData.path)
      }
    } catch (_error) {
      // エラーは無視（ユーザーがキャンセルした場合など）
    } finally {
      setIsLoading(false)
    }
  }

  const handleOpenFiles = async () => {
    setIsLoading(true)
    try {
      const filePaths = await invoke<string[]>('select_photo_files')
      if (filePaths.length > 0) {
        // 並列で写真データを取得
        const photoDataPromises = filePaths.map((path) =>
          invoke<PhotoData>('get_photo_data', { path }),
        )
        const photosData = await Promise.all(photoDataPromises)
        addPhotos(photosData)
        // 最初の写真を選択
        const firstPhoto = photosData[0]
        if (firstPhoto) {
          selectPhoto(firstPhoto.path)
        }
      }
    } catch (_error) {
      // エラーは無視（ユーザーがキャンセルした場合など）
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
        {photos.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No photos loaded yet. Click &quot;Open Photo(s)&quot; to get started.
          </div>
        ) : (
          <div className="space-y-2">
            {photos.map((photo) => (
              <button
                type="button"
                key={photo.path}
                onClick={() => selectPhoto(photo.path)}
                className={`w-full rounded p-2 text-left text-sm transition-colors ${
                  selectedPhoto?.path === photo.path
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted hover:bg-muted/80'
                }`}
              >
                <div className="truncate font-medium">{photo.filename}</div>
                <div className="mt-1 flex items-center gap-2 text-xs opacity-80">
                  {photo.exif?.gps && <span>📍 GPS</span>}
                  {photo.exif?.datetime && (
                    <span>{new Date(photo.exif.datetime).toLocaleDateString()}</span>
                  )}
                </div>
                <div className="mt-1 truncate text-xs opacity-60">{photo.path}</div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
