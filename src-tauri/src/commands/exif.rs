use crate::error::{PhotoError, Result};
use crate::models::{CameraInfo, ExifData, Gps};
use exif::{In, Tag};
use std::fs::File;
use std::io::BufReader;
use std::path::Path;

/// EXIF情報を読み取る
#[tracing::instrument]
pub fn read_exif(path: &str) -> Result<ExifData> {
    let file_path = Path::new(path);

    // ファイルの存在確認
    if !file_path.exists() {
        return Err(PhotoError::FileNotFound(path.to_string()));
    }

    // ファイルを開く
    let file = File::open(file_path)
        .map_err(|e| PhotoError::FileReadError(format!("{}: {}", path, e)))?;

    let mut bufreader = BufReader::new(file);

    // EXIFデータを読み取る
    let exif_reader = exif::Reader::new();
    let exif = exif_reader
        .read_from_container(&mut bufreader)
        .map_err(|e| PhotoError::ExifReadError(format!("{}: {}", path, e)))?;

    // GPS情報を抽出
    let gps = extract_gps(&exif);

    // 撮影日時を抽出
    let datetime = extract_datetime(&exif);

    // カメラ情報を抽出
    let camera = extract_camera(&exif);

    // 画像サイズを抽出
    let (width, height) = extract_image_size(&exif);

    // ISO感度を抽出
    let iso = extract_iso(&exif);

    // 絞り値を抽出
    let aperture = extract_aperture(&exif);

    // シャッター速度を抽出
    let shutter_speed = extract_shutter_speed(&exif);

    // 焦点距離を抽出
    let focal_length = extract_focal_length(&exif);

    Ok(ExifData {
        gps,
        datetime,
        camera,
        width,
        height,
        iso,
        aperture,
        shutter_speed,
        focal_length,
    })
}

/// GPS情報を抽出
fn extract_gps(exif: &exif::Exif) -> Option<Gps> {
    let lat = extract_gps_coordinate(exif, Tag::GPSLatitude, Tag::GPSLatitudeRef)?;
    let lng = extract_gps_coordinate(exif, Tag::GPSLongitude, Tag::GPSLongitudeRef)?;

    Some(Gps { lat, lng })
}

/// GPS座標を抽出（度分秒 → 十進法に変換）
fn extract_gps_coordinate(exif: &exif::Exif, coord_tag: Tag, ref_tag: Tag) -> Option<f64> {
    use exif::Value;

    let coord_field = exif.get_field(coord_tag, In::PRIMARY)?;
    let ref_field = exif.get_field(ref_tag, In::PRIMARY)?;

    // 度分秒を取得
    let (degrees, minutes, seconds) = match &coord_field.value {
        Value::Rational(ref v) if v.len() >= 3 => {
            let d = v[0].to_f64();
            let m = v[1].to_f64();
            let s = v[2].to_f64();
            (d, m, s)
        }
        _ => return None,
    };

    // 十進法に変換
    let mut decimal = degrees + minutes / 60.0 + seconds / 3600.0;

    // 南緯または西経の場合は負の値にする
    let ref_str = ref_field.display_value().to_string();
    if ref_str == "S" || ref_str == "W" {
        decimal = -decimal;
    }

    Some(decimal)
}

/// 撮影日時を抽出（ISO 8601形式に変換）
fn extract_datetime(exif: &exif::Exif) -> Option<String> {
    let datetime_field = exif
        .get_field(Tag::DateTimeOriginal, In::PRIMARY)
        .or_else(|| exif.get_field(Tag::DateTime, In::PRIMARY))?;

    let datetime_str = datetime_field.display_value().to_string();

    // EXIF形式 "YYYY:MM:DD HH:MM:SS" を ISO 8601形式 "YYYY-MM-DDTHH:MM:SS" に変換
    let iso_datetime = datetime_str.replace(' ', "T").replace(':', "-");

    // 最初の2つのハイフンだけを保持（日付部分）、時刻部分はコロンに戻す
    let parts: Vec<&str> = iso_datetime.split('T').collect();
    if parts.len() == 2 {
        let date = parts[0];
        let time = parts[1].replace('-', ":");
        Some(format!("{}T{}", date, time))
    } else {
        Some(datetime_str)
    }
}

/// カメラ情報を抽出
fn extract_camera(exif: &exif::Exif) -> Option<CameraInfo> {
    let make = exif
        .get_field(Tag::Make, In::PRIMARY)?
        .display_value()
        .to_string()
        .trim()
        .to_string();

    let model = exif
        .get_field(Tag::Model, In::PRIMARY)?
        .display_value()
        .to_string()
        .trim()
        .to_string();

    Some(CameraInfo { make, model })
}

/// 画像サイズを抽出
fn extract_image_size(exif: &exif::Exif) -> (Option<u32>, Option<u32>) {
    let width = exif
        .get_field(Tag::PixelXDimension, In::PRIMARY)
        .or_else(|| exif.get_field(Tag::ImageWidth, In::PRIMARY))
        .and_then(|f| f.value.get_uint(0));

    let height = exif
        .get_field(Tag::PixelYDimension, In::PRIMARY)
        .or_else(|| exif.get_field(Tag::ImageLength, In::PRIMARY))
        .and_then(|f| f.value.get_uint(0));

    (width, height)
}

/// ISO感度を抽出
fn extract_iso(exif: &exif::Exif) -> Option<u32> {
    exif.get_field(Tag::PhotographicSensitivity, In::PRIMARY)
        .and_then(|f| f.value.get_uint(0))
}

/// 絞り値（F値）を抽出
fn extract_aperture(exif: &exif::Exif) -> Option<f64> {
    use exif::Value;

    exif.get_field(Tag::FNumber, In::PRIMARY)
        .and_then(|f| match &f.value {
            Value::Rational(ref v) if !v.is_empty() => Some(v[0].to_f64()),
            _ => None,
        })
}

/// シャッター速度を抽出
fn extract_shutter_speed(exif: &exif::Exif) -> Option<f64> {
    use exif::Value;

    exif.get_field(Tag::ExposureTime, In::PRIMARY)
        .and_then(|f| match &f.value {
            Value::Rational(ref v) if !v.is_empty() => Some(v[0].to_f64()),
            _ => None,
        })
}

/// 焦点距離を抽出
fn extract_focal_length(exif: &exif::Exif) -> Option<f64> {
    use exif::Value;

    exif.get_field(Tag::FocalLength, In::PRIMARY)
        .and_then(|f| match &f.value {
            Value::Rational(ref v) if !v.is_empty() => Some(v[0].to_f64()),
            _ => None,
        })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_read_exif_nonexistent_file() {
        let result = read_exif("/nonexistent/file.jpg");
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), PhotoError::FileNotFound(_)));
    }
}
