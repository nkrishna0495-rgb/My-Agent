"""
ui.py — Rich terminal UI components for BizClippy.

Provides a UI class built on top of the rich library for beautiful terminal
output including tables, panels, progress bars, spinners, and interactive prompts.
"""

from __future__ import annotations

import contextlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from rich.align import Align
from rich.bar import Bar
from rich.columns import Columns
from rich.console import Console, RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
)
from rich.rule import Rule
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

if TYPE_CHECKING:
    from bizclippy.storage import Goal, Task

# ── ASCII Art ────────────────────────────────────────────────────────────────

BIZCLIPPY_BANNER = r"""
 ____  _       ____ _               _
| __ )(_)_ __ / ___| | __ _ _ __ __| |
|  _ \| | '__| |   | |/ _` | '__/ _` |
| |_) | | |  | |___| | (_| | | | (_| |
|____/|_|_|   \____|_|\__,_|_|  \__,_|
           Your AI Business Assistant
"""

CLIPPY_ASCII = r"""
     __
    /  \   (^‿^)
    |  |   /    Hey there!
    @  @   |
    || ||
    || ||
    |\_/|
    \___/
"""


class SpinnerContext:
    """Context manager wrapper for rich spinners."""

    def __init__(self, console: Console, message: str) -> None:
        self.console = console
        self.message = message
        self.live: Optional[Live] = None
        self.spinner = Spinner("dots", text=Text(message, style="bold blue"))

    def __enter__(self) -> "SpinnerContext":
        self.live = Live(
            self.spinner,
            console=self.console,
            refresh_per_second=12,
            transient=True,
        )
        self.live.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.live is not None:
            self.live.__exit__(exc_type, exc_val, exc_tb)


