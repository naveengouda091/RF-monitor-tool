"""
Real-time hardware-accelerated Spectrum Analyzer plot widget using PyQtGraph.
Displays Power vs. Frequency, noise floor line, peak markers, and mouse crosshair tracking.
"""

from typing import Optional
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton


class SpectrumWidget(QWidget):
    """Interactive Power Spectral Density (PSD) display widget."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Plot Widget Configuration
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#0d121f")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.25)
        self.plot_widget.setLabel("bottom", "Frequency", units="MHz")
        self.plot_widget.setLabel("left", "Amplitude", units="dBFS")
        self.plot_widget.setYRange(-115, 5, padding=0)
        self.plot_widget.getAxis("bottom").setPen(pg.mkPen("#475569"))
        self.plot_widget.getAxis("left").setPen(pg.mkPen("#475569"))

        # Main Spectrum Curve
        self.curve_pen = pg.mkPen(color="#38bdf8", width=1.5)
        self.curve_brush = pg.mkBrush(color=(56, 189, 248, 30))
        self.spectrum_curve = self.plot_widget.plot(
            pen=self.curve_pen,
            fillLevel=-115,
            fillBrush=self.curve_brush,
        )

        # Noise Floor Indicator Line
        self.noise_floor_line = pg.InfiniteLine(
            angle=0,
            movable=False,
            pen=pg.mkPen(color="#f59e0b", style=Qt.PenStyle.DashLine, width=1.2),
        )
        self.plot_widget.addItem(self.noise_floor_line, ignoreBounds=True)

        # Peak Marker Point
        self.peak_scatter = pg.ScatterPlotItem(
            size=10,
            pen=pg.mkPen(color="#ffffff", width=1.5),
            brush=pg.mkBrush("#ef4444"),
            symbol="o",
        )
        self.plot_widget.addItem(self.peak_scatter)

        # Baseline Reference Curve (P0)
        self.baseline_curve = self.plot_widget.plot(
            pen=pg.mkPen(color="#f8fafc", style=Qt.PenStyle.DashLine, width=1.3),
        )
        self.baseline_curve.setVisible(False)

        # Differential Delta Curve (P0 - P1)
        self.delta_curve = self.plot_widget.plot(
            pen=pg.mkPen(color="#10b981", width=1.8),
        )
        self.delta_curve.setVisible(False)

        # Crosshair cursor lines
        self.v_line = pg.InfiniteLine(
            angle=90, movable=False, pen=pg.mkPen("#64748b", style=Qt.PenStyle.DotLine)
        )
        self.h_line = pg.InfiniteLine(
            angle=0, movable=False, pen=pg.mkPen("#64748b", style=Qt.PenStyle.DotLine)
        )
        self.plot_widget.addItem(self.v_line, ignoreBounds=True)
        self.plot_widget.addItem(self.h_line, ignoreBounds=True)

        # Header controls & metrics bar
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(6, 2, 6, 2)

        self.title_label = QLabel("LIVE SPECTRUM ANALYZER")
        self.title_label.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 13px;")

        self.cursor_label = QLabel("Cursor: --- MHz | --- dBFS")
        self.cursor_label.setStyleSheet("color: #94a3b8; font-family: monospace; font-size: 12px;")

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["dBFS (Digital Full Scale)", "dBm (Estimated)"])
        self.unit_combo.currentIndexChanged.connect(self._on_unit_changed)
        self.unit_combo.setMaximumWidth(180)

        self.reset_btn = QPushButton("Reset View")
        self.reset_btn.setFixedHeight(24)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #f8fafc;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_view)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.cursor_label)
        header_layout.addSpacing(10)
        header_layout.addWidget(self.reset_btn)
        header_layout.addSpacing(6)
        header_layout.addWidget(self.unit_combo)

        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addLayout(header_layout)
        layout.addWidget(self.plot_widget)

        # Connect mouse hover tracker
        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)

        self._active_unit = "dBFS"
        self._last_freqs: Optional[np.ndarray] = None
        self._last_psd_dbfs: Optional[np.ndarray] = None
        self._last_psd_dbm: Optional[np.ndarray] = None
        self._last_f_min: Optional[float] = None
        self._last_f_max: Optional[float] = None

    def reset_view(self):
        """Resets both X and Y ranges to fit the current active frequency span."""
        if self._last_f_min is not None and self._last_f_max is not None:
            self.plot_widget.setXRange(self._last_f_min, self._last_f_max, padding=0)
        if self._active_unit == "dBFS":
            self.plot_widget.setYRange(-115, 5, padding=0)
        else:
            self.plot_widget.setYRange(-125, -5, padding=0)

    def _on_unit_changed(self, index: int):
        self._active_unit = "dBFS" if index == 0 else "dBm"
        self.plot_widget.setLabel("left", "Amplitude", units=self._active_unit)
        if self._active_unit == "dBFS":
            self.plot_widget.setYRange(-115, 5, padding=0)
            self.spectrum_curve.setFillLevel(-115)
        else:
            self.plot_widget.setYRange(-125, -5, padding=0)
            self.spectrum_curve.setFillLevel(-125)

        # Re-render immediately if we have current frame data
        if (
            self._last_freqs is not None
            and self._last_psd_dbfs is not None
            and self._last_psd_dbm is not None
        ):
            y_data = self._last_psd_dbfs if self._active_unit == "dBFS" else self._last_psd_dbm
            self.spectrum_curve.setData(self._last_freqs, y_data)
            dbm_offset = float(self._last_psd_dbm[0] - self._last_psd_dbfs[0]) if len(self._last_psd_dbfs) > 0 else 0.0
            if hasattr(self, "_last_noise_floor"):
                noise_val = self._last_noise_floor if self._active_unit == "dBFS" else (self._last_noise_floor + dbm_offset)
                self.noise_floor_line.setPos(noise_val)

    def _on_mouse_moved(self, pos):
        """Updates crosshair lines and cursor label on mouse move."""
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            self.v_line.setPos(mouse_point.x())
            self.h_line.setPos(mouse_point.y())
            self.cursor_label.setText(
                f"Cursor: {mouse_point.x():.4f} MHz | {mouse_point.y():.1f} {self._active_unit}"
            )

    def update_spectrum(
        self,
        freq_axis_mhz: np.ndarray,
        psd_dbfs: np.ndarray,
        psd_dbm: np.ndarray,
        peak_freq_mhz: float,
        peak_power_dbfs: float,
        noise_floor_dbfs: float,
        peaks: Optional[list] = None,
    ):
        """Updates the plot with newly processed FFT data (called by QThread signal)."""
        self._last_freqs = freq_axis_mhz
        self._last_psd_dbfs = psd_dbfs
        self._last_psd_dbm = psd_dbm
        self._last_noise_floor = noise_floor_dbfs

        # Automatically update X view range whenever tuned center frequency or span changes
        f_min = float(freq_axis_mhz[0])
        f_max = float(freq_axis_mhz[-1])
        if (
            self._last_f_min is None
            or abs(f_min - self._last_f_min) > 0.001
            or abs(f_max - self._last_f_max) > 0.001
        ):
            self._last_f_min = f_min
            self._last_f_max = f_max
            self.plot_widget.setXRange(f_min, f_max, padding=0)

        dbm_offset = float(psd_dbm[0] - psd_dbfs[0]) if len(psd_dbfs) > 0 and len(psd_dbm) > 0 else 0.0

        if self._active_unit == "dBFS":
            y_data = psd_dbfs
            noise_val = noise_floor_dbfs
            peak_y = peak_power_dbfs
        else:
            y_data = psd_dbm
            noise_val = noise_floor_dbfs + dbm_offset
            if len(psd_dbfs) > 0 and len(psd_dbm) > 0:
                peak_idx = int(np.argmax(psd_dbfs))
                peak_y = float(psd_dbm[peak_idx])
            else:
                peak_y = peak_power_dbfs + dbm_offset

        # Update curve
        self.spectrum_curve.setData(freq_axis_mhz, y_data)

        # Update noise floor line
        self.noise_floor_line.setPos(noise_val)

        # Update peak markers (multi-peak if available)
        if peaks:
            xs = [p.freq_mhz for p in peaks]
            ys = [p.power_dbfs if self._active_unit == "dBFS" else (p.power_dbfs + dbm_offset) for p in peaks]
            self.peak_scatter.setData(x=xs, y=ys)
        else:
            self.peak_scatter.setData(x=[peak_freq_mhz], y=[peak_y])

    def set_baseline_curve(self, freq_axis_mhz: np.ndarray, baseline_psd_dbfs: np.ndarray):
        """Displays the reference baseline P0 curve."""
        dbm_offset = (
            float(self._last_psd_dbm[0] - self._last_psd_dbfs[0])
            if (self._last_psd_dbm is not None and self._last_psd_dbfs is not None and len(self._last_psd_dbfs) > 0)
            else 0.0
        )
        y_data = baseline_psd_dbfs if self._active_unit == "dBFS" else (baseline_psd_dbfs + dbm_offset)
        self.baseline_curve.setData(freq_axis_mhz, y_data)
        self.baseline_curve.setVisible(True)

    def clear_baseline_curve(self):
        """Hides and clears the baseline curve."""
        self.baseline_curve.setData([], [])
        self.baseline_curve.setVisible(False)

    def set_delta_curve(self, freq_axis_mhz: np.ndarray, delta_curve_db: np.ndarray):
        """Displays the live differential attenuation curve (in dB)."""
        # Render delta scaled relative to current display floor
        floor_ref = -115.0 if self._active_unit == "dBFS" else -125.0
        y_data = np.clip(delta_curve_db + floor_ref, floor_ref, 0.0)
        self.delta_curve.setData(freq_axis_mhz, y_data)
        self.delta_curve.setVisible(True)

    def clear_delta_curve(self):
        """Hides and clears the delta curve."""
        self.delta_curve.setData([], [])
        self.delta_curve.setVisible(False)
