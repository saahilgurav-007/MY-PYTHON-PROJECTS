"""Entity extraction module for natural language computer commands."""

import re
from pathlib import Path
from typing import Dict, Any, Optional
from ..config import DOWNLOADS_DIR, DESKTOP_DIR, DOCUMENTS_DIR, APP_REGISTRY

class EntityExtractor:
    """Extracts operational slots and parameters from natural language inputs."""

    @staticmethod
    def extract(text: str) -> Dict[str, Any]:
        """Extract all potential entities from the command string."""
        entities: Dict[str, Any] = {}
        cleaned = text.strip()

        # 1. Target Directory
        entities["directory"] = EntityExtractor.extract_directory(cleaned)

        # 2. Application Name
        entities["app_name"] = EntityExtractor.extract_app_name(cleaned)

        # 3. URL
        entities["url"] = EntityExtractor.extract_url(cleaned)

        # 4. Location / City (for Weather)
        entities["location"] = EntityExtractor.extract_location(cleaned)

        # 5. Wikipedia Query Topic
        entities["wiki_topic"] = EntityExtractor.extract_wiki_topic(cleaned)

        # 6. File Extension
        entities["extension"] = EntityExtractor.extract_extension(cleaned)

        # 7. Time duration (seconds) and Reminder message
        duration, message = EntityExtractor.extract_reminder(cleaned)
        if duration is not None:
            entities["duration_seconds"] = duration
            entities["reminder_message"] = message

        # 8. Process Target (name or PID)
        entities["process_target"] = EntityExtractor.extract_process_target(cleaned)

        # 9. Currency Conversion (amount, from, to)
        currency_info = EntityExtractor.extract_currency(cleaned)
        if currency_info:
            entities.update(currency_info)

        # 10. Routine Name
        entities["routine_name"] = EntityExtractor.extract_routine_name(cleaned)

        # 11. Search pattern / query
        entities["search_query"] = EntityExtractor.extract_search_query(cleaned)

        return entities

    @staticmethod
    def extract_directory(text: str) -> Optional[Path]:
        """Identifies target directory from known aliases or explicit paths."""
        lower = text.lower()
        if "downloads" in lower or "download" in lower:
            return DOWNLOADS_DIR
        if "desktop" in lower:
            return DESKTOP_DIR
        if "documents" in lower or "document" in lower:
            return DOCUMENTS_DIR

        # Check for quoted paths or absolute path patterns (e.g. C:\... or C:/...)
        path_match = re.search(r'["\']([a-zA-Z]:[\\/][^"\']+)["\']|([a-zA-Z]:[\\/][^\s]+)', text)
        if path_match:
            raw_path = path_match.group(1) or path_match.group(2)
            p = Path(raw_path)
            if p.exists():
                return p
        return None

    @staticmethod
    def extract_app_name(text: str) -> Optional[str]:
        """Extracts recognizable application names."""
        lower = text.lower()
        for app in sorted(APP_REGISTRY.keys(), key=len, reverse=True):
            # Check whole word match
            pattern = rf"\b{re.escape(app)}\b"
            if re.search(pattern, lower):
                return app
        return None

    @staticmethod
    def extract_url(text: str) -> Optional[str]:
        """Extracts web URLs or domain references."""
        # Full URL with schema
        match = re.search(r"https?://[^\s]+", text)
        if match:
            return match.group(0)

        # Domain shorthand like google.com, github.com
        match = re.search(r"\b([a-zA-Z0-9-]+\.(?:com|org|net|io|edu|gov|co|in|dev|ai))\b(?:/[^\s]*)?", text, re.IGNORECASE)
        if match:
            url_str = match.group(0)
            return f"https://{url_str}"
        return None

    @staticmethod
    def extract_location(text: str) -> Optional[str]:
        """Extracts location for weather queries (e.g. 'weather in Mumbai')."""
        match = re.search(r"(?:weather|temperature|forecast|raining)\s+(?:in|for|at|around)?\s*([A-Za-z\s]+?)(?:\s+right\s+now|\s+today|\s*\?|$)", text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Filter out non-location words
            if candidate.lower() not in {"my area", "here", "the world", "outside", ""}:
                return candidate.title()

        # Fallback check: "Tokyo weather"
        match = re.search(r"([A-Za-z]+)\s+weather", text, re.IGNORECASE)
        if match:
            return match.group(1).title()
        return None

    @staticmethod
    def extract_wiki_topic(text: str) -> Optional[str]:
        """Extracts subject for Wikipedia queries."""
        match = re.search(r"(?:summarize|tell me about|who was|who is|what is|wiki(?:pedia)?(?: article for| search)?)\s+([A-Za-z0-9\s]+?)(?:\s+on\s+wikipedia|\s*\?|$)", text, re.IGNORECASE)
        if match:
            topic = match.group(1).strip()
            # Clean noise words
            topic = re.sub(r"^(wikipedia|wiki|the|about)\s+", "", topic, flags=re.IGNORECASE)
            if topic:
                return topic
        return None

    @staticmethod
    def extract_extension(text: str) -> Optional[str]:
        """Extracts file extension (e.g. '.pdf' or 'pdf')."""
        match = re.search(r"\.([a-zA-Z0-9]{1,5})\b", text)
        if match:
            return f".{match.group(1).lower()}"
        match = re.search(r"\b([a-zA-Z0-9]{2,4})\s+files\b", text, re.IGNORECASE)
        if match:
            ext = match.group(1).lower()
            if ext not in {"all", "any", "some", "the", "few"}:
                return f".{ext}"
        return None

    @staticmethod
    def extract_reminder(text: str) -> tuple[Optional[int], Optional[str]]:
        """Extracts reminder duration in seconds and the message body."""
        match = re.search(r"(?:remind me(?:\s+to)?|alert me(?:\s+to)?|timer for)\s+(.+?)\s+in\s+(\d+)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)", text, re.IGNORECASE)
        if match:
            msg = match.group(1).strip()
            amount = int(match.group(2))
            unit = match.group(3).lower()
            multiplier = 1
            if "min" in unit:
                multiplier = 60
            elif "hour" in unit or "hr" in unit:
                multiplier = 3600
            return amount * multiplier, msg

        # Pattern 2: "timer for 5 minutes" or "remind me in 10 minutes to drink water"
        match = re.search(r"(?:in|for)\s+(\d+)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)(?:\s+to\s+(.+))?", text, re.IGNORECASE)
        if match:
            amount = int(match.group(1))
            unit = match.group(2).lower()
            msg = match.group(3).strip() if match.group(3) else "Timer finished!"
            multiplier = 1
            if "min" in unit:
                multiplier = 60
            elif "hour" in unit or "hr" in unit:
                multiplier = 3600
            return amount * multiplier, msg

        return None, None

    @staticmethod
    def extract_process_target(text: str) -> Optional[str]:
        """Extracts target process name or PID from kill/close command."""
        match = re.search(r"(?:kill|terminate|stop|close|end task)\s+(?:process\s+|pid\s+)?([a-zA-Z0-9_\-\.]+)", text, re.IGNORECASE)
        if match:
            target = match.group(1).strip()
            if target.lower() not in {"a", "the", "process", "app", "task", "program"}:
                return target
        return None

    @staticmethod
    def extract_currency(text: str) -> Optional[Dict[str, Any]]:
        """Extracts currency conversion parameters."""
        match = re.search(r"(?:convert\s+)?([\d\.]+)\s*([A-Za-z]{3})\s+(?:to|in|into)\s+([A-Za-z]{3})", text, re.IGNORECASE)
        if match:
            return {
                "amount": float(match.group(1)),
                "from_currency": match.group(2).upper(),
                "to_currency": match.group(3).upper()
            }
        match = re.search(r"exchange rate\s+([A-Za-z]{3})\s+(?:to|against|for)\s+([A-Za-z]{3})", text, re.IGNORECASE)
        if match:
            return {
                "amount": 1.0,
                "from_currency": match.group(1).upper(),
                "to_currency": match.group(2).upper()
            }
        return None

    @staticmethod
    def extract_routine_name(text: str) -> Optional[str]:
        """Extracts routine identifier."""
        match = re.search(r"(?:routine|workflow|macro)\s+([a-zA-Z0-9_\-]+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # Common aliases
        if "morning" in text.lower():
            return "morning_setup"
        if "dev" in text.lower() or "developer" in text.lower():
            return "dev_session"
        if "clean" in text.lower() and "workspace" in text.lower():
            return "clean_workspace"
        return None

    @staticmethod
    def extract_search_query(text: str) -> Optional[str]:
        """Extracts search keyword for file searches."""
        match = re.search(r"(?:named|called|matching|query|for)\s+[\"']?([a-zA-Z0-9_\-\.\*]+)[\"']?", text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if candidate.lower() not in {"files", "file", "all", "the", "in", "with"}:
                return candidate
        return None
