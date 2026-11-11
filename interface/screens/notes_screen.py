"""
Notes Management Screen for J.A.R.V.I.S. PySide6 HUD.

Two-pane cybernetic workspace for creating, searching, editing,
and deleting notes stored in SQLite and synced with ~/JARVIS_Notes.
"""

from typing import List, Optional
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from interface.components import HudFrame, create_vector_icon
from interface.theme import HudPalette


class NotesScreen(QWidget):
    """Two-pane HUD notes workspace."""

    note_saved = Signal(object, str, str)  # (note_id_or_None, title, content)
    note_deleted = Signal(int)
    search_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_note_id: Optional[int] = None
        self._init_ui()

    def _init_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # Left Note Index Pane
        left_frame = HudFrame()
        left_frame.setFixedWidth(290)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(14, 12, 14, 12)
        left_layout.setSpacing(10)

        hdr_row = QHBoxLayout()
        hdr = QLabel("SAVED NOTES")
        hdr.setObjectName("sectionHeader")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch(1)

        new_btn = QPushButton(" NEW")
        new_btn.setObjectName("primaryButton")
        new_btn.setIcon(create_vector_icon("plus", HudPalette.CYAN_ELECTRIC, 13))
        new_btn.setIconSize(QSize(13, 13))
        new_btn.setFixedHeight(28)
        new_btn.clicked.connect(self._new_note)
        hdr_row.addWidget(new_btn)
        left_layout.addLayout(hdr_row)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search notes...")
        self.search_input.textChanged.connect(self.search_changed.emit)
        left_layout.addWidget(self.search_input)

        self.list_scroll = QScrollArea()
        self.list_scroll.setWidgetResizable(True)
        self.list_scroll.setFrameShape(QFrame.NoFrame)
        self._list_container = QWidget()
        self._list_container.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 4, 0)
        self._list_layout.setSpacing(6)
        self._list_layout.addStretch(1)
        self.list_scroll.setWidget(self._list_container)
        left_layout.addWidget(self.list_scroll, stretch=1)

        root.addWidget(left_frame)

        # Right Editor Pane
        editor_frame = HudFrame()
        editor_layout = QVBoxLayout(editor_frame)
        editor_layout.setContentsMargins(16, 14, 16, 14)
        editor_layout.setSpacing(10)

        ed_hdr = QHBoxLayout()
        ed_title = QLabel("NOTE EDITOR")
        ed_title.setObjectName("sectionHeader")
        ed_hdr.addWidget(ed_title)
        ed_hdr.addStretch(1)

        self.delete_btn = QPushButton(" DELETE")
        self.delete_btn.setObjectName("dangerButton")
        self.delete_btn.setIcon(create_vector_icon("trash", HudPalette.RED_ALERT, 13))
        self.delete_btn.setIconSize(QSize(13, 13))
        self.delete_btn.setFixedHeight(30)
        self.delete_btn.clicked.connect(self._on_delete)
        ed_hdr.addWidget(self.delete_btn)

        save_btn = QPushButton(" SAVE NOTE")
        save_btn.setObjectName("primaryButton")
        save_btn.setIcon(create_vector_icon("check", HudPalette.CYAN_ELECTRIC, 13))
        save_btn.setIconSize(QSize(13, 13))
        save_btn.setFixedHeight(30)
        save_btn.clicked.connect(self._on_save)
        ed_hdr.addWidget(save_btn)
        editor_layout.addLayout(ed_hdr)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Note title...")
        self.title_input.setStyleSheet("font-size: 14px; font-weight: 700; padding: 8px 12px;")
        editor_layout.addWidget(self.title_input)

        self.content_edit = QPlainTextEdit()
        self.content_edit.setPlaceholderText("Write note details here or say 'Take a note...'")
        editor_layout.addWidget(self.content_edit, stretch=1)

        root.addWidget(editor_frame, stretch=1)

    def _new_note(self) -> None:
        self._current_note_id = None
        self.title_input.clear()
        self.content_edit.clear()
        self.title_input.setFocus()

    def _on_save(self) -> None:
        title = self.title_input.text().strip() or "Untitled Note"
        content = self.content_edit.toPlainText().strip()
        if not content:
            return
        self.note_saved.emit(self._current_note_id, title, content)

    def _on_delete(self) -> None:
        if self._current_note_id is not None:
            nid = self._current_note_id
            self._new_note()
            self.note_deleted.emit(nid)

    def _load_note(self, note) -> None:
        self._current_note_id = note.id
        self.title_input.setText(note.title)
        self.content_edit.setPlainText(note.content)

    def render_notes(self, notes: List[object]) -> None:
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not notes:
            empty = QLabel("No notes recorded yet.")
            empty.setStyleSheet(f"color: {HudPalette.TEXT_MUTED}; font-size: 11px; padding: 10px;")
            self._list_layout.insertWidget(0, empty)
            return

        for n in notes:
            btn = QPushButton()
            title_short = (n.title[:26] + "...") if len(n.title) > 29 else n.title
            flat = n.content.replace("\n", " ")
            preview = (flat[:31] + "...") if len(flat) > 34 else flat
            btn.setText(f"{title_short}\n{preview}")
            btn.setStyleSheet(
                f"QPushButton {{ text-align: left; padding: 8px 10px; font-size: 11px; "
                f"background: {HudPalette.BG_CARD}; border: 1px solid {HudPalette.BORDER_SUBTLE}; }}"
                f"QPushButton:hover {{ border-color: {HudPalette.CYAN_ELECTRIC}; }}"
            )
            btn.clicked.connect(lambda _=False, note=n: self._load_note(note))
            self._list_layout.insertWidget(self._list_layout.count() - 1, btn)
