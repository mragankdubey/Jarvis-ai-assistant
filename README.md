# J.A.R.V.I.S. (Just A Rather Very Intelligent System)

An Iron Man-inspired futuristic Windows desktop AI assistant built in Python and PySide6, featuring a Stark Industries Arc Reactor HUD, local offline wake-word activation, multi-turn conversational intelligence (Groq & Google Gemini), asynchronous text-to-speech, SQLite persistence, and allowlisted desktop automation.

---

## 🚀 Key Features & Screens

### Futuristic PySide6 Command Centre
* **Cinematic Startup Sequence:** Powers up the Arc Reactor while running real, non-fabricated subsystem probes (configuration, SQLite DB, audio hardware, ONNX wake-word, and AI uplink).
* **Reimagined 6-Layer Arc Reactor:** Custom vector `QPainter` core with rotating shroud arcs, `0°–360°` azimuth ticks, counter-rotating orbital rings, expanding pulse waves, and smooth color/velocity interpolation across all 8 states (`IDLE`, `ACTIVATING`, `LISTENING`, `PROCESSING`, `SPEAKING`, `SLEEPING`, `ERROR`, `STOPPING`).
* **Holographic Multi-Ribbon Waveform:** Layered harmonic oscilloscope responding to live microphone RMS levels and speech synthesis while staying strictly honest about microphone availability.
* **Custom Multi-Resolution Identity:** Original Arc Reactor emblem (`assets/icons/jarvis.ico`) shared across the executable, taskbar, window chrome, desktop shortcut, and system tray.

### 7 Dedicated HUD Screens
1. **DASHBOARD:** 3-column command centre combining the Arc Reactor, waveform visualizer, subsystem readiness chips, quick directives, recent activity, live CPU/RAM/Battery gauges, next reminder, and compact conversation stream.
2. **AI CONVERSATION:** Full-height chat workspace with animated user & JARVIS bubbles, typing/processing indicator, starter prompts, and dual voice/text bar.
3. **MEMORY:** Inspect, search, add, and delete persistent long-term SQLite facts (`"Remember that..."`), plus inspect/flush the active RAM sliding-window context.
4. **NOTES:** Two-pane searchable notes editor persisted in SQLite and synced to `%LOCALAPPDATA%\JARVIS\notes\`.
5. **REMINDERS:** Schedule, filter, complete, and delete tasks with automatic due-time toast and voice notifications.
6. **SYSTEM STATUS:** Rolling CPU & RAM sparklines, hardware summary, network uplink check, wake-word runtime check, and detected audio devices list.
7. **SETTINGS:** Categorized preferences for AI provider (`auto`, `groq`, `gemini`), voice TTS rate/volume/mute, local wake-word sensitivity, inactivity timeout, startup animation, tray behavior, HUD glow intensity, and user-local API key entry.

### Voice & AI Intelligence
* **Dual AI Brain (Groq & Google Gemini):** High-speed inference using Groq (auto-selecting compatible models like `openai/gpt-oss-120b` / `openai/gpt-oss-20b`) and Google Gemini 2.5 Flash (`google-genai`) with automatic failover.
* **Local Offline Wake-Word Detection:** Powered by `openWakeWord` with pre-trained ONNX models (`hey_jarvis_v0.1.onnx`). Zero audio leaves your machine while `IDLE`.
* **Continuous Multi-Turn Dialogue:** Say *"Hey Jarvis"* once to activate (*"Yes, Mragank?"*), issue consecutive commands without repeating the wake phrase, and deactivate via *"Go to sleep"* or silence timeout.
* **Safe Allowlisted Desktop Automation:** Launches verified Windows utilities (`notepad`, `calc`, `explorer`, `cmd`, `powershell`, `settings`, `taskmgr`), controls master volume, reads system telemetry, saves notes, and locks workstation on explicit demand. Never executes arbitrary AI-generated shell commands or `eval()`.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Language** | Python 3.12 (64-bit) |
| **Desktop GUI** | PySide6 (Qt 6.12) |
| **AI Providers** | Groq API (`requests`) & Google Gemini (`google-genai`) |
| **Wake-Word Engine** | `openWakeWord` + `onnxruntime` (ONNX offline inference) |
| **Speech Recognition** | `SpeechRecognition` + `PyAudio` |
| **Text-to-Speech** | `pyttsx3` (persistent Windows SAPI5 worker thread) |
| **Local Storage** | `sqlite3` (Windows `%LOCALAPPDATA%\JARVIS\`) |
| **Telemetry & Win32** | `psutil`, `pywin32`, `comtypes` |
| **Packaging** | PyInstaller 6 (`--onedir`, `--windowed`) + Inno Setup script |

---

## 💻 Development Setup (Running from Source)

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/your-username/Jarvis-ai-assistant.git
   cd Jarvis-ai-assistant
   ```

