import { Button } from '@renderer/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@renderer/components/ui/card'
import { Progress } from '@renderer/components/ui/progress'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@renderer/components/ui/tooltip'
import { useAppStore } from '@renderer/stores/appStore'
import { useQueryClient } from '@tanstack/react-query'
import { Loader2, Maximize2, Minimize2, Minus, Plus, RotateCcw, RotateCw, ZoomIn } from 'lucide-react'
import { useState } from 'react'
import { TransformComponent, TransformWrapper } from 'react-zoom-pan-pinch'
import { toast } from 'sonner'

interface ImagePreviewProps {
  filePath: string | null
}

export function ImagePreview({ filePath }: ImagePreviewProps) {
  console.log('=== ImagePreview Component ===')
  console.log('filePath prop:', filePath)
  console.log('==============================')

  const { togglePanel } = useAppStore()
  const [imageLoading, setImageLoading] = useState(false)
  const [isRotating, setIsRotating] = useState(false)
  const [imageKey, setImageKey] = useState(0) // Force re-render after rotation
  const queryClient = useQueryClient()
  // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
  const isElectron = !!(window as any).api

  const handleRotate = async (angle: 90 | 180 | 270 | -90) => {
    if (!filePath || isRotating) return

    setIsRotating(true)
    try {
      // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
      const result = await (window as any).api.rotateImage({ path: filePath, angle })

      if (result.success) {
        // Force image reload by changing key
        setImageKey((prev) => prev + 1)

        // Invalidate EXIF cache to force reload
        await queryClient.invalidateQueries({ queryKey: ['exif-for-map', filePath] })
        await queryClient.invalidateQueries({ queryKey: ['exif-data', filePath] })

        toast.success('Image Rotated', {
          description: `Rotated ${angle > 0 ? angle : 360 + angle}° clockwise`,
        })
      } else {
        toast.error('Rotation Failed', {
          description: result.error?.message || 'Failed to rotate image',
        })
      }
    } catch (error) {
      toast.error('Rotation Error', {
        description: error instanceof Error ? error.message : 'Unknown error occurred',
      })
    } finally {
      setIsRotating(false)
    }
  }

  if (!filePath) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Image Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            Select an image to preview
          </p>
        </CardContent>
      </Card>
    )
  }

  if (!isElectron) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Image Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            Image preview is only available in the Electron app
          </p>
        </CardContent>
      </Card>
    )
  }

  // Convert file path to local-file:// URL for Electron custom protocol
  // Add imageKey as timestamp to bust cache after rotation
  // Use encodeURI for the path to properly handle special characters while preserving slashes
  const imageUrl = filePath ? `local-file://${encodeURI(filePath)}?t=${imageKey}` : ''

  if (filePath) {
    console.log('=== ImagePreview URL Generation ===')
    console.log('Original file path:', filePath)
    console.log('Encoded URI:', encodeURI(filePath))
    console.log('Final image URL:', imageUrl)
    console.log('===================================')
  }

  return (
    <TooltipProvider>
      <Card className="h-full flex flex-col">
        <CardHeader className="flex-shrink-0">
          <CardTitle>Image Preview</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 overflow-hidden p-0">
          <TransformWrapper
            initialScale={1}
            minScale={0.1}
            maxScale={8}
            centerOnInit
            limitToBounds={false}
            doubleClick={{ mode: 'reset' }}
          >
            {({ zoomIn, zoomOut, resetTransform }) => (
              <>
                {/* Control buttons */}
                <div className="absolute top-20 right-6 z-10 flex flex-col gap-2">
                  {/* Panel collapse button */}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="secondary"
                        onClick={() => togglePanel('imagePreview')}
                        className="shadow-lg"
                      >
                        <Minimize2 className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>Collapse Panel</p>
                    </TooltipContent>
                  </Tooltip>

                  {/* Separator */}
                  <div className="h-px bg-border my-1" />

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="secondary"
                        onClick={() => zoomIn()}
                        className="shadow-lg"
                      >
                        <Plus className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>Zoom In</p>
                    </TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="secondary"
                        onClick={() => zoomOut()}
                        className="shadow-lg"
                      >
                        <Minus className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>Zoom Out</p>
                    </TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="secondary"
                        onClick={() => resetTransform()}
                        className="shadow-lg"
                      >
                        <Maximize2 className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>Reset Zoom</p>
                    </TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="secondary"
                        onClick={() => {
                          resetTransform()
                          zoomIn()
                        }}
                        className="shadow-lg"
                      >
                        <ZoomIn className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>Fit to Screen</p>
                    </TooltipContent>
                  </Tooltip>

                  {/* Separator */}
                  <div className="h-px bg-border my-1" />

                  {/* Rotation controls */}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="secondary"
                        onClick={() => handleRotate(-90)}
                        disabled={isRotating}
                        className="shadow-lg"
                      >
                        <RotateCcw className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>Rotate Left (90°)</p>
                    </TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="secondary"
                        onClick={() => handleRotate(90)}
                        disabled={isRotating}
                        className="shadow-lg"
                      >
                        <RotateCw className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>Rotate Right (90°)</p>
                    </TooltipContent>
                  </Tooltip>
                </div>

                {/* Image container */}
                <TransformComponent
                  wrapperClass="!w-full !h-full"
                  contentClass="!w-full !h-full flex items-center justify-center"
                >
                  {imageLoading && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-muted/50 backdrop-blur-sm gap-4">
                      <Loader2 className="h-12 w-12 animate-spin text-primary" />
                      <div className="w-1/3">
                        <Progress value={undefined} className="h-2" />
                      </div>
                      <p className="text-sm text-muted-foreground">Loading image...</p>
                    </div>
                  )}
                  <img
                    key={`${filePath}-${imageKey}`}
                    src={imageUrl}
                    alt={filePath.split('/').pop() || 'Preview'}
                    className="max-w-full max-h-full object-contain"
                    onLoadStart={() => setImageLoading(true)}
                    onLoad={() => setImageLoading(false)}
                    onError={(e) => {
                      setImageLoading(false)
                      console.error('Failed to load image:', filePath)
                      toast.error('Failed to Load Image', {
                        description: `Could not load: ${filePath.split('/').pop()}`,
                      })
                      ;(e.target as HTMLImageElement).style.display = 'none'
                    }}
                  />
                </TransformComponent>
              </>
            )}
          </TransformWrapper>
        </CardContent>
      </Card>
    </TooltipProvider>
  )
}
