<div align="center">

# 🔍 DevWatchMan

![DevWatchMan Banner](https://img.shields.io/badge/DevWatchMan-System_Monitor-2563EB? style=for-the-badge)

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB? style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![WebSocket](https://img.shields.io/badge/WebSocket-010101?style=for-the-badge&logo=socketdotio&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Chart.js](https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![Tauri](https://img.shields.io/badge/Tauri-FFC131?style=for-the-badge&logo=tauri&logoColor=white)](https://tauri.app/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Rust](https://img.shields.io/badge/Rust-000000?style=for-the-badge&logo=rust&logoColor=white)](https://www.rust-lang.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

**A comprehensive real-time system monitoring application built with FastAPI and modern web technologies**

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [API Documentation](#-api-endpoints) • [Configuration](#%EF%B8%8F-configuration) • [Tech Stack](#%EF%B8%8F-tech-stack) • [Architecture](#-architecture)

</div>

---

## 📋 Overview

**DevWatchMan** is a powerful, production-ready system monitoring solution that provides real-time insights into your system's performance.  Built with FastAPI for high-performance backend operations and modern web technologies for a responsive frontend, it offers comprehensive monitoring capabilities including CPU, memory, disk usage, network statistics, port monitoring, Docker container tracking, and intelligent alerting—all through a beautiful, responsive web dashboard.

### 🎯 Key Highlights

- 🔄 **Real-time WebSocket Updates** - Instant metric visualization with 3-second refresh intervals
- 📊 **Interactive Charts** - Powered by Chart.js with historical data up to 30 days
- 🚨 **Smart Alert System** - Configurable thresholds with cooldown periods and severity levels
- 🌐 **Network Quality Monitoring** - Latency tracking and connectivity status
- 🔌 **Port Monitoring** - Track critical development and production ports
- 🐳 **Docker Integration** - Monitor container status and resource usage
- 💾 **SQLite Database** - Persistent historical data storage with automatic retention
- ⚡ **FastAPI Backend** - High-performance async API endpoints
- 🎨 **Modern UI** - Beautiful dark/light mode with TailwindCSS
- 🖥️ **Desktop Application** - Cross-platform Tauri-based desktop app
- 📱 **Responsive Design** - Works seamlessly on desktop and mobile devices
- 🔐 **Profile Management** - Multiple monitoring profiles for different environments

---

## ✨ Features

### 📈 System Monitoring
- **CPU Usage** - Real-time CPU percentage tracking across all cores
- **Memory Monitoring** - RAM usage with detailed bytes-level information and swap memory
- **Disk Usage** - Track disk space utilization across all mounted drives
- **Network Statistics** - Upload/download speeds in real-time with historical graphs
- **Process Monitoring** - Top processes by CPU and memory consumption
- **Network Quality** - Ping-based latency monitoring with quality classification

### 🚨 Advanced Features
- **WebSocket Live Updates** - Get instant updates without page refresh (3-second intervals)
- **Historical Data** - View performance trends over time (up to 720 hours / 30 days)
- **Port Status Monitoring** - Track critical ports (3000, 5173, 8000, 1433, 5672, 15672)
- **Network Quality Checks** - Ping-based latency monitoring (default:  1. 1. 1.1)
- **Docker Container Monitoring** - Real-time status and resource usage of Docker containers
- **Profile System** - Switch between monitoring profiles (default, frontend-dev, microservices)
- **Alert System** with: 
  - CPU threshold alerts (default: 85%)
  - RAM threshold alerts (default: 90%)
  - Required port monitoring with cooldown (60 seconds)
  - Severity levels:  critical, warning, info
  - Alert muting and acknowledgment
  - Event timeline tracking

### 🎨 Dashboard Features
- **Real-time KPIs** - CPU, RAM, Disk, Network metrics updated live
- **Historical Charts** - Interactive time-series visualizations
- **Port Status Grid** - Visual status of monitored ports with process information
- **Alert Panel** - Recent alerts with severity indicators
- **Timeline View** - System events and alert history
- **Docker Dashboard** - Container status and resource graphs
- **Profile Switcher** - Quick switching between monitoring profiles
- **Dark/Light Mode** - Automatic theme switching
- **Responsive Layout** - Optimized for all screen sizes

---

## 🛠️ Tech Stack

### Backend Technologies

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.10+ | Core programming language |
| **FastAPI** | Latest | Modern, high-performance web framework |
| **Uvicorn** | Latest | Lightning-fast ASGI server |
| **Pydantic** | Latest | Data validation using Python type annotations |
| **psutil** | Latest | Cross-platform library for system monitoring |
| **SQLite** | 3.x | Lightweight embedded database |
| **Jinja2** | Latest | Server-side template rendering |
| **Python-multipart** | Latest | Form data handling |
| **Docker SDK** | Latest | Docker container monitoring |

### Frontend Technologies

| Technology | Purpose |
|-----------|---------|
| **HTML5/CSS3** | Semantic markup and modern styling |
| **JavaScript (Vanilla)** | No framework dependencies, pure performance |
| **TailwindCSS** | Utility-first CSS framework (via CDN) |
| **Chart.js** | Beautiful, responsive charts and graphs |
| **WebSocket API** | Real-time bidirectional communication |

### Desktop Application

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Tauri** | v2 | Cross-platform desktop framework |
| **TypeScript** | ~5.6.2 | Type-safe desktop app development |
| **Vite** | ^6.0.3 | Fast build tool and dev server |
| **Rust** | Latest | Backend runtime for Tauri |

### Development Tools

- **Git** - Version control
- **PyInstaller** - Python application bundling (desktop version)
- **Virtual Environment** - Isolated Python dependencies

### System Requirements

| Component | Requirement |
|-----------|-------------|
| **Python** | 3.10 or higher |
| **Operating System** | Windows, macOS, Linux |
| **Browser** | Modern browser with WebSocket support (Chrome, Firefox, Safari, Edge) |
| **RAM** | Minimum 2GB (4GB+ recommended) |
| **Disk Space** | 100MB for application + database growth |
| **Network** | Required for network quality monitoring |

---

## 📊 Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         DevWatchMan                              │
│                    System Monitor Platform                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│   Web Dashboard      │◄───────►│  Desktop App (Tauri) │
│   (Browser-based)    │  HTTP   │  (Cross-platform)    │
└──────────┬───────────┘         └──────────┬───────────┘
           │                                 │
           │ WebSocket / REST API            │
           │                                 │
┌──────────▼─────────────────────────────────▼───────────┐
│              FastAPI Backend Server                     │
│  ┌─────────────────────────────────────────────────┐  │
│  │           API Routes Layer                       │  │
│  │  /api/health  /api/summary  /api/history        │  │
│  │  /api/ports   /api/alerts   /api/docker         │  │
│  │  /ws/live (WebSocket)                           │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │         Core Services Layer                      │  │
│  │  • Snapshot Scheduler (3s interval)             │  │
│  │  • WebSocket Manager                            │  │
│  │  • Alert State Manager                          │  │
│  │  • Profile State Manager                        │  │
│  │  • Retention Service                            │  │
│  │  • Docker Monitor                               │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │         Data Collectors Layer                    │  │
│  │  • CPU Collector      • Network Collector       │  │
│  │  • Memory Collector   • Port Scanner            │  │
│  │  • Disk Collector     • Process Monitor         │  │
│  │  • Network Quality    • Docker Collector        │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │         Storage Layer                            │  │
│  │  • SQLite Database                              │  │
│  │    - snapshots table (metrics history)          │  │
│  │    - alerts table (alert history)               │  │
│  │    - events table (timeline events)             │  │
│  │    - app_state table (configuration)            │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │      System Resources          │
         │  • psutil (CPU, RAM, Disk)    │
         │  • Network Interfaces          │
         │  • Running Processes           │
         │  • Docker Daemon               │
         └───────────────────────────────┘
```

### Data Flow Diagram

```
┌────────────────────────────────────────────────────────────┐
│                    Data Collection Flow                     │
└────────────────────────────────────────────────────────────┘

┌──────────────┐     Every 3 seconds     ┌──────────────┐
│   Snapshot   │────────────────────────►│   System     │
│   Scheduler  │                         │  Collectors  │
└──────────────┘                         └──────┬───────┘
                                                │
                                                ▼
                                    ┌───────────────────┐
                                    │  Collect Metrics  │
                                    │  • CPU %          │
                                    │  • Memory %       │
                                    │  • Disk %         │
                                    │  • Network I/O    │
                                    └─────────┬─────────┘
                                              │
                                              ▼
                                    ┌───────────────────┐
                                    │  Alert Engine     │
                                    │  • Check CPU      │
                                    │  • Check RAM      │
                                    │  • Check Ports    │
                                    │  • Check Network  │
                                    └─────────┬─────────┘
                                              │
                                              ▼
                                    ┌───────────────────┐
                                    │  Store in SQLite  │
                                    │  • snapshots      │
                                    │  • alerts         │
                                    │  • events         │
                                    └─────────┬─────────┘
                                              │
                                              ▼
                                    ┌───────────────────┐
                                    │ Broadcast via WS  │
                                    │ to all clients    │
                                    └───────────────────┘
```

### WebSocket Communication

```
┌──────────────┐                           ┌──────────────┐
│   Client     │                           │   Server     │
│  (Browser)   │                           │  (FastAPI)   │
└──────┬───────┘                           └──────┬───────┘
       │                                          │
       │  1. Connect:  ws://host/ws/live          │
       │─────────────────────────────────────────►│
       │                                          │
       │  2. Connection Established               │
       │◄─────────────────────────────────────────│
       │                                          │
       │  3. Snapshot Update (every 3s)           │
       │◄─────────────────────────────────────────│
       │  {                                       │
       │    "type": "snapshot",                   │
       │    "v": 1,                               │
       │    "data": {                             │
       │      "cpu_percent": 45. 2,                │
       │      "mem_percent": 62.8,                │
       │      ...                                  │
       │    }                                     │
       │  }                                       │
       │                                          │
       │  4. Alert Update                         │
       │◄─────────────────────────────────────────│
       │  {                                       │
       │    "type": "timeline_event",             │
       │    "v":  1,                               │
       │    "data": {... }                         │
       │  }                                       │
       │                                          │
       │  5. Heartbeat / Keep-alive               │
       │◄────────────────────────────────────────►│
       │                                          │
```

---

## 🚀 Installation

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10 or higher** ([Download](https://www.python.org/downloads/))
- **pip** (Python package installer - usually comes with Python)
- **Git** ([Download](https://git-scm.com/downloads))
- **Virtual environment** (recommended for isolation)

### Step 1: Clone the Repository

```bash
git clone https://github.com/Sakilalakmal/DevWatchMan.git
cd DevWatchMan
```

### Step 2: Create Virtual Environment (Recommended)

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install all required Python packages
pip install -r requirements. txt
```

**Required Python packages:**
```
fastapi          # Modern web framework
uvicorn          # ASGI server
psutil           # System and process utilities
pydantic         # Data validation
jinja2           # Template engine
python-multipart # For form data handling
docker           # Docker container monitoring
```

Alternatively, install packages individually:
```bash
pip install fastapi uvicorn psutil pydantic jinja2 python-multipart docker
```

### Step 4: Verify Installation

```bash
python -c "import fastapi, uvicorn, psutil; print('All dependencies installed successfully!')"
```

---

## 🎯 Quick Start

### Running the Web Application

#### Development Mode (with auto-reload)
```bash
# Navigate to the application directory
cd devwatchman

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode
```bash
# Navigate to the application directory
cd devwatchman

# Start with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Accessing the Dashboard

Once the server is running, access the application: 

- **Main Dashboard**: http://localhost:8000
- **API Documentation (Swagger UI)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc

### Running the Desktop Application

#### Prerequisites for Desktop App
```bash
# Install Node.js dependencies
cd devwatchman-desktop
npm install

# Install Rust (required for Tauri)
# Visit:  https://www.rust-lang.org/tools/install
```

#### Development Mode
```bash
cd devwatchman-desktop
npm run tauri dev
```

#### Build Desktop App
```bash
cd devwatchman-desktop
npm run tauri build
```

---

## 📖 Usage

### Starting the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Custom port
uvicorn app.main:app --port 8001

# With SSL (HTTPS)
uvicorn app.main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

### Monitoring Your System

1. **Dashboard** - Navigate to `http://localhost:8000` for the main monitoring interface
2. **Real-time Updates** - The dashboard automatically connects via WebSocket for live data
3. **Historical View** - Charts display configurable time ranges (1-720 hours)
4. **Alerts** - Check the alerts panel for system warnings and critical notifications
5. **Docker Monitoring** - View container status and resource usage in the Docker panel
6. **Profile Switching** - Select different monitoring profiles for various environments

### Monitoring Profiles

DevWatchMan supports multiple monitoring profiles: 

- **default** - General system monitoring (ports:  3000, 5173, 8000, 1433, 5672, 15672)
- **frontend-dev** - Frontend development (ports: 3000, 5173, 8000)
- **microservices** - Microservices environment (custom port configuration)

Switch profiles via the dashboard or API:
```bash
curl -X POST "http://localhost:8000/api/profiles/select? name=frontend-dev"
```

---

## 🔌 API Endpoints

### Health Check
```http
GET /api/health
```

Returns the API health status. 

**Response:**
```json
{
  "ok": true,
  "data": {"status": "ok"},
  "meta": {}
}
```

---

### Latest System Snapshot
```http
GET /api/summary
```

Returns the most recent system metrics. 

**Response:**
```json
{
  "ok": true,
  "data": {
    "id": 1234,
    "ts_utc": "2026-01-15T15:30:00.000Z",
    "cpu_percent": 45.2,
    "mem_percent": 62.8,
    "mem_used_bytes": 8589934592,
    "mem_total_bytes": 17179869184,
    "disk_percent": 55.3,
    "disk_used_bytes": 268435456000,
    "disk_total_bytes": 512000000000,
    "net_sent_bps": 1048576.5,
    "net_recv_bps": 2097152.8
  },
  "meta": {}
}
```

---

### Historical Data
```http
GET /api/history? hours=24
```

Returns historical snapshots for time-series analysis.

**Query Parameters:**
- `hours` (optional): Number of hours to retrieve (1-720, default: 24)

**Response:**
```json
{
  "ok": true,
  "data": {
    "snapshots": [
      {
        "id": 1,
        "ts_utc": "2026-01-15T15:00:00.000Z",
        "cpu_percent": 42.1,
        "mem_percent":  60.5,
        ... 
      }
    ]
  },
  "meta": {"hours": 24, "count": 288}
}
```

---

### Port Status
```http
GET /api/ports
```

Returns the status of monitored ports.

**Response:**
```json
{
  "ok": true,
  "data":  [
    {
      "port":  3000,
      "listening": true,
      "pid": 1234,
      "process_name": "node"
    },
    {
      "port": 8000,
      "listening": true,
      "pid": 5678,
      "process_name":  "python"
    }
  ],
  "meta": {"watch_ports": [3000, 5173, 8000, 1433, 5672, 15672]}
}
```

---

### All Listening Ports
```http
GET /api/ports/listening? limit=500
```

Returns all ports currently listening on the system.

**Query Parameters:**
- `limit` (optional): Maximum number of ports to return (1-2000, default: 500)

---

### Network Quality
```http
GET /api/network
```

Returns network latency and quality status.

**Response:**
```json
{
  "ok": true,
  "data": {
    "host": "1.1.1.1",
    "timeout_ms": 800,
    "latency_ms": 45. 2,
    "status": "good"
  },
  "meta":  {}
}
```

**Status Values:**
- `excellent` - Latency < 30ms
- `good` - Latency 30-100ms
- `fair` - Latency 100-200ms
- `poor` - Latency > 200ms
- `offline` - No connectivity

---

### Alerts
```http
GET /api/alerts? limit=50&include_ack=false
```

Returns recent system alerts.

**Query Parameters:**
- `limit` (optional): Number of alerts to retrieve (1-200, default: 50)
- `include_ack` (optional): Include acknowledged alerts (default: false)

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "id": 1,
      "ts_utc": "2026-01-15T15:30:00.000Z",
      "severity": "warning",
      "message": "CPU usage high:  87. 3%",
      "acknowledged": false
    }
  ],
  "meta": {"limit":  50}
}
```

---

### Acknowledge Alert
```http
POST /api/alerts/{alert_id}/ack
```

Acknowledges a specific alert. 

---

### Mute Alerts
```http
POST /api/alerts/mute? minutes=30
```

Mutes all alerts for a specified duration.

**Query Parameters:**
- `minutes` (required): Duration to mute (0-1440 minutes)

---

### Timeline Events
```http
GET /api/timeline? hours=24&limit=200
```

Returns system events and alert history.

**Query Parameters:**
- `hours` (optional): Time range in hours (1-168, default: 24)
- `limit` (optional): Maximum events to return (1-500, default: 200)

---

### Top Processes
```http
GET /api/processes
```

Returns top processes by CPU and memory usage.

**Response:**
```json
{
  "ok": true,
  "data":  {
    "by_cpu": [
      {"pid": 1234, "name": "chrome", "cpu_percent": 15.2, "mem_percent": 5.3}
    ],
    "by_mem": [
      {"pid": 5678, "name": "node", "cpu_percent": 2.1, "mem_percent":  12.8}
    ]
  },
  "meta": {}
}
```

---

### Docker Status
```http
GET /api/docker/status
```

Returns Docker daemon availability status.

---

### Docker Containers
```http
GET /api/docker/containers? include_stopped=true&limit=50
```

Returns Docker container information with resource usage.

**Query Parameters:**
- `include_stopped` (optional): Include stopped containers (default: true)
- `limit` (optional): Maximum containers to return (1-200, default: 50)

---

### Monitoring Profiles
```http
GET /api/profiles
```

Returns available monitoring profiles and the active profile.

---

### Select Profile
```http
POST /api/profiles/select? name=frontend-dev
```

Switches to a different monitoring profile.

**Query Parameters:**
- `name` (required): Profile name to activate

---

### WebSocket Endpoint
```http
WS /ws/live
```

Real-time system updates via WebSocket connection.

**Message Format:**
```json
{
  "type": "snapshot",
  "v": 1,
  "data": {
    "cpu_percent": 45.2,
    "mem_percent": 62.8,
    "disk_percent": 55.3,
    "net_sent_bps":  1048576.5,
    "net_recv_bps": 2097152.8
  }
}
```

**Message Types:**
- `snapshot` - System metrics update
- `timeline_event` - New alert or event
- `alert` - Critical alert notification

---

## ⚙️ Configuration

All configuration settings are located in `devwatchman/app/core/config.py`

### Key Settings

```python
# Application Settings
APP_NAME:  str = "DevWatchMan"
DB_PATH: Path = Path(__file__).resolve().parents[2] / "devwatchman. db"

