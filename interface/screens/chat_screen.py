"""
Dedicated AI Conversation Screen for J.A.R.V.I.S. PySide6 HUD.

Provides an uncluttered, full-height holographic workspace for extended
multi-turn dialogues, quick starter prompts, and compact reactor presence.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from core.states import AssistantState
from interface.chat_panel import ChatPanel
from interface.components import HudFrame
from interface.reactor_widget import ArcReactorWidget
from interface.theme import HudPalette
from interface.waveform_widget import WaveformWidget


class ConversationScreen(QWidget):
    """Full-height AI conversation screen."""

    prompt_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # Left Compact Reactor & Context Strip
        left_frame = HudFrame(show_grid=True)
        left_frame.setFixedWidth(250)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(10)

        hdr = QLabel("NEURAL DIALOGUE")
        hdr.setObjectName("sectionHeader")
        left_layout.addWidget(hdr)

        self.reactor = ArcReactorWidget(compact=True)
        self.reactor.setFixedSize(180, 180)
        left_layout.addWidget(self.reactor, alignment=Qt.AlignCenter)

        self.waveform = WaveformWidget()
        left_layout.addWidget(self.waveform)

        self.provider_lbl = QLabel("PROVIDER: AUTO")
        self.provider_lbl.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 10px; font-weight: 700; color: {HudPalette.CYAN_ICE};"
        )
        left_layout.addWidget(self.provider_lbl)

        prompts_hdr = QLabel("SUGGESTED PROMPTS")
        prompts_hdr.setObjectName("sectionHeader")
        left_layout.addWidget(prompts_hdr)

        prompts = [
            "Brief me on top headlines",
            "Check full system status",
            "Explain async/await in Python",
            "Remember I prefer dark mode",
        ]
        for p in prompts:
            btn = QPushButton(p)
            btn.setStyleSheet("text-align: left; padding: 7px 10px; font-size: 10px;")
            btn.clicked.connect(lambda _=False, text=p: self.prompt_clicked.emit(text))
            left_layout.addWidget(btn)

        left_layout.addStretch(1)
        root.addWidget(left_frame)

        # Right Full-Height Chat Workspace
        self.chat_panel = ChatPanel(compact=False)
        root.addWidget(self.chat_panel, stretch=1)

    def set_state(self, state: AssistantState) -> None:
        self.reactor.set_state(state)
        self.waveform.set_state(state)
        self.chat_panel.set_processing(state == AssistantState.PROCESSING)
