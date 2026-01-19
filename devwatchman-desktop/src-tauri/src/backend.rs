use serde::Serialize;
use std::{
    collections::VecDeque,
    fs,
    io::{Read, Write},
    net::{SocketAddr, TcpStream},
    path::{Path, PathBuf},
    sync::{Arc, Mutex},
    time::{Duration, Instant},
};
use tauri::{AppHandle, Emitter, Manager};
use tauri_plugin_shell::{
    process::{CommandChild, CommandEvent},
    ShellExt,
};

const PORT_LINE_PREFIX: &str = "DEVWATCHMAN_PORT=";
const LOG_RING_MAX_LINES: usize = 200;
const PORT_DETECT_TIMEOUT: Duration = Duration::from_secs(15);
const HEALTH_TIMEOUT: Duration = Duration::from_secs(45);

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum BackendEventPayload {
    Starting,
    PortDetected { port: u16 },
    Ready {
        port: u16,
        base_url: String,
        log_path: String,
    },
    Error {
        message: String,
        details: String,
        log_path: String,
        last_logs: String,
    },
}

#[derive(Debug, Clone)]
struct TerminationInfo {
    code: Option<i32>,
    signal: Option<i32>,
}

#[derive(Debug)]
struct BackendRuntime {
    log_path: PathBuf,
    log_file: Mutex<fs::File>,
    ring: Mutex<VecDeque<String>>,
    state: Mutex<BackendEventPayload>,
    termination: Mutex<Option<TerminationInfo>>,
    child: Mutex<Option<CommandChild>>,
}

#[derive(Clone)]
pub struct BackendManager {
    inner: Arc<BackendRuntime>,
}

impl BackendManager {
    pub fn new(log_path: PathBuf, log_file: fs::File) -> Self {
        Self {
            inner: Arc::new(BackendRuntime {
                log_path,
                log_file: Mutex::new(log_file),
                ring: Mutex::new(VecDeque::new()),
                state: Mutex::new(BackendEventPayload::Starting),
                termination: Mutex::new(None),
                child: Mutex::new(None),
            }),
        }
    }

    pub fn log_path_string(&self) -> String {
        self.inner.log_path.to_string_lossy().to_string()
    }

    pub fn state(&self) -> BackendEventPayload {
        self.inner.state.lock().unwrap().clone()
    }

    pub fn set_state(&self, state: BackendEventPayload) {
        *self.inner.state.lock().unwrap() = state;
    }

    pub fn last_logs_string(&self) -> String {
        let ring = self.inner.ring.lock().unwrap();
        ring.iter().cloned().collect::<Vec<_>>().join("\n")
    }

    fn push_log_line(&self, line: String) {
        {
            let mut ring = self.inner.ring.lock().unwrap();
            ring.push_back(line.clone());
            while ring.len() > LOG_RING_MAX_LINES {
                ring.pop_front();
            }
        }

        let mut file = self.inner.log_file.lock().unwrap();
        let _ = writeln!(file, "{line}");
        let _ = file.flush();
    }

    fn set_termination(&self, info: TerminationInfo) {
        *self.inner.termination.lock().unwrap() = Some(info);
    }

    fn termination(&self) -> Option<TerminationInfo> {
        self.inner.termination.lock().unwrap().clone()
    }

    pub fn set_child(&self, child: CommandChild) {
        *self.inner.child.lock().unwrap() = Some(child);
    }

    pub fn take_child(&self) -> Option<CommandChild> {
        self.inner.child.lock().unwrap().take()
    }
}

fn rotate_log_if_needed(path: &Path) -> std::io::Result<()> {
    const MAX_BYTES: u64 = 5 * 1024 * 1024;
    let Ok(metadata) = fs::metadata(path) else {
        return Ok(());
    };
    if metadata.len() <= MAX_BYTES {
        return Ok(());
    }

    let backup = path.with_extension("log.1");
    let _ = fs::remove_file(&backup);
    fs::rename(path, backup)?;
    Ok(())
}

pub fn init_backend_manager(app: &AppHandle) -> std::io::Result<BackendManager> {
    let base_dir = app
        .path()
        .app_data_dir()
        .unwrap_or_else(|_| std::env::temp_dir().join("DevWatchMan"));

    let log_dir = base_dir.join("logs");
    fs::create_dir_all(&log_dir)?;

    let log_path = log_dir.join("backend.log");
    let _ = rotate_log_if_needed(&log_path);

    let log_file = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&log_path)?;

    Ok(BackendManager::new(log_path, log_file))
}

