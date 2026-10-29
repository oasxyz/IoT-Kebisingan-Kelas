"""
Unit Tests untuk Kontrak MQTT, Normalizer JSON, Deduplikasi, dan Room Fusion Engine.
Kelompok 7 - IoT Kebisingan Ruang Belajar / Ruang Kelas.
"""

import json
import unittest
from shared.mqtt_contract import (
    DEFAULT_THRESHOLD_DB,
    TelemetryDeduplicator,
    build_control_json,
    build_control_payload,
    normalize_telemetry,
)
from shared.room_fusion import fuse_room_state


class TestMqttContractAndNormalizer(unittest.TestCase):

    def test_normalize_wokwi_esp32_payload(self):
        """Memverifikasi normalisasi payload dari firmware ESP32 Wokwi (src/main.cpp)."""
        raw_esp32 = {
            "device_id": "NODE_01",
            "device_name": "ESP32_Edge_Sound_Sensor",
            "location": "Ruang_Kelas_Depan",
            "raw_adc": 1820,
            "peak_to_peak": 410,
            "rms": 12.34,
            "db_instant": 64.2,
            "db_smooth": 63.8,
            "status": "KONDUSIF",
            "threshold_db": 75.0,
            "alert": False,
            "uptime_ms": 120400,
        }

        norm = normalize_telemetry("kelas/kebisingan/node1/telemetry", raw_esp32)

        self.assertEqual(norm.slot, "node1")
        self.assertEqual(norm.device_id, "NODE_01")
        self.assertEqual(norm.db, 63.8)  # harus memilih db_smooth
        self.assertEqual(norm.db_instant, 64.2)
        self.assertAlmostEqual(norm.peak, round(410 / 4095.0, 3))
        self.assertEqual(norm.status, "KONDUSIF")
        self.assertFalse(norm.alert)
        self.assertEqual(norm.classification, "SENSOR_DB_UMUM")

    def test_normalize_hp1_web_mic_payload(self):
        """Memverifikasi normalisasi payload dari HP 1 Web Mic (client_mobile_hp1/hp1_web_mic.html)."""
        raw_hp1 = {
            "device_id": "HP_01",
            "device_type": "Smartphone_Android_Mic",
            "location": "Ruang_Kelas_Tengah",
            "rms": 0.0234,
            "peak": 0.18,
            "db": 66.5,
            "status": "KONDUSIF",
            "alert": False,
            "timestamp": "2026-10-29T08:00:00.000Z",
        }

        norm = normalize_telemetry("kelas/kebisingan/hp1/telemetry", raw_hp1)

        self.assertEqual(norm.slot, "node1")
        self.assertEqual(norm.device_id, "HP_01")
        self.assertEqual(norm.db, 66.5)
        self.assertEqual(norm.peak, 0.18)
        self.assertEqual(norm.rms, 0.0234)
        self.assertEqual(norm.threshold_db, DEFAULT_THRESHOLD_DB)
        self.assertFalse(norm.alert)

    def test_normalize_hp2_web_mic_payload(self):
        """Memverifikasi normalisasi payload AI dari HP 2 (client_mobile_hp2/hp2_web_mic.html)."""
        raw_hp2 = {
            "device_id": "HP_02",
            "device_name": "HP2_Edge_Chatter_Classifier",
            "device_type": "Smartphone_Android_Mic_Node2",
            "location": "Ruang_Kelas_Belakang",
            "rms": 0.0451,
            "peak": 0.22,
            "db": 71.4,
            "threshold_db": 75.0,
            "chatter_detected": True,
            "vocal_energy_ratio": 72.5,
            "chatter_prob": 78,
            "classification": "OBROLAN_DISKUSI",
            "status": "OBROLAN AKTIF / DISKUSI",
            "alert": False,
            "timestamp": "2026-10-29T08:00:01.000Z",
        }

        norm = normalize_telemetry("kelas/kebisingan/node2/telemetry", raw_hp2)

        self.assertEqual(norm.slot, "node2")
        self.assertEqual(norm.device_id, "HP_02")
        self.assertEqual(norm.db, 71.4)
        self.assertTrue(norm.chatter_detected)
        self.assertEqual(norm.vocal_energy_ratio, 72.5)
        self.assertEqual(norm.chatter_prob, 78)
        self.assertEqual(norm.classification, "OBROLAN_DISKUSI")

    def test_telemetry_deduplicator(self):
        """Memverifikasi deduplikasi saat Edge 2 mengirim paket kembar ke node2 dan hp2."""
        dedup = TelemetryDeduplicator(window_seconds=0.40)

        raw = {
            "device_id": "HP_02",
            "location": "Ruang_Kelas_Belakang",
            "db": 68.0,
            "timestamp": "2026-10-29T08:00:02.000Z",
        }

        norm1 = normalize_telemetry("kelas/kebisingan/node2/telemetry", raw)
        norm2 = normalize_telemetry("kelas/kebisingan/hp2/telemetry", raw)

        # Paket 1 harus diterima
        self.assertTrue(dedup.should_accept(norm1))
        # Paket 2 yang kembar identik dalam window < 400ms harus ditolak
        self.assertFalse(dedup.should_accept(norm2))

        # Paket berikutnya dengan timestamp dan dB baru harus diterima
        raw_next = {
            "device_id": "HP_02",
            "location": "Ruang_Kelas_Belakang",
            "db": 69.5,
            "timestamp": "2026-10-29T08:00:03.000Z",
        }
        norm3 = normalize_telemetry("kelas/kebisingan/node2/telemetry", raw_next)
        self.assertTrue(dedup.should_accept(norm3))

    def test_build_control_payload_and_json(self):
        """Memverifikasi pembentukan JSON kontrol dua arah."""
        payload = build_control_payload(set_threshold=80.0, mute=True, mode="diskusi")
        self.assertEqual(payload["set_threshold"], 80.0)
        self.assertTrue(payload["mute"])
        self.assertEqual(payload["mode"], "diskusi")

        json_str = build_control_json(set_threshold=60.0, mute=False)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["set_threshold"], 60.0)
        self.assertFalse(parsed["mute"])


