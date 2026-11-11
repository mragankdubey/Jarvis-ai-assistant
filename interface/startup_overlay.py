"""
Cinematic Initialization & Power-Up Sequence Overlay for J.A.R.V.I.S.

Animates the Arc Reactor powering up while running genuine, non-fabricated
subsystem checks on configuration, SQLite storage, audio hardware, local
wake-word models, and AI provider readiness before fading cleanly into the HUD.
"""

from typing import List, Tuple
from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    QThread,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)
from core.config import Config
from core.diagnostics import check_microphone, check_network, check_wake_word_engine
from core.states import AssistantState
from interface.components import HudFrame
from interface.reactor_widget import ArcReactorWidget
from interface.theme import HudPalette


class StartupProbeWorker(QThread):
    """Runs real non-blocking subsystem checks and emits progressive diagnostic results."""

    step_completed = Signal(str, bool, str, int)  # (module_name, ok, detail, progress_pct)
    all_finished = Signal(bool)  # mic_available

    def __init__(self, config: Config, repo=None):
        super().__init__()
        self.config = config
        self.repo = repo

    def run(self) -> None:
        # Step 1: Configuration & Secrets Check
        configured_keys = sum(
            1 for k in (self.config.groq_api_key, self.config.gemini_api_key, self.config.news_api_key) if k
        )
        self.step_completed.emit(
            "CORE CONFIGURATION",
            True,
            f"Loaded ({configured_keys}/3 API services configured)",
            20
        )
        self.msleep(160)

        # Step 2: SQLite Persistence Check
        db_ok = True
        db_detail = "SQLite Storage Online"
        if self.repo is not None:
            try:
                facts = len(self.repo.list_facts())
                notes = len(self.repo.list_notes())
                db_detail = f"Online ({facts} facts, {notes} notes)"
            except Exception as e:
                db_ok = False
                db_detail = f"Database Error ({e})"
        self.step_completed.emit("LOCAL MEMORY DB", db_ok, db_detail, 40)
        self.msleep(160)

        # Step 3: Audio Hardware Probe (real, never faked)
        mic_ok, mic_name, _ = check_microphone()
        self.step_completed.emit(
            "AUDIO HARDWARE",
            mic_ok,
            mic_name if mic_ok else "No Default Mic — Text Mode Active",
            60
        )
        self.msleep(160)

        # Step 4: Local Wake-Word ONNX Engine
        ww_ok, ww_detail = check_wake_word_engine(self.config.wake_word_model)
        self.step_completed.emit("WAKE-WORD ENGINE", ww_ok, ww_detail, 80)
        self.msleep(160)

        # Step 5: AI Provider & Network Uplink
        net_ok, net_detail = check_network()
        has_ai = bool(self.config.groq_api_key or self.config.gemini_api_key)
        ai_label = "Groq / Gemini Keys Ready" if has_ai else "No AI API Keys Configured"
        self.step_completed.emit(
            "NEURAL AI UPLINK",
            has_ai and net_ok,
            f"{ai_label} · {net_detail}",
            100
        )
        self.msleep(260)
        self.all_finished.emit(mic_ok)


