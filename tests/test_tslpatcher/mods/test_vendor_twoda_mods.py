from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


REPO_ROOT = Path(__file__).resolve().parents[3]
PYKOTOR_SRC = REPO_ROOT / "Libraries" / "PyKotor" / "src"
UTILITY_SRC = REPO_ROOT / "Libraries" / "Utility" / "src"
for candidate in (PYKOTOR_SRC, UTILITY_SRC):
    candidate_str = str(candidate)
    if candidate.exists() and candidate_str not in sys.path:
        sys.path.append(candidate_str)


from pykotor.resource.formats.twoda import TwoDA
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.twoda import (
    AddColumn2DA,
    AddRow2DA,
    ChangeRow2DA,
    CopyRow2DA,
    RowValueConstant,
    RowValueRowIndex,
)
from pykotor.tslpatcher.mods.twoda import Target, TargetType


def _base_twoda() -> TwoDA:
    twoda = TwoDA()
    twoda.add_column("C1")
    twoda.add_column("C2")
    twoda.add_column("C3")
    row0 = twoda.add_row("l0")
    row1 = twoda.add_row("l1")
    twoda.get_row(row0).update_values({"C1": "a0", "C2": "", "C3": ""})
    twoda.get_row(row1).update_values({"C1": "a1", "C2": "", "C3": ""})
    return twoda


class TestVendorAddColumnModifier(TestCase):
    def setUp(self) -> None:
        self.memory = PatcherMemory()
        self.twoda = _base_twoda()

    def test_correct_column_header(self) -> None:
        modifier = AddColumn2DA("add", "NewColumn", "", {}, {})
        modifier.apply(self.twoda, self.memory)
        headers = self.twoda.get_headers()
        self.assertEqual(len(headers), 4)
        self.assertEqual(headers[-1], "NewColumn")

    def test_correct_default_value(self) -> None:
        modifier = AddColumn2DA("add", "NewColumn", "xyz", {}, {})
        modifier.apply(self.twoda, self.memory)
        self.assertEqual(self.twoda.get_cell(0, "NewColumn"), "xyz")
        self.assertEqual(self.twoda.get_cell(1, "NewColumn"), "xyz")


class TestVendorAddRowModifier(TestCase):
    def setUp(self) -> None:
        self.memory = PatcherMemory()
        self.twoda = _base_twoda()

    def test_not_exclusive_no_row_label_no_store(self) -> None:
        modifier = AddRow2DA(
            "add",
            None,
            None,
            {"C1": RowValueConstant("a"), "C2": RowValueConstant("b"), "C3": RowValueConstant("c")},
        )
        modifier.apply(self.twoda, self.memory)
        self.assertEqual(self.twoda.get_height(), 3)
        self.assertEqual(self.twoda.get_row_label(2), "2")
        self.assertEqual(self.twoda.get_cell(2, "C1"), "a")
        self.assertEqual(self.twoda.get_cell(2, "C2"), "b")
        self.assertEqual(self.twoda.get_cell(2, "C3"), "c")

    def test_assign_row_label(self) -> None:
        modifier = AddRow2DA(
            "add",
            None,
            "somelabel",
            {"C1": RowValueConstant("a"), "C2": RowValueConstant("b"), "C3": RowValueConstant("c")},
        )
        modifier.apply(self.twoda, self.memory)
        self.assertEqual(self.twoda.get_height(), 3)
        self.assertEqual(self.twoda.get_row_label(2), "somelabel")

    def test_exclusive_and_existing(self) -> None:
        self.twoda.get_row(0).set_string("C1", "a")
        modifier = AddRow2DA(
            "add",
            "C1",
            None,
            {"C1": RowValueConstant("a"), "C2": RowValueConstant("b"), "C3": RowValueConstant("c")},
        )
        modifier.apply(self.twoda, self.memory)
        self.assertEqual(self.twoda.get_height(), 2)
        self.assertEqual(self.twoda.get_cell(0, "C1"), "a")
        self.assertEqual(self.twoda.get_cell(0, "C2"), "b")
        self.assertEqual(self.twoda.get_cell(0, "C3"), "c")

    def test_exclusive_and_not_existing(self) -> None:
        modifier = AddRow2DA(
            "add",
            "C1",
            None,
            {"C1": RowValueConstant("a"), "C2": RowValueConstant("b"), "C3": RowValueConstant("c")},
        )
        modifier.apply(self.twoda, self.memory)
        self.assertEqual(self.twoda.get_height(), 3)
        self.assertEqual(self.twoda.get_cell(2, "C1"), "a")
        self.assertEqual(self.twoda.get_cell(2, "C2"), "b")
        self.assertEqual(self.twoda.get_cell(2, "C3"), "c")

    def test_store_value(self) -> None:
        modifier = AddRow2DA(
            "add",
            None,
            None,
            {"C1": RowValueConstant("a"), "C2": RowValueConstant("b"), "C3": RowValueConstant("c")},
            store_2da={30: RowValueRowIndex()},
        )
        modifier.apply(self.twoda, self.memory)
        self.assertEqual(self.memory.memory_2da[30], "2")


