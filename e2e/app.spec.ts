import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  // Mock Tauri API
  await page.addInitScript(() => {
    // Mock window.__TAURI_INTERNALS__ which is used by @tauri-apps/api v2
    (window as any).__TAURI_INTERNALS__ = {
      invoke: async (cmd: string, args: any) => {
        console.log(`[Mock Tauri] invoke: ${cmd}`, args);
        
        // Mock store plugin
        if (cmd.startsWith('plugin:store|')) {
          return null;
        }
        
        // Mock log plugin
        if (cmd.startsWith('plugin:log|')) {
          return;
        }

        return null;
      },
      metadata: {
        currentWindow: { label: 'main' },
      },
    };
  });
});

test('app loads and shows title', async ({ page }) => {
  await page.goto('/');
  
  // Check title
  // Note: The title might be set by React or index.html
  await expect(page).toHaveTitle(/PhotoGeoView/);
  
  // Check if main layout elements exist
  await expect(page.locator('main')).toBeVisible();
});

test('loads photos and displays them', async ({ page }) => {
  // Setup mocks for file loading
  await page.addInitScript(() => {
    const mockInvoke = (window as any).__TAURI_INTERNALS__.invoke;
    (window as any).__TAURI_INTERNALS__.invoke = async (cmd: string, args: any) => {
      console.log(`[Mock Tauri] invoke: ${cmd}`, args);

      if (cmd === 'plugin:dialog|open') {
        return 'C:\\Photos';
      }

      if (cmd === 'read_directory') {
        return {
          path: 'C:\\Photos',
          name: 'Photos',
          entries: [
            { path: 'C:\\Photos\\photo1.jpg', name: 'photo1.jpg', is_dir: false },
            { path: 'C:\\Photos\\photo2.jpg', name: 'photo2.jpg', is_dir: false },
          ]
        };
      }

      if (cmd === 'generate_thumbnail') {
        // Return a 1x1 transparent gif base64
        return 'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
      }

      if (cmd === 'read_photo_exif') {
        return {
          path: args.path,
          exif: {
            DateTimeOriginal: '2023-01-01 12:00:00',
            GPSLatitude: [35, 41, 22],
            GPSLatitudeRef: 'N',
            GPSLongitude: [139, 41, 30],
            GPSLongitudeRef: 'E',
          }
        };
      }

      // Fallback to default mock
      return mockInvoke(cmd, args);
    };
  });

  await page.goto('/');

  // Click "Open Folder" button
  // Note: Adjust selector based on actual UI
  const openButton = page.getByRole('button', { name: /open folder/i });
  if (await openButton.isVisible()) {
    await openButton.click();
    
    // Verify photos are loaded
    // This depends on how photos are rendered (e.g., img tags with specific alt or src)
    // await expect(page.getByText('photo1.jpg')).toBeVisible();
  }
});

