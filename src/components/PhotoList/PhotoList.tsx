import { invoke } from '@tauri-apps/api/core'
import {
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Folder,
  FolderOpen,
  Grid,
  Image,
  LayoutList,
  List,
  RefreshCw,
} from 'lucide-react'
import React, { useEffect, useState } from 'react'
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
import { Progress } from '@/components/ui/progress'
import { usePhotoStore } from '@/stores/photoStore'
import { useSettingsStore } from '@/stores/settingsStore'
import type { PhotoData } from '@/types/photo'

export function PhotoList(): React.ReactElement {
  const {
    photos,
    selectedPhoto,
    viewMode,
    currentPath,
    directoryEntries,
    addPhotos,
    selectPhoto,
    setViewMode,
    navigateToDirectory,
  } = usePhotoStore()
  const { settings, updateSettings } = useSettingsStore()
  const [isLoading, setIsLoading] = useState(false)
  const [loadingProgress, setLoadingProgress] = useState(0)
  const [loadingStatus, setLoadingStatus] = useState('')

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

  const handleOpenFolder = async () => {
    setIsLoading(true)
    setLoadingStatus('フォルダを選択中...')
    try {
      const folderPath = await invoke<string | null>('select_photo_folder')
      if (folderPath) {
        setLoadingStatus('フォルダを読み込み中...')
        // ナビゲーションモードに入る
        await navigateToDirectory(folderPath)
        // 設定に保存
        updateSettings({ lastOpenedFolder: folderPath })
        toast.success('フォルダを開きました', {
          description: `${directoryEntries.length}件のアイテムが見つかりました`,
        })
      }
    } catch (error) {
      toast.error('フォルダの読み込みに失敗しました', {
        description: String(error),
      })
    } finally {
      setIsLoading(false)
      setLoadingStatus('')
      setLoadingProgress(0)
    }
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

  // 画像ファイルをダブルクリックして読み込み
  const handleFileDoubleClick = async (filePath: string) => {
    setIsLoading(true)
    setLoadingStatus('写真データを読み込み中...')
    try {
      const photoData = await invoke<PhotoData>('get_photo_data', { path: filePath })
      addPhotos([photoData])
      selectPhoto(photoData.path)
    } catch (error) {
      toast.error('写真の読み込みに失敗しました', {
        description: String(error),
      })
    } finally {
      setIsLoading(false)
      setLoadingStatus('')
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
      toast.error('上位フォルダに移動できませんでした', {
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
    try {
      await navigateToDirectory(currentPath)
      toast.success('フォルダを再読み込みしました')
    } catch (error) {
      toast.error('再読み込みに失敗しました', {
        description: String(error),
      })
    } finally {
      setIsLoading(false)
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
            title="戻る"
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
            title="進む"
          >
            <ArrowRight className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handleNavigateUp}
            disabled={!currentPath || isLoading}
            title="上位フォルダへ"
          >
            <ArrowUp className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handleRefresh}
            disabled={!currentPath || isLoading}
            title="再読み込み"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handleOpenFolder}
            disabled={isLoading}
            title="フォルダを開く"
          >
            <FolderOpen className="h-4 w-4" />
          </Button>
        </div>

        {/* 右側: ビューモード切り替えボタン */}
        <div className="flex items-center rounded-md border border-border bg-background p-1">
          <button
            type="button"
            onClick={() => setViewMode('list')}
            className={`rounded p-1.5 transition-colors ${
              viewMode === 'list'
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            }`}
            title="リスト表示"
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
            title="詳細表示"
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
            title="グリッド表示"
          >
            <Grid className="h-4 w-4" />
          </button>
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

      {/* Loading indicator */}
      {isLoading && (
        <div className="mb-4 space-y-2">
          <Progress value={loadingProgress} className="h-2" />
          <p className="text-xs text-muted-foreground text-center">{loadingStatus}</p>
        </div>
      )}

      {/* コンテンツ表示エリア */}
      <div className="flex-1 overflow-y-auto">
        {/* ナビゲーションモード: ディレクトリ内容を表示 */}
        {currentPath && directoryEntries.length > 0 ? (
          <div className="space-y-2">
            {directoryEntries.map((entry) => (
              <button
                type="button"
                key={entry.path}
                onDoubleClick={() =>
                  entry.isDirectory
                    ? handleFolderDoubleClick(entry.path)
                    : handleFileDoubleClick(entry.path)
                }
                className="w-full rounded p-2 text-left text-sm transition-colors bg-muted hover:bg-muted/80 flex items-center gap-2"
              >
                {/* アイコン */}
                {entry.isDirectory ? (
                  <Folder className="h-4 w-4 text-yellow-500" />
                ) : (
                  <Image className="h-4 w-4 text-blue-500" />
                )}

                {/* エントリ名 */}
                <div className="flex-1">
                  <div className="truncate font-medium">{entry.name}</div>
                  {!entry.isDirectory && (
                    <div className="text-xs opacity-60">
                      {(entry.fileSize / 1024).toFixed(1)} KB
                    </div>
                  )}
                </div>

                {/* 最終更新日時 */}
                <div className="text-xs opacity-60">
                  {new Date(entry.modifiedTime).toLocaleDateString()}
                </div>
              </button>
            ))}
          </div>
        ) : photos.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            写真がまだ読み込まれていません。
            <br />
            上のボタンから写真やフォルダを開いてください。
          </div>
        ) : (
          <>
            {/* リスト表示 */}
            {viewMode === 'list' && (
              <div className="space-y-2">
                {photos.map((photo) => (
                  <button
                    type="button"
                    key={photo.path}
                    onClick={() => selectPhoto(photo.path)}
                    className={`w-full rounded p-2 text-left text-sm transition-colors ${
                      selectedPhoto?.path === photo.path
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                  >
                    <div className="truncate font-medium">{photo.filename}</div>
                    <div className="mt-1 flex items-center gap-2 text-xs opacity-80">
                      {photo.exif?.gps && <span>📍 GPS</span>}
                      {photo.exif?.datetime && (
                        <span>{new Date(photo.exif.datetime).toLocaleDateString()}</span>
                      )}
                    </div>
                    <div className="mt-1 truncate text-xs opacity-60">{photo.path}</div>
                  </button>
                ))}
              </div>
            )}

            {/* 詳細表示 */}
            {viewMode === 'detail' && (
              <div className="space-y-3">
                {photos.map((photo) => (
                  <button
                    type="button"
                    key={photo.path}
                    onClick={() => selectPhoto(photo.path)}
                    className={`w-full rounded p-3 text-left text-sm transition-colors ${
                      selectedPhoto?.path === photo.path
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                  >
                    <div className="truncate font-semibold">{photo.filename}</div>
                    <div className="mt-2 space-y-1 text-xs opacity-80">
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
                    <div className="mt-2 truncate text-xs opacity-60">{photo.path}</div>
                  </button>
                ))}
              </div>
            )}

            {/* グリッド表示 */}
            {viewMode === 'grid' && (
              <div className="grid grid-cols-2 gap-2">
                {photos.map((photo) => (
                  <button
                    type="button"
                    key={photo.path}
                    onClick={() => selectPhoto(photo.path)}
                    className={`aspect-square rounded p-2 text-left transition-colors ${
                      selectedPhoto?.path === photo.path
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                  >
                    <div className="flex h-full flex-col">
                      {/* サムネイル領域 */}
                      <div className="flex-1 flex items-center justify-center bg-background/50 rounded mb-2 overflow-hidden">
                        {photo.thumbnail ? (
                          <img
                            src={photo.thumbnail}
                            alt={photo.filename}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <span className="text-4xl">🖼️</span>
                        )}
                      </div>
                      <div className="truncate text-xs font-medium">{photo.filename}</div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
