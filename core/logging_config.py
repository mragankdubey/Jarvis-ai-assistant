"""
Secret-Safe Rotating Logging and Windowed Stream Guard for J.A.R.V.I.S.

Writes diagnostic logs to %LOCALAPPDATA%\\JARVIS\\logs\\jarvis.log,
automatically redacts API credentials/tokens, and ensures sys.stdout/stderr
are non-None when launched as a PyInstaller --windowed executable.
"""

import io
import logging
from logging.handlers import RotatingFileHandler
import re
import sys
from typing import Iterable, Optional
from core.paths import get_logs_dir

_SECRET_PATTERNS = [
    re.compile(r"gsk_[A-Za-z0-9]{10,}"),
    re.compile(r"AIza[A-Za-z0-9_\-]{15,}"),
    re.compile(r"(?i)(apiKey|api_key|token|authorization)=([^&\s\"']+)"),
    re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9_\-\.]{10,}"),
]


class SecretMaskingFilter(logging.Filter):
    """Redacts known API key patterns and active secrets from all log records."""

    def __init__(self, known_secrets: Optional[Iterable[str]] = None):
        super().__init__()
        self._known_secrets = [s for s in (known_secrets or []) if s and len(s) >= 6]

    def set_known_secrets(self, secrets: Iterable[str]) -> None:
        self._known_secrets = [s for s in secrets if s and len(s) >= 6]

    def redact(self, text: str) -> str:
        if not text:
            return text
        masked = text
        for secret in self._known_secrets:
            if secret in masked:
                masked = masked.replace(secret, "[REDACTED]")
        for pat in _SECRET_PATTERNS:
            if pat.groups >= 2:
                masked = pat.sub(r"\1=[REDACTED]", masked)
            elif pat.groups == 1:
                masked = pat.sub(r"\1[REDACTED]", masked)
            else:
                masked = pat.sub("[REDACTED]", masked)
        return masked

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
            redacted = self.redact(msg)
            if redacted != msg:
                record.msg = redacted
                record.args = ()
        except Exception:
            pass
        return True


class _NullSafeStream(io.TextIOBase):
    """Fallback stream when sys.stdout / sys.stderr are None in --windowed mode."""

    def write(self, s: str) -> int:
        return len(s) if s else 0

    def flush(self) -> None:
        pass

    def isatty(self) -> bool:
        return False


_secret_filter = SecretMaskingFilter()
_configured = False


def _unhandled_exception_handler(exc_type, exc_value, exc_traceback):
    """Capture unhandled fatal exceptions to jarvis.log and crash.log."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger = logging.getLogger("CRASH")
    logger.critical("Unhandled fatal exception occurred:", exc_info=(exc_type, exc_value, exc_traceback))

    try:
        import datetime
        import traceback
        crash_log = get_logs_dir() / "crash.log"
        with open(str(crash_log), "a", encoding="utf-8") as f:
            f.write(f"\n--- FATAL CRASH: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    except Exception:
        pass


def install_exception_hook() -> None:
    """Ensure any unhandled exception is logged to file rather than silently dropped."""
    sys.excepthook = _unhandled_exception_handler


def ensure_stdio_safe() -> None:
    """Prevent NoneType stream crashes in PyInstaller --windowed builds and pythonw."""
    if sys.stdout is None:
        sys.stdout = _NullSafeStream()  # type: ignore[assignment]
    if sys.stderr is None:
        sys.stderr = _NullSafeStream()  # type: ignore[assignment]


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure root logger with secret masking, rotating log file, and crash hook."""
    global _configured
    ensure_stdio_safe()
    install_exception_hook()

    root = logging.getLogger()
    if _configured:
        return root

    root.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        log_file = get_logs_dir() / "jarvis.log"
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=2 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(fmt)
        file_handler.addFilter(_secret_filter)
        root.addHandler(file_handler)
    except Exception:
        pass

    # Console handler only if attached to a real console
    if hasattr(sys.stderr, "fileno"):
        try:
            sys.stderr.fileno()
            stream_handler = logging.StreamHandler(sys.stderr)
            stream_handler.setFormatter(fmt)
            stream_handler.addFilter(_secret_filter)
            root.addHandler(stream_handler)
        except Exception:
            pass

    _configured = True
    return root


def register_secrets_for_redaction(*secrets: Optional[str]) -> None:
    """Register runtime API keys with the redaction filter so they never enter logs."""
    _secret_filter.set_known_secrets([s for s in secrets if s])
