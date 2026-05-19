"""Configuration management for BizClippy.

Manages configuration via environment variables and a JSON config file
located at ~/.bizclippy/config.json. Environment variables take precedence
over file-based configuration.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Environment variable name for the API key
ENV_API_KEY = "BIZCLIPPY_API_KEY"

# Default configuration values
DEFAULT_MODEL_NAME = "meta/llama-3.1-8b-instruct"
DEFAULT_API_BASE = "https://integrate.api.nvidia.com/v1"
DEFAULT_DATA_DIR = Path.home() / ".bizclippy"


@dataclass
class Config:
    """Manages configuration via environment variables and ~/.bizclippy/config.json.

    Configuration is loaded from (in order of precedence):
    1. Environment variables
    2. Config file (~/.bizclippy/config.json)
    3. Default values

    Attributes:
        NVIDIA_API_KEY: API key for NVIDIA NIM API (from env BIZCLIPPY_API_KEY).
        MODEL_NAME: The AI model name to use for completions.
        API_BASE: Base URL for the NVIDIA NIM API.
        DATA_DIR: Directory for local data storage.
        CONFIG_FILE: Path to the configuration file.
    """

    NVIDIA_API_KEY: str = ""
    MODEL_NAME: str = DEFAULT_MODEL_NAME
    API_BASE: str = DEFAULT_API_BASE
    DATA_DIR: Path = field(default_factory=lambda: DEFAULT_DATA_DIR)
    CONFIG_FILE: Path = field(default_factory=lambda: DEFAULT_DATA_DIR / "config.json")

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from config file and/or environment variables.

        Environment variables take precedence over file configuration.
        If no config file exists, default values are used.

        Returns:
            Config: A populated Config instance.
        """
        config = cls()
        config.ensure_data_dir()

        # 1. Load from config file if it exists
        if config.CONFIG_FILE.exists():
            try:
                with open(config.CONFIG_FILE, "r", encoding="utf-8") as f:
                    file_data: Dict[str, Any] = json.load(f)

                config.NVIDIA_API_KEY = file_data.get("NVIDIA_API_KEY", config.NVIDIA_API_KEY)
                config.MODEL_NAME = file_data.get("MODEL_NAME", config.MODEL_NAME)
                config.API_BASE = file_data.get("API_BASE", config.API_BASE)
                if "DATA_DIR" in file_data:
                    config.DATA_DIR = Path(file_data["DATA_DIR"]).expanduser()
                    config.CONFIG_FILE = config.DATA_DIR / "config.json"

                logger.debug("Loaded configuration from %s", config.CONFIG_FILE)
            except (json.JSONDecodeError, OSError, KeyError) as exc:
                logger.warning("Failed to load config file: %s. Using defaults.", exc)
        else:
            logger.debug("No config file found at %s. Using defaults.", config.CONFIG_FILE)

        # 2. Environment variables always take precedence
        env_api_key = os.environ.get(ENV_API_KEY, "")
        if env_api_key:
            config.NVIDIA_API_KEY = env_api_key
            logger.debug("Using API key from environment variable %s", ENV_API_KEY)

        env_model = os.environ.get("BIZCLIPPY_MODEL", "")
        if env_model:
            config.MODEL_NAME = env_model

        env_api_base = os.environ.get("BIZCLIPPY_API_BASE", "")
        if env_api_base:
            config.API_BASE = env_api_base

        env_data_dir = os.environ.get("BIZCLIPPY_DATA_DIR", "")
        if env_data_dir:
            config.DATA_DIR = Path(env_data_dir).expanduser()
            config.CONFIG_FILE = config.DATA_DIR / "config.json"

        return config

    def save(self) -> None:
        """Persist the current configuration to the config file.

        Creates the data directory if it does not exist.

        Raises:
            OSError: If the config file cannot be written.
        """
        self.ensure_data_dir()

        config_dict: Dict[str, Any] = {
            "NVIDIA_API_KEY": self.NVIDIA_API_KEY,
            "MODEL_NAME": self.MODEL_NAME,
            "API_BASE": self.API_BASE,
            "DATA_DIR": str(self.DATA_DIR),
        }

        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2)
            logger.debug("Saved configuration to %s", self.CONFIG_FILE)
        except OSError as exc:
            logger.error("Failed to save config file: %s", exc)
            raise ConfigError(f"Failed to save config file: {exc}") from exc

    def validate(self) -> bool:
        """Validate that the configuration is usable.

        Checks:
            - NVIDIA_API_KEY is set (non-empty).

        Returns:
            bool: True if the configuration is valid, False otherwise.
        """
        if not self.NVIDIA_API_KEY or not self.NVIDIA_API_KEY.strip():
            logger.warning("Configuration validation failed: NVIDIA_API_KEY is not set")
            return False
        return True

    def ensure_data_dir(self) -> None:
        """Ensure the data directory exists.

        Creates the DATA_DIR (default ~/.bizclippy) and all parent directories
        if they do not already exist. Safe to call multiple times.

        Raises:
            OSError: If the directory cannot be created.
        """
        try:
            self.DATA_DIR.mkdir(parents=True, exist_ok=True)
            logger.debug("Data directory ensured at %s", self.DATA_DIR)
        except OSError as exc:
            logger.error("Failed to create data directory %s: %s", self.DATA_DIR, exc)
            raise ConfigError(f"Failed to create data directory: {exc}") from exc

    def to_dict(self) -> Dict[str, str]:
        """Convert the configuration to a dictionary.

        Returns:
            Dict[str, str]: Configuration as a plain dictionary with string values.
        """
        return {
            "NVIDIA_API_KEY": self._mask_key(self.NVIDIA_API_KEY),
            "MODEL_NAME": self.MODEL_NAME,
            "API_BASE": self.API_BASE,
            "DATA_DIR": str(self.DATA_DIR),
            "CONFIG_FILE": str(self.CONFIG_FILE),
        }

    @staticmethod
    def _mask_key(key: str) -> str:
        """Mask an API key for safe display.

        Args:
            key: The API key to mask.

        Returns:
            str: The masked key showing only the first 8 and last 4 characters,
                 or '<not set>' if the key is empty.
        """
        if not key:
            return "<not set>"
        if len(key) <= 16:
            return "***" + key[-4:] if len(key) > 4 else "****"
        return key[:8] + "..." + key[-4:]


class ConfigError(Exception):
    """Exception raised for configuration-related errors."""

    pass
