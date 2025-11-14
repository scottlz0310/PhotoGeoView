import type { ElectronAPI } from '@electron-toolkit/preload'

// Custom API type definition
// Will be populated with API methods as features are added
type API = Record<string, never>

declare global {
  interface Window {
    electron: ElectronAPI
    api: API
  }
}
