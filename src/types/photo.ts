/**
 * 写真データの型定義
 */

/**
 * GPS座標情報
 */
export interface Gps {
  /** 緯度 */
  lat: number
  /** 経度 */
  lng: number
}

/**
 * カメラ情報
 */
export interface CameraInfo {
  /** メーカー名 */
  make: string
  /** モデル名 */
  model: string
}

/**
 * EXIF情報
 */
export interface ExifData {
  /** GPS座標（存在しない場合はnull） */
  gps: Gps | null
  /** 撮影日時（ISO 8601形式、存在しない場合はnull） */
  datetime: string | null
  /** カメラ情報（存在しない場合はnull） */
  camera: CameraInfo | null
  /** 画像の幅（ピクセル） */
  width: number | null
  /** 画像の高さ（ピクセル） */
  height: number | null
  /** ISO感度 */
  iso: number | null
  /** 絞り値（F値） */
  aperture: number | null
  /** シャッター速度（秒） */
  shutterSpeed: number | null
  /** 焦点距離（mm） */
  focalLength: number | null
}

/**
 * 写真データ
 */
export interface PhotoData {
  /** ファイルの絶対パス */
  path: string
  /** ファイル名（拡張子含む） */
  filename: string
  /** ファイルサイズ（バイト） */
  fileSize: number
  /** ファイルの最終更新日時（ISO 8601形式） */
  modifiedTime: string
  /** EXIF情報（存在しない場合はnull） */
  exif: ExifData | null
  /** サムネイル画像（Base64エンコード、未生成の場合はnull） */
  thumbnail: string | null
}

/**
 * 写真リストのフィルター条件
 */
export interface PhotoFilter {
  /** 撮影日時の開始日（この日付以降） */
  dateFrom: Date | null
  /** 撮影日時の終了日（この日付以前） */
  dateTo: Date | null
  /** GPS情報の有無でフィルタリング */
  hasGps: boolean | null
}

/**
 * 地図の表示設定
 */
export interface MapSettings {
  /** 中心座標 */
  center: Gps
  /** ズームレベル（1-18） */
  zoom: number
  /** 地図タイルの種類 */
  tileLayer: 'osm' | 'google' | 'satellite'
}

/**
 * ディレクトリエントリ（フォルダまたはファイル）
 */
export interface DirectoryEntry {
  /** エントリの名前（ファイル名またはフォルダ名） */
  name: string
  /** エントリの絶対パス */
  path: string
  /** ディレクトリかどうか（true: フォルダ, false: ファイル） */
  isDirectory: boolean
  /** 最終更新日時（ISO 8601形式） */
  modifiedTime: string
  /** ファイルサイズ（バイト、ディレクトリの場合は0） */
  fileSize: number
}

/**
 * ディレクトリの内容
 */
export interface DirectoryContent {
  /** 現在のディレクトリパス */
  currentPath: string
  /** 親ディレクトリパス（ルートディレクトリの場合はnull） */
  parentPath: string | null
  /** ディレクトリ内のエントリ一覧（フォルダとファイル） */
  entries: DirectoryEntry[]
}
