"""
RF Exposure Index Computation Engine.
Calculates integrated channel power, maps exposure onto a 0-100 index,
and assigns Low/Medium/High public health risk tiers.
"""

from dataclasses import dataclass
from typing import Tuple
import numpy as np


@dataclass
class ExposureMetrics:
    score: int                     # 0 - 100
    tier: str                      # "Low", "Medium", "High"
    color_hex: str                 # Green (#10b981), Amber (#f59e0b), Red (#ef4444)
    total_power_dbfs: float
    total_power_dbm: float
    status_summary: str
    advice: str


class ExposureIndexEngine:
    """
    Computes cumulative RF power and normalized exposure tier for audiences and evaluators.
    """

    # Power calibration baseline range for 0-100 score mapping
    QUIET_LEVEL_DBFS = -70.0   # Baseline ambient room noise
    HIGH_LEVEL_DBFS = -15.0    # Near-field transmitter saturation

    def __init__(self, cal_offset_dbm: float = -10.0):
        self.cal_offset_dbm = cal_offset_dbm

    def compute(
        self,
        psd_dbfs: np.ndarray,
        psd_dbm: np.ndarray,
        peak_power_dbfs: float,
    ) -> ExposureMetrics:
        """
        Computes composite exposure score and tier from current PSD.
        """
        if len(psd_dbfs) == 0:
            return ExposureMetrics(
                score=0,
                tier="Low",
                color_hex="#10b981",
                total_power_dbfs=-100.0,
                total_power_dbm=-140.0,
                status_summary="No signal detected",
                advice="Hardware idle",
            )

        # Integrated spectral power: sum of linear power bins across sampled bandwidth
        linear_power = 10.0 ** (psd_dbfs / 10.0)
        integrated_linear = np.sum(linear_power) / len(linear_power)
        total_power_dbfs = float(10.0 * np.log10(max(integrated_linear, 1e-12)))

        # Total power in estimated dBm
        linear_dbm = 10.0 ** (psd_dbm / 10.0)
        integrated_dbm = np.sum(linear_dbm) / len(linear_dbm)
        total_power_dbm = float(10.0 * np.log10(max(integrated_dbm, 1e-12)))

        # Normalize score 0 - 100
        span = self.HIGH_LEVEL_DBFS - self.QUIET_LEVEL_DBFS
        normalized = (total_power_dbfs - self.QUIET_LEVEL_DBFS) / span
        score = int(np.clip(normalized * 100.0, 0.0, 100.0))

        # Assign tier
        if score <= 35:
            tier = "Low"
            color = "#10b981"
            summary = "LOW EXPOSURE (Safe Ambient)"
            advice = "Minimal RF power detected. Within natural background levels."
        elif score <= 70:
            tier = "Medium"
            color = "#f59e0b"
            summary = "MODERATE EXPOSURE (Active Nearby Wireless)"
            advice = "Moderate carrier activity. Typical residential / classroom exposure."
        else:
            tier = "High"
            color = "#ef4444"
            summary = "HIGH EXPOSURE (High-Power Carrier / Close Proximity)"
            advice = "Strong transmitter nearby (active cellular transmission or broadcast antenna)."

        return ExposureMetrics(
            score=score,
            tier=tier,
            color_hex=color,
            total_power_dbfs=round(total_power_dbfs, 2),
            total_power_dbm=round(total_power_dbm, 2),
            status_summary=summary,
            advice=advice,
        )
