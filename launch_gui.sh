#!/bin/bash
# Cross-platform launcher for Python Script Runner
# macOS and Linux

cd "$(dirname "$0")"

# ── Check for Python 3 ──────────────────────────────────────────
if ! command -v python3 &> /dev/null; then
    MSG="Python 3 is required but not installed."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        osascript -e "display dialog \"$MSG\n\nPlease download and install Python 3 from:\nhttps://www.python.org/downloads/\" buttons {\"OK\"} default button \"OK\" with icon stop with title \"Python Script Runner\"" 2>/dev/null
    else
        echo "ERROR: $MSG" >&2
        echo "" >&2
        echo "Install Python 3 using your package manager:" >&2
        echo "  Ubuntu/Debian:  sudo apt install python3" >&2
        echo "  Fedora/RHEL:    sudo dnf install python3" >&2
        echo "  Arch:           sudo pacman -S python" >&2
        echo "" >&2
        echo "Then re-run this script." >&2
    fi
    exit 1
fi

# ── Check for tkinter (not bundled on some Linux distros) ────────
if ! python3 -c "import tkinter" 2>/dev/null; then
    MSG="Python 3 tkinter module is required but not installed."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        osascript -e "display dialog \"$MSG\n\nReinstall Python from python.org — the official installer includes tkinter.\" buttons {\"OK\"} default button \"OK\" with icon stop with title \"Python Script Runner\"" 2>/dev/null
    else
        echo "ERROR: $MSG" >&2
        echo "" >&2
        echo "Install tkinter using your package manager:" >&2
        echo "  Ubuntu/Debian:  sudo apt install python3-tk" >&2
        echo "  Fedora/RHEL:    sudo dnf install python3-tkinter" >&2
        echo "  Arch:           sudo pacman -S tk" >&2
        echo "" >&2
        echo "Then re-run this script." >&2
    fi
    exit 1
fi

# ── Check for venv module (not bundled on Debian/Ubuntu) ─────────
if ! python3 -c "import venv" 2>/dev/null; then
    MSG="Python 3 venv module is required but not installed."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        osascript -e "display dialog \"$MSG\n\nReinstall Python from python.org to fix this.\" buttons {\"OK\"} default button \"OK\" with icon stop with title \"Python Script Runner\"" 2>/dev/null
    else
        echo "ERROR: $MSG" >&2
        echo "" >&2
        echo "Install the venv module using your package manager:" >&2
        echo "  Ubuntu/Debian:  sudo apt install python3-venv" >&2
        echo "  Fedora/RHEL:    (included with python3)" >&2
        echo "  Arch:           (included with python)" >&2
        echo "" >&2
        echo "Then re-run this script." >&2
    fi
    exit 1
fi

# ── Launch ───────────────────────────────────────────────────────
python3 PythonScriptRunner.py

# On macOS, close the Terminal window that opened the .command file
if [[ "$OSTYPE" == "darwin"* ]]; then
    osascript -e 'tell application "Terminal" to close front window' &>/dev/null &
fi
