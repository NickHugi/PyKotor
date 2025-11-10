from __future__ import annotations

import os
import pathlib
import sys
import unittest


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

from typing import TYPE_CHECKING, cast

from utility.common.geometry import Vector3  # pyright: ignore[reportMissingImports]
from pykotor.common.language import Gender, Language
from pykotor.common.misc import Color
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.git import construct_git, dismantle_git
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.git import GIT

TEST_GIT_XML = """<gff3>
  <struct id="-1">
    <byte label="UseTemplates">1</byte>
    <struct label="AreaProperties" id="100">
      <sint32 label="AmbientSndDay">17</sint32>
      <sint32 label="AmbientSndNight">17</sint32>
      <sint32 label="AmbientSndDayVol">127</sint32>
      <sint32 label="AmbientSndNitVol">127</sint32>
      <sint32 label="EnvAudio">1</sint32>
      <sint32 label="MusicBattle">41</sint32>
      <sint32 label="MusicDay">15</sint32>
      <sint32 label="MusicNight">15</sint32>
      <sint32 label="MusicDelay">20000</sint32>
      </struct>
    <list label="CameraList">
      <struct id="14">
        <sint32 label="CameraID">1</sint32>
        <vector label="Position">
          <double>-57.16752624511719</double>
          <double>-28.255794525146484</double>
          <double>0.0</double>
          </vector>
        <float label="Pitch">69.69999694824219</float>
        <float label="MicRange">0.0</float>
        <orientation label="Orientation">
          <double>0.9719610214233398</double>
          <double>0.0</double>
          <double>0.0</double>
          <double>0.23514211177825928</double>
          </orientation>
        <float label="Height">3.0</float>
        <float label="FieldOfView">55.0</float>
        </struct>
      </list>
    <list label="Creature List">
      <struct id="4">
        <float label="XPosition">-41.23826599121094</float>
        <float label="YPosition">-53.214324951171875</float>
        <float label="ZPosition">0.0</float>
        <float label="XOrientation">-0.8314653635025024</float>
        <float label="YOrientation">0.5555765628814697</float>
        <resref label="TemplateResRef">c_ithorian001</resref>
        </struct>
      </list>
    <list label="Door List">
      <struct id="8">
        <resref label="TemplateResRef">sw_door_taris007</resref>
        <exostring label="Tag">Ithorian</exostring>
        <resref label="LinkedToModule">resref</resref>
        <exostring label="LinkedTo">linkedto</exostring>
        <byte label="LinkedToFlags">1</byte>
        <locstring label="TransitionDestin" strref="13" />
        <float label="X">-43.76350021362305</float>
        <float label="Y">-20.14310073852539</float>
        <float label="Z">1.0</float>
        <float label="Bearing">1.0</float>
        <byte label="UseTweakColor">1</byte>
        <uint32 label="TweakColor">10197915</uint32>
        </struct>
      </list>
    <list label="Encounter List">
      <struct id="7">
        <resref label="TemplateResRef">mercenariesentry</resref>
        <float label="XPosition">-41.31961441040039</float>
        <float label="YPosition">-19.222841262817383</float>
        <float label="ZPosition">1.0</float>
        <list label="Geometry">
          <struct id="1">
            <float label="X">-5.890754699707031</float>
            <float label="Y">3.072599411010742</float>
            <float label="Z">0.025000059977173805</float>
            </struct>
          </list>
        <list label="SpawnPointList">
          <struct id="2">
            <float label="X">-48.936973571777344</float>
            <float label="Y">-29.831298828125</float>
            <float label="Z">1.0</float>
            <float label="Orientation">0.19634968042373657</float>
            </struct>
          </list>
        </struct>
      </list>
    <list label="SoundList">
      <struct id="6">
        <resref label="TemplateResRef">computerpanne001</resref>
        <uint32 label="GeneratedType">0</uint32>
        <float label="XPosition">-78.53829193115234</float>
        <float label="YPosition">13.498023986816406</float>
        <float label="ZPosition">2.0</float>
        </struct>
      </list>
    <list label="StoreList">
      <struct id="11">
        <float label="XPosition">106.23011016845703</float>
        <float label="YPosition">-16.590370178222656</float>
        <float label="ZPosition">0.0634458065032959</float>
        <float label="XOrientation">0.0</float>
        <float label="YOrientation">1.0</float>
        <resref label="ResRef">m_chano</resref>
        </struct>
      </list>
    <list label="TriggerList">
      <struct id="1">
        <resref label="TemplateResRef">newgeneric001</resref>
        <exostring label="Tag">to_203TEL</exostring>
        <locstring label="TransitionDestin" strref="104245" />
        <resref label="LinkedToModule">203tel</resref>
        <exostring label="LinkedTo">from_204TEL</exostring>
        <byte label="LinkedToFlags">2</byte>
        <float label="XPosition">-29.903594970703125</float>
        <float label="YPosition">-11.463098526000977</float>
        <float label="ZPosition">-2.384000062942505</float>
        <list label="Geometry">
          <struct id="3">
            <float label="PointX">-7.433097839355469</float>
            <float label="PointY">1.2834482192993164</float>
            <float label="PointZ">0.025282764807343483</float>
            </struct>
          </list>
        </struct>
      </list>
    <list label="WaypointList">
      <struct id="5">
        <byte label="Appearance">1</byte>
        <resref label="TemplateResRef">wp_transabort</resref>
        <exostring label="Tag">wp_transabort</exostring>
        <locstring label="LocalizedName" strref="135283" />
        <locstring label="Description" strref="-1" />
        <byte label="HasMapNote">1</byte>
        <locstring label="MapNote" strref="123" />
        <byte label="MapNoteEnabled">1</byte>
        <float label="XPosition">-33.620662689208984</float>
        <float label="YPosition">-16.065120697021484</float>
        <float label="ZPosition">1.0</float>
        </struct>
      </list>
    <list label="Placeable List">
      <struct id="9">
        <resref label="TemplateResRef">k_trans_abort</resref>
        <float label="X">-33.26881408691406</float>
        <float label="Y">-15.299334526062012</float>
        <float label="Z">9.53600025177002</float>
        <float label="Bearing">1.0</float>
        <byte label="UseTweakColor">1</byte>
        <uint32 label="TweakColor">10197915</uint32>
        </struct>
      </list>
    </struct>
  </gff3>
"""

