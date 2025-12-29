// Tauri Commandsをインポート
use tauri::{command, Manager};

/// Hello Worldコマンド（テスト用）
#[command]
fn greet(name: String) -> String {
    format!("Hello, {}! Welcome to PhotoGeoView.", name)
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
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
