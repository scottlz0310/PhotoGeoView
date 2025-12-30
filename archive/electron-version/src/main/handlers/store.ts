import { ipcMain } from 'electron'
import Store from 'electron-store'
import { IPC_CHANNELS } from '../../types/ipc'

// Define the schema for our store
interface StoreSchema {
  windowBounds: {
    width: number
    height: number
    x?: number
    y?: number
  }
  panelLayout: {
    leftPanelSize: number
    middlePanelSize: number
    rightPanelSize: number
    fileBrowserSize: number
    thumbnailGridSize: number
    imagePreviewSize: number
    mapViewSize: number
  }
  panelVisibility: {
    fileBrowser: boolean
    thumbnailGrid: boolean
    exifPanel: boolean
    imagePreview: boolean
    mapView: boolean
  }
}

// Initialize the store
const store = new Store<StoreSchema>({
  defaults: {
    windowBounds: {
      width: 1200,
      height: 800,
    },
    panelLayout: {
      leftPanelSize: 25,
      middlePanelSize: 20,
      rightPanelSize: 55,
      fileBrowserSize: 40,
      thumbnailGridSize: 60,
      imagePreviewSize: 60,
      mapViewSize: 40,
    },
    panelVisibility: {
      fileBrowser: true,
      thumbnailGrid: true,
      exifPanel: true,
      imagePreview: true,
      mapView: true,
    },
  },
})

export function registerStoreHandlers(): void {
  ipcMain.handle(IPC_CHANNELS.GET_STORE_VALUE, (_event, key: string) => {
    return store.get(key)
  })

  ipcMain.handle(IPC_CHANNELS.SET_STORE_VALUE, (_event, key: string, value: unknown) => {
    store.set(key, value)
  })
}

export function getStore(): Store<StoreSchema> {
  return store
}
