# Sistem Pemantau Kebisingan Ruang Kelas Berbasis IoT (Multi-Node)

Sistem pemantau akustik dan kebisingan ruang kelas terdistribusi yang membandingkan kondisi suara zona depan (meja pengajar) dan zona belakang (area siswa) secara real-time. Sistem ini menyelesaikan kelemahan sensor tunggal biasa (yang sering menganggap suara pengajar mengajar sebagai kebisingan, sementara obrolan siswa di barisan belakang tidak terdeteksi) menggunakan pemrosesan sinyal digital (DSP), analisis spektrum frekuensi vokal manusia (300–3.400 Hz), klasifikasi obrolan berbasis Decision Tree, serta kontrol dua arah (*bi-directional*) via protokol MQTT.

Proyek ini dikembangkan untuk memenuhi tugas mata kuliah **Internet of Things (IoT) — Praktik Multikomunikasi Dua Arah dan Multisensor**.

---

## Anggota Kelompok 7

| No | Nama Lengkap | NIM |
| :-: | :--- | :-: |
| 1 | **Shalom Kurniawan** | `24060124120033` |
| 2 | **Romualdus Yoas Wicaksono** | `24060124120046` |
| 3 | **Reynaldi Bertinus Hutagaol** | `24060124140157` |
| 4 | **Raffie Aditya Akbar** | `24060124130054` |

---