K1_SAME_GIT_XML = """<gff3>
  <struct id="-1">
    <struct label="AreaProperties" id="100">
      <sint32 label="AmbientSndDay">8</sint32>
      <sint32 label="AmbientSndNight">8</sint32>
      <sint32 label="AmbientSndDayVol">82</sint32>
      <sint32 label="AmbientSndNitVol">60</sint32>
      <sint32 label="EnvAudio">58</sint32>
      <sint32 label="MusicBattle">39</sint32>
      <sint32 label="MusicDay">19</sint32>
      <sint32 label="MusicNight">19</sint32>
      <sint32 label="MusicDelay">5000</sint32>
      </struct>
    <list label="CameraList">
      <struct id="14">
        <sint32 label="CameraID">10</sint32>
        <vector label="Position">
          <double>28.31999969482422</double>
          <double>-26.440000534057617</double>
          <double>-0.03999999910593033</double>
          </vector>
        <float label="Pitch">90.0</float>
        <float label="MicRange">0.0</float>
        <orientation label="Orientation">
          <double>0.8786699771881104</double>
          <double>0.0</double>
          <double>0.0</double>
          <double>0.4774399995803833</double>
          </orientation>
        <float label="Height">1.5</float>
        <float label="FieldOfView">45.0</float>
        </struct>
      </list>
    <list label="Creature List">
      <struct id="4">
        <float label="XPosition">13.425110816955566</float>
        <float label="YPosition">-29.33724594116211</float>
        <float label="ZPosition">-0.03956466168165207</float>
        <float label="XOrientation">0.0</float>
        <float label="YOrientation">1.0</float>
        <resref label="TemplateResRef">ldr_umand02</resref>
        </struct>
      </list>
    <list label="Door List">
      <struct id="8">
        <resref label="TemplateResRef">ldr_agtoah</resref>
        <exostring label="Tag">ldr_agtoah</exostring>
        <resref label="LinkedToModule">unk_m41ah</resref>
        <exostring label="LinkedTo">ldr_from41ah</exostring>
        <byte label="LinkedToFlags">2</byte>
        <locstring label="TransitionDestin" strref="-1">
          <string language="0">Engine Deck</string>
          </locstring>
        <float label="X">22.007699966430664</float>
        <float label="Y">-47.4744987487793</float>
        <float label="Z">-1.525880009012326e-07</float>
        <float label="Bearing">-0.0</float>
        <byte label="UseTweakColor">1</byte>
        <uint32 label="TweakColor">3224629</uint32>
        </struct>
      </list>
    </struct>
  </gff3>
"""
class TestGIT(unittest.TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, message=""):
        self.log_messages.append(message)

    def test_k1_io_construct(self):
        gff = read_gff(K1_SAME_GIT_XML.encode(), file_format=ResourceType.GFF_XML)
        git = construct_git(gff)
        self.validate_k1_io(git)

    def test_k2_io_construct(self):
        gff = read_gff(TEST_GIT_XML.encode(), file_format=ResourceType.GFF_XML)
        git = construct_git(gff)
        self.validate_io(git)

    def test_k2_io_reconstruct(self):
        gff = read_gff(TEST_GIT_XML.encode(), file_format=ResourceType.GFF_XML)
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

    def validate_k1_io(self, git: GIT):
        self.assertEqual(82, git.ambient_volume)
        self.assertEqual(8, git.ambient_sound_id)
        self.assertEqual(58, git.env_audio)
        self.assertEqual(39, git.music_battle_id)
        self.assertEqual(19, git.music_standard_id)
        self.assertEqual(5000, git.music_delay)

        self.assertEqual(10, git.cameras[0].camera_id)
        self.assertEqual(45, git.cameras[0].fov)
        self.assertEqual(1.5, git.cameras[0].height)
        self.assertEqual(0.0, git.cameras[0].mic_range)
        self.assertAlmostEqual(90.0, git.cameras[0].pitch, 2)
        self.assertAlmostEqual(0.8787, git.cameras[0].orientation.x, 4)
        self.assertAlmostEqual(0.0, git.cameras[0].orientation.y, 4)
        self.assertAlmostEqual(0.0, git.cameras[0].orientation.z, 4)
        self.assertAlmostEqual(0.4774, git.cameras[0].orientation.w, 4)
        self.assertAlmostEqual(28.32, git.cameras[0].position.x, 2)
        self.assertAlmostEqual(-26.44, git.cameras[0].position.y, 2)
        self.assertAlmostEqual(-0.04, git.cameras[0].position.z, 2)

        self.assertEqual("ldr_umand02", git.creatures[0].resref)
        self.assertAlmostEqual(13.425, git.creatures[0].position.x, 3)
        self.assertAlmostEqual(-29.337, git.creatures[0].position.y, 3)
        self.assertAlmostEqual(-0.0396, git.creatures[0].position.z, 4)
        self.assertAlmostEqual(0.0, git.creatures[0].bearing, 3)

        self.assertAlmostEqual(0.0, git.doors[0].bearing, 3)
        self.assertAlmostEqual(22.0077, git.doors[0].position.x, 4)
        self.assertAlmostEqual(-47.4745, git.doors[0].position.y, 4)
        self.assertAlmostEqual(0.0, git.doors[0].position.z, 4)
        self.assertEqual("ldr_from41ah", git.doors[0].linked_to)
        self.assertEqual(2, git.doors[0].linked_to_flags.value)
        self.assertEqual("unk_m41ah", git.doors[0].linked_to_module)
        self.assertEqual("ldr_agtoah", git.doors[0].tag)
        self.assertEqual("ldr_agtoah", git.doors[0].resref)
        self.assertEqual(-1, git.doors[0].transition_destination.stringref)
        self.assertEqual(
            "Engine Deck",
            git.doors[0].transition_destination.get(Language.ENGLISH, Gender.MALE),
        )
        self.assertEqual(Color.from_bgr_integer(3224629), git.doors[0].tweak_color)

        self.assertEqual(0, len(git.encounters))
        self.assertEqual(0, len(git.placeables))
        self.assertEqual(0, len(git.sounds))
        self.assertEqual(0, len(git.stores))
        self.assertEqual(0, len(git.triggers))
        self.assertEqual(0, len(git.waypoints))

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
        encounter_vertex: Vector3 = cast(Vector3, git.encounters[0].geometry[0])
        self.assertAlmostEqual(-5.890, encounter_vertex.x, 2)
        self.assertAlmostEqual(3.072, encounter_vertex.y, 2)
        self.assertAlmostEqual(0.025, encounter_vertex.z, 2)
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
        trigger_vertex: Vector3 = cast(Vector3, git.triggers[0].geometry[0])
        self.assertAlmostEqual(-7.433, trigger_vertex.x, 2)
        self.assertAlmostEqual(1.283, trigger_vertex.y, 2)
        self.assertAlmostEqual(0.025, trigger_vertex.z, 2)

        self.assertEqual("wp_transabort", git.waypoints[0].resref)
        self.assertEqual("wp_transabort", git.waypoints[0].tag)
        self.assertEqual(135283, git.waypoints[0].name.stringref)
        self.assertTrue(git.waypoints[0].map_note_enabled)
        waypoint_0 = git.waypoints[0]
        assert waypoint_0.map_note is not None, "Map note is required"
        self.assertEqual(123, waypoint_0.map_note.stringref)
        self.assertAlmostEqual(-33.620, waypoint_0.position.x, 2)
        self.assertAlmostEqual(-16.065, waypoint_0.position.y, 2)
        self.assertAlmostEqual(1.0, waypoint_0.position.z, 2)
        self.assertAlmostEqual(0.000, waypoint_0.bearing, 2)


if __name__ == "__main__":
    unittest.main()
