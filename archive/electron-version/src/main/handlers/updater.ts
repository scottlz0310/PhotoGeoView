import { type BrowserWindow, ipcMain } from 'electron'
import { autoUpdater } from 'electron-updater'
import { IPC_CHANNELS } from '../../types/ipc'

export function setupAutoUpdater(mainWindow: BrowserWindow): void {
  // Configure autoUpdater
  autoUpdater.autoDownload = false
  autoUpdater.autoInstallOnAppQuit = true

  // --- Event Listeners (Main Process -> Renderer) ---

  autoUpdater.on('checking-for-update', () => {
    // Optional: notify renderer if needed
  })

  autoUpdater.on('update-available', (info) => {
    mainWindow.webContents.send(IPC_CHANNELS.UPDATE_AVAILABLE, info)
  })

  autoUpdater.on('update-not-available', (info) => {
    mainWindow.webContents.send(IPC_CHANNELS.UPDATE_NOT_AVAILABLE, info)
  })

  autoUpdater.on('error', (err) => {
    mainWindow.webContents.send(IPC_CHANNELS.UPDATE_ERROR, err.message)
  })

  autoUpdater.on('download-progress', (progressObj) => {
    mainWindow.webContents.send(IPC_CHANNELS.DOWNLOAD_PROGRESS, progressObj)
  })

  autoUpdater.on('update-downloaded', (info) => {
    mainWindow.webContents.send(IPC_CHANNELS.UPDATE_DOWNLOADED, info)
  })

  // --- IPC Handlers (Renderer -> Main Process) ---

  ipcMain.handle(IPC_CHANNELS.CHECK_FOR_UPDATES, async () => {
    // Only check for updates in production or if explicitly enabled for dev
    if (!process.env.ELECTRON_IS_DEV) {
      return await autoUpdater.checkForUpdates()
    }
    return null
  })

  ipcMain.handle(IPC_CHANNELS.DOWNLOAD_UPDATE, async () => {
    return await autoUpdater.downloadUpdate()
  })

  ipcMain.handle(IPC_CHANNELS.QUIT_AND_INSTALL, () => {
    autoUpdater.quitAndInstall()
  })
}
