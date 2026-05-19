"""JSON-based local persistence for BizClippy.

Provides the Storage class for managing JSON files that store goals, tasks,
chat history, and business profile data. All data models are defined as
dataclasses with full type hint support.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class Milestone:
    """A milestone within a business goal.

    Attributes:
        id: Unique identifier (UUID).
        title: Short title of the milestone.
        completed: Whether the milestone has been achieved.
        completed_at: ISO-formatted timestamp when completed, or None.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    completed: bool = False
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Milestone":
        """Create a Milestone from a dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Goal:
    """A business goal with milestones.

    Attributes:
        id: Unique identifier (UUID).
        title: Short title of the goal.
        description: Detailed description of the goal.
        deadline: ISO-formatted date string for the deadline, or None.
        status: One of "active", "completed", or "abandoned".
        milestones: List of Milestone objects tracking progress.
        created_at: ISO-formatted timestamp when the goal was created.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    description: str = ""
    deadline: Optional[str] = None
    status: str = "active"  # "active" | "completed" | "abandoned"
    milestones: List[Milestone] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary with nested milestone serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "deadline": self.deadline,
            "status": self.status,
            "milestones": [m.to_dict() for m in self.milestones],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Goal":
        """Create a Goal from a dictionary, handling nested milestones."""
        milestones_data = data.get("milestones", [])
        milestones = [Milestone.from_dict(m) for m in milestones_data]
        return cls(
            id=data.get("id", str(uuid4())),
            title=data.get("title", ""),
            description=data.get("description", ""),
            deadline=data.get("deadline"),
            status=data.get("status", "active"),
            milestones=milestones,
            created_at=data.get(
                "created_at", datetime.now(timezone.utc).isoformat()
            ),
        )


@dataclass
class Task:
    """A task associated with a business goal.

    Attributes:
        id: Unique identifier (UUID).
        title: Short title of the task.
        description: Detailed description of the task.
        goal_id: UUID of the associated goal, or None.
        status: One of "todo", "in_progress", or "done".
        priority: One of "low", "medium", "high", or "urgent".
        due_date: ISO-formatted date string for the due date, or None.
        created_at: ISO-formatted timestamp when the task was created.
        completed_at: ISO-formatted timestamp when completed, or None.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    description: str = ""
    goal_id: Optional[str] = None
    status: str = "todo"  # "todo" | "in_progress" | "done"
    priority: str = "medium"  # "low" | "medium" | "high" | "urgent"
    due_date: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create a Task from a dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Message:
    """A chat message in the conversation history.

    Attributes:
        role: The message role — "system", "user", or "assistant".
        content: The message text content.
        timestamp: ISO-formatted timestamp when the message was sent.
    """
    role: str  # "system" | "user" | "assistant"
    content: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create a Message from a dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class BusinessProfile:
    """The user's business profile information.

    Attributes:
        business_name: Name of the business.
        industry: Industry sector (e.g., "technology", "retail").
        mission_statement: The business mission statement.
        target_audience: Description of the target customers.
        revenue_model: How the business generates revenue.
        current_stage: One of "idea", "mvp", "growth", or "scaling".
        founded_date: ISO-formatted date string, or None.
    """
    business_name: str = ""
    industry: str = ""
    mission_statement: str = ""
    target_audience: str = ""
    revenue_model: str = ""
    current_stage: str = "idea"  # "idea" | "mvp" | "growth" | "scaling"
    founded_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusinessProfile":
        """Create a BusinessProfile from a dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def is_complete(self) -> bool:
        """Check if the profile has all required fields filled.

        Returns:
            bool: True if all fields are non-empty, False otherwise.
        """
        return all(
            [
                self.business_name,
                self.industry,
                self.mission_statement,
                self.target_audience,
                self.revenue_model,
            ]
        )


# ---------------------------------------------------------------------------
# Storage Manager
# ---------------------------------------------------------------------------

