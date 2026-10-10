"""
Main Application Window for RF Noise Monitoring and Reduction Analysis.
Integrates real-time PyQtGraph Spectrum and Waterfall displays, Indian/ITU-R3 Band Classification,
Peak Transmitters Table, Audience RF Exposure Index Gauge, and Live Shielding Differential Analyzer.
"""

import sys
import logging
from typing import Optional
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QLabel,
    QMessageBox,
    QStatusBar,
    QTabWidget,
)

from src.hardware.sdr_device import SDRDevice
from src.hardware.worker import SDRWorker
from src.dsp.fft_processor import FFTProcessor
from src.dsp.peak_detector import PeakDetector
from src.classifier.classifier import BandClassifier
from src.exposure.exposure_index import ExposureIndexEngine
from src.shielding.differential_engine import ShieldingDifferentialEngine
from src.storage.survey_database import SurveyDatabase
from src.storage.survey_logger import SurveyLogger
from src.gui.spectrum_widget import SpectrumWidget
from src.gui.waterfall_widget import WaterfallWidget
from src.gui.controls_panel import ControlsPanel
from src.gui.audience_cards import AudienceExposureCard
from src.gui.carrier_table import CarrierTableWidget
from src.gui.shielding_panel import ShieldingPanel
from src.gui.survey_panel import SurveyPanel
from src.gui.styles import DARK_STYLESHEET

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main graphical dashboard window."""

    def __init__(self, device: SDRDevice, processor: FFTProcessor):
        super().__init__()
        self.device = device
        self.processor = processor

        # DSP Analytics, Classification & Shielding Engines
        self.peak_detector = PeakDetector(min_prominence_db=6.0, min_distance_bins=15, max_peaks=8)
        self.band_classifier = BandClassifier()
        self.exposure_engine = ExposureIndexEngine()
        self.shielding_engine = ShieldingDifferentialEngine(target_baseline_frames=50)

        # Survey Data Storage & Session Logger (FR-08)
        self.survey_db = SurveyDatabase()
        self.survey_logger = SurveyLogger(db=self.survey_db, parent=self)
        self._latest_spectrum_cache = None

        self.setWindowTitle("RF Noise Monitor & Reduction Analyzer | RTL-SDR Blog V3")
        self.resize(1380, 880)
        self.setStyleSheet(DARK_STYLESHEET)

        # Build Worker Thread
        self.worker = SDRWorker(
            device=self.device,
            processor=self.processor,
            target_fps=30,
            parent=self,
        )

        self._init_ui()
        self._connect_signals()

        # Start streaming
        self.worker.start_acquisition()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # 1. Top Header Bar
        header = QHBoxLayout()
        header.setContentsMargins(4, 2, 4, 2)

        title_box = QVBoxLayout()
        title = QLabel("SDR-BASED RF NOISE MONITOR & REDUCTION ANALYZER")
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #f8fafc; letter-spacing: 0.5px;")
        subtitle = QLabel("KLS VDIT Haliyal | Dept. of Electronics & Communication Engineering")
        subtitle.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: 500;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        # Status Pills
        self.status_pill = QLabel("RTL-SDR: CONNECTED")
        self.status_pill.setStyleSheet(
            "background-color: rgba(16, 185, 129, 0.15); color: #10b981; "
            "border: 1px solid #10b981; border-radius: 6px; padding: 4px 10px; font-weight: 700; font-size: 11px;"
        )

        self.fps_pill = QLabel("FPS: --")
        self.fps_pill.setStyleSheet(
            "background-color: rgba(56, 189, 248, 0.15); color: #38bdf8; "
            "border: 1px solid #38bdf8; border-radius: 6px; padding: 4px 10px; font-weight: 700; font-size: 11px;"
        )

        self.peak_pill = QLabel("Peak: --- dBFS")
        self.peak_pill.setStyleSheet(
            "background-color: rgba(245, 158, 11, 0.15); color: #f59e0b; "
            "border: 1px solid #f59e0b; border-radius: 6px; padding: 4px 10px; font-weight: 700; font-size: 11px;"
        )

        self.noise_pill = QLabel("Floor: --- dBFS")
        self.noise_pill.setStyleSheet(
            "background-color: rgba(148, 163, 184, 0.15); color: #94a3b8; "
            "border: 1px solid #64748b; border-radius: 6px; padding: 4px 10px; font-weight: 700; font-size: 11px;"
        )

        header.addWidget(self.status_pill)
        header.addSpacing(6)
        header.addWidget(self.fps_pill)
        header.addSpacing(6)
        header.addWidget(self.peak_pill)
        header.addSpacing(6)
        header.addWidget(self.noise_pill)

        main_layout.addLayout(header)

        # 2. Audience Exposure Metric Ribbon
        self.audience_card = AudienceExposureCard(self)
        self.audience_card.presentation_mode_toggled.connect(self._on_presentation_mode)
        main_layout.addWidget(self.audience_card)

        # 3. Main Horizontal Splitter (Plots on Left, Tabs on Right)
        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Vertical Splitter for Spectrum and Waterfall
        self.v_splitter = QSplitter(Qt.Orientation.Vertical)
        self.spectrum_widget = SpectrumWidget(self)
        self.waterfall_widget = WaterfallWidget(self)

        self.v_splitter.addWidget(self.spectrum_widget)
        self.v_splitter.addWidget(self.waterfall_widget)
        self.v_splitter.setStretchFactor(0, 3)
        self.v_splitter.setStretchFactor(1, 2)
        # Synchronize frequency axes between spectrum analyzer and waterfall spectrogram
        self.waterfall_widget.plot_widget.setXLink(self.spectrum_widget.plot_widget)

        # Right: Tabbed Sidebar (Controls, Transmitters Table, Shielding Analysis)
        self.right_tabs = QTabWidget()
        self.right_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #1e293b;
                background-color: #131b2e;
                border-radius: 6px;
            }
            QTabBar::tab {
                background: #0b0f19;
                color: #94a3b8;
                padding: 6px 10px;
                border: 1px solid #1e293b;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: 600;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background: #131b2e;
                color: #38bdf8;
                border-color: #38bdf8;
            }
        """)

        valid_gains = self.device.get_valid_gains()
        self.controls_panel = ControlsPanel(valid_gains=valid_gains, parent=self)
        self.carrier_table = CarrierTableWidget(parent=self)
        self.shielding_panel = ShieldingPanel(parent=self)
        self.survey_panel = SurveyPanel(logger=self.survey_logger, db=self.survey_db, parent=self)

        self.right_tabs.addTab(self.controls_panel, "Tuner & Presets")
        self.right_tabs.addTab(self.carrier_table, "Active Transmitters")
        self.right_tabs.addTab(self.shielding_panel, "Shielding Analysis")
        self.right_tabs.addTab(self.survey_panel, "Survey & Logging")
        self.right_tabs.setFixedWidth(360)

        self.h_splitter.addWidget(self.v_splitter)
        self.h_splitter.addWidget(self.right_tabs)
        self.h_splitter.setStretchFactor(0, 1)
        self.h_splitter.setStretchFactor(1, 0)

        main_layout.addWidget(self.h_splitter)

        # Status Bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("background-color: #0b0f19; color: #64748b; font-size: 11px;")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Hardware streaming active | RTL-SDR Blog V3 ready")

    def _connect_signals(self):
        # Worker to GUI
        self.worker.spectrum_ready.connect(self._on_spectrum_data)
        self.worker.status_updated.connect(self._on_status_updated)
        self.worker.error_occurred.connect(self._on_error_occurred)

        # Controls to Worker & Processor
        self.controls_panel.frequency_changed.connect(self.worker.request_frequency)
        self.controls_panel.gain_changed.connect(self.worker.request_gain)
        self.controls_panel.sample_rate_changed.connect(self.worker.request_sample_rate)
        self.controls_panel.fft_size_changed.connect(self._on_fft_size_changed)
        self.controls_panel.window_changed.connect(self._on_window_changed)
        self.controls_panel.averaging_changed.connect(self._on_averaging_changed)
        self.controls_panel.pause_toggled.connect(self._on_pause_toggled)

        # Shielding Panel Signals
        self.shielding_panel.capture_baseline_requested.connect(self._on_capture_baseline_requested)
        self.shielding_panel.clear_baseline_requested.connect(self._on_clear_baseline_requested)
        self.shielding_panel.differential_mode_toggled.connect(self._on_diff_mode_toggled)
        self.shielding_panel.log_shielding_requested.connect(self._on_log_shielding_requested)

        # Survey Panel Signals
        self.survey_panel.snapshot_requested.connect(self._on_snapshot_requested)

    def _on_spectrum_data(
        self,
        freq_axis_mhz,
        psd_dbfs,
        psd_dbm,
        peak_freq_mhz,
        peak_power_dbfs,
        noise_floor_dbfs,
    ):
        """Processes analytics, shielding differentials, and updates UI components."""
        # 1. Detect peaks and compute occupied bandwidths
        peaks = self.peak_detector.detect(freq_axis_mhz, psd_dbfs, noise_floor_dbfs)

        # 2. Classify peaks according to Indian/ITU-R3 regulatory allocations
        peaks = self.band_classifier.classify_peaks(peaks)
        dominant_band = self.band_classifier.get_dominant_band(peaks)

        # 3. Compute Composite RF Exposure Index
        exposure = self.exposure_engine.compute(psd_dbfs, psd_dbm, peak_power_dbfs)
        max_snr = float(np.max([p.snr_db for p in peaks])) if peaks else float(peak_power_dbfs - noise_floor_dbfs)

        # 4. Shielding Baseline & Differential Processing
        if self.shielding_engine.is_capturing_baseline:
            complete, progress = self.shielding_engine.feed_baseline_frame(freq_axis_mhz, psd_dbfs)
            self.shielding_panel.update_capture_progress(int(progress * 100))
            if complete:
                base_info = self.shielding_engine.get_baseline()
                if base_info is not None:
                    base_freqs, base_psd = base_info
                    p0_peak = float(np.max(base_psd))
                    self.shielding_panel.set_baseline_ready(p0_peak)
                    self.spectrum_widget.set_baseline_curve(base_freqs, base_psd)
                    self.status_bar.showMessage(f"Baseline P0 captured across 50 frames. Peak: {p0_peak:.1f} dBFS")

        elif self.shielding_panel.diff_toggle.isChecked() and self.shielding_engine.has_baseline:
            mat_name = self.shielding_panel.get_material_name()
            diff = self.shielding_engine.compute_differential(freq_axis_mhz, psd_dbfs, material_name=mat_name)
            if diff is not None:
                delta_curve, res = diff
                self.shielding_panel.update_shielding_result(res)
                self.spectrum_widget.set_delta_curve(freq_axis_mhz, delta_curve)
            else:
                self.spectrum_widget.clear_delta_curve()
                self.shielding_panel._on_clear_clicked()
                self.status_bar.showMessage("Differential unavailable: please recapture baseline.")

        # 5. Survey Logging (FR-08: Throttled Periodic Persistence & Cache)
        center_mhz = float(self.device.center_freq / 1e6)
        sample_rate_mhz = float(self.device.sample_rate / 1e6)

        self._latest_spectrum_cache = {
            "freq_axis_mhz": freq_axis_mhz,
            "psd_dbfs": psd_dbfs,
            "peak_freq_mhz": peak_freq_mhz,
            "peak_power_dbfs": peak_power_dbfs,
            "noise_floor_dbfs": noise_floor_dbfs,
            "peaks": peaks,
            "dominant_band": dominant_band,
            "exposure": exposure,
            "center_freq_mhz": center_mhz,
            "sample_rate_msps": sample_rate_mhz,
        }

        self.survey_logger.process_frame(
            freq_axis_mhz=freq_axis_mhz,
            psd_dbfs=psd_dbfs,
            peak_freq_mhz=peak_freq_mhz,
            peak_power_dbfs=peak_power_dbfs,
            noise_floor_dbfs=noise_floor_dbfs,
            peaks=peaks,
            dominant_band=dominant_band,
            exposure=exposure,
            center_freq_mhz=center_mhz,
            sample_rate_msps=sample_rate_mhz,
        )

        # 6. Update Visual Displays
        self.spectrum_widget.update_spectrum(
            freq_axis_mhz,
            psd_dbfs,
            psd_dbm,
            peak_freq_mhz,
            peak_power_dbfs,
            noise_floor_dbfs,
            peaks=peaks,
        )
        self.waterfall_widget.update_waterfall(freq_axis_mhz, psd_dbfs)
        self.audience_card.update_metrics(exposure, dominant_band, len(peaks), max_snr)
        self.carrier_table.update_peaks(peaks)

    def _on_snapshot_requested(self, location_id: str, notes: str):
        """Captures immediate snapshot of current spectrum state."""
        if self._latest_spectrum_cache is not None:
            c = self._latest_spectrum_cache
            rec = self.survey_logger.log_snapshot(
                freq_axis_mhz=c["freq_axis_mhz"],
                psd_dbfs=c["psd_dbfs"],
                peak_freq_mhz=c["peak_freq_mhz"],
                peak_power_dbfs=c["peak_power_dbfs"],
                noise_floor_dbfs=c["noise_floor_dbfs"],
                peaks=c["peaks"],
                dominant_band=c["dominant_band"],
                exposure=c["exposure"],
                center_freq_mhz=c["center_freq_mhz"],
                sample_rate_msps=c["sample_rate_msps"],
                location_id=location_id,
                notes=notes,
            )
            self.status_bar.showMessage(
                f"Snapshot logged [{location_id}]: Peak {rec['peak_power_dbfs']:.1f} dBFS ({rec['dominant_band']})"
            )
        else:
            self.status_bar.showMessage("Snapshot unavailable: waiting for live spectrum frames.")

    def _on_log_shielding_requested(self, result):
        """Persists a measured shielding attenuation result."""
        center_mhz = float(self.device.center_freq / 1e6)
        rec = self.survey_logger.log_shielding_result(
            result=result,
            center_freq_mhz=center_mhz,
        )
        self.status_bar.showMessage(
            f"Shielding test logged: {rec['material_name']} (+{rec['se_peak_db']:.1f} dB SE, {rec['percentage_reduction']:.1f}% blocked)"
        )

    def _on_capture_baseline_requested(self, num_frames: int):
        self.shielding_engine.start_baseline_capture(num_frames)
        self.status_bar.showMessage(f"Acquiring {num_frames} reference baseline frames...")

    def _on_clear_baseline_requested(self):
        self.shielding_engine.clear_baseline()
        self.spectrum_widget.clear_baseline_curve()
        self.spectrum_widget.clear_delta_curve()
        self.status_bar.showMessage("Reference baseline cleared.")

    def _on_diff_mode_toggled(self, enabled: bool):
        if not enabled:
            self.spectrum_widget.clear_delta_curve()
            self.status_bar.showMessage("Shielding differential mode paused.")
        else:
            self.status_bar.showMessage("Live Shielding Differential Mode active. Measuring attenuation...")

    def _on_status_updated(self, status: dict):
        fps = status.get("fps", 0.0)
        peak = status.get("peak_power_dbfs", 0.0)
        noise = status.get("noise_floor_dbfs", 0.0)

        self.fps_pill.setText(f"FPS: {fps:.1f}")
        self.peak_pill.setText(f"Peak: {peak:.1f} dBFS")
        self.noise_pill.setText(f"Floor: {noise:.1f} dBFS")

    def _on_error_occurred(self, err_msg: str):
        self.status_pill.setText("RTL-SDR: ERROR")
        self.status_pill.setStyleSheet(
            "background-color: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid #ef4444;"
        )
        self.status_bar.showMessage(f"Error: {err_msg}")
        QMessageBox.critical(self, "Hardware Error", err_msg)

    def _on_fft_size_changed(self, size: int):
        self.processor.fft_size = size

    def _on_window_changed(self, name: str):
        self.processor.window_name = name

    def _on_averaging_changed(self, count: int):
        self.processor.averaging_count = count

    def _on_pause_toggled(self, is_paused: bool):
        if is_paused:
            self.worker.pause()
            self.status_bar.showMessage("Acquisition PAUSED")
        else:
            self.worker.resume()
            self.status_bar.showMessage("Acquisition RESUMED")

    def _on_presentation_mode(self, enabled: bool):
        """Toggles presentation mode: hides secondary tabs & waterfall to maximize gauge and spectrum."""
        self.waterfall_widget.setVisible(not enabled)
        self.right_tabs.setVisible(not enabled)
        if enabled:
            self.status_bar.showMessage("PRESENTATION MODE: Maximized spectrum and exposure gauge for demonstration")
        else:
            self.status_bar.showMessage("Hardware streaming active | RTL-SDR Blog V3 ready")

    def closeEvent(self, event):
        """Ensures worker thread and hardware are released cleanly on close."""
        self.status_bar.showMessage("Stopping acquisition...")
        stopped = self.worker.stop_acquisition(1500)
        if not stopped:
            logger.warning("Worker did not stop within timeout; terminating thread.")
            self.worker.terminate()
            self.worker.wait(500)
        if self.device.is_connected:
            self.device.disconnect()
        event.accept()
