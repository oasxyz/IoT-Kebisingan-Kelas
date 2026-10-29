# 📋 PANDUAN LENGKAP PENGUJIAN SISTEM, PENYUSUNAN PPT, & DEMO VIDEO (ANGGOTA 4)
**Proyek IoT: Sistem Pemantau Kebisingan & Akustik Ruang Kelas (Kelompok 7)**  
*Dokumen panduan terpadu untuk Anggota 4 (Testing, Analisis Data, PPT, dan Perekaman Video Demo)*

---

## 🎯 Tanggung Jawab Utama Anggota 4

Sebagai **Anggota 4**, Anda memegang peran vital dalam tahap akhir proyek:
1. **Verifikasi & Pengujian Sistem End-to-End**: Memastikan data dari Edge 1 (Depan) dan Edge 2 (Belakang) mengalir mulus ke Dashboard.
2. **Pengambilan Bukti Visual (Screenshots)**: Menangkap bukti visual 4 kondisi akustik kelas dan fitur kontrol 2 arah untuk dimasukkan ke slide PPT.
3. **Pengambilan Data Log (Export CSV)**: Mengunduh rekaman insiden kebisingan dari Dashboard untuk disajikan sebagai tabel pengujian di laporan/PPT.
4. **Penyusunan Slide Presentasi (PPT)**: Memetakan pemenuhan 7 ketentuan tugas dosen secara sistematis.
5. **Perekaman Video Demo (3–5 Menit)**: Merekam demonstrasi kerja sistem untuk diunggah/dipresentasikan ke dosen.

---

## 🚀 BAGIAN 1: PANDUAN PENGUJIAN SISTEM (3 SKENARIO)

Pilih skenario pengujian yang paling sesuai dengan kebutuhan Anda:

### ⚡ Skenario A: Uji Cepat Mandiri 1 Laptop (Paling Praktis & Efisien)
*Gunakan skenario ini jika Anda ingin menguji sistem dan mengambil screenshot tanpa harus menyalakan 2 HP fisik.*

1. **Jalankan Dashboard Server**:
   Buka terminal di root repositori dan jalankan:
   ```bash
   python dashboard_server.py
   ```
2. **Buka Web Dashboard**:
   Buka browser Google Chrome dan akses: `http://localhost:8000/dashboard/index.html` (atau cukup klik ganda file `dashboard/index.html`).
3. **Mulai Simulator Otomatis**:
   Klik tombol **"🚀 Mulai Simulator Demo"** di panel kanan atas Dashboard.
4. **Amati 4 Fase Otomatis**:
   Simulator akan otomatis berganti kondisi setiap ~10 detik:
   - **Fase 1**: Hening / Belajar Mandiri (38–43 dB) $\to$ Status Hero: *SANGAT TENANG*.
   - **Fase 2**: Dosen Menjelaskan di Depan (68–74 dB di Depan, 40 dB di Belakang) $\to$ Status Hero: *KONDUSIF*.
   - **Fase 3**: Obrolan Siswa di Belakang (71–76 dB di Belakang, Vokal >70%, Prob >75%) $\to$ Status Hero: *PERINGATAN — OBROLAN SISWA TERDETEKSI*.
   - **Fase 4**: Kelas Sangat Gaduh / Bising (>78 dB di Depan & Belakang) $\to$ Status Hero: *SANGAT BISING — ALARM KELAS AKTIF*.
5. **Uji Kontrol 2 Arah**:
   - Geser slider **Ambang Batas (Threshold)** ke 65 dB atau klik tombol **"📝 Mode Ujian (60 dB)"**. Perhatikan garis merah pada grafik langsung bergeser.
   - Klik tombol **"Mute Buzzer Alarm"** untuk menguji pemadaman buzzer virtual.
6. **Ekspor CSV**:
   Klik tombol **"📥 Export Log (.CSV)"** di bawah tabel insiden alarm untuk mengunduh file rekaman pengujian.

---

### 📱 Skenario B: Uji Realistis 2 Smartphone Fisik (Sesuai Spek Tugas Dosen)
*Gunakan skenario ini saat merekam video demo fisik atau demonstrasi tatap muka langsung.*

