// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/

mod backend;

use backend::{init_backend_manager, start_backend_supervised, BackendEventPayload, BackendManager};
use tauri::Manager;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
fn backend_get_state(manager: tauri::State<'_, BackendManager>) -> BackendEventPayload {
    manager.state()
}

#[tauri::command]
fn backend_get_last_logs(manager: tauri::State<'_, BackendManager>) -> String {
    manager.last_logs_string()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let manager = init_backend_manager(app.handle())?;
            app.manage(manager.clone());

            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                start_backend_supervised(app_handle, manager).await;
            });

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();

                let manager = window.state::<BackendManager>().clone();
                if let Some(child) = manager.take_child() {
                    let _ = child.kill();
                }
                let _ = window.close();
            }
        })
        .invoke_handler(tauri::generate_handler![
            greet,
            backend_get_state,
            backend_get_last_logs
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
