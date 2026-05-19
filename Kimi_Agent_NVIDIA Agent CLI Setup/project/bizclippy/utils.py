"""
utils.py — Helper functions for BizClippy.

Provides utility functions for date validation, relative time formatting,
text truncation, and spinner context management.
"""

from __future__ import annotations

import contextlib
from datetime import datetime, timezone
from typing import Optional

from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzutc
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text


class SpinnerContext:
    """A context manager that displays an animated spinner while work is in progress.

    Usage::

        with SpinnerContext(console, "Loading..."):
            do_slow_work()
    """

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


def get_spinner(console: Console, message: str) -> SpinnerContext:
    """Return a SpinnerContext for the given console and message.

    This is a convenience factory so callers can write::

        with get_spinner(console, "Thinking..."):
            result = make_api_call()

    Args:
        console: The Rich Console instance to render the spinner on.
        message: The text shown next to the spinner animation.

    Returns:
        A SpinnerContext ready to be used as a context manager.
    """
    return SpinnerContext(console, message)


def validate_date(date_str: str) -> bool:
    """Validate whether a string is in ISO date (YYYY-MM-DD) format.

    Args:
        date_str: The date string to validate.

    Returns:
        True if the string is a valid ISO date, False otherwise.
    """
    if not date_str or not isinstance(date_str, str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def format_relative_time(iso_date: str) -> str:
    """Convert an ISO date string into a human-friendly relative expression.

    Examples::

        >>> format_relative_time("2024-01-15")
        '2 days ago'
        >>> format_relative_time("2024-12-25")
        'in 3 days'

    Args:
        iso_date: An ISO-formatted date string (YYYY-MM-DD).

    Returns:
        A human-readable relative time string, or the original string
        if it could not be parsed.
    """
    if not iso_date:
        return ""
    try:
        # Parse the date — try full ISO datetime first, then plain date
        try:
            dt = date_parser.isoparse(iso_date)
        except (ValueError, TypeError):
            dt = datetime.strptime(iso_date, "%Y-%m-%d")

        # Ensure both datetimes are timezone-aware (or both naive)
        now = datetime.now()
        if dt.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        elif dt.tzinfo is None and now.tzinfo is not None:
            dt = dt.replace(tzinfo=timezone.utc)

        # Use naive datetimes for comparison
        dt_cmp = dt.replace(tzinfo=None) if dt.tzinfo else dt
        now_cmp = now.replace(tzinfo=None) if now.tzinfo else now
        delta = relativedelta(now_cmp, dt_cmp)

        if dt_cmp.date() == now_cmp.date():
            return "today"

        if dt_cmp < now_cmp:
            # Past — use absolute values
            years, months, days, hours = abs(delta.years), abs(delta.months), abs(delta.days), abs(delta.hours)
            if years:
                return f"{years} year{'s' if years != 1 else ''} ago"
            if months:
                return f"{months} month{'s' if months != 1 else ''} ago"
            if days:
                return f"{days} day{'s' if days != 1 else ''} ago"
            if hours:
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            return "just now"
        else:
            # Future — use absolute values
            years, months, days, hours = abs(delta.years), abs(delta.months), abs(delta.days), abs(delta.hours)
            if years:
                return f"in {years} year{'s' if years != 1 else ''}"
            if months:
                return f"in {months} month{'s' if months != 1 else ''}"
            if days:
                return f"in {days} day{'s' if days != 1 else ''}"
            if hours:
                return f"in {hours} hour{'s' if hours != 1 else ''}"
            return "soon"
    except Exception:
        return str(iso_date)


def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to max_length characters, appending '...' if truncated.

    Args:
        text: The original text.
        max_length: Maximum number of characters to allow.

    Returns:
        The truncated text string. Returns the original text if it is
        shorter than or equal to max_length.
    """
    if not text or len(text) <= max_length:
        return text or ""
    return text[: max_length - 3] + "..."
