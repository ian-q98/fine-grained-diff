# finediff

A regular line diff tells you line 12 changed. It doesn't tell you that
the only thing that changed on line 12 was `timeout=30` becoming
`timeout=60`. You end up scanning the whole line by eye to find the
one word that moved. `finediff` does that scanning for you: it diffs
line by line like any other tool, but for lines that were modified
(rather than added or removed outright) it also diffs the words inside
those two lines and marks up just the parts that differ.

It's standard library only - no dependencies to install.

## Usage

As a CLI:

```
$ python -m finediff.cli before.txt after.txt
@@ -10,3 +10,3 @@
  def connect(host, port):
-     client = Client(host, port, timeout=30)
+     client = Client(host, port, timeout=60)
      return client
```

Output is grouped into unified-diff style hunks, each with a
`@@ -a,b +c,d @@` header giving the line ranges in the original and
changed file. By default each hunk carries 3 lines of unchanged
context on either side of a change; pass `-U N` / `--context N` to
change that, or `--full` to print the whole file with no hunk
splitting (the old default behaviour).

In a real terminal the `-` line has the removed word coloured red and
the `+` line has the added word coloured green; everything unchanged
on those two lines is printed plain. Pass `--no-color` to turn that
off (it's also disabled automatically when output isn't a terminal).

As a library:

```python
from finediff import diff_lines

edits = diff_lines(
    ["def connect(host, port):", "    client = Client(host, port, timeout=30)"],
    ["def connect(host, port):", "    client = Client(host, port, timeout=60)"],
)

for edit in edits:
    if edit.tag == "replace":
        # edit.a_words / edit.b_words are lists of WordEdit(tag, text),
        # tag is one of "equal", "delete", "insert"
        changed = [w.text for w in edit.b_words if w.tag == "insert"]
        print(changed)  # ["60"]
```

`diff_text(a, b)` is a shortcut for `diff_lines` when you have two
whole strings instead of line lists already split.

## How it works

Line-level matching is `difflib.SequenceMatcher` run over the lines of
each file, same as the standard library's own diff tools use. The new
part is what happens to a "replace" block: instead of leaving it as an
opaque old-line/new-line pair, each pair of lines in the block is run
through a second `SequenceMatcher` over their word tokens (words and
whitespace runs, so the original text can be reassembled exactly),
producing the equal/delete/insert tags used for the inline highlight.

## Status

Early. Line and word diffing both work, and the CLI groups output into
unified-diff style hunks with context. Still missing:

- reading from stdin for one file argument
- a `--json` output mode for scripting
- handling very large files without quadratic slowdown
