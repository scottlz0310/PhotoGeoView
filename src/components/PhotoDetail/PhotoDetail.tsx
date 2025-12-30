import { convertFileSrc } from '@tauri-apps/api/core'
import { Maximize2, RotateCcw, ZoomIn, ZoomOut } from 'lucide-react'
import type React from 'react'
import { TransformComponent, TransformWrapper } from 'react-zoom-pan-pinch'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { usePhotoStore } from '@/stores/photoStore'

export function PhotoDetail(): React.ReactElement {
  const { selectedPhoto } = usePhotoStore()

  if (!selectedPhoto) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-card">
        <p className="text-sm text-muted-foreground">写真が選択されていません</p>
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
          {({ zoomIn, zoomOut, resetTransform, centerView }) => (
            <>
              {/* ズーム操作ツールバー */}
              <div className="absolute top-4 right-4 z-10 flex flex-col gap-2">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="secondary"
                        onClick={() => zoomIn(0.2)}
                        className="h-8 w-8 shadow-md"
                      >
                        <ZoomIn className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>拡大 (マウスホイールでも可)</p>
                    </TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="secondary"
                        onClick={() => zoomOut(0.2)}
                        className="h-8 w-8 shadow-md"
                      >
                        <ZoomOut className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>縮小</p>
                    </TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="secondary"
                        onClick={() => {
                          resetTransform()
                          centerView(1, 0)
                        }}
                        className="h-8 w-8 shadow-md"
                      >
                        <RotateCcw className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>リセット (等倍・中央配置)</p>
                    </TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="secondary"
                        onClick={() => {
                          resetTransform()
                          centerView(1, 0)
                        }}
                        className="h-8 w-8 shadow-md"
                      >
                        <Maximize2 className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>画面にフィット</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>

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
            </>
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
                    <span className="font-medium">絞り:</span> F/{selectedPhoto.exif.aperture}
                  </div>
                )}
                {selectedPhoto.exif.shutterSpeed && (
                  <div>
                    <span className="font-medium">シャッター速度:</span>{' '}
                    {selectedPhoto.exif.shutterSpeed}
                  </div>
                )}
                {selectedPhoto.exif.focalLength && (
                  <div>
                    <span className="font-medium">焦点距離:</span> {selectedPhoto.exif.focalLength}
                    mm
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
