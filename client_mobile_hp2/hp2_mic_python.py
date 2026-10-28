"""
=============================================================================
Sistem Pemantau Kebisingan Ruang Kelas (IoT) - Edge Device HP 2 (Node 2)
Fokus: Klasifikasi Khusus Kebisingan Saat Mengobrol (Classroom Chatter Noise)
=============================================================================
Peran: Anggota 2 (Edge HP 2 / Node 2 Belakang Kelas & Algoritma Klasifikasi)
Format: Kompatibel dengan format HP 1 dan kontrak telemetri tim.
=============================================================================
"""

import time
import math
import json
import sys
import numpy as np
import paho.mqtt.client as mqtt

# Cek ketersediaan pustaka sounddevice untuk mikrofon fisik
try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

# ================= Konfigurasi Jaringan & Topik MQTT =================
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
TOPIC_TELEMETRY_NODE2 = "kelas/kebisingan/node2/telemetry"
TOPIC_TELEMETRY_HP2   = "kelas/kebisingan/hp2/telemetry"
TOPIC_ALERT           = "kelas/kebisingan/node2/alert"

DEVICE_ID = "HP_02"
DEVICE_NAME = "HP2_Edge_Chatter_Classifier"
LOCATION = "Ruang_Kelas_Belakang"

# Parameter Sampling Audio
SAMPLE_RATE = 44100      # 44.1 kHz
DURATION = 1.0           # Window sampling 1 detik
VOCAL_FREQ_MIN = 300.0   # Batas bawah pita suara vokal manusia (Hz)
VOCAL_FREQ_MAX = 3400.0  # Batas atas pita suara vokal manusia (Hz)

# Ambang Batas Kebisingan Obrolan (dB)
THRESHOLD_CHATTER_DB = 75.0


def calculate_rms(audio_data):
    """Menghitung Root Mean Square (RMS) dari amplitudo audio."""
    if len(audio_data) == 0:
        return 0.0
    return float(np.sqrt(np.mean(audio_data ** 2)))


def rms_to_db(rms):
    """
    Konversi nilai RMS amplitudo audio ke estimasi dB SPL (Sound Pressure Level).
    Mengacu pada kalibrasi standar SPL ~94 dB ref point.
    """
    if rms <= 1e-5:
        return 30.0
    db = 20.0 * math.log10(rms) + 94.0
    return float(max(30.0, min(105.0, db)))


def extract_spectral_vocal_ratio(audio_data, sample_rate):
    """
    Data Processing & Feature Extraction:
    Menghitung proporsi energi spektral pada rentang pita frekuensi suara manusia
    (vocal formant band: 300 Hz - 3400 Hz) menggunakan FFT (Fast Fourier Transform).
    Suara percakapan / obrolan manusia memiliki konsentrasi energi dominan pada rentang ini.
    """
    n = len(audio_data)
    if n == 0:
        return 0.0

    # Fast Fourier Transform (real-valued)
    fft_vals = np.abs(np.fft.rfft(audio_data))
    freqs = np.fft.rfftfreq(n, 1.0 / sample_rate)

    # Total energi spektral
    total_energy = np.sum(fft_vals ** 2)
    if total_energy <= 1e-9:
        return 0.0

    # Mask pita frekuensi vokal manusia (300 - 3400 Hz)
    vocal_mask = (freqs >= VOCAL_FREQ_MIN) & (freqs <= VOCAL_FREQ_MAX)
    vocal_energy = np.sum(fft_vals[vocal_mask] ** 2)

    vocal_ratio = float((vocal_energy / total_energy) * 100.0)
    return min(100.0, max(0.0, vocal_ratio))


def calculate_zcr(audio_data):
    """
    Menghitung Zero-Crossing Rate (ZCR) dari sinyal audio.
    Sinyal suara percakapan manusia umumnya memiliki ZCR moderat (0.04 - 0.25),
    berbeda dengan dengungan AC (ZCR sangat rendah) atau desis/gesekan (ZCR sangat tinggi).
    """
    if len(audio_data) < 2:
        return 0.0
    zero_crossings = np.sum(np.abs(np.diff(np.signbit(audio_data))))
    return float(zero_crossings / len(audio_data))


