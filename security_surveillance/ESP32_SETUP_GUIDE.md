# ESP32 Smart Irrigation Integration Guide

## 🎯 Current Status
**NOT READY** - Requires hardware setup and integration

## 📋 What You Need

### Hardware ($80-100 total)
- ✅ Raspberry Pi 3 (you have)
- 🛒 ESP32-WROOM-32 Development Board ($8)
- 🛒 Capacitive Soil Moisture Sensor v1.2 ($5)
- 🛒 DHT11 Temperature & Humidity Sensor ($2)
- 🛒 LDR Photoresistor Module ($2)
- 🛒 5V Relay Module (1 Channel) ($3)
- 🛒 12V DC Water Pump ($15)
- 🛒 12V Power Supply (2A) ($10)
- 🛒 Silicone tubes, connectors ($10)
- 🛒 Breadboard & jumper wires ($10)

### Software
- Arduino IDE (for ESP32)
- MQTT Broker (Mosquitto)
- Python MQTT library (paho-mqtt)

## 🔧 Step-by-Step Setup

### Part 1: Raspberry Pi MQTT Broker Setup

```bash
# 1. Install Mosquitto MQTT Broker
sudo apt update
sudo apt install mosquitto mosquitto-clients -y

# 2. Enable and start service
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
sudo systemctl status mosquitto

# 3. Test broker
mosquitto_sub -t "test" -v &
mosquitto_pub -t "test" -m "Hello MQTT"

# 4. Install Python MQTT library
cd /path/to/EdgeAI-IoT/security_surveillance
source venv/bin/activate
pip install paho-mqtt

# 5. Find your Raspberry Pi IP address
hostname -I
# Note this IP - you'll need it for ESP32 configuration
```

### Part 2: ESP32 Hardware Wiring

#### Pin Connections

**Soil Moisture Sensor:**
- VCC → 3.3V (ESP32)
- GND → GND
- AOUT → GPIO 34 (Analog)

**DHT11 Sensor:**
- VCC → 3.3V
- GND → GND
- DATA → GPIO 4

**LDR Module:**
- VCC → 3.3V
- GND → GND
- DO → GPIO 35 (Analog)

**5V Relay Module:**
- VCC → VIN (5V from ESP32)
- GND → GND
- IN → GPIO 26

**Pump Connection:**
- Pump (+) → Relay COM
- Relay NO → 12V Power Supply (+)
- Pump (-) → 12V Power Supply (-)

#### Wiring Diagram
```
ESP32                                     12V Supply
                                              |
  GPIO 34 ← Soil Moisture                    |
  GPIO 4  ← DHT11                            |
  GPIO 35 ← LDR                              |
  GPIO 26 → Relay IN                         |
                  ↓                           |
              Relay Module                    |
                COM → NO                      |
                  ↓                           ↓
              Water Pump (+) ← ← ← ← ← ← ← (+)
              Water Pump (-) → → → → → → → (-)
```

### Part 3: ESP32 Programming

#### 1. Install Arduino IDE
```bash
# Download from https://www.arduino.cc/en/software
# Or install via snap:
sudo snap install arduino
```

#### 2. Configure Arduino IDE for ESP32
1. Open Arduino IDE
2. Go to **File → Preferences**
3. Add to "Additional Board Manager URLs":
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Go to **Tools → Board → Boards Manager**
5. Search for "ESP32" and install "ESP32 by Espressif Systems"

#### 3. Install Required Libraries
**Tools → Manage Libraries**, search and install:
- **PubSubClient** by Nick O'Leary (for MQTT)
- **DHT sensor library** by Adafruit
- **Adafruit Unified Sensor** (dependency)
- **ArduinoJson** by Benoit Blanchon

#### 4. Upload Code to ESP32

1. Open `esp32_sensors/esp32_agriculture_sensors.ino` in Arduino IDE

2. **Edit WiFi credentials** (lines 21-22):
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```

3. **Edit Raspberry Pi IP** (line 25):
   ```cpp
   const char* mqtt_server = "192.168.1.100";  // Your Pi's IP
   ```

4. **Select Board & Port:**
   - Tools → Board → ESP32 Dev Module
   - Tools → Port → (select your ESP32's port, e.g., /dev/ttyUSB0)

5. **Upload:**
   - Click Upload button (→)
   - Wait for "Done uploading"

6. **Monitor Serial Output:**
   - Tools → Serial Monitor (115200 baud)
   - You should see:
     ```
     === ESP32 Agriculture Sensors ===
     Connecting to WiFi...
     ✓ WiFi connected!
     IP Address: 192.168.1.150
     Connecting to MQTT broker... ✓ Connected!
     --- Reading Sensors ---
     Soil Moisture: 45.2%
     Temperature: 24.5°C
     Humidity: 62.8%
     Light Level: 850 lux
     ✓ Data published to MQTT
     ```

### Part 4: Calibrate Soil Moisture Sensor

```bash
# On Raspberry Pi, subscribe to sensor data
mosquitto_sub -t "agriculture/sensors/data" -v

