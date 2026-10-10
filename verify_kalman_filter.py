"""
Verification Script: Kalman Filter for RSSI & Spectral Smoothing.
Tests noise variance reduction, step response tracking, and vectorized PSD smoothing.
"""

import sys
import os
import time
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.dsp.kalman_filter import KalmanFilter1D, VectorKalmanSmoother


def run_kalman_verification():
    print("=" * 70)
    print("  VERIFICATION SUITE: KALMAN FILTER RSSI & SPECTRAL SMOOTHING")
    print("=" * 70)

    # 1. 1D Scalar RSSI Smoothing Test
    print("\n--- [PART 1] 1D Scalar Kalman Filter: Noise Variance Reduction ---")
    np.random.seed(42)
    n_samples = 500
    true_rssi = -45.0  # Constant true signal at -45 dBm
    noise_sigma = 3.0   # 3 dB measurement noise jitter
    noisy_measurements = true_rssi + np.random.randn(n_samples) * noise_sigma

    kf = KalmanFilter1D(process_variance=1e-3, measurement_variance=9.0)
    filtered = kf.batch_filter(noisy_measurements)

    raw_var = np.var(noisy_measurements[50:])
    filtered_var = np.var(filtered[50:])
    variance_reduction_ratio = raw_var / (filtered_var + 1e-12)

    print(f"  True Signal Level       : {true_rssi:.1f} dBm")
    print(f"  Raw Measurement Variance: {raw_var:.2f} dB^2 (Std: {np.sqrt(raw_var):.2f} dB)")
    print(f"  Kalman Filtered Variance: {filtered_var:.2f} dB^2 (Std: {np.sqrt(filtered_var):.2f} dB)")
    print(f"  Jitter Reduction Factor : {variance_reduction_ratio:.1f}x reduction")

    assert variance_reduction_ratio > 3.0, "Kalman filter should significantly reduce measurement variance."
    print("  [PASS] 1D Kalman Filter successfully smoothed noisy RSSI.")

    # 2. Dynamic Step Tracking Test (Transient Response)
    print("\n--- [PART 2] Step Response Tracking Under Sudden Signal Attenuation ---")
    step_signal = np.concatenate([
        np.full(100, -35.0) + np.random.randn(100) * 1.5,   # Unshielded
        np.full(100, -55.0) + np.random.randn(100) * 1.5    # Shield applied (20 dB drop)
    ])
    step_filtered = kf.batch_filter(step_signal)
    settled_level = np.mean(step_filtered[150:])

    print(f"  Initial State (Baseline) : {np.mean(step_filtered[50:100]):.2f} dBm")
    print(f"  Attenuated State (Shield): {settled_level:.2f} dBm (Expected: -55.0 dBm)")
    assert abs(settled_level - (-55.0)) < 1.0, "Kalman filter must track true step attenuation within 1 dB."
    print("  [PASS] Step response converges accurately to new physical state.")

    # 3. Vectorized FFT Spectrum Smoother
    print("\n--- [PART 1] Vectorized Spectral Kalman Smoother Benchmark ---")
    fft_size = 2048
    v_smoother = VectorKalmanSmoother(
        fft_size=fft_size,
        process_variance=0.01,
        measurement_variance=4.0,
        adaptive_threshold=4.5
    )

    # Generate baseline noisy spectrum frame with a sharp carrier at bin 1000
    base_spectrum = np.full(fft_size, -90.0)
    base_spectrum[1000] = -30.0  # Strong peak

    num_frames = 100
    t0 = time.perf_counter()
    for _ in range(num_frames):
        noisy_frame = base_spectrum + np.random.randn(fft_size) * 2.0
        noisy_frame[1000] = -30.0 + np.random.randn() * 0.5
        smoothed_frame = v_smoother.update(noisy_frame)
    dt = time.perf_counter() - t0
    ms_per_frame = (dt / num_frames) * 1000.0

    peak_preserved = abs(smoothed_frame[1000] - (-30.0)) < 1.5
    noise_reduced = np.std(smoothed_frame[100:900]) < 1.0

    print(f"  Benchmark Frames         : {num_frames} frames (FFT size = {fft_size})")
    print(f"  Vector Processing Time   : {ms_per_frame:.3f} ms per frame")
    print(f"  Peak Signal Preserved    : {'YES' if peak_preserved else 'NO'}")
    print(f"  Floor Noise Suppressed   : {'YES' if noise_reduced else 'NO'}")
    assert peak_preserved and noise_reduced, "Vector Kalman filter must preserve carrier while smoothing floor."
    print("  [PASS] Vectorized Spectral Kalman Smoother verified.")

    # 4. Immutability & Newly Appearing Carrier Response
    print("\n--- [PART 4] Verification of Copy-Immutability & Sudden Carrier Emergence ---")
    # Immutability check
    returned_copy = v_smoother.update(base_spectrum)
    returned_copy[0] = 999.0  # Mutate caller copy
    assert v_smoother.x[0] != 999.0, "Mutating returned spectrum must not mutate internal filter state."
    print("  [PASS] Returned spectrum is a detached copy; internal state is protected.")

    # Settle noise floor on empty spectrum
    settler = VectorKalmanSmoother(fft_size=1024)
    empty_noise = np.full(1024, -90.0)
    for _ in range(60):
        settler.update(empty_noise + np.random.randn(1024) * 1.0)

    # Carrier suddenly bursts at bin 500 (-30 dBFS)
    burst_frame = empty_noise.copy()
    burst_frame[500] = -30.0
    first_resp = settler.update(burst_frame)

    print(f"  Settled Floor Level     : -90.0 dBFS")
    print(f"  Burst Carrier Level     : -30.0 dBFS")
    print(f"  First Frame Filter Resp : {first_resp[500]:.2f} dBFS")
    assert first_resp[500] > -35.0, "Per-bin uncertainty inflation must track sudden carrier emergence within 1 frame."
    print("  [PASS] Newly emerging carrier promptly tracked via adaptive per-bin uncertainty.")

    print("\n" + "=" * 70)
    print("  ALL KALMAN FILTER VERIFICATION TESTS PASSED SUCCESSFULLY")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = run_kalman_verification()
    sys.exit(0 if success else 1)
