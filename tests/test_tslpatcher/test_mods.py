from __future__ import annotations

import pathlib
import sys
import unittest
from pathlib import PureWindowsPath
from typing import TYPE_CHECKING, cast
from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from utility.common.geometry import Vector3, Vector4  # pyright: ignore[reportMissingImports]  # noqa: E402
from pykotor.common.language import LocalizedString  # pyright: ignore[reportMissingImports]  # noqa: E402
from pykotor.common.misc import Game, ResRef  # pyright: ignore[reportMissingImports]  # noqa: E402
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff  # pyright: ignore[reportMissingImports]  # noqa: E402
from pykotor.resource.formats.gff.gff_data import GFF, GFFFieldType, GFFList, GFFStruct  # pyright: ignore[reportMissingImports]  # noqa: E402
from pykotor.resource.formats.ssf.ssf_auto import bytes_ssf, read_ssf  # pyright: ignore[reportMissingImports]  # noqa: E402
from pykotor.resource.formats.ssf.ssf_data import SSF, SSFSound  # pyright: ignore[reportMissingImports]  # noqa: E402
from pykotor.resource.formats.tlk.tlk_data import TLK  # pyright: ignore[reportMissingImports]  # noqa: E402
from pykotor.resource.formats.twoda.twoda_auto import bytes_2da, read_2da  # pyright: ignore[reportMissingImports]  # noqa: E402
from pykotor.resource.formats.twoda.twoda_data import TwoDA  # pyright: ignore[reportMissingImports]  # noqa: E402
from pykotor.tslpatcher.logger import PatchLogger  # pyright: ignore[reportMissingImports]  # noqa: E402
from pykotor.tslpatcher.memory import (  # pyright: ignore[reportMissingImports]  # noqa: E402
    NoTokenUsage,
    PatcherMemory,
    TokenUsage2DA,
    TokenUsageTLK,
)
from pykotor.tslpatcher.mods.gff import (  # pyright: ignore[reportMissingImports]  # noqa: E402
    AddFieldGFF,
    AddStructToListGFF,
    FieldValue2DAMemory,
    FieldValueConstant,
    FieldValueTLKMemory,
    LocalizedStringDelta,
    ModificationsGFF,
    ModifyFieldGFF,
)
from pykotor.tslpatcher.mods.ssf import ModificationsSSF, ModifySSF  # pyright: ignore[reportMissingImports]  # noqa: E402
from pykotor.tslpatcher.mods.tlk import ModificationsTLK, ModifyTLK  # pyright: ignore[reportMissingImports]  # noqa: E402
from pykotor.tslpatcher.mods.twoda import (  # pyright: ignore[reportMissingImports]  # noqa: E402
    AddColumn2DA,
    AddRow2DA,
    ChangeRow2DA,
    CopyRow2DA,
    Modifications2DA,
    RowValue2DAMemory,
    RowValueConstant,
    RowValueHigh,
    RowValueRowCell,
    RowValueRowIndex,
    RowValueRowLabel,
    RowValueTLKMemory,
    Target,
    TargetType,
)

if TYPE_CHECKING:
    from pykotor.tslpatcher.mods.gff import (  # pyright: ignore[reportMissingImports]  # noqa: E402
        ModifyGFF,
    )

# TODO(NickHugi): Error, Warning tracking


class TestManipulateTLK(TestCase):
    def test_apply_append(self):
        memory = PatcherMemory()

        config = ModificationsTLK()

        m1 = ModifyTLK(0)
        m1.text = "Append2"
        m1.sound = ResRef.from_blank()
        m2 = ModifyTLK(1)
        m2.text = "Append1"
        m2.sound = ResRef.from_blank()

        config.modifiers.append(m1)
        config.modifiers.append(m2)

        dialog_tlk = TLK()
        dialog_tlk.add("Old1")
        dialog_tlk.add("Old2")

        config.apply(dialog_tlk, memory, PatchLogger(), Game.K1)

        self.assertEqual(4, len(dialog_tlk))
        get_2 = dialog_tlk.get(2)
        get_3 = dialog_tlk.get(3)
        if get_2 is None or get_3 is None:
            raise AssertionError("get_2 or get_3 is None")
        self.assertEqual("Append2", get_2.text)
        self.assertEqual("Append1", get_3.text)

        assert memory.memory_str[0] == 2
        assert memory.memory_str[1] == 3

        # [Dialog] [Append] [Token] [Text]
        # 0        -        -       Old1
        # 1        -        -       Old2
        # 2        1        0       Append2
        # 3        0        1       Append1

    def test_apply_replace(self):
        memory = PatcherMemory()

        config = ModificationsTLK()

        m1 = ModifyTLK(1)
        m1.text = "Replace2"
        m1.sound = ResRef.from_blank()
        m1.is_replacement = True
        m2 = ModifyTLK(2)
        m2.text = "Replace3"
        m2.sound = ResRef.from_blank()
        m2.is_replacement = True

        config.modifiers.append(m1)
        config.modifiers.append(m2)

        dialog_tlk = TLK()
        dialog_tlk.add("Old1")
        dialog_tlk.add("Old2")
        dialog_tlk.add("Old3")
        dialog_tlk.add("Old4")

        config.apply(dialog_tlk, memory, PatchLogger(), Game.K1)

        self.assertEqual(4, len(dialog_tlk))
        get_1 = dialog_tlk.get(1)
        get_2 = dialog_tlk.get(2)
        if get_1 is None or get_2 is None:
            raise AssertionError("get_1 or get_2 is None")
        self.assertEqual("Replace2", get_1.text)
        self.assertEqual("Replace3", get_2.text)

        # Replace operations no longer store memory
        self.assertNotIn(1, memory.memory_str)
        self.assertNotIn(2, memory.memory_str)

        # [Dialog] [Append] [Token] [Text]
        # 0        -        -       Old1
        # 1        -        -       Old2
        # 2        1        0       Append2
        # 3        0        1       Append1


