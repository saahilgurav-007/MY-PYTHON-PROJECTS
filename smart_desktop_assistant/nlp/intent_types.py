"""Intent types and classifications for Smart Desktop Assistant."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any

class RiskLevel(Enum):
    """Risk severity level for user commands."""
    READ_ONLY = "read_only"       # Info queries, stats, weather, wiki
    SAFE_WRITE = "safe_write"     # Folder organization, screenshot, app launch, routine save
    DESTRUCTIVE = "destructive"   # File deletion, killing processes, lock/shutdown


@dataclass
class IntentResult:
    """Encapsulates the parsed intent and extracted parameters."""
    intent: "IntentType"
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    risk_level: RiskLevel = RiskLevel.READ_ONLY

    @property
    def is_destructive(self) -> bool:
        return self.risk_level == RiskLevel.DESTRUCTIVE


class IntentType(str, Enum):
    """Supported user intent categories."""
    # File Automation
    ORGANIZE_FILES = "organize_files"
    SEARCH_FILES = "search_files"
    BATCH_RENAME = "batch_rename"
    CLEANUP_TEMP = "cleanup_temp"

    # System & Hardware Automation
    SYSTEM_STATS = "system_stats"
    LIST_PROCESSES = "list_processes"
    KILL_PROCESS = "kill_process"
    TAKE_SCREENSHOT = "take_screenshot"
    LOCK_WORKSTATION = "lock_workstation"
    CLIPBOARD_GET = "clipboard_get"
    CLIPBOARD_SET = "clipboard_set"

    # Application & Web
    LAUNCH_APP = "launch_app"
    OPEN_URL = "open_url"

    # External APIs
    WEATHER_QUERY = "weather_query"
    WIKI_SUMMARY = "wiki_summary"
    NETWORK_DIAGNOSTICS = "network_diagnostics"
    CURRENCY_CONVERT = "currency_convert"

    # Routines & Scheduling
    CREATE_ROUTINE = "create_routine"
    RUN_ROUTINE = "run_routine"
    LIST_ROUTINES = "list_routines"
    SET_REMINDER = "set_reminder"

    # Meta
    HELP = "help"
    EXIT = "exit"
    UNKNOWN = "unknown"


INTENT_RISK_MAP = {
    IntentType.ORGANIZE_FILES: RiskLevel.SAFE_WRITE,
    IntentType.SEARCH_FILES: RiskLevel.READ_ONLY,
    IntentType.BATCH_RENAME: RiskLevel.SAFE_WRITE,
    IntentType.CLEANUP_TEMP: RiskLevel.DESTRUCTIVE,

    IntentType.SYSTEM_STATS: RiskLevel.READ_ONLY,
    IntentType.LIST_PROCESSES: RiskLevel.READ_ONLY,
    IntentType.KILL_PROCESS: RiskLevel.DESTRUCTIVE,
    IntentType.TAKE_SCREENSHOT: RiskLevel.SAFE_WRITE,
    IntentType.LOCK_WORKSTATION: RiskLevel.DESTRUCTIVE,
    IntentType.CLIPBOARD_GET: RiskLevel.READ_ONLY,
    IntentType.CLIPBOARD_SET: RiskLevel.SAFE_WRITE,

    IntentType.LAUNCH_APP: RiskLevel.SAFE_WRITE,
    IntentType.OPEN_URL: RiskLevel.SAFE_WRITE,

    IntentType.WEATHER_QUERY: RiskLevel.READ_ONLY,
    IntentType.WIKI_SUMMARY: RiskLevel.READ_ONLY,
    IntentType.NETWORK_DIAGNOSTICS: RiskLevel.READ_ONLY,
    IntentType.CURRENCY_CONVERT: RiskLevel.READ_ONLY,

    IntentType.CREATE_ROUTINE: RiskLevel.SAFE_WRITE,
    IntentType.RUN_ROUTINE: RiskLevel.SAFE_WRITE,
    IntentType.LIST_ROUTINES: RiskLevel.READ_ONLY,
    IntentType.SET_REMINDER: RiskLevel.SAFE_WRITE,

    IntentType.HELP: RiskLevel.READ_ONLY,
    IntentType.EXIT: RiskLevel.READ_ONLY,
    IntentType.UNKNOWN: RiskLevel.READ_ONLY,
}
