from unittest import TestCase

from pykotor.common.misc import ResRef

from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import LocalizedString, Language, Gender
from pykotor.resource.formats.gff import GFF, GFFList, GFFFieldType
from pykotor.resource.formats.ssf import SSF, SSFSound
from pykotor.resource.formats.tlk import TLK
from pykotor.resource.formats.twoda import TwoDA
from pykotor.tslpatcher.mods.tlk import ModificationsTLK, ModifyTLK
from pykotor.tslpatcher.mods.gff import ModificationsGFF, ModifyFieldGFF, AddFieldGFF, AddStructToListGFF, \
    LocalizedStringDelta
from pykotor.tslpatcher.memory import PatcherMemory, NoTokenUsage, TokenUsage2DA, TokenUsageTLK
from pykotor.tslpatcher.mods.ssf import ModificationsSSF, ModifySSF
from pykotor.tslpatcher.mods.twoda import Modifications2DA, ChangeRow2DA, Target, TargetType, AddRow2DA, CopyRow2DA, \
    AddColumn2DA


class TestManipulateTLK(TestCase):
    def test_apply(self):
        memory = PatcherMemory()

        config = ModificationsTLK()
        config.modifiers.append(ModifyTLK(0, "Append2", ResRef.from_blank()))
        config.modifiers.append(ModifyTLK(1, "Append1", ResRef.from_blank()))

        dialog_tlk = TLK()
        dialog_tlk.add("Old1")
        dialog_tlk.add("Old2")

        config.apply(dialog_tlk, memory)

        self.assertEqual(4, len(dialog_tlk))
        self.assertEqual("Append2", dialog_tlk.get(2).text)
        self.assertEqual("Append1", dialog_tlk.get(3).text)

        self.assertEqual(2, memory.memory_str[0])
        self.assertEqual(3, memory.memory_str[1])

        # [Dialog] [Append] [Token] [Text]
        # 0        -        -       Old1
        # 1        -        -       Old2
        # 2        1        0       Append2
        # 3        0        1       Append1


