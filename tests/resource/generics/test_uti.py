from unittest import TestCase

from pykotor.common.language import LocalizedString
from pykotor.common.misc import EquipmentSlot, Game
from pykotor.resource.formats.gff import load_gff
from pykotor.resource.generics.uti import construct_uti, dismantle_uti

TEST_FILE = "../../files/test.uti"


class TestUTI(TestCase):
    def test_io(self):
        gff = load_gff(TEST_FILE)
        uti = construct_uti(gff)
        self.validate_io(uti)

        gff = dismantle_uti(uti)
        uti = construct_uti(gff)
        self.validate_io(uti)

    def validate_io(self, uti):
        self.assertEqual("g_a_class4001", uti.resref)
        self.assertEqual(38, uti.base_item)
        self.assertEqual(5632, uti.name.stringref)
        self.assertEqual(456, uti.description.stringref)
        self.assertEqual("G_A_CLASS4001", uti.tag)
        self.assertEqual(13, uti.charges)
        self.assertEqual(50, uti.cost)
        self.assertEqual(1, uti.stolen)
        self.assertEqual(1, uti.stack_size)
        self.assertEqual(1, uti.plot)
        self.assertEqual(50, uti.add_cost)
        self.assertEqual(3, uti.body_variation)
        self.assertEqual(1, uti.texture_variation)
        self.assertEqual(1, uti.palette_id)
        self.assertEqual("itemo", uti.comment)

        self.assertEqual(2, len(uti.properties))
        self.assertIsNone(uti.properties[0].upgrade_type, None)
        self.assertEqual(100, uti.properties[1].chance_appear)
        self.assertEqual(1, uti.properties[1].cost_table)
        self.assertEqual(1, uti.properties[1].cost_value)
        self.assertEqual(255, uti.properties[1].param1)
        self.assertEqual(1, uti.properties[1].param1_value)
        self.assertEqual(45, uti.properties[1].property_name)
        self.assertEqual(6, uti.properties[1].subtype)
        self.assertEqual(24, uti.properties[1].upgrade_type)
