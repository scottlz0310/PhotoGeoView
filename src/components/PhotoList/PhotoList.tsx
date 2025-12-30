import { invoke } from '@tauri-apps/api/core'
import { File, Files, FolderOpen } from 'lucide-react'
import type React from 'react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { usePhotoStore, type ViewMode } from '@/stores/photoStore'
import type { PhotoData } from '@/types/photo'

export function PhotoList(): React.ReactElement {
  const { photos, selectedPhoto, viewMode, addPhotos, selectPhoto, setViewMode } = usePhotoStore()
  const [isLoading, setIsLoading] = useState(false)
  const [recursive, setRecursive] = useState(true)
  const [loadingProgress, setLoadingProgress] = useState(0)
  const [loadingStatus, setLoadingStatus] = useState('')

  const handleOpenFile = async () => {
    setIsLoading(true)
    setLoadingStatus('ファイルを選択中...')
    try {
      const filePath = await invoke<string | null>('select_photo_file')
      if (filePath) {
        setLoadingStatus('写真データを読み込み中...')
        const photoData = await invoke<PhotoData>('get_photo_data', { path: filePath })
        addPhotos([photoData])
        selectPhoto(photoData.path)
      }
    } catch (_error) {
      // エラーは無視（ユーザーがキャンセルした場合など）
    } finally {
      setIsLoading(false)
      setLoadingStatus('')
      setLoadingProgress(0)
    }
  }

  const handleOpenFiles = async () => {
    setIsLoading(true)
    setLoadingStatus('ファイルを選択中...')
    try {
      const filePaths = await invoke<string[]>('select_photo_files')
      if (filePaths.length > 0) {
        setLoadingStatus(`${filePaths.length}個の写真を読み込み中...`)
        // 並列で写真データを取得
        const photoDataPromises = filePaths.map((path, index) =>
          invoke<PhotoData>('get_photo_data', { path }).then((data) => {
            setLoadingProgress(((index + 1) / filePaths.length) * 100)
            return data
          }),
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
      setLoadingStatus('')
      setLoadingProgress(0)
    }
  }

  const handleOpenFolder = async () => {
    setIsLoading(true)
    setLoadingStatus('フォルダを選択中...')
    try {
      const folderPath = await invoke<string | null>('select_photo_folder')
      if (folderPath) {
        setLoadingStatus('フォルダをスキャン中...')
        const filePaths = await invoke<string[]>('scan_folder_for_photos', {
          folderPath,
          recursive,
        })

        if (filePaths.length > 0) {
          setLoadingStatus(`${filePaths.length}個の写真を読み込み中...`)
          // 並列で写真データを取得
          const photoDataPromises = filePaths.map((path, index) =>
            invoke<PhotoData>('get_photo_data', { path }).then((data) => {
              setLoadingProgress(((index + 1) / filePaths.length) * 100)
              return data
            }),
          )
          const photosData = await Promise.all(photoDataPromises)
          addPhotos(photosData)
          // 最初の写真を選択
          const firstPhoto = photosData[0]
          if (firstPhoto) {
            selectPhoto(firstPhoto.path)
          }
        } else {
          setLoadingStatus('画像ファイルが見つかりませんでした')
          setTimeout(() => setLoadingStatus(''), 2000)
        }
      }
    } catch (_error) {
      // エラーは無視（ユーザーがキャンセルした場合など）
    } finally {
      setIsLoading(false)
      setLoadingStatus('')
      setLoadingProgress(0)
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

      {/* File/Folder selection buttons */}
      <div className="mb-4 space-y-3">
        <div className="flex gap-2">
          <Button onClick={handleOpenFile} disabled={isLoading} size="sm" className="flex-1">
            <File className="mr-2 h-4 w-4" />
            単一ファイル
          </Button>
          <Button onClick={handleOpenFiles} disabled={isLoading} size="sm" className="flex-1">
            <Files className="mr-2 h-4 w-4" />
            複数ファイル
          </Button>
        </div>

        <div className="space-y-2">
          <Button
            onClick={handleOpenFolder}
            disabled={isLoading}
            variant="secondary"
            size="sm"
            className="w-full"
          >
            <FolderOpen className="mr-2 h-4 w-4" />
            フォルダから開く
          </Button>

          {/* 再帰的スキャンオプション */}
          <div className="flex items-center gap-2 px-1">
            <input
              type="checkbox"
              id="recursive-scan"
              checked={recursive}
              onChange={(e) => setRecursive(e.target.checked)}
              className="h-4 w-4 rounded border-border"
              disabled={isLoading}
            />
            <label
              htmlFor="recursive-scan"
              className="text-xs text-muted-foreground cursor-pointer select-none"
            >
              サブフォルダも含める
            </label>
          </div>
        </div>

        {/* Loading indicator */}
        {isLoading && (
          <div className="space-y-2">
            <Progress value={loadingProgress} className="h-2" />
            <p className="text-xs text-muted-foreground text-center">{loadingStatus}</p>
          </div>
        )}
      </div>

      {/* コンテンツ表示エリア */}
      <div className="flex-1 overflow-y-auto">
        {photos.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            写真がまだ読み込まれていません。
            <br />
            上のボタンから写真やフォルダを開いてください。
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
