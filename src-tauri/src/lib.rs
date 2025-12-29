// Tauri Commandsをインポート
use tauri::command;

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
                use tauri_plugin_log::Target;

                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Debug)
                        .targets([
                            Target::Stdout,
                            Target::LogDir { file_name: Some("photogeoview.log".to_string()) },
                        ])
                        .build(),
                )?;

                // ログファイルの場所を出力
                if let Some(log_dir) = app.path().app_log_dir().ok() {
                    log::info!("📝 ログファイル: {}/photogeoview.log", log_dir.display());
                }
            }

            #[cfg(not(debug_assertions))]
            {
                use tauri_plugin_log::Target;

                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .targets([
                            Target::Stdout,
                            Target::LogDir { file_name: Some("photogeoview.log".to_string()) },
                        ])
                        .build(),
                )?;
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