class TestVendorCopyRowModifier(TestCase):
    def setUp(self) -> None:
        self.memory = PatcherMemory()
        self.twoda = _base_twoda()

    def test_copy_row(self) -> None:
        modifier = CopyRow2DA(
            "copy",
            Target(TargetType.ROW_INDEX, 1),
            None,
            None,
            {"C1": RowValueConstant("a")},
            {},
        )
        modifier.apply(self.twoda, self.memory)
        self.assertEqual(self.twoda.get_height(), 3)
        self.assertEqual(self.twoda.get_row_label(2), "2")
        self.assertEqual(self.twoda.get_cell(2, "C1"), "a")
        self.assertEqual(self.twoda.get_cell(2, "C2"), "")
        self.assertEqual(self.twoda.get_cell(2, "C3"), "")

    def test_copy_row_exclusive_and_existing(self) -> None:
        self.twoda.get_row(0).set_string("C1", "a")
        self.twoda.get_row(1).set_string("C2", "x")
        self.twoda.get_row(1).set_string("C3", "y")
        modifier = CopyRow2DA(
            "copy",
            Target(TargetType.ROW_INDEX, 1),
            "C1",
            None,
            {"C1": RowValueConstant("a"), "C2": RowValueConstant("00")},
            {},
        )
        modifier.apply(self.twoda, self.memory)
        self.assertEqual(self.twoda.get_height(), 2)
        self.assertEqual(self.twoda.get_row_label(0), "l0")
        self.assertEqual(self.twoda.get_cell(0, "C1"), "a")
        self.assertEqual(self.twoda.get_cell(0, "C2"), "00")
        self.assertEqual(self.twoda.get_cell(0, "C3"), "y")


class TestVendorEditRowModifier(TestCase):
    def setUp(self) -> None:
        self.memory = PatcherMemory()
        self.twoda = _base_twoda()

    def test_edit_cells(self) -> None:
        modifier = ChangeRow2DA(
            "change",
            Target(TargetType.ROW_INDEX, 1),
            {"C1": RowValueConstant("a"), "C2": RowValueConstant("b"), "C3": RowValueConstant("c")},
        )
        modifier.apply(self.twoda, self.memory)
        self.assertEqual(self.twoda.get_height(), 2)
        self.assertEqual(self.twoda.get_cell(1, "C1"), "a")
        self.assertEqual(self.twoda.get_cell(1, "C2"), "b")
        self.assertEqual(self.twoda.get_cell(1, "C3"), "c")

    def test_store_value(self) -> None:
        modifier = ChangeRow2DA(
            "change",
            Target(TargetType.ROW_INDEX, 1),
            {"C1": RowValueConstant("a"), "C2": RowValueConstant("b"), "C3": RowValueConstant("c")},
            store_2da={30: RowValueRowIndex()},
        )
        modifier.apply(self.twoda, self.memory)
        self.assertEqual(self.memory.memory_2da[30], "1")

