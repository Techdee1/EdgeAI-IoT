/*
 * ESP32 Agriculture Sensors - EcoGuard System
 * Reads sensors and publishes data to Raspberry Pi via MQTT
 * 
 * CONFIGURATION INSTRUCTIONS:
 * 1. Open config/config.yaml on Raspberry Pi
 * 2. Under 'agriculture.esp32', update:
 *    - wifi_ssid: Your WiFi network name
 *    - wifi_password: Your WiFi password
 * 3. Get Raspberry Pi IP: Run 'hostname -I' on Pi
 * 4. Update mqtt_server below with Pi's IP address
 * 5. Adjust calibration values if needed (see config.yaml agriculture.esp32.calibration)
 * 
 * Hardware:
 * - ESP32-WROOM-32 Development Board
 * - Capacitive Soil Moisture Sensor v1.2 (Analog) -> GPIO 34
 * - DHT11 Temperature & Humidity Sensor -> GPIO 4
 * - LDR Photoresistor (Light Detection) -> GPIO 35
 * - 5V Relay Module (Pump Control) -> GPIO 26
 * 
 * Pin assignments match config.yaml agriculture.esp32.pins section
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ===== WiFi Configuration =====
// TODO: Get these values from config/config.yaml (agriculture.esp32 section)
const char* ssid = "YOUR_WIFI_SSID";           // Replace with your WiFi name
const char* password = "YOUR_WIFI_PASSWORD";   // Replace with your WiFi password

// ===== MQTT Configuration =====
// TODO: Get Raspberry Pi IP with 'hostname -I' command
const char* mqtt_server = "192.168.1.100";     // Replace with your Raspberry Pi IP address
const int mqtt_port = 1883;                    // Default MQTT port (from config.yaml)
const char* mqtt_client_id = "ESP32_Agriculture_Sensors";  // Must match config.yaml
const char* mqtt_topic_sensors = "agriculture/sensors/data";     // Must match config.yaml
const char* mqtt_topic_control = "agriculture/control/pump";     // Must match config.yaml

// ===== Pin Definitions =====
// These match config.yaml agriculture.esp32.pins section
#define SOIL_MOISTURE_PIN 34    // Analog pin for soil moisture sensor (GPIO 34)
#define DHT_PIN 4               // Digital pin for DHT11 (GPIO 4)
#define LDR_PIN 35              // Analog pin for light sensor (GPIO 35)
#define RELAY_PIN 26            // Digital pin for relay/pump control (GPIO 26)

// ===== Sensor Configuration =====
#define DHT_TYPE DHT11
DHT dht(DHT_PIN, DHT_TYPE);

// ===== Timing Configuration =====
const unsigned long SENSOR_INTERVAL = 30000;  // Read sensors every 30 seconds (matches config.yaml)
const unsigned long IRRIGATION_DURATION = 30000;  // 30 seconds default irrigation (from config.yaml)
unsigned long lastSensorRead = 0;
unsigned long pumpStartTime = 0;
bool pumpActive = false;

// ===== Calibration Values =====
// Get these from config.yaml agriculture.esp32.calibration.soil_moisture section
// Calibrate these values for your specific soil moisture sensor:
// 1. Place sensor in completely DRY soil -> note the value
// 2. Place sensor in completely WET soil -> note the value
const int SOIL_DRY_VALUE = 3200;    // Sensor reading in completely dry soil
const int SOIL_WET_VALUE = 1200;    // Sensor reading in completely wet soil

// ===== MQTT Client =====
WiFiClient espClient;
PubSubClient client(espClient);

// ===== Function Prototypes =====
void setup_wifi();
void reconnect_mqtt();
void callback(char* topic, byte* payload, unsigned int length);
void readSensors();
void publishSensorData(float soilMoisture, float temp, float humidity, float lightLevel);
void controlPump(bool activate, unsigned long duration = IRRIGATION_DURATION);
void checkAutoIrrigation(float soilMoisture, float lightLevel);

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== ESP32 Agriculture Sensors ===");
  
  // Initialize DHT sensor
  dht.begin();
  
  // Initialize relay (pump control)
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);  // Pump OFF initially
  
  // Setup WiFi
  setup_wifi();
  
  // Setup MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  
  Serial.println("Setup complete!");
  Serial.println("Waiting for sensor readings...\n");
}

void loop() {
  // Maintain MQTT connection
  if (!client.connected()) {
    reconnect_mqtt();
  }
  client.loop();
  
  // Read and publish sensor data at interval
  unsigned long currentTime = millis();
  if (currentTime - lastSensorRead >= SENSOR_INTERVAL) {
    lastSensorRead = currentTime;
    readSensors();
  }
  
  // Check if pump should be turned off (manual irrigation timer)
  if (pumpActive && (currentTime - pumpStartTime >= IRRIGATION_DURATION)) {
    controlPump(false);
  }
}

void setup_wifi() {
  delay(10);
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n✗ WiFi connection failed!");
  }
}

void reconnect_mqtt() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT broker...");
    
    if (client.connect(mqtt_client_id)) {
      Serial.println(" ✓ Connected!");
      
      // Subscribe to control topic
      client.subscribe(mqtt_topic_control);
      Serial.print("Subscribed to: ");
      Serial.println(mqtt_topic_control);
    } else {
      Serial.print(" ✗ Failed, rc=");
      Serial.print(client.state());
      Serial.println(" | Retrying in 5 seconds...");
      delay(5000);
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  // Handle incoming MQTT messages (pump control commands)
  Serial.print("Message received on topic: ");
  Serial.println(topic);
  
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.print("Message: ");
  Serial.println(message);
  
  // Parse JSON command
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.print("JSON parse error: ");
    Serial.println(error.c_str());
    return;
  }
  
  // Control pump based on command
  if (strcmp(topic, mqtt_topic_control) == 0) {
    const char* action = doc["action"];
    unsigned long duration = doc["duration"] | IRRIGATION_DURATION;
    
    if (strcmp(action, "start") == 0) {
      controlPump(true, duration);
    } else if (strcmp(action, "stop") == 0) {
      controlPump(false);
    }
  }
}

void readSensors() {
  Serial.println("--- Reading Sensors ---");
  
  // Read Soil Moisture (Analog 0-4095)
  int soilRaw = analogRead(SOIL_MOISTURE_PIN);
  // Convert to percentage (0% = dry, 100% = wet)
  float soilMoisture = map(soilRaw, SOIL_DRY_VALUE, SOIL_WET_VALUE, 0, 100);
  soilMoisture = constrain(soilMoisture, 0, 100);
  
  // Read DHT11 (Temperature & Humidity)
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  // Read Light Level (Analog 0-4095)
  int lightRaw = analogRead(LDR_PIN);
  // Convert to lux (approximate mapping)
  float lightLevel = map(lightRaw, 0, 4095, 0, 2000);
  
  // Validate readings
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("✗ Failed to read from DHT sensor!");
    temperature = 0;
    humidity = 0;
  }
  
  // Print readings
  Serial.print("Soil Moisture: ");
  Serial.print(soilMoisture, 1);
  Serial.println("%");
  
  Serial.print("Temperature: ");
  Serial.print(temperature, 1);
  Serial.println("°C");
  
  Serial.print("Humidity: ");
  Serial.print(humidity, 1);
  Serial.println("%");
  
  Serial.print("Light Level: ");
  Serial.print(lightLevel, 0);
  Serial.println(" lux");
  
  Serial.print("Pump Status: ");
  Serial.println(pumpActive ? "ACTIVE" : "OFF");
  
  // Publish to MQTT
  publishSensorData(soilMoisture, temperature, humidity, lightLevel);
  
  // Check if automatic irrigation is needed
  checkAutoIrrigation(soilMoisture, lightLevel);
  
  Serial.println();
}

void publishSensorData(float soilMoisture, float temp, float humidity, float lightLevel) {
  // Create JSON payload
  StaticJsonDocument<300> doc;
  doc["device_id"] = mqtt_client_id;
  doc["timestamp"] = millis();
  doc["soil_moisture"] = round(soilMoisture * 10) / 10.0;
  doc["temperature"] = round(temp * 10) / 10.0;
  doc["humidity"] = round(humidity * 10) / 10.0;
  doc["light_intensity"] = round(lightLevel);
  doc["pump_active"] = pumpActive;
  
  // Serialize JSON to string
  char jsonBuffer[300];
  serializeJson(doc, jsonBuffer);
  
  // Publish to MQTT
  if (client.publish(mqtt_topic_sensors, jsonBuffer, true)) {  // retained = true
    Serial.println("✓ Data published to MQTT");
  } else {
    Serial.println("✗ Failed to publish data");
  }
}

void controlPump(bool activate, unsigned long duration) {
  if (activate && !pumpActive) {
    digitalWrite(RELAY_PIN, HIGH);  // Turn pump ON
    pumpActive = true;
    pumpStartTime = millis();
    IRRIGATION_DURATION = duration;
    Serial.println("🚿 PUMP ACTIVATED");
    Serial.print("Duration: ");
    Serial.print(duration / 1000);
    Serial.println(" seconds");
  } else if (!activate && pumpActive) {
    digitalWrite(RELAY_PIN, LOW);   // Turn pump OFF
    pumpActive = false;
    Serial.println("🛑 PUMP DEACTIVATED");
  }
}

void checkAutoIrrigation(float soilMoisture, float lightLevel) {
  // Automatic irrigation logic
  // Rule 1: Critical low moisture -> Always irrigate
  if (soilMoisture < 20) {
    if (!pumpActive) {
      Serial.println("⚠️ CRITICAL: Soil moisture very low!");
      controlPump(true, 60000);  // 60 seconds emergency irrigation
    }
  }
  // Rule 2: Low moisture during daytime -> Regular irrigation
  else if (soilMoisture < 30 && lightLevel > 200) {
    if (!pumpActive) {
      Serial.println("💧 AUTO-IRRIGATION: Soil moisture low");
      controlPump(true, 30000);  // 30 seconds irrigation
    }
  }
  // Rule 3: Very high moisture -> Skip irrigation
  else if (soilMoisture > 70) {
    Serial.println("✓ Soil moisture optimal - no irrigation needed");
  }
}