# 1. Place sensor in completely DRY soil
# Note the raw analog value (e.g., 3200)
# Update SOIL_DRY_VALUE in ESP32 code

# 2. Place sensor in completely WET soil (saturated)
# Note the raw analog value (e.g., 1200)
# Update SOIL_WET_VALUE in ESP32 code

# 3. Re-upload code to ESP32
```

### Part 5: Integrate with Dashboard

The MQTT client module is ready. Now update the dashboard to use real data:

```bash
cd /path/to/EdgeAI-IoT/security_surveillance

# Test MQTT client standalone
python modules/mqtt_client.py

# You should see:
# 🌱 Agriculture MQTT Client initialized
# ✅ Agriculture database initialized
# 🔌 Connecting to MQTT broker at localhost:1883...
# ✅ Connected to MQTT broker successfully!
# 📡 Subscribed to topic: agriculture/sensors/data
#
# 📥 Received sensor data:
#    Soil Moisture: 45.2%
#    Temperature: 24.5°C
#    ...
```

## 🧪 Testing the System

### 1. Test Sensor Readings
```bash
# Subscribe to sensor topic
mosquitto_sub -t "agriculture/sensors/data" -v

# You should see JSON every 30 seconds:
# {
#   "device_id": "ESP32_Agriculture_Sensors",
#   "soil_moisture": 45.2,
#   "temperature": 24.5,
#   "humidity": 62.8,
#   "light_intensity": 850,
#   "pump_active": false
# }
```

### 2. Test Pump Control
```bash
# Start pump for 30 seconds
mosquitto_pub -t "agriculture/control/pump" -m '{"action":"start","duration":30000}'

# Stop pump immediately
mosquitto_pub -t "agriculture/control/pump" -m '{"action":"stop"}'

# Watch ESP32 serial monitor - you should see:
# 🚿 PUMP ACTIVATED
# Duration: 30 seconds
```

### 3. Test Auto-Irrigation

Simulate low soil moisture:
1. Remove soil moisture sensor from soil (reads as dry)
2. ESP32 should detect moisture < 30%
3. If light > 200 lux (daytime), pump automatically activates
4. Serial monitor shows: "💧 AUTO-IRRIGATION: Soil moisture low"

## 📊 Dashboard Integration

### Update agriculture.py routes

The `/api/agriculture/sensors` endpoint needs modification to use real MQTT data instead of placeholders. I've created the MQTT client - now you need to:

1. Initialize MQTT client in `launch_integrated.py`
2. Store reference in `app_state`
3. Update agriculture routes to read from `mqtt_client.get_current_readings()`

Would you like me to update these files now?

## 🐛 Troubleshooting

### ESP32 won't connect to WiFi
- Double-check SSID and password
- Ensure 2.4GHz WiFi (ESP32 doesn't support 5GHz)
- Check signal strength

### MQTT connection fails
- Verify Mosquitto is running: `sudo systemctl status mosquitto`
- Check firewall: `sudo ufw allow 1883`
- Verify IP address is correct
- Test with: `mosquitto_sub -t "test" -v`

### Sensor readings seem wrong
- **Soil Moisture:** Calibrate SOIL_DRY_VALUE and SOIL_WET_VALUE
- **DHT11:** Check wiring, try 10kΩ pull-up resistor on data line
- **LDR:** Adjust lux mapping in code

### Pump doesn't activate
- Check relay LED - should light up when active
- Verify relay is getting 5V power
- Test relay manually: `digitalWrite(RELAY_PIN, HIGH);`
- Check pump power supply (12V, 2A minimum)

### Database not storing data
- Check permissions: `ls -la data/logs/`
- Verify MQTT client is running
- Check Python console for errors

## 💰 Cost Breakdown

| Item | Cost | Link |
|------|------|------|
| ESP32 Dev Board | $8 | Amazon/AliExpress |
| Soil Moisture Sensor | $5 | Amazon |
| DHT11 Sensor | $2 | Amazon |
| LDR Module | $2 | Amazon |
| 5V Relay Module | $3 | Amazon |
| Water Pump 12V | $15 | Amazon |
| 12V Power Supply | $10 | Amazon |
| Tubes & Connectors | $10 | Hardware store |
| Wires & Breadboard | $10 | Amazon |
| **TOTAL** | **$65** | |

## 🚀 Next Steps

1. ✅ Purchase hardware components
2. ✅ Set up Raspberry Pi MQTT broker
3. ✅ Wire ESP32 sensors
4. ✅ Upload and test ESP32 code
5. ✅ Calibrate sensors
6. ⏳ Integrate MQTT client with dashboard
7. ⏳ Test full system end-to-end
8. ⏳ Deploy in actual garden/farm

## ⏱️ Estimated Time
- Hardware assembly: 2-3 hours
- Software setup: 1-2 hours
- Calibration & testing: 1 hour
- **Total: 4-6 hours**

---

**Need help with any step? Let me know!**
