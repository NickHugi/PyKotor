from __future__ import annotations

import sys
from pathlib import Path
from typing import cast
from unittest import TestCase


REPO_ROOT = Path(__file__).resolve().parents[3]
PYKOTOR_SRC = REPO_ROOT / "Libraries" / "PyKotor" / "src"
UTILITY_SRC = REPO_ROOT / "Libraries" / "Utility" / "src"
for candidate in (PYKOTOR_SRC, UTILITY_SRC):
    candidate_str = str(candidate)
    if candidate.exists() and candidate_str not in sys.path:
        sys.path.append(candidate_str)


from pykotor.resource.formats.twoda import TwoDA, bytes_2da
from pykotor.tslpatcher.diff.analyzers import TwoDADiffAnalyzer
from pykotor.tslpatcher.mods.twoda import AddColumn2DA, AddRow2DA, RowValueConstant


class TestVendorTwoDAComparison(TestCase):
    def test_column_count_mismatch(self) -> None:
        older = TwoDA()
        older.add_column("ABC")
        older.add_column("123")

        newer = TwoDA()
        newer.add_column("ABC")

        self.assertFalse(older.compare(newer, lambda *_: None))

    def test_row_count_mismatch(self) -> None:
        older = TwoDA()
        older.add_column("A")
        older.add_column("B")
        older.add_row("0")
        older.add_row("1")

        newer = TwoDA()
        newer.add_column("A")
        newer.add_column("B")
        newer.add_row("0")

        self.assertFalse(older.compare(newer, lambda *_: None))

    def test_cell_mismatch(self) -> None:
        older = TwoDA()
        older.add_column("A")
        older.add_column("B")
        older.add_row("0")
        older.add_row("1")

        newer = TwoDA()
        newer.add_column("A")
        newer.add_column("B")
        newer.add_row("0")
        newer.add_row("1")
        newer.get_row(0).set_string("A", "asdf")

        self.assertFalse(older.compare(newer, lambda *_: None))

    def test_are_matching(self) -> None:
        older = TwoDA()
        older.add_column("A")
        older.add_column("B")
        older.add_row("0")
        older.add_row("1")
        older.get_row(0).set_string("A", "asdf")

        newer = TwoDA()
        newer.add_column("A")
        newer.add_column("B")
        newer.add_row("0")
        newer.add_row("1")
        newer.get_row(0).set_string("A", "asdf")

        self.assertTrue(older.compare(newer, lambda *_: None))


class TestVendorTwoDADiffAnalyzer(TestCase):
    def test_find_new_column(self) -> None:
        older = TwoDA()
        older.add_column("A")
        older_row0 = older.add_row("0")
        older_row1 = older.add_row("1")
        older.get_row(older_row0).set_string("A", "a0")
        older.get_row(older_row1).set_string("A", "a1")

        newer = TwoDA()
        newer.add_column("A")
        newer.add_column("B")
        newer_row0 = newer.add_row("0")
        newer_row1 = newer.add_row("1")
        newer.get_row(newer_row0).set_string("A", "a0")
        newer.get_row(newer_row1).set_string("A", "a1")
        newer.get_row(newer_row0).set_string("B", "b1")

        analyzer = TwoDADiffAnalyzer()
        modifications = analyzer.analyze(bytes_2da(older), bytes_2da(newer), "test.2da")
        self.assertIsNotNone(modifications)
        assert modifications is not None

        self.assertEqual(len(modifications.modifiers), 1)
        modifier = modifications.modifiers[0]
        self.assertIsInstance(modifier, AddColumn2DA)
        modifier = cast(AddColumn2DA, modifier)

        self.assertEqual(modifier.header, "B")
        self.assertEqual(modifier.default, "****")
        self.assertIn(0, modifier.index_insert)
        self.assertIn(1, modifier.index_insert)
        self.assertIsInstance(modifier.index_insert[0], RowValueConstant)
        self.assertIsInstance(modifier.index_insert[1], RowValueConstant)
        self.assertEqual(modifier.index_insert[0].string, "b1")
        self.assertEqual(modifier.index_insert[1].string, "")

    def test_find_new_row(self) -> None:
        older = TwoDA()
        older.add_column("A")
        older.add_column("B")
        older_row0 = older.add_row("0")
        older_row1 = older.add_row("1")
        older.get_row(older_row0).set_string("A", "a0")
        older.get_row(older_row1).set_string("A", "a1")
        older.get_row(older_row1).set_string("B", "b1")

        newer = TwoDA()
        newer.add_column("A")
        newer.add_column("B")
        newer_row0 = newer.add_row("0")
        newer_row1 = newer.add_row("1")
        newer_row2 = newer.add_row("2")
        newer.get_row(newer_row0).set_string("A", "a0")
        newer.get_row(newer_row1).set_string("A", "a1")
        newer.get_row(newer_row1).set_string("B", "b1")
        newer.get_row(newer_row2).set_string("A", "a2")
        newer.get_row(newer_row2).set_string("B", "b2")

        analyzer = TwoDADiffAnalyzer()
        modifications = analyzer.analyze(bytes_2da(older), bytes_2da(newer), "test.2da")
        self.assertIsNotNone(modifications)
        assert modifications is not None

        self.assertEqual(len(modifications.modifiers), 1)
        modifier = modifications.modifiers[0]
        self.assertIsInstance(modifier, AddRow2DA)
        modifier = cast(AddRow2DA, modifier)

        self.assertEqual(modifier.row_label, "2")
        self.assertIn("A", modifier.cells)
        self.assertIn("B", modifier.cells)
        self.assertIsInstance(modifier.cells["A"], RowValueConstant)
        self.assertIsInstance(modifier.cells["B"], RowValueConstant)
        self.assertEqual(modifier.cells["A"].string, "a2")
        self.assertEqual(modifier.cells["B"].string, "b2")

