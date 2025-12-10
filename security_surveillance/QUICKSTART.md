# 🚀 Quick Start Guide - EcoGuard

## Start Dashboard (Development/Testing)

```bash
cd security_surveillance
python -m uvicorn dashboard.app:app --host 0.0.0.0 --port 8080 --reload
```

Open: **http://localhost:8080**

## Start Complete System (Production)

```bash
cd security_surveillance
python launch_integrated.py
```

This starts:
- Surveillance system (camera, detection, recording)
- Web dashboard on port 8080
- Both systems communicate via shared state

## 📱 Dashboard Features

### Security Mode 🔒
- **Live Video**: MJPEG stream with quality control (low/medium/high)
- **Detection Stats**: Total detections, events, recordings count
- **Recent Detections**: Real-time list with confidence scores
- **Zone Activity**: Bar chart showing detections per zone
- **Video Recordings**: Browse, play, download MP4 files
- **People Count**: Current number of people detected

### Agriculture Mode 🌱
- **Sensor Readings**: Soil moisture, temperature, humidity, light
- **History Chart**: Line graph of sensor data over time (6-48 hours)
- **Irrigation Control**: Start/stop manual irrigation, auto mode
- **System Alerts**: Warnings for low moisture, high temp, etc.
- **Statistics**: Daily irrigation totals, sensor averages

### Mode Switching
Click **Security** or **Agriculture** buttons in header to switch dashboards.

## 🌐 API Quick Reference

### Security Endpoints

```bash
# Get overall stats
curl http://localhost:8080/api/security/stats

# Get recent detections
curl http://localhost:8080/api/security/detections?limit=10

# Get zone statistics (last 7 days)
curl http://localhost:8080/api/security/zones?days=7

# List recordings (newest first)
curl http://localhost:8080/api/security/recordings?sort=newest&limit=5

# Download specific recording
curl http://localhost:8080/api/security/recording/FILENAME.mp4 -o video.mp4

# Take snapshot
curl http://localhost:8080/api/security/snapshot -o snapshot.jpg

# Get system status
curl http://localhost:8080/api/security/system/status

# Get people count
curl http://localhost:8080/api/security/people/count
```

### Agriculture Endpoints

```bash
# Get all sensors
curl http://localhost:8080/api/agriculture/sensors

# Get specific sensor
curl http://localhost:8080/api/agriculture/sensor/soil_moisture

# Get sensor history (last 24 hours)
curl http://localhost:8080/api/agriculture/history?sensor=soil_moisture&hours=24

# Get irrigation status
curl http://localhost:8080/api/agriculture/irrigation/status

# Start irrigation (15 minutes)
curl -X POST "http://localhost:8080/api/agriculture/irrigation/control?action=start&duration=15"

# Stop irrigation
curl -X POST "http://localhost:8080/api/agriculture/irrigation/control?action=stop"

# Enable auto mode
curl -X POST "http://localhost:8080/api/agriculture/irrigation/control?action=auto"

# Get agriculture stats
curl http://localhost:8080/api/agriculture/stats?days=7

# Get alerts
curl http://localhost:8080/api/agriculture/alerts?limit=10

# Get system status
curl http://localhost:8080/api/agriculture/system/status
```

### WebSocket Connection

```javascript
// Connect to live updates
const ws = new WebSocket('ws://localhost:8080/ws/live');

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Received:', message.type, message.data);
};

// Send ping
ws.send(JSON.stringify({ type: 'ping' }));

// Request status
ws.send(JSON.stringify({ type: 'request_status' }));
```

## 📊 API Documentation

Interactive API docs available at:
- **Swagger UI**: http://localhost:8080/api/docs
- **ReDoc**: http://localhost:8080/api/redoc

## 🔧 Configuration

### Camera RTSP URL
Edit `config/config.yaml`:
```yaml
camera:
  source: "rtsp://IP_ADDRESS:554/1"
```

### Dashboard Port
Change port in `launch_integrated.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8080)
```

### Video Stream Quality
Change in browser or via URL parameter:
```
http://localhost:8080/api/security/stream?quality=low    # 320x240
http://localhost:8080/api/security/stream?quality=medium # 640x480 (default)
http://localhost:8080/api/security/stream?quality=high   # 1280x720
```

## 🐛 Troubleshooting

### Dashboard won't start
```bash
# Install dependencies
pip install fastapi uvicorn websockets aiofiles python-multipart

# Check port 8080 is available
netstat -tuln | grep 8080
```

### Camera not showing
- Verify RTSP URL in `config/config.yaml`
- Check camera is powered and connected
- Test RTSP URL with VLC: `vlc rtsp://IP:554/1`

### No detection data
- Start with `launch_integrated.py` (not standalone dashboard)
- Check database exists: `data/logs/events.db`
- Run a test detection first

### WebSocket disconnects
- Check browser console for errors
- Verify firewall allows WebSocket connections
- Dashboard auto-reconnects (max 5 attempts)

## 📦 File Locations

```
security_surveillance/
├── dashboard/
│   ├── app.py                    # Main FastAPI app
│   ├── routes/                   # API endpoints
│   ├── static/css/style.css      # Dashboard styling
│   ├── static/js/dashboard.js    # Dashboard logic
│   └── templates/index.html      # Main HTML
├── config/config.yaml            # System configuration
├── data/
│   ├── logs/events.db           # Detection events
│   ├── recordings/              # Video files
│   └── models/yolov8n.pt        # AI model
├── main.py                       # Surveillance system
└── launch_integrated.py          # Unified launcher
```

## 🚀 Raspberry Pi Deployment

### 1. Install Dependencies
```bash
sudo apt update
sudo apt install -y python3-opencv python3-pip
pip3 install -r requirements.txt
pip3 install fastapi uvicorn websockets aiofiles python-multipart
```

### 2. Configure Camera
Edit `config/config.yaml` with your camera RTSP URL

### 3. Test Dashboard
```bash
python3 -m uvicorn dashboard.app:app --host 0.0.0.0 --port 8080
```

### 4. Launch Full System
```bash
python3 launch_integrated.py
```

### 5. Access from Other Devices
```
http://RASPBERRY_PI_IP:8080
```

## 📱 Mobile Access

Dashboard is responsive and works on mobile devices. Simply access:
```
http://RASPBERRY_PI_IP:8080
```

from your phone's browser (must be on same network).

## 🔐 Security Notes

For production deployment:
1. Enable authentication (add middleware)
2. Use HTTPS (nginx reverse proxy)
3. Restrict CORS origins in `dashboard/app.py`
4. Add rate limiting for API endpoints
5. Change default ports

## 📚 More Information

- **Full Documentation**: See `dashboard/README.md`
- **API Reference**: http://localhost:8080/api/docs
- **GitHub**: https://github.com/Techdee1/EdgeAI-IoT

---

**Need help?** Check logs, API docs, or open an issue on GitHub.
