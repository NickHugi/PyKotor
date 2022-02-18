from unittest import TestCase

from pykotor.common.language import LocalizedString
from pykotor.common.misc import EquipmentSlot, Game
from pykotor.resource.formats.gff import load_gff
from pykotor.resource.generics.utd import construct_utd, dismantle_utd

TEST_FILE = "../../files/test.utd"


class TestUTD(TestCase):
    def test_io(self):
        gff = load_gff(TEST_FILE)
        utd = construct_utd(gff)
        self.validate_io(utd)

        gff = dismantle_utd(utd)
        utd = construct_utd(gff)
        self.validate_io(utd)

    def validate_io(self, utd):
        self.assertEqual("TelosDoor13", utd.tag)
        self.assertEqual(123731, utd.name.stringref)
        self.assertEqual(-1, utd.description.stringref)
        self.assertEqual("door_tel014", utd.resref)
        self.assertEqual(1, utd.auto_remove_key)
        self.assertEqual(0, utd.lock_dc)
        self.assertEqual("convoresref", utd.conversation)
        self.assertEqual(1, utd.interruptable)
        self.assertEqual(1, utd.faction_id)
        self.assertEqual(1, utd.plot)
        self.assertEqual(1, utd.not_blastable)
        self.assertEqual(1, utd.min1_hp)
        self.assertEqual(1, utd.key_required)
        self.assertEqual(1, utd.lockable)
        self.assertEqual(1, utd.locked)
        self.assertEqual(28, utd.unlock_dc)
        self.assertEqual(1, utd.unlock_diff_mod)
        self.assertEqual(1, utd.unlock_diff_mod)
        self.assertEqual(0, utd.portrait_id)
        self.assertEqual(1, utd.trap_detectable)
        self.assertEqual(0, utd.trap_detect_dc)
        self.assertEqual(1, utd.trap_disarmable)
        self.assertEqual(28, utd.trap_disarm_dc)
        self.assertEqual(0, utd.trap_flag)
        self.assertEqual(1, utd.trap_one_shot)
        self.assertEqual(2, utd.trap_type)
        self.assertEqual("keyname", utd.key_name)
        self.assertEqual(1, utd.animation_state)
        self.assertEqual(1, utd.unused_appearance)
        self.assertEqual(1, utd.min1_hp)
        self.assertEqual(60, utd.current_hp)
        self.assertEqual(5, utd.hardness)
        self.assertEqual(28, utd.fortitude)
        self.assertEqual("door_tel014", utd.resref)
        self.assertEqual(0, utd.willpower)
        self.assertEqual("onclosed", utd.on_closed)
        self.assertEqual("ondamaged", utd.on_damaged)
        self.assertEqual("ondeath", utd.on_death)
        self.assertEqual("ondisarm", utd.on_disarm)
        self.assertEqual("onheartbeat", utd.on_heartbeat)
        self.assertEqual("onlock", utd.on_lock)
        self.assertEqual("onmeleeattacked", utd.on_melee)
        self.assertEqual("onopen", utd.on_open)
        self.assertEqual("onspellcastat", utd.on_power)
        self.assertEqual("ontraptriggered", utd.on_trap_triggered)
        self.assertEqual("onunlock", utd.on_unlock)
        self.assertEqual("onuserdefined", utd.on_user_defined)
        self.assertEqual(0, utd.loadscreen_id)
        self.assertEqual(110, utd.appearance_id)
        self.assertEqual(1, utd.static)
        self.assertEqual(1, utd.open_state)
        self.assertEqual("onclick", utd.on_click)
        self.assertEqual("onfailtoopen", utd.on_open_failed)
        self.assertEqual(1, utd.palette_id)
        self.assertEqual("abcdefg", utd.comment)

