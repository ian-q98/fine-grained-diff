"""Tests for finediff.core, focused on how replace blocks get paired.

difflib's SequenceMatcher only tells us "these a-lines became those
b-lines" as one block; diff_lines has to decide which a-line pairs
with which b-line for word-level detail, and what happens to the
leftovers when the block is uneven. That pairing logic has no test
coverage elsewhere, so it's covered here directly.
"""

from __future__ import annotations

import unittest

from finediff.core import diff_lines


class ReplaceBlockPairingTests(unittest.TestCase):
    def test_more_deletes_than_inserts_pairs_by_position(self):
        # 3 old lines, 1 new line: only the first old line should get
        # word-level detail against the single replacement; the rest
        # are plain deletes.
        a = ["one", "two", "three"]
        b = ["uno"]
        edits = diff_lines(a, b)

        self.assertEqual([e.tag for e in edits], ["replace", "delete", "delete"])
        self.assertEqual(edits[0].a, "one")
        self.assertEqual(edits[0].b, "uno")
        self.assertIsNotNone(edits[0].a_words)
        self.assertIsNotNone(edits[0].b_words)
        self.assertEqual(edits[1].a, "two")
        self.assertEqual(edits[2].a, "three")

    def test_more_inserts_than_deletes_pairs_by_position(self):
        # 1 old line, 3 new lines: only the first new line is paired
        # with the old one; the rest are plain inserts.
        a = ["uno"]
        b = ["one", "two", "three"]
        edits = diff_lines(a, b)

        self.assertEqual([e.tag for e in edits], ["replace", "insert", "insert"])
        self.assertEqual(edits[0].a, "uno")
        self.assertEqual(edits[0].b, "one")
        self.assertIsNotNone(edits[0].a_words)
        self.assertIsNotNone(edits[0].b_words)
        self.assertEqual(edits[1].b, "two")
        self.assertEqual(edits[2].b, "three")

    def test_uneven_block_pairs_in_original_order(self):
        # Two old lines, three new lines: the two pairs should line up
        # positionally (old[0] with new[0], old[1] with new[1]), not
        # by best word-level match.
        a = ["alpha zero", "beta zero"]
        b = ["alpha one", "beta one", "gamma one"]
        edits = diff_lines(a, b)

        self.assertEqual([e.tag for e in edits], ["replace", "replace", "insert"])
        self.assertEqual((edits[0].a, edits[0].b), ("alpha zero", "alpha one"))
        self.assertEqual((edits[1].a, edits[1].b), ("beta zero", "beta one"))
        self.assertEqual(edits[2].b, "gamma one")

    def test_equal_length_block_pairs_every_line(self):
        a = ["red apple", "green pear"]
        b = ["red banana", "green plum"]
        edits = diff_lines(a, b)

        self.assertEqual([e.tag for e in edits], ["replace", "replace"])
        for edit, old, new in zip(edits, a, b):
            self.assertEqual(edit.a, old)
            self.assertEqual(edit.b, new)
            self.assertIsNotNone(edit.a_words)
            self.assertIsNotNone(edit.b_words)


if __name__ == "__main__":
    unittest.main()
