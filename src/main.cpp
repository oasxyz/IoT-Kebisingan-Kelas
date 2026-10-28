#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <math.h>

// ==========================================
// TUGAS BESAR IOT: PEMANTAU KEBISINGAN RUANG KELAS
// NODE 1: EDGE DEVICE (ESP32 + SENSOR SUARA)
// ==========================================

// --- Konfigurasi Pin Hardware ---
const int PIN_SOUND_ANALOG = 34; // Pin ADC untuk pembacaan sinyal mic analog
const int PIN_LED_ALERT    = 2;  // LED Merah (Indikator Kebisingan Melebihi Batas)
const int PIN_LED_NORMAL   = 4;  // LED Hijau (Indikator Kondusif / Tenang)
const int PIN_BUZZER       = 5;  // Buzzer Alarm

// --- Konfigurasi WiFi (Wokwi Sim) ---
const char* WIFI_SSID     = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

// --- Konfigurasi MQTT Broker ---
const char* MQTT_BROKER   = "broker.hivemq.com";
const int   MQTT_PORT     = 1883;
const char* TOPIC_TELEMETRY = "kelas/kebisingan/node1/telemetry";
const char* TOPIC_ALERT     = "kelas/kebisingan/node1/alert";
const char* TOPIC_CONTROL   = "kelas/kebisingan/node1/control";

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// --- Parameter Pengolahan Sinyal Audio (RMS & dB) ---
const int SAMPLE_WINDOW_MS = 50;  // Window sampling 50ms untuk menangkap gelombang audio
float thresholdDb = 75.0;         // Batas ambang kebisingan kelas (dB)
bool buzzerMuted = false;

// Moving Average Buffer (Data Processing ke-2)
const int MA_SIZE = 5;
float maHistory[MA_SIZE] = {40.0, 40.0, 40.0, 40.0, 40.0};
int maIndex = 0;

unsigned long lastPublishTime = 0;
const unsigned long PUBLISH_INTERVAL_MS = 1000; // Kirim telemetri setiap 1 detik

// --- Deklarasi Fungsi ---
void connectWiFi();
void connectMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
float calculateMovingAverage(float newSample);
void processNoiseActuation(float dbSmooth, String& status, bool& isAlarm);

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n=============================================");
  Serial.println("  SISTEM PEMANTAU KEBISINGAN KELAS (NODE 1)  ");
  Serial.println("=============================================");

  pinMode(PIN_SOUND_ANALOG, INPUT);
  pinMode(PIN_LED_ALERT, OUTPUT);
  pinMode(PIN_LED_NORMAL, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);

  // Inisialisasi awal LED
  digitalWrite(PIN_LED_ALERT, LOW);
  digitalWrite(PIN_LED_NORMAL, HIGH);
  digitalWrite(PIN_BUZZER, LOW);

  connectWiFi();
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (!mqttClient.connected()) {
    connectMQTT();
  }
  mqttClient.loop();

  unsigned long currentMillis = millis();
  if (currentMillis - lastPublishTime >= PUBLISH_INTERVAL_MS) {
    lastPublishTime = currentMillis;

    // ----------------------------------------------------
    // DATA PROCESSING 1: SAMPLING SINYAL & PERHITUNGAN RMS
    // ----------------------------------------------------
    unsigned long startSampleTime = millis();
    int minVal = 4095;
    int maxVal = 0;
    long sumRaw = 0;
    int sampleCount = 0;

    // Buffer sampel untuk perhitungan deviasi kuadrat (RMS)
    const int MAX_SAMPLES = 120;
    int samples[MAX_SAMPLES];

    while (millis() - startSampleTime < SAMPLE_WINDOW_MS && sampleCount < MAX_SAMPLES) {
      int val = analogRead(PIN_SOUND_ANALOG);
      samples[sampleCount++] = val;
      sumRaw += val;
      if (val < minVal) minVal = val;
      if (val > maxVal) maxVal = val;
      delayMicroseconds(400); // interval sampling mikrofon
    }

    // Nilai DC Offset / Rata-rata sinyal
    float meanBias = (float)sumRaw / sampleCount;

    // Menghitung RMS dari deviasi gelombang AC: sqrt( 1/N * sum((x - mean)^2) )
    double sumSquareDiff = 0.0;
    for (int i = 0; i < sampleCount; i++) {
      float diff = (float)samples[i] - meanBias;
      sumSquareDiff += (diff * diff);
    }
    float rms = sqrt(sumSquareDiff / sampleCount);
    int peakToPeak = maxVal - minVal;

    // Konversi RMS & Vpp ke estimasi desibel SPL (Sound Pressure Level)
    // Formula kalibrasi desibel dari amplitudo ADC:
    // dB = 20 * log10(RMS + 1) + Offset Kalibrasi (misal 32 dB untuk ambient noise terendah)
    float calculatedDb = 20.0 * log10(rms + 1.0) + 32.0;

    // Batasi dalam rentang realistis kebisingan ruangan (30 s.d. 100 dB)
    if (calculatedDb < 30.0) calculatedDb = 30.0;
    if (calculatedDb > 100.0) calculatedDb = 100.0;

    // ----------------------------------------------------
    // DATA PROCESSING 2: MOVING AVERAGE & KLASIFIKASI STATUS
    // ----------------------------------------------------
    float dbSmooth = calculateMovingAverage(calculatedDb);

    String noiseStatus;
    bool isAlarm = false;
    processNoiseActuation(dbSmooth, noiseStatus, isAlarm);

    // ----------------------------------------------------
    // PENGIRIMAN TELEMETRI MQTT (JSON)
    // ----------------------------------------------------
    JsonDocument doc;
    doc["device_id"]    = "NODE_01";
    doc["device_name"]  = "ESP32_Edge_Sound_Sensor";
    doc["location"]     = "Ruang_Kelas_Depan";
    doc["raw_adc"]      = samples[sampleCount - 1];
    doc["peak_to_peak"] = peakToPeak;
    doc["rms"]          = round(rms * 100.0) / 100.0;
    doc["db_instant"]   = round(calculatedDb * 10.0) / 10.0;
    doc["db_smooth"]    = round(dbSmooth * 10.0) / 10.0;
    doc["status"]       = noiseStatus;
    doc["threshold_db"] = thresholdDb;
    doc["alert"]        = isAlarm;
    doc["uptime_ms"]    = currentMillis;

    char jsonBuffer[384];
    serializeJson(doc, jsonBuffer);

    // Publish data utama ke broker
    mqttClient.publish(TOPIC_TELEMETRY, jsonBuffer);

    // Tampilkan di Serial Monitor
    Serial.printf("[TELEMETRY] dB: %.1f | RMS: %.2f | Vpp: %d | Status: %s | Alarm: %s\n",
                  dbSmooth, rms, peakToPeak, noiseStatus.c_str(), isAlarm ? "YES" : "NO");

    // Jika terjadi alarm kebisingan, kirim pesan prioritas ke topik alert
    if (isAlarm) {
      JsonDocument alertDoc;
      alertDoc["device_id"] = "NODE_01";
      alertDoc["event"]     = "NOISE_EXCEEDED";
      alertDoc["db_level"]  = dbSmooth;
      alertDoc["message"]   = "Peringatan: Tingkat kebisingan ruang kelas melebihi batas aman!";
      char alertBuffer[200];
      serializeJson(alertDoc, alertBuffer);
      mqttClient.publish(TOPIC_ALERT, alertBuffer);
    }
  }
}