class UI:
    """Rich terminal UI components for BizClippy.

    Usage::

        ui = UI()
        ui.show_welcome("Acme Corp")
        ui.show_success("Goal created!")
        name = ui.prompt("What's your name?")
    """

    def __init__(self, console: Optional[Console] = None) -> None:
        self.console = console or Console()

    # ── Display helpers ──────────────────────────────────────────────────────

    def show_welcome(self, business_name: str) -> None:
        """Display a big banner with BizClippy ASCII art and welcome message."""
        banner = Text(BIZCLIPPY_BANNER, style="bold bright_cyan", justify="center")
        clippy = Text(CLIPPY_ASCII, style="yellow", justify="center")

        welcome_text = Text()
        welcome_text.append(f"\n  Welcome, ", style="white")
        welcome_text.append(f"{business_name}", style="bold bright_green")
        welcome_text.append("! \n", style="white")
        welcome_text.append("  Let's build something amazing together.\n", style="dim")

        content = RenderableType.__class__( 0 )  # type-check placeholder
        # Build the layout manually using simple concatenation
        self.console.print()
        self.console.print(banner)
        self.console.print(clippy)
        self.console.print(welcome_text, justify="center")
        self.print_divider()

    def show_clippy_message(self, message: str, style: str = "blue") -> None:
        """Display a message in a styled panel with a BizClippy header."""
        header = Text("🖇️  BizClippy", style=f"bold {style}")
        panel = Panel(
            Text(message, style="default"),
            title=header,
            border_style=style,
            padding=(1, 2),
            expand=False,
        )
        self.console.print(panel)

    def show_error(self, message: str) -> None:
        """Display an error message in a red panel."""
        panel = Panel(
            Text(f"✖  {message}", style="bold red"),
            title=Text("Error", style="bold white on red"),
            border_style="red",
            padding=(1, 2),
        )
        self.console.print(panel)

    def show_success(self, message: str) -> None:
        """Display a success message in a green panel."""
        panel = Panel(
            Text(f"✔  {message}", style="bold green"),
            title=Text("Success", style="bold white on green"),
            border_style="green",
            padding=(1, 2),
        )
        self.console.print(panel)

    def show_info(self, message: str) -> None:
        """Display an informational message in a blue panel."""
        panel = Panel(
            Text(message, style="default"),
            title=Text("Info", style="bold white on blue"),
            border_style="blue",
            padding=(1, 2),
        )
        self.console.print(panel)

    def print_divider(self) -> None:
        """Print a decorative horizontal line."""
        self.console.print(Rule(style="dim cyan"))

    # ── Tables ───────────────────────────────────────────────────────────────

    def show_goals_table(self, goals: List[Dict[str, Any]]) -> None:
        """Display a rich table of goals.

        Columns: Title, Description, Status, Deadline, Progress
        """
        if not goals:
            self.show_info("No goals found. Create one with 'bizclippy add-goal'!")
            return

        table = Table(
            title="📋  Business Goals",
            title_style="bold bright_cyan",
            show_header=True,
            header_style="bold bright_white on dark_blue",
            row_styles=["none", "dim"],
            border_style="bright_black",
            padding=(0, 1),
            expand=True,
        )
        table.add_column("Title", style="bold bright_yellow", min_width=15)
        table.add_column("Description", style="white", min_width=25, max_width=40)
        table.add_column("Status", style="bold", min_width=10, justify="center")
        table.add_column("Deadline", style="bright_cyan", min_width=12)
        table.add_column("Progress", min_width=20)

        for goal in goals:
            status = goal.get("status", "unknown")
            status_style = {
                "active": "[bold bright_green]● active[/bold bright_green]",
                "completed": "[bold bright_blue]✔ completed[/bold bright_blue]",
                "abandoned": "[bold bright_red]✖ abandoned[/bold bright_red]",
            }.get(status, f"[bold]{status}[/bold]")

            progress = goal.get("progress", 0)
            bar = self._render_progress_bar(progress)

            table.add_row(
                goal.get("title", "—"),
                self._truncate(goal.get("description", ""), 40),
                status_style,
                goal.get("deadline") or "—",
                bar,
            )

        self.console.print(table)

    def show_tasks_table(self, tasks: List[Dict[str, Any]]) -> None:
        """Display a rich table of tasks.

        Columns: Title, Priority, Status, Due Date, Goal
        """
        if not tasks:
            self.show_info("No tasks found. Create one with 'bizclippy add-task'!")
            return

        table = Table(
            title="✅  Tasks",
            title_style="bold bright_green",
            show_header=True,
            header_style="bold bright_white on dark_green",
            row_styles=["none", "dim"],
            border_style="bright_black",
            padding=(0, 1),
            expand=True,
        )
        table.add_column("Title", style="bold bright_white", min_width=15)
        table.add_column("Priority", style="bold", min_width=10, justify="center")
        table.add_column("Status", style="bold", min_width=12, justify="center")
        table.add_column("Due Date", style="bright_cyan", min_width=12)
        table.add_column("Goal", style="dim", min_width=12)

        for task in tasks:
            priority = task.get("priority", "medium")
            priority_style = {
                "low": "[dim white]● low[/dim white]",
                "medium": "[bold yellow]● medium[/bold yellow]",
                "high": "[bold bright_red]● high[/bold bright_red]",
                "urgent": "[bold white on red] 🚨 urgent [/bold white on red]",
            }.get(priority, f"[bold]{priority}[/bold]")

            status = task.get("status", "todo")
            status_style = {
                "todo": "[white]○ todo[/white]",
                "in_progress": "[bold yellow]⟳ in progress[/bold yellow]",
                "done": "[bold green]✔ done[/bold green]",
            }.get(status, f"[bold]{status}[/bold]")

            table.add_row(
                task.get("title", "—"),
                priority_style,
                status_style,
                task.get("due_date") or "—",
                task.get("goal_title") or task.get("goal_id") or "—",
            )

        self.console.print(table)

    # ── Dashboard ────────────────────────────────────────────────────────────

    def show_dashboard(self, stats: Dict[str, Any]) -> None:
        """Display a beautiful dashboard with business statistics.

        Expected stats keys:
            total_goals, active_goals, completed_tasks, pending_tasks,
            overdue_tasks, completion_rate (0-100)
        """
        self.print_divider()
        self.console.print(Align("📊  Business Dashboard", align="center", style="bold bright_cyan underline"))
        self.print_divider()

        # Top metrics grid
        metrics = [
            ("🎯 Total Goals", str(stats.get("total_goals", 0)), "bright_yellow"),
            ("⚡ Active Goals", str(stats.get("active_goals", 0)), "bright_green"),
            ("✅ Completed Tasks", str(stats.get("completed_tasks", 0)), "bright_blue"),
            ("📌 Pending Tasks", str(stats.get("pending_tasks", 0)), "bright_magenta"),
            ("⏰ Overdue Tasks", str(stats.get("overdue_tasks", 0)), "bright_red"),
            ("📈 Completion Rate", f"{stats.get('completion_rate', 0):.1f}%", "bright_cyan"),
        ]

        metric_panels = []
        for label, value, color in metrics:
            panel = Panel(
                Align(Text(value, style=f"bold {color}"), align="center"),
                title=Text(label, style=f"bold {color}"),
                border_style=color,
                padding=(1, 2),
            )
            metric_panels.append(panel)

        self.console.print(Columns(metric_panels, equal=True, expand=True))

        # Completion rate progress bar
        self.console.print()
        self.show_progress_bar("Overall Completion Rate", stats.get("completion_rate", 0))

        # Active goals mini table
        active_goals = stats.get("active_goals_list", [])
        if active_goals:
            self.console.print()
            self.print_divider()
            active_table = Table(
                title="⚡ Active Goal Progress",
                title_style="bold bright_green",
                show_header=True,
                header_style="bold",
                border_style="bright_black",
                padding=(0, 1),
            )
            active_table.add_column("Goal", style="bold bright_yellow", min_width=20)
            active_table.add_column("Progress", min_width=25)
            active_table.add_column("Deadline", style="bright_cyan", min_width=12)

            for goal in active_goals:
                progress = goal.get("progress", 0)
                bar = self._render_progress_bar(progress)
                active_table.add_row(
                    goal.get("title", "—"),
                    bar,
                    goal.get("deadline") or "—",
                )
            self.console.print(active_table)

        # Upcoming tasks
        upcoming_tasks = stats.get("upcoming_tasks", [])
        if upcoming_tasks:
            self.console.print()
            self.print_divider()
            upcoming_table = Table(
                title="📌 Upcoming Tasks",
                title_style="bold bright_magenta",
                show_header=True,
                header_style="bold",
                border_style="bright_black",
                padding=(0, 1),
            )
            upcoming_table.add_column("Task", style="bold bright_white", min_width=20)
            upcoming_table.add_column("Due", style="bright_cyan", min_width=15)
            upcoming_table.add_column("Priority", min_width=10)

            for task in upcoming_tasks:
                priority = task.get("priority", "medium")
                priority_style = {
                    "low": "[dim]● low[/dim]",
                    "medium": "[yellow]● medium[/yellow]",
                    "high": "[bright_red]● high[/bright_red]",
                    "urgent": "[white on red]urgent[/white on red]",
                }.get(priority, priority)

                upcoming_table.add_row(
                    task.get("title", "—"),
                    task.get("due_date") or "—",
                    priority_style,
                )
            self.console.print(upcoming_table)

        self.print_divider()
        self.console.print()

    # ── Progress bar ─────────────────────────────────────────────────────────

    def show_progress_bar(self, label: str, percent: float) -> None:
        """Display a labeled progress bar.

        Args:
            label: The label shown to the left of the bar.
            percent: Completion percentage (0–100).
        """
        clamped = max(0, min(100, percent))
        progress = Progress(
            TextColumn(f"[bold]{label:<25}"),
            BarColumn(bar_width=40, complete_style="bright_green", finished_style="green"),
            TextColumn(f"[bold bright_cyan]{clamped:.1f}%[/bold bright_cyan]"),
            console=self.console,
            expand=False,
        )
        task_id = progress.add_task(label, total=100, completed=clamped)
        self.console.print(progress.get_renderable())

    # ── Interactive prompts ──────────────────────────────────────────────────

    def prompt(self, message: str, default: Optional[str] = None) -> str:
        """Display a styled input prompt and return the user's input.

        Args:
            message: The prompt text to display.
            default: Optional default value shown in brackets.

        Returns:
            The user's input as a string (empty string if no input given).
        """
        prompt_text = f"[bold bright_yellow]?[/bold bright_yellow] {message}"
        if default is not None:
            prompt_text += f" [dim]({default})[/dim]"
        prompt_text += ": "

        self.console.print(prompt_text, end="")
        value = input().strip()
        if not value and default is not None:
            return default
        return value

    def confirm(self, message: str) -> bool:
        """Ask the user a yes/no question.

        Args:
            message: The confirmation question.

        Returns:
            True if the user answered yes, False otherwise.
        """
        prompt_text = f"[bold bright_yellow]?[/bold bright_yellow] {message} [dim](y/N)[/dim]: "
        self.console.print(prompt_text, end="")
        answer = input().strip().lower()
        return answer in ("y", "yes", "yeah", "yep")

    def select(self, message: str, choices: List[str]) -> str:
        """Display a numbered selection menu.

        Args:
            message: The prompt shown above the choices.
            choices: List of option strings.

        Returns:
            The selected choice string.
        """
        self.console.print(f"[bold bright_cyan]{message}[/bold bright_cyan]")
        for idx, choice in enumerate(choices, start=1):
            self.console.print(f"  [bold bright_yellow]{idx})[/bold bright_yellow] {choice}")

        while True:
            self.console.print("[bold bright_yellow]\n?[/bold bright_yellow] Select [dim](number)[/dim]: ", end="")
            answer = input().strip()
            try:
                selected = int(answer)
                if 1 <= selected <= len(choices):
                    return choices[selected - 1]
                else:
                    self.show_error(f"Please enter a number between 1 and {len(choices)}.")
            except ValueError:
                self.show_error("Please enter a valid number.")

    # ── Spinner ──────────────────────────────────────────────────────────────

    def show_spinner(self, message: str) -> SpinnerContext:
        """Return a context manager that shows an animated loading spinner.

        Usage::

            with ui.show_spinner("Thinking..."):
                do_slow_work()
        """
        return SpinnerContext(self.console, message)

    # ── Help ─────────────────────────────────────────────────────────────────

    def show_help(self) -> None:
        """Display help text with all available commands."""
        help_text = """
[bold bright_cyan]BizClippy[/bold bright_cyan] — Your AI Business Assistant
[dim]Version 1.0.0[/dim]

[bold bright_yellow]Usage:[/bold bright_yellow]
  bizclippy [COMMAND] [OPTIONS]

[bold bright_green]Commands:[/bold bright_green]
  [bold]init[/bold]              First-time setup — configure API key and business profile
  [bold]chat[/bold]              Interactive chat session with BizClippy
  [bold]dashboard[/bold]         Show business dashboard with stats and progress
  [bold]goals[/bold]             List all business goals
  [bold]tasks[/bold]             List all tasks
  [bold]add-goal[/bold]          Add a new business goal (interactive)
  [bold]add-task[/bold]          Add a new task (interactive)
  [bold]complete-task[/bold]     Mark a task as completed (interactive)
  [bold]plan[/bold]              Generate a business plan using AI
  [bold]suggest[/bold]           Get AI suggestions for your goals and tasks
  [bold]status[/bold]            Show detailed status report with goal progress
  [bold]profile[/bold]           Display current business profile
  [bold]edit-profile[/bold]      Edit business profile (interactive)
  [bold]config[/bold]            Show current configuration
  [bold]help[/bold]              Show this help message

[bold bright_magenta]Examples:[/bold bright_magenta]
  bizclippy init                  # Run first-time setup
  bizclippy chat                  # Start chatting with BizClippy
  bizclippy dashboard             # View your business dashboard
  bizclippy goals --status active  # Filter goals by status
  bizclippy tasks --goal abc123    # Filter tasks by goal

[bold bright_yellow]Tips:[/bold bright_yellow]
  • Type 'quit' or 'exit' during chat to return to the shell.
  • Use --help after any command for more options.
  • Set BIZCLIPPY_API_KEY environment variable to skip API key prompt.
        """
        panel = Panel(
            Text.from_markup(help_text),
            title=Text("🖇️  BizClippy Help", style="bold bright_cyan"),
            border_style="bright_cyan",
            padding=(1, 2),
        )
        self.console.print(panel)

    # ── Internal helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _render_progress_bar(percent: float) -> str:
        """Return a progress bar string suitable for embedding in a table cell."""
        clamped = max(0, min(100, percent))
        filled = int(clamped / 100 * 20)
        empty = 20 - filled
        bar = "█" * filled + "░" * empty
        if clamped >= 100:
            color = "bright_green"
        elif clamped >= 50:
            color = "bright_yellow"
        else:
            color = "bright_red"
        return f"[{color}]{bar}[/{color}] [bold bright_cyan]{clamped:.0f}%[/bold bright_cyan]"

    @staticmethod
    def _truncate(text: str, max_length: int) -> str:
        """Truncate text with ellipsis if it exceeds max_length."""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."
