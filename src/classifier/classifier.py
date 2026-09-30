"""
RF Signal and Band Classifier.
Maps detected frequencies to regulatory allocations and identifies dominant bands.
"""

from typing import List, Optional, Tuple
from src.classifier.band_definitions import INDIAN_FREQUENCY_BANDS, BandInfo
from src.dsp.peak_detector import DetectedPeak


class BandClassifier:
    """Classifies RF peaks and finds dominant service allocations."""

    def __init__(self, bands: Optional[List[BandInfo]] = None):
        raw_bands = bands or INDIAN_FREQUENCY_BANDS
        # Sort by frequency span ascending so specific narrow allocations
        # (e.g. ISM 433 MHz, LoRa India, ADS-B) take priority over broad allocations
        self.bands = sorted(raw_bands, key=lambda b: (b.freq_max_mhz - b.freq_min_mhz))

    def classify_frequency(self, freq_mhz: float) -> Tuple[str, str, str]:
        """
        Looks up frequency in standard allocations.

        Returns:
            (band_name, service_type, description)
        """
        for band in self.bands:
            if band.freq_min_mhz <= freq_mhz <= band.freq_max_mhz:
                return (band.name, band.service, band.description)
        return ("Unassigned / Unknown", "General RF", "No specific regional allocation recorded")

    def classify_peaks(self, peaks: List[DetectedPeak]) -> List[DetectedPeak]:
        """Annotates each DetectedPeak with its regulatory band label."""
        for peak in peaks:
            band_name, _, _ = self.classify_frequency(peak.freq_mhz)
            peak.band_label = band_name
        return peaks

    def get_dominant_band(self, peaks: List[DetectedPeak]) -> str:
        """Determines dominant band based on detected active carrier strength."""
        if not peaks:
            return "Quiet / Ambient"

        band_counts = {}
        for p in peaks:
            band = p.band_label
            band_counts[band] = band_counts.get(band, 0) + (10.0 ** (p.power_dbfs / 10.0))

        dominant = max(band_counts.items(), key=lambda item: item[1])
        return dominant[0]
