import type { FileEntry } from '@/types/ipc'
import { FileItem } from '@renderer/components/file-browser/FileItem'
import { useAppStore } from '@renderer/stores/appStore'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('FileItem', () => {
  const mockImageFile: FileEntry = {
    name: 'vacation.jpg',
    path: '/photos/vacation.jpg',
    isDirectory: false,
    isImage: true,
    size: 2048000, // 2 MB
    modifiedTime: new Date('2024-01-15T12:00:00Z').getTime(),
  }

  const mockDirectoryFile: FileEntry = {
    name: 'Documents',
    path: '/home/user/Documents',
    isDirectory: true,
    isImage: false,
    size: 0,
    modifiedTime: new Date('2024-01-10T10:00:00Z').getTime(),
  }

  const mockRegularFile: FileEntry = {
    name: 'readme.txt',
    path: '/files/readme.txt',
    isDirectory: false,
    isImage: false,
    size: 1024, // 1 KB
    modifiedTime: new Date('2024-02-20T15:30:00Z').getTime(),
  }

  beforeEach(() => {
    // Reset store before each test
    useAppStore.setState({
      selectedFiles: [],
    })
  })

  describe('File Display', () => {
    it('should display file name', () => {
      render(<FileItem file={mockImageFile} />)

      expect(screen.getByText('vacation.jpg')).toBeInTheDocument()
    })

    it('should display formatted file size for non-directory files', () => {
      render(<FileItem file={mockImageFile} />)

      // 2048000 bytes = 1.95 MB (actual formatted value)
      expect(screen.getByText(/1\.95 MB/i)).toBeInTheDocument()
    })

    it('should not display size for directory files', () => {
      const { container } = render(<FileItem file={mockDirectoryFile} />)

      expect(screen.getByText('Documents')).toBeInTheDocument()
      // Directory should not show file size info
      const sizeInfo = container.querySelector('.text-xs')
      expect(sizeInfo).not.toBeInTheDocument()
    })

    it('should display modified date for non-directory files', () => {
      render(<FileItem file={mockImageFile} />)

      // Date is formatted using date-fns format 'PPp'
      // Should contain the date in some form
      expect(screen.getByText(/Jan|2024|12:00/)).toBeInTheDocument()
    })
  })

  describe('File Size Formatting', () => {
    it('should format bytes correctly', () => {
      const file: FileEntry = {
        ...mockRegularFile,
        size: 500,
      }
      render(<FileItem file={file} />)

      expect(screen.getByText(/500 B/i)).toBeInTheDocument()
    })

    it('should format kilobytes correctly', () => {
      const file: FileEntry = {
        ...mockRegularFile,
        size: 1024, // 1 KB
      }
      render(<FileItem file={file} />)

      expect(screen.getByText(/1 KB/i)).toBeInTheDocument()
    })

    it('should format megabytes correctly', () => {
      const file: FileEntry = {
        ...mockRegularFile,
        size: 1024 * 1024, // 1 MB
      }
      render(<FileItem file={file} />)

      expect(screen.getByText(/1 MB/i)).toBeInTheDocument()
    })

    it('should format gigabytes correctly', () => {
      const file: FileEntry = {
        ...mockRegularFile,
        size: 1024 * 1024 * 1024, // 1 GB
      }
      render(<FileItem file={file} />)

      expect(screen.getByText(/1 GB/i)).toBeInTheDocument()
    })

    it('should handle zero size', () => {
      const file: FileEntry = {
        ...mockRegularFile,
        size: 0,
      }
      render(<FileItem file={file} />)

      expect(screen.getByText(/0 B/i)).toBeInTheDocument()
    })
  })

  describe('Icon Display', () => {
    it('should display folder icon for directories', () => {
      const { container } = render(<FileItem file={mockDirectoryFile} />)

      const folderIcon = container.querySelector('.text-blue-500')
      expect(folderIcon).toBeInTheDocument()
    })

    it('should display image icon for image files', () => {
      const { container } = render(<FileItem file={mockImageFile} />)

      const imageIcon = container.querySelector('.text-green-500')
      expect(imageIcon).toBeInTheDocument()
    })

    it('should display generic file icon for non-image files', () => {
      const { container } = render(<FileItem file={mockRegularFile} />)

      const fileIcon = container.querySelector('.text-muted-foreground')
      expect(fileIcon).toBeInTheDocument()
    })
  })

  describe('Selection Behavior', () => {
    it('should select file on click', async () => {
      const user = userEvent.setup()
      render(<FileItem file={mockImageFile} />)

      const fileItem = screen.getByRole('button')
      await user.click(fileItem)

      expect(useAppStore.getState().selectedFiles).toEqual([mockImageFile.path])
    })

    it('should add file to selection with Ctrl+click', () => {
      useAppStore.setState({ selectedFiles: ['/other/file.jpg'] })

      render(<FileItem file={mockImageFile} />)

      const fileItem = screen.getByRole('button')
      fireEvent.click(fileItem, { ctrlKey: true })

      const selectedFiles = useAppStore.getState().selectedFiles
      expect(selectedFiles).toContain(mockImageFile.path)
      expect(selectedFiles).toContain('/other/file.jpg')
      expect(selectedFiles).toHaveLength(2)
    })

    it('should add file to selection with Meta+click (Cmd on Mac)', () => {
      useAppStore.setState({ selectedFiles: ['/other/file.jpg'] })

      render(<FileItem file={mockImageFile} />)

      const fileItem = screen.getByRole('button')
      fireEvent.click(fileItem, { metaKey: true })

      const selectedFiles = useAppStore.getState().selectedFiles
      expect(selectedFiles).toContain(mockImageFile.path)
      expect(selectedFiles).toContain('/other/file.jpg')
      expect(selectedFiles).toHaveLength(2)
    })

    it('should remove file from selection with Ctrl+click when already selected', () => {
      useAppStore.setState({ selectedFiles: [mockImageFile.path, '/other/file.jpg'] })

      render(<FileItem file={mockImageFile} />)

      const fileItem = screen.getByRole('button')
      fireEvent.click(fileItem, { ctrlKey: true })

      const selectedFiles = useAppStore.getState().selectedFiles
      expect(selectedFiles).not.toContain(mockImageFile.path)
      expect(selectedFiles).toContain('/other/file.jpg')
      expect(selectedFiles).toHaveLength(1)
    })

    it('should replace selection on normal click', async () => {
      const user = userEvent.setup()
      useAppStore.setState({ selectedFiles: ['/other/file1.jpg', '/other/file2.jpg'] })

      render(<FileItem file={mockImageFile} />)

      const fileItem = screen.getByRole('button')
      await user.click(fileItem)

      expect(useAppStore.getState().selectedFiles).toEqual([mockImageFile.path])
    })

    it('should apply selected style when file is selected', () => {
      useAppStore.setState({ selectedFiles: [mockImageFile.path] })

      const { container } = render(<FileItem file={mockImageFile} />)

      const fileItem = screen.getByRole('button')
      expect(fileItem).toHaveClass('bg-primary/10')
      expect(fileItem).toHaveClass('text-primary')
    })

    it('should not apply selected style when file is not selected', () => {
      useAppStore.setState({ selectedFiles: ['/other/file.jpg'] })

      const { container } = render(<FileItem file={mockImageFile} />)

      const fileItem = screen.getByRole('button')
      expect(fileItem).not.toHaveClass('bg-primary/10')
      expect(fileItem).not.toHaveClass('text-primary')
    })
  })

  describe('Double Click Behavior', () => {
    it('should call onDoubleClick handler when provided', async () => {
      const user = userEvent.setup()
      const handleDoubleClick = vi.fn()

      render(<FileItem file={mockImageFile} onDoubleClick={handleDoubleClick} />)

      const fileItem = screen.getByRole('button')
      await user.dblClick(fileItem)

      expect(handleDoubleClick).toHaveBeenCalledWith(mockImageFile)
      expect(handleDoubleClick).toHaveBeenCalledTimes(1)
    })

    it('should not throw error when onDoubleClick is not provided', async () => {
      const user = userEvent.setup()

      render(<FileItem file={mockImageFile} />)

      const fileItem = screen.getByRole('button')
      await expect(user.dblClick(fileItem)).resolves.not.toThrow()
    })
  })

  describe('Keyboard Interaction', () => {
    it('should select file on Enter key', async () => {
      const user = userEvent.setup()
      render(<FileItem file={mockImageFile} />)

      const fileItem = screen.getByRole('button')
      fileItem.focus()
      await user.keyboard('{Enter}')

      expect(useAppStore.getState().selectedFiles).toEqual([mockImageFile.path])
    })

    it('should select file on Space key', async () => {
      const user = userEvent.setup()
      render(<FileItem file={mockImageFile} />)

      const fileItem = screen.getByRole('button')
      fileItem.focus()
      await user.keyboard(' ')

      expect(useAppStore.getState().selectedFiles).toEqual([mockImageFile.path])
    })
  })

  describe('Accessibility', () => {
    it('should render as a button element', () => {
      render(<FileItem file={mockImageFile} />)

      const fileItem = screen.getByRole('button')
      expect(fileItem).toBeInTheDocument()
    })

    it('should have proper button type', () => {
      render(<FileItem file={mockImageFile} />)

      const fileItem = screen.getByRole('button')
      expect(fileItem).toHaveAttribute('type', 'button')
    })
  })
})
