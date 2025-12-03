# Security & Surveillance System

**Edge AI-powered security system for Raspberry Pi 3**  
Offline person detection with zone monitoring, tamper detection, and behavioral learning.

---

## 🌟 Project Overview

An intelligent security system that runs entirely on the edge (Raspberry Pi 3) without requiring cloud connectivity or internet access. Designed for privacy-conscious applications in remote areas, homes, and small businesses.

### Core Capabilities
- 🎯 **Real-time Person Detection** - YOLOv8n optimized for Pi 3 (1-3 FPS)
- 🗺️ **Zone-Based Monitoring** - Multiple configurable detection zones with custom alerts
- 🧠 **Behavioral Learning** - Learns normal activity patterns, alerts on anomalies
- 🛡️ **Tamper Detection** - Detects camera covering or movement attempts
- 📹 **Event Recording** - Automatic clip saving with timestamps
- 🚫 **Privacy-First** - All processing local, no cloud/data upload
- ⚡ **Motion Pre-Filter** - Efficient CPU usage through motion-triggered detection

### Unique Features
1. **Context-Aware Intelligence** - Knows what's normal vs suspicious based on time/location
2. **Self-Protection** - Alerts if camera is tampered with
3. **Zero Connectivity** - Works completely offline in remote areas

---

## 📊 Development Progress

**Status:** 🟢 Active Development  
**Completion:** 3/30 core tasks (10%)

See [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for detailed progress tracking.

### ✅ Completed
- [x] Project structure and configuration
- [x] Software dependencies installed
- [x] Camera capture module (tested with simulation)

### 🚧 Current Focus
- [ ] YOLOv8n model download and preparation
- [ ] Person detection pipeline

### 📋 Upcoming
- Motion detection, zone system, alerts, recording, unique features

---

## 📁 Project Structure

```
security_surveillance/
├── modules/              # Core system modules
│   ├── camera.py         ✅ Camera capture (complete)
│   ├── detector.py       🔜 Person detection
│   ├── motion.py         🔜 Motion detection
│   ├── zones.py          🔜 Zone management
│   ├── alerts.py         🔜 Alert system
│   ├── recorder.py       🔜 Video recording
│   ├── tamper.py         🔜 Tamper detection
│   └── behavioral.py     🔜 Pattern learning
├── config/
│   └── config.yaml       ✅ System configuration
├── data/
│   ├── models/           📁 AI models storage
│   ├── recordings/       📁 Video clips
│   ├── logs/             📁 System logs
│   └── test_output/      ✅ Test frames
├── tests/                🧪 Test scripts
├── PROJECT_SUMMARY.md    📋 Progress tracking
├── requirements.txt      ✅ Dependencies
└── README.md             📖 This file
```

---

## 🚀 Quick Start

### Development Setup (Current)
```bash
# Install dependencies
pip install -r requirements.txt

# Test camera module (simulation)
python test_camera_sim.py

# View configuration
cat config/config.yaml
```

### Production Setup (When Ready)
```bash
# 1. Configure camera source in config.yaml
#    - For device camera: source: 0
#    - For IP camera: source: "rtsp://username:password@ip:port/stream"

# 2. Run the system
python main.py
```

---

## 💻 Hardware Requirements

### Minimum (Development)
- Any computer with Python 3.8+
- Works with simulated frames for testing

### Target Deployment
- **Raspberry Pi 3** (1GB RAM, Quad-core 1.2 GHz)
- **Camera:** Pi Camera Module v2, USB webcam, or WiFi IP camera
- **Optional:** LEDs (GPIO 17, 27), Buzzer (GPIO 22)
- **Storage:** 8GB+ microSD card
- **Power:** 5V 2.5A power supply

### Performance Expectations on Pi 3
- Person detection: 1-3 FPS @ 416x416
- Motion detection: 15-30 FPS
- RAM usage: 400-500 MB
- CPU usage: 60-80% during active detection

---

## ⚙️ Configuration

Edit `config/config.yaml` to customize:
- Camera source and resolution
- Detection sensitivity and zones
- Alert settings and GPIO pins
- Recording duration and storage limits
- Behavioral learning parameters

---

## 📖 Use Cases

1. **Remote Area Monitoring** - Farms, construction sites (no internet needed)
2. **Privacy-Conscious Security** - Home security without cloud cameras
3. **Elderly Monitoring** - Fall detection without invasive surveillance
4. **Small Business** - Affordable after-hours security
5. **Wildlife Monitoring** - Distinguish humans from animals

---

## 🛠️ Technical Stack

- **Language:** Python 3.8+
- **Computer Vision:** OpenCV
- **AI Framework:** PyTorch + Ultralytics YOLOv8
- **Model:** YOLOv8n (nano) - 6MB, optimized for edge
- **Database:** SQLite (event logging)
- **Config:** YAML

---

## 📚 Documentation

- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Detailed progress and technical decisions
- [config/config.yaml](config/config.yaml) - Full configuration options
- Individual module docstrings - In-code documentation

---

## 🤝 Development Notes

Currently building in GitHub Codespace with simulated data. The system is designed to work seamlessly when deployed to Raspberry Pi 3 with actual camera hardware.

**Camera Testing:**
- Dev environment: Using simulated frames
- Local VSCode: Can test with webcam
- Pi deployment: WiFi IP camera (RTSP) or Pi Camera Module

---

## 📝 License

Edge AI & IoT Hackathon Project - 2025

---

**For detailed progress tracking, see [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)**