class Storage:
    """JSON-based local storage for goals, tasks, conversations, and profile.

    All data is stored as JSON files in the configured DATA_DIR:
        - goals.json          -> List[Goal]
        - tasks.json          -> List[Task]
        - chat_history.json   -> List[Message]
        - business_profile.json -> BusinessProfile

    Attributes:
        DATA_DIR: The directory path where all JSON files are stored.
    """

    def __init__(self, data_dir: Path) -> None:
        """Initialize Storage with a data directory.

        Args:
            data_dir: Path to the directory for storing JSON files.
                      Created automatically if it does not exist.
        """
        self.DATA_DIR: Path = data_dir
        self._ensure_dir()

        # File paths
        self._goals_file: Path = self.DATA_DIR / "goals.json"
        self._tasks_file: Path = self.DATA_DIR / "tasks.json"
        self._chat_file: Path = self.DATA_DIR / "chat_history.json"
        self._profile_file: Path = self.DATA_DIR / "business_profile.json"

    # -- Internal helpers --------------------------------------------------

    def _ensure_dir(self) -> None:
        """Ensure the data directory exists."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _write_json(self, filepath: Path, data: Any) -> None:
        """Write data to a JSON file atomically.

        Args:
            filepath: Target file path.
            data: JSON-serializable data.

        Raises:
            StorageError: If the file cannot be written.
        """
        try:
            # Write to a temporary file first, then rename for atomicity
            tmp_path = filepath.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            tmp_path.replace(filepath)
            logger.debug("Wrote %s", filepath.name)
        except (OSError, TypeError, ValueError) as exc:
            logger.error("Failed to write %s: %s", filepath.name, exc)
            raise StorageError(f"Failed to write {filepath.name}: {exc}") from exc

    def _read_json(self, filepath: Path, default: Any = None) -> Any:
        """Read data from a JSON file.

        Args:
            filepath: Target file path.
            default: Value to return if the file does not exist.

        Returns:
            The parsed JSON data, or *default* if the file is missing.

        Raises:
            StorageError: If the file exists but cannot be read.
        """
        if not filepath.exists():
            return default
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to read %s: %s", filepath.name, exc)
            raise StorageError(f"Failed to read {filepath.name}: {exc}") from exc

    # -- Goals -------------------------------------------------------------

    def load_goals(self) -> List[Goal]:
        """Load all goals from storage.

        Returns:
            List[Goal]: All stored goals, or an empty list if none exist.
        """
        raw = self._read_json(self._goals_file, [])
        if not isinstance(raw, list):
            logger.warning("goals.json is not a list, returning empty goals")
            return []
        return [Goal.from_dict(item) for item in raw]

    def save_goals(self, goals: List[Goal]) -> None:
        """Persist the given list of goals to storage.

        Args:
            goals: List of Goal objects to save.
        """
        self._write_json(self._goals_file, [g.to_dict() for g in goals])

    # -- Tasks -------------------------------------------------------------

    def load_tasks(self) -> List[Task]:
        """Load all tasks from storage.

        Returns:
            List[Task]: All stored tasks, or an empty list if none exist.
        """
        raw = self._read_json(self._tasks_file, [])
        if not isinstance(raw, list):
            logger.warning("tasks.json is not a list, returning empty tasks")
            return []
        return [Task.from_dict(item) for item in raw]

    def save_tasks(self, tasks: List[Task]) -> None:
        """Persist the given list of tasks to storage.

        Args:
            tasks: List of Task objects to save.
        """
        self._write_json(self._tasks_file, [t.to_dict() for t in tasks])

    # -- Chat History ------------------------------------------------------

    def load_chat_history(self) -> List[Message]:
        """Load the full chat history from storage.

        Returns:
            List[Message]: All stored messages, or an empty list if none exist.
        """
        raw = self._read_json(self._chat_file, [])
        if not isinstance(raw, list):
            logger.warning("chat_history.json is not a list, returning empty history")
            return []
        return [Message.from_dict(item) for item in raw]

    def append_chat(self, message: Message) -> None:
        """Append a single message to the chat history.

        Args:
            message: The Message to append.
        """
        history = self.load_chat_history()
        history.append(message)
        self._write_json(self._chat_file, [m.to_dict() for m in history])

    def clear_chat_history(self) -> None:
        """Clear all chat history."""
        self._write_json(self._chat_file, [])
        logger.info("Chat history cleared")

    # -- Business Profile --------------------------------------------------

    def load_profile(self) -> Optional[BusinessProfile]:
        """Load the business profile from storage.

        Returns:
            BusinessProfile if one exists, otherwise None.
        """
        raw = self._read_json(self._profile_file, None)
        if raw is None:
            return None
        if not isinstance(raw, dict):
            logger.warning("business_profile.json is not an object, returning None")
            return None
        return BusinessProfile.from_dict(raw)

    def save_profile(self, profile: BusinessProfile) -> None:
        """Persist the business profile to storage.

        Args:
            profile: The BusinessProfile to save.
        """
        self._write_json(self._profile_file, profile.to_dict())

    # -- Initialization ----------------------------------------------------

    def init_defaults(self) -> None:
        """Initialize all storage files with default (empty) data.

        Creates empty goals, tasks, chat history, and a default business profile
        if the files do not already exist. Safe to call multiple times —
        existing data is never overwritten.
        """
        if not self._goals_file.exists():
            self.save_goals([])
            logger.info("Initialized empty goals storage")
        if not self._tasks_file.exists():
            self.save_tasks([])
            logger.info("Initialized empty tasks storage")
        if not self._chat_file.exists():
            self._write_json(self._chat_file, [])
            logger.info("Initialized empty chat history storage")
        if not self._profile_file.exists():
            self.save_profile(BusinessProfile())
            logger.info("Initialized default business profile")

    def reset_all(self) -> None:
        """Reset all storage files to empty/default state.

        WARNING: This deletes all existing data. Use with caution.
        """
        self.save_goals([])
        self.save_tasks([])
        self._write_json(self._chat_file, [])
        self.save_profile(BusinessProfile())
        logger.warning("All storage data has been reset")


class StorageError(Exception):
    """Exception raised for storage-related errors."""

    pass
