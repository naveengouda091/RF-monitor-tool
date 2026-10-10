"""
1D Kalman Filter & Vectorized Spectral Kalman Smoother.
Ports adaptive state-space RSSI and spectrum smoothing from RFA-Gemini into RF-monitor-tool.

Mathematical Model:
- State equation:       x[k] = x[k-1] + w[k],   w[k] ~ N(0, Q)
- Measurement equation: z[k] = x[k] + v[k],     v[k] ~ N(0, R)
- Innovation:           y = z[k] - x[k|k-1]
- Adaptive Gating:      If |y| > 3.0 * sqrt(R), inflate P to quickly track physical steps
- Kalman Gain:          K = P[k|k-1] / (P[k|k-1] + R)
- State Update:         x[k|k] = x[k|k-1] + K * y
- Covariance Update:    P[k|k] = (1 - K) * P[k|k-1]
"""

from typing import Optional, Union, List
import numpy as np


class KalmanFilter1D:
    """
    1D discrete Kalman filter for optimal recursive smoothing of scalar RF metrics
    (e.g., RSSI, carrier peak power, noise floor) in low-SNR environments.
    Includes adaptive innovation tracking for rapid response to sudden shielding steps.
    """

    def __init__(self, process_variance: float = 0.05, measurement_variance: float = 1.0, adaptive_threshold: float = 3.0):
        """
        Args:
            process_variance: Q (process noise covariance, controls agility).
            measurement_variance: R (measurement noise covariance, controls smoothing).
            adaptive_threshold: Innovation factor (multiplied by sqrt(R)) to detect step changes.
        """
        self.q = float(process_variance)
        self.r = float(measurement_variance)
        self.adaptive_threshold = float(adaptive_threshold)
        self.x: float = 0.0
        self.p: float = 1.0
        self.initialized: bool = False

    def update(self, measurement: float) -> float:
        """Processes a new scalar measurement and returns the optimal posterior estimate."""
        z = float(measurement)
        if not self.initialized:
            self.x = z
            self.p = 1.0
            self.initialized = True
            return self.x

        # 1. Prediction step
        self.p = self.p + self.q

        # 2. Innovation check for fast step-response (e.g. Shield barrier suddenly applied)
        innovation = z - self.x
        sigma_r = np.sqrt(self.r)
        if abs(innovation) > self.adaptive_threshold * sigma_r:
            # Significant physical jump detected: temporarily increase state uncertainty
            self.p = max(self.p, float(abs(innovation)))

        # 3. Kalman gain & update
        k = self.p / (self.p + self.r)
        self.x = self.x + k * innovation
        self.p = (1.0 - k) * self.p

        return self.x

    def reset(self, initial_state: Optional[float] = None) -> None:
        """Resets filter state and estimation covariance."""
        if initial_state is not None:
            self.x = float(initial_state)
            self.initialized = True
        else:
            self.x = 0.0
            self.initialized = False
        self.p = 1.0

    def batch_filter(self, measurements: Union[np.ndarray, List[float]]) -> np.ndarray:
        """Filters an array of chronological measurements."""
        measurements = np.asarray(measurements, dtype=np.float64)
        out = np.empty_like(measurements)
        self.reset()
        for idx, val in enumerate(measurements):
            out[idx] = self.update(val)
        return out


class VectorKalmanSmoother:
    """
    Vectorized Kalman smoother for continuous real-time FFT / PSD spectrum arrays.
    Smoothes bin-by-bin noise floor jitter while tracking carrier peaks with low lag.
    """

    def __init__(
        self,
        fft_size: int = 2048,
        process_variance: float = 0.01,
        measurement_variance: float = 2.0,
        adaptive_threshold: float = 4.0
    ):
        self.fft_size = fft_size
        self.q = float(process_variance)
        self.r = float(measurement_variance)
        self.adaptive_threshold = float(adaptive_threshold)
        self.x: Optional[np.ndarray] = None
        self.p: np.ndarray = np.ones(fft_size, dtype=np.float64)

    def update(self, psd_frame: np.ndarray) -> np.ndarray:
        """Processes a 1D PSD frame (length equal to fft_size) and returns smoothed spectrum."""
        psd_frame = np.asarray(psd_frame, dtype=np.float64)
        if self.x is None or len(self.x) != len(psd_frame):
            self.fft_size = len(psd_frame)
            self.x = psd_frame.copy()
            self.p = np.ones(self.fft_size, dtype=np.float64)
            return self.x.copy()

        # Vectorized prediction
        self.p += self.q

        # Per-bin uncertainty inflation when innovation is large (promptly tracks new carriers)
        innovation = psd_frame - self.x
        abs_innov = np.abs(innovation)
        sigma_r = np.sqrt(self.r)
        large_innov_mask = abs_innov > (self.adaptive_threshold * sigma_r)
        if np.any(large_innov_mask):
            self.p[large_innov_mask] = np.maximum(self.p[large_innov_mask], abs_innov[large_innov_mask])

        # Vectorized Kalman gain & update
        k = self.p / (self.p + self.r)
        self.x += k * innovation
        self.p *= (1.0 - k)

        return self.x.copy()

    def reset(self) -> None:
        """Clears state."""
        self.x = None
        self.p = np.ones(self.fft_size, dtype=np.float64)
