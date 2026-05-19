#!/bin/bash
# BizClippy — One-Line Installer
# Usage: curl -sSL https://raw.githubusercontent.com/yourusername/bizclippy/main/install.sh | bash

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║   🖇️  Welcome to BizClippy Installer!                    ║"
echo "║      Your AI Business Assistant                          ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo -e "${RED}Error: Python 3.8+ is required but not found.${NC}"
    echo "Please install Python from https://python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python $REQUIRED_VERSION+ is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check pip
echo -e "${BLUE}Checking pip...${NC}"
if ! command -v pip3 &>/dev/null && ! command -v pip &>/dev/null; then
    echo -e "${YELLOW}pip not found. Installing...${NC}"
    $PYTHON_CMD -m ensurepip --upgrade 2>/dev/null || {
        echo -e "${RED}Failed to install pip. Please install manually.${NC}"
        exit 1
    }
fi
echo -e "${GREEN}✓ pip is available${NC}"

# Create virtual environment (optional but recommended)
read -p "Create a virtual environment? [Y/n]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    VENV_DIR="$HOME/.bizclippy-venv"
    echo -e "${BLUE}Creating virtual environment at $VENV_DIR...${NC}"
    $PYTHON_CMD -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
    echo "To activate later: source $VENV_DIR/bin/activate"
fi

# Install BizClippy
echo -e "${BLUE}Installing BizClippy...${NC}"
pip install --upgrade bizclippy 2>/dev/null || {
    echo -e "${YELLOW}PyPI package not found. Installing from source...${NC}"
    # Fallback: clone and install
    TMP_DIR=$(mktemp -d)
    git clone --depth 1 https://github.com/yourusername/bizclippy.git "$TMP_DIR" 2>/dev/null || {
        echo -e "${YELLOW}Git clone failed. Installing from local...${NC}"
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        pip install "$SCRIPT_DIR"
    }
    rm -rf "$TMP_DIR"
}

echo -e "${GREEN}✓ BizClippy installed!${NC}"

# Check for NVIDIA API Key
echo ""
if [ -z "$BIZCLIPPY_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  NVIDIA API Key not found in environment${NC}"
    echo ""
    echo "You'll need a free NVIDIA API key to use AI features."
    echo "Get one at: https://build.nvidia.com/explore/discover"
    echo ""
    read -p "Enter your NVIDIA API Key (or press Enter to skip): " API_KEY
    if [ ! -z "$API_KEY" ]; then
        echo "export BIZCLIPPY_API_KEY=\"$API_KEY\"" >> ~/.bashrc
        echo "export BIZCLIPPY_API_KEY=\"$API_KEY\"" >> ~/.profile
        export BIZCLIPPY_API_KEY="$API_KEY"
        echo -e "${GREEN}✓ API Key saved to ~/.bashrc and ~/.profile${NC}"
    fi
else
    echo -e "${GREEN}✓ NVIDIA API Key found in environment${NC}"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║   🎉 Installation Complete!                              ║"
echo "║                                                          ║"
echo "║   Next steps:                                            ║"
echo "║     1. bizclippy init      → Setup your business         ║"
echo "║     2. bizclippy chat      → Talk to BizClippy           ║"
echo "║     3. bizclippy dashboard → View your business          ║"
echo "║                                                          ║"
echo "║   Need help? Run: bizclippy --help                       ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
