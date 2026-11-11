"""
Refined Holographic Conversation Panel for J.A.R.V.I.S. PySide6 HUD.

Uses custom-styled MessageBubble cards with subtle entrance animations,
selectable message text, an animated neural processing indicator, and
vector icon input controls.
"""

from datetime import datetime
from typing import List, Optional
from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from interface.components import HudFrame, create_vector_icon
from interface.theme import HudPalette


class MessageBubble(QFrame):
    """Individual animated conversation bubble for User or J.A.R.V.I.S."""

    def __init__(self, role: str, text: str, timestamp: Optional[str] = None, animate: bool = True, parent=None):
        super().__init__(parent)
        self.role = role.lower()
        self.text_content = text
        ts = timestamp or datetime.now().strftime("%H:%M:%S")

        is_user = (self.role == "user")
        accent = HudPalette.CYAN_ELECTRIC if is_user else "#52E5FF"
        bg = "rgba(0, 229, 255, 0.08)" if is_user else "rgba(16, 25, 43, 0.90)"
        border_side = "border-right: 3px solid" if is_user else "border-left: 3px solid"
        role_title = "MRAGANK // COMMAND" if is_user else "J.A.R.V.I.S. // RESPONSE"

        self.setStyleSheet(
            f"MessageBubble {{ background-color: {bg}; border: 1px solid {HudPalette.BORDER_SUBTLE}; "
            f"{border_side} {accent}; border-radius: 6px; }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 9)
        layout.setSpacing(4)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        role_lbl = QLabel(role_title)
        role_lbl.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 9px; font-weight: 700; "
            f"color: {accent}; letter-spacing: 1px;"
        )
        ts_lbl = QLabel(ts)
        ts_lbl.setStyleSheet(f"font-family: 'Consolas', monospace; font-size: 9px; color: {HudPalette.TEXT_MUTED};")

        if is_user:
            meta_row.addWidget(ts_lbl)
            meta_row.addStretch(1)
            meta_row.addWidget(role_lbl)
        else:
            meta_row.addWidget(role_lbl)
            meta_row.addStretch(1)
            meta_row.addWidget(ts_lbl)

        body = QLabel(text)
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        body.setStyleSheet(f"font-size: 12px; color: {HudPalette.TEXT_PRIMARY}; line-height: 1.4;")

        layout.addLayout(meta_row)
        layout.addWidget(body)

        if animate:
            eff = QGraphicsOpacityEffect(self)
            eff.setOpacity(0.0)
            self.setGraphicsEffect(eff)
            self._anim = QPropertyAnimation(eff, b"opacity", self)
            self._anim.setDuration(220)
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
            self._anim.setEasingCurve(QEasingCurve.OutCubic)
            self._anim.start()


