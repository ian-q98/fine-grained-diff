"""Line- and word-level diffing built on difflib's SequenceMatcher.

Ordinary line diffs mark a whole line as changed even when only one
word in it moved. This module adds a second pass: for lines that
difflib pairs up as a "replace", it diffs the words inside those two
lines too, so a caller can show exactly what changed instead of the
whole line.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

# Whitespace and non-whitespace runs, kept as separate tokens so the
# original line can be reassembled exactly by joining the pieces.
_WORD_RE = re.compile(r"\s+|\S+")


def tokenize_words(line: str) -> list[str]:
    """Split a line into words and whitespace runs, preserving both."""
    return _WORD_RE.findall(line)


@dataclass
class WordEdit:
    tag: str  # "equal", "delete", "insert"
    text: str


def word_diff(a: str, b: str) -> tuple[list[WordEdit], list[WordEdit]]:
    """Return per-word edits for the "before" and "after" versions of a line."""
    a_words = tokenize_words(a)
    b_words = tokenize_words(b)
    matcher = SequenceMatcher(None, a_words, b_words, autojunk=False)
    before: list[WordEdit] = []
    after: list[WordEdit] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            before.append(WordEdit("equal", "".join(a_words[i1:i2])))
            after.append(WordEdit("equal", "".join(b_words[j1:j2])))
        else:
            if i1 != i2:
                before.append(WordEdit("delete", "".join(a_words[i1:i2])))
            if j1 != j2:
                after.append(WordEdit("insert", "".join(b_words[j1:j2])))
    return before, after


@dataclass
class LineEdit:
    tag: str  # "equal", "delete", "insert", "replace"
    a: str | None = None
    b: str | None = None
    a_words: list[WordEdit] | None = None
    b_words: list[WordEdit] | None = None


def diff_lines(a_lines: list[str], b_lines: list[str]) -> list[LineEdit]:
    """Diff two sequences of lines, adding word-level detail to replacements."""
    matcher = SequenceMatcher(None, a_lines, b_lines, autojunk=False)
    edits: list[LineEdit] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for a_line, b_line in zip(a_lines[i1:i2], b_lines[j1:j2]):
                edits.append(LineEdit("equal", a=a_line, b=b_line))
        elif tag == "delete":
            for a_line in a_lines[i1:i2]:
                edits.append(LineEdit("delete", a=a_line))
        elif tag == "insert":
            for b_line in b_lines[j1:j2]:
                edits.append(LineEdit("insert", b=b_line))
        elif tag == "replace":
            a_block = a_lines[i1:i2]
            b_block = b_lines[j1:j2]
            # Pair lines 1:1 where possible so a replacement reads as
            # "this line became that line" instead of an unrelated
            # delete/insert pile; leftovers fall back to plain edits.
            paired = min(len(a_block), len(b_block))
            for k in range(paired):
                a_words, b_words = word_diff(a_block[k], b_block[k])
                edits.append(
                    LineEdit(
                        "replace",
                        a=a_block[k],
                        b=b_block[k],
                        a_words=a_words,
                        b_words=b_words,
                    )
                )
            for a_line in a_block[paired:]:
                edits.append(LineEdit("delete", a=a_line))
            for b_line in b_block[paired:]:
                edits.append(LineEdit("insert", b=b_line))
    return edits


def diff_text(a: str, b: str) -> list[LineEdit]:
    """Convenience wrapper for diffing two whole strings by line."""
    return diff_lines(a.splitlines(), b.splitlines())
