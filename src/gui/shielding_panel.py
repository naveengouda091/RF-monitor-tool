"""
Shielding Analysis Panel Widget.
Controls baseline reference recording, free-text material labeling,
live continuous differential mode, and real-time attenuation metrics display.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QCheckBox,
    QFrame,
)

from src.shielding.differential_engine import ShieldingResult


class ShieldingPanel(QWidget):
    """Panel for controlling and viewing shielding effectiveness measurements."""

    capture_baseline_requested = pyqtSignal(int)
    clear_baseline_requested = pyqtSignal()
    differential_mode_toggled = pyqtSignal(bool)
    material_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # 1. Material Input Group
        mat_group = QGroupBox("Test Material Metadata")
        mat_layout = QVBoxLayout(mat_group)

        mat_label = QLabel("Material Description:")
        mat_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.mat_input = QLineEdit()
        self.mat_input.setPlaceholderText("e.g. Aluminum Foil / Copper Mesh / Plastic")
        self.mat_input.setText("Aluminum Foil (Single Layer)")
        self.mat_input.textChanged.connect(self.material_changed.emit)

        mat_layout.addWidget(mat_label)
        mat_layout.addWidget(self.mat_input)
        layout.addWidget(mat_group)

        # 2. Baseline Acquisition Group
        base_group = QGroupBox("Reference Baseline (P0)")
        base_layout = QVBoxLayout(base_group)

        self.base_status_label = QLabel("Status: No Baseline Captured")
        self.base_status_label.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        base_layout.addWidget(self.base_status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Recording Baseline: %v%")
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1e293b;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
                font-weight: 700;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #0284c7;
                border-radius: 4px;
            }
        """)
        self.progress_bar.setVisible(False)
        base_layout.addWidget(self.progress_bar)

        btn_row = QHBoxLayout()
        self.capture_btn = QPushButton("RECORD BASELINE (P0)")
        self.capture_btn.setProperty("class", "primary")
        self.capture_btn.setFixedHeight(34)
        self.capture_btn.clicked.connect(self._on_capture_clicked)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedWidth(65)
        self.clear_btn.setFixedHeight(34)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        self.clear_btn.setEnabled(False)

        btn_row.addWidget(self.capture_btn)
        btn_row.addWidget(self.clear_btn)
        base_layout.addLayout(btn_row)

        layout.addWidget(base_group)

        # 3. Live Differential Mode Group
        diff_group = QGroupBox("Live Attenuation Differential")
        diff_layout = QVBoxLayout(diff_group)

        self.diff_toggle = QCheckBox("Enable Live Differential Mode")
        self.diff_toggle.setStyleSheet("font-weight: 700; color: #38bdf8;")
        self.diff_toggle.setEnabled(False)
        self.diff_toggle.toggled.connect(self.differential_mode_toggled.emit)
        diff_layout.addWidget(self.diff_toggle)

        # Attenuation Readout Card
        self.results_card = QFrame()
        self.results_card.setStyleSheet("""
            QFrame {
                background-color: #0d121f;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        res_layout = QVBoxLayout(self.results_card)
        res_layout.setSpacing(6)

        pct_label = QLabel("POWER REDUCTION")
        pct_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;")
        res_layout.addWidget(pct_label)

        self.pct_val_label = QLabel("--.- %")
        self.pct_val_label.setStyleSheet("font-size: 24px; font-weight: 800; color: #10b981;")
        res_layout.addWidget(self.pct_val_label)

        self.se_val_label = QLabel("Attenuation: --.- dB (Ratio: -.--x)")
        self.se_val_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #f8fafc;")
        res_layout.addWidget(self.se_val_label)

        self.levels_label = QLabel("P0 (Baseline): --- dBFS | P1 (Shield): --- dBFS")
        self.levels_label.setStyleSheet("font-size: 10px; color: #64748b; font-family: monospace;")
        res_layout.addWidget(self.levels_label)

        self.rating_badge = QLabel("AWAITING BASELINE")
        self.rating_badge.setStyleSheet(
            "background-color: rgba(148, 163, 184, 0.15); color: #94a3b8; "
            "border: 1px solid #64748b; border-radius: 4px; padding: 3px 8px; font-weight: 800; font-size: 11px;"
        )
        self.rating_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        res_layout.addWidget(self.rating_badge)

        diff_layout.addWidget(self.results_card)
        layout.addWidget(diff_group)

        layout.addStretch()

    def get_material_name(self) -> str:
        return self.mat_input.text().strip() or "Custom Material"

    def _on_capture_clicked(self):
        self.capture_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.base_status_label.setText("Status: Capturing 50 reference frames...")
        self.capture_baseline_requested.emit(50)

    def _on_clear_clicked(self):
        self.clear_baseline_requested.emit()
        self.diff_toggle.setChecked(False)
        self.diff_toggle.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.capture_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.base_status_label.setText("Status: Baseline cleared")
        self.pct_val_label.setText("--.- %")
        self.pct_val_label.setStyleSheet("font-size: 24px; font-weight: 800; color: #94a3b8;")
        self.se_val_label.setText("Attenuation: --.- dB")
        self.levels_label.setText("P0: --- | P1: ---")
        self.rating_badge.setText("AWAITING BASELINE")
        self.rating_badge.setStyleSheet(
            "background-color: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid #64748b;"
        )

    def update_capture_progress(self, progress_pct: int):
        self.progress_bar.setValue(progress_pct)

    def set_baseline_ready(self, peak_p0_dbfs: float):
        self.progress_bar.setVisible(False)
        self.capture_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.diff_toggle.setEnabled(True)
        self.diff_toggle.setChecked(True)
        self.base_status_label.setText(f"Status: Baseline Saved (P0 Peak: {peak_p0_dbfs:.1f} dBFS)")

    def update_shielding_result(self, result: ShieldingResult):
        """Renders live attenuation metrics."""
        self.pct_val_label.setText(f"{result.percentage_reduction:.1f}% BLOCKED")
        self.pct_val_label.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {result.color_hex};")

        self.se_val_label.setText(f"Attenuation: +{result.se_peak_db:.1f} dB (Ratio: {result.attenuation_ratio:.1f}x)")
        self.levels_label.setText(
            f"P0: {result.baseline_peak_dbfs:.1f} dBFS  |  P1: {result.live_peak_dbfs:.1f} dBFS"
        )

        self.rating_badge.setText(result.rating)
        self.rating_badge.setStyleSheet(
            f"background-color: rgba({int(result.color_hex[1:3], 16)}, "
            f"{int(result.color_hex[3:5], 16)}, {int(result.color_hex[5:7], 16)}, 0.2); "
            f"color: {result.color_hex}; border: 1px solid {result.color_hex}; "
            f"border-radius: 4px; padding: 3px 8px; font-weight: 800; font-size: 11px;"
        )