pub async fn start_backend_supervised(app: AppHandle, manager: BackendManager) {
    manager.set_state(BackendEventPayload::Starting);
    let _ = app.emit("backend://state", manager.state());

    let (mut rx, child) = match spawn_sidecar(&app) {
        Ok(v) => v,
        Err(e) => {
            let details = format!("Failed to spawn backend sidecar: {e}");
            let last_logs = manager.last_logs_string();
            manager.set_state(BackendEventPayload::Error {
                message: "Backend spawn failed".to_string(),
                details,
                log_path: manager.log_path_string(),
                last_logs,
            });
            let _ = app.emit("backend://state", manager.state());
            return;
        }
    };

    manager.set_child(child);

    let manager_for_reader = manager.clone();
    let app_for_reader = app.clone();
    let (port_tx, port_rx) = tokio::sync::oneshot::channel::<u16>();

    tauri::async_runtime::spawn(async move {
        let mut port_tx = Some(port_tx);
        let mut port_sent = false;

        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    let line = bytes_to_line(&line);
                    if !line.is_empty() {
                        manager_for_reader.push_log_line(format!("[stdout] {line}"));
                    }

                    if !port_sent {
                        if let Some(port) = parse_port_from_stdout_line(&line) {
                            port_sent = true;
                            if let Some(tx) = port_tx.take() {
                                let _ = tx.send(port);
                            }
                            manager_for_reader.set_state(BackendEventPayload::PortDetected { port });
                            let _ = app_for_reader.emit("backend://state", manager_for_reader.state());
                        }
                    }
                }
                CommandEvent::Stderr(line) => {
                    let line = bytes_to_line(&line);
                    if !line.is_empty() {
                        manager_for_reader.push_log_line(format!("[stderr] {line}"));
                    }
                }
                CommandEvent::Error(err) => {
                    manager_for_reader.push_log_line(format!("[error] {err}"));
                }
                CommandEvent::Terminated(payload) => {
                    manager_for_reader.set_termination(TerminationInfo {
                        code: payload.code,
                        signal: payload.signal,
                    });
                    manager_for_reader.push_log_line(format!(
                        "[process] terminated (code={:?}, signal={:?})",
                        payload.code, payload.signal
                    ));
                    break;
                }
                _ => {}
            }
        }
    });

    let port = match tokio::time::timeout(PORT_DETECT_TIMEOUT, port_rx).await {
        Ok(Ok(port)) => port,
        Ok(Err(_)) => {
            emit_startup_error(
                &app,
                &manager,
                "Backend exited before reporting port",
                "Backend process ended before printing DEVWATCHMAN_PORT=<port> on stdout.",
            );
            return;
        }
        Err(_) => {
            emit_startup_error(
                &app,
                &manager,
                "Backend port detection timed out",
                &format!(
                    "Didn't see {PORT_LINE_PREFIX}<port> on stdout within {:?}.",
                    PORT_DETECT_TIMEOUT
                ),
            );
            return;
        }
    };

    let base_url = format!("http://127.0.0.1:{port}");
    match wait_for_health(&manager, port).await {
        Ok(()) => {
            manager.set_state(BackendEventPayload::Ready {
                port,
                base_url,
                log_path: manager.log_path_string(),
            });
            let _ = app.emit("backend://state", manager.state());
        }
        Err(err) => {
            emit_startup_error(&app, &manager, "Backend health check failed", &err);
        }
    }
}

fn emit_startup_error(app: &AppHandle, manager: &BackendManager, message: &str, details: &str) {
    let mut details_out = details.to_string();

    if let Some(term) = manager.termination() {
        let exit = match (term.code, term.signal) {
            (Some(code), Some(sig)) => format!("exit code: {code}, signal: {sig}"),
            (Some(code), None) => format!("exit code: {code}"),
            (None, Some(sig)) => format!("signal: {sig}"),
            (None, None) => "exit: unknown".to_string(),
        };
        details_out = format!("{details_out}\n{exit}");
    }

    let last_logs = manager.last_logs_string();
    manager.set_state(BackendEventPayload::Error {
        message: message.to_string(),
        details: details_out,
        log_path: manager.log_path_string(),
        last_logs: last_logs.clone(),
    });
    let _ = app.emit("backend://state", manager.state());
}

