"""
Survey Logger Module for real-time and scheduled spectral data logging.
Manages survey session state, throttled background capture, and signal emission.
"""

import time
from datetime import datetime
from typing import Optional, Dict, Any, List
import numpy as np

from PyQt6.QtCore import QObject, pyqtSignal

from src.storage.survey_database import SurveyDatabase
from src.exposure.exposure_index import ExposureMetrics
from src.dsp.peak_detector import DetectedPeak
from src.shielding.differential_engine import ShieldingResult


class SurveyLogger(QObject):
    """
    Coordinates active survey recording sessions and persists snapshot/interval records.
    """

    survey_logged = pyqtSignal(dict)
    shielding_logged = pyqtSignal(dict)
    recording_state_changed = pyqtSignal(bool)
    session_stats_updated = pyqtSignal(dict)

    def __init__(self, db: Optional[SurveyDatabase] = None, parent=None):
        super().__init__(parent)
        self.db = db or SurveyDatabase()

        # Session properties
        self._is_recording: bool = False
        self._location_id: str = "Comm Lab (Room 101)"
        self._interval_sec: float = 2.0
        self._notes: str = ""
        self._last_log_time: float = 0.0

        # Current session tracking metrics
        self._session_count: int = 0
        self._session_max_peak: float = -120.0
        self._session_start_time: Optional[float] = None

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @property
    def location_id(self) -> str:
        return self._location_id

    @location_id.setter
    def location_id(self, val: str):
        self._location_id = val.strip() or "General Lab"

    @property
    def interval_sec(self) -> float:
        return self._interval_sec

    @interval_sec.setter
    def interval_sec(self, val: float):
        self._interval_sec = max(0.2, float(val))

    @property
    def notes(self) -> str:
        return self._notes

    @notes.setter
    def notes(self, val: str):
        self._notes = val.strip()

    def start_session(self, location_id: str, interval_sec: float = 2.0, notes: str = ""):
        """Starts a continuous logging survey session."""
        self.location_id = location_id
        self.interval_sec = interval_sec
        self.notes = notes
        self._is_recording = True
        self._last_log_time = 0.0  # Force immediate first capture
        self._session_count = 0
        self._session_max_peak = -120.0
        self._session_start_time = time.time()

        self.recording_state_changed.emit(True)
        self._emit_session_stats()

    def stop_session(self):
        """Stops the continuous survey logging session."""
        self._is_recording = False
        self.recording_state_changed.emit(False)

    def process_frame(
        self,
        freq_axis_mhz: np.ndarray,
        psd_dbfs: np.ndarray,
        peak_freq_mhz: float,
        peak_power_dbfs: float,
        noise_floor_dbfs: float,
        peaks: List[DetectedPeak],
        dominant_band: str,
        exposure: ExposureMetrics,
        center_freq_mhz: float,
        sample_rate_msps: float,
    ) -> bool:
        """
        Evaluates incoming spectrum frame. If recording is active and interval has elapsed,
        logs the record to the database. Returns True if a record was logged.
        """
        if not self._is_recording:
            return False

        now = time.monotonic()
        if (now - self._last_log_time) < self._interval_sec:
            return False

        self._last_log_time = now
        record = self._build_survey_record(
            freq_axis_mhz=freq_axis_mhz,
            psd_dbfs=psd_dbfs,
            peak_freq_mhz=peak_freq_mhz,
            peak_power_dbfs=peak_power_dbfs,
            noise_floor_dbfs=noise_floor_dbfs,
            peaks=peaks,
            dominant_band=dominant_band,
            exposure=exposure,
            center_freq_mhz=center_freq_mhz,
            sample_rate_msps=sample_rate_msps,
        )

        row_id = self.db.insert_survey_log(record)
        record["id"] = row_id

        # Update session stats
        self._session_count += 1
        if peak_power_dbfs > self._session_max_peak:
            self._session_max_peak = peak_power_dbfs

        self.survey_logged.emit(record)
        self._emit_session_stats(latest_tier=exposure.tier)
        return True

    def log_snapshot(
        self,
        freq_axis_mhz: np.ndarray,
        psd_dbfs: np.ndarray,
        peak_freq_mhz: float,
        peak_power_dbfs: float,
        noise_floor_dbfs: float,
        peaks: List[DetectedPeak],
        dominant_band: str,
        exposure: ExposureMetrics,
        center_freq_mhz: float,
        sample_rate_msps: float,
        location_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Manually captures a single-shot RF survey record regardless of active session state.
        """
        loc = location_id if location_id is not None else self._location_id
        note_str = notes if notes is not None else self._notes

        record = self._build_survey_record(
            freq_axis_mhz=freq_axis_mhz,
            psd_dbfs=psd_dbfs,
            peak_freq_mhz=peak_freq_mhz,
            peak_power_dbfs=peak_power_dbfs,
            noise_floor_dbfs=noise_floor_dbfs,
            peaks=peaks,
            dominant_band=dominant_band,
            exposure=exposure,
            center_freq_mhz=center_freq_mhz,
            sample_rate_msps=sample_rate_msps,
            override_location=loc,
            override_notes=note_str,
        )

        row_id = self.db.insert_survey_log(record)
        record["id"] = row_id

        self._session_count += 1
        if peak_power_dbfs > self._session_max_peak:
            self._session_max_peak = peak_power_dbfs

        self.survey_logged.emit(record)
        self._emit_session_stats(latest_tier=exposure.tier)
        return record

    def log_shielding_result(
        self,
        result: ShieldingResult,
        center_freq_mhz: float,
        notes: str = "",
    ) -> Dict[str, Any]:
        """
        Persists a shielding effectiveness measurement into shielding_logs.
        """
        record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "material_name": result.material_name,
            "baseline_peak_dbfs": round(result.baseline_peak_dbfs, 2),
            "live_peak_dbfs": round(result.live_peak_dbfs, 2),
            "se_peak_db": round(result.se_peak_db, 2),
            "percentage_reduction": round(result.percentage_reduction, 2),
            "attenuation_ratio": round(result.attenuation_ratio, 2),
            "rating": result.rating,
            "center_freq_mhz": round(center_freq_mhz, 4),
            "notes": notes,
        }

        row_id = self.db.insert_shielding_log(record)
        record["id"] = row_id
        self.shielding_logged.emit(record)
        return record

    def _build_survey_record(
        self,
        freq_axis_mhz: np.ndarray,
        psd_dbfs: np.ndarray,
        peak_freq_mhz: float,
        peak_power_dbfs: float,
        noise_floor_dbfs: float,
        peaks: List[DetectedPeak],
        dominant_band: str,
        exposure: ExposureMetrics,
        center_freq_mhz: float,
        sample_rate_msps: float,
        override_location: Optional[str] = None,
        override_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Assembles a clean survey record dictionary."""
        f_start = float(freq_axis_mhz[0]) if len(freq_axis_mhz) > 0 else center_freq_mhz - 1.0
        f_end = float(freq_axis_mhz[-1]) if len(freq_axis_mhz) > 0 else center_freq_mhz + 1.0
        avg_power = float(np.mean(psd_dbfs)) if len(psd_dbfs) > 0 else -100.0

        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "location_id": override_location or self._location_id,
            "center_freq_mhz": round(center_freq_mhz, 4),
            "sample_rate_msps": round(sample_rate_msps, 3),
            "freq_start_mhz": round(f_start, 4),
            "freq_end_mhz": round(f_end, 4),
            "peak_power_dbfs": round(peak_power_dbfs, 2),
            "peak_freq_mhz": round(peak_freq_mhz, 4),
            "avg_power_dbfs": round(avg_power, 2),
            "noise_floor_dbfs": round(noise_floor_dbfs, 2),
            "dominant_band": dominant_band,
            "exposure_score": int(exposure.score),
            "exposure_tier": exposure.tier,
            "active_carriers_count": len(peaks),
            "notes": override_notes if override_notes is not None else self._notes,
        }

    def _emit_session_stats(self, latest_tier: str = "Low"):
        stats = {
            "is_recording": self._is_recording,
            "session_count": self._session_count,
            "session_max_peak": self._session_max_peak,
            "latest_tier": latest_tier,
            "location_id": self._location_id,
        }
        self.session_stats_updated.emit(stats)
