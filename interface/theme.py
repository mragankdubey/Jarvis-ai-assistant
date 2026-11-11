"""
Centralized Design System & Stark HUD Theme for J.A.R.V.I.S.

Defines color tokens, typography scale, dynamic accent intensity helpers,
and unified QSS stylesheets across all screens and reusable widgets.
"""

from PySide6.QtGui import QColor


class HudPalette:
    """Iron Man / Stark Industries inspired deep obsidian & electric cyan palette."""
    BG_VOID = "#04070D"
    BG_DARK = "#070B14"
    BG_PANEL = "#0B111E"
    BG_CARD = "#10192B"
    BG_ELEVATED = "#162238"

    CYAN_ELECTRIC = "#00E5FF"
    CYAN_ICE = "#80F3FF"
    CYAN_MID = "#00A8CC"
    CYAN_DIM = "#0E4B68"
    BLUE_DEEP = "#0066FF"

    WHITE_PURE = "#F2FAFF"
    TEXT_PRIMARY = "#E2F1F8"
    TEXT_SECONDARY = "#8EA4BC"
    TEXT_MUTED = "#51657A"

    RED_ALERT = "#FF2E63"
    AMBER_WARN = "#FFB300"
    GREEN_OK = "#00E676"

    BORDER_SUBTLE = "#162640"
    BORDER_GLOW = "#1B4B6B"


def qcolor_with_alpha(hex_color: str, alpha: int) -> QColor:
    """Create QColor from hex string with specified 0-255 alpha."""
    c = QColor(hex_color)
    c.setAlpha(max(0, min(255, alpha)))
    return c


