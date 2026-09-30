"""
FFT Processing Engine for real-time Power Spectral Density (PSD) calculation.
Supports selectable windowing functions, frame averaging, dBFS / estimated dBm scaling,
and noise floor estimation.
"""

from typing import Tuple, Optional
import numpy as np
from scipy import signal


class FFTProcessor:
    """
    Computes windowed FFTs on complex I/Q buffers and produces calibrated
    Power Spectral Density (PSD) curves with temporal smoothing.
    """

    SUPPORTED_WINDOWS = ["hann", "hamming", "blackman", "rectangular"]
    DEFAULT_FFT_SIZE = 2048
    CALIBRATION_OFFSET_DBM = -10.0  # Empirical baseline for RTL-SDR Blog V3 (50 ohm)

    def __init__(
        self,
        fft_size: int = DEFAULT_FFT_SIZE,
        window_name: str = "hann",
        averaging_count: int = 5,
        cal_offset: float = CALIBRATION_OFFSET_DBM,
    ):
        self._fft_size = fft_size
        self._window_name = window_name.lower()
        self._averaging_count = max(1, averaging_count)
        self._cal_offset = cal_offset
        self._smoothed_psd: Optional[np.ndarray] = None
        self._window_cache: Optional[np.ndarray] = None
        self._win_norm: float = 1.0

        self._update_window()

    @property
    def fft_size(self) -> int:
        return self._fft_size

    @fft_size.setter
    def fft_size(self, size: int):
        if size != self._fft_size:
            self._fft_size = int(size)
            self._smoothed_psd = None
            self._update_window()

    @property
    def window_name(self) -> str:
        return self._window_name

    @window_name.setter
    def window_name(self, name: str):
        name_lower = name.lower()
        if name_lower in self.SUPPORTED_WINDOWS and name_lower != self._window_name:
            self._window_name = name_lower
            self._update_window()

    @property
    def averaging_count(self) -> int:
        return self._averaging_count

    @averaging_count.setter
    def averaging_count(self, count: int):
        self._averaging_count = max(1, int(count))

    def reset_averaging(self):
        """Clears smoothed PSD history (e.g. after frequency retuning)."""
        self._smoothed_psd = None

    def _update_window(self):
        """Generates and normalizes the selected window array."""
        n = self._fft_size
        if self._window_name == "hann":
            w = np.hanning(n)
        elif self._window_name == "hamming":
            w = np.hamming(n)
        elif self._window_name == "blackman":
            w = np.blackman(n)
        elif self._window_name == "rectangular":
            w = np.ones(n)
        else:
            w = np.hanning(n)

        self._window_cache = w
        # Energy normalization factor: sum of squared window coefficients
        self._win_norm = np.sum(w ** 2)

    def process(
        self,
        samples: np.ndarray,
        center_freq_hz: float,
        sample_rate_hz: float,
        tuner_gain_db: float = 0.0,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float, float]:
        """
        Processes complex I/Q samples into calibrated frequency and PSD arrays.

        Returns:
            freq_axis_mhz: 1D array of frequency bins in MHz
            psd_dbfs: 1D array of smoothed power spectral density in dBFS
            psd_dbm: 1D array of estimated power in dBm
            peak_power_dbfs: Peak signal power in dBFS
            noise_floor_dbfs: Estimated baseline noise floor in dBFS
        """
        # Ensure we have enough samples
        if len(samples) < self._fft_size:
            # Zero-pad if needed
            padded = np.zeros(self._fft_size, dtype=np.complex64)
            padded[: len(samples)] = samples
            samples = padded
        else:
            samples = samples[: self._fft_size]

        # Apply window
        windowed = samples * self._window_cache

        # Compute FFT and shift DC bin to center
        fft_result = np.fft.fftshift(np.fft.fft(windowed, n=self._fft_size))

        # Power calculation: normalized relative to full scale
        power = (np.abs(fft_result) ** 2) / (self._fft_size * self._win_norm + 1e-12)

        # Convert to dBFS (0 dBFS = full scale continuous wave)
        raw_psd_dbfs = 10.0 * np.log10(np.maximum(power, 1e-15))

        # Temporal smoothing (Exponential Moving Average)
        if self._smoothed_psd is None or len(self._smoothed_psd) != self._fft_size:
            self._smoothed_psd = raw_psd_dbfs.copy()
        else:
            alpha = 2.0 / (self._averaging_count + 1.0)
            self._smoothed_psd = alpha * raw_psd_dbfs + (1.0 - alpha) * self._smoothed_psd

        # Estimated dBm conversion:
        # P_dBm = P_dBFS + calibration_offset - tuner_gain
        psd_dbm = self._smoothed_psd + self._cal_offset - (tuner_gain_db if tuner_gain_db > 0 else 0)

        # Compute frequency axis in MHz
        half_sr = sample_rate_hz / 2.0
        freq_axis_hz = np.linspace(
            center_freq_hz - half_sr,
            center_freq_hz + half_sr,
            self._fft_size,
            endpoint=False,
        )
        freq_axis_mhz = freq_axis_hz / 1e6

        # Metrics extraction
        peak_power_dbfs = float(np.max(self._smoothed_psd))
        # Estimate noise floor using 20th percentile to ignore carrier spikes
        noise_floor_dbfs = float(np.percentile(self._smoothed_psd, 20))

        return (
            freq_axis_mhz,
            self._smoothed_psd,
            psd_dbm,
            peak_power_dbfs,
            noise_floor_dbfs,
        )
