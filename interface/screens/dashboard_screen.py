"""
Main Command Centre (Dashboard) Screen for J.A.R.V.I.S. PySide6 HUD.

Balanced 3-column tactical command dashboard combining the 6-layer Arc Reactor,
holographic audio visualizer, subsystem readiness, quick actions, live telemetry
rings, recent activity log, and embedded conversation stream.
"""

from datetime import datetime
from typing import List
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from core.states import AssistantState
from interface.chat_panel import ChatPanel
from interface.components import HudFrame, StatusChip, TelemetryRing
from interface.reactor_widget import ArcReactorWidget
from interface.theme import HudPalette
from interface.waveform_widget import WaveformWidget


class DashboardScreen(QWidget):
    """Primary Command Centre HUD screen."""

    quick_command = Signal(str)
    mic_triggered = Signal()
    open_reminders_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recent_logs: List[str] = []
        self._init_ui()

    def _init_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # === LEFT COLUMN: Subsystems + Quick Directives + Recent Activity ===
        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        # 1. Subsystem Readiness
        sub_frame = HudFrame()
        sub_layout = QVBoxLayout(sub_frame)
        sub_layout.setContentsMargins(14, 12, 14, 12)
        sub_layout.setSpacing(8)

        sub_hdr = QLabel("SUBSYSTEM DIAGNOSTICS")
        sub_hdr.setObjectName("sectionHeader")
        sub_layout.addWidget(sub_hdr)

        self.chip_ai = StatusChip("AI BRAIN: CHECKING", True)
        self.chip_mic = StatusChip("MIC: PROBING", False)
        self.chip_wake = StatusChip("WAKE WORD: LOCAL ONNX", True)
        self.chip_tts = StatusChip("VOICE TTS: ACTIVE", True)

        for chip in (self.chip_ai, self.chip_mic, self.chip_wake, self.chip_tts):
            sub_layout.addWidget(chip)
        left_col.addWidget(sub_frame)

        # 2. Quick Directives Matrix
        actions_frame = HudFrame()
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(14, 12, 14, 12)
        actions_layout.setSpacing(10)

        act_hdr = QLabel("QUICK DIRECTIVES")
        act_hdr.setObjectName("sectionHeader")
        actions_layout.addWidget(act_hdr)

        grid = QGridLayout()
        grid.setSpacing(6)
        directives = [
            ("NOTEPAD", "open notepad"),
            ("CALC", "open calculator"),
            ("BROWSER", "open google"),
            ("EXPLORER", "open file explorer"),
            ("NEWS", "news"),
            ("SLEEP", "go to sleep"),
        ]
        for idx, (label, cmd) in enumerate(directives):
            btn = QPushButton(label)
            btn.setMinimumHeight(31)
            btn.setStyleSheet("padding: 5px 6px; font-size: 10px;")
            if label == "SLEEP":
                btn.setObjectName("dangerButton")
            btn.clicked.connect(lambda _=False, c=cmd: self.quick_command.emit(c))
            grid.addWidget(btn, idx // 2, idx % 2)
        actions_layout.addLayout(grid)
        left_col.addWidget(actions_frame)

        # 3. Recent Activity Log
        act_log_frame = HudFrame()
        act_log_layout = QVBoxLayout(act_log_frame)
        act_log_layout.setContentsMargins(14, 12, 14, 12)
        act_log_layout.setSpacing(6)

        log_hdr = QLabel("RECENT ACTIVITY")
        log_hdr.setObjectName("sectionHeader")
        act_log_layout.addWidget(log_hdr)

        self.activity_label = QLabel("System initialized. Awaiting directives.")
        self.activity_label.setWordWrap(True)
        self.activity_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.activity_label.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 10px; color: {HudPalette.TEXT_SECONDARY}; line-height: 1.45;"
        )
        act_log_layout.addWidget(self.activity_label, stretch=1)
        left_col.addWidget(act_log_frame, stretch=1)

        root.addLayout(left_col, stretch=3)

        # === CENTER COLUMN: Focal Arc Reactor & Audio Oscilloscope ===
        center_frame = HudFrame(show_grid=True)
        center_layout = QVBoxLayout(center_frame)
        center_layout.setContentsMargins(18, 14, 18, 16)
        center_layout.setSpacing(10)

        # Core Header Row
        core_hdr = QHBoxLayout()
        core_title = QLabel("PRIMARY CORE")
        core_title.setObjectName("sectionHeader")
        core_hdr.addWidget(core_title)
        core_hdr.addStretch(1)

        self.core_state_lbl = QLabel("STATE: IDLE")
        self.core_state_lbl.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 11px; font-weight: 700; color: {HudPalette.CYAN_ELECTRIC};"
        )
        core_hdr.addWidget(self.core_state_lbl)
        center_layout.addLayout(core_hdr)

        # Reimagined 6-Layer Reactor
        self.reactor = ArcReactorWidget()
        center_layout.addWidget(self.reactor, stretch=1)

        # Multi-Ribbon Holographic Waveform
        self.waveform = WaveformWidget()
        center_layout.addWidget(self.waveform)

        # Voice Activation Bar
        voice_bar = QHBoxLayout()
        voice_bar.setSpacing(8)
        self.activate_btn = QPushButton("VOICE LINK")
        self.activate_btn.setObjectName("primaryButton")
        self.activate_btn.setMinimumHeight(34)
        self.activate_btn.clicked.connect(self.mic_triggered.emit)
        voice_bar.addWidget(self.activate_btn, stretch=1)

        self.sleep_btn = QPushButton("STANDBY")
        self.sleep_btn.setMinimumHeight(34)
        self.sleep_btn.clicked.connect(lambda: self.quick_command.emit("go to sleep"))
        voice_bar.addWidget(self.sleep_btn)
        center_layout.addLayout(voice_bar)

        root.addWidget(center_frame, stretch=5)

        # === RIGHT COLUMN: Telemetry Rings + Upcoming Reminder + Stream ===
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        # 1. Live Telemetry Gauges
        tel_frame = HudFrame()
        tel_layout = QVBoxLayout(tel_frame)
        tel_layout.setContentsMargins(12, 10, 12, 10)
        tel_layout.setSpacing(6)

        tel_hdr = QLabel("SYSTEM TELEMETRY")
        tel_hdr.setObjectName("sectionHeader")
        tel_layout.addWidget(tel_hdr)

        gauges_row = QHBoxLayout()
        gauges_row.setSpacing(4)
        self.gauge_cpu = TelemetryRing("CPU")
        self.gauge_ram = TelemetryRing("RAM", accent=HudPalette.CYAN_ICE)
        self.gauge_bat = TelemetryRing("PWR", accent=HudPalette.GREEN_OK, warn_high=False)
        gauges_row.addWidget(self.gauge_cpu)
        gauges_row.addWidget(self.gauge_ram)
        gauges_row.addWidget(self.gauge_bat)
        tel_layout.addLayout(gauges_row)
        right_col.addWidget(tel_frame)

        # 2. Next Reminder Card
        rem_frame = HudFrame()
        rem_layout = QHBoxLayout(rem_frame)
        rem_layout.setContentsMargins(14, 10, 14, 10)
        rem_layout.setSpacing(8)

        rem_text_col = QVBoxLayout()
        rem_text_col.setSpacing(2)
        rem_hdr = QLabel("NEXT REMINDER")
        rem_hdr.setObjectName("sectionHeader")
        self.next_reminder_lbl = QLabel("No pending reminders")
        self.next_reminder_lbl.setWordWrap(True)
        self.next_reminder_lbl.setStyleSheet(f"font-size: 11px; color: {HudPalette.TEXT_PRIMARY};")
        rem_text_col.addWidget(rem_hdr)
        rem_text_col.addWidget(self.next_reminder_lbl)

        rem_btn = QPushButton("OPEN")
        rem_btn.setFixedHeight(28)
        rem_btn.clicked.connect(self.open_reminders_requested.emit)

        rem_layout.addLayout(rem_text_col, stretch=1)
        rem_layout.addWidget(rem_btn)
        right_col.addWidget(rem_frame)

        # 3. Embedded Compact Chat Panel
        self.chat_panel = ChatPanel(compact=True)
        right_col.addWidget(self.chat_panel, stretch=1)

        root.addLayout(right_col, stretch=4)

    def add_activity(self, entry: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._recent_logs.append(f"[{ts}] {entry}")
        self._recent_logs = self._recent_logs[-6:]
        self.activity_label.setText("\n".join(self._recent_logs))

    def set_state(self, state: AssistantState) -> None:
        self.reactor.set_state(state)
        self.waveform.set_state(state)
        self.core_state_lbl.setText(f"STATE: {state.value}")
        self.chat_panel.set_processing(state == AssistantState.PROCESSING)

    def update_telemetry(self, cpu: float, ram: float, bat_pct, bat_plugged) -> None:
        self.gauge_cpu.set_value(cpu)
        self.gauge_ram.set_value(ram)
        if bat_pct is not None:
            sub = "AC" if bat_plugged else "BAT"
            self.gauge_bat.set_value(float(bat_pct), sub)
        else:
            self.gauge_bat.set_value(100.0, "AC")
