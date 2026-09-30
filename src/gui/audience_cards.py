"""
Audience Cards Component.
Provides simplified, color-coded visual metrics for non-technical audiences,
and precise technical measurements for evaluators and judges.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
)

from src.exposure.exposure_index import ExposureMetrics


PRESENTATION_BTN_NORMAL_STYLE = """
    QPushButton {
        background-color: #1e293b;
        border: 1px solid #38bdf8;
        border-radius: 6px;
        color: #38bdf8;
        font-weight: 700;
        font-size: 11px;
        padding: 4px 12px;
    }
    QPushButton:hover {
        background-color: #0284c7;
        color: #ffffff;
    }
"""

PRESENTATION_BTN_ACTIVE_STYLE = """
    QPushButton {
        background-color: #0284c7;
        border: 1px solid #38bdf8;
        border-radius: 6px;
        color: #ffffff;
        font-weight: 700;
        font-size: 11px;
        padding: 4px 12px;
    }
    QPushButton:hover {
        background-color: #0369a1;
    }
"""


class AudienceExposureCard(QFrame):
    """Dual-audience exposure metrics display card."""

    presentation_mode_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AudienceExposureCard")
        self.setStyleSheet("""
            #AudienceExposureCard {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 8px;
                padding: 6px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(16)

        # 1. Left: RF Exposure Gauge
        left_layout = QVBoxLayout()
        left_layout.setSpacing(4)

        top_row = QHBoxLayout()
        self.gauge_title = QLabel("RF EXPOSURE INDEX")
        self.gauge_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #9ca3af; letter-spacing: 0.5px;")

        self.tier_badge = QLabel("LOW")
        self.tier_badge.setStyleSheet(
            "background-color: rgba(16, 185, 129, 0.2); color: #10b981; "
            "border: 1px solid #10b981; border-radius: 4px; padding: 2px 8px; font-weight: 800; font-size: 11px;"
        )
        top_row.addWidget(self.gauge_title)
        top_row.addWidget(self.tier_badge)
        top_row.addStretch()
        left_layout.addLayout(top_row)

        self.score_bar = QProgressBar()
        self.score_bar.setRange(0, 100)
        self.score_bar.setValue(15)
        self.score_bar.setTextVisible(True)
        self.score_bar.setFormat("Index: %v / 100")
        self.score_bar.setFixedHeight(18)
        self.score_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1f2937;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
                font-weight: 700;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 4px;
            }
        """)
        left_layout.addWidget(self.score_bar)

        self.advice_label = QLabel("Safe ambient environment. Background power within baseline.")
        self.advice_label.setStyleSheet("font-size: 11px; color: #9ca3af;")
        left_layout.addWidget(self.advice_label)
        layout.addLayout(left_layout, stretch=3)

        # Divider
        div1 = QFrame()
        div1.setFrameShape(QFrame.Shape.VLine)
        div1.setStyleSheet("color: #374151;")
        layout.addWidget(div1)

        # 2. Middle: Dominant Band & Signal Analytics
        mid_layout = QVBoxLayout()
        mid_layout.setSpacing(4)

        band_title = QLabel("DOMINANT RF ALLOCATION")
        band_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #9ca3af; letter-spacing: 0.5px;")
        mid_layout.addWidget(band_title)

        self.dominant_band_label = QLabel("FM Broadcast Radio")
        self.dominant_band_label.setStyleSheet("font-size: 15px; font-weight: 800; color: #38bdf8;")
        mid_layout.addWidget(self.dominant_band_label)

        self.band_details_label = QLabel("Active Carriers: 0 | Total Power: -.- dBFS (~ -.- dBm)")
        self.band_details_label.setStyleSheet("font-size: 11px; color: #9ca3af;")
        mid_layout.addWidget(self.band_details_label)
        layout.addLayout(mid_layout, stretch=3)

        # Divider
        div2 = QFrame()
        div2.setFrameShape(QFrame.Shape.VLine)
        div2.setStyleSheet("color: #374151;")
        layout.addWidget(div2)

        # 3. Right: Presentation Mode Toggle
        right_layout = QVBoxLayout()
        right_layout.setSpacing(4)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.presentation_btn = QPushButton("PRESENTATION VIEW")
        self.presentation_btn.setFixedHeight(34)
        self.presentation_btn.setStyleSheet(PRESENTATION_BTN_NORMAL_STYLE)
        self.presentation_btn.clicked.connect(self._toggle_presentation)
        right_layout.addWidget(self.presentation_btn)
        layout.addLayout(right_layout, stretch=1)

        self._presentation_active = False

    def _toggle_presentation(self):
        self._presentation_active = not self._presentation_active
        if self._presentation_active:
            self.presentation_btn.setText("NORMAL VIEW")
            self.presentation_btn.setStyleSheet(PRESENTATION_BTN_ACTIVE_STYLE)
        else:
            self.presentation_btn.setText("PRESENTATION VIEW")
            self.presentation_btn.setStyleSheet(PRESENTATION_BTN_NORMAL_STYLE)
        self.presentation_mode_toggled.emit(self._presentation_active)

    def update_metrics(
        self,
        exposure: ExposureMetrics,
        dominant_band: str,
        carrier_count: int,
        max_snr: float,
    ):
        """Updates the card with fresh calculated metrics."""
        # Tier badge
        self.tier_badge.setText(exposure.tier.upper())
        self.tier_badge.setStyleSheet(
            f"background-color: rgba({int(exposure.color_hex[1:3], 16)}, "
            f"{int(exposure.color_hex[3:5], 16)}, {int(exposure.color_hex[5:7], 16)}, 0.2); "
            f"color: {exposure.color_hex}; border: 1px solid {exposure.color_hex}; "
            f"border-radius: 4px; padding: 2px 8px; font-weight: 800; font-size: 11px;"
        )

        # Score bar
        self.score_bar.setValue(exposure.score)
        self.score_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1f2937;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
                font-weight: 700;
                font-size: 10px;
            }}
            QProgressBar::chunk {{
                background-color: {exposure.color_hex};
                border-radius: 4px;
            }}
        """)

        self.advice_label.setText(exposure.advice)
        self.dominant_band_label.setText(dominant_band)
        self.band_details_label.setText(
            f"Active Carriers: {carrier_count} | Peak SNR: {max_snr:.1f} dB | Total: {exposure.total_power_dbfs:.1f} dBFS (~ {exposure.total_power_dbm:.1f} dBm)"
        )
