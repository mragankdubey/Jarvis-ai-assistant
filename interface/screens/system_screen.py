"""
System Status & Telemetry Diagnostics Screen for J.A.R.V.I.S. PySide6 HUD.

Displays live rolling CPU/RAM sparklines, memory allocation, battery health,
network uplink status, audio hardware devices, and AI/voice diagnostics.
"""

from typing import Any, Dict, List
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from core.diagnostics import check_microphone, check_network, check_wake_word_engine
from interface.components import HudFrame, SparklineGraph, TelemetryRing
from interface.theme import HudPalette


class DiagnosticRefreshWorker(QThread):
    """Non-blocking background probe for network, microphone, and wake engine."""
    done = Signal(bool, str, list, bool, str, bool, str)

    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name

    def run(self) -> None:
        mic_ok, mic_name, devices = check_microphone()
        net_ok, net_detail = check_network()
        ww_ok, ww_detail = check_wake_word_engine(self.model_name)
        self.done.emit(mic_ok, mic_name, devices, net_ok, net_detail, ww_ok, ww_detail)


class SystemScreen(QWidget):
    """Deep system telemetry and diagnostics dashboard."""

    def __init__(self, wake_model: str = "hey_jarvis", parent=None):
        super().__init__(parent)
        self.wake_model = wake_model
        self._worker: DiagnosticRefreshWorker | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # Row 1: Rolling Sparkline Graphs
        graphs_row = QHBoxLayout()
        graphs_row.setSpacing(12)

        cpu_frame = HudFrame(show_grid=True)
        cpu_l = QVBoxLayout(cpu_frame)
        cpu_l.setContentsMargins(14, 10, 14, 10)
        self.cpu_graph = SparklineGraph("CPU UTILIZATION HISTORY", HudPalette.CYAN_ELECTRIC)
        cpu_l.addWidget(self.cpu_graph)
        graphs_row.addWidget(cpu_frame, stretch=1)

        ram_frame = HudFrame(show_grid=True)
        ram_l = QVBoxLayout(ram_frame)
        ram_l.setContentsMargins(14, 10, 14, 10)
        self.ram_graph = SparklineGraph("RAM ALLOCATION HISTORY", HudPalette.CYAN_ICE)
        ram_l.addWidget(self.ram_graph)
        graphs_row.addWidget(ram_frame, stretch=1)

        root.addLayout(graphs_row)

        # Row 2: Gauges + Hardware Specifications + Audio/AI Diagnostics
        mid_row = QHBoxLayout()
        mid_row.setSpacing(12)

        # Hardware Specs Card
        hw_frame = HudFrame()
        hw_layout = QVBoxLayout(hw_frame)
        hw_layout.setContentsMargins(16, 12, 16, 12)
        hw_layout.setSpacing(10)

        hw_hdr = QLabel("HARDWARE & SYSTEM TELEMETRY")
        hw_hdr.setObjectName("sectionHeader")
        hw_layout.addWidget(hw_hdr)

        rings_row = QHBoxLayout()
        self.ring_cpu = TelemetryRing("CPU")
        self.ring_ram = TelemetryRing("RAM", accent=HudPalette.CYAN_ICE)
        self.ring_bat = TelemetryRing("BATTERY", accent=HudPalette.GREEN_OK, warn_high=False)
        rings_row.addWidget(self.ring_cpu)
        rings_row.addWidget(self.ring_ram)
        rings_row.addWidget(self.ring_bat)
        hw_layout.addLayout(rings_row)

        self.hw_details = QLabel("Collecting telemetry...")
        self.hw_details.setWordWrap(True)
        self.hw_details.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 11px; color: {HudPalette.TEXT_SECONDARY}; line-height: 1.55;"
        )
        hw_layout.addWidget(self.hw_details, stretch=1)
        mid_row.addWidget(hw_frame, stretch=1)

        # Subsystems & Diagnostics Card
        sub_frame = HudFrame()
        sub_layout = QVBoxLayout(sub_frame)
        sub_layout.setContentsMargins(16, 12, 16, 12)
        sub_layout.setSpacing(10)

        hdr_row = QHBoxLayout()
        sub_hdr = QLabel("AUDIO, NETWORK & AI SUBSYSTEMS")
        sub_hdr.setObjectName("sectionHeader")
        hdr_row.addWidget(sub_hdr)
        hdr_row.addStretch(1)

        self.probe_btn = QPushButton("RE-PROBE HARDWARE")
        self.probe_btn.setObjectName("primaryButton")
        self.probe_btn.setFixedHeight(28)
        self.probe_btn.clicked.connect(self.run_diagnostics)
        hdr_row.addWidget(self.probe_btn)
        sub_layout.addLayout(hdr_row)

        grid = QGridLayout()
        grid.setSpacing(8)
        self.lbl_net = self._add_row(grid, 0, "NETWORK UPLINK", "Checking...")
        self.lbl_mic = self._add_row(grid, 1, "PRIMARY MICROPHONE", "Checking...")
        self.lbl_wake = self._add_row(grid, 2, "WAKE-WORD ENGINE", "Checking...")
        self.lbl_ai = self._add_row(grid, 3, "AI NEURAL LINK", "Checking...")
        self.lbl_tts = self._add_row(grid, 4, "VOICE SYNTHESIS", "pyttsx3 SAPI5 Worker")
        sub_layout.addLayout(grid)

        dev_hdr = QLabel("DETECTED AUDIO INPUT DEVICES")
        dev_hdr.setObjectName("sectionHeader")
        sub_layout.addWidget(dev_hdr)

        self.devices_lbl = QLabel("Probing audio drivers...")
        self.devices_lbl.setWordWrap(True)
        self.devices_lbl.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 10px; color: {HudPalette.TEXT_SECONDARY}; line-height: 1.45;"
        )
        sub_layout.addWidget(self.devices_lbl, stretch=1)
        mid_row.addWidget(sub_frame, stretch=1)

        root.addLayout(mid_row, stretch=1)

    def _add_row(self, grid: QGridLayout, row: int, key: str, default: str) -> QLabel:
        k_lbl = QLabel(key)
        k_lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {HudPalette.TEXT_MUTED}; letter-spacing: 0.8px;")
        v_lbl = QLabel(default)
        v_lbl.setStyleSheet(f"font-family: 'Consolas', monospace; font-size: 11px; font-weight: 700; color: {HudPalette.CYAN_ICE};")
        grid.addWidget(k_lbl, row, 0)
        grid.addWidget(v_lbl, row, 1)
        return v_lbl

    def update_telemetry(self, tel: Dict[str, Any], ai_status: str, tts_enabled: bool) -> None:
        cpu = float(tel.get("cpu_percent", 0.0))
        ram = float(tel.get("ram_percent", 0.0))
        bat = tel.get("battery_percent")
        plugged = tel.get("battery_plugged")

        self.cpu_graph.push_value(cpu)
        self.ram_graph.push_value(ram)
        self.ring_cpu.set_value(cpu, f"{tel.get('cpu_cores', 0)} Cores")
        self.ring_ram.set_value(ram, f"{tel.get('ram_used_gb', 0):.1f}/{tel.get('ram_total_gb', 0):.0f}G")
        if bat is not None:
            self.ring_bat.set_value(float(bat), "AC" if plugged else "BAT")
        else:
            self.ring_bat.set_value(100.0, "AC")

        self.hw_details.setText(
            f"PLATFORM:   {tel.get('os', 'Windows')}\n"
            f"MEMORY:     {tel.get('ram_used_gb', 0):.2f} GB / {tel.get('ram_total_gb', 0):.2f} GB ({ram:.1f}%)\n"
            f"NET I/O:    TX {tel.get('net_sent_mb', 0):.1f} MB  |  RX {tel.get('net_recv_mb', 0):.1f} MB\n"
            f"POWER:      {'AC Connected' if plugged or bat is None else f'On Battery ({bat:.0f}%)'}"
        )
        self.lbl_ai.setText(ai_status)
        self.lbl_tts.setText("pyttsx3 SAPI5 Active" if tts_enabled else "Muted in Settings")

    def stop(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.wait(2000)

    def run_diagnostics(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self.probe_btn.setEnabled(False)
        self.probe_btn.setText("PROBING...")
        self._worker = DiagnosticRefreshWorker(self.wake_model)
        self._worker.done.connect(self._on_diag_done)
        self._worker.start()

    def _on_diag_done(
        self,
        mic_ok: bool,
        mic_name: str,
        devices: List[str],
        net_ok: bool,
        net_detail: str,
        ww_ok: bool,
        ww_detail: str,
    ) -> None:
        self.probe_btn.setEnabled(True)
        self.probe_btn.setText("RE-PROBE HARDWARE")

        self.lbl_net.setText(net_detail)
        self.lbl_net.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 11px; font-weight: 700; "
            f"color: {HudPalette.GREEN_OK if net_ok else HudPalette.AMBER_WARN};"
        )
        self.lbl_mic.setText(mic_name)
        self.lbl_mic.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 11px; font-weight: 700; "
            f"color: {HudPalette.CYAN_ELECTRIC if mic_ok else HudPalette.RED_ALERT};"
        )
        self.lbl_wake.setText(ww_detail)
        self.lbl_wake.setStyleSheet(
            f"font-family: 'Consolas', monospace; font-size: 11px; font-weight: 700; "
            f"color: {HudPalette.CYAN_ELECTRIC if ww_ok else HudPalette.AMBER_WARN};"
        )

        if devices:
            self.devices_lbl.setText("\n".join(f"• {d}" for d in devices[:6]))
        else:
            self.devices_lbl.setText("No audio input capture devices detected by PyAudio.")
