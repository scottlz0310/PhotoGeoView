import { convertFileSrc } from '@tauri-apps/api/core'
import type React from 'react'
import { TransformComponent, TransformWrapper } from 'react-zoom-pan-pinch'
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

      {/* 画像プレビュー（ズーム・パン対応） */}
      <div className="flex-1 overflow-hidden bg-muted/20" style={{ position: 'relative' }}>
        <TransformWrapper
          initialScale={1}
          minScale={0.1}
          maxScale={10}
          wheel={{ step: 0.1 }}
          panning={{ disabled: false }}
          doubleClick={{ disabled: false }}
          centerOnInit={true}
        >
          {() => (
            <TransformComponent
              wrapperStyle={{
                width: '100%',
                height: '100%',
                position: 'absolute',
                top: 0,
                left: 0,
              }}
              contentStyle={{
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <img
                src={imageUrl}
                alt={selectedPhoto.filename}
                style={{
                  maxWidth: '100%',
                  maxHeight: '100%',
                  objectFit: 'contain',
                  pointerEvents: 'none',
                }}
              />
            </TransformComponent>
          )}
        </TransformWrapper>
      </div>

      {/* EXIF情報（1行コンパクト表示） */}
      <div className="group relative border-t border-border px-3 py-2">
        {selectedPhoto.exif ? (
          <>
            {/* 通常表示: 1行 */}
            <div className="flex items-center gap-3 overflow-hidden text-xs text-muted-foreground">
              {/* GPS有無 */}
              {selectedPhoto.exif.gps && <span title="GPS情報あり">📍</span>}

              {/* 撮影日時 */}
              {selectedPhoto.exif.datetime && (
                <span className="flex items-center gap-1">
                  <span>📅</span>
                  <span className="truncate">
                    {new Date(selectedPhoto.exif.datetime).toLocaleString()}
                  </span>
                </span>
              )}

              {/* 画像サイズ */}
              {selectedPhoto.exif.width && selectedPhoto.exif.height && (
                <span className="flex items-center gap-1">
                  <span>📐</span>
                  <span>
                    {selectedPhoto.exif.width}×{selectedPhoto.exif.height}
                  </span>
                </span>
              )}

              {/* カメラ情報（省略表示） */}
              {selectedPhoto.exif.camera && (
                <span className="flex items-center gap-1 truncate">
                  <span>📷</span>
                  <span className="truncate">{selectedPhoto.exif.camera.model}</span>
                </span>
              )}

              {/* その他の情報（省略） */}
              {(selectedPhoto.exif.iso ||
                selectedPhoto.exif.aperture ||
                selectedPhoto.exif.shutterSpeed ||
                selectedPhoto.exif.focalLength) && (
                <span className="ml-auto text-muted-foreground/60">···</span>
              )}
            </div>

            {/* ホバー時の詳細表示 */}
            <div className="absolute bottom-full left-0 right-0 mb-1 hidden rounded border border-border bg-card p-3 shadow-lg group-hover:block">
              <div className="space-y-1 text-xs">
                {/* GPS情報 */}
                {selectedPhoto.exif.gps && (
                  <div>
                    <span className="font-medium">📍 GPS:</span>{' '}
                    {selectedPhoto.exif.gps.lat.toFixed(6)}, {selectedPhoto.exif.gps.lng.toFixed(6)}
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
                    <span className="font-medium">📐 Size:</span> {selectedPhoto.exif.width} ×{' '}
                    {selectedPhoto.exif.height}
                  </div>
                )}

                {/* 撮影設定 */}
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
            </div>
          </>
        ) : (
          <div className="text-xs text-muted-foreground">No EXIF data</div>
        )}
      </div>
    </div>
  )
}
