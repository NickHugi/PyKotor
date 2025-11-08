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

from pykotor.common.misc import Game
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.are import construct_are, dismantle_are

if TYPE_CHECKING:
    from pykotor.resource.formats.gff import GFF
    from pykotor.resource.generics.are import ARE

TEST_ARE_XML = """<gff3>
  <struct id="-1">
    <sint32 label="ID">0</sint32>
    <sint32 label="Creator_ID">0</sint32>
    <uint32 label="Version">88</uint32>
    <exostring label="Tag">Untitled</exostring>
    <locstring label="Name" strref="75101" />
    <exostring label="Comments">comments</exostring>
    <struct label="Map" id="0">
      <sint32 label="MapResX">18</sint32>
      <sint32 label="NorthAxis">1</sint32>
      <float label="WorldPt1X">-14.180000305175781</float>
      <float label="WorldPt1Y">-15.0600004196167</float>
      <float label="WorldPt2X">13.279999732971191</float>
      <float label="WorldPt2Y">12.859999656677246</float>
      <float label="MapPt1X">0.3779999911785126</float>
      <float label="MapPt1Y">0.7680000066757202</float>
      <float label="MapPt2X">0.621999979019165</float>
      <float label="MapPt2Y">0.27300000190734863</float>
      <sint32 label="MapZoom">1</sint32>
      </struct>
    <list label="Expansion_List" />
    <uint32 label="Flags">0</uint32>
    <sint32 label="ModSpotCheck">0</sint32>
    <sint32 label="ModListenCheck">0</sint32>
    <float label="AlphaTest">0.20000000298023224</float>
    <sint32 label="CameraStyle">1</sint32>
    <resref label="DefaultEnvMap">defaultenvmap</resref>
    <resref label="Grass_TexName">grasstexture</resref>
    <float label="Grass_Density">1.0</float>
    <float label="Grass_QuadSize">1.0</float>
    <uint32 label="Grass_Ambient">16777215</uint32>
    <uint32 label="Grass_Diffuse">16777215</uint32>
    <uint32 label="Grass_Emissive">16777215</uint32>
    <float label="Grass_Prob_LL">0.25</float>
    <float label="Grass_Prob_LR">0.25</float>
    <float label="Grass_Prob_UL">0.25</float>
    <float label="Grass_Prob_UR">0.25</float>
    <uint32 label="MoonAmbientColor">0</uint32>
    <uint32 label="MoonDiffuseColor">0</uint32>
    <byte label="MoonFogOn">0</byte>
    <float label="MoonFogNear">99.0</float>
    <float label="MoonFogFar">100.0</float>
    <uint32 label="MoonFogColor">0</uint32>
    <byte label="MoonShadows">0</byte>
    <uint32 label="SunAmbientColor">16777215</uint32>
    <uint32 label="SunDiffuseColor">16777215</uint32>
    <byte label="SunFogOn">1</byte>
    <float label="SunFogNear">99.0</float>
    <float label="SunFogFar">100.0</float>
    <uint32 label="SunFogColor">16777215</uint32>
    <byte label="SunShadows">1</byte>
    <uint32 label="DynAmbientColor">16777215</uint32>
    <byte label="IsNight">0</byte>
    <byte label="LightingScheme">0</byte>
    <byte label="ShadowOpacity">205</byte>
    <byte label="DayNightCycle">0</byte>
    <sint32 label="ChanceRain">99</sint32>
    <sint32 label="ChanceSnow">99</sint32>
    <sint32 label="ChanceLightning">99</sint32>
    <sint32 label="WindPower">1</sint32>
    <uint16 label="LoadScreenID">0</uint16>
    <byte label="PlayerVsPlayer">3</byte>
    <byte label="NoRest">0</byte>
    <byte label="NoHangBack">0</byte>
    <byte label="PlayerOnly">0</byte>
    <byte label="Unescapable">1</byte>
    <byte label="DisableTransit">1</byte>
    <byte label="StealthXPEnabled">1</byte>
    <uint32 label="StealthXPLoss">25</uint32>
    <uint32 label="StealthXPMax">25</uint32>
    <sint32 label="DirtyARGBOne">123</sint32>
    <sint32 label="DirtySizeOne">1</sint32>
    <sint32 label="DirtyFormulaOne">1</sint32>
    <sint32 label="DirtyFuncOne">1</sint32>
    <sint32 label="DirtyARGBTwo">1234</sint32>
    <sint32 label="DirtySizeTwo">1</sint32>
    <sint32 label="DirtyFormulaTwo">1</sint32>
    <sint32 label="DirtyFuncTwo">1</sint32>
    <sint32 label="DirtyARGBThree">12345</sint32>
    <sint32 label="DirtySizeThree">1</sint32>
    <sint32 label="DirtyFormulaThre">1</sint32>
    <sint32 label="DirtyFuncThree">1</sint32>
    <list label="Rooms">
      <struct id="0">
        <exostring label="RoomName">002ebo</exostring>
        <sint32 label="EnvAudio">17</sint32>
        <float label="AmbientScale">0.9300000071525574</float>
        <sint32 label="ForceRating">1</sint32>
        <byte label="DisableWeather">1</byte>
        </struct>
      <struct id="0">
        <exostring label="RoomName">002ebo2</exostring>
        <sint32 label="EnvAudio">17</sint32>
        <float label="AmbientScale">0.9800000190734863</float>
        <sint32 label="ForceRating">2</sint32>
        <byte label="DisableWeather">0</byte>
        </struct>
      </list>
    <resref label="OnEnter">k_on_enter</resref>
    <resref label="OnExit">onexit</resref>
    <resref label="OnHeartbeat">onheartbeat</resref>
    <resref label="OnUserDefined">onuserdefined</resref>
    </struct>
  </gff3>
"""
class TestARE(unittest.TestCase):
    def setUp(self):
        self.log_messages: list[str] = [os.linesep]

    def log_func(self, message=""):
        self.log_messages.append(message)

    def test_io_construct(self):
        gff = read_gff(TEST_ARE_XML.encode(), file_format=ResourceType.GFF_XML)
        are = construct_are(gff)
        self.validate_io(are)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_ARE_XML.encode(), file_format=ResourceType.GFF_XML)
        gff = dismantle_are(construct_are(gff), Game.K2)
        are = construct_are(gff)
        self.validate_io(are)

    def validate_io(self, are: ARE):
        self.assertEqual(0, are.unused_id)
        self.assertEqual(0, are.creator_id)
        self.assertEqual("Untitled", are.tag)
        self.assertEqual(75101, are.name.stringref)
        self.assertEqual("comments", are.comment)
        self.assertEqual(0, are.flags)
        self.assertEqual(0, are.mod_spot_check)
        self.assertEqual(0, are.mod_listen_check)
        self.assertEqual(0.20000000298023224, are.alpha_test)
        self.assertEqual(1, are.camera_style)
        self.assertEqual("defaultenvmap", are.default_envmap)
        self.assertEqual("grasstexture", are.grass_texture)
        self.assertEqual(1.0, are.grass_density)
        self.assertEqual(1.0, are.grass_size)
        self.assertEqual(0.25, are.grass_prob_ll)
        self.assertEqual(0.25, are.grass_prob_lr)
        self.assertEqual(0.25, are.grass_prob_ul)
        self.assertEqual(0.25, are.grass_prob_ur)
        self.assertEqual(0, are.moon_ambient)
        self.assertEqual(0, are.moon_diffuse)
        self.assertEqual(0, are.moon_fog)
        self.assertEqual(99.0, are.moon_fog_near)
        self.assertEqual(100.0, are.moon_fog_far)
        self.assertEqual(0, are.moon_fog_color)
        self.assertEqual(0, are.moon_shadows)
        self.assertEqual(1, are.fog_enabled)
        self.assertEqual(99.0, are.fog_near)
        self.assertEqual(100.0, are.fog_far)
        self.assertEqual(1, are.shadows)
        self.assertEqual(0, are.is_night)
        self.assertEqual(0, are.lighting_scheme)
        self.assertEqual(205, are.shadow_opacity)
        self.assertEqual(0, are.day_night)
        self.assertEqual(99, are.chance_rain)
        self.assertEqual(99, are.chance_snow)
        self.assertEqual(99, are.chance_lightning)
        self.assertEqual(1, are.wind_power)
        self.assertEqual(0, are.loadscreen_id)
        self.assertEqual(3, are.player_vs_player)
        self.assertEqual(0, are.no_rest)
        self.assertEqual(0, are.no_hang_back)
        self.assertEqual(0, are.player_only)
        self.assertEqual(1, are.unescapable)
        self.assertEqual(1, are.disable_transit)
        self.assertEqual(1, are.stealth_xp)
        self.assertEqual(25, are.stealth_xp_loss)
        self.assertEqual(25, are.stealth_xp_max)
        self.assertEqual(1, are.dirty_size_1)
        self.assertEqual(1, are.dirty_formula_1)
        self.assertEqual(1, are.dirty_func_1)
        self.assertEqual(1, are.dirty_size_2)
        self.assertEqual(1, are.dirty_formula_2)
        self.assertEqual(1, are.dirty_func_2)
        self.assertEqual(1, are.dirty_size_3)
        self.assertEqual(1, are.dirty_formula_3)
        self.assertEqual(1, are.dirty_func_3)
        self.assertEqual("k_on_enter", are.on_enter)
        self.assertEqual("onexit", are.on_exit)
        self.assertEqual("onheartbeat", are.on_heartbeat)
        self.assertEqual("onuserdefined", are.on_user_defined)

        self.assertEqual(88, are.version)
        self.assertEqual(16777215, are.grass_ambient.bgr_integer())
        self.assertEqual(16777215, are.grass_diffuse.bgr_integer())
        self.assertEqual(16777215, are.sun_ambient.bgr_integer())
        self.assertEqual(16777215, are.sun_diffuse.bgr_integer())
        self.assertEqual(16777215, are.fog_color.bgr_integer())
        self.assertEqual(16777215, are.dynamic_light.bgr_integer())
        self.assertEqual(8060928, are.dirty_argb_1.bgr_integer())
        self.assertEqual(13763584, are.dirty_argb_2.bgr_integer())
        self.assertEqual(3747840, are.dirty_argb_3.bgr_integer())
        # TODO: Fix RGB/BGR mix up


if __name__ == "__main__":
    unittest.main()
