# Sistem Pemantau Kebisingan Ruang Kelas (IoT)
**Project Based Learning - Internet of Things — Kelompok 7**  
*Fokus Implementasi: Anggota 1 (Edge Node 1 / HP 1), Anggota 2 (Edge Node 2 / HP 2 - Klasifikasi Kebisingan Obrolan), dan Anggota 3 (MQTT & Web Dashboard Terpadu)*

---

## 1. Pemenuhan 7 Ketentuan Tugas Dosen

| No | Ketentuan Tugas Dosen | Implementasi pada Proyek Ini |
|:---|:---|:---|
| 1 | **Berkelompok, 3 – 4 orang** | Dibagi menjadi 4 peran (Anggota 1, 2, 3, dan 4) dengan batasan tanggung jawab yang jelas. |
| 2 | **Minimal 2 edge device & 2 sensor** | **Edge 1:** ESP32 (Wokwi) + Sensor Suara Analog (atau HP 1 via Web Mic/Python) di Zona Depan Kelas.<br>**Edge 2:** HP 2 / Node 2 (Web Mic & Python) dengan sensor mic untuk klasifikasi obrolan di Zona Belakang Kelas. |
| 3 | **Minimal 2 jenis data processing** | **Processing 1:** Window sampling audio, perhitungan deviasi AC, Peak-to-Peak ($V_{pp}$), dan Root Mean Square (**RMS**) dikonversi ke estimasi desibel (**dB SPL**).<br>**Processing 2:** **Moving Average Filter** (meredam lonjakan sesaat) + **FFT Spectral Vocal Band (300–3400 Hz)** & **Zero-Crossing Rate (ZCR)**. |
| 4 | **Pengolahan data memakai AI / algoritma lain** | Menggunakan algoritma *DSP (RMS & FFT)*, *Moving Average Smoothing*, dan *Decision Tree / Multi-Feature Rule Classifier* khusus untuk mendeteksi intensitas dan probabilitas kebisingan obrolan siswa. |
| 5 | **Minimal 1 protokol cloud** | **MQTT** melalui broker cloud publik (`broker.hivemq.com` port TCP `1883`, TLS `8883`, & WebSockets SSL `8884/mqtt`). |
| 6 | **Dashboard satu jaringan (opsional)** | **Web Dashboard Terpadu (Dark Glassmorphism)** dengan grafik real-time 60 detik, panel AI obrolan, Classroom State Fusion, dan kontrol 2 arah (Threshold & Mute). |
| 7 | **Ide/Tugas tidak boleh sama** | Pemantau Tingkat Kebisingan & Akustik Ruang Kelas berbasis Multi-Node Edge Computing dengan Deteksi Obrolan Siswa. |

---

## 2. Struktur Proyek

```text
IoT-Kebisingan-Kelas/
├── dashboard/                      # [ANGGOTA 3] Web Dashboard Monitoring & Kontrol Utama
│   └── index.html                  # Antarmuka Glassmorphism, Grafik Real-Time, Fusion Engine & Kontrol
├── shared/                         # [ANGGOTA 3] Modul Standar MQTT & Normalizer
│   ├── __init__.py
│   ├── mqtt_contract.py            # Kamus topik, normalisasi payload heterogen, & filter deduplikasi
│   └── room_fusion.py              # Logika agregasi akustik multi-node ruang kelas
├── scripts/                        # [ANGGOTA 3] Alat Bantu Simulasi & Pengujian
│   └── simulate_multi_node.py      # Simulator multi-node (Node 1 + Node 2) + respons perintah kontrol
├── tests/                          # [ANGGOTA 3] Automated Unit Tests
│   └── test_dashboard_contract.py  # Pengujian otomatis normalizer, deduplikasi, dan room fusion
├── dashboard_server.py             # [ANGGOTA 3] Web server lokal & service background MQTT
├── requirements.txt                # [ANGGOTA 3] Daftar dependensi pustaka Python
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
└── README_ANGGOTA.md               # Dokumentasi & panduan integrasi tim
```

