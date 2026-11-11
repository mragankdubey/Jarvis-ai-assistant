# J.A.R.V.I.S. (Just A Rather Very Intelligent System)

An Iron Man-inspired futuristic Windows desktop AI assistant built in Python and PySide6, featuring a Stark Industries Arc Reactor HUD, local offline wake-word activation, multi-turn conversational intelligence (Groq & Google Gemini), asynchronous text-to-speech, and allowlisted desktop automation.

---

## 🚀 Key Features

* **Futuristic PySide6 HUD Interface:**
  * **Cinematic Startup Sequence:** Powers up the Arc Reactor while running real, non-fabricated subsystem probes (config, SQLite DB, audio hardware, ONNX wake-word, and AI uplink).
  * **Reimagined 6-Layer Arc Reactor:** Custom vector `QPainter` core with rotating shroud arcs, degree azimuth ticks, counter-rotating orbital rings, expanding pulse waves, and smooth color/speed transitions across all 8 states.
  * **Holographic Multi-Ribbon Waveform:** Layered harmonic oscilloscope responding to live microphone RMS levels and speech synthesis while staying strictly honest about microphone availability.
  * **7 Dedicated Command Screens:** Seamless animated navigation across `DASHBOARD`, `AI CONVERSATION`, `MEMORY`, `NOTES`, `REMINDERS`, `SYSTEM STATUS` (with live rolling CPU/RAM sparklines), and `SETTINGS`.
  * **SQLite Local Persistence:** Stores conversation logs, long-term memory facts, notes, scheduled reminders, and user settings locally in `database/jarvis.db`.
  * **Custom Multi-Resolution Identity:** Original Arc Reactor emblem (`assets/icons/jarvis.ico`) shared across taskbar, window chrome, and system tray.
* **Dual AI Brain (Groq & Google Gemini):**
  * Pluggable provider abstraction with automatic failover.
  * High-speed voice turnarounds using Groq (Llama / GPT-OSS models) and Google Gemini 2.5 Flash.
  * Configurable JARVIS persona: intelligent, professional, concise, subtly witty, and natural.
  * In-memory sliding-window conversational context for natural follow-up dialogue.
* **Local Offline Wake-Word Detection:**
  * Powered by `openWakeWord` with pre-trained ONNX models (`hey_jarvis`).
  * 100% offline, zero-latency CPU inference.
  * **Zero cloud streaming during idle:** Ambient room audio is never sent to third-party servers while waiting.
* **Continuous Multi-Turn Voice Conversations:**
  * Say *"Hey Jarvis"* once to activate.
  * Speak back-to-back commands and queries without repeating the wake word before every sentence.
  * Hands-free deactivation via sleep phrases (*"Go to sleep"*, *"Stop listening"*, *"Deactivate"*) or automatic silence timeouts.
* **Safe Desktop Automation:**
  * Allowlisted application launching (Notepad, Calculator, File Explorer, Command Prompt, PowerShell, Settings, Task Manager).
  * Native Windows media controls (Volume Up, Volume Down, Mute/Unmute).
  * System telemetry (battery percentage, CPU/RAM usage, OS details).
  * Current date and time reporting.
  * Safe note recording in dedicated `~/JARVIS_Notes` directory.
  * Workstation locking upon explicit request.
  * Strictly forbids arbitrary AI shell execution, `eval`, or unsanitized script running.
* **Asynchronous Audio Pipeline:**
  * Persistent worker thread for Windows SAPI5 `pyttsx3` text-to-speech engine.
  * Queued speech output that never freezes or lags the desktop GUI.
  * Decoupled microphone access preventing audio device competition.

---

## 📋 System Prerequisites

* **Operating System:** Windows 10 or Windows 11 (64-bit)
* **Python Version:** Python 3.12 (64-bit recommended)
* **Audio Hardware:** Working microphone and speakers / headphones

---

## 🛠️ Installation & Setup

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

4. **Configure environment credentials:**
   Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
   Edit `.env` and fill in your API credentials:
   ```env
   # NewsAPI (https://newsapi.org/)
   NEWS_API_KEY=your_news_api_key_here

   # Groq API (https://console.groq.com/)
   GROQ_API_KEY=your_groq_api_key_here

   # Google Gemini API (https://aistudio.google.com/)
   GEMINI_API_KEY=your_gemini_api_key_here

   # AI Provider Selection: 'auto', 'groq', or 'gemini'
   AI_PROVIDER=auto

   # Assistant Identity (Optional)
   JARVIS_USER_NAME=Mragank
   JARVIS_VOICE_RATE=180
   JARVIS_VOICE_VOLUME=1.0
   JARVIS_INACTIVITY_TIMEOUT=10.0
   ```

---

## 🎮 Launching J.A.R.V.I.S.

