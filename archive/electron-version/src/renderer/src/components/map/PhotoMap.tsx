import { Button } from '@renderer/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@renderer/components/ui/card'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@renderer/components/ui/tooltip'
import { useAppStore } from '@renderer/stores/appStore'
import { Minimize2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import type { ExifData } from '@/types/ipc'
import 'leaflet/dist/leaflet.css'

interface PhotoMapProps {
  exifData: ExifData | null
  filePath: string | null
}

export function PhotoMap({ exifData, filePath }: PhotoMapProps) {
  const { togglePanel } = useAppStore()
  const [isClient, setIsClient] = useState(false)
  const [iconFixed, setIconFixed] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  useEffect(() => {
    if (isClient && !iconFixed) {
      // Fix for default marker icons in Leaflet with webpack/vite
      // Use CDN URLs for marker icons
      import('leaflet')
        .then((L) => {
          ;(L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl = undefined
          L.Icon.Default.mergeOptions({
            iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
            iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
            shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
          })
          setIconFixed(true)
        })
        .catch((err) => {
          console.error('Failed to initialize Leaflet icons:', err)
          toast.error('Map Initialization Failed', {
            description: 'Could not load map marker icons',
          })
        })
    }
  }, [isClient, iconFixed])
  if (!filePath) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Map</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            Select an image to view its location on the map
          </p>
        </CardContent>
      </Card>
    )
  }

  if (!exifData?.gps) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Map</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            This image does not contain GPS coordinates
          </p>
        </CardContent>
      </Card>
    )
  }

  if (!isClient || !iconFixed) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Map</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        </CardContent>
      </Card>
    )
  }

  const { latitude, longitude } = exifData.gps
  const position: [number, number] = [latitude, longitude]

  return (
    <TooltipProvider>
      <Card className="h-full flex flex-col">
        <CardHeader className="flex-shrink-0">
          <div className="flex items-center justify-between">
            <CardTitle>Map</CardTitle>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button onClick={() => togglePanel('mapView')} size="icon" variant="ghost">
                  <Minimize2 className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Collapse panel</p>
              </TooltipContent>
            </Tooltip>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-hidden p-0">
          <DynamicMap position={position} filePath={filePath} exifData={exifData} />
        </CardContent>
      </Card>
    </TooltipProvider>
  )
}

// Component to update map center when position changes and handle resizing
// biome-ignore lint/suspicious/noExplicitAny: react-leaflet useMap is from dynamic import
function MapUpdater({ position, useMapHook }: { position: [number, number]; useMapHook: any }) {
  const map = useMapHook()

  // Update view when position changes
  useEffect(() => {
    if (map) {
      map.setView(position, 13)
    }
  }, [map, position])

  // Handle map resizing
  useEffect(() => {
    if (!map) return

    const resizeObserver = new ResizeObserver(() => {
      // Invalidate size to force Leaflet to redraw when container size changes
      map.invalidateSize()
    })

    // Observe the map container
    const container = map.getContainer()
    if (container) {
      resizeObserver.observe(container)
    }

    return () => {
      resizeObserver.disconnect()
    }
  }, [map])

  return null
}

// Dynamic import component to avoid SSR issues
function DynamicMap({
  position,
  filePath,
  exifData,
}: {
  position: [number, number]
  filePath: string
  exifData: ExifData
}) {
  // biome-ignore lint/suspicious/noExplicitAny: Dynamic import requires any type
  const [Components, setComponents] = useState<any>(null)
  // biome-ignore lint/suspicious/noExplicitAny: Leaflet icon type
  const [customIcon, setCustomIcon] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Dynamically import react-leaflet components and leaflet
    Promise.all([import('react-leaflet'), import('leaflet')])
      .then(([reactLeaflet, L]) => {
        setComponents({
          MapContainer: reactLeaflet.MapContainer,
          TileLayer: reactLeaflet.TileLayer,
          Marker: reactLeaflet.Marker,
          Popup: reactLeaflet.Popup,
          useMap: reactLeaflet.useMap,
        })

        // Create custom icon explicitly to avoid issues with default icon
        const icon = L.icon({
          iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
          iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
          shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
          iconSize: [25, 41],
          iconAnchor: [12, 41],
          popupAnchor: [1, -34],
          shadowSize: [41, 41],
        })
        setCustomIcon(icon)
      })
      .catch((err) => {
        console.error('Failed to load map components:', err)
        const errorMsg = err.message || 'Failed to load map components'
        setError(errorMsg)
        toast.error('Map Loading Failed', {
          description: errorMsg,
        })
      })
  }, [])

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4">
        <p className="text-sm text-destructive text-center">Failed to load map</p>
        <p className="text-xs text-muted-foreground text-center mt-2">{error}</p>
      </div>
    )
  }

  if (!Components) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  const { MapContainer, TileLayer, Marker, Popup, useMap } = Components
  const altitude = exifData.gps?.altitude

  return (
    <MapContainer
      center={position}
      zoom={13}
      scrollWheelZoom={true}
      style={{ height: '100%', width: '100%', minHeight: '300px' }}
    >
      <MapUpdater position={position} useMapHook={useMap} />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {customIcon && (
        <Marker position={position} icon={customIcon}>
          <Popup>
            <div className="text-sm">
              <p className="font-semibold mb-1">{filePath.split('/').pop() || 'Photo Location'}</p>
              <p className="text-xs text-muted-foreground">Latitude: {position[0].toFixed(6)}</p>
              <p className="text-xs text-muted-foreground">Longitude: {position[1].toFixed(6)}</p>
              {altitude !== undefined && (
                <p className="text-xs text-muted-foreground">Altitude: {altitude.toFixed(1)}m</p>
              )}
            </div>
          </Popup>
        </Marker>
      )}
    </MapContainer>
  )
}
