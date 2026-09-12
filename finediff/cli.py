"""Command-line front end for finediff."""

from __future__ import annotations

import argparse
import sys

from .core import LineEdit, WordEdit, diff_lines

RED = "\x1b[31m"
GREEN = "\x1b[32m"
RESET = "\x1b[0m"


def _render_words(words: list[WordEdit], tag: str, color: str, use_color: bool) -> str:
    out = []
    for w in words:
        if w.tag not in (tag, "equal"):
            continue
        if use_color and w.tag != "equal":
            out.append(f"{color}{w.text}{RESET}")
        else:
            out.append(w.text)
    return "".join(out)


def format_diff(edits: list[LineEdit], use_color: bool) -> str:
    lines = []
    for edit in edits:
        if edit.tag == "equal":
            lines.append(f"  {edit.a}")
        elif edit.tag == "delete":
            prefix = f"{RED}-{RESET}" if use_color else "-"
            lines.append(f"{prefix} {edit.a}")
        elif edit.tag == "insert":
            prefix = f"{GREEN}+{RESET}" if use_color else "+"
            lines.append(f"{prefix} {edit.b}")
        elif edit.tag == "replace":
            before = _render_words(edit.a_words, "delete", RED, use_color)
            after = _render_words(edit.b_words, "insert", GREEN, use_color)
            prefix_a = f"{RED}-{RESET}" if use_color else "-"
            prefix_b = f"{GREEN}+{RESET}" if use_color else "+"
            lines.append(f"{prefix_a} {before}")
            lines.append(f"{prefix_b} {after}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="finediff",
        description="Diff two text files, highlighting the words that changed inside modified lines.",
    )
    parser.add_argument("first", help="original file")
    parser.add_argument("second", help="changed file")
    parser.add_argument(
        "--no-color", action="store_true", help="disable ANSI colour even on a terminal"
    )
    args = parser.parse_args(argv)

    with open(args.first, encoding="utf-8") as f:
        a_lines = f.read().splitlines()
    with open(args.second, encoding="utf-8") as f:
        b_lines = f.read().splitlines()

    use_color = sys.stdout.isatty() and not args.no_color
    edits = diff_lines(a_lines, b_lines)
    print(format_diff(edits, use_color))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
