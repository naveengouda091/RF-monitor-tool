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

        # Compute 3dB and 10dB widths (in bins)
        try:
            widths_3db, _, _, _ = signal.peak_widths(psd_dbfs, peak_indices, rel_height=3.0)
            widths_10db, _, _, _ = signal.peak_widths(psd_dbfs, peak_indices, rel_height=10.0)
        except Exception:
            widths_3db = np.ones(len(peak_indices)) * 2.0
            widths_10db = np.ones(len(peak_indices)) * 5.0

        peaks: List[DetectedPeak] = []
        for i, idx in enumerate(peak_indices):
            p_val = float(psd_dbfs[idx])
            f_val = float(freq_axis_mhz[idx])
            snr = float(p_val - noise_floor_dbfs)
            bw3 = float(widths_3db[i] * df_khz) if i < len(widths_3db) else 100.0
            bw10 = float(widths_10db[i] * df_khz) if i < len(widths_10db) else 250.0

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
