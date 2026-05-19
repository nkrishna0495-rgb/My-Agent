# 🖇️ BizClippy — Your AI Business Assistant

> *"It looks like you're building a business! Need help?"*

BizClippy is an AI-powered CLI business assistant with the charm and personality of the classic Microsoft Office paperclip — but actually helpful. Powered by NVIDIA's AI APIs, BizClippy helps you set goals, track tasks, generate business plans, and get personalized advice to grow your business.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![NVIDIA](https://img.shields.io/badge/powered%20by-NVIDIA-76B900)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 💬 **Interactive Chat** | Have natural conversations with BizClippy about your business |
| 🎯 **Goal Management** | Set, track, and achieve business goals with milestones |
| ✅ **Task Tracking** | Create, prioritize, and manage tasks linked to your goals |
| 📊 **Rich Dashboard** | Beautiful terminal dashboard with progress bars and stats |
| 🧠 **AI-Powered Insights** | Get personalized business advice powered by NVIDIA AI |
| 📋 **Business Plans** | Generate complete business plans with one command |
| 📈 **Progress Analytics** | Track completion rates and get AI-driven suggestions |
| 🖇️ **Clippy Personality** | Fun, encouraging personality that makes work enjoyable |

---

## 🚀 Installation

### Option 1: Quick Install (Recommended)

```bash
# Using the install script
curl -sSL https://raw.githubusercontent.com/yourusername/bizclippy/main/install.sh | bash
```

### Option 2: Install from Source

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/bizclippy.git
cd bizclippy

# 2. Create a virtual environment (recommended)
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install the package
pip install -e .
```

### Option 3: Install with pip

```bash
pip install bizclippy
```

---

## 🔑 Setup Your NVIDIA API Key

BizClippy uses NVIDIA's AI APIs to provide intelligent responses. You need a free API key:

### Step 1: Get Your API Key
1. Go to [NVIDIA Build](https://build.nvidia.com/explore/discover)
2. Sign up or log in (it's free!)
3. Generate an API key
4. Copy your key (starts with `nvapi-`)

### Step 2: Configure BizClippy

**Option A — Environment Variable (Recommended):**

```bash
# Add to your ~/.bashrc or ~/.zshrc
export BIZCLIPPY_API_KEY="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"

# Reload your shell
source ~/.bashrc  # or source ~/.zshrc
```

**Option B — Via BizClippy Init:**

```bash
bizclippy init
# You'll be prompted to enter your API key interactively
```

---

## 📖 Quick Start Guide

### Step 1: Initialize BizClippy

```bash
$ bizclippy init

🖇️  Welcome to BizClippy!
─────────────────────────────────
It looks like you're starting a new business adventure!
Let's get you set up...

? Enter your NVIDIA API Key: nvapi-***
? Business name: My Awesome Startup
? Industry: Technology
? Mission statement: To revolutionize...
? Target audience: Small businesses
? Revenue model: SaaS subscription
? Current stage: mvp

✓ Configuration saved!
✓ Business profile created!
```

### Step 2: Start Chatting with BizClippy

```bash
$ bizclippy chat

🖇️  BizClippy
─────────────────────────────────
Hi there! I'm BizClippy, your AI business assistant!
It looks like you're working on My Awesome Startup. How can I help you today?

You: I need help with marketing
BizClippy: Hey! Great question about marketing for My Awesome Startup!
Since you're in the SaaS space targeting small businesses, I'd recommend...

You: quit
BizClippy: See you later! Keep clipping along! 👋
```

### Step 3: View Your Dashboard

```bash
$ bizclippy dashboard

╔══════════════════════════════════════════════════════════╗
║              📊 MY AWESOME STARTUP DASHBOARD             ║
╠══════════════════════════════════════════════════════════╣
║  Total Goals: 3     Active: 2     Completed: 1          ║
║  Tasks: 12          Done: 5        Pending: 7            ║
║  Completion Rate: ████████████░░░░ 42%                   ║
╚══════════════════════════════════════════════════════════╝
```

### Step 4: Add Goals and Tasks

```bash
# Add a business goal
$ bizclippy add-goal
? Goal title: Launch Product v1.0
? Description: Release the first version of our SaaS product
? Deadline (YYYY-MM-DD): 2024-12-31

