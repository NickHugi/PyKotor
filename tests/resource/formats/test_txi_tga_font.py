import os
import pathlib
import sys
from tempfile import TemporaryDirectory
import unittest

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[3] / "pykotor"
    if pykotor_path.exists() and str(pykotor_path) not in sys.path:
        sys.path.insert(0, str(pykotor_path.parent))

from pykotor.common.language import Language
from pykotor.resource.formats.tpc.tpc_auto import write_bitmap_font
from pykotor.helpers.path import Path

FONT_PATH = "tests/files/roboto/Roboto-Black.ttf"

unittest.skip("unfinished")
class TestTGA(unittest.TestCase):
    def setUp(self):
        #self.output_path = Path(TemporaryDirectory().name)
        self.output_path = Path("./test_bitmap_font_output")
        self.output_path.mkdir(exist_ok=True)
    def cleanUp(self):
        #self.output_path.unlink()
        pass
    def test_bitmap_font(self):
        write_bitmap_font(self.output_path / "test_font.tga", FONT_PATH, (512,512), Language.ENGLISH)


if __name__ == "__main__":
    unittest.main()