class TestManipulate2DA(TestCase):
    # TODO Error, Warning tracking

    # region Change Row
    def test_change_existing_rowindex(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        config = Modifications2DA("")
        config.rows.append(ChangeRow2DA("", Target(TargetType.ROW_INDEX, 1), {"Col1": "X"}))
        config.apply(twoda, memory)

        self.assertEqual(["a", "X"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f"], twoda.get_column("Col3"))

    def test_change_existing_rowlabel(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        config = Modifications2DA("")
        config.rows.append(ChangeRow2DA("", Target(TargetType.ROW_LABEL, "1"), {"Col1": "X"}))
        config.apply(twoda, memory)

        self.assertEqual(["a", "X"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f"], twoda.get_column("Col3"))

    def test_change_existing_labelindex(self):
        twoda = TwoDA(["label", "Col2", "Col3"])
        twoda.add_row("0", {"label": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"label": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        config = Modifications2DA("")
        config.rows.append(ChangeRow2DA("", Target(TargetType.LABEL_COLUMN, "d"), {"Col2": "X"}))
        config.apply(twoda, memory)

        self.assertEqual(["a", "d"], twoda.get_column("label"))
        self.assertEqual(["b", "X"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f"], twoda.get_column("Col3"))

    def test_change_assign_tlkmemory(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        memory.memory_str[0] = 0
        memory.memory_str[1] = 1
        config = Modifications2DA("")
        config.rows.append(ChangeRow2DA("", Target(TargetType.ROW_INDEX, 0), {"Col1": "StrRef0"}))
        config.rows.append(ChangeRow2DA("", Target(TargetType.ROW_INDEX, 1), {"Col1": "StrRef1"}))
        config.apply(twoda, memory)

        self.assertEqual(["0", "1"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f"], twoda.get_column("Col3"))

    def test_change_assign_2damemory(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        memory.memory_2da[0] = "mem0"
        memory.memory_2da[1] = "mem1"
        config = Modifications2DA("")
        config.rows.append(ChangeRow2DA("", Target(TargetType.ROW_INDEX, 0), {"Col1": "2DAMEMORY0"}))
        config.rows.append(ChangeRow2DA("", Target(TargetType.ROW_INDEX, 1), {"Col1": "2DAMEMORY1"}))
        config.apply(twoda, memory)

        self.assertEqual(["mem0", "mem1"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f"], twoda.get_column("Col3"))

    def test_change_assign_high(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": " ", "Col2": "3", "Col3": "5"})
        twoda.add_row("1", {"Col1": "2", "Col2": "4", "Col3": "6"})

        memory = PatcherMemory()
        config = Modifications2DA("")
        config.rows.append(ChangeRow2DA("", Target(TargetType.ROW_INDEX, 0), {"Col1": "high()"}))
        config.rows.append(ChangeRow2DA("", Target(TargetType.ROW_INDEX, 0), {"Col2": "high()"}))
        config.apply(twoda, memory)

        self.assertEqual(["3", "2"], twoda.get_column("Col1"))
        self.assertEqual(["5", "4"], twoda.get_column("Col2"))
        self.assertEqual(["5", "6"], twoda.get_column("Col3"))

    def test_set_2damemory_rowindex(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        config = Modifications2DA("")
        config.rows.append(ChangeRow2DA("", Target(TargetType.ROW_INDEX, 1), {"2DAMEMORY5": "RowIndex"}))
        config.apply(twoda, memory)

        self.assertEqual(["a", "d"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f"], twoda.get_column("Col3"))
        self.assertEqual(1, memory.memory_2da[5])
    # endregion

    # region Add Row
    def test_add_exclusive_notexists(self):
        """Exclusive column is specified and the value in the new row is unique. Add a new row."""
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        config = Modifications2DA("")
        config.rows.append(AddRow2DA("", "Col1", {"RowLabel": "2", "Col1": "g", "Col2": "h", "Col3": "i"}))
        config.apply(twoda, memory)

        self.assertEqual(3, twoda.get_height())
        self.assertEqual("2", twoda.get_label(2))
        self.assertEqual(["a", "d", "g"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e", "h"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f", "i"], twoda.get_column("Col3"))

    def test_add_exclusive_exists(self):
        """Exclusive column is specified but the value in the new row is already used. Edit the existing row."""
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})
        twoda.add_row("1", {"Col1": "g", "Col2": "h", "Col3": "i"})

        memory = PatcherMemory()
        config = Modifications2DA("")
        config.rows.append(AddRow2DA("", "Col1", {"Col1": "g", "Col2": "X", "Col3": "Y"}))
        config.apply(twoda, memory)

        self.assertEqual(3, twoda.get_height())
        self.assertEqual(["a", "d", "g"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e", "X"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f", "Y"], twoda.get_column("Col3"))

    def test_add_exclusive_badcolumn(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        config = Modifications2DA("")
        config.rows.append(AddRow2DA("", "Col4", {}))
        # config.apply(twoda, memory)
        # TODO

    def test_add_exclusive_none(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        config = Modifications2DA("")
        config.rows.append(AddRow2DA("", "", {"Col1": "g", "Col2": "h", "Col3": "i"}))
        config.rows.append(AddRow2DA("", None, {"Col1": "j", "Col2": "k", "Col3": "l"}))
        config.apply(twoda, memory)

        self.assertEqual(4, twoda.get_height())
        self.assertEqual(["a", "d", "g", "j"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e", "h", "k"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f", "i", "l"], twoda.get_column("Col3"))

    def test_add_assign_high(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "1", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "2", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        config = Modifications2DA("")
        config.rows.append(AddRow2DA("", "", {"Col1": "high()"}))
        config.apply(twoda, memory)

        self.assertEqual(["1", "2", "3"], twoda.get_column("Col1"))

    def test_add_assign_tlkmemory(self):
        twoda = TwoDA(["Col1"])

        memory = PatcherMemory()
        memory.memory_str[0] = 5
        memory.memory_str[1] = 6

        config = Modifications2DA("")
        config.rows.append(AddRow2DA("", None, {"Col1": "StrRef0"}))
        config.rows.append(AddRow2DA("", None, {"Col1": "StrRef1"}))
        config.apply(twoda, memory)

        self.assertEqual(["5", "6"], twoda.get_column("Col1"))

    def test_add_assign_2damemory(self):
        twoda = TwoDA(["Col1"])

        memory = PatcherMemory()
        memory.memory_2da[0] = "5"
        memory.memory_2da[1] = "6"

        config = Modifications2DA("")
        config.rows.append(AddRow2DA("", None, {"Col1": "2DAMEMORY0"}))
        config.rows.append(AddRow2DA("", None, {"Col1": "2DAMEMORY1"}))
        config.apply(twoda, memory)

        self.assertEqual(["5", "6"], twoda.get_column("Col1"))

    def test_add_2damemory_rowindex(self):
        twoda = TwoDA(["Col1"])
        twoda.add_row("0", {"Col1": "X"})

        memory = PatcherMemory()
        config = Modifications2DA("")
        config.rows.append(AddRow2DA("", "Col1", {"Col1": "X", "2DAMEMORY5": "RowIndex"}))
        config.rows.append(AddRow2DA("", None, {"Col1": "Y", "2DAMEMORY6": "RowIndex"}))
        config.apply(twoda, memory)

        self.assertEqual(["X", "Y"], twoda.get_column("Col1"))
        self.assertEqual(0, memory.memory_2da[5])
        self.assertEqual(1, memory.memory_2da[6])
    # endregion

    # region Copy Row
    def test_copy_existing_rowindex(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()

        config = Modifications2DA("")
        config.rows.append(CopyRow2DA("", Target(TargetType.ROW_INDEX, 0), None, {"Col2": "X"}))
        config.apply(twoda, memory)

        self.assertEqual(3, twoda.get_height())
        self.assertEqual(["a", "c", "a"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d", "X"], twoda.get_column("Col2"))

    def test_copy_existing_rowlabel(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()

        config = Modifications2DA("")
        config.rows.append(CopyRow2DA("", Target(TargetType.ROW_LABEL, "1"), None, {"Col2": "X"}))
        config.apply(twoda, memory)

        self.assertEqual(3, twoda.get_height())
        self.assertEqual(["a", "c", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d", "X"], twoda.get_column("Col2"))

    def test_copy_exclusive_notexists(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})

        memory = PatcherMemory()

        config = Modifications2DA("")
        config.rows.append(CopyRow2DA("", Target(TargetType.ROW_INDEX, 0), "Col1", {"Col1": "c", "Col2": "d"}))
        config.apply(twoda, memory)

        self.assertEqual(2, twoda.get_height())
        self.assertEqual("1", twoda.get_label(1))
        self.assertEqual(["a", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d"], twoda.get_column("Col2"))

    def test_copy_exclusive_exists(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})

        memory = PatcherMemory()

        config = Modifications2DA("")
        config.rows.append(CopyRow2DA("", Target(TargetType.ROW_INDEX, 0), "Col1", {"Col1": "a", "Col2": "X"}))
        config.apply(twoda, memory)

        self.assertEqual(1, twoda.get_height())
        self.assertEqual("0", twoda.get_label(0))
        self.assertEqual(["a"], twoda.get_column("Col1"))
        self.assertEqual(["X"], twoda.get_column("Col2"))

    def test_copy_exclusive_none(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})

        memory = PatcherMemory()

        config = Modifications2DA("")
        config.rows.append(CopyRow2DA("", Target(TargetType.ROW_INDEX, 0), None, {"Col1": "c", "Col2": "d"}))
        config.rows.append(CopyRow2DA("", Target(TargetType.ROW_INDEX, 0), "", {"RowLabel": "r2", "Col1": "e", "Col2": "f"}))
        config.apply(twoda, memory)

        self.assertEqual(3, twoda.get_height())
        self.assertEqual("1", twoda.get_label(1))
        self.assertEqual("r2", twoda.get_label(2))
        self.assertEqual(["a", "c", "e"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d", "f"], twoda.get_column("Col2"))

    def test_copy_set_newrowlabel(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()

        config = Modifications2DA("")
        config.rows.append(CopyRow2DA("", Target(TargetType.ROW_INDEX, 0), None, {"NewRowLabel": "r2"}))
        config.apply(twoda, memory)

        self.assertEqual("r2", twoda.get_label(2))
        self.assertEqual(["a", "c", "a"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d", "b"], twoda.get_column("Col2"))

    def test_copy_assign_high(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "1"})
        twoda.add_row("1", {"Col1": "c", "Col2": "2"})

        memory = PatcherMemory()

        config = Modifications2DA("")
        config.rows.append(CopyRow2DA("", Target(TargetType.ROW_INDEX, 0), None, {"Col2": "high()"}))
        config.apply(twoda, memory)

        self.assertEqual(["a", "c", "a"], twoda.get_column("Col1"))
        self.assertEqual(["1", "2", "3"], twoda.get_column("Col2"))

    def test_copy_assign_tlkmemory(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "1"})
        twoda.add_row("1", {"Col1": "c", "Col2": "2"})

        memory = PatcherMemory()
        memory.memory_str[0] = 5

        config = Modifications2DA("")
        config.rows.append(CopyRow2DA("", Target(TargetType.ROW_INDEX, 0), None, {"Col2": "StrRef0"}))
        config.apply(twoda, memory)

        self.assertEqual(["a", "c", "a"], twoda.get_column("Col1"))
        self.assertEqual(["1", "2", "5"], twoda.get_column("Col2"))

    def test_copy_assign_2damemory(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "1"})
        twoda.add_row("1", {"Col1": "c", "Col2": "2"})

        memory = PatcherMemory()
        memory.memory_2da[0] = "5"

        config = Modifications2DA("")
        config.rows.append(CopyRow2DA("", Target(TargetType.ROW_INDEX, 0), None, {"Col2": "2DAMEMORY0"}))
        config.apply(twoda, memory)

        self.assertEqual(["a", "c", "a"], twoda.get_column("Col1"))
        self.assertEqual(["1", "2", "5"], twoda.get_column("Col2"))

    def test_copy_2damemory_rowindex(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()

        config = Modifications2DA("")
        config.rows.append(CopyRow2DA("", Target(TargetType.ROW_INDEX, 0), None, {"2DAMEMORY5": "RowIndex"}))
        config.apply(twoda, memory)

        self.assertEqual(["a", "c", "a"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d", "b"], twoda.get_column("Col2"))
        self.assertEqual(2, memory.memory_2da[5])
    # endregion

    # region Add Column
    def test_addcolumn_empty(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()

        config = Modifications2DA("")
        config.rows.append(AddColumn2DA("", "Col3", "", {}, {}, {}))
        config.apply(twoda, memory)

        self.assertEqual(["a", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d"], twoda.get_column("Col2"))
        self.assertEqual(["", ""], twoda.get_column("Col3"))

    def test_addcolumn_default(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()

        config = Modifications2DA("")
        config.rows.append(AddColumn2DA("", "Col3", "X", {}, {}, {}))
        config.apply(twoda, memory)

        self.assertEqual(["a", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d"], twoda.get_column("Col2"))
        self.assertEqual(["X", "X"], twoda.get_column("Col3"))

    def test_addcolumn_row_index(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()

        config = Modifications2DA("")
        config.rows.append(AddColumn2DA("", "Col3", "", {0: "X"}, {}, {}))
        config.apply(twoda, memory)

        self.assertEqual(["a", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d"], twoda.get_column("Col2"))
        self.assertEqual(["X", ""], twoda.get_column("Col3"))

    def test_addcolumn_row_label(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()

        config = Modifications2DA("")
        config.rows.append(AddColumn2DA("", "Col3", "", {}, {"1": "X"}, {}))
        config.apply(twoda, memory)

        self.assertEqual(["a", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d"], twoda.get_column("Col2"))
        self.assertEqual(["", "X"], twoda.get_column("Col3"))

    def test_addcolumn_2damemory_index(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()

        config = Modifications2DA("")
        config.rows.append(AddColumn2DA("", "Col3", "", {0: "X", 1: "Y"}, {}, {0: "I0"}))
        config.apply(twoda, memory)

        self.assertEqual(["a", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d"], twoda.get_column("Col2"))
        self.assertEqual(["X", "Y"], twoda.get_column("Col3"))
        self.assertEqual("X", memory.memory_2da[0])

    def test_addcolumn_2damemory_line(self):
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()

        config = Modifications2DA("")
        config.rows.append(AddColumn2DA("", "Col3", "", {0: "X", 1: "Y"}, {}, {0: "L1"}))
        config.apply(twoda, memory)

        self.assertEqual(["a", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d"], twoda.get_column("Col2"))
        self.assertEqual(["X", "Y"], twoda.get_column("Col3"))
        self.assertEqual("Y", memory.memory_2da[0])

    # endregion


class TestManipulateGFF(TestCase):
    def test_modify_field_uint8(self):
        gff = GFF()
        gff.root.set_uint8("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [ModifyFieldGFF("Field1", 2)])
        config.apply(gff, memory)

        self.assertEqual(2, gff.root.get_uint8("Field1"))

    def test_modify_field_int8(self):
        gff = GFF()
        gff.root.set_int8("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [ModifyFieldGFF("Field1", 2)])
        config.apply(gff, memory)

        self.assertEqual(2, gff.root.get_int8("Field1"))

    def test_modify_field_uint16(self):
        gff = GFF()
        gff.root.set_uint16("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [ModifyFieldGFF("Field1", 2)])
        config.apply(gff, memory)

        self.assertEqual(2, gff.root.get_uint16("Field1"))

    def test_modify_field_int16(self):
        gff = GFF()
        gff.root.set_int16("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [ModifyFieldGFF("Field1", 2)])
        config.apply(gff, memory)

        self.assertEqual(2, gff.root.get_int16("Field1"))

    def test_modify_field_uint32(self):
        gff = GFF()
        gff.root.set_uint32("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [ModifyFieldGFF("Field1", 2)])
        config.apply(gff, memory)

        self.assertEqual(2, gff.root.get_uint32("Field1"))

    def test_modify_field_int32(self):
        gff = GFF()
        gff.root.set_int32("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [ModifyFieldGFF("Field1", 2)])
        config.apply(gff, memory)

        self.assertEqual(2, gff.root.get_int32("Field1"))

    def test_modify_field_uint64(self):
        gff = GFF()
        gff.root.set_uint64("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [ModifyFieldGFF("Field1", 2)])
        config.apply(gff, memory)

        self.assertEqual(2, gff.root.get_uint64("Field1"))

    def test_modify_field_int64(self):
        gff = GFF()
        gff.root.set_int64("Field1", 1)

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [ModifyFieldGFF("Field1", 2)])
        config.apply(gff, memory)

        self.assertEqual(2, gff.root.get_int64("Field1"))

    def test_modify_field_single(self):
        gff = GFF()
        gff.root.set_single("Field1", 1.234)

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [ModifyFieldGFF("Field1", 2.345)])
        config.apply(gff, memory)

        self.assertEqual(2.345, gff.root.get_single("Field1"))

    def test_modify_field_double(self):
        gff = GFF()
        gff.root.set_double("Field1", 1.234567)

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [ModifyFieldGFF("Field1", 2.345678)])
        config.apply(gff, memory)

        self.assertEqual(2.345678, gff.root.get_double("Field1"))

    def test_modify_field_string(self):
        gff = GFF()
        gff.root.set_string("Field1", "abc")

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [ModifyFieldGFF("Field1", "def")])
        config.apply(gff, memory)

        self.assertEqual("def", gff.root.get_string("Field1"))

    def test_modify_field_locstring(self):
        gff = GFF()
        gff.root.set_locstring("Field1", LocalizedString(0))

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [ModifyFieldGFF("Field1", LocalizedStringDelta(1))])
        config.apply(gff, memory)

        self.assertEqual(1, gff.root.get_locstring("Field1").stringref)

    def test_modify_field_vector3(self):
        gff = GFF()
        gff.root.set_vector3("Field1", Vector3(0, 1, 2))

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [ModifyFieldGFF("Field1", Vector3(1, 2, 3))])
        config.apply(gff, memory)

        self.assertEqual(Vector3(1, 2, 3), gff.root.get_vector3("Field1"))

    def test_modify_field_vector4(self):
        gff = GFF()
        gff.root.set_vector4("Field1", Vector4(0, 1, 2, 3))

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [ModifyFieldGFF("Field1", Vector4(1, 2, 3, 4))])
        config.apply(gff, memory)

        self.assertEqual(Vector4(1, 2, 3, 4), gff.root.get_vector4("Field1"))

    def test_modify_nested(self):
        gff = GFF()
        gff_list = gff.root.set_list("List", GFFList())
        gff_struct = gff_list.add(0)
        gff_struct.set_string("String", "")

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [ModifyFieldGFF("List\\0\\String", "abc")])
        config.apply(gff, memory)

        self.assertEqual("abc", gff_struct.get_string("String"))

    def test_modify_2damemory(self):
        gff = GFF()
        gff.root.set_string("String", "")
        gff.root.set_uint8("Integer", 0)

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"

        config = ModificationsGFF("", False, [])
        config.modifiers.append(ModifyFieldGFF("String", "2DAMEMORY5"))
        config.modifiers.append(ModifyFieldGFF("Integer", "2DAMEMORY5"))
        config.apply(gff, memory)

        self.assertEqual("123", gff.root.get_string("String"))
        self.assertEqual(123, gff.root.get_uint8("Integer"))

    def test_modify_tlkmemory(self):
        gff = GFF()
        gff.root.set_string("String", "")
        gff.root.set_uint8("Integer", 0)

        memory = PatcherMemory()
        memory.memory_str[5] = 123

        config = ModificationsGFF("", False, [])
        config.modifiers.append(ModifyFieldGFF("String", "StrRef5"))
        config.modifiers.append(ModifyFieldGFF("Integer", "StrRef5"))
        config.apply(gff, memory)

        self.assertEqual("123", gff.root.get_string("String"))
        self.assertEqual(123, gff.root.get_uint8("Integer"))

    def test_add_newnested(self):
        gff = GFF()

        memory = PatcherMemory()

        add_field1 = AddFieldGFF("", "List", GFFFieldType.List, GFFList())

        add_field2 = AddStructToListGFF("", 0)
        add_field1.modifiers.append(add_field2)

        add_field3 = AddFieldGFF("", "SomeInteger", GFFFieldType.UInt8, 123)
        add_field2.modifiers.append(add_field3)

        config = ModificationsGFF("", False, [add_field1])
        config.apply(gff, memory)

        self.assertIsNotNone(gff.root.get_list("List"))
        self.assertIsNotNone(gff.root.get_list("List").at(0))
        self.assertIsNotNone(gff.root.get_list("List").at(0).get_uint8("SomeInteger"))

    def test_add_nested(self):
        gff = GFF()
        gff_list = gff.root.set_list("List", GFFList())
        gff_struct = gff_list.add(0)

        memory = PatcherMemory()
        memory.memory_str[5] = 123

        config = ModificationsGFF("", False, [])
        config.modifiers.append(AddFieldGFF("", "String", GFFFieldType.String, "abc", path="List\\0"))
        config.apply(gff, memory)

        self.assertEqual("abc", gff_struct.get_string("String"))

    def test_add_use_2damemory(self):
        gff = GFF()

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"

        config = ModificationsGFF("", False, [])
        config.modifiers.append(AddFieldGFF("", "String", GFFFieldType.String, "2DAMEMORY5"))
        config.modifiers.append(AddFieldGFF("", "Integer", GFFFieldType.UInt8, "2DAMEMORY5"))
        config.apply(gff, memory)

        self.assertEqual("123", gff.root.get_string("String"))
        self.assertEqual(123, gff.root.get_uint8("Integer"))

    def test_add_use_tlkmemory(self):
        gff = GFF()

        memory = PatcherMemory()
        memory.memory_str[5] = 123

        config = ModificationsGFF("", False, [])
        config.modifiers.append(AddFieldGFF("", "String", GFFFieldType.String, "StrRef5"))
        config.modifiers.append(AddFieldGFF("", "Integer", GFFFieldType.UInt8, "StrRef5"))
        config.apply(gff, memory)

        self.assertEqual("123", gff.root.get_string("String"))
        self.assertEqual(123, gff.root.get_uint8("Integer"))

    def test_add_field_locstring(self):
        gff = GFF()
        gff.root.set_locstring("Field1", LocalizedString(0))

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"

        config = ModificationsGFF("", False, [AddFieldGFF("", "Field1", GFFFieldType.LocalizedString, LocalizedStringDelta("2DAMEMORY5"))])
        config.apply(gff, memory)

        self.assertEqual(123, gff.root.get_locstring("Field1").stringref)

    def test_addlist_listindex(self):
        gff = GFF()
        gff_list = gff.root.set_list("List", GFFList())

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [])
        config.modifiers.append(AddStructToListGFF("", None, "List"))
        config.modifiers.append(AddStructToListGFF("", None, "List"))
        config.modifiers.append(AddStructToListGFF("", None, "List"))
        config.apply(gff, memory)

        self.assertEqual(0, gff_list.at(0).struct_id)
        self.assertEqual(1, gff_list.at(1).struct_id)
        self.assertEqual(2, gff_list.at(2).struct_id)

    def test_addlist_store_2damemory(self):
        gff = GFF()
        gff.root.set_list("List", GFFList())

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [])
        config.modifiers.append(AddStructToListGFF("", 0, path="List"))
        config.modifiers.append(AddStructToListGFF("", 0, path="List", index_to_token=12))
        config.apply(gff, memory)

        self.assertEqual("1", memory.memory_2da[12])


class TestManipulateSSF(TestCase):
    def test_assign_int(self):
        ssf = SSF()

        memory = PatcherMemory()

        config = ModificationsSSF("", False, [])
        config.modifiers.append(ModifySSF(SSFSound.BATTLE_CRY_1, NoTokenUsage(5)))
        config.apply(ssf, memory)

        self.assertEqual(5, ssf.get(SSFSound.BATTLE_CRY_1))

    def test_assign_2datoken(self):
        ssf = SSF()

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"

        config = ModificationsSSF("", False, [])
        config.modifiers.append(ModifySSF(SSFSound.BATTLE_CRY_2, TokenUsage2DA(5)))
        config.apply(ssf, memory)

        self.assertEqual(123, ssf.get(SSFSound.BATTLE_CRY_2))

    def test_assign_tlktoken(self):
        ssf = SSF()

        memory = PatcherMemory()
        memory.memory_str[5] = 321

        config = ModificationsSSF("", False, [])
        config.modifiers.append(ModifySSF(SSFSound.BATTLE_CRY_3, TokenUsageTLK(5)))
        config.apply(ssf, memory)

        self.assertEqual(321, ssf.get(SSFSound.BATTLE_CRY_3))

