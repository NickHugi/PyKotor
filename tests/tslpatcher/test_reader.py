from configparser import ConfigParser
from unittest import TestCase

from pykotor.resource.formats.tlk import TLK
from pykotor.tslpatcher.config import PatcherConfig
from pykotor.tslpatcher.mods.twoda import ChangeRow2DA, TargetType, RowValueRowIndex, RowValueRowLabel, RowValueRowCell, \
    RowValueConstant, RowValue2DAMemory, RowValueTLKMemory, AddRow2DA
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

        config = PatcherConfig("", "")

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

        config = PatcherConfig("", "")
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

        config = PatcherConfig("", "")
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

        config = PatcherConfig("", "")
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

        config = PatcherConfig("", "")
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
            RowIndex=1
            [add_row_1]
            RowLabel=1
            """

        tlk = TLK()

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        config = PatcherConfig("", "")
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

        config = PatcherConfig("", "")
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: AddRow2DA = config.patches_2da[0].modifiers.pop(0)
        self.assertIsInstance(mod_0, AddRow2DA)
        self.assertEqual("add_row_0", mod_0.identifier)
        self.assertEqual("label", mod_0.exclusive_column)

        # noinspection PyTypeChecker
        mod_1: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)
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

        config = PatcherConfig("", "")
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

        config = PatcherConfig("", "")
        ConfigReader(ini, tlk).load(config)

        # noinspection PyTypeChecker
        mod_0: ChangeRow2DA = config.patches_2da[0].modifiers.pop(0)

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

        config = PatcherConfig("", "")
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
