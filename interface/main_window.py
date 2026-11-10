"""
Main Desktop HUD Window for J.A.R.V.I.S. PySide6 Application.

Assembles the Arc Reactor visualizer, waveform oscilloscope, system telemetry,
quick actions bar, and conversational chat panel into a unified Iron Man HUD.
"""

from datetime import datetime
import threading
from typing import Optional

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QFont, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.assistant import Assistant
from core.config import Config, get_config
from core.states import AssistantState
from interface.chat_panel import ChatPanel
from interface.reactor_widget import ArcReactorWidget
from interface.styles import HUD_STYLESHEET
from interface.system_tray import SystemTrayController, create_reactor_pixmap
from interface.waveform_widget import WaveformWidget


class StateBridge(QObject):
    """Qt Signal bridge enabling thread-safe state and message notifications."""
    state_changed = Signal(str)
    message_received = Signal(str, str)  # (role, text)


class CommandWorker(QThread):
    """Background worker for asynchronous text command execution."""
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
    Primary HUD Window for J.A.R.V.I.S.
    """

    def __init__(self, assistant: Optional[Assistant] = None):
        super().__init__()
        self.config: Config = get_config()
        self.bridge = StateBridge()

        # Connect Assistant callbacks to Qt Signals
        self.assistant = assistant or Assistant(
            config=self.config,
            on_state_change=self._on_assistant_state_change,
            on_message=self._on_assistant_message,
        )

        self.setWindowTitle("J.A.R.V.I.S. — STARK INDUSTRIES OS")
        self.setWindowIcon(QIcon(create_reactor_pixmap(64)))
        self.resize(1000, 680)
        self.setMinimumSize(850, 560)

        # Apply HUD Stylesheet
        self.setStyleSheet(HUD_STYLESHEET)

        # Setup System Tray
        self.tray = SystemTrayController(self)
        self.tray.show_requested.connect(self._show_hud)
        self.tray.hide_requested.connect(self.hide)
        self.tray.toggle_voice_requested.connect(self.assistant.trigger_activation)
        self.tray.sleep_requested.connect(lambda: self.assistant.process_text_command("go to sleep"))
        self.tray.exit_requested.connect(self._full_exit)
        self.tray.show()

        self._init_ui()
        self._init_telemetry_timer()

        # Wire Qt Signal bridge to GUI slots
        self.bridge.state_changed.connect(self._handle_state_update)
        self.bridge.message_received.connect(self.chat_panel.append_message)

        # Welcome message
        self.chat_panel.append_message(
            "assistant",
            f"All systems initialized, {self.config.user_name}. J.A.R.V.I.S. is online and standing by."
        )

    def _on_assistant_state_change(self, state: AssistantState) -> None:
        """Called from assistant thread; bridges safely to Qt main thread."""
        self.bridge.state_changed.emit(state.value)

    def _on_assistant_message(self, role: str, text: str) -> None:
        """Called from assistant thread; bridges safely to Qt main thread."""
        self.bridge.message_received.emit(role, text)

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(12)

        # 1. Top Header Bar
        header = QHBoxLayout()
        header.setSpacing(10)

        title_label = QLabel("J.A.R.V.I.S.  //  STARK INDUSTRIES HUD v3.0")
        title_label.setObjectName("hudTitle")
        header.addWidget(title_label)

        header.addStretch(1)

        # State Indicator Pill
        self.state_pill = QLabel("STATE: IDLE")
        self.state_pill.setObjectName("statusValue")
        self.state_pill.setStyleSheet(
            "background: rgba(0, 229, 255, 0.12); color: #00E5FF; "
            "padding: 4px 10px; border: 1px solid #007799; border-radius: 4px; font-weight: bold;"
        )
        header.addWidget(self.state_pill)

        # Clock
        self.clock_label = QLabel("--:--:--")
        self.clock_label.setObjectName("statusValue")
        header.addWidget(self.clock_label)

        main_layout.addLayout(header)

        # 2. Main Content Split: Left Visualizer, Right Telemetry & Chat
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        # LEFT PANEL: Arc Reactor & Audio Oscilloscope
        left_panel = QFrame()
        left_panel.setObjectName("hudPanel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(12)

        # Arc Reactor Central Display
        self.reactor = ArcReactorWidget()
        left_layout.addWidget(self.reactor, stretch=1)

        # Audio Oscilloscope Waveform
        self.waveform = WaveformWidget()
        left_layout.addWidget(self.waveform)

        # Quick Actions Strip
        actions_label = QLabel("QUICK DIRECTIVES")
        actions_label.setObjectName("sectionHeader")
        left_layout.addWidget(actions_label)

        actions_grid = QGridLayout()
        actions_grid.setSpacing(6)

        actions = [
            ("Notepad", "open notepad"),
            ("Calculator", "open calculator"),
            ("Browser", "open google"),
            ("Explorer", "open file explorer"),
            ("Status", "system status"),
            ("Sleep", "go to sleep"),
        ]

        for i, (label, cmd) in enumerate(actions):
            btn = QPushButton(label)
            btn.setObjectName("actionButton")
            btn.clicked.connect(lambda checked=False, c=cmd: self._on_quick_action(c))
            actions_grid.addWidget(btn, i // 3, i % 3)

        left_layout.addLayout(actions_grid)
        content_layout.addWidget(left_panel, stretch=5)

        # RIGHT PANEL: Telemetry & Conversation Stream
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)

        # Telemetry Card
        telemetry_card = QFrame()
        telemetry_card.setObjectName("statusCard")
        tel_layout = QGridLayout(telemetry_card)
        tel_layout.setContentsMargins(10, 8, 10, 8)
        tel_layout.setSpacing(8)

        # Telemetry metrics
        tel_layout.addWidget(QLabel("AI PROVIDER:"), 0, 0)
        self.provider_val = QLabel(self.assistant.ai.active_provider.name if self.assistant.ai.active_provider else "None")
        self.provider_val.setObjectName("statusValue")
        tel_layout.addWidget(self.provider_val, 0, 1)

        tel_layout.addWidget(QLabel("WAKE WORD:"), 0, 2)
        self.wakeword_val = QLabel(f"'{self.config.wake_word_model}' (Local ONNX)")
        self.wakeword_val.setObjectName("statusValue")
        tel_layout.addWidget(self.wakeword_val, 0, 3)

        tel_layout.addWidget(QLabel("CPU LOAD:"), 1, 0)
        self.cpu_val = QLabel("0%")
        self.cpu_val.setObjectName("statusValue")
        tel_layout.addWidget(self.cpu_val, 1, 1)

        tel_layout.addWidget(QLabel("RAM USAGE:"), 1, 2)
        self.ram_val = QLabel("0%")
        self.ram_val.setObjectName("statusValue")
        tel_layout.addWidget(self.ram_val, 1, 3)

        right_panel.addWidget(telemetry_card)

        # Chat Panel
        self.chat_panel = ChatPanel()
        self.chat_panel.command_submitted.connect(self._handle_user_text_command)
        self.chat_panel.mic_clicked.connect(self.assistant.trigger_activation)
        self.chat_panel.clear_clicked.connect(self.assistant.ai.clear_memory)
        right_panel.addWidget(self.chat_panel, stretch=1)

        content_layout.addLayout(right_panel, stretch=6)
        main_layout.addLayout(content_layout, stretch=1)

    def _init_telemetry_timer(self) -> None:
        """Periodic timer updating clock and CPU/RAM telemetry without lag."""
        self._tel_timer = QTimer(self)
        self._tel_timer.timeout.connect(self._update_telemetry)
        self._tel_timer.start(1000)
        self._update_telemetry()

    def _update_telemetry(self) -> None:
        # Clock
        now_str = datetime.now().strftime("%H:%M:%S")
        self.clock_label.setText(now_str)

        # CPU & RAM via psutil
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            self.cpu_val.setText(f"{cpu:.0f}%")
            self.ram_val.setText(f"{ram:.0f}%")
        except Exception:
            pass

    def _handle_state_update(self, state_str: str) -> None:
        """Update HUD UI state badge, Arc Reactor, and waveform."""
        try:
            state = AssistantState(state_str)
        except ValueError:
            state = AssistantState.IDLE

        self.state_pill.setText(f"STATE: {state.value}")
        self.reactor.set_state(state)
        self.waveform.set_state(state)

        # Adjust state pill styling based on state
        if state == AssistantState.ERROR:
            self.state_pill.setStyleSheet("background: rgba(255, 42, 109, 0.2); color: #FF2A6D; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
        elif state in (AssistantState.LISTENING, AssistantState.SPEAKING):
            self.state_pill.setStyleSheet("background: rgba(0, 229, 255, 0.25); color: #00E5FF; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
        elif state == AssistantState.PROCESSING:
            self.state_pill.setStyleSheet("background: rgba(0, 100, 255, 0.25); color: #40C4FF; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
        else:
            self.state_pill.setStyleSheet("background: rgba(0, 229, 255, 0.12); color: #00B4D8; padding: 4px 10px; border-radius: 4px; font-weight: bold;")

    def _handle_user_text_command(self, text: str) -> None:
        """Run text command in background thread so GUI never stutters."""
        worker = CommandWorker(self.assistant, text)
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def _on_quick_action(self, cmd: str) -> None:
        """Trigger a quick action directive."""
        self._handle_user_text_command(cmd)

    def _show_hud(self) -> None:
        self.showNormal()
        self.activateWindow()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Minimize to system tray on close instead of exiting completely."""
        if self.tray.isVisible():
            self.hide()
            self.tray.showMessage(
                "J.A.R.V.I.S. Running in Background",
                "J.A.R.V.I.S. is still monitoring for wake words. Click the tray icon to restore.",
                create_reactor_pixmap(32),
                2500
            )
            event.ignore()
        else:
            self._full_exit()
            event.accept()

    def _full_exit(self) -> None:
        """Cleanly terminate all background worker threads and quit."""
        self.assistant.stop()
        self.tray.hide()
        self.close()
