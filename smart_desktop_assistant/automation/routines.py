"""Routines and macro workflows manager."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from ..config import ROUTINES_FILE

DEFAULT_ROUTINES: Dict[str, Dict[str, Any]] = {
    "morning_setup": {
        "description": "Opens daily news, checks local weather, and reviews system health.",
        "steps": [
            "open website https://news.google.com",
            "what is the weather in Delhi",
            "check system performance"
        ]
    },
    "clean_workspace": {
        "description": "Organizes messy downloads, cleans temp caches, and reports disk stats.",
        "steps": [
            "organize my downloads folder",
            "clean temporary files",
            "check system performance"
        ]
    },
    "dev_session": {
        "description": "Launches developer environment (VS Code & Terminal) and monitors hardware.",
        "steps": [
            "start visual studio code",
            "open terminal console",
            "check system performance"
        ]
    }
}

class RoutineManager:
    """Saves, loads, and executes sequential multi-step desktop workflows."""

    def __init__(self):
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Initializes routines file with defaults if missing."""
        if not ROUTINES_FILE.exists():
            ROUTINES_FILE.parent.mkdir(parents=True, exist_ok=True)
            self._save_routines(DEFAULT_ROUTINES)

    def _load_routines(self) -> Dict[str, Dict[str, Any]]:
        """Loads routines dictionary from JSON file."""
        if not ROUTINES_FILE.exists():
            return DEFAULT_ROUTINES
        try:
            with open(ROUTINES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_ROUTINES

    def _save_routines(self, routines: Dict[str, Dict[str, Any]]) -> bool:
        """Persists routines to JSON file."""
        try:
            with open(ROUTINES_FILE, "w", encoding="utf-8") as f:
                json.dump(routines, f, indent=2)
            return True
        except Exception:
            return False

    def get_all_routines(self) -> Dict[str, Dict[str, Any]]:
        """Returns all configured routines."""
        return self._load_routines()

    def get_routine(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a routine by identifier."""
        routines = self._load_routines()
        norm_name = name.lower().replace(" ", "_")
        return routines.get(norm_name)

    def save_routine(self, name: str, steps: List[str], description: str = "") -> bool:
        """Creates or updates a custom routine."""
        routines = self._load_routines()
        norm_name = name.lower().replace(" ", "_")
        routines[norm_name] = {
            "description": description or f"Custom workflow: {norm_name}",
            "steps": steps
        }
        return self._save_routines(routines)

    def delete_routine(self, name: str) -> bool:
        """Removes a routine by identifier."""
        routines = self._load_routines()
        norm_name = name.lower().replace(" ", "_")
        if norm_name in routines:
            del routines[norm_name]
            return self._save_routines(routines)
        return False
