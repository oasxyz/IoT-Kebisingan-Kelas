"""
Dashboard Web Server & Room Fusion MQTT Service (Kelompok 7).
Menjalankan HTTP Server lokal untuk menyajikan Web Dashboard & Web Edge Microphone,
sekaligus menjalankan background service MQTT yang memproses Normalisasi & Room Fusion.
"""

from __future__ import annotations
import argparse
import http.server
import json
import os
import socket
import socketserver
import sys
import threading
import time
from pathlib import Path

# Setup path impor shared
REPO_ROOT = Path(__file__).resolve().parent
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
    TOPIC_ROOM_STATUS,
    TOPIC_TELEMETRY_WILDCARD,
    NormalizedTelemetry,
    TelemetryDeduplicator,
    normalize_telemetry,
)
from shared.room_fusion import RoomAcousticState, fuse_room_state

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("[PERINGATAN] Library paho-mqtt belum terinstall. Fitur bridge MQTT terminal dinonaktifkan.")
    mqtt = None


def get_local_ip() -> str:
    """Mendapatkan alamat IP lokal perangkat dalam jaringan WiFi/LAN."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler yang mengarahkan root '/' ke '/dashboard/index.html'."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO_ROOT), **kwargs)

    def do_GET(self):
        if self.path in ("/", "/dashboard", "/dashboard/"):
            self.path = "/dashboard/index.html"
        elif self.path == "/favicon.ico":
            # Beri respon 204 (No Content) langsung agar browser tidak error 404
            self.send_response(204)
            self.end_headers()
            return
        return super().do_GET()

    def log_message(self, format, *args):
        # Format pesan log secara aman untuk semua tipe request (string maupun HTTPStatus)
        try:
            msg = format % args
            # Sembunyikan log sukses 200 / 304 / 204 agar terminal tetap rapi
            if any(code in msg for code in (" 200 ", " 304 ", " 204 ", "200 -", "304 -", "204 -")):
                return
            if "favicon.ico" in msg:
                return
            sys.stderr.write(f"[{self.log_date_time_string()}] {msg}\n")
        except Exception:
            pass


class MqttRoomFusionWorker:
    """Background worker yang memproses telemetri MQTT dan mempublikasikan status ruangan."""

    def __init__(self, broker: str = BROKER_HOST, port: int = BROKER_TCP_PORT):
        self.broker = broker
        self.port = port
        self.dedup = TelemetryDeduplicator()
        self.last_node1: NormalizedTelemetry | None = None
        self.last_node2: NormalizedTelemetry | None = None
        self.current_state: RoomAcousticState | None = None
        self.client = None
        self.running = False
        self.threshold_db = 75.0

    def start(self):
        if mqtt is None:
            return

        client_id = f"DashboardServer_Fusion_{os.getpid()}"
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
        except AttributeError:
            self.client = mqtt.Client(client_id=client_id)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            self.running = True
        except Exception as e:
            print(f"[MQTT SERVICE] Gagal terhubung ke broker {self.broker}: {e}")

    def stop(self):
        if self.client and self.running:
            self.client.loop_stop()
            self.client.disconnect()
            self.running = False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            client.subscribe([(TOPIC_TELEMETRY_WILDCARD, 0), (TOPIC_ALERT_WILDCARD, 0)])
            print(f"[MQTT SERVICE] Subscribed ke {TOPIC_TELEMETRY_WILDCARD} & {TOPIC_ALERT_WILDCARD}")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload_str = msg.payload.decode("utf-8", errors="ignore")

        # Jika topik alarm
        if "alert" in topic:
            try:
                alert_json = json.loads(payload_str)
                print(f"\n🚨 [MQTT ALARM DETEKSI] Topik: {topic} | Pesan: {alert_json.get('message', payload_str)}")
            except Exception:
                pass
            return

        # Normalisasi Telemetri
        try:
            norm = normalize_telemetry(topic, payload_str)
            if not self.dedup.should_accept(norm):
                return  # Abaikan duplikasi dual-publish

            if norm.slot == "node1":
                self.last_node1 = norm
            else:
                self.last_node2 = norm

            # Update threshold aktif jika ada di telemetri
            self.threshold_db = norm.threshold_db

            # Hitung Room Fusion
            state = fuse_room_state(self.last_node1, self.last_node2, self.threshold_db)
            self.current_state = state

            # Publish status agregasi ruangan
            status_json = json.dumps(state.to_dict())
            client.publish(TOPIC_ROOM_STATUS, status_json)

        except Exception as e:
            # Toleransi payload anomali
            pass


def run_server(port: int = 8000, enable_mqtt: bool = True):
    local_ip = get_local_ip()

    worker = None
    if enable_mqtt and mqtt is not None:
        worker = MqttRoomFusionWorker()
        worker.start()

    handler = CustomHTTPRequestHandler

    print("\n" + "=" * 70)
    print("  🚀 WEB DASHBOARD & SERVER IOT KEBISINGAN RUANG KELAS (KELOMPOK 7)")
    print("=" * 70)
    print(f"  Akses Web Dashboard Utama:")
    print(f"  👉 Lokal (PC Ini)   : http://localhost:{port}/dashboard/index.html")
    print(f"  👉 Jaringan WiFi/LAN: http://{local_ip}:{port}/dashboard/index.html")
    print("-" * 70)
    print(f"  Akses Web Edge Microphone (Buka dari Chrome Smartphone):")
    print(f"  📱 HP 1 (Depan)    : http://{local_ip}:{port}/client_mobile_hp1/hp1_web_mic.html")
    print(f"  📱 HP 2 (Belakang) : http://{local_ip}:{port}/client_mobile_hp2/hp2_web_mic.html")
    print("=" * 70)
    print("  Tekan Ctrl+C untuk menghentikan server.\n")

    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER] Menghentikan HTTP Server...")
    finally:
        if worker:
            worker.stop()
        print("[SERVER] Selesai. Selamat bertugas!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Server Web Dashboard IoT Kebisingan Kelas (Kelompok 7)")
    parser.add_argument("--port", type=int, default=8000, help="Port HTTP Server (default: 8000)")
    parser.add_argument("--no-mqtt", action="store_true", help="Nonaktifkan background worker MQTT")
    args = parser.parse_args()

    run_server(port=args.port, enable_mqtt=not args.no_mqtt)
