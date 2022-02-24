import os
from unittest import TestCase

from pykotor.common.geometry import Vector3

from pykotor.resource.type import ResourceType

from pykotor.resource.formats.bwm import BWMBinaryReader, BWMBinaryWriter, BWM, write_bwm, load_bwm

BINARY_TEST_FILE = "../../files/test.wok"


class TestBWM(TestCase):
    def test_binary_io(self):
        wok = BWMBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(wok)

        data = bytearray()
        write_bwm(wok, data)
        wok = load_bwm(data)
        self.validate_io(wok)

    def validate_io(self, wok: BWM):
        self.assertEqual(114, len(wok.vertices()))
        self.assertEqual(195, len(wok.faces))
        self.assertTrue(wok.faces[1].v1.distance(Vector3(12.6670, 23.8963, -1.2749)) < 1e6)
        self.assertTrue(wok.faces[1].v2.distance(Vector3(12.4444, 28.6584, -1.2750)) < 1e6)
        self.assertTrue(wok.faces[1].v3.distance(Vector3(11.3294, 18.5879, -1.2750)) < 1e6)

        face2_adj = wok.adjacencies(wok.faces[2])
        self.assertIsNone(face2_adj[0])
        self.assertIs(wok.faces[29], face2_adj[1].face)
        self.assertIs(2, face2_adj[1].edge)
        self.assertIs(wok.faces[1], face2_adj[2].face)
        self.assertIs(0, face2_adj[2].edge)

        face4_adj = wok.adjacencies(wok.faces[4])
        self.assertIs(wok.faces[30], face4_adj[0].face)
        self.assertIs(2, face4_adj[0].edge)
        self.assertIs(wok.faces[35], face4_adj[1].face)
        self.assertIs(2, face4_adj[1].edge)
        self.assertIs(wok.faces[25], face4_adj[2].face)
        self.assertIs(1, face4_adj[2].edge)

        edges = wok.edges()
        self.assertEqual(73, len(edges))

        # The following tests may fail if the algorithms used to build the aabb tree or edges change. They may, however,
        # still work ingame.
        self.assertEqual([59, 66, 73], [edges.index(edge) + 1 for edge in edges if edge.final])
        self.assertEqual(389, len(wok.aabbs()))


