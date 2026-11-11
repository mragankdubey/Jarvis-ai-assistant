"""
Reusable Stark HUD Primitives and Vector Controls for J.A.R.V.I.S.

Provides custom-painted HudFrame containers with corner reticles, circular
TelemetryRing gauges, live SparklineGraph charts, animated HudToggleSwitch
controls, and crisp QPainter vector icons (zero emoji icons).
"""

from collections import deque
import math
from typing import Deque, Optional
from PySide6.QtCore import (
    QEasingCurve,
    QPointF,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    QTimer,
    Property,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from interface.theme import HudPalette, qcolor_with_alpha


def create_vector_icon(name: str, color: str = HudPalette.CYAN_ELECTRIC, size: int = 18) -> QIcon:
    """Render clean technical vector line icons with QPainter (zero emojis)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    c = QColor(color)
    pen = QPen(c, max(1.3, size * 0.09), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    m = size * 0.16
    w = size - 2 * m
    h = size - 2 * m

    if name == "dashboard":
        # 2x2 HUD grid
        b = w * 0.42
        p.drawRect(QRectF(m, m, b, b))
        p.drawRect(QRectF(m + w - b, m, b, b))
        p.drawRect(QRectF(m, m + h - b, b, b))
        p.drawRect(QRectF(m + w - b, m + h - b, b, b))
    elif name == "chat":
        # Speech polygon
        path = QPainterPath()
        path.moveTo(m, m)
        path.lineTo(m + w, m)
        path.lineTo(m + w, m + h * 0.72)
        path.lineTo(m + w * 0.42, m + h * 0.72)
        path.lineTo(m + w * 0.18, m + h)
        path.lineTo(m + w * 0.22, m + h * 0.72)
        path.lineTo(m, m + h * 0.72)
        path.closeSubpath()
        p.drawPath(path)
    elif name == "memory":
        # Hexagonal neural core / node
        cx, cy = size / 2.0, size / 2.0
        r = w * 0.48
        pts = [
            QPointF(cx + math.cos(math.radians(a)) * r, cy + math.sin(math.radians(a)) * r)
            for a in range(0, 360, 60)
        ]
        p.drawPolygon(pts)
        p.drawEllipse(QPointF(cx, cy), r * 0.35, r * 0.35)
    elif name == "notes":
        # Document lines
        p.drawRect(QRectF(m + w * 0.08, m, w * 0.84, h))
        p.drawLine(QPointF(m + w * 0.26, m + h * 0.32), QPointF(m + w * 0.74, m + h * 0.32))
        p.drawLine(QPointF(m + w * 0.26, m + h * 0.55), QPointF(m + w * 0.74, m + h * 0.55))
        p.drawLine(QPointF(m + w * 0.26, m + h * 0.78), QPointF(m + w * 0.55, m + h * 0.78))
    elif name == "reminders":
        # Clock / alarm arc
        cx, cy = size / 2.0, size / 2.0
        r = w * 0.46
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.drawLine(QPointF(cx, cy), QPointF(cx, cy - r * 0.58))
        p.drawLine(QPointF(cx, cy), QPointF(cx + r * 0.45, cy + r * 0.2))
    elif name == "system":
        # Telemetry pulse wave
        path = QPainterPath()
        path.moveTo(m, m + h * 0.55)
        path.lineTo(m + w * 0.25, m + h * 0.55)
        path.lineTo(m + w * 0.40, m + h * 0.15)
        path.lineTo(m + w * 0.60, m + h * 0.88)
        path.lineTo(m + w * 0.75, m + h * 0.42)
        path.lineTo(m + w, m + h * 0.42)
        p.drawPath(path)
    elif name == "settings":
        # Concentric gear circle
        cx, cy = size / 2.0, size / 2.0
        p.drawEllipse(QPointF(cx, cy), w * 0.22, w * 0.22)
        p.drawEllipse(QPointF(cx, cy), w * 0.42, w * 0.42)
        for a in range(0, 360, 45):
            rad = math.radians(a)
            p.drawLine(
                QPointF(cx + math.cos(rad) * w * 0.38, cy + math.sin(rad) * w * 0.38),
                QPointF(cx + math.cos(rad) * w * 0.52, cy + math.sin(rad) * w * 0.52),
            )
    elif name == "mic":
        # Microphone capsule
        cx = size / 2.0
        p.drawRoundedRect(QRectF(cx - w * 0.18, m, w * 0.36, h * 0.55), w * 0.18, w * 0.18)
        p.drawArc(QRectF(cx - w * 0.34, m + h * 0.22, w * 0.68, h * 0.52), 180 * 16, 180 * 16)
        p.drawLine(QPointF(cx, m + h * 0.74), QPointF(cx, m + h))
        p.drawLine(QPointF(cx - w * 0.22, m + h), QPointF(cx + w * 0.22, m + h))
    elif name == "send":
        path = QPainterPath()
        path.moveTo(m, m + h * 0.15)
        path.lineTo(m + w, m + h * 0.5)
        path.lineTo(m, m + h * 0.85)
        path.lineTo(m + w * 0.24, m + h * 0.5)
        path.closeSubpath()
        p.drawPath(path)
    elif name == "sleep":
        # Crescent / standby circle
        cx, cy = size / 2.0, size / 2.0
        p.drawArc(QRectF(m + w * 0.1, m + h * 0.1, w * 0.8, h * 0.8), 120 * 16, 300 * 16)
        p.drawLine(QPointF(cx, m), QPointF(cx, cy))
    elif name == "plus":
        cx, cy = size / 2.0, size / 2.0
        p.drawLine(QPointF(cx, m), QPointF(cx, m + h))
        p.drawLine(QPointF(m, cy), QPointF(m + w, cy))
    elif name == "trash":
        p.drawLine(QPointF(m + w * 0.1, m + h * 0.2), QPointF(m + w * 0.9, m + h * 0.2))
        p.drawRect(QRectF(m + w * 0.22, m + h * 0.2, w * 0.56, h * 0.75))
        p.drawLine(QPointF(m + w * 0.36, m + h * 0.06), QPointF(m + w * 0.64, m + h * 0.06))
    elif name == "check":
        p.drawLine(QPointF(m + w * 0.12, m + h * 0.54), QPointF(m + w * 0.42, m + h * 0.82))
        p.drawLine(QPointF(m + w * 0.42, m + h * 0.82), QPointF(m + w * 0.90, m + h * 0.22))
    elif name == "clear":
        p.drawLine(QPointF(m + w * 0.18, m + h * 0.18), QPointF(m + w * 0.82, m + h * 0.82))
        p.drawLine(QPointF(m + w * 0.82, m + h * 0.18), QPointF(m + w * 0.18, m + h * 0.82))

    p.end()
    return QIcon(pm)


class HudFrame(QFrame):
    """
    Signature Stark Industries HUD Container.
    Draws translucent dark-navy glass, hairline technical border, subtle grid,
    and glowing cyan corner bracket reticles.
    """

    def __init__(self, parent=None, show_grid: bool = False, accent: str = HudPalette.CYAN_ELECTRIC):
        super().__init__(parent)
        self.show_grid = show_grid
        self.accent_color = accent
        self.setAttribute(Qt.WA_StyledBackground, False)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)

        # 1. Translucent obsidian gradient fill
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0.0, qcolor_with_alpha(HudPalette.BG_PANEL, 232))
        grad.setColorAt(1.0, qcolor_with_alpha(HudPalette.BG_DARK, 240))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(qcolor_with_alpha(HudPalette.BORDER_GLOW, 170), 1.0))
        p.drawRoundedRect(rect, 6, 6)

        # 2. Optional subtle engineering micro-grid
        if self.show_grid:
            p.save()
            clip = QPainterPath()
            clip.addRoundedRect(rect, 6, 6)
            p.setClipPath(clip)
            p.setPen(QPen(qcolor_with_alpha(self.accent_color, 13), 1.0))
            step = 24
            x = int(rect.left()) + step
            while x < rect.right():
                p.drawLine(x, int(rect.top()), x, int(rect.bottom()))
                x += step
            y = int(rect.top()) + step
            while y < rect.bottom():
                p.drawLine(int(rect.left()), y, int(rect.right()), y)
                y += step
            p.restore()

        # 3. Sharp corner reticle brackets
        L = 11.0
        p.setPen(QPen(qcolor_with_alpha(self.accent_color, 210), 1.8, Qt.SolidLine, Qt.SquareCap))
        l, t, r, b = rect.left(), rect.top(), rect.right(), rect.bottom()

        # Top-Left
        p.drawLine(QPointF(l, t + L), QPointF(l, t))
        p.drawLine(QPointF(l, t), QPointF(l + L, t))
        # Top-Right
        p.drawLine(QPointF(r - L, t), QPointF(r, t))
        p.drawLine(QPointF(r, t), QPointF(r, t + L))
        # Bottom-Left
        p.drawLine(QPointF(l, b - L), QPointF(l, b))
        p.drawLine(QPointF(l, b), QPointF(l + L, b))
        # Bottom-Right
        p.drawLine(QPointF(r - L, b), QPointF(r, b))
        p.drawLine(QPointF(r, b), QPointF(r, b - L))


class TelemetryRing(QWidget):
    """Circular arc telemetry gauge showing a percentage metric cleanly."""

    def __init__(self, title: str, accent: str = HudPalette.CYAN_ELECTRIC, warn_high: bool = True, parent=None):
        super().__init__(parent)
        self.title = title
        self.accent = accent
        self.warn_high = warn_high
        self._value = 0.0
        self._subtitle = ""
        self.setMinimumSize(74, 96)

    def set_value(self, percent: float, subtitle: str = "") -> None:
        self._value = max(0.0, min(100.0, percent))
        self._subtitle = subtitle
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        ring_size = min(w - 14, h - 28)
        if ring_size < 30:
            return

        cx = w / 2.0
        cy = ring_size / 2.0 + 4.0
        rect = QRectF(cx - ring_size / 2.0, cy - ring_size / 2.0, ring_size, ring_size)

        # Background track
        p.setPen(QPen(qcolor_with_alpha(HudPalette.BORDER_GLOW, 160), 4.5, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 0, 360 * 16)

        # Value arc (start top 90deg clockwise)
        ring_color = QColor(self.accent)
        if self.warn_high:
            if self._value > 85:
                ring_color = QColor(HudPalette.RED_ALERT)
            elif self._value > 70:
                ring_color = QColor(HudPalette.AMBER_WARN)
        else:
            # For battery/power, warn when low
            if self._value < 18:
                ring_color = QColor(HudPalette.RED_ALERT)
            elif self._value < 35:
                ring_color = QColor(HudPalette.AMBER_WARN)

        p.setPen(QPen(ring_color, 5.0, Qt.SolidLine, Qt.RoundCap))
        span = int(-360.0 * (self._value / 100.0) * 16)
        p.drawArc(rect, 90 * 16, span)

        # Center percentage text
        p.setPen(QColor(HudPalette.WHITE_PURE))
        p.setFont(QFont("Consolas", 11, QFont.Bold))
        p.drawText(rect, Qt.AlignCenter, f"{self._value:.0f}%")

        # Label underneath
        label_rect = QRectF(0, cy + ring_size / 2.0 + 4, w, 20)
        p.setPen(QColor(HudPalette.TEXT_SECONDARY))
        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        caption = f"{self.title}" if not self._subtitle else f"{self.title} · {self._subtitle}"
        p.drawText(label_rect, Qt.AlignCenter, caption)


class SparklineGraph(QWidget):
    """Live rolling line chart with glowing stroke and translucent fill."""

    def __init__(self, title: str, color: str = HudPalette.CYAN_ELECTRIC, max_points: int = 40, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        self.values: Deque[float] = deque([0.0] * max_points, maxlen=max_points)
        self.setMinimumHeight(88)

    def push_value(self, val: float) -> None:
        self.values.append(max(0.0, min(100.0, val)))
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        top_pad = 22.0
        bot_pad = 6.0
        graph_h = max(10.0, h - top_pad - bot_pad)

        # Header title & latest value
        latest = self.values[-1] if self.values else 0.0
        p.setPen(QColor(HudPalette.TEXT_SECONDARY))
        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.drawText(QRectF(4, 2, w - 60, 18), Qt.AlignLeft | Qt.AlignVCenter, self.title)

        p.setPen(QColor(self.color))
        p.setFont(QFont("Consolas", 9, QFont.Bold))
        p.drawText(QRectF(w - 56, 2, 52, 18), Qt.AlignRight | Qt.AlignVCenter, f"{latest:.1f}%")

        # Horizontal reference grid lines
        p.setPen(QPen(qcolor_with_alpha(HudPalette.BORDER_SUBTLE, 140), 1.0, Qt.DashLine))
        for frac in (0.0, 0.5, 1.0):
            y = top_pad + graph_h * frac
            p.drawLine(QPointF(2, y), QPointF(w - 2, y))

        pts = list(self.values)
        if len(pts) < 2:
            return

        step_x = (w - 4.0) / float(len(pts) - 1)
        line_path = QPainterPath()
        fill_path = QPainterPath()

        for i, val in enumerate(pts):
            x = 2.0 + i * step_x
            y = top_pad + graph_h * (1.0 - val / 100.0)
            if i == 0:
                line_path.moveTo(x, y)
                fill_path.moveTo(x, top_pad + graph_h)
                fill_path.lineTo(x, y)
            else:
                line_path.lineTo(x, y)
                fill_path.lineTo(x, y)

        fill_path.lineTo(2.0 + (len(pts) - 1) * step_x, top_pad + graph_h)
        fill_path.closeSubpath()

        fill_grad = QLinearGradient(0, top_pad, 0, top_pad + graph_h)
        fill_grad.setColorAt(0.0, qcolor_with_alpha(self.color, 75))
        fill_grad.setColorAt(1.0, qcolor_with_alpha(self.color, 5))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(fill_grad))
        p.drawPath(fill_path)

        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(self.color), 1.8))
        p.drawPath(line_path)


class HudToggleSwitch(QAbstractButton):
    """Animated futuristic pill toggle switch for HUD settings."""

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(46, 24)
        self.setCursor(Qt.PointingHandCursor)

        self._thumb_pos = 1.0 if checked else 0.0
        self._anim = QPropertyAnimation(self, b"thumbPos", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self.toggled.connect(self._animate)

    def get_thumb_pos(self) -> float:
        return self._thumb_pos

    def set_thumb_pos(self, pos: float) -> None:
        self._thumb_pos = pos
        self.update()

    thumbPos = Property(float, get_thumb_pos, set_thumb_pos)

    def _animate(self, checked: bool) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._thumb_pos)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        if self.isChecked():
            track_bg = qcolor_with_alpha(HudPalette.CYAN_ELECTRIC, 65)
            border = QColor(HudPalette.CYAN_ELECTRIC)
            thumb = QColor(HudPalette.WHITE_PURE)
        else:
            track_bg = QColor(HudPalette.BG_DARK)
            border = QColor(HudPalette.BORDER_GLOW)
            thumb = QColor(HudPalette.TEXT_SECONDARY)

        p.setBrush(QBrush(track_bg))
        p.setPen(QPen(border, 1.3))
        p.drawRoundedRect(rect, rect.height() / 2.0, rect.height() / 2.0)

        r = rect.height() - 6.0
        x_min = 4.0
        x_max = self.width() - r - 4.0
        cx = x_min + (x_max - x_min) * self._thumb_pos

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(thumb))
        p.drawEllipse(QRectF(cx, 4.0, r, r))


class StatusChip(QWidget):
    """Compact status indicator badge with colored dot and label."""

    def __init__(self, label: str, ok: bool = True, parent=None):
        super().__init__(parent)
        self._dot_color = HudPalette.GREEN_OK if ok else HudPalette.TEXT_MUTED
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 10, 4)
        layout.setSpacing(6)

        self.dot = QLabel()
        self.dot.setFixedSize(8, 8)
        self.text = QLabel(label)
        self.text.setStyleSheet("font-size: 10px; font-weight: 700; letter-spacing: 0.8px;")

        layout.addWidget(self.dot)
        layout.addWidget(self.text)
        self.set_status(label, ok)

    def set_status(self, label: str, ok: bool, color: Optional[str] = None) -> None:
        c = color or (HudPalette.CYAN_ELECTRIC if ok else HudPalette.RED_ALERT)
        self._dot_color = c
        self.text.setText(label)
        self.text.setStyleSheet(f"color: {c}; font-size: 10px; font-weight: 700; letter-spacing: 0.8px;")
        self.dot.setStyleSheet(f"background-color: {c}; border-radius: 4px;")


class ToastNotification(QFrame):
    """Non-blocking floating HUD feedback toast."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("toastBanner")
        self.setStyleSheet(
            f"QFrame#toastBanner {{ background-color: rgba(11, 20, 36, 240); "
            f"border: 1px solid {HudPalette.CYAN_ELECTRIC}; border-radius: 6px; padding: 8px 14px; }}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        self.label = QLabel("")
        self.label.setStyleSheet(f"color: {HudPalette.WHITE_PURE}; font-size: 11px; font-weight: 600;")
        layout.addWidget(self.label)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)
        self.hide()

    def show_message(self, text: str, duration_ms: int = 2800, is_error: bool = False) -> None:
        border = HudPalette.RED_ALERT if is_error else HudPalette.CYAN_ELECTRIC
        self.setStyleSheet(
            f"QFrame#toastBanner {{ background-color: rgba(11, 20, 36, 242); "
            f"border: 1px solid {border}; border-radius: 6px; }}"
        )
        self.label.setText(text)
        self.adjustSize()
        if self.parentWidget():
            pw = self.parentWidget().width()
            self.move(max(16, pw - self.width() - 24), 56)
        self.raise_()
        self.show()
        self._hide_timer.start(duration_ms)
