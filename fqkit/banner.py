"""The FQKIT mark printed after install and shown on the package page."""

import os
import sys

# First names of Felix Owusu and Dr. Addo Dorcas Attuabea.
AUTHOR_FIRST_NAMES = ("Felix", "Dorcas")

BANNER = """\
-------------------------------------------
|                                         |
|                        /\\               |
|                       /  \\              |
|                     / /\\ \\              |
|                    / /  \\ \\             |
|                  / /    \\ \\             |
|                 / /______\\ \\            |
|              /_/          \\_\\           |
|                                         |
|  ███████╗ ██████╗ ██╗  ██╗██╗████████╗  |
|  ██╔════╝██╔═══██╗██║ ██╔╝██║╚══██╔══╝  |
|   █████╗  ██║   ██║█████╔╝ ██║   ██║    |
|   ██╔══╝  ██║▄▄ ██║██╔═██╗ ██║   ██║    |
|   ██║     ╚██████╔╝██║  ██╗██║   ██║    |
|   ╚═╝      ╚══▀▀═╝ ╚═╝  ╚═╝╚═╝   ╚═╝    |
|                                         |
|         Felix            Dorcas         |
|                                         |
-------------------------------------------\
"""

_BLUE = "\033[38;5;39m"
_RESET = "\033[0m"


def show(stream=None):
    """Print the mark. Color it when the stream is a terminal."""
    stream = stream or sys.stdout
    text = BANNER
    use_color = bool(getattr(stream, "isatty", lambda: False)()) and not os.environ.get("NO_COLOR")
    if use_color:
        text = f"{_BLUE}{text}{_RESET}"
    print(text, file=stream)