fn spawn_sidecar(
    app: &AppHandle,
) -> Result<(tauri::async_runtime::Receiver<CommandEvent>, CommandChild), String>
{
    let candidates = ["devwatchman-backend", "binaries/devwatchman-backend"];
    let parent_pid = std::process::id().to_string();

    let mut last_err = None;
    for id in candidates {
        match app
            .shell()
            .sidecar(id)
            .map_err(|e| e.to_string())?
            .args(["--port", "0"])
            .env("DEVWATCHMAN_PARENT_PID", &parent_pid)
            .spawn()
        {
            Ok(pair) => return Ok(pair),
            Err(e) => last_err = Some(format!("{id}: {e}")),
        }
    }

    Err(last_err.unwrap_or_else(|| "Unknown spawn error".to_string()))
}

fn parse_port_from_stdout_line(line: &str) -> Option<u16> {
    let line = line.trim();
    if !line.starts_with(PORT_LINE_PREFIX) {
        return None;
    }
    let port_str = line[PORT_LINE_PREFIX.len()..].trim();
    let port: u16 = port_str.parse().ok()?;
    if port == 0 {
        return None;
    }
    Some(port)
}

fn bytes_to_line(bytes: &[u8]) -> String {
    String::from_utf8_lossy(bytes)
        .trim_end_matches(&['\r', '\n'][..])
        .to_string()
}

async fn wait_for_health(manager: &BackendManager, port: u16) -> Result<(), String> {
    let start = Instant::now();
    let mut delay = Duration::from_millis(250);
    let mut last_err = String::new();

    loop {
        if start.elapsed() >= HEALTH_TIMEOUT {
            let suffix = if last_err.is_empty() {
                "no response"
            } else {
                last_err.as_str()
            };
            return Err(format!(
                "Backend didn't become healthy within {:?} ({suffix})",
                HEALTH_TIMEOUT
            ));
        }

        if let Some(term) = manager.termination() {
            let exit = match (term.code, term.signal) {
                (Some(code), Some(sig)) => format!("exit code: {code}, signal: {sig}"),
                (Some(code), None) => format!("exit code: {code}"),
                (None, Some(sig)) => format!("signal: {sig}"),
                (None, None) => "exit: unknown".to_string(),
            };
            return Err(format!("Backend exited during startup ({exit})"));
        }

        match tokio::task::spawn_blocking(move || check_health_http(port)).await {
            Ok(Ok(true)) => return Ok(()),
            Ok(Ok(false)) => {
                last_err = "unhealthy response".to_string();
            }
            Ok(Err(e)) => {
                last_err = e;
            }
            Err(e) => {
                last_err = e.to_string();
            }
        }

        tokio::time::sleep(delay).await;
        delay = std::cmp::min(delay * 2, Duration::from_secs(1));
    }
}

fn check_health_http(port: u16) -> Result<bool, String> {
    let addr: SocketAddr = ([127, 0, 0, 1], port).into();
    let mut stream = match TcpStream::connect_timeout(&addr, Duration::from_millis(800)) {
        Ok(s) => s,
        Err(e) => {
            // connection refused / timed out: not ready yet
            return Err(e.to_string());
        }
    };

    let _ = stream.set_read_timeout(Some(Duration::from_millis(800)));
    let _ = stream.set_write_timeout(Some(Duration::from_millis(800)));

    let req = format!(
        "GET /api/health HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nConnection: close\r\nAccept: application/json\r\n\r\n"
    );
    stream
        .write_all(req.as_bytes())
        .map_err(|e| e.to_string())?;

    let mut resp = String::new();
    stream.read_to_string(&mut resp).map_err(|e| e.to_string())?;

    let (status_ok, body) = match resp.split_once("\r\n\r\n") {
        Some((head, body)) => (head.starts_with("HTTP/1.1 200") || head.starts_with("HTTP/1.0 200"), body),
        None => (resp.starts_with("HTTP/1.1 200") || resp.starts_with("HTTP/1.0 200"), ""),
    };

    if !status_ok {
        return Ok(false);
    }

    let body_trim = body.trim();
    if body_trim.is_empty() {
        return Ok(false);
    }

    // Minimal JSON check: endpoint should be {"ok": true}
    let normalized = body_trim.replace(' ', "");
    Ok(normalized.contains("\"ok\":true"))
}
