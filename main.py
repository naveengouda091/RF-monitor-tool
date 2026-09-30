"""
Main Application Entry Point for SDR-Based RF Noise Monitoring and Reduction Analysis.
Department of Electronics & Communication Engineering, KLS VDIT Haliyal.
"""

import os
import sys
import logging

# Ensure project root is in system path & DLL path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if hasattr(os, "add_dll_directory"):
    try:
        os.add_dll_directory(PROJECT_ROOT)
    except Exception as e:
        pass

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.hardware.sdr_device import SDRDevice
from src.dsp.fft_processor import FFTProcessor
from src.gui.main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    # Enable High DPI pixmaps
    app = QApplication(sys.argv)
    app.setApplicationName("RF Noise Monitor & Reduction Analyzer")
    app.setOrganizationName("KLS VDIT ECE")

    # Initialize Hardware and DSP Core
    device = SDRDevice(device_index=0)
    processor = FFTProcessor(
        fft_size=2048,
        window_name="hann",
        averaging_count=5,
    )

    window = MainWindow(device=device, processor=processor)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
