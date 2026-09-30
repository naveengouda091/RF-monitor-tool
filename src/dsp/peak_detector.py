"""
Peak Detection and Occupied Bandwidth Extraction Module.
Uses SciPy signal processing to extract active carriers, noise floor differentials,
and 3dB/10dB channel bandwidths from calibrated PSD data.
"""

from dataclasses import dataclass
from typing import List, Optional
import numpy as np
from scipy import signal


@dataclass
class DetectedPeak:
    """Represents an active RF carrier peak."""
    freq_mhz: float
    power_dbfs: float
    snr_db: float
    bw_3db_khz: float
    bw_10db_khz: float
    bin_index: int
    band_label: str = "Unknown"


class PeakDetector:
    """
    Detects spectral peaks and calculates occupied channel bandwidths.
    """

    def __init__(
        self,
        min_prominence_db: float = 6.0,
        min_distance_bins: int = 15,
        max_peaks: int = 8,
    ):
        self.min_prominence_db = min_prominence_db
        self.min_distance_bins = min_distance_bins
        self.max_peaks = max_peaks

    @staticmethod
    def _calculate_bandwidth_at_drop(
        psd_dbfs: np.ndarray, peak_idx: int, db_drop: float, df_khz: float
    ) -> float:
        """Calculates fractional occupied bandwidth at a given dB drop from peak."""
        p_peak = float(psd_dbfs[peak_idx])
        target = p_peak - db_drop
        n = len(psd_dbfs)

        # Search left
        left_idx = peak_idx
        while left_idx > 0 and psd_dbfs[left_idx] > target:
            left_idx -= 1

        if left_idx < peak_idx and psd_dbfs[left_idx] <= target:
            denom = float(psd_dbfs[left_idx + 1] - psd_dbfs[left_idx])
            frac_left = left_idx + (target - float(psd_dbfs[left_idx])) / denom if abs(denom) > 1e-12 else float(left_idx)
        else:
            frac_left = float(left_idx)

        # Search right
        right_idx = peak_idx
        while right_idx < n - 1 and psd_dbfs[right_idx] > target:
            right_idx += 1

        if right_idx > peak_idx and psd_dbfs[right_idx] <= target:
            denom = float(psd_dbfs[right_idx - 1] - psd_dbfs[right_idx])
            frac_right = right_idx - (target - float(psd_dbfs[right_idx])) / denom if abs(denom) > 1e-12 else float(right_idx)
        else:
            frac_right = float(right_idx)

        width_bins = max(1.0, frac_right - frac_left)
        return float(width_bins * df_khz)

    def detect(
        self,
        freq_axis_mhz: np.ndarray,
        psd_dbfs: np.ndarray,
        noise_floor_dbfs: float,
    ) -> List[DetectedPeak]:
        """
        Finds active carrier peaks in PSD above the noise floor.

        Returns:
            List of DetectedPeak sorted by power descending.
        """
        if len(psd_dbfs) < 16:
            return []

        # Find peaks with minimum height and prominence
        min_height = noise_floor_dbfs + self.min_prominence_db
        peak_indices, properties = signal.find_peaks(
            psd_dbfs,
            height=min_height,
            prominence=self.min_prominence_db,
            distance=self.min_distance_bins,
        )

        if len(peak_indices) == 0:
            return []

        # Calculate frequency resolution per bin
        df_khz = (freq_axis_mhz[1] - freq_axis_mhz[0]) * 1000.0

        peaks: List[DetectedPeak] = []
        for idx in peak_indices:
            p_val = float(psd_dbfs[idx])
            f_val = float(freq_axis_mhz[idx])
            snr = float(p_val - noise_floor_dbfs)
            bw3 = self._calculate_bandwidth_at_drop(psd_dbfs, idx, 3.0, df_khz)
            bw10 = self._calculate_bandwidth_at_drop(psd_dbfs, idx, 10.0, df_khz)

            peaks.append(
                DetectedPeak(
                    freq_mhz=round(f_val, 4),
                    power_dbfs=round(p_val, 2),
                    snr_db=round(snr, 2),
                    bw_3db_khz=round(bw3, 1),
                    bw_10db_khz=round(bw10, 1),
                    bin_index=idx,
                )
            )

        # Sort by power descending and limit to max_peaks
        peaks.sort(key=lambda p: p.power_dbfs, reverse=True)
        return peaks[: self.max_peaks]