def classify_chatter_noise(db, vocal_ratio, zcr):
    """
    Algoritma Klasifikasi Obrolan Kelas (Decision Tree & Multi-Feature Rule Classifier)
    Fokus Khusus: Kebisingan Saat Mengobrol (Classroom Chatter Noise Detection)

    Parameter Masukan:
    - db: Tingkat tekanan suara (dB SPL)
    - vocal_ratio: Persentase energi pada pita suara vokal manusia (%)
    - zcr: Zero Crossing Rate sinyal

    Keluaran:
    - status: Deskripsi status kondisi ruangan
    - classification: Label kategori machine learning / rule
    - chatter_detected: Boolean apakah terdeteksi obrolan manusia
    - chatter_prob: Estimasi probabilitas bahwa kebisingan berasal dari obrolan (%)
    - alert: Boolean indikator bahaya/kebisingan melebihi batas aman
    """
    # 1. Kondisi Kelas Sangat Hening (Di bawah threshold bicara)
    if db < 52.0:
        return {
            "status": "SANGAT TENANG (HENING)",
            "classification": "HENING",
            "chatter_detected": False,
            "chatter_prob": round(max(2.0, vocal_ratio * 0.15), 1),
            "alert": False
        }

    # 2. Kondisi Bising Bukan Obrolan (misal mesin AC, dengung, gesekan frekuensi tinggi)
    # Jika dB tinggi tetapi rasio energi pita vokal rendah (< 42%)
    if vocal_ratio < 42.0 and db >= 65.0:
        return {
            "status": "BISING LAIN (BUKAN OBROLAN)",
            "classification": "BISING_NON_OBROLAN",
            "chatter_detected": False,
            "chatter_prob": round(vocal_ratio * 0.3, 1),
            "alert": db >= THRESHOLD_CHATTER_DB
        }

    # 3. Hitung estimasi probabilitas suara obrolan
    # Kombinasi vocal_ratio (bobot 70%) dan kesesuaian ZCR (bobot 30%)
    zcr_fitness = 100.0 - min(100.0, abs(zcr - 0.12) * 500.0)
    chatter_prob = (vocal_ratio * 0.7) + (max(0.0, zcr_fitness) * 0.3)
    chatter_prob = round(min(98.5, max(15.0, chatter_prob)), 1)

    # 4. Evaluasi Tingkat Kebisingan Obrolan
    if db < 65.0:
        return {
            "status": "OBROLAN KONDUSIF (BISIK / TENANG)",
            "classification": "OBROLAN_KONDUSIF",
            "chatter_detected": True,
            "chatter_prob": chatter_prob,
            "alert": False
        }
    elif db < THRESHOLD_CHATTER_DB:
        return {
            "status": "OBROLAN AKTIF / DISKUSI",
            "classification": "OBROLAN_DISKUSI",
            "chatter_detected": True,
            "chatter_prob": chatter_prob,
            "alert": False
        }
    else:
        return {
            "status": "OBROLAN SANGAT BISING / GADUH",
            "classification": "OBROLAN_GADUH",
            "chatter_detected": True,
            "chatter_prob": chatter_prob,
            "alert": True
        }


