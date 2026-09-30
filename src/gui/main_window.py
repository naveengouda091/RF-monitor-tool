"""
Main Application Window for RF Noise Monitoring and Reduction Analysis.
Integrates real-time PyQtGraph Spectrum and Waterfall displays with hardware controls.
"""

import sys
import logging
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
)

from src.hardware.sdr_device import SDRDevice
from src.hardware.worker import SDRWorker
from src.dsp.fft_processor import FFTProcessor
from src.gui.spectrum_widget import SpectrumWidget
from src.gui.waterfall_widget import WaterfallWidget
from src.gui.controls_panel import ControlsPanel
from src.gui.styles import DARK_STYLESHEET

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main graphical dashboard window."""

    def __init__(self, device: SDRDevice, processor: FFTProcessor):
        super().__init__()
        self.device = device
        self.processor = processor

        self.setWindowTitle("RF Noise Monitor & Reduction Analyzer | RTL-SDR Blog V3")
        self.resize(1280, 800)
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
        header.setContentsMargins(4, 2, 4, 6)

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

        # 2. Main Horizontal Splitter (Plots on Left, Controls on Right)
        h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Vertical Splitter for Spectrum and Waterfall
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        self.spectrum_widget = SpectrumWidget(self)
        self.waterfall_widget = WaterfallWidget(self)

        v_splitter.addWidget(self.spectrum_widget)
        v_splitter.addWidget(self.waterfall_widget)
        v_splitter.setStretchFactor(0, 3)
        v_splitter.setStretchFactor(1, 2)

        # Right: Sidebar Controls Panel
        valid_gains = self.device.get_valid_gains()
        self.controls_panel = ControlsPanel(valid_gains=valid_gains, parent=self)
        self.controls_panel.setFixedWidth(290)

        h_splitter.addWidget(v_splitter)
        h_splitter.addWidget(self.controls_panel)
        h_splitter.setStretchFactor(0, 1)
        h_splitter.setStretchFactor(1, 0)

        main_layout.addWidget(h_splitter)

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

    def _on_spectrum_data(
        self,
        freq_axis_mhz,
        psd_dbfs,
        psd_dbm,
        peak_freq_mhz,
        peak_power_dbfs,
        noise_floor_dbfs,
    ):
        """Dispatches fresh FFT frame to spectrum and waterfall widgets."""
        self.spectrum_widget.update_spectrum(
            freq_axis_mhz,
            psd_dbfs,
            psd_dbm,
            peak_freq_mhz,
            peak_power_dbfs,
            noise_floor_dbfs,
        )
        self.waterfall_widget.update_waterfall(freq_axis_mhz, psd_dbfs)

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

    def closeEvent(self, event):
        """Ensures worker thread and hardware are released cleanly on close."""
        self.status_bar.showMessage("Stopping acquisition...")
        self.worker.stop_acquisition()
        self.device.disconnect()
        event.accept()
