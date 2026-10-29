# 📢 Sistem Pemantau Kebisingan Ruang Kelas Berbasis IoT (Multi-Node)

> **Mata Kuliah / Proyek**: Internet of Things (IoT) Multikomunikasi — Kelompok 7  
> **Tema Proyek**: Sistem Pemantau Kebisingan Ruang Belajar (Ruang Kelas)  
> **Status Tim**:
> - **Anggota 1 (Edge 1 — Depan Kelas)**: ✅ **SELESAI** (ESP32 Wokwi `src/main.cpp`, RMS, dB SPL, Moving Average, & HP 1 Web Mic).
> - **Anggota 2 (Edge 2 — Belakang Kelas)**: ✅ **SELESAI** (FFT Spectral Vocal Band 300–3400 Hz, ZCR, & Decision Tree AI Obrolan Siswa).
> - **Anggota 3 (MQTT & Dashboard Terpadu)**: ✅ **SELESAI** (Modul Kontrak MQTT, Normalizer JSON, Room Fusion Engine, Web Dashboard Glassmorphism Real-Time, & Kontrol 2 Arah).
> - **Anggota 4 (Integrasi, Pengujian, PPT & Demo)**: 🎯 Siap untuk pengujian akhir dan penyusunan laporan/PPT berdasarkan data terpadu dari Dashboard.

---

## 🏛️ Arsitektur Sistem Terpadu (End-to-End)

```
   [ Edge 1: ESP32 Wokwi / HP 1 ]  ---> Topic: kelas/kebisingan/node1/telemetry ---\
   (Depan: RMS & Moving Average)                                                   \
                                                                                    +---> [ Broker Cloud HiveMQ ] <---> [ Anggota 3: Web Dashboard ]
   [ Edge 2: HP 2 / Node 2 ]       ---> Topic: kelas/kebisingan/node2/telemetry ---/     (wss://...:8884/mqtt)          (Real-Time Charts, AI Meter,
   (Belakang: FFT Vokal & AI)                                                                                            Room Fusion, & Kontrol 2 Arah)
```

---

## 🚀 PANDUAN CEPAT MENJALANKAN DASHBOARD & SISTEM (Tugas Anggota 3)

### 1. Instalasi Dependensi Python (Opsional untuk Server & Simulator)
Buka terminal di folder root proyek dan jalankan:
```bash
pip install -r requirements.txt
```

### 2. Menjalankan Web Dashboard Utama
Tersedia dua cara mudah untuk membuka Dashboard:

#### Opsi A (Menggunakan Web Server Lokal Python — Direkomendasikan):
Jalankan perintah berikut di terminal:
```bash
python dashboard_server.py
```
Terminal akan menampilkan URL akses:
- **Web Dashboard (Laptop/PC)**: `http://localhost:8000/dashboard/index.html`
- **Web Edge HP 1 (Smartphone 1)**: `http://<IP_LAPTOP>:8000/client_mobile_hp1/hp1_web_mic.html`
- **Web Edge HP 2 (Smartphone 2)**: `http://<IP_LAPTOP>:8000/client_mobile_hp2/hp2_web_mic.html`

#### Opsi B (Buka Langsung File HTML):
Cukup klik ganda (double click) file `dashboard/index.html` di File Explorer untuk membukanya di browser Google Chrome / Edge. Dashboard langsung terkoneksi ke Cloud HiveMQ via Secure WebSocket SSL (`wss://broker.hivemq.com:8884/mqtt`).

---

### 3. Menjalankan Pengujian / Demo Simulator Otomatis
Jika kamu ingin menguji atau mendemokan tampilan Dashboard tanpa harus menyalakan Wokwi dan memegang 2 HP fisik sekaligus:

#### Cara 1: Menggunakan Tombol di Web Dashboard
Klik tombol **"🚀 Mulai Simulator Demo"** langsung di dalam Dashboard. Simulator internal akan mem-publish data dinamis 4 fase akustik ke HiveMQ.

#### Cara 2: Menggunakan Skrip Multi-Node Simulator Python
Buka terminal terpisah dan jalankan:
```bash
python scripts/simulate_multi_node.py
```
Simulator ini akan mensimulasikan Edge 1 (Depan) dan Edge 2 (Belakang) secara bersamaan, berganti fase secara otomatis (Hening $\to$ Dosen Menjelaskan $\to$ Obrolan Belakang $\to$ Kelas Gaduh), dan langsung merespons perintah kontrol (`set_threshold` & `mute`) dari Dashboard!

---

### 4. Menjalankan Pengujian Otomatis (Unit Tests)
Untuk memverifikasi bahwa Normalizer, Kontrak Topik, Deduplikasi, dan Room Fusion bebas bug:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 🎛️ Fitur Unggulan Web Dashboard Anggota 3

1. **Classroom Acoustic State Fusion (Hero Banner)**:
   - Menggabungkan data spasial Zona Depan dan Zona Belakang menjadi satu kesimpulan kondisi ruangan:
     - ✨ `SANGAT TENANG — SUASANA FOKUS / UJIAN`
     - ✅ `KONDUSIF — PEMBELAJARAN BERLANGSUNG`
     - 🗣️ `PERINGATAN — OBROLAN SISWA TERDETEKSI DI BELAKANG`
     - 🚨 `SANGAT BISING — ALARM KELAS AKTIF`
2. **Dual Real-Time Edge Monitoring**:
   - **Edge 1 (Depan Kelas)**: Memantau level dB, RMS, Peak, dan Moving Average.
   - **Edge 2 (Belakang Kelas)**: Memantau level dB, **Rasio Pita Energi Suara Vokal Manusia (300–3400 Hz %)**, **Probabilitas Obrolan Siswa (0–100%)**, dan klasifikasi Decision Tree.
