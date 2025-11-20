import { electronAPI } from '@electron-toolkit/preload'
import { contextBridge, ipcRenderer } from 'electron'
import { IPC_CHANNELS, type IpcApi } from '../types/ipc'

// Custom APIs for renderer
const api: IpcApi = {
  // File System
  getDirectoryContents: (request) =>
    ipcRenderer.invoke(IPC_CHANNELS.GET_DIRECTORY_CONTENTS, request),
  getFileInfo: (request) => ipcRenderer.invoke(IPC_CHANNELS.GET_FILE_INFO, request),
  readImageMetadata: (request) => ipcRenderer.invoke(IPC_CHANNELS.READ_IMAGE_METADATA, request),
  selectDirectory: () => ipcRenderer.invoke(IPC_CHANNELS.SELECT_DIRECTORY),

  // Image Processing
  generateThumbnail: (request) => ipcRenderer.invoke(IPC_CHANNELS.GENERATE_THUMBNAIL, request),
  readExif: (request) => ipcRenderer.invoke(IPC_CHANNELS.READ_EXIF, request),
  rotateImage: (request) => ipcRenderer.invoke(IPC_CHANNELS.ROTATE_IMAGE, request),

  // Window
  minimizeWindow: () => ipcRenderer.send(IPC_CHANNELS.MINIMIZE_WINDOW),
  maximizeWindow: () => ipcRenderer.send(IPC_CHANNELS.MAXIMIZE_WINDOW),
  closeWindow: () => ipcRenderer.send(IPC_CHANNELS.CLOSE_WINDOW),

  // Theme
  getSystemTheme: () => ipcRenderer.invoke(IPC_CHANNELS.GET_SYSTEM_THEME),

  // Store
  getStoreValue: (key) => ipcRenderer.invoke(IPC_CHANNELS.GET_STORE_VALUE, key),
  setStoreValue: (key, value) => ipcRenderer.invoke(IPC_CHANNELS.SET_STORE_VALUE, key, value),
}

// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  // @ts-expect-error (define in dts)
  window.electron = electronAPI
  // @ts-expect-error (define in dts)
  window.api = api
}
