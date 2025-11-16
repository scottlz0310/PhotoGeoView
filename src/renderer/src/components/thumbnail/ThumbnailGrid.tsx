import type { FileEntry } from '@/types/ipc'
import { Button } from '@renderer/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@renderer/components/ui/card'
import { Progress } from '@renderer/components/ui/progress'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@renderer/components/ui/tooltip'
import { useAppStore } from '@renderer/stores/appStore'
import { useQuery } from '@tanstack/react-query'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Image as ImageIcon, Loader2, Minimize2 } from 'lucide-react'
import { useRef } from 'react'

interface ThumbnailGridProps {
  files: FileEntry[]
  currentPath: string | null
}

export function ThumbnailGrid({ files, currentPath }: ThumbnailGridProps) {
  const { selectedFiles, setSelectedFiles, togglePanel } = useAppStore()
  const parentRef = useRef<HTMLDivElement>(null)

  // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
  const isElectron = !!(window as any).api

  // Filter only image files
  const imageFiles = files.filter((file) => file.isImage && !file.isDirectory)

  // Virtual scrolling configuration
  const rowVirtualizer = useVirtualizer({
    count: Math.ceil(imageFiles.length / 4), // 4 columns
    getScrollElement: () => parentRef.current,
    estimateSize: () => 200, // Estimated row height
    overscan: 5, // Number of items to render outside visible area
  })

  const handleThumbnailClick = (filePath: string, e: React.MouseEvent) => {
    if (e.ctrlKey || e.metaKey) {
      // Multi-select
      if (selectedFiles.includes(filePath)) {
        setSelectedFiles(selectedFiles.filter((f) => f !== filePath))
      } else {
        setSelectedFiles([...selectedFiles, filePath])
      }
    } else {
      // Single select
      setSelectedFiles([filePath])
    }
  }

  if (!currentPath) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Thumbnails</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            Select a folder to view thumbnails
          </p>
        </CardContent>
      </Card>
    )
  }

  if (!isElectron) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Thumbnails</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            Thumbnails are only available in the Electron app
          </p>
        </CardContent>
      </Card>
    )
  }

  if (imageFiles.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Thumbnails</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            No images found in this folder
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <TooltipProvider>
      <Card className="h-full flex flex-col">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Thumbnails ({imageFiles.length})</CardTitle>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  onClick={() => togglePanel('thumbnailGrid')}
                  size="icon"
                  variant="ghost"
                >
                  <Minimize2 className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Collapse panel</p>
              </TooltipContent>
            </Tooltip>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-hidden">
        <div ref={parentRef} className="h-full overflow-auto">
          <div
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`,
              width: '100%',
              position: 'relative',
            }}
          >
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const startIdx = virtualRow.index * 4
              const rowImages = imageFiles.slice(startIdx, startIdx + 4)

              return (
                <div
                  key={virtualRow.key}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: `${virtualRow.size}px`,
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                >
                  <div className="grid grid-cols-4 gap-2 p-2">
                    {rowImages.map((file) => (
                      <ThumbnailItem
                        key={file.path}
                        file={file}
                        isSelected={selectedFiles.includes(file.path)}
                        onClick={(e) => handleThumbnailClick(file.path, e)}
                      />
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </CardContent>
    </Card>
    </TooltipProvider>
  )
}

interface ThumbnailItemProps {
  file: FileEntry
  isSelected: boolean
  onClick: (e: React.MouseEvent) => void
}

function ThumbnailItem({ file, isSelected, onClick }: ThumbnailItemProps) {
  const {
    data: result,
    isLoading,
    fetchStatus,
  } = useQuery({
    queryKey: ['thumbnail', file.path],
    queryFn: async () => {
      // biome-ignore lint/suspicious/noExplicitAny: Type definition issue, will be fixed later
      return await (window as any).api.generateThumbnail({
        path: file.path,
        width: 150,
        height: 150,
      })
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  })

  const thumbnail = result?.success ? result.data.thumbnail : null
  const showProgress = isLoading && fetchStatus === 'fetching'

  return (
    <button
      type="button"
      onClick={onClick}
      className={`
        relative aspect-square rounded-lg overflow-hidden border-2 transition-all
        hover:border-primary hover:shadow-lg
        ${isSelected ? 'border-primary ring-2 ring-primary/20' : 'border-border'}
      `}
    >
      {showProgress && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-muted gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <div className="w-3/4">
            <Progress value={undefined} className="h-1" />
          </div>
        </div>
      )}

      {!isLoading && thumbnail && (
        <img
          src={thumbnail}
          alt={file.name}
          className="w-full h-full object-cover"
          loading="lazy"
        />
      )}

      {!isLoading && !thumbnail && (
        <div className="absolute inset-0 flex items-center justify-center bg-muted">
          <ImageIcon className="h-12 w-12 text-muted-foreground" />
        </div>
      )}

      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2">
        <p className="text-xs text-white truncate">{file.name}</p>
      </div>
    </button>
  )
}
