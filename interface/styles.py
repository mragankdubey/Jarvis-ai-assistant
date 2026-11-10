"""
Stark Industries Cybernetic HUD Styling for J.A.R.V.I.S.

Features an Iron Man-inspired dark navy/obsidian theme with electric cyan,
neon blue highlights, subtle glowing borders, and technical HUD typography.
"""

# Palette Constants
COLOR_BG_DARK = "#070B12"
COLOR_BG_PANEL = "#0D1321"
COLOR_BG_CARD = "#141C2E"
COLOR_CYAN_PRIMARY = "#00E5FF"
COLOR_CYAN_DIM = "#007799"
COLOR_BLUE_ACCENT = "#0055FF"
COLOR_RED_ALERT = "#FF2A6D"
COLOR_TEXT_WHITE = "#E0F7FA"
COLOR_TEXT_DIM = "#78909C"
COLOR_BORDER = "#1B2A4A"

HUD_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLOR_BG_DARK};
    color: {COLOR_TEXT_WHITE};
}}

QWidget {{
    font-family: 'Segoe UI', 'Consolas', sans-serif;
    color: {COLOR_TEXT_WHITE};
}}

/* Panels and Cards */
QFrame#hudPanel {{
    background-color: {COLOR_BG_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
}}

QFrame#statusCard {{
    background-color: {COLOR_BG_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 6px;
}}

/* Headers and Labels */
QLabel#hudTitle {{
    font-size: 16px;
    font-weight: bold;
    color: {COLOR_CYAN_PRIMARY};
    letter-spacing: 2px;
}}

QLabel#sectionHeader {{
    font-size: 12px;
    font-weight: bold;
    color: {COLOR_CYAN_DIM};
    letter-spacing: 1.5px;
    text-transform: uppercase;
}}

QLabel#statusValue {{
    font-size: 11px;
    color: {COLOR_TEXT_WHITE};
    font-weight: 500;
}}

/* Buttons */
QPushButton {{
    background-color: {COLOR_BG_CARD};
    color: {COLOR_CYAN_PRIMARY};
    border: 1px solid {COLOR_CYAN_DIM};
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 1px;
}}

QPushButton:hover {{
    background-color: {COLOR_CYAN_DIM};
    color: #FFFFFF;
    border: 1px solid {COLOR_CYAN_PRIMARY};
}}

QPushButton:pressed {{
    background-color: {COLOR_CYAN_PRIMARY};
    color: {COLOR_BG_DARK};
}}

QPushButton#actionButton {{
    background-color: rgba(0, 229, 255, 0.08);
    border: 1px solid {COLOR_CYAN_DIM};
}}

QPushButton#actionButton:hover {{
    background-color: rgba(0, 229, 255, 0.25);
    border: 1px solid {COLOR_CYAN_PRIMARY};
}}

QPushButton#micButton {{
    background-color: rgba(0, 229, 255, 0.15);
    border: 1px solid {COLOR_CYAN_PRIMARY};
    border-radius: 18px;
    font-size: 14px;
}}

QPushButton#micButton:hover {{
    background-color: {COLOR_CYAN_PRIMARY};
    color: {COLOR_BG_DARK};
}}

/* Text Input & Message Log */
QLineEdit#commandInput {{
    background-color: {COLOR_BG_DARK};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    color: {COLOR_TEXT_WHITE};
    padding: 8px 12px;
    font-size: 12px;
    selection-background-color: {COLOR_CYAN_DIM};
}}

QLineEdit#commandInput:focus {{
    border: 1px solid {COLOR_CYAN_PRIMARY};
}}

QTextEdit#chatLog {{
    background-color: {COLOR_BG_DARK};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    color: {COLOR_TEXT_WHITE};
    padding: 8px;
    font-size: 12px;
    line-height: 1.4;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: {COLOR_BG_DARK};
    width: 6px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {COLOR_CYAN_DIM};
    min-height: 20px;
    border-radius: 3px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""
