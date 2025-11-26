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

from typing import TYPE_CHECKING


from pykotor.resource.formats.gff.gff_data import GFF
from pykotor.resource.type import ResourceType
from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.are import ARE, construct_are, dismantle_are

if TYPE_CHECKING:
    from pykotor.resource.formats.gff import GFF
    from pykotor.resource.generics.are import ARE

TEST_FILE = "tests/test_pykotor/test_files/test.are"
K1_PATH: str | None = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH: str | None = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")


class TestARE(unittest.TestCase):
    def setUp(self):
        self.log_messages: list[str] = [os.linesep]

    def log_func(self, message=""):
        self.log_messages.append(message)

    def test_io_construct(self):
        gff: GFF = read_gff(TEST_FILE)
        are: ARE = construct_are(gff)
        self.validate_io(are)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_FILE)
        gff = dismantle_are(construct_are(gff), Game.K2)
        are = construct_are(gff)
        self.validate_io(are)

    def validate_io(self, are: ARE):
        assert are.unused_id == 0, f"{are.unused_id} != 0"
        assert are.creator_id == 0, f"{are.creator_id} != 0"
        assert are.tag == "Untitled", f"{are.tag} != Untitled"
        assert are.name.stringref == 75101, f"{are.name.stringref} != 75101"
        assert are.comment == "comments", f"{are.comment} != comments"
        assert are.flags == 0, f"{are.flags} != 0"
        assert are.mod_spot_check == 0, f"{are.mod_spot_check} != 0"
        assert are.mod_listen_check == 0, f"{are.mod_listen_check} != 0"
        assert are.alpha_test == 0.20000000298023224, f"{are.alpha_test} != 0.20000000298023224"
        assert are.camera_style == 1, f"{are.camera_style} != 1"
        assert are.default_envmap == "defaultenvmap", f"{are.default_envmap} != defaultenvmap"
        assert are.grass_texture == "grasstexture", f"{are.grass_texture} != grasstexture"
        assert are.grass_density == 1.0, f"{are.grass_density} != 1.0"
        assert are.grass_size == 1.0, f"{are.grass_size} != 1.0"
        assert are.grass_prob_ll == 0.25, f"{are.grass_prob_ll} != 0.25"
        assert are.grass_prob_lr == 0.25, f"{are.grass_prob_lr} != 0.25"
        assert are.grass_prob_ul == 0.25, f"{are.grass_prob_ul} != 0.25"
        assert are.grass_prob_ur == 0.25, f"{are.grass_prob_ur} != 0.25"
        assert are.moon_ambient == 0, f"{are.moon_ambient} != 0"
        assert are.moon_diffuse == 0, f"{are.moon_diffuse} != 0"
        assert are.moon_fog == 0, f"{are.moon_fog} != 0"
        assert are.moon_fog_near == 99.0, f"{are.moon_fog_near} != 99.0"
        assert are.moon_fog_far == 100.0, f"{are.moon_fog_far} != 100.0"
        assert are.moon_fog_color == 0, f"{are.moon_fog_color} != 0"
        assert are.moon_shadows == 0, f"{are.moon_shadows} != 0"
        assert are.fog_enabled == 1, f"{are.fog_enabled} != 1"
        assert are.fog_near == 99.0, f"{are.fog_near} != 99.0"
        assert are.fog_far == 100.0, f"{are.fog_far} != 100.0"
        assert are.shadows == 1, f"{are.shadows} != 1"
        assert are.is_night == 0, f"{are.is_night} != 0"
        assert are.lighting_scheme == 0, f"{are.lighting_scheme} != 0"
        assert are.shadow_opacity == 205, f"{are.shadow_opacity} != 205"
        assert are.day_night == 0, f"{are.day_night} != 0"
        assert are.chance_rain == 99, f"{are.chance_rain} != 99"
        assert are.chance_snow == 99, f"{are.chance_snow} != 99"
        assert are.chance_lightning == 99, f"{are.chance_lightning} != 99"
        assert are.wind_power == 1, f"{are.wind_power} != 1"
        assert are.loadscreen_id == 0, f"{are.loadscreen_id} != 0"
        assert are.player_vs_player == 3, f"{are.player_vs_player} != 3"
        assert are.no_rest == 0, f"{are.no_rest} != 0"
        assert are.no_hang_back == 0, f"{are.no_hang_back} != 0"
        assert are.player_only == 0, f"{are.player_only} != 0"
        assert are.unescapable == 1, f"{are.unescapable} != 1"
        assert are.disable_transit == 1, f"{are.disable_transit} != 1"
        assert are.stealth_xp == 1, f"{are.stealth_xp} != 1"
        assert are.stealth_xp_loss == 25, f"{are.stealth_xp_loss} != 25"
        assert are.stealth_xp_max == 25, f"{are.stealth_xp_max} != 25"
        assert are.dirty_size_1 == 1, f"{are.dirty_size_1} != 1"
        assert are.dirty_formula_1 == 1, f"{are.dirty_formula_1} != 1"
        assert are.dirty_func_1 == 1, f"{are.dirty_func_1} != 1"
        assert are.dirty_size_2 == 1, f"{are.dirty_size_2} != 1"
        assert are.dirty_formula_2 == 1, f"{are.dirty_formula_2} != 1"
        assert are.dirty_func_2 == 1, f"{are.dirty_func_2} != 1"
        assert are.dirty_size_3 == 1, f"{are.dirty_size_3} != 1"
        assert are.dirty_formula_3 == 1, f"{are.dirty_formula_3} != 1"
        assert are.dirty_func_3 == 1, f"{are.dirty_func_3} != 1"
        assert are.on_enter == "k_on_enter", f"{are.on_enter} != k_on_enter"
        assert are.on_exit == "onexit", f"{are.on_exit} != onexit"
        assert are.on_heartbeat == "onheartbeat", f"{are.on_heartbeat} != onheartbeat"
        assert are.on_user_defined == "onuserdefined", f"{are.on_user_defined} != onuserdefined"

        assert are.version == 88, f"{are.version} != 88"
        assert are.grass_ambient.bgr_integer() == 16777215, f"{are.grass_ambient.bgr_integer()} != 16777215"
        assert are.grass_diffuse.bgr_integer() == 16777215, f"{are.grass_diffuse.bgr_integer()} != 16777215"
        assert are.sun_ambient.bgr_integer() == 16777215, f"{are.sun_ambient.bgr_integer()} != 16777215"
        assert are.sun_diffuse.bgr_integer() == 16777215, f"{are.sun_diffuse.bgr_integer()} != 16777215"
        assert are.fog_color.bgr_integer() == 16777215, f"{are.fog_color.bgr_integer()} != 16777215"
        assert are.dynamic_light.bgr_integer() == 16777215, f"{are.dynamic_light.bgr_integer()} != 16777215"
        assert are.dirty_argb_1.bgr_integer() == 8060928, f"{are.dirty_argb_1.bgr_integer()} != 8060928"
        assert are.dirty_argb_2.bgr_integer() == 13763584, f"{are.dirty_argb_2.bgr_integer()} != 13763584"
        assert are.dirty_argb_3.bgr_integer() == 3747840, f"{are.dirty_argb_3.bgr_integer()} != 3747840"
        # TODO: Fix RGB/BGR mix up


if __name__ == "__main__":
    unittest.main()
