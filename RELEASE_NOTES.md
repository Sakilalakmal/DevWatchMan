# 🖥️ DevWatchMan v0.1.0

**Real-time system monitoring desktop application for Windows**

## ✨ Features

- 📊 **Live System Metrics**: CPU, RAM, disk usage, and network stats
- 🔌 **Port Monitoring**: Track active network connections and services
- 🚨 **Intelligent Alerts**: Configurable thresholds with real-time notifications
- 📈 **Interactive Charts**: Beautiful, responsive visualizations
- 🎨 **Modern UI**: Built with Tauri for native performance
- 🔒 **Privacy First**: 100% local processing—no data leaves your machine

## 🛠️ Tech Stack

- **Frontend**: Tauri (Rust + WebView)
- **Backend**: FastAPI (Python)
- **Architecture**: Desktop app with embedded sidecar server

## 📥 Installation

1. Download `DevWatchMan_0.1.0_x64-setup.exe` below
2. Run the installer
3. Windows SmartScreen may appear—click **"More info"** → **"Run anyway"**
4. Launch DevWatchMan from Start Menu or Desktop shortcut

## 💻 System Requirements

- **OS**: Windows 10/11 (x64)
- **Runtime**: WebView2 (auto-installed if missing)
- **No external dependencies**: Python/Node.js not required

## 🔐 Security Note

This app runs entirely on your local machine. No telemetry, no cloud services, no internet required.

---

## 🐛 Known Issues

- First launch may take 5-10 seconds while the sidecar initializes
- Antivirus software may require manual approval on first run

## 📝 Feedback

Found a bug? Have a feature request? [Open an issue](https://github.com/Sakilalakmal/DevWatchMan/issues)!

---

**Full Changelog**: https://github.com/Sakilalakmal/DevWatchMan/commits/v0.1.0