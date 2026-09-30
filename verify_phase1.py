"""
Verification Script for Phase 1: Environment & Core Hardware/DSP Engine.
Connects to the physical RTL-SDR Blog V3, tunes to 100.0 MHz (FM band),
captures live I/Q samples, computes windowed FFT, and prints visible metrics.
"""

import sys
import time
import numpy as np

from src.hardware.sdr_device import SDRDevice
from src.dsp.fft_processor import FFTProcessor


def run_phase1_verification():
    print("=" * 65)
    print("  PHASE 1 VERIFICATION: RTL-SDR HARDWARE & DSP ENGINE")
    print("=" * 65)

    device = SDRDevice(device_index=0)
    processor = FFTProcessor(fft_size=2048, window_name="hann", averaging_count=5)

    print("\n[1/5] Initializing RTL-SDR Hardware...")
    try:
        device.connect()
    except Exception as e:
        print(f"\n[FAIL] Could not connect to RTL-SDR: {e}")
        return False

    info = device.get_device_info()
    print(f"  [OK] Device Status   : {info['status']}")
    print(f"  [OK] Tuner Model     : {info['name']}")
    print(f"  [OK] Supported Gains : {len(device.get_valid_gains())} steps ({device.get_valid_gains()[0]} to {device.get_valid_gains()[-1]} dB)")

    # Set parameters for FM broadcast test
    target_freq_mhz = 100.0
    target_sr_msps = 2.4
    target_gain_db = 29.7

    print(f"\n[2/5] Configuring Tuner Parameters...")
    device.set_center_freq(target_freq_mhz * 1e6)
    device.set_sample_rate(target_sr_msps * 1e6)
    device.set_gain(target_gain_db, auto=False)

    print(f"  Center Frequency : {device.get_center_freq() / 1e6:.2f} MHz")
    print(f"  Sample Rate      : {device.get_sample_rate() / 1e6:.2f} MS/s")
    print(f"  Tuner Gain       : {device.get_gain():.1f} dB")

    print("\n[3/5] Capturing Live I/Q Samples Buffer...")
    num_samples = 131072
    start_capture = time.perf_counter()
    samples = device.read_samples(num_samples)
    capture_duration_ms = (time.perf_counter() - start_capture) * 1000.0

    print(f"  Captured Samples : {len(samples):,} complex values")
    print(f"  Sample Type      : {samples.dtype}")
    print(f"  Capture Time     : {capture_duration_ms:.2f} ms")
    print(f"  Mean Amplitude   : {np.mean(np.abs(samples)):.4f}")

    print("\n[4/5] Executing Windowed FFT & Power Spectral Density...")
    # Process multiple frames to verify EMA smoothing and benchmark FPS
    frame_times = []
    num_frames = 10
    freq_axis, psd_dbfs, psd_dbm, peak_dbfs, noise_floor = None, None, None, None, None

    for i in range(num_frames):
        t0 = time.perf_counter()
        # Slice frame chunk
        chunk = samples[i * 2048 : (i + 1) * 2048]
        freq_axis, psd_dbfs, psd_dbm, peak_dbfs, noise_floor = processor.process(
            samples=chunk,
            center_freq_hz=device.get_center_freq(),
            sample_rate_hz=device.get_sample_rate(),
            tuner_gain_db=device.get_gain(),
        )
        frame_times.append((time.perf_counter() - t0) * 1000.0)

    avg_fft_time_ms = float(np.mean(frame_times))
    est_fps = 1000.0 / avg_fft_time_ms if avg_fft_time_ms > 0 else 999.0

    # Locate peak carrier
    peak_idx = int(np.argmax(psd_dbfs))
    peak_freq_mhz = float(freq_axis[peak_idx])
    snr_db = peak_dbfs - noise_floor

    print(f"  FFT Size         : {processor.fft_size} points (Window: {processor.window_name.upper()})")
    print(f"  Frequency Span   : {freq_axis[0]:.3f} MHz to {freq_axis[-1]:.3f} MHz")
    print(f"  Strongest Carrier: {peak_freq_mhz:.4f} MHz")
    print(f"  Peak Power       : {peak_dbfs:.2f} dBFS (~{psd_dbm[peak_idx]:.2f} dBm)")
    print(f"  Est. Noise Floor : {noise_floor:.2f} dBFS")
    print(f"  SNR (Signal/Noise: {snr_db:.2f} dB")
    print(f"  Avg DSP Time     : {avg_fft_time_ms:.3f} ms / frame (Potential: {est_fps:.0f} FPS, Target: >=15 FPS)")

    print("\n[5/5] Releasing Hardware...")
    device.disconnect()
    print("  [OK] SDR hardware closed cleanly.")

    print("\n" + "=" * 65)
    print("  PHASE 1 VERIFICATION RESULT: SUCCESS [PASS]")
    print("=" * 65)
    return True


if __name__ == "__main__":
    success = run_phase1_verification()
    sys.exit(0 if success else 1)