class TestRoomFusionEngine(unittest.TestCase):

    def test_fuse_quiet_room(self):
        """Memverifikasi kondisi kelas sangat tenang."""
        n1 = normalize_telemetry("kelas/kebisingan/node1/telemetry", {"db": 42.0, "alert": False})
        n2 = normalize_telemetry(
            "kelas/kebisingan/node2/telemetry",
            {"db": 44.0, "chatter_detected": False, "chatter_prob": 10, "alert": False},
        )

        state = fuse_room_state(n1, n2, threshold_db=75.0)
        self.assertEqual(state.status_code, "SANGAT_TENANG")
        self.assertEqual(state.status_color, "emerald")
        self.assertFalse(state.is_alarm)
        self.assertEqual(state.avg_db, 43.0)

    def test_fuse_teacher_explaining(self):
        """Memverifikasi kondisi kondusif saat pengajar menjelaskan di depan."""
        n1 = normalize_telemetry("kelas/kebisingan/node1/telemetry", {"db": 65.0, "alert": False})
        n2 = normalize_telemetry(
            "kelas/kebisingan/node2/telemetry",
            {"db": 56.0, "chatter_detected": False, "chatter_prob": 25, "alert": False},
        )

        state = fuse_room_state(n1, n2, threshold_db=75.0)
        self.assertEqual(state.status_code, "KONDUSIF_BELAJAR")
        self.assertEqual(state.status_color, "cyan")
        self.assertFalse(state.is_alarm)
        self.assertIn("Zona Depan", state.zone_comparison)

    def test_fuse_student_chatter_warning(self):
        """Memverifikasi peringatan saat siswa di belakang mengobrol aktif."""
        n1 = normalize_telemetry("kelas/kebisingan/node1/telemetry", {"db": 58.0, "alert": False})
        n2 = normalize_telemetry(
            "kelas/kebisingan/node2/telemetry",
            {
                "db": 69.0,
                "chatter_detected": True,
                "chatter_prob": 82,
                "classification": "OBROLAN_DISKUSI",
                "alert": False,
            },
        )

        state = fuse_room_state(n1, n2, threshold_db=75.0)
        self.assertEqual(state.status_code, "PERINGATAN_DISKUSI")
        self.assertEqual(state.status_color, "amber")
        self.assertFalse(state.is_alarm)
        self.assertIn("Zona Belakang", state.zone_comparison)

    def test_fuse_alarm_high_noise(self):
        """Memverifikasi kondisi alarm saat kebisingan melampaui batas ambang."""
        n1 = normalize_telemetry("kelas/kebisingan/node1/telemetry", {"db": 78.5, "alert": True})
        n2 = normalize_telemetry(
            "kelas/kebisingan/node2/telemetry",
            {
                "db": 77.0,
                "chatter_detected": True,
                "chatter_prob": 90,
                "classification": "OBROLAN_GADUH",
                "alert": True,
            },
        )

        state = fuse_room_state(n1, n2, threshold_db=75.0)
        self.assertEqual(state.status_code, "SANGAT_BISING_ALARM")
        self.assertEqual(state.status_color, "rose")
        self.assertTrue(state.is_alarm)


if __name__ == "__main__":
    unittest.main()
