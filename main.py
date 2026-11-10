"""
J.A.R.V.I.S. (Just A Rather Very Intelligent System)
Main Application Entry Point - Phase 3 (AI Brain & Futuristic PySide6 HUD)

Launches the futuristic Stark Industries Iron Man HUD desktop interface.
Supports fallback to terminal interactive mode when '--cli' is specified
or in headless environments.
"""

import sys
from core.assistant import Assistant
from core.config import get_config
from voice.text_to_speech import shutdown as shutdown_tts


def run_gui() -> int:
    """Launch the PySide6 Stark Industries HUD Application."""
    from PySide6.QtWidgets import QApplication
    from interface.main_window import MainWindow

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    config = get_config()
    assistant = Assistant(config=config)

    # Start assistant background loop
    assistant.start(voice_enabled=True)

    window = MainWindow(assistant=assistant)
    window.show()

    exit_code = app.exec()

    # Clean shutdown on application exit
    assistant.stop()
    shutdown_tts()
    return exit_code


def run_cli() -> None:
    """Fallback interactive terminal mode."""
    config = get_config()
    assistant = Assistant(config=config)
    assistant.start(voice_enabled=False)

    print("=" * 60)
    print("        J.A.R.V.I.S. - Just A Rather Very Intelligent System")
    print("                    Phase 3 Terminal Mode")
    print("=" * 60)
    print(f"User:           {config.user_name}")
    summary = config.status_summary()
    print(f"AI Provider:    {summary['AI Provider']}")
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
    # Check if CLI mode was explicitly requested
    if "--cli" in sys.argv or "--terminal" in sys.argv or "--no-gui" in sys.argv:
        run_cli()
        return

    # Attempt to launch the PySide6 GUI
    try:
        sys.exit(run_gui())
    except Exception as e:
        print(f"GUI launch failed or display unavailable ({e}). Falling back to Terminal mode...")
        run_cli()


if __name__ == "__main__":
    main()