// Menghitung filter moving average untuk meredam lonjakan sesaat
float calculateMovingAverage(float newSample) {
  maHistory[maIndex] = newSample;
  maIndex = (maIndex + 1) % MA_SIZE;

  float sum = 0.0;
  for (int i = 0; i < MA_SIZE; i++) {
    sum += maHistory[i];
  }
  return (sum / MA_SIZE);
}

// Logika aktuator lokal (LED & Buzzer) berdasarkan status kebisingan
void processNoiseActuation(float db, String& status, bool& isAlarm) {
  if (db < 55.0) {
    status = "SANGAT TENANG";
    digitalWrite(PIN_LED_NORMAL, HIGH);
    digitalWrite(PIN_LED_ALERT, LOW);
    digitalWrite(PIN_BUZZER, LOW);
    isAlarm = false;
  } else if (db < thresholdDb) {
    status = "KONDUSIF";
    digitalWrite(PIN_LED_NORMAL, HIGH);
    digitalWrite(PIN_LED_ALERT, LOW);
    digitalWrite(PIN_BUZZER, LOW);
    isAlarm = false;
  } else if (db < thresholdDb + 8.0) {
    status = "RAMAI / PERINGATAN";
    digitalWrite(PIN_LED_NORMAL, LOW);
    digitalWrite(PIN_LED_ALERT, HIGH);
    digitalWrite(PIN_BUZZER, LOW);
    isAlarm = true;
  } else {
    status = "SANGAT BISING";
    digitalWrite(PIN_LED_NORMAL, LOW);
    digitalWrite(PIN_LED_ALERT, HIGH);
    if (!buzzerMuted) {
      digitalWrite(PIN_BUZZER, HIGH);
    }
    isAlarm = true;
  }
}

// Callback penerima perintah MQTT (misal dari Dashboard Anggota 3)
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  char message[length + 1];
  for (unsigned int i = 0; i < length; i++) {
    message[i] = (char)payload[i];
  }
  message[length] = '\0';

  Serial.printf("[MQTT CMD] Topik: %s | Pesan: %s\n", topic, message);

  // Parsing perintah JSON atau text
  // Contoh: {"set_threshold": 80.0} atau {"mute": true}
  JsonDocument cmdDoc;
  DeserializationError error = deserializeJson(cmdDoc, message);
  if (!error) {
    if (cmdDoc["set_threshold"].is<float>()) {
      thresholdDb = cmdDoc["set_threshold"];
      Serial.printf("[CONFIG] Threshold kebisingan diubah ke: %.1f dB\n", thresholdDb);
    }
    if (cmdDoc["mute"].is<bool>()) {
      buzzerMuted = cmdDoc["mute"];
      if (buzzerMuted) digitalWrite(PIN_BUZZER, LOW);
      Serial.printf("[CONFIG] Buzzer mute set: %s\n", buzzerMuted ? "TRUE" : "FALSE");
    }
  }
}

void connectWiFi() {
  Serial.print("Menghubungkan ke WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" TERHUBUNG!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println(" Gagal tersambung (akan dicoba lagi).");
  }
}

void connectMQTT() {
  Serial.print("Menghubungkan ke MQTT Broker...");
  String clientId = "ESP32_NoiseMonitor_Node1_" + String(random(0xffff), HEX);
  if (mqttClient.connect(clientId.c_str())) {
    Serial.println(" TERHUBUNG!");
    mqttClient.subscribe(TOPIC_CONTROL);
    Serial.printf("Subscribed ke topik: %s\n", TOPIC_CONTROL);
  } else {
    Serial.print(" Gagal, rc=");
    Serial.print(mqttClient.state());
    Serial.println(" Coba lagi dalam 2 detik...");
    delay(2000);
  }
}

