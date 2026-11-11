"""
Windows System Tray Controller for J.A.R.V.I.S. PySide6 HUD.

Provides background operation, custom multi-resolution Arc Reactor tray icon,
and right-click quick actions matching the Stark Industries HUD theme.
"""

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon
from interface.icon_generator import get_app_icon, render_reactor_image
from interface.theme import HudPalette


def create_reactor_pixmap(size: int = 32) -> QPixmap:
    """Return high-contrast Arc Reactor emblem pixmap."""
    return QPixmap.fromImage(render_reactor_image(size))


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
        self.setIcon(get_app_icon())
        self.setToolTip("J.A.R.V.I.S. // Stark Industries OS")
        self._create_menu()
        self.activated.connect(self._on_tray_activated)

    def _create_menu(self) -> None:
        menu = QMenu()
        menu.setStyleSheet(
            f"QMenu {{ background-color: {HudPalette.BG_PANEL}; color: {HudPalette.TEXT_PRIMARY}; "
            f"border: 1px solid {HudPalette.CYAN_MID}; padding: 4px; }}"
            f"QMenu::item {{ padding: 6px 18px; border-radius: 3px; }}"
            f"QMenu::item:selected {{ background-color: rgba(0, 229, 255, 0.2); color: {HudPalette.WHITE_PURE}; }}"
        )

        show_action = QAction("Show J.A.R.V.I.S. HUD", menu)
        show_action.triggered.connect(self.show_requested.emit)
        menu.addAction(show_action)

        hide_action = QAction("Hide to Tray", menu)
        hide_action.triggered.connect(self.hide_requested.emit)
        menu.addAction(hide_action)

        menu.addSeparator()

        voice_action = QAction("Activate Voice Link", menu)
        voice_action.triggered.connect(self.toggle_voice_requested.emit)
        menu.addAction(voice_action)

        sleep_action = QAction("Standby / Sleep", menu)
        sleep_action.triggered.connect(self.sleep_requested.emit)
        menu.addAction(sleep_action)

        menu.addSeparator()

        exit_action = QAction("Exit J.A.R.V.I.S.", menu)
        exit_action.triggered.connect(self.exit_requested.emit)
        menu.addAction(exit_action)

        self._menu = menu
        self.setContextMenu(menu)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Restore HUD window when tray icon is clicked."""
        if reason == QSystemTrayIcon.Trigger:
            self.show_requested.emit()
