# Crewlyze Terminal & CLI Output Formatter
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

import os
import re
import sys
import unicodedata

# Ensure UTF-8 output encoding across all Windows shells
try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Enable ANSI VT100 escape sequence processing on Windows terminals
if sys.platform == "win32":
    try:
        os.system("")
    except Exception:
        pass


def rgb(r: int, g: int, b: int) -> str:
    """Generate 24-bit TrueColor ANSI escape sequence."""
    return f"\x1b[38;2;{r};{g};{b}m"


# Text Styling
CLR_RESET = "\x1b[0m"
CLR_BOLD = "\x1b[1m"
CLR_DIM = "\x1b[2m"
CLR_ITALIC = "\x1b[3m"
CLR_UNDERLINE = "\x1b[4m"

# Signature Crimson Palette (Matches web frontend #ff252a / #ff5a5e)
CRIMSON_PEAK = rgb(255, 130, 136)   # Coral / Highlight Red
CRIMSON_LIGHT = rgb(255, 88, 94)    # Vivid Light Crimson
CRIMSON = rgb(255, 37, 42)          # Core Brand Crimson (#ff252a)
SCARLET = rgb(228, 18, 25)          # Deep Scarlet
RUBY = rgb(190, 10, 18)             # Deep Ruby Red
WINE = rgb(140, 4, 12)              # Velvet Shadow Red

# Interface Accents
GREEN = rgb(16, 185, 129)           # Emerald Green (#10b981)
BRIGHT_GREEN = rgb(52, 211, 153)
YELLOW = rgb(245, 158, 11)          # Amber (#f59e0b)
AMBER = rgb(245, 158, 11)
CYAN = rgb(255, 110, 115)           # Crimson-cyan remapped to warm accent
BRIGHT_CYAN = rgb(255, 140, 145)
BLUE = rgb(96, 165, 250)
PURPLE = rgb(255, 75, 82)           # Remapped to crimson brand
MAGENTA = rgb(255, 45, 55)
ORANGE = rgb(251, 146, 60)
RED = rgb(255, 37, 42)
GRAY = rgb(160, 160, 172)
DARK_GRAY = rgb(95, 95, 105)
WHITE = rgb(245, 245, 250)

# ASCII Art Logo for Crewlyze
BANNER_ASCII = [
    "  ██████╗██████╗ ███████╗██╗    ██╗██╗  ██╗   ██╗███████╗███████╗",
    "  ██╔════╝██╔══██╗██╔════╝██║    ██║██║  ╚██╗ ██╔╝╚══███╔╝██╔════╝",
    "  ██║     ██████╔╝█████╗  ██║ █╗ ██║██║   ╚████╔╝   ███╔╝ █████╗  ",
    "  ██║     ██╔══██╗██╔══╝  ██║███╗██║██║    ╚██╔╝   ███╔╝  ██╔══╝  ",
    "  ╚██████╗██║  ██║███████╗╚███╔███╔╝███████╗██║   ███████╗███████╗",
    "   ╚═════╝╚═╝  ╚═╝╚══════╝ ╚══╝╚══╝ ╚══════╝╚═╝   ╚══════╝╚══════╝",
]

# 6-Tier Crimson Sunset Gradient
GRADIENT_TIERS = [
    CRIMSON_PEAK,
    CRIMSON_LIGHT,
    CRIMSON,
    SCARLET,
    RUBY,
    WINE,
]


def print_banner(style: str = "sunset"):
    """
    Renders an awesome red-gradiented CLI banner for Crewlyze.
    Supports 'sunset' (vertical 6-tier gradient) and 'fire' (2D diagonal matrix).
    """
    print()
    if style == "fire":
        # 2D diagonal flame matrix
        for i, line in enumerate(BANNER_ASCII):
            out = ""
            total = len(line)
            for j, ch in enumerate(line):
                t = 0.45 * (j / max(total - 1, 1)) + 0.55 * (i / (len(BANNER_ASCII) - 1))
                r = int(255 * (1 - t) + 175 * t)
                g = int(130 * (1 - t) ** 1.6 + 8 * t)
                b = int(138 * (1 - t) ** 1.6 + 16 * t)
                out += f"{CLR_BOLD}{rgb(r, g, b)}{ch}"
            print(out + CLR_RESET)
    else:
        # 6-Tier Crimson Sunset
        for i, line in enumerate(BANNER_ASCII):
            color = GRADIENT_TIERS[i] if i < len(GRADIENT_TIERS) else CRIMSON
            print(f"{CLR_BOLD}{color}{line}{CLR_RESET}")

    print()
    print(f"  {CLR_BOLD}{WHITE}Autonomous Multi-Agent Business Intelligence & Data Engineering Platform{CLR_RESET}")
    print(
        f"  {CRIMSON_LIGHT}•{CLR_RESET} {GRAY}Powered by {CLR_BOLD}{WHITE}CrewAI{CLR_RESET} {GRAY}&{CLR_RESET} "
        f"{CLR_BOLD}{WHITE}FastAPI{CLR_RESET}   {DARK_GRAY}│{CLR_RESET}   {CRIMSON_LIGHT}v1.0.9{CLR_RESET}   "
        f"{DARK_GRAY}│{CLR_RESET}   {GREEN}● Core Online{CLR_RESET}"
    )
    print()


