from __future__ import annotations

import os
import pathlib
import sys
import unittest
from unittest import TestCase

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


from utility.common.geometry import Vector2, Vector4
from pykotor.resource.formats.gff import GFF, GFFStruct
from pykotor.common.misc import Color, Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff, GFFComparisonResult, GFFList
from pykotor.resource.generics.gui import GUI, construct_gui, dismantle_gui, GUIControl, GUIControlType, GUIBorder, GUIText, GUIScrollbar, GUIButton, GUISlider, GUIPanel, GUIListBox, GUICheckBox, GUIProtoItem, GUIProgressBar
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.gui import GUI

TEST_FILE_1 = r"tests\test_pykotor\test_files\name_x.gui"
TEST_FILE_2 = r"tests\test_pykotor\test_files\pazaakgame_p.gui"
TEST_FILE_3 = r"tests\test_pykotor\test_files\component_p.gui"
TEST_FILE_4 = r"tests\test_pykotor\test_files\inventory_x.gui"
K1_PATH: str | None = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH: str | None = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")


class TestGUI(TestCase):
    def setUp(self):
        self.log_messages: list[str] = [os.linesep]

    def log_func(self, message=""):
        self.log_messages.append(message)

    def test_io_construct(self):
        gff: GFF = read_gff(TEST_FILE_1)
        gui: GUI = construct_gui(gff)
        self.validate_io(gui)

    def test_io_reconstruct(self):
        gff: GFF = read_gff(TEST_FILE_1)
        gff = dismantle_gui(construct_gui(gff))
        gui: GUI = construct_gui(gff)
        self.validate_io(gui)

    def validate_io(self, gui: GUI):
        # GUI class validation
        assert isinstance(gui, GUI), f"{gui} is {type(gui)}"
        assert isinstance(gui.tag, str), f"{gui.tag} is {type(gui.tag)}"
        assert isinstance(gui.root, GUIControl), f"{gui.root} is {type(gui.root)}"
        assert isinstance(gui.controls, list), f"{gui.controls} is {type(gui.controls)}"
        assert gui.tag == "", f"{gui.tag} == ''"

        # Root control validation
        root: GUIControl = gui.root
        assert root is not None

        # Basic GUIControl attributes
        assert isinstance(root.gui_type, GUIControlType), f"{root.gui_type} is {type(root.gui_type)}"
        assert isinstance(root.id, (int, type(None))), f"{root.id} is {type(root.id)}"
        assert isinstance(root.tag, str), f"{root.tag} is {type(root.tag)}"
        assert isinstance(root.extent, Vector4), f"{root.extent} is {type(root.extent)}"
        assert isinstance(root._position, Vector2), f"{root._position} is {type(root._position)}"
        assert isinstance(root._size, Vector2), f"{root._size} is {type(root._size)}"
        assert isinstance(root.color, Color), f"{root.color} is {type(root.color)}"
        assert isinstance(root.parent_tag, (str, type(None))), f"{root.parent_tag} is {type(root.parent_tag)}"
        assert isinstance(root.parent_id, (int, type(None))), f"{root.parent_id} is {type(root.parent_id)}"
        assert isinstance(root.locked, (bool, type(None))), f"{root.locked} is {type(root.locked)}"
        assert isinstance(root.font, str), f"{root.font} is {type(root.font)}"
        assert isinstance(root.children, list), f"{root.children} is {type(root.children)}"
        assert isinstance(root.properties, dict), f"{root.properties} is {type(root.properties)}"

        assert root.gui_type == GUIControlType.Panel, f"{root.gui_type} == {GUIControlType.Panel}"
        assert root.id == None, f"{root.id} == None"
        assert root.tag == "TGuiPanel", f"{root.tag} == TGuiPanel"
        assert root.extent == Vector4(0, 0, 0, 0), f"{root.extent} == {Vector4(0, 0, 0, 0)}"
        assert root._position == Vector2(0, 0), f"{root._position} == {Vector2(0, 0)}"
        assert root._size == Vector2(640, 480), f"{root._size} == {Vector2(640, 480)}"
        assert root.color == Color(0, 0, 0, 1), f"{root.color} == {Color(0, 0, 0, 1)}"
        assert root.parent_tag == None, f"{root.parent_tag} == None"
        assert root.parent_id == -1, f"{root.parent_id} == -1"
        assert root.locked is True, f"{root.locked} is True"
        assert root.font == "", f"{root.font} == ''"

        # Border validation
        if root.border:
            assert isinstance(root.border, GUIBorder), f"{root.border} is {type(root.border)}"
            assert isinstance(root.border.color, Color), f"{root.border.color} is {type(root.border.color)}"
            assert isinstance(root.border.corner, str), f"{root.border.corner} is {type(root.border.corner)}"
            assert isinstance(root.border.dimension, int), f"{root.border.dimension} is {type(root.border.dimension)}"
            assert isinstance(root.border.edge, str), f"{root.border.edge} is {type(root.border.edge)}"
            assert isinstance(root.border.fill, str), f"{root.border.fill} is {type(root.border.fill)}"
            assert isinstance(root.border.fill_style, int), f"{root.border.fill_style} is {type(root.border.fill_style)}"
            assert isinstance(root.border.inner_offset, int), f"{root.border.inner_offset} is {type(root.border.inner_offset)}"
            assert isinstance(root.border.inner_offset_y, int), f"{root.border.inner_offset_y} is {type(root.border.inner_offset_y)}"
            assert isinstance(root.border.pulsing, int), f"{root.border.pulsing} is {type(root.border.pulsing)}"

            assert root.border.color == Color(1, 1, 1, 1), f"{root.border.color} == {Color(1, 1, 1, 1)}"
            assert root.border.corner == "", f"{root.border.corner} == ''"
            assert root.border.dimension == 0, f"{root.border.dimension} == 0"
            assert root.border.edge == "", f"{root.border.edge} == ''"
            assert root.border.fill == "pnl_pause_x", f"{root.border.fill} == 'pnl_pause_x'"
            assert root.border.fill_style == 2, f"{root.border.fill_style} == 2"
            assert root.border.inner_offset == 0, f"{root.border.inner_offset} == 0"
            assert root.border.inner_offset_y == 0, f"{root.border.inner_offset_y} == 0"
            assert root.border.pulsing == 0, f"{root.border.pulsing} == 0"

        # Hilight validation
        if root.hilight is not None:
            assert isinstance(root.hilight, GUIBorder), f"{root.hilight} is {type(root.hilight)}"
            assert isinstance(root.hilight.color, Color), f"{root.hilight.color} is {type(root.hilight.color)}"
            assert isinstance(root.hilight.corner, str), f"{root.hilight.corner} is {type(root.hilight.corner)}"
            assert isinstance(root.hilight.dimension, int), f"{root.hilight.dimension} is {type(root.hilight.dimension)}"
            assert isinstance(root.hilight.edge, str), f"{root.hilight.edge} is {type(root.hilight.edge)}"
            assert isinstance(root.hilight.fill, str), f"{root.hilight.fill} is {type(root.hilight.fill)}"
            assert isinstance(root.hilight.fill_style, int), f"{root.hilight.fill_style} is {type(root.hilight.fill_style)}"
            assert isinstance(root.hilight.inner_offset, int), f"{root.hilight.inner_offset} is {type(root.hilight.inner_offset)}"
            assert isinstance(root.hilight.inner_offset_y, int), f"{root.hilight.inner_offset_y} is {type(root.hilight.inner_offset_y)}"
            assert isinstance(root.hilight.pulsing, int), f"{root.hilight.pulsing} is {type(root.hilight.pulsing)}"

            assert root.hilight.color == Color(0, 0, 0, 0), f"{root.hilight.color} == {Color(0, 0, 0, 0)}"
            assert root.hilight.corner == "", f"{root.hilight.corner} == ''"
            assert root.hilight.dimension == 0, f"{root.hilight.dimension} == 0"
            assert root.hilight.edge == "", f"{root.hilight.edge} == ''"
            assert root.hilight.fill == "", f"{root.hilight.fill} == ''"
            assert root.hilight.fill_style == 0, f"{root.hilight.fill_style} == 0"
            assert root.hilight.inner_offset == 0, f"{root.hilight.inner_offset} == 0"
            assert root.hilight.inner_offset_y == 0, f"{root.hilight.inner_offset_y} == 0"
            assert root.hilight.pulsing == 0, f"{root.hilight.pulsing} == 0"

        # Text validation
        if root.gui_text is not None:
            assert isinstance(root.gui_text, GUIText), f"{root.gui_text} is {type(root.gui_text)}"
            assert isinstance(root.gui_text.alignment, int), f"{root.gui_text.alignment} is {type(root.gui_text.alignment)}"
            assert isinstance(root.gui_text.color, Color), f"{root.gui_text.color} is {type(root.gui_text.color)}"
            assert isinstance(root.gui_text.font, str), f"{root.gui_text.font} is {type(root.gui_text.font)}"
            assert isinstance(root.gui_text.pulsing, int), f"{root.gui_text.pulsing} is {type(root.gui_text.pulsing)}"
            assert isinstance(root.gui_text.strref, int), f"{root.gui_text.strref} is {type(root.gui_text.strref)}"
            assert isinstance(root.gui_text.text, str), f"{root.gui_text.text} is {type(root.gui_text.text)}"

            assert root.gui_text.alignment == 0, f"{root.gui_text.alignment} == 0"
            assert root.gui_text.color == Color(0, 0, 0, 1), f"{root.gui_text.color} == {Color(0, 0, 0, 1)}"
            assert root.gui_text.font == "", f"{root.gui_text.font} == ''"
            assert root.gui_text.pulsing == 0, f"{root.gui_text.pulsing} == 0"
            assert root.gui_text.strref == -1, f"{root.gui_text.strref} == -1"
            assert root.gui_text.text == "", f"{root.gui_text.text} == ''"

        for control in root.children:
            if isinstance(control, GUIButton):
                assert isinstance(control.text, (str, type(None))), f"{control.text} is {type(control.text)}"
                assert isinstance(control.color, (Color, type(None))), f"{control.color} is {type(control.color)}"
                assert isinstance(control.border, (GUIBorder, type(None))), f"{control.border} is {type(control.border)}"
                assert isinstance(control.pulsing, (int, type(None))), f"{control.pulsing} is {type(control.pulsing)}"

                assert control.text == None, f"{control.text} == None"
                assert control.color == None, f"{control.color} == None"
                assert control.pulsing == None, f"{control.pulsing} == None"

            elif isinstance(control, GUISlider):
                assert isinstance(control.value, float), f"{control.value} is {type(control.value)}"
                assert isinstance(control.min_value, float), f"{control.min_value} is {type(control.min_value)}"
                assert isinstance(control.max_value, float), f"{control.max_value} is {type(control.max_value)}"
                assert isinstance(control.direction, str), f"{control.direction} is {type(control.direction)}"

                assert control.value == 0.0, f"{control.value} == 0.0"
                assert control.min_value == 0.0, f"{control.min_value} == 0.0"
                assert control.max_value == 100.0, f"{control.max_value} == 100.0"
                assert control.direction == "horizontal", f"{control.direction} == 'horizontal'"

            elif isinstance(control, GUIPanel):
                assert isinstance(control.background_texture, (str, type(None))), f"{control.background_texture} is {type(control.background_texture)}"
                assert isinstance(control.border_texture, (str, type(None))), f"{control.border_texture} is {type(control.border_texture)}"

                if control.background_texture:
                    assert control.background_texture == "", f"{control.background_texture} == ''"
                if control.border_texture:
                    assert control.border_texture == "", f"{control.border_texture} == ''"

            elif isinstance(control, GUIListBox):
                assert isinstance(control.proto_item, (GUIProtoItem, type(None))), f"{control.proto_item} is {type(control.proto_item)}"
                assert isinstance(control.scroll_bar, (GUIScrollbar, type(None))), f"{control.scroll_bar} is {type(control.scroll_bar)}"

            elif isinstance(control, GUICheckBox):
                assert isinstance(control.gui_text, GUIText), f"{control.gui_text} is {type(control.gui_text)}"
                assert isinstance(control.color, Color), f"{control.color} is {type(control.color)}"

                assert control.gui_text.text == "", f"{control.gui_text.text} == ''"
                assert control.color == Color(0, 0, 0, 1), f"{control.color} == {Color(0, 0, 0, 1)}"

            elif isinstance(control, GUIProtoItem):
                assert isinstance(control.gui_text, GUIText), f"{control.gui_text} is {type(control.gui_text)}"
                assert isinstance(control.color, (Color, type(None))), f"{control.color} is {type(control.color)}"
                assert isinstance(control.border, (GUIBorder, type(None))), f"{control.border} is {type(control.border)}"
                assert isinstance(control.pulsing, (int, type(None))), f"{control.pulsing} is {type(control.pulsing)}"

                assert control.gui_text.text in ("Entered Name", None, ""), f"'{control.gui_text.text}' in ('Entered Name', None)"
                assert control.color == None, f"{control.color} == None"
                assert control.pulsing == None, f"{control.pulsing} == None"

            elif isinstance(control, GUIProgressBar):
                assert isinstance(control.max_value, float), f"{control.max_value} is {type(control.max_value)}"
                assert isinstance(control.progress_fill_texture, str), f"{control.progress_fill_texture} is {type(control.progress_fill_texture)}"
                assert isinstance(control.progress_border, (GUIBorder, type(None))), f"{control.progress_border} is {type(control.progress_border)}"
                
                assert control.progress_fill_texture == "", f"{control.progress_fill_texture} == ''"

                if control.progress_border:
                    assert isinstance(control.progress_border.color, Color), f"{control.progress_border.color} is {type(control.progress_border.color)}"
                    assert isinstance(control.progress_border.corner, str), f"{control.progress_border.corner} is {type(control.progress_border.corner)}"
                    assert isinstance(control.progress_border.dimension, int), f"{control.progress_border.dimension} is {type(control.progress_border.dimension)}"
                    assert isinstance(control.progress_border.edge, str), f"{control.progress_border.edge} is {type(control.progress_border.edge)}"
                    assert isinstance(control.progress_border.fill, str), f"{control.progress_border.fill} is {type(control.progress_border.fill)}"
                    assert isinstance(control.progress_border.fill_style, int), f"{control.progress_border.fill_style} is {type(control.progress_border.fill_style)}"
                    assert isinstance(control.progress_border.inner_offset, int), f"{control.progress_border.inner_offset} is {type(control.progress_border.inner_offset)}"
                    assert isinstance(control.progress_border.inner_offset_y, int), f"{control.progress_border.inner_offset_y} is {type(control.progress_border.inner_offset_y)}"
                    assert isinstance(control.progress_border.pulsing, int), f"{control.progress_border.pulsing} is {type(control.progress_border.pulsing)}"

                    assert control.progress_border.color == Color(0, 0, 0, 0), f"{control.progress_border.color} == {Color(0, 0, 0, 0)}"
                    assert control.progress_border.corner == "", f"{control.progress_border.corner} == ''"
                    assert control.progress_border.dimension == 0, f"{control.progress_border.dimension} == 0"
                    assert control.progress_border.edge == "", f"{control.progress_border.edge} == ''"
                    assert control.progress_border.fill == "", f"{control.progress_border.fill} == ''"
                    assert control.progress_border.fill_style == 0, f"{control.progress_border.fill_style} == 0"
                    assert control.progress_border.inner_offset == 0, f"{control.progress_border.inner_offset} == 0"
                    assert control.progress_border.inner_offset_y == 0, f"{control.progress_border.inner_offset_y} == 0"
                    assert control.progress_border.pulsing == 0, f"{control.progress_border.pulsing} == 0"


if __name__ == "__main__":
    unittest.main()