def build_stylesheet(accent_intensity: int = 85) -> str:
    """
    Generate unified QSS stylesheet tuned by accent_intensity (30-100).
    """
    alpha_scale = max(0.3, min(1.0, accent_intensity / 100.0))
    border_alpha = int(160 * alpha_scale)
    hover_alpha = int(55 * alpha_scale)

    return f"""
    QMainWindow, QWidget#rootWindow {{
        background-color: {HudPalette.BG_VOID};
        color: {HudPalette.TEXT_PRIMARY};
    }}

    QWidget {{
        font-family: 'Segoe UI', 'Bahnschrift', 'Consolas', sans-serif;
        color: {HudPalette.TEXT_PRIMARY};
    }}

    QLabel {{
        background: transparent;
        border: none;
    }}

    QFrame#topBar, QFrame#navRail, QFrame#listCard {{
        background-color: {HudPalette.BG_PANEL};
        border: 1px solid {HudPalette.BORDER_SUBTLE};
        border-radius: 6px;
    }}

    QFrame#listCard {{
        background-color: {HudPalette.BG_CARD};
        border-radius: 5px;
    }}

    QLabel#brandTitle {{
        font-size: 15px;
        font-weight: 700;
        color: {HudPalette.WHITE_PURE};
        letter-spacing: 3px;
    }}

    QLabel#brandSub {{
        font-size: 10px;
        font-weight: 600;
        color: {HudPalette.CYAN_ELECTRIC};
        letter-spacing: 2px;
    }}

    QLabel#screenTitle {{
        font-size: 18px;
        font-weight: 700;
        color: {HudPalette.WHITE_PURE};
        letter-spacing: 2px;
    }}

    QLabel#sectionHeader {{
        font-size: 10px;
        font-weight: 700;
        color: {HudPalette.CYAN_MID};
        letter-spacing: 1.8px;
    }}

    QLabel#metricValue {{
        font-family: 'Consolas', 'Cascadia Mono', 'Segoe UI', monospace;
        font-size: 13px;
        font-weight: 700;
        color: {HudPalette.CYAN_ICE};
    }}

    QLabel#clockLabel {{
        font-family: 'Consolas', 'Cascadia Mono', monospace;
        font-size: 15px;
        font-weight: 700;
        color: {HudPalette.WHITE_PURE};
        letter-spacing: 1.5px;
    }}

    QLabel#dateLabel {{
        font-size: 10px;
        font-weight: 600;
        color: {HudPalette.TEXT_SECONDARY};
        letter-spacing: 1px;
    }}

    /* Navigation Rail Buttons */
    QPushButton#navButton {{
        background-color: transparent;
        color: {HudPalette.TEXT_SECONDARY};
        border: 1px solid transparent;
        border-left: 3px solid transparent;
        border-radius: 4px;
        padding: 10px 10px;
        text-align: left;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.8px;
    }}

    QPushButton#navButton:hover {{
        background-color: rgba(0, 229, 255, 0.08);
        color: {HudPalette.WHITE_PURE};
    }}

    QPushButton#navButton[active="true"] {{
        background-color: rgba(0, 229, 255, 0.14);
        color: {HudPalette.CYAN_ELECTRIC};
        border-left: 3px solid {HudPalette.CYAN_ELECTRIC};
        border-top: 1px solid rgba(0, 229, 255, 0.20);
        border-right: 1px solid rgba(0, 229, 255, 0.10);
        border-bottom: 1px solid rgba(0, 229, 255, 0.20);
    }}

    /* Standard Tactical Buttons */
    QPushButton {{
        background-color: {HudPalette.BG_CARD};
        color: {HudPalette.CYAN_ICE};
        border: 1px solid rgba(0, 168, 204, {border_alpha});
        border-radius: 5px;
        padding: 7px 14px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.9px;
    }}

    QPushButton:hover {{
        background-color: rgba(0, 229, 255, {hover_alpha});
        color: {HudPalette.WHITE_PURE};
        border: 1px solid {HudPalette.CYAN_ELECTRIC};
    }}

    QPushButton:pressed {{
        background-color: {HudPalette.CYAN_ELECTRIC};
        color: {HudPalette.BG_VOID};
    }}

    QPushButton#primaryButton {{
        background-color: rgba(0, 229, 255, 0.18);
        color: {HudPalette.CYAN_ELECTRIC};
        border: 1px solid {HudPalette.CYAN_ELECTRIC};
        font-weight: 700;
    }}

    QPushButton#primaryButton:hover {{
        background-color: {HudPalette.CYAN_ELECTRIC};
        color: {HudPalette.BG_VOID};
    }}

    QPushButton#dangerButton {{
        background-color: rgba(255, 46, 99, 0.12);
        color: {HudPalette.RED_ALERT};
        border: 1px solid rgba(255, 46, 99, 0.5);
    }}

    QPushButton#dangerButton:hover {{
        background-color: {HudPalette.RED_ALERT};
        color: {HudPalette.WHITE_PURE};
    }}

    QPushButton#chromeButton {{
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 4px 8px;
        color: {HudPalette.TEXT_SECONDARY};
    }}

    QPushButton#chromeButton:hover {{
        background-color: rgba(0, 229, 255, 0.15);
        color: {HudPalette.WHITE_PURE};
    }}

    QPushButton#chromeCloseButton {{
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 4px 8px;
        color: {HudPalette.TEXT_SECONDARY};
    }}

    QPushButton#chromeCloseButton:hover {{
        background-color: rgba(255, 46, 99, 0.85);
        color: {HudPalette.WHITE_PURE};
    }}

    /* Inputs, Text Areas & ComboBoxes */
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDateTimeEdit {{
        background-color: {HudPalette.BG_DARK};
        color: {HudPalette.TEXT_PRIMARY};
        border: 1px solid {HudPalette.BORDER_GLOW};
        border-radius: 5px;
        padding: 8px 12px;
        font-size: 12px;
        selection-background-color: {HudPalette.CYAN_DIM};
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QDateTimeEdit:focus {{
        border: 1px solid {HudPalette.CYAN_ELECTRIC};
        background-color: #09101E;
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {HudPalette.BG_PANEL};
        color: {HudPalette.TEXT_PRIMARY};
        border: 1px solid {HudPalette.CYAN_ELECTRIC};
        selection-background-color: {HudPalette.CYAN_DIM};
    }}

    /* Sliders */
    QSlider::groove:horizontal {{
        height: 4px;
        background: {HudPalette.BORDER_SUBTLE};
        border-radius: 2px;
    }}

    QSlider::sub-page:horizontal {{
        background: {HudPalette.CYAN_ELECTRIC};
        border-radius: 2px;
    }}

    QSlider::handle:horizontal {{
        background: {HudPalette.WHITE_PURE};
        border: 2px solid {HudPalette.CYAN_ELECTRIC};
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }}

    /* ScrollArea & Scrollbars */
    QScrollArea {{
        background: transparent;
        border: none;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical {{
        background: {HudPalette.CYAN_DIM};
        min-height: 24px;
        border-radius: 3px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {HudPalette.CYAN_ELECTRIC};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        height: 0px;
    }}
    """
