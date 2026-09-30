"""
Visual styling and dark theme stylesheet for PyQt6 application.
"""

DARK_STYLESHEET = """
QMainWindow {
    background-color: #0b0f19;
    color: #e6edf3;
}

QWidget {
    font-family: "Segoe UI", "Inter", -apple-system, sans-serif;
    font-size: 13px;
    color: #e6edf3;
}

/* Group boxes and Cards */
QGroupBox {
    background-color: #131b2e;
    border: 1px solid #1e293b;
    border-radius: 8px;
    margin-top: 24px;
    padding: 14px 12px 12px 12px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 6px;
    padding: 0 6px;
    color: #38bdf8;
    background-color: transparent;
}

QFrame.card {
    background-color: #131b2e;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 10px;
}

/* Push Buttons */
QPushButton {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #334155;
    border-color: #38bdf8;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #0284c7;
    border-color: #0284c7;
    color: #ffffff;
}

QPushButton.primary {
    background-color: #0284c7;
    border: 1px solid #38bdf8;
    color: #ffffff;
    font-weight: 600;
}

QPushButton.primary:hover {
    background-color: #0369a1;
    border-color: #7dd3fc;
}

QPushButton.danger {
    background-color: #dc2626;
    border: 1px solid #ef4444;
    color: #ffffff;
    font-weight: 600;
}

QPushButton.danger:hover {
    background-color: #b91c1c;
}

/* Inputs and Combos */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #0b0f19;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 8px;
    selection-background-color: #0284c7;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #38bdf8;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #334155;
}

QComboBox QAbstractItemView {
    background-color: #131b2e;
    color: #f8fafc;
    selection-background-color: #0284c7;
    border: 1px solid #334155;
    outline: none;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 6px;
    background: #1e293b;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #0284c7;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #38bdf8;
    border: 2px solid #0b0f19;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #7dd3fc;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #334155;
    border-radius: 4px;
    background-color: #0b0f19;
}

QCheckBox::indicator:checked {
    background-color: #0284c7;
    border-color: #38bdf8;
}

/* Splitters */
QSplitter::handle {
    background-color: #1e293b;
}

QSplitter::handle:hover {
    background-color: #38bdf8;
}

/* Labels */
QLabel.header-title {
    font-size: 16px;
    font-weight: 700;
    color: #f8fafc;
}

QLabel.badge {
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 11px;
}

QLabel.badge-green {
    background-color: rgba(16, 185, 129, 0.2);
    color: #10b981;
    border: 1px solid #10b981;
}

QLabel.badge-cyan {
    background-color: rgba(56, 189, 248, 0.2);
    color: #38bdf8;
    border: 1px solid #38bdf8;
}

QLabel.badge-amber {
    background-color: rgba(245, 158, 11, 0.2);
    color: #f59e0b;
    border: 1px solid #f59e0b;
}

QLabel.badge-red {
    background-color: rgba(239, 68, 68, 0.2);
    color: #ef4444;
    border: 1px solid #ef4444;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #0b0f19;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}
"""
