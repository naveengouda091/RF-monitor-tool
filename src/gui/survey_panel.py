"""
Survey & Logging Panel Widget for Phase 5.
Provides real-time location tagging, periodic survey recording, snapshot logging,
recent log table display, CSV export, and academic HTML report generation (FR-08).
"""

import os
import webbrowser
from datetime import datetime
from typing import Optional, Dict, Any, List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QFrame,
)

from src.storage.survey_database import SurveyDatabase
from src.storage.survey_logger import SurveyLogger
from src.storage.report_generator import ReportGenerator


class SurveyPanel(QWidget):
    """Panel for configuring and executing RF spatial surveys and data persistence."""

    snapshot_requested = pyqtSignal(str, str)  # (location_id, notes)

    def __init__(self, logger: SurveyLogger, db: SurveyDatabase, parent=None):
        super().__init__(parent)
        self.logger = logger
        self.db = db
        self.report_gen = ReportGenerator(db=self.db)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # 1. Location & Environment Metadata Group
        meta_group = QGroupBox("Survey Site & Environment")
        meta_layout = QVBoxLayout(meta_group)
        meta_layout.setSpacing(6)

        loc_label = QLabel("Site / Location Tag:")
        loc_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")
        meta_layout.addWidget(loc_label)

        self.loc_combo = QComboBox()
        self.loc_combo.setEditable(True)
        self.loc_combo.addItems([
            "Comm Lab (Room 101)",
            "DSP & VLSI Lab (Room 105)",
            "Server Room (Admin Block)",
            "Classroom 204 (Academic Block)",
            "Library & Study Hall",
            "Campus Outdoor Quad",
            "Hostel / Residential Quarters",
        ])
        self.loc_combo.currentTextChanged.connect(self._on_location_changed)
        meta_layout.addWidget(self.loc_combo)

        notes_label = QLabel("Survey Notes (Optional):")
        notes_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")
        meta_layout.addWidget(notes_label)

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("e.g. Near window, 5m from Wi-Fi router")
        self.notes_input.textChanged.connect(self._on_notes_changed)
        meta_layout.addWidget(self.notes_input)

        layout.addWidget(meta_group)

        # 2. Survey Logging Controls Group
        ctrl_group = QGroupBox("Survey Recording Session")
        ctrl_layout = QVBoxLayout(ctrl_group)
        ctrl_layout.setSpacing(8)

        # Row 1: Start/Stop button + Interval dropdown
        row1 = QHBoxLayout()
        self.record_btn = QPushButton("START LOGGING")
        self.record_btn.setProperty("class", "primary")
        self.record_btn.setFixedHeight(34)
        self.record_btn.clicked.connect(self._on_toggle_recording)
        row1.addWidget(self.record_btn, stretch=3)

        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["1.0s", "2.0s", "5.0s", "10.0s"])
        self.interval_combo.setCurrentText("2.0s")
        self.interval_combo.setFixedWidth(70)
        self.interval_combo.setFixedHeight(34)
        self.interval_combo.currentTextChanged.connect(self._on_interval_changed)
        row1.addWidget(self.interval_combo, stretch=1)
        ctrl_layout.addLayout(row1)

        # Row 2: Manual snapshot button
        self.snapshot_btn = QPushButton("CAPTURE SNAPSHOT NOW")
        self.snapshot_btn.setFixedHeight(30)
        self.snapshot_btn.clicked.connect(self._on_snapshot_clicked)
        ctrl_layout.addWidget(self.snapshot_btn)

        # Live Session Stat Card
        self.stat_card = QFrame()
        self.stat_card.setStyleSheet("""
            QFrame {
                background-color: #0d121f;
                border: 1px solid #1e293b;
                border-radius: 6px;
                padding: 6px 8px;
            }
        """)
        stat_layout = QHBoxLayout(self.stat_card)
        stat_layout.setContentsMargins(4, 4, 4, 4)

        self.count_label = QLabel("Points: 0")
        self.count_label.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 11px;")

        self.max_peak_label = QLabel("Peak: --- dBFS")
        self.max_peak_label.setStyleSheet("color: #f59e0b; font-weight: 700; font-size: 11px;")

        self.status_indicator = QLabel("IDLE")
        self.status_indicator.setStyleSheet(
            "background-color: rgba(148, 163, 184, 0.15); color: #94a3b8; "
            "border: 1px solid #64748b; border-radius: 4px; padding: 2px 6px; font-weight: 700; font-size: 10px;"
        )
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)

        stat_layout.addWidget(self.count_label)
        stat_layout.addStretch()
        stat_layout.addWidget(self.max_peak_label)
        stat_layout.addStretch()
        stat_layout.addWidget(self.status_indicator)

        ctrl_layout.addWidget(self.stat_card)
        layout.addWidget(ctrl_group)

        # 3. Recent Survey History Table
        hist_label = QLabel("RECENT SURVEY MEASUREMENTS")
        hist_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #38bdf8; letter-spacing: 0.5px; margin-top: 4px;")
        layout.addWidget(hist_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Time",
            "Location",
            "Peak",
            "Band",
            "Tier",
        ])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0d121f;
                gridline-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #1e293b;
                border-radius: 6px;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #131b2e;
                color: #94a3b8;
                font-weight: 600;
                font-size: 10px;
                padding: 4px;
                border: 1px solid #1e293b;
            }
            QTableWidget::item {
                padding: 2px 4px;
            }
        """)
        h_hdr = self.table.horizontalHeader()
        h_hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h_hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h_hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h_hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # 4. Export & Report Actions
        act_row1 = QHBoxLayout()
        self.export_csv_btn = QPushButton("Export CSV...")
        self.export_csv_btn.setFixedHeight(30)
        self.export_csv_btn.clicked.connect(self._on_export_csv)

        self.gen_report_btn = QPushButton("Generate Report...")
        self.gen_report_btn.setProperty("class", "primary")
        self.gen_report_btn.setFixedHeight(30)
        self.gen_report_btn.clicked.connect(self._on_generate_report)

        act_row1.addWidget(self.export_csv_btn)
        act_row1.addWidget(self.gen_report_btn)
        layout.addLayout(act_row1)

        self.clear_btn = QPushButton("Clear Survey Records")
        self.clear_btn.setFixedHeight(26)
        self.clear_btn.setStyleSheet("font-size: 10px; color: #94a3b8; background-color: transparent; border: 1px solid #334155;")
        self.clear_btn.clicked.connect(self._on_clear_records)
        layout.addWidget(self.clear_btn)

        # Connect logger signals
        self.logger.survey_logged.connect(self._on_survey_logged)
        self.logger.recording_state_changed.connect(self._on_recording_state_changed)
        self.logger.session_stats_updated.connect(self._on_session_stats_updated)

        # Load existing records if any
        self._refresh_table()

    def _on_location_changed(self, text: str):
        self.logger.location_id = text

    def _on_notes_changed(self, text: str):
        self.logger.notes = text

    def _on_interval_changed(self, text: str):
        try:
            val = float(text.replace("s", "").strip())
            self.logger.interval_sec = val
        except ValueError:
            pass

    def _on_toggle_recording(self):
        if not self.logger.is_recording:
            loc = self.loc_combo.currentText().strip() or "Comm Lab (Room 101)"
            interval_str = self.interval_combo.currentText().replace("s", "").strip()
            interval = float(interval_str) if interval_str else 2.0
            notes = self.notes_input.text().strip()
            self.logger.start_session(location_id=loc, interval_sec=interval, notes=notes)
        else:
            self.logger.stop_session()

    def _on_snapshot_clicked(self):
        loc = self.loc_combo.currentText().strip() or "Comm Lab (Room 101)"
        notes = self.notes_input.text().strip()
        self.snapshot_requested.emit(loc, notes)

    def _on_recording_state_changed(self, is_recording: bool):
        if is_recording:
            self.record_btn.setText("STOP LOGGING")
            self.record_btn.setStyleSheet("background-color: #dc2626; color: #ffffff; font-weight: 700;")
            self.status_indicator.setText("RECORDING")
            self.status_indicator.setStyleSheet(
                "background-color: rgba(239, 68, 68, 0.2); color: #ef4444; "
                "border: 1px solid #ef4444; border-radius: 4px; padding: 2px 6px; font-weight: 700; font-size: 10px;"
            )
        else:
            self.record_btn.setText("START LOGGING")
            self.record_btn.setStyleSheet("")
            self.status_indicator.setText("IDLE")
            self.status_indicator.setStyleSheet(
                "background-color: rgba(148, 163, 184, 0.15); color: #94a3b8; "
                "border: 1px solid #64748b; border-radius: 4px; padding: 2px 6px; font-weight: 700; font-size: 10px;"
            )

    def _on_session_stats_updated(self, stats: dict):
        count = stats.get("session_count", 0)
        peak = stats.get("session_max_peak", -120.0)
        self.count_label.setText(f"Points: {count}")
        if peak > -110.0:
            self.max_peak_label.setText(f"Peak: {peak:.1f} dBFS")
        else:
            self.max_peak_label.setText("Peak: --- dBFS")

    def _on_survey_logged(self, record: dict):
        self._add_record_to_table(record)

    def _refresh_table(self):
        self.table.setRowCount(0)
        records = self.db.get_recent_survey_logs(limit=20)
        # Oldest to newest or newest at top
        for rec in reversed(records):
            self._add_record_to_table(rec)

    def _add_record_to_table(self, record: dict):
        row = self.table.rowCount()
        self.table.insertRow(0)

        # 1. Time (HH:MM:SS)
        ts = record.get("timestamp", "")
        time_display = ts.split("T")[-1] if "T" in ts else ts.split(" ")[-1]
        time_item = QTableWidgetItem(time_display)
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # 2. Location
        loc_item = QTableWidgetItem(record.get("location_id", ""))

        # 3. Peak
        peak_val = record.get("peak_power_dbfs", -100.0)
        peak_item = QTableWidgetItem(f"{peak_val:.1f}")
        peak_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # 4. Band
        band_item = QTableWidgetItem(record.get("dominant_band", "Unknown"))
        band_item.setForeground(Qt.GlobalColor.cyan)

        # 5. Tier
        tier = record.get("exposure_tier", "Low")
        tier_item = QTableWidgetItem(tier)
        tier_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if tier == "Low":
            tier_item.setForeground(Qt.GlobalColor.green)
        elif tier == "Medium":
            tier_item.setForeground(Qt.GlobalColor.yellow)
        else:
            tier_item.setForeground(Qt.GlobalColor.red)

        self.table.setItem(0, 0, time_item)
        self.table.setItem(0, 1, loc_item)
        self.table.setItem(0, 2, peak_item)
        self.table.setItem(0, 3, band_item)
        self.table.setItem(0, 4, tier_item)

        # Keep max 50 rows in table
        if self.table.rowCount() > 50:
            self.table.removeRow(self.table.rowCount() - 1)

    def _on_export_csv(self):
        default_name = f"rf_survey_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export RF Survey Data to CSV",
            default_name,
            "CSV Files (*.csv);;All Files (*)",
        )
        if filepath:
            count = self.db.export_survey_to_csv(filepath)
            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported {count} survey records to:\n{filepath}",
            )

    def _on_generate_report(self):
        default_name = f"rf_survey_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Generate Academic Survey Report",
            default_name,
            "HTML Files (*.html);;All Files (*)",
        )
        if filepath:
            abs_path = self.report_gen.generate_html_report(filepath)
            res = QMessageBox.question(
                self,
                "Report Generated",
                f"Report successfully compiled at:\n{abs_path}\n\nWould you like to open it in your web browser?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if res == QMessageBox.StandardButton.Yes:
                webbrowser.open(f"file:///{abs_path.replace(os.sep, '/')}")

    def _on_clear_records(self):
        confirm = QMessageBox.warning(
            self,
            "Confirm Clear Records",
            "Are you sure you want to clear all logged survey records from the database?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.clear_survey_logs()
            self.table.setRowCount(0)
            self.count_label.setText("Points: 0")
            self.max_peak_label.setText("Peak: --- dBFS")
