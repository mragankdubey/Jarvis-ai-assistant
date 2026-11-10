"""
Audio Oscilloscope / Waveform Visualizer for J.A.R.V.I.S. PySide6 HUD.

Renders an animated cyan waveform responding dynamically to assistant audio states.
"""

import math
from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget
from core.states import AssistantState


class WaveformWidget(QWidget):
    """
    Renders an animated audio waveform reflecting voice and listening activity.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self._state = AssistantState.IDLE
        self._phase = 0.0

        # Animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def set_state(self, new_state: AssistantState) -> None:
        """Update active audio state."""
        self._state = new_state
        self.update()

    def _tick(self) -> None:
        speed = 0.08
        if self._state == AssistantState.SPEAKING:
            speed = 0.22
        elif self._state == AssistantState.LISTENING:
            speed = 0.16
        elif self._state == AssistantState.PROCESSING:
            speed = 0.28

        self._phase = (self._phase + speed) % (2 * math.pi)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        mid_y = h / 2.0

        if self._state == AssistantState.ERROR:
            pen_color = QColor(255, 42, 109, 220)
        elif self._state in (AssistantState.LISTENING, AssistantState.SPEAKING):
            pen_color = QColor(0, 229, 255, 240)
        elif self._state == AssistantState.PROCESSING:
            pen_color = QColor(0, 150, 255, 200)
        else:
            pen_color = QColor(0, 180, 216, 90)

        pen = QPen(pen_color, 1.8)
        painter.setPen(pen)

        # Amplitude factor depending on state
        if self._state == AssistantState.SPEAKING:
            amp = h * 0.38
        elif self._state == AssistantState.LISTENING:
            amp = h * 0.28
        elif self._state == AssistantState.PROCESSING:
            amp = h * 0.18
        else:
            amp = h * 0.06

        num_points = 80
        step = w / float(num_points - 1)
        prev_point = None

        for i in range(num_points):
            x = i * step
            norm_x = (x / w) * 2 * math.pi
            # Windowing envelope so edges fade to center
            window = math.sin(x / w * math.pi)

            # Composite sine wave
            y_offset = (
                math.sin(norm_x * 3 + self._phase) * 0.6 +
                math.sin(norm_x * 7 - self._phase * 1.5) * 0.4
            ) * amp * window

            pt = QPointF(x, mid_y + y_offset)
            if prev_point is not None:
                painter.drawLine(prev_point, pt)
            prev_point = pt
