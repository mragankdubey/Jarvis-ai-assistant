"""
Holographic Multi-Ribbon Audio Visualizer for J.A.R.V.I.S. PySide6 HUD.

Draws layered harmonic waveform ribbons, subtle equalizer bars, and an honest
voice/microphone status readout reflecting actual hardware availability.
"""

import math
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget
from core.states import AssistantState
from interface.theme import HudPalette, qcolor_with_alpha


class WaveformWidget(QWidget):
    """
    Renders a multi-ribbon harmonic oscilloscope responding to live audio
    amplitude and assistant operational state.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(76)
        self.setMaximumHeight(92)
        self._state = AssistantState.IDLE
        self._mic_available = False
        self._wake_enabled = True
        self._audio_level = 0.0
        self._phase = 0.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(28)

    def set_state(self, new_state: AssistantState) -> None:
        self._state = new_state
        self.update()

    def set_mic_status(self, available: bool, wake_enabled: bool = True) -> None:
        self._mic_available = available
        self._wake_enabled = wake_enabled
        self.update()

    def set_audio_level(self, level: float) -> None:
        target = max(0.0, min(1.0, level))
        self._audio_level = self._audio_level * 0.5 + target * 0.5

    def pause_animations(self) -> None:
        if self._timer.isActive():
            self._timer.stop()

    def resume_animations(self) -> None:
        if not self._timer.isActive():
            self._timer.start(28)

    def _tick(self) -> None:
        speed = 0.06
        if self._state == AssistantState.SPEAKING:
            speed = 0.24
            # Natural cadence envelope when synthesizing speech
            self._audio_level = 0.45 + 0.35 * abs(math.sin(self._phase * 1.4))
        elif self._state == AssistantState.LISTENING:
            speed = 0.18
            if self._mic_available:
                self._audio_level = max(self._audio_level * 0.85, 0.22)
        elif self._state == AssistantState.PROCESSING:
            speed = 0.30
            self._audio_level *= 0.9
        else:
            self._audio_level *= 0.86

        self._phase = (self._phase + speed) % (2.0 * math.pi)
        self.update()

    def _status_text(self) -> tuple[str, QColor]:
        if self._state == AssistantState.ERROR:
            return "AUDIO SUBSYSTEM ALERT", QColor(HudPalette.RED_ALERT)
        if self._state == AssistantState.SPEAKING:
            return "SPEAKING // VOCAL SYNTHESIS", QColor(HudPalette.CYAN_ICE)
        if self._state == AssistantState.PROCESSING:
            return "PROCESSING // NEURAL DISPATCH", QColor("#40C4FF")
        if self._state == AssistantState.LISTENING:
            if self._mic_available:
                return "LISTENING // VOICE CAPTURE ACTIVE", QColor("#00FFCC")
            return "MIC UNAVAILABLE // TEXT MODE", QColor(HudPalette.AMBER_WARN)
        if self._state == AssistantState.SLEEPING:
            return "SLEEPING // STANDBY", QColor(HudPalette.TEXT_MUTED)
        if not self._mic_available:
            return "MIC OFFLINE // TEXT INPUT READY", QColor(HudPalette.TEXT_SECONDARY)
        if not self._wake_enabled:
            return "WAKE WORD PAUSED // MANUAL MIC", QColor(HudPalette.TEXT_SECONDARY)
        return "IDLE // LOCAL WAKE MONITOR", QColor(HudPalette.CYAN_MID)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.width(), self.height()
        rect = QRectF(0.5, 0.5, w - 1, h - 1)

        # Subtle HUD backdrop box
        p.setBrush(QBrush(qcolor_with_alpha(HudPalette.BG_DARK, 210)))
        p.setPen(QPen(qcolor_with_alpha(HudPalette.BORDER_SUBTLE, 190), 1.0))
        p.drawRoundedRect(rect, 5, 5)

        # Center baseline axis
        mid_y = h * 0.58
        p.setPen(QPen(qcolor_with_alpha(HudPalette.CYAN_DIM, 75), 1.0, Qt.DashLine))
        p.drawLine(QPointF(8, mid_y), QPointF(w - 8, mid_y))

        # Status readout header inside visualizer
        status_label, status_color = self._status_text()
        p.setPen(status_color)
        p.setFont(QFont("Consolas", 8, QFont.Bold))
        p.drawText(QRectF(10, 4, w - 20, 16), Qt.AlignLeft | Qt.AlignVCenter, status_label)

        # Determine wave amplitude cleanly (no fake active wave when mic is offline & idle)
        if self._state == AssistantState.SPEAKING:
            amp = (h * 0.30) * max(0.35, self._audio_level)
        elif self._state == AssistantState.LISTENING and self._mic_available:
            amp = (h * 0.28) * max(0.28, self._audio_level)
        elif self._state == AssistantState.PROCESSING:
            amp = h * 0.14
        elif self._mic_available and self._wake_enabled and self._state == AssistantState.IDLE:
            # Reflect true ambient microphone level when monitoring locally
            amp = (h * 0.20) * max(0.03, self._audio_level)
        else:
            amp = 1.5  # Quiet resting flatline when sleeping or mic unavailable

        # Subtle vertical frequency equalizer bars
        num_bars = 36
        bar_w = max(2.0, (w - 28.0) / (num_bars * 1.6))
        bar_step = (w - 24.0) / num_bars
        for b in range(num_bars):
            bx = 12.0 + b * bar_step
            norm = (b / float(num_bars)) * math.pi
            env = math.sin(norm)
            bar_val = abs(math.sin(norm * 4.0 + self._phase * 1.2) * math.cos(norm * 2.5 - self._phase * 0.8))
            bh = max(2.0, amp * 1.15 * env * bar_val)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(qcolor_with_alpha(HudPalette.CYAN_ELECTRIC, 42)))
            p.drawRect(QRectF(bx, mid_y - bh, bar_w, bh * 2.0))

        # Draw 3 layered glowing harmonic wave ribbons
        ribbons = [
            (1.0, 2.2, 0.0, HudPalette.CYAN_ELECTRIC, 230),
            (0.75, 1.5, 1.1, HudPalette.CYAN_ICE, 160),
            (0.55, 1.2, 2.2, "#4080FF" if self._state != AssistantState.ERROR else HudPalette.RED_ALERT, 130),
        ]

        samples = 84
        dx = (w - 16.0) / float(samples - 1)
        for freq_scale, stroke_w, phase_shift, color_hex, alpha in ribbons:
            path = QPainterPath()
            for i in range(samples):
                x = 8.0 + i * dx
                t = i / float(samples - 1)
                window = math.sin(t * math.pi) ** 1.3
                ang = t * 2.0 * math.pi * (2.5 * freq_scale)
                y = mid_y + (
                    math.sin(ang + self._phase + phase_shift) * 0.65
                    + math.sin(ang * 2.1 - self._phase * 1.4 + phase_shift) * 0.35
                ) * amp * window
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)

            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(qcolor_with_alpha(color_hex, alpha), stroke_w))
            p.drawPath(path)
