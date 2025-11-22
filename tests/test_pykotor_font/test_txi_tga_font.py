from __future__ import annotations

import os
import unittest
import tempfile
import shutil
import warnings

from PIL import Image
from pathlib import Path

from pykotor.common.language import Language
from pykotor.font.draw import write_bitmap_font, write_bitmap_fonts

if __name__ == "__main__":
    os.chdir("./Libraries/PyKotorFont")


FONT_PATH_FILE = Path("tests/test_pykotor_font/test_files/roboto/Roboto-Black.ttf")
CHINESE_FONT_PATH_FILE = Path("tests/test_pykotor_font/test_files/chinese_simplified_ttf/Unifontexmono-AL3RA.ttf")
THAI_FONT_PATH_FILE = Path("tests/test_pykotor_font/test_files/TH Sarabun New Regular/TH Sarabun New Regular.ttf").resolve()


class TestWriteBitmapFont(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test outputs
        self.test_dir: str = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the temporary directory and all its contents
        shutil.rmtree(self.test_dir, ignore_errors=True, onerror=lambda *args: warnings.warn(f"Error removing directory: {args}"))

    def test_bitmap_font(self):
        write_bitmap_fonts(self.test_dir, r"C:\Windows\Fonts\Inkfree.ttf", (2048, 2048), Language.ENGLISH, custom_scaling=1.0, draw_debug_box=True)

    def test_bitmap_font_thai(self):
        write_bitmap_font(Path(self.test_dir) / "test_font_thai.tga", THAI_FONT_PATH_FILE, (2048, 2048), Language.THAI, draw_debug_box=True)

    def test_valid_inputs(self):
        # Test with valid inputs
        target_path: Path = Path(self.test_dir) / "font2.tga"
        resolution: tuple[int, int] = (1024, 1024)
        lang: Language = Language.ENGLISH

        write_bitmap_font(target_path, FONT_PATH_FILE, resolution, lang, draw_debug_box=True)

        # Verify output files were generated
        assert target_path.exists()
        assert target_path.with_suffix(".txi").exists()

        # Verify image file
        img = Image.open(target_path)
        assert img.size == resolution
        assert img.mode == "RGBA"
        img.close()

    def test_invalid_font_path(self):
        # Test with invalid font path
        font_path: Path = Path("invalid.ttf")
        target_path: Path = Path(self.test_dir) / "font.tga"
        resolution: tuple[int, int] = (256, 256)
        lang: Language = Language.ENGLISH

        with self.assertRaises(OSError):
            write_bitmap_font(target_path, font_path, resolution, lang, draw_debug_box=True)

    def test_invalid_language(self):
        # Test with invalid language
        target_path: Path = Path(self.test_dir) / "font.tga"
        resolution: tuple[int, int] = (256, 256)
        lang: str = "invalid"

        with self.assertRaises((AttributeError, ValueError)):
            write_bitmap_font(target_path, FONT_PATH_FILE, resolution, lang, draw_debug_box=True)  # type: ignore[arg-type]

    def test_invalid_resolution(self):
        # Test with invalid resolution
        target_path: Path = Path(self.test_dir) / "font.tga"
        resolution: tuple[int, int] = (0, 0)
        lang: Language = Language.ENGLISH

        with self.assertRaises(ZeroDivisionError):
            write_bitmap_font(target_path, FONT_PATH_FILE, resolution, lang, draw_debug_box=True)


# Edge cases:
# - Resolution is very small or very large
# - Font file contains lots of glyphs
# - Language uses complex script

if __name__ == "__main__":
    try:
        import pytest
    except ImportError:  # pragma: no cover
        unittest.main()
    else:
        pytest.main(["-v", __file__])