# Monitoring Intervals
SNAPSHOT_INTERVAL_SECONDS: int = 3  # Data collection frequency
HISTORY_DEFAULT_HOURS: int = 24     # Default history timeframe

# Port Monitoring
WATCH_PORTS:  list[int] = [3000, 5173, 8000, 1433, 5672, 15672]

# Alert Thresholds
ALERT_CPU_PERCENT: int = 85         # CPU usage alert threshold
ALERT_RAM_PERCENT: int = 90         # Memory usage alert threshold
ALERT_PORTS_REQUIRED: list[int] = [3000, 1433, 5672]  # Critical ports
ALERT_COOLDOWN_SECONDS: int = 60    # Minimum time between alerts

# Alert Duration Thresholds
ALERT_CPU_DURATION_SECONDS: int = 30    # CPU must be high for 30s
ALERT_RAM_DURATION_SECONDS:  int = 30    # RAM must be high for 30s
ALERT_NET_OFFLINE_SECONDS: int = 10     # Network offline threshold

# Flapping Detection
FLAP_THRESHOLD:  int = 6              # Number of state changes
FLAP_WINDOW_SECONDS: int = 120       # Time window for flap detection

# Network Monitoring
NETWORK_PING_HOST: str = "1.1.1.1"  # Ping target for network quality
NETWORK_PING_TIMEOUT_MS: int = 800  # Ping timeout in milliseconds
```

### Customizing Monitored Ports

Edit the `WATCH_PORTS` list in `config.py` to monitor your specific ports:

```python
WATCH_PORTS = [3000, 5000, 8080, 9000]  # Your custom ports
```

### Adjusting Alert Thresholds

Modify alert sensitivity: 

```python
ALERT_CPU_PERCENT = 70   # Alert when CPU > 70%
ALERT_RAM_PERCENT = 85   # Alert when RAM > 85%
```

### Changing Snapshot Interval

Adjust data collection frequency:

```python
SNAPSHOT_INTERVAL_SECONDS = 5  # Collect every 5 seconds (default:  3)
```

---

## 📁 Project Structure

```
DevWatchMan/
├── devwatchman/                      # Main web application
│   ��── app/
│   │   ├── main.py                   # FastAPI application entry point
│   │   ├── api/
│   │   │   ├── routes.py             # API endpoint definitions
│   │   │   └── schemas.py            # Pydantic models
│   │   ├── collectors/
│   │   │   ├── cpu.py                # CPU metrics collector
│   │   │   ├── disk.py               # Disk metrics collector
│   │   │   ├── memory.py             # Memory metrics collector
│   │   │   ├── network.py            # Network metrics collector
│   │   │   ├── network_quality.py    # Network ping/latency
│   │   │   ├── ports.py              # Port status checker
│   │   │   ├── listening_ports.py    # All listening ports scanner
│   │   │   └── processes.py          # Process monitoring
│   │   ├── core/
│   │   │   ├── config.py             # Application configuration
│   │   │   ├── logging.py            # Logging setup
│   │   │   └── profiles.py           # Monitoring profile management
│   │   ├── services/
│   │   │   ├── scheduler.py          # Background snapshot scheduler
│   │   │   ├── ws_manager.py         # WebSocket connection manager
│   │   │   ├── alert_state.py        # Alert state management
│   │   │   ├── profile_state.py      # Profile state management
│   │   │   ├── retention.py          # Data retention service
│   │   │   └── docker_monitor.py     # Docker container monitoring
│   │   ├── storage/
│   │   │   ├── db.py                 # Database initialization
│   │   │   ├── snapshots.py          # Snapshot data operations
│   │   │   ├── alerts.py             # Alert storage operations
│   │   │   └── events.py             # Event timeline storage
│   │   └── web/
│   │       ├── static/
│   │       │   ├── app.js            # Frontend JavaScript
│   │       │   └── app.css           # Custom styles
│   │       └── templates/
│   │           └── dashboard.html    # Main dashboard template
│   └── devwatchman.db                # SQLite database (auto-created)
│
├── devwatchman-desktop/              # Desktop application (Tauri)
│   ├── backend/
│   │   ├── devwatchman/              # Same as web app backend
│   │   ├── run_devwatchman.py        # Desktop backend launcher
│   │   └── requirements.txt          # Python dependencies
│   ├── src/
│   │   ├── main.ts                   # Tauri frontend entry
│   │   └── styles.css                # Desktop app styles
│   ├── src-tauri/                    # Rust/Tauri configuration
│   │   ├── src/
│   │   │   └── main.rs               # Rust main file
│   │   ├── Cargo.toml                # Rust dependencies
│   │   └── tauri.conf. json           # Tauri configuration
│   ├── index.html                    # Desktop app HTML
│   ├── package.json                  # Node.js dependencies
│   └── vite.config.ts                # Vite configuration
│
├── requirements.txt                  # Python dependencies (web app)
├── .gitignore                        # Git ignore rules
└── README.md                         # This file
```

---

## 🎯 Use Cases

### Development Environment Monitoring
- Track resource usage during development
- Monitor development server ports (3000, 5173, 8000)
- Detect memory leaks in development
- Network quality monitoring for remote development

### Server Performance
- Monitor production server health
- Track system resource utilization
- Historical performance analysis
- Alert on critical resource thresholds

### Network Diagnostics
- Identify network quality issues
- Monitor latency to external services
- Detect connectivity problems
- Track network bandwidth usage

### Port Management
- Ensure critical services are running
- Monitor development tools (Vite, Node, Python servers)
- Track database ports (SQL Server, RabbitMQ)
- Detect port conflicts

### Docker Container Monitoring
- Real-time container status
- Resource usage per container
- Container health checks
- Multi-container application monitoring

### Resource Optimization
- Identify resource bottlenecks
- Track process-level resource usage
- Historical trend analysis
- Capacity planning

### System Alerts
- Get notified of critical system events
- CPU/RAM threshold violations
- Port availability monitoring
- Network connectivity issues

---

## 📊 Performance

| Metric | Value | Notes |
|--------|-------|-------|
| **Snapshot Interval** | 3 seconds | Configurable in config.py |
| **Database** | SQLite | Lightweight with optimized queries |
| **Memory Footprint** | < 50MB | Typical usage in production |
| **WebSocket** | Binary protocol | Efficient bidirectional communication |
| **API Response Time** | < 50ms | Average for most endpoints |
| **Historical Data Retention** | Configurable | Default: automatic cleanup of old data |
| **Concurrent WebSocket Connections** | Unlimited | Limited by system resources |
| **Database Size** | ~1MB/day | Depends on snapshot interval and retention |

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Change the port in the uvicorn command
uvicorn app.main:app --port 8001

# Or find and kill the process using the port (Linux/macOS)
lsof -ti: 8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Database Issues

The database is automatically created on first run. If you encounter issues:

```bash
# Delete the database file to reset
rm devwatchman/devwatchman.db

