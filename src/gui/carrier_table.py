"""
Carrier Table Component.
Displays active detected RF carriers, their regulatory band classifications,
peak powers, occupied bandwidths, and signal-to-noise ratios.
"""

from typing import List
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
)

from src.dsp.peak_detector import DetectedPeak


class CarrierTableWidget(QWidget):
    """Real-time table displaying identified RF carriers."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header_label = QLabel("ACTIVE RF TRANSMITTERS & CARRIERS")
        header_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #38bdf8; letter-spacing: 0.5px;")
        layout.addWidget(header_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Carrier (MHz)",
            "Allocation Band",
            "Peak (dBFS)",
            "3dB BW (kHz)",
            "SNR (dB)",
        ])

        # Style table
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0d121f;
                gridline-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #1e293b;
                border-radius: 6px;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #131b2e;
                color: #94a3b8;
                font-weight: 600;
                font-size: 11px;
                padding: 4px;
                border: 1px solid #1e293b;
            }
            QTableWidget::item {
                padding: 3px;
            }
        """)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.table)

    def update_peaks(self, peaks: List[DetectedPeak]):
        """Populates table with fresh peak data."""
        self.table.setRowCount(len(peaks))

        for row, peak in enumerate(peaks):
            item_freq = QTableWidgetItem(f"{peak.freq_mhz:.4f}")
            item_freq.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_band = QTableWidgetItem(peak.band_label)
            item_band.setForeground(Qt.GlobalColor.cyan)

            item_pwr = QTableWidgetItem(f"{peak.power_dbfs:.1f}")
            item_pwr.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_bw = QTableWidgetItem(f"{peak.bw_3db_khz:.1f}")
            item_bw.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_snr = QTableWidgetItem(f"+{peak.snr_db:.1f}")
            item_snr.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if peak.snr_db > 15:
                item_snr.setForeground(Qt.GlobalColor.green)
            else:
                item_snr.setForeground(Qt.GlobalColor.yellow)

            self.table.setItem(row, 0, item_freq)
            self.table.setItem(row, 1, item_band)
            self.table.setItem(row, 2, item_pwr)
            self.table.setItem(row, 3, item_bw)
            self.table.setItem(row, 4, item_snr)
