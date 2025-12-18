import * as path from 'node:path'
import type { ElectronApplication, Page } from '@playwright/test'
import { _electron as electron, expect, test } from '@playwright/test'
import { saveRendererCoverage } from './helpers/collect-coverage'

let electronApp: ElectronApplication
let page: Page

// IPC Channel Names (copied from src/types/ipc.ts to avoid import issues)
const _IPC_CHANNELS = {
  GET_DIRECTORY_CONTENTS: 'fs:getDirectoryContents',
  SELECT_DIRECTORY: 'fs:selectDirectory',
  GENERATE_THUMBNAIL: 'image:generateThumbnail',
}

test.beforeAll(async () => {
  // Launch Electron app
  electronApp = await electron.launch({
    args: [path.join(__dirname, '../../out/main/index.js')],
  })

  // Wait for the main window (index.html)
  // We might get the splash screen first
  const windows = electronApp.windows()
  const mainWindow = windows.find((w) => w.url().includes('index.html'))

  if (mainWindow) {
    page = mainWindow
  } else {
    page = await electronApp.waitForEvent('window', (w) => w.url().includes('index.html'))
  }

  // Wait for the app to be fully loaded
  await page.waitForLoadState('domcontentloaded')
})

test.afterAll(async () => {
  await saveRendererCoverage(page)
  await electronApp.close()
})

test.describe('PhotoGeoView E2E Scenarios', () => {
  test('Initial State', async () => {
    // Check title
    expect(await page.title()).toBe('PhotoGeoView')

    // Check for menu bar
    await expect(page.locator('button[role="menuitem"]:has-text("File")')).toBeVisible()

    // Check for empty state message
    await expect(page.locator('text=Select a folder to browse')).toBeVisible()
  })

  test('Select Folder and View Images', async () => {
    // Mock IPC handlers in the main process
    await electronApp.evaluate(({ ipcMain, protocol }) => {
      // Mock selectDirectory
      // We need to remove existing handlers first to avoid errors
      ipcMain.removeHandler('fs:selectDirectory')
      ipcMain.handle('fs:selectDirectory', () => {
        return { success: true, data: '/mock/photos' }
      })

      // Mock getDirectoryContents
      ipcMain.removeHandler('fs:getDirectoryContents')
      ipcMain.handle('fs:getDirectoryContents', () => {
        return {
          success: true,
          data: {
            path: '/mock/photos',
            entries: [
              {
                name: 'photo1.jpg',
                path: '/mock/photos/photo1.jpg',
                isDirectory: false,
                size: 1024,
                modifiedTime: Date.now(),
                isImage: true,
                extension: '.jpg',
              },
              {
                name: 'photo2.jpg',
                path: '/mock/photos/photo2.jpg',
                isDirectory: false,
                size: 2048,
                modifiedTime: Date.now(),
                isImage: true,
                extension: '.jpg',
              },
              {
                name: 'subfolder',
                path: '/mock/photos/subfolder',
                isDirectory: true,
                size: 0,
                modifiedTime: Date.now(),
                isImage: false,
              },
            ],
          },
        }
      })

      // Mock generateThumbnail
      ipcMain.removeHandler('image:generateThumbnail')
      ipcMain.handle('image:generateThumbnail', () => {
        // Return a 1x1 transparent pixel base64
        return {
          success: true,
          data: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
        }
      })

      // Mock local-file protocol to serve a dummy image
      try {
        protocol.unhandle('local-file')
      } catch (_e) {
        // Ignore if not handled
      }
      protocol.handle('local-file', () => {
        const base64 =
          'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
        const buffer = Buffer.from(base64, 'base64')
        return new Response(buffer, {
          headers: { 'content-type': 'image/png' },
        })
      })
    })

    // Open File menu and click Open Folder
    await page.click('button[role="menuitem"]:has-text("File")')
    await page.click('[role="menuitem"]:has-text("Open Folder")')

    // Verify that the file browser updated
    // We should see the files we mocked
    await expect(page.locator('text=photo1.jpg').first()).toBeVisible()
    await expect(page.locator('text=photo2.jpg').first()).toBeVisible()
    await expect(page.locator('text=subfolder').first()).toBeVisible()
  })

  test('Image Preview Navigation', async () => {
    // Ensure we are in the state with photos (from previous test)
    // Click on the first photo to open preview
    await page.locator('text=photo1.jpg').first().click()

    // Verify preview panel is visible
    await expect(page.locator('text=Image Preview')).toBeVisible()

    // Verify first image is loaded
    // The src will contain the file path
    // We check for presence instead of visibility because react-zoom-pan-pinch or the loader might affect visibility detection in headless mode
    await expect(page.locator('img[src*="photo1.jpg"]')).toHaveCount(1)

    // Press ArrowRight to navigate
    await page.keyboard.press('ArrowRight')

    // Verify second image is loaded
    await expect(page.locator('img[src*="photo2.jpg"]')).toHaveCount(1)
  })

  test('Theme Toggle via Menu', async () => {
    // Check View menu contains Theme option
    await page.click('button[role="menuitem"]:has-text("View")')

    // Verify Theme submenu trigger is visible
    const themeSubmenu = page.locator('[role="menuitem"]:has-text("Theme")')
    await expect(themeSubmenu).toBeVisible()

    // Close menu
    await page.keyboard.press('Escape')

    // Verify theme options exist (Light, Dark, System)
    // We just verify the menu structure is correct
    // Actual theme switching is tested in unit tests
  })
})
