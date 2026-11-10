"""
Windows System Tray Controller for J.A.R.V.I.S. PySide6 HUD.

Provides background operation, tray icon indicator, and right-click quick actions.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


def create_reactor_pixmap(size: int = 32) -> QPixmap:
    """Dynamically generate a high-contrast Arc Reactor tray icon."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    center = size / 2.0
    radius = (size / 2.0) - 2.0

    # Cyan outer ring
    painter.setPen(QColor(0, 229, 255))
    painter.setBrush(QColor(10, 20, 35))
    painter.drawEllipse(center, radius, radius)

    # Inner bright core
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(0, 255, 230))
    painter.drawEllipse(center, radius * 0.45, radius * 0.45)

    painter.end()
    return pixmap


class SystemTrayController(QSystemTrayIcon):
    """
    Manages background desktop tray icon and contextual controls.
    """

    show_requested = Signal()
    hide_requested = Signal()
    toggle_voice_requested = Signal()
    sleep_requested = Signal()
    exit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon(create_reactor_pixmap(32)))
        self.setToolTip("J.A.R.V.I.S. // Stark Industries OS")
        self._create_menu()
        self.activated.connect(self._on_tray_activated)

    def _create_menu(self) -> None:
        menu = QMenu()

        show_action = QAction("Show HUD", menu)
        show_action.triggered.connect(self.show_requested.emit)
        menu.addAction(show_action)

        hide_action = QAction("Hide to Tray", menu)
        hide_action.triggered.connect(self.hide_requested.emit)
        menu.addAction(hide_action)

        menu.addSeparator()

        voice_action = QAction("Activate Voice (Wake)", menu)
        voice_action.triggered.connect(self.toggle_voice_requested.emit)
        menu.addAction(voice_action)

        sleep_action = QAction("Sleep Mode", menu)
        sleep_action.triggered.connect(self.sleep_requested.emit)
        menu.addAction(sleep_action)

        menu.addSeparator()

        exit_action = QAction("Exit J.A.R.V.I.S.", menu)
        exit_action.triggered.connect(self.exit_requested.emit)
        menu.addAction(exit_action)

        self.setContextMenu(menu)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Toggle HUD window when tray icon is clicked."""
        if reason == QSystemTrayIcon.Trigger:
            self.show_requested.emit()