### 1. Launch Futuristic Desktop HUD (Recommended)
```powershell
.\.venv\Scripts\python.exe main.py
```
* Displays the Iron Man Arc Reactor HUD window.
* Automatically initializes the local wake-word listener and system tray icon.
* Click the **MIC** button or say *"Hey Jarvis"* to begin speaking.

### 2. Launch Terminal Interactive Mode (CLI)
```powershell
.\.venv\Scripts\python.exe main.py --cli
```
* Runs the assistant directly in PowerShell or Command Prompt.
* Supports keyboard text interaction and full desktop skill execution.

---

## 🗣️ Voice & Wake-Word Interaction

1. **Wake Phrase:** Say **"Hey Jarvis"** or click the **MIC** button in the HUD.
2. **Activation:** The Arc Reactor flashes bright cyan and JARVIS announces: *"Yes, Mragank?"*
3. **Continuous Conversation:** Issue commands naturally:
   * *User:* *"What is the time right now?"*
   * *JARVIS:* *"The time is currently 09:15 PM, sir."*
   * *User:* *"Open Calculator."*
   * *JARVIS:* *"Opening Calculator, sir."*
   * *User:* *"Who was Nikola Tesla?"*
   * *JARVIS:* *"Nikola Tesla was a Serbian-American engineer and inventor known for developing alternating current electricity..."*
4. **Deactivation:**
   * Say *"Go to sleep"*, *"Stop listening"*, or *"Deactivate"*.
   * Or remain silent for 10 seconds (configurable via `JARVIS_INACTIVITY_TIMEOUT`).

---

## 💻 Supported Desktop Commands

| Category | Voice / Text Triggers | Action Taken |
| :--- | :--- | :--- |
| **Applications** | `open notepad`, `open calculator`, `open file explorer`, `open cmd`, `open powershell`, `open settings`, `open task manager` | Safely launches allowlisted system binaries. |
| **Browser** | `open google`, `open youtube`, `open github`, `open whatsapp` | Opens default web browser to destination. |
| **Media Search** | `play <song/video>`, `search youtube for <query>` | Navigates to YouTube search results. |
| **Volume** | `volume up`, `increase volume`, `volume down`, `decrease volume`, `mute`, `unmute` | Adjusts master Windows audio via virtual key events. |
| **Telemetry** | `system status`, `system info`, `cpu load`, `battery status` | Reads real-time hardware telemetry via `psutil`. |
| **Date & Time** | `what time is it`, `today's date`, `current time` | Reports formatted system date and clock. |
| **Folders** | `open downloads`, `open documents`, `open notes folder` | Opens verified user folder locations. |
| **Notes** | `take a note <content>`, `create a note: <content>` | Saves formatted text file in `~/JARVIS_Notes/`. |
| **Workstation** | `lock pc`, `lock workstation`, `lock my screen` | Locks current Windows user session via `user32.dll`. |
| **News** | `news`, `headlines` | Fetches top business news headlines via NewsAPI. |
| **AI Brain** | Any general question, calculation, reasoning, or coding query | Dispatches to Groq / Gemini with sliding context. |

---

## 🛡️ Privacy & Safety Guardrails

* **Zero Idle Cloud Streaming:** Wake-word detection runs locally using `openWakeWord` ONNX models. No audio leaves your computer during idle standby.
* **No Arbitrary Shell Execution:** The AI brain is strictly decoupled from system command execution. JARVIS never passes raw AI responses to `eval()`, `exec()`, or `subprocess(shell=True)`.
* **Allowlist Enforcement:** Application launching is restricted to verified Windows utilities in `ALLOWED_APPS`.
* **Secret Protection:** API keys in `.env` are masked and never printed to console logs, GUI panels, or serialized representations. `.env` and `.venv/` are strictly ignored in `.gitignore`.
* **Isolated Threading:** Background audio capture and AI network requests run on dedicated worker threads, ensuring the desktop GUI stays fluid at 60 FPS.

---

## 🧪 Running Automated Tests

Run the full 26-test automated suite (no physical microphone or live API keys required; external services are mocked):

```powershell
.\.venv\Scripts\python.exe -m unittest discover tests
```

To run individual test modules:
```powershell
# Phase 2 Core Engine Tests
.\.venv\Scripts\python.exe -m unittest tests/test_phase2.py

# Phase 3 AI, Wake-Word, Desktop & GUI Tests
.\.venv\Scripts\python.exe -m unittest tests/test_phase3.py

# Phase 4 Persistence, Diagnostics, Icons & HUD Screen Tests
.\.venv\Scripts\python.exe -m unittest tests/test_phase4.py
```

---

## ⚠️ Known Limitations

1. **Headless Audio:** On virtualized or cloud Windows environments without an active recording device, microphone calibration falls back to text mode. Physical microphone input activates automatically on standard desktop hardware.
2. **Wake-Word Sensitivity:** Background room acoustics or fan noise can affect wake-word accuracy. You can fine-tune sensitivity in `.env` with `JARVIS_WAKE_THRESHOLD=0.4` (default: 0.5).