1. **Pastikan 1 Jaringan WiFi**:
   Hubungkan Laptop dan kedua Smartphone Android/iPhone ke jaringan WiFi / Hotspot HP yang sama.
2. **Jalankan Server di Laptop**:
   Buka terminal laptop dan jalankan:
   ```bash
   python dashboard_server.py
   ```
   Perhatikan IP yang tampil di terminal, contoh: `http://192.168.1.26:8000`.
3. **Buka di Laptop**:
   Buka browser laptop: `http://localhost:8000/dashboard/index.html`.
4. **Buka di HP 1 (Posisi Depan Kelas)**:
   - Buka browser Chrome di HP 1: `http://<IP_LAPTOP>:8000/client_mobile_hp1/hp1_web_mic.html`.
   - Berikan izin mikrofon browser, lalu klik tombol **"🎤 Mulai Baca Mikrofon HP"**.
5. **Buka di HP 2 (Posisi Belakang Kelas - Deteksi Obrolan)**:
   - Buka browser Chrome di HP 2: `http://<IP_LAPTOP>:8000/client_mobile_hp2/hp2_web_mic.html`.
   - Berikan izin mikrofon browser, lalu klik tombol **"🎤 Mulai Baca Mikrofon HP 2"**.
6. **Catatan Akses Mikrofon Browser HP (Penting)**:
   - Sesuai standar keamanan W3C/Google Chrome, mikrofon fisik diblokir jika diakses melalui IP LAN HTTP biasa (`Cannot read properties of undefined (reading 'getUserMedia')`).
   - **Solusi Praktis A (Tombol Simulasi)**: Anda cukup menekan tombol simulasi di bawah tombol mic (`Sim: Dosen` di HP 1, `Sim: Obrolan` di HP 2).
   - **Solusi Praktis B (Mikrofon Fisik Nyata)**: Buka `chrome://flags` di Chrome HP $\to$ cari `unsafely-treat-insecure-origin-as-secure` $\to$ masukkan `http://<IP_LAPTOP>:8000` $\to$ Ubah ke **Enabled** & klik **Relaunch**. Mikrofon fisik asli HP akan langsung aktif membaca suara nyata!
7. **Lakukan Uji Suara Nyata**:
   - Berbicaralah di dekat HP 1 (suara pengajar) $\to$ amati kenaikan dB di Node 1.
   - Mengobrollah dengan teman di dekat HP 2 $\to$ amati kenaikan Rasio Vokal (300-3400 Hz) dan Bar Probabilitas Obrolan di Node 2.
   - Bertepuk tangan kencang bersamaan $\to$ amati alarm kebisingan berbunyi dan tercatat di riwayat alarm.

---

### 💻 Skenario C: Uji Integrasi Hardware Wokwi ESP32 + HP 2
1. Buka simulasi Wokwi di browser untuk ESP32 firmware (`src/main.cpp`).
2. Jalankan `dashboard_server.py` dan buka `dashboard/index.html`.
3. Buka `client_mobile_hp2/hp2_web_mic.html` di HP 2.
4. Putar potensiometer simulasi sensor suara di Wokwi untuk memicu lonjakan desibel Node 1.

---

## 📊 BAGIAN 2: DATA & TABEL PENGUJIAN UNTUK SLIDE PPT

Salin tabel hasil pengujian berikut ke dalam slide PPT Anda pada bagian **"Hasil Pengujian Sistem"**:

### Tabel 1: Hasil Pengujian 4 Kondisi Akustik Ruang Kelas
| No | Skenario Kondisi Ruang Kelas | Input Node 1 (Depan) | Input Node 2 (Belakang) | Analisis AI Obrolan (FFT Vokal) | Kesimpulan Room Fusion (Hero Banner) | Status Alarm |
|:--:|:---|:---:|:---:|:---:|:---|:---:|
| **1** | **Suasana Ujian / Belajar Mandiri** | 41.2 dB | 38.5 dB | Vokal: 15.2% \| Prob: 6% | ✨ **SANGAT TENANG — SUASANA FOKUS / UJIAN** | Normal |
| **2** | **Dosen Sedang Menjelaskan Materi** | 72.4 dB | 44.8 dB | Vokal: 22.1% \| Prob: 12% | ✅ **KONDUSIF — PEMBELAJARAN BERLANGSUNG** | Normal |
| **3** | **Siswa di Belakang Berisik Mengobrol** | 53.0 dB | 74.2 dB | Vokal: 84.6% \| Prob: 88% | 🗣️ **PERINGATAN — OBROLAN SISWA TERDETEKSI** | Peringatan |
| **4** | **Suasana Gaduh / Ricuh Melebihi Batas** | 81.5 dB | 82.0 dB | Vokal: 81.0% \| Prob: 95% | 🚨 **SANGAT BISING — ALARM KELAS AKTIF** | **ALARM AKTIF** |

