use serde::{Deserialize, Serialize};

/// GPS座標情報
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Gps {
    /// 緯度
    pub lat: f64,
    /// 経度
    pub lng: f64,
}

/// カメラ情報
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CameraInfo {
    /// メーカー名
    pub make: String,
    /// モデル名
    pub model: String,
}

/// EXIF情報
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExifData {
    /// GPS座標（存在しない場合はNone）
    pub gps: Option<Gps>,
    /// 撮影日時（ISO 8601形式、存在しない場合はNone）
    pub datetime: Option<String>,
    /// カメラ情報（存在しない場合はNone）
    pub camera: Option<CameraInfo>,
    /// 画像の幅（ピクセル）
    pub width: Option<u32>,
    /// 画像の高さ（ピクセル）
    pub height: Option<u32>,
    /// ISO感度
    pub iso: Option<u32>,
    /// 絞り値（F値）
    pub aperture: Option<f64>,
    /// シャッター速度（秒）
    pub shutter_speed: Option<f64>,
    /// 焦点距離（mm）
    pub focal_length: Option<f64>,
}

/// 写真データ
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhotoData {
    /// ファイルの絶対パス
    pub path: String,
    /// ファイル名（拡張子含む）
    pub filename: String,
    /// ファイルサイズ（バイト）
    pub file_size: u64,
    /// ファイルの最終更新日時（ISO 8601形式）
    pub modified_time: String,
    /// EXIF情報（存在しない場合はNone）
    pub exif: Option<ExifData>,
    /// サムネイル画像（Base64エンコード、未生成の場合はNone）
    pub thumbnail: Option<String>,
}

impl PhotoData {
    /// ファイルパスから PhotoData を作成（EXIF情報とサムネイルは後から追加）
    #[allow(dead_code)]
    pub fn new(path: String, filename: String, file_size: u64, modified_time: String) -> Self {
        Self {
            path,
            filename,
            file_size,
            modified_time,
            exif: None,
            thumbnail: None,
        }
    }

    /// GPS情報を持っているかチェック
    #[allow(dead_code)]
    pub fn has_gps(&self) -> bool {
        self.exif.as_ref().and_then(|e| e.gps.as_ref()).is_some()
    }

    /// 撮影日時を持っているかチェック
    #[allow(dead_code)]
    pub fn has_datetime(&self) -> bool {
        self.exif
            .as_ref()
            .and_then(|e| e.datetime.as_ref())
            .is_some()
    }
}

/// ディレクトリエントリ（フォルダまたはファイル）
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DirectoryEntry {
    /// エントリの名前（ファイル名またはフォルダ名）
    pub name: String,
    /// エントリの絶対パス
    pub path: String,
    /// ディレクトリかどうか（true: フォルダ, false: ファイル）
    pub is_directory: bool,
    /// 最終更新日時（ISO 8601形式）
    pub modified_time: String,
    /// 撮影日時（ISO 8601形式、存在しない場合はNone）
    pub captured_time: Option<String>,
    /// ファイルサイズ（バイト、ディレクトリの場合は0）
    pub file_size: u64,
}

/// ディレクトリの内容
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DirectoryContent {
    /// 現在のディレクトリパス
    pub current_path: String,
    /// 親ディレクトリパス（ルートディレクトリの場合はNone）
    pub parent_path: Option<String>,
    /// ディレクトリ内のエントリ一覧（フォルダとファイル）
    pub entries: Vec<DirectoryEntry>,
}
