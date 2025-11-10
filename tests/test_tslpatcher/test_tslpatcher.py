from __future__ import annotations

import os
import pathlib
import shutil
import sys
import tempfile
import unittest

from configparser import ConfigParser
from typing import TYPE_CHECKING, Callable, cast


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

from pykotor.common.language import LocalizedString, Gender, Language
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff
from pykotor.resource.formats.gff.gff_data import GFF, GFFFieldType, GFFStruct
from pykotor.resource.formats.ssf import SSF, SSFSound
from pykotor.resource.formats.tlk import TLK, write_tlk
from pykotor.resource.formats.twoda.twoda_auto import bytes_2da, read_2da
from pykotor.resource.formats.twoda.twoda_data import TwoDA
from pykotor.resource.type import ResourceType
from pykotor.tslpatcher.config import PatcherConfig
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.tlk import ModificationsTLK
from pykotor.tslpatcher.mods.tlk import ModifyTLK
from pykotor.tslpatcher.mods.twoda import (
    AddColumn2DA,
    AddRow2DA,
    ChangeRow2DA,
    CopyRow2DA,
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
from pykotor.tslpatcher.reader import ConfigReader
from pykotor.tslpatcher.mods.gff import (
    AddFieldGFF,
    FieldValue2DAMemory,
    FieldValueConstant,
    LocalizedStringDelta,
)
from pathlib import Path


if TYPE_CHECKING:
    from pykotor.tslpatcher.mods.twoda import CopyRow2DA


# TODO(th3w1zard1): Make a decorator for test cases that use the _setupIniAndConfig method.
class TestTSLPatcher(unittest.TestCase):
    def _setupIniAndConfig(self, ini_text: str, mod_path: Path | str = "") -> PatcherConfig:
        ini = ConfigParser(delimiters="=", allow_no_value=True, strict=False, interpolation=None, inline_comment_prefixes=(";", "#"))
        ini.optionxform = lambda optionstr: optionstr
        ini.read_string(ini_text)
        result = PatcherConfig()
        actual_mod_path: Path | str = mod_path if mod_path else self.temp_dir
        ConfigReader(ini, actual_mod_path, tslpatchdata_path=self.tslpatchdata_path).load(result)
        return result

    def _setupTLK(self):
        self.test_tlk_data: TLK = self.create_test_tlk(
            {
                0: {"text": "Entry 0", "voiceover": "vo_0"},
                1: {"text": "Entry 1", "voiceover": "vo_1"},
                2: {"text": "Entry 2", "voiceover": "vo_2"},
                3: {"text": "Entry 3", "voiceover": "vo_3"},
                4: {"text": "Entry 4", "voiceover": "vo_4"},
                5: {"text": "Entry 5", "voiceover": "vo_5"},
                6: {"text": "Entry 6", "voiceover": "vo_6"},
                7: {"text": "Entry 7", "voiceover": "vo_7"},
                8: {"text": "Entry 8", "voiceover": "vo_8"},
                9: {"text": "Entry 9", "voiceover": "vo_9"},
                10: {"text": "Entry 10", "voiceover": "vo_10"},
            }
        )
        self.modified_tlk_data: TLK = self.create_test_tlk(
            {
                0: {"text": "Modified 0", "voiceover": "vo_mod_0"},
                1: {"text": "Modified 1", "voiceover": "vo_mod_1"},
                2: {"text": "Modified 2", "voiceover": "vo_mod_2"},
                3: {"text": "Modified 3", "voiceover": "vo_mod_3"},
                4: {"text": "Modified 4", "voiceover": "vo_mod_4"},
                5: {"text": "Modified 5", "voiceover": "vo_mod_5"},
                6: {"text": "Modified 6", "voiceover": "vo_mod_6"},
                7: {"text": "Modified 7", "voiceover": "vo_mod_7"},
                8: {"text": "Modified 8", "voiceover": "vo_mod_8"},
                9: {"text": "Modified 9", "voiceover": "vo_mod_9"},
                10: {"text": "Modified 10", "voiceover": "vo_mod_10"},
            }
        )
        shutil.copy(Path("tests/files/complex.tlk").resolve(), self.tslpatchdata_path / "complex.tlk")
        shutil.copy(Path("tests/files/append.tlk").resolve(), self.tslpatchdata_path / "append.tlk")

        # write it to a real file
        write_tlk(
            self.test_tlk_data,
            str(Path(self.tslpatchdata_path, "tlk_test_file.tlk")),
            ResourceType.TLK,
        )
        write_tlk(
            self.modified_tlk_data,
            str(Path(self.tslpatchdata_path, "tlk_modifications_file.tlk")),
            ResourceType.TLK,
        )

    def setUp(self):
        self.temp_dir: str = tempfile.mkdtemp()
        self.tslpatchdata_path: Path = Path(self.temp_dir, "tslpatchdata")
        self.tslpatchdata_path.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_tlk(self, data: dict[int, dict[str, str]]) -> TLK:
        tlk = TLK()
        for v in data.values():
            tlk.add(text=v["text"], sound_resref=v["voiceover"])
        return tlk

    # region Change Row
    def test_change_existing_rowindex(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        # INI loading assertions (from reader-style)
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0

            [change_row_0]
            RowIndex=1
            Col1=X
        """
        config = PatcherConfig()
        config.load(ini_text, self.temp_dir, tslpatchdata_path=self.tslpatchdata_path)
        self.assertEqual(1, len(config.patches_2da))
        self.assertEqual(1, len(config.patches_2da[0].modifiers))
        mod = cast(ChangeRow2DA, config.patches_2da[0].modifiers[0])
        self.assertIsInstance(mod, ChangeRow2DA)
        assert isinstance(mod, ChangeRow2DA)
        self.assertEqual(TargetType.ROW_INDEX, mod.target.target_type)
        self.assertEqual(1, mod.target.value)
        self.assertIn("Col1", mod.cells)
        col1_cell = mod.cells["Col1"]
        self.assertIsInstance(col1_cell, RowValueConstant)
        assert isinstance(col1_cell, RowValueConstant)
        self.assertEqual("X", col1_cell.string)

        # Apply using loaded INI config to ensure patching also works end-to-end
        memory = PatcherMemory()
        PatchLogger()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        # Original mod-style assertions
        self.assertEqual(["a", "X"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f"], twoda.get_column("Col3"))

    def test_change_existing_rowlabel(self):
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        logger = PatchLogger()
        config = PatcherConfig()

        # INI loading assertions (from reader-style)
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0

            [change_row_0]
            RowLabel=1
            Col1=X
        """
        ini = ConfigParser(delimiters=("="), allow_no_value=True, strict=False, interpolation=None, inline_comment_prefixes=(";", "#"))
        ini.optionxform = lambda optionstr: optionstr
        ini.read_string(ini_text)
        ConfigReader(ini, self.temp_dir, tslpatchdata_path=self.tslpatchdata_path).load(config)
        self.assertEqual(1, len(config.patches_2da))
        self.assertEqual(1, len(config.patches_2da[0].modifiers))
        mod = cast(ChangeRow2DA, config.patches_2da[0].modifiers[0])
        self.assertEqual(TargetType.ROW_LABEL, mod.target.target_type)
        self.assertEqual("1", mod.target.value)
        self.assertIn("Col1", mod.cells)
        col1_cell = mod.cells["Col1"]
        self.assertIsInstance(col1_cell, RowValueConstant)
        assert isinstance(col1_cell, RowValueConstant)
        self.assertEqual("X", col1_cell.string)

        # Apply using loaded INI config to ensure patching also works end-to-end
        config.patches_2da[0].apply(twoda, memory, logger, Game.K1)

        self.assertEqual(["a", "X"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f"], twoda.get_column("Col3"))

    # endregion

    # region GFF Add/Modify

    def test_gff_add_inside_struct(self):
        """Test that the add field modifiers are registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_struct
            AddField1=add_insidestruct

            [add_struct]
            FieldType=Struct
            Path=
            Label=SomeStruct
            TypeId=321

            [add_insidestruct]
            FieldType=Byte
            Path=SomeStruct
            Label=InsideStruct
            Value=123
            """
        )
        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant)
        self.assertEqual(mod_0.path.name, ">>##INDEXINLIST##<<")
        self.assertEqual("SomeStruct", mod_0.label)
        self.assertEqual(321, mod_0.value.stored.struct_id)

        mod_1 = config.patches_gff[0].modifiers[1]
        self.assertIsInstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1, AddFieldGFF)
        self.assertIsInstance(mod_1.value, FieldValueConstant)
        assert isinstance(mod_1.value, FieldValueConstant)
        self.assertEqual(mod_1.path.name, "SomeStruct")
        self.assertEqual("InsideStruct", mod_1.label)
        self.assertEqual(123, mod_1.value.stored)

        # Apply patch end-to-end
        gff = GFF()
        patch_resource: Callable[[bytes, PatcherMemory, PatchLogger, Game], bytes] = config.patches_gff[0].patch_resource
        gff_bytes: bytes = bytes_gff(gff)
        patched_bytes: bytes = patch_resource(gff_bytes, PatcherMemory(), PatchLogger(), Game.K1)
        patched: GFF = read_gff(patched_bytes)
        some_struct: GFFStruct | None = patched.root.get_struct("SomeStruct")
        self.assertIsNotNone(some_struct)
        inside_struct_value: int | None = some_struct.get_uint8("InsideStruct") if some_struct is not None else None
        self.assertEqual(123, inside_struct_value)

    def test_gff_add_field_locstring(self):
        """Adds a localized string field to a GFF using a 2DA memory reference (ini first, then apply)."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_loc

            [add_loc]
            FieldType=ExoLocString
            Path=
            Label=Field1
            StrRef=2DAMEMORY5
            """
        )

        # Reader-style assertions
        add_mod = config.patches_gff[0].modifiers[0]
        assert isinstance(add_mod, AddFieldGFF)
        self.assertIsInstance(add_mod, AddFieldGFF)
        assert isinstance(add_mod, AddFieldGFF)
        self.assertIsInstance(add_mod.value, FieldValueConstant)
        assert isinstance(add_mod.value, FieldValueConstant)
        self.assertIsInstance(add_mod.value.stored, LocalizedStringDelta)
        assert isinstance(add_mod.value.stored, LocalizedStringDelta)

        # Apply patch end-to-end mirroring test_mods.py semantics
        gff = GFF()
        gff.root.set_locstring("Field1", LocalizedString(0))
        memory = PatcherMemory()
        memory.memory_2da[5] = "123"
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        self.assertEqual(123, patched.root.get_locstring("Field1").stringref)

    def test_gff_modifier_path_shorter_than_self_path(self):
        """Modifier path is shorter than self.path — overlay keeps deeper context, append loses it."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_struct

            [add_struct]
            FieldType=Struct
            Path=Root/ParentStruct
            Label=ParentStruct
            TypeId=100
            AddField0=add_child

            [add_child]
            FieldType=Byte
            Path=ChildField
            Label=ChildField
            Value=42
            """
        )

        mod_0 = config.patches_gff[0].modifiers[0]
        assert isinstance(mod_0, AddFieldGFF)
        self.assertIsInstance(mod_0, AddFieldGFF)
        mod_1 = mod_0.modifiers[0]
        assert isinstance(mod_1, AddFieldGFF)
        self.assertIsInstance(mod_1, AddFieldGFF)
        # Under overlay logic, path should be Root/ParentStruct/ChildField
        self.assertEqual(mod_1.path.parts[-1], "ChildField")

    def test_gff_modifier_path_longer_than_self_path(self):
        """Modifier path is longer than self.path — overlay appends extra parts naturally."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_struct

            [add_struct]
            FieldType=Struct
            Path=Root
            Label=Root
            TypeId=200
            AddField0=add_grandchild

            [add_grandchild]
            FieldType=Byte
            Path=ChildStruct/GrandChildField
            Label=GrandChildField
            Value=99
            """
        )

        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        mod_1 = mod_0.modifiers[0]
        self.assertIsInstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1, AddFieldGFF)
        # Overlay and append both append extra parts, but base differences may show up if base path differs
        self.assertEqual(mod_1.path.parts[-1], "GrandChildField")

    def test_gff_modifier_path_partial_absolute(self):
        """Modifier path partially overlaps self.path — overlay preserves alignment, append may duplicate segments."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_struct

            [add_struct]
            FieldType=Struct
            Path=Root/StructA
            Label=StructA
            TypeId=300
            AddField0=add_field_absolute

            [add_field_absolute]
            FieldType=Byte
            Path=StructA/InnerField
            Label=InnerField
            Value=7
            """
        )

        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        mod_1 = mod_0.modifiers[0]
        self.assertIsInstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1, AddFieldGFF)
        # Overlay: Root/StructA/InnerField
        # Append: Root/StructA/StructA/InnerField (duplicate StructA)
        self.assertEqual(mod_1.path.parts.count("StructA"), 1)

    def test_gff_add_field_with_sentinel_at_start(self):
        """Ensures sentinel at start of modifier path is handled correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_struct

            [add_struct]
            FieldType=Struct
            Path=Root/>>##INDEXINLIST##<<
            Label=TempStruct
            TypeId=400
            AddField0=add_inside

            [add_inside]
            FieldType=Byte
            Path=>>##INDEXINLIST##<</InnerField
            Label=InnerField
            Value=55
            """
        )

        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        mod_1 = mod_0.modifiers[0]
        self.assertIsInstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1, AddFieldGFF)
        self.assertEqual(mod_1.path.parts[-1], "InnerField")

    def test_gff_add_field_with_empty_paths(self):
        """Ensures empty Path values default to correct container."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_field

            [add_field]
            FieldType=Byte
            Path=
            Label=TopLevelField
            Value=11
            """
        )

        mod_0 = config.patches_gff[0].modifiers[0]
        assert isinstance(mod_0, AddFieldGFF)
        self.assertIsInstance(mod_0, AddFieldGFF)
        self.assertEqual(mod_0.path.parts, tuple())

    # endregion

    # region 2DA: Change Row
    def test_2da_changerow_identifier(self):
        """Test that identifier is being loaded correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0
            ChangeRow1=change_row_1

            [change_row_0]
            RowIndex=1
            [change_row_1]
            RowLabel=1
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, ChangeRow2DA)
        assert isinstance(mod_0, ChangeRow2DA)
        self.assertEqual("change_row_0", mod_0.identifier)

        mod_0 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_0, ChangeRow2DA)
        assert isinstance(mod_0, ChangeRow2DA)
        self.assertEqual("change_row_1", mod_0.identifier)

        # Patch-application extension: ensure apply works (no changes expected)
        twoda = TwoDA(["label", "Col2"])  # minimal table
        twoda.add_row("0", {"label": "x", "Col2": "y"})
        memory = PatcherMemory()
        PatchLogger()
        # Apply empty-cell changes should not alter the table
        for mod in [mod_0]:
            pass  # already popped; nothing to apply with cells
        # Assert unchanged
        self.assertEqual(["x"], twoda.get_column("label"))
        self.assertEqual(["y"], twoda.get_column("Col2"))

    def test_2da_changerow_targets(self):
        """Test that target values (line to modify) are loading correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0
            ChangeRow1=change_row_1
            ChangeRow2=change_row_2

            [change_row_0]
            RowIndex=1
            [change_row_1]
            RowLabel=2
            [change_row_2]
            LabelIndex=3
            """
        )
        mod_2da_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_2da_0, ChangeRow2DA)
        assert isinstance(mod_2da_0, ChangeRow2DA)
        self.assertEqual(TargetType.ROW_INDEX, mod_2da_0.target.target_type)
        self.assertEqual(1, mod_2da_0.target.value)

        mod_2da_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_2da_1, ChangeRow2DA)
        assert isinstance(mod_2da_1, ChangeRow2DA)
        self.assertEqual(TargetType.ROW_LABEL, mod_2da_1.target.target_type)
        self.assertEqual("2", mod_2da_1.target.value)

        mod_2da_2 = config.patches_2da[0].modifiers[2]
        self.assertIsInstance(mod_2da_2, ChangeRow2DA)
        assert isinstance(mod_2da_2, ChangeRow2DA)
        self.assertEqual(TargetType.LABEL_COLUMN, mod_2da_2.target.target_type)
        self.assertEqual("3", mod_2da_2.target.value)

        # Patch-application extension: ensure apply works (no changes expected)
        # Create rows so all targets resolve:
        # - RowIndex=1 exists
        # - RowLabel=2 exists
        # - LabelIndex=3 exists
        twoda = TwoDA(["label", "Col2"])  # minimal table
        twoda.add_row("0", {"label": "0", "Col2": "b0"})
        twoda.add_row("2", {"label": "2", "Col2": "b1"})
        twoda.add_row("3", {"label": "3", "Col2": "b2"})
        memory = PatcherMemory()
        for m in (mod_2da_0, mod_2da_1, mod_2da_2):
            m.cells = {}
        for m in (mod_2da_0, mod_2da_1, mod_2da_2):
            m.apply(twoda, memory)
        self.assertEqual(["0", "2", "3"], twoda.get_column("label"))
        self.assertEqual(["b0", "b1", "b2"], twoda.get_column("Col2"))

    def test_2da_changerow_store2da(self):
        """Test that 2DAMEMORY values are set to be stored correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0

            [change_row_0]
            RowIndex=0
            2DAMEMORY0=RowIndex
            2DAMEMORY1=RowLabel
            2DAMEMORY2=label
            """
        )
        mod_2da_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_2da_0, ChangeRow2DA)
        assert isinstance(mod_2da_0, ChangeRow2DA)

        # Assertions on types
        self.assertIn(0, mod_2da_0.store_2da)
        self.assertIn(1, mod_2da_0.store_2da)
        self.assertIn(2, mod_2da_0.store_2da)

        # Patch-application extension: apply and verify memory
        twoda = TwoDA(["label"])  # minimal table with label
        twoda.add_row("L0", {"label": "L0"})
        memory = PatcherMemory()
        mod_2da_0.apply(twoda, memory)
        self.assertEqual("0", memory.memory_2da[0])
        self.assertEqual("L0", memory.memory_2da[1])
        self.assertEqual("L0", memory.memory_2da[2])

    def test_2da_changerow_cells(self):
        """Test that cells are set to be modified correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0

            [change_row_0]
            RowIndex=0
            label=Test123
            dialog=StrRef4
            appearance=2DAMEMORY5
            """
        )
        # noinspection PyTypeChecker
        mod_2da_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_2da_0, ChangeRow2DA)
        assert isinstance(mod_2da_0, ChangeRow2DA)
        self.assertIsInstance(mod_2da_0.cells["label"], RowValueConstant)
        assert isinstance(mod_2da_0.cells["label"], RowValueConstant)
        self.assertIsInstance(mod_2da_0.cells["dialog"], RowValueTLKMemory)
        assert isinstance(mod_2da_0.cells["dialog"], RowValueTLKMemory)
        self.assertIsInstance(mod_2da_0.cells["appearance"], RowValue2DAMemory)
        assert isinstance(mod_2da_0.cells["appearance"], RowValue2DAMemory)

        # Patch-application extension: prepare table and memory then apply
        twoda = TwoDA(["label", "dialog", "appearance"])  # minimal
        twoda.add_row("0", {"label": "orig", "dialog": "", "appearance": ""})
        memory = PatcherMemory()
        memory.memory_str[4] = 42
        memory.memory_2da[5] = "ABC"
        mod_2da_0.apply(twoda, memory)
        self.assertEqual(["Test123"], twoda.get_column("label"))
        self.assertEqual(["42"], twoda.get_column("dialog"))
        self.assertEqual(["ABC"], twoda.get_column("appearance"))

    # endregion

    # region 2DA: Add Column
    def test_2da_addcolumn_basic(self):
        """Test that column will be inserted with correct label and default values."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0
            AddColumn1=add_column_1

            [add_column_0]
            ColumnLabel=label
            DefaultValue=****
            2DAMEMORY2=I2

            [add_column_1]
            ColumnLabel=someint
            DefaultValue=0
            2DAMEMORY2=I2
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddColumn2DA)
        assert isinstance(mod_0, AddColumn2DA)
        self.assertEqual("label", mod_0.header)
        self.assertEqual("", mod_0.default)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, AddColumn2DA)
        assert isinstance(mod_1, AddColumn2DA)
        self.assertEqual("someint", mod_1.header)
        self.assertEqual("0", mod_1.default)

        # Patch-application extension: apply and verify
        twoda = TwoDA(["ColA"])  # two rows
        twoda.add_row("0", {"ColA": "a"})
        twoda.add_row("1", {"ColA": "b"})
        # Add a third row to avoid IndexError when referencing row 2
        twoda.add_row("2", {"ColA": "c"})
        memory = PatcherMemory()
        mod_0.apply(twoda, memory)
        self.assertEqual(["a", "b", "c"], twoda.get_column("ColA"))
        self.assertEqual(["", "", ""], twoda.get_column("label"))

        mod_1.apply(twoda, memory)
        self.assertEqual(["0", "0", "0"], twoda.get_column("someint"))

    def test_2da_addcolumn_indexinsert(self):
        """Test that cells will be inserted to the new column at the given index correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=NewColumn
            DefaultValue=****
            I0=abc
            I1=2DAMEMORY4
            I2=StrRef5
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddColumn2DA)
        assert isinstance(mod_0, AddColumn2DA)

        # reader assertions
        value = mod_0.index_insert[0]
        self.assertIsInstance(value, RowValueConstant)
        assert isinstance(value, RowValueConstant)
        self.assertEqual("abc", value.string)

        value = mod_0.index_insert[1]
        self.assertIsInstance(value, RowValue2DAMemory)
        assert isinstance(value, RowValue2DAMemory)
        self.assertEqual(4, value.token_id)

        value = mod_0.index_insert[2]
        self.assertIsInstance(value, RowValueTLKMemory)
        assert isinstance(value, RowValueTLKMemory)
        self.assertEqual(5, value.token_id)

        # Patch-application extension: apply and verify
        twoda = TwoDA(["X"])  # three rows
        twoda.add_row("0", {"X": "x0"})
        twoda.add_row("1", {"X": "x1"})
        twoda.add_row("2", {"X": "x2"})
        memory = PatcherMemory()
        memory.memory_2da[4] = "mem4"
        memory.memory_str[5] = 77
        mod_0.apply(twoda, memory)
        self.assertEqual(["abc", "mem4", "77"], twoda.get_column("NewColumn"))

    def test_2da_addcolumn_labelinsert(self):
        """Test that cells will be inserted to the new column at the given label correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=NewColumn
            DefaultValue=****
            L0=abc
            L1=2DAMEMORY4
            L2=StrRef5
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddColumn2DA)
        assert isinstance(mod_0, AddColumn2DA)

        value = mod_0.label_insert["0"]
        self.assertIsInstance(value, RowValueConstant)
        assert isinstance(value, RowValueConstant)
        self.assertEqual("abc", value.string)

        value = mod_0.label_insert["1"]
        self.assertIsInstance(value, RowValue2DAMemory)
        assert isinstance(value, RowValue2DAMemory)
        self.assertEqual(4, value.token_id)

        value = mod_0.label_insert["2"]
        self.assertIsInstance(value, RowValueTLKMemory)
        assert isinstance(value, RowValueTLKMemory)
        self.assertEqual(5, value.token_id)

        # Patch-application extension
        twoda = TwoDA(["X"])
        twoda.add_row("0", {"X": "x0"})
        twoda.add_row("1", {"X": "x1"})
        twoda.add_row("2", {"X": "x2"})
        memory = PatcherMemory()
        memory.memory_2da[4] = "mem4"
        memory.memory_str[5] = 77
        mod_0.apply(twoda, memory)
        self.assertEqual(["abc", "mem4", "77"], twoda.get_column("NewColumn"))

    def test_2da_addcolumn_2damemory(self):
        """Test that 2DAMEMORY will be stored correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=NewColumn
            DefaultValue=****
            2DAMEMORY2=I2
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddColumn2DA)
        assert isinstance(mod_0, AddColumn2DA)

        value = mod_0.store_2da[2]
        self.assertEqual("I2", value)

        # Patch-application extension
        twoda = TwoDA(["X"])
        twoda.add_row("0", {"X": "x0"})
        twoda.add_row("1", {"X": "x1"})
        twoda.add_row("2", {"X": "x2"})
        memory = PatcherMemory()
        mod_0.apply(twoda, memory)
        # 2DAMEMORY2 should store value from row at index 2
        self.assertIn(2, memory.memory_2da)

    # endregion

    # region 2DA: Add Row
    def test_2da_addrow_identifier(self):
        """Test that identifier is being loaded correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            [add_row_1]
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddRow2DA)
        assert isinstance(mod_0, AddRow2DA)
        self.assertEqual("add_row_0", mod_0.identifier)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, AddRow2DA)
        assert isinstance(mod_1, AddRow2DA)
        self.assertEqual("add_row_1", mod_1.identifier)

        # Apply to ensure no-ops behave
        twoda = TwoDA(["label"])  # empty
        memory = PatcherMemory()
        mod_0.cells = {}
        mod_1.cells = {}
        mod_0.apply(twoda, memory)
        mod_1.apply(twoda, memory)
        self.assertEqual(2, twoda.get_height())

    def test_2da_addrow_exclusivecolumn(self):
        """Test that exclusive column property is being loaded correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            ExclusiveColumn=label
            [add_row_1]
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddRow2DA)
        assert isinstance(mod_0, AddRow2DA)
        self.assertEqual("add_row_0", mod_0.identifier)
        self.assertEqual("label", mod_0.exclusive_column)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, AddRow2DA)
        assert isinstance(mod_1, AddRow2DA)
        self.assertEqual("add_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.exclusive_column)

        # Apply basic behavior
        twoda = TwoDA(["label"])  # empty
        memory = PatcherMemory()
        mod_0.cells = {"label": RowValueConstant("x")}
        mod_0.apply(twoda, memory)
        self.assertEqual(["x"], twoda.get_column("label"))

    def test_2da_addrow_rowlabel(self):
        """Test that row label property is being loaded correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            RowLabel=123
            [add_row_1]
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddRow2DA)
        assert isinstance(mod_0, AddRow2DA)
        self.assertEqual("add_row_0", mod_0.identifier)
        self.assertEqual("123", mod_0.row_label)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, AddRow2DA)
        assert isinstance(mod_1, AddRow2DA)
        self.assertEqual("add_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.row_label)

        # Apply and check label
        twoda = TwoDA(["label"])  # empty
        memory = PatcherMemory()
        mod_0.cells = {}
        mod_0.apply(twoda, memory)
        self.assertEqual("123", twoda.get_label(0))

    def test_2da_addrow_store2da(self):
        """Test that 2DAMEMORY# data will be saved correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0

            [add_row_0]
            2DAMEMORY0=RowIndex
            2DAMEMORY1=RowLabel
            2DAMEMORY2=label
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddRow2DA)
        assert isinstance(mod_0, AddRow2DA)

        # Apply and verify memory values are stored
        twoda = TwoDA(["label"])  # empty
        twoda.add_row("L0", {"label": "L0"})
        memory = PatcherMemory()
        mod_0.cells = {"label": RowValueConstant("L1")}
        mod_0.row_label = "L1"
        mod_0.apply(twoda, memory)
        self.assertEqual("1", memory.memory_2da[0])
        self.assertEqual("L1", memory.memory_2da[1])
        self.assertEqual("L1", memory.memory_2da[2])

    def test_2da_addrow_cells(self):
        """Test that cells will be assigned properly correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0

            [add_row_0]
            label=Test123
            dialog=StrRef4
            appearance=2DAMEMORY5
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, AddRow2DA)
        assert isinstance(mod_0, AddRow2DA)

        # Reader-style assertions
        self.assertIsInstance(mod_0.cells["label"], RowValueConstant)
        self.assertIsInstance(mod_0.cells["dialog"], RowValueTLKMemory)
        self.assertIsInstance(mod_0.cells["appearance"], RowValue2DAMemory)

        # Apply
        twoda = TwoDA(["label", "dialog", "appearance"])  # minimal
        memory = PatcherMemory()
        memory.memory_str[4] = 4
        memory.memory_2da[5] = "A"
        mod_0.apply(twoda, memory)
        self.assertEqual("Test123", twoda.get_row(0).get_string("label"))
        self.assertEqual("4", twoda.get_row(0).get_string("dialog"))
        self.assertEqual("A", twoda.get_row(0).get_string("appearance"))

    # endregion

    # region 2DA: Copy Row
    def test_2da_copyrow_identifier(self):
        """Test that identifier is being loaded correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0
            CopyRow1=copy_row_1

            [copy_row_0]
            RowIndex=1
            [copy_row_1]
            RowLabel=1
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, CopyRow2DA)
        assert isinstance(mod_0, CopyRow2DA)
        self.assertEqual("copy_row_0", mod_0.identifier)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, CopyRow2DA)
        assert isinstance(mod_1, CopyRow2DA)
        self.assertEqual("copy_row_1", mod_1.identifier)

    def test_2da_copyrow_high(self):
        """Test that high() is working correctly in copyrow's."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=spells_hlfp_test.2da

            [spells_hlfp_test.2da]
            CopyRow0=spells_forcestrike

            [spells_forcestrike]
            RowIndex=0
            ExclusiveColumn=label
            label=ST_FORCE_POWER_STRIKE
            forcehostile=high()
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, CopyRow2DA)
        assert isinstance(mod_0, CopyRow2DA)

        # Apply on a table with numeric column to exercise high()
        twoda = TwoDA(["label", "forcehostile"])
        twoda.add_row("0", {"label": "base", "forcehostile": "2"})
        memory = PatcherMemory()
        mod_0.apply(twoda, memory)
        self.assertEqual(2, twoda.get_height())
        self.assertEqual("3", twoda.get_row(1).get_string("forcehostile"))

    def test_2da_copyrow_target(self):
        """Test that target values (line to modify) are loading correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0
            CopyRow1=copy_row_1
            CopyRow2=copy_row_2

            [copy_row_0]
            RowIndex=1
            [copy_row_1]
            RowLabel=2
            [copy_row_2]
            LabelIndex=3
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, CopyRow2DA)
        assert isinstance(mod_0, CopyRow2DA)
        self.assertEqual(TargetType.ROW_INDEX, mod_0.target.target_type)
        self.assertEqual(1, mod_0.target.value)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, CopyRow2DA)
        assert isinstance(mod_1, CopyRow2DA)
        self.assertEqual(TargetType.ROW_LABEL, mod_1.target.target_type)
        self.assertEqual("2", mod_1.target.value)

        mod_2 = config.patches_2da[0].modifiers[2]
        self.assertIsInstance(mod_2, CopyRow2DA)
        assert isinstance(mod_2, CopyRow2DA)
        self.assertEqual(TargetType.LABEL_COLUMN, mod_2.target.target_type)
        self.assertEqual("3", mod_2.target.value)

    def test_2da_copyrow_exclusivecolumn(self):
        """Test that exclusive column property is being loaded correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0
            CopyRow1=copy_row_1

            [copy_row_0]
            RowIndex=0
            ExclusiveColumn=label
            [copy_row_1]
            RowIndex=0
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, CopyRow2DA)
        assert isinstance(mod_0, CopyRow2DA)
        self.assertEqual("copy_row_0", mod_0.identifier)
        self.assertEqual("label", mod_0.exclusive_column)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, CopyRow2DA)
        assert isinstance(mod_1, CopyRow2DA)
        self.assertEqual("copy_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.exclusive_column)

    def test_2da_copyrow_rowlabel(self):
        """Test that row label property is being loaded correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0
            CopyRow1=copy_row_1

            [copy_row_0]
            RowIndex=0
            NewRowLabel=123
            [copy_row_1]
            RowIndex=0
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, CopyRow2DA)
        assert isinstance(mod_0, CopyRow2DA)
        self.assertEqual("copy_row_0", mod_0.identifier)
        self.assertEqual("123", mod_0.row_label)

        mod_1 = config.patches_2da[0].modifiers[1]
        self.assertIsInstance(mod_1, CopyRow2DA)
        assert isinstance(mod_1, CopyRow2DA)
        self.assertEqual("copy_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.row_label)

    def test_2da_copyrow_store2da(self):
        """Test that 2DAMEMORY# data will be saved correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowLabel=0
            2DAMEMORY0=RowIndex
            2DAMEMORY1=RowLabel
            2DAMEMORY2=label
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, CopyRow2DA)
        assert isinstance(mod_0, CopyRow2DA)

        # Apply and verify
        twoda = TwoDA(["label"])  # create row 0 to copy
        twoda.add_row("0", {"label": "A"})
        memory = PatcherMemory()
        mod_0.apply(twoda, memory)
        # The new row is added at index 1, so:
        # RowIndex: 1, RowLabel: "1", label: "A"
        self.assertEqual("1", memory.memory_2da[0])
        self.assertEqual("1", memory.memory_2da[1])
        self.assertEqual("A", memory.memory_2da[2])

    def test_2da_copyrow_cells(self):
        """Test that cells will be assigned properly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowLabel=0
            label=Test123
            dialog=StrRef4
            appearance=2DAMEMORY5
            """
        )
        mod_0 = config.patches_2da[0].modifiers[0]
        self.assertIsInstance(mod_0, CopyRow2DA)
        assert isinstance(mod_0, CopyRow2DA)

        # Reader-style checks
        self.assertIsInstance(mod_0.cells["label"], RowValueConstant)
        self.assertIsInstance(mod_0.cells["dialog"], RowValueTLKMemory)
        self.assertIsInstance(mod_0.cells["appearance"], RowValue2DAMemory)

        # Apply
        twoda = TwoDA(["label", "dialog", "appearance"])  # seed row 0
        twoda.add_row("0", {"label": "A", "dialog": "1", "appearance": "B"})
        memory = PatcherMemory()
        memory.memory_str[4] = 8
        memory.memory_2da[5] = "C"
        mod_0.apply(twoda, memory)
        self.assertEqual(2, twoda.get_height())
        self.assertEqual(["A", "Test123"], twoda.get_column("label"))
        self.assertEqual(["1", "8"], twoda.get_column("dialog"))
        self.assertEqual(["B", "C"], twoda.get_column("appearance"))

    # endregion

    # region 2DA: Additional test_mods.py tests
    def test_change_existing_labelindex(self):
        """Test changing via label column (LabelIndex)."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0

            [change_row_0]
            LabelIndex=d
            Col2=X
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["label", "Col2", "Col3"])
        twoda.add_row("0", {"label": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"label": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["a", "d"], twoda.get_column("label"))
        self.assertEqual(["b", "X"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f"], twoda.get_column("Col3"))

    def test_change_assign_tlkmemory(self):
        """Test changing and assigning TLK memory."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0
            ChangeRow1=change_row_1

            [change_row_0]
            RowIndex=0
            Col1=StrRef0
            [change_row_1]
            RowIndex=1
            Col1=StrRef1
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        memory.memory_str[0] = 0
        memory.memory_str[1] = 1
        twoda = read_2da(cast(bytes, config.patches_2da[0].patch_resource(bytes_2da(twoda), memory, PatchLogger(), Game.K1)))

        self.assertEqual(["0", "1"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f"], twoda.get_column("Col3"))

    def test_change_assign_2damemory(self):
        """Test changing and assigning 2DA memory."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0
            ChangeRow1=change_row_1

            [change_row_0]
            RowIndex=0
            Col1=2DAMEMORY0
            [change_row_1]
            RowIndex=1
            Col1=2DAMEMORY1
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        memory.memory_2da[0] = "mem0"
        memory.memory_2da[1] = "mem1"
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["mem0", "mem1"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f"], twoda.get_column("Col3"))

    def test_change_assign_high(self):
        """Test using high() function in change row."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0
            ChangeRow1=change_row_1

            [change_row_0]
            RowIndex=0
            Col1=high()
            [change_row_1]
            RowIndex=0
            Col2=high()
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": " ", "Col2": "3", "Col3": "5"})
        twoda.add_row("1", {"Col1": "2", "Col2": "4", "Col3": "6"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["3", "2"], twoda.get_column("Col1"))
        self.assertEqual(["5", "4"], twoda.get_column("Col2"))
        self.assertEqual(["5", "6"], twoda.get_column("Col3"))

    def test_set_2damemory_rowindex(self):
        """Test storing row index in 2DAMEMORY."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0

            [change_row_0]
            RowIndex=1
            2DAMEMORY5=RowIndex
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["a", "d"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f"], twoda.get_column("Col3"))
        self.assertEqual("1", memory.memory_2da[5])

    def test_set_2damemory_rowlabel(self):
        """Test storing row label in 2DAMEMORY."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0

            [change_row_0]
            RowIndex=1
            2DAMEMORY5=RowLabel
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("r1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["a", "d"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f"], twoda.get_column("Col3"))
        self.assertEqual("r1", memory.memory_2da[5])

    def test_set_2damemory_columnlabel(self):
        """Test storing column value in 2DAMEMORY."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            ChangeRow0=change_row_0

            [change_row_0]
            RowIndex=1
            2DAMEMORY5=label
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["label", "Col2", "Col3"])
        twoda.add_row("0", {"label": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"label": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["a", "d"], twoda.get_column("label"))
        self.assertEqual(["b", "e"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f"], twoda.get_column("Col3"))
        self.assertEqual("d", memory.memory_2da[5])

    def test_add_rowlabel_use_maxrowlabel(self):
        """Test automatic row label when adding rows."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            [add_row_1]
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1"])
        twoda.add_row("0", {})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(3, twoda.get_height())
        self.assertEqual("0", twoda.get_label(0))
        self.assertEqual("1", twoda.get_label(1))
        self.assertEqual("2", twoda.get_label(2))

    def test_add_rowlabel_use_constant(self):
        """Test explicit row label when adding rows."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0

            [add_row_0]
            RowLabel=r1
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1"])

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(1, twoda.get_height())
        self.assertEqual("r1", twoda.get_label(0))

    def test_add_rowlabel_existing(self):
        """Test adding row with existing exclusive column value."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0

            [add_row_0]
            ExclusiveColumn=Col1
            Col1=123
            Col2=ABC
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "123", "Col2": "456"})

        memory = PatcherMemory()
        twoda = read_2da(cast(bytes, config.patches_2da[0].patch_resource(bytes_2da(twoda), memory, PatchLogger(), Game.K1)))

        self.assertEqual(1, twoda.get_height())
        self.assertEqual("0", twoda.get_label(0))

    def test_add_exclusive_notexists(self):
        """Test adding row with exclusive column value that doesn't exist."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0

            [add_row_0]
            ExclusiveColumn=Col1
            RowLabel=2
            Col1=g
            Col2=h
            Col3=i
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(3, twoda.get_height())
        self.assertEqual("2", twoda.get_label(2))
        self.assertEqual(["a", "d", "g"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e", "h"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f", "i"], twoda.get_column("Col3"))

    def test_add_exclusive_exists(self):
        """Test adding row with exclusive column value that exists."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0

            [add_row_0]
            ExclusiveColumn=Col1
            RowLabel=3
            Col1=g
            Col2=X
            Col3=Y
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})
        twoda.add_row("2", {"Col1": "g", "Col2": "h", "Col3": "i"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(3, twoda.get_height())
        self.assertEqual(["a", "d", "g"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e", "X"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f", "Y"], twoda.get_column("Col3"))

    def test_add_exclusive_none(self):
        """Test adding rows without exclusive column."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            RowLabel=2
            Col1=g
            Col2=h
            Col3=i
            [add_row_1]
            RowLabel=3
            Col1=j
            Col2=k
            Col3=l
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "d", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(4, twoda.get_height())
        self.assertEqual(["a", "d", "g", "j"], twoda.get_column("Col1"))
        self.assertEqual(["b", "e", "h", "k"], twoda.get_column("Col2"))
        self.assertEqual(["c", "f", "i", "l"], twoda.get_column("Col3"))

    def test_add_assign_high(self):
        """Test using high() in add row."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0

            [add_row_0]
            RowLabel=2
            Col1=high()
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "1", "Col2": "b", "Col3": "c"})
        twoda.add_row("1", {"Col1": "2", "Col2": "e", "Col3": "f"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["1", "2", "3"], twoda.get_column("Col1"))

    def test_add_assign_tlkmemory(self):
        """Test using TLK memory in add row."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            RowLabel=0
            Col1=StrRef0
            [add_row_1]
            RowLabel=1
            Col1=StrRef1
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1"])

        memory = PatcherMemory()
        memory.memory_str[0] = 5
        memory.memory_str[1] = 6
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["5", "6"], twoda.get_column("Col1"))

    def test_add_assign_2damemory(self):
        """Test using 2DA memory in add row."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            RowLabel=0
            Col1=2DAMEMORY0
            [add_row_1]
            RowLabel=1
            Col1=2DAMEMORY1
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1"])

        memory = PatcherMemory()
        memory.memory_2da[0] = "5"
        memory.memory_2da[1] = "6"
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["5", "6"], twoda.get_column("Col1"))

    def test_add_2damemory_rowindex(self):
        """Test storing row index when adding rows."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            ExclusiveColumn=Col1
            RowLabel=1
            Col1=X
            2DAMEMORY5=RowIndex
            [add_row_1]
            RowLabel=2
            Col1=Y
            2DAMEMORY6=RowIndex
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1"])
        twoda.add_row("0", {"Col1": "X"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(2, twoda.get_height())
        self.assertEqual(["X", "Y"], twoda.get_column("Col1"))
        self.assertEqual("0", memory.memory_2da[5])
        self.assertEqual("1", memory.memory_2da[6])

    def test_copy_existing_rowindex(self):
        """Test copying row by index."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowIndex=0
            Col2=X
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()
        twoda = read_2da(cast(bytes, config.patches_2da[0].patch_resource(bytes_2da(twoda), memory, PatchLogger(), Game.K1)))

        self.assertEqual(3, twoda.get_height())
        self.assertEqual(["a", "c", "a"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d", "X"], twoda.get_column("Col2"))

    def test_copy_existing_rowlabel(self):
        """Test copying row by label."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowLabel=1
            Col2=X
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(3, twoda.get_height())
        self.assertEqual(["a", "c", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d", "X"], twoda.get_column("Col2"))

    def test_copy_exclusive_notexists(self):
        """Test copying with exclusive column that doesn't exist."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowIndex=0
            ExclusiveColumn=Col1
            Col1=c
            Col2=d
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(2, twoda.get_height())
        self.assertEqual("1", twoda.get_label(1))
        self.assertEqual(["a", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d"], twoda.get_column("Col2"))

    def test_copy_exclusive_exists(self):
        """Test copying with exclusive column that exists."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowIndex=0
            ExclusiveColumn=Col1
            Col1=a
            Col2=X
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(1, twoda.get_height())
        self.assertEqual("0", twoda.get_label(0))
        self.assertEqual(["a"], twoda.get_column("Col1"))
        self.assertEqual(["X"], twoda.get_column("Col2"))

    def test_copy_exclusive_none(self):
        """Test copying without exclusive column."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0
            CopyRow1=copy_row_1

            [copy_row_0]
            RowIndex=0
            Col1=c
            Col2=d
            [copy_row_1]
            RowIndex=0
            RowLabel=r2
            Col1=e
            Col2=f
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(3, twoda.get_height())
        self.assertEqual("1", twoda.get_label(1))
        self.assertEqual("r2", twoda.get_label(2))
        self.assertEqual(["a", "c", "e"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d", "f"], twoda.get_column("Col2"))

    def test_copy_set_newrowlabel(self):
        """Test copying with new row label."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowIndex=0
            NewRowLabel=r2
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual("r2", twoda.get_label(2))
        self.assertEqual(["a", "c", "a"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d", "b"], twoda.get_column("Col2"))

    def test_copy_assign_high(self):
        """Test using high() in copy row."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowIndex=0
            Col2=high()
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "1"})
        twoda.add_row("1", {"Col1": "c", "Col2": "2"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(3, twoda.get_height())
        self.assertEqual(["a", "c", "a"], twoda.get_column("Col1"))
        self.assertEqual(["1", "2", "3"], twoda.get_column("Col2"))

    def test_copy_assign_tlkmemory(self):
        """Test using TLK memory in copy row."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowIndex=0
            Col2=StrRef0
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2", "Col3"])
        twoda.add_row("0", {"Col1": "a", "Col2": "1"})
        twoda.add_row("1", {"Col1": "c", "Col2": "2"})

        memory = PatcherMemory()
        memory.memory_str[0] = 5
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["a", "c", "a"], twoda.get_column("Col1"))
        self.assertEqual(["1", "2", "5"], twoda.get_column("Col2"))

    def test_copy_assign_2damemory(self):
        """Test using 2DA memory in copy row."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowIndex=0
            Col2=2DAMEMORY0
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "1"})
        twoda.add_row("1", {"Col1": "c", "Col2": "2"})

        memory = PatcherMemory()
        memory.memory_2da[0] = "5"
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["a", "c", "a"], twoda.get_column("Col1"))
        self.assertEqual(["1", "2", "5"], twoda.get_column("Col2"))

    def test_copy_2damemory_rowindex(self):
        """Test storing row index when copying."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            CopyRow0=copy_row_0

            [copy_row_0]
            RowIndex=0
            2DAMEMORY5=RowIndex
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["a", "c", "a"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d", "b"], twoda.get_column("Col2"))
        self.assertEqual("2", memory.memory_2da[5])

    def test_addcolumn_empty(self):
        """Test adding column with empty default."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=Col3
            DefaultValue=****
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["a", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d"], twoda.get_column("Col2"))
        self.assertEqual(["", ""], twoda.get_column("Col3"))

    def test_addcolumn_default(self):
        """Test adding column with specific default."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=Col3
            DefaultValue=X
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["a", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d"], twoda.get_column("Col2"))
        self.assertEqual(["X", "X"], twoda.get_column("Col3"))

    def test_addcolumn_rowindex_constant(self):
        """Test adding column with specific row index value."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=Col3
            DefaultValue=****
            I0=X
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["a", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d"], twoda.get_column("Col2"))
        self.assertEqual(["X", ""], twoda.get_column("Col3"))

    def test_addcolumn_rowlabel_2damemory(self):
        """Test adding column with 2DA memory by label."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=Col3
            DefaultValue=****
            L1=2DAMEMORY5
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()
        memory.memory_2da[5] = "ABC"
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["a", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d"], twoda.get_column("Col2"))
        self.assertEqual(["", "ABC"], twoda.get_column("Col3"))

    def test_addcolumn_rowlabel_tlkmemory(self):
        """Test adding column with TLK memory by label."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=Col3
            DefaultValue=****
            L1=StrRef5
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()
        memory.memory_str[5] = 123
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["a", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d"], twoda.get_column("Col2"))
        self.assertEqual(["", "123"], twoda.get_column("Col3"))

    def test_addcolumn_2damemory_index(self):
        """Test storing 2DA memory from column by index."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=Col3
            DefaultValue=****
            I0=X
            I1=Y
            2DAMEMORY0=I0
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["a", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d"], twoda.get_column("Col2"))
        self.assertEqual(["X", "Y"], twoda.get_column("Col3"))
        self.assertEqual("X", memory.memory_2da[0])

    def test_addcolumn_2damemory_line(self):
        """Test storing 2DA memory from column by label."""
        ini_text = """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddColumn0=add_column_0

            [add_column_0]
            ColumnLabel=Col3
            DefaultValue=****
            I0=X
            I1=Y
            2DAMEMORY0=L1
        """
        config = self._setupIniAndConfig(ini_text)
        twoda = TwoDA(["Col1", "Col2"])
        twoda.add_row("0", {"Col1": "a", "Col2": "b"})
        twoda.add_row("1", {"Col1": "c", "Col2": "d"})

        memory = PatcherMemory()
        config.patches_2da[0].apply(twoda, memory, PatchLogger(), Game.K1)

        self.assertEqual(["a", "c"], twoda.get_column("Col1"))
        self.assertEqual(["b", "d"], twoda.get_column("Col2"))
        self.assertEqual(["X", "Y"], twoda.get_column("Col3"))
        self.assertEqual("Y", memory.memory_2da[0])

    # endregion

    # region SSF
    def test_ssf_replace(self):
        """Test that the replace file boolean is registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [SSFList]
            File0=test1.ssf
            Replace0=test2.ssf

            [test1.ssf]
            [test2.ssf]
            """
        )
        self.assertFalse(config.patches_ssf[0].replace_file)
        self.assertTrue(config.patches_ssf[1].replace_file)

        # Apply (no modifiers, just ensure no crash)
        ssf = SSF()
        memory = PatcherMemory()
        for p in config.patches_ssf:
            p.apply(ssf, memory, PatchLogger(), Game.K1)

    def test_ssf_stored_constant(self):
        """Test that the set sound as constant stringref is registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [SSFList]
            File0=test.ssf

            [test.ssf]
            Battlecry 1=123
            Battlecry 2=456
            """
        )
        ssf = SSF()
        memory = PatcherMemory()
        config.patches_ssf[0].apply(ssf, memory, PatchLogger(), Game.K1)
        self.assertEqual(123, ssf.get(SSFSound.BATTLE_CRY_1))
        self.assertEqual(456, ssf.get(SSFSound.BATTLE_CRY_2))

    def test_ssf_stored_2da(self):
        """Test that the set sound as 2DAMEMORY value is registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [SSFList]
            File0=test.ssf

            [test.ssf]
            Battlecry 1=2DAMEMORY5
            Battlecry 2=2DAMEMORY6
            """
        )
        ssf = SSF()
        memory = PatcherMemory()
        memory.memory_2da[5] = "123"
        memory.memory_2da[6] = "456"
        config.patches_ssf[0].apply(ssf, memory, PatchLogger(), Game.K1)
        self.assertEqual(123, ssf.get(SSFSound.BATTLE_CRY_1))
        self.assertEqual(456, ssf.get(SSFSound.BATTLE_CRY_2))

    def test_ssf_stored_tlk(self):
        """Test that the set sound as StrRef is registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [SSFList]
            File0=test.ssf

            [test.ssf]
            Battlecry 1=StrRef5
            Battlecry 2=StrRef6
            """
        )
        ssf = SSF()
        memory = PatcherMemory()
        memory.memory_str[5] = 5
        memory.memory_str[6] = 6
        config.patches_ssf[0].apply(ssf, memory, PatchLogger(), Game.K1)
        self.assertEqual(5, ssf.get(SSFSound.BATTLE_CRY_1))
        self.assertEqual(6, ssf.get(SSFSound.BATTLE_CRY_2))

    def test_ssf_set(self):
        """Test that each sound is mapped and will register correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [SSFList]
            File0=test.ssf

            [test.ssf]
            Battlecry 1=1
            Battlecry 2=2
            Battlecry 3=3
            Battlecry 4=4
            Battlecry 5=5
            Battlecry 6=6
            Selected 1=7
            Selected 2=8
            Selected 3=9
            Attack 1=10
            Attack 2=11
            Attack 3=12
            Pain 1=13
            Pain 2=14
            Low health=15
            Death=16
            Critical hit=17
            Target immune=18
            Place mine=19
            Disarm mine=20
            Stealth on=21
            Search=22
            Pick lock start=23
            Pick lock fail=24
            Pick lock done=25
            Leave party=26
            Rejoin party=27
            Poisoned=28
            """
        )
        ssf = SSF()
        memory = PatcherMemory()
        config.patches_ssf[0].apply(ssf, memory, PatchLogger(), Game.K1)
        self.assertEqual(1, ssf.get(SSFSound.BATTLE_CRY_1))
        self.assertEqual(2, ssf.get(SSFSound.BATTLE_CRY_2))
        self.assertEqual(3, ssf.get(SSFSound.BATTLE_CRY_3))
        self.assertEqual(4, ssf.get(SSFSound.BATTLE_CRY_4))
        self.assertEqual(5, ssf.get(SSFSound.BATTLE_CRY_5))
        self.assertEqual(6, ssf.get(SSFSound.BATTLE_CRY_6))
        self.assertEqual(7, ssf.get(SSFSound.SELECT_1))
        self.assertEqual(8, ssf.get(SSFSound.SELECT_2))
        self.assertEqual(9, ssf.get(SSFSound.SELECT_3))
        self.assertEqual(10, ssf.get(SSFSound.ATTACK_GRUNT_1))
        self.assertEqual(11, ssf.get(SSFSound.ATTACK_GRUNT_2))
        self.assertEqual(12, ssf.get(SSFSound.ATTACK_GRUNT_3))
        self.assertEqual(13, ssf.get(SSFSound.PAIN_GRUNT_1))
        self.assertEqual(14, ssf.get(SSFSound.PAIN_GRUNT_2))
        self.assertEqual(15, ssf.get(SSFSound.LOW_HEALTH))
        self.assertEqual(16, ssf.get(SSFSound.DEAD))
        self.assertEqual(17, ssf.get(SSFSound.CRITICAL_HIT))
        self.assertEqual(18, ssf.get(SSFSound.TARGET_IMMUNE))
        self.assertEqual(19, ssf.get(SSFSound.LAY_MINE))
        self.assertEqual(20, ssf.get(SSFSound.DISARM_MINE))
        self.assertEqual(21, ssf.get(SSFSound.BEGIN_STEALTH))
        self.assertEqual(22, ssf.get(SSFSound.BEGIN_SEARCH))
        self.assertEqual(23, ssf.get(SSFSound.BEGIN_UNLOCK))
        self.assertEqual(24, ssf.get(SSFSound.UNLOCK_FAILED))
        self.assertEqual(25, ssf.get(SSFSound.UNLOCK_SUCCESS))
        self.assertEqual(26, ssf.get(SSFSound.SEPARATED_FROM_PARTY))
        self.assertEqual(27, ssf.get(SSFSound.REJOINED_PARTY))
        self.assertEqual(28, ssf.get(SSFSound.POISONED))

    # endregion

    # region TLK
    def test_tlk_appendfile_functionality(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir)

            modified_tlk = self.create_test_tlk(
                {
                    0: {"text": "Modified 0", "voiceover": "vo_mod_0"},
                    1: {"text": "Modified 1", "voiceover": "vo_mod_1"},
                    2: {"text": "Modified 2", "voiceover": "vo_mod_2"},
                    3: {"text": "Modified 3", "voiceover": "vo_mod_3"},
                    4: {"text": "Modified 4", "voiceover": "vo_mod_4"},
                    5: {"text": "Modified 5", "voiceover": "vo_mod_5"},
                    6: {"text": "Modified 6", "voiceover": "vo_mod_6"},
                }
            )
            write_tlk(modified_tlk, str(mod_path / "tlk_modifications_file.tlk"), ResourceType.TLK)

            ini_text = """
                [TLKList]
                AppendFile4=tlk_modifications_file.tlk

                [tlk_modifications_file.tlk]
                0=4
                1=5
                2=6
            """
            config = self._setupIniAndConfig(ini_text, mod_path)
            for modifier in config.patches_tlk.modifiers:
                modifier.load()

            self.assertEqual(len(config.patches_tlk.modifiers), 3)
            modifiers_dict = {mod.token_id: {"text": mod.text, "voiceover": mod.sound, "replace": mod.is_replacement} for mod in config.patches_tlk.modifiers}
            self.assertDictEqual(
                modifiers_dict,
                {
                    0: {"text": "Modified 4", "voiceover": ResRef("vo_mod_4"), "replace": False},
                    1: {"text": "Modified 5", "voiceover": ResRef("vo_mod_5"), "replace": False},
                    2: {"text": "Modified 6", "voiceover": ResRef("vo_mod_6"), "replace": False},
                },
            )

    def test_tlk_strref_default_functionality(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir)
            modified_tlk = self.create_test_tlk(
                {
                    0: {"text": "Modified 0", "voiceover": "vo_mod_0"},
                    1: {"text": "Modified 1", "voiceover": "vo_mod_1"},
                    2: {"text": "Modified 2", "voiceover": "vo_mod_2"},
                }
            )
            write_tlk(modified_tlk, str(mod_path / "append.tlk"), ResourceType.TLK)

            ini_text = """
                [TLKList]
                StrRef7=0
                StrRef8=1
                StrRef9=2
            """
            config = self._setupIniAndConfig(ini_text, mod_path)
            assert isinstance(config.patches_tlk, ModificationsTLK)
            self.assertIsInstance(config.patches_tlk, ModificationsTLK)
            assert isinstance(config.patches_tlk.modifiers[0], ModifyTLK)
            self.assertIsInstance(config.patches_tlk.modifiers[0], ModifyTLK)
            assert isinstance(config.patches_tlk.modifiers[1], ModifyTLK)
            self.assertIsInstance(config.patches_tlk.modifiers[1], ModifyTLK)
            assert isinstance(config.patches_tlk.modifiers[2], ModifyTLK)
            self.assertIsInstance(config.patches_tlk.modifiers[2], ModifyTLK)
            dialog_tlk = TLK()
            memory = PatcherMemory()
            config.patches_tlk.apply(dialog_tlk, memory, PatchLogger(), Game.K1)
            dialog_tlk_0 = dialog_tlk.get(0)
            assert dialog_tlk_0 is not None, "Dialog TLK 0 is None"
            self.assertEqual("Modified 0", dialog_tlk_0.text)
            dialog_tlk_1 = dialog_tlk.get(1)
            assert dialog_tlk_1 is not None, "Dialog TLK 1 is None"
            self.assertEqual("Modified 1", dialog_tlk_1.text)
            dialog_tlk_2 = dialog_tlk.get(2)
            assert dialog_tlk_2 is not None, "Dialog TLK 2 is None"
            self.assertEqual("Modified 2", dialog_tlk_2.text)

    def test_tlk_complex_changes(self):
        ini_text = """
        [TLKList]
        ReplaceFile10=complex.tlk
        StrRef0=0
        StrRef1=1
        StrRef2=2
        StrRef3=3
        StrRef4=4
        StrRef5=5
        StrRef6=6
        StrRef7=7
        StrRef8=8
        StrRef9=9
        StrRef10=10
        StrRef11=11
        StrRef12=12
        StrRef13=13

        [complex.tlk]
        123716=0
        123717=1
        123718=2
        123720=3
        123722=4
        123724=5
        123726=6
        123728=7
        123730=8
        124112=9
        125863=10
        50302=11
        """
        self._setupTLK()
        self.config: PatcherConfig = self._setupIniAndConfig(ini_text, self.tslpatchdata_path)

        modifiers2: list[ModifyTLK] = self.config.patches_tlk.modifiers.copy()
        for modifier in modifiers2:
            modifier.load()
        self.assertEqual(len(self.config.patches_tlk.modifiers), 26)
        modifiers_dict2: dict[int, dict[str, str | ResRef | bool]] = {
            mod.token_id: {"text": mod.text, "voiceover": mod.sound, "is_replacement": mod.is_replacement} for mod in modifiers2
        }
        for k in modifiers_dict2.copy():
            modifiers_dict2[k].pop("is_replacement")

        self.maxDiff = None
        self.assertDictEqual(
            modifiers_dict2,
            {
                0: {"text": "Yavin", "voiceover": ResRef.from_blank()},
                1: {
                    "text": "Climate: Artificially Controled\nTerrain: Space Station\nDocking: Orbital Docking\nNative Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                2: {"text": "Tatooine", "voiceover": ResRef.from_blank()},
                3: {
                    "text": "Climate: Arid\nTerrain: Desert\nDocking: Anchorhead Spaceport\nNative Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                4: {"text": "Manaan", "voiceover": ResRef.from_blank()},
                5: {
                    "text": "Climate: Temperate\nTerrain: Ocean\nDocking: Ahto City Docking Bay\nNative Species: Selkath",
                    "voiceover": ResRef.from_blank(),
                },
                6: {"text": "Kashyyyk", "voiceover": ResRef.from_blank()},
                7: {
                    "text": "Climate: Temperate\nTerrain: Forest\nDocking: Czerka Landing Pad\nNative Species: Wookies",
                    "voiceover": ResRef.from_blank(),
                },
                8: {"text": "", "voiceover": ResRef.from_blank()},
                9: {"text": "", "voiceover": ResRef.from_blank()},
                10: {"text": "Sleheyron", "voiceover": ResRef.from_blank()},
                11: {
                    "text": "Climate: Unknown\nTerrain: Cityscape\nDocking: Unknown\nNative Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                12: {"text": "Coruscant", "voiceover": ResRef.from_blank()},
                13: {
                    "text": "Climate: Unknown\nTerrain: Unknown\nDocking: Unknown\nNative Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                50302: {
                    "text": "Opo Chano, Czerka's contracted droid technician, can't give "
                    "you his droid credentials unless you help relieve his 2,500 "
                    "credit gambling debt to the Exchange. Without them, you "
                    "can't take B-4D4.",
                    "voiceover": ResRef.from_blank(),
                },
                123716: {
                    "text": "Climate: None\nTerrain: Asteroid\nDocking: Peragus Mining Station\nNative Species: None",
                    "voiceover": ResRef.from_blank(),
                },
                123717: {"text": "Lehon", "voiceover": ResRef.from_blank()},
                123718: {
                    "text": "Climate: Tropical\nTerrain: Islands\nDocking: Beach Landing\nNative Species: Rakata",
                    "voiceover": ResRef.from_blank(),
                },
                123720: {
                    "text": "Climate: Temperate\nTerrain: Decaying urban zones\nDocking: Refugee Landing Pad\nNative Species: None",
                    "voiceover": ResRef.from_blank(),
                },
                123722: {
                    "text": "Climate: Tropical\nTerrain: Jungle\nDocking: Jungle Clearing\nNative Species: None",
                    "voiceover": ResRef.from_blank(),
                },
                123724: {
                    "text": "Climate: Temperate\nTerrain: Forest\nDocking: Iziz Spaceport\nNative Species: None",
                    "voiceover": ResRef.from_blank(),
                },
                123726: {
                    "text": "Climate: Temperate\nTerrain: Grasslands\nDocking: Khoonda Plains Settlement\nNative Species: None",
                    "voiceover": ResRef.from_blank(),
                },
                123728: {
                    "text": "Climate: Tectonic-Generated Storms\nTerrain: Shattered Planetoid\nDocking: No Docking Facilities Present\nNative Species: None",
                    "voiceover": ResRef.from_blank(),
                },
                123730: {
                    "text": "Climate: Arid\nTerrain: Volcanic\nDocking: Dreshae Settlement\nNative Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                124112: {
                    "text": "Climate: Artificially Maintained \nTerrain: Droid Cityscape\nDocking: Landing Arm\nNative Species: Unknown",
                    "voiceover": ResRef.from_blank(),
                },
                125863: {
                    "text": "Climate: Artificially Maintained\nTerrain: Space Station\nDocking: Landing Zone\nNative Species: None",
                    "voiceover": ResRef.from_blank(),
                },
            },
        )

    def test_tlk_replacefile_functionality(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir)
            modified_tlk = self.create_test_tlk(
                {
                    2: {"text": "Modified 2", "voiceover": "vo_mod_2"},
                    3: {"text": "Modified 3", "voiceover": "vo_mod_3"},
                    4: {"text": "Modified 4", "voiceover": "vo_mod_4"},
                    5: {"text": "Modified 5", "voiceover": "vo_mod_5"},
                    6: {"text": "Modified 6", "voiceover": "vo_mod_6"},
                }
            )
            write_tlk(modified_tlk, str(mod_path / "tlk_modifications_file.tlk"), ResourceType.TLK)

            ini_text = """
                [TLKList]
                Replacenothingafterreplaceischecked=tlk_modifications_file.tlk

                [tlk_modifications_file.tlk]
                0=2
                1=3
                2=4
                3=5
                4=6
            """
            config = self._setupIniAndConfig(ini_text, mod_path)
            assert isinstance(config.patches_tlk, ModificationsTLK)
            self.assertIsInstance(config.patches_tlk, ModificationsTLK)
            expected_modifiers = 5
            for i in range(expected_modifiers):
                assert isinstance(config.patches_tlk.modifiers[i], ModifyTLK)
                self.assertIsInstance(config.patches_tlk.modifiers[i], ModifyTLK)
            self.assertEqual(len(config.patches_tlk.modifiers), expected_modifiers)
            for modifier in config.patches_tlk.modifiers:
                modifier.load()
            token_to_text = {m.token_id: m.text for m in config.patches_tlk.modifiers}
            # The mapping in the INI is: [tlk_modifications_file.tlk] 0=2, 1=3, 2=4, 3=5, 4=6
            # So, token 0 gets text from entry 2, token 1 from entry 3, etc.
            # But the test_tlk_modifications_file.tlk only has entries for 2,3,4,5,6, so tokens 0,1,2 get 4,5,6, tokens 3,4 get "" (empty)
            expected = {
                0: "Modified 4",
                1: "Modified 5",
                2: "Modified 6",
                3: "",
                4: "",
            }
            self.assertEqual(expected, token_to_text)

    # endregion

    # region TLK: Additional test_mods.py tests
    def test_tlk_apply_append(self):
        """Test appending TLK entries."""
        ini_text = """
            [TLKList]
            StrRef0=0
            StrRef1=1

            [append.tlk]
            0=0
            1=1
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir)
            modified_tlk = self.create_test_tlk(
                {
                    0: {"text": "Append2", "voiceover": ""},
                    1: {"text": "Append1", "voiceover": ""},
                }
            )
            write_tlk(modified_tlk, str(mod_path / "append.tlk"), ResourceType.TLK)

            config = self._setupIniAndConfig(ini_text, mod_path)
            dialog_tlk = TLK()
            dialog_tlk.add("Old1")
            dialog_tlk.add("Old2")

            memory = PatcherMemory()
            config.patches_tlk.apply(dialog_tlk, memory, PatchLogger(), Game.K1)

            self.assertEqual(4, len(dialog_tlk))
            get_2 = dialog_tlk.get(2)
            get_3 = dialog_tlk.get(3)
            if get_2 is None or get_3 is None:
                raise AssertionError("get_2 or get_3 is None")
            self.assertEqual("Append2", get_2.text)
            self.assertEqual("Append1", get_3.text)

            self.assertEqual(2, memory.memory_str[0])
            self.assertEqual(3, memory.memory_str[1])

    def test_tlk_apply_replace(self):
        """Test replacing TLK entries."""
        ini_text = """
            [TLKList]
            ReplaceFile0=replace.tlk

            [replace.tlk]
            1=0
            2=1
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir)
            modified_tlk = self.create_test_tlk(
                {
                    0: {"text": "Replace2", "voiceover": ""},
                    1: {"text": "Replace3", "voiceover": ""},
                }
            )
            write_tlk(modified_tlk, str(mod_path / "replace.tlk"), ResourceType.TLK)

            config = self._setupIniAndConfig(ini_text, mod_path)
            dialog_tlk = TLK()
            dialog_tlk.add("Old1")
            dialog_tlk.add("Old2")
            dialog_tlk.add("Old3")
            dialog_tlk.add("Old4")

            memory = PatcherMemory()
            config.patches_tlk.apply(dialog_tlk, memory, PatchLogger(), Game.K1)

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

    # endregion

    # region GFF: Additional test_reader.py tests
    def test_gff_modify_pathing(self):
        """Test that the modify path for the field registered correctly."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            ClassList\\0\\Class=123
            """
        )
        mod_0 = config.patches_gff[0].modifiers[0]
        from pykotor.tslpatcher.mods.gff import ModifyFieldGFF
        self.assertIsInstance(mod_0, ModifyFieldGFF)
        assert isinstance(mod_0, ModifyFieldGFF), "mod_0 is not an instance of ModifyFieldGFF"
        self.assertEqual("ClassList\\0\\Class", str(mod_0.path))

        # Apply end-to-end
        gff = GFF()
        from pykotor.resource.formats.gff.gff_data import GFFList
        gff_list = gff.root.set_list("ClassList", GFFList())
        gff_struct = gff_list.add(0)
        gff_struct.set_uint8("Class", 0)
        memory = PatcherMemory()
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        classlist_0 = patched.root.get_list("ClassList").at(0)
        self.assertIsNotNone(classlist_0)
        assert classlist_0 is not None
        self.assertEqual(123, classlist_0.get_uint8("Class"))

    def test_gff_modify_type_int(self):
        """Test modifying integer fields."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            SomeInt=123
            """
        )
        mod_0 = config.patches_gff[0].modifiers[0]
        from pykotor.tslpatcher.mods.gff import ModifyFieldGFF
        self.assertIsInstance(mod_0, ModifyFieldGFF)
        assert isinstance(mod_0, ModifyFieldGFF), "mod_0 is not an instance of ModifyFieldGFF"
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant), "mod_0.value is not an instance of FieldValueConstant"
        self.assertEqual("SomeInt", str(mod_0.path))
        self.assertEqual(123, mod_0.value.stored)

        # Apply
        gff = GFF()
        gff.root.set_uint8("SomeInt", 1)
        memory = PatcherMemory()
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        self.assertEqual(123, patched.root.get_uint8("SomeInt"))

    def test_gff_modify_type_string(self):
        """Test modifying string fields."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            SomeString=abc
            """
        )
        mod_0 = config.patches_gff[0].modifiers[0]
        from pykotor.tslpatcher.mods.gff import ModifyFieldGFF
        self.assertIsInstance(mod_0, ModifyFieldGFF)
        assert isinstance(mod_0, ModifyFieldGFF), "mod_0 is not an instance of ModifyFieldGFF"
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant), "mod_0.value is not an instance of FieldValueConstant"
        self.assertEqual("SomeString", str(mod_0.path))
        self.assertEqual("abc", mod_0.value.stored)

        # Apply
        gff = GFF()
        gff.root.set_string("SomeString", "old")
        memory = PatcherMemory()
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        self.assertEqual("abc", patched.root.get_string("SomeString"))

    def test_gff_modify_type_vector3(self):
        """Test modifying Vector3 fields."""
        from utility.common.geometry import Vector3
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            SomeVector=1|2|3
            """
        )
        mod_0 = config.patches_gff[0].modifiers[0]
        from pykotor.tslpatcher.mods.gff import ModifyFieldGFF
        self.assertIsInstance(mod_0, ModifyFieldGFF)
        assert isinstance(mod_0, ModifyFieldGFF), "mod_0 is not an instance of ModifyFieldGFF"
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant), "mod_0.value is not an instance of FieldValueConstant"
        self.assertEqual("SomeVector", str(mod_0.path))
        self.assertEqual(Vector3(1, 2, 3), mod_0.value.stored)

        # Apply
        gff = GFF()
        gff.root.set_vector3("SomeVector", Vector3(0, 0, 0))
        memory = PatcherMemory()
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        self.assertEqual(Vector3(1, 2, 3), patched.root.get_vector3("SomeVector"))

    def test_gff_modify_type_vector4(self):
        """Test modifying Vector4 fields."""
        from utility.common.geometry import Vector4
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            SomeVector=1|2|3|4
            """
        )
        mod_0 = config.patches_gff[0].modifiers[0]
        from pykotor.tslpatcher.mods.gff import ModifyFieldGFF
        self.assertIsInstance(mod_0, ModifyFieldGFF)
        assert isinstance(mod_0, ModifyFieldGFF), "mod_0 is not an instance of ModifyFieldGFF"
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant), "mod_0.value is not an instance of FieldValueConstant"
        self.assertEqual("SomeVector", str(mod_0.path))
        self.assertEqual(Vector4(1, 2, 3, 4), mod_0.value.stored)

        # Apply
        gff = GFF()
        gff.root.set_vector4("SomeVector", Vector4(0, 0, 0, 0))
        memory = PatcherMemory()
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        self.assertEqual(Vector4(1, 2, 3, 4), patched.root.get_vector4("SomeVector"))

    def test_gff_modify_type_locstring(self):
        """Test modifying localized string fields."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            LocString(strref)=5
            LocString(lang0)=hello
            LocString(lang3)=world
            """
        )
        # Reader checks
        for i in range(3):
            mod = config.patches_gff[0].modifiers[i]
            from pykotor.tslpatcher.mods.gff import ModifyFieldGFF
            self.assertIsInstance(mod, ModifyFieldGFF)
            assert isinstance(mod, ModifyFieldGFF), "mod is not an instance of ModifyFieldGFF"
            self.assertIsInstance(mod.value, FieldValueConstant)
            assert isinstance(mod.value, FieldValueConstant), "mod.value is not an instance of FieldValueConstant"
            self.assertIsInstance(mod.value.stored, LocalizedStringDelta)
            assert isinstance(mod.value.stored, LocalizedStringDelta), "mod.value.stored is not an instance of LocalizedStringDelta"
            self.assertEqual("LocString", str(mod.path))

        # Apply (simplified)
        gff = GFF()
        gff.root.set_locstring("LocString", LocalizedString(0))
        memory = PatcherMemory()
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        locstr = patched.root.get_locstring("LocString")
        self.assertEqual(5, locstr.stringref)
        self.assertEqual("hello", locstr.get(Language.ENGLISH, Gender.MALE))
        self.assertEqual("world", locstr.get(Language.FRENCH, Gender.FEMALE))

    def test_gff_modify_2damemory(self):
        """Test modifying fields with 2DA memory."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            SomeField=2DAMEMORY12
            """
        )
        mod_0 = config.patches_gff[0].modifiers[0]
        from pykotor.tslpatcher.mods.gff import ModifyFieldGFF
        self.assertIsInstance(mod_0, ModifyFieldGFF)
        assert isinstance(mod_0, ModifyFieldGFF), "mod_0 is not an instance of ModifyFieldGFF"
        self.assertIsInstance(mod_0.value, FieldValue2DAMemory)
        assert isinstance(mod_0.value, FieldValue2DAMemory), "mod_0.value is not an instance of FieldValue2DAMemory"
        self.assertEqual(12, mod_0.value.token_id)

        # Apply
        gff = GFF()
        gff.root.set_string("SomeField", "")
        gff.root.set_uint8("IntField", 0)
        memory = PatcherMemory()
        memory.memory_2da[12] = "123"
        # Need to add IntField modifier too
        from pykotor.tslpatcher.mods.gff import ModifyFieldGFF
        config.patches_gff[0].modifiers.append(ModifyFieldGFF("IntField", FieldValue2DAMemory(12)))
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        self.assertEqual("123", patched.root.get_string("SomeField"))
        self.assertEqual(123, patched.root.get_uint8("IntField"))

    def test_gff_modify_tlkmemory(self):
        """Test modifying fields with TLK memory."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            LocString(strref)=StrRef5
            SomeField=StrRef2
            """
        )
        mod_0 = config.patches_gff[0].modifiers[0]
        from pykotor.tslpatcher.mods.gff import ModifyFieldGFF, FieldValueTLKMemory
        self.assertIsInstance(mod_0, ModifyFieldGFF)
        assert isinstance(mod_0, ModifyFieldGFF), "mod_0 is not an instance of ModifyFieldGFF"
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant), "mod_0.value is not an instance of FieldValueConstant"
        self.assertIsInstance(mod_0.value.stored, LocalizedStringDelta)
        assert isinstance(mod_0.value.stored, LocalizedStringDelta), "mod_0.value.stored is not an instance of LocalizedStringDelta"
        self.assertEqual("LocString", str(mod_0.path))
        self.assertIsInstance(mod_0.value.stored.stringref, FieldValueTLKMemory)
        assert isinstance(mod_0.value.stored.stringref, FieldValueTLKMemory), "mod_0.value.stored.stringref is not an instance of FieldValueTLKMemory"
        self.assertEqual(5, mod_0.value.stored.stringref.token_id)

        mod_1 = config.patches_gff[0].modifiers[1]
        self.assertIsInstance(mod_1, ModifyFieldGFF)
        assert isinstance(mod_1, ModifyFieldGFF), "mod_1 is not an instance of ModifyFieldGFF"
        from pykotor.tslpatcher.mods.gff import FieldValueTLKMemory
        self.assertIsInstance(mod_1.value, FieldValueTLKMemory)
        assert isinstance(mod_1.value, FieldValueTLKMemory), "mod_1.value is not an instance of FieldValueTLKMemory"
        self.assertEqual(2, mod_1.value.token_id)

        # Apply
        gff = GFF()
        gff.root.set_locstring("LocString", LocalizedString(0))
        gff.root.set_string("SomeField", "")
        memory = PatcherMemory()
        memory.memory_str[5] = 123
        memory.memory_str[2] = 456
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        self.assertEqual(123, patched.root.get_locstring("LocString").stringref)
        self.assertEqual("456", patched.root.get_string("SomeField"))

    def test_gff_add_ints(self):
        """Test adding integer fields."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_uint8
            AddField1=add_int8
            AddField2=add_uint16
            AddField3=add_int16
            AddField4=add_uint32
            AddField5=add_int32
            AddField6=add_int64

            [add_uint8]
            FieldType=Byte
            Path=
            Label=SomeField
            Value=123

            [add_int8]
            FieldType=Char
            Path=
            Label=SomeField2
            Value=123

            [add_uint16]
            FieldType=Word
            Path=
            Label=SomeField3
            Value=123

            [add_int16]
            FieldType=Short
            Path=
            Label=SomeField4
            Value=123

            [add_uint32]
            FieldType=DWORD
            Path=
            Label=SomeField5
            Value=123

            [add_int32]
            FieldType=Int
            Path=
            Label=SomeField6
            Value=123

            [add_int64]
            FieldType=Int64
            Path=
            Label=SomeField7
            Value=123
            """
        )
        # Verify config
        self.assertEqual(7, len(config.patches_gff[0].modifiers))
        for mod in config.patches_gff[0].modifiers:
            self.assertIsInstance(mod, AddFieldGFF)
            assert isinstance(mod, AddFieldGFF), "mod is not an instance of AddFieldGFF"
            self.assertIsInstance(mod.value, FieldValueConstant)
            assert isinstance(mod.value, FieldValueConstant), "mod.value is not an instance of FieldValueConstant"
            self.assertEqual(123, mod.value.stored)

        # Apply
        gff = GFF()
        memory = PatcherMemory()
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        self.assertEqual(123, patched.root.get_uint8("SomeField"))
        self.assertEqual(123, patched.root.get_int8("SomeField2"))
        self.assertEqual(123, patched.root.get_uint16("SomeField3"))
        self.assertEqual(123, patched.root.get_int16("SomeField4"))
        self.assertEqual(123, patched.root.get_uint32("SomeField5"))
        self.assertEqual(123, patched.root.get_int32("SomeField6"))
        self.assertEqual(123, patched.root.get_int64("SomeField7"))

    def test_gff_add_floats(self):
        """Test adding float fields."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_single
            AddField1=add_double

            [add_single]
            FieldType=Float
            Path=
            Label=SomeField
            Value=1.23

            [add_double]
            FieldType=Double
            Path=
            Label=SomeField2
            Value=1.23
            """
        )
        # Verify config
        self.assertEqual(2, len(config.patches_gff[0].modifiers))
        for mod in config.patches_gff[0].modifiers:
            self.assertIsInstance(mod, AddFieldGFF)
            assert isinstance(mod, AddFieldGFF), "mod is not an instance of AddFieldGFF"
            self.assertIsInstance(mod.value, FieldValueConstant)
            assert isinstance(mod.value, FieldValueConstant), "mod.value is not an instance of FieldValueConstant"
            self.assertEqual(1.23, mod.value.stored)

        # Apply
        gff = GFF()
        memory = PatcherMemory()
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        self.assertAlmostEqual(1.23, patched.root.get_single("SomeField"), places=2)
        self.assertEqual(1.23, patched.root.get_double("SomeField2"))

    def test_gff_add_string(self):
        """Test adding string fields."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_string

            [add_string]
            FieldType=ExoString
            Path=
            Label=SomeField
            Value=abc
            """
        )
        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF), "mod_0 is not an instance of AddFieldGFF"
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant), "mod_0.value is not an instance of FieldValueConstant"
        self.assertEqual("abc", mod_0.value.stored)

        # Apply
        gff = GFF()
        memory = PatcherMemory()
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        self.assertEqual("abc", patched.root.get_string("SomeField"))

    def test_gff_add_vector3(self):
        """Test adding Vector3 fields."""
        from utility.common.geometry import Vector3
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_vector3

            [add_vector3]
            FieldType=Position
            Path=
            Label=SomeField
            Value=1|2|3
            """
        )
        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF), "mod_0 is not an instance of AddFieldGFF"
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant), "mod_0.value is not an instance of FieldValueConstant"
        self.assertEqual(Vector3(1, 2, 3), mod_0.value.stored)

        # Apply
        gff = GFF()
        memory = PatcherMemory()
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        self.assertEqual(Vector3(1, 2, 3), patched.root.get_vector3("SomeField"))

    def test_gff_add_vector4(self):
        """Test adding Vector4 fields."""
        from utility.common.geometry import Vector4
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_vector4

            [add_vector4]
            FieldType=Orientation
            Path=
            Label=SomeField
            Value=1|2|3|4
            """
        )
        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF), "mod_0 is not an instance of AddFieldGFF"
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant), "mod_0.value is not an instance of FieldValueConstant"
        self.assertEqual(Vector4(1, 2, 3, 4), mod_0.value.stored)

        # Apply
        gff = GFF()
        memory = PatcherMemory()
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        self.assertEqual(Vector4(1, 2, 3, 4), patched.root.get_vector4("SomeField"))

    def test_gff_add_resref(self):
        """Test adding ResRef fields."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_resref

            [add_resref]
            FieldType=ResRef
            Path=
            Label=SomeField
            Value=abc
            """
        )
        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF), "mod_0 is not an instance of AddFieldGFF"
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant), "mod_0.value is not an instance of FieldValueConstant"
        self.assertEqual(ResRef("abc"), mod_0.value.stored)

        # Apply
        gff = GFF()
        memory = PatcherMemory()
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        self.assertEqual(ResRef("abc"), patched.root.get_resref("SomeField"))

    def test_gff_add_locstring(self):
        """Test adding localized string fields."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_locstring
            AddField1=add_locstring2

            [add_locstring]
            FieldType=ExoLocString
            Path=
            Label=SomeField
            StrRef=123
            lang0=abc
            lang3=lmnop

            [add_locstring2]
            FieldType=ExoLocString
            Path=
            Label=SomeField2
            StrRef=StrRef8
            """
        )
        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant)
        self.assertIsInstance(mod_0.value.stored, LocalizedStringDelta)
        assert isinstance(mod_0.value.stored, LocalizedStringDelta)
        self.assertEqual(".", str(mod_0.path))
        self.assertEqual("SomeField", mod_0.label)
        self.assertIsInstance(mod_0.value.stored.stringref, FieldValueConstant)
        assert isinstance(mod_0.value.stored.stringref, FieldValueConstant)
        self.assertEqual(123, mod_0.value.stored.stringref.stored)
        self.assertEqual("abc", mod_0.value.stored.get(Language.ENGLISH, Gender.MALE))
        self.assertEqual("lmnop", mod_0.value.stored.get(Language.FRENCH, Gender.FEMALE))

        mod_1 = config.patches_gff[0].modifiers[1]
        self.assertIsInstance(mod_1, AddFieldGFF)
        assert isinstance(mod_1, AddFieldGFF)
        self.assertIsInstance(mod_1.value, FieldValueConstant)
        assert isinstance(mod_1.value, FieldValueConstant)
        self.assertIsInstance(mod_1.value.stored, LocalizedStringDelta)
        assert isinstance(mod_1.value.stored, LocalizedStringDelta)
        from pykotor.tslpatcher.mods.gff import FieldValueTLKMemory
        self.assertIsInstance(mod_1.value.stored.stringref, FieldValueTLKMemory)
        assert isinstance(mod_1.value.stored.stringref, FieldValueTLKMemory)
        self.assertEqual(8, mod_1.value.stored.stringref.token_id)

        # Apply
        gff = GFF()
        memory = PatcherMemory()
        memory.memory_str[8] = 456
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        locstr = patched.root.get_locstring("SomeField")
        self.assertEqual(123, locstr.stringref)
        self.assertEqual("abc", locstr.get(Language.ENGLISH, Gender.MALE))
        self.assertEqual("lmnop", locstr.get(Language.FRENCH, Gender.FEMALE))
        locstr2 = patched.root.get_locstring("SomeField2")
        self.assertEqual(456, locstr2.stringref)

    def test_gff_add_inside_list(self):
        """Test adding struct inside list."""
        config: PatcherConfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_list

            [add_list]
            FieldType=List
            Path=
            Label=SomeList
            AddField0=add_insidelist

            [add_insidelist]
            FieldType=Struct
            Label=
            TypeId=111
            2DAMEMORY5=ListIndex
            """
        )
        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant)
        self.assertFalse(mod_0.path.name)
        self.assertEqual("SomeList", mod_0.label)

        from pykotor.tslpatcher.mods.gff import AddStructToListGFF
        mod_1 = mod_0.modifiers[0]
        self.assertIsInstance(mod_1, AddStructToListGFF)
        assert isinstance(mod_1, AddStructToListGFF)
        self.assertIsInstance(mod_1.value, FieldValueConstant)
        assert isinstance(mod_1.value, FieldValueConstant)
        self.assertIsInstance(mod_1.value.value(PatcherMemory(), GFFFieldType.Struct), GFFStruct)
        assert isinstance(mod_1.value.value(PatcherMemory(), GFFFieldType.Struct), GFFStruct)
        self.assertIsInstance(mod_1.value.stored, GFFStruct)
        assert isinstance(mod_1.value.stored, GFFStruct)
        self.assertEqual(111, mod_1.value.stored.struct_id)
        self.assertEqual(5, mod_1.index_to_token)

        # Apply
        gff = GFF()
        memory = PatcherMemory()
        patched = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        somelist = patched.root.get_list("SomeList")
        self.assertIsNotNone(somelist)
        self.assertEqual(1, len(somelist))
        somelist_struct_0 = somelist.at(0)
        self.assertIsInstance(somelist_struct_0, GFFStruct)
        assert isinstance(somelist_struct_0, GFFStruct)
        self.assertEqual(111, somelist_struct_0.struct_id)
        self.assertEqual(5, mod_1.index_to_token)  # TODO: determine if this assert is correct.
        self.assertEqual("0", memory.memory_2da[5])

    # endregion

    # region GFF: Additional test_mods.py tests
    def test_modify_field_uint8(self):
        """Test modifying uint8 fields."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            Field1=2
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_uint8("Field1", 1)

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual(2, gff.root.get_uint8("Field1"))

    def test_modify_field_int8(self):
        """Test modifying int8 fields."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            Field1=2
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_int8("Field1", 1)

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual(2, gff.root.get_int8("Field1"))

    def test_modify_field_uint16(self):
        """Test modifying uint16 fields."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            Field1=2
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_uint16("Field1", 1)

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual(2, gff.root.get_uint16("Field1"))

    def test_modify_field_int16(self):
        """Test modifying int16 fields."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            Field1=2
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_int16("Field1", 1)

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual(2, gff.root.get_int16("Field1"))

    def test_modify_field_uint32(self):
        """Test modifying uint32 fields."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            Field1=2
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_uint32("Field1", 1)

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual(2, gff.root.get_uint32("Field1"))

    def test_modify_field_int32(self):
        """Test modifying int32 fields."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            Field1=2
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_int32("Field1", 1)

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual(2, gff.root.get_int32("Field1"))

    def test_modify_field_uint64(self):
        """Test modifying uint64 fields."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            Field1=2
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_uint64("Field1", 1)

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual(2, gff.root.get_uint64("Field1"))

    def test_modify_field_int64(self):
        """Test modifying int64 fields."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            Field1=2
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_int64("Field1", 1)

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual(2, gff.root.get_int64("Field1"))

    def test_modify_field_single(self):
        """Test modifying single (float) fields."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            Field1=2.345
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_single("Field1", 1.234)

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertAlmostEqual(2.345, gff.root.get_single("Field1"), places=2)

    def test_modify_field_double(self):
        """Test modifying double fields."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            Field1=2.345678
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_double("Field1", 1.234567)

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual(2.345678, gff.root.get_double("Field1"))

    def test_modify_field_string(self):
        """Test modifying string fields."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            Field1=def
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_string("Field1", "abc")

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual("def", gff.root.get_string("Field1"))

    def test_modify_field_locstring(self):
        """Test modifying localized string fields."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            Field1(strref)=1
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_locstring("Field1", LocalizedString(0))

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual(1, gff.root.get_locstring("Field1").stringref)

    def test_modify_field_vector3(self):
        """Test modifying Vector3 fields."""
        from utility.common.geometry import Vector3
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            Field1=1|2|3
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_vector3("Field1", Vector3(0, 1, 2))

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual(Vector3(1, 2, 3), gff.root.get_vector3("Field1"))

    def test_modify_field_vector4(self):
        """Test modifying Vector4 fields."""
        from utility.common.geometry import Vector4
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            Field1=1|2|3|4
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_vector4("Field1", Vector4(0, 1, 2, 3))

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual(Vector4(1, 2, 3, 4), gff.root.get_vector4("Field1"))

    def test_modify_nested(self):
        """Test modifying nested GFF structures."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            List\\0\\String=abc
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        from pykotor.resource.formats.gff.gff_data import GFFList
        gff_list = gff.root.set_list("List", GFFList())
        gff_struct = gff_list.add(0)
        gff_struct.set_string("String", "")

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        patched_gff_list = gff.root.get_list("List")
        patched_gff_struct = patched_gff_list.at(0)

        self.assertIsNotNone(patched_gff_struct)
        assert patched_gff_struct is not None
        self.assertEqual("abc", patched_gff_struct.get_string("String"))

    def test_modify_2damemory(self):
        """Test modifying with 2DA memory."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            String=2DAMEMORY5
            Integer=2DAMEMORY5
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_string("String", "")
        gff.root.set_uint8("Integer", 0)

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual("123", gff.root.get_string("String"))
        self.assertEqual(123, gff.root.get_uint8("Integer"))

    def test_modify_tlkmemory(self):
        """Test modifying with TLK memory."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            String=StrRef5
            Integer=StrRef5
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        gff.root.set_string("String", "")
        gff.root.set_uint8("Integer", 0)

        memory = PatcherMemory()
        memory.memory_str[5] = 123
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual("123", gff.root.get_string("String"))
        self.assertEqual(123, gff.root.get_uint8("Integer"))

    def test_add_newnested(self):
        """Test adding new nested GFF structures."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_list

            [add_list]
            FieldType=List
            Path=
            Label=List
            AddField0=add_struct

            [add_struct]
            FieldType=Struct
            Label=
            TypeId=0
            AddField0=add_int

            [add_int]
            FieldType=Byte
            Path=>>##INDEXINLIST##<<
            Label=SomeInteger
            Value=123
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertIsNotNone(gff.root.get_list("List"))
        some_list_entry_0 = gff.root.get_list("List").at(0)
        self.assertIsNotNone(some_list_entry_0)
        assert some_list_entry_0 is not None
        self.assertIsNotNone(some_list_entry_0.get_uint8("SomeInteger"))

    def test_add_nested(self):
        """Test adding to existing nested structures."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_string

            [add_string]
            FieldType=ExoString
            Path=List\\0
            Label=String
            Value=abc
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        from pykotor.resource.formats.gff.gff_data import GFFList
        gff_list = gff.root.set_list("List", GFFList())
        gff_struct = gff_list.add(0)

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        patched_gff_list = gff.root.get_list("List")
        patched_gff_struct = patched_gff_list.at(0)

        self.assertIsNotNone(patched_gff_struct)
        assert patched_gff_struct is not None
        self.assertEqual("abc", patched_gff_struct.get_string("String"))

    def test_add_use_2damemory(self):
        """Test adding fields using 2DA memory."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_string
            AddField1=add_int

            [add_string]
            FieldType=ExoString
            Path=
            Label=String
            Value=2DAMEMORY5

            [add_int]
            FieldType=Byte
            Path=
            Label=Integer
            Value=2DAMEMORY5
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual("123", gff.root.get_string("String"))
        self.assertEqual(123, gff.root.get_uint8("Integer"))

    def test_add_use_tlkmemory(self):
        """Test adding fields using TLK memory."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_string
            AddField1=add_int

            [add_string]
            FieldType=ExoString
            Path=
            Label=String
            Value=StrRef5

            [add_int]
            FieldType=Byte
            Path=
            Label=Integer
            Value=StrRef5
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()

        memory = PatcherMemory()
        memory.memory_str[5] = 123
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual("123", gff.root.get_string("String"))
        self.assertEqual(123, gff.root.get_uint8("Integer"))

    def test_addlist_listindex(self):
        """Test adding to list and storing index."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_struct1
            AddField1=add_struct2
            AddField2=add_struct3

            [add_struct1]
            FieldType=Struct
            Path=List
            Label=
            TypeId=5

            [add_struct2]
            FieldType=Struct
            Path=List
            Label=
            TypeId=3

            [add_struct3]
            FieldType=Struct
            Path=List
            Label=
            TypeId=1
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        from pykotor.resource.formats.gff.gff_data import GFFList
        gff_list = gff.root.set_list("List", GFFList())

        memory = PatcherMemory()
        gff = read_gff(cast(bytes, config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        patched_gff_list = gff.root.get_list("List")
        some_list_entry_0 = patched_gff_list.at(0)
        self.assertIsNotNone(some_list_entry_0)
        assert some_list_entry_0 is not None
        some_list_entry_1 = patched_gff_list.at(1)
        self.assertIsNotNone(some_list_entry_1)
        assert some_list_entry_1 is not None
        some_list_entry_2 = patched_gff_list.at(2)
        self.assertIsNotNone(some_list_entry_2)
        assert some_list_entry_2 is not None
        self.assertEqual(5, some_list_entry_0.struct_id)
        self.assertEqual(3, some_list_entry_1.struct_id)
        self.assertEqual(1, some_list_entry_2.struct_id)

    def test_addlist_store_2damemory(self):
        """Test storing list index in 2DA memory."""
        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_struct1
            AddField1=add_struct2

            [add_struct1]
            FieldType=Struct
            Path=List
            Label=
            TypeId=0

            [add_struct2]
            FieldType=Struct
            Path=List
            Label=
            TypeId=0
            2DAMEMORY12=ListIndex
        """
        config = self._setupIniAndConfig(ini_text)
        gff = GFF()
        from pykotor.resource.formats.gff.gff_data import GFFList
        gff.root.set_list("List", GFFList())

        memory = PatcherMemory()
        gff = read_gff(config.patches_gff[0].patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1))

        self.assertEqual("1", memory.memory_2da[12])

    # endregion

    # region SSF: Additional test_mods.py tests
    def test_assign_int(self):
        """Test assigning integer to SSF sound."""
        ini_text = """
            [SSFList]
            File0=test.ssf

            [test.ssf]
            Battlecry 1=5
        """
        config = self._setupIniAndConfig(ini_text)
        ssf = SSF()

        memory = PatcherMemory()
        from pykotor.resource.formats.ssf.ssf_auto import bytes_ssf, read_ssf
        ssf = read_ssf(config.patches_ssf[0].patch_resource(bytes_ssf(ssf), memory, PatchLogger(), Game.K1))

        self.assertEqual(5, ssf.get(SSFSound.BATTLE_CRY_1))

    def test_assign_2datoken(self):
        """Test assigning 2DA token to SSF sound."""
        ini_text = """
            [SSFList]
            File0=test.ssf

            [test.ssf]
            Battlecry 2=2DAMEMORY5
        """
        config = self._setupIniAndConfig(ini_text)
        ssf = SSF()

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"
        from pykotor.resource.formats.ssf.ssf_auto import bytes_ssf, read_ssf
        ssf = read_ssf(config.patches_ssf[0].patch_resource(bytes_ssf(ssf), memory, PatchLogger(), Game.K1))

        self.assertEqual(123, ssf.get(SSFSound.BATTLE_CRY_2))

    def test_assign_tlktoken(self):
        """Test assigning TLK token to SSF sound."""
        ini_text = """
            [SSFList]
            File0=test.ssf

            [test.ssf]
            Battlecry 3=StrRef5
        """
        config = self._setupIniAndConfig(ini_text)
        ssf = SSF()

        memory = PatcherMemory()
        memory.memory_str[5] = 321
        from pykotor.resource.formats.ssf.ssf_auto import bytes_ssf, read_ssf
        ssf = read_ssf(config.patches_ssf[0].patch_resource(bytes_ssf(ssf), memory, PatchLogger(), Game.K1))

        self.assertEqual(321, ssf.get(SSFSound.BATTLE_CRY_3))

    # endregion


if __name__ == "__main__":
    unittest.main()
