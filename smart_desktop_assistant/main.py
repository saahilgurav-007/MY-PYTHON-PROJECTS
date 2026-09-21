"""Main entry point for Smart Desktop Assistant."""

import argparse
import sys
from .ui.cli import run_cli
from .ui.gui import run_gui
from .demo import run_demo

def main():
    parser = argparse.ArgumentParser(
        description="🤖 Smart Desktop Assistant - Natural language computer automation."
    )
    parser.add_argument(
        "command",
        nargs="?",
        default=None,
        help="Optional direct natural language instruction to execute immediately."
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the modern desktop graphical user interface (GUI)."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the automated scenario showcase demonstration."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without modifying files or terminating processes."
    )
    parser.add_argument(
        "--force",
        "-y",
        action="store_true",
        help="Bypass confirmation warnings for destructive operations."
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Verify GUI launch and exit immediately (for automated testing)."
    )

    args = parser.parse_args()

    if args.demo:
        run_demo()
    elif args.gui:
        run_gui(check_only=args.check_only)
    else:
        run_cli(initial_command=args.command, dry_run=args.dry_run, force=args.force)

if __name__ == "__main__":
    main()
