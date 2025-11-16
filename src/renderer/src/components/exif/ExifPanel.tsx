import { Badge } from '@renderer/components/ui/badge'
import { Button } from '@renderer/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@renderer/components/ui/card'
import { Separator } from '@renderer/components/ui/separator'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@renderer/components/ui/tooltip'
import { useAppStore } from '@renderer/stores/appStore'
import { useQuery } from '@tanstack/react-query'
import { Camera, MapPin, Minimize2, Settings } from 'lucide-react'
import { useEffect } from 'react'
import { toast } from 'sonner'

interface ExifPanelProps {
  filePath: string | null
}

export function ExifPanel({ filePath }: ExifPanelProps) {
  const { togglePanel } = useAppStore()
  // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
  const isElectron = !!(window as any).api

  const {
    data: result,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['exif', filePath],
    queryFn: async () => {
      if (!filePath || !isElectron) return null
      // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
      return await (window as any).api.readExif({ path: filePath })
    },
    enabled: !!filePath && isElectron,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const exifData = result?.success ? result.data.exif : null

  // Show error toast when EXIF read fails
  useEffect(() => {
    if (error) {
      toast.error('Failed to Read EXIF Data', {
        description: error instanceof Error ? error.message : 'Unknown error occurred',
      })
    }
  }, [error])

  if (!filePath) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>EXIF Information</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            Select an image to view EXIF data
          </p>
        </CardContent>
      </Card>
    )
  }

  if (!isElectron) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>EXIF Information</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            EXIF reading is only available in the Electron app
          </p>
        </CardContent>
      </Card>
    )
  }

  if (isLoading) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>EXIF Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>EXIF Information</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive text-center py-8">
            Error loading EXIF data: {(error as Error).message}
          </p>
        </CardContent>
      </Card>
    )
  }

  if (!exifData) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>EXIF Information</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">No EXIF data available</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <TooltipProvider>
      <Card className="h-full">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>EXIF Information</CardTitle>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  onClick={() => togglePanel('exifPanel')}
                  size="icon"
                  variant="ghost"
                >
                  <Minimize2 className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Collapse panel</p>
              </TooltipContent>
            </Tooltip>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
        {/* Camera Information */}
        {exifData.camera && (
          <>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Camera className="h-4 w-4 text-muted-foreground" />
                <h3 className="text-sm font-semibold">Camera</h3>
              </div>
              <div className="space-y-2 pl-6">
                {exifData.camera.make && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Make</span>
                    <Badge variant="secondary">{exifData.camera.make}</Badge>
                  </div>
                )}
                {exifData.camera.model && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Model</span>
                    <Badge variant="secondary">{exifData.camera.model}</Badge>
                  </div>
                )}
                {exifData.camera.lens && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Lens</span>
                    <Badge variant="secondary">{exifData.camera.lens}</Badge>
                  </div>
                )}
              </div>
            </div>
            <Separator />
          </>
        )}

        {/* Exposure Settings */}
        {exifData.exposure && (
          <>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Settings className="h-4 w-4 text-muted-foreground" />
                <h3 className="text-sm font-semibold">Exposure</h3>
              </div>
              <div className="space-y-2 pl-6">
                {exifData.exposure.iso !== undefined && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">ISO</span>
                    <Badge variant="outline">{exifData.exposure.iso}</Badge>
                  </div>
                )}
                {exifData.exposure.aperture !== undefined && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Aperture</span>
                    <Badge variant="outline">f/{exifData.exposure.aperture}</Badge>
                  </div>
                )}
                {exifData.exposure.shutterSpeed && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Shutter</span>
                    <Badge variant="outline">{exifData.exposure.shutterSpeed}</Badge>
                  </div>
                )}
                {exifData.exposure.focalLength !== undefined && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Focal Length</span>
                    <Badge variant="outline">{exifData.exposure.focalLength}mm</Badge>
                  </div>
                )}
              </div>
            </div>
            <Separator />
          </>
        )}

        {/* GPS Information */}
        {exifData.gps && (
          <>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-muted-foreground" />
                <h3 className="text-sm font-semibold">Location</h3>
              </div>
              <div className="space-y-2 pl-6">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Latitude</span>
                  <code className="text-xs bg-muted px-2 py-1 rounded">
                    {exifData.gps.latitude.toFixed(6)}
                  </code>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Longitude</span>
                  <code className="text-xs bg-muted px-2 py-1 rounded">
                    {exifData.gps.longitude.toFixed(6)}
                  </code>
                </div>
                {exifData.gps.altitude !== undefined && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Altitude</span>
                    <Badge variant="outline">{exifData.gps.altitude.toFixed(1)}m</Badge>
                  </div>
                )}
              </div>
            </div>
            <Separator />
          </>
        )}

        {/* Image Metadata */}
        <div className="space-y-2">
          {exifData.timestamp && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Date Taken</span>
              <span className="text-xs">{new Date(exifData.timestamp).toLocaleString()}</span>
            </div>
          )}
          {exifData.width && exifData.height && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Dimensions</span>
              <Badge variant="secondary">
                {exifData.width} × {exifData.height}
              </Badge>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
    </TooltipProvider>
  )
}
