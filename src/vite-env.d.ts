/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BUILD_TIME?: string
  readonly VITE_GIT_SHA?: string
  readonly VITE_MAPBOX_TOKEN?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
