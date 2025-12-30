/**
 * アプリケーション設定の型定義
 */

import type { ViewMode } from '@/stores/photoStore'

/**
 * 地図タイルの種類
 */
export type TileLayerType = 'osm' | 'satellite'

/**
 * テーマ設定
 */
export type Theme = 'light' | 'dark' | 'system'

/**
 * 言語設定
 */
export type Language = 'ja' | 'en'

/**
 * 表示設定
 */
export interface DisplaySettings {
  /** デフォルトのビューモード */
  defaultViewMode: ViewMode
  /** EXIF情報を常に表示するか */
  showExifByDefault: boolean
  /** グリッド表示の列数 */
  gridColumns: number
}

/**
 * 地図設定
 */
export interface MapSettings {
  /** デフォルトのズームレベル（1-18） */
  defaultZoom: number
  /** 地図タイルの種類 */
  tileLayer: TileLayerType
  /** マーカークラスタリングを有効化 */
  enableClustering: boolean
}

/**
 * UI設定
 */
export interface UISettings {
  /** テーマ */
  theme: Theme
  /** 言語 */
  language: Language
  /** サイドバーの幅（ピクセル） */
  sidebarWidth: number
}

/**
 * アプリケーション設定全体
 */
export interface AppSettings {
  /** 表示設定 */
  display: DisplaySettings
  /** 地図設定 */
  map: MapSettings
  /** UI設定 */
  ui: UISettings
  /** 前回開いたフォルダパス */
  lastOpenedFolder: string | null
  /** 設定のバージョン（将来の互換性のため） */
  version: number
}

/**
 * デフォルト設定
 */
export const DEFAULT_SETTINGS: AppSettings = {
  display: {
    defaultViewMode: 'list',
    showExifByDefault: true,
    gridColumns: 2,
  },
  map: {
    defaultZoom: 13,
    tileLayer: 'osm',
    enableClustering: true,
  },
  ui: {
    theme: 'system',
    language: 'ja',
    sidebarWidth: 300,
  },
  lastOpenedFolder: null,
  version: 1,
}
