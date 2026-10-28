# 📢 Sistem Pemantau Kebisingan Ruang Kelas Berbasis IoT (Multi-Node)

> **Mata Kuliah / Proyek**: Internet of Things (IoT)  
> **Status**: Selesai Tahap 1 (Anggota 1: Edge 1, Sensor Audio, DSP RMS, Setup Wokwi & PlatformIO)  
> **Next Step**: Dilanjutkan oleh Anggota 2 (Edge 2 & Algoritma), Anggota 3 (Dashboard MQTT), dan Anggota 4 (Integrasi & Uji Coba).

---

## 🚀 PANDUAN CEPAT MENJALANKAN DEMO (Tugas Anggota 1)

Ikuti langkah-langkah di bawah ini untuk mendemokan sistem ke dosen / asisten lab:

### Langkah 1: Buka Web Monitor MQTT (Layar Pemantau Cloud)
Sebelum menyalakan simulasi, buka web monitor MQTT publik agar data yang dikirim ESP32 bisa langsung terlihat:
1. Buka browser, akses: [HiveMQ Web Client](http://www.hivemq.com/demos/websocket-client/)
2. Klik tombol **"Connect"** (biarkan pengaturan host default `broker.hivemq.com`).
3. Pada bagian **Subscriptions**, klik **"Add New Topic Subscription"**:
   - Topic: `kelas/kebisingan/#`
   - Klik **"Subscribe"**.
   *(Layar ini akan menangkap semua data telemetri dan alert secara realtime).*

---

### Langkah 2: Jalankan Simulasi Wokwi di VS Code
1. Buka folder `Pemantau_Kebisingan_Ruang_Kelas` di VS Code.
2. Pastikan ekstensi **PlatformIO IDE** dan **Wokwi Simulator** aktif di VS Code.
3. Klik ikon centang **PlatformIO: Build** (`✓`) di status bar bawah VS Code.
4. Buka file `diagram.json`, lalu klik tombol **Start Simulation** (ikon Play hijau di atas jendela editor Wokwi).
5. Buka tab **Serial Monitor** PlatformIO (`115200 baud`) untuk melihat log:
   - Terkoneksi ke WiFi `Wokwi-GUEST`.
   - Terkoneksi ke Broker `broker.hivemq.com`.
   - Data telemetri mulai dikirim setiap 1 detik.

---

### Langkah 3: Skenario Pengujian / Uji Coba

Putar kenop potensiometer (simulasi sensor suara mic analog di Wokwi) untuk menguji respon sistem:

| Skenario | Posisi Kenop Potensiometer | Respon Hardware (Wokwi) | Status di Serial & HiveMQ |
|:---|:---|:---|:---|
| **A. Kelas Hening / Kondusif** | Putar ke kiri bawah (< 55 dB) | **LED Hijau ON**, LED Merah OFF, Buzzer OFF | `"SANGAT TENANG"` / `"KONDUSIF"` |
| **B. Suasana Ramai (Peringatan)** | Putar ke tengah/jam 1 (70 - 75 dB) | **LED Merah ON**, LED Hijau OFF, Buzzer OFF | `"RAMAI / PERINGATAN"` |
| **C. Kelas Sangat Bising (Alarm)** | Putar ke kanan penuh (> 75 dB) | **LED Merah ON**, **Buzzer Berbunyi BEEP** | `"SANGAT BISING"` + Pesan Alert |

---

### Langkah 4: Demo Alternatif via HP Android Asli (Web Mic API)
Jika dosen meminta bukti pembacaan dari mikrofon HP asli:
1. Buka file `client_mobile_hp1/hp1_web_mic.html` di browser laptop atau kirim/buka di browser Chrome HP Android.
2. Klik **"🎤 Mulai Baca Mikrofon HP"** dan izinkan akses audio.
3. Berbicaralah atau tepuk tangan:
   - Nilai desibel (dB) dan grafik RMS akan bergerak mengikuti suara asli.
   - Data langsung terkirim secara bersamaan ke topik `kelas/kebisingan/hp1/telemetry` di HiveMQ!

---

## 🔄 PETUNJUK LANJUTAN UNTUK ANGGOTA TIM

Bagian ini adalah acuan kerja untuk **Anggota 2, 3, dan 4** agar pengembangan sistem tetap terintegrasi tanpa ada miskomunikasi format data.

```
       [ Edge 1: ESP32 / HP 1 ]  ---> Topic: kelas/kebisingan/node1/telemetry ---\
                                                                                 +---> [ Broker HiveMQ Cloud ] ---> [ Anggota 3: Dashboard ]
       [ Edge 2: HP 2 / Node 2 ] ---> Topic: kelas/kebisingan/node2/telemetry ---/
```

### 👤 Tugas Anggota 2 — Edge 2 & Algoritma Klasifikasi
* **Tanggung Jawab**:
  1. Menyiapkan perangkat Edge ke-2 (bisa menduplikasi folder ESP32 ini atau menggunakan script HP 2).
  2. Mengubah ID perangkat menjadi `"NODE_02"` / `"HP_02"` dan topik kirim menjadi:  
     `kelas/kebisingan/node2/telemetry`
  3. Menerapkan algoritma cerdas/klasifikasi tambahan (misal: *Exponential Moving Average*, *K-Nearest Neighbor (KNN)* sederhana, atau *Fuzzy Logic*) untuk membedakan antara kebisingan kontinu (obrolan siswa) vs kebisingan impulsif (ketukan meja/benda jatuh).
  4. Memastikan Edge 2 mengirim status yang konsisten ke broker MQTT.

---

### 👤 Tugas Anggota 3 — Broker MQTT & Dashboard Monitoring
* **Tanggung Jawab**:
  1. Menyiapkan dashboard antarmuka visual (bisa menggunakan **Python Tkinter / Streamlit / Web HTML & Chart.js**).
  2. Melakukan *Subscribe* ke topik:
     - `kelas/kebisingan/node1/telemetry` (Data Edge 1)
     - `kelas/kebisingan/node2/telemetry` (Data Edge 2)
     - `kelas/kebisingan/+/alert` (Notifikasi darurat kebisingan)
  3. Menampilkan elemen visual:
     - Grafik garis *real-time* tingkat dB Node 1 vs Node 2.
     - Indikator status kelas (*Kondusif* = Hijau, *Peringatan* = Kuning, *Bising* = Merah).
     - Riwayat log alarm kebisingan.
  4. Menyiapkan tombol kontrol perintah (*Publish* ke `kelas/kebisingan/node1/control`):
     - Ubah batas ambang: `{"set_threshold": 80.0}`
     - Mute alarm buzzer: `{"mute": true}`

---

### 👤 Tugas Anggota 4 — Integrasi, Pengujian, PPT & Demo Video
* **Tanggung Jawab**:
  1. Menggabungkan pengujian seluruh node: Node 1 (ESP32) + Node 2 berjalan bersamaan dan terbaca serentak di Dashboard Anggota 3.
  2. Mencatat data hasil pengujian tabel perbandingan:
     - Nilai dB saat kelas kosong.
     - Nilai dB saat guru/dosen menjelaskan.
     - Nilai dB saat diskusi kelompok berlangsung.
  3. Menyusun slide PowerPoint (PPT) presentasi:
     - Masalah: Gangguan konsentrasi belajar akibat kebisingan kelas.
     - Solusi & Arsitektur IoT (Edge Devices, MQTT, Dashboard).
     - Data Processing yang digunakan (RMS, Moving Average, Algoritma Klasifikasi).
     - Hasil pengujian dan kesimpulan.
  4. Merekam video demo singkat (screen recording simulasi Wokwi + Dashboard aktif).
  5. Merapikan repositori GitHub kelompok.

---

## 📋 KONTRAK DATA & FORMAT JSON (Standard Payload)

### 1. Payload Telemetri Edge (`kelas/kebisingan/+/telemetry`)
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

### 2. Payload Peringatan Alarm (`kelas/kebisingan/+/alert`)
```json
{
  "device_id": "NODE_01",
  "event": "NOISE_EXCEEDED",
  "db_level": 84.2,
  "message": "Peringatan: Tingkat kebisingan ruang kelas melebihi batas aman!"
}
```

### 3. Payload Perintah Kontrol Dashboard (`kelas/kebisingan/node1/control`)
- Mengubah batas dB: `{"set_threshold": 80.0}`
- Mematikan suara buzzer: `{"mute": true}`

---

## 🛠 Struktur File Proyek

```text
Pemantau_Kebisingan_Ruang_Kelas/
├── README.md                   # File panduan utama ini (Demo & Handoff tugas tim)
├── platformio.ini              # Konfigurasi PlatformIO & library
├── wokwi.toml                  # Konfigurasi target simulasi Wokwi
├── diagram.json                # Rangkaian sirkuit Wokwi (ESP32, Mic/Pot, LED, Buzzer)
├── src/
│   └── main.cpp                # Firmware ESP32: Sampling audio, RMS, dB, Filter, MQTT
└── client_mobile_hp1/          # Alternatif Edge HP Android
    ├── hp1_web_mic.html        # Web Audio API (buka di browser Chrome HP)
    └── hp1_mic_python.py       # Script Python pembaca mic
```

