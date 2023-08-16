from unittest import TestCase

from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.ute import construct_ute, dismantle_ute

TEST_FILE = "tests/files/test.ute"


class TestUTE(TestCase):
    def test_io(self):
        gff = read_gff(TEST_FILE)
        ute = construct_ute(gff)
        self.validate_io(ute)

        gff = dismantle_ute(ute)
        ute = construct_ute(gff)
        self.validate_io(ute)

    def validate_io(self, ute):
        self.assertEqual("G_KATAARNGROUP01", ute.tag)
        self.assertEqual(31918, ute.name.stringref)
        self.assertEqual("g_kataarngroup01", ute.resref)
        self.assertEqual(1, ute.active)
        self.assertEqual(1, ute.unused_difficulty)
        self.assertEqual(2, ute.difficulty_id)
        self.assertEqual(1, ute.faction_id)
        self.assertEqual(6, ute.max_creatures)
        self.assertEqual(1, ute.player_only)
        self.assertEqual(3, ute.rec_creatures)
        self.assertEqual(1, ute.reset)
        self.assertEqual(60, ute.reset_time)
        self.assertEqual(1, ute.respawns)
        self.assertEqual(1, ute.single_shot)
        self.assertEqual("onentered", ute.on_entered)
        self.assertEqual("onexit", ute.on_exit)
        self.assertEqual("onexhausted", ute.on_exhausted)
        self.assertEqual("onheartbeat", ute.on_heartbeat)
        self.assertEqual("onuserdefined", ute.on_user_defined)
        self.assertEqual(7, ute.palette_id)
        self.assertEqual("Kashyyyk", ute.comment)

        self.assertEqual(2, len(ute.creatures))
        self.assertEqual(74, ute.creatures[1].appearance_id)
        self.assertEqual(8.0, ute.creatures[1].challenge_rating)
        self.assertEqual("g_kataarn02", ute.creatures[1].resref)
        self.assertEqual(1, ute.creatures[1].guaranteed_count)
        self.assertTrue(ute.creatures[1].single_spawn)
