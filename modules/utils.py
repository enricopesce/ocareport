# coding: utf-8
"""Utility functions for terminal output and colors."""

import os


class Color:
    """ANSI color wrapper for terminal output."""
    ESCAPE_SEQ_START = '\033[{}m'
    ESCAPE_SEQ_END = '\033[0m'

    def __init__(self, code):
        self.code = code

    def __call__(self, text):
        try:
            return f'{self.ESCAPE_SEQ_START.format(self.code)}{text}{self.ESCAPE_SEQ_END}'
        except Exception:
            return text


# Color instances
yellow = Color(93)
green = Color(92)
red = Color(91)


def clear():
    """Clear the terminal screen."""
    try:
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')
    except Exception:
        pass


def print_info(color, v1, v2, v3):
    """Print formatted info line."""
    align = '<35' if isinstance(v3, int) else '35'
    print(color(f"{'*'*5:10} {v1:20} {v2:20} {v3:{align}} {'*'*5:5}"))


def print_error(*args, color=None):
    """Print formatted error box."""
    if color is None:
        color = red
    max_length = min(max(len(str(msg)) for msg in args) + 6, 98)
    box_width = max_length + 4
    msg_width = max_length + 2
    blank = color("║" + " " * box_width + "║")

    print(color("\n╔" + "=" * box_width + "╗"))
    print(blank)
    print(color("║"), color("ERROR!".center(msg_width)), color("║"))
    print(blank)

    for msg in args:
        msg = str(msg)
        if len(msg) > 98:
            for chunk in [msg[i:i + 98] for i in range(0, len(msg), 98)]:
                print(color("║"), color(chunk.center(msg_width)), color("║"))
        else:
            print(color("║"), color(msg.center(msg_width)), color("║"))

    print(blank)
    print(color("╚" + "=" * box_width + "╝\n"))