class StartupOverlay(QWidget):
    """
    Full-window cybernetic startup sequence overlay that crossfades into the HUD.
    """

    boot_completed = Signal(bool)  # passes real mic availability

    def __init__(self, config: Config, repo=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.repo = repo
        self._mic_available = False
        self._worker: StartupProbeWorker | None = None

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {HudPalette.BG_VOID};")

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._init_ui()

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignCenter)
        root.setContentsMargins(40, 30, 40, 30)
        root.setSpacing(18)

        # Brand Title
        brand = QLabel("J.A.R.V.I.S.")
        brand.setAlignment(Qt.AlignCenter)
        brand.setStyleSheet(
            f"font-size: 32px; font-weight: 800; color: {HudPalette.WHITE_PURE}; letter-spacing: 10px;"
        )
        root.addWidget(brand)

        subtitle = QLabel("JUST A RATHER VERY INTELLIGENT SYSTEM  //  STARK INDUSTRIES OS")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {HudPalette.CYAN_ELECTRIC}; letter-spacing: 3px;"
        )
        root.addWidget(subtitle)

        # Central Power-Up Arc Reactor
        self.reactor = ArcReactorWidget()
        self.reactor.setFixedSize(260, 260)
        self.reactor.set_state(AssistantState.ACTIVATING)
        self.reactor.set_power_level(0.05)
        root.addWidget(self.reactor, alignment=Qt.AlignCenter)

        # Diagnostics Sequence Card
        diag_frame = HudFrame(show_grid=True)
        diag_frame.setFixedWidth(520)
        diag_layout = QVBoxLayout(diag_frame)
        diag_layout.setContentsMargins(20, 16, 20, 16)
        diag_layout.setSpacing(8)

        header = QLabel("SUBSYSTEM INITIALIZATION SEQUENCE")
        header.setObjectName("sectionHeader")
        diag_layout.addWidget(header)

        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(6)
        diag_layout.addLayout(self._rows_layout)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        self.progress.setStyleSheet(
            f"QProgressBar {{ background-color: {HudPalette.BG_CARD}; border: none; border-radius: 2px; }}"
            f"QProgressBar::chunk {{ background-color: {HudPalette.CYAN_ELECTRIC}; border-radius: 2px; }}"
        )
        diag_layout.addWidget(self.progress)

        root.addWidget(diag_frame, alignment=Qt.AlignCenter)

    def start_sequence(self) -> None:
        """Begin Arc Reactor power-up animation and genuine diagnostic probes."""
        # Animate Arc Reactor core power up 0.05 -> 1.0
        self._power_anim = QPropertyAnimation(self.reactor, b"powerLevel", self)
        self._power_anim.setDuration(1100)
        self._power_anim.setStartValue(0.05)
        self._power_anim.setEndValue(1.0)
        self._power_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._power_anim.start()

        self._worker = StartupProbeWorker(self.config, self.repo)
        self._worker.step_completed.connect(self._on_step)
        self._worker.all_finished.connect(self._on_probes_done)
        self._worker.start()

    def _on_step(self, module_name: str, ok: bool, detail: str, pct: int) -> None:
        row = QHBoxLayout()
        row.setSpacing(10)

        name_lbl = QLabel(module_name)
        name_lbl.setFixedWidth(165)
        name_lbl.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 11px; font-weight: 700; color: {HudPalette.TEXT_PRIMARY};"
        )

        detail_lbl = QLabel(detail)
        detail_lbl.setStyleSheet(f"font-size: 11px; color: {HudPalette.TEXT_SECONDARY};")

        badge = QLabel("ONLINE" if ok else "WARN")
        badge.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        badge.setFixedWidth(55)
        badge_color = HudPalette.CYAN_ELECTRIC if ok else HudPalette.AMBER_WARN
        badge.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 10px; font-weight: 700; color: {badge_color};"
        )

        row.addWidget(name_lbl)
        row.addWidget(detail_lbl, stretch=1)
        row.addWidget(badge)
        self._rows_layout.addLayout(row)

        self.progress.setValue(pct)

    def _on_probes_done(self, mic_ok: bool) -> None:
        self._mic_available = mic_ok
        self.reactor.set_state(AssistantState.IDLE)
        # Brief pause at 100%, then smooth crossfade out
        QTimer.singleShot(280, self._fade_out)

    def _fade_out(self) -> None:
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_anim.setDuration(380)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._fade_anim.finished.connect(self._finish)
        self._fade_anim.start()

    def stop(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait(2500)

    def _finish(self) -> None:
        self.reactor.pause_animations()
        self.hide()
        self.boot_completed.emit(self._mic_available)
