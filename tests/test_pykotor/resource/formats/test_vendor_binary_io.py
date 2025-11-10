from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


REPO_ROOT = Path(__file__).resolve().parents[3]
PYKOTOR_SRC = REPO_ROOT / "Libraries" / "PyKotor" / "src"
UTILITY_SRC = REPO_ROOT / "Libraries" / "Utility" / "src"
for candidate in (PYKOTOR_SRC, UTILITY_SRC):
    candidate_str = str(candidate)
    if candidate.exists() and candidate_str not in sys.path:
        sys.path.append(candidate_str)


from pykotor.common.language import Gender, Language  # type: ignore[import](module)
from pykotor.resource.formats.erf import bytes_erf, read_erf
from pykotor.resource.formats.gff import bytes_gff, read_gff
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.formats.rim import bytes_rim, read_rim
from pykotor.resource.formats.ssf import bytes_ssf, read_ssf
from pykotor.resource.formats.ssf.ssf_data import SSFSound
from pykotor.resource.formats.tlk import bytes_tlk, read_tlk
from pykotor.resource.formats.twoda import bytes_2da, read_2da
from pykotor.resource.type import ResourceType


TEST_FILES = REPO_ROOT / "tests" / "test_pykotor" / "test_files"
MDL_FILES = TEST_FILES / "mdl"


class TestVendorTwoDABinaryIO(TestCase):
    def test_read_and_write(self) -> None:
        data = (TEST_FILES / "test.2da").read_bytes()
        twoda = read_2da(data)
        self._assert_twoda_contents(twoda)

        roundtrip = read_2da(bytes_2da(twoda))
        self._assert_twoda_contents(roundtrip)

    def _assert_twoda_contents(self, twoda) -> None:
        self.assertEqual(twoda.get_headers(), ["col3", "col2", "col1"])

        self.assertEqual(twoda.get_cell(0, "col3"), "ghi")
        self.assertEqual(twoda.get_cell(0, "col2"), "def")
        self.assertEqual(twoda.get_cell(0, "col1"), "abc")

        self.assertEqual(twoda.get_cell(1, "col3"), "123")
        self.assertEqual(twoda.get_cell(1, "col2"), "ghi")
        self.assertEqual(twoda.get_cell(1, "col1"), "def")

        self.assertEqual(twoda.get_cell(2, "col3"), "abc")
        self.assertEqual(twoda.get_cell(2, "col2"), "")
        self.assertEqual(twoda.get_cell(2, "col1"), "123")


class TestVendorERFBinaryIO(TestCase):
    def test_read_and_write(self) -> None:
        data = (TEST_FILES / "test.erf").read_bytes()
        erf = read_erf(data)
        self._assert_erf_contents(erf)

        roundtrip = read_erf(bytes_erf(erf))
        self._assert_erf_contents(roundtrip)

    def _assert_erf_contents(self, erf) -> None:
        npc_data = erf.get("npc", ResourceType.UTC)
        self.assertIsNotNone(npc_data)
        self.assertEqual(npc_data, b"a")

        door_data = erf.get("door", ResourceType.UTD)
        self.assertIsNotNone(door_data)
        self.assertEqual(door_data, b"b")

        sword_data = erf.get("sword", ResourceType.UTI)
        self.assertIsNotNone(sword_data)
        self.assertEqual(sword_data, b"c")


