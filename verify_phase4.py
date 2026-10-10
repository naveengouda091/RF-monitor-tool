"""
Verification Script for Phase 4: Shielding Analysis & Live Differential Engine.
Tests baseline acquisition, attenuation formulations, material rating tiering,
and live hardware streaming with differential spectrum overlay.
"""

import sys
import time
import os
import numpy as np

if sys.platform == "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "windows")

from PyQt6.QtWidgets import QApplication

from src.hardware.sdr_device import SDRDevice
from src.dsp.fft_processor import FFTProcessor
from src.shielding.differential_engine import ShieldingDifferentialEngine
from src.gui.main_window import MainWindow


def test_shielding_differential_math() -> bool:
    print("\n--- Sub-test 1: Shielding Differential Formulations & Material Tiers ---")
    engine = ShieldingDifferentialEngine(target_baseline_frames=10)
    freqs = np.linspace(98.8, 101.2, 2048)

    # 1. Simulate unshielded baseline (strong carrier at 100 MHz: -30 dBFS)
    unshielded_psd = np.full(2048, -75.0)
    unshielded_psd[1024] = -30.0  # Carrier peak

    engine.start_baseline_capture(num_frames=5)
    for _ in range(5):
        done, prog = engine.feed_baseline_frame(freqs, unshielded_psd)

    assert engine.has_baseline, "Baseline failed to finalize"
    print(f"  [PASS] Baseline recorded across 5 frames. Baseline peak: {np.max(engine.get_baseline()[1]):.1f} dBFS")

    # 2. Test high-attenuation material (Aluminum Foil: 25 dB drop)
    shielded_foil = np.full(2048, -75.0)
    shielded_foil[1024] = -55.0  # 25 dB drop from -30 dBFS
    delta_curve, res_foil = engine.compute_differential(freqs, shielded_foil, "Multi-layer Aluminum Foil")

    print(f"  Material: {res_foil.material_name}")
    print(f"    SE (Peak Attenuation) : +{res_foil.se_peak_db:.1f} dB")
    print(f"    Power Reduction       : {res_foil.percentage_reduction:.2f}%")
    print(f"    Attenuation Ratio     : {res_foil.attenuation_ratio:.1f}x")
    print(f"    Effectiveness Rating  : {res_foil.rating}")
    assert res_foil.se_peak_db == 25.0, f"Expected 25 dB, got {res_foil.se_peak_db}"
    assert res_foil.percentage_reduction >= 99.5, f"Expected >99.5% reduction, got {res_foil.percentage_reduction}"
    assert "EXCELLENT" in res_foil.rating, f"Expected EXCELLENT rating, got {res_foil.rating}"

    # 3. Test weak material (Plastic Enclosure: only 3 dB drop)
    shielded_plastic = np.full(2048, -75.0)
    shielded_plastic[1024] = -33.0  # 3 dB drop
    _, res_plastic = engine.compute_differential(freqs, shielded_plastic, "Plastic Enclosure")
    print(f"  Material: {res_plastic.material_name}")
    print(f"    SE (Peak Attenuation) : +{res_plastic.se_peak_db:.1f} dB")
    print(f"    Power Reduction       : {res_plastic.percentage_reduction:.2f}%")
    print(f"    Effectiveness Rating  : {res_plastic.rating}")
    assert "MINIMAL" in res_plastic.rating, f"Expected MINIMAL rating, got {res_plastic.rating}"

    return True