---

## 3. Rincian Status & Tanggung Jawab Anggota Kelompok

### 👤 Anggota 1 (Edge Node 1 / Depan Kelas)
- **Status: SELESAI**
- Menyelesaikan setup proyek Wokwi + PlatformIO (`src/main.cpp`, `diagram.json`).
- Implementasi pembacaan sinyal audio analog, kalkulasi RMS & estimasi dB SPL, moving average smoothing, aktuasi LED & Buzzer lokal, serta penerima perintah kontrol (`set_threshold` & `mute`).
- Menyediakan `client_mobile_hp1/hp1_web_mic.html` dan `hp1_mic_python.py` untuk opsi demo menggunakan mikrofon fisik smartphone di depan kelas.

### 👤 Anggota 2 (Edge Node 2 / Belakang Kelas — AI Obrolan)
- **Status: SELESAI**
- Menyiapkan perangkat Edge ke-2 pada folder `client_mobile_hp2/` (`hp2_web_mic.html` dan `hp2_mic_python.py`).
- Implementasi FFT ekstraksi energi pita frekuensi vokal manusia (300 Hz – 3400 Hz), Zero-Crossing Rate (ZCR), dan Decision Tree Rule Classifier untuk mendeteksi intensitas obrolan siswa (`HENING`, `OBROLAN KONDUSIF`, `OBROLAN DISKUSI`, `OBROLAN GADUH`, `BISING NON OBROLAN`).
- Mem-publish telemetri ke `kelas/kebisingan/node2/telemetry` & `kelas/kebisingan/hp2/telemetry`, serta alarm ke `kelas/kebisingan/node2/alert`.

### 👤 Anggota 3 (MQTT Contract, Normalizer, & Dashboard Terpadu — Kamu)
- **Status: SELESAI**
- Membangun `shared/mqtt_contract.py` untuk standarisasi topik, normalisasi format JSON antar-node yang heterogen, dan deduplikasi paket ganda.
- Membangun `shared/room_fusion.py` untuk mengolah data multi-node secara spasial menjadi kesimpulan kondisi kelas terpadu.
- Membangun `dashboard/index.html` (Web Dashboard Dark Glassmorphism):
  - Koneksi live ke HiveMQ Cloud (`wss://broker.hivemq.com:8884/mqtt`).
  - Indikator Hero Akustik Ruang Kelas Terpadu (Emerald / Cyan / Amber / Rose).
  - Kartu Node 1 (Depan) & Kartu Node 2 (Belakang lengkap dengan gauge vokal & progress bar obrolan).
  - Grafik garis real-time 60 detik (Node 1 vs Node 2 vs Threshold Line).
  - Panel kontrol dua arah: Ubah Threshold dB (slider + preset Ujian/Belajar/Diskusi) dan tombol Mute Buzzer Alarm.
  - Tabel riwayat insiden alarm dan tombol **Export CSV** untuk mempermudah Anggota 4 menyusun laporan PPT.
  - Built-in simulator interaktif langsung di dalam Dashboard.
- Membangun `dashboard_server.py` dan `scripts/simulate_multi_node.py`.
- Melakukan unit test otomatis di `tests/test_dashboard_contract.py`.

### 👤 Anggota 4 (Integrasi, Pengujian, PPT & Demo Video)
- **Status: SIAP DILAKUKAN**
- **Panduan Operasional Lengkap**: Silakan baca dokumen panduan mandiri [**PANDUAN_PENGUJIAN_ANGGOTA4.md**](file:///d:/IOT%202/PANDUAN_PENGUJIAN_ANGGOTA4.md) yang mencakup:
  1. Langkah pengujian end-to-end (3 skenario).
  2. Template tabel data pengujian siap salin untuk slide PPT.
  3. Checklist screenshot 4 kondisi akustik kelas.
  4. Storyboard & naskah lengkap perekaman video demo (durasi 3–5 menit).
  5. Prosedur export log alarm ke format spreadsheet (.CSV).
