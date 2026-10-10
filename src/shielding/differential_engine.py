"""
Shielding Effectiveness (SE) Differential Engine.
Implements dual-pass and live continuous differential measurement workflows (PRD Section 8).
Calculates baseline P0, live P1, delta spectrum, SE in dB, and power reduction percentage.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, List
import numpy as np


@dataclass
class ShieldingResult:
    """Encapsulates shielding attenuation metrics for a measured material."""
    material_name: str
    se_peak_db: float
    se_avg_db: float
    attenuation_ratio: float
    percentage_reduction: float
    rating: str
    color_hex: str
    baseline_peak_dbfs: float
    live_peak_dbfs: float


class ShieldingDifferentialEngine:
    """
    Manages baseline reference capture (P0) and live real-time differential calculation (P0 - P1).
    """

    def __init__(self, target_baseline_frames: int = 50):
        self.target_baseline_frames = target_baseline_frames
        self._capturing_baseline = False
        self._baseline_frames: List[np.ndarray] = []
        self._baseline_freqs: Optional[np.ndarray] = None
        self._baseline_psd: Optional[np.ndarray] = None

    @property
    def is_capturing_baseline(self) -> bool:
        return self._capturing_baseline

    @property
    def has_baseline(self) -> bool:
        return self._baseline_psd is not None

    def start_baseline_capture(self, num_frames: int = 50):
        """Begins recording reference baseline frames."""
        self.target_baseline_frames = max(5, num_frames)
        self._capturing_baseline = True
        self._baseline_frames.clear()
        self._baseline_psd = None

    def cancel_baseline_capture(self):
        """Aborts in-progress baseline acquisition."""
        self._capturing_baseline = False
        self._baseline_frames.clear()

    def clear_baseline(self):
        """Clears stored baseline reference."""
        self._baseline_psd = None
        self._baseline_freqs = None
        self._baseline_frames.clear()
        self._capturing_baseline = False

    def feed_baseline_frame(
        self, freq_axis_mhz: np.ndarray, psd_dbfs: np.ndarray
    ) -> Tuple[bool, float]:
        """
        Feeds a frame during baseline capture.

        Returns:
            (is_complete, progress_fraction)
        """
        if not self._capturing_baseline:
            return False, 0.0

        if self._baseline_frames and len(psd_dbfs) != len(self._baseline_frames[0]):
            self._baseline_frames.clear()

        self._baseline_frames.append(psd_dbfs.copy())
        self._baseline_freqs = freq_axis_mhz.copy()
        count = len(self._baseline_frames)
        progress = min(1.0, count / self.target_baseline_frames)

        if count >= self.target_baseline_frames:
            # Average captured linear power to avoid dB averaging bias
            linear_frames = [10.0 ** (f / 10.0) for f in self._baseline_frames]
            mean_linear = np.mean(linear_frames, axis=0)
            self._baseline_psd = 10.0 * np.log10(np.maximum(mean_linear, 1e-15))
            self._capturing_baseline = False
            return True, 1.0

        return False, progress

    def get_baseline(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Returns (freq_axis_mhz, baseline_psd_dbfs) if available."""
        if self._baseline_psd is not None and self._baseline_freqs is not None:
            return self._baseline_freqs, self._baseline_psd
        return None

    def compute_differential(
        self,
        freq_axis_mhz: np.ndarray,
        live_psd_dbfs: np.ndarray,
        material_name: str = "Shield Material",
    ) -> Optional[Tuple[np.ndarray, ShieldingResult]]:
        """
        Calculates live differential delta curve and attenuation metrics relative to baseline.

        Returns:
            (delta_curve_db, ShieldingResult) or None if no baseline exists.
        """
        if self._baseline_psd is None or len(self._baseline_psd) != len(live_psd_dbfs):
            return None

        # Differential Delta Spectrum: Delta(f) = P0(f) - P1(f) (in dB)
        # Positive values indicate signal reduction/attenuation by the shield
        delta_curve_db = self._baseline_psd - live_psd_dbfs

        p0_peak = float(np.max(self._baseline_psd))
        p1_peak = float(np.max(live_psd_dbfs))

        # Peak Shielding Effectiveness: SE = P0_peak - P1_peak
        se_peak_db = max(0.0, p0_peak - p1_peak)

        # Mean Band Attenuation: average across positive delta bins
        se_avg_db = max(0.0, float(np.mean(delta_curve_db)))

        # Attenuation Ratio: 10^(SE / 10)
        attenuation_ratio = float(10.0 ** (se_peak_db / 10.0))

        # Percentage Power Reduction: (1 - 10^(-SE / 10)) * 100%
        percentage_reduction = float((1.0 - 10.0 ** (-se_peak_db / 10.0)) * 100.0)
        percentage_reduction = max(0.0, min(100.0, percentage_reduction))

        # Effectiveness Rating & Color
        if se_peak_db >= 20.0:
            rating = "EXCELLENT SHIELDING (>20 dB)"
            color = "#10b981"  # Emerald Green
        elif se_peak_db >= 10.0:
            rating = "GOOD SHIELDING (10 - 20 dB)"
            color = "#38bdf8"  # Cyan
        elif se_peak_db >= 6.0:
            rating = "MODERATE SHIELDING (6 - 10 dB)"
            color = "#f59e0b"  # Amber
        else:
            rating = "MINIMAL / INEFFECTIVE (<6 dB)"
            color = "#ef4444"  # Red

        result = ShieldingResult(
            material_name=material_name.strip() or "Custom Material",
            se_peak_db=round(se_peak_db, 2),
            se_avg_db=round(se_avg_db, 2),
            attenuation_ratio=round(attenuation_ratio, 2),
            percentage_reduction=round(percentage_reduction, 2),
            rating=rating,
            color_hex=color,
            baseline_peak_dbfs=round(p0_peak, 2),
            live_peak_dbfs=round(p1_peak, 2),
        )

        return delta_curve_db, result
