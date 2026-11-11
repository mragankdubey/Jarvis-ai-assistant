# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for J.A.R.V.I.S. Windows Desktop Application (ONEDIR).
Bundles PySide6 HUD, local openWakeWord ONNX models, ONNX Runtime binaries,
custom Arc Reactor icon assets, and required Windows/AI hidden imports.
Excludes .env secrets, tests, virtual environments, and bloated unused Qt modules.
"""

import importlib.util
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

PROJECT_DIR = Path(SPECPATH).resolve()

datas = [
    (str(PROJECT_DIR / "assets" / "icons" / "jarvis.ico"), "assets/icons"),
    (str(PROJECT_DIR / "assets" / "icons" / "jarvis.png"), "assets/icons"),
    (str(PROJECT_DIR / ".env.example"), "."),
]

# SSL root certificates for Groq / Gemini / NewsAPI / SpeechRecognition
datas += collect_data_files("certifi")

# Collect required openWakeWord ONNX models cleanly
oww_spec = importlib.util.find_spec("openwakeword")
if oww_spec and oww_spec.origin:
    oww_models_dir = Path(oww_spec.origin).parent / "resources" / "models"
    required_onnx = [
        "hey_jarvis_v0.1.onnx",
        "embedding_model.onnx",
        "melspectrogram.onnx",
        "silero_vad.onnx",
    ]
    for model_file in required_onnx:
        candidate = oww_models_dir / model_file
        if candidate.exists():
            datas.append((str(candidate), "openwakeword/resources/models"))

# Collect ONNX Runtime dynamic libraries
binaries = collect_dynamic_libs("onnxruntime")

hiddenimports = [
    "pyttsx3.drivers",
    "pyttsx3.drivers.sapi5",
    "win32api",
    "win32com",
    "win32com.client",
    "pythoncom",
    "pywintypes",
    "comtypes",
    "comtypes.stream",
    "comtypes.client",
    "speech_recognition",
    "pyaudio",
    "openwakeword",
    "openwakeword.model",
    "openwakeword.utils",
    "openwakeword.vad",
    "onnxruntime",
    "psutil",
    "dotenv",
    "sqlite3",
    "google.genai",
    "google.genai.types",
    "truststore",
]
hiddenimports += collect_submodules("comtypes.gen")

# Exclude heavy unused packages and dev/test artifacts
excludes = [
    "tkinter",
    "_tkinter",
    "matplotlib",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.QtQml",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtDesigner",
    "PySide6.QtTest",
]

a = Analysis(
    [str(PROJECT_DIR / "main.py")],
    pathex=[str(PROJECT_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="JARVIS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_DIR / "assets" / "icons" / "jarvis.ico"),
    version=str(PROJECT_DIR / "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="JARVIS",
)
