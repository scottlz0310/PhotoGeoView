import { invoke } from '@tauri-apps/api/core'
import { act } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { PhotoData } from '../types/photo'
import { usePhotoStore } from './photoStore'

// モック
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}))

vi.mock('./settingsStore', () => ({
  useSettingsStore: {
    getState: () => ({
      settings: { display: { defaultViewMode: 'list' } },
      updateSettings: vi.fn(),
      isLoaded: true,
    }),
  },
}))

// テスト用のダミーデータ
const mockPhoto1: PhotoData = {
  path: '/path/to/photo1.jpg',
  filename: 'photo1.jpg',
  fileSize: 1024 * 1024,
  modifiedTime: '2023-01-01T12:00:00',
  thumbnail: 'data:image/jpeg;base64,...',
  exif: {
    gps: { lat: 35.6895, lng: 139.6917 },
    datetime: '2023-01-01T12:00:00',
    camera: { make: 'Sony', model: 'Alpha' },
    width: 1000,
    height: 1000,
    iso: 100,
    aperture: 2.8,
    shutterSpeed: 0.01,
    focalLength: 50,
  },
}

const mockPhoto2: PhotoData = {
  path: '/path/to/photo2.jpg',
  filename: 'photo2.jpg',
  fileSize: 1024 * 1024,
  modifiedTime: '2023-01-02T12:00:00',
  thumbnail: 'data:image/jpeg;base64,...',
  exif: {
    gps: { lat: 34.6937, lng: 135.5023 },
    datetime: '2023-01-02T12:00:00',
    camera: { make: 'Canon', model: 'EOS' },
    width: 1000,
    height: 1000,
    iso: 100,
    aperture: 2.8,
    shutterSpeed: 0.01,
    focalLength: 50,
  },
}

describe('photoStore', () => {
  // 各テストの前にストアをリセット
  beforeEach(() => {
    act(() => {
      usePhotoStore.setState({
        photos: [],
        selectedPhoto: null,
        currentPath: null,
        directoryEntries: [],
      })
    })
  })

  it('should initialize with default values', () => {
    const state = usePhotoStore.getState()
    expect(state.photos).toEqual([])
    expect(state.selectedPhoto).toBeNull()
    expect(state.currentPath).toBeNull()
    expect(state.directoryEntries).toEqual([])
  })

  it('should set photos', () => {
    act(() => {
      usePhotoStore.getState().setPhotos([mockPhoto1])
    })
    const state = usePhotoStore.getState()
    expect(state.photos).toHaveLength(1)
    expect(state.photos[0]).toEqual(mockPhoto1)
  })

  it('should add photos', () => {
    act(() => {
      usePhotoStore.getState().setPhotos([mockPhoto1])
      usePhotoStore.getState().addPhotos([mockPhoto2])
    })
    const state = usePhotoStore.getState()
    expect(state.photos).toHaveLength(2)
    expect(state.photos).toContainEqual(mockPhoto1)
    expect(state.photos).toContainEqual(mockPhoto2)
  })

  it('should not add duplicate photos', () => {
    act(() => {
      usePhotoStore.getState().setPhotos([mockPhoto1])
      usePhotoStore.getState().addPhotos([mockPhoto1]) // Duplicate
    })
    const state = usePhotoStore.getState()
    expect(state.photos).toHaveLength(1)
  })

  it('should select a photo', () => {
    act(() => {
      usePhotoStore.getState().setPhotos([mockPhoto1, mockPhoto2])
      usePhotoStore.getState().selectPhoto(mockPhoto1.path)
    })
    const state = usePhotoStore.getState()
    expect(state.selectedPhoto).toEqual(mockPhoto1)
  })

  it('should clear selection if photo not found', () => {
    act(() => {
      usePhotoStore.getState().setPhotos([mockPhoto1])
      usePhotoStore.getState().selectPhoto('/nonexistent.jpg')
    })
    const state = usePhotoStore.getState()
    expect(state.selectedPhoto).toBeNull()
  })

  it('should remove a photo', () => {
    act(() => {
      usePhotoStore.getState().setPhotos([mockPhoto1, mockPhoto2])
      usePhotoStore.getState().selectPhoto(mockPhoto1.path) // Select it first
      usePhotoStore.getState().removePhoto(mockPhoto1.path)
    })
    const state = usePhotoStore.getState()
    expect(state.photos).toHaveLength(1)
    expect(state.photos[0]).toEqual(mockPhoto2)
    expect(state.selectedPhoto).toBeNull() // Selection should be cleared
  })

  it('should navigate to directory', async () => {
    const path = '/path/to/folder'
    const mockContent = {
      currentPath: path,
      entries: [],
    }
    vi.mocked(invoke).mockResolvedValue(mockContent)

    await act(async () => {
      await usePhotoStore.getState().navigateToDirectory(path)
    })

    expect(usePhotoStore.getState().currentPath).toBe(path)
    expect(invoke).toHaveBeenCalledWith('read_directory', { path })
  })
})
