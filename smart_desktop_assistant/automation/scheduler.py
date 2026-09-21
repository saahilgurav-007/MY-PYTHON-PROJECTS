"""Scheduler and reminder timer daemon."""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable

class Scheduler:
    """Manages asynchronous timed reminders and scheduled alerts."""

    def __init__(self):
        self.active_reminders: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def set_reminder(
        self,
        seconds: int,
        message: str,
        callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Schedules a non-blocking reminder alert."""
        due_time = datetime.now() + timedelta(seconds=seconds)
        reminder_id = f"rem_{int(time.time())}_{len(self.active_reminders)}"

        reminder_entry = {
            "id": reminder_id,
            "message": message,
            "seconds": seconds,
            "due_at": due_time.strftime("%H:%M:%S"),
            "status": "pending"
        }

        with self._lock:
            self.active_reminders.append(reminder_entry)

        def _timer_worker():
            time.sleep(seconds)
            with self._lock:
                reminder_entry["status"] = "triggered"

            # Alert notification
            self._trigger_alert(message)

            if callback:
                try:
                    callback(f"[REMINDER ALERT] {message}")
                except Exception:
                    pass

        t = threading.Thread(target=_timer_worker, daemon=True)
        t.start()

        return {
            "success": True,
            "id": reminder_id,
            "seconds": seconds,
            "due_at": reminder_entry["due_at"],
            "message": f"Reminder set for '{message}' in {seconds} seconds (at {reminder_entry['due_at']})."
        }

    def _trigger_alert(self, message: str) -> None:
        """Plays Windows chime and prints notification."""
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass
        print(f"\n🔔 [REMINDER ALERT] {message}\n", flush=True)

    def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """Returns currently pending reminders."""
        with self._lock:
            return [r for r in self.active_reminders if r["status"] == "pending"]