## Daftar Isi
1. [Latar Belakang & Masalah Spasial](#1-latar-belakang--masalah-spasial)
2. [Arsitektur Sistem (End-to-End)](#2-arsitektur-sistem-end-to-end)
3. [Spesifikasi Perangkat & Pengolahan Data di Edge](#3-spesifikasi-perangkat--pengolahan-data-di-edge)
4. [Kontrak Komunikasi MQTT](#4-kontrak-komunikasi-mqtt)
5. [Panduan Menjalankan Sistem](#5-panduan-menjalankan-sistem)
6. [Hasil Pengujian Sistem (4 Skenario & Kontrol 2 Arah)](#6-hasil-pengujian-sistem-4-skenario--kontrol-2-arah)
7. [Fitur Web Dashboard](#7-fitur-web-dashboard)
8. [Struktur Direktori Repositori](#8-struktur-direktori-repositori)

---

## 1. Latar Belakang & Masalah Spasial

### Kelemahan Pendekatan Sensor Tunggal
Pada sistem pemantau kebisingan konvensional yang hanya menggunakan satu sensor di tengah ruangan:
1. **Tuli Spasial**: Sistem tidak mengetahui asal sumber suara. Saat pengajar menerangkan materi dengan suara lantang (~70–75 dB), sensor tunggal menganggapnya sebagai kebisingan ruangan dan memicu alarm palsu (*false positive*).
2. **Titik Buta (Blindspot) Barisan Belakang**: Obrolan siswa di barisan belakang (~65 dB) sering tidak terdengar jelas dari meja pengajar di depan, namun mengganggu konsentrasi siswa di sekitarnya.
3. **Ketidakmampuan Membedakan Karakter Suara**: Sensor biasa tidak dapat membedakan suara benda jatuh (ketukan/pintu sesaat) dengan suara percakapan manusia yang terus-menerus.

### Solusi: Logika Akustik Multi-Node (Depan vs Belakang)
Sistem ini menggunakan dua titik pemantauan terpisah yang dianalisis secara komparatif:

| Zona Depan (Pengajar) | Zona Belakang (Siswa) | AI Pita Vokal (HP 2) | Kesimpulan Kondisi Ruang Kelas | Status Alarm |
| :--- | :--- | :--- | :--- | :---: |
| Hening (< 50 dB) | Hening (< 50 dB) | Rendah (< 30%) | **Sangat Tenang (Ujian / Mandiri)** | Aman (Mati) |
| Bersuara (60–75 dB) | Hening (< 50 dB) | Rendah (< 30%) | **Kondusif (Pengajar Menjelaskan)** | Aman (Mati) |
| Sedang (50–65 dB) | Bising (> 65 dB) | **Tinggi (> 70%)** | **Peringatan Obrolan Siswa Aktif** | Peringatan Visual |
| Bising (> 75 dB) | Bising (> 75 dB) | Campuran / Tinggi | **Sangat Bising (Kelas Gaduh)** | **Alarm Aktif** |

---

## 2. Arsitektur Sistem (End-to-End)

```text
 [ Edge 1: ESP32 / HP 1 ]  ---> Topic: kelas/kebisingan/node1/telemetry ---\
 (Depan: RMS & Moving Avg)                                                 \
                                                                            +---> [ Broker Cloud HiveMQ ] <---> [ Web Dashboard & Server ]
 [ Edge 2: Smartphone HP 2] ---> Topic: kelas/kebisingan/node2/telemetry ---/     (wss://...:8884/mqtt)          (Real-Time Charts, AI Meter,
 (Belakang: FFT Vokal & AI)                                                                                      Room Fusion, & Kontrol 2 Arah)
                                                                            <---  Topic: kelas/kebisingan/control
                                                                                  (Perintah: set_threshold & mute)
```

Komunikasi terbagi menjadi dua arah yang saling melengkapi:
- **Arah 1 (Aliran Telemetri)**: Perangkat Edge menghitung desibel dan analisis spektral, lalu mengirim ringkasan data terstruktur ke Cloud Broker HiveMQ.
- **Arah 2 (Aliran Kontrol Balik)**: Pengguna (pengajar/pengawas) dapat mengubah ambang batas toleransi desibel atau membungkam buzzer alarm langsung dari Web Dashboard. Perintah diterima oleh seluruh perangkat edge dalam waktu rata-rata **< 140 ms**.

---

## 3. Spesifikasi Perangkat & Pengolahan Data di Edge

### A. Edge Node 1: Area Depan Kelas
- **Perangkat**: Mikrokontroler ESP32 (Wokwi Simulation / board fisik) atau Smartphone HP 1 via Web Audio API.
- **Sensor**: Sensor Suara Analog (Electret / MAX4466) terhubung ke pin ADC 34.
- **Pengolahan Data (DSP 1)**:
  - *Window Sampling*: 50 ms untuk menangkap siklus gelombang audio analog.
  - *Root Mean Square (RMS)*: Dihitung dari deviasi kuadrat terhadap tegangan offset DC:
    $$\text{RMS} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (x_i - \bar{x})^2}$$
  - *Konversi dB SPL*: Dikonversi ke skala logaritmik desibel:
    $$\text{dB SPL} = 20 \log_{10}(\text{RMS} + 1.0) + 32.0$$
  - *Moving Average Filter ($N=5$)*: Meredam lonjakan sesaat (seperti suara buku jatuh atau ketukan meja) agar tidak memicu alarm palsu.
- **Aktuator Lokal**: Indikator LED Merah/Hijau dan Piezo Buzzer 1.8 kHz pada pin GPIO 5.

### B. Edge Node 2: Area Belakang Kelas
- **Perangkat**: Smartphone Android (HP 2) via Web Mic atau skrip Python.
- **Sensor**: Mikrofon bawaan perangkat fisik smartphone (sampling rate 44.1 kHz).
- **Pengolahan Data (DSP 2)**:
  - *Fast Fourier Transform (FFT)*: Memetakan sinyal domain waktu ke spektrum frekuensi secara real-time.
  - *Isolasi Pita Frekuensi Vokal Manusia*: Rentang frekuensi percakapan (300 Hz – 3.400 Hz).
  - *Rasio Energi Vokal*:
    $$\text{Vocal Energy Ratio} = \frac{\sum |X(f_{\text{vokal}})|^2}{\sum |X(f_{\text{total}})|^2} \times 100\%$$
  - *Zero-Crossing Rate (ZCR)*: Mengukur frekuensi pemotongan titik nol sinyal untuk membedakan desis/dengung dengan suara bicara manusia.
- **Algoritma AI (Decision Tree Classifier)**:
  Mengevaluasi kombinasi desibel, rasio energi vokal, dan stabilitas ZCR:
  - Jika $\text{dB} \ge 65.0$ dan $\text{Vocal Ratio} \ge 70.0\% \implies$ **OBROLAN GADUH** (*Chatter Probability* > 80%).
  - Jika $\text{dB} \ge 65.0$ tetapi $\text{Vocal Ratio} < 42.0\% \implies$ **BISING NON-OBROLAN** (misal suara gesekan kursi atau dengung pendingin ruangan).
- **Aktuator Lokal**: Web Audio Synthesizer (alarm frekuensi 880 Hz / 1760 Hz).

---

## 4. Kontrak Komunikasi MQTT

Sistem menerapkan prinsip **"Kirim Hasil, Bukan Data Mentah"**. Perangkat edge tidak mengirim rekaman audio mentah (yang memboroskan bandwidth dan melanggar privasi percakapan), melainkan mengirim paket JSON ringkas (< 200 bytes per kirim).

### Daftar Topik Standar

| Arah Komunikasi | Topik MQTT | Keterangan |
| :--- | :--- | :--- |
| **Edge 1 $\to$ Cloud** | `kelas/kebisingan/node1/telemetry`<br>`kelas/kebisingan/hp1/telemetry` | Telemetri level desibel & moving average zona depan |
| **Edge 2 $\to$ Cloud** | `kelas/kebisingan/node2/telemetry`<br>`kelas/kebisingan/hp2/telemetry` | Telemetri FFT pita vokal & klasifikasi obrolan belakang |
| **Edge $\to$ Cloud** | `kelas/kebisingan/+/alert` | Notifikasi darurat saat kebisingan melampaui ambang batas |
| **Dashboard $\to$ Edge** | `kelas/kebisingan/control` | Perintah pengaturan ambang batas (`set_threshold`) & `mute` |
| **Aggregator $\to$ Cloud** | `kelas/kebisingan/room/status` | Status terpadu hasil Classroom Room Fusion Engine |

### Format Payload JSON

**1. Telemetri Edge Node 2 (Hasil Olah AI Belakang):**
```json
{
  "device_id": "HP_02",
  "location": "Ruang_Kelas_Belakang",
  "db": 74.2,
  "vocal_energy_ratio": 84.6,
  "chatter_prob": 88.0,
  "classification": "OBROLAN_GADUH",
  "alert": true,
  "timestamp": "2026-10-29T10:15:30.000Z"
}
```

**2. Perintah Kontrol Dua Arah (Dashboard ke Edge):**
```json
{
  "set_threshold": 65.0,
  "mute": true,
  "mode": "ujian"
}
```

---

## 5. Panduan Menjalankan Sistem

### Persyaratan Awal
Pastikan Python 3.9+ sudah terpasang. Instal dependensi pustaka Python:
```bash
pip install -r requirements.txt
```

### Opsi A: Menjalankan Server Lokal Terpadu (Direkomendasikan)
Jalankan web server lokal:
```bash
python dashboard_server.py
```
Akses antarmuka melalui browser:
- **Web Dashboard (Laptop/PC)**: `http://localhost:8000/dashboard/index.html`
- **Web Edge HP 1 (Smartphone Depan)**: `http://<IP_LAPTOP>:8000/client_mobile_hp1/hp1_web_mic.html`
- **Web Edge HP 2 (Smartphone Belakang)**: `http://<IP_LAPTOP>:8000/client_mobile_hp2/hp2_web_mic.html`

> **Catatan Izin Mikrofon di Smartphone (LAN Context):**  
> Pada Google Chrome Android, akses mikrofon via koneksi HTTP lokal dapat dibuka melalui menu `chrome://flags` $\to$ cari `unsafely-treat-insecure-origin-as-secure` $\to$ masukkan `http://<IP_LAPTOP>:8000` $\to$ pilih **Enabled** dan klik **Relaunch**. Atau, gunakan tombol simulasi bawaan di layar HP.

### Opsi B: Buka Langsung File HTML Dashboard
Cukup buka file `dashboard/index.html` langsung di browser Chrome/Edge. Dashboard akan otomatis terhubung ke broker HiveMQ publik melalui WebSocket SSL (`wss://broker.hivemq.com:8884/mqtt`).

### Opsi C: Menjalankan Simulator Otomatis Multi-Node
Jika ingin mendemokan pergerakan grafik dan respons kontrol tanpa harus menyalakan smartphone fisik:
- **Via Dashboard**: Klik tombol **"Mulai Simulator Demo"** di bagian kanan atas Web Dashboard.
- **Via Terminal**: Jalankan skrip simulator Python multi-node:
  ```bash
  python scripts/simulate_multi_node.py
  ```
  Simulator ini menjalankan 4 fase akustik secara otomatis (Hening $\to$ Dosen Menerangkan $\to$ Obrolan Belakang $\to$ Kelas Gaduh) dan merespons perintah kontrol dari Dashboard secara real-time.

### Menjalankan Automated Unit Tests
Untuk memverifikasi modul normalizer data, penanganan deduplikasi, dan engine room fusion:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 6. Hasil Pengujian Sistem (4 Skenario & Kontrol 2 Arah)

Pengujian end-to-end dilakukan pada 4 skenario kondisi ruang kelas nyata:

| No | Skenario Pengujian | Node 1 (Depan) | Node 2 (Belakang) | AI Obrolan (Pita Vokal) | Kesimpulan Dashboard | Status Alarm |
| :-: | :--- | :---: | :---: | :---: | :--- | :---: |
| **1** | **Suasana Ujian / Mandiri** | 41.2 dB | 38.5 dB | 15.2% (Prob: 6%) | ✨ **SANGAT TENANG** | Normal (Mati) |
| **2** | **Dosen Menerangkan** | 72.4 dB | 44.8 dB | 22.1% (Prob: 12%) | ✅ **KONDUSIF (BELAJAR)** | Normal (Tidak Memicu Alarm) |
| **3** | **Obrolan di Belakang** | 53.0 dB | 74.2 dB | **84.6% (Prob: 88%)** | ⚠️ **PERINGATAN OBROLAN** | Peringatan Visual |
| **4** | **Kelas Sangat Gaduh** | 81.5 dB | 82.0 dB | 81.0% (Prob: 95%) | 🚨 **SANGAT BISING** | **Buzzer Berbunyi** |

### Hasil Pengujian Kontrol Dua Arah
- **Latensi Respon**: Perintah perubahan ambang batas (`set_threshold`) dari Dashboard diterima dan dieksekusi oleh seluruh perangkat edge dalam waktu rata-rata **< 140 ms**.
- **Tombol Mute Buzzer**: Berhasil mematikan suara alarm piezo buzzer dan web audio secara instan tanpa mengganggu aliran telemetri grafik live.

---

## 7. Fitur Web Dashboard

1. **Classroom Acoustic State Fusion (Hero Banner)**:
   Menggabungkan data spasial kedua node menjadi satu indikator status ruangan yang jelas:
   - `SANGAT TENANG — SUASANA FOKUS / UJIAN` (Hijau / Emerald)
   - `KONDUSIF — PEMBELAJARAN BERLANGSUNG` (Biru / Cyan)
   - `PERINGATAN — OBROLAN SISWA TERDETEKSI DI BELAKANG` (Oranye / Amber)
   - `SANGAT BISING — ALARM KELAS AKTIF` (Merah / Rose)
2. **Dual Real-Time Edge Monitoring**:
   - **Node 1 (Depan)**: Level dB, RMS, dan Moving Average.
   - **Node 2 (Belakang)**: Level dB, Gauge Rasio Pita Vokal (300–3.400 Hz), dan Progress Bar Probabilitas Obrolan AI.
3. **Grafik Garis Real-Time 60 Detik**:
   Visualisasi live multi-kurva (Node Depan, Node Belakang, dan Garis Threshold aktif) dilengkapi filter deduplikasi agar data tidak terplot ganda.
4. **Kontrol Interaktif Dua Arah**:
   - Slider pengaturan ambang batas dinamis (50–95 dB).
   - Tombol Preset Sekali Klik: `Mode Ujian (60 dB)`, `Mode Belajar (75 dB)`, `Mode Diskusi (85 dB)`.
   - Tombol `Mute / Unmute Buzzer Alarm`.
5. **Riwayat Alarm & Ekspor CSV**:
   Mencatat riwayat insiden lonjakan kebisingan lengkap dengan timestamp, level desibel, dan status obrolan, serta tombol **"Export CSV"** untuk pelaporan evaluasi kedisiplinan kelas.

---

## 8. Struktur Direktori Repositori

```text
IoT-Kebisingan-Kelas/
├── dashboard/                      # Web Dashboard monitoring & antarmuka kontrol utama
│   └── index.html                  # Antarmuka Glassmorphism, grafik live, fusion engine, & kontrol 2 arah
├── shared/                         # Modul bersama standar MQTT & agregasi sistem
│   ├── __init__.py
│   ├── mqtt_contract.py            # Definisi topik standar, normalisasi payload, & deduplikasi
│   └── room_fusion.py              # Logika agregasi spasial kondisi akustik ruang kelas
├── scripts/                        # Skrip utilitas & simulasi pengujian
│   └── simulate_multi_node.py      # Simulator multi-node terdistribusi (Node 1 + Node 2)
├── tests/                          # Pengujian otomatis (Automated Unit Tests)
│   └── test_dashboard_contract.py  # Unit test normalizer, deduplikasi, dan logika fusion
├── src/                            # Firmware mikrokontroler (Edge Node 1)
│   └── main.cpp                    # Firmware ESP32 Wokwi (RMS, Moving Average, & Kontrol Buzzer)
├── diagram.json                    # Rangkaian sirkuit virtual ESP32 di Wokwi
├── platformio.ini                  # Konfigurasi PlatformIO untuk ESP32
├── wokwi.toml                      # Konfigurasi environment simulator Wokwi
├── client_mobile_hp1/              # Edge Node 1 versi smartphone (Depan Kelas)
│   ├── hp1_web_mic.html            # Web Audio API mic depan + subscribe kontrol
│   └── hp1_mic_python.py           # Skrip pembacaan mic berbasis Python
├── client_mobile_hp2/              # Edge Node 2 versi smartphone (Belakang Kelas - AI Obrolan)
│   ├── hp2_web_mic.html            # Web Audio API, FFT vokal, & AI Decision Tree
│   └── hp2_mic_python.py           # Skrip pembacaan mic Python FFT vokal & ZCR
├── dashboard_server.py             # Server HTTP lokal & background service MQTT
├── requirements.txt                # Daftar dependensi pustaka Python
└── README.md                       # Dokumentasi tunggal resmi sistem
```
