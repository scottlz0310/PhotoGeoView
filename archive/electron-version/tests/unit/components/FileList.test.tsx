import { FileList } from '@renderer/components/file-browser/FileList'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { FileEntry } from '@/types/ipc'

describe('FileList', () => {
  const mockFiles: FileEntry[] = [
    {
      name: 'photo1.jpg',
      path: '/photos/photo1.jpg',
      isDirectory: false,
      isImage: true,
      size: 1024000,
      modifiedTime: Date.now(),
    },
    {
      name: 'photo2.jpg',
      path: '/photos/photo2.jpg',
      isDirectory: false,
      isImage: true,
      size: 2048000,
      modifiedTime: Date.now(),
    },
    {
      name: 'documents',
      path: '/photos/documents',
      isDirectory: true,
      isImage: false,
      size: 0,
      modifiedTime: Date.now(),
    },
  ]

  describe('Loading State', () => {
    it('should display loading spinner when isLoading is true', () => {
      render(<FileList files={[]} isLoading={true} />)

      expect(screen.getByText('Loading files...')).toBeInTheDocument()
    })

    it('should display loading indicator with animation', () => {
      const { container } = render(<FileList files={[]} isLoading={true} />)

      const spinner = container.querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should display error message when error is provided', () => {
      const error = new Error('Failed to load directory')
      render(<FileList files={[]} error={error} />)

      expect(screen.getByText('Error loading files')).toBeInTheDocument()
      expect(screen.getByText('Failed to load directory')).toBeInTheDocument()
    })

    it('should display loading state when both loading and error are true', () => {
      const error = new Error('Test error')
      render(<FileList files={[]} isLoading={true} error={error} />)

      // In current implementation, loading takes priority
      expect(screen.getByText('Loading files...')).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('should display "No files found" when files array is empty', () => {
      render(<FileList files={[]} />)

      expect(screen.getByText('No files found')).toBeInTheDocument()
    })

    it('should not display loading or error when showing empty state', () => {
      render(<FileList files={[]} isLoading={false} error={null} />)

      expect(screen.queryByText('Loading files...')).not.toBeInTheDocument()
      expect(screen.queryByText('Error loading files')).not.toBeInTheDocument()
      expect(screen.getByText('No files found')).toBeInTheDocument()
    })
  })

  describe('File Rendering', () => {
    it('should render all files in the list', () => {
      render(<FileList files={mockFiles} />)

      expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
      expect(screen.getByText('photo2.jpg')).toBeInTheDocument()
      expect(screen.getByText('documents')).toBeInTheDocument()
    })

    it('should render correct number of FileItem components', () => {
      const { container } = render(<FileList files={mockFiles} />)

      // Each FileItem is rendered as a button
      const fileItems = container.querySelectorAll('button')
      expect(fileItems).toHaveLength(mockFiles.length)
    })

    it('should not display empty state when files are present', () => {
      render(<FileList files={mockFiles} />)

      expect(screen.queryByText('No files found')).not.toBeInTheDocument()
    })

    it('should not display loading or error when files are successfully loaded', () => {
      render(<FileList files={mockFiles} isLoading={false} error={null} />)

      expect(screen.queryByText('Loading files...')).not.toBeInTheDocument()
      expect(screen.queryByText('Error loading files')).not.toBeInTheDocument()
    })
  })

  describe('Props Handling', () => {
    it('should handle single file in array', () => {
      const singleFile = [mockFiles[0]]
      render(<FileList files={singleFile} />)

      expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
    })

    it('should handle large file list', () => {
      const manyFiles: FileEntry[] = Array.from({ length: 100 }, (_, i) => ({
        name: `file${i}.jpg`,
        path: `/files/file${i}.jpg`,
        isDirectory: false,
        isImage: true,
        size: 1024 * i,
        modifiedTime: Date.now(),
      }))

      const { container } = render(<FileList files={manyFiles} />)

      const fileItems = container.querySelectorAll('button')
      expect(fileItems).toHaveLength(100)
    })
  })
})