class ProcessingIndicator(QWidget):
    """Subtle animated processing indicator shown while AI or skill runs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        self._dots = 0
        self.label = QLabel("J.A.R.V.I.S. IS PROCESSING")
        self.label.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 10px; font-weight: 700; "
            f"color: {HudPalette.CYAN_ELECTRIC}; letter-spacing: 1.2px;"
        )
        layout.addWidget(self.label)
        layout.addStretch(1)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.hide()

    def start(self) -> None:
        self._dots = 0
        self.show()
        if not self._timer.isActive():
            self._timer.start(280)

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def _tick(self) -> None:
        self._dots = (self._dots + 1) % 4
        self.label.setText(f"J.A.R.V.I.S. IS PROCESSING{'.' * self._dots}")


class ChatPanel(HudFrame):
    """
    Holographic conversation feed, processing indicator, and dual voice/text bar.
    """

    command_submitted = Signal(str)
    mic_clicked = Signal()
    clear_clicked = Signal()

    def __init__(self, compact: bool = False, parent=None):
        super().__init__(parent, show_grid=False)
        self.compact = compact
        self._messages: List[str] = []
        self._mic_available = False
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Header Strip
        header = QHBoxLayout()
        title = QLabel("CONVERSATION STREAM" if self.compact else "NEURAL DIALOGUE WORKSPACE")
        title.setObjectName("sectionHeader")
        header.addWidget(title)
        header.addStretch(1)

        self.clear_btn = QPushButton(" CLEAR")
        self.clear_btn.setIcon(create_vector_icon("clear", HudPalette.TEXT_SECONDARY, 13))
        self.clear_btn.setIconSize(QSize(13, 13))
        self.clear_btn.setFixedHeight(26)
        self.clear_btn.setStyleSheet(
            f"QPushButton {{ padding: 2px 10px; font-size: 10px; color: {HudPalette.TEXT_SECONDARY}; "
            f"border: 1px solid {HudPalette.BORDER_SUBTLE}; background: transparent; }}"
            f"QPushButton:hover {{ color: {HudPalette.RED_ALERT}; border-color: {HudPalette.RED_ALERT}; }}"
        )
        self.clear_btn.clicked.connect(self._on_clear)
        header.addWidget(self.clear_btn)
        layout.addLayout(header)

        # Scrollable Bubble Stream
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._msg_layout = QVBoxLayout(self._container)
        self._msg_layout.setContentsMargins(2, 2, 4, 2)
        self._msg_layout.setSpacing(8)
        self._msg_layout.addStretch(1)

        self.scroll_area.setWidget(self._container)
        layout.addWidget(self.scroll_area, stretch=1)

        # Typing / Processing Indicator
        self.processing_indicator = ProcessingIndicator()
        layout.addWidget(self.processing_indicator)

        # Futuristic Input Row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.mic_btn = QPushButton()
        self.mic_btn.setIcon(create_vector_icon("mic", HudPalette.CYAN_ELECTRIC, 16))
        self.mic_btn.setIconSize(QSize(16, 16))
        self.mic_btn.setFixedSize(38, 36)
        self.mic_btn.setToolTip("Activate Voice Listening")
        self.mic_btn.clicked.connect(self.mic_clicked.emit)
        input_row.addWidget(self.mic_btn)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Issue directive or ask J.A.R.V.I.S. anything...")
        self.input_field.setFixedHeight(36)
        self.input_field.returnPressed.connect(self._on_send)
        input_row.addWidget(self.input_field, stretch=1)

        self.send_btn = QPushButton(" SEND")
        self.send_btn.setObjectName("primaryButton")
        self.send_btn.setIcon(create_vector_icon("send", HudPalette.CYAN_ELECTRIC, 14))
        self.send_btn.setIconSize(QSize(14, 14))
        self.send_btn.setFixedHeight(36)
        self.send_btn.clicked.connect(self._on_send)
        input_row.addWidget(self.send_btn)

        layout.addLayout(input_row)

    def set_mic_available(self, available: bool) -> None:
        self._mic_available = available
        if available:
            self.mic_btn.setIcon(create_vector_icon("mic", HudPalette.CYAN_ELECTRIC, 16))
            self.mic_btn.setToolTip("Activate Voice Listening")
        else:
            self.mic_btn.setIcon(create_vector_icon("mic", HudPalette.TEXT_MUTED, 16))
            self.mic_btn.setToolTip("Microphone Unavailable — Text Input Active")

    def set_processing(self, active: bool) -> None:
        if active:
            self.processing_indicator.start()
        else:
            self.processing_indicator.stop()

    def _on_send(self) -> None:
        text = self.input_field.text().strip()
        if text:
            self.input_field.clear()
            self.command_submitted.emit(text)

    def _on_clear(self) -> None:
        self.clear_messages()
        self.clear_clicked.emit()

    def clear_messages(self) -> None:
        self._messages.clear()
        while self._msg_layout.count() > 1:
            item = self._msg_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def append_message(self, role: str, text: str, timestamp: Optional[str] = None, animate: bool = True) -> None:
        self._messages.append(text)
        bubble = MessageBubble(role, text, timestamp=timestamp, animate=animate)

        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)
        if role.lower() == "user":
            wrapper.addStretch(1)
            wrapper.addWidget(bubble, stretch=5)
        else:
            wrapper.addWidget(bubble, stretch=5)
            wrapper.addStretch(1)

        row_widget = QWidget()
        row_widget.setStyleSheet("background: transparent;")
        row_widget.setLayout(wrapper)

        # Insert before trailing stretch
        self._msg_layout.insertWidget(self._msg_layout.count() - 1, row_widget)
        QTimer.singleShot(30, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())

    def all_text(self) -> str:
        """Helper returning concatenated displayed messages for verification/testing."""
        return "\n".join(self._messages)
