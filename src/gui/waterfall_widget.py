"""
Real-time scrolling Waterfall Heatmap widget using PyQtGraph ImageItem.
Displays time vs. frequency spectrogram with selectable color palettes and dynamic contrast.
"""

from typing import Optional
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QSlider,
)


class WaterfallWidget(QWidget):
    """Scrolling spectrogram heatmap widget."""

    HISTORY_ROWS = 150  # Number of historical time slices to retain

    COLORMAPS = {
        "Viridis": "viridis",
        "Inferno": "inferno",
        "Turbo": "turbo",
        "Plasma": "plasma",
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self.num_bins = 2048
        # Buffer shape: (time_rows, freq_bins)
        self.waterfall_data = np.full(
            (self.HISTORY_ROWS, self.num_bins), -115.0, dtype=np.float32
        )

        # Plot Widget Configuration
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#0d121f")
        self.plot_widget.setLabel("bottom", "Frequency", units="MHz")
        self.plot_widget.setLabel("left", "Time History", units="lines")
        self.plot_widget.getAxis("bottom").setPen(pg.mkPen("#475569"))
        self.plot_widget.getAxis("left").setPen(pg.mkPen("#475569"))
        self.plot_widget.setYRange(0, self.HISTORY_ROWS, padding=0)

        # Image Item for Waterfall
        self.image_item = pg.ImageItem()
        self.plot_widget.addItem(self.image_item)

        # Header controls
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(6, 2, 6, 2)

        title = QLabel("LIVE WATERFALL SPECTROGRAM")
        title.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 13px;")

        cmap_label = QLabel("Palette:")
        cmap_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.cmap_combo = QComboBox()
        self.cmap_combo.addItems(list(self.COLORMAPS.keys()))
        self.cmap_combo.currentIndexChanged.connect(self._on_cmap_changed)

        contrast_label = QLabel("Contrast:")
        contrast_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(-120, -10)
        self.contrast_slider.setValue(-50)
        self.contrast_slider.setFixedWidth(100)
        self.contrast_slider.valueChanged.connect(self._on_contrast_changed)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(cmap_label)
        header_layout.addWidget(self.cmap_combo)
        header_layout.addSpacing(10)
        header_layout.addWidget(contrast_label)
        header_layout.addWidget(self.contrast_slider)

        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addLayout(header_layout)
        layout.addWidget(self.plot_widget)

        self._min_dbfs = -110.0
        self._max_dbfs = -40.0
        self._last_f_min: Optional[float] = None
        self._last_f_max: Optional[float] = None
        self._set_colormap("viridis")

    def _set_colormap(self, cmap_name: str):
        """Applies PyQtGraph color map to the image item."""
        try:
            cmap = pg.colormap.get(cmap_name)
            lut = cmap.getLookupTable(0.0, 1.0, 256)
            self.image_item.setLookupTable(lut)
        except Exception:
            pass

    def _on_cmap_changed(self):
        selected_text = self.cmap_combo.currentText()
        cmap_key = self.COLORMAPS.get(selected_text, "viridis")
        self._set_colormap(cmap_key)

    def _on_contrast_changed(self, val: int):
        self._max_dbfs = float(val)
        self.image_item.setLevels([self._min_dbfs, self._max_dbfs])

    def update_waterfall(self, freq_axis_mhz: np.ndarray, psd_dbfs: np.ndarray):
        """Rolls history buffer and updates the waterfall image."""
        num_new_bins = len(psd_dbfs)
        if num_new_bins != self.num_bins:
            self.num_bins = num_new_bins
            self.waterfall_data = np.full(
                (self.HISTORY_ROWS, self.num_bins), -115.0, dtype=np.float32
            )

        # Roll buffer down by 1 row
        self.waterfall_data = np.roll(self.waterfall_data, 1, axis=0)
        # Insert newest frame at top row
        self.waterfall_data[0, :] = psd_dbfs

        # Update image data
        self.image_item.setImage(
            self.waterfall_data.T,
            autoLevels=False,
            levels=[self._min_dbfs, self._max_dbfs],
        )

        # Scale image rectangle only when frequency axis changes
        f_min = float(freq_axis_mhz[0])
        f_max = float(freq_axis_mhz[-1])
        if (
            self._last_f_min is None
            or abs(f_min - self._last_f_min) > 0.001
            or abs(f_max - self._last_f_max) > 0.001
        ):
            self._last_f_min = f_min
            self._last_f_max = f_max
            self.image_item.setRect(f_min, 0, f_max - f_min, self.HISTORY_ROWS)
            self.plot_widget.setXRange(f_min, f_max, padding=0)
