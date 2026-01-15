# DevWatchMan

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![WebSocket](https://img.shields.io/badge/WebSocket-010101?style=for-the-badge&logo=socketdotio&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)

**A powerful real-time system monitoring tool with live dashboards and intelligent alerts**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [API Documentation](#-api-endpoints) • [Configuration](#-configuration)

</div>

---

## 📋 Overview

**DevWatchMan** is a comprehensive real-time system monitoring application built with FastAPI and modern web technologies. It provides live insights into your system's performance including CPU, memory, disk usage, network statistics, port monitoring, and intelligent alerting—all through a beautiful, responsive web dashboard.

### Key Highlights
- 🔄 **Real-time WebSocket updates** for instant metric visualization
- 📊 **Interactive charts** powered by Chart.js
- 🚨 **Smart alert system** with configurable thresholds
- 🌐 **Network quality monitoring** with latency tracking
- 🔌 **Port monitoring** for development services
- 💾 **SQLite database** for historical data storage
- ⚡ **FastAPI backend** for high-performance API endpoints
- 🎨 **Modern UI** built with TailwindCSS

---

## ✨ Features

### System Monitoring
- **CPU Usage**: Real-time CPU percentage tracking
- **Memory Monitoring**: RAM usage with detailed bytes-level information
- **Disk Usage**: Track disk space utilization across drives
- **Network Statistics**: Upload/download speeds in real-time

### Advanced Features
- **WebSocket Live Updates**: Get instant updates without page refresh
- **Historical Data**: View performance trends over time (up to 168 hours)
- **Port Status Monitoring**: Track ports 3000, 5173, 8000, 1433, 5672, 15672
- **Network Quality Checks**: Ping-based latency monitoring (default: 1.1.1.1)
- **Alert System**: 
  - CPU threshold alerts (default: 85%)
  - RAM threshold alerts (default: 90%)
  - Required port monitoring with cooldown (60 seconds)
  - Severity levels: critical, warning, info

### Dashboard Features
- Interactive time-series charts
- Live connection status indicator
- Alert feed with severity badges
- Port status table with process information
- Network quality indicators
- Responsive design for all devices

---

## 🚀 Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Step 1: Clone the Repository
```bash
git clone https://github.com/Sakilalakmal/DevWatchMan.git
cd DevWatchMan
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install fastapi uvicorn psutil pydantic jinja2 python-multipart
```

**Required Python packages:**
- `fastapi` - Modern web framework
- `uvicorn` - ASGI server
- `psutil` - System and process utilities
- `pydantic` - Data validation
- `jinja2` - Template engine
- `python-multipart` - For form data

### Step 4: Run the Application
```bash
# From the project root directory
cd devwatchman
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: Access the Dashboard
Open your browser and navigate to:
```
http://localhost:8000
```

For API documentation (Swagger UI):
```
http://localhost:8000/docs
```

---

## 📖 Usage

### Starting the Server
```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Monitoring Your System
1. **Dashboard**: Navigate to `http://localhost:8000` for the main monitoring interface
2. **Real-time Updates**: The dashboard automatically connects via WebSocket for live data
3. **Historical View**: Charts display the last hour of data by default
4. **Alerts**: Check the alerts panel for system warnings and critical notifications

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

### Historical Data
```http
GET /api/history?hours=24
```
Returns historical snapshots.

**Query Parameters:**
- `hours` (optional): Number of hours to retrieve (1-168, default: 24)

### Port Status
```http
GET /api/ports
```
Returns the status of monitored ports.

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "port": 3000,
      "listening": true,
      "pid": 1234,
      "process_name": "node"
    },
    {
      "port": 8000,
      "listening": true,
      "pid": 5678,
      "process_name": "python"
    }
  ],
  "meta": {"watch_ports": [3000, 5173, 8000, 1433, 5672, 15672]}
}
```

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
    "latency_ms": 45.2,
    "status": "good"
  },
  "meta": {}
}
```

### Alerts
```http
GET /api/alerts?limit=50
```
Returns recent system alerts.

**Query Parameters:**
- `limit` (optional): Number of alerts to retrieve (1-200, default: 50)

### WebSocket Endpoint
```http
WS /ws/live
```
Real-time system updates via WebSocket connection.

**Message Format:**
```json
{
  "type": "snapshot",
  "data": {
    "cpu_percent": 45.2,
    "mem_percent": 62.8,
    ...
  }
}
```

---

## ⚙️ Configuration

Configuration is managed in `devwatchman/app/core/config.py`:

### Key Settings

