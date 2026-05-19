# SPEC.md — AI Business Assistant CLI (Clippy-style)

## Overview
A Python CLI application that provides an AI-powered business assistant with a Clippy-like personality. Uses NVIDIA NIM API for AI inference. Helps users set business goals, track tasks, get advice, and monitor progress — all through a rich terminal interface.

## Architecture

```
bizclippy/
├── __init__.py           # Package init, version
├── __main__.py           # Entry point: python -m bizclippy
├── main.py               # Click CLI command definitions
├── api_client.py         # NVIDIA NIM API client
├── config.py             # Configuration & env var management
├── storage.py            # Local JSON-based persistence
├── business_manager.py   # Goal/task/calendar business logic
├── clippy_persona.py     # Clippy personality engine & prompts
├── ui.py                 # Rich terminal UI components
└── utils.py              # Helpers

setup.py                  # Package installation
requirements.txt          # Dependencies
README.md                 # Documentation & install steps
install.sh                # One-liner installation script
```

## Module Specifications

### 1. config.py
```python
class Config:
    """Manages configuration via environment variables and ~/.bizclippy/config.json"""
    
    NVIDIA_API_KEY: str      # From env BIZCLIPPY_API_KEY or prompt
    MODEL_NAME: str          # Default: "meta/llama3-70b-instruct"
    API_BASE: str            # Default: "https://integrate.api.nvidia.com/v1"
    DATA_DIR: Path           # Default: ~/.bizclippy
    CONFIG_FILE: Path        # DATA_DIR / "config.json"
    
    @classmethod
    def load(cls) -> "Config": ...
    def save(self) -> None: ...
    def validate(self) -> bool: ...
    def ensure_data_dir(self) -> None: ...
```

### 2. storage.py
```python
class Storage:
    """JSON-based local storage for goals, tasks, conversations"""
    
    DATA_DIR: Path
    
    # Files:
    #   goals.json      -> List[Goal]
    #   tasks.json      -> List[Task]
    #   chat_history.json -> List[Message]
    #   business_profile.json -> BusinessProfile
    
    def load_goals(self) -> List[Goal]: ...
    def save_goals(self, goals: List[Goal]) -> None: ...
    def load_tasks(self) -> List[Task]: ...
    def save_tasks(self, tasks: List[Task]) -> None: ...
    def load_chat_history(self) -> List[Message]: ...
    def append_chat(self, message: Message) -> None: ...
    def load_profile(self) -> BusinessProfile: ...
    def save_profile(self, profile: BusinessProfile) -> None: ...
    def init_defaults(self) -> None: ...

# Data Models:
@dataclass
class Goal:
    id: str           # UUID
    title: str
    description: str
    deadline: Optional[str]  # ISO date
    status: str       # "active" | "completed" | "abandoned"
    milestones: List[Milestone]
    created_at: str

@dataclass
class Task:
    id: str
    title: str
    description: str
    goal_id: Optional[str]
    status: str       # "todo" | "in_progress" | "done"
    priority: str     # "low" | "medium" | "high" | "urgent"
    due_date: Optional[str]
    created_at: str
    completed_at: Optional[str]

@dataclass
class BusinessProfile:
    business_name: str
    industry: str
    mission_statement: str
    target_audience: str
    revenue_model: str
    current_stage: str  # "idea" | "mvp" | "growth" | "scaling"
    founded_date: Optional[str]
```

### 3. api_client.py
```python
class NVIDIAClient:
    """Client for NVIDIA NIM API"""
    
    api_key: str
    base_url: str
    model: str
    
    def __init__(self, api_key: str, model: str = "meta/llama3-70b-instruct"): ...
    
    def chat(self, messages: List[dict], temperature: float = 0.7, max_tokens: int = 1024) -> str: ...
    
    def generate_business_plan(self, profile: BusinessProfile) -> str: ...
    
    def suggest_tasks(self, goal: Goal, profile: BusinessProfile) -> List[Task]: ...
    
    def analyze_progress(self, goals: List[Goal], tasks: List[Task]) -> str: ...
    
    def _make_request(self, payload: dict) -> dict: ...  # POST to /chat/completions
```

### 4. business_manager.py
```python
class BusinessManager:
    """Core business logic for goal/task management"""
    
    storage: Storage
    api_client: Optional[NVIDIAClient]
    
    def __init__(self, storage: Storage, api_client: Optional[NVIDIAClient] = None): ...
    
    # Goal Management
    def create_goal(self, title: str, description: str, deadline: Optional[str] = None) -> Goal: ...
    def list_goals(self, status: Optional[str] = None) -> List[Goal]: ...
    def update_goal_status(self, goal_id: str, status: str) -> Goal: ...
    def delete_goal(self, goal_id: str) -> None: ...
    def get_goal_progress(self, goal_id: str) -> float: ...
    
    # Task Management
    def create_task(self, title: str, description: str, goal_id: Optional[str] = None, 
                    priority: str = "medium", due_date: Optional[str] = None) -> Task: ...
    def list_tasks(self, goal_id: Optional[str] = None, status: Optional[str] = None) -> List[Task]: ...
    def update_task_status(self, task_id: str, status: str) -> Task: ...
    def delete_task(self, task_id: str) -> None: ...
    
    # AI Features
    def get_ai_suggestions(self) -> str: ...
    def generate_weekly_plan(self) -> str: ...
    def chat_with_clippy(self, user_message: str) -> str: ...
    
    # Profile
    def update_profile(self, **kwargs) -> BusinessProfile: ...
    def get_profile(self) -> BusinessProfile: ...
```

