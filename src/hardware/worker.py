"""
Asynchronous QThread SDR Worker for non-blocking I/Q sample acquisition and DSP processing.
Emits PyQt signals to decouple real-time hardware I/O from the GUI thread.
"""

import time
import logging
from typing import Optional
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

from src.hardware.sdr_device import SDRDevice
from src.dsp.fft_processor import FFTProcessor

logger = logging.getLogger(__name__)


class SDRWorker(QThread):
    """
    Acquires I/Q data buffers from SDRDevice, processes FFT via FFTProcessor,
    and safely streams results to the GUI at target frame rates (>= 15 FPS).
    """

    # Signal signatures:
    # (freq_axis_mhz, psd_dbfs, psd_dbm, peak_freq_mhz, peak_power_dbfs, noise_floor_dbfs)
    spectrum_ready = pyqtSignal(object, object, object, float, float, float)
    status_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        device: SDRDevice,
        processor: FFTProcessor,
        target_fps: int = 30,
        parent=None,
    ):
        super().__init__(parent)
        self.device = device
        self.processor = processor
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps if target_fps > 0 else 0.033

        self._running = False
        self._paused = False
        self._mutex = QMutex()

        # Pending hardware updates applied safely inside the loop
        self._pending_freq: Optional[float] = None
        self._pending_gain: Optional[tuple] = None  # (gain_db, auto)
        self._pending_sr: Optional[float] = None

        # Performance monitoring
        self._fps_counter = 0
        self._fps_last_time = time.perf_counter()
        self._current_fps = 0.0

    def start_acquisition(self):
        """Starts the worker thread."""
        self._running = True
        self._paused = False
        self.start()

    def stop_acquisition(self):
        """Signals the worker thread to stop and waits for exit."""
        self._running = False
        self.wait(1500)

    def pause(self):
        """Pauses acquisition streaming."""
        with QMutexLocker(self._mutex):
            self._paused = True

    def resume(self):
        """Resumes acquisition streaming."""
        with QMutexLocker(self._mutex):
            self._paused = False

    def is_paused(self) -> bool:
        with QMutexLocker(self._mutex):
            return self._paused

    def request_frequency(self, freq_hz: float):
        """Thread-safe request to retune center frequency."""
        with QMutexLocker(self._mutex):
            self._pending_freq = freq_hz

    def request_gain(self, gain_db: float, auto: bool = False):
        """Thread-safe request to change tuner gain or toggle AGC."""
        with QMutexLocker(self._mutex):
            self._pending_gain = (gain_db, auto)

    def request_sample_rate(self, rate_hz: float):
        """Thread-safe request to change sample rate."""
        with QMutexLocker(self._mutex):
            self._pending_sr = rate_hz

    def run(self):
        """Main acquisition and processing loop."""
        logger.info("SDRWorker thread started.")

        if not self.device.is_connected:
            try:
                self.device.connect()
            except Exception as e:
                self.error_occurred.emit(str(e))
                return

        read_chunk_size = 32768  # ~13.6 ms of data at 2.4 MS/s

        while self._running:
            # Handle paused state
            with QMutexLocker(self._mutex):
                paused = self._paused
                pending_freq = self._pending_freq
                self._pending_freq = None
                pending_gain = self._pending_gain
                self._pending_gain = None
                pending_sr = self._pending_sr
                self._pending_sr = None

            if paused:
                time.sleep(0.05)
                continue

            # Apply pending hardware changes
            try:
                if pending_freq is not None:
                    self.device.set_center_freq(pending_freq)
                    self.processor.reset_averaging()
                if pending_gain is not None:
                    self.device.set_gain(pending_gain[0], pending_gain[1])
                if pending_sr is not None:
                    self.device.set_sample_rate(pending_sr)
                    self.processor.reset_averaging()
            except Exception as e:
                logger.error(f"Error applying hardware parameters: {e}")
                self.error_occurred.emit(f"Hardware tuning error: {e}")

            loop_start = time.perf_counter()

            # Acquire I/Q samples from RTL-SDR
            try:
                samples = self.device.read_samples(read_chunk_size)
            except Exception as e:
                logger.error(f"SDR read error: {e}")
                self.error_occurred.emit(f"Device disconnected or read error: {e}")
                break

            if len(samples) == 0:
                time.sleep(0.01)
                continue

            # Process FFT
            center_freq = self.device.get_center_freq()
            sample_rate = self.device.get_sample_rate()
            gain = self.device.get_gain()

            freq_axis, psd_dbfs, psd_dbm, peak_power, noise_floor = self.processor.process(
                samples=samples,
                center_freq_hz=center_freq,
                sample_rate_hz=sample_rate,
                tuner_gain_db=gain,
            )

            # Strongest peak frequency
            peak_idx = int(np.argmax(psd_dbfs))
            peak_freq_mhz = float(freq_axis[peak_idx])

            # Emit signal to GUI
            self.spectrum_ready.emit(
                freq_axis,
                psd_dbfs,
                psd_dbm,
                peak_freq_mhz,
                peak_power,
                noise_floor,
            )

            # Update FPS calculation
            self._fps_counter += 1
            now = time.perf_counter()
            elapsed_sec = now - self._fps_last_time
            if elapsed_sec >= 1.0:
                self._current_fps = self._fps_counter / elapsed_sec
                self._fps_counter = 0
                self._fps_last_time = now

                status = {
                    "connected": True,
                    "center_freq_mhz": center_freq / 1e6,
                    "sample_rate_msps": sample_rate / 1e6,
                    "gain_db": gain,
                    "fps": round(self._current_fps, 1),
                    "peak_power_dbfs": round(peak_power, 1),
                    "noise_floor_dbfs": round(noise_floor, 1),
                }
                self.status_updated.emit(status)

            # Rate-limit loop to prevent pegging 100% CPU on GUI event loop
            process_duration = time.perf_counter() - loop_start
            sleep_time = self.frame_interval - process_duration
            if sleep_time > 0.001:
                time.sleep(sleep_time)

        logger.info("SDRWorker thread terminating.")
