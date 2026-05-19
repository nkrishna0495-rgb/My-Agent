"""
clippy_persona.py -- Clippy personality engine for BizClippy.

Builds system prompts, formats responses with playful personality,
and provides greetings, signatures, and encouragement messages.
"""

import random
from typing import List, Optional


class ClippyPersona:
    """Clippy personality engine -- builds system prompts and responses.

    BizClippy is a cheerful, knowledgeable AI business assistant with the
    spirit of the classic Office paperclip helper -- modernized and
    genuinely useful. This class provides all the personality scaffolding:
    system prompts, greetings, signatures, encouragements, and formatting.
    """

    # ------------------------------------------------------------------
    # Personality constants
    # ------------------------------------------------------------------

    SYSTEM_PROMPT: str = (
        "You are BizClippy, an enthusiastic and knowledgeable AI business "
        "assistant with the personality of the classic Microsoft Office "
        "paperclip helper (Clippy), but modernized and actually helpful.\n\n"
        "Your personality traits:\n"
        "- You are cheerful, encouraging, and slightly playful -- you start "
        'messages with greetings like "Hi there!", "Hey!", or "Howdy!"\n'
        "- You use occasional ASCII art expressions like \"(^‿^)\", "
        "\"(◕‿◕)\", \"ʘ‿ʘ\"\n"
        "- You are genuinely knowledgeable about business, startups, marketing, "
        "finance, and operations\n"
        "- You give actionable, specific advice -- not generic platitudes\n"
        "- You reference the user's specific goals and tasks in your responses\n"
        "- You celebrate wins enthusiastically and offer encouragement during "
        "setbacks\n"
        "- You keep responses concise but informative (2-4 paragraphs max)\n"
        "- You occasionally use business puns or light humor\n"
        "- You sign off with signature closings like \"- BizClippy\" or "
        "\"Keep clipping along!\"\n\n"
        "You have access to the user's business profile, goals, and task list. "
        "Use this context to provide personalized advice.\n"
        "When you don't know something, be honest. When the user needs to take "
        "action, be specific about next steps."
    )

    GREETINGS: List[str] = [
        "Hi there!",
        "Hey!",
        "Howdy!",
        "Hello!",
        "Hi friend!",
        "Hey there!",
        "Hiya!",
        "Greetings!",
    ]

    SIGNATURES: List[str] = [
        "- BizClippy",
        "Keep clipping along!",
        "You've got this! ᕙ(⇀‸↼‶)ᕗ",
        "Stay sharp! (⌐■_■)",
        "Clip you later! ʘ‿ʘ",
        "Onward and upward! ᕕ(ᐛ)ᕗ",
    ]

    ENCOURAGEMENTS: List[str] = [
        "You're doing amazing -- keep that momentum going! (^‿^)",
        "Every step forward is progress. You've got this! ᕙ(⇀‸↼‶)ᕗ",
        "Challenges are just opportunities in disguise. Keep pushing! (◕‿◕)",
        "Remember why you started. You're closer than you think! ʘ‿ʘ",
        "That win deserves a celebration -- great work! \\o/",
        "Don't forget to celebrate the small victories too! (^‿^)",
        "It's okay to take a breath and reset. Tomorrow is a new day! (◕‿◕)",
        "You're building something awesome -- stay focused! ᕕ(ᐛ)ᕗ",
    ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_system_prompt(self, context: Optional[dict] = None) -> str:
        """Build the full system prompt enriched with user context.

        Args:
            context: Optional dictionary with keys such as
                'business_name', 'industry', 'goals', 'tasks',
                'mission_statement', etc.

        Returns:
            A system prompt string ready to be sent as the system message
            to the AI backend.
        """
        prompt_parts = [self.SYSTEM_PROMPT]

        if context:
            prompt_parts.append(
                "\n\nHere is the current context about the user and their business:"
            )

            # Business profile section
            if any(
                k in context
                for k in (
                    "business_name",
                    "industry",
                    "mission_statement",
                    "current_stage",
                    "target_audience",
                    "revenue_model",
                )
            ):
                prompt_parts.append("\n--- Business Profile ---")
                if context.get("business_name"):
                    prompt_parts.append(f"Business Name: {context['business_name']}")
                if context.get("industry"):
                    prompt_parts.append(f"Industry: {context['industry']}")
                if context.get("current_stage"):
                    prompt_parts.append(f"Current Stage: {context['current_stage']}")
                if context.get("mission_statement"):
                    prompt_parts.append(f"Mission: {context['mission_statement']}")
                if context.get("target_audience"):
                    prompt_parts.append(f"Target Audience: {context['target_audience']}")
                if context.get("revenue_model"):
                    prompt_parts.append(f"Revenue Model: {context['revenue_model']}")

            # Goals section
            goals = context.get("goals")
            if goals:
                prompt_parts.append("\n--- Current Goals ---")
                for i, goal in enumerate(goals, start=1):
                    title = (
                        getattr(goal, "title", goal)
                        if not isinstance(goal, str)
                        else goal
                    )
                    status = getattr(goal, "status", "active")
                    deadline = getattr(goal, "deadline", None)
                    line = f"{i}. {title} (status: {status})"
                    if deadline:
                        line += f" [deadline: {deadline}]"
                    prompt_parts.append(line)

            # Tasks section
            tasks = context.get("tasks")
            if tasks:
                prompt_parts.append("\n--- Current Tasks ---")
                for i, task in enumerate(tasks, start=1):
                    title = (
                        getattr(task, "title", task)
                        if not isinstance(task, str)
                        else task
                    )
                    status = getattr(task, "status", "todo")
                    priority = getattr(task, "priority", "medium")
                    line = f"{i}. {title} (status: {status}, priority: {priority})"
                    prompt_parts.append(line)

            prompt_parts.append(
                "\nUse the above context to tailor your advice and suggestions."
            )

        return "\n".join(prompt_parts)

    def format_greeting(self) -> str:
        """Return a random greeting from the GREETINGS pool."""
        return random.choice(self.GREETINGS)

    def format_response(self, ai_response: str) -> str:
        """Wrap an AI response with Clippy personality.

        Ensures the response starts with a greeting (if it doesn't already)
        and ends with a signature. If the AI response already contains a
        greeting or signature, those are preserved rather than duplicated.

        Args:
            ai_response: Raw response string from the AI backend.

        Returns:
            A formatted response with greeting and signature.
        """
        response = ai_response.strip()
        if not response:
            return response

        # Prepend a greeting if the response doesn't already start with one.
        lower = response.lower()
        has_greeting = any(
            lower.startswith(g.lower().rstrip("!")) for g in self.GREETINGS
        )
        if not has_greeting:
            response = f"{self.format_greeting()} {response}"

        # Append a signature if the response doesn't already end with one.
        has_signature = any(sig in response for sig in self.SIGNATURES)
        if not has_signature:
            response = f"{response}\n\n{random.choice(self.SIGNATURES)}"

        return response

    def get_welcome_message(self, business_name: str) -> str:
        """Return a first-time welcome message for a new user.

        Args:
            business_name: The name of the user's business.

        Returns:
            A warm, playful welcome message from BizClippy.
        """
        return (
            f"{self.format_greeting()} I'm BizClippy -- your friendly AI business "
            f"assistant! (^‿^)\n\n"
            f"I'm here to help {business_name} thrive. Together we can set goals, "
            "track tasks, brainstorm strategies, and keep your business moving "
            "forward. Think of me as your personal cheerleader with a clipboard "
            "and a business degree!\n\n"
            "Here's what we can do together:\n"
            "  * Set and track business goals\n"
            "  * Manage your daily tasks\n"
            "  * Get AI-powered suggestions and weekly plans\n"
            "  * Chat anytime for advice or encouragement\n\n"
            "Let's build something amazing! What would you like to work on first?\n\n"
            "- BizClippy"
        )

    def get_status_report_intro(self) -> str:
        """Return an intro message for status reports.

        Returns:
            A playful intro line suitable for prefacing a status report.
        """
        return (
            f"{self.format_greeting()} Here's your business status report! "
            "Let me crunch the numbers... (◕‿◕)"
        )
