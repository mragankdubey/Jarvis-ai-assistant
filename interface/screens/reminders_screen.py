"""
Reminders & Tasks Management Screen for J.A.R.V.I.S. PySide6 HUD.

Allows scheduling timestamped reminders, toggling completion status,
filtering active vs completed items, and storing reminders in SQLite.
"""

from typing import List
from PySide6.QtCore import QDateTime, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QDateTimeEdit,
    QFrame,
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


class RemindersScreen(QWidget):
    """HUD reminders and task management screen."""

    reminder_added = Signal(str, str)       # (title, due_at)
    reminder_toggled = Signal(int, str)     # (id, new_status)
    reminder_deleted = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter = "all"
        self._cached_items: List[object] = []
        self._init_ui()

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # Create Reminder Card
        add_frame = HudFrame()
        add_layout = QVBoxLayout(add_frame)
        add_layout.setContentsMargins(16, 12, 16, 12)
        add_layout.setSpacing(10)

        hdr = QLabel("SCHEDULE NEW REMINDER / TASK")
        hdr.setObjectName("sectionHeader")
        add_layout.addWidget(hdr)

        row = QHBoxLayout()
        row.setSpacing(8)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Reminder description (e.g., 'Review AI pull request')...")
        self.title_input.returnPressed.connect(self._on_add)
        row.addWidget(self.title_input, stretch=1)

        self.dt_edit = QDateTimeEdit()
        self.dt_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.dt_edit.setCalendarPopup(True)
        self.dt_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.dt_edit.setFixedWidth(165)
        row.addWidget(self.dt_edit)

        add_btn = QPushButton(" SCHEDULE")
        add_btn.setObjectName("primaryButton")
        add_btn.setIcon(create_vector_icon("plus", HudPalette.CYAN_ELECTRIC, 14))
        add_btn.setIconSize(QSize(14, 14))
        add_btn.clicked.connect(self._on_add)
        row.addWidget(add_btn)
        add_layout.addLayout(row)

        root.addWidget(add_frame)

        # Reminder List Card
        list_frame = HudFrame()
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(16, 12, 16, 12)
        list_layout.setSpacing(10)

        filter_row = QHBoxLayout()
        lbl = QLabel("ACTIVE & UPCOMING DIRECTIVES")
        lbl.setObjectName("sectionHeader")
        filter_row.addWidget(lbl)
        filter_row.addStretch(1)

        for key in ("all", "pending", "completed"):
            btn = QPushButton(key.upper())
            btn.setFixedHeight(26)
            btn.clicked.connect(lambda _=False, k=key: self._set_filter(k))
            filter_row.addWidget(btn)
        list_layout.addLayout(filter_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._cards_layout = QVBoxLayout(self._container)
        self._cards_layout.setContentsMargins(0, 0, 4, 0)
        self._cards_layout.setSpacing(8)
        self._cards_layout.addStretch(1)
        self.scroll.setWidget(self._container)
        list_layout.addWidget(self.scroll, stretch=1)

        root.addWidget(list_frame, stretch=1)

    def _on_add(self) -> None:
        title = self.title_input.text().strip()
        if not title:
            return
        due_str = self.dt_edit.dateTime().toString("yyyy-MM-dd HH:mm")
        self.title_input.clear()
        self.reminder_added.emit(title, due_str)

    def _set_filter(self, key: str) -> None:
        self._filter = key
        self.render_reminders(self._cached_items)

    def render_reminders(self, reminders: List[object]) -> None:
        self._cached_items = reminders
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filtered = [
            r for r in reminders
            if self._filter == "all" or r.status == self._filter
        ]

        if not filtered:
            empty = QLabel("No reminders matching current filter.")
            empty.setStyleSheet(f"color: {HudPalette.TEXT_MUTED}; font-size: 11px; padding: 12px;")
            self._cards_layout.insertWidget(0, empty)
            return

        for rem in filtered:
            done = (rem.status == "completed")
            card = QFrame()
            card.setObjectName("listCard")
            border_c = HudPalette.BORDER_SUBTLE if done else HudPalette.CYAN_DIM
            card.setStyleSheet(
                f"QFrame#listCard {{ background: {HudPalette.BG_CARD}; border: 1px solid {border_c}; border-radius: 5px; }}"
            )
            row = QHBoxLayout(card)
            row.setContentsMargins(12, 9, 12, 9)
            row.setSpacing(10)

            next_status = "pending" if done else "completed"
            check_btn = QPushButton()
            check_btn.setFixedSize(28, 28)
            check_btn.setIcon(create_vector_icon("check", HudPalette.GREEN_OK if done else HudPalette.TEXT_MUTED, 14))
            check_btn.setIconSize(QSize(14, 14))
            check_btn.clicked.connect(lambda _=False, rid=rem.id, ns=next_status: self.reminder_toggled.emit(rid, ns))

            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            title_lbl = QLabel(rem.title)
            title_style = (
                f"font-size: 12px; color: {HudPalette.TEXT_MUTED}; text-decoration: line-through;"
                if done else f"font-size: 12px; font-weight: 600; color: {HudPalette.TEXT_PRIMARY};"
            )
            title_lbl.setStyleSheet(title_style)
            due_lbl = QLabel(f"DUE: {rem.due_at}  ·  STATUS: {rem.status.upper()}")
            due_lbl.setStyleSheet(f"font-family: 'Consolas', monospace; font-size: 10px; color: {HudPalette.CYAN_MID};")
            text_col.addWidget(title_lbl)
            text_col.addWidget(due_lbl)

            del_btn = QPushButton()
            del_btn.setFixedSize(28, 28)
            del_btn.setObjectName("dangerButton")
            del_btn.setIcon(create_vector_icon("trash", HudPalette.RED_ALERT, 14))
            del_btn.setIconSize(QSize(14, 14))
            del_btn.clicked.connect(lambda _=False, rid=rem.id: self.reminder_deleted.emit(rid))

            row.addWidget(check_btn)
            row.addLayout(text_col, stretch=1)
            row.addWidget(del_btn)
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)
