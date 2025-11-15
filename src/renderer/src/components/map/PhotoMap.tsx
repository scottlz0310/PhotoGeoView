import type { ExifData } from '@/types/ipc'
import { Card, CardContent, CardHeader, CardTitle } from '@renderer/components/ui/card'
import { useEffect, useState } from 'react'
import 'leaflet/dist/leaflet.css'

interface PhotoMapProps {
  exifData: ExifData | null
  filePath: string | null
}

export function PhotoMap({ exifData, filePath }: PhotoMapProps) {
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
          // biome-ignore lint/performance/noDelete: Required for Leaflet icon fix
          delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
          L.Icon.Default.mergeOptions({
            iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
            iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
            shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
          })
          setIconFixed(true)
        })
        .catch((err) => {
          console.error('Failed to initialize Leaflet icons:', err)
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
    <Card className="h-full flex flex-col">
      <CardHeader className="flex-shrink-0">
        <CardTitle>Map</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-0">
        <DynamicMap position={position} filePath={filePath} exifData={exifData} />
      </CardContent>
    </Card>
  )
}

// Component to update map center when position changes
function MapUpdater({ position }: { position: [number, number] }) {
  // biome-ignore lint/suspicious/noExplicitAny: Dynamic import requires any type
  const [useMap, setUseMap] = useState<any>(null)

  useEffect(() => {
    import('react-leaflet').then((module) => {
      setUseMap(() => module.useMap)
    })
  }, [])

  const map = useMap ? useMap() : null

  useEffect(() => {
    if (map) {
      map.setView(position, 13)
    }
  }, [map, position])

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
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Dynamically import react-leaflet components
    import('react-leaflet')
      .then((module) => {
        setComponents({
          MapContainer: module.MapContainer,
          TileLayer: module.TileLayer,
          Marker: module.Marker,
          Popup: module.Popup,
        })
      })
      .catch((err) => {
        console.error('Failed to load react-leaflet:', err)
        setError(err.message || 'Failed to load map components')
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

  const { MapContainer, TileLayer, Marker, Popup } = Components
  const altitude = exifData.gps?.altitude

  return (
    <MapContainer
      center={position}
      zoom={13}
      scrollWheelZoom={true}
      style={{ height: '100%', width: '100%', minHeight: '300px' }}
    >
      <MapUpdater position={position} />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Marker position={position}>
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
    </MapContainer>
  )
}
