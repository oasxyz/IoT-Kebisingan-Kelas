"""
Kontrak MQTT, Topik Standar, Normalizer JSON, dan Deduplikasi untuk Sistem Pemantau Kebisingan Kelas.
Kelompok 7 - IoT Multikomunikasi.
"""

from __future__ import annotations
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

# ==========================================
# KONFIGURASI GLOBAL BROKER MQTT
# ==========================================
BROKER_HOST = "broker.hivemq.com"
BROKER_TCP_PORT = 1883
BROKER_TLS_PORT = 8883
BROKER_WS_PORT = 8884
BROKER_WS_PATH = "/mqtt"
BROKER_WSS_URL = f"wss://{BROKER_HOST}:{BROKER_WS_PORT}{BROKER_WS_PATH}"

# ==========================================
# STRUKTUR TOPIK MQTT STANDAR TIM (ISOLASI TOPIK UNIK)
# ==========================================
# Telemetri
TOPIC_NODE1_TELEMETRY = "if/kebisingan/kelas/node1/telemetry"
TOPIC_HP1_TELEMETRY = "if/kebisingan/kelas/hp1/telemetry"
TOPIC_NODE2_TELEMETRY = "if/kebisingan/kelas/node2/telemetry"
TOPIC_HP2_TELEMETRY = "if/kebisingan/kelas/hp2/telemetry"
TOPIC_TELEMETRY_WILDCARD = "if/kebisingan/kelas/+/telemetry"

# Alarm
TOPIC_NODE1_ALERT = "if/kebisingan/kelas/node1/alert"
TOPIC_NODE2_ALERT = "if/kebisingan/kelas/node2/alert"
TOPIC_ALERT_WILDCARD = "if/kebisingan/kelas/+/alert"

# Kontrol 2 Arah (Dashboard -> Edge Nodes)
TOPIC_NODE1_CONTROL = "if/kebisingan/kelas/node1/control"
TOPIC_NODE2_CONTROL = "if/kebisingan/kelas/node2/control"
TOPIC_GLOBAL_CONTROL = "if/kebisingan/kelas/control"

# Status Agregasi Ruangan (Room Fusion)
TOPIC_ROOM_STATUS = "if/kebisingan/kelas/room/status"

# Default ambang kebisingan (dB SPL)
DEFAULT_THRESHOLD_DB = 75.0


