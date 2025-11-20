import { FileFilters } from '@renderer/components/filters/FileFilters'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@renderer/components/ui/breadcrumb'
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
import {
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  ChevronLeft,
  FolderOpen,
  Home,
  Minimize2,
  RotateCw,
  Search,
  X,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import type { FileEntry } from '@/types/ipc'
import { FileList } from './FileList'

export function FileBrowser() {
  const {
    currentPath,
    navigateToPath,
    canGoBack,
    canGoForward,
    goBack,
    goForward,
    clearSelectedFiles,
    filters,
    togglePanel,
  } = useAppStore()
  const [imageOnly, setImageOnly] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

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

  // Filter files based on search query and filters
  const filteredFiles = useMemo(() => {
    let filtered = files

    // Apply search query filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter((file) => file.name.toLowerCase().includes(query))
    }

    // Apply date range filter
    if (filters.dateFrom || filters.dateTo) {
      filtered = filtered.filter((file) => {
        if (!file.modifiedTime) return false

        const fileDate = new Date(file.modifiedTime)

        if (filters.dateFrom && fileDate < filters.dateFrom) {
          return false
        }
        if (filters.dateTo) {
          // Set end of day for dateTo
          const endOfDay = new Date(filters.dateTo)
          endOfDay.setHours(23, 59, 59, 999)
          if (fileDate > endOfDay) {
            return false
          }
        }
        return true
      })
    }

    return filtered
  }, [files, searchQuery, filters])

  // Parse current path into breadcrumb segments
  const pathSegments = useMemo(() => {
    if (!currentPath) return []

    // Normalize path separators to forward slashes for consistent handling
    const normalizedPath = currentPath.replace(/\\/g, '/')
    const segments = normalizedPath.split('/').filter(Boolean)

    // Check if it's a Windows path (starts with drive letter)
    const isWindowsPath = /^[a-zA-Z]:/.test(normalizedPath)

    return segments.map((segment, index) => {
      // Reconstruct path
      const pathPrefix = isWindowsPath ? '' : '/'
      const segmentPath = pathPrefix + segments.slice(0, index + 1).join('/')

      return {
        name: segment,
        path: segmentPath,
      }
    })
  }, [currentPath])

  const handleBreadcrumbClick = (path: string) => {
    navigateToPath(path)
    clearSelectedFiles()
  }

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
        navigateToPath(result.data)
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
      navigateToPath(file.path)
      clearSelectedFiles()
    }
  }

  const goToParentDirectory = () => {
    if (!currentPath) return

    const normalizedPath = currentPath.replace(/\\/g, '/')
    const segments = normalizedPath.split('/').filter(Boolean)

    if (segments.length === 0) return

    const isWindowsPath = /^[a-zA-Z]:/.test(normalizedPath)

    // If it's a Windows drive root (e.g. C: or C:/), we can't go up
    if (isWindowsPath && segments.length === 1) return

    // If it's a Unix root subdir (e.g. /usr), going up means going to /
    if (!isWindowsPath && segments.length === 1) {
      navigateToPath('/')
      clearSelectedFiles()
      return
    }

    const parentSegments = segments.slice(0, -1)
    const pathPrefix = isWindowsPath ? '' : '/'
    const parentPath = pathPrefix + parentSegments.join('/')

    if (parentPath) {
      navigateToPath(parentPath)
      clearSelectedFiles()
    } else if (!isWindowsPath) {
      // Fallback for Unix root
      navigateToPath('/')
      clearSelectedFiles()
    }
  }

  const goToHomeDirectory = async () => {
    try {
      // On Linux/Mac, home is ~, on Windows it's typically C:\Users\username
      const homeDir = process.platform === 'win32' ? process.env.USERPROFILE : process.env.HOME
      if (homeDir) {
        navigateToPath(homeDir)
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
            <div className="flex items-center gap-2">
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
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button onClick={() => togglePanel('fileBrowser')} size="icon" variant="ghost">
                    <Minimize2 className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Collapse panel</p>
                </TooltipContent>
              </Tooltip>
            </div>
          </div>

          {currentPath && (
            <div className="space-y-3">
              {/* Navigation Buttons */}
              <div className="flex items-center gap-2">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="outline" size="icon" onClick={goBack} disabled={!canGoBack()}>
                      <ArrowLeft className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Go Back</p>
                  </TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={goForward}
                      disabled={!canGoForward()}
                    >
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Go Forward</p>
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
                      <ArrowUp className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Up to Parent Directory</p>
                  </TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => refetch()}
                      disabled={isLoading}
                    >
                      <RotateCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Refresh</p>
                  </TooltipContent>
                </Tooltip>

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
              </div>

              {/* Breadcrumb Path */}
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem>
                    <BreadcrumbLink
                      onClick={() => handleBreadcrumbClick('/')}
                      className="cursor-pointer"
                    >
                      Root
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  {pathSegments.map((segment, index) => (
                    <span key={segment.path} className="flex items-center">
                      <BreadcrumbSeparator />
                      <BreadcrumbItem>
                        {index === pathSegments.length - 1 ? (
                          <BreadcrumbPage>{segment.name}</BreadcrumbPage>
                        ) : (
                          <BreadcrumbLink
                            onClick={() => handleBreadcrumbClick(segment.path)}
                            className="cursor-pointer"
                          >
                            {segment.name}
                          </BreadcrumbLink>
                        )}
                      </BreadcrumbItem>
                    </span>
                  ))}
                </BreadcrumbList>
              </Breadcrumb>

              {/* Search Bar and Filters */}
              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="Search files..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 pr-9"
                  />
                  {searchQuery && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
                          onClick={() => setSearchQuery('')}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Clear search</p>
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>

                <FileFilters availableCameraModels={[]} />
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
                {(searchQuery || filters.dateFrom || filters.dateTo) && (
                  <span className="text-xs text-muted-foreground ml-auto">
                    {filteredFiles.length} of {files.length} file{files.length !== 1 ? 's' : ''}
                  </span>
                )}
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
          ) : filteredFiles.length === 0 && searchQuery ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Search className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground mb-2">No files found</p>
                <p className="text-sm text-muted-foreground">No files match "{searchQuery}"</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-4"
                  onClick={() => setSearchQuery('')}
                >
                  Clear search
                </Button>
              </div>
            </div>
          ) : (
            <FileList
              files={filteredFiles}
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
