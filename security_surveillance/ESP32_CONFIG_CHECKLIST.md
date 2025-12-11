# ESP32 Hardware Configuration Checklist

## 📋 Before Deployment - Configuration Steps

### 1. Raspberry Pi Configuration

**Edit `config/config.yaml`:**

```bash
nano config/config.yaml
```

**Update these values:**

```yaml
agriculture:
  esp32:
    wifi_ssid: "YOUR_WIFI_NETWORK"      # ← Change this
    wifi_password: "YOUR_WIFI_PASSWORD"  # ← Change this
```

**Get your Raspberry Pi IP address:**
```bash
hostname -I
# Example output: 192.168.1.100
```

**Note this IP - you'll need it for ESP32!**

---

### 2. ESP32 Arduino Code Configuration

**Edit `esp32_sensors/esp32_agriculture_sensors.ino`:**

Update lines 26-28:
```cpp
const char* ssid = "YOUR_WIFI_SSID";           // ← Same as config.yaml
const char* password = "YOUR_WIFI_PASSWORD";   // ← Same as config.yaml
const char* mqtt_server = "192.168.1.100";     // ← Your Pi's IP from step 1
```

---

### 3. Hardware Wiring Verification

**Verify these connections match config.yaml:**

| Component | ESP32 Pin | Config Value |
|-----------|-----------|--------------|
| Soil Moisture Sensor | GPIO 34 | `agriculture.esp32.pins.soil_moisture: 34` |
| DHT11 Data | GPIO 4 | `agriculture.esp32.pins.dht11_data: 4` |
| LDR Sensor | GPIO 35 | `agriculture.esp32.pins.ldr_sensor: 35` |
| Relay (Pump) | GPIO 26 | `agriculture.esp32.pins.relay_pump: 26` |

**Power connections:**
- ESP32 VIN → 5V power
- ESP32 GND → Ground
- All sensors VCC → 3.3V
- All sensors GND → Ground
- Relay VCC → 5V (ESP32 VIN)
- Relay GND → Ground

---

### 4. Sensor Calibration

**Soil Moisture Calibration:**

1. **Dry calibration:**
   ```bash
   # On ESP32 Serial Monitor (115200 baud):
   # Remove sensor from soil - let it dry completely
   # Note the analog reading (e.g., 3200)
   ```

2. **Wet calibration:**
   ```bash
   # Place sensor in saturated soil/water
   # Note the analog reading (e.g., 1200)
   ```

3. **Update values in BOTH places:**
   
   **config.yaml:**
   ```yaml
   agriculture:
     esp32:
       calibration:
         soil_moisture:
           dry_value: 3200  # ← Your dry reading
           wet_value: 1200  # ← Your wet reading
   ```
   
   **ESP32 code (lines 47-48):**
   ```cpp
   const int SOIL_DRY_VALUE = 3200;  // ← Your dry reading
   const int SOIL_WET_VALUE = 1200;  // ← Your wet reading
   ```

---

### 5. Irrigation Settings

**Review and adjust if needed in `config.yaml`:**

```yaml
agriculture:
  irrigation:
    auto_rules:
      critical_trigger:
        moisture_below: 20  # % - Emergency irrigation
        duration: 60        # seconds
      
      daytime_trigger:
        moisture_below: 30  # % - Regular irrigation  
        duration: 30        # seconds
        light_above: 200    # lux (daytime detection)
```

**Safety limits:**
```yaml
    safety:
      max_daily_runtime: 1800   # 30 minutes max per day
      min_interval: 600         # 10 minutes between irrigations
      pump_timeout: 300         # 5 minutes max continuous run
```

---

### 6. MQTT Topics Verification

**Ensure these match in ALL locations:**

| Purpose | Topic | Config Path |
|---------|-------|-------------|
| Sensor Data | `agriculture/sensors/data` | `agriculture.mqtt.topics.sensor_data` |
| Pump Control | `agriculture/control/pump` | `agriculture.mqtt.topics.pump_control` |

**ESP32 code (lines 30-31):**
```cpp
const char* mqtt_topic_sensors = "agriculture/sensors/data";
const char* mqtt_topic_control = "agriculture/control/pump";
```

---

## ✅ Pre-Deployment Verification

Run this checklist before powering on:

- [ ] WiFi SSID/password updated in **both** config.yaml and ESP32 code
- [ ] Raspberry Pi IP address updated in ESP32 code
- [ ] All sensor pins wired correctly (match config.yaml)
- [ ] Relay connected to GPIO 26
- [ ] Pump power supply connected (12V, 2A minimum)
- [ ] Soil moisture sensor calibrated
- [ ] MQTT broker installed: `sudo systemctl status mosquitto`
- [ ] Python dependencies installed: `pip install paho-mqtt`
- [ ] Config file validated: `python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"`

