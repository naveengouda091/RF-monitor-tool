"""
SDR Hardware Controller for RTL-SDR Blog V3.
Handles device initialization, lifecycle management, frequency tuning,
gain configuration, and asynchronous/synchronous I/Q sample acquisition.
"""

import os
import sys
import logging
from typing import Optional, List, Tuple
import numpy as np

# Ensure Windows finds rtlsdr.dll in the project root or subdirectories
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if hasattr(os, "add_dll_directory"):
    try:
        os.add_dll_directory(PROJECT_ROOT)
    except Exception as e:
        logging.warning(f"Failed to add project root to DLL directory: {e}")

try:
    from rtlsdr import RtlSdr
except ImportError as err:
    raise ImportError(
        f"Unable to load pyrtlsdr or rtlsdr.dll. Ensure rtlsdr.dll is in the project root or system PATH. Details: {err}"
    )

logger = logging.getLogger(__name__)


class SDRDevice:
    """Encapsulates the physical RTL-SDR device with safe parameter bounds."""

    # RTL-SDR Blog V3 tuning limits
    MIN_FREQ_HZ = 24_000_000       # 24 MHz
    MAX_FREQ_HZ = 1_766_000_000     # 1.766 GHz
    DEFAULT_SAMPLE_RATE = 2_400_000 # 2.4 MS/s
    SUPPORTED_SAMPLE_RATES = [1_000_000, 1_800_000, 2_048_000, 2_400_000, 2_560_000]

    def __init__(self, device_index: int = 0):
        self.device_index = device_index
        self._sdr: Optional[RtlSdr] = None
        self._center_freq_hz: float = 100_000_000.0  # Default 100 MHz (FM band)
        self._sample_rate: float = self.DEFAULT_SAMPLE_RATE
        self._gain: float = 20.0
        self._auto_gain: bool = False
        self._ppm_correction: int = 0

    @property
    def is_connected(self) -> bool:
        """Returns True if the RTL-SDR device is currently initialized."""
        return self._sdr is not None

    def connect(self) -> bool:
        """Opens connection to the physical RTL-SDR device."""
        if self._sdr is not None:
            logger.info("Device already connected.")
            return True

        try:
            self._sdr = RtlSdr(device_index=self.device_index)
            # Apply initial hardware parameters
            self.set_sample_rate(self._sample_rate)
            self.set_center_freq(self._center_freq_hz)
            self.set_gain(self._gain, self._auto_gain)
            self.set_ppm_correction(self._ppm_correction)
            logger.info(
                f"RTL-SDR connected successfully on index {self.device_index}. "
                f"Center: {self._center_freq_hz / 1e6:.2f} MHz, Sample Rate: {self._sample_rate / 1e6:.2f} MSps"
            )
            return True
        except Exception as e:
            self._sdr = None
            logger.error(f"Failed to connect to RTL-SDR device: {e}")
            raise RuntimeError(
                f"Cannot initialize RTL-SDR dongle (Device #{self.device_index}). "
                f"Please ensure your RTL-SDR Blog V3 is securely plugged in and WinUSB drivers are installed via Zadig. Error: {e}"
            ) from e

    def disconnect(self):
        """Safely closes the RTL-SDR device connection."""
        if self._sdr is not None:
            try:
                self._sdr.close()
            except Exception as e:
                logger.warning(f"Error while closing RTL-SDR: {e}")
            finally:
                self._sdr = None
                logger.info("RTL-SDR device disconnected.")

    def set_center_freq(self, freq_hz: float):
        """Sets tuner center frequency in Hz with bounds checking."""
        if not (self.MIN_FREQ_HZ <= freq_hz <= self.MAX_FREQ_HZ):
            raise ValueError(
                f"Frequency {freq_hz / 1e6:.3f} MHz is outside RTL-SDR Blog V3 limits ({self.MIN_FREQ_HZ / 1e6} to {self.MAX_FREQ_HZ / 1e6} MHz)."
            )
        self._center_freq_hz = freq_hz
        if self._sdr is not None:
            self._sdr.center_freq = freq_hz

    def get_center_freq(self) -> float:
        """Returns currently configured center frequency in Hz."""
        if self._sdr is not None:
            self._center_freq_hz = float(self._sdr.center_freq)
        return self._center_freq_hz

    @property
    def center_freq(self) -> float:
        return self.get_center_freq()

    def set_sample_rate(self, rate_hz: float):
        """Sets ADC sample rate in Hz."""
        self._sample_rate = rate_hz
        if self._sdr is not None:
            self._sdr.sample_rate = rate_hz

    def get_sample_rate(self) -> float:
        """Returns currently configured sample rate in Hz."""
        if self._sdr is not None:
            self._sample_rate = float(self._sdr.sample_rate)
        return self._sample_rate

    @property
    def sample_rate(self) -> float:
        return self.get_sample_rate()

    def set_gain(self, gain_db: float, auto: bool = False):
        """Sets tuner gain in dB or activates hardware AGC."""
        self._auto_gain = auto
        self._gain = gain_db
        if self._sdr is not None:
            if auto:
                self._sdr.set_gain('auto')
            else:
                self._sdr.set_gain(gain_db)

    def get_gain(self) -> float:
        """Returns current gain value in dB."""
        if self._sdr is not None:
            try:
                g = self._sdr.get_gain()
                if isinstance(g, (int, float)):
                    self._gain = float(g)
            except Exception:
                pass
        return self._gain

    def get_valid_gains(self) -> List[float]:
        """Returns list of supported hardware gain values in dB."""
        if self._sdr is not None:
            return [float(g) for g in self._sdr.valid_gains_db]
        return [0.0, 0.9, 1.4, 2.7, 3.7, 7.7, 8.7, 12.5, 14.4, 15.7, 16.6, 19.7, 20.7, 22.9, 25.4, 28.0, 29.7, 32.8, 33.8, 36.4, 37.2, 38.6, 40.2, 42.1, 43.4, 43.9, 44.5, 48.0, 49.6]

    def set_ppm_correction(self, ppm: int):
        """Sets frequency correction in PPM (parts per million)."""
        self._ppm_correction = ppm
        if self._sdr is not None and ppm != 0:
            try:
                self._sdr.freq_correction = ppm
            except Exception as e:
                logger.warning(f"Could not set ppm correction ({ppm}): {e}")

    def read_samples(self, num_samples: int = 131072) -> np.ndarray:
        """
        Reads complex I/Q samples synchronously from the RTL-SDR.
        Returns a 1D numpy array of complex128/complex64 samples.
        """
        if not self.is_connected:
            raise RuntimeError("Cannot read samples: RTL-SDR is not connected.")
        samples = self._sdr.read_samples(num_samples)
        return samples

    def get_device_info(self) -> dict:
        """Returns descriptive metadata about the connected hardware."""
        if not self.is_connected:
            return {"status": "Disconnected", "name": "None"}
        return {
            "status": "Connected",
            "name": "RTL-SDR Blog V3 (Rafael Micro R820T)",
            "center_freq_mhz": self._center_freq_hz / 1e6,
            "sample_rate_msps": self._sample_rate / 1e6,
            "gain_db": self.get_gain(),
            "auto_gain": self._auto_gain,
            "ppm": self._ppm_correction,
        }

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
