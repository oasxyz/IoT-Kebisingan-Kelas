"""
Classroom Multi-Node Fusion Engine (Kelompok 7).
Menggabungkan data telemetri dari Edge 1 (Depan Kelas) dan Edge 2 (Belakang Kelas)
untuk menghasilkan kesimpulan kondisi akustik ruang kelas secara terpadu.
"""

from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .mqtt_contract import NormalizedTelemetry


@dataclass
class RoomAcousticState:
    """Status agregasi kondisi ruang kelas terpadu."""
    status_code: str          # "SANGAT_TENANG", "KONDUSIF_BELAJAR", "PERINGATAN_DISKUSI", "SANGAT_BISING_ALARM"
    status_label: str         # Deskripsi ringkas untuk tampilan Dashboard
    status_color: str         # "emerald", "cyan", "amber", "rose"
    avg_db: float             # Rata-rata dB kelas
    node1_db: Optional[float] # dB Sensor Depan Kelas
    node2_db: Optional[float] # dB Sensor Belakang Kelas
    threshold_db: float       # Ambang batas aktif
    chatter_detected: bool    # Obrolan siswa terdeteksi di belakang
    chatter_prob: int         # Probabilitas obrolan (0-100%)
    classification: str       # Kategori AI Edge 2
    is_alarm: bool            # Apakah kelas dalam kondisi alarm / bising berlebih
    zone_comparison: str      # Analisis perbedaan akustik zona depan vs belakang
    recommendation: str       # Rekomendasi tindakan (misal untuk guru / pengawas)
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def fuse_room_state(
    node1: Optional[NormalizedTelemetry],
    node2: Optional[NormalizedTelemetry],
    threshold_db: float = 75.0,
) -> RoomAcousticState:
    """
    Rumus penggabungan kondisi akustik ruang kelas:
    1. Hening: Keduanya < 52 dB.
    2. Kondusif Belajar: Depan 52-75 dB (suara pengajar normal), Belakang kondusif/bukan obrolan bising.
    3. Peringatan Diskusi: Edge 2 mendeteksi obrolan aktif/gaduh (> 50% chatter_prob) atau dB 68-75 dB.
    4. Sangat Bising / Alarm: Salah satu atau kedua node >= threshold_db atau Edge 2 klasifikasi OBROLAN_GADUH.
    """
    n1_db = node1.db if node1 is not None else None
    n2_db = node2.db if node2 is not None else None

    # Tentukan rata-rata dB
    valid_dbs = [v for v in (n1_db, n2_db) if v is not None]
    if valid_dbs:
        avg_db = round(sum(valid_dbs) / len(valid_dbs), 1)
    else:
        avg_db = 40.0

    # Ambil metrik AI dari Edge 2 jika tersedia
    chatter_det = node2.chatter_detected if node2 is not None else False
    chatter_prob = node2.chatter_prob if node2 is not None else 0
    classification = node2.classification if node2 is not None else "TIDAK_ADA_DATA"

    # Evaluasi kondisi kebisingan
    any_alert = (
        (node1.alert if node1 is not None else False) or
        (node2.alert if node2 is not None else False) or
        (avg_db >= threshold_db) or
        (classification == "OBROLAN_GADUH")
    )

    now_iso = datetime.now(timezone.utc).isoformat()

    # Logika Pengambilan Keputusan Kondisi Kelas
    if any_alert:
        code = "SANGAT_BISING_ALARM"
        label = "🚨 SANGAT BISING — ALARM KELAS MELEBIHI BATAS"
        color = "rose"
        is_alarm = True
        rec = "Beri peringatan kepada kelas untuk menjaga ketenangan belajar."
    elif chatter_det and chatter_prob >= 50 and avg_db >= 62.0:
        code = "PERINGATAN_DISKUSI"
        label = "⚠️ PERINGATAN — OBROLAN SISWA AKTIF DI BELAKANG"
        color = "amber"
        is_alarm = False
        rec = "Siswa di zona belakang terdeteksi mengobrol; pantau agar suasana tetap kondusif."
    elif avg_db < 52.0 and chatter_prob < 30:
        code = "SANGAT_TENANG"
        label = "✨ SANGAT TENANG — SUASANA FOKUS / UJIAN"
        color = "emerald"
        is_alarm = False
        rec = "Kondisi sangat tenang dan hening, ideal untuk belajar mandiri atau ujian."
    else:
        code = "KONDUSIF_BELAJAR"
        label = "✅ KONDUSIF — PROSES PEMBELAJARAN BERLANGSUNG"
        color = "cyan"
        is_alarm = False
        rec = "Tingkat suara berada dalam batas wajar penjelasan materi / kegiatan belajar."

    # Analisis perbandingan zona depan vs belakang
    if n1_db is not None and n2_db is not None:
        diff = round(n1_db - n2_db, 1)
        if diff >= 6.0:
            comparison = f"Zona Depan ({n1_db} dB) lebih dominan dibanding Belakang ({n2_db} dB) — Suara Pengajar/Papan Tulis."
        elif diff <= -6.0:
            comparison = f"Zona Belakang ({n2_db} dB) lebih ramai dibanding Depan ({n1_db} dB) — Potensi Obrolan Siswa."
        else:
            comparison = f"Distribusi suara merata di seluruh ruangan (Depan: {n1_db} dB, Belakang: {n2_db} dB)."
    elif n1_db is not None:
        comparison = f"Hanya data Zona Depan aktif ({n1_db} dB). Menunggu data Zona Belakang."
    elif n2_db is not None:
        comparison = f"Hanya data Zona Belakang aktif ({n2_db} dB). Menunggu data Zona Depan."
    else:
        comparison = "Menunggu koneksi data dari kedua sensor Edge..."

    return RoomAcousticState(
        status_code=code,
        status_label=label,
        status_color=color,
        avg_db=avg_db,
        node1_db=n1_db,
        node2_db=n2_db,
        threshold_db=threshold_db,
        chatter_detected=chatter_det,
        chatter_prob=chatter_prob,
        classification=classification,
        is_alarm=is_alarm,
        zone_comparison=comparison,
        recommendation=rec,
        timestamp=now_iso,
    )
