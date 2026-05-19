"""BizClippy — AI-powered business assistant with a Clippy personality."""

__version__ = "0.1.0"

from bizclippy.config import Config, ConfigError
from bizclippy.storage import (
    BusinessProfile,
    Goal,
    Message,
    Milestone,
    Storage,
    StorageError,
    Task,
)
from bizclippy.api_client import NVIDIAClient, NVIDIAAPIError

__all__ = [
    "__version__",
    "BusinessProfile",
    "Config",
    "ConfigError",
    "Goal",
    "Message",
    "Milestone",
    "NVIDIAClient",
    "NVIDIAAPIError",
    "Storage",
    "StorageError",
    "Task",
]