class TestVendorGFFBinaryIO(TestCase):
    def test_read_and_write(self) -> None:
        data = (TEST_FILES / "test.gff").read_bytes()
        gff = read_gff(data)
        self._assert_gff_contents(gff)

        roundtrip = read_gff(bytes_gff(gff))
        self._assert_gff_contents(roundtrip)

    def _assert_gff_contents(self, gff) -> None:
        root = gff.root

        self.assertEqual(root["uint8"], 255)
        self.assertEqual(root["int8"], -128)
        self.assertEqual(root["uint16"], 65535)
        self.assertEqual(root["int16"], -32768)
        self.assertEqual(root["uint32"], 4294967295)
        self.assertEqual(root["int32"], -2147483648)
        self.assertEqual(root["uint64"], 4294967296)
        self.assertEqual(root["int64"], 2147483647)
        self.assertAlmostEqual(root["single"], 12.345669746398926)
        self.assertAlmostEqual(root["double"], 12.345678901234)
        self.assertEqual(root["string"], "abcdefghij123456789")
        self.assertEqual(str(root["resref"]), "resref01")

        position = root["position"]
        self.assertEqual((position.x, position.y, position.z), (11, 22, 33))

        orientation = root["orientation"]
        self.assertEqual((orientation.x, orientation.y, orientation.z, orientation.w), (1, 2, 3, 4))

        locstring = root["locstring"]
        self.assertEqual(locstring.stringref, -1)
        self.assertEqual(locstring.get(Language.ENGLISH, Gender.MALE), "male_eng")
        self.assertEqual(locstring.get(Language.GERMAN, Gender.FEMALE), "fem_german")

        gff_list = root["list"]
        self.assertEqual(len(gff_list), 2)
        self.assertEqual(gff_list[0].struct_id, 1)
        self.assertEqual(gff_list[1].struct_id, 2)

        child_struct = root["child_struct"]
        self.assertEqual(child_struct.struct_id, 0)
        self.assertEqual(child_struct["child_uint8"], 4)


class TestVendorMDLBinaryIO(TestCase):
    def test_read_and_write(self) -> None:
        mdl_path = MDL_FILES / "c_dewback.mdl"
        mdx_path = MDL_FILES / "c_dewback.mdx"

        mdl = read_mdl(mdl_path, source_ext=mdx_path)

        mdl_buffer = bytearray()
        mdx_buffer = bytearray()
        write_mdl(mdl, mdl_buffer, ResourceType.MDL, target_ext=mdx_buffer)

        roundtrip = read_mdl(mdl_buffer, source_ext=mdx_buffer)

        # Ensure the round-trip preserves the geometry.
        self.assertTrue(mdl.compare(roundtrip, lambda *_: None))


class TestVendorRIMBinaryIO(TestCase):
    def test_read_and_write(self) -> None:
        data = (TEST_FILES / "test.rim").read_bytes()
        rim = read_rim(data)
        self._assert_rim_contents(rim)

        roundtrip = read_rim(bytes_rim(rim))
        self._assert_rim_contents(roundtrip)

    def _assert_rim_contents(self, rim) -> None:
        npc_data = rim.get("npc", ResourceType.UTC)
        self.assertIsNotNone(npc_data)
        self.assertEqual(npc_data, b"a")

        door_data = rim.get("door", ResourceType.UTD)
        self.assertIsNotNone(door_data)
        self.assertEqual(door_data, b"b")

        sword_data = rim.get("sword", ResourceType.UTI)
        self.assertIsNotNone(sword_data)
        self.assertEqual(sword_data, b"c")


class TestVendorSSFBinaryIO(TestCase):
    def test_read_and_write(self) -> None:
        data = (TEST_FILES / "test.ssf").read_bytes()
        ssf = read_ssf(data)
        self._assert_ssf_contents(ssf)

        roundtrip = read_ssf(bytes_ssf(ssf))
        self._assert_ssf_contents(roundtrip)

    def _assert_ssf_contents(self, ssf) -> None:
        for offset, sound in enumerate(SSFSound):
            expected = 123075 - offset
            self.assertEqual(ssf.get(sound), expected)


class TestVendorTLKBinaryIO(TestCase):
    def test_read_and_write(self) -> None:
        data = (TEST_FILES / "test.tlk").read_bytes()
        tlk = read_tlk(data)
        self._assert_tlk_contents(tlk)

        roundtrip = read_tlk(bytes_tlk(tlk))
        self._assert_tlk_contents(roundtrip)

    def _assert_tlk_contents(self, tlk) -> None:
        self.assertEqual(tlk.language, Language.ENGLISH)
        self.assertEqual(len(tlk), 3)

        entry0 = tlk.get(0)
        self.assertIsNotNone(entry0)
        self.assertEqual(entry0.text, "abcdef")
        self.assertEqual(str(entry0.voiceover), "resref01")

        entry1 = tlk.get(1)
        self.assertIsNotNone(entry1)
        self.assertEqual(entry1.text, "ghijklmnop")
        self.assertEqual(str(entry1.voiceover), "resref02")

        entry2 = tlk.get(2)
        self.assertIsNotNone(entry2)
        self.assertEqual(entry2.text, "qrstuvwxyz")
        self.assertEqual(str(entry2.voiceover), "")

