"""
Custom Application Identity Icon Generator for J.A.R.V.I.S.

Generates crisp multi-resolution Windows ICO and PNG Arc Reactor brand assets
in assets/icons/ so the taskbar, window chrome, system tray, and shortcuts
share a cohesive high-contrast Stark Industries identity.
"""

import io
import math
from pathlib import Path
import struct
from typing import List
from PySide6.QtCore import QBuffer, QIODevice, QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QImage, QPainter, QPen, QPixmap, QRadialGradient

from core.paths import get_asset_path, is_frozen

ICONS_DIR = get_asset_path("icons")
ICO_PATH = ICONS_DIR / "jarvis.ico"
PNG_PATH = ICONS_DIR / "jarvis.png"


def render_reactor_image(size: int) -> QImage:
    """Render an antialiased, crisp Arc Reactor emblem at the target pixel size."""
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)

    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    c = size / 2.0
    center = QPointF(c, c)
    r = size * 0.45

    # 1. Dark metallic circular badge background
    bg_grad = QRadialGradient(center, r)
    bg_grad.setColorAt(0.0, QColor(12, 26, 48))
    bg_grad.setColorAt(0.75, QColor(7, 12, 22))
    bg_grad.setColorAt(1.0, QColor(4, 7, 13))
    painter.setBrush(QBrush(bg_grad))
    painter.setPen(QPen(QColor(0, 229, 255), max(1.2, size * 0.055)))
    painter.drawEllipse(center, r, r)

    # 2. Outer segmented coil ring (visible from 24px upwards)
    if size >= 24:
        seg_pen = QPen(QColor(0, 195, 255, 220), max(1.0, size * 0.042), Qt.SolidLine, Qt.FlatCap)
        painter.setPen(seg_pen)
        segments = 8 if size < 48 else 12
        for i in range(segments):
            ang = math.radians((360.0 / segments) * i)
            p1 = QPointF(c + math.cos(ang) * r * 0.61, c + math.sin(ang) * r * 0.61)
            p2 = QPointF(c + math.cos(ang) * r * 0.88, c + math.sin(ang) * r * 0.88)
            painter.drawLine(p1, p2)

    # 3. Inner bright ring
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(QColor(112, 243, 255), max(1.0, size * 0.042)))
    painter.drawEllipse(center, r * 0.56, r * 0.56)

    # 4. Stark triangular emitter outline (strong silhouette even at small sizes)
    tri_pts = []
    for i in range(3):
        ang = math.radians(i * 120 + 90)
        tri_pts.append(QPointF(c + math.cos(ang) * r * 0.40, c + math.sin(ang) * r * 0.40))
    painter.setPen(QPen(QColor(220, 252, 255), max(1.0, size * 0.036), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(QBrush(QColor(0, 229, 255, 55)))
    painter.drawPolygon(tri_pts)

    # 5. Glowing white-cyan plasma core
    core_r = r * 0.25
    core_grad = QRadialGradient(center, core_r * 1.4)
    core_grad.setColorAt(0.0, QColor(255, 255, 255))
    core_grad.setColorAt(0.55, QColor(0, 229, 255))
    core_grad.setColorAt(1.0, QColor(0, 140, 255, 0))
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(core_grad))
    painter.drawEllipse(center, core_r * 1.4, core_r * 1.4)

    painter.end()
    return img


def _image_to_png_bytes(img: QImage) -> bytes:
    """Encode QImage as PNG bytes in memory."""
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    data = bytes(buf.data())
    buf.close()
    return data


def save_multi_res_ico(ico_path: Path, png_path: Path) -> None:
    """Generate and save a valid multi-resolution Windows .ico and master .png."""
    ico_path.parent.mkdir(parents=True, exist_ok=True)
    sizes: List[int] = [16, 24, 32, 48, 64, 128, 256]
    png_blobs: List[bytes] = []

    for sz in sizes:
        img = render_reactor_image(sz)
        if sz == 256:
            img.save(str(png_path), "PNG")
        png_blobs.append(_image_to_png_bytes(img))

    # Build Windows ICO header (6 bytes) + directory entries (16 bytes each) + PNG payloads
    count = len(sizes)
    header = struct.pack("<HHH", 0, 1, count)
    offset = 6 + (16 * count)
    entries = bytearray()
    payload = bytearray()

    for sz, blob in zip(sizes, png_blobs):
        w_byte = 0 if sz == 256 else sz
        h_byte = 0 if sz == 256 else sz
        entry = struct.pack(
            "<BBBBHHII",
            w_byte,
            h_byte,
            0,      # color palette
            0,      # reserved
            1,      # color planes
            32,     # bits per pixel
            len(blob),
            offset,
        )
        entries.extend(entry)
        payload.extend(blob)
        offset += len(blob)

    ico_path.write_bytes(header + entries + payload)


def get_app_icon() -> QIcon:
    """Load or generate the multi-resolution JARVIS application QIcon."""
    if not ICO_PATH.exists() and not is_frozen():
        try:
            save_multi_res_ico(ICO_PATH, PNG_PATH)
        except Exception:
            pass
    icon = QIcon(str(ICO_PATH)) if ICO_PATH.exists() else QIcon()
    if icon.isNull():
        for sz in (16, 24, 32, 48, 64, 128):
            icon.addPixmap(QPixmap.fromImage(render_reactor_image(sz)))
    return icon
