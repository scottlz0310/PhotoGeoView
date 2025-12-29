// Tauri Commandsをインポート
use tauri::{command, Manager};

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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .setup(|app| {
            #[cfg(debug_assertions)]
            {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Debug)
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
                        .build(),
                )?;
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            greet,
            select_photo_file,
            select_photo_files
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