# The database will be recreated on next startup
```

### Permission Errors (Linux/macOS)

Some metrics may require elevated privileges:

```bash
# Run with sudo (not recommended for production)
sudo uvicorn app.main:app --host 0.0.0.0 --port 8000

# Better: adjust file permissions
chmod 644 devwatchman/devwatchman.db
```

### WebSocket Connection Issues

- Check firewall settings
- Ensure no proxy is blocking WebSocket connections
- Verify the server is running and accessible
- Check browser console for WebSocket errors

### Docker Monitoring Not Working

```bash
# Ensure Docker daemon is running
docker ps

# Check Docker socket permissions
ls -la /var/run/docker.sock

# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker
```

### High CPU Usage

```bash
# Increase snapshot interval to reduce CPU load
# Edit config.py:
SNAPSHOT_INTERVAL_SECONDS = 5  # or higher
```

### ImportError: No module named 'app'

```bash
# Ensure you're in the correct directory
cd devwatchman

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r ../requirements.txt
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### How to Contribute

1. **Fork the repository**
   ```bash
   # Click the "Fork" button on GitHub
   ```

2. **Create your feature branch**
   ```bash
   git checkout -b feature/AmazingFeature
   ```

3. **Commit your changes**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```

4. **Push to the branch**
   ```bash
   git push origin feature/AmazingFeature
   ```

5. **Open a Pull Request**
   - Go to your fork on GitHub
   - Click "Pull Request"
   - Describe your changes

### Development Guidelines

- Follow PEP 8 style guide for Python code
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed
- Ensure code passes all existing tests

### Code Style

```bash
# Format code with black
pip install black
black devwatchman/

