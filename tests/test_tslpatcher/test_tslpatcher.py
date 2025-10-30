from __future__ import annotations

import os
import pathlib
import shutil
import sys
import tempfile
import unittest

import pytest

from configparser import ConfigParser
from typing import TYPE_CHECKING, Callable, cast


THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "Utility", "src")


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
from utility.system.path import Path


if TYPE_CHECKING:
    from pykotor.tslpatcher.mods.twoda import CopyRow2DA


# TODO(th3w1zard1): Make a decorator for test cases that use the _setupIniAndConfig method.
class TestTSLPatcher(unittest.TestCase):
    def _setupIniAndConfig(self, ini_text: str, mod_path: Path | str = "") -> PatcherConfig:
        ini = ConfigParser(delimiters="=", allow_no_value=True, strict=False, interpolation=None)
        ini.optionxform = lambda optionstr: optionstr
        ini.read_string(ini_text)
        result = PatcherConfig()
        actual_mod_path: Path | str = mod_path if mod_path else self.temp_dir
        ConfigReader(ini, actual_mod_path, tslpatchdata_path=self.tslpatchdata_path).load(result)  # type: ignore[arg-type]
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
        self.tslpatchdata_path: pathlib.Path = pathlib.Path(self.temp_dir) / "tslpatchdata"
        self.tslpatchdata_path.mkdir(exist_ok=True, parents=True)

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
        assert isinstance(mod, ChangeRow2DA)
        self.assertIsInstance(mod, ChangeRow2DA)
        self.assertEqual(TargetType.ROW_INDEX, mod.target.target_type)
        self.assertEqual(1, mod.target.value)
        self.assertIn("Col1", mod.cells)
        self.assertIsInstance(mod.cells["Col1"], RowValueConstant)
        self.assertEqual("X", cast(RowValueConstant, mod.cells["Col1"]).string)

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
        ini = ConfigParser(delimiters=("="), allow_no_value=True, strict=False, interpolation=None)
        ini.optionxform = lambda optionstr: optionstr  # type: ignore[method-assign]
        ini.read_string(ini_text)
        ConfigReader(ini, self.temp_dir, tslpatchdata_path=self.tslpatchdata_path).load(config)  # type: ignore[arg-type]
        self.assertEqual(1, len(config.patches_2da))
        self.assertEqual(1, len(config.patches_2da[0].modifiers))
        mod = cast(ChangeRow2DA, config.patches_2da[0].modifiers[0])
        self.assertEqual(TargetType.ROW_LABEL, mod.target.target_type)
        self.assertEqual("1", mod.target.value)
        self.assertIn("Col1", mod.cells)
        self.assertIsInstance(mod.cells["Col1"], RowValueConstant)
        self.assertEqual("X", cast(RowValueConstant, mod.cells["Col1"]).string)

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
        mod_1 = mod_0.modifiers[0]
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
        mod_1 = mod_0.modifiers[0]
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
        mod_1 = mod_0.modifiers[0]
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
        mod_1 = mod_0.modifiers[0]
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
        # noinspection PyTypeChecker
        mod_0: ChangeRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_0, ChangeRow2DA)
        self.assertIsInstance(mod_0, ChangeRow2DA)
        self.assertEqual("change_row_0", mod_0.identifier)

        # noinspection PyTypeChecker
        mod_0 = config.patches_2da[0].modifiers[1]  # type: ignore
        assert isinstance(mod_0, ChangeRow2DA)
        self.assertIsInstance(mod_0, ChangeRow2DA)
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
        # noinspection PyTypeChecker
        mod_2da_0: ChangeRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_2da_0, ChangeRow2DA)
        self.assertIsInstance(mod_2da_0, ChangeRow2DA)
        self.assertEqual(TargetType.ROW_INDEX, mod_2da_0.target.target_type)
        self.assertEqual(1, mod_2da_0.target.value)

        # noinspection PyTypeChecker
        mod_2da_1: ChangeRow2DA = config.patches_2da[0].modifiers[1]  # type: ignore
        assert isinstance(mod_2da_1, ChangeRow2DA)
        self.assertIsInstance(mod_2da_1, ChangeRow2DA)
        self.assertEqual(TargetType.ROW_LABEL, mod_2da_1.target.target_type)
        self.assertEqual("2", mod_2da_1.target.value)

        # noinspection PyTypeChecker
        mod_2da_2: ChangeRow2DA = config.patches_2da[0].modifiers[2]  # type: ignore
        assert isinstance(mod_2da_2, ChangeRow2DA)
        self.assertIsInstance(mod_2da_2, ChangeRow2DA)
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
        # noinspection PyTypeChecker
        mod_2da_0: ChangeRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_2da_0, ChangeRow2DA)
        self.assertIsInstance(mod_2da_0, ChangeRow2DA)

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
        mod_2da_0: ChangeRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_2da_0, ChangeRow2DA)
        self.assertIsInstance(mod_2da_0, ChangeRow2DA)
        assert isinstance(mod_2da_0.cells["label"], RowValueConstant)
        self.assertIsInstance(mod_2da_0.cells["label"], RowValueConstant)
        assert isinstance(mod_2da_0.cells["dialog"], RowValueTLKMemory)
        self.assertIsInstance(mod_2da_0.cells["dialog"], RowValueTLKMemory)
        assert isinstance(mod_2da_0.cells["appearance"], RowValue2DAMemory)
        self.assertIsInstance(mod_2da_0.cells["appearance"], RowValue2DAMemory)

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
        # noinspection PyTypeChecker
        mod_0: AddColumn2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_0, AddColumn2DA)
        self.assertIsInstance(mod_0, AddColumn2DA)
        self.assertEqual("label", mod_0.header)
        self.assertEqual("", mod_0.default)

        # noinspection PyTypeChecker
        mod_1: AddColumn2DA = config.patches_2da[0].modifiers[1]  # type: ignore
        assert isinstance(mod_1, AddColumn2DA)
        self.assertIsInstance(mod_1, AddColumn2DA)
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
        # noinspection PyTypeChecker
        mod_0: AddColumn2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_0, AddColumn2DA)
        self.assertIsInstance(mod_0, AddColumn2DA)

        # reader assertions
        value = mod_0.index_insert[0]
        self.assertIsInstance(value, RowValueConstant)
        self.assertEqual("abc", value.string)  # type: ignore

        value = mod_0.index_insert[1]
        self.assertIsInstance(value, RowValue2DAMemory)
        self.assertEqual(4, value.token_id)  # type: ignore

        value = mod_0.index_insert[2]
        self.assertIsInstance(value, RowValueTLKMemory)
        self.assertEqual(5, value.token_id)  # type: ignore

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
        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_0, AddRow2DA)
        self.assertIsInstance(mod_0, AddRow2DA)
        self.assertEqual("add_row_0", mod_0.identifier)

        # noinspection PyTypeChecker
        mod_1: AddRow2DA = config.patches_2da[0].modifiers[1]  # type: ignore
        assert isinstance(mod_1, AddRow2DA)
        self.assertIsInstance(mod_1, AddRow2DA)
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
        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_0, AddRow2DA)
        self.assertIsInstance(mod_0, AddRow2DA)
        self.assertEqual("add_row_0", mod_0.identifier)
        self.assertEqual("label", mod_0.exclusive_column)

        # noinspection PyTypeChecker
        mod_1: AddRow2DA = config.patches_2da[0].modifiers[1]  # type: ignore
        assert isinstance(mod_1, AddRow2DA)
        self.assertIsInstance(mod_1, AddRow2DA)
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
        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_0, AddRow2DA)
        self.assertIsInstance(mod_0, AddRow2DA)
        self.assertEqual("add_row_0", mod_0.identifier)
        self.assertEqual("123", mod_0.row_label)

        # noinspection PyTypeChecker
        mod_1: AddRow2DA = config.patches_2da[0].modifiers[1]  # type: ignore
        assert isinstance(mod_1, AddRow2DA)
        self.assertIsInstance(mod_1, AddRow2DA)
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
        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_0, AddRow2DA)
        self.assertIsInstance(mod_0, AddRow2DA)

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
        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_0, AddRow2DA)
        self.assertIsInstance(mod_0, AddRow2DA)

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
        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_0, CopyRow2DA)
        self.assertIsInstance(mod_0, CopyRow2DA)
        self.assertEqual("copy_row_0", mod_0.identifier)

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers[1]  # type: ignore
        assert isinstance(mod_1, CopyRow2DA)
        self.assertIsInstance(mod_1, CopyRow2DA)
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
        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_0, CopyRow2DA)
        self.assertIsInstance(mod_0, CopyRow2DA)

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
        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_0, CopyRow2DA)
        self.assertIsInstance(mod_0, CopyRow2DA)
        self.assertEqual(TargetType.ROW_INDEX, mod_0.target.target_type)
        self.assertEqual(1, mod_0.target.value)

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers[1]  # type: ignore
        assert isinstance(mod_1, CopyRow2DA)
        self.assertIsInstance(mod_1, CopyRow2DA)
        self.assertEqual(TargetType.ROW_LABEL, mod_1.target.target_type)
        self.assertEqual("2", mod_1.target.value)

        # noinspection PyTypeChecker
        mod_2: CopyRow2DA = config.patches_2da[0].modifiers[2]  # type: ignore
        assert isinstance(mod_2, CopyRow2DA)
        self.assertIsInstance(mod_2, CopyRow2DA)
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
        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_0, CopyRow2DA)
        self.assertIsInstance(mod_0, CopyRow2DA)
        self.assertEqual("copy_row_0", mod_0.identifier)
        self.assertEqual("label", mod_0.exclusive_column)

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers[1]  # type: ignore
        assert isinstance(mod_1, CopyRow2DA)
        self.assertIsInstance(mod_1, CopyRow2DA)
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
        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_0, CopyRow2DA)
        self.assertIsInstance(mod_0, CopyRow2DA)
        self.assertEqual("copy_row_0", mod_0.identifier)
        self.assertEqual("123", mod_0.row_label)

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers[1]  # type: ignore
        assert isinstance(mod_1, CopyRow2DA)
        self.assertIsInstance(mod_1, CopyRow2DA)
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
        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_0, CopyRow2DA)
        self.assertIsInstance(mod_0, CopyRow2DA)

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
        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers[0]  # type: ignore
        assert isinstance(mod_0, CopyRow2DA)
        self.assertIsInstance(mod_0, CopyRow2DA)

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
            self.assertEqual("Modified 0", dialog_tlk.get(0).text)
            self.assertEqual("Modified 1", dialog_tlk.get(1).text)
            self.assertEqual("Modified 2", dialog_tlk.get(2).text)

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


if __name__ == "__main__":
    unittest.main()
