from __future__ import annotations

import os
import pathlib
import sys
import unittest

from pykotor.resource.type import ResourceType

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

from pykotor.common.misc import Color, Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.git import construct_git, dismantle_git

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.git import GIT

TEST_FILE = "tests/files/test.git"
K1_SAME_TEST = "tests/files/k1_same_git_test.git"
K1_LAST_GOOD_EXTRACT = "tests/files/k1_extracted_git_test.git"
K1_PATH = os.environ.get("K1_PATH")
K2_PATH = os.environ.get("K2_PATH")


class TestGIT(unittest.TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, message=""):
        self.log_messages.append(message)

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for git_resource in (resource for resource in self.installation if resource.restype() is ResourceType.GIT):
            gff: GFF = read_gff(git_resource.data())
            reconstructed_gff: GFF = dismantle_git(construct_git(gff), Game.K1)
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages))

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for git_resource in (resource for resource in self.installation if resource.restype() is ResourceType.GIT):
            gff: GFF = read_gff(git_resource.data())
            reconstructed_gff: GFF = dismantle_git(construct_git(gff))
            self.assertTrue(gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages))

    def test_k1_gff_reconstruct(self):
        gff: GFF = read_gff(K1_SAME_TEST)
        reconstructed_gff: GFF = dismantle_git(construct_git(gff), Game.K1)
        self.assertTrue(gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages))

    def test_k2_gff_reconstruct(self):
        gff: GFF = read_gff(TEST_FILE)
        reconstructed_gff: GFF = dismantle_git(construct_git(gff), Game.K2)
        self.assertTrue(gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages))

    def test_io_construct(self):
        gff = read_gff(TEST_FILE)
        git = construct_git(gff)
        self.validate_io(git)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
        gff = dismantle_git(construct_git(gff))
        git = construct_git(gff)
        self.validate_io(git)

    def assertDeepEqual(self, obj1, obj2, context=""):
        if isinstance(obj1, dict) and isinstance(obj2, dict):
            self.assertEqual(set(obj1.keys()), set(obj2.keys()), context)
            for key in obj1:
                new_context = f"{context}.{key}" if context else str(key)
                self.assertDeepEqual(obj1[key], obj2[key], new_context)

        elif isinstance(obj1, (list, tuple)) and isinstance(obj2, (list, tuple)):
            self.assertEqual(len(obj1), len(obj2), context)
            for index, (item1, item2) in enumerate(zip(obj1, obj2)):
                new_context = f"{context}[{index}]" if context else f"[{index}]"
                self.assertDeepEqual(item1, item2, new_context)

        elif hasattr(obj1, "__dict__") and hasattr(obj2, "__dict__"):
            self.assertDeepEqual(obj1.__dict__, obj2.__dict__, context)

        else:
            self.assertEqual(obj1, obj2, context)

    def validate_io(self, git: GIT):
        self.assertEqual(127, git.ambient_volume)
        self.assertEqual(17, git.ambient_sound_id)
        self.assertEqual(1, git.env_audio)
        self.assertEqual(41, git.music_battle_id)
        self.assertEqual(15, git.music_standard_id)
        self.assertEqual(20000, git.music_delay)

        self.assertEqual(1, git.cameras[0].camera_id)
        self.assertEqual(55, git.cameras[0].fov)
        self.assertEqual(3.0, git.cameras[0].height)
        self.assertEqual(0.0, git.cameras[0].mic_range)
        self.assertAlmostEqual(69.699, git.cameras[0].pitch, 2)
        self.assertAlmostEqual(0.971, git.cameras[0].orientation.x, 2)
        self.assertAlmostEqual(0.000, git.cameras[0].orientation.y, 2)
        self.assertAlmostEqual(0.000, git.cameras[0].orientation.z, 2)
        self.assertAlmostEqual(0.235, git.cameras[0].orientation.w, 2)
        self.assertAlmostEqual(-57.167, git.cameras[0].position.x, 2)
        self.assertAlmostEqual(-28.255, git.cameras[0].position.y, 2)
        self.assertAlmostEqual(0.000, git.cameras[0].position.z, 2)

        self.assertEqual("c_ithorian001", git.creatures[0].resref)
        self.assertAlmostEqual(-41.238, git.creatures[0].position.x, 2)
        self.assertAlmostEqual(-53.214, git.creatures[0].position.y, 2)
        self.assertAlmostEqual(0.000, git.creatures[0].position.z, 2)
        self.assertAlmostEqual(0.982, git.creatures[0].bearing, 2)

        self.assertAlmostEqual(1.0, git.doors[0].bearing, 2)
        self.assertAlmostEqual(-43.763, git.doors[0].position.x, 2)
        self.assertAlmostEqual(-20.143, git.doors[0].position.y, 2)
        self.assertAlmostEqual(1.000, git.doors[0].position.z, 2)
        self.assertEqual("linkedto", git.doors[0].linked_to)
        self.assertEqual(1, git.doors[0].linked_to_flags.value)
        self.assertEqual("resref", git.doors[0].linked_to_module)
        self.assertEqual("Ithorian", git.doors[0].tag)
        self.assertEqual("sw_door_taris007", git.doors[0].resref)
        self.assertEqual(13, git.doors[0].transition_destination.stringref)
        self.assertEqual(Color.from_bgr_integer(10197915), git.doors[0].tweak_color)

        self.assertEqual("mercenariesentry", git.encounters[0].resref)
        self.assertAlmostEqual(-41.319, git.encounters[0].position.x, 2)
        self.assertAlmostEqual(-19.222, git.encounters[0].position.y, 2)
        self.assertAlmostEqual(1.000, git.encounters[0].position.z, 2)
        self.assertAlmostEqual(-5.890, git.encounters[0].geometry[0].x, 2)
        self.assertAlmostEqual(3.072, git.encounters[0].geometry[0].y, 2)
        self.assertAlmostEqual(0.025, git.encounters[0].geometry[0].z, 2)
        self.assertAlmostEqual(-48.936, git.encounters[0].spawn_points[0].x, 2)
        self.assertAlmostEqual(-29.831, git.encounters[0].spawn_points[0].y, 2)
        self.assertAlmostEqual(1.000, git.encounters[0].spawn_points[0].z, 2)
        self.assertAlmostEqual(0.196, git.encounters[0].spawn_points[0].orientation, 2)

        self.assertEqual("k_trans_abort", git.placeables[0].resref)
        self.assertAlmostEqual(1.0, git.placeables[0].bearing, 2)
        self.assertAlmostEqual(-33.268, git.placeables[0].position.x, 2)
        self.assertAlmostEqual(-15.299, git.placeables[0].position.y, 2)
        self.assertAlmostEqual(9.536, git.placeables[0].position.z, 2)
        self.assertEqual(Color.from_bgr_integer(10197915), git.placeables[0].tweak_color)

        self.assertEqual("computerpanne001", git.sounds[0].resref)
        self.assertAlmostEqual(-78.538, git.sounds[0].position.x, 2)
        self.assertAlmostEqual(13.498, git.sounds[0].position.y, 2)
        self.assertAlmostEqual(2.000, git.sounds[0].position.z, 2)

        self.assertEqual("m_chano", git.stores[0].resref)
        self.assertAlmostEqual(106.230, git.stores[0].position.x, 2)
        self.assertAlmostEqual(-16.590, git.stores[0].position.y, 2)
        self.assertAlmostEqual(0.063, git.stores[0].position.z, 2)
        self.assertAlmostEqual(0.000, git.stores[0].bearing, 2)

        self.assertEqual("newgeneric001", git.triggers[0].resref)
        self.assertAlmostEqual(-29.903, git.triggers[0].position.x, 2)
        self.assertAlmostEqual(-11.463, git.triggers[0].position.y, 2)
        self.assertAlmostEqual(-2.384, git.triggers[0].position.z, 2)
        self.assertEqual("from_204TEL", git.triggers[0].linked_to)
        self.assertEqual(2, git.triggers[0].linked_to_flags.value)
        self.assertEqual("203tel", git.triggers[0].linked_to_module)
        self.assertEqual("to_203TEL", git.triggers[0].tag)
        self.assertEqual(104245, git.triggers[0].transition_destination.stringref)
        self.assertAlmostEqual(-7.433, git.triggers[0].geometry[0].x, 2)
        self.assertAlmostEqual(1.283, git.triggers[0].geometry[0].y, 2)
        self.assertAlmostEqual(0.025, git.triggers[0].geometry[0].z, 2)

        self.assertEqual("wp_transabort", git.waypoints[0].resref)
        self.assertEqual("wp_transabort", git.waypoints[0].tag)
        self.assertEqual(135283, git.waypoints[0].name.stringref)
        self.assertTrue(git.waypoints[0].map_note_enabled)
        self.assertEqual(123, git.waypoints[0].map_note.stringref)
        self.assertAlmostEqual(-33.620, git.waypoints[0].position.x, 2)
        self.assertAlmostEqual(-16.065, git.waypoints[0].position.y, 2)
        self.assertAlmostEqual(1.0, git.waypoints[0].position.z, 2)
        self.assertAlmostEqual(0.000, git.waypoints[0].bearing, 2)


if __name__ == "__main__":
    unittest.main()
