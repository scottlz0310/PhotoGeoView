import { readFile } from 'node:fs/promises'
import { join } from 'node:path'
import { electronApp, is, optimizer } from '@electron-toolkit/utils'
import { app, BrowserWindow, ipcMain, nativeTheme, protocol } from 'electron'
import { IPC_CHANNELS } from '../types/ipc'
import { getDirectoryContents, getFileInfo, selectDirectory } from './handlers/fileSystem'
import { generateThumbnail, readExif, rotateImage } from './handlers/imageProcessing'
import { getStore, registerStoreHandlers } from './handlers/store'

// Register custom protocol scheme as privileged before app is ready
protocol.registerSchemesAsPrivileged([
  {
    scheme: 'local-file',
    privileges: {
      secure: true,
      supportFetchAPI: true,
      bypassCSP: false,
      corsEnabled: false,
    },
  },
])

function createWindow(): void {
  const store = getStore()
  const bounds = store.get('windowBounds')

  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: bounds.width,
    height: bounds.height,
    x: bounds.x,
    y: bounds.y,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      nodeIntegration: false,
      contextIsolation: true,
    },
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  // Save window bounds on resize/move
  const saveBounds = () => {
    const bounds = mainWindow.getBounds()
    store.set('windowBounds', bounds)
  }

  mainWindow.on('resize', saveBounds)
  mainWindow.on('move', saveBounds)

  mainWindow.webContents.setWindowOpenHandler((details) => {
    // Open external links in the default browser
    require('electron').shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // HMR for renderer base on electron-vite cli.
  // Load the remote URL for development or the local html file for production.
  if (is.dev && process.env.ELECTRON_RENDERER_URL) {
    mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// Register IPC handlers
function registerIpcHandlers(): void {
  // File System handlers
  ipcMain.handle(IPC_CHANNELS.GET_DIRECTORY_CONTENTS, async (_event, request) => {
    return await getDirectoryContents(request)
  })

  ipcMain.handle(IPC_CHANNELS.GET_FILE_INFO, async (_event, request) => {
    return await getFileInfo(request)
  })

  ipcMain.handle(IPC_CHANNELS.SELECT_DIRECTORY, async () => {
    return await selectDirectory()
  })

  // Store handlers
  registerStoreHandlers()

  // Image Processing handlers
  ipcMain.handle(IPC_CHANNELS.GENERATE_THUMBNAIL, async (_event, request) => {
    return await generateThumbnail(request)
  })

  ipcMain.handle(IPC_CHANNELS.READ_EXIF, async (_event, request) => {
    return await readExif(request)
  })

  ipcMain.handle(IPC_CHANNELS.ROTATE_IMAGE, async (_event, request) => {
    return await rotateImage(request)
  })

  // Window handlers
  ipcMain.on(IPC_CHANNELS.MINIMIZE_WINDOW, (event) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    window?.minimize()
  })

  ipcMain.on(IPC_CHANNELS.MAXIMIZE_WINDOW, (event) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    if (window?.isMaximized()) {
      window.unmaximize()
    } else {
      window?.maximize()
    }
  })

  ipcMain.on(IPC_CHANNELS.CLOSE_WINDOW, (event) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    window?.close()
  })

  // Theme handlers
  ipcMain.handle(IPC_CHANNELS.GET_SYSTEM_THEME, () => {
    return {
      success: true,
      data: {
        shouldUseDarkColors: nativeTheme.shouldUseDarkColors,
        themeSource: nativeTheme.themeSource,
      },
    }
  })
}

// Register custom protocol for loading local files
function registerLocalFileProtocol(): void {
  protocol.handle('local-file', async (request) => {
    try {
      const url = request.url
      // Remove 'local-file://' prefix
      let filePath = url.replace('local-file://', '')

      // Remove query parameters
      const queryIndex = filePath.indexOf('?')
      if (queryIndex !== -1) {
        filePath = filePath.substring(0, queryIndex)
      }

      // Decode URI components
      filePath = decodeURIComponent(filePath)

      // Handle Windows file URLs: /C:/path -> C:/path
      if (
        process.platform === 'win32' &&
        filePath.startsWith('/') &&
        /^\/[A-Za-z]:/.test(filePath)
      ) {
        filePath = filePath.substring(1)
      }

      const data = await readFile(filePath)

      // Determine MIME type based on file extension
      const ext = filePath.split('.').pop()?.toLowerCase()
      const mimeTypes: Record<string, string> = {
        jpg: 'image/jpeg',
        jpeg: 'image/jpeg',
        png: 'image/png',
        gif: 'image/gif',
        webp: 'image/webp',
        bmp: 'image/bmp',
        svg: 'image/svg+xml',
        tiff: 'image/tiff',
        tif: 'image/tiff',
      }

      return new Response(data, {
        headers: { 'Content-Type': mimeTypes[ext || ''] || 'application/octet-stream' },
      })
    } catch (error) {
      console.error('Failed to load local file:', request.url, error)
      return new Response('Not Found', { status: 404 })
    }
  })
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  // Set app user model id for windows
  electronApp.setAppUserModelId('com.photogeoview')

  // Register custom protocol for local file access
  registerLocalFileProtocol()

  // Default open or close DevTools by F12 in development
  // and ignore CommandOrControl + R in production.
  // see https://github.com/alex8088/electron-toolkit/tree/master/packages/utils
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // Register IPC handlers
  registerIpcHandlers()

  createWindow()

  app.on('activate', () => {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.
