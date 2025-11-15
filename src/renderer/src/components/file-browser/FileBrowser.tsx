import type { FileEntry } from '@/types/ipc'
import { Button } from '@renderer/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@renderer/components/ui/card'
import { Input } from '@renderer/components/ui/input'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@renderer/components/ui/tooltip'
import { useAppStore } from '@renderer/stores/appStore'
import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, FolderOpen, Home } from 'lucide-react'
import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { FileList } from './FileList'

export function FileBrowser() {
  const { currentPath, setCurrentPath, clearSelectedFiles } = useAppStore()
  const [imageOnly, setImageOnly] = useState(true)

  // Check if running in Electron environment
  // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
  const isElectron = !!(window as any).api

  // Fetch directory contents
  const {
    data: result,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['directory-contents', currentPath, imageOnly],
    queryFn: async () => {
      if (!currentPath) return null
      // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
      return await (window as any).api.getDirectoryContents({
        path: currentPath,
        includeHidden: false,
        imageOnly,
      })
    },
    enabled: !!currentPath,
  })

  const files = result?.success ? result.data.entries : []

  const handleSelectDirectory = async () => {
    if (!isElectron) {
      toast.error('Electron Required', {
        description: 'This feature is only available in the Electron app.',
      })
      return
    }
    try {
      // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
      const result = await (window as any).api.selectDirectory()
      if (result.success && result.data) {
        setCurrentPath(result.data)
        clearSelectedFiles()
        toast.success('Folder Selected', {
          description: `Opened: ${result.data}`,
        })
      } else if (result.error) {
        toast.error('Failed to Select Folder', {
          description: result.error.message,
        })
      }
    } catch (error) {
      toast.error('Error', {
        description: error instanceof Error ? error.message : 'Failed to select directory',
      })
    }
  }

  const handleFileDoubleClick = (file: FileEntry) => {
    if (file.isDirectory) {
      setCurrentPath(file.path)
      clearSelectedFiles()
    }
  }

  const goToParentDirectory = () => {
    if (!currentPath) return
    const parentPath = currentPath.split('/').slice(0, -1).join('/')
    if (parentPath) {
      setCurrentPath(parentPath)
      clearSelectedFiles()
    }
  }

  const goToHomeDirectory = async () => {
    try {
      // On Linux/Mac, home is ~, on Windows it's typically C:\Users\username
      const homeDir = process.platform === 'win32' ? process.env.USERPROFILE : process.env.HOME
      if (homeDir) {
        setCurrentPath(homeDir)
        clearSelectedFiles()
        toast.success('Home Directory', {
          description: `Navigated to: ${homeDir}`,
        })
      } else {
        toast.error('Home Directory Not Found', {
          description: 'Could not determine home directory path',
        })
      }
    } catch (error) {
      toast.error('Navigation Error', {
        description: error instanceof Error ? error.message : 'Failed to navigate to home',
      })
    }
  }

  useEffect(() => {
    // Refetch when path changes
    if (currentPath) {
      refetch()
    }
  }, [currentPath, refetch])

  // Show error toast when query fails
  useEffect(() => {
    if (error) {
      toast.error('Failed to Load Directory', {
        description: error instanceof Error ? error.message : 'Unknown error occurred',
      })
    }
  }, [error])

  return (
    <TooltipProvider>
      <Card className="h-full flex flex-col">
        <CardHeader>
          <div className="flex items-center justify-between mb-4">
            <CardTitle>File Browser</CardTitle>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button onClick={handleSelectDirectory} size="sm">
                  <FolderOpen className="h-4 w-4 mr-2" />
                  Select Folder
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Open folder selection dialog</p>
              </TooltipContent>
            </Tooltip>
          </div>

          {currentPath && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="outline" size="icon" onClick={goToHomeDirectory}>
                      <Home className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Go to Home Directory</p>
                  </TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={goToParentDirectory}
                      disabled={!currentPath || currentPath === '/'}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Go to Parent Directory</p>
                  </TooltipContent>
                </Tooltip>
                <Input value={currentPath} readOnly className="flex-1 text-sm" />
              </div>

              <div className="flex items-center gap-2">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={imageOnly}
                    onChange={(e) => setImageOnly(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  Show images only
                </label>
              </div>
            </div>
          )}
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto">
          {!isElectron ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <FolderOpen className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground mb-2">Running in Browser Mode</p>
                <p className="text-sm text-muted-foreground">
                  File system access is only available in the Electron desktop app.
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  Please run: <code className="bg-muted px-2 py-1 rounded">pnpm dev</code>
                </p>
              </div>
            </div>
          ) : !currentPath ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <FolderOpen className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">Select a folder to browse</p>
              </div>
            </div>
          ) : (
            <FileList
              files={files}
              onFileDoubleClick={handleFileDoubleClick}
              isLoading={isLoading}
              error={error as Error | null}
            />
          )}
        </CardContent>
      </Card>
    </TooltipProvider>
  )
}
