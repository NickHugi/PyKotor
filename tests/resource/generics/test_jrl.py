from unittest import TestCase

from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.jrl import construct_jrl, dismantle_jrl

TEST_FILE = "../../files/test.jrl"


class TestJRL(TestCase):
    def test_io(self):
        gff = read_gff(TEST_FILE)
        jrl = construct_jrl(gff)
        self.validate_io(jrl)

        gff = dismantle_jrl(jrl)
        jrl = construct_jrl(gff)
        self.validate_io(jrl)

    def validate_io(self, jrl):
        quest = jrl.quests[0]
        self.assertEqual("Plot to be considered worthy to hear the Sand People history.", quest.comment)
        self.assertEqual(33089, quest.name.stringref)
        self.assertEqual(4, quest.planet_id)
        self.assertEqual(72, quest.plot_index)
        self.assertEqual(1, quest.priority)
        self.assertEqual("Tat20aa_worthy", quest.tag)

        entry1 = quest.entries[0]
        self.assertFalse(entry1.end)
        self.assertEqual(10, entry1.entry_id)
        self.assertEqual(33090, entry1.text.stringref)
        self.assertAlmostEqual(5.0, entry1.xp_percentage, 1)

        entry2 = quest.entries[1]
        self.assertTrue(entry2.end)
        self.assertEqual(20, entry2.entry_id)
        self.assertEqual(33091, entry2.text.stringref)
        self.assertAlmostEqual(6.0, entry2.xp_percentage, 1)
