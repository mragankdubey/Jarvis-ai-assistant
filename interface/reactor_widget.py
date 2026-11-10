"""
Animated Arc Reactor Widget for J.A.R.V.I.S. PySide6 HUD.

Custom vector-rendered QWidget inspired by the Stark Industries Arc Reactor.
Animates concentric rotating rings, pulsing energy cores, and state-reactive glows.
"""

import math
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QConicalGradient, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget
from core.states import AssistantState


class ArcReactorWidget(QWidget):
    """
    Renders an animated, state-reactive Arc Reactor using QPainter.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)

        self._state = AssistantState.IDLE
        self._outer_angle = 0.0
        self._inner_angle = 0.0
        self._pulse_phase = 0.0

        # Animation timer (running at ~40 FPS for smooth rendering without high CPU)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_animation)
        self._timer.start(25)

    def set_state(self, new_state: AssistantState) -> None:
        """Update active visual state."""
        self._state = new_state
        self.update()

    def _update_animation(self) -> None:
        """Advance rotational angles and pulse cycles according to state."""
        speed_multiplier = 1.0
        if self._state == AssistantState.PROCESSING:
            speed_multiplier = 3.5
        elif self._state == AssistantState.LISTENING:
            speed_multiplier = 1.8
        elif self._state == AssistantState.SPEAKING:
            speed_multiplier = 2.2
        elif self._state in (AssistantState.IDLE, AssistantState.SLEEPING):
            speed_multiplier = 0.6

        self._outer_angle = (self._outer_angle + 0.8 * speed_multiplier) % 360
        self._inner_angle = (self._inner_angle - 1.2 * speed_multiplier) % 360
        self._pulse_phase = (self._pulse_phase + 0.06 * speed_multiplier) % (2 * math.pi)

        self.update()

    def paintEvent(self, event) -> None:
        """Draw Arc Reactor geometry and lighting effects."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        width = self.width()
        height = self.height()
        center = QPointF(width / 2.0, height / 2.0)
        radius = min(width, height) / 2.0 - 15.0

        if radius <= 10:
            return

        # Determine state-based color palette
        if self._state == AssistantState.ERROR:
            primary_color = QColor(255, 42, 109)    # Red / Crimson alert
            secondary_color = QColor(255, 120, 0)
        elif self._state == AssistantState.PROCESSING:
            primary_color = QColor(0, 229, 255)    # Electric Cyan
            secondary_color = QColor(0, 100, 255)   # Deep Blue
        elif self._state == AssistantState.LISTENING:
            primary_color = QColor(0, 255, 200)    # Bright Aquamarine
            secondary_color = QColor(0, 229, 255)
        elif self._state == AssistantState.SPEAKING:
            primary_color = QColor(64, 196, 255)   # Light Blue energy
            secondary_color = QColor(0, 229, 255)
        elif self._state == AssistantState.ACTIVATING:
            primary_color = QColor(255, 255, 255)  # Flash White
            secondary_color = QColor(0, 229, 255)
        else:  # IDLE / SLEEPING
            primary_color = QColor(0, 180, 216)    # Subdued Cyan
            secondary_color = QColor(0, 80, 120)

        # Pulse amplitude
        pulse = 0.5 + 0.5 * math.sin(self._pulse_phase)

        # 1. Background radial glow
        glow_grad = QRadialGradient(center, radius)
        glow_alpha = int(40 + 45 * pulse) if self._state != AssistantState.IDLE else 25
        glow_color = QColor(primary_color.red(), primary_color.green(), primary_color.blue(), glow_alpha)
        glow_grad.setColorAt(0.0, glow_color)
        glow_grad.setColorAt(0.7, QColor(secondary_color.red(), secondary_color.green(), secondary_color.blue(), int(glow_alpha / 2)))
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, radius, radius)

        # 2. Outer Containment Ring
        outer_pen = QPen(primary_color, 2.0)
        painter.setPen(outer_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, radius * 0.95, radius * 0.95)

        # 3. Rotating Segmented Outer Ring
        painter.save()
        painter.translate(center)
        painter.rotate(self._outer_angle)
        seg_pen = QPen(primary_color, 3.0)
        painter.setPen(seg_pen)
        num_segments = 12
        for i in range(num_segments):
            angle = (360.0 / num_segments) * i
            rad = math.radians(angle)
            p1 = QPointF(math.cos(rad) * radius * 0.82, math.sin(rad) * radius * 0.82)
            p2 = QPointF(math.cos(rad) * radius * 0.93, math.sin(rad) * radius * 0.93)
            painter.drawLine(p1, p2)
        painter.restore()

        # 4. Middle Counter-Rotating Ring
        painter.save()
        painter.translate(center)
        painter.rotate(self._inner_angle)
        mid_pen = QPen(secondary_color, 2.0)
        painter.setPen(mid_pen)
        painter.drawEllipse(QPointF(0, 0), radius * 0.72, radius * 0.72)

        # Inner ring tick marks
        num_inner_ticks = 8
        tick_pen = QPen(primary_color, 2.5)
        painter.setPen(tick_pen)
        for i in range(num_inner_ticks):
            angle = (360.0 / num_inner_ticks) * i
            rad = math.radians(angle)
            p1 = QPointF(math.cos(rad) * radius * 0.58, math.sin(rad) * radius * 0.58)
            p2 = QPointF(math.cos(rad) * radius * 0.70, math.sin(rad) * radius * 0.70)
            painter.drawLine(p1, p2)
        painter.restore()

        # 5. Core Triangular Coil Emitter
        painter.save()
        painter.translate(center)
        painter.rotate(-self._outer_angle * 0.5)
        triangle_pen = QPen(primary_color, 2.0)
        painter.setPen(triangle_pen)
        triangle_brush = QColor(secondary_color.red(), secondary_color.green(), secondary_color.blue(), int(30 + 30 * pulse))
        painter.setBrush(QBrush(triangle_brush))

        tri_points = []
        for i in range(3):
            angle = math.radians(i * 120 - 90)
            tri_points.append(QPointF(math.cos(angle) * radius * 0.45, math.sin(angle) * radius * 0.45))
        painter.drawPolygon(tri_points)
        painter.restore()

        # 6. Central Arc Energy Core
        core_radius = radius * (0.22 + 0.05 * pulse)
        core_grad = QRadialGradient(center, core_radius)
        core_grad.setColorAt(0.0, QColor(255, 255, 255, 240))
        core_grad.setColorAt(0.4, primary_color)
        core_grad.setColorAt(1.0, QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 20))
        painter.setBrush(QBrush(core_grad))
        painter.setPen(QPen(primary_color, 1.5))
        painter.drawEllipse(center, core_radius, core_radius)
