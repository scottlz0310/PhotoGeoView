import { convertFileSrc } from '@tauri-apps/api/core'
import type React from 'react'
import { usePhotoStore } from '@/stores/photoStore'

export function PhotoDetail(): React.ReactElement {
  const { selectedPhoto } = usePhotoStore()

  if (!selectedPhoto) {
    return (
      <div className="h-full w-full overflow-y-auto bg-card p-4">
        <h2 className="mb-4 text-lg font-semibold text-card-foreground">Photo Details</h2>
        <div className="text-sm text-muted-foreground">
          Select a photo to view its details and EXIF information
        </div>
      </div>
    )
  }

  // Tauriでファイルパスを安全なURLに変換
  const imageUrl = convertFileSrc(selectedPhoto.path)

  return (
    <div className="flex h-full w-full flex-col bg-card">
      {/* ヘッダー */}
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-lg font-semibold text-card-foreground">Photo Details</h2>
        <p className="truncate text-sm text-muted-foreground">{selectedPhoto.filename}</p>
      </div>

      {/* 画像プレビュー */}
      <div className="flex-1 overflow-auto bg-muted/20 p-4">
        <div className="flex h-full items-center justify-center">
          <img
            src={imageUrl}
            alt={selectedPhoto.filename}
            className="max-h-full max-w-full object-contain"
          />
        </div>
      </div>

      {/* EXIF情報 */}
      <div className="border-t border-border px-4 py-3">
        <h3 className="mb-2 text-sm font-semibold text-card-foreground">EXIF Information</h3>
        {selectedPhoto.exif ? (
          <div className="space-y-1 text-xs text-muted-foreground">
            {/* GPS情報 */}
            {selectedPhoto.exif.gps && (
              <div>
                <span className="font-medium">📍 GPS:</span> {selectedPhoto.exif.gps.lat.toFixed(6)}
                , {selectedPhoto.exif.gps.lng.toFixed(6)}
              </div>
            )}

            {/* 撮影日時 */}
            {selectedPhoto.exif.datetime && (
              <div>
                <span className="font-medium">📅 Date:</span>{' '}
                {new Date(selectedPhoto.exif.datetime).toLocaleString()}
              </div>
            )}

            {/* カメラ情報 */}
            {selectedPhoto.exif.camera && (
              <div>
                <span className="font-medium">📷 Camera:</span> {selectedPhoto.exif.camera.make}{' '}
                {selectedPhoto.exif.camera.model}
              </div>
            )}

            {/* 画像サイズ */}
            {selectedPhoto.exif.width && selectedPhoto.exif.height && (
              <div>
                <span className="font-medium">📐 Size:</span> {selectedPhoto.exif.width} x{' '}
                {selectedPhoto.exif.height}
              </div>
            )}

            {/* 撮影設定 */}
            {(selectedPhoto.exif.iso ||
              selectedPhoto.exif.aperture ||
              selectedPhoto.exif.shutterSpeed ||
              selectedPhoto.exif.focalLength) && (
              <div className="mt-2 border-t border-border pt-2">
                {selectedPhoto.exif.iso && (
                  <div>
                    <span className="font-medium">ISO:</span> {selectedPhoto.exif.iso}
                  </div>
                )}
                {selectedPhoto.exif.aperture && (
                  <div>
                    <span className="font-medium">Aperture:</span> f/
                    {selectedPhoto.exif.aperture.toFixed(1)}
                  </div>
                )}
                {selectedPhoto.exif.shutterSpeed && (
                  <div>
                    <span className="font-medium">Shutter:</span> 1/
                    {Math.round(1 / selectedPhoto.exif.shutterSpeed)}s
                  </div>
                )}
                {selectedPhoto.exif.focalLength && (
                  <div>
                    <span className="font-medium">Focal Length:</span>{' '}
                    {selectedPhoto.exif.focalLength.toFixed(0)}mm
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="text-xs text-muted-foreground">No EXIF data available</div>
        )}
      </div>
    </div>
  )
}