@dataclass
class NormalizedTelemetry:
    """Struktur telemetri seragam hasil normalisasi untuk Dashboard & Analisis."""
    slot: str  # "node1" (Depan Kelas) atau "node2" (Belakang Kelas)
    topic: str
    device_id: str
    device_name: str
    location: str
    db: float
    db_instant: float
    rms: float
    peak: float
    threshold_db: float
    status: str
    alert: bool
    chatter_detected: bool
    vocal_energy_ratio: float
    chatter_prob: int
    classification: str
    timestamp: str
    raw_payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Konversi ke dictionary murni."""
        res = asdict(self)
        del res["raw_payload"]
        return res

    def to_json(self) -> str:
        """Serialisasi ke JSON string."""
        return json.dumps(self.to_dict())


def determine_slot(topic: str, raw: Dict[str, Any]) -> str:
    """
    Menentukan apakah telemetri berasal dari Partisi Depan (node1) atau Belakang (node2).
    """
    topic_lower = topic.lower()
    dev_id = str(raw.get("device_id", "")).upper()
    loc = str(raw.get("location", "")).lower()

    if "node1" in topic_lower or "hp1" in topic_lower or dev_id in ("NODE_01", "HP_01") or "depan" in loc:
        return "node1"
    if "node2" in topic_lower or "hp2" in topic_lower or dev_id in ("NODE_02", "HP_02") or "belakang" in loc:
        return "node2"
    return "node1" if "1" in topic_lower else "node2"


def normalize_telemetry(topic: str, raw_input: Union[Dict[str, Any], str, bytes]) -> NormalizedTelemetry:
    """
    Menyeragamkan struktur data dari berbagai sumber:
    - Node 1 Wokwi ESP32 (`src/main.cpp`): db_smooth, db_instant, peak_to_peak
    - Node 1 HP (`hp1_web_mic.html` / `hp1_mic_python.py`): db, peak, rms
    - Node 2 HP (`hp2_web_mic.html` / `hp2_mic_python.py`): db, peak, vocal_energy_ratio, chatter_prob, classification
    """
    if isinstance(raw_input, (str, bytes)):
        try:
            raw = json.loads(raw_input)
        except Exception:
            raw = {}
    elif isinstance(raw_input, dict):
        raw = raw_input
    else:
        raw = {}

    slot = determine_slot(topic, raw)
    is_node1 = (slot == "node1")

    # 1. Desibel (dB)
    # Wokwi ESP32 mengirim `db_smooth` dan `db_instant`. HP mengirim `db`.
    raw_db = raw.get("db")
    raw_smooth = raw.get("db_smooth")
    raw_instant = raw.get("db_instant")

    if raw_db is not None:
        db_val = float(raw_db)
    elif raw_smooth is not None:
        db_val = float(raw_smooth)
    elif raw_instant is not None:
        db_val = float(raw_instant)
    else:
        db_val = 40.0

    inst_val = float(raw_instant if raw_instant is not None else db_val)

    # 2. RMS & Peak
    rms_val = float(raw.get("rms", 0.0))
    raw_peak = raw.get("peak")
    raw_p2p = raw.get("peak_to_peak")

    if raw_peak is not None:
        peak_val = float(raw_peak)
    elif raw_p2p is not None:
        # Konversi ADC 12-bit (0-4095) ESP32 menjadi skala ternormalisasi 0.0 s.d. 1.0
        peak_val = round(float(raw_p2p) / 4095.0, 3)
    else:
        peak_val = 0.0

    # 3. Metadata Perangkat
    default_dev_id = "NODE_01" if is_node1 else "HP_02"
    device_id = str(raw.get("device_id") or default_dev_id)

    default_dev_name = "ESP32_Edge_Sound_Sensor" if is_node1 else "HP2_Edge_Chatter_Classifier"
    device_name = str(raw.get("device_name") or default_dev_name)

    default_loc = "Ruang_Kelas_Depan" if is_node1 else "Ruang_Kelas_Belakang"
    location = str(raw.get("location") or default_loc)

    threshold_db = float(raw.get("threshold_db") or DEFAULT_THRESHOLD_DB)
    status_str = str(raw.get("status") or ("KONDUSIF" if db_val < threshold_db else "SANGAT BISING"))
    alert_flag = bool(raw.get("alert") or (db_val >= threshold_db))

    # 4. Fitur AI & FFT Pita Suara Vokal (Khusus Edge 2)
    chatter_det = bool(raw.get("chatter_detected", False))
    vocal_ratio = float(raw.get("vocal_energy_ratio", 0.0))
    chatter_prob = int(raw.get("chatter_prob", 0))
    classification = str(raw.get("classification") or ("SENSOR_DB_UMUM" if is_node1 else "HENING"))

    # 5. Timestamp
    raw_ts = raw.get("timestamp")
    if not raw_ts:
        raw_ts = datetime.now(timezone.utc).isoformat()
    else:
        raw_ts = str(raw_ts)

    return NormalizedTelemetry(
        slot=slot,
        topic=topic,
        device_id=device_id,
        device_name=device_name,
        location=location,
        db=round(db_val, 1),
        db_instant=round(inst_val, 1),
        rms=round(rms_val, 4),
        peak=round(peak_val, 3),
        threshold_db=round(threshold_db, 1),
        status=status_str,
        alert=alert_flag,
        chatter_detected=chatter_det,
        vocal_energy_ratio=round(vocal_ratio, 1),
        chatter_prob=max(0, min(100, chatter_prob)),
        classification=classification,
        timestamp=raw_ts,
        raw_payload=raw,
    )


class TelemetryDeduplicator:
    """
    Menyaring pesan kembar dari Edge 2 yang mem-publish JSON identik
    ke kedua topik sekaligus ('if/kebisingan/kelas/node2/telemetry' dan 'if/kebisingan/kelas/hp2/telemetry').
    """

    def __init__(self, window_seconds: float = 0.40):
        self.window_seconds = window_seconds
        self._last_seen: Dict[str, Dict[str, Any]] = {
            "node1": {"sig": "", "time": 0.0, "dev": "", "ts": ""},
            "node2": {"sig": "", "time": 0.0, "dev": "", "ts": ""},
        }

    def should_accept(self, item: NormalizedTelemetry, current_time: Optional[float] = None) -> bool:
        slot = item.slot
        now = current_time if current_time is not None else time.monotonic()
        prev = self._last_seen.get(slot, {"sig": "", "time": 0.0, "dev": "", "ts": ""})

        # Signature unik: gabungan device_id, timestamp asli, dan nilai desibel
        sig = f"{item.device_id}|{item.timestamp}|{item.db}"

        # 1. Jika signature persis sama -> duplikat murni!
        if prev["sig"] == sig:
            return False

        # 2. Jika timestamp sama dari device_id yang sama (paket kembar beda topik)
        if item.timestamp and prev["dev"] == item.device_id and prev["ts"] == item.timestamp:
            return False

        # 3. Jika tanpa timestamp unik dan dari device_id yang sama masuk dalam window_seconds (< 400ms)
        if prev["dev"] == item.device_id and (now - prev["time"]) < self.window_seconds:
            # Jika timestamp berbeda jelas, ini adalah sampel pembacaan baru
            if prev["ts"] and item.timestamp and prev["ts"] != item.timestamp:
                pass  # Lolos karena pembacaan baru dengan timestamp berbeda
            else:
                return False

        # Lolos filter
        self._last_seen[slot] = {
            "sig": sig,
            "time": now,
            "dev": item.device_id,
            "ts": item.timestamp,
        }
        return True


def build_control_payload(
    set_threshold: Optional[float] = None,
    mute: Optional[bool] = None,
    mode: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Menyusun payload perintah kontrol 2 arah yang kompatibel dengan C++ Wokwi ESP32 dan Web Mic.
    Contoh: {"set_threshold": 80.0, "mute": true, "mode": "ujian"}
    """
    payload: Dict[str, Any] = {}
    if set_threshold is not None:
        payload["set_threshold"] = round(float(set_threshold), 1)
    if mute is not None:
        payload["mute"] = bool(mute)
    if mode is not None:
        payload["mode"] = str(mode)
    payload["timestamp"] = datetime.now(timezone.utc).isoformat()
    return payload


def build_control_json(
    set_threshold: Optional[float] = None,
    mute: Optional[bool] = None,
    mode: Optional[str] = None,
) -> str:
    """Serialisasi payload kontrol ke JSON string."""
    return json.dumps(build_control_payload(set_threshold, mute, mode))