2. **Create and activate virtual environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   python -m pip install -r requirements.txt
   ```

4. **Configure API keys:**
   Copy `.env.example` to `.env` in the repo root (or configure inside Settings / `%LOCALAPPDATA%\JARVIS\.env`):
   ```env
   NEWS_API_KEY=your_news_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   AI_PROVIDER=auto
   JARVIS_USER_NAME=Mragank
   ```

5. **Run from source:**
   ```powershell
   # Desktop HUD
   .\.venv\Scripts\python.exe main.py

   # Terminal Interactive Mode
   .\.venv\Scripts\python.exe main.py --cli
   ```

---

## 📦 Building the Windows Application (`JARVIS.exe`)

J.A.R.V.I.S. uses a reliable PyInstaller `--onedir` `--windowed` configuration (`JARVIS.spec`) that bundles PySide6, ONNX Runtime DLLs, the `hey_jarvis` ONNX models, SSL certificates, and the multi-resolution Arc Reactor icon — while excluding `.env` secrets, `.venv`, and test files.

```powershell
# Build dist\JARVIS\JARVIS.exe
cmd /c build_windows.bat
```

### Creating Desktop & Start Menu Shortcuts
Once `dist\JARVIS\JARVIS.exe` is built:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\create_shortcuts.ps1
```
This creates a Windows `.lnk` shortcut on your **Desktop** and **Start Menu** pointing to `dist\JARVIS\JARVIS.exe` with the Arc Reactor icon.

> **Note for Windows 11 Smart App Control:** If your system has Windows Application Control / Smart App Control enabled and blocks the unsigned `JARVIS.exe` (`WinError 4551`), either sign `dist\JARVIS\JARVIS.exe` with a trusted code-signing certificate or create the shortcut using the signed Python Software Foundation `pythonw.exe` windowed launcher:
> ```powershell
> powershell -ExecutionPolicy Bypass -File scripts\create_shortcuts.ps1 -UseSignedLauncher
> ```

### Optional Inno Setup Installer (`installer\JARVIS.iss`)
If you have **Inno Setup 6** (`ISCC.exe`) installed, compile a standard Windows installer wizard:
```powershell
iscc installer\JARVIS.iss
```
The installer places the application in `%LOCALAPPDATA%\Programs\JARVIS` (or Program Files), creates shortcuts, and **preserves** user databases, notes, and `.env` credentials during upgrades and normal uninstalls.

---

## 🗄️ Persistent Data Storage Location

Both packaged (`JARVIS.exe`) and development launches store user data safely outside the installation directory inside:

```text
%LOCALAPPDATA%\JARVIS\
├── database\
│   └── jarvis.db        # Conversations, memory facts, notes, reminders, settings
├── notes\               # Exported plain-text notes
├── logs\
│   └── jarvis.log       # Rotating diagnostic logs (API keys automatically redacted)
├── backups\             # Rolling SQLite backups
├── .env                 # Optional user API credentials for packaged executable
└── .env.example         # Template created automatically on first run
```

