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


from pykotor.common.geometry import Vector2, Vector4
from pykotor.resource.formats.gff import GFF, GFFStruct
from pykotor.common.misc import Color, Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff, GFFComparisonResult, GFFList
from pykotor.resource.generics.gui import GUI, construct_gui, dismantle_gui, GUIControl, GUIControlType, GUIBorder, GUIText, GUIScrollbar, GUIButton, GUISlider, GUIPanel, GUIListBox, GUICheckBox, GUIProtoItem, GUIProgressBar
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.gui import GUI

TEST_FILE_1 = r"C:\GitHub\PyKotor\tests\test_pykotor\test_files\name_x.gui"
TEST_FILE_2 = r"C:\GitHub\PyKotor\tests\test_pykotor\test_files\pazaakgame_p.gui"
TEST_FILE_3 = r"C:\GitHub\PyKotor\tests\test_pykotor\test_files\component_p.gui"
TEST_FILE_4 = r"C:\GitHub\PyKotor\tests\test_pykotor\test_files\inventory_x.gui"
K1_PATH: str | None = os.environ.get("K1_PATH")
K2_PATH: str | None = os.environ.get("K2_PATH")


class TestGUI(TestCase):
    def setUp(self):
        self.log_messages: list[str] = [os.linesep]

    def log_func(self, message=""):
        self.log_messages.append(message)

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for gui_resource in (resource for resource in self.installation if resource.restype() is ResourceType.GUI):
            if gui_resource.identifier() in (
                "abilities.gui",
                "character.gui",
                "container.gui",
                "debug.gui",
            ):
                continue
            print(f"Testing {gui_resource.filename()}")
            gff: GFF = read_gff(gui_resource.data())
            reconstructed_gff: GFF = dismantle_gui(construct_gui(gff), Game.K1)
            assert gff.compare(
                reconstructed_gff,
                self.log_func,
                ignore_default_changes=True,
                ignore_values={"Obj_ParentID": {0}, "CONTROLTYPE": {4, 5, 6, 7}},
            ), os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for gui_resource in (resource for resource in self.installation if resource.restype() is ResourceType.GUI):
            if gui_resource.identifier() in (
                "abilities.gui",
                "character.gui",
                "container.gui",
                "debug.gui",
            ):
                continue
            print(f"Testing {gui_resource.filename()}")
            gff: GFF = read_gff(gui_resource.data())
            reconstructed_gff: GFF = dismantle_gui(construct_gui(gff), Game.K2)
            assert gff.compare(
                reconstructed_gff,
                self.log_func,
                ignore_default_changes=True,
                ignore_values={"Obj_ParentID": {0}, "CONTROLTYPE": {4, 5, 6, 7}},
            ), os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation_comprehensive(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        all_results: list[tuple[str, GFFComparisonResult, GFF]] = []
        
        for gui_resource in (resource for resource in self.installation if resource.restype() is ResourceType.GUI):
            print(f"\nTesting {gui_resource.filename()}")
            gff: GFF = read_gff(gui_resource.data())
            reconstructed_gff: GFF = dismantle_gui(construct_gui(gff))
            result: GFFComparisonResult = gff.compare(
                reconstructed_gff,
                self.log_func,
                ignore_default_changes=True,
                ignore_values={"Obj_ParentID": {0}, "CONTROLTYPE": {4, 5, 6, 7}},
            )
            all_results.append((gui_resource.filename(), result, gff))
            
        # Print comprehensive statistics
        print("\n=== Field Usage Statistics by Control Type ===")
        
        # Initialize stats structure
        control_type_stats = {}
        for control_type in GUIControlType:
            if control_type != GUIControlType.Invalid:
                control_type_stats[control_type] = {
                    "used": {},
                    "missing": {},
                    "extra": {},
                    "mismatched": {},
                    "total_controls": 0
                }
        
        def get_control_type(struct: GFFStruct) -> GUIControlType:
            return GUIControlType(struct.get_int32("CONTROLTYPE", GUIControlType.Control.value))
        
        def process_struct_fields(struct: GFFStruct, control_type: GUIControlType, result: GFFComparisonResult, path: str) -> None:
            control_type_stats[control_type]["total_controls"] += 1
            
            # Process direct fields
            for label, field_type, _ in struct:
                if label in {"CONTROLS"}:  # Skip special fields
                    continue
                    
                # Check if this field was used/missing/extra/mismatched for this path
                field_path = f"{path}\\{label}"
                
                for category in ["used", "missing", "extra", "mismatched"]:
                    if label in result.field_stats[category]:
                        stats = control_type_stats[control_type][category]
                        if label not in stats:
                            stats[label] = {"count": 0, "type": field_type.name}
                        stats[label]["count"] += 1
            
            # Process child controls recursively
            controls_list: GFFList | None = struct.get_list("CONTROLS", None)
            if controls_list:
                for idx, child_struct in enumerate(controls_list):
                    child_type: GUIControlType = get_control_type(child_struct)
                    process_struct_fields(child_struct, child_type, result, f"{path}\\CONTROLS\\{idx}")
        
        # Collect statistics
        for filename, result, gff in all_results:
            process_struct_fields(gff.root, get_control_type(gff.root), result, "GFFRoot")
        
        # Print statistics for each control type
        for control_type in GUIControlType:
            if control_type == GUIControlType.Invalid:
                continue
                
            stats = control_type_stats[control_type]
            if stats["total_controls"] > 0:
                print(f"\n{control_type.name} ({stats['total_controls']} controls):")
                
                for category in ["used", "missing", "extra", "mismatched"]:
                    fields = stats[category]
                    if fields:
                        print(f"\n  {category.upper()} Fields:")
                        for field, data in sorted(fields.items(), key=lambda x: (-x[1]["count"], x[0])):
                            print(f"    {field} ({data['type']}): {data['count']} occurrences")
        
        # Print files with mismatches
        files_with_mismatches: list[tuple[str, GFFComparisonResult]] = [(f, r) for f, r, _ in all_results if not r.is_identical]
        if files_with_mismatches:
            print("\n=== Files with Mismatches ===")
            for filename, result in files_with_mismatches:
                print(f"\n{filename}:")
                if result.struct_id_mismatches:
                    print("  Struct ID Mismatches:")
                    for path, src_id, tgt_id in result.struct_id_mismatches:
                        print(f"    {path}: {src_id} -> {tgt_id}")
                if result.field_count_mismatches:
                    print("  Field Count Mismatches:")
                    for path, src_count, tgt_count in result.field_count_mismatches:
                        print(f"    {path}: {src_count} -> {tgt_count}")
                if result.value_mismatches:
                    print("  Value Mismatches:")
                    for path, field_type, src_val, tgt_val in result.value_mismatches:
                        print(f"    {path} ({field_type}): {src_val} -> {tgt_val}")
        
        # Check for any issues
        has_issues = False
        for control_type in GUIControlType:
            if control_type == GUIControlType.Invalid:
                continue
                
            stats = control_type_stats[control_type]
            if stats["total_controls"] > 0:
                if stats["missing"] or stats["extra"] or stats["mismatched"]:
                    has_issues = True
                    break
        
        # Final assertion
        assert not has_issues, "Some controls have missing, extra, or mismatched fields. See the output above for details."

    def test_gff_reconstruct(self):
        gff: GFF = read_gff(TEST_FILE_1)
        reconstructed_gff: GFF = dismantle_gui(construct_gui(gff), Game.K2)
        assert gff.compare(reconstructed_gff, self.log_func, ignore_default_changes=True), os.linesep.join(self.log_messages)

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

        elif isinstance(root, GUIButton):
            assert isinstance(root.text, str), f"{root.text} is {type(root.text)}"
            assert isinstance(root.text_color, Color), f"{root.text_color} is {type(root.text_color)}"
            assert isinstance(root.border, bool), f"{root.border} is {type(root.border)}"
            assert isinstance(root.pulsing, int), f"{root.pulsing} is {type(root.pulsing)}"

            assert root.text == "", f"{root.text} == ''"
            assert root.text_color == Color(0, 0, 0, 0), f"{root.text_color} == {Color(0, 0, 0, 0)}"
            assert root.border is True, f"{root.border} is True"
            assert root.pulsing == 0, f"{root.pulsing} == 0"

        elif isinstance(root, GUISlider):
            assert isinstance(root.value, float), f"{root.value} is {type(root.value)}"
            assert isinstance(root.min_value, float), f"{root.min_value} is {type(root.min_value)}"
            assert isinstance(root.max_value, float), f"{root.max_value} is {type(root.max_value)}"
            assert isinstance(root.direction, str), f"{root.direction} is {type(root.direction)}"

            assert root.value == 0.0, f"{root.value} == 0.0"
            assert root.min_value == 0.0, f"{root.min_value} == 0.0"
            assert root.max_value == 100.0, f"{root.max_value} == 100.0"
            assert root.direction == "horizontal", f"{root.direction} == 'horizontal'"

        elif isinstance(root, GUIPanel):
            assert isinstance(root.background_texture, (str, type(None))), f"{root.background_texture} is {type(root.background_texture)}"
            assert isinstance(root.border_texture, (str, type(None))), f"{root.border_texture} is {type(root.border_texture)}"

            if root.background_texture:
                assert root.background_texture == "", f"{root.background_texture} == ''"
            if root.border_texture:
                assert root.border_texture == "", f"{root.border_texture} == ''"

        elif isinstance(root, GUIListBox):
            assert isinstance(root.proto_item, (GUIProtoItem, type(None))), f"{root.proto_item} is {type(root.proto_item)}"
            assert isinstance(root.scroll_bar, (GUIScrollbar, type(None))), f"{root.scroll_bar} is {type(root.scroll_bar)}"

        elif isinstance(root, GUICheckBox):
            assert isinstance(root.text, str), f"{root.text} is {type(root.text)}"
            assert isinstance(root.text_color, Color), f"{root.text_color} is {type(root.text_color)}"

            assert root.text == "", f"{root.text} == ''"
            assert root.text_color == Color(0, 0, 0, 0), f"{root.text_color} == {Color(0, 0, 0, 0)}"

        elif isinstance(root, GUIProtoItem):
            assert isinstance(root.gui_text, GUIText), f"{root.gui_text} is {type(root.gui_text)}"
            assert isinstance(root.text_color, Color), f"{root.text_color} is {type(root.text_color)}"
            assert isinstance(root.border, bool), f"{root.border} is {type(root.border)}"
            assert isinstance(root.pulsing, int), f"{root.pulsing} is {type(root.pulsing)}"

            assert root.gui_text.text == "", f"{root.gui_text.text} == ''"
            assert root.text_color == Color(0, 0, 0, 0), f"{root.text_color} == {Color(0, 0, 0, 0)}"
            assert root.border is True, f"{root.border} is True"
            assert root.pulsing == 0, f"{root.pulsing} == 0"

        elif isinstance(root, GUIProgressBar):
            assert isinstance(root.max_value, float), f"{root.max_value} is {type(root.max_value)}"
            assert isinstance(root.progress_fill_texture, str), f"{root.progress_fill_texture} is {type(root.progress_fill_texture)}"
            assert isinstance(root.progress_border, (GUIBorder, type(None))), f"{root.progress_border} is {type(root.progress_border)}"
            
            assert root.progress_fill_texture == "", f"{root.progress_fill_texture} == ''"

            if root.progress_border:
                assert isinstance(root.progress_border.color, Color), f"{root.progress_border.color} is {type(root.progress_border.color)}"
                assert isinstance(root.progress_border.corner, str), f"{root.progress_border.corner} is {type(root.progress_border.corner)}"
                assert isinstance(root.progress_border.dimension, int), f"{root.progress_border.dimension} is {type(root.progress_border.dimension)}"
                assert isinstance(root.progress_border.edge, str), f"{root.progress_border.edge} is {type(root.progress_border.edge)}"
                assert isinstance(root.progress_border.fill, str), f"{root.progress_border.fill} is {type(root.progress_border.fill)}"
                assert isinstance(root.progress_border.fill_style, int), f"{root.progress_border.fill_style} is {type(root.progress_border.fill_style)}"
                assert isinstance(root.progress_border.inner_offset, int), f"{root.progress_border.inner_offset} is {type(root.progress_border.inner_offset)}"
                assert isinstance(root.progress_border.inner_offset_y, int), f"{root.progress_border.inner_offset_y} is {type(root.progress_border.inner_offset_y)}"
                assert isinstance(root.progress_border.pulsing, int), f"{root.progress_border.pulsing} is {type(root.progress_border.pulsing)}"

                assert root.progress_border.color == Color(0, 0, 0, 0), f"{root.progress_border.color} == {Color(0, 0, 0, 0)}"
                assert root.progress_border.corner == "", f"{root.progress_border.corner} == ''"
                assert root.progress_border.dimension == 0, f"{root.progress_border.dimension} == 0"
                assert root.progress_border.edge == "", f"{root.progress_border.edge} == ''"
                assert root.progress_border.fill == "", f"{root.progress_border.fill} == ''"
                assert root.progress_border.fill_style == 0, f"{root.progress_border.fill_style} == 0"
                assert root.progress_border.inner_offset == 0, f"{root.progress_border.inner_offset} == 0"
                assert root.progress_border.inner_offset_y == 0, f"{root.progress_border.inner_offset_y} == 0"
                assert root.progress_border.pulsing == 0, f"{root.progress_border.pulsing} == 0"


if __name__ == "__main__":
    unittest.main()
