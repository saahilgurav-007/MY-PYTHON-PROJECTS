"""Automated interactive showcase demonstrating full capabilities of Smart Desktop Assistant."""

import time
import shutil
from pathlib import Path
from .core.dispatcher import CommandDispatcher
from .core.audit_logger import AuditLogger
from .config import DATA_DIR

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_header(title: str) -> None:
    print(f"\n{CYAN}{BOLD}{'='*60}{RESET}")
    print(f"{CYAN}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{BOLD}{'='*60}{RESET}\n")

def run_demo() -> None:
    """Executes a realistic end-to-end demonstration."""
    print_header("🤖 SMART DESKTOP ASSISTANT - FEATURE SHOWCASE")
    dispatcher = CommandDispatcher()

    # Scenario 1: System & Hardware Diagnostics
    print_header("1. System Health & Hardware Diagnostics")
    cmd1 = "check system performance"
    print(f"{BOLD}User Command:{RESET} '{GREEN}{cmd1}{RESET}'")
    res1 = dispatcher.dispatch(cmd1)
    print(f"{YELLOW}[Intent: {res1.intent.value} | Confidence: {res1.confidence:.2f}]{RESET}")
    print(f"{res1.message}\n")
    time.sleep(0.5)

    # Scenario 2: Active Process Inspection
    print_header("2. Process Management & Monitoring")
    cmd2 = "list running processes"
    print(f"{BOLD}User Command:{RESET} '{GREEN}{cmd2}{RESET}'")
    res2 = dispatcher.dispatch(cmd2)
    print(f"{YELLOW}[Intent: {res2.intent.value} | Confidence: {res2.confidence:.2f}]{RESET}")
    print(f"{res2.message}\n")
    time.sleep(0.5)

    # Scenario 3: File Automation (Sandbox Directory Organization)
    print_header("3. File Automation: Categorize & Organize Sandbox")
    sandbox_dir = DATA_DIR / "demo_sandbox"
    sandbox_dir.mkdir(parents=True, exist_ok=True)

    # Create mock files
    mock_files = [
        "annual_report.pdf", "quarterly_budget.xlsx", "logo_design.png",
        "family_vacation.jpg", "main_algorithm.py", "backup_archive.zip", "readme_notes.txt"
    ]
    for mf in mock_files:
        (sandbox_dir / mf).write_text("demo content", encoding="utf-8")

    print(f"Created sandbox test directory at: {sandbox_dir}")
    print(f"Initial files in directory: {len(mock_files)}")

    # Command referencing explicit path
    cmd3 = f"organize files in \"{sandbox_dir}\""
    print(f"{BOLD}User Command:{RESET} '{GREEN}{cmd3}{RESET}'")
    res3 = dispatcher.dispatch(cmd3)
    print(f"{YELLOW}[Intent: {res3.intent.value} | Confidence: {res3.confidence:.2f}]{RESET}")
    print(f"{res3.message}")
    if res3.data.get("category_counts"):
        print("Categorized folders:")
        for cat, cnt in res3.data["category_counts"].items():
            print(f"  📁 {cat}/ ({cnt} files)")
    print()
    time.sleep(0.5)

    # Scenario 4: External Web APIs
    print_header("4. Live External APIs (Weather, Wikipedia, Currency)")

    api_commands = [
        "what is the weather in Delhi",
        "summarize Artificial Intelligence on wikipedia",
        "convert 100 USD to INR"
    ]

    for api_cmd in api_commands:
        print(f"{BOLD}User Command:{RESET} '{GREEN}{api_cmd}{RESET}'")
        res = dispatcher.dispatch(api_cmd)
        print(f"{YELLOW}[Intent: {res.intent.value} | Confidence: {res.confidence:.2f}]{RESET}")
        print(f"{res.message}\n")
        time.sleep(0.5)

    # Scenario 5: Safety Guardrails & Dry-Run Mode
    print_header("5. Safety Guardrails & Dry-Run Simulation")
    cmd_destr = "clean temporary files"
    print(f"{BOLD}User Command (with --dry-run):{RESET} '{GREEN}{cmd_destr}{RESET}'")
    res_dry = dispatcher.dispatch(cmd_destr, dry_run=True)
    print(f"{YELLOW}[Intent: {res_dry.intent.value} | Confidence: {res_dry.confidence:.2f} | DRY RUN]{RESET}")
    print(f"{res_dry.message}\n")
    time.sleep(0.5)

    # Scenario 6: Multi-Step Routine Workflow
    print_header("6. Multi-Step Routine Automation (Macro)")
    cmd_routine = "run morning routine"
    print(f"{BOLD}User Command:{RESET} '{GREEN}{cmd_routine}{RESET}'")
    res_routine = dispatcher.dispatch(cmd_routine, dry_run=True)
    print(f"{YELLOW}[Intent: {res_routine.intent.value} | Confidence: {res_routine.confidence:.2f}]{RESET}")
    print(f"{res_routine.message}\n")
    time.sleep(0.5)

    # Scenario 7: Audit Trail
    print_header("7. Persistent Audit Trail & History")
    recent = AuditLogger.get_recent_history(5)
    print(f"Logged {len(recent)} recent events to {AuditLogger.__module__}:")
    for r in recent:
        dry_flag = " [DRY RUN]" if r.get("dry_run") else ""
        print(f"  • [{r['timestamp'][11:19]}] {r['intent']}: '{r['command']}' -> {r['status']}{dry_flag} ({r['duration_ms']}ms)")

    # Cleanup demo sandbox
    try:
        shutil.rmtree(sandbox_dir)
    except Exception:
        pass

    print_header("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY")
    print(f"{GREEN}The Smart Desktop Assistant is fully operational and ready to automate tasks!{RESET}\n")

if __name__ == "__main__":
    run_demo()
