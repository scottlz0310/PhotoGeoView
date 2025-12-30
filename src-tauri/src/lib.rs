// Tauri Commandsをインポート
use tauri::{command, Manager};

// モジュール定義
mod commands;
mod error;
mod models;

use crate::models::{ExifData, PhotoData};

/// Hello Worldコマンド（テスト用）
#[command]
fn greet(name: String) -> String {
    format!("Hello, {}! Welcome to PhotoGeoView.", name)
}

/// 単一ファイル選択ダイアログを開く
#[command]
async fn select_photo_file(app: tauri::AppHandle) -> Result<Option<String>, String> {
    use tauri_plugin_dialog::DialogExt;

    let file_path = app
        .dialog()
        .file()
        .add_filter("Images", &["jpg", "jpeg", "png", "tiff", "tif", "webp"])
        .blocking_pick_file();

    Ok(file_path.and_then(|path| path.as_path().map(|p| p.to_string_lossy().to_string())))
}

/// 複数ファイル選択ダイアログを開く
#[command]
async fn select_photo_files(app: tauri::AppHandle) -> Result<Vec<String>, String> {
    use tauri_plugin_dialog::DialogExt;

    let file_paths = app
        .dialog()
        .file()
        .add_filter("Images", &["jpg", "jpeg", "png", "tiff", "tif", "webp"])
        .blocking_pick_files();

    Ok(file_paths
        .unwrap_or_default()
        .into_iter()
        .filter_map(|path| path.as_path().map(|p| p.to_string_lossy().to_string()))
        .collect())
}

/// フォルダ選択ダイアログを開く
#[command]
async fn select_photo_folder(app: tauri::AppHandle) -> Result<Option<String>, String> {
    use tauri_plugin_dialog::DialogExt;

    let folder_path = app.dialog().file().blocking_pick_folder();

    Ok(folder_path.and_then(|path| path.as_path().map(|p| p.to_string_lossy().to_string())))
}

/// フォルダ内の画像ファイルをスキャン
#[command]
async fn scan_folder_for_photos(
    folder_path: String,
    recursive: bool,
) -> Result<Vec<String>, String> {
    use std::fs;
    use std::path::PathBuf;

    let supported_extensions = ["jpg", "jpeg", "png", "tiff", "tif", "webp"];
    let mut image_paths = Vec::new();

    fn scan_directory(
        dir: &std::path::Path,
        recursive: bool,
        extensions: &[&str],
        results: &mut Vec<String>,
    ) -> std::io::Result<()> {
        if !dir.is_dir() {
            return Ok(());
        }

        for entry in fs::read_dir(dir)? {
            let entry = entry?;
            let path = entry.path();

            if path.is_file() {
                if let Some(ext) = path.extension() {
                    let ext_str = ext.to_string_lossy().to_lowercase();
                    if extensions.contains(&ext_str.as_ref()) {
                        if let Some(path_str) = path.to_str() {
                            results.push(path_str.to_string());
                        }
                    }
                }
            } else if recursive && path.is_dir() {
                scan_directory(&path, recursive, extensions, results)?;
            }
        }

        Ok(())
    }

    let folder = PathBuf::from(&folder_path);
    scan_directory(&folder, recursive, &supported_extensions, &mut image_paths)
        .map_err(|e| format!("フォルダのスキャンに失敗: {}", e))?;

    log::info!(
        "フォルダスキャン完了: {} 個の画像ファイルを検出",
        image_paths.len()
    );

    Ok(image_paths)
}

/// 写真ファイルのEXIF情報を読み取る
#[command]
async fn read_photo_exif(path: String) -> Result<ExifData, String> {
    commands::read_exif(&path).map_err(|e| e.to_string())
}

/// 写真ファイルの基本情報とEXIF情報を取得
#[command]
async fn get_photo_data(path: String) -> Result<PhotoData, String> {
    use std::fs;

    // ファイルの基本情報を取得
    let file_path = std::path::Path::new(&path);
    let metadata = fs::metadata(&path).map_err(|e| format!("ファイル情報の取得に失敗: {}", e))?;

    let filename = file_path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown")
        .to_string();

    let file_size = metadata.len();

    let modified_time = metadata
        .modified()
        .ok()
        .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
        .map(|d| {
            chrono::DateTime::from_timestamp(d.as_secs() as i64, 0)
                .map(|dt| dt.to_rfc3339())
                .unwrap_or_default()
        })
        .unwrap_or_default();

    // EXIF情報を読み取る
    let exif = commands::read_exif(&path).ok();

    // サムネイルを生成（失敗しても続行）
    log::info!("サムネイル生成を開始: {}", path);
    let thumbnail = match commands::generate_thumbnail(&path) {
        Ok(thumb) => {
            log::info!("サムネイル生成成功: 長さ={}", thumb.len());
            Some(thumb)
        }
        Err(e) => {
            log::error!("サムネイル生成失敗: {}", e);
            None
        }
    };

    Ok(PhotoData {
        path: path.clone(),
        filename,
        file_size,
        modified_time,
        exif,
        thumbnail,
    })
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .setup(|app| {
            // ログファイルのクリーンアップ（起動時）
            if let Ok(log_dir) = app.path().app_log_dir() {
                if let Ok(entries) = std::fs::read_dir(&log_dir) {
                    for entry in entries.flatten() {
                        let path = entry.path();
                        if path.extension().and_then(|s| s.to_str()) == Some("log") {
                            // 古いログファイルを削除
                            let _ = std::fs::remove_file(&path);
                        }
                    }
                }
            }

            #[cfg(debug_assertions)]
            {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Debug)
                        .targets([
                            tauri_plugin_log::Target::new(tauri_plugin_log::TargetKind::LogDir { file_name: Some("photogeoview".into()) }),
                        ])
                        .build(),
                )?;

                // ログファイルの場所を出力
                if let Some(log_dir) = app.path().app_log_dir().ok() {
                    log::info!("📝 ログファイル: {:?}", log_dir);
                }
            }

            #[cfg(not(debug_assertions))]
            {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .targets([
                            tauri_plugin_log::Target::new(tauri_plugin_log::TargetKind::LogDir { file_name: Some("photogeoview".into()) }),
                        ])
                        .build(),
                )?;
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            greet,
            select_photo_file,
            select_photo_files,
            select_photo_folder,
            scan_folder_for_photos,
            read_photo_exif,
            get_photo_data
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
