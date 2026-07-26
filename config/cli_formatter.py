# Crewlyze Terminal & CLI Output Formatter
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

import os
import sys

# Enable ANSI escape sequence support on Windows terminals
if sys.platform == "win32":
    try:
        os.system("")
    except Exception:
        pass

# Color palette definition (ANSI 256 / Standard Colors)
CLR_RESET = "\x1b[0m"
CLR_BOLD = "\x1b[1m"
CLR_DIM = "\x1b[2m"
CLR_ITALIC = "\x1b[3m"
CLR_UNDERLINE = "\x1b[4m"

# Vivid Colors
CYAN = "\x1b[38;5;51m"
BRIGHT_CYAN = "\x1b[38;5;87m"
BLUE = "\x1b[38;5;39m"
PURPLE = "\x1b[38;5;141m"
MAGENTA = "\x1b[38;5;201m"
GREEN = "\x1b[38;5;48m"
BRIGHT_GREEN = "\x1b[38;5;82m"
YELLOW = "\x1b[38;5;220m"
ORANGE = "\x1b[38;5;208m"
RED = "\x1b[38;5;196m"
GRAY = "\x1b[38;5;245m"
WHITE = "\x1b[38;5;255m"

# Gradient Header Text
def print_banner():
    """Renders a colorful, stylish Cyberpunk CLI banner for Crewlyze."""
    banner = f"""
{CYAN}  ██████╗██████╗ ███████╗██╗    ██╗██╗  ██╗   ██╗███████╗███████╗{CLR_RESET}
{BRIGHT_CYAN}  ██╔════╝██╔══██╗██╔════╝██║    ██║██║  ╚██╗ ██╔╝╚══███╔╝██╔════╝{CLR_RESET}
{PURPLE}  ██║     ██████╔╝█████╗  ██║ █╗ ██║██║   ╚████╔╝   ███╔╝ █████╗  {CLR_RESET}
{MAGENTA}  ██║     ██╔══██╗██╔══╝  ██║███╗██║██║    ╚██╔╝   ███╔╝  ██╔══╝  {CLR_RESET}
{RED}  ╚██████╗██║  ██║███████╗╚███╔███╔╝███████╗██║   ███████╗███████╗{CLR_RESET}
{ORANGE}   ╚═════╝╚═╝  ╚═╝╚══════╝ ╚══╝╚══╝ ╚══════╝╚═╝   ╚══════╝╚══════╝{CLR_RESET}

  {CLR_BOLD}{WHITE}Autonomous Multi-Agent Business Intelligence & Data Engineering Platform{CLR_RESET}
  {GRAY}Powered by CrewAI & FastAPI • v1.0.9{CLR_RESET}
"""
    print(banner)


def badge(label: str, color_code: str = CYAN) -> str:
    """Format a styled badge string like [SUCCESS] or [INFO]."""
    return f"{color_code}{CLR_BOLD}[{label}]{CLR_RESET}"


def log_info(msg: str):
    """Print an informational log line."""
    print(f"{badge('INFO', CYAN)} {msg}")


def log_success(msg: str):
    """Print a success log line."""
    print(f"{badge('SUCCESS', BRIGHT_GREEN)} {msg}")


def log_warn(msg: str):
    """Print a warning log line."""
    print(f"{badge('WARNING', YELLOW)} {msg}")


def log_error(msg: str):
    """Print an error log line."""
    print(f"{badge('ERROR', RED)} {msg}")


def log_step(step_num: int, title: str, desc: str = ""):
    """Print a styled step indicator for workflows."""
    extra = f" {GRAY}— {desc}{CLR_RESET}" if desc else ""
    print(f"{PURPLE}{CLR_BOLD}➔ Step {step_num}:{CLR_RESET} {WHITE}{CLR_BOLD}{title}{CLR_RESET}{extra}")


def print_server_ready(url: str, port: int):
    """Prints a styled server ready card."""
    box_top    = f"{CYAN}┌─────────────────────────────────────────────────────────────┐{CLR_RESET}"
    box_bottom = f"{CYAN}└─────────────────────────────────────────────────────────────┘{CLR_RESET}"
    
    print("\n" + box_top)
    print(f"{CYAN}│{CLR_RESET}  {BRIGHT_GREEN}{CLR_BOLD}🚀 CREWLYZE ENGINE IS LIVE & READY!{CLR_RESET}                        {CYAN}│{CLR_RESET}")
    print(f"{CYAN}│{CLR_RESET}                                                             {CYAN}│{CLR_RESET}")
    print(f"{CYAN}│{CLR_RESET}  {WHITE}Web Dashboard URL:{CLR_RESET} {BRIGHT_CYAN}{CLR_BOLD}{url}{CLR_RESET}")
    print(f"{CYAN}│{CLR_RESET}  {WHITE}Local Port:{CLR_RESET}        {YELLOW}{port}{CLR_RESET}")
    print(f"{CYAN}│{CLR_RESET}  {WHITE}Status:{CLR_RESET}            {BRIGHT_GREEN}Active & Listening{CLR_RESET}")
    print(box_bottom + "\n")
