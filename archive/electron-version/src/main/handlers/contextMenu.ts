import { BrowserWindow, Menu, MenuItem, shell } from 'electron'
import {
  failure,
  type Result,
  type ShowContextMenuRequest,
  ShowContextMenuRequestSchema,
  success,
} from '../../types/ipc'

export async function showContextMenu(request: ShowContextMenuRequest): Promise<Result<void>> {
  try {
    const validated = ShowContextMenuRequestSchema.parse(request)
    const { type, path: filePath } = validated
    const window = BrowserWindow.getFocusedWindow()

    if (!window) {
      return failure(new Error('No focused window'))
    }

    const menu = new Menu()

    if (type === 'file' || type === 'folder') {
      if (filePath) {
        menu.append(
          new MenuItem({
            label: 'Open',
            click: () => {
              shell.openPath(filePath)
            },
          })
        )

        menu.append(
          new MenuItem({
            label: 'Show in Explorer',
            click: () => {
              shell.showItemInFolder(filePath)
            },
          })
        )

        menu.append(new MenuItem({ type: 'separator' }))

        menu.append(
          new MenuItem({
            label: 'Copy Path',
            click: () => {
              // We can't easily access clipboard from main process without requiring it
              // But we can send an event back to renderer or just use electron's clipboard
              require('electron').clipboard.writeText(filePath)
            },
          })
        )
      }
    } else if (type === 'background') {
      menu.append(
        new MenuItem({
          label: 'Refresh',
          click: () => {
            // Send event to renderer to refresh
            window.webContents.send('menu:refresh')
          },
        })
      )

      menu.append(new MenuItem({ type: 'separator' }))

      menu.append(
        new MenuItem({
          label: 'Up to Parent',
          click: () => {
            window.webContents.send('menu:go-up')
          },
        })
      )
    }

    menu.popup({ window })
    return success(undefined)
  } catch (error) {
    return failure(error instanceof Error ? error : new Error(String(error)))
  }
}
