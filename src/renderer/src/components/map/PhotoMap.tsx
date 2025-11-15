import { Card, CardContent, CardHeader, CardTitle } from '@renderer/components/ui/card'
import type { ExifData } from '@/types/ipc'
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Fix for default marker icons in Leaflet with webpack/vite
// Use CDN URLs for marker icons
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

interface PhotoMapProps {
  exifData: ExifData | null
  filePath: string | null
}

export function PhotoMap({ exifData, filePath }: PhotoMapProps) {
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

  const { latitude, longitude } = exifData.gps
  const position: [number, number] = [latitude, longitude]

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex-shrink-0">
        <CardTitle>Map</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-0">
        <MapContainer
          center={position}
          zoom={13}
          scrollWheelZoom={true}
          className="h-full w-full"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={position}>
            <Popup>
              <div className="text-sm">
                <p className="font-semibold mb-1">
                  {filePath.split('/').pop() || 'Photo Location'}
                </p>
                <p className="text-xs text-muted-foreground">
                  Latitude: {latitude.toFixed(6)}
                </p>
                <p className="text-xs text-muted-foreground">
                  Longitude: {longitude.toFixed(6)}
                </p>
                {exifData.gps.altitude !== undefined && (
                  <p className="text-xs text-muted-foreground">
                    Altitude: {exifData.gps.altitude.toFixed(1)}m
                  </p>
                )}
              </div>
            </Popup>
          </Marker>
        </MapContainer>
      </CardContent>
    </Card>
  )
}
