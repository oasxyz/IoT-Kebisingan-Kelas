"""
Multi-Node Edge Simulator untuk Sistem Pemantau Kebisingan Kelas (Kelompok 7).
Mensimulasikan Edge 1 (Depan Kelas) dan Edge 2 (Belakang Kelas) secara bersamaan ke Cloud MQTT Broker.
Mendukung penerimaan perintah 2 arah (set_threshold, mute) dari Dashboard.
"""

from __future__ import annotations
import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Tambahkan root repo ke sys.path agar bisa import shared
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Windows UTF-8 console output safe guard
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from shared.mqtt_contract import (
    BROKER_HOST,
    BROKER_TCP_PORT,
    TOPIC_ALERT_WILDCARD,
    TOPIC_HP1_TELEMETRY,
    TOPIC_HP2_TELEMETRY,
    TOPIC_NODE1_ALERT,
    TOPIC_NODE1_CONTROL,
    TOPIC_NODE1_TELEMETRY,
    TOPIC_NODE2_ALERT,
    TOPIC_NODE2_CONTROL,
    TOPIC_NODE2_TELEMETRY,
)

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Error: Library paho-mqtt belum terinstall. Jalankan: pip install paho-mqtt")
    sys.exit(1)


# State simulasi
class SimulationState:
    def __init__(self, threshold_db: float = 75.0):
        self.threshold_db = threshold_db
        self.is_muted = False
        self.mode = "normal"
        self.running = True