```python
# Application
APP_NAME = "DevWatchMan"
DB_PATH = Path(__file__).resolve().parents[2] / "devwatchman.db"

# Monitoring Intervals
SNAPSHOT_INTERVAL_SECONDS = 3  # Data collection frequency
HISTORY_DEFAULT_HOURS = 24     # Default history timeframe

# Port Monitoring
WATCH_PORTS = [3000, 5173, 8000, 1433, 5672, 15672]

# Alert Thresholds
ALERT_CPU_PERCENT = 85         # CPU usage alert threshold
ALERT_RAM_PERCENT = 90         # Memory usage alert threshold
ALERT_PORTS_REQUIRED = [3000, 1433, 5672]  # Critical ports
ALERT_COOLDOWN_SECONDS = 60    # Minimum time between alerts

# Network Monitoring
NETWORK_PING_HOST = "1.1.1.1"  # Ping target for network quality
NETWORK_PING_TIMEOUT_MS = 800  # Ping timeout
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

---

## 📁 Project Structure

```
DevWatchMan/
├── devwatchman/
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── api/
│   │   │   ├── routes.py          # API endpoint definitions
│   │   │   └── schemas.py         # Pydantic models
│   │   ├── collectors/
│   │   │   ├── cpu.py             # CPU metrics collector
│   │   │   ├── disk.py            # Disk metrics collector
│   │   │   ├── memory.py          # Memory metrics collector
│   │   │   ├── network.py         # Network metrics collector
│   │   │   ├── network_quality.py # Network ping/latency
│   │   │   └── ports.py           # Port status checker
│   │   ├── core/
│   │   │   ├── config.py          # Application configuration
│   │   │   └── logging.py         # Logging setup
│   │   ├── services/
│   │   │   ├── scheduler.py       # Background snapshot scheduler
│   │   │   └── ws_manager.py      # WebSocket connection manager
│   │   ├── storage/
│   │   │   ├── db.py              # Database initialization
│   │   │   ├── snapshots.py       # Snapshot data operations
│   │   │   └── alerts.py          # Alert storage operations
│   │   └── web/
│   │       ├── static/
│   │       │   ├── app.js         # Frontend JavaScript
│   │       │   └── app.css        # Custom styles
│   │       └── templates/
│   │           └── dashboard.html # Main dashboard template
│   └── devwatchman.db             # SQLite database (auto-created)
├── .gitignore
└── README.md
```

---

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern, high-performance web framework
- **Uvicorn**: Lightning-fast ASGI server
- **Pydantic**: Data validation using Python type annotations
- **psutil**: Cross-platform library for system monitoring
- **SQLite**: Lightweight embedded database

### Frontend
- **HTML5/CSS3**: Semantic markup and modern styling
- **JavaScript (Vanilla)**: No framework dependencies
- **TailwindCSS**: Utility-first CSS framework (via CDN)
- **Chart.js**: Beautiful, responsive charts
- **WebSocket API**: Real-time bidirectional communication
- **Jinja2**: Server-side template rendering

### System Requirements
- **Python**: 3.10+
- **Operating System**: Windows, macOS, Linux
- **Browser**: Modern browser with WebSocket support

---

## 🎯 Use Cases

- **Development Environment Monitoring**: Track resource usage during development
- **Server Performance**: Monitor production server health
- **Network Diagnostics**: Identify network quality issues
- **Port Management**: Ensure critical services are running
- **Resource Optimization**: Identify resource bottlenecks
- **System Alerts**: Get notified of critical system events

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Change the port in the uvicorn command
uvicorn app.main:app --port 8001
```

### Database Issues
The database is automatically created. If you encounter issues:
```bash
# Delete the database file to reset
rm devwatchman/devwatchman.db
```

### Permission Errors (Linux/macOS)
Some metrics may require elevated privileges:
```bash
sudo uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### WebSocket Connection Issues
- Check firewall settings
- Ensure no proxy is blocking WebSocket connections
- Verify the server is running and accessible

---

## 📊 Performance

- **Snapshot Interval**: 3 seconds (configurable)
- **Database**: Lightweight SQLite with optimized queries
- **Memory Footprint**: Minimal (typically < 50MB)
- **WebSocket**: Efficient binary protocol
- **API Response Time**: < 50ms average

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👤 Author

**Sakila Lakmal**
- GitHub: [@Sakilalakmal](https://github.com/Sakilalakmal)

---

## 🙏 Acknowledgments

- FastAPI framework for excellent documentation
- psutil library for comprehensive system metrics
- Chart.js for beautiful visualizations
- TailwindCSS for rapid UI development

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

Made with ❤️ by Sakila Lakmal

</div>