**First-Run Setup for Packaged `JARVIS.exe`:**  
Launch `JARVIS.exe`, open **SETTINGS**, enter your Groq / Gemini / NewsAPI keys in the masked **Persistent Storage & API Credentials** fields (or edit `%LOCALAPPDATA%\JARVIS\.env`), and click **SAVE & APPLY SETTINGS**.

---

## 💻 Supported Desktop & Voice Commands

| Category | Voice / Text Triggers | Action Taken |
| :--- | :--- | :--- |
| **Applications** | `open notepad`, `open calculator`, `open file explorer`, `open cmd`, `open powershell`, `open settings`, `open task manager` | Safely launches allowlisted system binaries. |
| **Browser** | `open google`, `open youtube`, `open github`, `open whatsapp` | Opens default web browser to destination. |
| **Media Search** | `play <song/video>`, `search youtube for <query>` | Navigates to YouTube search results. |
| **Volume** | `volume up`, `increase volume`, `volume down`, `decrease volume`, `mute`, `unmute` | Adjusts master Windows audio via virtual key events. |
| **Telemetry** | `system status`, `system info`, `cpu load`, `battery status` | Reads real-time hardware telemetry via `psutil`. |
| **Date & Time** | `what time is it`, `today's date`, `current time` | Reports formatted system date and clock. |
| **Folders** | `open downloads`, `open documents`, `open notes folder` | Opens verified user folder locations. |
| **Notes & Memory** | `take a note <content>`, `remember that <fact>` | Saves notes and persistent long-term memory facts. |
| **Window Control** | `minimize jarvis`, `maximize jarvis`, `hide jarvis`, `show jarvis` | Controls HUD visibility. |
| **Workstation** | `lock pc`, `lock workstation`, `lock my screen` | Locks current Windows user session via `user32.dll`. |
| **News** | `news`, `headlines` | Fetches top business news headlines via NewsAPI. |
| **AI Brain** | Any general question, calculation, reasoning, or coding query | Dispatches to Groq / Gemini with context & memory. |

---

## 🧪 Running Automated Tests

Run the full automated suite (no physical microphone or live API keys required; external services and destructive actions are mocked):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v tests
```

---

## 🔧 Troubleshooting Guide

1. **HUD shows `"MIC: UNAVAILABLE"` / `"No Default Input Device"`:**
   * Check Windows *Settings &rarr; System &rarr; Sound &rarr; Input* and ensure a working microphone is connected and enabled as the default recording device. Text interaction in the HUD remains fully functional without a microphone.
2. **AI Brain responds `"No AI API Keys Configured"` in packaged mode:**
   * Open **SETTINGS &rarr; Persistent Storage & API Credentials**, enter your Groq or Gemini API key, and click **SAVE & APPLY SETTINGS** (or place keys in `%LOCALAPPDATA%\JARVIS\.env`).
3. **Diagnostic logs for packaged app errors:**
   * Check `%LOCALAPPDATA%\JARVIS\logs\jarvis.log`. All API keys and bearer tokens are automatically masked (`[REDACTED]`).
4. **Wake-word sensitivity in noisy rooms:**
   * Adjust the **Detection Threshold** slider in **SETTINGS** (`50%` default; try `35%–45%` for quieter pickup or `60%–70%` to reduce false activations).

---

## ⚠️ Known Limitations

1. **Physical Microphone Verification:** Continuous acoustic wake-word detection (*"Hey Jarvis"*) and live Google Web Speech transcription require a working physical Windows microphone and speaker setup.
2. **Inno Setup Compilation:** `installer\JARVIS.iss` is ready for compilation with Inno Setup 6 (`ISCC.exe`), which must be installed separately if a standalone `.exe` setup wizard is desired alongside the portable `dist\JARVIS\` directory and shortcut script.