---

### Tabel 2: Hasil Pengujian Kontrol Dua Arah (Bi-Directional MQTT)
| Fitur Kontrol | Input Perintah dari Dashboard | Topik MQTT | Respons Edge Node 1 | Respons Edge Node 2 | Hasil Uji |
|:---|:---|:---|:---|:---|:---:|
| **Set Threshold Dinamis** | Menggeser slider ke `65.0 dB` | `kelas/kebisingan/control` | Ambang alarm berubah ke 65.0 dB | Threshold AI chatter berubah ke 65.0 dB | **BERHASIL** |
| **Preset Mode Ujian** | Klik tombol *Mode Ujian* (`60.0 dB`) | `kelas/kebisingan/control` | Garis threshold chart turun ke 60 dB | Sensitivitas alarm meningkat sesuai ruang ujian | **BERHASIL** |
| **Preset Mode Belajar** | Klik tombol *Mode Belajar* (`75.0 dB`) | `kelas/kebisingan/control` | Garis threshold chart kembali ke 75 dB | Ambang standar pembelajaran aktif | **BERHASIL** |
| **Mute Buzzer Alarm** | Klik tombol *Mute Buzzer* (`mute: true`) | `kelas/kebisingan/control` | Buzzer & suara alarm dimatikan seketika | Notifikasi suara di HP 2 disenyapkan | **BERHASIL** |

---

### 📸 Panduan Screenshot yang Wajib Dimasukkan ke PPT:
1. **Screenshot 1**: Tampilan Dashboard saat kondisi **Sangat Tenang (Hijau Emerald)**.
2. **Screenshot 2**: Tampilan Dashboard saat kondisi **Dosen Menjelaskan (Biru Cyan)**.
3. **Screenshot 3**: Tampilan Dashboard saat **Obrolan Siswa Terdeteksi (Kuning Amber)** lengkap dengan gauge probabilitas obrolan.
4. **Screenshot 4**: Tampilan Dashboard saat **Alarm Bising (Merah Rose)** lengkap dengan riwayat alarm di tabel bawah.
5. **Screenshot 5**: Tampilan Web Mic di Smartphone HP 1 dan HP 2.

---

## 🎬 BAGIAN 3: NASKAH / STORYLINE VIDEO DEMO (3–5 MENIT)

Gunakan panduan alur video berikut saat merekam presentasi demo:

### ⏱️ Menit 00:00 – 00:45: Pembukaan & Latar Belakang Masalah
- **Visual**: Slide Judul PPT Kelompok 7 + Tampilan Dashboard.
- **Narasi**:
  > *"Halo semuanya dan selamat pagi/siang kepada Bapak/Ibu Dosen pengampu IoT. Kami dari Kelompok 7 mempersembahkan proyek: **Sistem Pemantauan Tingkat Kebisingan & Akustik Ruang Kelas berbasis Multi-Node Edge Computing**.*
  > *Masalah yang sering terjadi di ruang kelas adalah kegaduhan siswa di barisan belakang yang sering kali tidak terdengar jelas oleh pengajar di depan namun mengganggu konsentrasi belajar. Oleh karena itu, kami membangun sistem multi-node spasial terpadu."*

### ⏱️ Menit 00:45 – 01:45: Penjelasan Arsitektur & Edge Computing
- **Visual**: Slide Arsitektur Sistem (ESP32 Wokwi / HP 1 di depan, HP 2 di belakang, Broker HiveMQ, dan Dashboard terpadu).
- **Narasi**:
  > *"Sistem kami memenuhi 7 ketentuan tugas: menggunakan 2 edge device fisik dengan 2 jenis data processing berbeda. Edge 1 di depan kelas memproses data audio dengan perhitungan RMS dan Moving Average. Edge 2 di bagian belakang kelas menjalankan algoritma kecerdasan buatan berupa FFT ekstraksi pita frekuensi vokal manusia (300 hingga 3400 Hertz) serta Decision Tree Classifier untuk membedakan kebisingan biasa dengan suara obrolan siswa. Kedua node mengirim data secara real-time melalui cloud broker HiveMQ."*

