"""
Verification Script for Phase 5: Persistent Survey Data Logging & Multi-Location Export Engine (FR-08).
Tests SQLite database CRUD operations, interval throttling, spatial location summaries,
CSV exports, academic HTML report generation, and real-time GUI integration.
"""

import sys
import os
import time
import tempfile
import csv
import numpy as np

if sys.platform == "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "windows")

# Ensure project root is in system path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if hasattr(os, "add_dll_directory"):
    try:
        os.add_dll_directory(PROJECT_ROOT)
    except Exception:
        pass

from PyQt6.QtWidgets import QApplication

from src.storage.survey_database import SurveyDatabase
from src.storage.survey_logger import SurveyLogger
from src.storage.report_generator import ReportGenerator
from src.exposure.exposure_index import ExposureMetrics, ExposureIndexEngine
from src.dsp.peak_detector import DetectedPeak, PeakDetector
from src.shielding.differential_engine import ShieldingResult
from src.hardware.sdr_device import SDRDevice
from src.dsp.fft_processor import FFTProcessor
from src.gui.main_window import MainWindow


def test_survey_database_crud() -> bool:
    print("\n--- Sub-test 1: Survey Database CRUD, Stats & CSV Exports ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_surveys.db")
        db = SurveyDatabase(db_path=db_path)

        # 1. Insert multiple survey records across two locations
        sample1 = {
            "timestamp": "2026-10-05T10:00:00",
            "location_id": "Comm Lab (Room 101)",
            "center_freq_mhz": 100.0,
            "sample_rate_msps": 2.4,
            "freq_start_mhz": 98.8,
            "freq_end_mhz": 101.2,
            "peak_power_dbfs": -35.2,
            "peak_freq_mhz": 100.1,
            "avg_power_dbfs": -68.4,
            "noise_floor_dbfs": -75.0,
            "dominant_band": "FM Broadcast (88 - 108 MHz)",
            "exposure_score": 45,
            "exposure_tier": "Medium",
            "active_carriers_count": 3,
            "notes": "Near bench 4",
        }
        id1 = db.insert_survey_log(sample1)
        assert id1 > 0, f"Failed to insert survey record 1: id={id1}"

        sample2 = {
            "timestamp": "2026-10-05T10:05:00",
            "location_id": "Server Room (Admin Block)",
            "center_freq_mhz": 900.0,
            "sample_rate_msps": 2.4,
            "freq_start_mhz": 898.8,
            "freq_end_mhz": 901.2,
            "peak_power_dbfs": -22.5,
            "peak_freq_mhz": 900.4,
            "avg_power_dbfs": -55.1,
            "noise_floor_dbfs": -70.0,
            "dominant_band": "GSM 900 Downlink",
            "exposure_score": 75,
            "exposure_tier": "High",
            "active_carriers_count": 5,
            "notes": "Next to rack 2",
        }
        id2 = db.insert_survey_log(sample2)
        assert id2 > id1, f"Expected autoincrement ID, got {id2}"

        # 2. Test recent records query & filtering
        all_logs = db.get_recent_survey_logs(limit=10)
        assert len(all_logs) == 2, f"Expected 2 records, got {len(all_logs)}"
        assert all_logs[0]["id"] == id2, "Expected newest record first"

        comm_logs = db.get_recent_survey_logs(limit=10, location_id="Comm Lab (Room 101)")
        assert len(comm_logs) == 1 and comm_logs[0]["location_id"] == "Comm Lab (Room 101)", "Location filter failed"

        # 3. Test aggregate statistics
        stats = db.get_survey_statistics()
        assert stats["total_entries"] == 2, f"Expected 2 total entries, got {stats['total_entries']}"
        assert abs(stats["max_peak_dbfs"] - (-22.5)) < 0.1, f"Expected max peak -22.5, got {stats['max_peak_dbfs']}"

        # 4. Test spatial location summaries
        locs = db.get_locations_summary()
        assert len(locs) == 2, f"Expected 2 locations, got {len(locs)}"
        server_loc = [l for l in locs if "Server Room" in l["location_id"]][0]
        assert server_loc["highest_tier"] == "High", f"Expected High tier for server room, got {server_loc['highest_tier']}"

        # 5. Insert shielding test record
        sh_record = {
            "timestamp": "2026-10-05T10:10:00",
            "material_name": "Multi-layer Aluminum Foil",
            "baseline_peak_dbfs": -30.0,
            "live_peak_dbfs": -55.0,
            "se_peak_db": 25.0,
            "percentage_reduction": 99.68,
            "attenuation_ratio": 316.2,
            "rating": "EXCELLENT SHIELDING",
            "center_freq_mhz": 100.0,
            "notes": "3 layers wrapped tight",
        }
        sh_id = db.insert_shielding_log(sh_record)
        assert sh_id > 0, "Failed to insert shielding log"

        sh_logs = db.get_recent_shielding_logs(limit=10)
        assert len(sh_logs) == 1, f"Expected 1 shielding log, got {len(sh_logs)}"
        assert sh_logs[0]["se_peak_db"] == 25.0, "Shielding SE mismatch"

        # 6. Test CSV Export for Surveys
        csv_survey_path = os.path.join(tmp_dir, "survey_export.csv")
        exported_survey_count = db.export_survey_to_csv(csv_survey_path)
        assert exported_survey_count == 2, f"Expected 2 exported survey rows, got {exported_survey_count}"
        with open(csv_survey_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            assert "location_id" in header and "peak_power_dbfs" in header, "CSV header missing fields"
            rows = list(reader)
            assert len(rows) == 2, f"Expected 2 CSV data rows, got {len(rows)}"

        # 7. Test CSV Export for Shielding
        csv_shielding_path = os.path.join(tmp_dir, "shielding_export.csv")
        exported_sh_count = db.export_shielding_to_csv(csv_shielding_path)
        assert exported_sh_count == 1, f"Expected 1 exported shielding row, got {exported_sh_count}"
        with open(csv_shielding_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            assert "material_name" in header and "se_peak_db" in header, "Shielding CSV header missing"

        # 8. Test Clear Operations
        db.clear_survey_logs(location_id="Comm Lab (Room 101)")
        remaining = db.get_recent_survey_logs(limit=10)
        assert len(remaining) == 1, f"Expected 1 remaining record after selective clear, got {len(remaining)}"

        db.clear_shielding_logs()
        assert len(db.get_recent_shielding_logs()) == 0, "Shielding logs failed to clear"

    print("  [PASS] SurveyDatabase CRUD, indexing, aggregates, and CSV export verified.")
    return True


def test_survey_logger_throttling_and_snapshots() -> bool:
    print("\n--- Sub-test 2: SurveyLogger Session & Time Throttling ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_logger.db")
        db = SurveyDatabase(db_path=db_path)
        logger = SurveyLogger(db=db)

        logged_events = []
        logger.survey_logged.connect(lambda rec: logged_events.append(rec))

        freq_axis = np.linspace(98.8, 101.2, 2048)
        psd_dbfs = np.full(2048, -75.0)
        psd_dbfs[1024] = -32.0  # Peak carrier

        peak = DetectedPeak(
            freq_mhz=100.0,
            power_dbfs=-32.0,
            snr_db=43.0,
            bw_3db_khz=180.0,
            bw_10db_khz=250.0,
            bin_index=1024,
            band_label="FM Broadcast",
        )
        exposure = ExposureMetrics(
            score=48,
            tier="Medium",
            color_hex="#f59e0b",
            total_power_dbfs=-32.0,
            total_power_dbm=-42.0,
            status_summary="Elevated FM power",
            advice="Acceptable for general public",
        )

        # 1. Without starting session, process_frame should return False
        accepted = logger.process_frame(
            freq_axis_mhz=freq_axis,
            psd_dbfs=psd_dbfs,
            peak_freq_mhz=100.0,
            peak_power_dbfs=-32.0,
            noise_floor_dbfs=-75.0,
            peaks=[peak],
            dominant_band="FM Broadcast",
            exposure=exposure,
            center_freq_mhz=100.0,
            sample_rate_msps=2.4,
        )
        assert not accepted, "Logger processed frame when session was idle"
        assert len(logged_events) == 0

        # 2. Start session with 0.2s interval
        logger.start_session("Comm Lab (Room 101)", interval_sec=0.2, notes="Automated test session")
        assert logger.is_recording, "Logger failed to enter recording state"

        # First frame should be accepted immediately
        accepted1 = logger.process_frame(
            freq_axis_mhz=freq_axis,
            psd_dbfs=psd_dbfs,
            peak_freq_mhz=100.0,
            peak_power_dbfs=-32.0,
            noise_floor_dbfs=-75.0,
            peaks=[peak],
            dominant_band="FM Broadcast",
            exposure=exposure,
            center_freq_mhz=100.0,
            sample_rate_msps=2.4,
        )
        assert accepted1, "First frame in active session was rejected"
        assert len(logged_events) == 1

        # Rapidly sending second frame immediately (< 0.2s) should be throttled
        accepted2 = logger.process_frame(
            freq_axis_mhz=freq_axis,
            psd_dbfs=psd_dbfs,
            peak_freq_mhz=100.0,
            peak_power_dbfs=-32.0,
            noise_floor_dbfs=-75.0,
            peaks=[peak],
            dominant_band="FM Broadcast",
            exposure=exposure,
            center_freq_mhz=100.0,
            sample_rate_msps=2.4,
        )
        assert not accepted2, "Throttling failed: frame accepted within interval window"
        assert len(logged_events) == 1

        # Wait 0.22s, next frame should be accepted
        time.sleep(0.22)
        accepted3 = logger.process_frame(
            freq_axis_mhz=freq_axis,
            psd_dbfs=psd_dbfs,
            peak_freq_mhz=100.0,
            peak_power_dbfs=-32.0,
            noise_floor_dbfs=-75.0,
            peaks=[peak],
            dominant_band="FM Broadcast",
            exposure=exposure,
            center_freq_mhz=100.0,
            sample_rate_msps=2.4,
        )
        assert accepted3, "Frame rejected after interval elapsed"
        assert len(logged_events) == 2

        # 3. Test Manual Snapshot
        snap_rec = logger.log_snapshot(
            freq_axis_mhz=freq_axis,
            psd_dbfs=psd_dbfs,
            peak_freq_mhz=100.0,
            peak_power_dbfs=-32.0,
            noise_floor_dbfs=-75.0,
            peaks=[peak],
            dominant_band="FM Broadcast",
            exposure=exposure,
            center_freq_mhz=100.0,
            sample_rate_msps=2.4,
            location_id="Library & Study Hall",
            notes="Snapshot verification",
        )
        assert snap_rec["location_id"] == "Library & Study Hall"
        assert len(logged_events) == 3

        logger.stop_session()
        assert not logger.is_recording, "Logger failed to stop session"

    print("  [PASS] SurveyLogger session states, throttling, and snapshot operations verified.")
    return True


def test_academic_report_generator() -> bool:
    print("\n--- Sub-test 3: Academic Survey Report Generation (HTML) ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "report_test.db")
        db = SurveyDatabase(db_path=db_path)

        # Seed data
        db.insert_survey_log({
            "timestamp": "2026-10-05T11:00:00",
            "location_id": "DSP Lab (Room 105)",
            "center_freq_mhz": 433.92,
            "sample_rate_msps": 2.4,
            "freq_start_mhz": 432.72,
            "freq_end_mhz": 435.12,
            "peak_power_dbfs": -41.0,
            "peak_freq_mhz": 433.92,
            "avg_power_dbfs": -72.0,
            "noise_floor_dbfs": -78.0,
            "dominant_band": "ISM 433 MHz",
            "exposure_score": 32,
            "exposure_tier": "Low",
            "active_carriers_count": 1,
            "notes": "Low power telemetry beacon",
        })

        db.insert_shielding_log({
            "timestamp": "2026-10-05T11:05:00",
            "material_name": "Copper Wire Mesh Enclosure",
            "baseline_peak_dbfs": -28.0,
            "live_peak_dbfs": -47.0,
            "se_peak_db": 19.0,
            "percentage_reduction": 98.74,
            "attenuation_ratio": 79.4,
            "rating": "GOOD SHIELDING",
            "center_freq_mhz": 433.92,
            "notes": "0.5mm mesh pitch grounded to chassis",
        })

        report_gen = ReportGenerator(db=db)
        html_out = os.path.join(tmp_dir, "survey_report.html")
        abs_path = report_gen.generate_html_report(html_out)

        assert os.path.exists(abs_path), f"Report file was not created: {abs_path}"
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check expected institutional and technical content
        assert "KLS Vishwanathrao Deshpande Institute of Technology" in content
        assert "DSP Lab (Room 105)" in content
        assert "Copper Wire Mesh Enclosure" in content
        assert "19.0 dB" in content
        assert "ISM 433 MHz" in content
        assert "GOOD SHIELDING" in content

    print("  [PASS] ReportGenerator produced valid, formatted HTML academic report.")
    return True


def run_phase5_verification() -> bool:
    print("=" * 65)
    print("  PHASE 5 VERIFICATION: PERSISTENT SURVEY LOGGING & REPORTING")
    print("=" * 65)

    assert test_survey_database_crud(), "Database CRUD test failed"
    assert test_survey_logger_throttling_and_snapshots(), "Survey logger test failed"
    assert test_academic_report_generator(), "Report generator test failed"

    print("\n--- Sub-test 4: Live Hardware & SurveyPanel Integration ---")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    device = SDRDevice(device_index=0)
    processor = FFTProcessor(fft_size=2048, window_name="hann", averaging_count=5)
    window = MainWindow(device=device, processor=processor)
    window.show()

    assert window.survey_panel is not None, "SurveyPanel not mounted"
    print("  [OK] SurveyPanel mounted in main window tab 4.")

    received_frames = []
    def on_frame(*args):
        received_frames.append(time.perf_counter())

    window.worker.spectrum_ready.connect(on_frame)

    # Wait for first frames and cache to be established
    timeout = time.perf_counter() + 6.0
    while (window._latest_spectrum_cache is None or len(received_frames) < 3) and time.perf_counter() < timeout:
        app.processEvents()
        time.sleep(0.02)

    if window._latest_spectrum_cache is None or len(received_frames) == 0:
        print("  [FAIL] Timed out waiting for RTL-SDR stream.")
        window.close()
        return False

    print(f"  [OK] Hardware stream established. First frame received at {received_frames[0]:.2f}s")

    # 1. Test live snapshot trigger from SurveyPanel
    initial_rows = window.survey_panel.table.rowCount()
    window.survey_panel._on_snapshot_clicked()
    for _ in range(15):
        app.processEvents()
        time.sleep(0.02)

    new_rows = window.survey_panel.table.rowCount()
    assert new_rows >= initial_rows + 1, f"Snapshot did not add row: before={initial_rows}, after={new_rows}"
    print(f"  [OK] Survey snapshot added to live table. Total table rows: {new_rows}")

    # 2. Test live recording session toggle
    window.survey_panel.interval_combo.setCurrentText("1.0s")
    window.survey_panel._on_toggle_recording()
    assert window.survey_logger.is_recording, "Survey session did not start"
    print("  [OK] Live recording session started (1.0s interval).")

    # Run for 2.5 seconds to capture ~2-3 periodic entries
    start_t = time.perf_counter()
    while time.perf_counter() - start_t < 2.5:
        app.processEvents()
        time.sleep(0.01)

    window.survey_panel._on_toggle_recording()
    assert not window.survey_logger.is_recording, "Survey session did not stop"
    logged_count = int(window.survey_panel.count_label.text().split(":")[-1].strip())
    print(f"  [OK] Live recording session stopped. Logged points in session: {logged_count}")
    assert logged_count >= 2, f"Expected >= 2 logged points in 2.5s, got {logged_count}"

    # 3. Test export from SurveyPanel
    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_file = os.path.join(tmp_dir, "live_export.csv")
        count = window.survey_db.export_survey_to_csv(csv_file)
        assert count >= logged_count, f"Exported {count} rows, expected at least {logged_count}"
        print(f"  [OK] Successfully exported {count} live survey rows to CSV.")

        html_file = os.path.join(tmp_dir, "live_report.html")
        window.survey_panel.report_gen.generate_html_report(html_file)
        assert os.path.exists(html_file), "Live HTML report failed to generate"
        print(f"  [OK] Successfully compiled academic HTML report ({os.path.getsize(html_file)} bytes).")

    # 4. Measure rendering frame rate across 30 frames
    frame_times = []
    def frame_tick(*args):
        frame_times.append(time.perf_counter())

    window.worker.spectrum_ready.connect(frame_tick)
    target_frames = 30
    run_timeout = time.perf_counter() + 5.0
    while len(frame_times) < target_frames and time.perf_counter() < run_timeout:
        app.processEvents()
        time.sleep(0.005)

    window.close()

    total_frames = len(frame_times)
    if total_frames > 1:
        elapsed = frame_times[-1] - frame_times[0]
        measured_fps = (total_frames - 1) / elapsed if elapsed > 0 else 0
    else:
        measured_fps = 0.0

    print(f"\n  [BENCHMARK] Sustained FPS with Survey Logging Active: {measured_fps:.1f} FPS (Target >= 15.0 FPS)")

    if measured_fps >= 15.0 and total_frames >= 20:
        print("\n" + "=" * 65)
        print("  PHASE 5 VERIFICATION RESULT: SUCCESS [PASS]")
        print("=" * 65)
        return True
    else:
        print(f"  [FAIL] Phase 5 Performance benchmark not met: FPS={measured_fps:.1f}")
        return False


if __name__ == "__main__":
    success = run_phase5_verification()
    sys.exit(0 if success else 1)
