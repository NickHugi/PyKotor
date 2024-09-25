from __future__ import annotations

import pathlib
import sys
import unittest
from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from typing import TYPE_CHECKING

from pykotor.common.geometry import Vector3
from pykotor.resource.formats.bwm import BWMBinaryReader, read_bwm, write_bwm

if TYPE_CHECKING:
    from pykotor.resource.formats.bwm import BWM

BINARY_TEST_FILE = "tests/files/test.wok"


class TestBWM(TestCase):
    def test_binary_io(self):
        wok = BWMBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(wok)

        data = bytearray()
        write_bwm(wok, data)
        wok = read_bwm(data)
        self.validate_io(wok)

    def validate_io(self, wok: BWM):
        assert len(wok.vertices()) == 114
        assert len(wok.faces) == 195
        assert wok.faces[1].v1.distance(Vector3(12.667, 23.8963, -1.2749)) < 1000000.0
        assert wok.faces[1].v2.distance(Vector3(12.4444, 28.6584, -1.275)) < 1000000.0
        assert wok.faces[1].v3.distance(Vector3(11.3294, 18.5879, -1.275)) < 1000000.0

        face2_adj = wok.adjacencies(wok.faces[2])
        assert face2_adj[0] is None
        assert wok.faces[29] is face2_adj[1].face
        assert 2 is face2_adj[1].edge
        assert wok.faces[1] is face2_adj[2].face
        assert 0 is face2_adj[2].edge

        face4_adj = wok.adjacencies(wok.faces[4])
        assert wok.faces[30] is face4_adj[0].face
        assert 2 is face4_adj[0].edge
        assert wok.faces[35] is face4_adj[1].face
        assert 2 is face4_adj[1].edge
        assert wok.faces[25] is face4_adj[2].face
        assert 1 is face4_adj[2].edge

        edges = wok.edges()
        assert len(edges) == 73

        # The following tests may fail if the algorithms used to build the aabb tree or edges change. They may, however,
        # still work ingame.
        assert [edges.index(edge) + 1 for edge in edges if edge.final] == [59, 66, 73]
        assert len(wok.aabbs()) == 389


if __name__ == "__main__":
    unittest.main()
