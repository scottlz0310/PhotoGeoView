import * as path from 'node:path'
import type { ElectronApplication } from '@playwright/test'
import { _electron as electron, expect, type Page, test } from '@playwright/test'
import { saveRendererCoverage } from './helpers/collect-coverage'

let electronApp: ElectronApplication
let page: Page

test.beforeAll(async () => {
  // Launch Electron app
  electronApp = await electron.launch({
    args: [path.join(__dirname, '../../out/main/index.js')],
  })

  // Wait for the main window (index.html)
  const windows = electronApp.windows()
  const mainWindow = windows.find((w) => w.url().includes('index.html'))

  if (mainWindow) {
    page = mainWindow
  } else {
    page = await electronApp.waitForEvent('window', (w) => w.url().includes('index.html'))
  }

  await page.waitForLoadState('domcontentloaded')
})

test.afterAll(async () => {
  await saveRendererCoverage(page)
  await electronApp.close()
})

test.describe('PhotoGeoView Basic Flow', () => {
  test('should launch application successfully', async () => {
    // Check if window is visible
    expect(await page.title()).toBe('PhotoGeoView')
  })

  test('should display main UI components', async () => {
    // Check for header
    await expect(page.locator('h1:has-text("PhotoGeoView")')).toBeVisible()

    // Check for menu bar items
    await expect(page.locator('button[role="menuitem"]:has-text("File")')).toBeVisible()
    await expect(page.locator('button[role="menuitem"]:has-text("View")')).toBeVisible()
    await expect(page.locator('button[role="menuitem"]:has-text("Settings")')).toBeVisible()
    await expect(page.locator('button[role="menuitem"]:has-text("Help")')).toBeVisible()
  })

  test('should have File menu with Open Folder option', async () => {
    // Click File menu
    await page.click('button[role="menuitem"]:has-text("File")')
    // Check for Open Folder menu item
    await expect(page.locator('[role="menuitem"]:has-text("Open Folder")')).toBeVisible()
    // Close menu by clicking elsewhere
    await page.keyboard.press('Escape')
  })

  test('should show browser mode message when no path selected', async () => {
    // Look for the message that appears when no folder is selected
    const noFolderMessage = page.locator('text=Select a folder to browse')
    await expect(noFolderMessage).toBeVisible()
  })
})

test.describe('File Browser Navigation', () => {
  test('should enable navigation buttons after selecting folder', async () => {
    // Note: This test would need a real folder selection
    // In a real E2E test, you might mock the file dialog or use a test folder
  })
})
