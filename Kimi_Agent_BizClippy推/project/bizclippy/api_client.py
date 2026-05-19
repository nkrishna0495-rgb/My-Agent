"""NVIDIA NIM API client for BizClippy.

Provides the NVIDIAClient class for interacting with the NVIDIA NIM API
(chat completions endpoint). Includes high-level methods for generating
business plans, suggesting tasks, and analyzing progress.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import requests

from bizclippy.storage import BusinessProfile, Goal, Task

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 60  # seconds for API requests

# System prompt used when generating business plans
_BUSINESS_PLAN_SYSTEM_PROMPT = (
    "You are an expert business strategist and consultant. "
    "Generate a comprehensive, actionable business plan based on the user's "
    "business profile. Include sections: Executive Summary, Market Analysis, "
    "Product/Service Strategy, Marketing & Sales, Operations, Financial Projections, "
    "and Milestones. Be specific, practical, and encouraging."
)

# System prompt used when suggesting tasks
_TASK_SUGGESTION_SYSTEM_PROMPT = (
    "You are a productivity expert and business operations specialist. "
    "Given a business goal and company profile, suggest a list of concrete, "
    "actionable tasks needed to achieve that goal. Each task should have a "
    "clear title and brief description. Prioritize tasks logically. "
    "Return ONLY a JSON array of task objects with 'title' and 'description' fields."
)

# System prompt used when analyzing progress
_PROGRESS_ANALYSIS_SYSTEM_PROMPT = (
    "You are a business coach and progress analyst. Review the user's goals "
    "and tasks, then provide a concise, encouraging progress analysis. "
    "Highlight achievements, flag risks (e.g., approaching deadlines, blocked tasks), "
    "and suggest next steps. Be specific and reference actual goals and tasks."
)


class NVIDIAClient:
    """Client for the NVIDIA NIM API (chat completions).

    Handles authentication, request building, response parsing, and
    provides high-level convenience methods for common AI operations.

    Attributes:
        api_key: The NVIDIA API key for authentication.
        base_url: The base URL of the NVIDIA NIM API.
        model: The model name to use for completions.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "meta/llama-3.1-8b-instruct",
        base_url: str = "https://integrate.api.nvidia.com/v1",
    ) -> None:
        """Initialize the NVIDIA API client.

        Args:
            api_key: The NVIDIA API key (Bearer token).
            model: The model identifier for completions.
            base_url: The API base URL.

        Raises:
            ValueError: If the api_key is empty or not a string.
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("A valid API key string is required.")
        self.api_key: str = api_key
        self.model: str = model
        self.base_url: str = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })
        logger.debug(
            "NVIDIAClient initialized with model=%s, base_url=%s",
            self.model,
            self.base_url,
        )

    # -- Model management --------------------------------------------------

    def list_models(self) -> List[str]:
        """List available models from the NVIDIA API.
        
        Returns:
            List of model ID strings available for this API key.
            Returns empty list if the request fails.
        """
        url = f"{self.base_url}/models"
        try:
            response = self._session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            models = [m["id"] for m in data.get("data", [])]
            logger.debug("Found %d available models", len(models))
            return models
        except requests.exceptions.RequestException as exc:
            logger.warning("Failed to list models: %s", exc)
            return []

    def validate_model(self) -> bool:
        """Check if the currently configured model is available.
        
        Returns:
            True if the model is in the available models list.
        """
        available = self.list_models()
        if not available:
            # Can't verify, assume OK
            return True
        return self.model in available

    # -- Core request method -----------------------------------------------

    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a POST request to the chat completions endpoint.

        Args:
            payload: The JSON payload containing model, messages, temperature,
                     max_tokens, and other parameters.

        Returns:
            The parsed JSON response from the API.

        Raises:
            NVIDIAAPIError: If the API returns a non-2xx status or the
                            response cannot be parsed.
            requests.RequestException: For network-level errors.
        """
        url = f"{self.base_url}/chat/completions"

        try:
            response = self._session.post(
                url,
                json=payload,
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else 0
            try:
                error_body = exc.response.json() if exc.response is not None else {}
                error_msg = error_body.get("error", {}).get("message", str(exc))
            except (ValueError, AttributeError):
                error_msg = str(exc)
            logger.error("NVIDIA API HTTP error %s: %s", status_code, error_msg)
            
            # Provide helpful messages for common errors
            if status_code == 404:
                model_used = payload.get("model", self.model)
                error_msg = (
                    f"Model '{model_used}' not found (404).\n"
                    f"This model may not be available for your API key.\n"
                    f"Try: 1) Run 'bizclippy config' to check your model setting\n"
                    f"     2) Use a known working model like 'meta/llama-3.1-8b-instruct'\n"
                    f"     3) Visit https://build.nvidia.com/explore/discover to browse models"
                )
            elif status_code == 401:
                error_msg = (
                    "Invalid API key (401).\n"
                    "Please check your BIZCLIPPY_API_KEY environment variable or run 'bizclippy init'."
                )
            elif status_code == 403:
                error_msg = (
                    "Authorization failed (403).\n"
                    "Your API key may not have access to this model.\n"
                    "Verify your key at https://build.nvidia.com/explore/discover"
                )
            
            raise NVIDIAAPIError(
                f"API HTTP error {status_code}: {error_msg}", status_code=status_code
            ) from exc

        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error to NVIDIA API: %s", exc)
            raise NVIDIAAPIError(
                f"Unable to connect to NVIDIA API at {self.base_url}. "
                "Please check your network connection."
            ) from exc

        except requests.exceptions.Timeout as exc:
            logger.error("Timeout connecting to NVIDIA API: %s", exc)
            raise NVIDIAAPIError(
                f"Request to NVIDIA API timed out after {DEFAULT_TIMEOUT}s."
            ) from exc

        except requests.exceptions.RequestException as exc:
            logger.error("Request to NVIDIA API failed: %s", exc)
            raise NVIDIAAPIError(f"Request failed: {exc}") from exc

    # -- Public API methods ------------------------------------------------

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Send a chat completion request and return the AI response.

        Args:
            messages: A list of message dicts, each with "role" and "content" keys.
                      Roles: "system", "user", "assistant".
            temperature: Sampling temperature (0.0–1.0). Higher = more random.
            max_tokens: Maximum number of tokens to generate.

        Returns:
            str: The content of the AI assistant's response message.

        Raises:
            NVIDIAAPIError: If the API request fails or the response is malformed.
            ValueError: If messages is empty or malformed.
        """
        if not messages or not isinstance(messages, list):
            raise ValueError("messages must be a non-empty list of message dicts.")

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        response_data = self._make_request(payload)
        return self._extract_content(response_data)

    def generate_business_plan(self, profile: BusinessProfile) -> str:
        """Generate an AI-written business plan based on a business profile.

        Args:
            profile: The user's BusinessProfile.

        Returns:
            str: A formatted business plan text.

        Raises:
            NVIDIAAPIError: If the API request fails.
        """
        profile_summary = self._format_profile_for_prompt(profile)
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": _BUSINESS_PLAN_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Please generate a business plan for the following business:\n\n"
                    f"{profile_summary}"
                ),
            },
        ]
        return self.chat(messages, temperature=0.7, max_tokens=2048)

    def suggest_tasks(self, goal: Goal, profile: BusinessProfile) -> List[Task]:
        """Get AI-suggested tasks for achieving a goal.

        Sends a prompt to the API requesting task suggestions and attempts
        to parse the response as JSON. Falls back to a plain-text heuristic
        if JSON parsing fails.

        Args:
            goal: The Goal for which to generate tasks.
            profile: The user's BusinessProfile for context.

        Returns:
            List[Task]: A list of suggested Task objects (not yet persisted).

        Raises:
            NVIDIAAPIError: If the API request fails.
        """
        profile_summary = self._format_profile_for_prompt(profile)
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": _TASK_SUGGESTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Business Profile:\n{profile_summary}\n\n"
                    f"Goal: {goal.title}\n"
                    f"Description: {goal.description}\n\n"
                    f"Please suggest tasks as a JSON array like:\n"
                    f'[{{"title": "Task name", "description": "What to do"}}, ...]'
                ),
            },
        ]

        response_text = self.chat(messages, temperature=0.6, max_tokens=2048)
        return self._parse_task_suggestions(response_text, goal.id)

    def analyze_progress(self, goals: List[Goal], tasks: List[Task]) -> str:
        """Get an AI analysis of business progress based on goals and tasks.

        Args:
            goals: List of the user's goals.
            tasks: List of the user's tasks.

        Returns:
            str: A textual progress analysis with insights and recommendations.

        Raises:
            NVIDIAAPIError: If the API request fails.
        """
        # Build a summary of the current state
        goals_summary = self._format_goals_summary(goals)
        tasks_summary = self._format_tasks_summary(tasks)
        stats = self._calculate_stats(goals, tasks)

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": _PROGRESS_ANALYSIS_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Progress Statistics:\n"
                    f"- Total Goals: {stats['total_goals']} "
                    f"(Active: {stats['active_goals']}, "
                    f"Completed: {stats['completed_goals']})\n"
                    f"- Total Tasks: {stats['total_tasks']} "
                    f"(Todo: {stats['todo_tasks']}, "
                    f"In Progress: {stats['in_progress_tasks']}, "
                    f"Done: {stats['done_tasks']})\n\n"
                    f"Goals:\n{goals_summary}\n\n"
                    f"Tasks:\n{tasks_summary}\n\n"
                    f"Please provide a progress analysis with encouragement "
                    f"and actionable next steps."
                ),
            },
        ]
        return self.chat(messages, temperature=0.7, max_tokens=2048)

    # -- Response parsing helpers ------------------------------------------

    @staticmethod
    def _extract_content(response_data: Dict[str, Any]) -> str:
        """Extract the assistant message content from an API response.

        Args:
            response_data: The parsed JSON response from the API.

        Returns:
            str: The content string from the first choice message.

        Raises:
            NVIDIAAPIError: If the response structure is unexpected.
        """
        try:
            choices = response_data.get("choices", [])
            if not choices:
                raise NVIDIAAPIError("API response contained no choices.")
            message = choices[0].get("message", {})
            content = message.get("content", "")
            return content.strip()
        except (AttributeError, IndexError, TypeError) as exc:
            logger.error("Failed to parse API response: %s", response_data)
            raise NVIDIAAPIError(f"Unexpected API response format: {exc}") from exc

    @staticmethod
    def _parse_task_suggestions(response_text: str, goal_id: Optional[str]) -> List[Task]:
        """Parse task suggestions from the AI response.

        Attempts JSON parsing first, then falls back to a regex-based
        heuristic for extracting task-like lines.

        Args:
            response_text: Raw text returned by the API.
            goal_id: The goal ID to associate with generated tasks.

        Returns:
            List[Task]: Parsed Task objects.
        """
        tasks: List[Task] = []

        # Attempt 1: Parse as JSON
        try:
            # Find JSON array in the response (the model may wrap it in markdown)
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            tasks.append(
                                Task(
                                    id=str(uuid4()),
                                    title=item.get("title", "Untitled Task"),
                                    description=item.get("description", ""),
                                    goal_id=goal_id,
                                    status="todo",
                                    priority="medium",
                                    created_at=datetime.now(timezone.utc).isoformat(),
                                )
                            )
                    if tasks:
                        logger.info("Parsed %d tasks from JSON response", len(tasks))
                        return tasks
        except (json.JSONDecodeError, TypeError) as exc:
            logger.debug("JSON parsing failed, trying fallback: %s", exc)

        # Attempt 2: Fallback — extract numbered or bullet-point lines
        lines = response_text.strip().splitlines()
        current_title: Optional[str] = None
        current_desc: Optional[str] = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Match numbered items like "1. Task Title" or "- Task Title"
            match = re.match(r"^(?:\d+[.):-]\s*|[\-*•]\s+)(.+)", line)
            if match:
                # Save previous task if exists
                if current_title:
                    tasks.append(
                        Task(
                            id=str(uuid4()),
                            title=current_title,
                            description=current_desc or "",
                            goal_id=goal_id,
                            status="todo",
                            priority="medium",
                            created_at=datetime.now(timezone.utc).isoformat(),
                        )
                    )
                current_title = match.group(1).strip()
                current_desc = None
            elif current_title and not current_desc:
                # This line might be a description for the current title
                current_desc = line

        # Don't forget the last task
        if current_title:
            tasks.append(
                Task(
                    id=str(uuid4()),
                    title=current_title,
                    description=current_desc or "",
                    goal_id=goal_id,
                    status="todo",
                    priority="medium",
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
            )

        if not tasks:
            # Last resort: wrap the entire response as a single task
            first_line = response_text.strip().split("\n")[0][:100]
            tasks.append(
                Task(
                    id=str(uuid4()),
                    title=first_line or "AI-suggested task",
                    description=response_text.strip(),
                    goal_id=goal_id,
                    status="todo",
                    priority="medium",
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
            )

        logger.info("Parsed %d tasks using fallback parser", len(tasks))
        return tasks

    # -- Formatting helpers ------------------------------------------------

    @staticmethod
    def _format_profile_for_prompt(profile: BusinessProfile) -> str:
        """Format a BusinessProfile into a string suitable for prompts.

        Args:
            profile: The business profile.

        Returns:
            str: A formatted summary string.
        """
        lines = [
            f"Business Name: {profile.business_name or 'N/A'}",
            f"Industry: {profile.industry or 'N/A'}",
            f"Mission: {profile.mission_statement or 'N/A'}",
            f"Target Audience: {profile.target_audience or 'N/A'}",
            f"Revenue Model: {profile.revenue_model or 'N/A'}",
            f"Current Stage: {profile.current_stage or 'N/A'}",
        ]
        if profile.founded_date:
            lines.append(f"Founded: {profile.founded_date}")
        return "\n".join(lines)

    @staticmethod
    def _format_goals_summary(goals: List[Goal]) -> str:
        """Format a list of goals into a concise summary string.

        Args:
            goals: The goals to summarize.

        Returns:
            str: A formatted summary.
        """
        if not goals:
            return "  (No goals set yet)"
        lines = []
        for g in goals:
            ms_completed = sum(1 for m in g.milestones if m.completed)
            ms_total = len(g.milestones)
            lines.append(
                f"  - {g.title} [{g.status}] "
                f"(Milestones: {ms_completed}/{ms_total})"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_tasks_summary(tasks: List[Task]) -> str:
        """Format a list of tasks into a concise summary string.

        Args:
            tasks: The tasks to summarize.

        Returns:
            str: A formatted summary.
        """
        if not tasks:
            return "  (No tasks created yet)"
        lines = []
        for t in tasks:
            lines.append(f"  - {t.title} [{t.status}] (priority: {t.priority})")
        return "\n".join(lines)

    @staticmethod
    def _calculate_stats(goals: List[Goal], tasks: List[Task]) -> Dict[str, int]:
        """Calculate summary statistics for goals and tasks.

        Args:
            goals: All goals.
            tasks: All tasks.

        Returns:
            Dict[str, int]: Statistics dictionary.
        """
        return {
            "total_goals": len(goals),
            "active_goals": sum(1 for g in goals if g.status == "active"),
            "completed_goals": sum(1 for g in goals if g.status == "completed"),
            "total_tasks": len(tasks),
            "todo_tasks": sum(1 for t in tasks if t.status == "todo"),
            "in_progress_tasks": sum(1 for t in tasks if t.status == "in_progress"),
            "done_tasks": sum(1 for t in tasks if t.status == "done"),
        }

    def __repr__(self) -> str:
        return (
            f"NVIDIAClient(model={self.model!r}, "
            f"base_url={self.base_url!r})"
        )


class NVIDIAAPIError(Exception):
    """Exception raised for errors communicating with the NVIDIA NIM API.

    Attributes:
        message: Human-readable error description.
        status_code: HTTP status code if applicable, otherwise 0.
    """

    def __init__(self, message: str, status_code: int = 0) -> None:
        super().__init__(message)
        self.status_code = status_code