def run_phase4_verification() -> bool:
    print("=" * 65)
    print("  PHASE 4 VERIFICATION: SHIELDING LIVE DIFFERENTIAL ENGINE")
    print("=" * 65)

    assert test_shielding_differential_math(), "Math and tier unit test failed"

    print("\n--- Sub-test 2: Live Hardware & Shielding Panel Integration ---")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    device = SDRDevice(device_index=0)
    processor = FFTProcessor(fft_size=2048, window_name="hann", averaging_count=5)
    window = MainWindow(device=device, processor=processor)
    window.show()

    assert window.shielding_panel is not None, "ShieldingPanel not mounted"
    print("  [OK] ShieldingPanel mounted in main window tab 3.")

    received_frames = []
    def on_frame(*args):
        received_frames.append(time.perf_counter())

    window.worker.spectrum_ready.connect(on_frame)

    # Wait for first frame
    timeout = time.perf_counter() + 5.0
    while len(received_frames) == 0 and time.perf_counter() < timeout:
        app.processEvents()
        time.sleep(0.01)

    if len(received_frames) == 0:
        print("  [FAIL] Timed out waiting for RTL-SDR stream.")
        window.close()
        app.processEvents()
        return False

    print("  [OK] Initial stream connected.")

    # 1. Trigger Baseline Capture
    print("\n--- Sub-test 3: Triggering Live Baseline Capture (P0) ---")
    window.shielding_panel.capture_btn.click()
    app.processEvents()

    # Wait for 50 frames to be captured into baseline
    wait_baseline = time.perf_counter() + 6.0
    while window.shielding_engine.is_capturing_baseline and time.perf_counter() < wait_baseline:
        app.processEvents()
        time.sleep(0.02)

    assert window.shielding_engine.has_baseline, "Baseline capture did not complete within timeout"
    p0_info = window.shielding_engine.get_baseline()
    assert p0_info is not None, "Baseline data is None"
    base_freqs, base_psd = p0_info
    p0_peak = float(np.max(base_psd))
    print(f"  [OK] Live Baseline P0 recorded across 50 frames: Peak = {p0_peak:.1f} dBFS")
    assert window.spectrum_widget.baseline_curve.isVisible(), "Baseline curve should be visible on spectrum"
    print("  [OK] Baseline reference curve rendered on spectrum plot.")

    # 2. Benchmark streaming with Live Differential Mode active
    print("\n--- Sub-test 4: Live Differential Streaming Benchmark ---")
    assert window.shielding_panel.diff_toggle.isChecked(), "Differential toggle should be active"

    received_frames.clear()
    start_time = time.perf_counter()
    duration = 3.0

    while time.perf_counter() - start_time < duration:
        app.processEvents()
        time.sleep(0.005)

    total_time = time.perf_counter() - start_time
    total_frames = len(received_frames)
    measured_fps = total_frames / total_time if total_time > 0 else 0.0

    # Read live values from ShieldingPanel
    pct_text = window.shielding_panel.pct_val_label.text()
    se_text = window.shielding_panel.se_val_label.text()
    rating_text = window.shielding_panel.rating_badge.text()

    print(f"  Streaming Duration  : {total_time:.2f} seconds")
    print(f"  Frames Processed    : {total_frames} frames")
    print(f"  Measured Frame Rate : {measured_fps:.1f} FPS (Target: >= 15 FPS)")
    print(f"  Live Shielding UI   : {pct_text} | {se_text} | [{rating_text}]")
    print(f"  Delta Curve Status  : Visible={window.spectrum_widget.delta_curve.isVisible()}")

    # 3. Clean up
    window.shielding_panel.clear_btn.click()
    app.processEvents()
    assert not window.shielding_engine.has_baseline, "Baseline should be cleared"
    assert not window.spectrum_widget.baseline_curve.isVisible(), "Baseline curve should be hidden"
    print("  [OK] Baseline cleared and curves reset.")

    window.close()
    app.processEvents()
    print("  [OK] GUI closed and hardware released.")

    print("\n" + "=" * 65)
    if measured_fps >= 15.0 and total_frames >= 30:
        print("  PHASE 4 VERIFICATION RESULT: SUCCESS [PASS]")
        print(f"  Shielding Live Differential Mode sustained {measured_fps:.1f} FPS >= 15.0 FPS")
        print("=" * 65)
        return True
    else:
        print(f"  PHASE 4 RESULT: FAILED [FPS={measured_fps:.1f} < 15.0 or Frames={total_frames} < 30]")
        print("=" * 65)
        return False


if __name__ == "__main__":
    success = run_phase4_verification()
    sys.exit(0 if success else 1)
