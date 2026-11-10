"""
Futuristic Cybernetic Chat Panel for J.A.R.V.I.S. PySide6 HUD.

Displays multi-turn conversational dialogue with distinct role styling,
command input bar, voice activation trigger, and clear history control.
"""

from datetime import datetime
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ChatPanel(QFrame):
    """
    HUD conversational messaging stream and command entry widget.
    """

    command_submitted = Signal(str)
    mic_clicked = Signal()
    clear_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("hudPanel")
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Message History Display
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("chatLog")
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display, stretch=1)

        # Input and Control Bar
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        # Voice Trigger Button
        self.mic_btn = QPushButton("MIC")
        self.mic_btn.setObjectName("micButton")
        self.mic_btn.setToolTip("Activate Voice Listening")
        self.mic_btn.setFixedSize(50, 36)
        self.mic_btn.clicked.connect(self.mic_clicked.emit)
        input_layout.addWidget(self.mic_btn)

        # Command Text Field
        self.input_field = QLineEdit()
        self.input_field.setObjectName("commandInput")
        self.input_field.setPlaceholderText("Enter command or query (e.g. 'open notepad', 'news')...")
        self.input_field.returnPressed.connect(self._on_send)
        input_layout.addWidget(self.input_field, stretch=1)

        # Send Button
        self.send_btn = QPushButton("SEND")
        self.send_btn.setFixedSize(65, 36)
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)

        # Clear Button
        self.clear_btn = QPushButton("CLEAR")
        self.clear_btn.setFixedSize(65, 36)
        self.clear_btn.clicked.connect(self._on_clear)
        input_layout.addWidget(self.clear_btn)

        layout.addLayout(input_layout)

    def _on_send(self) -> None:
        text = self.input_field.text().strip()
        if text:
            self.input_field.clear()
            self.command_submitted.emit(text)

    def _on_clear(self) -> None:
        self.chat_display.clear()
        self.clear_clicked.emit()

    def append_message(self, role: str, text: str) -> None:
        """
        Append a styled message bubble into the conversation stream.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        if role.lower() == "user":
            header_color = "#00E5FF"
            role_label = "USER"
            align = "left"
            bg = "rgba(0, 229, 255, 0.06)"
        else:
            header_color = "#64FFDA"
            role_label = "JARVIS"
            align = "left"
            bg = "rgba(100, 255, 218, 0.04)"

        formatted_html = f"""
        <div style="margin-bottom: 8px; padding: 8px 12px; background: {bg}; border-left: 2px solid {header_color}; border-radius: 4px;">
            <div style="font-size: 10px; font-weight: bold; color: {header_color}; margin-bottom: 4px;">
                [{timestamp}] {role_label}
            </div>
            <div style="font-size: 12px; color: #ECEFF1; line-height: 1.4;">
                {text}
            </div>
        </div>
        """
        self.chat_display.append(formatted_html)
        # Scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
