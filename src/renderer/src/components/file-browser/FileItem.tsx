import type { FileEntry } from '@/types/ipc'
import { cn } from '@renderer/lib/utils'
import { useAppStore } from '@renderer/stores/appStore'
import { format } from 'date-fns'
import { File, Folder, Image } from 'lucide-react'

interface FileItemProps {
  file: FileEntry
  onDoubleClick?: (file: FileEntry) => void
}

export function FileItem({ file, onDoubleClick }: FileItemProps) {
  const { selectedFiles, addSelectedFile, removeSelectedFile } = useAppStore()
  const isSelected = selectedFiles.includes(file.path)

  const handleClick = (e: React.MouseEvent) => {
    if (e.ctrlKey || e.metaKey) {
      // Multi-select with Ctrl/Cmd
      if (isSelected) {
        removeSelectedFile(file.path)
      } else {
        addSelectedFile(file.path)
      }
    } else {
      // Single select
      useAppStore.setState({ selectedFiles: [file.path] })
    }
  }

  const handleDoubleClick = () => {
    if (onDoubleClick) {
      onDoubleClick(file)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${Number.parseFloat((bytes / k ** i).toFixed(2))} ${sizes[i]}`
  }

  const getIcon = () => {
    if (file.isDirectory) {
      return <Folder className="h-5 w-5 text-blue-500" />
    }
    if (file.isImage) {
      return <Image className="h-5 w-5 text-green-500" />
    }
    return <File className="h-5 w-5 text-muted-foreground" />
  }

  return (
    <button
      type="button"
      className={cn(
        'flex items-center gap-3 px-4 py-2 rounded-md cursor-pointer transition-colors w-full text-left',
        'hover:bg-accent hover:text-accent-foreground',
        isSelected && 'bg-primary/10 text-primary'
      )}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleClick(e as unknown as React.MouseEvent)
        }
      }}
    >
      <div className="flex-shrink-0">{getIcon()}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{file.name}</p>
        {!file.isDirectory && (
          <p className="text-xs text-muted-foreground">
            {formatFileSize(file.size)} • {format(new Date(file.modifiedTime), 'PPp')}
          </p>
        )}
      </div>
    </button>
  )
}
