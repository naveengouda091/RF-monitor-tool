"""
Controls panel for tuner parameters, frequency presets, gain, FFT options, and stream state.
"""

from typing import List
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
    QComboBox,
    QSlider,
    QCheckBox,
)


class ControlsPanel(QWidget):
    """Sidebar control panel providing dynamic parameter adjustments."""

    frequency_changed = pyqtSignal(float)      # freq in Hz
    gain_changed = pyqtSignal(float, bool)     # gain_db, auto
    sample_rate_changed = pyqtSignal(float)    # rate in Hz
    fft_size_changed = pyqtSignal(int)
    window_changed = pyqtSignal(str)
    averaging_changed = pyqtSignal(int)
    pause_toggled = pyqtSignal(bool)           # is_paused

    PRESETS = [
        ("Select Band Preset...", 0.0),
        ("FM Radio Broadcast (100.0 MHz)", 100.0),
        ("Aviation Airband (125.0 MHz)", 125.0),
        ("Amateur 2m VHF (145.0 MHz)", 145.0),
        ("ISM Sub-GHz (433.92 MHz)", 433.92),
        ("ISM / LoRa India (866.0 MHz)", 866.0),
        ("GSM 900 Downlink (945.0 MHz)", 945.0),
        ("ADS-B Flight Radar (1090.0 MHz)", 1090.0),
    ]

    def __init__(self, valid_gains: List[float], parent=None):
        super().__init__(parent)
        self.valid_gains = valid_gains or [0.0, 14.4, 28.0, 38.6, 49.6]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # 1. Frequency Control Group
        freq_group = QGroupBox("Tuner Frequency")
        freq_layout = QVBoxLayout(freq_group)

        # Preset selector
        self.preset_combo = QComboBox()
        for label, _ in self.PRESETS:
            self.preset_combo.addItem(label)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        freq_layout.addWidget(self.preset_combo)

        # Numeric Frequency Spinner
        spin_layout = QHBoxLayout()
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(24.0, 1766.0)
        self.freq_spin.setValue(100.0)
        self.freq_spin.setDecimals(4)
        self.freq_spin.setSuffix(" MHz")
        self.freq_spin.setSingleStep(0.1)
        self.freq_spin.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.freq_spin.valueChanged.connect(self._on_freq_spin_changed)
        spin_layout.addWidget(self.freq_spin)
        freq_layout.addLayout(spin_layout)

        # Quick Step Buttons
        step_layout = QHBoxLayout()
        btn_down_1m = QPushButton("-1M")
        btn_up_1m = QPushButton("+1M")
        btn_down_100k = QPushButton("-100k")
        btn_up_100k = QPushButton("+100k")

        btn_down_1m.clicked.connect(lambda: self._step_freq(-1.0))
        btn_up_1m.clicked.connect(lambda: self._step_freq(1.0))
        btn_down_100k.clicked.connect(lambda: self._step_freq(-0.1))
        btn_up_100k.clicked.connect(lambda: self._step_freq(0.1))

        for btn in [btn_down_1m, btn_down_100k, btn_up_100k, btn_up_1m]:
            btn.setMaximumWidth(55)
            step_layout.addWidget(btn)
        freq_layout.addLayout(step_layout)
        layout.addWidget(freq_group)

        # 2. Gain & Hardware Group
        gain_group = QGroupBox("Hardware Gain & ADC")
        gain_layout = QVBoxLayout(gain_group)

        gain_header = QHBoxLayout()
        self.gain_val_label = QLabel("Gain: 29.7 dB")
        self.gain_val_label.setStyleSheet("color: #38bdf8; font-weight: 600;")
        self.agc_check = QCheckBox("Auto AGC")
        self.agc_check.toggled.connect(self._on_agc_toggled)
        gain_header.addWidget(self.gain_val_label)
        gain_header.addStretch()
        gain_header.addWidget(self.agc_check)
        gain_layout.addLayout(gain_header)

        # Gain Slider
        self.gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.gain_slider.setRange(0, len(self.valid_gains) - 1)
        # Default to middle-high gain
        default_idx = min(len(self.valid_gains) - 1, 15)
        self.gain_slider.setValue(default_idx)
        initial_gain = self.valid_gains[default_idx]
        self.gain_val_label.setText(f"Gain: {initial_gain:.1f} dB")
        self.gain_slider.valueChanged.connect(self._on_gain_slider_changed)
        gain_layout.addWidget(self.gain_slider)

        # Sample Rate Selector
        sr_layout = QHBoxLayout()
        sr_label = QLabel("Sample Rate:")
        self.sr_combo = QComboBox()
        self.sr_combo.addItems(["1.0 MSps", "1.8 MSps", "2.048 MSps", "2.4 MSps"])
        self.sr_combo.setCurrentText("2.4 MSps")
        self.sr_combo.currentIndexChanged.connect(self._on_sample_rate_changed)
        sr_layout.addWidget(sr_label)
        sr_layout.addWidget(self.sr_combo)
        gain_layout.addLayout(sr_layout)
        layout.addWidget(gain_group)

        # 3. DSP Settings Group
        dsp_group = QGroupBox("DSP & FFT Settings")
        dsp_layout = QVBoxLayout(dsp_group)

        # FFT Size
        fft_row = QHBoxLayout()
        fft_label = QLabel("FFT Size:")
        self.fft_combo = QComboBox()
        self.fft_combo.addItems(["512", "1024", "2048", "4096"])
        self.fft_combo.setCurrentText("2048")
        self.fft_combo.currentIndexChanged.connect(
            lambda: self.fft_size_changed.emit(int(self.fft_combo.currentText()))
        )
        fft_row.addWidget(fft_label)
        fft_row.addWidget(self.fft_combo)
        dsp_layout.addLayout(fft_row)

        # Window function
        win_row = QHBoxLayout()
        win_label = QLabel("Window:")
        self.win_combo = QComboBox()
        self.win_combo.addItems(["Hann", "Hamming", "Blackman", "Rectangular"])
        self.win_combo.currentIndexChanged.connect(
            lambda: self.window_changed.emit(self.win_combo.currentText().lower())
        )
        win_row.addWidget(win_label)
        win_row.addWidget(self.win_combo)
        dsp_layout.addLayout(win_row)

        # Averaging Slider
        avg_row = QHBoxLayout()
        self.avg_label = QLabel("Smoothing (EMA): 5")
        self.avg_slider = QSlider(Qt.Orientation.Horizontal)
        self.avg_slider.setRange(1, 20)
        self.avg_slider.setValue(5)
        self.avg_slider.valueChanged.connect(self._on_avg_changed)
        avg_row.addWidget(self.avg_label)
        dsp_layout.addLayout(avg_row)
        dsp_layout.addWidget(self.avg_slider)
        layout.addWidget(dsp_group)

        # 4. Stream State Button
        self.pause_btn = QPushButton("PAUSE ACQUISITION")
        self.pause_btn.setFixedHeight(38)
        self.pause_btn.setProperty("class", "primary")
        self.pause_btn.clicked.connect(self._toggle_pause)
        layout.addWidget(self.pause_btn)

        layout.addStretch()

        self._is_paused = False

    def _step_freq(self, delta_mhz: float):
        new_val = self.freq_spin.value() + delta_mhz
        self.freq_spin.setValue(new_val)

    def _on_freq_spin_changed(self, val: float):
        self.frequency_changed.emit(val * 1e6)

    def _on_preset_selected(self, index: int):
        if index > 0:
            _, freq_mhz = self.PRESETS[index]
            self.freq_spin.setValue(freq_mhz)

    def _on_gain_slider_changed(self, index: int):
        gain_db = self.valid_gains[index]
        self.gain_val_label.setText(f"Gain: {gain_db:.1f} dB")
        if not self.agc_check.isChecked():
            self.gain_changed.emit(gain_db, False)

    def _on_agc_toggled(self, checked: bool):
        self.gain_slider.setEnabled(not checked)
        if checked:
            self.gain_val_label.setText("Gain: AUTO AGC")
            self.gain_changed.emit(0.0, True)
        else:
            gain_db = self.valid_gains[self.gain_slider.value()]
            self.gain_val_label.setText(f"Gain: {gain_db:.1f} dB")
            self.gain_changed.emit(gain_db, False)

    def _on_sample_rate_changed(self):
        text = self.sr_combo.currentText()
        rates = {
            "1.0 MSps": 1_000_000.0,
            "1.8 MSps": 1_800_000.0,
            "2.048 MSps": 2_048_000.0,
            "2.4 MSps": 2_400_000.0,
        }
        sr = rates.get(text, 2_400_000.0)
        self.sample_rate_changed.emit(sr)

    def _on_avg_changed(self, val: int):
        self.avg_label.setText(f"Smoothing (EMA): {val}")
        self.averaging_changed.emit(val)

    def _toggle_pause(self):
        self._is_paused = not self._is_paused
        if self._is_paused:
            self.pause_btn.setText("RESUME ACQUISITION")
            self.pause_btn.setStyleSheet("background-color: #10b981; border-color: #34d399;")
        else:
            self.pause_btn.setText("PAUSE ACQUISITION")
            self.pause_btn.setStyleSheet("")
        self.pause_toggled.emit(self._is_paused)
