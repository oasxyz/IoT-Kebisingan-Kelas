"""
Edge Device HP 1 (Python / Laptop / Termux / Pydroid 3)
Membaca sinyal audio mikrofon, menghitung RMS dan dB, lalu mengirim telemetry ke broker MQTT.
"""

import time
import math
import json
import numpy as np
import paho.mqtt.client as mqtt

# Jika menggunakan sounddevice (opsional, jika modul terinstall)
try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
TOPIC_TELEMETRY = "kelas/kebisingan/hp1/telemetry"

SAMPLE_RATE = 44100
DURATION = 1.0 # baca tiap 1 detik

def calculate_rms(audio_data):
    """Menghitung Root Mean Square (RMS) dari array audio"""
    return np.sqrt(np.mean(audio_data**2))

def rms_to_db(rms):
    """Konversi RMS ke estimasi level dB SPL"""
    if rms <= 0.00001:
        return 30.0
    db = 20.0 * math.log10(rms) + 94.0 # Kalibrasi standar 94 dB SPL
    return max(30.0, min(100.0, db))

def main():
    print("==========================================")
    print(" EDGE DEVICE HP 1 - AUDIO RMS TO MQTT ")
    print("==========================================")

    client = mqtt.Client()
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        print(f"[OK] Terhubung ke MQTT Broker: {MQTT_BROKER}")
    except Exception as e:
        print(f"[ERR] Gagal terhubung ke MQTT: {e}")
        return

    print("Memulai pembacaan audio mikrofon...")
    try:
        while True:
            if HAS_SOUNDDEVICE:
                # Rekam 1 detik audio mono
                recording = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
                sd.wait()
                audio_mono = recording.flatten()
                rms = float(calculate_rms(audio_mono))
            else:
                # Mode simulasi jika sounddevice belum terinstall
                rms = float(np.random.uniform(0.005, 0.08))
                time.sleep(1)

            db = float(rms_to_db(rms))

            if db < 55.0:
                status = "SANGAT TENANG"
                alert = False
            elif db < 75.0:
                status = "KONDUSIF"
                alert = False
            elif db < 85.0:
                status = "RAMAI / PERINGATAN"
                alert = True
            else:
                status = "SANGAT BISING"
                alert = True

            payload = {
                "device_id": "HP_01",
                "device_type": "Smartphone_Or_PC_Mic",
                "rms": round(rms, 4),
                "db": round(db, 1),
                "status": status,
                "alert": alert,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            client.publish(TOPIC_TELEMETRY, json.dumps(payload))
            print(f"[TELEMETRY] RMS: {rms:.4f} | dB: {db:.1f} | Status: {status}")

    except KeyboardInterrupt:
        print("\nProgram dihentikan.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()

