import pathlib
import sys
import unittest

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[3] / "pykotor"
    if pykotor_path.joinpath("__init__.py").exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, str(pykotor_path.parent))

from pykotor.common.language import Language
from pykotor.resource.formats.tpc.txi_data import write_bitmap_font
from pykotor.utility.path import Path

FONT_PATH = Path("tests/files/roboto/Roboto-Black.ttf")
CHINESE_FONT_PATH = Path("tests/files/chinese_simplified_ttf/Unifontexmono-AL3RA.ttf")
THAI_FONT_PATH = Path("tests/files/TH Sarabun New Regular/TH Sarabun New Regular.ttf")

from PIL import Image


class TestWriteBitmapFont(unittest.TestCase):
    def setUp(self):
        #self.output_path = Path(TemporaryDirectory().name)
        self.output_path = Path("./test_bitmap_font_output")
        self.output_path.mkdir(exist_ok=True)
    def cleanUp(self):
        #self.output_path.unlink()
        pass
    def test_bitmap_font(self):
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (256, 256), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (512, 512), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (1024, 1024), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (2048, 2048), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (4096, 4096), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (256, 512), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (512, 1024), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (1024, 2048), Language.ENGLISH)
        write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (2048, 4096), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (128, 512), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (256, 1024), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (512, 2048), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (1024, 4096), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (300, 300), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (600, 600), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (1200, 1200), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (2400, 2400), Language.ENGLISH)
        #write_bitmap_font(self.output_path / "fnt_creditsb", FONT_PATH, (4800, 4800), Language.ENGLISH)
    def test_bitmap_font_chinese(self):
        write_bitmap_font(self.output_path / "test_font_chinese.tga", CHINESE_FONT_PATH, (10240,10240), Language.CHINESE_SIMPLIFIED)
    def test_bitmap_font_thai(self):
        write_bitmap_font(self.output_path / "test_font_thai.tga", THAI_FONT_PATH, (2048,2048), Language.THAI)
    def test_valid_inputs(self) -> None:
        # Test with valid inputs
        target_path = Path("output/font.tga").resolve()
        resolution = (2048, 2048)
        lang = Language.ENGLISH

        write_bitmap_font(target_path, FONT_PATH, resolution, lang)

        # Verify output files were generated
        self.assertTrue(target_path.exists())
        self.assertTrue(target_path.with_suffix(".txi").exists())

        # Verify image file
        img = Image.open(target_path)
        self.assertEqual(img.size, resolution)
        self.assertEqual(img.mode, "RGBA")
        img.close()

    def test_invalid_font_path(self):
        # Test with invalid font path
        font_path = "invalid.ttf"
        target_path = "output/font.tga"
        resolution = (256, 256)
        lang = Language.ENGLISH

        with self.assertRaises(OSError):
            write_bitmap_font(target_path, font_path, resolution, lang)

    def test_invalid_language(self):
        # Test with invalid language
        target_path = "output/font.tga"
        resolution = (256, 256)
        lang = "invalid"

        with self.assertRaises((AttributeError, ValueError)):
            write_bitmap_font(target_path, FONT_PATH, resolution, lang)

    def test_invalid_resolution(self):
        # Test with invalid resolution
        target_path = "output/font.tga"
        resolution = (0, 0)
        lang = Language.ENGLISH

        with self.assertRaises(ZeroDivisionError):
            write_bitmap_font(target_path, FONT_PATH, resolution, lang)

# Edge cases:
# - Resolution is very small or very large
# - Font file contains lots of glyphs
# - Language uses complex script

if __name__ == '__main__':
    unittest.main()
