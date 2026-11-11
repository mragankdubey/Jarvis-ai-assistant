"""
HUD Settings Screen for J.A.R.V.I.S. PySide6 Application.

Organized into clean cybernetic categories with custom animated toggle
switches, precision sliders, credential safety indicators, and instant save feedback.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from core.config import Config
from interface.components import HudFrame, HudToggleSwitch
from interface.theme import HudPalette


class SettingsScreen(QWidget):
    """Categorized HUD settings and configuration editor."""

    settings_saved = Signal()

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self._init_ui()
        self.load_from_config(config)

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        grid_root = QGridLayout(body)
        grid_root.setContentsMargins(0, 0, 6, 0)
        grid_root.setSpacing(12)

        # === CATEGORY 1: AI & IDENTITY ===
        ai_frame = HudFrame()
        ai_l = QVBoxLayout(ai_frame)
        ai_l.setContentsMargins(16, 14, 16, 14)
        ai_l.setSpacing(10)
        ai_hdr = QLabel("IDENTITY & AI INTELLIGENCE")
        ai_hdr.setObjectName("sectionHeader")
        ai_l.addWidget(ai_hdr)

        ai_grid = QGridLayout()
        ai_grid.setSpacing(10)
        ai_grid.addWidget(self._lbl("USER DESIGNATION"), 0, 0)
        self.user_name_edit = QLineEdit()
        ai_grid.addWidget(self.user_name_edit, 0, 1)

        ai_grid.addWidget(self._lbl("AI PROVIDER"), 1, 0)
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["auto", "groq", "gemini"])
        ai_grid.addWidget(self.provider_combo, 1, 1)

        ai_grid.addWidget(self._lbl("CREDENTIAL STATUS"), 2, 0)
        self.cred_status_lbl = QLabel("")
        self.cred_status_lbl.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 10px; color: {HudPalette.CYAN_ICE};"
        )
        ai_grid.addWidget(self.cred_status_lbl, 2, 1)
        ai_l.addLayout(ai_grid)
        ai_l.addStretch(1)
        grid_root.addWidget(ai_frame, 0, 0)

        # === CATEGORY 2: VOICE SYNTHESIS ===
        tts_frame = HudFrame()
        tts_l = QVBoxLayout(tts_frame)
        tts_l.setContentsMargins(16, 14, 16, 14)
        tts_l.setSpacing(10)
        tts_hdr = QLabel("VOICE SYNTHESIS (TTS)")
        tts_hdr.setObjectName("sectionHeader")
        tts_l.addWidget(tts_hdr)

        tts_grid = QGridLayout()
        tts_grid.setSpacing(10)
        tts_grid.addWidget(self._lbl("SPEAK RESPONSES ALOUD"), 0, 0)
        self.voice_toggle = HudToggleSwitch(True)
        tts_grid.addWidget(self.voice_toggle, 0, 1, alignment=Qt.AlignRight)

        tts_grid.addWidget(self._lbl("SPEECH RATE (WPM)"), 1, 0)
        rate_row, self.rate_slider, self.rate_val_lbl = self._slider_row(120, 260, 180, " wpm")
        tts_grid.addLayout(rate_row, 1, 1)

        tts_grid.addWidget(self._lbl("OUTPUT VOLUME"), 2, 0)
        vol_row, self.vol_slider, self.vol_val_lbl = self._slider_row(0, 100, 100, "%")
        tts_grid.addLayout(vol_row, 2, 1)
        tts_l.addLayout(tts_grid)
        tts_l.addStretch(1)
        grid_root.addWidget(tts_frame, 0, 1)

        # === CATEGORY 3: WAKE WORD & CONVERSATION ===
        ww_frame = HudFrame()
        ww_l = QVBoxLayout(ww_frame)
        ww_l.setContentsMargins(16, 14, 16, 14)
        ww_l.setSpacing(10)
        ww_hdr = QLabel("WAKE WORD & VOICE SESSION")
        ww_hdr.setObjectName("sectionHeader")
        ww_l.addWidget(ww_hdr)

        ww_grid = QGridLayout()
        ww_grid.setSpacing(10)
        ww_grid.addWidget(self._lbl("LOCAL WAKE WORD ('HEY JARVIS')"), 0, 0)
        self.wake_toggle = HudToggleSwitch(True)
        ww_grid.addWidget(self.wake_toggle, 0, 1, alignment=Qt.AlignRight)

        ww_grid.addWidget(self._lbl("DETECTION THRESHOLD"), 1, 0)
        thr_row, self.thresh_slider, self.thresh_val_lbl = self._slider_row(20, 90, 50, "%")
        ww_grid.addLayout(thr_row, 1, 1)

        ww_grid.addWidget(self._lbl("INACTIVITY SLEEP TIMEOUT"), 2, 0)
        to_row, self.timeout_slider, self.timeout_val_lbl = self._slider_row(4, 30, 10, "s")
        ww_grid.addLayout(to_row, 2, 1)
        ww_l.addLayout(ww_grid)
        ww_l.addStretch(1)
        grid_root.addWidget(ww_frame, 1, 0)

        # === CATEGORY 4: INTERFACE & STARTUP ===
        ui_frame = HudFrame()
        ui_l = QVBoxLayout(ui_frame)
        ui_l.setContentsMargins(16, 14, 16, 14)
        ui_l.setSpacing(10)
        ui_hdr = QLabel("INTERFACE & SYSTEM TRAY")
        ui_hdr.setObjectName("sectionHeader")
        ui_l.addWidget(ui_hdr)

        ui_grid = QGridLayout()
        ui_grid.setSpacing(10)
        ui_grid.addWidget(self._lbl("CINEMATIC STARTUP SEQUENCE"), 0, 0)
        self.startup_toggle = HudToggleSwitch(True)
        ui_grid.addWidget(self.startup_toggle, 0, 1, alignment=Qt.AlignRight)

        ui_grid.addWidget(self._lbl("MINIMIZE TO TRAY ON CLOSE"), 1, 0)
        self.tray_toggle = HudToggleSwitch(True)
        ui_grid.addWidget(self.tray_toggle, 1, 1, alignment=Qt.AlignRight)

        ui_grid.addWidget(self._lbl("HUD ACCENT INTENSITY"), 2, 0)
        acc_row, self.accent_slider, self.accent_val_lbl = self._slider_row(30, 100, 85, "%")
        ui_grid.addLayout(acc_row, 2, 1)
        ui_l.addLayout(ui_grid)
        ui_l.addStretch(1)
        grid_root.addWidget(ui_frame, 1, 1)

        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

        # Bottom Save Strip
        footer = HudFrame()
        footer_l = QHBoxLayout(footer)
        footer_l.setContentsMargins(16, 10, 16, 10)
        self.save_note = QLabel("Settings are persisted locally in SQLite. API keys remain protected in .env.")
        self.save_note.setStyleSheet(f"font-size: 11px; color: {HudPalette.TEXT_SECONDARY};")
        footer_l.addWidget(self.save_note, stretch=1)

        save_btn = QPushButton("SAVE && APPLY SETTINGS")
        save_btn.setObjectName("primaryButton")
        save_btn.setMinimumHeight(34)
        save_btn.clicked.connect(self._on_save)
        footer_l.addWidget(save_btn)
        root.addWidget(footer)

    def _lbl(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {HudPalette.TEXT_PRIMARY};")
        return l

    def _slider_row(self, mn: int, mx: int, val: int, suffix: str):
        row = QHBoxLayout()
        row.setSpacing(8)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(mn, mx)
        slider.setValue(val)
        lbl = QLabel(f"{val}{suffix}")
        lbl.setFixedWidth(54)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setStyleSheet(f"font-family: 'Consolas', monospace; font-size: 11px; color: {HudPalette.CYAN_ELECTRIC};")
        slider.valueChanged.connect(lambda v: lbl.setText(f"{v}{suffix}"))
        row.addWidget(slider, stretch=1)
        row.addWidget(lbl)
        return row, slider, lbl

    def load_from_config(self, cfg: Config) -> None:
        self.user_name_edit.setText(cfg.user_name)
        idx = self.provider_combo.findText(cfg.ai_provider)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)

        summary = cfg.status_summary()
        self.cred_status_lbl.setText(
            f"Groq: {summary['Groq API']}  |  Gemini: {summary['Gemini API']}  |  News: {summary['NewsAPI']}"
        )

        self.voice_toggle.setChecked(cfg.voice_enabled)
        self.rate_slider.setValue(cfg.voice_rate)
        self.vol_slider.setValue(int(cfg.voice_volume * 100))

        self.wake_toggle.setChecked(cfg.wake_word_enabled)
        self.thresh_slider.setValue(int(cfg.wake_word_threshold * 100))
        self.timeout_slider.setValue(int(cfg.inactivity_timeout))

        self.startup_toggle.setChecked(cfg.startup_animation)
        self.tray_toggle.setChecked(cfg.minimize_to_tray)
        self.accent_slider.setValue(cfg.accent_intensity)

    def _on_save(self) -> None:
        self.config.user_name = self.user_name_edit.text().strip() or "Mragank"
        self.config.ai_provider = self.provider_combo.currentText()
        self.config.voice_enabled = self.voice_toggle.isChecked()
        self.config.voice_rate = self.rate_slider.value()
        self.config.voice_volume = self.vol_slider.value() / 100.0
        self.config.wake_word_enabled = self.wake_toggle.isChecked()
        self.config.wake_word_threshold = self.thresh_slider.value() / 100.0
        self.config.inactivity_timeout = float(self.timeout_slider.value())
        self.config.startup_animation = self.startup_toggle.isChecked()
        self.config.minimize_to_tray = self.tray_toggle.isChecked()
        self.config.accent_intensity = self.accent_slider.value()

        self.settings_saved.emit()
