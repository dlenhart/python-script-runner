class Config:

    APP_NAME = "Python Script Runner"
    APP_VERSION = "1.0"
    APP_DESCRIPTION = "A GUI utility for running Python scripts -- by Drew D. Lenhart"
    APP_FRAMEWORK = "Python and tkinter"

    WINDOW_WIDTH = 750
    WINDOW_HEIGHT = 550

    BG_DARK = "#1e1e1e"
    BG_MID = "#3c3c3c"
    BG_HOVER = "#4a4a4a"
    FG_PRIMARY = "#e0e0e0"
    FG_SECONDARY = "#a0a0a0"
    ACCENT_BLUE = "#4a9eff"
    ACCENT_GREEN = "#4caf50"
    ACCENT_RED = "#e74c3c"
    BORDER_COLOR = "#555555"

    TAB_INDICATOR_RUNNING = "\U0001F7E2"
    TAB_INDICATOR_ERROR = "\u274C"
    TAB_INDICATOR_COMPLETE = "\u2705"
    TAB_INDICATOR_STOPPED = "\u2716"
    TAB_INDICATOR_WARNING = "\u26A0"

    DEFAULT_FONT = ("Arial", 12)
    HEADER_FONT = ("Arial", 20, "bold")
    CONSOLE_FONT = ("Consolas", 10)
    BUTTON_FONT = ("Arial", 12, "bold")
    STATUS_BAR_FONT = ("Arial", 9)

    CONSOLE_BG = "#1a1a1a"
    CONSOLE_FG = "#4a9eff"
    CONSOLE_HEIGHT = 15
    CONSOLE_WIDTH = 80

    SCRIPTS_DIR = "scripts"
    MANIFESTS_DIR = "scripts/manifests"
    MANIFEST_EXTENSION = ".manifest.json"
    REQUIREMENTS_FILE = "requirements.txt"

    MANAGE_WINDOW_WIDTH = 700
    MANAGE_WINDOW_HEIGHT = 500

    BUTTON_HEIGHT = 2
    BUTTON_DISABLED_BG = "#2a2a2a"
    BUTTON_DISABLED_FG = "#666666"

    MANIFEST_REQUIRED_FIELDS = ["tab_name", "script_file"]


def about_text():
    return (
        f"{Config.APP_NAME}\n\n"
        f"{Config.APP_DESCRIPTION}\n\n"
        f"Version: {Config.APP_VERSION}\n"
        f"Built with {Config.APP_FRAMEWORK}"
    )
