from configparser import ConfigParser
from unittest import TestCase

from pykotor.resource.formats.ssf import SSFSound
from pykotor.resource.formats.tlk import TLK
from pykotor.tslpatcher.config import PatcherConfig
from pykotor.tslpatcher.memory import NoTokenUsage, TokenUsage2DA, TokenUsageTLK
from pykotor.tslpatcher.mods.twoda import ChangeRow2DA, TargetType, RowValueRowIndex, RowValueRowLabel, RowValueRowCell, \
    RowValueConstant, RowValue2DAMemory, RowValueTLKMemory, AddRow2DA, CopyRow2DA, AddColumn2DA
from pykotor.tslpatcher.reader import ConfigReader


class TestConfigReader(TestCase):
    def test(self):
        ...

    def test_tlk(self):
        ini_text = \
            """
            [TLKList]
            StrRef0=2
            StrRef1=1
            StrRef2=0
            """

        tlk = TLK()
        tlk.add("Num1")
        tlk.add("Num2")
        tlk.add("Num3")

        ini = ConfigParser()
        ini.read_string(ini_text)
        ini.optionxform = str

        config = PatcherConfig()

        ConfigReader(ini, tlk).load(config)
        tlk_mod0 = config.patches_tlk.modifiers.pop(0)
        tlk_mod1 = config.patches_tlk.modifiers.pop(0)
        tlk_mod2 = config.patches_tlk.modifiers.pop(0)

        self.assertEqual(tlk_mod0.text, "Num3")
        self.assertEqual(tlk_mod1.text, "Num2")
        self.assertEqual(tlk_mod2.text, "Num1")

    # region 2DA: Change Row
    def test_2da_changerow_identifier(self):
        """Test that identifier is being loaded correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertEqual("change_row_0", mod_0.identifier)

        # noinspection PyTypeChecker
        mod_0: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertEqual("change_row_1", mod_0.identifier)

    def test_2da_changerow_targets(self):
        """Test that target values (line to modify) are loading correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_2da_0: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertEqual(TargetType.ROW_INDEX, mod_2da_0.target.target_type)
        self.assertEqual(1, mod_2da_0.target.value)

        # noinspection PyTypeChecker
        mod_2da_1: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertEqual(TargetType.ROW_LABEL, mod_2da_1.target.target_type)
        self.assertEqual("2", mod_2da_1.target.value)

        # noinspection PyTypeChecker
        mod_2da_2: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertEqual(TargetType.LABEL_COLUMN, mod_2da_2.target.target_type)
        self.assertEqual("3", mod_2da_2.target.value)

    def test_2da_changerow_store2da(self):
        """Test that 2DAMEMORY values are set to be stored correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_2da_0: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)

        # noinspection PyTypeChecker
        store_2da_0a: RowValueRowIndex = mod_2da_0.store_2da[0]
        self.assertIsInstance(store_2da_0a, RowValueRowIndex)

        # noinspection PyTypeChecker
        store_2da_0b: RowValueRowLabel = mod_2da_0.store_2da[1]
        self.assertIsInstance(store_2da_0b, RowValueRowLabel)

        # noinspection PyTypeChecker
        store_2da_0c: RowValueRowCell = mod_2da_0.store_2da[2]
        self.assertIsInstance(store_2da_0c, RowValueRowCell)
        self.assertEqual("label", store_2da_0c.column)

    def test_2da_changerow_cells(self):
        """Test that cells are set to be modified correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_2da_0: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)

        # noinspection PyTypeChecker
        cell_0_label: RowValueConstant = mod_2da_0.cells["label"]
        self.assertIsInstance(cell_0_label, RowValueConstant)
        self.assertEqual("Test123", cell_0_label.string)

        # noinspection PyTypeChecker
        cell_0_dialog: RowValueTLKMemory = mod_2da_0.cells["dialog"]
        self.assertIsInstance(cell_0_dialog, RowValueTLKMemory)
        self.assertEqual(4, cell_0_dialog.token_id)

        # noinspection PyTypeChecker
        cell_0_appearance: RowValue2DAMemory = mod_2da_0.cells["appearance"]
        self.assertIsInstance(cell_0_appearance, RowValue2DAMemory)
        self.assertEqual(5, cell_0_appearance.token_id)
    # endregion

    # region 2DA: Add Row
    def test_2da_addrow_identifier(self):
        """Test that identifier is being loaded correctly."""

        ini_text = \
            """
            [2DAList]
            Table0=test.2da

            [test.2da]
            AddRow0=add_row_0
            AddRow1=add_row_1

            [add_row_0]
            [add_row_1]
            """

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertEqual("add_row_0", mod_0.identifier)

        # noinspection PyTypeChecker
        mod_1: AddRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertEqual("add_row_1", mod_1.identifier)

    def test_2da_addrow_exclusivecolumn(self):
        """Test that exclusive column property is being loaded correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertIsInstance(mod_0, AddRow2DA)
        self.assertEqual("add_row_0", mod_0.identifier)
        self.assertEqual("label", mod_0.exclusive_column)

        # noinspection PyTypeChecker
        mod_1: AddRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertIsInstance(mod_1, AddRow2DA)
        self.assertEqual("add_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.exclusive_column)

    def test_2da_addrow_rowlabel(self):
        """Test that row label property is being loaded correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertIsInstance(mod_0, AddRow2DA)
        self.assertEqual("add_row_0", mod_0.identifier)
        self.assertEqual("123", mod_0.row_label)

        # noinspection PyTypeChecker
        mod_1: AddRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertIsInstance(mod_1, AddRow2DA)
        self.assertEqual("add_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.row_label)

    def test_2da_addrow_store2da(self):
        """Test that 2DAMEMORY# data will be saved correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers.pop(0)

        # noinspection PyTypeChecker
        store_0a: RowValueRowIndex = mod_0.store_2da[0]
        self.assertIsInstance(store_0a, RowValueRowIndex)

        # noinspection PyTypeChecker
        store_0b: RowValueRowLabel = mod_0.store_2da[1]
        self.assertIsInstance(store_0b, RowValueRowLabel)

        # noinspection PyTypeChecker
        store_0c: RowValueRowCell = mod_0.store_2da[2]
        self.assertIsInstance(store_0c, RowValueRowCell)
        self.assertEqual("label", store_0c.column)

    def test_2da_addrow_cells(self):
        """Test that cells will be assigned properly correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers.pop(0)

        # noinspection PyTypeChecker
        cell_0_label: RowValueConstant = mod_0.cells["label"]
        self.assertIsInstance(cell_0_label, RowValueConstant)
        self.assertEqual("Test123", cell_0_label.string)

        # noinspection PyTypeChecker
        cell_0_dialog: RowValueTLKMemory = mod_0.cells["dialog"]
        self.assertIsInstance(cell_0_dialog, RowValueTLKMemory)
        self.assertEqual(4, cell_0_dialog.token_id)

        # noinspection PyTypeChecker
        cell_0_appearance: RowValue2DAMemory = mod_0.cells["appearance"]
        self.assertIsInstance(cell_0_appearance, RowValue2DAMemory)
        self.assertEqual(5, cell_0_appearance.token_id)
    # endregion Add Row

    # region 2DA: Copy Row
    def test_2da_copyrow_identifier(self):
        """Test that identifier is being loaded correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertEqual("copy_row_0", mod_0.identifier)

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertEqual("copy_row_1", mod_1.identifier)

    def test_2da_copyrow_target(self):
        """Test that target values (line to modify) are loading correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertEqual(TargetType.ROW_INDEX, mod_0.target.target_type)
        self.assertEqual(1, mod_0.target.value)

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertEqual(TargetType.ROW_LABEL, mod_1.target.target_type)
        self.assertEqual("2", mod_1.target.value)

        # noinspection PyTypeChecker
        mod_2: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertEqual(TargetType.LABEL_COLUMN, mod_2.target.target_type)
        self.assertEqual("3", mod_2.target.value)

    def test_2da_copyrow_exclusivecolumn(self):
        """Test that exclusive column property is being loaded correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertIsInstance(mod_0, CopyRow2DA)
        self.assertEqual("copy_row_0", mod_0.identifier)
        self.assertEqual("label", mod_0.exclusive_column)

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertIsInstance(mod_1, CopyRow2DA)
        self.assertEqual("copy_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.exclusive_column)

    def test_2da_copyrow_rowlabel(self):
        """Test that row label property is being loaded correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertIsInstance(mod_0, CopyRow2DA)
        self.assertEqual("copy_row_0", mod_0.identifier)
        self.assertEqual("123", mod_0.row_label)

        # noinspection PyTypeChecker
        mod_1: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertIsInstance(mod_1, CopyRow2DA)
        self.assertEqual("copy_row_1", mod_1.identifier)
        self.assertIsNone(mod_1.row_label)

    def test_2da_copyrow_store2da(self):
        """Test that 2DAMEMORY# data will be saved correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)

        # noinspection PyTypeChecker
        store_0a: RowValueRowIndex = mod_0.store_2da[0]
        self.assertIsInstance(store_0a, RowValueRowIndex)

        # noinspection PyTypeChecker
        store_0b: RowValueRowLabel = mod_0.store_2da[1]
        self.assertIsInstance(store_0b, RowValueRowLabel)

        # noinspection PyTypeChecker
        store_0c: RowValueRowCell = mod_0.store_2da[2]
        self.assertIsInstance(store_0c, RowValueRowCell)
        self.assertEqual("label", store_0c.column)

    def test_2da_copyrow_cells(self):
        """Test that cells will be assigned properly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: CopyRow2DA = config.patches_2da[0].modifiers.pop(0)

        # noinspection PyTypeChecker
        cell_0_label: RowValueConstant = mod_0.cells["label"]
        self.assertIsInstance(cell_0_label, RowValueConstant)
        self.assertEqual("Test123", cell_0_label.string)

        # noinspection PyTypeChecker
        cell_0_dialog: RowValueTLKMemory = mod_0.cells["dialog"]
        self.assertIsInstance(cell_0_dialog, RowValueTLKMemory)
        self.assertEqual(4, cell_0_dialog.token_id)

        # noinspection PyTypeChecker
        cell_0_appearance: RowValue2DAMemory = mod_0.cells["appearance"]
        self.assertIsInstance(cell_0_appearance, RowValue2DAMemory)
        self.assertEqual(5, cell_0_appearance.token_id)
    # endregion

    # region 2DA: Add Column
    def test_2da_addcolumn_basic(self):
        """Test that column will be inserted with correct label and default values."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: AddColumn2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertEqual("label", mod_0.header)
        self.assertEqual("", mod_0.default)

        # noinspection PyTypeChecker
        mod_1: AddColumn2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertEqual("someint", mod_1.header)
        self.assertEqual("0", mod_1.default)

    def test_2da_addcolumn_indexinsert(self):
        """Test that cells will be inserted to the new column at the given index correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: AddColumn2DA = config.patches_2da[0].modifiers.pop(0)

        value = mod_0.index_insert[0]
        self.assertIsInstance(value, RowValueConstant)
        self.assertEqual("abc", value.string)

        value = mod_0.index_insert[1]
        self.assertIsInstance(value, RowValue2DAMemory)
        self.assertEqual(4, value.token_id)

        value = mod_0.index_insert[2]
        self.assertIsInstance(value, RowValueTLKMemory)
        self.assertEqual(5, value.token_id)

    def test_2da_addcolumn_labelinsert(self):
        """Test that cells will be inserted to the new column at the given label correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: AddColumn2DA = config.patches_2da[0].modifiers.pop(0)

        value = mod_0.label_insert["0"]
        self.assertIsInstance(value, RowValueConstant)
        self.assertEqual("abc", value.string)

        value = mod_0.label_insert["1"]
        self.assertIsInstance(value, RowValue2DAMemory)
        self.assertEqual(4, value.token_id)

        value = mod_0.label_insert["2"]
        self.assertIsInstance(value, RowValueTLKMemory)
        self.assertEqual(5, value.token_id)

    def test_2da_addcolumn_2damemory(self):
        """Test that 2DAMEMORY will be stored correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: AddColumn2DA = config.patches_2da[0].modifiers.pop(0)

        value = mod_0.store_2da[2]
        self.assertEqual("I2", value)
    # endregion

    # region SSF
    def test_ssf_replace(self):
        """Test that column will be inserted with correct label and default values."""

        ini_text = \
            """
            [SSFList]
            File0=test1.ssf
            Replace0=test2.ssf

            [test1.ssf]
            [test2.ssf]
            """

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        self.assertFalse(config.patches_ssf[0].replace_file)
        self.assertTrue(config.patches_ssf[1].replace_file)

    def test_ssf_stored_constant(self):
        """Test that column will be inserted with correct label and default values."""

        ini_text = \
            """
            [SSFList]
            File0=test.ssf

            [test.ssf]
            Battlecry 1=123
            Battlecry 2=456
            """

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        mod_0 = config.patches_ssf[0].modifiers.pop(0)
        self.assertIsInstance(mod_0.stringref, NoTokenUsage)
        self.assertEqual("123", mod_0.stringref.stored)

        mod_1 = config.patches_ssf[0].modifiers.pop(0)
        self.assertIsInstance(mod_1.stringref, NoTokenUsage)
        self.assertEqual("456", mod_1.stringref.stored)

    def test_ssf_stored_2da(self):
        """Test that column will be inserted with correct label and default values."""

        ini_text = \
            """
            [SSFList]
            File0=test.ssf

            [test.ssf]
            Battlecry 1=2DAMEMORY5
            Battlecry 2=2DAMEMORY6
            """

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        mod_0 = config.patches_ssf[0].modifiers.pop(0)
        self.assertIsInstance(mod_0.stringref, TokenUsage2DA)
        self.assertEqual(5, mod_0.stringref.token_id)

        mod_1 = config.patches_ssf[0].modifiers.pop(0)
        self.assertIsInstance(mod_1.stringref, TokenUsage2DA)
        self.assertEqual(6, mod_1.stringref.token_id)

    def test_ssf_stored_tlk(self):
        """Test that column will be inserted with correct label and default values."""

        ini_text = \
            """
            [SSFList]
            File0=test.ssf

            [test.ssf]
            Battlecry 1=StrRef5
            Battlecry 2=StrRef6
            """

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        mod_0 = config.patches_ssf[0].modifiers.pop(0)
        self.assertIsInstance(mod_0.stringref, TokenUsageTLK)
        self.assertEqual(5, mod_0.stringref.token_id)

        mod_1 = config.patches_ssf[0].modifiers.pop(0)
        self.assertIsInstance(mod_1.stringref, TokenUsageTLK)
        self.assertEqual(6, mod_1.stringref.token_id)

    def test_ssf_set(self):
        """Test that each sound is registered correctly."""

        ini_text = \
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

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig()
        ConfigReader(ini, tlk).load(config)

        mod_battlecry1 = config.patches_ssf[0].modifiers.pop(0)
        mod_battlecry2 = config.patches_ssf[0].modifiers.pop(0)
        mod_battlecry3 = config.patches_ssf[0].modifiers.pop(0)
        mod_battlecry4 = config.patches_ssf[0].modifiers.pop(0)
        mod_battlecry5 = config.patches_ssf[0].modifiers.pop(0)
        mod_battlecry6 = config.patches_ssf[0].modifiers.pop(0)
        mod_selected1 = config.patches_ssf[0].modifiers.pop(0)
        mod_selected2 = config.patches_ssf[0].modifiers.pop(0)
        mod_selected3 = config.patches_ssf[0].modifiers.pop(0)
        mod_attack1 = config.patches_ssf[0].modifiers.pop(0)
        mod_attack2 = config.patches_ssf[0].modifiers.pop(0)
        mod_attack3 = config.patches_ssf[0].modifiers.pop(0)
        mod_pain1 = config.patches_ssf[0].modifiers.pop(0)
        mod_pain2 = config.patches_ssf[0].modifiers.pop(0)
        mod_lowhealth = config.patches_ssf[0].modifiers.pop(0)
        mod_death = config.patches_ssf[0].modifiers.pop(0)
        mod_criticalhit = config.patches_ssf[0].modifiers.pop(0)
        mod_targetimmune = config.patches_ssf[0].modifiers.pop(0)
        mod_placemine = config.patches_ssf[0].modifiers.pop(0)
        mod_disarmmine = config.patches_ssf[0].modifiers.pop(0)
        mod_stealthon = config.patches_ssf[0].modifiers.pop(0)
        mod_search = config.patches_ssf[0].modifiers.pop(0)
        mod_picklockstart = config.patches_ssf[0].modifiers.pop(0)
        mod_picklockfail = config.patches_ssf[0].modifiers.pop(0)
        mod_picklockdone = config.patches_ssf[0].modifiers.pop(0)
        mod_leaveparty = config.patches_ssf[0].modifiers.pop(0)
        mod_rejoinparty = config.patches_ssf[0].modifiers.pop(0)
        mod_poisoned = config.patches_ssf[0].modifiers.pop(0)

        self.assertEqual(SSFSound.BATTLE_CRY_1, mod_battlecry1.sound)
        self.assertEqual(SSFSound.BATTLE_CRY_2, mod_battlecry2.sound)
        self.assertEqual(SSFSound.BATTLE_CRY_3, mod_battlecry3.sound)
        self.assertEqual(SSFSound.BATTLE_CRY_4, mod_battlecry4.sound)
        self.assertEqual(SSFSound.BATTLE_CRY_5, mod_battlecry5.sound)
        self.assertEqual(SSFSound.BATTLE_CRY_6, mod_battlecry6.sound)
        self.assertEqual(SSFSound.SELECT_1, mod_selected1.sound)
        self.assertEqual(SSFSound.SELECT_2, mod_selected2.sound)
        self.assertEqual(SSFSound.SELECT_3, mod_selected3.sound)
        self.assertEqual(SSFSound.ATTACK_GRUNT_1, mod_attack1.sound)
        self.assertEqual(SSFSound.ATTACK_GRUNT_2, mod_attack2.sound)
        self.assertEqual(SSFSound.ATTACK_GRUNT_3, mod_attack3.sound)
        self.assertEqual(SSFSound.PAIN_GRUNT_1, mod_pain1.sound)
        self.assertEqual(SSFSound.PAIN_GRUNT_2, mod_pain2.sound)
        self.assertEqual(SSFSound.LOW_HEALTH, mod_lowhealth.sound)
        self.assertEqual(SSFSound.DEAD, mod_death.sound)
        self.assertEqual(SSFSound.CRITICAL_HIT, mod_criticalhit.sound)
        self.assertEqual(SSFSound.TARGET_IMMUNE, mod_targetimmune.sound)
        self.assertEqual(SSFSound.LAY_MINE, mod_placemine.sound)
        self.assertEqual(SSFSound.DISARM_MINE, mod_disarmmine.sound)
        self.assertEqual(SSFSound.BEGIN_STEALTH, mod_stealthon.sound)
        self.assertEqual(SSFSound.BEGIN_SEARCH, mod_search.sound)
        self.assertEqual(SSFSound.BEGIN_UNLOCK, mod_picklockstart.sound)
        self.assertEqual(SSFSound.UNLOCK_FAILED, mod_picklockfail.sound)
        self.assertEqual(SSFSound.UNLOCK_SUCCESS, mod_picklockdone.sound)
        self.assertEqual(SSFSound.SEPARATED_FROM_PARTY, mod_leaveparty.sound)
        self.assertEqual(SSFSound.REJOINED_PARTY, mod_rejoinparty.sound)
        self.assertEqual(SSFSound.POISONED, mod_poisoned.sound)
    # endregion
