import type { LatLngExpression } from 'leaflet'
import L from 'leaflet'
import type React from 'react'
import { useEffect, useMemo, useState } from 'react'
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet'
import { usePhotoStore } from '@/stores/photoStore'

// Leafletのデフォルトアイコンを修正（Viteでの問題対応）
delete (L.Icon.Default.prototype as { _getIconUrl?: unknown })._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// シャッター速度を分数表記に変換するヘルパー関数
// 以前のオーバーレイ表示は削除済み
function formatShutterSpeed(seconds: number): string {
  if (seconds >= 1) {
    return `${seconds}s`
  }
  const denominator = Math.round(1 / seconds)
  return `1/${denominator}s`
}

export function MapView(): React.ReactElement {
  const { photos, selectPhoto } = usePhotoStore()
  const [mapKey, setMapKey] = useState(0)

  // GPS情報を持つ写真のみフィルタリング
  const photosWithGps = useMemo(() => {
    return photos.filter((photo) => photo.exif?.gps)
  }, [photos])

  // 地図の中心とズームレベルを計算
  const { center, zoom } = useMemo(() => {
    if (photosWithGps.length === 0) {
      // デフォルト: 東京
      return { center: [35.6762, 139.6503] as LatLngExpression, zoom: 10 }
    }

    if (photosWithGps.length === 1) {
      const gps = photosWithGps[0]?.exif?.gps
      if (gps) {
        return { center: [gps.lat, gps.lng] as LatLngExpression, zoom: 15 }
      }
    }

    // 複数の写真がある場合、中心を計算
    let minLat = Number.POSITIVE_INFINITY
    let maxLat = Number.NEGATIVE_INFINITY
    let minLng = Number.POSITIVE_INFINITY
    let maxLng = Number.NEGATIVE_INFINITY

    for (const photo of photosWithGps) {
      const gps = photo.exif?.gps
      if (gps) {
        minLat = Math.min(minLat, gps.lat)
        maxLat = Math.max(maxLat, gps.lat)
        minLng = Math.min(minLng, gps.lng)
        maxLng = Math.max(maxLng, gps.lng)
      }
    }

    const centerLat = (minLat + maxLat) / 2
    const centerLng = (minLng + maxLng) / 2

    return { center: [centerLat, centerLng] as LatLngExpression, zoom: 10 }
  }, [photosWithGps])

  // 写真が変更されたら地図を再レンダリング
  useEffect(() => {
    setMapKey((prev) => prev + 1)
  }, [])

  if (photosWithGps.length === 0) {
    return (
      <div className="relative h-full w-full bg-muted">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <h2 className="mb-2 text-xl font-semibold text-foreground">Map View</h2>
            <p className="text-sm text-muted-foreground">
              Load photos with GPS data to see them on the map
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative h-full w-full">
      <MapContainer
        key={mapKey}
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {photosWithGps.map((photo) => {
          const gps = photo.exif?.gps
          if (!gps) {
            return null
          }

          return (
            <Marker
              key={photo.path}
              position={[gps.lat, gps.lng]}
              eventHandlers={{
                click: () => selectPhoto(photo.path),
              }}
            >
              <Popup>
                <div className="text-sm min-w-[200px]">
                  <div className="font-semibold mb-2">{photo.filename}</div>

                  <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">
                    {photo.exif?.datetime && (
                      <>
                        <div className="text-muted-foreground font-medium">Date:</div>
                        <div>{new Date(photo.exif.datetime).toLocaleString()}</div>
                      </>
                    )}

                    {photo.exif?.camera && (
                      <>
                        <div className="text-muted-foreground font-medium">Camera:</div>
                        <div>
                          {photo.exif.camera.make} {photo.exif.camera.model}
                        </div>
                      </>
                    )}

                    {(photo.exif?.aperture || photo.exif?.shutterSpeed || photo.exif?.iso) && (
                      <>
                        <div className="text-muted-foreground font-medium">Settings:</div>
                        <div>
                          {photo.exif?.aperture && `f/${photo.exif.aperture} `}
                          {photo.exif?.shutterSpeed &&
                            `${formatShutterSpeed(photo.exif.shutterSpeed)} `}
                          {photo.exif?.iso && `ISO${photo.exif.iso}`}
                        </div>
                      </>
                    )}

                    {photo.exif?.focalLength && (
                      <>
                        <div className="text-muted-foreground font-medium">Focal:</div>
                        <div>{photo.exif.focalLength}mm</div>
                      </>
                    )}

                    {photo.exif?.width && photo.exif?.height && (
                      <>
                        <div className="text-muted-foreground font-medium">Size:</div>
                        <div>
                          {photo.exif.width} x {photo.exif.height}
                        </div>
                      </>
                    )}

                    <div className="text-muted-foreground font-medium">Location:</div>
                    <div>
                      {gps.lat.toFixed(6)}, {gps.lng.toFixed(6)}
                    </div>
                  </div>
                </div>
              </Popup>
            </Marker>
          )
        })}
      </MapContainer>
    </div>
  )
}
