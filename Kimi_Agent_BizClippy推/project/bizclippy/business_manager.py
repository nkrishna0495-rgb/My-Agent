"""
business_manager.py -- Core business logic for BizClippy.

Orchestrates goal and task CRUD operations, AI-powered features,
and profile management. Acts as the bridge between the CLI/UI layer
and the underlying storage and API clients.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

# These modules are provided by sibling packages in the bizclippy project.
from bizclippy.storage import Storage, Goal, Task, BusinessProfile, Message
from bizclippy.api_client import NVIDIAClient
from bizclippy.clippy_persona import ClippyPersona


class BusinessManager:
    """Core business logic for goal/task management and AI features.

    The BusinessManager is the primary orchestrator for all business-domain
    operations. It owns a Storage instance for persistence and an optional
    NVIDIAClient for AI-powered suggestions, planning, and chat.

    When ``api_client`` is None the manager operates in offline mode: AI
    methods degrade gracefully by returning helpful fallback messages instead
    of raising errors.
    """

    def __init__(
        self,
        storage: Storage,
        api_client: Optional[NVIDIAClient] = None,
    ) -> None:
        self.storage: Storage = storage
        self.api_client: Optional[NVIDIAClient] = api_client
        self._persona = ClippyPersona()

    # ================================================================
    # Goal Management
    # ================================================================

    def create_goal(
        self,
        title: str,
        description: str,
        deadline: Optional[str] = None,
    ) -> Goal:
        """Create a new goal and persist it.

        Args:
            title: Short title of the goal.
            description: Detailed description.
            deadline: Optional ISO-8601 date string.

        Returns:
            The newly created Goal instance.
        """
        goal = Goal(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            deadline=deadline,
            status="active",
            milestones=[],
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        goals = self.storage.load_goals()
        goals.append(goal)
        self.storage.save_goals(goals)
        return goal

    def list_goals(self, status: Optional[str] = None) -> List[Goal]:
        """List all goals, optionally filtered by status.

        Args:
            status: One of ``"active"``, ``"completed"``, ``"abandoned"``.

        Returns:
            A list of matching Goal objects.
        """
        goals = self.storage.load_goals()
        if status is not None:
            goals = [g for g in goals if g.status == status]
        return goals

    def update_goal_status(self, goal_id: str, status: str) -> Goal:
        """Update the status of a goal and persist the change.

        Args:
            goal_id: UUID string of the goal to update.
            status: New status value.

        Returns:
            The updated Goal.

        Raises:
            ValueError: If no goal with the given ID exists.
        """
        goals = self.storage.load_goals()
        for goal in goals:
            if goal.id == goal_id:
                goal.status = status
                self.storage.save_goals(goals)
                return goal
        raise ValueError(f"Goal with id '{goal_id}' not found.")

    def delete_goal(self, goal_id: str) -> None:
        """Remove a goal by ID and persist.

        Args:
            goal_id: UUID string of the goal to delete.

        Raises:
            ValueError: If no goal with the given ID exists.
        """
        goals = self.storage.load_goals()
        original_len = len(goals)
        goals = [g for g in goals if g.id != goal_id]
        if len(goals) == original_len:
            raise ValueError(f"Goal with id '{goal_id}' not found.")
        self.storage.save_goals(goals)

    def get_goal_progress(self, goal_id: str) -> float:
        """Calculate goal completion percentage based on milestones.

        Args:
            goal_id: UUID string of the goal.

        Returns:
            A float between 0.0 and 100.0 representing the percentage of
            completed milestones. Returns 0.0 if the goal has no milestones.

        Raises:
            ValueError: If no goal with the given ID exists.
        """
        goals = self.storage.load_goals()
        for goal in goals:
            if goal.id == goal_id:
                milestones = goal.milestones
                if not milestones:
                    return 0.0
                completed = sum(
                    1 for m in milestones if getattr(m, "completed", False)
                )
                return (completed / len(milestones)) * 100.0
        raise ValueError(f"Goal with id '{goal_id}' not found.")

    # ================================================================
    # Task Management
    # ================================================================

    def create_task(
        self,
        title: str,
        description: str,
        goal_id: Optional[str] = None,
        priority: str = "medium",
        due_date: Optional[str] = None,
    ) -> Task:
        """Create a new task and persist it.

        Args:
            title: Short title of the task.
            description: Detailed description.
            goal_id: Optional UUID of an associated goal.
            priority: One of ``"low"``, ``"medium"``, ``"high"``, ``"urgent"``.
            due_date: Optional ISO-8601 date string.

        Returns:
            The newly created Task instance.
        """
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            goal_id=goal_id,
            status="todo",
            priority=priority,
            due_date=due_date,
            created_at=datetime.now(timezone.utc).isoformat(),
            completed_at=None,
        )
        tasks = self.storage.load_tasks()
        tasks.append(task)
        self.storage.save_tasks(tasks)
        return task

    def list_tasks(
        self,
        goal_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Task]:
        """List tasks, optionally filtered by goal or status.

        Args:
            goal_id: Filter to tasks associated with this goal UUID.
            status: One of ``"todo"``, ``"in_progress"``, ``"done"``.

        Returns:
            A list of matching Task objects.
        """
        tasks = self.storage.load_tasks()
        if goal_id is not None:
            tasks = [t for t in tasks if t.goal_id == goal_id]
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def update_task_status(self, task_id: str, status: str) -> Task:
        """Update the status of a task and persist.

        Args:
            task_id: UUID string of the task to update.
            status: New status value.

        Returns:
            The updated Task.

        Raises:
            ValueError: If no task with the given ID exists.
        """
        tasks = self.storage.load_tasks()
        for task in tasks:
            if task.id == task_id:
                task.status = status
                if status == "done":
                    task.completed_at = datetime.now(timezone.utc).isoformat()
                else:
                    task.completed_at = None
                self.storage.save_tasks(tasks)
                return task
        raise ValueError(f"Task with id '{task_id}' not found.")

    def delete_task(self, task_id: str) -> None:
        """Remove a task by ID and persist.

        Args:
            task_id: UUID string of the task to delete.

        Raises:
            ValueError: If no task with the given ID exists.
        """
        tasks = self.storage.load_tasks()
        original_len = len(tasks)
        tasks = [t for t in tasks if t.id != task_id]
        if len(tasks) == original_len:
            raise ValueError(f"Task with id '{task_id}' not found.")
        self.storage.save_tasks(tasks)

    # ================================================================
    # AI Features
    # ================================================================

    def _is_offline(self) -> bool:
        """Return True if no API client is configured."""
        return self.api_client is None

    def _gather_context(self) -> dict:
        """Collect user profile, goals, and tasks into a context dict.

        Returns:
            Dictionary suitable for passing to
            :meth:`ClippyPersona.build_system_prompt`.
        """
        context: dict = {}
        try:
            profile = self.storage.load_profile()
            context["business_name"] = getattr(profile, "business_name", "")
            context["industry"] = getattr(profile, "industry", "")
            context["mission_statement"] = getattr(profile, "mission_statement", "")
            context["target_audience"] = getattr(profile, "target_audience", "")
            context["revenue_model"] = getattr(profile, "revenue_model", "")
            context["current_stage"] = getattr(profile, "current_stage", "")
        except Exception:
            # Profile may not be initialised yet.
            pass

        try:
            context["goals"] = self.storage.load_goals()
        except Exception:
            context["goals"] = []

        try:
            context["tasks"] = self.storage.load_tasks()
        except Exception:
            context["tasks"] = []

        return context

    def get_ai_suggestions(self) -> str:
        """Generate AI-powered business suggestions based on current context.

        Returns:
            A formatted suggestion string from BizClippy, or a friendly
            offline-mode message when no API client is available.
        """
        if self._is_offline():
            return (
                self._persona.format_greeting()
                + " I'd love to offer AI-powered suggestions, but I'm running in "
                "offline mode right now. Set your NVIDIA API key with "
                "`bizclippy config` to unlock the full experience! (◕‿◕)\n\n"
                "- BizClippy"
            )

        context = self._gather_context()
        system_prompt = self._persona.build_system_prompt(context)

        goals = context.get("goals", [])
        tasks = context.get("tasks", [])

        user_content = (
            "Based on my current business situation, what are the top 3 "
            "actions I should take this week?\n\n"
        )
        if goals:
            user_content += "My goals:\n"
            for g in goals:
                user_content += f"- {g.title}\n"
        if tasks:
            user_content += "\nMy tasks:\n"
            for t in tasks:
                user_content += f"- {t.title} ({t.status})\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        try:
            ai_response = self.api_client.chat(
                messages=messages, temperature=0.7, max_tokens=1024
            )
        except Exception as exc:
            return (
                self._persona.format_greeting()
                + f" Hmm, I ran into a little trouble connecting to the AI: {exc}\n"
                "Let's try again in a moment! ʘ‿ʘ\n\n- BizClippy"
            )

        return self._persona.format_response(ai_response)

    def generate_weekly_plan(self) -> str:
        """Generate an AI-powered weekly task plan.

        Returns:
            A formatted weekly plan from BizClippy, or a friendly
            offline-mode message when no API client is available.
        """
        if self._is_offline():
            return (
                self._persona.format_greeting()
                + " Weekly planning is one of my favourite features, but I need "
                "an API connection to make it shine. Run `bizclippy config` to "
                "set your NVIDIA API key! ᕕ(ᐛ)ᕗ\n\n"
                "- BizClippy"
            )

        context = self._gather_context()
        system_prompt = self._persona.build_system_prompt(context)

        goals = context.get("goals", [])
        tasks = context.get("tasks", [])

        user_content = (
            "Create a weekly plan for me. Break it down by day with specific "
            "tasks and priorities. Consider my goals and current tasks.\n\n"
        )
        if goals:
            user_content += "My goals:\n"
            for g in goals:
                user_content += f"- {g.title} ({g.status})\n"
        if tasks:
            user_content += "\nMy open tasks:\n"
            for t in tasks:
                if t.status != "done":
                    user_content += f"- {t.title} (priority: {t.priority})\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        try:
            ai_response = self.api_client.chat(
                messages=messages, temperature=0.7, max_tokens=1024
            )
        except Exception as exc:
            return (
                self._persona.format_greeting()
                + f" I couldn't generate your plan right now: {exc}\n"
                "Let's give it another shot soon! (◕‿◕)\n\n- BizClippy"
            )

        return self._persona.format_response(ai_response)

    def chat_with_clippy(self, user_message: str) -> str:
        """Send a user message to BizClippy and return the formatted reply.

        Loads conversation history, enriches the system prompt with current
        context, calls the AI backend, appends both messages to history,
        and returns a personality-formatted response.

        Args:
            user_message: The text the user typed.

        Returns:
            BizClippy's formatted response string.
        """
        # Record the user's message.
        user_msg = Message(
            role="user",
            content=user_message,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        try:
            self.storage.append_chat(user_msg)
        except Exception:
            pass  # Best-effort history logging.

        # Offline fallback
        if self._is_offline():
            return (
                self._persona.format_greeting()
                + " I'm in offline mode right now, but I still want to help! "
                "Set your NVIDIA API key with `bizclippy config` so we can "
                "have full conversations. In the meantime, you can still use "
                "`bizclippy goals` and `bizclippy tasks` to manage your business. "
                "(◕‿◕)\n\n- BizClippy"
            )

        # Build context and system prompt.
        context = self._gather_context()
        system_prompt = self._persona.build_system_prompt(context)

        # Load recent chat history for continuity.
        try:
            history = self.storage.load_chat_history()
        except Exception:
            history = []

        # Build the messages list (system + recent history + current message).
        messages: List[dict] = [{"role": "system", "content": system_prompt}]
        # Include up to the last 10 messages to keep context manageable.
        for msg in history[-10:]:
            role = getattr(msg, "role", "user")
            content = getattr(msg, "content", "")
            messages.append({"role": role, "content": content})
        # Ensure the current user message is the final entry.
        if not history or getattr(history[-1], "content", None) != user_message:
            messages.append({"role": "user", "content": user_message})

        # Call the AI.
        try:
            ai_response = self.api_client.chat(
                messages=messages, temperature=0.7, max_tokens=1024
            )
        except Exception as exc:
            error_reply = (
                self._persona.format_greeting()
                + f" Oops, I hit a snag: {exc}\n"
                "Let's try our conversation again in just a moment! ʘ‿ʘ\n\n"
                "- BizClippy"
            )
            # Log the assistant's error reply as well.
            try:
                self.storage.append_chat(
                    Message(
                        role="assistant",
                        content=error_reply,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                )
            except Exception:
                pass
            return error_reply

        # Format and persist the assistant reply.
        formatted = self._persona.format_response(ai_response)
        try:
            self.storage.append_chat(
                Message(
                    role="assistant",
                    content=formatted,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )
        except Exception:
            pass

        return formatted

    # ================================================================
    # Profile Management
    # ================================================================

    def update_profile(self, **kwargs) -> BusinessProfile:
        """Update business profile fields and persist.

        Accepts any keyword argument that is a valid attribute of
        BusinessProfile. Missing fields are left unchanged.

        Returns:
            The updated (or newly created) BusinessProfile.
        """
        try:
            profile = self.storage.load_profile()
        except Exception:
            # Create a default profile if one doesn't exist.
            profile = BusinessProfile(
                business_name=kwargs.get("business_name", ""),
                industry=kwargs.get("industry", ""),
                mission_statement=kwargs.get("mission_statement", ""),
                target_audience=kwargs.get("target_audience", ""),
                revenue_model=kwargs.get("revenue_model", ""),
                current_stage=kwargs.get("current_stage", "idea"),
                founded_date=kwargs.get("founded_date", None),
            )
            self.storage.save_profile(profile)
            return profile

        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        self.storage.save_profile(profile)
        return profile

    def get_profile(self) -> BusinessProfile:
        """Load and return the current business profile.

        Returns:
            The persisted BusinessProfile.

        Raises:
            Exception: If no profile exists (propagated from storage).
        """
        return self.storage.load_profile()
