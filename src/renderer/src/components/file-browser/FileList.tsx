import type { FileEntry } from '@/types/ipc'
import { FileItem } from './FileItem'

interface FileListProps {
  files: FileEntry[]
  onFileDoubleClick?: (file: FileEntry) => void
  isLoading?: boolean
  error?: Error | null
}

export function FileList({ files, onFileDoubleClick, isLoading, error }: FileListProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading files...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center text-destructive">
          <p className="font-semibold mb-2">Error loading files</p>
          <p className="text-sm">{error.message}</p>
        </div>
      </div>
    )
  }

  if (files.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">No files found</p>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {files.map((file) => (
        <FileItem key={file.path} file={file} onDoubleClick={onFileDoubleClick} />
      ))}
    </div>
  )
}