class TestManipulate2DA(TestCase):
    # region Change Row
    def test_change_existing_rowindex(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        logger = PatchLogger()
        config = Modifications2DA("")
        config.modifiers.append(ChangeRow2DA("", Target(TargetType.ROW_INDEX, 1), {"Col1": RowValueConstant("X")}))
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["a", "X"]
        assert twoda.get_column("Col2") == ["b", "e"]
        assert twoda.get_column("Col3") == ["c", "f"]

    def test_change_existing_rowlabel(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        logger = PatchLogger()
        config = Modifications2DA("")
        config.modifiers.append(ChangeRow2DA("", Target(TargetType.ROW_LABEL, "1"), {"Col1": RowValueConstant("X")}))
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["a", "X"]
        assert twoda.get_column("Col2") == ["b", "e"]
        assert twoda.get_column("Col3") == ["c", "f"]

    def test_change_existing_labelindex(self):
        twoda = TwoDA(["label", "Col2", "Col3"])
        twoda.add_row("0", {"label": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"label": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        logger = PatchLogger()
        config = Modifications2DA("")
        config.modifiers.append(
            ChangeRow2DA(
                identifier="",
                target=Target(TargetType.LABEL_COLUMN, "d"),
                cells={"Col2": RowValueConstant("X")},
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("label") == ["a", "d"]
        assert twoda.get_column("Col2") == ["b", "X"]
        assert twoda.get_column("Col3") == ["c", "f"]

    def test_change_assign_tlkmemory(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        logger = PatchLogger()
        memory = PatcherMemory()
        memory.memory_str[0] = 0
        memory.memory_str[1] = 1
        config = Modifications2DA("")
        config.modifiers.append(ChangeRow2DA("", Target(TargetType.ROW_INDEX, 0), {"Col1": RowValueTLKMemory(0)}))
        config.modifiers.append(ChangeRow2DA("", Target(TargetType.ROW_INDEX, 1), {"Col1": RowValueTLKMemory(1)}))
        twoda = read_2da(cast(bytes, config.patch_resource(bytes_2da(twoda), memory, logger, Game.K1)))

        assert twoda.get_column("Col1") == ["0", "1"]
        assert twoda.get_column("Col2") == ["b", "e"]
        assert twoda.get_column("Col3") == ["c", "f"]

    def test_change_assign_2damemory(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        logger = PatchLogger()
        memory = PatcherMemory()
        memory.memory_2da[0] = "mem0"
        memory.memory_2da[1] = "mem1"
        config = Modifications2DA("")
        config.modifiers.append(ChangeRow2DA("", Target(TargetType.ROW_INDEX, 0), {"Col1": RowValue2DAMemory(0)}))
        config.modifiers.append(ChangeRow2DA("", Target(TargetType.ROW_INDEX, 1), {"Col1": RowValue2DAMemory(1)}))
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["mem0", "mem1"]
        assert twoda.get_column("Col2") == ["b", "e"]
        assert twoda.get_column("Col3") == ["c", "f"]

    def test_change_assign_high(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": " ", "Col2": "3", "Col3": "5"})
        twoda.add_row("1", {"Col1": "2", "Col2": "4", "Col3": "6"})

        logger = PatchLogger()
        memory = PatcherMemory()
        config = Modifications2DA("")
        config.modifiers.append(ChangeRow2DA("", Target(TargetType.ROW_INDEX, 0), {"Col1": RowValueHigh("Col1")}))
        config.modifiers.append(ChangeRow2DA("", Target(TargetType.ROW_INDEX, 0), {"Col2": RowValueHigh("Col2")}))
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["3", "2"]
        assert twoda.get_column("Col2") == ["5", "4"]
        assert twoda.get_column("Col3") == ["5", "6"]

    def test_set_2damemory_rowindex(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        logger = PatchLogger()
        memory = PatcherMemory()
        config = Modifications2DA("")
        config.modifiers.append(
            ChangeRow2DA(
                identifier="",
                target=Target(TargetType.ROW_INDEX, 1),
                cells={},
                store_2da={5: RowValueRowIndex()},
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["a", "d"]
        assert twoda.get_column("Col2") == ["b", "e"]
        assert twoda.get_column("Col3") == ["c", "f"]
        assert memory.memory_2da[5] == "1"

    def test_set_2damemory_rowlabel(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("r1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        logger = PatchLogger()
        memory = PatcherMemory()
        config = Modifications2DA("")
        config.modifiers.append(
            ChangeRow2DA(
                identifier="",
                target=Target(TargetType.ROW_INDEX, 1),
                cells={},
                store_2da={5: RowValueRowLabel()},
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["a", "d"]
        assert twoda.get_column("Col2") == ["b", "e"]
        assert twoda.get_column("Col3") == ["c", "f"]
        assert memory.memory_2da[5] == "r1"

    def test_set_2damemory_columnlabel(self):
        twoda = TwoDA(["label", "Col2", "Col3"])
        twoda.add_row("0", {"label": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"label": "d", "Col2": "e", "Col3": "f"})

        logger = PatchLogger()
        memory = PatcherMemory()
        config = Modifications2DA("")
        config.modifiers.append(
            ChangeRow2DA(
                identifier="",
                target=Target(TargetType.ROW_INDEX, 1),
                cells={},
                store_2da={5: RowValueRowCell("label")},
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("label") == ["a", "d"]
        assert twoda.get_column("Col2") == ["b", "e"]
        assert twoda.get_column("Col3") == ["c", "f"]
        assert memory.memory_2da[5] == "d"

    # endregion

    # region Add Row
    def test_add_rowlabel_use_maxrowlabel(self):
        twoda = TwoDA(["Col1"])
        twoda.add_row("0", {})

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(AddRow2DA("", None, None, {}))
        config.modifiers.append(AddRow2DA("", None, None, {}))
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_height() == 3
        assert twoda.get_label(0) == "0"
        assert twoda.get_label(1) == "1"
        assert twoda.get_label(2) == "2"

    def test_add_rowlabel_use_constant(self):
        twoda = TwoDA(["Col1"])

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(AddRow2DA("", None, "r1", {}))
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_height() == 1
        assert twoda.get_label(0) == "r1"

    def test_add_rowlabel_existing(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "123", "Col2": "456"})

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(
            AddRow2DA(
                identifier="",
                exclusive_column="Col1",
                row_label=None,
                cells={"Col1": RowValueConstant("123"), "Col2": RowValueConstant("ABC")},
            )
        )
        twoda = read_2da(cast(bytes, config.patch_resource(bytes_2da(twoda), memory, logger, Game.K1)))

        assert twoda.get_height() == 1
        assert twoda.get_label(0) == "0"

    def test_add_exclusive_notexists(self):
        """Exclusive column is specified and the value in the new row is unique. Add a new row."""
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        logger = PatchLogger()
        memory = PatcherMemory()
        config = Modifications2DA("")
        config.modifiers.append(
            AddRow2DA(
                identifier="",
                exclusive_column="Col1",
                row_label="2",
                cells={
                    "Col1": RowValueConstant("g"),
                    "Col2": RowValueConstant("h"),
                    "Col3": RowValueConstant("i"),
                },
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_height() == 3
        assert twoda.get_label(2) == "2"
        assert twoda.get_column("Col1") == ["a", "d", "g"]
        assert twoda.get_column("Col2") == ["b", "e", "h"]
        assert twoda.get_column("Col3") == ["c", "f", "i"]

    def test_add_exclusive_exists(self):
        """Exclusive column is specified but the value in the new row is already used. Edit the existing row."""
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})
        twoda.add_row("2", {"Col1": "g", "Col2": "h", "Col3": "i"})

        logger = PatchLogger()
        memory = PatcherMemory()
        config = Modifications2DA("")
        config.modifiers.append(
            AddRow2DA(
                identifier="",
                exclusive_column="Col1",
                row_label="3",
                cells={
                    "Col1": RowValueConstant("g"),
                    "Col2": RowValueConstant("X"),
                    "Col3": RowValueConstant("Y"),
                },
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_height() == 3
        assert twoda.get_column("Col1") == ["a", "d", "g"]
        assert twoda.get_column("Col2") == ["b", "e", "X"]
        assert twoda.get_column("Col3") == ["c", "f", "Y"]

    def test_add_exclusive_badcolumn(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        logger = PatchLogger()
        memory = PatcherMemory()
        config = Modifications2DA("")
        config.modifiers.append(AddRow2DA("", "Col4", "2", {}))
        # twoda = read_2da(config.apply(bytes_2da(twoda), memory))
        # TODO

    def test_add_exclusive_none(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        logger = PatchLogger()
        memory = PatcherMemory()
        config = Modifications2DA("")
        config.modifiers.append(
            AddRow2DA(
                identifier="",
                exclusive_column="",
                row_label="2",
                cells={
                    "Col1": RowValueConstant("g"),
                    "Col2": RowValueConstant("h"),
                    "Col3": RowValueConstant("i"),
                },
            )
        )
        config.modifiers.append(
            AddRow2DA(
                identifier="",
                exclusive_column=None,
                row_label="3",
                cells={
                    "Col1": RowValueConstant("j"),
                    "Col2": RowValueConstant("k"),
                    "Col3": RowValueConstant("l"),
                },
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_height() == 4
        assert twoda.get_column("Col1") == ["a", "d", "g", "j"]
        assert twoda.get_column("Col2") == ["b", "e", "h", "k"]
        assert twoda.get_column("Col3") == ["c", "f", "i", "l"]

    def test_add_assign_high(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "1", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "2", "Col2": "e", "Col3": "f"})

        logger = PatchLogger()
        memory = PatcherMemory()
        config = Modifications2DA("")
        config.modifiers.append(AddRow2DA("", "", "2", {"Col1": RowValueHigh("Col1")}))
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["1", "2", "3"]

    def test_add_assign_tlkmemory(self):
        twoda = TwoDA(["Col1"])

        logger = PatchLogger()
        memory = PatcherMemory()
        memory.memory_str[0] = 5
        memory.memory_str[1] = 6

        config = Modifications2DA("")
        config.modifiers.append(AddRow2DA("", None, "0", {"Col1": RowValueTLKMemory(0)}))
        config.modifiers.append(AddRow2DA("", None, "1", {"Col1": RowValueTLKMemory(1)}))
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["5", "6"]

    def test_add_assign_2damemory(self):
        twoda = TwoDA(["Col1"])

        logger = PatchLogger()
        memory = PatcherMemory()
        memory.memory_2da[0] = "5"
        memory.memory_2da[1] = "6"

        config = Modifications2DA("")
        config.modifiers.append(AddRow2DA("", None, "0", {"Col1": RowValue2DAMemory(0)}))
        config.modifiers.append(AddRow2DA("", None, "1", {"Col1": RowValue2DAMemory(1)}))
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["5", "6"]

    def test_add_2damemory_rowindex(self):
        twoda = TwoDA(["Col1"])
        twoda.add_row("0", {"Col1": "X"})

        logger = PatchLogger()
        memory = PatcherMemory()
        config = Modifications2DA("")
        config.modifiers.append(
            AddRow2DA(
                identifier="",
                exclusive_column="Col1",
                row_label="1",
                cells={"Col1": RowValueConstant("X")},
                store_2da={5: RowValueRowIndex()},
            )
        )
        config.modifiers.append(
            AddRow2DA(
                identifier="",
                exclusive_column=None,
                row_label="2",
                cells={"Col1": RowValueConstant("Y")},
                store_2da={6: RowValueRowIndex()},
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_height() == 2
        assert twoda.get_column("Col1") == ["X", "Y"]
        assert memory.memory_2da[5] == "0"
        assert memory.memory_2da[6] == "1"

    # endregion

    # region Copy Row
    def test_copy_existing_rowindex(self):
        twoda: TwoDA = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(
            CopyRow2DA(
                identifier="",
                target=Target(TargetType.ROW_INDEX, 0),
                exclusive_column=None,
                row_label=None,
                cells={"Col2": RowValueConstant("X")},
            )
        )
        twoda = read_2da(cast(bytes, config.patch_resource(bytes_2da(twoda), memory, logger, Game.K1)))

        assert twoda.get_height() == 3
        assert twoda.get_column("Col1") == ["a", "c", "a"]
        assert twoda.get_column("Col2") == ["b", "d", "X"]

    def test_copy_existing_rowlabel(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(
            CopyRow2DA(
                identifier="",
                target=Target(TargetType.ROW_LABEL, "1"),
                exclusive_column=None,
                row_label=None,
                cells={"Col2": RowValueConstant("X")},
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_height() == 3
        assert twoda.get_column("Col1") == ["a", "c", "c"]
        assert twoda.get_column("Col2") == ["b", "d", "X"]

    def test_copy_exclusive_notexists(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(
            CopyRow2DA(
                identifier="",
                target=Target(TargetType.ROW_INDEX, 0),
                exclusive_column="Col1",
                row_label=None,
                cells={"Col1": RowValueConstant("c"), "Col2": RowValueConstant("d")},
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_height() == 2
        assert twoda.get_label(1) == "1"
        assert twoda.get_column("Col1") == ["a", "c"]
        assert twoda.get_column("Col2") == ["b", "d"]

    def test_copy_exclusive_exists(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(
            CopyRow2DA(
                identifier="",
                target=Target(TargetType.ROW_INDEX, 0),
                exclusive_column="Col1",
                row_label=None,
                cells={"Col1": RowValueConstant("a"), "Col2": RowValueConstant("X")},
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_height() == 1
        assert twoda.get_label(0) == "0"
        assert twoda.get_column("Col1") == ["a"]
        assert twoda.get_column("Col2") == ["X"]

    def test_copy_exclusive_none(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(
            CopyRow2DA(
                identifier="",
                target=Target(TargetType.ROW_INDEX, 0),
                exclusive_column=None,
                row_label=None,
                cells={"Col1": RowValueConstant("c"), "Col2": RowValueConstant("d")},
            )
        )
        config.modifiers.append(
            CopyRow2DA(
                identifier="",
                target=Target(TargetType.ROW_INDEX, 0),
                exclusive_column="",
                row_label="r2",
                cells={"Col1": RowValueConstant("e"), "Col2": RowValueConstant("f")},
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_height() == 3
        assert twoda.get_label(1) == "1"
        assert twoda.get_label(2) == "r2"
        assert twoda.get_column("Col1") == ["a", "c", "e"]
        assert twoda.get_column("Col2") == ["b", "d", "f"]

    def test_copy_set_newrowlabel(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(CopyRow2DA("", Target(TargetType.ROW_INDEX, 0), None, "r2", {}))
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_label(2) == "r2"
        assert twoda.get_column("Col1") == ["a", "c", "a"]
        assert twoda.get_column("Col2") == ["b", "d", "b"]

    def test_copy_assign_high(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "1"})
        twoda.add_row("1", {"Col1": "c", "Col2": "2"})

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(
            CopyRow2DA(
                identifier="",
                target=Target(TargetType.ROW_INDEX, 0),
                exclusive_column=None,
                row_label=None,
                cells={"Col2": RowValueHigh("Col2")},
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_height() == 3
        assert twoda.get_column("Col1") == ["a", "c", "a"]
        assert twoda.get_column("Col2") == ["1", "2", "3"]

    def test_copy_assign_tlkmemory(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "1"})
        twoda.add_row("1", {"Col1": "c", "Col2": "2"})

        logger = PatchLogger()
        memory = PatcherMemory()
        memory.memory_str[0] = 5

        config = Modifications2DA("")
        config.modifiers.append(
            CopyRow2DA(
                identifier="",
                target=Target(TargetType.ROW_INDEX, 0),
                exclusive_column=None,
                row_label=None,
                cells={"Col2": RowValueTLKMemory(0)},
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["a", "c", "a"]
        assert twoda.get_column("Col2") == ["1", "2", "5"]

    def test_copy_assign_2damemory(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "1"})
        twoda.add_row("1", {"Col1": "c", "Col2": "2"})

        logger = PatchLogger()
        memory = PatcherMemory()
        memory.memory_2da[0] = "5"

        config = Modifications2DA("")
        config.modifiers.append(
            CopyRow2DA(
                identifier="",
                target=Target(TargetType.ROW_INDEX, 0),
                exclusive_column=None,
                row_label=None,
                cells={"Col2": RowValue2DAMemory(0)},
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["a", "c", "a"]
        assert twoda.get_column("Col2") == ["1", "2", "5"]

    def test_copy_2damemory_rowindex(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(
            CopyRow2DA(
                identifier="",
                target=Target(TargetType.ROW_INDEX, 0),
                exclusive_column=None,
                row_label=None,
                cells={},
                store_2da={5: RowValueRowIndex()},
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["a", "c", "a"]
        assert twoda.get_column("Col2") == ["b", "d", "b"]
        assert memory.memory_2da[5] == "2"

    # endregion

    # region Add Column
    def test_addcolumn_empty(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(AddColumn2DA("", "Col3", "", {}, {}, {}))
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["a", "c"]
        assert twoda.get_column("Col2") == ["b", "d"]
        assert twoda.get_column("Col3") == ["", ""]

    def test_addcolumn_default(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(AddColumn2DA("", "Col3", "X", {}, {}, {}))
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["a", "c"]
        assert twoda.get_column("Col2") == ["b", "d"]
        assert twoda.get_column("Col3") == ["X", "X"]

    def test_addcolumn_rowindex_constant(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(AddColumn2DA("", "Col3", "", {0: RowValueConstant("X")}, {}, {}))
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["a", "c"]
        assert twoda.get_column("Col2") == ["b", "d"]
        assert twoda.get_column("Col3") == ["X", ""]

    def test_addcolumn_rowlabel_2damemory(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        logger = PatchLogger()
        memory = PatcherMemory()
        memory.memory_2da[5] = "ABC"

        config = Modifications2DA("")
        config.modifiers.append(AddColumn2DA("", "Col3", "", {}, {"1": RowValue2DAMemory(5)}, {}))
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["a", "c"]
        assert twoda.get_column("Col2") == ["b", "d"]
        assert twoda.get_column("Col3") == ["", "ABC"]

    def test_addcolumn_rowlabel_tlkmemory(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        logger = PatchLogger()
        memory = PatcherMemory()
        memory.memory_str[5] = 123

        config = Modifications2DA("")
        config.modifiers.append(AddColumn2DA("", "Col3", "", {}, {"1": RowValueTLKMemory(5)}, {}))
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["a", "c"]
        assert twoda.get_column("Col2") == ["b", "d"]
        assert twoda.get_column("Col3") == ["", "123"]

    def test_addcolumn_2damemory_index(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(
            AddColumn2DA(
                identifier="",
                header="Col3",
                default="",
                index_insert={0: RowValueConstant("X"), 1: RowValueConstant("Y")},
                label_insert={},
                store_2da={0: "I0"},
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["a", "c"]
        assert twoda.get_column("Col2") == ["b", "d"]
        assert twoda.get_column("Col3") == ["X", "Y"]
        assert memory.memory_2da[0] == "X"

    def test_addcolumn_2damemory_line(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        logger = PatchLogger()
        memory = PatcherMemory()

        config = Modifications2DA("")
        config.modifiers.append(
            AddColumn2DA(
                identifier="",
                header="Col3",
                default="",
                index_insert={0: RowValueConstant("X"), 1: RowValueConstant("Y")},
                label_insert={},
                store_2da={0: "L1"},
            )
        )
        config.apply(twoda, memory, logger, Game.K1)

        assert twoda.get_column("Col1") == ["a", "c"]
        assert twoda.get_column("Col2") == ["b", "d"]
        assert twoda.get_column("Col3") == ["X", "Y"]
        assert memory.memory_2da[0] == "Y"

    # endregion


class TestManipulateGFF(TestCase):
    def test_modify_field_uint8(self):
        gff = GFF()
        gff.root.set_uint8("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", replace=False, modifiers=[ModifyFieldGFF("Field1", FieldValueConstant(2))])
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_uint8("Field1") == 2

    def test_modify_field_int8(self):
        gff = GFF()
        gff.root.set_int8("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", replace=False, modifiers=[ModifyFieldGFF("Field1", FieldValueConstant(2))])
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_int8("Field1") == 2

    def test_modify_field_uint16(self):
        gff = GFF()
        gff.root.set_uint16("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", replace=False, modifiers=[ModifyFieldGFF("Field1", FieldValueConstant(2))])
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_uint16("Field1") == 2

    def test_modify_field_int16(self):
        gff = GFF()
        gff.root.set_int16("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", replace=False, modifiers=[ModifyFieldGFF("Field1", FieldValueConstant(2))])
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_int16("Field1") == 2

    def test_modify_field_uint32(self):
        gff = GFF()
        gff.root.set_uint32("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", replace=False, modifiers=[ModifyFieldGFF("Field1", FieldValueConstant(2))])
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_uint32("Field1") == 2

    def test_modify_field_int32(self):
        gff = GFF()
        gff.root.set_int32("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", replace=False, modifiers=[ModifyFieldGFF("Field1", FieldValueConstant(2))])
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_int32("Field1") == 2

    def test_modify_field_uint64(self):
        gff = GFF()
        gff.root.set_uint64("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", replace=False, modifiers=[ModifyFieldGFF("Field1", FieldValueConstant(2))])
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_uint64("Field1") == 2

    def test_modify_field_int64(self):
        gff = GFF()
        gff.root.set_int64("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", replace=False, modifiers=[ModifyFieldGFF("Field1", FieldValueConstant(2))])
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_int64("Field1") == 2

    def test_modify_field_single(self):
        gff = GFF()
        gff.root.set_single("Field1", 1.234)

        memory = PatcherMemory()

        config = ModificationsGFF("", replace=False, modifiers=[ModifyFieldGFF("Field1", FieldValueConstant(2.345))])
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_single("Field1") == 2.3450000286102295

    def test_modify_field_double(self):
        gff = GFF()
        gff.root.set_double("Field1", 1.234567)

        memory = PatcherMemory()

        config = ModificationsGFF("", replace=False, modifiers=[ModifyFieldGFF("Field1", FieldValueConstant(2.345678))])
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_double("Field1") == 2.345678

    def test_modify_field_string(self):
        gff = GFF()
        gff.root.set_string("Field1", "abc")

        memory = PatcherMemory()

        config = ModificationsGFF("", replace=False, modifiers=[ModifyFieldGFF("Field1", FieldValueConstant("def"))])
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_string("Field1") == "def"

    def test_modify_field_locstring(self):
        gff = GFF()
        gff.root.set_locstring("Field1", LocalizedString(0))

        memory = PatcherMemory()

        config = ModificationsGFF(
            "",
            replace=False,
            modifiers=[
                ModifyFieldGFF(
                    "Field1",
                    FieldValueConstant(LocalizedStringDelta(FieldValueConstant(1))),
                )
            ],
        )
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_locstring("Field1").stringref == 1

    def test_modify_field_vector3(self):
        gff = GFF()
        gff.root.set_vector3("Field1", Vector3(0, 1, 2))

        memory = PatcherMemory()

        config = ModificationsGFF("", replace=False, modifiers=[ModifyFieldGFF("Field1", FieldValueConstant(Vector3(1, 2, 3)))])
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert Vector3(1, 2, 3) == gff.root.get_vector3("Field1")

    def test_modify_field_vector4(self):
        gff = GFF()
        gff.root.set_vector4("Field1", Vector4(0, 1, 2, 3))

        memory = PatcherMemory()

        config = ModificationsGFF(
            "",
            replace=False,
            modifiers=[ModifyFieldGFF("Field1", FieldValueConstant(Vector4(1, 2, 3, 4)))],
        )
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert Vector4(1, 2, 3, 4) == gff.root.get_vector4("Field1")

    def test_modify_nested(self):
        gff = GFF()
        gff_list = gff.root.set_list("List", GFFList())
        gff_struct = gff_list.add(0)
        gff_struct.set_string("String", "")

        memory = PatcherMemory()
        modifiers: list[ModifyGFF] = [ModifyFieldGFF(PureWindowsPath("List\\0\\String"), FieldValueConstant("abc"))]

        config = ModificationsGFF("", replace=False, modifiers=modifiers)
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        patched_gff_list = gff.root.get_list("List")
        patched_gff_struct = patched_gff_list.at(0)

        self.assertIsNotNone(patched_gff_struct)
        assert patched_gff_struct is not None
        self.assertEqual("abc", patched_gff_struct.get_string("String"))

    def test_modify_2damemory(self):
        gff = GFF()
        gff.root.set_string("String", "")
        gff.root.set_uint8("Integer", 0)

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"

        config = ModificationsGFF("", replace=False, modifiers=[])
        config.modifiers.append(ModifyFieldGFF("String", FieldValue2DAMemory(5)))
        config.modifiers.append(ModifyFieldGFF("Integer", FieldValue2DAMemory(5)))
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_string("String") == "123"
        assert gff.root.get_uint8("Integer") == 123

    def test_modify_tlkmemory(self):
        gff = GFF()
        gff.root.set_string("String", "")
        gff.root.set_uint8("Integer", 0)

        memory = PatcherMemory()
        memory.memory_str[5] = 123

        config = ModificationsGFF("", replace=False, modifiers=[])
        config.modifiers.append(ModifyFieldGFF("String", FieldValueTLKMemory(5)))
        config.modifiers.append(ModifyFieldGFF("Integer", FieldValueTLKMemory(5)))
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_string("String") == "123"
        assert gff.root.get_uint8("Integer") == 123

    def test_add_newnested(self):
        gff = GFF()

        memory = PatcherMemory()

        add_field1 = AddFieldGFF("", "List", GFFFieldType.List, FieldValueConstant(GFFList()), PureWindowsPath(""))

        add_field2 = AddStructToListGFF("", FieldValueConstant(GFFStruct()), PureWindowsPath("List"))
        add_field1.modifiers.append(add_field2)

        add_field3 = AddFieldGFF("", "SomeInteger", GFFFieldType.UInt8, FieldValueConstant(123), PureWindowsPath("List\\>>##INDEXINLIST##<<"))
        add_field2.modifiers.append(add_field3)

        config = ModificationsGFF("", replace=False, modifiers=[add_field1])
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_list("List") is not None
        assert gff.root.get_list("List").at(0) is not None
        assert gff.root.get_list("List").at(0).get_uint8("SomeInteger") is not None  # type: ignore

    def test_add_nested(self):
        gff = GFF()
        gff_list = gff.root.set_list("List", GFFList())
        gff_struct = gff_list.add(0)

        memory = PatcherMemory()
        memory.memory_str[5] = 123

        config = ModificationsGFF("", replace=False, modifiers=[])
        config.modifiers.append(
            AddFieldGFF(
                "",
                "String",
                GFFFieldType.String,
                FieldValueConstant("abc"),
                path=PureWindowsPath("List\\0"),
            )
        )
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        patched_gff_list = gff.root.get_list("List")
        patched_gff_struct = patched_gff_list.at(0)

        self.assertIsNotNone(patched_gff_struct)
        assert patched_gff_struct is not None
        self.assertEqual("abc", patched_gff_struct.get_string("String"))

    def test_add_use_2damemory(self):
        gff = GFF()

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"

        config = ModificationsGFF("", replace=False, modifiers=[])
        config.modifiers.append(AddFieldGFF("", "String", GFFFieldType.String, FieldValue2DAMemory(5), PureWindowsPath("")))
        config.modifiers.append(AddFieldGFF("", "Integer", GFFFieldType.UInt8, FieldValue2DAMemory(5), PureWindowsPath("")))
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_string("String") == "123"
        assert gff.root.get_uint8("Integer") == 123

    def test_add_use_tlkmemory(self):
        gff = GFF()

        memory = PatcherMemory()
        memory.memory_str[5] = 123

        config = ModificationsGFF("", replace=False, modifiers=[])
        config.modifiers.append(AddFieldGFF("", "String", GFFFieldType.String, FieldValueTLKMemory(5), PureWindowsPath("")))
        config.modifiers.append(AddFieldGFF("", "Integer", GFFFieldType.UInt8, FieldValueTLKMemory(5), PureWindowsPath("")))
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_string("String") == "123"
        assert gff.root.get_uint8("Integer") == 123

    def test_add_field_locstring(self):
        """Adds a localized string field to a GFF using a 2DA memory reference.

        Processing Logic:
        ----------------
            1. Creates a GFF object
            2. Sets a locstring field on the root node
            3. Populates the memory with a test string
            4. Creates an AddField modifier to add the Field1 locstring using the memory reference
            5. Applies the modifier to the GFF
            6. Checks that the locstring was set correctly from memory
        """
        gff = GFF()
        gff.root.set_locstring("Field1", LocalizedString(0))

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"
        modifiers: list[ModifyGFF] = [
            AddFieldGFF(
                "",
                "Field1",
                GFFFieldType.LocalizedString,
                FieldValueConstant(LocalizedStringDelta(FieldValue2DAMemory(5))),
                PureWindowsPath(""),
            )
        ]

        config = ModificationsGFF("", replace=False, modifiers=modifiers)
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        assert gff.root.get_locstring("Field1").stringref == 123

    def test_addlist_listindex(self):
        gff = GFF()
        gff_list = gff.root.set_list("List", GFFList())

        memory = PatcherMemory()

        config = ModificationsGFF("", replace=False, modifiers=[])
        config.modifiers.append(AddStructToListGFF("test1", FieldValueConstant(GFFStruct(5)), "List", None))
        config.modifiers.append(AddStructToListGFF("test2", FieldValueConstant(GFFStruct(3)), "List", None))
        config.modifiers.append(AddStructToListGFF("test3", FieldValueConstant(GFFStruct(1)), "List", None))

        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        patched_gff_list = gff.root.get_list("List")

        assert patched_gff_list.at(0).struct_id == 5  # type: ignore
        assert patched_gff_list.at(1).struct_id == 3  # type: ignore
        assert patched_gff_list.at(2).struct_id == 1  # type: ignore

    def test_addlist_store_2damemory(self):
        gff = GFF()
        gff.root.set_list("List", GFFList())

        memory = PatcherMemory()

        config = ModificationsGFF("", replace=False, modifiers=[])
        config.modifiers.append(AddStructToListGFF("test1", FieldValueConstant(GFFStruct()), "List"))
        config.modifiers.append(AddStructToListGFF("test2", FieldValueConstant(GFFStruct()), "List", index_to_token=12))
        gff = read_gff(config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1))

        assert memory.memory_2da[12] == "1"


class TestManipulateSSF(TestCase):
    def test_assign_int(self):
        ssf = SSF()

        memory = PatcherMemory()

        config = ModificationsSSF("", replace=False, modifiers=[])
        config.modifiers.append(ModifySSF(SSFSound.BATTLE_CRY_1, NoTokenUsage(5)))
        ssf = read_ssf(config.patch_resource(bytes_ssf(ssf), memory, PatchLogger(), Game.K1))

        assert ssf.get(SSFSound.BATTLE_CRY_1) == 5

    def test_assign_2datoken(self):
        ssf = SSF()

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"

        config = ModificationsSSF("", replace=False, modifiers=[])
        config.modifiers.append(ModifySSF(SSFSound.BATTLE_CRY_2, TokenUsage2DA(5)))
        ssf = read_ssf(config.patch_resource(bytes_ssf(ssf), memory, PatchLogger(), Game.K1))

        assert ssf.get(SSFSound.BATTLE_CRY_2) == 123

    def test_assign_tlktoken(self):
        ssf = SSF()

        memory = PatcherMemory()
        memory.memory_str[5] = 321

        config = ModificationsSSF("", False, [])
        config.modifiers.append(ModifySSF(SSFSound.BATTLE_CRY_3, TokenUsageTLK(5)))
        ssf = read_ssf(config.patch_resource(bytes_ssf(ssf), memory, PatchLogger(), Game.K1))

        assert ssf.get(SSFSound.BATTLE_CRY_3) == 321


if __name__ == "__main__":
    unittest.main()
