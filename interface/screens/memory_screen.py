"""
Memory Management Screen for J.A.R.V.I.S. PySide6 HUD.

Allows the user to inspect, search, add, and delete persistent long-term
facts stored in SQLite as well as monitor active short-term RAM context.
"""

from typing import List
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
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


class MemoryScreen(QWidget):
    """Long-term SQLite facts & short-term RAM context screen."""

    fact_added = Signal(str, str)  # (fact, category)
    fact_deleted = Signal(int)
    search_changed = Signal(str)
    clear_ram_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # Top Add & Search Bar
        top_frame = HudFrame()
        top_layout = QVBoxLayout(top_frame)
        top_layout.setContentsMargins(16, 12, 16, 12)
        top_layout.setSpacing(10)

        hdr = QLabel("PERSISTENT MEMORY MATRIX")
        hdr.setObjectName("sectionHeader")
        top_layout.addWidget(hdr)

        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        self.category_combo = QComboBox()
        self.category_combo.addItems(["preference", "project", "personal", "general"])
        self.category_combo.setFixedWidth(130)
        add_row.addWidget(self.category_combo)

        self.fact_input = QLineEdit()
        self.fact_input.setPlaceholderText("Teach J.A.R.V.I.S. a persistent fact (e.g., 'My primary workspace is C:\\MY STUFF\\Projects')...")
        self.fact_input.returnPressed.connect(self._on_add)
        add_row.addWidget(self.fact_input, stretch=1)

        add_btn = QPushButton(" STORE FACT")
        add_btn.setObjectName("primaryButton")
        add_btn.setIcon(create_vector_icon("plus", HudPalette.CYAN_ELECTRIC, 14))
        add_btn.setIconSize(QSize(14, 14))
        add_btn.clicked.connect(self._on_add)
        add_row.addWidget(add_btn)
        top_layout.addLayout(add_row)

        root.addWidget(top_frame)

        # Split Content: Left Long-Term Facts, Right Short-Term RAM Context
        split = QHBoxLayout()
        split.setSpacing(12)

        # Left: Long-Term Facts List
        facts_frame = HudFrame()
        facts_layout = QVBoxLayout(facts_frame)
        facts_layout.setContentsMargins(14, 12, 14, 12)
        facts_layout.setSpacing(8)

        search_row = QHBoxLayout()
        lbl_lt = QLabel("LONG-TERM STORED FACTS")
        lbl_lt.setObjectName("sectionHeader")
        search_row.addWidget(lbl_lt)
        search_row.addStretch(1)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter memory...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self.search_changed.emit)
        search_row.addWidget(self.search_input)
        facts_layout.addLayout(search_row)

        self.facts_scroll = QScrollArea()
        self.facts_scroll.setWidgetResizable(True)
        self.facts_scroll.setFrameShape(QFrame.NoFrame)
        self._facts_container = QWidget()
        self._facts_container.setStyleSheet("background: transparent;")
        self._facts_list_layout = QVBoxLayout(self._facts_container)
        self._facts_list_layout.setContentsMargins(0, 0, 4, 0)
        self._facts_list_layout.setSpacing(6)
        self._facts_list_layout.addStretch(1)
        self.facts_scroll.setWidget(self._facts_container)
        facts_layout.addWidget(self.facts_scroll, stretch=1)

        split.addWidget(facts_frame, stretch=6)

        # Right: Active RAM Window
        ram_frame = HudFrame()
        ram_layout = QVBoxLayout(ram_frame)
        ram_layout.setContentsMargins(14, 12, 14, 12)
        ram_layout.setSpacing(8)

        ram_hdr = QHBoxLayout()
        lbl_ram = QLabel("ACTIVE RAM CONTEXT WINDOW")
        lbl_ram.setObjectName("sectionHeader")
        ram_hdr.addWidget(lbl_ram)
        ram_hdr.addStretch(1)

        clear_ram_btn = QPushButton("FLUSH RAM")
        clear_ram_btn.setObjectName("dangerButton")
        clear_ram_btn.setFixedHeight(26)
        clear_ram_btn.clicked.connect(self.clear_ram_requested.emit)
        ram_hdr.addWidget(clear_ram_btn)
        ram_layout.addLayout(ram_hdr)

        self.ram_label = QLabel("No active context turns buffered.")
        self.ram_label.setWordWrap(True)
        self.ram_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.ram_label.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 11px; color: {HudPalette.TEXT_SECONDARY}; line-height: 1.5;"
        )
        ram_scroll = QScrollArea()
        ram_scroll.setWidgetResizable(True)
        ram_scroll.setFrameShape(QFrame.NoFrame)
        ram_scroll.setWidget(self.ram_label)
        ram_layout.addWidget(ram_scroll, stretch=1)

        split.addWidget(ram_frame, stretch=4)
        root.addLayout(split, stretch=1)

    def _on_add(self) -> None:
        text = self.fact_input.text().strip()
        if text:
            cat = self.category_combo.currentText()
            self.fact_input.clear()
            self.fact_added.emit(text, cat)

    def render_facts(self, facts: List[object]) -> None:
        while self._facts_list_layout.count() > 1:
            item = self._facts_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not facts:
            empty = QLabel("No facts stored yet. Say 'Remember that...' or add a fact above.")
            empty.setStyleSheet(f"color: {HudPalette.TEXT_MUTED}; font-size: 11px; padding: 12px;")
            self._facts_list_layout.insertWidget(0, empty)
            return

        for f in facts:
            card = QFrame()
            card.setObjectName("listCard")
            card.setStyleSheet(
                f"QFrame#listCard {{ background: {HudPalette.BG_CARD}; border: 1px solid {HudPalette.BORDER_SUBTLE}; border-radius: 5px; }}"
            )
            row = QHBoxLayout(card)
            row.setContentsMargins(10, 8, 10, 8)
            row.setSpacing(10)

            cat_badge = QLabel(f.category.upper())
            cat_badge.setFixedWidth(84)
            cat_badge.setAlignment(Qt.AlignCenter)
            cat_badge.setStyleSheet(
                f"background: rgba(0, 229, 255, 0.12); color: {HudPalette.CYAN_ELECTRIC}; "
                f"border: 1px solid {HudPalette.CYAN_DIM}; border-radius: 3px; font-size: 9px; font-weight: 700; padding: 2px 4px;"
            )

            fact_lbl = QLabel(f.fact)
            fact_lbl.setWordWrap(True)
            fact_lbl.setStyleSheet(f"font-size: 12px; color: {HudPalette.TEXT_PRIMARY}; border: none;")

            del_btn = QPushButton()
            del_btn.setIcon(create_vector_icon("trash", HudPalette.RED_ALERT, 14))
            del_btn.setIconSize(QSize(14, 14))
            del_btn.setFixedSize(28, 28)
            del_btn.setObjectName("dangerButton")
            del_btn.clicked.connect(lambda _=False, fid=f.id: self.fact_deleted.emit(fid))

            row.addWidget(cat_badge)
            row.addWidget(fact_lbl, stretch=1)
            row.addWidget(del_btn)
            self._facts_list_layout.insertWidget(self._facts_list_layout.count() - 1, card)

    def render_ram_context(self, context: list) -> None:
        if not context:
            self.ram_label.setText("Active RAM context buffer is empty.")
            return
        lines = []
        for idx, turn in enumerate(context, 1):
            role = turn.get("role", "user").upper()
            content = turn.get("content", "")
            lines.append(f"[{idx:02d}] {role}: {content}")
        self.ram_label.setText("\n\n".join(lines))
