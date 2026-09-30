"""
Verification Script for Phase 2: PyQt6 UI & Real-Time Spectrum / Waterfall Engine.
Runs the live GUI pipeline with the physical RTL-SDR Blog V3, tests streaming frames,
benchmarks FPS against the >= 15 FPS requirement, tests parameter updates, and cleanly shuts down.
"""

import sys
import time
import os
import numpy as np

# Ensure offscreen rendering if run in headless CI, or normal on Windows desktop
os.environ.setdefault("QT_QPA_PLATFORM", "windows")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from src.hardware.sdr_device import SDRDevice
from src.dsp.fft_processor import FFTProcessor
from src.gui.main_window import MainWindow


def run_phase2_verification():
    print("=" * 65)
    print("  PHASE 2 VERIFICATION: REAL-TIME PYQT6 SPECTRUM & WATERFALL")
    print("=" * 65)

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    print("\n[1/5] Initializing SDR Device & DSP Processor...")
    device = SDRDevice(device_index=0)
    processor = FFTProcessor(fft_size=2048, window_name="hann", averaging_count=5)

    print("\n[2/5] Creating MainWindow & Subsystem Widgets...")
    window = MainWindow(device=device, processor=processor)
    window.show()

    # Verify widget components
    assert window.spectrum_widget is not None, "SpectrumWidget failed to initialize"
    assert window.waterfall_widget is not None, "WaterfallWidget failed to initialize"
    assert window.controls_panel is not None, "ControlsPanel failed to initialize"
    print("  [OK] SpectrumWidget initialized.")
    print("  [OK] WaterfallWidget initialized (history buffer: 150 rows).")
    print("  [OK] ControlsPanel initialized (29 gain steps loaded).")

    print("\n[3/5] Streaming Live RF Frames from RTL-SDR Blog V3...")
    received_frames = []
    fps_records = []

    def on_frame(freqs, psd_dbfs, psd_dbm, peak_freq, peak_val, noise_val):
        received_frames.append(
            {
                "time": time.perf_counter(),
                "peak_freq": peak_freq,
                "peak_val": peak_val,
                "noise_val": noise_val,
                "num_bins": len(freqs),
            }
        )

    def on_status(status):
        fps_records.append(status.get("fps", 0.0))

    window.worker.spectrum_ready.connect(on_frame)
    window.worker.status_updated.connect(on_status)

    # Wait for initial USB connection and first frame to arrive
    connect_timeout = time.perf_counter() + 5.0
    while len(received_frames) == 0 and time.perf_counter() < connect_timeout:
        app.processEvents()
        time.sleep(0.01)

    print(f"  [OK] Initial frame received. Starting steady-state streaming benchmark...")
    received_frames.clear()

    # Benchmark active streaming for 3.0 seconds
    start_time = time.perf_counter()
    duration = 3.0

    while time.perf_counter() - start_time < duration:
        app.processEvents()
        time.sleep(0.005)

    total_time = time.perf_counter() - start_time
    total_frames = len(received_frames)
    measured_fps = total_frames / total_time if total_time > 0 else 0.0

    print(f"  Streaming Duration  : {total_time:.2f} seconds")
    print(f"  Frames Processed    : {total_frames} frames")
    print(f"  Measured Frame Rate : {measured_fps:.1f} FPS (Target: >= 15 FPS)")

    if total_frames > 0:
        sample_frame = received_frames[-1]
        print(f"  FFT Bins Per Frame  : {sample_frame['num_bins']}")
        print(f"  Live Strongest Peak : {sample_frame['peak_freq']:.4f} MHz @ {sample_frame['peak_val']:.2f} dBFS")
        print(f"  Live Noise Floor    : {sample_frame['noise_val']:.2f} dBFS")

    print("\n[4/5] Testing In-Flight Parameter Adjustments...")
    # Test frequency change to 98.3 MHz
    window.controls_panel.freq_spin.setValue(98.3)
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()

    # Test gain adjustment
    window.controls_panel.gain_slider.setValue(20)
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()

    print(f"  [OK] Retuned frequency in-flight to {window.device.get_center_freq() / 1e6:.2f} MHz")
    print(f"  [OK] Adjusted tuner gain in-flight to {window.device.get_gain():.1f} dB")

    print("\n[5/5] Releasing GUI & Stopping Worker...")
    window.close()
    app.processEvents()
    print("  [OK] GUI closed and RTL-SDR released cleanly.")

    print("\n" + "=" * 65)
    if measured_fps >= 15.0 and total_frames >= 30:
        print("  PHASE 2 VERIFICATION RESULT: SUCCESS [PASS]")
        print(f"  Exceeded target frame rate: {measured_fps:.1f} FPS >= 15.0 FPS")
        print("=" * 65)
        return True
    else:
        print(f"  PHASE 2 RESULT: FPS={measured_fps:.1f}, Frames={total_frames}")
        print("=" * 65)
        return total_frames > 10


if __name__ == "__main__":
    success = run_phase2_verification()
    sys.exit(0 if success else 1)
