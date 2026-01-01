import { useVirtualizer } from '@tanstack/react-virtual'
import { invoke } from '@tauri-apps/api/core'
import {
  ArrowDownAZ,
  ArrowDownWideNarrow,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  ArrowUpAZ,
  ArrowUpWideNarrow,
  Calendar,
  FileText,
  Folder,
  FolderOpen,
  Grid,
  Image,
  LayoutList,
  List,
  RefreshCw,
} from 'lucide-react'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { usePhotoStore } from '@/stores/photoStore'
import { useSettingsStore } from '@/stores/settingsStore'
import type { DirectoryEntry, PhotoData } from '@/types/photo'

const LIST_ROW_HEIGHT = {
  list: 64,
  detail: 112,
}

const GRID_ITEM_SIZE = 160
const GRID_GAP = 8

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) {
    return `${bytes} B`
  }

  const kb = bytes / 1024
  if (kb < 1024) {
    return `${kb.toFixed(1)} KB`
  }

  const mb = kb / 1024
  return `${mb.toFixed(1)} MB`
}

export function PhotoList(): React.ReactElement {
  const { t } = useTranslation()
  const {
    photos,
    selectedPhoto,
    selectedEntryPath,
    viewMode,
    currentPath,
    directoryEntries,
    isLoading,
    addPhotos,
    selectPhoto,
    setSelectedEntryPath,
    setViewMode,
    setIsLoading,
    setLoadingStatus,
    navigateToDirectory,
  } = usePhotoStore()
  const { settings, updateSettings } = useSettingsStore()
  const scrollParentRef = useRef<HTMLDivElement | null>(null)
  const [entryThumbnails, setEntryThumbnails] = useState<Record<string, string>>({})
  const pendingThumbnails = useRef<Set<string>>(new Set())
  const [gridWidth, setGridWidth] = useState(0)
  const selectionRequestIdRef = useRef(0)
  const selectionLoadingRef = useRef(false)
  const [sortKey, setSortKey] = useState<'name' | 'date'>('name')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')

  const isDirectoryView = Boolean(currentPath)

  const sortedListItems = useMemo(() => {
    const items = isDirectoryView ? [...directoryEntries] : [...photos]

    return items.sort((a, b) => {
      // ディレクトリ優先（directoryEntriesの場合）
      if ('isDirectory' in a && 'isDirectory' in b) {
        if (a.isDirectory !== b.isDirectory) {
          return a.isDirectory ? -1 : 1
        }
      }

      let comparison = 0
      if (sortKey === 'name') {
        const nameA = 'name' in a ? a.name : a.filename
        const nameB = 'name' in b ? b.name : b.filename
        comparison = nameA.localeCompare(nameB)
      } else {
        // date
        const getDate = (item: PhotoData | DirectoryEntry) => {
          if ('capturedTime' in item && item.capturedTime) {
            return item.capturedTime
          }
          if ('exif' in item && item.exif?.datetime) {
            return item.exif.datetime
          }
          if ('modifiedTime' in item) {
            return item.modifiedTime
          }
          return ''
        }
        const dateA = getDate(a) || ''
        const dateB = getDate(b) || ''
        // 日付がない場合は後ろにする
        if (!(dateA || dateB)) {
          return 0
        }
        if (!dateA) {
          return 1
        }
        if (!dateB) {
          return -1
        }
        comparison = dateA.localeCompare(dateB)
      }

      return sortOrder === 'asc' ? comparison : -comparison
    })
  }, [directoryEntries, photos, isDirectoryView, sortKey, sortOrder])

  const listItems = sortedListItems
  const listCount = listItems.length
  const listRowHeight = viewMode === 'detail' ? LIST_ROW_HEIGHT.detail : LIST_ROW_HEIGHT.list
  const listRowClass = viewMode === 'detail' ? 'h-28' : 'h-16'
  const listVirtualizer = useVirtualizer({
    count: listCount,
    getScrollElement: () => scrollParentRef.current,
    estimateSize: () => listRowHeight,
    overscan: 6,
  })
  const listVirtualItems = listVirtualizer.getVirtualItems()
  const gridColumns = Math.max(1, Math.floor((gridWidth + GRID_GAP) / (GRID_ITEM_SIZE + GRID_GAP)))
  const gridRowCount = Math.ceil(listCount / gridColumns)
  const gridVirtualizer = useVirtualizer({
    count: gridRowCount,
    getScrollElement: () => scrollParentRef.current,
    estimateSize: () => GRID_ITEM_SIZE + GRID_GAP,
    overscan: 4,
  })
  const gridVirtualItems = gridVirtualizer.getVirtualItems()

  const PHOTO_LOADING_STATUS = t('photoList.loading')

  // 起動時に前回開いたフォルダを自動的に開く
  useEffect(() => {
    const loadLastFolder = async () => {
      if (settings.lastOpenedFolder && !currentPath) {
        try {
          await navigateToDirectory(settings.lastOpenedFolder)
        } catch {
          // フォルダが存在しない場合などはエラーを無視
        }
      }
    }
    loadLastFolder()
  }, [settings.lastOpenedFolder, currentPath, navigateToDirectory])

  useEffect(() => {
    const element = scrollParentRef.current
    if (!element) {
      return
    }
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0]
      if (entry) {
        setGridWidth(entry.contentRect.width)
      }
    })
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    setEntryThumbnails({})
    pendingThumbnails.current.clear()
    if (currentPath === null) {
      return
    }
  }, [currentPath])

  useEffect(() => {
    if (!isDirectoryView) {
      return
    }
    if (directoryEntries.length === 0) {
      if (selectedEntryPath !== null) {
        setSelectedEntryPath(null)
      }
      return
    }
    if (selectedEntryPath) {
      const exists = directoryEntries.some((entry) => entry.path === selectedEntryPath)
      if (exists) {
        return
      }
    }
    setSelectedEntryPath(directoryEntries[0]?.path ?? null)
  }, [directoryEntries, isDirectoryView, selectedEntryPath, setSelectedEntryPath])

  useEffect(() => {
    if (!(selectedPhoto && isDirectoryView)) {
      return
    }
    // selectedEntryPathのチェックを削除し、selectedPhotoの変更のみに反応させる
    // これにより、ユーザーがクリックしてselectedEntryPathを変更した直後に
    // 古いselectedPhotoによってハイライトが戻されるのを防ぐ
    const exists = directoryEntries.some((entry) => entry.path === selectedPhoto.path)
    if (exists) {
      setSelectedEntryPath(selectedPhoto.path)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [directoryEntries, isDirectoryView, selectedPhoto, setSelectedEntryPath])

  useEffect(() => {
    if (isDirectoryView || !selectedPhoto) {
      return
    }
    setSelectedEntryPath(selectedPhoto.path)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDirectoryView, selectedPhoto, setSelectedEntryPath])

  useEffect(() => {
    const layoutKey = `${viewMode}-${gridColumns}-${listCount}`
    if (layoutKey) {
      listVirtualizer.measure()
      gridVirtualizer.measure()
    }
  }, [gridColumns, listCount, listVirtualizer, gridVirtualizer, viewMode])

  useEffect(() => {
    if (!isDirectoryView) {
      return
    }

    const visibleEntries: DirectoryEntry[] = []
    if (viewMode === 'grid') {
      for (const row of gridVirtualItems) {
        const start = row.index * gridColumns
        const end = Math.min(start + gridColumns, directoryEntries.length)
        for (let i = start; i < end; i += 1) {
          const entry = directoryEntries[i]
          if (entry) {
            visibleEntries.push(entry)
          }
        }
      }
    } else {
      for (const row of listVirtualItems) {
        const entry = directoryEntries[row.index]
        if (entry) {
          visibleEntries.push(entry)
        }
      }
    }

    for (const entry of visibleEntries) {
      if (entry.isDirectory) {
        continue
      }
      if (entryThumbnails[entry.path] || pendingThumbnails.current.has(entry.path)) {
        continue
      }

      pendingThumbnails.current.add(entry.path)
      invoke<string>('generate_thumbnail', { path: entry.path })
        .then((thumbnail) => {
          setEntryThumbnails((prev) => {
            if (prev[entry.path]) {
              return prev
            }
            return { ...prev, [entry.path]: thumbnail }
          })
        })
        .catch(() => {
          // サムネイル生成失敗時は静かに無視
        })
        .finally(() => {
          pendingThumbnails.current.delete(entry.path)
        })
    }
  }, [
    directoryEntries,
    entryThumbnails,
    gridColumns,
    gridVirtualItems,
    isDirectoryView,
    listVirtualItems,
    viewMode,
  ])

  const handleOpenFolder = async () => {
    setIsLoading(true)
    setLoadingStatus(t('common.loading'))
    try {
      const folderPath = await invoke<string | null>('select_photo_folder')
      if (folderPath) {
        setLoadingStatus(t('common.loading'))
        // ナビゲーションモードに入る
        await navigateToDirectory(folderPath)
        // 設定に保存
        updateSettings({ lastOpenedFolder: folderPath })
        toast.success(t('menu.openFolder'), {
          description: `${directoryEntries.length} items found`,
        })
      }
    } catch (error) {
      toast.error(t('common.error'), {
        description: String(error),
      })
    } finally {
      setIsLoading(false)
      setLoadingStatus('')
    }
  }

  const handleDirectoryEntryClick = (entry: DirectoryEntry) => {
    setSelectedEntryPath(entry.path)

    if (!entry.isDirectory) {
      handleFileSelect(entry.path)
      return
    }

    // フォルダ選択時は、以前の選択状態をクリアするが、
    // 読み込み中のフラグなどはリセットしないように注意
    selectionRequestIdRef.current += 1
    selectionLoadingRef.current = false
    const { loadingStatus } = usePhotoStore.getState()
    if (loadingStatus === PHOTO_LOADING_STATUS) {
      setIsLoading(false)
      setLoadingStatus('')
    }
    selectPhoto(null)
  }

  const handleDirectoryEntryDoubleClick = (entry: DirectoryEntry) => {
    setSelectedEntryPath(entry.path)
    if (entry.isDirectory) {
      handleFolderDoubleClick(entry.path)
    }
  }

  const scrollToIndex = (index: number) => {
    if (viewMode === 'grid') {
      const rowIndex = Math.floor(index / gridColumns)
      gridVirtualizer.scrollToIndex(rowIndex)
    } else {
      listVirtualizer.scrollToIndex(index)
    }
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.altKey || event.ctrlKey || event.metaKey) {
      return
    }

    if (listCount === 0) {
      return
    }

    const key = event.key
    const isGrid = viewMode === 'grid'
    const maxIndex = listCount - 1
    const currentIndex = (() => {
      if (isDirectoryView) {
        if (!selectedEntryPath) {
          return 0
        }
        const index = directoryEntries.findIndex((entry) => entry.path === selectedEntryPath)
        return index >= 0 ? index : 0
      }
      if (!selectedEntryPath) {
        return 0
      }
      const index = photos.findIndex((photo) => photo.path === selectedEntryPath)
      return index >= 0 ? index : 0
    })()

    if (key === 'Backspace') {
      if (!isDirectoryView || isLoading) {
        return
      }
      event.preventDefault()
      handleNavigateUp()
      return
    }

    if (key === 'Enter') {
      if (isDirectoryView && selectedEntryPath) {
        const entry = directoryEntries.find((e) => e.path === selectedEntryPath)
        if (entry?.isDirectory) {
          event.preventDefault()
          handleFolderDoubleClick(entry.path)
        }
      }
      return
    }

    let nextIndex = currentIndex
    switch (key) {
      case 'ArrowDown':
        nextIndex = currentIndex + (isGrid ? gridColumns : 1)
        break
      case 'ArrowUp':
        nextIndex = currentIndex - (isGrid ? gridColumns : 1)
        break
      case 'ArrowRight':
        nextIndex = currentIndex + 1
        break
      case 'ArrowLeft':
        nextIndex = currentIndex - 1
        break
      case 'Home':
        nextIndex = 0
        break
      case 'End':
        nextIndex = maxIndex
        break
      default:
        return
    }

    nextIndex = Math.max(0, Math.min(maxIndex, nextIndex))
    if (nextIndex === currentIndex) {
      return
    }

    event.preventDefault()

    if (isDirectoryView) {
      const entry = directoryEntries[nextIndex]
      if (entry) {
        handleDirectoryEntryClick(entry)
      }
    } else {
      const photo = photos[nextIndex]
      if (photo) {
        setSelectedEntryPath(photo.path)
        selectPhoto(photo.path)
      }
    }

    scrollToIndex(nextIndex)
  }

  // パンくずリストのセグメント生成
  const getBreadcrumbSegments = (path: string): Array<{ name: string; path: string }> => {
    if (!path) {
      return []
    }

    // Windowsのパスを分割（例: C:\Users\Photos -> ["C:\", "Users", "Photos"]）
    const parts = path.split(/[\\/]/).filter(Boolean)
    const segments: Array<{ name: string; path: string }> = []

    let currentPath = ''
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i]
      if (!part) {
        continue // undefinedチェック
      }

      if (i === 0 && part.endsWith(':')) {
        // Windowsのドライブレター（C:など）
        currentPath = `${part}\\`
        segments.push({ name: currentPath, path: currentPath })
      } else {
        currentPath = currentPath ? `${currentPath}\\${part}` : part
        segments.push({ name: part, path: currentPath })
      }
    }

    return segments
  }

  // パンくずリストをクリックして親フォルダに移動
  const handleBreadcrumbClick = async (folderPath: string) => {
    try {
      await navigateToDirectory(folderPath)
      // 設定に保存
      updateSettings({ lastOpenedFolder: folderPath })
    } catch (error) {
      toast.error('フォルダを開けませんでした', {
        description: String(error),
      })
    }
  }

  // フォルダをダブルクリックして移動
  const handleFolderDoubleClick = async (folderPath: string) => {
    try {
      await navigateToDirectory(folderPath)
      // 設定に保存
      updateSettings({ lastOpenedFolder: folderPath })
    } catch (error) {
      toast.error('フォルダを開けませんでした', {
        description: String(error),
      })
    }
  }

  // 画像ファイルを選択して読み込み
  const handleFileSelect = async (filePath: string) => {
    const requestId = selectionRequestIdRef.current + 1
    selectionRequestIdRef.current = requestId

    const cachedPhoto = photos.find((photo) => photo.path === filePath)
    if (cachedPhoto) {
      selectionLoadingRef.current = false
      const { loadingStatus } = usePhotoStore.getState()
      if (loadingStatus === PHOTO_LOADING_STATUS) {
        setIsLoading(false)
        setLoadingStatus('')
      }
      selectPhoto(cachedPhoto.path)
      return
    }

    selectionLoadingRef.current = true
    setIsLoading(true)
    setLoadingStatus(PHOTO_LOADING_STATUS)

    try {
      const photoData = await invoke<PhotoData>('get_photo_data', { path: filePath })
      if (selectionRequestIdRef.current !== requestId) {
        return
      }
      addPhotos([photoData])
      selectPhoto(photoData.path)
    } catch (error) {
      if (selectionRequestIdRef.current === requestId) {
        toast.error(t('common.error'), {
          description: String(error),
        })
      }
    } finally {
      if (selectionRequestIdRef.current === requestId && selectionLoadingRef.current) {
        selectionLoadingRef.current = false
        const { loadingStatus } = usePhotoStore.getState()
        if (loadingStatus === PHOTO_LOADING_STATUS) {
          setIsLoading(false)
          setLoadingStatus('')
        }
      }
    }
  }

  // 上位フォルダに移動
  const handleNavigateUp = async () => {
    if (!currentPath) {
      return
    }
    try {
      // パス区切り文字で分割して親パスを生成
      const separator = currentPath.includes('\\') ? '\\' : '/'
      const parts = currentPath.split(separator).filter(Boolean)
      if (parts.length > 1) {
        // ドライブレターの処理（Windows）
        const firstPart = parts[0]
        const isWindowsDrive = firstPart ? firstPart.endsWith(':') : false
        const parentParts = parts.slice(0, -1)
        let parentPath = parentParts.join(separator)

        if (isWindowsDrive && parentParts.length === 1) {
          parentPath += separator // C: -> C:\
        } else if (currentPath.startsWith('/')) {
          parentPath = `/${parentPath}` // Unix absolute path
        }

        await navigateToDirectory(parentPath)
        updateSettings({ lastOpenedFolder: parentPath })
      }
    } catch (error) {
      toast.error(t('common.error'), {
        description: String(error),
      })
    }
  }

  // フォルダ再読み込み
  const handleRefresh = async () => {
    if (!currentPath) {
      return
    }
    setIsLoading(true)
    setLoadingStatus(t('common.loading'))
    try {
      await navigateToDirectory(currentPath)
      toast.success(t('menu.refresh'))
    } catch (error) {
      toast.error(t('common.error'), {
        description: String(error),
      })
    } finally {
      setIsLoading(false)
      setLoadingStatus('')
    }
  }

  return (
    <div className="flex h-full w-full flex-col bg-card p-4">
      {/* ヘッダー（ナビゲーション & ビュー切り替え） */}
      <div className="mb-4 flex items-center justify-between gap-2">
        {/* 左側: ナビゲーションボタン群 */}
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => {
              /* TODO: 履歴戻る実装 */
            }}
            disabled={true /* TODO: 履歴状態と連携 */}
            title={t('common.back')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => {
              /* TODO: 履歴進む実装 */
            }}
            disabled={true /* TODO: 履歴状態と連携 */}
            title={t('common.next')}
          >
            <ArrowRight className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handleNavigateUp}
            disabled={!currentPath || isLoading}
            title={t('common.back')}
          >
            <ArrowUp className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handleRefresh}
            disabled={!currentPath || isLoading}
            title={t('menu.refresh')}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handleOpenFolder}
            disabled={isLoading}
            title={t('menu.openFolder')}
          >
            <FolderOpen className="h-4 w-4" />
          </Button>
        </div>

        {/* 右側: コントロール */}
        <div className="flex items-center gap-2">
          {/* ソートメニュー */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8" title={t('common.sort')}>
                {sortKey === 'date' ? (
                  <Calendar className="h-4 w-4" />
                ) : (
                  <FileText className="h-4 w-4" />
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>{t('common.sortBy')}</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuRadioGroup
                value={sortKey}
                onValueChange={(v) => setSortKey(v as 'name' | 'date')}
              >
                <DropdownMenuRadioItem value="name">
                  <FileText className="mr-2 h-4 w-4" />
                  {t('common.name')}
                </DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="date">
                  <Calendar className="mr-2 h-4 w-4" />
                  {t('common.date')}
                </DropdownMenuRadioItem>
              </DropdownMenuRadioGroup>
              <DropdownMenuSeparator />
              <DropdownMenuRadioGroup
                value={sortOrder}
                onValueChange={(v) => setSortOrder(v as 'asc' | 'desc')}
              >
                <DropdownMenuRadioItem value="asc">
                  {sortKey === 'date' ? (
                    <ArrowUpWideNarrow className="mr-2 h-4 w-4" />
                  ) : (
                    <ArrowUpAZ className="mr-2 h-4 w-4" />
                  )}
                  {t('common.ascending')}
                </DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="desc">
                  {sortKey === 'date' ? (
                    <ArrowDownWideNarrow className="mr-2 h-4 w-4" />
                  ) : (
                    <ArrowDownAZ className="mr-2 h-4 w-4" />
                  )}
                  {t('common.descending')}
                </DropdownMenuRadioItem>
              </DropdownMenuRadioGroup>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* ビューモード切り替えボタン */}
          <div className="flex items-center rounded-md border border-border bg-background p-1">
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`rounded p-1.5 transition-colors ${
                viewMode === 'list'
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              }`}
              title={t('photoList.viewMode.list')}
            >
              <List className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('detail')}
              className={`rounded p-1.5 transition-colors ${
                viewMode === 'detail'
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              }`}
              title={t('photoList.viewMode.detail')}
            >
              <LayoutList className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`rounded p-1.5 transition-colors ${
                viewMode === 'grid'
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              }`}
              title={t('photoList.viewMode.grid')}
            >
              <Grid className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* パンくずリスト（フォルダナビゲーション） */}
      {currentPath && (
        <div className="mb-3 rounded border border-border bg-background p-2">
          <Breadcrumb>
            <BreadcrumbList>
              {getBreadcrumbSegments(currentPath).map((segment, index, array) => (
                <React.Fragment key={segment.path}>
                  <BreadcrumbItem>
                    {index === array.length - 1 ? (
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
                  {index < array.length - 1 && <BreadcrumbSeparator />}
                </React.Fragment>
              ))}
            </BreadcrumbList>
          </Breadcrumb>
        </div>
      )}

      {/* コンテンツ表示エリア */}
      <div
        className="flex-1 overflow-y-auto focus:outline-none"
        ref={scrollParentRef}
        tabIndex={0}
        onKeyDown={handleKeyDown}
        role="listbox"
        aria-label={t('photoList.title')}
      >
        {isDirectoryView ? (
          directoryEntries.length === 0 ? (
            <div className="text-sm text-muted-foreground">{t('photoList.empty')}</div>
          ) : viewMode === 'grid' ? (
            <div className="relative w-full" style={{ height: gridVirtualizer.getTotalSize() }}>
              {gridVirtualItems.map((row) => {
                const start = row.index * gridColumns
                const rowItems = directoryEntries.slice(start, start + gridColumns)
                return (
                  <div
                    key={row.key}
                    className="absolute left-0 w-full"
                    style={{ height: row.size, transform: `translateY(${row.start}px)` }}
                  >
                    <div
                      className="grid gap-2"
                      style={{
                        gridTemplateColumns: `repeat(${gridColumns}, minmax(0, 1fr))`,
                      }}
                    >
                      {rowItems.map((entry) => {
                        const thumbnail = entryThumbnails[entry.path]
                        const isActive = entry.path === selectedEntryPath
                        return (
                          <button
                            type="button"
                            key={entry.path}
                            onClick={() => handleDirectoryEntryClick(entry)}
                            onDoubleClick={() => handleDirectoryEntryDoubleClick(entry)}
                            className={`rounded p-2 text-left transition-colors flex flex-col ${
                              isActive
                                ? 'bg-primary text-primary-foreground'
                                : 'bg-muted hover:bg-muted/80'
                            }`}
                            style={{ height: GRID_ITEM_SIZE }}
                          >
                            <div className="flex-1 flex items-center justify-center bg-background/50 rounded mb-2 overflow-hidden">
                              {entry.isDirectory ? (
                                <Folder className="h-6 w-6 text-yellow-500" />
                              ) : thumbnail ? (
                                <img
                                  src={thumbnail}
                                  alt={entry.name}
                                  className="h-full w-full object-cover"
                                />
                              ) : (
                                <Image className="h-6 w-6 text-blue-500" />
                              )}
                            </div>
                            <div className="truncate text-xs font-medium">{entry.name}</div>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="relative w-full" style={{ height: listVirtualizer.getTotalSize() }}>
              {listVirtualItems.map((row) => {
                const entry = directoryEntries[row.index]
                if (!entry) {
                  return null
                }
                const isDetail = viewMode === 'detail'
                const thumbnail = entryThumbnails[entry.path]
                const isActive = entry.path === selectedEntryPath
                return (
                  <div
                    key={entry.path}
                    className="absolute left-0 top-0 w-full"
                    style={{ height: row.size, transform: `translateY(${row.start}px)` }}
                  >
                    <button
                      type="button"
                      onClick={() => handleDirectoryEntryClick(entry)}
                      onDoubleClick={() => handleDirectoryEntryDoubleClick(entry)}
                      className={`w-full rounded p-2 text-left text-sm transition-colors flex items-center gap-3 overflow-hidden ${listRowClass} ${
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted hover:bg-muted/80'
                      }`}
                    >
                      <div
                        className={`flex items-center justify-center rounded bg-background/50 overflow-hidden ${
                          isDetail ? 'h-12 w-12' : 'h-10 w-10'
                        }`}
                      >
                        {entry.isDirectory ? (
                          <Folder className="h-5 w-5 text-yellow-500" />
                        ) : thumbnail ? (
                          <img
                            src={thumbnail}
                            alt={entry.name}
                            className="h-full w-full object-cover"
                          />
                        ) : (
                          <Image className="h-5 w-5 text-blue-500" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className={`truncate ${isDetail ? 'font-semibold' : 'font-medium'}`}>
                          {entry.name}
                        </div>
                        {entry.isDirectory ? (
                          <div className="mt-1 text-xs opacity-60">{t('common.folder')}</div>
                        ) : (
                          <div className="mt-1 text-xs opacity-60">
                            {formatFileSize(entry.fileSize)}
                            {isDetail &&
                              (entry.capturedTime ? (
                                <> • 📷 {new Date(entry.capturedTime).toLocaleString()}</>
                              ) : (
                                <> • 🕒 {new Date(entry.modifiedTime).toLocaleString()}</>
                              ))}
                          </div>
                        )}
                        {isDetail && (
                          <div className="mt-1 truncate text-xs opacity-60">{entry.path}</div>
                        )}
                      </div>
                      {!isDetail && (
                        <div className="text-xs opacity-60">
                          {entry.capturedTime ? (
                            <span title="撮影日時">
                              📷 {new Date(entry.capturedTime).toLocaleDateString()}
                            </span>
                          ) : (
                            <span title="更新日時">
                              🕒 {new Date(entry.modifiedTime).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      )}
                    </button>
                  </div>
                )
              })}
            </div>
          )
        ) : photos.length === 0 ? (
          <div className="text-sm text-muted-foreground">{t('photoList.empty')}</div>
        ) : viewMode === 'grid' ? (
          <div className="relative w-full" style={{ height: gridVirtualizer.getTotalSize() }}>
            {gridVirtualItems.map((row) => {
              const start = row.index * gridColumns
              const rowItems = photos.slice(start, start + gridColumns)
              return (
                <div
                  key={row.key}
                  className="absolute left-0 w-full"
                  style={{ height: row.size, transform: `translateY(${row.start}px)` }}
                >
                  <div
                    className="grid gap-2"
                    style={{ gridTemplateColumns: `repeat(${gridColumns}, minmax(0, 1fr))` }}
                  >
                    {rowItems.map((photo) => (
                      <button
                        type="button"
                        key={photo.path}
                        onClick={() => {
                          setSelectedEntryPath(photo.path)
                          selectPhoto(photo.path)
                        }}
                        className={`rounded p-2 text-left transition-colors flex flex-col ${
                          selectedEntryPath === photo.path
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted hover:bg-muted/80'
                        }`}
                        style={{ height: GRID_ITEM_SIZE }}
                      >
                        <div className="flex-1 flex items-center justify-center bg-background/50 rounded mb-2 overflow-hidden">
                          {photo.thumbnail ? (
                            <img
                              src={photo.thumbnail}
                              alt={photo.filename}
                              className="h-full w-full object-cover"
                            />
                          ) : (
                            <span className="text-3xl">🖼️</span>
                          )}
                        </div>
                        <div className="truncate text-xs font-medium">{photo.filename}</div>
                      </button>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="relative w-full" style={{ height: listVirtualizer.getTotalSize() }}>
            {listVirtualItems.map((row) => {
              const photo = photos[row.index]
              if (!photo) {
                return null
              }
              const isDetail = viewMode === 'detail'
              return (
                <div
                  key={photo.path}
                  className="absolute left-0 top-0 w-full"
                  style={{ height: row.size, transform: `translateY(${row.start}px)` }}
                >
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedEntryPath(photo.path)
                      selectPhoto(photo.path)
                    }}
                    className={`w-full rounded p-2 text-left text-sm transition-colors flex items-center gap-3 overflow-hidden ${listRowClass} ${
                      selectedEntryPath === photo.path
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                  >
                    <div
                      className={`flex items-center justify-center rounded bg-background/50 overflow-hidden ${
                        isDetail ? 'h-12 w-12' : 'h-10 w-10'
                      }`}
                    >
                      {photo.thumbnail ? (
                        <img
                          src={photo.thumbnail}
                          alt={photo.filename}
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <Image className="h-5 w-5 text-blue-500" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className={`truncate ${isDetail ? 'font-semibold' : 'font-medium'}`}>
                        {photo.filename}
                      </div>
                      {isDetail ? (
                        <div className="mt-1 space-y-1 text-xs opacity-80">
                          {photo.exif?.datetime && (
                            <div>📅 {new Date(photo.exif.datetime).toLocaleString()}</div>
                          )}
                          {photo.exif?.gps && (
                            <div>
                              📍 {photo.exif.gps.lat.toFixed(6)}, {photo.exif.gps.lng.toFixed(6)}
                            </div>
                          )}
                          {photo.exif?.camera && (
                            <div>
                              📷 {photo.exif.camera.make} {photo.exif.camera.model}
                            </div>
                          )}
                          {photo.exif?.width && photo.exif?.height && (
                            <div>
                              📐 {photo.exif.width} x {photo.exif.height}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="mt-1 flex items-center gap-2 text-xs opacity-80">
                          {photo.exif?.gps && <span>📍 GPS</span>}
                          {photo.exif?.datetime && (
                            <span>{new Date(photo.exif.datetime).toLocaleDateString()}</span>
                          )}
                        </div>
                      )}
                      {isDetail && (
                        <div className="mt-1 truncate text-xs opacity-60">{photo.path}</div>
                      )}
                    </div>
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
