import type React from 'react'
import { usePhotoStore } from '@/stores/photoStore'
import { useSettingsStore } from '@/stores/settingsStore'

// シャッター速度を分数表記に変換するヘルパー関数
function formatShutterSpeed(seconds: number): string {
  if (seconds >= 1) {
    return `${seconds}s`
  }
  const denominator = Math.round(1 / seconds)
  return `1/${denominator}s`
}

export function StatusBar(): React.ReactElement {
  const selectedPhoto = usePhotoStore((state) => state.selectedPhoto)
  const loadingStatus = usePhotoStore((state) => state.loadingStatus)
  const showExifDetails = useSettingsStore((state) => state.settings.display.showExifByDefault)

  return (
    <footer className="border-t bg-card px-4 py-1 text-xs text-muted-foreground">
      <div className="flex items-center justify-between h-6">
        <div className="flex items-center gap-4 overflow-hidden">
          {loadingStatus ? (
            <span className="font-medium text-foreground truncate">{loadingStatus}</span>
          ) : selectedPhoto ? (
            <>
              <span className="font-medium text-foreground truncate max-w-[200px]">
                {selectedPhoto.filename}
              </span>

              {showExifDetails && (
                <>
                  {selectedPhoto.exif?.datetime && (
                    <span className="flex items-center gap-1 truncate border-l border-border pl-3">
                      <span>📅</span>
                      <span>{new Date(selectedPhoto.exif.datetime).toLocaleString()}</span>
                    </span>
                  )}

                  {selectedPhoto.exif?.camera && (
                    <span className="flex items-center gap-1 truncate border-l border-border pl-3">
                      <span>📷</span>
                      <span>
                        {selectedPhoto.exif.camera.make} {selectedPhoto.exif.camera.model}
                      </span>
                    </span>
                  )}

                  {selectedPhoto.exif?.focalLength && (
                    <span className="flex items-center gap-1 border-l border-border pl-3">
                      <span>🔭</span>
                      <span>{selectedPhoto.exif.focalLength}mm</span>
                    </span>
                  )}

                  {selectedPhoto.exif?.aperture && (
                    <span className="flex items-center gap-1 border-l border-border pl-3">
                      <span>⭕</span>
                      <span>f/{selectedPhoto.exif.aperture}</span>
                    </span>
                  )}

                  {selectedPhoto.exif?.shutterSpeed && (
                    <span className="flex items-center gap-1 border-l border-border pl-3">
                      <span>⏱️</span>
                      <span>{formatShutterSpeed(selectedPhoto.exif.shutterSpeed)}</span>
                    </span>
                  )}

                  {selectedPhoto.exif?.iso && (
                    <span className="flex items-center gap-1 border-l border-border pl-3">
                      <span>ISO</span>
                      <span>{selectedPhoto.exif.iso}</span>
                    </span>
                  )}

                  {selectedPhoto.exif?.gps && (
                    <span className="flex items-center gap-1 border-l border-border pl-3 text-green-600 dark:text-green-400">
                      <span>📍</span>
                      <span>
                        {selectedPhoto.exif.gps.lat.toFixed(6)},{' '}
                        {selectedPhoto.exif.gps.lng.toFixed(6)}
                      </span>
                    </span>
                  )}

                  {selectedPhoto.exif?.width && selectedPhoto.exif.height && (
                    <span className="flex items-center gap-1 border-l border-border pl-3">
                      <span>📐</span>
                      <span>
                        {selectedPhoto.exif.width} × {selectedPhoto.exif.height}
                      </span>
                    </span>
                  )}
                </>
              )}
            </>
          ) : (
            <span>Ready</span>
          )}
        </div>
        <div className="flex items-center gap-4 flex-shrink-0">
          <span>v3.0.0</span>
        </div>
      </div>
    </footer>
  )
}
