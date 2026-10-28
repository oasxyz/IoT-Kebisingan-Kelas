# Sistem Pemantau Kebisingan Ruang Kelas (IoT)
**Project Based Learning - Internet of Things**  
*Fokus Implementasi: Anggota 1 (Edge Node 1 & Project Setup Wokwi/PlatformIO)*

---

## 1. Pemenuhan 7 Ketentuan Tugas

| No | Ketentuan Tugas Dosen | Implementasi pada Proyek Ini |
|:---|:---|:---|
| 1 | **Berkelompok, 3 – 4 orang** | Dibagi menjadi 4 peran (Anggota 1, 2, 3, dan 4) sesuai tabel pembagian tugas. |
| 2 | **Minimal 2 edge device & 2 sensor** | **Edge 1:** ESP32 (Wokwi) + Sensor Suara Analog (atau HP 1 via Web Mic/Python).<br>**Edge 2:** HP 2 / Node 2 dengan algoritma klasifikasi. |
| 3 | **Minimal 2 jenis data processing** | **Processing 1:** Window sampling audio, perhitungan deviasi AC, Peak-to-Peak ($V_{pp}$), dan Root Mean Square (**RMS**) dikonversi ke estimasi desibel (**dB SPL**).<br>**Processing 2:** **Moving Average Filter** (meredam lonjakan sesaat) + **Thresholding & Noise Level Classification** (Sangat Tenang, Kondusif, Peringatan, Sangat Bising). |
| 4 | **Pengolahan data memakai AI / algoritma lain** | Menggunakan algoritma *Digital Signal Processing (RMS)*, *Moving Average Smoothing*, dan *Rule-based / Classifier thresholding* untuk deteksi kegaduhan kelas secara otomatis. |
| 5 | **Minimal 1 protokol cloud** | **MQTT** melalui broker cloud publik (`broker.hivemq.com` port `1883` / WebSockets `8884`). |
| 6 | **Dashboard satu jaringan (opsional)** | Disediakan topik MQTT standar untuk dashboard Anggota 3 (Web/Desktop GUI). |
| 7 | **Ide/Tugas tidak boleh sama** | Pemantau Tingkat Kebisingan & Akustik Ruang Kelas berbasis Multi-Node Edge Computing. |

---

## 2. Struktur Proyek

```text
Pemantau_Kebisingan_Ruang_Kelas/
├── platformio.ini              # Konfigurasi PlatformIO & dependency library
├── wokwi.toml                  # Konfigurasi target simulasi Wokwi
├── diagram.json                # Rangkaian sirkuit virtual Wokwi (ESP32, Pot/Mic, LED, Buzzer)
├── src/
│   └── main.cpp                # Firmware ESP32: Sampling audio, RMS, dB, Filter, MQTT Telemetry
├── client_mobile_hp1/          # Alternatif Edge HP 1 (sesuai tabel kelompok)
│   ├── hp1_web_mic.html        # Web Audio API (bisa dibuka langsung di browser HP Android)
│   └── hp1_mic_python.py       # Python script pembaca mic via PC / Termux Android
└── README_ANGGOTA.md           # Dokumentasi & panduan integrasi tim
```

---

## 3. Rangkaian Wokwi (Hardware Setup)

Komponen pada `diagram.json`:
- **ESP32 DevKit V4**
- **Sensor Suara (Analog Mic / Potentiometer)**:
  - `VCC` -> `ESP32 3V3`
  - `GND` -> `ESP32 GND`
  - `SIG` -> `GPIO 34` (ADC1)
- **LED Merah (Indikator Bahaya/Bising)**: `GPIO 2` via Resistor `220Ω`
- **LED Hijau (Indikator Kondusif/Aman)**: `GPIO 4` via Resistor `220Ω`
- **Buzzer Alarm**: `GPIO 5`

---

## 4. Format Protokol MQTT & Topik (Kontrak Integrasi Tim)

### A. Topik MQTT
- **Publish Telemetry (Node 1)**: `kelas/kebisingan/node1/telemetry`
- **Publish Alarm (Node 1)**: `kelas/kebisingan/node1/alert`
- **Subscribe Kontrol (Dari Dashboard)**: `kelas/kebisingan/node1/control`
- **Publish Telemetry (Node 2 / HP 2)**: `kelas/kebisingan/node2/telemetry`

### B. Payload Telemetri JSON (`kelas/kebisingan/node1/telemetry`)
```json
{
  "device_id": "NODE_01",
  "device_name": "ESP32_Edge_Sound_Sensor",
  "location": "Ruang_Kelas_Depan",
  "raw_adc": 2150,
  "peak_to_peak": 480,
  "rms": 142.35,
  "db_instant": 75.1,
  "db_smooth": 73.8,
  "status": "RAMAI / PERINGATAN",
  "threshold_db": 75.0,
  "alert": true,
  "uptime_ms": 35200
}
```

### C. Payload Kontrol dari Dashboard (`kelas/kebisingan/node1/control`)
- Mengubah batas threshold kebisingan:
  ```json
  {"set_threshold": 80.0}
  ```
- Mematikan suara buzzer:
  ```json
  {"mute": true}
  ```

---

## 5. Panduan Tugas Anggota Kelompok

- **Anggota 1 (Kamu):** 
  - Telah menyelesaikan setup proyek Wokwi + PlatformIO.
  - Implementasi firmware pembacaan sensor analog mic, kalkulasi RMS & dB, aktuasi LED/Buzzer lokal, serta pengiriman JSON ke MQTT broker.
  - Menyediakan file `hp1_web_mic.html` jika dosen menginginkan demo langsung dari mikrofon HP Android asli.
- **Anggota 2 (Edge HP 2 & Algoritma):**
  - Mengambil referensi dari Edge 1 untuk membuat Node 2 (misal diletakkan di bagian belakang kelas).
  - Menerapkan algoritma klasifikasi (misal Decision Tree, KNN, atau fuzzy logic) untuk menentukan apakah suara bising berasal dari obrolan siswa atau suara ketukan/benda jatuh.
- **Anggota 3 (MQTT & Dashboard):**
  - Membuat dashboard (bisa berbasis Streamlit, Tkinter/Python, atau Web Dashboard) yang men-subscribe `kelas/kebisingan/#`.
  - Menampilkan grafik realtime dB dari Node 1 dan Node 2, status kondusifitas kelas, dan tombol set threshold / buzzer mute.
- **Anggota 4 (Integrasi, Pengujian, Dokumentasi):**
  - Menjalankan uji kebisingan pada beberapa kondisi (kelas sepi, kelas diskusi kelompok, kelas ricuh).
  - Menyusun slide presentasi PowerPoint dan video demo simulasi Wokwi + Dashboard.

---

## 6. Cara Menjalankan Simulasi Wokwi di VS Code

1. Buka folder `Pemantau_Kebisingan_Ruang_Kelas` di VS Code.
2. Pastikan ekstensi **PlatformIO IDE** dan **Wokwi Simulator** telah terinstal di VS Code.
3. Klik tombol **PlatformIO: Build** (ikon centang di status bar bawah) untuk meng-compile firmware `main.cpp`.
4. Buka file `diagram.json`, lalu klik tombol **Start Simulation** (ikon Play hijau Wokwi).
5. Putar kenop slider potensiometer sensor suara di simulator Wokwi untuk menguji perubahan desibel:
   - Nilai rendah: LED Hijau menyala (Kondusif).
   - Nilai tinggi: LED Merah menyala + Buzzer berbunyi (Bising / Peringatan).
6. Pantau output log dan telemetri yang terkirim pada Serial Monitor VS Code.