# Add a task
$ bizclippy add-task
? Task title: Design landing page
? Description: Create a compelling landing page for our product
? Link to goal? (optional): Launch Product v1.0
? Priority: high
? Due date: 2024-06-15

# Mark a task complete
$ bizclippy complete-task
# Shows list of tasks — select one to complete
```

### Step 5: Get AI Insights

```bash
# Generate a business plan
$ bizclippy plan
🤔 Thinking...

📋 BUSINESS PLAN FOR MY AWESOME STARTUP
═══════════════════════════════════════

1. EXECUTIVE SUMMARY
My Awesome Startup is a SaaS company targeting...

# Get AI suggestions
$ bizclippy suggest
🤔 Analyzing your goals and tasks...

Here are my top 3 suggestions for this week:
1. Focus on completing the landing page design...
2. Set up analytics tracking before launch...
3. Reach out to 5 potential beta customers...
```

---

## 📚 Command Reference

| Command | Description |
|---------|-------------|
| `bizclippy init` | First-time setup wizard |
| `bizclippy chat` | Interactive chat with BizClippy |
| `bizclippy dashboard` | View business dashboard |
| `bizclippy goals` | List all goals |
| `bizclippy add-goal` | Create a new goal |
| `bizclippy tasks` | List all tasks |
| `bizclippy add-task` | Create a new task |
| `bizclippy complete-task` | Mark a task as done |
| `bizclippy plan` | Generate AI business plan |
| `bizclippy suggest` | Get AI suggestions |
| `bizclippy status` | View detailed status report |
| `bizclippy profile` | View business profile |
| `bizclippy edit-profile` | Update business profile |
| `bizclippy config` | View configuration |
| `bizclippy --help` | Show help message |

---

## 🏗️ Architecture

```
bizclippy/
├── __init__.py              # Package initialization
├── __main__.py              # Entry point (python -m bizclippy)
├── main.py                  # CLI commands (Click)
├── config.py                # Configuration management
├── storage.py               # JSON-based data persistence
├── api_client.py            # NVIDIA NIM API client
├── business_manager.py      # Business logic & AI orchestration
├── clippy_persona.py        # Clippy personality engine
├── ui.py                    # Rich terminal UI components
└── utils.py                 # Helper functions
```

---

## ⚙️ Configuration

Configuration is stored in `~/.bizclippy/config.json`:

```json
{
  "NVIDIA_API_KEY": "nvapi-...",
  "MODEL_NAME": "meta/llama3-70b-instruct",
  "API_BASE": "https://integrate.api.nvidia.com/v1",
  "DATA_DIR": "~/.bizclippy"
}
```

Environment variables (override config file):
- `BIZCLIPPY_API_KEY` — Your NVIDIA API key
- `BIZCLIPPY_MODEL` — Model name to use
- `BIZCLIPPY_API_BASE` — API endpoint URL

---

## 📂 Data Storage

All data is stored locally in `~/.bizclippy/`:

| File | Contents |
|------|----------|
| `config.json` | API key and settings |
| `business_profile.json` | Your business information |
| `goals.json` | Business goals and milestones |
| `tasks.json` | Tasks and their status |
| `chat_history.json` | Chat conversation history |

---

## 🛠️ Development

```bash
# Clone the repo
git clone https://github.com/yourusername/bizclippy.git
cd bizclippy

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/
```

---

## 📝 Requirements

- Python 3.8 or higher
- NVIDIA API key (free at [build.nvidia.com](https://build.nvidia.com/explore/discover))
- Internet connection for AI features (offline mode works for basic features)

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Powered by [NVIDIA NIM](https://www.nvidia.com/en-us/ai/)
- Inspired by the classic Microsoft Office Clippy (RIP 🪦)
- Built with [Click](https://click.palletsprojects.com/) and [Rich](https://rich.readthedocs.io/)

---

<div align="center">

**Made with 🖇️ by BizClippy Team**

*"Looks like you're building something amazing! Need help?"*

</div>
