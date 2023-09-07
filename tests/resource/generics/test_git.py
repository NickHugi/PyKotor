from unittest import TestCase

from pykotor.common.misc import Color
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.git import construct_git, dismantle_git

TEST_FILE = "../../files/test.git"


class TestGIT(TestCase):
    def test_io(self):
        gff = read_gff(TEST_FILE)
        git = construct_git(gff)
        self.validate_io(git)

        gff = dismantle_git(git)
        git = construct_git(gff)
        self.validate_io(git)

    def validate_io(self, git):
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
        self.assertAlmostEqual(0.9817400806520653, git.creatures[0].bearing, 2)

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
