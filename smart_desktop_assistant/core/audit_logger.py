"""Audit logger for tracking all natural language actions and executions."""

import json
import time
from datetime import datetime
from typing import Dict, Any, List
from ..config import HISTORY_FILE

class AuditLogger:
    """Records executed actions, parameters, and results to persistent JSON log."""

    @staticmethod
    def log_event(
        raw_text: str,
        intent: str,
        confidence: float,
        status: str,
        execution_time_ms: float,
        details: str,
        dry_run: bool = False
    ) -> None:
        """Appends an execution record to the history file."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "command": raw_text,
            "intent": intent,
            "confidence": confidence,
            "status": status,
            "dry_run": dry_run,
            "duration_ms": round(execution_time_ms, 2),
            "details": details[:300]  # truncate to prevent excessive log bloat
        }

        history: List[Dict[str, Any]] = []
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

        history.append(record)

        # Retain last 200 records
        if len(history) > 200:
            history = history[-200:]

        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def get_recent_history(limit: int = 10) -> List[Dict[str, Any]]:
        """Returns the most recent audit records."""
        if not HISTORY_FILE.exists():
            return []
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
                return history[-limit:]
        except Exception:
            return []
