"""Interactive command-line interface with ANSI styling and autocomplete."""

import sys
from typing import Optional
from ..core.dispatcher import CommandDispatcher
from ..core.audit_logger import AuditLogger
from ..nlp.intent_types import IntentType

# ANSI Color Codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

BANNER = f"""{CYAN}{BOLD}
╔═══════════════════════════════════════════════════════════════════╗
║               🤖 SMART DESKTOP ASSISTANT v1.0.0                  ║
║      Executes repetitive computer commands from natural language  ║
║             [Automation • APIs • Offline NLP Engine]             ║
╚═══════════════════════════════════════════════════════════════════╝{RESET}
Type any command in plain English (e.g. {GREEN}'organize my downloads'{RESET} or {YELLOW}'what is the weather in Delhi'{RESET}).
Type {BOLD}'help'{RESET} for sample commands or {BOLD}'exit'{RESET} to quit.
"""

def cli_confirm(warning_msg: str) -> bool:
    """Prompts user on console for confirmation of destructive commands."""
    print(f"\n{RED}{BOLD}⚠️  {warning_msg}{RESET}")
    try:
        choice = input(f"{YELLOW}Proceed with execution? (y/N): {RESET}").strip().lower()
        return choice in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        return False


def run_cli(initial_command: Optional[str] = None, dry_run: bool = False, force: bool = False) -> None:
    """Starts the CLI session or executes a single direct command."""
    # Configure UTF-8 output if available
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    dispatcher = CommandDispatcher(confirmation_callback=cli_confirm)

    if initial_command:
        # One-shot direct command execution
        res = dispatcher.dispatch(initial_command, dry_run=dry_run, force=force)
        prefix = f"{YELLOW}[DRY RUN] {RESET}" if res.dry_run else (f"{GREEN}✓ {RESET}" if res.success else f"{RED}✗ {RESET}")
        print(f"\n{prefix}{BOLD}{res.message}{RESET}\n")
        return

    print(BANNER)

    while True:
        try:
            prompt_str = f"{CYAN}{BOLD}assistant>{RESET} "
            user_input = input(prompt_str).strip()

            if not user_input:
                continue

            # Check for dry-run flag at prompt level
            current_dry_run = dry_run
            if user_input.endswith(" --dry-run"):
                current_dry_run = True
                user_input = user_input[:-10].strip()

            if user_input.lower() in ("exit", "quit", "q", ":q"):
                print(f"{CYAN}Goodbye! Assistant shutting down.{RESET}")
                break

            if user_input.lower() == "history":
                records = AuditLogger.get_recent_history(5)
                print(f"\n{BOLD}Recent Activity Log:{RESET}")
                for r in records:
                    print(f"  • [{r['timestamp'][11:19]}] {r['intent']}: {r['command']} ({r['status']})")
                print()
                continue

            res = dispatcher.dispatch(user_input, dry_run=current_dry_run, force=force)

            status_icon = f"{YELLOW}[DRY RUN] {RESET}" if res.dry_run else (f"{GREEN}✓ {RESET}" if res.success else f"{RED}✗ {RESET}")
            intent_tag = f"{CYAN}[{res.intent.value} | conf: {res.confidence:.2f} | {res.duration_ms:.0f}ms]{RESET}"

            print(f"{status_icon}{intent_tag}")
            print(f"{res.message}\n")

            if res.intent == IntentType.EXIT:
                break

        except (KeyboardInterrupt, EOFError):
            print(f"\n{CYAN}Session ended.{RESET}")
            break
        except Exception as e:
            print(f"{RED}Unexpected error: {str(e)}{RESET}")
