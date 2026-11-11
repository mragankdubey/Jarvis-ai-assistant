"""
Master Stark Industries HUD Window for J.A.R.V.I.S. PySide6 Desktop Application.

Integrates custom frameless cybernetic window chrome, left vector navigation
rail across 7 dedicated screens, cinematic startup sequence, real-time telemetry,
thread-safe Signal bridges, system tray daemon control, and due-reminder alerts.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from PySide6.QtCore import (
    QEasingCurve,
    QObject,
    QPoint,
    QPropertyAnimation,
    QSize,
    Qt,
    QThread,
    QTimer,
    Signal,
)
from PySide6.QtGui import QCloseEvent, QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizeGrip,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from core.assistant import Assistant
from core.config import Config, get_config
from core.diagnostics import get_system_telemetry
from core.states import AssistantState
from database.models import JarvisRepository
from interface.components import ToastNotification, create_vector_icon
from interface.icon_generator import get_app_icon
from interface.screens import (
    ConversationScreen,
    DashboardScreen,
    MemoryScreen,
    NotesScreen,
    RemindersScreen,
    SettingsScreen,
    SystemScreen,
)
from interface.startup_overlay import StartupOverlay
from interface.system_tray import SystemTrayController, create_reactor_pixmap
from interface.theme import HudPalette, build_stylesheet


class AssistantBridge(QObject):
    """Thread-safe Qt Signal bridge from Assistant threads to MainWindow GUI."""
    state_changed = Signal(str)
    message_received = Signal(str, str)
    audio_level_changed = Signal(float)
    window_action_requested = Signal(str)


class CommandWorker(QThread):
    """Background worker for non-blocking text command execution."""
    result_ready = Signal(str)

    def __init__(self, assistant: Assistant, command: str):
        super().__init__()
        self.assistant = assistant
        self.command = command

    def run(self) -> None:
        response = self.assistant.process_text_command(self.command)
        self.result_ready.emit(response)


class MainWindow(QMainWindow):
    """
    Primary Stark Industries Command Centre HUD Window.
    """

    NAV_ITEMS = [
        ("dashboard", "DASHBOARD", "dashboard"),
        ("chat", "AI CONVERSATION", "chat"),
        ("memory", "MEMORY", "memory"),
        ("notes", "NOTES", "notes"),
        ("reminders", "REMINDERS", "reminders"),
        ("system", "SYSTEM STATUS", "system"),
        ("settings", "SETTINGS", "settings"),
    ]

    def __init__(
        self,
        assistant: Optional[Assistant] = None,
        repo: Optional[JarvisRepository] = None,
        skip_startup: bool = False,
    ):
        super().__init__()
        self.config: Config = get_config()
        self.repo = repo or JarvisRepository()
        self.bridge = AssistantBridge()
        self._drag_pos: Optional[QPoint] = None
        self._nav_buttons: Dict[str, QPushButton] = {}
        self._screen_indices: Dict[str, int] = {}
        self._reminder_tick = 0

        # Wire or construct Assistant
        if assistant is None:
            self.assistant = Assistant(
                config=self.config,
                repo=self.repo,
                on_state_change=self._on_assistant_state,
                on_message=self._on_assistant_message,
                on_audio_level=self._on_audio_level,
                on_window_action=self._on_window_action,
            )
        else:
            self.assistant = assistant
            self.assistant.repo = self.repo
            self.assistant.on_state_change = self._on_assistant_state
            self.assistant.on_message = self._on_assistant_message
            self.assistant.on_audio_level = self._on_audio_level
            self.assistant.on_window_action = self._on_window_action

        # Window Identity & Frameless Chrome
        self.setWindowTitle("J.A.R.V.I.S. — STARK INDUSTRIES COMMAND CENTRE")
        self.setWindowIcon(get_app_icon())
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.resize(1240, 780)
        self.setMinimumSize(1024, 650)
        self.setStyleSheet(build_stylesheet(self.config.accent_intensity))

        # System Tray
        self.tray = SystemTrayController(self)
        self.tray.show_requested.connect(self._show_hud)
        self.tray.hide_requested.connect(self._hide_to_tray)
        self.tray.toggle_voice_requested.connect(self.assistant.trigger_activation)
        self.tray.sleep_requested.connect(lambda: self._run_command("go to sleep"))
        self.tray.exit_requested.connect(self._full_exit)
        self.tray.show()

        self._init_ui()
        self._connect_signals()
        self._hydrate_persisted_data()
        self._init_timers()

        # Toast overlay
        self.toast = ToastNotification(self)

        # Startup sequence
        if not skip_startup and self.config.startup_animation:
            self.startup_overlay = StartupOverlay(self.config, self.repo, self)
            self.startup_overlay.setGeometry(self.rect())
            self.startup_overlay.boot_completed.connect(self._on_startup_done)
            self.startup_overlay.raise_()
            self.startup_overlay.show()
            QTimer.singleShot(60, self.startup_overlay.start_sequence)
        else:
            self.startup_overlay = None
            mic_ok = self.assistant.probe_audio()
            self._apply_mic_status(mic_ok)

    # --- Thread-Safe Signal Marshaling ---
    def _on_assistant_state(self, state: AssistantState) -> None:
        self.bridge.state_changed.emit(state.value)

    def _on_assistant_message(self, role: str, text: str) -> None:
        self.bridge.message_received.emit(role, text)

    def _on_audio_level(self, level: float) -> None:
        self.bridge.audio_level_changed.emit(level)

    def _on_window_action(self, action: str) -> None:
        self.bridge.window_action_requested.emit(action)

    # --- UI Construction ---
    def _init_ui(self) -> None:
        root_widget = QWidget(self)
        root_widget.setObjectName("rootWindow")
        self.setCentralWidget(root_widget)

        outer = QVBoxLayout(root_widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Outer border container for frameless definition
        shell = QFrame()
        shell.setStyleSheet(
            f"QFrame#outerShell {{ background-color: {HudPalette.BG_VOID}; border: 1px solid {HudPalette.BORDER_GLOW}; }}"
        )
        shell.setObjectName("outerShell")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(14, 10, 14, 12)
        shell_layout.setSpacing(10)

        # 1. Custom Top Command Chrome Bar
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(44)
        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(12, 4, 10, 4)
        tb_layout.setSpacing(12)

        # Emblem + Title
        icon_lbl = QLabel()
        icon_lbl.setPixmap(create_reactor_pixmap(24))
        tb_layout.addWidget(icon_lbl)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(0)
        brand_title = QLabel("J.A.R.V.I.S.")
        brand_title.setObjectName("brandTitle")
        brand_sub = QLabel("STARK INDUSTRIES COMMAND CENTRE")
        brand_sub.setObjectName("brandSub")
        brand_col.addWidget(brand_title)
        brand_col.addWidget(brand_sub)
        tb_layout.addLayout(brand_col)

        tb_layout.addStretch(1)

        # Current View Title
        self.view_title_lbl = QLabel("DASHBOARD")
        self.view_title_lbl.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 11px; font-weight: 700; "
            f"color: {HudPalette.TEXT_SECONDARY}; letter-spacing: 2px;"
        )
        tb_layout.addWidget(self.view_title_lbl)

        tb_layout.addStretch(1)

        # Global State Pill
        self.state_pill = QLabel("STATE: IDLE")
        self.state_pill.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 10px; font-weight: 700; "
            f"color: {HudPalette.CYAN_ELECTRIC}; background: rgba(0, 229, 255, 0.12); "
            f"border: 1px solid {HudPalette.CYAN_DIM}; border-radius: 4px; padding: 4px 10px;"
        )
        tb_layout.addWidget(self.state_pill)

        # Date & Clock Block
        time_col = QVBoxLayout()
        time_col.setSpacing(0)
        self.clock_lbl = QLabel("--:--:--")
        self.clock_lbl.setObjectName("clockLabel")
        self.clock_lbl.setAlignment(Qt.AlignRight)
        self.date_lbl = QLabel("---")
        self.date_lbl.setObjectName("dateLabel")
        self.date_lbl.setAlignment(Qt.AlignRight)
        time_col.addWidget(self.clock_lbl)
        time_col.addWidget(self.date_lbl)
        tb_layout.addLayout(time_col)

        # Window Controls
        min_btn = QPushButton("—")
        min_btn.setObjectName("chromeButton")
        min_btn.setFixedSize(30, 28)
        min_btn.clicked.connect(self.showMinimized)

        max_btn = QPushButton("□")
        max_btn.setObjectName("chromeButton")
        max_btn.setFixedSize(30, 28)
        max_btn.clicked.connect(self._toggle_maximize)

        close_btn = QPushButton("×")
        close_btn.setObjectName("chromeCloseButton")
        close_btn.setFixedSize(30, 28)
        close_btn.clicked.connect(self.close)

        tb_layout.addWidget(min_btn)
        tb_layout.addWidget(max_btn)
        tb_layout.addWidget(close_btn)

        self._top_bar = top_bar
        shell_layout.addWidget(top_bar)

        # 2. Body: Left Navigation Rail + Multi-Screen Stacked Content
        body_row = QHBoxLayout()
        body_row.setSpacing(12)

        # Left Navigation Rail
        nav_rail = QFrame()
        nav_rail.setObjectName("navRail")
        nav_rail.setFixedWidth(204)
        nav_layout = QVBoxLayout(nav_rail)
        nav_layout.setContentsMargins(10, 14, 10, 12)
        nav_layout.setSpacing(6)

        nav_hdr = QLabel("NAVIGATION")
        nav_hdr.setObjectName("sectionHeader")
        nav_hdr.setContentsMargins(6, 0, 0, 6)
        nav_layout.addWidget(nav_hdr)

        for key, label, icon_name in self.NAV_ITEMS:
            btn = QPushButton(f"  {label}")
            btn.setObjectName("navButton")
            btn.setIcon(create_vector_icon(icon_name, HudPalette.CYAN_ELECTRIC, 16))
            btn.setIconSize(QSize(16, 16))
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self.switch_screen(k))
            nav_layout.addWidget(btn)
            self._nav_buttons[key] = btn

        nav_layout.addStretch(1)

        # Operator Badge & Full Exit
        self.operator_lbl = QLabel(f"OPERATOR: {self.config.user_name.upper()}")
        self.operator_lbl.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 9px; font-weight: 700; "
            f"color: {HudPalette.TEXT_MUTED}; padding: 4px 6px;"
        )
        nav_layout.addWidget(self.operator_lbl)

        quit_btn = QPushButton("  EXIT SYSTEM")
        quit_btn.setObjectName("dangerButton")
        quit_btn.setIcon(create_vector_icon("sleep", HudPalette.RED_ALERT, 14))
        quit_btn.setIconSize(QSize(14, 14))
        quit_btn.clicked.connect(self._full_exit)
        nav_layout.addWidget(quit_btn)

        body_row.addWidget(nav_rail)

        # Multi-Screen Content Stack
        self.stack = QStackedWidget()
        self.stack_opacity = QGraphicsOpacityEffect(self.stack)
        self.stack_opacity.setOpacity(1.0)
        self.stack.setGraphicsEffect(self.stack_opacity)

        self.dashboard_screen = DashboardScreen()
        self.chat_screen = ConversationScreen()
        self.memory_screen = MemoryScreen()
        self.notes_screen = NotesScreen()
        self.reminders_screen = RemindersScreen()
        self.system_screen = SystemScreen(self.config.wake_word_model)
        self.settings_screen = SettingsScreen(self.config)

        screens = [
            ("dashboard", self.dashboard_screen),
            ("chat", self.chat_screen),
            ("memory", self.memory_screen),
            ("notes", self.notes_screen),
            ("reminders", self.reminders_screen),
            ("system", self.system_screen),
            ("settings", self.settings_screen),
        ]
        for key, widget in screens:
            idx = self.stack.addWidget(widget)
            self._screen_indices[key] = idx

        body_row.addWidget(self.stack, stretch=1)
        shell_layout.addLayout(body_row, stretch=1)

        # Subtle bottom status / resize grip row
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(4, 0, 0, 0)
        self.footer_info = QLabel("J.A.R.V.I.S. DESKTOP COMMAND ARCHITECTURE  ·  ALL LOCAL SUBSYSTEMS PROTECTED")
        self.footer_info.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 9px; color: {HudPalette.TEXT_MUTED}; letter-spacing: 1px;"
        )
        bottom_row.addWidget(self.footer_info)
        bottom_row.addStretch(1)
        bottom_row.addWidget(QSizeGrip(shell), 0, Qt.AlignBottom | Qt.AlignRight)
        shell_layout.addLayout(bottom_row)

        outer.addWidget(shell)
        self.switch_screen("dashboard", animate=False)

    def _connect_signals(self) -> None:
        # Bridge connections
        self.bridge.state_changed.connect(self._handle_state_update)
        self.bridge.message_received.connect(self._handle_message)
        self.bridge.audio_level_changed.connect(self._handle_audio_level)
        self.bridge.window_action_requested.connect(self._handle_window_action)

        # Dashboard screen
        self.dashboard_screen.quick_command.connect(self._run_command)
        self.dashboard_screen.mic_triggered.connect(self.assistant.trigger_activation)
        self.dashboard_screen.open_reminders_requested.connect(lambda: self.switch_screen("reminders"))
        self.dashboard_screen.chat_panel.command_submitted.connect(self._run_command)
        self.dashboard_screen.chat_panel.mic_clicked.connect(self.assistant.trigger_activation)
        self.dashboard_screen.chat_panel.clear_clicked.connect(self._clear_all_chats)

        # Conversation screen
        self.chat_screen.prompt_clicked.connect(self._run_command)
        self.chat_screen.chat_panel.command_submitted.connect(self._run_command)
        self.chat_screen.chat_panel.mic_clicked.connect(self.assistant.trigger_activation)
        self.chat_screen.chat_panel.clear_clicked.connect(self._clear_all_chats)

        # Memory screen
        self.memory_screen.fact_added.connect(self._on_add_fact)
        self.memory_screen.fact_deleted.connect(self._on_delete_fact)
        self.memory_screen.search_changed.connect(self._refresh_memory)
        self.memory_screen.clear_ram_requested.connect(self._on_clear_ram)

        # Notes screen
        self.notes_screen.note_saved.connect(self._on_save_note)
        self.notes_screen.note_deleted.connect(self._on_delete_note)
        self.notes_screen.search_changed.connect(self._refresh_notes)

        # Reminders screen
        self.reminders_screen.reminder_added.connect(self._on_add_reminder)
        self.reminders_screen.reminder_toggled.connect(self._on_toggle_reminder)
        self.reminders_screen.reminder_deleted.connect(self._on_delete_reminder)

        # Settings screen
        self.settings_screen.settings_saved.connect(self._on_settings_saved)

    def _hydrate_persisted_data(self) -> None:
        # Load recent conversations from SQLite
        recent = self.repo.get_recent_messages(limit=30)
        if recent:
            for msg in recent:
                self.dashboard_screen.chat_panel.append_message(msg.role, msg.content, msg.timestamp[-8:], animate=False)
                self.chat_screen.chat_panel.append_message(msg.role, msg.content, msg.timestamp[-8:], animate=False)
        else:
            welcome = f"All systems initialized, {self.config.user_name}. J.A.R.V.I.S. is online and standing by."
            self.dashboard_screen.chat_panel.append_message("assistant", welcome, animate=False)
            self.chat_screen.chat_panel.append_message("assistant", welcome, animate=False)

        self._refresh_memory()
        self._refresh_notes()
        self._refresh_reminders()
        self._refresh_ai_chips()

    def _init_timers(self) -> None:
        self._tel_timer = QTimer(self)
        self._tel_timer.timeout.connect(self._update_telemetry)
        self._tel_timer.start(1000)
        self._update_telemetry()

    def _on_startup_done(self, mic_ok: bool) -> None:
        self.assistant.has_microphone = mic_ok
        self._apply_mic_status(mic_ok)
        self.dashboard_screen.add_activity("Startup diagnostics completed.")
        self.system_screen.run_diagnostics()

    def _apply_mic_status(self, mic_ok: bool) -> None:
        self.dashboard_screen.chip_mic.set_status(
            "MIC: ONLINE" if mic_ok else "MIC: UNAVAILABLE",
            mic_ok,
            HudPalette.CYAN_ELECTRIC if mic_ok else HudPalette.AMBER_WARN,
        )
        self.dashboard_screen.waveform.set_mic_status(mic_ok, self.config.wake_word_enabled)
        self.chat_screen.waveform.set_mic_status(mic_ok, self.config.wake_word_enabled)
        self.dashboard_screen.chat_panel.set_mic_available(mic_ok)
        self.chat_screen.chat_panel.set_mic_available(mic_ok)

    def _refresh_ai_chips(self) -> None:
        provider = self.assistant.ai.active_provider
        if provider:
            self.dashboard_screen.chip_ai.set_status(f"AI BRAIN: {provider.name.upper()}", True)
            self.chat_screen.provider_lbl.setText(f"PROVIDER: {provider.name.upper()} ({self.config.ai_provider.upper()})")
        else:
            self.dashboard_screen.chip_ai.set_status("AI BRAIN: NO KEYS", False, HudPalette.AMBER_WARN)
            self.chat_screen.provider_lbl.setText("PROVIDER: OFFLINE (CHECK .ENV)")

        self.dashboard_screen.chip_tts.set_status(
            "VOICE TTS: ACTIVE" if self.config.voice_enabled else "VOICE TTS: MUTED",
            self.config.voice_enabled,
            HudPalette.CYAN_ELECTRIC if self.config.voice_enabled else HudPalette.TEXT_MUTED,
        )
        self.dashboard_screen.chip_wake.set_status(
            "WAKE WORD: LOCAL ONNX" if self.config.wake_word_enabled else "WAKE WORD: PAUSED",
            self.config.wake_word_enabled,
            HudPalette.CYAN_ELECTRIC if self.config.wake_word_enabled else HudPalette.TEXT_MUTED,
        )

    # --- Navigation ---
    def switch_screen(self, key: str, animate: bool = True) -> None:
        idx = self._screen_indices.get(key)
        if idx is None:
            return

        for k, btn in self._nav_buttons.items():
            btn.setProperty("active", "true" if k == key else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        title_map = {k: lbl for k, lbl, _ in self.NAV_ITEMS}
        self.view_title_lbl.setText(title_map.get(key, key.upper()))
        self.stack.setCurrentIndex(idx)

        if key == "memory":
            self._refresh_memory()
        elif key == "notes":
            self._refresh_notes()
        elif key == "reminders":
            self._refresh_reminders()
        elif key == "system":
            self.system_screen.run_diagnostics()

        if animate:
            self._fade = QPropertyAnimation(self.stack_opacity, b"opacity", self)
            self._fade.setDuration(180)
            self._fade.setStartValue(0.35)
            self._fade.setEndValue(1.0)
            self._fade.setEasingCurve(QEasingCurve.OutCubic)
            self._fade.start()

    # --- Telemetry & Due Reminders ---
    def _update_telemetry(self) -> None:
        now = datetime.now()
        self.clock_lbl.setText(now.strftime("%H:%M:%S"))
        self.date_lbl.setText(now.strftime("%a %d %b %Y").upper())

        tel = get_system_telemetry()
        self.dashboard_screen.update_telemetry(
            tel["cpu_percent"],
            tel["ram_percent"],
            tel["battery_percent"],
            tel["battery_plugged"],
        )

        provider = self.assistant.ai.active_provider
        ai_lbl = f"{provider.name} ({self.config.ai_provider})" if provider else "Offline"
        self.system_screen.update_telemetry(tel, ai_lbl, self.config.voice_enabled)

        # Check due reminders every 15 seconds
        self._reminder_tick += 1
        if self._reminder_tick >= 15:
            self._reminder_tick = 0
            self._check_due_reminders()

    def _check_due_reminders(self) -> None:
        due = self.repo.get_due_unnotified_reminders()
        for rem in due:
            self.repo.mark_reminder_notified(rem.id)
            msg = f"Reminder: {rem.title}"
            self.toast.show_message(msg, duration_ms=5000)
            self.dashboard_screen.add_activity(msg)
            if self.config.voice_enabled:
                self.assistant.tts.speak(f"Excuse me, {self.config.user_name}. Reminder: {rem.title}", block=False)

    # --- Handlers ---
    def _handle_state_update(self, state_str: str) -> None:
        try:
            state = AssistantState(state_str)
        except ValueError:
            state = AssistantState.IDLE

        self.state_pill.setText(f"STATE: {state.value}")
        self.dashboard_screen.set_state(state)
        self.chat_screen.set_state(state)

        if state == AssistantState.ERROR:
            self.state_pill.setStyleSheet(
                f"font-family: 'Consolas', monospace; font-size: 10px; font-weight: 700; "
                f"color: {HudPalette.RED_ALERT}; background: rgba(255, 46, 99, 0.16); "
                f"border: 1px solid {HudPalette.RED_ALERT}; border-radius: 4px; padding: 4px 10px;"
            )
        elif state in (AssistantState.LISTENING, AssistantState.SPEAKING, AssistantState.ACTIVATING):
            self.state_pill.setStyleSheet(
                f"font-family: 'Consolas', monospace; font-size: 10px; font-weight: 700; "
                f"color: #00FFCC; background: rgba(0, 255, 204, 0.16); "
                f"border: 1px solid #00FFCC; border-radius: 4px; padding: 4px 10px;"
            )
        else:
            self.state_pill.setStyleSheet(
                f"font-family: 'Consolas', monospace; font-size: 10px; font-weight: 700; "
                f"color: {HudPalette.CYAN_ELECTRIC}; background: rgba(0, 229, 255, 0.12); "
                f"border: 1px solid {HudPalette.CYAN_DIM}; border-radius: 4px; padding: 4px 10px;"
            )

    def _handle_message(self, role: str, text: str) -> None:
        self.dashboard_screen.chat_panel.append_message(role, text)
        self.chat_screen.chat_panel.append_message(role, text)
        if role == "user":
            self.dashboard_screen.add_activity(f"CMD: {text[:40]}")
            self._refresh_notes()
            self._refresh_memory()

    def _handle_audio_level(self, level: float) -> None:
        self.dashboard_screen.reactor.set_audio_level(level)
        self.dashboard_screen.waveform.set_audio_level(level)
        self.chat_screen.reactor.set_audio_level(level)
        self.chat_screen.waveform.set_audio_level(level)

    def _handle_window_action(self, action: str) -> None:
        if action == "minimize":
            self.showMinimized()
        elif action == "maximize":
            self.showMaximized()
        elif action == "hide":
            self._hide_to_tray()
        elif action == "show":
            self._show_hud()

    def _run_command(self, text: str) -> None:
        worker = CommandWorker(self.assistant, text)
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def _clear_all_chats(self) -> None:
        self.assistant.ai.clear_memory()
        self.repo.clear_messages()
        self.dashboard_screen.chat_panel.clear_messages()
        self.chat_screen.chat_panel.clear_messages()
        self.toast.show_message("Conversation history cleared.")

    # --- Repository CRUD Handlers ---
    def _refresh_memory(self, query: str = "") -> None:
        facts = self.repo.list_facts(query)
        self.memory_screen.render_facts(facts)
        self.memory_screen.render_ram_context(self.assistant.ai.memory.get_context())

    def _on_add_fact(self, fact: str, category: str) -> None:
        self.repo.add_fact(fact, category)
        self._refresh_memory(self.memory_screen.search_input.text())
        self.toast.show_message("Fact committed to persistent memory.")

    def _on_delete_fact(self, fact_id: int) -> None:
        self.repo.delete_fact(fact_id)
        self._refresh_memory(self.memory_screen.search_input.text())

    def _on_clear_ram(self) -> None:
        self.assistant.ai.clear_memory()
        self._refresh_memory(self.memory_screen.search_input.text())
        self.toast.show_message("Active RAM context flushed.")

    def _refresh_notes(self, query: str = "") -> None:
        notes = self.repo.list_notes(query)
        self.notes_screen.render_notes(notes)

    def _on_save_note(self, note_id, title: str, content: str) -> None:
        if note_id is None:
            new_id = self.repo.create_note(title, content)
            self.notes_screen._current_note_id = new_id
            # Also mirror to persistent %LOCALAPPDATA%\JARVIS\notes
            try:
                from core.paths import get_notes_dir
                notes_dir = get_notes_dir()
                safe_title = "".join(c if c.isalnum() or c in "-_ " else "_" for c in title)[:35]
                (notes_dir / f"{safe_title}_{new_id}.txt").write_text(f"{title}\n\n{content}\n", encoding="utf-8")
            except Exception:
                pass
        else:
            self.repo.update_note(note_id, title, content)
        self._refresh_notes(self.notes_screen.search_input.text())
        self.toast.show_message(f"Note '{title}' saved.")

    def _on_delete_note(self, note_id: int) -> None:
        self.repo.delete_note(note_id)
        self._refresh_notes(self.notes_screen.search_input.text())
        self.toast.show_message("Note deleted.")

    def _refresh_reminders(self) -> None:
        rems = self.repo.list_reminders()
        self.reminders_screen.render_reminders(rems)
        pending = [r for r in rems if r.status == "pending"]
        if pending:
            self.dashboard_screen.next_reminder_lbl.setText(f"{pending[0].title} ({pending[0].due_at})")
        else:
            self.dashboard_screen.next_reminder_lbl.setText("No pending reminders")

    def _on_add_reminder(self, title: str, due_at: str) -> None:
        self.repo.add_reminder(title, due_at)
        self._refresh_reminders()
        self.toast.show_message(f"Scheduled reminder for {due_at}.")

    def _on_toggle_reminder(self, reminder_id: int, new_status: str) -> None:
        self.repo.set_reminder_status(reminder_id, new_status)
        self._refresh_reminders()

    def _on_delete_reminder(self, reminder_id: int) -> None:
        self.repo.delete_reminder(reminder_id)
        self._refresh_reminders()

    def _on_settings_saved(self) -> None:
        self.config.save_overrides(self.repo)
        self.assistant.apply_settings()
        self.setStyleSheet(build_stylesheet(self.config.accent_intensity))
        self.operator_lbl.setText(f"OPERATOR: {self.config.user_name.upper()}")
        self._refresh_ai_chips()
        self._apply_mic_status(self.assistant.has_microphone)
        self.dashboard_screen.add_activity("Configuration updated & saved.")
        self.toast.show_message("Settings saved & applied successfully.")

    # --- Window Chrome Dragging, Tray, Animations Lifecycle ---
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and event.position().y() <= 60:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton and not self.isMaximized():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = None

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.startup_overlay and self.startup_overlay.isVisible():
            self.startup_overlay.setGeometry(self.rect())

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized():
                self._pause_visuals()
            elif self.isVisible():
                self._resume_visuals()

    def _toggle_maximize(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _pause_visuals(self) -> None:
        self.dashboard_screen.reactor.pause_animations()
        self.dashboard_screen.waveform.pause_animations()
        self.chat_screen.reactor.pause_animations()
        self.chat_screen.waveform.pause_animations()

    def _resume_visuals(self) -> None:
        self.dashboard_screen.reactor.resume_animations()
        self.dashboard_screen.waveform.resume_animations()
        self.chat_screen.reactor.resume_animations()
        self.chat_screen.waveform.resume_animations()

    def _hide_to_tray(self) -> None:
        self._pause_visuals()
        self.hide()

    def _show_hud(self) -> None:
        self._resume_visuals()
        self.showNormal()
        self.activateWindow()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.config.minimize_to_tray and self.tray.isVisible():
            self._hide_to_tray()
            self.tray.showMessage(
                "J.A.R.V.I.S. Running in Background",
                "J.A.R.V.I.S. minimized to tray. Click the Arc Reactor icon to restore.",
                get_app_icon(),
                2200,
            )
            event.ignore()
        else:
            self._full_exit()
            event.accept()

    def _full_exit(self) -> None:
        self._pause_visuals()
        self._tel_timer.stop()
        if self.startup_overlay:
            self.startup_overlay.stop()
        self.system_screen.stop()
        self.assistant.stop()
        self.tray.hide()
        self.hide()
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
