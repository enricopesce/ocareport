# coding: utf-8
"""Utility functions for terminal output and colors."""

import os
import textwrap


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


def print_info(color, label, value, width=94):
    """Print one consistently aligned summary row, wrapping long values."""
    label_width = 14
    value_width = width - 27
    value_lines = textwrap.wrap(
        str(value),
        width=value_width,
        break_long_words=True,
        break_on_hyphens=False,
    ) or ['']

    for index, line in enumerate(value_lines):
        row_label = label if index == 0 else ''
        print(color(f"{'*' * 5} {row_label:<{label_width}} {line:<{value_width}} {'*' * 5}"))


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
