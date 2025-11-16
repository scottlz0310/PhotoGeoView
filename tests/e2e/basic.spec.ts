import * as path from 'node:path'
import { type Page, _electron as electron, expect, test } from '@playwright/test'
import type { ElectronApplication } from '@playwright/test'

let electronApp: ElectronApplication
let page: Page

test.beforeAll(async () => {
  // Launch Electron app
  electronApp = await electron.launch({
    args: [path.join(__dirname, '../../out/main/index.js')],
  })

  // Wait for the first window
  page = await electronApp.firstWindow()
})

test.afterAll(async () => {
  await electronApp.close()
})

test.describe('PhotoGeoView Basic Flow', () => {
  test('should launch application successfully', async () => {
    // Check if window is visible
    expect(await page.isVisible('text=PhotoGeoView')).toBeTruthy()
  })

  test('should display main UI components', async () => {
    // Check for File Browser
    await expect(page.locator('text=File Browser')).toBeVisible()

    // Check for header
    await expect(page.locator('h1:has-text("PhotoGeoView")')).toBeVisible()
  })

  test('should have Select Folder button', async () => {
    await expect(page.locator('button:has-text("Select Folder")')).toBeVisible()
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

test.describe('Image Display', () => {
  test.skip('should display thumbnail grid when images are present', async () => {
    // This test requires actual image files
    // Skip for now as it needs test data setup
  })

  test.skip('should show image preview on selection', async () => {
    // This test requires actual image files
    // Skip for now as it needs test data setup
  })
})

test.describe('EXIF and Map', () => {
  test.skip('should display EXIF information for selected image', async () => {
    // This test requires actual image files with EXIF data
    // Skip for now as it needs test data setup
  })

  test.skip('should show map with GPS coordinates', async () => {
    // This test requires actual image files with GPS data
    // Skip for now as it needs test data setup
  })
})