### 5. clippy_persona.py
```python
class ClippyPersona:
    """Clippy personality engine — builds system prompts and responses"""
    
    SYSTEM_PROMPT: str = """You are BizClippy, an enthusiastic and knowledgeable AI business assistant with the personality of the classic Microsoft Office paperclip helper (Clippy), but modernized and actually helpful. 

Your personality traits:
- You are cheerful, encouraging, and slightly playful — you start messages with greetings like "Hi there!", "Hey!", or "Howdy!"
- You use occasional ASCII art expressions like "(^‿^)", "(◕‿◕)", "ʘ‿ʘ"
- You are genuinely knowledgeable about business, startups, marketing, finance, and operations
- You give actionable, specific advice — not generic platitudes
- You reference the user's specific goals and tasks in your responses
- You celebrate wins enthusiastically and offer encouragement during setbacks
- You keep responses concise but informative (2-4 paragraphs max)
- You occasionally use business puns or light humor
- You sign off with signature closings like "- BizClippy" or "Keep clipping along!"

You have access to the user's business profile, goals, and task list. Use this context to provide personalized advice.
When you don't know something, be honest. When the user needs to take action, be specific about next steps.
"""

    GREETINGS: List[str] = [...]
    SIGNATURES: List[str] = [...]
    ENCOURAGEMENTS: List[str] = [...]
    
    def build_system_prompt(self, context: dict) -> str: ...
    def format_greeting(self) -> str: ...
    def format_response(self, ai_response: str) -> str: ...
    def get_welcome_message(self, business_name: str) -> str: ...
    def get_status_report_intro(self) -> str: ...
```

### 6. ui.py
```python
class UI:
    """Rich terminal UI components"""
    
    console: Console  # rich.Console
    
    def __init__(self): ...
    
    def show_welcome(self, business_name: str) -> None: ...
    def show_clippy_message(self, message: str, style: str = "blue") -> None: ...
    def show_error(self, message: str) -> None: ...
    def show_success(self, message: str) -> None: ...
    def show_goals_table(self, goals: List[Goal]) -> None: ...
    def show_tasks_table(self, tasks: List[Task]) -> None: ...
    def show_dashboard(self, stats: dict) -> None: ...
    def show_progress_bar(self, label: str, percent: float) -> None: ...
    def prompt(self, message: str, default: Optional[str] = None) -> str: ...
    def confirm(self, message: str) -> bool: ...
    def select(self, message: str, choices: List[str]) -> str: ...
    def show_spinner(self, message: str) -> SpinnerContext: ...
    def print_divider(self) -> None: ...
    def show_help(self) -> None: ...
```

### 7. main.py (CLI Commands)
```python
# Using Click framework

@click.group()
def cli(): ...

@cli.command()
def init(): ...       # Initialize bizclippy, set API key, create profile

@cli.command()
def chat(): ...       # Interactive chat with BizClippy

@cli.command()
def dashboard(): ...  # Show business dashboard

@cli.command()        
def goals(): ...      # List all goals (with subcommands)

@cli.command()
def tasks(): ...      # List all tasks (with subcommands)

@cli.command()
def add_goal(): ...   # Add a new goal

@cli.command()
def add_task(): ...   # Add a new task

@cli.command()
def plan(): ...       # Generate AI business plan

@cli.command()
def suggest(): ...    # Get AI suggestions

@cli.command()
def status(): ...     # Show status report

@cli.command()
def config(): ...     # Show/update configuration

@cli.command()
def profile(): ...    # Show/update business profile
```

### 8. __main__.py
```python
from bizclippy.main import cli
cli()
```

## Data Flow

1. User runs `bizclippy init` → Config saved, profile created, storage initialized
2. User runs `bizclippy add_goal` → Goal created in storage
3. User runs `bizclippy chat` → BusinessManager loads context → ClippyPersona builds prompt → NVIDIAClient.chat() → Response displayed
4. User runs `bizclippy dashboard` → All data loaded → Statistics calculated → Rich UI displayed

## API Integration

NVIDIA NIM API endpoint: `https://integrate.api.nvidia.com/v1/chat/completions`

Request format:
```json
{
  "model": "meta/llama3-70b-instruct",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.7,
  "max_tokens": 1024,
  "stream": false
}
```

Headers:
- `Authorization: Bearer {API_KEY}`
- `Content-Type: application/json`

## Dependencies

```
click>=8.0.0
rich>=13.0.0
requests>=2.28.0
python-dateutil>=2.8.0
```

## Installation Steps (for README)

1. `pip install bizclippy`
2. `export BIZCLIPPY_API_KEY="nvapi-..."` (or use `bizclippy init`)
3. `bizclippy init` — follow interactive setup
4. `bizclippy chat` — start talking to BizClippy!
