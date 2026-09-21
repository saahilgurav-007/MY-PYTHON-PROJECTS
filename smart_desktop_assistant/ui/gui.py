"""Modern Dark-Themed Desktop GUI for Smart Desktop Assistant using Tkinter."""

import sys
import threading
import time
from datetime import datetime
from typing import Optional
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from ..core.dispatcher import CommandDispatcher, ExecutionResult
from ..automation.system_ops import SystemOperations
from ..automation.routines import RoutineManager

# Catppuccin Mocha / Modern Dark Palette
BG_COLOR = "#181825"
SURFACE_COLOR = "#1e1e2e"
CARD_COLOR = "#313244"
TEXT_COLOR = "#cdd6f4"
TEXT_MUTED = "#a6adc8"
ACCENT_BLUE = "#89b4fa"
ACCENT_GREEN = "#a6e3a1"
ACCENT_YELLOW = "#f9e2af"
ACCENT_RED = "#f38ba8"
FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica"

class SmartAssistantGUI:
    """Desktop Application Interface for Smart Desktop Assistant."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Smart Desktop Assistant")
        self.root.geometry("960x700")
        self.root.minsize(800, 600)
        self.root.configure(bg=BG_COLOR)

        self.dispatcher = CommandDispatcher(confirmation_callback=self._confirm_dialog)
        self.routine_manager = RoutineManager()

        self._setup_styles()
        self._build_header()
        self._build_stats_panel()
        self._build_input_section()
        self._build_notebook()

        # Initial metrics load
        self.refresh_metrics()

    def _setup_styles(self) -> None:
        """Configures ttk widget styles."""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure(".", background=BG_COLOR, foreground=TEXT_COLOR, font=(FONT_FAMILY, 10))
        self.style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=CARD_COLOR, foreground=TEXT_COLOR, padding=[16, 8], font=(FONT_FAMILY, 10, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", SURFACE_COLOR)], foreground=[("selected", ACCENT_BLUE)])

    def _build_header(self) -> None:
        """Builds top status and branding bar."""
        header_frame = tk.Frame(self.root, bg=BG_COLOR, pady=10, padx=20)
        header_frame.pack(fill="x")

        title_lbl = tk.Label(
            header_frame,
            text="🤖 Smart Desktop Assistant",
            font=(FONT_FAMILY, 18, "bold"),
            bg=BG_COLOR,
            fg=ACCENT_BLUE
        )
        title_lbl.pack(side="left")

        status_lbl = tk.Label(
            header_frame,
            text="🟢 Engine Ready • Offline NLP & Automation",
            font=(FONT_FAMILY, 9),
            bg=BG_COLOR,
            fg=ACCENT_GREEN
        )
        status_lbl.pack(side="right")

    def _build_stats_panel(self) -> None:
        """Displays real-time hardware status cards."""
        stats_frame = tk.Frame(self.root, bg=BG_COLOR, padx=20, pady=5)
        stats_frame.pack(fill="x")

        self.cards = {}
        metrics = [
            ("cpu", "⚡ CPU Usage", "0%"),
            ("ram", "🧠 Memory (RAM)", "0 GB / 0 GB"),
            ("disk", "💾 Disk Space", "0 GB Free")
        ]

        for idx, (key, title, default_val) in enumerate(metrics):
            card = tk.Frame(stats_frame, bg=CARD_COLOR, padx=15, pady=10, relief="flat", bd=0)
            card.pack(side="left", fill="both", expand=True, padx=(0 if idx == 0 else 10, 0))

            t_lbl = tk.Label(card, text=title, font=(FONT_FAMILY, 9), bg=CARD_COLOR, fg=TEXT_MUTED)
            t_lbl.pack(anchor="w")

            v_lbl = tk.Label(card, text=default_val, font=(FONT_FAMILY, 13, "bold"), bg=CARD_COLOR, fg=TEXT_COLOR)
            v_lbl.pack(anchor="w", pady=(4, 0))

            self.cards[key] = v_lbl

        refresh_btn = tk.Button(
            stats_frame,
            text="🔄 Refresh",
            bg=CARD_COLOR,
            fg=TEXT_COLOR,
            activebackground=SURFACE_COLOR,
            activeforeground=ACCENT_BLUE,
            relief="flat",
            padx=10,
            command=self.refresh_metrics,
            cursor="hand2"
        )
        refresh_btn.pack(side="right", padx=(10, 0), fill="y")

    def _build_input_section(self) -> None:
        """Builds natural language command entry bar and quick action buttons."""
        input_container = tk.Frame(self.root, bg=BG_COLOR, padx=20, pady=10)
        input_container.pack(fill="x")

        # Quick action chips
        chips_frame = tk.Frame(input_container, bg=BG_COLOR)
        chips_frame.pack(fill="x", pady=(0, 10))

        quick_actions = [
            ("📁 Organize Downloads", "organize my downloads folder"),
            ("⚡ Morning Setup", "run morning routine"),
            ("🧹 Clean Temp Files", "clean temporary files"),
            ("📸 Screenshot", "take a screenshot"),
            ("🌦️ Weather (Delhi)", "what is the weather in Delhi"),
            ("🩺 System Health", "check system performance")
        ]

        for label, cmd in quick_actions:
            btn = tk.Button(
                chips_frame,
                text=label,
                bg=CARD_COLOR,
                fg=TEXT_COLOR,
                activebackground=ACCENT_BLUE,
                activeforeground=BG_COLOR,
                font=(FONT_FAMILY, 8),
                relief="flat",
                padx=8,
                pady=4,
                cursor="hand2",
                command=lambda c=cmd: self._set_and_run(c)
            )
            btn.pack(side="left", padx=(0, 6))

        # Command input bar
        entry_row = tk.Frame(input_container, bg=SURFACE_COLOR, padx=10, pady=6)
        entry_row.pack(fill="x")

        self.cmd_entry = tk.Entry(
            entry_row,
            font=(FONT_FAMILY, 12),
            bg=SURFACE_COLOR,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="flat",
            bd=0
        )
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=(5, 10))
        self.cmd_entry.bind("<Return>", lambda e: self.on_execute(dry_run=False))
        self.cmd_entry.focus()

        # Action Buttons
        self.dry_btn = tk.Button(
            entry_row,
            text="🔍 Dry Run",
            bg=CARD_COLOR,
            fg=ACCENT_YELLOW,
            activebackground=ACCENT_YELLOW,
            activeforeground=BG_COLOR,
            font=(FONT_FAMILY, 10, "bold"),
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=lambda: self.on_execute(dry_run=True)
        )
        self.dry_btn.pack(side="left", padx=(0, 8))

        self.run_btn = tk.Button(
            entry_row,
            text="▶ Execute",
            bg=ACCENT_BLUE,
            fg=BG_COLOR,
            activebackground=ACCENT_GREEN,
            activeforeground=BG_COLOR,
            font=(FONT_FAMILY, 10, "bold"),
            relief="flat",
            padx=16,
            pady=4,
            cursor="hand2",
            command=lambda: self.on_execute(dry_run=False)
        )
        self.run_btn.pack(side="left")

    def _build_notebook(self) -> None:
        """Builds tabs for activity log and routine manager."""
        notebook_frame = tk.Frame(self.root, bg=BG_COLOR, padx=20, pady=5)
        notebook_frame.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Execution Activity Log
        log_frame = tk.Frame(self.notebook, bg=SURFACE_COLOR)
        self.notebook.add(log_frame, text=" 📜 Execution Log ")

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            bg=SURFACE_COLOR,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            font=("Consolas", 10),
            relief="flat",
            bd=0,
            padx=12,
            pady=12
        )
        self.log_text.pack(fill="both", expand=True)

        # Configure color tags
        self.log_text.tag_config("SUCCESS", foreground=ACCENT_GREEN)
        self.log_text.tag_config("DRY_RUN", foreground=ACCENT_YELLOW)
        self.log_text.tag_config("ERROR", foreground=ACCENT_RED)
        self.log_text.tag_config("INFO", foreground=ACCENT_BLUE)
        self.log_text.tag_config("MUTED", foreground=TEXT_MUTED)

        self._append_log("INFO", "Ready. Enter a command above or click any quick action.\n")

        # Tab 2: Routine Automation Manager
        self.routines_tab = tk.Frame(self.notebook, bg=SURFACE_COLOR, padx=15, pady=15)
        self.notebook.add(self.routines_tab, text=" ⚡ Routine Workflows ")
        self._build_routines_tab()

    def _build_routines_tab(self) -> None:
        """Constructs the visual routine workflows management panel."""
        for widget in self.routines_tab.winfo_children():
            widget.destroy()

        routines = self.routine_manager.get_all_routines()

        top_bar = tk.Frame(self.routines_tab, bg=SURFACE_COLOR)
        top_bar.pack(fill="x", pady=(0, 10))

        lbl = tk.Label(
            top_bar,
            text="Automated Multi-Step Routines (Macros)",
            font=(FONT_FAMILY, 12, "bold"),
            bg=SURFACE_COLOR,
            fg=TEXT_COLOR
        )
        lbl.pack(side="left")

        # Routines List
        for r_name, r_meta in routines.items():
            r_card = tk.Frame(self.routines_tab, bg=CARD_COLOR, padx=12, pady=10)
            r_card.pack(fill="x", pady=5)

            left_box = tk.Frame(r_card, bg=CARD_COLOR)
            left_box.pack(side="left", fill="x", expand=True)

            name_lbl = tk.Label(left_box, text=f"⚡ {r_name}", font=(FONT_FAMILY, 11, "bold"), bg=CARD_COLOR, fg=ACCENT_BLUE)
            name_lbl.pack(anchor="w")

            desc_lbl = tk.Label(left_box, text=r_meta.get("description", ""), font=(FONT_FAMILY, 9), bg=CARD_COLOR, fg=TEXT_MUTED)
            desc_lbl.pack(anchor="w", pady=(2, 4))

            steps = r_meta.get("steps", [])
            steps_preview = " ➜ ".join(steps[:3]) + ("..." if len(steps) > 3 else "")
            steps_lbl = tk.Label(left_box, text=f"Steps ({len(steps)}): {steps_preview}", font=("Consolas", 8), bg=CARD_COLOR, fg=TEXT_COLOR)
            steps_lbl.pack(anchor="w")

            run_btn = tk.Button(
                r_card,
                text="Run Routine",
                bg=ACCENT_GREEN,
                fg=BG_COLOR,
                font=(FONT_FAMILY, 9, "bold"),
                relief="flat",
                padx=10,
                pady=4,
                cursor="hand2",
                command=lambda n=r_name: self._set_and_run(f"run routine {n}")
            )
            run_btn.pack(side="right", padx=5)

    def _set_and_run(self, cmd: str) -> None:
        """Sets entry text and executes immediately."""
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, cmd)
        self.on_execute(dry_run=False)

    def on_execute(self, dry_run: bool = False) -> None:
        """Handles command dispatch in a separate thread to prevent UI freezing."""
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return

        self.run_btn.config(state="disabled")
        self.dry_btn.config(state="disabled")

        def _worker():
            try:
                res = self.dispatcher.dispatch(cmd, dry_run=dry_run)
                self.root.after(0, self._render_result, res)
            except Exception as e:
                self.root.after(0, self._append_log, "ERROR", f"Execution error: {str(e)}\n")
            finally:
                self.root.after(0, lambda: self.run_btn.config(state="normal"))
                self.root.after(0, lambda: self.dry_btn.config(state="normal"))

        threading.Thread(target=_worker, daemon=True).start()

    def _render_result(self, res: ExecutionResult) -> None:
        """Appends formatted execution result to log text."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        tag = "DRY_RUN" if res.dry_run else ("SUCCESS" if res.success else "ERROR")
        icon = "🔍 [DRY RUN]" if res.dry_run else ("✅" if res.success else "❌")

        header = f"[{timestamp}] {icon} {res.command}\n"
        meta = f"  Intent: {res.intent.value} | Confidence: {res.confidence:.2f} | Time: {res.duration_ms:.0f}ms\n"
        body = f"{res.message}\n" + ("─" * 60) + "\n"

        self._append_log(tag, header)
        self._append_log("MUTED", meta)
        self._append_log("TEXT", body)

        # Switch to log tab
        self.notebook.select(0)
        self.refresh_metrics()

    def _append_log(self, tag: str, text: str) -> None:
        """Appends tagged text to scrolled text area."""
        self.log_text.insert(tk.END, text, tag if tag in ["SUCCESS", "DRY_RUN", "ERROR", "INFO", "MUTED"] else ())
        self.log_text.see(tk.END)

    def refresh_metrics(self) -> None:
        """Fetches latest system stats in background."""
        def _fetch():
            stats = SystemOperations.get_system_stats()
            cpu = f"{stats.get('cpu_percent', 0)}%"
            ram = stats.get("ram", {})
            ram_txt = f"{ram.get('used_gb', 0)} GB / {ram.get('total_gb', 0)} GB ({ram.get('percent_used', 0)}%)"
            disk = stats.get("disk", {})
            disk_txt = f"{disk.get('free_gb', 0)} GB Free ({disk.get('percent_used', 0)}% Used)"

            self.root.after(0, lambda: self.cards["cpu"].config(text=cpu))
            self.root.after(0, lambda: self.cards["ram"].config(text=ram_txt))
            self.root.after(0, lambda: self.cards["disk"].config(text=disk_txt))

        threading.Thread(target=_fetch, daemon=True).start()

    def _confirm_dialog(self, message: str) -> bool:
        """Shows GUI confirmation dialog for destructive actions."""
        return messagebox.askyesno("Safety Confirmation", f"{message}\n\nDo you want to proceed?")


def run_gui(check_only: bool = False) -> None:
    """Launches the Tkinter Desktop GUI.
    If check_only is True, verifies instantiation and closes immediately without blocking.
    """
    root = tk.Tk()
    app = SmartAssistantGUI(root)
    if check_only:
        root.update_idletasks()
        root.destroy()
        return
    root.mainloop()
