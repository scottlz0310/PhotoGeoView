use thiserror::Error;

/// PhotoGeoViewのエラー型
#[derive(Error, Debug)]
pub enum PhotoError {
    #[error("ファイルが見つかりません: {0}")]
    FileNotFound(String),

    #[error("ファイルの読み取りに失敗しました: {0}")]
    FileReadError(String),

    #[error("EXIF情報の読み取りに失敗しました: {0}")]
    ExifReadError(String),

    #[error("GPS情報が存在しません")]
    NoGpsData,

    #[error("画像処理に失敗しました: {0}")]
    ImageProcessError(String),

    #[error("サムネイル生成に失敗しました: {0}")]
    ThumbnailGenerationError(String),

    #[error("内部エラー: {0}")]
    InternalError(String),
}

/// Result型のエイリアス
pub type Result<T> = std::result::Result<T, PhotoError>;
