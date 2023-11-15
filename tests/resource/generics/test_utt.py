import pathlib
import sys
from unittest import TestCase

from pykotor.resource.formats.gff.gff_data import GFF

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[3] / "pykotor"
    if pykotor_path.joinpath("__init__.py").exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, str(pykotor_path.parent))

from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.utt import UTT, construct_utt, dismantle_utt

TEST_FILE = "tests/files/test.utt"


class TestUTT(TestCase):
    def test_io(self):
        gff: GFF = read_gff(TEST_FILE)
        utt: UTT = construct_utt(gff)
        self.validate_io(utt)

        gff = dismantle_utt(utt)
        utt = construct_utt(gff)
        self.validate_io(utt)

    def validate_io(self, utt: UTT):
        self.assertEqual("GenericTrigger001", utt.tag)
        self.assertEqual("generictrigge001", utt.resref)
        self.assertEqual(42968, utt.name.stringref)
        self.assertEqual(1, utt.auto_remove_key)
        self.assertEqual(1, utt.faction_id)
        self.assertEqual(1, utt.cursor_id)
        self.assertEqual(3.0, utt.highlight_height)
        self.assertEqual("somekey", utt.key_name)
        self.assertEqual(0, utt.loadscreen_id)
        self.assertEqual(0, utt.portrait_id)
        self.assertEqual(1, utt.type_id)
        self.assertEqual(1, utt.trap_detectable)
        self.assertEqual(10, utt.trap_detect_dc)
        self.assertEqual(1, utt.trap_disarmable)
        self.assertEqual(10, utt.trap_disarm_dc)
        self.assertEqual(1, utt.is_trap)
        self.assertEqual(1, utt.trap_once)
        self.assertEqual(1, utt.trap_type)
        self.assertEqual("ondisarm", utt.on_disarm)
        self.assertEqual("ontraptriggered", utt.on_trap_triggered)
        self.assertEqual("onclick", utt.on_click)
        self.assertEqual("onheartbeat", utt.on_heartbeat)
        self.assertEqual("onenter", utt.on_enter)
        self.assertEqual("onexit", utt.on_exit)
        self.assertEqual("onuserdefined", utt.on_user_defined)
        self.assertEqual(6, utt.palette_id)
        self.assertEqual("comment", utt.comment)