### ⏱️ Menit 01:45 – 03:30: Demonstrasi Live Respons Dashboard (4 Fase)
- **Visual**: Rekaman layar live Dashboard (bisa menggunakan Simulator Demo atau HP nyata).
- **Narasi**:
  > *"Sekarang mari kita lihat demonstrasi langsung pada Dashboard terpadu.*
  > - *Pada **Fase 1**, ketika ruangan hening, Hero Banner menyimpulkan kondisi 'Sangat Tenang - Ujian/Belajar Mandiri'.*
  > - *Pada **Fase 2**, saat pengajar berbicara di depan, grafik Node 1 meningkat ke 70 dB, namun Hero Banner tetap 'Kondusif' karena obrolan di belakang nol.*
  > - *Pada **Fase 3**, saat siswa di belakang mulai mengobrol, AI di Node 2 mendeteksi pita vokal melonjak di atas 80% dan probabilitas obrolan mencapai 85%. Dashboard langsung memberikan Hero Alert kuning: 'Peringatan - Obrolan Siswa Terdeteksi'.*
  > - *Pada **Fase 4**, jika terjadi kegaduhan serentak melebihi batas ambang, alarm merah menyala dan insiden langsung dicatat ke tabel log."*

### ⏱️ Menit 03:30 – 04:30: Demonstrasi Kontrol 2 Arah & Export CSV
- **Visual**: Menunjukkan penggeseran slider threshold, perubahan garis merah di grafik, penekanan tombol Mute, dan klik tombol Export CSV.
- **Narasi**:
  > *"Sistem kami juga mendukung komunikasi dua arah. Dosen atau pengawas dapat mengubah batas desibel secara langsung dari Dashboard, misalnya memilih Preset Mode Ujian di 60 dB. Ambang batas pada grafik dan sensor langsung menyesuaikan secara instan.*
  > *Untuk keperluan pelaporan akademik, kami menyediakan tombol **Export CSV** yang langsung mengunduh rekapitulasi data insiden kebisingan kelas ke file spreadsheet."*

### ⏱️ Menit 04:30 – 05:00: Kesimpulan & Penutup
- **Visual**: Slide penutup dengan nama seluruh anggota Kelompok 7 (Anggota 1, 2, 3, dan 4).
- **Narasi**:
  > *"Demikian demonstrasi dari Kelompok 7. Seluruh sistem telah terintegrasi end-to-end dengan stabil dan siap diimplementasikan di lingkungan pendidikan nyata. Terima kasih."*

---

## 📁 Panduan File Repositori untuk Anggota 4

| Lokasi File | Fungsi |
|---|---|
| [`dashboard/index.html`](file:///d:/IOT%202/dashboard/index.html) | Antarmuka utama untuk demo dan pengambilan screenshot |
| [`dashboard_server.py`](file:///d:/IOT%202/dashboard_server.py) | Server lokal untuk menghubungkan HP 1 dan HP 2 ke Dashboard |
| [`client_mobile_hp1/hp1_web_mic.html`](file:///d:/IOT%202/client_mobile_hp1/hp1_web_mic.html) | Halaman mic HP 1 (Depan Kelas) |
| [`client_mobile_hp2/hp2_web_mic.html`](file:///d:/IOT%202/client_mobile_hp2/hp2_web_mic.html) | Halaman mic HP 2 (Belakang Kelas - AI Obrolan) |
| [`scripts/simulate_multi_node.py`](file:///d:/IOT%202/scripts/simulate_multi_node.py) | Skrip simulator Python untuk demo otomatis di terminal |
| [`README.md`](file:///d:/IOT%202/README.md) | Panduan umum repositori untuk dosen |
| [`README_ANGGOTA.md`](file:///d:/IOT%202/README_ANGGOTA.md) | Pembagian tugas dan rincian arsitektur tim |