def generate_simulated_audio(iteration):
    """
    Menghasilkan data audio sintetis untuk simulasi jika mikrofon fisik tidak tersedia.
    Mensimulasikan skenario: Hening -> Obrolan Ringan -> Obrolan Diskusi -> Obrolan Gaduh/Bising.
    """
    t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
    phase = (iteration // 6) % 4

    if phase == 0:
        # Skenario 1: Kelas Hening (Kebisingan dasar rendah)
        noise = np.random.normal(0, 0.002, len(t))
        return noise, "Kelas Hening"
    elif phase == 1:
        # Skenario 2: Obrolan Ringan / Bisik-bisik (Frekuensi 400 - 900 Hz vokal)
        speech_synth = (0.015 * np.sin(2 * np.pi * 500 * t) +
                        0.010 * np.sin(2 * np.pi * 850 * t) +
                        0.008 * np.sin(2 * np.pi * 1400 * t))
        envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 3.0 * t)
        noise = np.random.normal(0, 0.004, len(t))
        return (speech_synth * envelope + noise), "Obrolan Ringan"
    elif phase == 2:
        # Skenario 3: Obrolan Diskusi Kelas (Frekuensi vokal dominan)
        speech_synth = (0.035 * np.sin(2 * np.pi * 450 * t) +
                        0.025 * np.sin(2 * np.pi * 750 * t) +
                        0.020 * np.sin(2 * np.pi * 1200 * t) +
                        0.015 * np.sin(2 * np.pi * 2200 * t))
        envelope = 0.6 + 0.4 * np.sin(2 * np.pi * 4.0 * t)
        noise = np.random.normal(0, 0.007, len(t))
        return (speech_synth * envelope + noise), "Obrolan Diskusi"
    else:
        # Skenario 4: Obrolan Sangat Bising / Siswa Ramai Ricuh
        speech_synth = (0.085 * np.sin(2 * np.pi * 400 * t) +
                        0.065 * np.sin(2 * np.pi * 700 * t) +
                        0.050 * np.sin(2 * np.pi * 1100 * t) +
                        0.040 * np.sin(2 * np.pi * 2100 * t) +
                        0.030 * np.sin(2 * np.pi * 2800 * t))
        envelope = 0.7 + 0.3 * np.sin(2 * np.pi * 5.0 * t)
        noise = np.random.normal(0, 0.012, len(t))
        return (speech_synth * envelope + noise), "Obrolan Sangat Gaduh"


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("==================================================================")
    print(" [NODE 2 / HP 2] KLASIFIKASI KEBISINGAN OBROLAN RUANG KELAS       ")
    print(" Proyek: Pemantau Kebisingan Ruang Kelas (IoT - Anggota 2)       ")
    print("==================================================================")
    print(f" [*] Device ID    : {DEVICE_ID} ({DEVICE_NAME})")
    print(f" [*] Lokasi       : {LOCATION}")
    print(f" [*] Broker MQTT  : {MQTT_BROKER}:{MQTT_PORT}")
    print(f" [*] Topik Utama  : {TOPIC_TELEMETRY_NODE2}")
    print(f" [*] Topik HP2    : {TOPIC_TELEMETRY_HP2}")
    print(f" [*] Fitur AI     : FFT Vocal Band Energy (300-3400 Hz) + ZCR + Rule")
    print(f" [*] Mode Mic     : {'Hardware sounddevice (Fisik)' if HAS_SOUNDDEVICE else 'Simulasi Skenario Audio Otomatis'}")
    print("------------------------------------------------------------------")

    # Inisialisasi client MQTT dengan kompatibilitas Paho v1 / v2
    client_id = f"HP2_Edge_{int(time.time())}"
    try:
        # Paho MQTT v2.x
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    except (AttributeError, TypeError):
        # Paho MQTT v1.x fallback
        client = mqtt.Client(client_id=client_id)

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()
        print(f"[OK] Berhasil terkoneksi ke MQTT Broker: {MQTT_BROKER}\n", flush=True)
    except Exception as e:
        print(f"[ERR] Gagal terhubung ke MQTT Broker: {e}", flush=True)
        return

    iteration = 0
    try:
        while True:
            iteration += 1

            if HAS_SOUNDDEVICE:
                try:
                    # Merekam 1 detik audio mono dari mikrofon perangkat
                    recording = sd.rec(
                        int(DURATION * SAMPLE_RATE),
                        samplerate=SAMPLE_RATE,
                        channels=1,
                        dtype='float32'
                    )
                    sd.wait()
                    audio_data = recording.flatten()
                    scenario_tag = "Live Mic"
                except Exception as mic_err:
                    print(f"[WARN] Error baca mic: {mic_err}. Beralih ke audio simulasi...", flush=True)
                    audio_data, scenario_tag = generate_simulated_audio(iteration)
            else:
                # Simulasi jika library audio fisik belum tersedia
                audio_data, scenario_tag = generate_simulated_audio(iteration)
                time.sleep(DURATION)

            # Ekstraksi Fitur Akustik
            rms = calculate_rms(audio_data)
            peak = float(np.max(np.abs(audio_data)))
            db = rms_to_db(rms)
            vocal_ratio = extract_spectral_vocal_ratio(audio_data, SAMPLE_RATE)
            zcr = calculate_zcr(audio_data)

            # Klasifikasi Kebisingan Obrolan
            decision = classify_chatter_noise(db, vocal_ratio, zcr)

            # Susun Payload Telemetri (Kompatibel penuh dengan standar HP 1 & Node 1)
            payload = {
                "device_id": DEVICE_ID,
                "device_name": DEVICE_NAME,
                "device_type": "Smartphone_Or_PC_Mic_Node2",
                "location": LOCATION,
                "rms": round(rms, 4),
                "peak": round(peak, 4),
                "db": round(db, 1),
                "threshold_db": THRESHOLD_CHATTER_DB,
                "chatter_detected": decision["chatter_detected"],
                "vocal_energy_ratio": round(vocal_ratio, 1),
                "chatter_prob": decision["chatter_prob"],
                "classification": decision["classification"],
                "status": decision["status"],
                "alert": decision["alert"],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            payload_json = json.dumps(payload)

            # Publish ke dua topik untuk kemudahan integrasi tim:
            # 1. Standar Node 2 (`kelas/kebisingan/node2/telemetry`)
            # 2. Standar HP 2 (`kelas/kebisingan/hp2/telemetry`)
            client.publish(TOPIC_TELEMETRY_NODE2, payload_json)
            client.publish(TOPIC_TELEMETRY_HP2, payload_json)

            # Jika terjadi kebisingan obrolan ekstrem melebihi threshold, kirim alarm
            if decision["alert"]:
                alert_payload = {
                    "device_id": DEVICE_ID,
                    "location": LOCATION,
                    "event": "CHATTER_NOISE_EXCEEDED",
                    "db_level": round(db, 1),
                    "chatter_prob": decision["chatter_prob"],
                    "message": f"Peringatan: Kebisingan obrolan di {LOCATION} mencapai {round(db, 1)} dB!",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                client.publish(TOPIC_ALERT, json.dumps(alert_payload))

            # Cetak Log Informasi Realtime
            alert_symbol = "[ALERT!]" if decision["alert"] else "[NORMAL]"
            print(f"[{time.strftime('%H:%M:%S')}] {alert_symbol} | "
                  f"dB: {db:5.1f} | "
                  f"Vokal: {vocal_ratio:4.1f}% | "
                  f"Prob Obrolan: {decision['chatter_prob']:4.1f}% | "
                  f"Status: {decision['status']} ({scenario_tag})", flush=True)

    except KeyboardInterrupt:
        print("\n[!] Program Edge HP 2 dihentikan pengguna.")
    finally:
        client.loop_stop()
        client.disconnect()
        print("[*] Koneksi MQTT ditutup.")


if __name__ == "__main__":
    main()
