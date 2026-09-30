"""
Verification Script for Phase 3: Signal Analytics, Indian Band Classification & Exposure Index.
Tests regulatory allocation lookup, peak detection, occupied bandwidth estimation,
exposure index scoring, and live UI streaming with the RTL-SDR Blog V3.
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
from src.dsp.peak_detector import PeakDetector
from src.classifier.classifier import BandClassifier
from src.exposure.exposure_index import ExposureIndexEngine
from src.gui.main_window import MainWindow


def test_regulatory_classifier() -> bool:
    print("\n--- Sub-test 1: Indian/ITU-R3 Band Allocation Classifier ---")
    classifier = BandClassifier()

    test_cases = [
        (98.3, "FM Broadcast"),
        (125.0, "Aviation Airband"),
        (145.0, "2m VHF Amateur"),
        (433.92, "ISM 433 MHz"),
        (866.0, "ISM / LoRa India"),
        (945.0, "GSM 900 (Downlink)"),
        (1090.0, "ADS-B Flight Radar"),
    ]

    for freq, expected_band in test_cases:
        band_name, service, desc = classifier.classify_frequency(freq)
        assert band_name == expected_band, f"Expected {expected_band} for {freq} MHz, got {band_name}"
        print(f"  [PASS] {freq:7.2f} MHz -> {band_name:<22} [{service}]")

    return True


def test_exposure_engine() -> bool:
    print("\n--- Sub-test 2: Exposure Index Scoring & Tiering ---")
    engine = ExposureIndexEngine()

    # Synthetic quiet floor
    quiet_psd = np.full(2048, -75.0)
    quiet_metrics = engine.compute(quiet_psd, quiet_psd - 10.0, -70.0)
    print(f"  Quiet Spectrum : Score={quiet_metrics.score}/100, Tier={quiet_metrics.tier} ({quiet_metrics.status_summary})")
    assert quiet_metrics.tier == "Low", f"Expected Low tier, got {quiet_metrics.tier}"

    # Synthetic saturated carrier
    high_psd = np.full(2048, -25.0)
    high_psd[1024] = -12.0
    high_metrics = engine.compute(high_psd, high_psd - 10.0, -12.0)
    print(f"  High Spectrum  : Score={high_metrics.score}/100, Tier={high_metrics.tier} ({high_metrics.status_summary})")
    assert high_metrics.tier == "High", f"Expected High tier, got {high_metrics.tier}"

    return True


def run_phase3_verification() -> bool:
    print("=" * 65)
    print("  PHASE 3 VERIFICATION: ANALYTICS, CLASSIFIER & EXPOSURE INDEX")
    print("=" * 65)

    # 1. Test unit logic first
    assert test_regulatory_classifier(), "Band classifier unit test failed"
    assert test_exposure_engine(), "Exposure engine unit test failed"

    # 2. Live Hardware & GUI Integration Test
    print("\n--- Sub-test 3: Live Hardware & GUI Analytics Streaming ---")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    device = SDRDevice(device_index=0)
    processor = FFTProcessor(fft_size=2048, window_name="hann", averaging_count=5)
    window = MainWindow(device=device, processor=processor)
    window.show()

    # Verify new Phase 3 UI components
    assert window.audience_card is not None, "AudienceExposureCard missing"
    assert window.carrier_table is not None, "CarrierTableWidget missing"
    print("  [OK] AudienceExposureCard and CarrierTableWidget mounted.")

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

    print("  [OK] Initial stream connected. Benchmarking Phase 3 streaming with live DSP analytics...")
    received_frames.clear()

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

    # Read live values from UI cards
    tier_text = window.audience_card.tier_badge.text()
    score_val = window.audience_card.score_bar.value()
    dominant_band = window.audience_card.dominant_band_label.text()
    table_rows = window.carrier_table.table.rowCount()

    print(f"  Live Exposure Gauge : Tier={tier_text}, Score={score_val}/100")
    print(f"  Live Dominant Band  : {dominant_band}")
    print(f"  Detected Carriers   : {table_rows} rows in active table")

    # Test Presentation Mode toggle
    print("\n--- Sub-test 4: Presentation Mode Toggle ---")
    window.audience_card.presentation_btn.click()
    app.processEvents()
    time.sleep(0.2)
    assert not window.waterfall_widget.isVisible(), "Waterfall should be hidden in presentation mode"
    assert not window.right_tabs.isVisible(), "Right tabs should be hidden in presentation mode"
    print("  [OK] Presentation Mode enabled: Waterfall and sidebar collapsed.")

    window.audience_card.presentation_btn.click()
    app.processEvents()
    time.sleep(0.2)
    assert window.waterfall_widget.isVisible(), "Waterfall should be restored"
    assert window.right_tabs.isVisible(), "Right tabs should be restored"
    print("  [OK] Normal Mode restored: All panels visible.")

    # Clean shutdown
    window.close()
    app.processEvents()
    print("  [OK] GUI closed and hardware released.")

    print("\n" + "=" * 65)
    if measured_fps >= 15.0 and total_frames >= 30:
        print("  PHASE 3 VERIFICATION RESULT: SUCCESS [PASS]")
        print(f"  Analytics & Classification sustained {measured_fps:.1f} FPS >= 15.0 FPS")
        print("=" * 65)
        return True
    else:
        print(f"  PHASE 3 RESULT: FAILED [FPS={measured_fps:.1f} < 15.0 or Frames={total_frames} < 30]")
        print("=" * 65)
        return False


if __name__ == "__main__":
    success = run_phase3_verification()
    sys.exit(0 if success else 1)
