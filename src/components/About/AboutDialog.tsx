import { getVersion as getAppVersion, getName, getTauriVersion } from '@tauri-apps/api/app'
import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { BUILD_INFO } from '@/constants/buildInfo'
import packageJson from '../../../package.json'

interface AboutDialogProps {
  isOpen: boolean
  onOpenChange: (open: boolean) => void
}

type PackageJson = {
  name?: string
  version?: string
  dependencies?: Record<string, string>
  devDependencies?: Record<string, string>
}

const pkg = packageJson as PackageJson
const dependencies = pkg.dependencies ?? {}
const devDependencies = pkg.devDependencies ?? {}

const getDependencyVersion = (name: string): string =>
  dependencies[name] ?? devDependencies[name] ?? 'unknown'

const CORE_DEPENDENCIES = [
  { name: 'React', version: getDependencyVersion('react') },
  { name: 'React DOM', version: getDependencyVersion('react-dom') },
  { name: 'Leaflet', version: getDependencyVersion('leaflet') },
  { name: 'React Leaflet', version: getDependencyVersion('react-leaflet') },
  { name: 'Tauri API', version: getDependencyVersion('@tauri-apps/api') },
  { name: 'Zustand', version: getDependencyVersion('zustand') },
  { name: 'TanStack React Virtual', version: getDependencyVersion('@tanstack/react-virtual') },
]

const MAP_PROVIDERS = [
  { name: 'OpenStreetMap Standard', detail: 'Default tiles (OSM policy compliant)' },
  { name: 'Mapbox Satellite', detail: 'Optional layer (API key required)' },
  { name: 'Google Maps', detail: 'External link only (no API usage)' },
]

export function AboutDialog({ isOpen, onOpenChange }: AboutDialogProps): React.ReactElement {
  const { t } = useTranslation()
  const [appName, setAppName] = useState(pkg.name ?? 'PhotoGeoView')
  const [appVersion, setAppVersion] = useState(pkg.version ?? '0.0.0')
  const [tauriVersion, setTauriVersion] = useState('unknown')
  const mapboxToken = import.meta.env.VITE_MAPBOX_TOKEN as string | undefined
  const mapboxTokenStatus = mapboxToken
    ? `${t('about.mapboxTokenSet')} (${mapboxToken.length})`
    : t('about.mapboxTokenMissing')

  useEffect(() => {
    if (!isOpen) {
      return
    }
    const loadInfo = async () => {
      try {
        setAppName(await getName())
      } catch {
        // ignore
      }
      try {
        setAppVersion(await getAppVersion())
      } catch {
        // ignore
      }
      try {
        setTauriVersion(await getTauriVersion())
      } catch {
        // ignore
      }
    }
    loadInfo().catch(() => {
      // ignore
    })
  }, [isOpen])

  const origin = typeof window === 'undefined' ? 'unknown' : window.location.origin

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl bg-card text-card-foreground border-border shadow-2xl">
        <DialogHeader>
          <DialogTitle>{t('menu.about')}</DialogTitle>
          <DialogDescription>{t('about.description')}</DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <section>
            <h3 className="text-sm font-semibold text-foreground">{t('about.appInfo')}</h3>
            <dl className="mt-3 grid grid-cols-[140px_1fr] gap-x-3 gap-y-2 text-sm">
              <dt className="text-muted-foreground">{t('about.appName')}</dt>
              <dd className="text-foreground">{appName}</dd>
              <dt className="text-muted-foreground">{t('about.appVersion')}</dt>
              <dd className="text-foreground">{appVersion}</dd>
              <dt className="text-muted-foreground">Tauri</dt>
              <dd className="text-foreground">{tauriVersion}</dd>
              <dt className="text-muted-foreground">Build Time</dt>
              <dd className="text-foreground">{BUILD_INFO.buildTime}</dd>
              <dt className="text-muted-foreground">Git SHA</dt>
              <dd className="text-foreground">{BUILD_INFO.gitSha}</dd>
              <dt className="text-muted-foreground">WebView Origin</dt>
              <dd className="text-foreground">{origin}</dd>
              <dt className="text-muted-foreground">{t('about.mapboxToken')}</dt>
              <dd className="text-foreground">{mapboxTokenStatus}</dd>
            </dl>
          </section>

          <section>
            <h3 className="text-sm font-semibold text-foreground">{t('about.dependencies')}</h3>
            <dl className="mt-3 grid grid-cols-[200px_1fr] gap-x-3 gap-y-2 text-sm">
              {CORE_DEPENDENCIES.map((entry) => (
                <React.Fragment key={entry.name}>
                  <dt className="text-muted-foreground">{entry.name}</dt>
                  <dd className="text-foreground">{entry.version}</dd>
                </React.Fragment>
              ))}
            </dl>
          </section>

          <section>
            <h3 className="text-sm font-semibold text-foreground">{t('about.mapProviders')}</h3>
            <dl className="mt-3 grid grid-cols-[200px_1fr] gap-x-3 gap-y-2 text-sm">
              {MAP_PROVIDERS.map((entry) => (
                <React.Fragment key={entry.name}>
                  <dt className="text-muted-foreground">{entry.name}</dt>
                  <dd className="text-foreground">{entry.detail}</dd>
                </React.Fragment>
              ))}
            </dl>
            <p className="mt-3 text-xs text-muted-foreground">{t('about.googleMapsHint')}</p>
          </section>
        </div>

        <DialogFooter className="mt-2">
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
            {t('common.close')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
