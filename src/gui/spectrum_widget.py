"""
Real-time hardware-accelerated Spectrum Analyzer plot widget using PyQtGraph.
Displays Power vs. Frequency, noise floor line, peak markers, and mouse crosshair tracking.
"""

from typing import Optional
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox


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
        self.plot_widget.addItem(self.noise_floor_line)

        # Peak Marker Point
        self.peak_scatter = pg.ScatterPlotItem(
            size=10,
            pen=pg.mkPen(color="#ffffff", width=1.5),
            brush=pg.mkBrush("#ef4444"),
            symbol="o",
        )
        self.plot_widget.addItem(self.peak_scatter)

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

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.cursor_label)
        header_layout.addSpacing(12)
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

    def _on_unit_changed(self, index: int):
        self._active_unit = "dBFS" if index == 0 else "dBm"
        self.plot_widget.setLabel("left", "Amplitude", units=self._active_unit)
        if self._active_unit == "dBFS":
            self.plot_widget.setYRange(-115, 5, padding=0)
            self.spectrum_curve.setFillLevel(-115)
        else:
            self.plot_widget.setYRange(-125, -5, padding=0)
            self.spectrum_curve.setFillLevel(-125)

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