# Lint with flake8
pip install flake8
flake8 devwatchman/

# Type checking with mypy
pip install mypy
mypy devwatchman/
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

```
MIT License

Copyright (c) 2026 Sakila Lakmal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
```

---

## 👤 Author

**Sakila Lakmal**

- GitHub: [@Sakilalakmal](https://github.com/Sakilalakmal)
- Project Link: [https://github.com/Sakilalakmal/DevWatchMan](https://github.com/Sakilalakmal/DevWatchMan)

---

## 🙏 Acknowledgments

Special thanks to the following open-source projects and communities:

- **[FastAPI](https://fastapi.tiangolo.com/)** - For the excellent web framework and documentation
- **[psutil](https://github.com/giampaolo/psutil)** - For comprehensive cross-platform system monitoring
- **[Chart.js](https://www.chartjs.org/)** - For beautiful and responsive data visualizations
- **[TailwindCSS](https://tailwindcss.com/)** - For rapid and modern UI development
- **[Uvicorn](https://www.uvicorn.org/)** - For the lightning-fast ASGI server
- **[SQLite](https://www.sqlite.org/)** - For the reliable embedded database
- **[Tauri](https://tauri.app/)** - For cross-platform desktop application framework
- **[Docker](https://www.docker.com/)** - For container monitoring capabilities

---

## 🗺️ Roadmap

Future features and improvements planned:

- [ ] **Email Notifications** - Send alerts via email
- [ ] **Slack/Discord Integration** - Push notifications to team channels
- [ ] **Multi-system Monitoring** - Monitor multiple servers from one dashboard
- [ ] **Custom Metrics** - User-defined custom collectors
- [ ] **Performance Predictions** - ML-based resource usage forecasting
- [ ] **Mobile App** - Native iOS/Android applications
- [ ] **Kubernetes Integration** - Monitor K8s pods and nodes
- [ ] **Advanced Alerting Rules** - Complex alert conditions and correlations
- [ ] **Data Export** - Export metrics to CSV/JSON
- [ ] **API Authentication** - Secure API with JWT tokens
- [ ] **User Management** - Multi-user support with roles
- [ ] **Plugins System** - Extensible plugin architecture
- [ ] **Grafana Integration** - Export metrics to Grafana

---

## 📚 Additional Resources

### Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [psutil Documentation](https://psutil.readthedocs.io/)
- [Chart.js Documentation](https://www.chartjs.org/docs/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Tauri Documentation](https://tauri.app/v2/)

### Tutorials

- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [WebSocket Tutorial](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_client_applications)
- [Docker Monitoring Best Practices](https://docs.docker.com/config/containers/runmetrics/)

### Related Projects

- [Netdata](https://github.com/netdata/netdata) - Real-time performance monitoring
- [Glances](https://github.com/nicolargo/glances) - Cross-platform monitoring tool
- [Prometheus](https://prometheus.io/) - Time-series monitoring
- [Grafana](https://grafana.com/) - Metrics visualization

---

## 💬 Support

If you encounter any issues or have questions: 

1. **Check the [Troubleshooting](#-troubleshooting) section**
2. **Search [existing issues](https://github.com/Sakilalakmal/DevWatchMan/issues)**
3. **Create a [new issue](https://github.com/Sakilalakmal/DevWatchMan/issues/new)** with: 
   - Clear description of the problem
   - Steps to reproduce
   - System information (OS, Python version, etc.)
   - Error messages and logs

---

## ⚡ Quick Links

- [Installation Guide](#-installation)
- [API Documentation](#-api-endpoints)
- [Configuration](#%EF%B8%8F-configuration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

<div align="center">

### ⭐ Star this repository if you find it helpful!

**Made with ❤️ by [Sakila Lakmal](https://github.com/Sakilalakmal)**

[![GitHub stars](https://img.shields.io/github/stars/Sakilalakmal/DevWatchMan?style=social)](https://github.com/Sakilalakmal/DevWatchMan/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Sakilalakmal/DevWatchMan?style=social)](https://github.com/Sakilalakmal/DevWatchMan/network/members)
[![GitHub watchers](https://img.shields.io/github/watchers/Sakilalakmal/DevWatchMan?style=social)](https://github.com/Sakilalakmal/DevWatchMan/watchers)

</div>
