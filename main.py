"""
J.A.R.V.I.S. (Just A Rather Very Intelligent System)
Main Application Entry Point - Phase 5 (Distributable Windows Application)

Launches the futuristic Iron Man-inspired PySide6 desktop application with
persistent %LOCALAPPDATA%\\JARVIS storage, rotating secret-safe logging,
cinematic startup diagnostics, multi-screen navigation, and voice intelligence.
"""

import logging
import os
import sys

# Ensure project root is in sys.path and is working directory for non-frozen launcher
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.paths import is_frozen
if not is_frozen() and os.getcwd() != PROJECT_ROOT:
    try:
        os.chdir(PROJECT_ROOT)
    except Exception:
        pass

from core.logging_config import setup_logging

# Initialize secret-masked logging & guard None stdio in --windowed builds
logger = setup_logging()

from core.assistant import Assistant
from core.config import get_config
from core.paths import is_frozen
from database.models import JarvisRepository
from voice.text_to_speech import shutdown as shutdown_tts


def run_gui(smoke_test: bool = False) -> int:
    """Launch the PySide6 Stark Industries HUD Application."""
    if smoke_test:
        os.environ.setdefault("QT_QPA_PLATFORM", "windows")

    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import QApplication
    from interface.icon_generator import get_app_icon
    from interface.main_window import MainWindow

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setApplicationName("J.A.R.V.I.S.")
    app.setOrganizationName("Stark Industries OS")
    app.setWindowIcon(get_app_icon())

    config = get_config()
    repo = JarvisRepository()
    assistant = Assistant(config=config, repo=repo)

    if not smoke_test:
        assistant.start(voice_enabled=True)

    window = MainWindow(assistant=assistant, repo=repo)
    if smoke_test:
        window.setAttribute(Qt.WA_DontShowOnScreen, True)
    window.show()

    if smoke_test:
        def _finish_smoke():
            for key in ("dashboard", "chat", "memory", "notes", "reminders", "system", "settings"):
                window.switch_screen(key, animate=False)
            window._full_exit()

        QTimer.singleShot(2500, _finish_smoke)

    exit_code = app.exec()

    assistant.stop()
    shutdown_tts()
    logger.info("J.A.R.V.I.S. exited cleanly (code=%s).", exit_code)
    return exit_code


def run_cli() -> None:
    """Fallback interactive terminal mode."""
    config = get_config()
    repo = JarvisRepository()
    assistant = Assistant(config=config, repo=repo)
    assistant.start(voice_enabled=False)

    print("=" * 60)
    print("        J.A.R.V.I.S. - Just A Rather Very Intelligent System")
    print("                    Terminal Interactive Mode")
    print("=" * 60)
    print(f"User:           {config.user_name}")
    summary = config.status_summary()
    print(f"AI Provider:    {summary['AI Provider']}")
    print(f"Data Folder:    {summary['User Data Dir']}")
    print(f"Wake Word:      {config.wake_word_model} (Local ONNX)")
    print("=" * 60)
    print("Type any command, question, or 'exit' to quit.")
    print("=" * 60)

    try:
        while True:
            try:
                user_input = input("\nJARVIS > ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                assistant.process_text_command("goodbye")
                break

            response = assistant.process_text_command(user_input)
            print(f"\n[Response]: {response}")

    except KeyboardInterrupt:
        print("\nShutdown signal received.")
    finally:
        assistant.stop()
        shutdown_tts()
        print("J.A.R.V.I.S. offline.")


def main() -> None:
    """Entry point dispatcher."""
    logger.info("Starting J.A.R.V.I.S. (frozen=%s)", is_frozen())

    if "--smoke-test" in sys.argv:
        sys.exit(run_gui(smoke_test=True))

    if "--cli" in sys.argv or "--terminal" in sys.argv or "--no-gui" in sys.argv:
        if is_frozen() and sys.stdin is None:
            logger.warning("--cli requested without attached console; launching GUI instead.")
        else:
            run_cli()
            return

    try:
        sys.exit(run_gui())
    except Exception as e:
        logger.exception("GUI launch failed: %s", e)
        if not is_frozen() and sys.stdin is not None:
            print(f"GUI launch failed or display unavailable ({e}). Falling back to Terminal mode...")
            run_cli()
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