def _term_display_width(s: str) -> int:
    """Calculate terminal visual column width, taking into account emojis and ANSI escape codes."""
    clean = re.sub(r"\x1b\[[0-9;]*m", "", s)
    width = 0
    for ch in clean:
        code = ord(ch)
        if 0x1F300 <= code <= 0x1FAFF:
            width += 2
        elif unicodedata.east_asian_width(ch) in ("W", "F"):
            width += 2
        else:
            width += 1
    return width


def badge(label: str, color_code: str = CRIMSON_LIGHT) -> str:
    """Format a styled badge string like [SUCCESS] or [INFO]."""
    return f"{color_code}{CLR_BOLD}[{label}]{CLR_RESET}"


def log_info(msg: str):
    """Print an informational log line."""
    print(f"{badge('INFO', CRIMSON_LIGHT)} {msg}")


def log_success(msg: str):
    """Print a success log line."""
    print(f"{badge('SUCCESS', GREEN)} {msg}")


def log_warn(msg: str):
    """Print a warning log line."""
    print(f"{badge('WARNING', AMBER)} {msg}")


def log_error(msg: str):
    """Print an error log line."""
    print(f"{badge('ERROR', CRIMSON)} {msg}")


def log_step(step_num: int, title: str, desc: str = ""):
    """Print a styled step indicator for workflows."""
    extra = f" {GRAY}— {desc}{CLR_RESET}" if desc else ""
    print(f"{CRIMSON_LIGHT}{CLR_BOLD}➔ Step {step_num}:{CLR_RESET} {WHITE}{CLR_BOLD}{title}{CLR_RESET}{extra}")


def print_server_ready(url: str, port: int):
    """Prints an awesome, pixel-perfect red-themed server status card."""
    inner_width = 61
    box_top = f"{CRIMSON}╭" + "─" * inner_width + f"╮{CLR_RESET}"
    box_mid = f"{CRIMSON}├" + "─" * inner_width + f"┤{CLR_RESET}"
    box_bottom = f"{CRIMSON}╰" + "─" * inner_width + f"╯{CLR_RESET}"

    def box_row(content: str) -> str:
        w = _term_display_width(content)
        pad = max(0, inner_width - 2 - w)
        return f"{CRIMSON}│{CLR_RESET}  {content}" + (" " * pad) + f"{CRIMSON}│{CLR_RESET}"

    print(box_top)
    print(box_row(f"{CLR_BOLD}{CRIMSON_PEAK}🚀 CREWLYZE ENGINE IS LIVE & READY!{CLR_RESET}"))
    print(box_mid)
    print(box_row(f"{GRAY}🌐 Web Dashboard URL :{CLR_RESET} {CLR_BOLD}{WHITE}{url}{CLR_RESET}"))
    print(box_row(f"{GRAY}🔌 Local Port        :{CLR_RESET} {CLR_BOLD}{AMBER}{port}{CLR_RESET}"))
    print(box_row(f"{GRAY}🟢 System Status     :{CLR_RESET} {CLR_BOLD}{GREEN}Active & Listening{CLR_RESET}"))
    print(box_row(f"{GRAY}🤖 Multi-Agent Fleet :{CLR_RESET} {CLR_BOLD}{CRIMSON_LIGHT}6 Specialized Crews Online{CLR_RESET}"))
    print(box_bottom)
    print(f"  {CLR_DIM}{GRAY}💡 Press {CLR_BOLD}{CRIMSON_LIGHT}Ctrl+C{CLR_RESET}{CLR_DIM}{GRAY} in this terminal anytime to stop the server.{CLR_RESET}\n")
