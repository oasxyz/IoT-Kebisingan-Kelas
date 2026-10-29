"""
Shared modules for IoT Kebisingan Kelas (Kelompok 7).
Includes MQTT topic contracts, payload normalization, deduplication, and room state fusion.
"""

from .mqtt_contract import (
    BROKER_HOST,
    BROKER_TCP_PORT,
    BROKER_WS_PORT,
    BROKER_WS_PATH,
    TOPIC_NODE1_TELEMETRY,
    TOPIC_HP1_TELEMETRY,
    TOPIC_NODE2_TELEMETRY,
    TOPIC_HP2_TELEMETRY,
    TOPIC_ALERT_WILDCARD,
    TOPIC_NODE1_ALERT,
    TOPIC_NODE2_ALERT,
    TOPIC_NODE1_CONTROL,
    TOPIC_NODE2_CONTROL,
    TOPIC_GLOBAL_CONTROL,
    TOPIC_ROOM_STATUS,
    NormalizedTelemetry,
    normalize_telemetry,
    build_control_payload,
    TelemetryDeduplicator,
)
from .room_fusion import RoomAcousticState, fuse_room_state

__all__ = [
    "BROKER_HOST",
    "BROKER_TCP_PORT",
    "BROKER_WS_PORT",
    "BROKER_WS_PATH",
    "TOPIC_NODE1_TELEMETRY",
    "TOPIC_HP1_TELEMETRY",
    "TOPIC_NODE2_TELEMETRY",
    "TOPIC_HP2_TELEMETRY",
    "TOPIC_ALERT_WILDCARD",
    "TOPIC_NODE1_ALERT",
    "TOPIC_NODE2_ALERT",
    "TOPIC_NODE1_CONTROL",
    "TOPIC_NODE2_CONTROL",
    "TOPIC_GLOBAL_CONTROL",
    "TOPIC_ROOM_STATUS",
    "NormalizedTelemetry",
    "normalize_telemetry",
    "build_control_payload",
    "TelemetryDeduplicator",
    "RoomAcousticState",
    "fuse_room_state",
]