sim_state = SimulationState()


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[SIMULATOR] Terhubung ke Broker MQTT {BROKER_HOST}:{BROKER_TCP_PORT} (rc=0)")
        client.subscribe([(TOPIC_NODE1_CONTROL, 0), (TOPIC_NODE2_CONTROL, 0)])
        print(f"[SIMULATOR] Subscribed ke perintah kontrol:")
        print(f"            - {TOPIC_NODE1_CONTROL}")
        print(f"            - {TOPIC_NODE2_CONTROL}")
    else:
        print(f"[SIMULATOR] Gagal konek MQTT, rc={rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        print(f"\n[KONTROL DITERIMA] Topik: {msg.topic}")
        print(f"                   Isi: {json.dumps(payload)}")

        if "set_threshold" in payload:
            old_th = sim_state.threshold_db
            sim_state.threshold_db = float(payload["set_threshold"])
            print(f"[KONTROL] Ambang batas (threshold) diubah: {old_th} dB -> {sim_state.threshold_db} dB")

        if "mute" in payload:
            sim_state.is_muted = bool(payload["mute"])
            print(f"[KONTROL] Status Mute Alarm: {'AKTIF (Senyap)' if sim_state.is_muted else 'NONAKTIF (Bunyi)'}")

        if "mode" in payload:
            sim_state.mode = str(payload["mode"])
            print(f"[KONTROL] Mode kelas diubah ke: {sim_state.mode}")

    except Exception as e:
        print(f"[SIMULATOR ERROR] Gagal memproses perintah: {e}")


def generate_node1_payload(phase: int, threshold_db: float) -> dict:
    """Simulasi data Edge 1 (Depan Kelas - Level dB umum & Moving Average)."""
    if phase == 1:  # Hening
        db_instant = round(random.uniform(38.0, 46.0), 1)
        rms = round(random.uniform(0.005, 0.015), 4)
    elif phase == 2:  # Dosen Menjelaskan di Depan
        db_instant = round(random.uniform(62.0, 71.0), 1)
        rms = round(random.uniform(0.035, 0.065), 4)
    elif phase == 3:  # Siswa Mengobrol di Belakang (Depan Sedang)
        db_instant = round(random.uniform(55.0, 63.0), 1)
        rms = round(random.uniform(0.020, 0.040), 4)
    else:  # Kelas Sangat Gaduh
        db_instant = round(random.uniform(76.0, 84.0), 1)
        rms = round(random.uniform(0.080, 0.150), 4)

    db_smooth = round(db_instant + random.uniform(-0.8, 0.8), 1)
    is_alert = (db_smooth >= threshold_db)

    status = "SANGAT TENANG" if db_smooth < 55 else ("KONDUSIF" if db_smooth < threshold_db else "SANGAT BISING")

    return {
        "device_id": "NODE_01",
        "device_name": "ESP32_Edge_Sound_Sensor",
        "location": "Ruang_Kelas_Depan",
        "raw_adc": int(random.uniform(1200, 3100)),
        "peak_to_peak": int(random.uniform(150, 850)),
        "rms": rms,
        "db_instant": db_instant,
        "db_smooth": db_smooth,
        "status": status,
        "threshold_db": threshold_db,
        "alert": is_alert,
        "uptime_ms": int(time.time() * 1000) % 10000000,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def generate_node2_payload(phase: int, threshold_db: float) -> dict:
    """Simulasi data Edge 2 (Belakang Kelas - FFT Vocal Band & Decision Tree AI)."""
    if phase == 1:  # Hening
        db = round(random.uniform(36.0, 44.0), 1)
        vocal_ratio = round(random.uniform(10.0, 22.0), 1)
        classification = "HENING"
        chatter_det = False
        chatter_prob = random.randint(2, 12)
        status = "SANGAT TENANG (HENING)"
    elif phase == 2:  # Dosen Menjelaskan (Belakang Tenang)
        db = round(random.uniform(48.0, 56.0), 1)
        vocal_ratio = round(random.uniform(25.0, 40.0), 1)
        classification = "HENING"
        chatter_det = False
        chatter_prob = random.randint(15, 30)
        status = "KONDUSIF"
    elif phase == 3:  # Siswa Mengobrol di Belakang
        db = round(random.uniform(67.0, 74.5), 1)
        vocal_ratio = round(random.uniform(66.0, 86.0), 1)
        classification = "OBROLAN_DISKUSI"
        chatter_det = True
        chatter_prob = random.randint(70, 88)
        status = "OBROLAN AKTIF / DISKUSI"
    else:  # Obrolan Gaduh / Sangat Bising
        db = round(random.uniform(77.0, 86.0), 1)
        vocal_ratio = round(random.uniform(75.0, 92.0), 1)
        classification = "OBROLAN_GADUH"
        chatter_det = True
        chatter_prob = random.randint(88, 98)
        status = "OBROLAN SANGAT BISING / GADUH"

    is_alert = (db >= threshold_db)

    return {
        "device_id": "HP_02",
        "device_name": "HP2_Edge_Chatter_Classifier",
        "device_type": "Smartphone_Android_Mic_Node2",
        "location": "Ruang_Kelas_Belakang",
        "rms": round(random.uniform(0.015, 0.085), 4),
        "peak": round(random.uniform(0.08, 0.42), 2),
        "db": db,
        "threshold_db": threshold_db,
        "chatter_detected": chatter_det,
        "vocal_energy_ratio": vocal_ratio,
        "chatter_prob": chatter_prob,
        "classification": classification,
        "status": status,
        "alert": is_alert,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="Multi-Node Edge Simulator untuk Kelompok 7 IoT Kebisingan Kelas")
    parser.add_argument("--broker", default=BROKER_HOST, help=f"Host broker MQTT (default: {BROKER_HOST})")
    parser.add_argument("--port", type=int, default=BROKER_TCP_PORT, help=f"Port MQTT (default: {BROKER_TCP_PORT})")
    parser.add_argument("--interval", type=float, default=1.0, help="Interval pengiriman dalam detik (default: 1.0)")
    parser.add_argument("--duration", type=int, default=0, help="Durasi simulasi dalam detik (0 = tanpa batas)")
    parser.add_argument("--phase", type=int, default=0, help="Kunci fase (1=Hening, 2=Dosen, 3=Obrolan, 4=Gaduh, 0=Siklus Otomatis)")
    args = parser.parse_args()

    client_id = f"Simulator_Kelompok7_{random.randint(1000, 9999)}"
    try:
        # Paho MQTT 2.x compatibility
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    except AttributeError:
        client = mqtt.Client(client_id=client_id)

    client.on_connect = on_connect
    client.on_message = on_message

    print("=" * 65)
    print("  SIMULATOR MULTI-NODE EDGE IOT KEBISINGAN RUANG KELAS (KELOMPOK 7)")
    print(f"  Broker: {args.broker}:{args.port}")
    print(f"  Publishing: Node 1 (Depan) & Node 2 (Belakang - Deteksi Obrolan)")
    print("=" * 65)

    try:
        client.connect(args.broker, args.port, keepalive=60)
        client.loop_start()
    except Exception as e:
        print(f"[FATAL] Gagal terhubung ke broker MQTT: {e}")
        sys.exit(1)

    start_time = time.time()
    tick = 0

    phase_names = {
        1: "✨ FASE 1: KELAS SANGAT TENANG (UJIAN/BELAJAR MANDIRI)",
        2: "👨‍🏫 FASE 2: DOSEN/GURU MENJELASKAN DI DEPAN KELAS",
        3: "🗣️ FASE 3: SISWA DI BELAKANG MULAI MENGOBROL",
        4: "🚨 FASE 4: KELAS SANGAT GADUH MELEBIHI THRESHOLD (ALARM)",
    }

    try:
        while True:
            tick += 1
            if args.phase in (1, 2, 3, 4):
                current_phase = args.phase
            else:
                # Siklus otomatis setiap 12 detik berganti fase
                current_phase = ((tick // 12) % 4) + 1

            if tick % 12 == 1 or args.phase != 0:
                print(f"\n>>> {phase_names[current_phase]} (Threshold: {sim_state.threshold_db} dB)")

            # 1. Generate & Publish Node 1 (Depan Kelas)
            p1 = generate_node1_payload(current_phase, sim_state.threshold_db)
            p1_json = json.dumps(p1)
            client.publish(TOPIC_NODE1_TELEMETRY, p1_json)
            client.publish(TOPIC_HP1_TELEMETRY, p1_json)

            if p1["alert"]:
                alert1 = {
                    "device_id": "NODE_01",
                    "location": "Ruang_Kelas_Depan",
                    "event": "NOISE_EXCEEDED",
                    "db_level": p1["db_smooth"],
                    "message": "Peringatan: Tingkat kebisingan ruang kelas depan melebihi batas aman!",
                    "timestamp": p1["timestamp"],
                }
                if not sim_state.is_muted:
                    client.publish(TOPIC_NODE1_ALERT, json.dumps(alert1))

            # 2. Generate & Publish Node 2 (Belakang Kelas - Dual Publish mirroring Edge 2)
            p2 = generate_node2_payload(current_phase, sim_state.threshold_db)
            p2_json = json.dumps(p2)
            client.publish(TOPIC_NODE2_TELEMETRY, p2_json)
            client.publish(TOPIC_HP2_TELEMETRY, p2_json)

            if p2["alert"]:
                alert2 = {
                    "device_id": "HP_02",
                    "location": "Ruang_Kelas_Belakang",
                    "event": "CHATTER_NOISE_EXCEEDED",
                    "db_level": p2["db"],
                    "chatter_prob": p2["chatter_prob"],
                    "message": f"Peringatan: Kebisingan obrolan di Ruang_Kelas_Belakang mencapai {p2['db']} dB!",
                    "timestamp": p2["timestamp"],
                }
                if not sim_state.is_muted:
                    client.publish(TOPIC_NODE2_ALERT, json.dumps(alert2))

            print(
                f"[TICK #{tick:03d}] Node 1 (Depan): {p1['db_smooth']:4.1f} dB | "
                f"Node 2 (Belakang): {p2['db']:4.1f} dB (Vokal: {p2['vocal_energy_ratio']:4.1f}%, Obrolan: {p2['chatter_prob']:2d}%) | "
                f"Status: {p2['classification']}"
            )

            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                print(f"\n[SIMULATOR] Durasi {args.duration} detik tercapai. Selesai.")
                break

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n[SIMULATOR] Dihentikan oleh pengguna (Ctrl+C).")
    finally:
        client.loop_stop()
        client.disconnect()
        print("[SIMULATOR] Koneksi MQTT ditutup dengan aman.")


if __name__ == "__main__":
    main()
