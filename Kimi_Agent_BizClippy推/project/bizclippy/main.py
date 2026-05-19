"""
main.py — Click CLI commands for BizClippy.

All commands use rich for output and follow the pattern defined in the spec.
Interactive commands use UI helper methods for prompts.
API calls show the spinner; errors are handled gracefully.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import Optional

import click

from bizclippy.config import Config
from bizclippy.storage import Storage
from bizclippy.api_client import NVIDIAClient
from bizclippy.business_manager import BusinessManager
from bizclippy.ui import UI
from bizclippy.utils import validate_date
from rich.table import Table

ui = UI()

PASSABLE_STATUSES = ["active", "completed", "abandoned"]
TASK_STATUSES = ["todo", "in_progress", "done"]
PRIORITIES = ["low", "medium", "high", "urgent"]


def _ensure_init() -> tuple[Config, Storage, BusinessManager]:
    """Load config, storage and business manager; handle uninitialised state."""
    try:
        config = Config.load()
    except Exception:
        ui.show_error(
            "BizClippy has not been initialised. Run 'bizclippy init' first."
        )
        sys.exit(1)

    config.ensure_data_dir()
    storage = Storage(config.DATA_DIR)

    api_client = None
    if config.NVIDIA_API_KEY:
        api_client = NVIDIAClient(
            api_key=config.NVIDIA_API_KEY,
            model=config.MODEL_NAME,
        )

    manager = BusinessManager(storage, api_client=api_client)
    return config, storage, manager


@click.group()
def cli() -> None:
    """BizClippy — Your AI Business Assistant"""
    pass


# ── Help (custom) ────────────────────────────────────────────────────────────

@cli.command(name="help")
def help_command() -> None:
    """Show help for all commands."""
    ui.show_help()


# ── Init ─────────────────────────────────────────────────────────────────────

@cli.command()
def init() -> None:
    """First-time setup: configure API key, business name, industry, etc."""
    ui.show_welcome("New User")
    ui.show_clippy_message(
        "Let's get you set up! I'll ask a few quick questions to personalise your experience.",
        style="bright_magenta",
    )

    # API key
    api_key = ui.prompt(
        "NVIDIA API Key (starts with nvapi-)",
        default=os.environ.get("BIZCLIPPY_API_KEY", ""),
    )
    if not api_key:
        ui.show_error(
            "An API key is required. You can get one at https://build.nvidia.com/explore/discover"
        )
        raise click.Abort()

    # Business profile
    business_name = ui.prompt("Business name")
    if not business_name:
        ui.show_error("Business name is required.")
        raise click.Abort()

    ui.print_divider()
    ui.show_clippy_message(
        "Great! Now tell me a bit more about your business...", style="bright_yellow"
    )

    industry = ui.prompt("Industry (e.g. SaaS, Retail, Consulting)", default="")
    mission_statement = ui.prompt("Mission statement", default="")
    target_audience = ui.prompt("Target audience", default="")
    revenue_model = ui.prompt("Revenue model", default="")

    stage_choices = ["idea", "mvp", "growth", "scaling"]
    current_stage = ui.select("What stage is your business at?", stage_choices)

    founded_date = ui.prompt("Founded date (YYYY-MM-DD, optional)", default="")
    if founded_date and not validate_date(founded_date):
        ui.show_error("Invalid date format. Using blank.")
        founded_date = ""

    # Save configuration
    from pathlib import Path

    data_dir = Path.home() / ".bizclippy"
    config_data = {
        "NVIDIA_API_KEY": api_key,
        "MODEL_NAME": "meta/llama3-70b-instruct",
        "API_BASE": "https://integrate.api.nvidia.com/v1",
        "DATA_DIR": str(data_dir),
    }

    data_dir.mkdir(parents=True, exist_ok=True)
    config_file = data_dir / "config.json"
    import json

    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=2)

    # Save profile
    profile = {
        "business_name": business_name,
        "industry": industry,
        "mission_statement": mission_statement,
        "target_audience": target_audience,
        "revenue_model": revenue_model,
        "current_stage": current_stage,
        "founded_date": founded_date or None,
    }
    profile_file = data_dir / "business_profile.json"
    with open(profile_file, "w") as f:
        json.dump(profile, f, indent=2)

    # Initialise default storage files
    storage = Storage(data_dir)
    storage.init_defaults()

    ui.print_divider()
    ui.show_success(f"BizClippy configured for '{business_name}'!")
    ui.show_clippy_message(
        f"You're all set, {business_name}! Try 'bizclippy chat' to start talking with me, "
        f"or 'bizclippy dashboard' to see your business overview.",
        style="bright_green",
    )


# ── Chat ─────────────────────────────────────────────────────────────────────

@cli.command()
def chat() -> None:
    """Interactive chat session with BizClippy."""
    config, storage, manager = _ensure_init()

    try:
        profile = manager.get_profile()
        business_name = profile.get("business_name", "there") if isinstance(profile, dict) else getattr(profile, "business_name", "there")
    except Exception:
        business_name = "there"

    ui.show_welcome(business_name)
    ui.show_clippy_message(
        f"Hey {business_name}! I'm BizClippy, your AI business assistant. "
        "Ask me anything about your business, goals, or just chat! "
        "Type 'quit' or 'exit' to leave.",
        style="bright_magenta",
    )
    ui.print_divider()

    while True:
        try:
            user_input = ui.prompt("You")
        except (EOFError, KeyboardInterrupt):
            ui.console.print()
            ui.show_clippy_message("See you later! Keep clipping along!  (◕‿◕)", style="bright_yellow")
            break

        if user_input.lower() in ("quit", "exit", "bye", "goodbye"):
            ui.show_clippy_message(
                "See you later! Keep clipping along!  (◕‿◕)", style="bright_yellow"
            )
            break

        if not user_input.strip():
            continue

        try:
            with ui.show_spinner("BizClippy is thinking..."):
                response = manager.chat_with_clippy(user_input)
            ui.show_clippy_message(response, style="bright_blue")
        except Exception as exc:
            ui.show_error(f"Chat error: {exc}")


# ── Dashboard ────────────────────────────────────────────────────────────────

@cli.command()
def dashboard() -> None:
    """Show business dashboard with statistics and progress."""
    config, storage, manager = _ensure_init()

    with ui.show_spinner("Loading dashboard..."):
        goals = manager.list_goals()
        tasks = manager.list_tasks()

    # Normalise goals and tasks to dicts for the UI
    goal_dicts = []
    for g in goals:
        if hasattr(g, "__dict__"):
            goal_dicts.append(vars(g))
        elif isinstance(g, dict):
            goal_dicts.append(g)
        else:
            goal_dicts.append({"title": str(g)})

    task_dicts = []
    for t in tasks:
        if hasattr(t, "__dict__"):
            task_dicts.append(vars(t))
        elif isinstance(t, dict):
            task_dicts.append(t)
        else:
            task_dicts.append({"title": str(t)})

    # Compute stats
    total_goals = len(goal_dicts)
    active_goals = [g for g in goal_dicts if g.get("status") == "active"]
    completed_tasks = [t for t in task_dicts if t.get("status") == "done"]
    pending_tasks = [t for t in task_dicts if t.get("status") in ("todo", "in_progress")]

    # Overdue tasks
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    overdue_tasks = [
        t for t in task_dicts
        if t.get("status") != "done"
        and t.get("due_date")
        and t.get("due_date", "") < today
    ]

    total_tasks = len(task_dicts)
    completion_rate = (len(completed_tasks) / total_tasks * 100) if total_tasks else 0

    # Compute progress for each active goal
    for goal in active_goals:
        gid = goal.get("id")
        goal_tasks = [t for t in task_dicts if t.get("goal_id") == gid]
        if goal_tasks:
            done = len([t for t in goal_tasks if t.get("status") == "done"])
            goal["progress"] = (done / len(goal_tasks)) * 100
        else:
            goal["progress"] = 0

    # Upcoming tasks (pending, sorted by due date)
    upcoming = [
        t for t in task_dicts
        if t.get("status") in ("todo", "in_progress") and t.get("due_date")
    ]
    upcoming.sort(key=lambda x: x.get("due_date", ""))
    upcoming = upcoming[:10]  # limit to 10

    stats = {
        "total_goals": total_goals,
        "active_goals": len(active_goals),
        "completed_tasks": len(completed_tasks),
        "pending_tasks": len(pending_tasks),
        "overdue_tasks": len(overdue_tasks),
        "completion_rate": completion_rate,
        "active_goals_list": active_goals,
        "upcoming_tasks": upcoming,
    }

    ui.show_dashboard(stats)


# ── Goals ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--status", type=click.Choice(PASSABLE_STATUSES), default=None, help="Filter by status.")
def goals(status: Optional[str]) -> None:
    """List all business goals, optionally filtered by status."""
    config, storage, manager = _ensure_init()

    with ui.show_spinner("Loading goals..."):
        goals_list = manager.list_goals(status=status)

    goal_dicts = []
    for g in goals_list:
        if hasattr(g, "__dict__"):
            d = vars(g).copy()
        elif isinstance(g, dict):
            d = g.copy()
        else:
            d = {"title": str(g)}

        # Compute progress
        gid = d.get("id")
        if gid:
            try:
                d["progress"] = manager.get_goal_progress(gid) * 100
            except Exception:
                d["progress"] = 0
        else:
            d["progress"] = 0

        goal_dicts.append(d)

    ui.show_goals_table(goal_dicts)


# ── Tasks ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--goal", "goal_id", default=None, help="Filter by goal ID.")
@click.option("--status", type=click.Choice(TASK_STATUSES), default=None, help="Filter by status.")
def tasks(goal_id: Optional[str], status: Optional[str]) -> None:
    """List all tasks, optionally filtered by goal or status."""
    config, storage, manager = _ensure_init()

    with ui.show_spinner("Loading tasks..."):
        tasks_list = manager.list_tasks(goal_id=goal_id, status=status)

    task_dicts = []
    for t in tasks_list:
        if hasattr(t, "__dict__"):
            d = vars(t).copy()
        elif isinstance(t, dict):
            d = t.copy()
        else:
            d = {"title": str(t)}
        task_dicts.append(d)

    ui.show_tasks_table(task_dicts)


# ── Add Goal ─────────────────────────────────────────────────────────────────

@cli.command(name="add-goal")
def add_goal() -> None:
    """Add a new business goal (interactive)."""
    config, storage, manager = _ensure_init()

    ui.show_clippy_message("Let's create a new goal! What do you want to achieve?", style="bright_magenta")

    title = ui.prompt("Goal title")
    if not title:
        ui.show_error("Goal title is required.")
        raise click.Abort()

    description = ui.prompt("Description", default="")
    deadline = ui.prompt("Deadline (YYYY-MM-DD, optional)", default="")
    if deadline and not validate_date(deadline):
        ui.show_error("Invalid date format. Goal will have no deadline.")
        deadline = None

    try:
        goal = manager.create_goal(title, description or "", deadline or None)
        ui.show_success(f"Goal '{title}' created successfully!")
    except Exception as exc:
        ui.show_error(f"Failed to create goal: {exc}")
        raise click.Abort()


# ── Add Task ─────────────────────────────────────────────────────────────────

@cli.command(name="add-task")
def add_task() -> None:
    """Add a new task (interactive)."""
    config, storage, manager = _ensure_init()

    ui.show_clippy_message("Let's add a new task! What needs to get done?", style="bright_magenta")

    title = ui.prompt("Task title")
    if not title:
        ui.show_error("Task title is required.")
        raise click.Abort()

    description = ui.prompt("Description", default="")

    # Optional goal selection
    goals_list = manager.list_goals()
    goal_id: Optional[str] = None
    if goals_list:
        goal_choices = ["(none)"] + [
            f"{g.title if hasattr(g, 'title') else g.get('title', 'Untitled')} "
            f"({g.id if hasattr(g, 'id') else g.get('id', '?')})"
            for g in goals_list
        ]
        selected = ui.select("Link to a goal? (optional)", goal_choices)
        if selected != "(none)":
            # Extract the goal ID from the parenthesised suffix
            import re
            match = re.search(r"\(([a-f0-9\-]+)\)$", selected)
            if match:
                goal_id = match.group(1)

    priority = ui.select("Priority", PRIORITIES)

    due_date = ui.prompt("Due date (YYYY-MM-DD, optional)", default="")
    if due_date and not validate_date(due_date):
        ui.show_error("Invalid date format. Task will have no due date.")
        due_date = None

    try:
        task = manager.create_task(
            title=title,
            description=description or "",
            goal_id=goal_id,
            priority=priority,
            due_date=due_date or None,
        )
        ui.show_success(f"Task '{title}' created successfully!")
    except Exception as exc:
        ui.show_error(f"Failed to create task: {exc}")
        raise click.Abort()


# ── Complete Task ────────────────────────────────────────────────────────────

@cli.command(name="complete-task")
def complete_task() -> None:
    """Show incomplete tasks and let the user mark one as completed."""
    config, storage, manager = _ensure_init()

    tasks_list = manager.list_tasks(status=None)
    incomplete = [t for t in tasks_list if (t.status if hasattr(t, "status") else t.get("status")) != "done"]

    if not incomplete:
        ui.show_info("All tasks are complete! Great job! 🎉")
        return

    ui.show_clippy_message(
        f"You have {len(incomplete)} incomplete task(s). Which one did you finish?",
        style="bright_yellow",
    )

    choices = [
        f"{t.title if hasattr(t, 'title') else t.get('title', 'Untitled')}"
        f"{' [due: ' + (t.due_date if hasattr(t, 'due_date') else t.get('due_date', '')) + ']' if (t.due_date if hasattr(t, 'due_date') else t.get('due_date')) else ''}"
        for t in incomplete
    ]
    selected_title = ui.select("Select a task to complete", choices)

    # Find the corresponding task object
    selected_idx = choices.index(selected_title)
    task = incomplete[selected_idx]
    task_id = task.id if hasattr(task, "id") else task.get("id")

    if ui.confirm(f"Mark '{selected_title}' as completed?"):
        try:
            manager.update_task_status(task_id, "done")
            ui.show_success(f"Task '{selected_title}' marked as completed! Great work! 🎉")
        except Exception as exc:
            ui.show_error(f"Failed to complete task: {exc}")
    else:
        ui.show_info("Task completion cancelled.")


# ── Plan ─────────────────────────────────────────────────────────────────────

@cli.command()
def plan() -> None:
    """Generate a business plan using AI."""
    config, storage, manager = _ensure_init()

    try:
        profile = manager.get_profile()
    except Exception as exc:
        ui.show_error(f"Could not load profile: {exc}")
        raise click.Abort()

    ui.show_clippy_message(
        "I'll generate a comprehensive business plan for you. This may take a moment...",
        style="bright_magenta",
    )

    try:
        with ui.show_spinner("Generating business plan..."):
            business_plan = manager.api_client.generate_business_plan(profile)
        ui.print_divider()
        ui.show_clippy_message(business_plan, style="bright_green")
        ui.print_divider()
    except Exception as exc:
        ui.show_error(f"Failed to generate business plan: {exc}")


# ── Suggest ──────────────────────────────────────────────────────────────────

@cli.command()
def suggest() -> None:
    """Get AI suggestions for your current goals and tasks."""
    config, storage, manager = _ensure_init()

    try:
        with ui.show_spinner("Analysing your business..."):
            suggestions = manager.get_ai_suggestions()
        ui.show_clippy_message(suggestions, style="bright_green")
    except Exception as exc:
        ui.show_error(f"Failed to get suggestions: {exc}")


# ── Status ───────────────────────────────────────────────────────────────────

@cli.command()
def status() -> None:
    """Show detailed status report with progress on all goals."""
    config, storage, manager = _ensure_init()

    with ui.show_spinner("Generating status report..."):
        goals_list = manager.list_goals()
        tasks_list = manager.list_tasks()

    if not goals_list:
        ui.show_info("No goals yet. Create one with 'bizclippy add-goal'!")
        return

    # Report header
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ui.print_divider()
    ui.console.print(
        f"[bold bright_cyan]📊  Status Report — {today}[/bold bright_cyan]", justify="center"
    )
    ui.print_divider()

    for goal in goals_list:
        gdict = vars(goal) if hasattr(goal, "__dict__") else goal
        gid = gdict.get("id", "")
        title = gdict.get("title", "Untitled")
        status = gdict.get("status", "unknown")
        deadline = gdict.get("deadline")

        # Compute progress
        try:
            progress = manager.get_goal_progress(gid) * 100
        except Exception:
            progress = 0

        # Goal tasks
        goal_tasks = [
            t for t in tasks_list
            if (t.goal_id if hasattr(t, "goal_id") else t.get("goal_id")) == gid
        ]
        total_goal_tasks = len(goal_tasks)
        done_goal_tasks = len([
            t for t in goal_tasks
            if (t.status if hasattr(t, "status") else t.get("status")) == "done"
        ])

        status_color = {
            "active": "bright_green",
            "completed": "bright_blue",
            "abandoned": "bright_red",
        }.get(status, "white")

        ui.console.print()
        ui.console.print(
            f"[bold bright_yellow]{title}[/bold bright_yellow]  "
            f"[{status_color}]({status})[/{status_color}]"
            f"{'  [dim]Due: ' + deadline + '[/dim]' if deadline else ''}"
        )
        ui.show_progress_bar(f"  Progress", progress)
        ui.console.print(
            f"  [dim]{done_goal_tasks}/{total_goal_tasks} tasks completed[/dim]"
            if total_goal_tasks
            else "  [dim]No tasks linked to this goal yet[/dim]"
        )

    ui.print_divider()

    # Overall summary
    total_tasks = len(tasks_list)
    done_tasks = len([
        t for t in tasks_list
        if (t.status if hasattr(t, "status") else t.get("status")) == "done"
    ])
    rate = (done_tasks / total_tasks * 100) if total_tasks else 0
    ui.console.print(
        f"[bold]Overall:[/bold] {done_tasks}/{total_tasks} tasks completed "
        f"([bold bright_cyan]{rate:.1f}%[/bold bright_cyan])"
    )
    ui.console.print()


# ── Profile ──────────────────────────────────────────────────────────────────

@cli.command()
def profile() -> None:
    """Display current business profile."""
    config, storage, manager = _ensure_init()

    try:
        profile_data = manager.get_profile()
    except Exception as exc:
        ui.show_error(f"Could not load profile: {exc}")
        return

    if hasattr(profile_data, "__dict__"):
        p = vars(profile_data)
    elif isinstance(profile_data, dict):
        p = profile_data
    else:
        ui.show_error("Profile data is in an unexpected format.")
        return

    # Map fields to display labels
    fields = [
        ("Business Name", p.get("business_name", "—")),
        ("Industry", p.get("industry", "—")),
        ("Mission Statement", p.get("mission_statement", "—")),
        ("Target Audience", p.get("target_audience", "—")),
        ("Revenue Model", p.get("revenue_model", "—")),
        ("Current Stage", p.get("current_stage", "—")),
        ("Founded Date", p.get("founded_date") or "—"),
    ]

    table = Table(
        title="🏢  Business Profile",
        title_style="bold bright_cyan",
        show_header=True,
        header_style="bold bright_white on dark_blue",
        border_style="bright_black",
        padding=(0, 1),
        expand=True,
    )
    table.add_column("Field", style="bold bright_yellow", min_width=20)
    table.add_column("Value", style="white", min_width=30)

    for field, value in fields:
        table.add_row(field, value)

    ui.console.print(table)


# ── Edit Profile ─────────────────────────────────────────────────────────────

@cli.command(name="edit-profile")
def edit_profile() -> None:
    """Edit business profile fields interactively."""
    config, storage, manager = _ensure_init()

    try:
        profile_data = manager.get_profile()
    except Exception as exc:
        ui.show_error(f"Could not load profile: {exc}")
        return

    if hasattr(profile_data, "__dict__"):
        p = vars(profile_data)
    elif isinstance(profile_data, dict):
        p = profile_data.copy()
    else:
        ui.show_error("Profile data is in an unexpected format.")
        return

    ui.show_clippy_message(
        "Let's update your business profile. Press Enter to keep the current value.",
        style="bright_magenta",
    )

    new_business_name = ui.prompt("Business name", default=p.get("business_name", ""))
    new_industry = ui.prompt("Industry", default=p.get("industry", ""))
    new_mission = ui.prompt("Mission statement", default=p.get("mission_statement", ""))
    new_audience = ui.prompt("Target audience", default=p.get("target_audience", ""))
    new_revenue = ui.prompt("Revenue model", default=p.get("revenue_model", ""))

    stage_choices = ["idea", "mvp", "growth", "scaling"]
    current_stage = p.get("current_stage", "idea")
    if current_stage and current_stage in stage_choices:
        # Put current stage first
        stage_choices.remove(current_stage)
        stage_choices.insert(0, current_stage)
    new_stage = ui.select("Current stage", stage_choices)

    new_founded = ui.prompt("Founded date (YYYY-MM-DD)", default=p.get("founded_date") or "")
    if new_founded and not validate_date(new_founded):
        ui.show_error("Invalid date format. Keeping previous value.")
        new_founded = p.get("founded_date")

    updates = {
        "business_name": new_business_name or p.get("business_name", ""),
        "industry": new_industry,
        "mission_statement": new_mission,
        "target_audience": new_audience,
        "revenue_model": new_revenue,
        "current_stage": new_stage,
        "founded_date": new_founded or None,
    }

    try:
        manager.update_profile(**updates)
        ui.show_success("Profile updated successfully!")
    except Exception as exc:
        ui.show_error(f"Failed to update profile: {exc}")


# ── Config ───────────────────────────────────────────────────────────────────

@cli.command()
def config() -> None:
    """Show current configuration (API key is partially hidden)."""
    try:
        config_obj = Config.load()
    except Exception:
        ui.show_error(
            "BizClippy has not been initialised. Run 'bizclippy init' first."
        )
        return

    # Build a dict of config values, hiding the API key
    cfg = {}
    if hasattr(config_obj, "__dict__"):
        cfg = vars(config_obj).copy()
    elif isinstance(config_obj, dict):
        cfg = config_obj.copy()
    else:
        # Try common attributes
        for attr in ("NVIDIA_API_KEY", "MODEL_NAME", "API_BASE", "DATA_DIR", "CONFIG_FILE"):
            if hasattr(config_obj, attr):
                cfg[attr] = getattr(config_obj, attr)

    # Mask the API key
    api_key = str(cfg.get("NVIDIA_API_KEY", ""))
    if api_key:
        if len(api_key) > 12:
            masked = api_key[:8] + "•" * (len(api_key) - 12) + api_key[-4:]
        else:
            masked = "•" * len(api_key)
        cfg["NVIDIA_API_KEY"] = masked

    table = Table(
        title="⚙️  Configuration",
        title_style="bold bright_cyan",
        show_header=True,
        header_style="bold bright_white on dark_blue",
        border_style="bright_black",
        padding=(0, 1),
        expand=True,
    )
    table.add_column("Setting", style="bold bright_yellow", min_width=20)
    table.add_column("Value", style="white", min_width=30)

    # Display known fields first, then any extras
    known_fields = [
        ("NVIDIA_API_KEY", cfg.pop("NVIDIA_API_KEY", "—")),
        ("MODEL_NAME", cfg.pop("MODEL_NAME", "—")),
        ("API_BASE", cfg.pop("API_BASE", "—")),
        ("DATA_DIR", str(cfg.pop("DATA_DIR", "—"))),
        ("CONFIG_FILE", str(cfg.pop("CONFIG_FILE", "—"))),
    ]
    for key, value in known_fields:
        table.add_row(key, str(value))

    # Any remaining config fields
    for key, value in sorted(cfg.items()):
        if not key.startswith("_"):
            table.add_row(key, str(value))

    ui.console.print(table)


