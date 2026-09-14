"""Command-line front end for finediff."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

from .core import LineEdit, WordEdit, diff_lines

RED = "\x1b[31m"
GREEN = "\x1b[32m"
CYAN = "\x1b[36m"
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


def _render_edit(edit: LineEdit, use_color: bool) -> list[str]:
    if edit.tag == "equal":
        return [f"  {edit.a}"]
    if edit.tag == "delete":
        prefix = f"{RED}-{RESET}" if use_color else "-"
        return [f"{prefix} {edit.a}"]
    if edit.tag == "insert":
        prefix = f"{GREEN}+{RESET}" if use_color else "+"
        return [f"{prefix} {edit.b}"]
    # replace
    before = _render_words(edit.a_words, "delete", RED, use_color)
    after = _render_words(edit.b_words, "insert", GREEN, use_color)
    prefix_a = f"{RED}-{RESET}" if use_color else "-"
    prefix_b = f"{GREEN}+{RESET}" if use_color else "+"
    return [f"{prefix_a} {before}", f"{prefix_b} {after}"]


@dataclass
class Hunk:
    a_start: int
    a_count: int
    b_start: int
    b_count: int
    edits: list[LineEdit]


def build_hunks(edits: list[LineEdit], context: int) -> list[Hunk]:
    """Group edits into unified-diff style hunks with surrounding context.

    Runs of unchanged lines shorter than 2*context between two changed
    regions get folded into a single hunk instead of splitting them,
    same as `diff -U`.
    """
    n = len(edits)
    # Running count of a/b lines consumed strictly before index i, so a
    # hunk's start line number can be read off without rescanning.
    before_a = [0] * (n + 1)
    before_b = [0] * (n + 1)
    for i, edit in enumerate(edits):
        before_a[i + 1] = before_a[i] + (1 if edit.tag in ("equal", "delete", "replace") else 0)
        before_b[i + 1] = before_b[i] + (1 if edit.tag in ("equal", "insert", "replace") else 0)

    changed = [i for i, e in enumerate(edits) if e.tag != "equal"]
    if not changed:
        return []

    spans: list[tuple[int, int]] = []
    start = prev = changed[0]
    for i in changed[1:]:
        if i - prev <= 2 * context:
            prev = i
        else:
            spans.append((start, prev))
            start = prev = i
    spans.append((start, prev))

    hunks = []
    for start, end in spans:
        lo = max(0, start - context)
        hi = min(n - 1, end + context)
        hunk_edits = edits[lo : hi + 1]
        a_count = before_a[hi + 1] - before_a[lo]
        b_count = before_b[hi + 1] - before_b[lo]
        a_start = before_a[lo] + 1 if a_count else before_a[lo]
        b_start = before_b[lo] + 1 if b_count else before_b[lo]
        hunks.append(Hunk(a_start, a_count, b_start, b_count, hunk_edits))
    return hunks


def _hunk_header(hunk: Hunk, use_color: bool) -> str:
    def side(start: int, count: int) -> str:
        return str(start) if count == 1 else f"{start},{count}"

    header = f"@@ -{side(hunk.a_start, hunk.a_count)} +{side(hunk.b_start, hunk.b_count)} @@"
    return f"{CYAN}{header}{RESET}" if use_color else header


def format_diff(edits: list[LineEdit], use_color: bool, context: int | None = None) -> str:
    if context is None:
        lines = []
        for edit in edits:
            lines.extend(_render_edit(edit, use_color))
        return "\n".join(lines)

    lines = []
    for hunk in build_hunks(edits, context):
        lines.append(_hunk_header(hunk, use_color))
        for edit in hunk.edits:
            lines.extend(_render_edit(edit, use_color))
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
    parser.add_argument(
        "-U",
        "--context",
        type=int,
        default=3,
        metavar="N",
        help="lines of unchanged context to show around each change (default: 3)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="show the whole file instead of splitting it into hunks",
    )
    args = parser.parse_args(argv)

    with open(args.first, encoding="utf-8") as f:
        a_lines = f.read().splitlines()
    with open(args.second, encoding="utf-8") as f:
        b_lines = f.read().splitlines()

    use_color = sys.stdout.isatty() and not args.no_color
    edits = diff_lines(a_lines, b_lines)
    context = None if args.full else args.context
    print(format_diff(edits, use_color, context))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
