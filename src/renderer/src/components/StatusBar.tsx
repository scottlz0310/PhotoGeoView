import { useAppStore } from '@renderer/stores/appStore'
import { useQuery } from '@tanstack/react-query'
import { Camera, Clock, MapPin, Aperture } from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@renderer/components/ui/tooltip'

interface StatusBarProps {
  filePath: string | null
}

export function StatusBar({ filePath }: StatusBarProps) {
  const { statusBarItems } = useAppStore()
  // biome-ignore lint/suspicious/noExplicitAny: Electron API
  const isElectron = !!(window as any).api

  const { data: result } = useQuery({
    queryKey: ['exif-statusbar', filePath],
    queryFn: async () => {
      if (!filePath || !isElectron) return null
      // biome-ignore lint/suspicious/noExplicitAny: Electron API
      return await (window as any).api.readExif({ path: filePath })
    },
    enabled: !!filePath && isElectron,
    staleTime: 5 * 60 * 1000,
  })

  const exifData = result?.success ? result.data.exif : null

  if (!filePath) {
    return (
      <footer className="flex-shrink-0 border-t bg-card px-4 py-1.5 text-xs text-muted-foreground">
        No image selected
      </footer>
    )
  }

  const fileName = filePath.split(/[\\/]/).pop() || ''

  return (
    <TooltipProvider>
      <footer className="flex-shrink-0 border-t bg-card px-4 py-1.5">
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          {/* File name */}
          <span className="font-medium text-foreground truncate max-w-[200px]">{fileName}</span>

          {exifData && (
            <>
              {/* Camera */}
              {statusBarItems.camera && exifData.camera?.model && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="flex items-center gap-1">
                      <Camera className="h-3 w-3" />
                      {exifData.camera.model}
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Camera: {exifData.camera.make} {exifData.camera.model}</p>
                    {exifData.camera.lens && <p>Lens: {exifData.camera.lens}</p>}
                  </TooltipContent>
                </Tooltip>
              )}

              {/* Exposure */}
              {statusBarItems.exposure && exifData.exposure && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="flex items-center gap-1">
                      <Aperture className="h-3 w-3" />
                      {exifData.exposure.aperture && `f/${exifData.exposure.aperture}`}
                      {exifData.exposure.shutterSpeed && ` ${exifData.exposure.shutterSpeed}`}
                      {exifData.exposure.iso && ` ISO${exifData.exposure.iso}`}
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Aperture: f/{exifData.exposure.aperture}</p>
                    <p>Shutter: {exifData.exposure.shutterSpeed}</p>
                    <p>ISO: {exifData.exposure.iso}</p>
                    {exifData.exposure.focalLength && <p>Focal: {exifData.exposure.focalLength}mm</p>}
                  </TooltipContent>
                </Tooltip>
              )}

              {/* GPS */}
              {statusBarItems.gps && exifData.gps && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="flex items-center gap-1 text-green-600">
                      <MapPin className="h-3 w-3" />
                      GPS
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Lat: {exifData.gps.latitude.toFixed(6)}</p>
                    <p>Lng: {exifData.gps.longitude.toFixed(6)}</p>
                    {exifData.gps.altitude && <p>Alt: {exifData.gps.altitude.toFixed(1)}m</p>}
                  </TooltipContent>
                </Tooltip>
              )}

              {/* Date */}
              {statusBarItems.datetime && exifData.timestamp && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {new Date(exifData.timestamp).toLocaleDateString()}
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{new Date(exifData.timestamp).toLocaleString()}</p>
                  </TooltipContent>
                </Tooltip>
              )}

              {/* Dimensions */}
              {statusBarItems.dimensions && exifData.width && exifData.height && (
                <span>{exifData.width} × {exifData.height}</span>
              )}
            </>
          )}
        </div>
      </footer>
    </TooltipProvider>
  )
}
