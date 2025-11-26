from __future__ import annotations

from io import BytesIO
import os
import pathlib
import pickle
import sys
import unittest
from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")
def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.resource.formats.tpc.tpc_data import TPC
from utility.common.more_collections import CaseInsensitiveDict
from pykotor.common.language import LocalizedString
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath

K1_PATH: str | None = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")


@unittest.skipIf(
    not K1_PATH or not CaseAwarePath(K1_PATH).joinpath("chitin.key").is_file(),
    "K1_PATH environment variable is not set or not found on disk.",
)
class TestInstallation(TestCase):
    @classmethod
    def setUpClass(cls):
        assert K1_PATH
        cls.installation = Installation(K1_PATH)  # type: ignore[attr-defined]
        # cls.installation.reload_all()

    def test_resource(self):
        installation: Installation = self.installation  # type: ignore[attr-defined]

        assert installation.resource("c_bantha", ResourceType.UTC, []) is None
        assert installation.resource("c_bantha", ResourceType.UTC) is not None

        assert installation.resource("c_bantha", ResourceType.UTC, [SearchLocation.CHITIN]) is not None
        assert installation.resource("xxx", ResourceType.UTC, [SearchLocation.CHITIN]) is None
        assert installation.resource("m13aa", ResourceType.ARE, [SearchLocation.MODULES]) is not None
        assert installation.resource("xxx", ResourceType.ARE, [SearchLocation.MODULES]) is None
        assert installation.resource("xxx", ResourceType.NSS, [SearchLocation.OVERRIDE]) is None
        assert installation.resource("NM03ABCITI06004_", ResourceType.WAV, [SearchLocation.VOICE]) is not None
        assert installation.resource("xxx", ResourceType.WAV, [SearchLocation.VOICE]) is None
        assert installation.resource("P_hk47_POIS", ResourceType.WAV, [SearchLocation.SOUND]) is not None
        assert installation.resource("xxx", ResourceType.WAV, [SearchLocation.SOUND]) is None
        assert installation.resource("mus_theme_carth", ResourceType.WAV, [SearchLocation.MUSIC]) is not None
        assert installation.resource("xxx", ResourceType.WAV, [SearchLocation.MUSIC]) is None
        assert installation.resource("n_gendro_coms1", ResourceType.LIP, [SearchLocation.LIPS]) is not None
        assert installation.resource("xxx", ResourceType.LIP, [SearchLocation.LIPS]) is None
        #assert installation.resource("darkjedi", ResourceType.SSF, [SearchLocation.RIMS]) is not None
        #assert installation.resource("xxx", ResourceType.SSF, [SearchLocation.RIMS]) is None
        assert installation.resource("blood", ResourceType.TPC, [SearchLocation.TEXTURES_TPA]) is not None
        assert installation.resource("xxx", ResourceType.TPC, [SearchLocation.TEXTURES_TPA]) is None
        assert installation.resource("blood", ResourceType.TPC, [SearchLocation.TEXTURES_TPB]) is not None
        assert installation.resource("xxx", ResourceType.TPC, [SearchLocation.TEXTURES_TPB]) is None
        assert installation.resource("blood", ResourceType.TPC, [SearchLocation.TEXTURES_TPC]) is not None
        assert installation.resource("xxx", ResourceType.TPC, [SearchLocation.TEXTURES_TPC]) is None
        assert installation.resource("PO_PCarth", ResourceType.TPC, [SearchLocation.TEXTURES_GUI]) is not None
        assert installation.resource("xxx", ResourceType.TPC, [SearchLocation.TEXTURES_GUI]) is None

        resource = installation.resource(
            "m13aa",
            ResourceType.ARE,
            [SearchLocation.CUSTOM_MODULES],
            capsules=[Capsule(installation.module_path() / "danm13.rim")],
        )
        assert resource is not None
        assert resource.data is not None  # type: ignore

    def test_resources(self):
        installation: Installation = self.installation  # type: ignore[attr-defined]

        chitin_resources = [
            ResourceIdentifier.from_path("c_bantha.utc"),
            ResourceIdentifier.from_path("x.utc"),
        ]
        chitin_results = installation.resources(chitin_resources, [SearchLocation.CHITIN])
        self._assert_from_path_tests(chitin_results, "c_bantha.utc", "x.utc")
        modules_resources = [
            ResourceIdentifier.from_path("m01aa.are"),
            ResourceIdentifier.from_path("x.tpc"),
        ]
        modules_results = installation.resources(modules_resources, [SearchLocation.MODULES])
        self._assert_from_path_tests(modules_results, "m01aa.are", "x.tpc")
        voices_resources = [
            ResourceIdentifier.from_path("NM17AE04NI04008_.wav"),
            ResourceIdentifier.from_path("x.mp3"),
        ]
        voices_results = installation.resources(voices_resources, [SearchLocation.VOICE])
        self._assert_from_path_tests(voices_results, "NM17AE04NI04008_.wav", "x.mp3")
        music_resources = [
            ResourceIdentifier.from_path("mus_theme_carth.wav"),
            ResourceIdentifier.from_path("x.mp3"),
        ]
        music_results = installation.resources(music_resources, [SearchLocation.MUSIC])
        self._assert_from_path_tests(music_results, "mus_theme_carth.wav", "x.mp3")
        sounds_resources = [
            ResourceIdentifier.from_path("P_ZAALBAR_POIS.wav"),
            ResourceIdentifier.from_path("x.mp3"),
        ]
        sounds_results = installation.resources(sounds_resources, [SearchLocation.SOUND])
        self._assert_from_path_tests(sounds_results, "P_ZAALBAR_POIS.wav", "x.mp3")
        lips_resources = [
            ResourceIdentifier.from_path("n_gendro_coms1.lip"),
            ResourceIdentifier.from_path("x.lip"),
        ]
        lips_results = installation.resources(lips_resources, [SearchLocation.LIPS])
        self._assert_from_path_tests(lips_results, "n_gendro_coms1.lip", "x.lip")
        #rims_resources = [
        #    ResourceIdentifier.from_path("darkjedi.ssf"),
        #    ResourceIdentifier.from_path("x.ssf"),
        #]
        #rims_results = installation.resources(rims_resources, [SearchLocation.RIMS])
        #self._assert_from_path_tests(rims_results, "darkjedi.ssf", "x.ssf")
        texa_resources = [
            ResourceIdentifier.from_path("blood.tpc"),
            ResourceIdentifier.from_path("x.tpc"),
        ]
        texa_results = installation.resources(texa_resources, [SearchLocation.TEXTURES_TPA])
        self._assert_from_path_tests(texa_results, "blood.tpc", "x.tpc")
        texb_resources = [
            ResourceIdentifier.from_path("blood.tpc"),
            ResourceIdentifier.from_path("x.tpc"),
        ]
        texb_results = installation.resources(texb_resources, [SearchLocation.TEXTURES_TPB])
        self._assert_from_path_tests(texb_results, "blood.tpc", "x.tpc")
        texc_resources = [
            ResourceIdentifier.from_path("blood.tpc"),
            ResourceIdentifier.from_path("x.tpc"),
        ]
        texc_results = installation.resources(texc_resources, [SearchLocation.TEXTURES_TPC])
        self._assert_from_path_tests(texc_results, "blood.tpc", "x.tpc")
        texg_resources = [
            ResourceIdentifier.from_path("1024x768back.tpc"),
            ResourceIdentifier.from_path("x.tpc"),
        ]
        texg_results = installation.resources(texg_resources, [SearchLocation.TEXTURES_GUI])
        self._assert_from_path_tests(texg_results, "1024x768back.tpc", "x.tpc")
        capsules: list[Capsule] = [Capsule(installation.module_path() / "danm13.rim")]
        capsules_resources = [
            ResourceIdentifier.from_path("m13aa.are"),
            ResourceIdentifier.from_path("xyz.ifo"),
        ]
        capsules_results = installation.resources(capsules_resources, [SearchLocation.CUSTOM_MODULES], capsules=capsules)
        self._assert_from_path_tests(capsules_results, "m13aa.are", "xyz.ifo")

    def test_location(self):
        installation: Installation = self.installation  # type: ignore[attr-defined]

        assert not installation.location("m13aa", ResourceType.ARE, [])
        assert installation.location("m13aa", ResourceType.ARE)

        assert installation.location("m13aa", ResourceType.ARE, [SearchLocation.MODULES])

        assert installation.location("c_bantha", ResourceType.UTC, [SearchLocation.CHITIN])
        assert not installation.location("xxx", ResourceType.UTC, [SearchLocation.CHITIN])
        assert installation.location("m13aa", ResourceType.ARE, [SearchLocation.MODULES])
        assert not installation.location("xxx", ResourceType.ARE, [SearchLocation.MODULES])
        assert not installation.location("xxx", ResourceType.NSS, [SearchLocation.OVERRIDE])
        assert installation.location("NM03ABCITI06004_", ResourceType.WAV, [SearchLocation.VOICE])
        assert not installation.location("xxx", ResourceType.WAV, [SearchLocation.VOICE])
        assert installation.location("P_hk47_POIS", ResourceType.WAV, [SearchLocation.SOUND])
        assert not installation.location("xxx", ResourceType.WAV, [SearchLocation.SOUND])
        assert installation.location("mus_theme_carth", ResourceType.WAV, [SearchLocation.MUSIC])
        assert not installation.location("xxx", ResourceType.WAV, [SearchLocation.MUSIC])
        assert installation.location("n_gendro_coms1", ResourceType.LIP, [SearchLocation.LIPS])
        assert not installation.location("xxx", ResourceType.LIP, [SearchLocation.LIPS])
        #assert installation.location("darkjedi", ResourceType.SSF, [SearchLocation.RIMS])
        #assert not installation.location("xxx", ResourceType.SSF, [SearchLocation.RIMS])
        assert installation.location("blood", ResourceType.TPC, [SearchLocation.TEXTURES_TPA])
        assert not installation.location("xxx", ResourceType.TPC, [SearchLocation.TEXTURES_TPA])
        assert installation.location("blood", ResourceType.TPC, [SearchLocation.TEXTURES_TPB])
        assert not installation.location("xxx", ResourceType.TPC, [SearchLocation.TEXTURES_TPB])
        assert installation.location("blood", ResourceType.TPC, [SearchLocation.TEXTURES_TPC])
        assert not installation.location("xxx", ResourceType.TPC, [SearchLocation.TEXTURES_TPC])
        assert installation.location("PO_PCarth", ResourceType.TPC, [SearchLocation.TEXTURES_GUI])
        assert not installation.location("xxx", ResourceType.TPC, [SearchLocation.TEXTURES_GUI])

    def test_locations(self):
        installation: Installation = self.installation  # type: ignore[attr-defined]

        chitin_resources = [
            ResourceIdentifier.from_path("c_bantha.utc"),
            ResourceIdentifier.from_path("x.utc"),
        ]
        chitin_results = installation.locations(chitin_resources, [SearchLocation.CHITIN])
        self._assert_from_path_tests(chitin_results, "c_bantha.utc", "x.utc")
        modules_resources = [
            ResourceIdentifier.from_path("m01aa.are"),
            ResourceIdentifier.from_path("x.tpc"),
        ]
        modules_results = installation.locations(modules_resources, [SearchLocation.MODULES])
        self._assert_from_path_tests(modules_results, "m01aa.are", "x.tpc")
        voices_resources = [
            ResourceIdentifier.from_path("NM17AE04NI04008_.wav"),
            ResourceIdentifier.from_path("x.mp3"),
        ]
        voices_results = installation.locations(voices_resources, [SearchLocation.VOICE])
        self._assert_from_path_tests(voices_results, "NM17AE04NI04008_.wav", "x.mp3")
        music_resources = [
            ResourceIdentifier.from_path("mus_theme_carth.wav"),
            ResourceIdentifier.from_path("x.mp3"),
        ]
        music_results = installation.locations(music_resources, [SearchLocation.MUSIC])
        self._assert_from_path_tests(music_results, "mus_theme_carth.wav", "x.mp3")
        sounds_resources = [
            ResourceIdentifier.from_path("P_ZAALBAR_POIS.wav"),
            ResourceIdentifier.from_path("x.mp3"),
        ]
        sounds_results = installation.locations(sounds_resources, [SearchLocation.SOUND])
        self._assert_from_path_tests(sounds_results, "P_ZAALBAR_POIS.wav", "x.mp3")
        lips_resources = [
            ResourceIdentifier.from_path("n_gendro_coms1.lip"),
            ResourceIdentifier.from_path("x.lip"),
        ]
        lips_results = installation.locations(lips_resources, [SearchLocation.LIPS])
        self._assert_from_path_tests(lips_results, "n_gendro_coms1.lip", "x.lip")
        #rims_resources = [
        #    ResourceIdentifier.from_path("darkjedi.ssf"),
        #    ResourceIdentifier.from_path("x.ssf"),
        #]
        #rims_results = installation.locations(rims_resources, [SearchLocation.RIMS])
        #self._assert_from_path_tests(rims_results, "darkjedi.ssf", "x.ssf")
        texa_resources = [
            ResourceIdentifier.from_path("blood.tpc"),
            ResourceIdentifier.from_path("x.tpc"),
        ]
        texa_results = installation.locations(texa_resources, [SearchLocation.TEXTURES_TPA])
        self._assert_from_path_tests(texa_results, "blood.tpc", "x.tpc")
        texb_resources = [
            ResourceIdentifier.from_path("blood.tpc"),
            ResourceIdentifier.from_path("x.tpc"),
        ]
        texb_results = installation.locations(texb_resources, [SearchLocation.TEXTURES_TPB])
        self._assert_from_path_tests(texb_results, "blood.tpc", "x.tpc")
        texc_resources = [
            ResourceIdentifier.from_path("blood.tpc"),
            ResourceIdentifier.from_path("x.tpc"),
        ]
        texc_results = installation.locations(texc_resources, [SearchLocation.TEXTURES_TPC])
        self._assert_from_path_tests(texc_results, "blood.tpc", "x.tpc")
        texg_resources = [
            ResourceIdentifier.from_path("1024x768back.tpc"),
            ResourceIdentifier.from_path("x.tpc"),
        ]
        texg_results = installation.locations(texg_resources, [SearchLocation.TEXTURES_GUI])
        self._assert_from_path_tests(texg_results, "1024x768back.tpc", "x.tpc")
        capsules = [Capsule(installation.module_path() / "danm13.rim")]
        capsules_resources = [
            ResourceIdentifier.from_path("m13aa.are"),
            ResourceIdentifier.from_path("xyz.ifo"),
        ]
        capsules_results = installation.locations(capsules_resources, [SearchLocation.CUSTOM_MODULES], capsules=capsules)
        self._assert_from_path_tests(capsules_results, "m13aa.are", "xyz.ifo")
        folders = [installation.override_path()]

    def _assert_from_path_tests(
        self,
        results: CaseInsensitiveDict[TPC | None],
        res1: str,
        res2: str,
    ):
        self.assertTrue(results[ResourceIdentifier.from_path(res1)])
        self.assertFalse(results[ResourceIdentifier.from_path(res2)])
        self.assertEqual(2, len(results))

    def test_texture(self):
        installation: Installation = self.installation  # type: ignore[attr-defined]

        assert installation.texture("m03ae_03a_lm4", [SearchLocation.CHITIN]) is not None
        assert installation.texture("x", [SearchLocation.CHITIN]) is None

        assert installation.texture("LEH_FLOOR01", [SearchLocation.TEXTURES_TPA]) is not None
        assert installation.texture("x", [SearchLocation.TEXTURES_TPA]) is None

        assert installation.texture("LEH_Floor01", [SearchLocation.TEXTURES_TPB]) is not None
        assert installation.texture("x", [SearchLocation.TEXTURES_TPB]) is None

        assert installation.texture("leh_floor01", [SearchLocation.TEXTURES_TPC]) is not None
        assert installation.texture("x", [SearchLocation.TEXTURES_TPC]) is None

        assert installation.texture("bluearrow", [SearchLocation.TEXTURES_GUI]) is not None
        assert installation.texture("x", [SearchLocation.TEXTURES_GUI]) is None

    def test_textures(self):
        installation: Installation = self.installation  # type: ignore[attr-defined]

        chitin_textures = ["m03ae_03a_lm4", "x"]
        chitin_results = installation.textures(chitin_textures, [SearchLocation.CHITIN])
        assert chitin_results["m03ae_03a_lm4"] is not None
        assert chitin_results["x"] is None
        assert len(chitin_results) == 2

        tpa_textures = ["LEH_Floor01", "x"]
        tpa_results = installation.textures(tpa_textures, [SearchLocation.TEXTURES_TPA])
        assert tpa_results["leh_floor01"] is not None
        assert tpa_results["x"] is None
        assert len(tpa_results) == 2

        tpb_textures = ["LEH_Floor01", "x"]
        tpb_results = installation.textures(tpb_textures, [SearchLocation.TEXTURES_TPB])
        assert tpb_results["leh_floor01"] is not None
        assert tpb_results["x"] is None
        assert len(tpb_results) == 2

        tpc_textures = ["LEH_Floor01", "x"]
        tpc_results = installation.textures(tpc_textures, [SearchLocation.TEXTURES_TPC])
        assert tpc_results["leh_floor01"] is not None
        assert tpc_results["x"] is None
        assert len(tpc_results) == 2

        gui_textures = ["bluearrow", "x"]
        gui_results = installation.textures(gui_textures, [SearchLocation.TEXTURES_GUI])
        assert gui_results["bluearrow"] is not None
        assert gui_results["x"] is None
        assert len(gui_results) == 2

    def test_sounds(self):
        installation: Installation = self.installation  # type: ignore[attr-defined]

        chitin_sounds = ["as_an_dantext_01", "x"]
        chitin_results = installation.sounds(chitin_sounds, [SearchLocation.CHITIN])
        assert chitin_results["as_an_dantext_01"] is not None
        assert chitin_results["x"] is None

        #rim_sounds = ["FS_metal1", "x"]
        #rim_results = installation.sounds(rim_sounds, [SearchLocation.RIMS])
        #assert rim_results["FS_metal1"] is not None
        #assert rim_results["x"] is None

        sound_sounds = ["al_an_flybuzz_01", "x"]
        sound_results = installation.sounds(sound_sounds, [SearchLocation.SOUND])
        assert sound_results["al_an_flybuzz_01"] is not None
        assert sound_results["x"] is None

        music_sounds = ["al_en_cityext", "x"]
        music_results = installation.sounds(music_sounds, [SearchLocation.MUSIC])
        assert music_results["al_en_cityext"] is not None
        assert music_results["x"] is None

        voice_sounds = ["n_gengamm_scrm", "x"]
        voice_results = installation.sounds(voice_sounds, [SearchLocation.VOICE])
        assert voice_results["n_gengamm_scrm"] is not None
        assert voice_results["x"] is None

    def test_string(self):
        """This test will fail on non-english versions of the game."""
        installation: Installation = self.installation  # type: ignore[attr-defined]

        locstring1 = LocalizedString.from_invalid()
        locstring2 = LocalizedString.from_english("Some text.")
        locstring3 = LocalizedString(2)

        assert installation.string(locstring1, "default text") == "default text"
        assert installation.string(locstring2, "default text") == "Some text."
        assert installation.string(locstring3, "default text") == "ERROR: FATAL COMPILER ERROR"

    def test_strings(self):
        """This test will fail on non-english versions of the game."""
        installation: Installation = self.installation  # type: ignore[attr-defined]

        locstring1 = LocalizedString.from_invalid()
        locstring2 = LocalizedString.from_english("Some text.")
        locstring3 = LocalizedString(2)

        results = installation.strings([locstring1, locstring2, locstring3], "default text")
        assert results[locstring1] == "default text"
        assert results[locstring2] == "Some text."
        assert results[locstring3] == "ERROR: FATAL COMPILER ERROR"  # This test will fail on non-english versions of the game

    def test_pickle_unpickle(self):
        """Test that an Installation object can be pickled and unpickled."""
        pickled_data = pickle.dumps(self.installation)
        unpickled_installation = pickle.loads(pickled_data)
        self.assertEqual(self.installation._path, unpickled_installation._path)

    def test_pickle_to_file(self):
        """Test pickling to and unpickling from a file."""
        with BytesIO() as file:
            pickle.dump(self.installation, file)
            file.seek(0)
            unpickled_installation = pickle.load(file)
            self.assertEqual(self.installation._path, unpickled_installation._path)

    def test_multiple_unpickle(self):
        """Test that multiple unpickling operations yield consistent results."""
        pickled_data = pickle.dumps(self.installation)
        for _ in range(3):
            unpickled_installation = pickle.loads(pickled_data)
            self.assertEqual(self.installation._path, unpickled_installation._path)


if __name__ == "__main__":
    try:
        import pytest
    except ImportError: # pragma: no cover
        unittest.main()
    else:
        pytest.main(["-v", __file__])