---

## 🚀 Deployment Steps

### On Raspberry Pi:

```bash
# 1. Start MQTT broker
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# 2. Test MQTT subscription (separate terminal)
mosquitto_sub -t "agriculture/sensors/data" -v

# 3. Start MQTT client
cd ~/EdgeAI-IoT/security_surveillance
source venv/bin/activate
python modules/mqtt_client.py
```

### On ESP32:

```bash
# 1. Open Arduino IDE
# 2. Load esp32_sensors/esp32_agriculture_sensors.ino
# 3. Verify WiFi/MQTT settings are correct
# 4. Upload to ESP32
# 5. Open Serial Monitor (115200 baud)
```

**Expected output:**
```
=== ESP32 Agriculture Sensors ===
Connecting to WiFi: YourNetwork
✓ WiFi connected!
IP Address: 192.168.1.150
Connecting to MQTT broker... ✓ Connected!
Subscribed to: agriculture/control/pump
--- Reading Sensors ---
Soil Moisture: 45.2%
Temperature: 24.5°C
Humidity: 62.8%
Light Level: 850 lux
Pump Status: OFF
✓ Data published to MQTT
```

---

## 🧪 System Testing

### Test 1: Sensor Reading
```bash
# On Raspberry Pi, you should see:
agriculture/sensors/data {
  "device_id": "ESP32_Agriculture_Sensors",
  "soil_moisture": 45.2,
  "temperature": 24.5,
  "humidity": 62.8,
  "light_intensity": 850,
  "pump_active": false
}
```

### Test 2: Manual Pump Control
```bash
# Start pump for 10 seconds
mosquitto_pub -t "agriculture/control/pump" \
  -m '{"action":"start","duration":10000}'

# Stop pump immediately
mosquitto_pub -t "agriculture/control/pump" \
  -m '{"action":"stop"}'
```

### Test 3: Auto-Irrigation
```
1. Remove soil moisture sensor from soil (simulates dry)
2. Expose LDR to light (simulates daytime)
3. ESP32 should auto-activate pump after next reading (30 sec)
4. Check ESP32 serial: "💧 AUTO-IRRIGATION: Soil moisture low"
5. Pump runs for 30 seconds then stops
```

### Test 4: Dashboard Integration
```bash
# Start dashboard
python launch_integrated.py

# Access: http://RASPBERRY_PI_IP:8000
# Click "Agriculture" tab
# Should see real-time sensor readings
```

---

## 🐛 Troubleshooting

### ESP32 won't connect to WiFi
- Check SSID/password are correct (case-sensitive)
- Verify 2.4GHz WiFi (ESP32 doesn't support 5GHz)
- Check WiFi signal strength
- Try WiFi hotspot from phone for testing

### MQTT connection fails
- Verify Mosquitto running: `sudo systemctl status mosquitto`
- Check firewall: `sudo ufw allow 1883`
- Ping Raspberry Pi from ESP32 network
- Verify IP address is correct

### Sensors read incorrect values
- **Soil Moisture:** Re-calibrate dry/wet values
- **DHT11:** Check wiring, add 10kΩ pull-up resistor to data line
- **LDR:** Adjust lux mapping in code (lines 200-203)
- Check 3.3V power supply voltage

### Pump doesn't activate
- Check relay LED lights up when commanded
- Verify relay gets 5V power (measure with multimeter)
- Test relay manually: `digitalWrite(RELAY_PIN, HIGH);` in setup()
- Check pump power supply (12V, 2A)
- Verify pump polarity

### Database not storing readings
- Check file permissions: `ls -la data/logs/`
- Verify MQTT client is running
- Check Python console for error messages
- Test database: `sqlite3 data/logs/agriculture.db ".tables"`

---

## 📝 Configuration Summary

**Files to configure:**
1. ✅ `config/config.yaml` - WiFi, IP, thresholds, irrigation rules
2. ✅ `esp32_sensors/esp32_agriculture_sensors.ino` - WiFi, MQTT server, calibration

**Values that MUST match:**
- WiFi SSID/password (config.yaml ↔ ESP32)
- MQTT topics (config.yaml ↔ ESP32)
- Pin assignments (config.yaml ↔ ESP32)
- Device ID (config.yaml ↔ ESP32)

**Values to calibrate:**
- Soil moisture dry/wet readings
- Temperature offset (if sensor is inaccurate)
- Light intensity mapping

**Ready to deploy when:**
- ✅ All configuration values updated
- ✅ Hardware wired and verified
- ✅ Sensors calibrated
- ✅ MQTT broker running
- ✅ Pre-deployment checklist complete