3. **Grafik Garis Real-Time 60 Detik**:
   - Kurva Cyan (Edge 1), Kurva Purple (Edge 2), dan Garis Merah Putus-Putus (Threshold Aktif).
   - Dilengkapi *Deduplication Filter* sehingga pesan ganda dari Edge 2 tidak terplot ganda.
4. **Kontrol Perintah 2 Arah (Bi-Directional MQTT)**:
   - Mengubah ambang batas desibel (`set_threshold`) ke ESP32 dan HP Web Mic secara real-time.
   - Preset Mode Instan: `📝 Mode Ujian (60 dB)`, `📖 Mode Belajar (75 dB)`, `💬 Mode Diskusi (85 dB)`.
   - Tombol `Mute / Unmute Buzzer Alarm` (`{"mute": true}`).
5. **Riwayat Alarm & Export CSV**:
   - Mencatat seluruh lonjakan bising dan obrolan berlebih lengkap dengan timestamp.
   - Tombol **"Export CSV"** untuk mengunduh laporan pengujian bagi Anggota 4 dalam penyusunan PPT.

---

## 📋 Struktur Folder Repositori

```text
IoT-Kebisingan-Kelas/
├── dashboard/                      # [BARU - ANGGOTA 3] Web Dashboard Monitoring & Kontrol Utama
│   └── index.html                  # Antarmuka Glassmorphism, Grafik Real-Time, Fusion Engine & Kontrol
├── shared/                         # [BARU - ANGGOTA 3] Modul Standar MQTT & Normalizer
│   ├── __init__.py
│   ├── mqtt_contract.py            # Kamus topik, normalisasi payload heterogen, & filter deduplikasi
│   └── room_fusion.py              # Logika agregasi akustik multi-node ruang kelas
├── scripts/                        # [BARU - ANGGOTA 3] Alat Bantu Simulasi & Pengujian
│   └── simulate_multi_node.py      # Simulator multi-node (Node 1 + Node 2) + respons perintah kontrol
├── tests/                          # [BARU - ANGGOTA 3] Automated Unit Tests
│   └── test_dashboard_contract.py  # Pengujian otomatis normalizer, deduplikasi, dan room fusion
├── dashboard_server.py             # [BARU - ANGGOTA 3] Web server lokal & service background MQTT
├── requirements.txt                # [BARU - ANGGOTA 3] Daftar dependensi pustaka Python
├── src/
│   └── main.cpp                    # [ANGGOTA 1] Firmware ESP32 Wokwi (RMS, Moving Average, Kontrol)
├── diagram.json                    # [ANGGOTA 1] Rangkaian sirkuit virtual Wokwi
├── platformio.ini                  # [ANGGOTA 1] Konfigurasi PlatformIO
├── wokwi.toml                      # [ANGGOTA 1] Konfigurasi target Wokwi
├── client_mobile_hp1/              # [ANGGOTA 1] Edge HP 1 (Depan Kelas)
│   ├── hp1_web_mic.html            # Web Audio API + Subscribe Kontrol 2 Arah
│   └── hp1_mic_python.py           # Skrip pembaca mic Python HP 1
├── client_mobile_hp2/              # [ANGGOTA 2] Edge HP 2 (Belakang Kelas - AI Obrolan)
│   ├── hp2_web_mic.html            # Web Audio API, FFT Vokal, AI Classifier + Subscribe Kontrol 2 Arah
│   └── hp2_mic_python.py           # Skrip Python FFT Vokal 300-3400Hz, ZCR & Decision Tree
├── README.md                       # Panduan lengkap proyek kelompok
└── README_ANGGOTA.md               # Pembagian tugas & checklist 4 anggota tim
```

---

## 📡 Rangkuman Kontrak Topik & Payload MQTT

| Arah Komunikasi | Topik MQTT | Format Payload | Keterangan |
| :--- | :--- | :--- | :--- |
| **Edge 1 $\to$ Cloud** | `kelas/kebisingan/node1/telemetry`<br>`kelas/kebisingan/hp1/telemetry` | `{"device_id":"NODE_01", "db_smooth":64.2, "rms":0.035, "alert":false, ...}` | Telemetri level desibel & moving average zona depan |
| **Edge 2 $\to$ Cloud** | `kelas/kebisingan/node2/telemetry`<br>`kelas/kebisingan/hp2/telemetry` | `{"device_id":"HP_02", "db":71.4, "vocal_energy_ratio":72.5, "chatter_prob":78, ...}` | Telemetri FFT pita vokal & AI klasifikasi obrolan belakang |
| **Edge $\to$ Cloud** | `kelas/kebisingan/node1/alert`<br>`kelas/kebisingan/node2/alert` | `{"device_id":"...", "event":"NOISE_EXCEEDED", "db_level":82.1, ...}` | Pesan darurat saat kebisingan melampaui batas ambang |
| **Dashboard $\to$ Edge** | `kelas/kebisingan/node1/control`<br>`kelas/kebisingan/node2/control`<br>`kelas/kebisingan/control` | `{"set_threshold":80.0, "mute":true, "mode":"diskusi"}` | Perintah kontrol batas desibel & mute buzzer alarm |
| **Aggregator $\to$ Cloud** | `kelas/kebisingan/room/status` | `{"status_code":"KONDUSIF_BELAJAR", "avg_db":63.5, ...}` | Status terpadu hasil Classroom Room Fusion Engine |
