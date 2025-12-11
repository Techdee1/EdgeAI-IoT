"""
MQTT Client for Agriculture Sensors
Receives data from ESP32 and integrates with dashboard
"""
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import sqlite3
import threading
import time
from modules.config_loader import Config


class AgricultureMQTTClient:
    """Handles MQTT communication with ESP32 sensors"""
    
    def __init__(self, config_path="config/config.yaml", db_path=None):
        """
        Initialize MQTT client
        
        Args:
            config_path: Path to configuration file
            db_path: Path to agriculture database (overrides config)
        """
        # Load configuration
        self.config = Config(config_path)
        
        # MQTT broker settings
        self.broker_host = self.config.get_value('agriculture.mqtt.broker_host', 'localhost')
        self.broker_port = self.config.get_value('agriculture.mqtt.broker_port', 1883)
        self.client_id = self.config.get_value('agriculture.mqtt.client_id', 'RaspberryPi_Dashboard')
        
        # Database path
        self.db_path = db_path or self.config.get_value('agriculture.database.path', 'data/logs/agriculture.db')
        
        # MQTT topics
        self.topic_sensors = self.config.get_value('agriculture.mqtt.topics.sensor_data', 'agriculture/sensors/data')
        self.topic_control = self.config.get_value('agriculture.mqtt.topics.pump_control', 'agriculture/control/pump')
        
        # Sensor thresholds
        self.thresholds = {
            'soil_moisture': {
                'critical_low': self.config.get_value('agriculture.sensors.thresholds.soil_moisture.critical_low', 20),
                'warning_low': self.config.get_value('agriculture.sensors.thresholds.soil_moisture.warning_low', 30),
                'warning_high': self.config.get_value('agriculture.sensors.thresholds.soil_moisture.warning_high', 80)
            },
            'temperature': {
                'min': self.config.get_value('agriculture.sensors.thresholds.temperature.min', 10),
                'max': self.config.get_value('agriculture.sensors.thresholds.temperature.max', 40)
            }
        }
        }
        
        # Current sensor readings
        self.current_readings = {
            "soil_moisture": None,
            "temperature": None,
            "humidity": None,
            "light_intensity": None,
            "pump_active": False,
            "last_updated": None,
            "esp32_connected": False
        }
        
        # Initialize MQTT client
        qos = self.config.get_value('agriculture.mqtt.qos', 1)
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # Connection status
        self.connected = False
        self.running = False
        
        # Initialize database
        self._init_database()
        
        print("🌱 Agriculture MQTT Client initialized")
    
    def _init_database(self):
        """Create agriculture database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sensor readings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                soil_moisture REAL,
                temperature REAL,
                humidity REAL,
                light_intensity REAL,
                pump_active INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Irrigation events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS irrigation_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                duration INTEGER,
                trigger TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agriculture_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                sensor TEXT,
                message TEXT,
                severity TEXT,
                resolved INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_timestamp ON sensor_readings(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_irrigation_timestamp ON irrigation_events(timestamp)')
        
        conn.commit()
        conn.close()
        print("✅ Agriculture database initialized")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            print(f"🔌 Connecting to MQTT broker at {self.broker_host}:{self.broker_port}...")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            self.running = True
            return True
        except Exception as e:
            print(f"❌ Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        print("🔌 Disconnected from MQTT broker")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            print("✅ Connected to MQTT broker successfully!")
            self.connected = True
            self.current_readings["esp32_connected"] = True
            
            # Subscribe to sensor data topic
            client.subscribe(self.topic_sensors)
            print(f"📡 Subscribed to topic: {self.topic_sensors}")
        else:
            print(f"❌ Connection failed with code {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        print(f"⚠️ Disconnected from MQTT broker (code: {rc})")
        self.connected = False
        self.current_readings["esp32_connected"] = False
    
    def on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            # Parse JSON payload
            payload = json.loads(msg.payload.decode())
            
            print(f"\n📥 Received sensor data:")
            print(f"   Soil Moisture: {payload.get('soil_moisture')}%")
            print(f"   Temperature: {payload.get('temperature')}°C")
            print(f"   Humidity: {payload.get('humidity')}%")
            print(f"   Light: {payload.get('light_intensity')} lux")
            print(f"   Pump: {'ON' if payload.get('pump_active') else 'OFF'}")
            
            # Update current readings
            self.current_readings.update({
                "soil_moisture": payload.get("soil_moisture"),
                "temperature": payload.get("temperature"),
                "humidity": payload.get("humidity"),
                "light_intensity": payload.get("light_intensity"),
                "pump_active": payload.get("pump_active", False),
                "last_updated": datetime.now().isoformat(),
                "esp32_connected": True
            })
            
            # Store in database
            self._store_reading(payload)
            
            # Check for alerts
            self._check_alerts(payload)
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def _store_reading(self, data):
        """Store sensor reading in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sensor_readings 
                (timestamp, soil_moisture, temperature, humidity, light_intensity, pump_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                data.get("soil_moisture"),
                data.get("temperature"),
                data.get("humidity"),
                data.get("light_intensity"),
                1 if data.get("pump_active") else 0
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Database error: {e}")
    
    def _check_alerts(self, data):
        """Check sensor values and create alerts if needed"""
        alerts = []
        
        # Soil moisture alerts
        soil_moisture = data.get("soil_moisture", 50)
        critical_low = self.thresholds['soil_moisture']['critical_low']
        warning_low = self.thresholds['soil_moisture']['warning_low']
        warning_high = self.thresholds['soil_moisture']['warning_high']
        
        if soil_moisture < critical_low:
            alerts.append(("critical", "soil_moisture", f"Critical: Soil moisture very low ({soil_moisture}%)"))
        elif soil_moisture < warning_low:
            alerts.append(("warning", "soil_moisture", f"Warning: Soil moisture low ({soil_moisture}%)"))
        elif soil_moisture > warning_high:
            alerts.append(("warning", "soil_moisture", f"Warning: Soil moisture very high ({soil_moisture}%)"))
        
        # Temperature alerts
        temperature = data.get("temperature", 25)
        temp_max = self.thresholds['temperature']['max']
        temp_min = self.thresholds['temperature']['min']
        
        if temperature > temp_max:
            alerts.append(("warning", "temperature", f"High temperature detected ({temperature}°C)"))
        elif temperature < temp_min:
            alerts.append(("warning", "temperature", f"Low temperature detected ({temperature}°C)"))
        
        # Store alerts in database
        if alerts:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for severity, sensor, message in alerts:
                cursor.execute('''
                    INSERT INTO agriculture_alerts 
                    (timestamp, alert_type, sensor, message, severity)
                    VALUES (?, ?, ?, ?, ?)
                ''', (datetime.now().isoformat(), "threshold", sensor, message, severity))
                
                print(f"⚠️ ALERT: {message}")
            
            conn.commit()
            conn.close()
    
    def control_pump(self, action, duration=30):
        """
        Send pump control command to ESP32
        
        Args:
            action: 'start' or 'stop'
            duration: Irrigation duration in seconds (for start command)
        """
        try:
            command = {
                "action": action,
                "duration": duration * 1000,  # Convert to milliseconds
                "timestamp": datetime.now().isoformat()
            }
            
            payload = json.dumps(command)
            result = self.client.publish(self.topic_control, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"✅ Pump control command sent: {action}")
                
                # Log irrigation event
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO irrigation_events 
                    (timestamp, action, duration, trigger)
                    VALUES (?, ?, ?, ?)
                ''', (datetime.now().isoformat(), action, duration if action == 'start' else 0, "manual"))
                conn.commit()
                conn.close()
                
                return True
            else:
                print(f"❌ Failed to send pump control command")
                return False
                
        except Exception as e:
            print(f"❌ Error controlling pump: {e}")
            return False
    
    def get_current_readings(self):
        """Get current sensor readings"""
        return self.current_readings.copy()
    
    def get_sensor_history(self, hours=24):
        """
        Get historical sensor data
        
        Args:
            hours: Number of hours to retrieve
        
        Returns:
            List of sensor readings
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM sensor_readings 
                WHERE timestamp >= datetime('now', '-' || ? || ' hours')
                ORDER BY timestamp ASC
            ''', (hours,))
            
            rows = cursor.fetchall()
            readings = [dict(row) for row in rows]
            
            conn.close()
            return readings
        except Exception as e:
            print(f"❌ Error retrieving history: {e}")
            return []


def main():
    """Test the MQTT client"""
    print("🌱 Starting Agriculture MQTT Client...\n")
    
    client = AgricultureMQTTClient(config_path="config/config.yaml")
    
    print(f"📋 Configuration loaded:")
    print(f"   MQTT Broker: {client.broker_host}:{client.broker_port}")
    print(f"   Client ID: {client.client_id}")
    print(f"   Sensor Topic: {client.topic_sensors}")
    print(f"   Control Topic: {client.topic_control}")
    print(f"   Database: {client.db_path}\n")
    
    if client.connect():
        print("✅ MQTT client running. Press Ctrl+C to stop.\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping MQTT client...")
            client.disconnect()
    else:
        print("❌ Failed to start MQTT client")


if __name__ == "__main__":
    main()
