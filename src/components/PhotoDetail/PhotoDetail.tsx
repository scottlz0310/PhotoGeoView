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
    </div>
  )
}
