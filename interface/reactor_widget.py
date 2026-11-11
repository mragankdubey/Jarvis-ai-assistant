"""
Reimagined 6-Layer Animated Arc Reactor Widget for J.A.R.V.I.S.

Features concentric rotating shroud arcs, degree azimuth telemetry ticks,
counter-rotating orbital rings, expanding energy pulse waves, Stark coil
geometry, smooth color/speed state interpolation, and power-up support.
"""

import math
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Property
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget
from core.states import AssistantState


def _lerp_color(c1: QColor, c2: QColor, t: float) -> QColor:
    """Linearly interpolate between two QColors."""
    t = max(0.0, min(1.0, t))
    return QColor(
        int(c1.red() + (c2.red() - c1.red()) * t),
        int(c1.green() + (c2.green() - c1.green()) * t),
        int(c1.blue() + (c2.blue() - c1.blue()) * t),
        int(c1.alpha() + (c2.alpha() - c1.alpha()) * t),
    )


class ArcReactorWidget(QWidget):
    """
    Signature animated Arc Reactor centerpiece responding to AssistantState,
    real-time audio amplitude, and boot power-up progression.
    """

    STATE_TARGETS = {
        AssistantState.IDLE:       (QColor(0, 200, 235), QColor(0, 95, 165), 0.75, 0.35),
        AssistantState.ACTIVATING: (QColor(210, 252, 255), QColor(0, 229, 255), 3.4, 1.0),
        AssistantState.LISTENING:  (QColor(0, 255, 220), QColor(0, 175, 255), 1.8, 0.90),
        AssistantState.PROCESSING: (QColor(64, 210, 255), QColor(0, 102, 255), 3.8, 0.85),
        AssistantState.SPEAKING:   (QColor(112, 243, 255), QColor(0, 180, 255), 2.3, 0.95),
        AssistantState.SLEEPING:   (QColor(0, 110, 155), QColor(0, 50, 90), 0.25, 0.18),
        AssistantState.ERROR:      (QColor(255, 46, 99), QColor(180, 30, 60), 1.4, 0.85),
        AssistantState.STOPPING:   (QColor(0, 90, 130), QColor(0, 40, 70), 0.2, 0.15),
    }

    def __init__(self, parent=None, compact: bool = False):
        super().__init__(parent)
        self.compact = compact
        if compact:
            self.setMinimumSize(140, 140)
        else:
            self.setMinimumSize(210, 210)

        self._state = AssistantState.IDLE
        self._power_level = 1.0  # 0.0 -> 1.0 used during cinematic boot
        self._audio_level = 0.0  # 0.0 -> 1.0 real/simulated envelope

        # Animated state variables
        self._curr_primary = QColor(0, 200, 235)
        self._curr_secondary = QColor(0, 95, 165)
        self._curr_speed = 0.75
        self._curr_intensity = 0.35

        self._angle_outer = 0.0
        self._angle_mid = 0.0
        self._angle_inner = 0.0
        self._pulse_phase = 0.0
        self._ripple_phase = 0.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(24)  # ~41 FPS smooth low-overhead animation

    def get_power_level(self) -> float:
        return self._power_level

    def set_power_level(self, val: float) -> None:
        self._power_level = max(0.0, min(1.0, float(val)))
        self.update()

    powerLevel = Property(float, get_power_level, set_power_level)

    def set_state(self, new_state: AssistantState) -> None:
        self._state = new_state

    def set_audio_level(self, level: float) -> None:
        # Smooth audio envelope follower
        target = max(0.0, min(1.0, level))
        self._audio_level = self._audio_level * 0.55 + target * 0.45

    def pause_animations(self) -> None:
        if self._timer.isActive():
            self._timer.stop()

    def resume_animations(self) -> None:
        if not self._timer.isActive():
            self._timer.start(24)

    def _tick(self) -> None:
        target_p, target_s, target_spd, target_int = self.STATE_TARGETS.get(
            self._state, self.STATE_TARGETS[AssistantState.IDLE]
        )

        # Smooth transition toward target state aesthetics
        self._curr_primary = _lerp_color(self._curr_primary, target_p, 0.14)
        self._curr_secondary = _lerp_color(self._curr_secondary, target_s, 0.14)
        self._curr_speed += (target_spd - self._curr_speed) * 0.12
        self._curr_intensity += (target_int - self._curr_intensity) * 0.12

        power_factor = 0.25 + 1.45 * self._power_level
        spd = self._curr_speed * power_factor

        self._angle_outer = (self._angle_outer + 0.55 * spd) % 360.0
        self._angle_mid = (self._angle_mid - 0.95 * spd) % 360.0
        self._angle_inner = (self._angle_inner + 1.35 * spd) % 360.0
        self._pulse_phase = (self._pulse_phase + 0.055 * max(0.6, spd)) % (2.0 * math.pi)
        self._ripple_phase = (self._ripple_phase + 0.022 * max(0.7, spd)) % 1.0

        # Decay audio level gently when idle
        if self._state not in (AssistantState.LISTENING, AssistantState.SPEAKING):
            self._audio_level *= 0.88

        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)

        w, h = self.width(), self.height()
        center = QPointF(w / 2.0, h / 2.0)
        max_r = min(w, h) / 2.0 - 16.0
        if max_r <= 20:
            return

        pwr = self._power_level
        intensity = self._curr_intensity * pwr
        audio_boost = self._audio_level * 0.25
        pulse = 0.5 + 0.5 * math.sin(self._pulse_phase)

        prim = QColor(self._curr_primary)
        sec = QColor(self._curr_secondary)

        # LAYER 1: Ambient Radial Glow Bloom
        bloom_r = max_r * (0.98 + 0.04 * pulse + audio_boost * 0.15)
        bloom = QRadialGradient(center, bloom_r)
        alpha_center = int((55 + 75 * intensity + 60 * audio_boost) * pwr)
        bloom.setColorAt(0.0, QColor(prim.red(), prim.green(), prim.blue(), min(220, alpha_center)))
        bloom.setColorAt(0.52, QColor(sec.red(), sec.green(), sec.blue(), min(120, int(alpha_center * 0.5))))
        bloom.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(bloom))
        p.drawEllipse(center, bloom_r, bloom_r)

        # LAYER 2: Azimuth Technical Degree Scale & Cardinal Ticks
        if not self.compact:
            scale_r = max_r * 0.96
            p.setPen(QPen(QColor(prim.red(), prim.green(), prim.blue(), int(45 + 50 * intensity)), 1.0))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(center, scale_r, scale_r)

            for deg in range(0, 360, 5):
                is_major = (deg % 30 == 0)
                is_mid = (deg % 15 == 0)
                tick_len = max_r * (0.06 if is_major else (0.038 if is_mid else 0.02))
                tick_alpha = int((145 if is_major else 65) * (0.4 + 0.6 * intensity))
                p.setPen(QPen(QColor(prim.red(), prim.green(), prim.blue(), tick_alpha), 1.4 if is_major else 0.9))
                rad = math.radians(deg)
                p1 = QPointF(center.x() + math.cos(rad) * (scale_r - tick_len), center.y() + math.sin(rad) * (scale_r - tick_len))
                p2 = QPointF(center.x() + math.cos(rad) * scale_r, center.y() + math.sin(rad) * scale_r)
                p.drawLine(p1, p2)

            # Subtle cardinal azimuth labels
            p.setFont(QFont("Consolas", 7, QFont.Bold))
            p.setPen(QColor(prim.red(), prim.green(), prim.blue(), int(110 * pwr)))
            for deg, text in ((0, "090"), (90, "180"), (180, "270"), (270, "000")):
                rad = math.radians(deg)
                lx = center.x() + math.cos(rad) * (max_r * 0.85) - 12
                ly = center.y() + math.sin(rad) * (max_r * 0.85) - 6
                p.drawText(QRectF(lx, ly, 24, 12), Qt.AlignCenter, text)

        # LAYER 3: Expanding Energy Ripple Wave (LISTENING / SPEAKING / ACTIVATING)
        if self._state in (AssistantState.LISTENING, AssistantState.SPEAKING, AssistantState.ACTIVATING) and pwr > 0.6:
            rip_r = max_r * (0.35 + 0.58 * self._ripple_phase)
            rip_alpha = int((1.0 - self._ripple_phase) * 140)
            p.setPen(QPen(QColor(prim.red(), prim.green(), prim.blue(), rip_alpha), 1.6))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(center, rip_r, rip_r)

        # LAYER 4: Outer Rotating Segmented Shroud Arcs & Coil Blocks
        p.save()
        p.translate(center)
        p.rotate(self._angle_outer)

        shroud_r = max_r * 0.78
        shroud_rect = QRectF(-shroud_r, -shroud_r, shroud_r * 2, shroud_r * 2)
        p.setPen(QPen(QColor(prim.red(), prim.green(), prim.blue(), int(190 * pwr)), 2.8, Qt.SolidLine, Qt.FlatCap))
        for i in range(4):
            p.drawArc(shroud_rect, (i * 90 + 10) * 16, 68 * 16)

        # 12 Precision Stator Coil Bars
        coil_pen = QPen(QColor(sec.red(), sec.green(), sec.blue(), int(170 * pwr)), max(2.2, max_r * 0.032), Qt.SolidLine, Qt.FlatCap)
        p.setPen(coil_pen)
        for i in range(12):
            ang = math.radians(i * 30)
            p1 = QPointF(math.cos(ang) * max_r * 0.62, math.sin(ang) * max_r * 0.62)
            p2 = QPointF(math.cos(ang) * max_r * 0.73, math.sin(ang) * max_r * 0.73)
            p.drawLine(p1, p2)
        p.restore()

        # LAYER 5: Counter-Rotating Middle Telemetry Ring + Orbital Nodes
        p.save()
        p.translate(center)
        p.rotate(self._angle_mid)

        mid_r = max_r * 0.56
        mid_rect = QRectF(-mid_r, -mid_r, mid_r * 2, mid_r * 2)
        p.setPen(QPen(QColor(180, 245, 255, int(175 * pwr)), 1.8, Qt.SolidLine, Qt.FlatCap))
        for i in range(6):
            p.drawArc(mid_rect, (i * 60 + 6) * 16, 44 * 16)

        # Orbital lock dots
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(240, 252, 255, int(220 * pwr))))
        for i in range(3):
            ang = math.radians(i * 120)
            p.drawEllipse(QPointF(math.cos(ang) * mid_r, math.sin(ang) * mid_r), 3.0, 3.0)
        p.restore()

        # LAYER 6: Inner Stark Triangular Coil & Luminous Plasma Core
        p.save()
        p.translate(center)
        p.rotate(self._angle_inner * 0.45)

        tri_r = max_r * (0.40 + audio_boost * 0.05)
        tri_pts = [
            QPointF(math.cos(math.radians(i * 120 - 90)) * tri_r, math.sin(math.radians(i * 120 - 90)) * tri_r)
            for i in range(3)
        ]
        p.setPen(QPen(QColor(prim.red(), prim.green(), prim.blue(), int(225 * pwr)), 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(QBrush(QColor(sec.red(), sec.green(), sec.blue(), int((35 + 45 * pulse) * pwr))))
        p.drawPolygon(tri_pts)

        # Inner Hexagon Accent
        hex_r = max_r * 0.28
        hex_pts = [
            QPointF(math.cos(math.radians(i * 60)) * hex_r, math.sin(math.radians(i * 60)) * hex_r)
            for i in range(6)
        ]
        p.setPen(QPen(QColor(225, 250, 255, int(140 * pwr)), 1.2))
        p.setBrush(Qt.NoBrush)
        p.drawPolygon(hex_pts)
        p.restore()

        # Central Energy Plasma Core
        core_r = max_r * (0.19 + 0.03 * pulse + audio_boost * 0.08) * (0.5 + 0.5 * pwr)
        core_grad = QRadialGradient(center, core_r * 1.35)
        core_grad.setColorAt(0.0, QColor(255, 255, 255, int(250 * pwr)))
        core_grad.setColorAt(0.45, QColor(prim.red(), prim.green(), prim.blue(), int(235 * pwr)))
        core_grad.setColorAt(0.85, QColor(sec.red(), sec.green(), sec.blue(), int(120 * pwr)))
        core_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(core_grad))
        p.drawEllipse(center, core_r * 1.35, core_r * 1.35)
