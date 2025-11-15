import { Button } from '@renderer/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@renderer/components/ui/card'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@renderer/components/ui/tooltip'
import { Minus, Plus, RotateCw, ZoomIn } from 'lucide-react'
import { TransformComponent, TransformWrapper } from 'react-zoom-pan-pinch'
import { toast } from 'sonner'

interface ImagePreviewProps {
  filePath: string | null
}

export function ImagePreview({ filePath }: ImagePreviewProps) {
  // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
  const isElectron = !!(window as any).api

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
  const imageUrl = `local-file://${filePath}`

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex-shrink-0">
        <CardTitle>Image Preview</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-0">
        <TooltipProvider>
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
                        <RotateCw className="h-4 w-4" />
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
                </div>

                {/* Image container */}
                <TransformComponent
                  wrapperClass="!w-full !h-full"
                  contentClass="!w-full !h-full flex items-center justify-center"
                >
                  <img
                    src={imageUrl}
                    alt={filePath.split('/').pop() || 'Preview'}
                    className="max-w-full max-h-full object-contain"
                    onError={(e) => {
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
        </TooltipProvider>
      </CardContent>
    </Card>
  )
}
