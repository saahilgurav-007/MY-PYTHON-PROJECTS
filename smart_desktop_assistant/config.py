"""Configuration management for Smart Desktop Assistant."""

import os
from pathlib import Path

# Assistant Root Directory
PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent
DATA_DIR = PROJECT_ROOT / "assistant_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Standard User Directories
USER_HOME = Path.home()
DOWNLOADS_DIR = USER_HOME / "Downloads"
DESKTOP_DIR = USER_HOME / "Desktop"
DOCUMENTS_DIR = USER_HOME / "Documents"
PICTURES_DIR = USER_HOME / "Pictures"
SCREENSHOTS_DIR = PICTURES_DIR / "Screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Temporary directory
SYSTEM_TEMP = Path(os.environ.get("TEMP", os.environ.get("TMP", "/tmp")))

# Storage Files
HISTORY_FILE = DATA_DIR / "assistant_history.json"
ROUTINES_FILE = DATA_DIR / "routines.json"
MODEL_CACHE_FILE = DATA_DIR / "intent_model.joblib"

# Categorization rules for File Automation
FILE_CATEGORIES = {
    "Documents": [
        ".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt", ".xlsx", ".xls",
        ".csv", ".pptx", ".ppt", ".epub", ".md"
    ],
    "Images": [
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico",
        ".tiff", ".heic"
    ],
    "Videos": [
        ".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm", ".m4v"
    ],
    "Audio": [
        ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma"
    ],
    "Archives": [
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".iso"
    ],
    "Code": [
        ".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yaml",
        ".yml", ".cpp", ".c", ".h", ".cs", ".java", ".sql", ".sh", ".ps1", ".bat"
    ],
    "Installers": [
        ".exe", ".msi", ".dmg", ".pkg", ".deb"
    ]
}

# Standard Application Launch Shortcuts for Windows
APP_REGISTRY = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "chrome": ["chrome.exe", "google-chrome"],
    "edge": ["msedge.exe"],
    "browser": ["msedge.exe", "chrome.exe"],
    "code": ["code.cmd", "code.exe"],
    "vs code": ["code.cmd", "code.exe"],
    "vscode": ["code.cmd", "code.exe"],
    "explorer": ["explorer.exe"],
    "files": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
    "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
    "powershell": ["powershell.exe"],
    "cmd": ["cmd.exe"],
    "command prompt": ["cmd.exe"],
    "task manager": ["taskmgr.exe"],
    "taskmgr": ["taskmgr.exe"],
    "settings": ["control.exe"],
    "paint": ["mspaint.exe"]
}

# Safety thresholds
SAFETY_SETTINGS = {
    "require_confirmation_for_destructive": True,
    "max_file_delete_batch": 50,
    "max_temp_file_age_days": 1,
}
