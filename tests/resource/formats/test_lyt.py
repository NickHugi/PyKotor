from unittest import TestCase

from pykotor.resource.type import ResourceType

from pykotor.common.geometry import Vector3, Vector4
from pykotor.resource.formats.lyt import LYTAsciiReader, LYTRoom, LYTTrack, LYT, LYTObstacle, LYTDoorHook
from pykotor.resource.formats.lyt.auto import write_lyt, load_lyt

ASCII_TEST_FILE = "../../files/test.lyt"


class TestLYT(TestCase):
    def test_binary_io(self):
        lyt = LYTAsciiReader(ASCII_TEST_FILE).load()
        self.validate_io(lyt)

        data = bytearray()
        write_lyt(lyt, data, ResourceType.LYT)
        lyt = load_lyt(data)
        self.validate_io(lyt)

    def validate_io(self, lyt: LYT):
        self.assertEqual(lyt.rooms[0], LYTRoom("M17mg_01a", Vector3(100.0, 100.0, 0.0)))
        self.assertEqual(lyt.rooms[1], LYTRoom("M17mg_01b", Vector3(100.0, 100.0, 0.0)))
        self.assertEqual(lyt.tracks[0], LYTTrack("M17mg_MGT01", Vector3(0.0, 0.0, 0.0)))
        self.assertEqual(lyt.tracks[1], LYTTrack("M17mg_MGT02", Vector3(112.047, 209.04, 0.0)))
        self.assertEqual(lyt.obstacles[0], LYTObstacle("M17mg_MGO01", Vector3(103.309, 3691.61, 0.0)))
        self.assertEqual(lyt.obstacles[1], LYTObstacle("M17mg_MGO02", Vector3(118.969, 3688.0, 0.0)))
        self.assertEqual(lyt.doorhooks[0], LYTDoorHook("M02ac_02h", "door_01", Vector3(170.475, 66.375, 0.0),
                                                       Vector4(0.707107, 0.0, 0.0, -0.707107)))
        self.assertEqual(lyt.doorhooks[1],
                         LYTDoorHook("M02ac_02a", "door_06", Vector3(90.0, 129.525, 0.0), Vector4(1.0, 0.0, 0.0, 0.0)))
