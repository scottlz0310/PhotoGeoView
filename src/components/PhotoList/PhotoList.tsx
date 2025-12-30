import { invoke } from '@tauri-apps/api/core'
import type React from 'react'
import { useState } from 'react'
import { usePhotoStore, type ViewMode } from '@/stores/photoStore'
import type { PhotoData } from '@/types/photo'

export function PhotoList(): React.ReactElement {
  const { photos, selectedPhoto, viewMode, addPhotos, selectPhoto, setViewMode } = usePhotoStore()
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

  const viewModeLabels: Record<ViewMode, string> = {
    list: 'リスト表示',
    detail: '詳細表示',
    grid: 'グリッド表示',
  }

  return (
    <div className="flex h-full w-full flex-col bg-card p-4">
      {/* ヘッダー */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-card-foreground">Photo List</h2>

        {/* ビューモード切り替えドロップダウン */}
        <select
          value={viewMode}
          onChange={(e) => setViewMode(e.target.value as ViewMode)}
          className="rounded border border-border bg-background px-2 py-1 text-sm text-foreground transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="list">{viewModeLabels.list}</option>
          <option value="detail">{viewModeLabels.detail}</option>
          <option value="grid">{viewModeLabels.grid}</option>
        </select>
      </div>

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

      {/* コンテンツ表示エリア */}
      <div className="flex-1 overflow-y-auto">
        {photos.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No photos loaded yet. Click &quot;Open Photo(s)&quot; to get started.
          </div>
        ) : (
          <>
            {/* リスト表示 */}
            {viewMode === 'list' && (
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

            {/* 詳細表示 */}
            {viewMode === 'detail' && (
              <div className="space-y-3">
                {photos.map((photo) => (
                  <button
                    type="button"
                    key={photo.path}
                    onClick={() => selectPhoto(photo.path)}
                    className={`w-full rounded p-3 text-left text-sm transition-colors ${
                      selectedPhoto?.path === photo.path
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                  >
                    <div className="truncate font-semibold">{photo.filename}</div>
                    <div className="mt-2 space-y-1 text-xs opacity-80">
                      {photo.exif?.datetime && (
                        <div>📅 {new Date(photo.exif.datetime).toLocaleString()}</div>
                      )}
                      {photo.exif?.gps && (
                        <div>
                          📍 {photo.exif.gps.lat.toFixed(6)}, {photo.exif.gps.lng.toFixed(6)}
                        </div>
                      )}
                      {photo.exif?.camera && (
                        <div>
                          📷 {photo.exif.camera.make} {photo.exif.camera.model}
                        </div>
                      )}
                      {photo.exif?.width && photo.exif?.height && (
                        <div>
                          📐 {photo.exif.width} x {photo.exif.height}
                        </div>
                      )}
                    </div>
                    <div className="mt-2 truncate text-xs opacity-60">{photo.path}</div>
                  </button>
                ))}
              </div>
            )}

            {/* グリッド表示 */}
            {viewMode === 'grid' && (
              <div className="grid grid-cols-2 gap-2">
                {photos.map((photo) => (
                  <button
                    type="button"
                    key={photo.path}
                    onClick={() => selectPhoto(photo.path)}
                    className={`aspect-square rounded p-2 text-left transition-colors ${
                      selectedPhoto?.path === photo.path
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                  >
                    <div className="flex h-full flex-col">
                      {/* サムネイル領域 */}
                      <div className="flex-1 flex items-center justify-center bg-background/50 rounded mb-2 overflow-hidden">
                        {photo.thumbnail ? (
                          <img
                            src={photo.thumbnail}
                            alt={photo.filename}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <span className="text-4xl">🖼️</span>
                        )}
                      </div>
                      <div className="truncate text-xs font-medium">{photo.filename}</div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
