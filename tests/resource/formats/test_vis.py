from unittest import TestCase

from pykotor.resource.type import ResourceType

from pykotor.resource.formats.vis import VISAsciiReader, VIS
from pykotor.resource.formats.vis.auto import write_vis, load_vis

ASCII_TEST_FILE = "../../files/test.vis"


class TestVIS(TestCase):
    def test_binary_io(self):
        vis = VISAsciiReader(ASCII_TEST_FILE).load()
        self.validate_io(vis)

        data = bytearray()
        write_vis(vis, data, ResourceType.VIS)
        vis = load_vis(data)
        self.validate_io(vis)

    def validate_io(self, vis: VIS):
        self.assertTrue(vis.get_visible("room_01", "room_02"))
        self.assertTrue(vis.get_visible("room_01", "room_03"))
        self.assertTrue(vis.get_visible("room_01", "room_04"))

        self.assertTrue(vis.get_visible("room_02", "room_01"))
        self.assertFalse(vis.get_visible("room_02", "room_03"))
        self.assertFalse(vis.get_visible("room_02", "room_04"))

        self.assertTrue(vis.get_visible("room_03", "room_01"))
        self.assertTrue(vis.get_visible("room_03", "room_04"))
        self.assertFalse(vis.get_visible("room_03", "room_02"))

        self.assertTrue(vis.get_visible("room_04", "room_01"))
        self.assertTrue(vis.get_visible("room_04", "room_03"))
        self.assertFalse(vis.get_visible("room_04", "room_02"))
