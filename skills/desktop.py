"""
Safe Windows Desktop Automation Skill for J.A.R.V.I.S.

Provides allowlisted operating system controls, application launching,
system health metrics, volume adjustments, date/time, and note creation.
Strictly disallows arbitrary shell execution or unsafe AI-generated commands.
"""

import ctypes
from datetime import datetime
import logging
import os
from pathlib import Path
import platform
import re
import subprocess
from typing import Any, Callable, Dict, Optional
from skills.base import BaseSkill, SkillResult

logger = logging.getLogger(__name__)

# Virtual Keycodes for Windows Media Controls
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002


def _send_volume_key(vk_code: int, times: int = 1) -> None:
    """Send synthetic volume keystrokes using Windows API."""
    try:
        import win32api
        for _ in range(times):
            win32api.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
            win32api.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
    except Exception as e:
        logger.warning("Could not send volume keycode: %s", e)


class DesktopSkill(BaseSkill):
    """
    Executes validated, safe desktop and system automation actions.
    """

    # Allowlisted applications mapped to their safe system commands
    ALLOWED_APPS: Dict[str, str] = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "file explorer": "explorer.exe",
        "explorer": "explorer.exe",
        "command prompt": "cmd.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "task manager": "taskmgr.exe",
        "settings": "ms-settings:",
    }

    def __init__(
        self,
        command_runner: Optional[Callable[[str], Any]] = None,
        notes_dir: Optional[Path] = None,
    ):
        """
        Args:
            command_runner: Optional custom runner for testing/mocking.
            notes_dir: Custom directory for saved notes (defaults to ~/JARVIS_Notes).
        """
        self._runner = command_runner or self._default_run
        self.notes_dir = notes_dir or (Path.home() / "JARVIS_Notes")

    @property
    def name(self) -> str:
        return "Desktop Automation"

    @property
    def description(self) -> str:
        return "Controls desktop applications, volume, system metrics, date/time, and notes."

    def _default_run(self, executable: str) -> bool:
        """Safely launch an allowlisted executable or URI."""
        try:
            if executable.startswith("ms-settings:"):
                os.system(f"start {executable}")
            else:
                subprocess.Popen([executable], shell=False)
            return True
        except Exception as e:
            logger.error("Failed launching executable %s: %s", executable, e)
            return False

    def can_handle(self, command: str) -> bool:
        cmd = command.strip().lower()
        if not cmd:
            return False

        # Match application launch
        if any(f"open {app}" in cmd or f"launch {app}" in cmd for app in self.ALLOWED_APPS):
            return True

        # Match volume controls
        if any(w in cmd for w in ["volume up", "increase volume", "volume down", "decrease volume", "mute", "unmute"]):
            return True

        # Match system metrics
        if any(w in cmd for w in ["battery", "cpu", "ram", "memory usage", "system info", "system status"]):
            return True

        # Match time/date
        if any(w in cmd for w in ["what time", "current time", "what is the time", "today's date", "what date", "current date"]):
            return True

        # Match folder navigation
        if any(f"open {f}" in cmd for f in ["downloads", "documents", "notes", "downloads folder", "documents folder"]):
            return True

        # Match notes creation
        if cmd.startswith("take a note") or cmd.startswith("create a note") or cmd.startswith("write a note"):
            return True

        # Match lock workstation
        if "lock pc" in cmd or "lock computer" in cmd or "lock my screen" in cmd or "lock workstation" in cmd:
            return True

        return False

    def execute(self, command: str, **kwargs) -> SkillResult:
        cmd = command.strip().lower()

        # 1. Application Launching
        for app_name, exe in self.ALLOWED_APPS.items():
            if f"open {app_name}" in cmd or f"launch {app_name}" in cmd:
                success = self._runner(exe)
                if success:
                    return SkillResult(
                        success=True,
                        message=f"Opening {app_name.title()}, sir.",
                        data={"app": app_name, "exe": exe}
                    )
                return SkillResult(
                    success=False,
                    message=f"I was unable to launch {app_name.title()}."
                )

        # 2. Volume Controls
        if "volume up" in cmd or "increase volume" in cmd:
            _send_volume_key(VK_VOLUME_UP, times=5)
            return SkillResult(success=True, message="Volume increased.")

        if "volume down" in cmd or "decrease volume" in cmd:
            _send_volume_key(VK_VOLUME_DOWN, times=5)
            return SkillResult(success=True, message="Volume decreased.")

        if "mute" in cmd or "unmute" in cmd:
            _send_volume_key(VK_VOLUME_MUTE, times=1)
            return SkillResult(success=True, message="Volume toggled.")

        # 3. System Metrics & Telemetry
        if "battery" in cmd:
            try:
                import psutil
                battery = psutil.sensors_battery()
                if battery:
                    status = "plugged in" if battery.power_plugged else "on battery"
                    return SkillResult(
                        success=True,
                        message=f"Battery is at {battery.percent:.0f}%, currently {status}.",
                        data={"percent": battery.percent, "plugged": battery.power_plugged}
                    )
                return SkillResult(success=True, message="No battery detected. This system appears to be running on direct AC power.")
            except Exception as e:
                return SkillResult(success=False, message=f"Unable to read battery status: {e}")

        if any(w in cmd for w in ["system info", "system status", "cpu", "ram", "memory usage"]):
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=0.1)
                ram = psutil.virtual_memory().percent
                os_info = f"{platform.system()} {platform.release()}"
                return SkillResult(
                    success=True,
                    message=f"System status: CPU utilization is at {cpu:.0f}%, RAM usage is at {ram:.0f}%, running {os_info}.",
                    data={"cpu": cpu, "ram": ram, "os": os_info}
                )
            except Exception as e:
                return SkillResult(success=False, message=f"Unable to read system metrics: {e}")

        # 4. Date and Time
        if any(w in cmd for w in ["time", "what time", "current time"]):
            now_str = datetime.now().strftime("%I:%M %p")
            return SkillResult(success=True, message=f"The time is currently {now_str}, sir.")

        if any(w in cmd for w in ["date", "today's date", "current date"]):
            date_str = datetime.now().strftime("%A, %B %d, %Y")
            return SkillResult(success=True, message=f"Today is {date_str}.")

        # 5. Folder Shortcuts
        if "downloads" in cmd:
            downloads_path = Path.home() / "Downloads"
            self._runner(f"explorer.exe {downloads_path}")
            return SkillResult(success=True, message="Opening your Downloads folder, sir.")

        if "documents" in cmd:
            docs_path = Path.home() / "Documents"
            self._runner(f"explorer.exe {docs_path}")
            return SkillResult(success=True, message="Opening your Documents folder, sir.")

        if "notes folder" in cmd or "open notes" in cmd:
            self.notes_dir.mkdir(parents=True, exist_ok=True)
            self._runner(f"explorer.exe {self.notes_dir}")
            return SkillResult(success=True, message="Opening your JARVIS Notes folder.")

        # 6. Create Note
        if any(cmd.startswith(prefix) for prefix in ["take a note", "create a note", "write a note"]):
            note_content = ""
            for prefix in ["take a note that ", "take a note: ", "take a note ", "create a note that ", "create a note: ", "create a note ", "write a note that ", "write a note "]:
                if cmd.startswith(prefix):
                    note_content = command[len(prefix):].strip()
                    break

            if not note_content:
                return SkillResult(success=False, message="Please specify what you would like me to note down.")

            try:
                self.notes_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                note_file = self.notes_dir / f"note_{timestamp}.txt"
                note_file.write_text(f"Recorded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{note_content}\n", encoding="utf-8")
                return SkillResult(
                    success=True,
                    message=f"Note saved successfully: '{note_content[:50]}...'",
                    data={"path": str(note_file), "content": note_content}
                )
            except Exception as e:
                return SkillResult(success=False, message=f"Failed to save note: {e}")

        # 7. Lock PC
        if any(w in cmd for w in ["lock pc", "lock computer", "lock my screen", "lock workstation"]):
            try:
                ctypes.windll.user32.LockWorkStation()
                return SkillResult(success=True, message="Locking workstation now, sir.")
            except Exception as e:
                return SkillResult(success=False, message=f"Unable to lock workstation: {e}")

        return SkillResult(success=False, message="Desktop action not recognized or permitted.")
