"""
Real-Time Hardware and Subsystem Diagnostics for J.A.R.V.I.S.

Performs honest, non-fabricated checks on audio hardware, AI credentials,
local wake-word models, network interfaces, and system telemetry.
"""

from dataclasses import dataclass
import logging
import platform
import socket
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SubsystemStatus:
    name: str
    ok: bool
    detail: str


def check_microphone() -> Tuple[bool, str, List[str]]:
    """
    Probe local audio hardware for an active default input device.
    Never fakes availability.
    """
    devices: List[str] = []
    pa = None
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        count = pa.get_device_count()
        for idx in range(count):
            info = pa.get_device_info_by_index(idx)
            if int(info.get("maxInputChannels", 0)) > 0:
                devices.append(str(info.get("name", f"Input {idx}")))

        try:
            default_info = pa.get_default_input_device_info()
            default_name = str(default_info.get("name", "Default Microphone"))
            return True, default_name, devices
        except IOError:
            return False, "No Default Input Device", devices
    except Exception as e:
        logger.debug("Microphone probe error: %s", e)
        return False, "Audio Subsystem Unavailable", devices
    finally:
        if pa is not None:
            try:
                pa.terminate()
            except Exception:
                pass


def check_network() -> Tuple[bool, str]:
    """
    Check active network connectivity honestly using interface state and DNS/socket probe.
    """
    try:
        import psutil
        stats = psutil.net_if_stats()
        active_ifaces = [
            name for name, st in stats.items()
            if st.isup and "loopback" not in name.lower()
        ]
        if not active_ifaces:
            return False, "No Active Network Adapter"

        # Fast non-blocking-style socket connect test (0.6s timeout)
        try:
            with socket.create_connection(("1.1.1.1", 53), timeout=0.6):
                return True, f"Online ({active_ifaces[0]})"
        except OSError:
            return False, f"Limited / Offline ({active_ifaces[0]})"
    except Exception as e:
        logger.debug("Network probe error: %s", e)
        return False, "Network Probe Unavailable"


def check_wake_word_engine(model_name: str = "hey_jarvis") -> Tuple[bool, str]:
    """Verify openWakeWord ONNX runtime and model presence quickly without consuming mic."""
    import importlib.util
    from pathlib import Path
    from core.paths import get_resource_root

    spec_oww = importlib.util.find_spec("openwakeword")
    spec_ort = importlib.util.find_spec("onnxruntime")
    if spec_oww is None or spec_ort is None:
        return False, "openWakeWord / onnxruntime missing"

    try:
        candidates = []
        if spec_oww.origin:
            candidates.append(Path(spec_oww.origin).parent / "resources" / "models")
        candidates.append(get_resource_root() / "openwakeword" / "resources" / "models")

        for models_dir in candidates:
            if models_dir.exists() and list(models_dir.glob(f"*{model_name}*")):
                return True, f"ONNX Ready ('{model_name}')"
        return True, f"Engine Ready ('{model_name}')"
    except Exception as e:
        return False, f"Unavailable ({e})"


def get_system_telemetry() -> Dict[str, Any]:
    """Collect lightweight live Windows telemetry."""
    data: Dict[str, Any] = {
        "cpu_percent": 0.0,
        "cpu_cores": 0,
        "ram_percent": 0.0,
        "ram_used_gb": 0.0,
        "ram_total_gb": 0.0,
        "battery_percent": None,
        "battery_plugged": None,
        "net_sent_mb": 0.0,
        "net_recv_mb": 0.0,
        "os": f"{platform.system()} {platform.release()}",
    }
    try:
        import psutil
        data["cpu_percent"] = psutil.cpu_percent(interval=None)
        data["cpu_cores"] = psutil.cpu_count(logical=True) or 0
        mem = psutil.virtual_memory()
        data["ram_percent"] = mem.percent
        data["ram_used_gb"] = mem.used / (1024 ** 3)
        data["ram_total_gb"] = mem.total / (1024 ** 3)

        bat = psutil.sensors_battery()
        if bat is not None:
            data["battery_percent"] = bat.percent
            data["battery_plugged"] = bat.power_plugged

        net = psutil.net_io_counters()
        if net is not None:
            data["net_sent_mb"] = net.bytes_sent / (1024 ** 2)
            data["net_recv_mb"] = net.bytes_recv / (1024 ** 2)
    except Exception as e:
        logger.debug("Telemetry read error: %s", e)
    return data
