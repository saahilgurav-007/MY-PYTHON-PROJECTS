"""Command dispatcher orchestrating NLP, safety verification, automation, and logging."""

import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, List

from ..nlp.intent_types import IntentType, RiskLevel
from ..nlp.intent_classifier import IntentClassifier, IntentResult
from ..core.safety import SafetyGuard
from ..core.audit_logger import AuditLogger
from ..automation.file_ops import FileOperations
from ..automation.system_ops import SystemOperations
from ..automation.app_ops import AppOperations
from ..automation.routines import RoutineManager
from ..automation.scheduler import Scheduler
from ..apis.weather_api import WeatherAPI
from ..apis.wiki_api import WikipediaAPI
from ..apis.network_api import NetworkAPI
from ..apis.currency_api import CurrencyAPI

@dataclass
class ExecutionResult:
    """Standardized result returned after processing any user instruction."""
    success: bool
    command: str
    intent: IntentType
    confidence: float
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    dry_run: bool = False
    duration_ms: float = 0.0

    def format_output(self) -> str:
        """Returns clean text representation of the result."""
        prefix = "🔍 [DRY RUN] " if self.dry_run else ("✅ " if self.success else "❌ ")
        return f"{prefix}{self.message}"


class CommandDispatcher:
    """Routes parsed natural language commands to target automation engines."""

    def __init__(
        self,
        classifier: Optional[IntentClassifier] = None,
        confirmation_callback: Optional[Callable[[str], bool]] = None
    ):
        self.classifier = classifier or IntentClassifier()
        self.safety = SafetyGuard(confirmation_callback)
        self.routines = RoutineManager()
        self.scheduler = Scheduler()

    def dispatch(
        self,
        command_text: str,
        dry_run: bool = False,
        force: bool = False
    ) -> ExecutionResult:
        """Executes a single natural language instruction."""
        start_time = time.time()
        intent_res = self.classifier.classify(command_text)

        # 1. Safety check
        can_proceed, reason = self.safety.verify_action(intent_res, dry_run=dry_run, force=force)
        if not can_proceed:
            duration = (time.time() - start_time) * 1000
            AuditLogger.log_event(
                raw_text=command_text,
                intent=intent_res.intent.value,
                confidence=intent_res.confidence,
                status="CANCELLED",
                execution_time_ms=duration,
                details=reason,
                dry_run=dry_run
            )
            return ExecutionResult(
                success=False,
                command=command_text,
                intent=intent_res.intent,
                confidence=intent_res.confidence,
                message=f"Action blocked by safety guard: {reason}",
                dry_run=dry_run,
                duration_ms=duration
            )

        # 2. Route by intent
        res = self._execute_intent(intent_res, dry_run=dry_run)
        duration = (time.time() - start_time) * 1000
        res.duration_ms = duration

        # 3. Audit log
        AuditLogger.log_event(
            raw_text=command_text,
            intent=intent_res.intent.value,
            confidence=intent_res.confidence,
            status="SUCCESS" if res.success else "FAILED",
            execution_time_ms=duration,
            details=res.message,
            dry_run=dry_run
        )

        return res

    def _execute_intent(self, res: IntentResult, dry_run: bool = False) -> ExecutionResult:
        """Invokes appropriate handler based on the intent."""
        intent = res.intent
        entities = res.entities
        text = res.raw_text

        # --- File Operations ---
        if intent == IntentType.ORGANIZE_FILES:
            target_dir = entities.get("directory")
            out = FileOperations.organize_directory(target_dir, dry_run=dry_run)
            moved_count = out.get("total_files", 0)
            dir_name = out.get("directory", "target directory")
            mode = "Would organize" if dry_run else "Successfully organized"
            msg = f"{mode} {moved_count} files in '{dir_name}' into category folders."
            return ExecutionResult(
                success=out.get("success", False),
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=msg,
                data=out,
                dry_run=dry_run
            )

        elif intent == IntentType.SEARCH_FILES:
            target_dir = entities.get("directory")
            query = entities.get("search_query") or ""
            ext = entities.get("extension")
            out = FileOperations.search_files(target_dir, query=query, extension=ext)
            count = out.get("total_matches", 0)
            msg = f"Found {count} matching file(s) in {out.get('directory')}."
            return ExecutionResult(
                success=out.get("success", False),
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=msg,
                data=out,
                dry_run=dry_run
            )

        elif intent == IntentType.BATCH_RENAME:
            target_dir = entities.get("directory")
            ext = entities.get("extension")
            out = FileOperations.batch_rename(target_dir, extension=ext, dry_run=dry_run)
            count = out.get("total_renamed", 0)
            msg = f"{'Would rename' if dry_run else 'Renamed'} {count} files in {out.get('directory')}."
            return ExecutionResult(
                success=out.get("success", False),
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=msg,
                data=out,
                dry_run=dry_run
            )

        elif intent == IntentType.CLEANUP_TEMP:
            out = FileOperations.clean_temp_files(dry_run=dry_run)
            return ExecutionResult(
                success=out.get("success", False),
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=out.get("message", "Cleaned temporary files."),
                data=out,
                dry_run=dry_run
            )

        # --- System Operations ---
        elif intent == IntentType.SYSTEM_STATS:
            stats = SystemOperations.get_system_stats()
            cpu = stats.get("cpu_percent", 0)
            ram = stats.get("ram", {})
            disk = stats.get("disk", {})
            msg = (
                f"System Health Summary:\n"
                f"  • CPU Usage: {cpu}%\n"
                f"  • Memory: {ram.get('used_gb', 0)} GB / {ram.get('total_gb', 0)} GB ({ram.get('percent_used', 0)}% used)\n"
                f"  • Disk Space: {disk.get('free_gb', 0)} GB free of {disk.get('total_gb', 0)} GB ({disk.get('percent_used', 0)}% used)"
            )
            return ExecutionResult(
                success=True,
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=msg,
                data=stats,
                dry_run=dry_run
            )

        elif intent == IntentType.LIST_PROCESSES:
            procs = SystemOperations.get_top_processes(count=8)
            proc_lines = [f"  [{p['pid']}] {p['name']}: {p['memory_mb']} MB" for p in procs]
            msg = f"Top Active Processes by Memory:\n" + "\n".join(proc_lines)
            return ExecutionResult(
                success=True,
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=msg,
                data={"processes": procs},
                dry_run=dry_run
            )

        elif intent == IntentType.KILL_PROCESS:
            target = entities.get("process_target") or "notepad"
            out = SystemOperations.kill_process(target, dry_run=dry_run)
            return ExecutionResult(
                success=out.get("success", False),
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=out.get("message", f"Terminated {target}"),
                data=out,
                dry_run=dry_run
            )

        elif intent == IntentType.TAKE_SCREENSHOT:
            out = SystemOperations.capture_screenshot()
            return ExecutionResult(
                success=out.get("success", False),
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=out.get("message", "Screenshot captured"),
                data=out,
                dry_run=dry_run
            )

        elif intent == IntentType.LOCK_WORKSTATION:
            if dry_run:
                msg = "[DRY RUN] Would lock the Windows workstation."
                return ExecutionResult(True, text, intent, res.confidence, msg, dry_run=True)
            out = SystemOperations.lock_workstation()
            return ExecutionResult(
                success=out.get("success", False),
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=out.get("message", "Locked workstation."),
                data=out,
                dry_run=dry_run
            )

        elif intent == IntentType.CLIPBOARD_GET:
            content = SystemOperations.get_clipboard()
            preview = content[:200] + ("..." if len(content) > 200 else "")
            msg = f"Clipboard Content:\n\"{preview}\"" if content else "Clipboard is currently empty."
            return ExecutionResult(
                success=True,
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=msg,
                data={"clipboard_text": content},
                dry_run=dry_run
            )

        elif intent == IntentType.CLIPBOARD_SET:
            # Extract text to set
            copy_match = text
            for prefix in ["copy", "set clipboard to", "store"]:
                if prefix in text.lower():
                    copy_match = text[text.lower().find(prefix) + len(prefix):].strip()
                    break
            success = SystemOperations.set_clipboard(copy_match)
            return ExecutionResult(
                success=success,
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=f"Copied to clipboard: \"{copy_match[:60]}\"",
                data={"copied": copy_match},
                dry_run=dry_run
            )

        # --- Applications & Browser ---
        elif intent == IntentType.LAUNCH_APP:
            app_name = entities.get("app_name") or "notepad"
            if dry_run:
                msg = f"[DRY RUN] Would launch application: {app_name}"
                return ExecutionResult(True, text, intent, res.confidence, msg, dry_run=True)
            out = AppOperations.launch_app(app_name)
            return ExecutionResult(
                success=out.get("success", False),
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=out.get("message", f"Launched {app_name}"),
                data=out,
                dry_run=dry_run
            )

        elif intent == IntentType.OPEN_URL:
            url = entities.get("url") or "https://www.google.com"
            if dry_run:
                msg = f"[DRY RUN] Would open URL: {url}"
                return ExecutionResult(True, text, intent, res.confidence, msg, dry_run=True)
            out = AppOperations.open_url(url)
            return ExecutionResult(
                success=out.get("success", False),
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=out.get("message", f"Opened URL {url}"),
                data=out,
                dry_run=dry_run
            )

        # --- APIs ---
        elif intent == IntentType.WEATHER_QUERY:
            loc = entities.get("location") or "Delhi"
            out = WeatherAPI.get_weather(loc)
            return ExecutionResult(
                success=out.get("success", False),
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=out.get("message", "Fetched weather"),
                data=out,
                dry_run=dry_run
            )

        elif intent == IntentType.WIKI_SUMMARY:
            topic = entities.get("wiki_topic") or text
            out = WikipediaAPI.get_summary(topic)
            return ExecutionResult(
                success=out.get("success", False),
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=out.get("message", "Fetched Wikipedia summary"),
                data=out,
                dry_run=dry_run
            )

        elif intent == IntentType.NETWORK_DIAGNOSTICS:
            out = NetworkAPI.full_diagnostics()
            return ExecutionResult(
                success=out.get("success", False),
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=out.get("message", "Completed network check"),
                data=out,
                dry_run=dry_run
            )

        elif intent == IntentType.CURRENCY_CONVERT:
            amount = entities.get("amount", 100.0)
            from_c = entities.get("from_currency", "USD")
            to_c = entities.get("to_currency", "INR")
            out = CurrencyAPI.convert(amount, from_c, to_c)
            return ExecutionResult(
                success=out.get("success", False),
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=out.get("message", "Currency converted"),
                data=out,
                dry_run=dry_run
            )

        # --- Routines & Scheduling ---
        elif intent == IntentType.CREATE_ROUTINE:
            r_name = entities.get("routine_name") or "custom_routine"
            # Interactive or default sample
            sample_steps = ["check system performance", "what is on my clipboard"]
            saved = self.routines.save_routine(r_name, sample_steps)
            return ExecutionResult(
                success=saved,
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=f"Created routine '{r_name}' with {len(sample_steps)} default steps.",
                data={"routine_name": r_name, "steps": sample_steps},
                dry_run=dry_run
            )

        elif intent == IntentType.RUN_ROUTINE:
            r_name = entities.get("routine_name") or "morning_setup"
            routine = self.routines.get_routine(r_name)
            if not routine:
                return ExecutionResult(
                    success=False,
                    command=text,
                    intent=intent,
                    confidence=res.confidence,
                    message=f"Routine '{r_name}' not found. Use 'list routines' to see options.",
                    dry_run=dry_run
                )

            steps = routine.get("steps", [])
            results = []
            for step in steps:
                sub_res = self.dispatch(step, dry_run=dry_run)
                results.append(sub_res)

            step_summary = "\n".join([f"  Step {i+1}: {r.command} -> {'OK' if r.success else 'FAILED'}" for i, r in enumerate(results)])
            return ExecutionResult(
                success=all(r.success for r in results),
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=f"Executed routine '{r_name}' ({len(steps)} steps):\n{step_summary}",
                data={"routine": r_name, "results": [r.message for r in results]},
                dry_run=dry_run
            )

        elif intent == IntentType.LIST_ROUTINES:
            all_r = self.routines.get_all_routines()
            lines = []
            for name, meta in all_r.items():
                lines.append(f"  • {name}: {meta.get('description')} ({len(meta.get('steps', []))} steps)")
            msg = "Saved Automation Routines:\n" + ("\n".join(lines) if lines else "No routines configured.")
            return ExecutionResult(
                success=True,
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=msg,
                data={"routines": all_r},
                dry_run=dry_run
            )

        elif intent == IntentType.SET_REMINDER:
            secs = entities.get("duration_seconds", 30)
            msg_text = entities.get("reminder_message", "Notification timer alert")
            out = self.scheduler.set_reminder(secs, msg_text)
            return ExecutionResult(
                success=True,
                command=text,
                intent=intent,
                confidence=res.confidence,
                message=out.get("message", f"Reminder scheduled in {secs} seconds."),
                data=out,
                dry_run=dry_run
            )

        elif intent == IntentType.HELP:
            help_text = (
                "🤖 Smart Desktop Assistant - Natural Language Commands:\n\n"
                "📁 File Automation:\n"
                "  • 'organize my downloads folder'\n"
                "  • 'search for files with pdf extension'\n"
                "  • 'clean temporary files'\n\n"
                "⚙️ System & Hardware:\n"
                "  • 'check system performance' (CPU, RAM, Disk)\n"
                "  • 'list running processes'\n"
                "  • 'kill process notepad'\n"
                "  • 'take a screenshot'\n"
                "  • 'what is on my clipboard'\n\n"
                "🚀 Apps & Web:\n"
                "  • 'open notepad', 'launch chrome', 'open calculator'\n"
                "  • 'go to github.com'\n\n"
                "🌐 APIs & Knowledge:\n"
                "  • 'what is the weather in Delhi'\n"
                "  • 'summarize Quantum Computing on wikipedia'\n"
                "  • 'what is my public ip address'\n"
                "  • 'convert 100 USD to INR'\n\n"
                "⚡ Macros & Routines:\n"
                "  • 'run morning routine'\n"
                "  • 'run clean_workspace routine'\n"
                "  • 'remind me to stretch in 15 minutes'\n"
                "  • 'list all routines'"
            )
            return ExecutionResult(True, text, intent, 1.0, help_text, dry_run=dry_run)

        elif intent == IntentType.EXIT:
            return ExecutionResult(True, text, intent, 1.0, "Goodbye! Have a productive day.", dry_run=dry_run)

        else:
            return ExecutionResult(
                success=False,
                command=text,
                intent=IntentType.UNKNOWN,
                confidence=res.confidence,
                message=(
                    f"I couldn't confidently understand '{text}'.\n"
                    f"Type 'help' to see sample commands or try rephrasing."
                ),
                dry_run=dry_run
            )
