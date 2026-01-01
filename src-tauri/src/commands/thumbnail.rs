use crate::error::{PhotoError, Result};
use base64::{engine::general_purpose, Engine as _};
use image::{imageops::FilterType, ImageFormat};
use std::io::Cursor;
use std::path::Path;

/// サムネイルの最大サイズ（ピクセル）
const THUMBNAIL_SIZE: u32 = 200;

/// 画像ファイルからサムネイルを生成してBase64文字列として返す
pub fn generate_thumbnail(path: &str) -> Result<String> {
    log::debug!("サムネイル生成開始: {}", path);
    let file_path = Path::new(path);

    // ファイルの存在確認
    if !file_path.exists() {
        log::error!("ファイルが見つかりません: {}", path);
        return Err(PhotoError::FileNotFound(path.to_string()));
    }

    // 画像を読み込む
    log::debug!("画像を読み込み中: {}", path);
    let img = image::open(file_path).map_err(|e| {
        log::error!("画像の読み込みに失敗: {}", e);
        PhotoError::ImageProcessError(format!("画像の読み込みに失敗: {}", e))
    })?;

    log::debug!("画像サイズ: {}x{}", img.width(), img.height());

    // アスペクト比を維持してLanczos3でリサイズ
    let thumbnail = img.resize(THUMBNAIL_SIZE, THUMBNAIL_SIZE, FilterType::Lanczos3);

    // JPEGとしてメモリにエンコード
    let mut buffer = Cursor::new(Vec::new());
    thumbnail
        .write_to(&mut buffer, ImageFormat::Jpeg)
        .map_err(|e| {
            PhotoError::ImageProcessError(format!("サムネイルのエンコードに失敗: {}", e))
        })?;

    // Base64エンコード
    let base64_data = buffer.into_inner();
    let base64_string = general_purpose::STANDARD.encode(&base64_data);

    log::debug!("サムネイル生成完了: サイズ={}バイト, Base64長={}", base64_data.len(), base64_string.len());

    // Data URI形式で返す
    let data_uri = format!("data:image/jpeg;base64,{}", base64_string);
    log::debug!("Data URI生成完了: 長さ={}", data_uri.len());

    Ok(data_uri)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_generate_thumbnail_nonexistent_file() {
        let result = generate_thumbnail("/nonexistent/file.jpg");
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), PhotoError::FileNotFound(_)));
    }
}
