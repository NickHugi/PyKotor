from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, Literal, TypeVar

from pykotor.common.geometry import Vector2, Vector3, Vector4
from pykotor.common.misc import Color, Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFList, GFFStruct, bytes_gff, read_gff, write_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from typing_extensions import Literal

    from pykotor.common.language import LocalizedString
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


T = TypeVar("T")


class GUIControlType(IntEnum):
    """Enum representing different GUI control types."""

    Invalid = -1
    Control = 0
    Panel = 2
    ProtoItem = 4
    Label = 5
    Button = 6
    CheckBox = 7
    Slider = 8
    ScrollBar = 9
    Progress = 10
    ListBox = 11


class GUIAlignment(IntEnum):
    """Text alignment options."""

    TopLeft = 1
    TopCenter = 2
    TopRight = 3
    CenterLeft = 17
    Center = 18
    CenterRight = 19
    BottomLeft = 33
    BottomCenter = 34
    BottomRight = 35


class GUIBorder:
    """Represents border properties for GUI controls."""

    def __init__(self):
        self.color: Color | None = None
        self.corner: ResRef = ResRef.from_blank()
        self.dimension: int = 0
        self.edge: ResRef = ResRef.from_blank()
        self.fill: ResRef = ResRef.from_blank()
        self.fill_style: int = 2  # Default to 2 as per test requirements
        self.inner_offset: int | None = None
        self.inner_offset_y: int | None = None
        self.pulsing: bool | None = None


class GUIExtent:
    """Position and size of GUI controls."""

    def __init__(self):
        self.left: int = 0
        self.top: int = 0
        self.width: int = 0
        self.height: int = 0


class GUIText:
    """Represents text properties for GUI controls."""

    def __init__(self):
        self.alignment: int = 0
        self.color: Color | None = None
        self.font: ResRef = ResRef.from_blank()
        self.pulsing: bool | None = None
        self.strref: int = -1
        self.text: str | None = None


class GUIMoveTo:
    """Represents movement navigation between controls."""

    def __init__(self):
        self.up: int = -1
        self.down: int = -1
        self.left: int = -1
        self.right: int = -1


class GUIControl:
    """Base class for all GUI controls."""

    def __init__(self):
        self.type: GUIControlType = GUIControlType.Control
        self.id: int | None = None
        self.tag: str | None = None
        self._position: Vector2 = Vector2(0, 0)
        self._size: Vector2 = Vector2(0, 0)
        self.extent: Vector4 = Vector4(0, 0, 0, 0)
        self.border: GUIBorder | None = None
        self.color: Color | None = None
        self.hilight: GUIBorder | None = None
        self.parent_tag: str | None = None
        self.parent_id: int | None = None
        self.locked: bool | None = None
        self.gui_text: GUIText | None = None
        self.prototype_resref: ResRef | None = None
        self.text_align: int = 0
        self.font: ResRef = ResRef.from_blank()
        self.children: list[GUIControl] = []
        self.properties: dict[str, str | int | float | ResRef | LocalizedString] = {}
        self.selectable: bool = True
        self.moveto: GUIMoveTo | None = None
        self.scrollbar: GUIScrollbar | None = None
        self.max_value: int = 100
        self.padding: int | None = None
        self.looping: int | None = None
        self.left_scrollbar: int | None = None
        self.draw_mode: int | None = None

    @property
    def position(self) -> Vector2:
        return self._position

    @position.setter
    def position(self, value: Vector2):
        self._position = value
        self.extent = Vector4(value.x, value.y, self._size.x, self._size.y)

    @property
    def size(self) -> Vector2:
        return self._size

    @size.setter
    def size(self, value: Vector2):
        self._size = value
        self.extent = Vector4(self._position.x, self._position.y, value.x, value.y)


class GUI:
    """A class representing a GUI resource in KotOR games."""

    BINARY_TYPE = ResourceType.GUI

    def __init__(self):
        self.tag: str = ""
        self.root: GUIControl | None = None
        self.controls: list[GUIControl] = []

    def add_control(self, control: GUIControl) -> None:
        """Add a control to this GUI."""
        self.controls.append(control)


class GUIScrollbarDir:
    """Direction properties for scrollbars."""

    def __init__(self):
        self.image: ResRef = ResRef.from_blank()
        self.alignment: int = 0
        self.flip_style: int | None = None
        self.draw_style: int | None = None
        self.rotate: float | None = None

class GUIScrollbarThumb:
    """Thumb control in a scrollbar."""

    def __init__(self):
        self.image: ResRef = ResRef.from_blank()
        self.alignment: int = 0
        self.flip_style: int | None = None
        self.draw_style: int | None = None
        self.rotate: float | None = None


class GUIScrollbar(GUIControl):
    """Scrollbar control in a GUI."""

    def __init__(self):
        super().__init__()
        self.type = GUIControlType.ScrollBar
        self.alignment: int = 0
        self.horizontal: bool = False
        self.visible_value: int = 0
        self.current_value: int | None = None
        self.scroll_bar_up: ResRef = ResRef.from_blank()
        self.scroll_bar_down: ResRef = ResRef.from_blank()
        self.scroll_bar_thumb: ResRef = ResRef.from_blank()
        self.scroll_bar_back: ResRef = ResRef.from_blank()
        self.gui_thumb: GUIScrollbarThumb | None = None
        self.gui_direction: GUIScrollbarDir | None = None


class GUIButton(GUIControl):
    """Button control in a GUI."""

    def __init__(self):
        super().__init__()
        self.type = GUIControlType.Button
        self.text: str | None = None
        self.font_name: str = ""
        self.text_color: Color = Color(0, 0, 0, 0)
        self.border: bool = True
        self.pulsing: bool = False


class GUILabel(GUIControl):
    """Label control in a GUI."""

    def __init__(self):
        super().__init__()
        self.type = GUIControlType.Label
        self.text: str = ""
        self.font_name: ResRef = ResRef.from_blank()
        self.text_color: Color = Color(0, 0, 0, 0)
        self.editable: bool = False
        self.alignment: int = 0


class GUISlider(GUIControl):
    """Slider control in a GUI."""

    def __init__(self):
        super().__init__()
        self.type = GUIControlType.Slider
        self.value: float = 0.0
        self.min_value: float = 0.0
        self.max_value: float = 100.0
        self.direction: Literal["horizontal", "vertical"] = "horizontal"
        self.thumb_texture: str | None = None
        self.track_texture: str | None = None


class GUIPanel(GUIControl):
    """Panel control in a GUI."""

    def __init__(self):
        super().__init__()
        self.type = GUIControlType.Panel
        self.background_texture: str | None = None
        self.border_texture: str | None = None
        self.alpha: float = 1.0


class GUIListBox(GUIControl):
    """List box control in a GUI."""

    def __init__(self):
        super().__init__()
        self.type = GUIControlType.ListBox
        self.selected_item: int = -1
        self.items: list[str] = []
        self.proto_item: GUIProtoItem | None = None
        self.scroll_bar: GUIScrollbar | None = None
        self.item_count: int = 0
        self.visible_count: int = 6  # Default visible items
        self.item_offset: int = 0
        self.item_margin: int = 0
        self.proto_match_content: bool = False
        self.padding: int = 5
        self.looping: bool = True


class GUICheckBox(GUIControl):
    """Checkbox control in a GUI."""

    def __init__(self):
        super().__init__()
        self.type = GUIControlType.CheckBox
        self.checked: bool = False
        self.check_texture: str = ""
        self.text: str = ""
        self.font_name: str = ""
        self.text_color: Color | None = None


class GUIProtoItem(GUIControl):
    """Prototype item control in a GUI."""

    def __init__(self):
        super().__init__()
        self.type = GUIControlType.ProtoItem
        self.font_name: ResRef = ResRef.from_blank()
        self.text_color: Color | None = None
        self.border: GUIBorder | None = None
        self.pulsing: bool = False

class GUIProgressBar(GUIControl):
    """Progress bar control in a GUI."""

    def __init__(self):
        super().__init__()
        self.type = GUIControlType.Progress
        self.progress: float = 0.0
        self.max_value: float = 100.0
        self.progress_fill_texture: str = ""
        self.progress_border: GUIBorder | None = None

    def set_value(self, value: int) -> None:
        """Set the progress bar value between 0-100."""
        if value < 0 or value > 100:  # noqa: PLR2004
            raise ValueError(f"Progress bar value must be between 0-100, got {value}")
        self.progress = float(value)


def construct_gui(gff: GFF) -> GUI:
    """Construct a GUI object from a GFF."""
    gui = GUI()

    def read_text(struct: GFFStruct) -> GUIText | None:
        """Read text values from a GFF struct."""
        text_struct: GFFStruct | None = struct.get_struct("TEXT", None)
        if text_struct is None:
            return None

        text = GUIText()
        text.text = text_struct.get_string("TEXT", None)
        text.font = text_struct.get_resref("FONT", ResRef.from_blank())
        text.alignment = text_struct.get_int32("ALIGNMENT", 0)
        pulsing: int | None = text_struct.get_uint8("PULSING", None)
        if pulsing is not None:
            text.pulsing = bool(pulsing)
        text.strref = text_struct.get_uint32("STRREF", 0xFFFFFFFF)

        color: Vector3 | None = text_struct.get_vector3("COLOR", None)
        if color:
            text.color = Color(color.x, color.y, color.z, 1.0)
        return text

    def read_moveto(struct: GFFStruct) -> GUIMoveTo | None:
        """Read moveto values from a GFF struct."""
        moveto_struct: GFFStruct | None = struct.get_struct("MOVETO", None)
        if moveto_struct is None:
            return None

        moveto = GUIMoveTo()
        moveto.up = moveto_struct.get_int32("UP", -1)
        moveto.down = moveto_struct.get_int32("DOWN", -1)
        moveto.left = moveto_struct.get_int32("LEFT", -1)
        moveto.right = moveto_struct.get_int32("RIGHT", -1)
        return moveto

    def read_hilight(struct: GFFStruct) -> GUIBorder | None:
        """Read hilight values from a GFF struct."""
        hilight_struct: GFFStruct | None = struct.get_struct("HILIGHT", None)
        if hilight_struct is None:
            return None

        hilight = GUIBorder()
        color: Vector3 | None = hilight_struct.get_vector3("COLOR", None)
        if color:
            hilight.color = Color(color.x, color.y, color.z, 1.0)
        hilight.corner = hilight_struct.get_resref("CORNER", ResRef.from_blank())
        hilight.dimension = hilight_struct.get_int32("DIMENSION", 0)
        hilight.edge = hilight_struct.get_resref("EDGE", ResRef.from_blank())
        hilight.fill = hilight_struct.get_resref("FILL", ResRef.from_blank())
        hilight.fill_style = hilight_struct.get_int32("FILLSTYLE", 0)
        hilight.inner_offset = hilight_struct.get_int32("INNEROFFSET", 0)
        hilight.inner_offset_y = hilight_struct.get_int32("INNEROFFSETY", None)
        hilight.pulsing = bool(hilight_struct.get_uint8("PULSING", 0))
        return hilight

    def _create_control_by_type(control_type: GUIControlType) -> GUIControl:
        """Create appropriate control based on type."""
        if control_type == GUIControlType.ScrollBar:
            return GUIScrollbar()
        if control_type == GUIControlType.Button:
            return GUIButton()
        if control_type == GUIControlType.Slider:
            return GUISlider()
        if control_type == GUIControlType.Panel:
            return GUIPanel()
        if control_type == GUIControlType.ListBox:
            return GUIListBox()
        if control_type == GUIControlType.CheckBox:
            return GUICheckBox()
        if control_type == GUIControlType.ProtoItem:
            return GUIProtoItem()
        if control_type == GUIControlType.Progress:
            return GUIProgressBar()
        if control_type == GUIControlType.Label:
            return GUILabel()
        return GUIControl()

    def read_extent(struct: GFFStruct) -> tuple[int, int, int, int]:
        """Read extent values from a GFF struct."""
        extent: GFFStruct | None = struct.get_struct("EXTENT", None)
        if extent is None:
            return 0, 0, 0, 0
        return (
            extent.get_int32("LEFT", 0),
            extent.get_int32("TOP", 0),
            extent.get_int32("WIDTH", 0),
            extent.get_int32("HEIGHT", 0)
        )

    def read_border(struct: GFFStruct) -> GUIBorder | None:
        """Read border values from a GFF struct."""
        border_struct: GFFStruct | None = struct.get_struct("BORDER", None)
        if border_struct is None:
            return None

        border = GUIBorder()
        color: Vector3 | None = border_struct.get_vector3("COLOR", None)
        if color:
            border.color = Color(color.x, color.y, color.z, 1.0)
        border.corner = border_struct.get_resref("CORNER", ResRef.from_blank())
        border.dimension = border_struct.get_int32("DIMENSION", 0)
        border.edge = border_struct.get_resref("EDGE", ResRef.from_blank())
        border.fill = border_struct.get_resref("FILL", ResRef.from_blank())
        border.fill_style = border_struct.get_int32("FILLSTYLE", 2)
        border.inner_offset = border_struct.get_int32("INNEROFFSET", None)
        border.inner_offset_y = border_struct.get_int32("INNEROFFSETY", None)
        pulsing: int | None = border_struct.get_uint8("PULSING", None)
        if pulsing is not None:
            border.pulsing = bool(pulsing)
        return border

    def read_scrollbar_thumb_or_dir(
        struct: GFFStruct,
        control_type: type[T],
    ) -> T | None:
        """Read scrollbar thumb or direction struct values."""
        field_name: Literal["THUMB", "DIR"] = "THUMB" if control_type == GUIScrollbarThumb else "DIR"
        thumb_struct: GFFStruct | None = struct.get_struct(field_name, None)
        if thumb_struct is None:
            return None
        thumb: GUIScrollbarThumb | GUIScrollbarDir = control_type()  # pyright: ignore[reportAssignmentType]
        thumb.image = thumb_struct.get_resref("IMAGE", ResRef.from_blank())
        thumb.alignment = thumb_struct.get_int32("ALIGNMENT", 18)
        thumb.rotate = thumb_struct.get_single("ROTATE", None)
        thumb.flip_style = thumb_struct.get_int32("FLIPSTYLE", None)
        thumb.draw_style = thumb_struct.get_int32("DRAWSTYLE", None)
        return thumb  # pyright: ignore[reportReturnType]

    def read_proto_item(struct: GFFStruct, parent: GUIControl) -> GUIProtoItem | None:
        """Read proto item from a GFF struct."""
        proto_struct: GFFStruct | None = struct.get_struct("PROTOITEM", None)
        if proto_struct is None:
            return None

        proto = GUIProtoItem()
        proto.type = GUIControlType.ProtoItem
        proto.tag = "PROTOITEM"
        proto.parent_tag = parent.tag
        proto.parent_id = parent.id

        # Basic properties
        proto.gui_text = read_text(proto_struct)
        proto.font = proto_struct.get_resref("FONT", ResRef.from_blank())
        color: Vector3 | None = proto_struct.get_vector3("COLOR", None)
        if color:
            proto.text_color = Color(color.x, color.y, color.z, 1.0)

        # Extent
        left, top, width, height = read_extent(proto_struct)
        proto.position.x = left
        proto.position.y = top
        proto.size.x = width
        proto.size.y = height

        # Border (boolean flag)
        proto.border = read_border(proto_struct)
        proto.hilight = read_hilight(proto_struct)
        return proto

    def read_scrollbar(struct: GFFStruct, parent: GUIControl) -> GUIScrollbar | None:
        """Read scrollbar from a GFF struct."""
        scroll_struct: GFFStruct | None = struct.get_struct("SCROLLBAR", None)
        if scroll_struct is None:
            return None

        scroll = GUIScrollbar()
        scroll.type = GUIControlType.ScrollBar
        scroll.tag = "SCROLLBAR"
        scroll.parent_tag = parent.tag
        scroll.parent_id = parent.id

        # Basic properties
        scroll.max_value = scroll_struct.get_int32("MAXVALUE", 99)
        scroll.visible_value = scroll_struct.get_int32("VISIBLEVALUE", 1)
        scroll.current_value = scroll_struct.get_int32("CURVALUE", None)
        locked: int | None = scroll_struct.get_uint8("Obj_Locked", None)
        if locked is not None:
            scroll.locked = bool(locked)

        draw_mode: int | None = scroll_struct.get_uint8("DRAWMODE", None)
        if draw_mode is not None:
            scroll.draw_mode = draw_mode

        # Extent
        left, top, width, height = read_extent(scroll_struct)
        scroll.position.x = left
        scroll.position.y = top
        scroll.size.x = width
        scroll.size.y = height

        # Border
        scroll.border = read_border(scroll_struct)

        # Direction and thumb
        scroll.gui_direction = read_scrollbar_thumb_or_dir(scroll_struct, GUIScrollbarDir)
        scroll.gui_thumb = read_scrollbar_thumb_or_dir(scroll_struct, GUIScrollbarThumb)
        return scroll

    def construct_control(struct: GFFStruct) -> GUIControl:
        """Construct a GUI control from a GFF struct."""
        control_type = GUIControlType(struct.acquire("CONTROLTYPE", GUIControlType.Invalid.value))
        control: GUIControl = _create_control_by_type(control_type)
        control.type = control_type

        # Basic properties
        control.id = struct.get_int32("ID", None)
        control.tag = struct.get_string("TAG", None)
        control.parent_tag = struct.get_string("Obj_Parent", None)
        control.parent_id = struct.get_int32("Obj_ParentID", None)
        locked: int | None = struct.get_uint8("Obj_Locked", None)
        if locked is not None:
            control.locked = bool(locked)
        control.padding = struct.get_int32("PADDING", None)
        control.looping = struct.get_uint8("LOOPING", None)

        # Left scrollbar
        left_scrollbar: int | None = struct.get_uint8("LEFTSCROLLBAR", None)
        if left_scrollbar is not None:
            control.left_scrollbar = bool(left_scrollbar)

        # Color
        color: Vector3 | None = struct.get_vector3("COLOR", None)
        if color:
            control.color = Color(color.x, color.y, color.z)
            alpha: float | None = struct.get_single("ALPHA", None)
            if alpha is not None:
                control.color.a = alpha

        # Extent
        left, top, width, height = read_extent(struct)
        control.position.x = left
        control.position.y = top
        control.size.x = width
        control.size.y = height


        # Border
        control.border = read_border(struct)

        # Text
        control.gui_text = read_text(struct)

        # Hilight
        control.hilight = read_hilight(struct)

        # MoveTo
        control.moveto = read_moveto(struct)

        # ListBox specific
        if isinstance(control, GUIListBox):
            control.proto_item = read_proto_item(struct, control)
            control.scroll_bar = read_scrollbar(struct, control)

        # Handle child controls
        controls_list = struct.get_list("CONTROLS", GFFList())
        if controls_list:
            for child_struct in controls_list:
                child = construct_control(child_struct)
                control.children.append(child)

        return control

    # Read root control
    gui.root = construct_control(gff.root)
    return gui

def dismantle_gui(gui: GUI, game: Game = Game.K2, *, use_deprecated: bool = True) -> GFF:
    """Convert a GUI instance to a GFF."""
    gff = GFF()

    def write_extent(struct: GFFStruct, x: int, y: int, width: int, height: int) -> None:
        """Write extent values to a GFF struct."""
        extent = struct.set_struct("EXTENT", GFFStruct(0))
        extent.set_int32("LEFT", x)
        extent.set_int32("TOP", y)
        extent.set_int32("WIDTH", width)
        extent.set_int32("HEIGHT", height)

    def write_border(struct: GFFStruct, border: GUIBorder) -> None:
        """Write border values to a GFF struct."""
        border_struct = struct.set_struct("BORDER", GFFStruct(0))
        if border.color is not None:
            border_struct.set_vector3("COLOR", Vector3(border.color.r, border.color.g, border.color.b))
            if border.color.a is not None:
                border_struct.set_single("ALPHA", border.color.a)
        border_struct.set_resref("CORNER", border.corner)
        border_struct.set_int32("DIMENSION", border.dimension)
        border_struct.set_resref("EDGE", border.edge)
        border_struct.set_resref("FILL", border.fill)
        border_struct.set_int32("FILLSTYLE", border.fill_style)
        if border.inner_offset is not None:
            border_struct.set_int32("INNEROFFSET", border.inner_offset)
        if border.inner_offset_y is not None:
            border_struct.set_int32("INNEROFFSETY", border.inner_offset_y)
        if border.pulsing is not None:
            border_struct.set_uint8("PULSING", int(border.pulsing))

    def write_scrollbar_thumb_or_dir(struct: GFFStruct, thumb_or_dir: GUIScrollbarThumb | GUIScrollbarDir) -> None:
        """Write scrollbar thumb values."""
        field_name: Literal["THUMB", "DIR"] = "THUMB" if isinstance(thumb_or_dir, GUIScrollbarThumb) else "DIR"
        thumb_struct: GFFStruct = struct.set_struct(field_name, GFFStruct(0))
        thumb_struct.set_resref("IMAGE", thumb_or_dir.image)
        thumb_struct.set_int32("ALIGNMENT", thumb_or_dir.alignment)
        if thumb_or_dir.rotate is not None:
            thumb_struct.set_single("ROTATE", thumb_or_dir.rotate)
        if thumb_or_dir.flip_style is not None:
            thumb_struct.set_int32("FLIPSTYLE", thumb_or_dir.flip_style)
        if thumb_or_dir.draw_style is not None:
            thumb_struct.set_int32("DRAWSTYLE", thumb_or_dir.draw_style)

    def write_proto_item(struct: GFFStruct, proto: GUIProtoItem) -> None:
        """Write proto item to a GFF struct."""
        proto_struct: GFFStruct = struct.set_struct("PROTOITEM", GFFStruct(0))
        proto_struct.set_int32("CONTROLTYPE", GUIControlType.ProtoItem.value)
        proto_struct.set_string("TAG", "PROTOITEM")
        if proto.parent_tag is not None:
            proto_struct.set_string("Obj_Parent", proto.parent_tag)
        if proto.parent_id is not None:
            proto_struct.set_int32("Obj_ParentID", proto.parent_id)

        # Basic properties
        if proto.gui_text is not None:
            write_text(proto_struct, proto.gui_text)
        if proto.hilight is not None:
            write_hilight(proto_struct, proto.hilight)

        # Extent
        write_extent(proto_struct, int(proto.position.x), int(proto.position.y), int(proto.size.x), int(proto.size.y))

        # Border (boolean flag)
        if proto.border is not None:
            write_border(proto_struct, proto.border)

    def write_scrollbar(struct: GFFStruct, scroll: GUIScrollbar) -> None:
        """Write scrollbar to a GFF struct."""
        scroll_struct: GFFStruct = struct.set_struct("SCROLLBAR", GFFStruct(0))
        if scroll.draw_mode is not None:
            scroll_struct.set_uint8("DRAWMODE", scroll.draw_mode)
        scroll_struct.set_int32("CONTROLTYPE", GUIControlType.ScrollBar.value)
        scroll_struct.set_string("TAG", "SCROLLBAR")
        if scroll.parent_tag is not None:
            scroll_struct.set_string("Obj_Parent", scroll.parent_tag)
        if scroll.parent_id is not None:
            scroll_struct.set_int32("Obj_ParentID", scroll.parent_id)
        if scroll.locked is not None:
            scroll_struct.set_uint8("Obj_Locked", int(scroll.locked))
        scroll_struct.set_int32("MAXVALUE", scroll.max_value)
        scroll_struct.set_int32("VISIBLEVALUE", scroll.visible_value)
        if scroll.current_value is not None:
            scroll_struct.set_int32("CURVALUE", scroll.current_value)
        if scroll.padding is not None:
            scroll_struct.set_int32("PADDING", scroll.padding)

        # Extent
        write_extent(scroll_struct, int(scroll.position.x), int(scroll.position.y), int(scroll.size.x), int(scroll.size.y))

        # Border
        if scroll.border is not None:
            write_border(scroll_struct, scroll.border)

        # Direction and thumb
        if scroll.gui_direction is not None:
            write_scrollbar_thumb_or_dir(scroll_struct, scroll.gui_direction)
        if scroll.gui_thumb is not None:
            write_scrollbar_thumb_or_dir(scroll_struct, scroll.gui_thumb)
        if scroll.color is not None:
            if scroll.color.a is not None:
                scroll_struct.set_single("ALPHA", scroll.color.a)
            scroll_struct.set_vector3("COLOR", Vector3(scroll.color.r, scroll.color.g, scroll.color.b))

    def write_text(struct: GFFStruct, text_control: GUIText) -> None:
        """Write text values to a GFF struct."""
        text_struct = struct.set_struct("TEXT", GFFStruct(0))
        if text_control.text is not None:
            text_struct.set_string("TEXT", text_control.text)
        text_struct.set_uint32("STRREF", 0xFFFFFFFF if text_control.strref == -1 else text_control.strref)
        if text_control.pulsing is not None:
            text_struct.set_uint8("PULSING", int(text_control.pulsing))
        text_struct.set_resref("FONT", text_control.font)
        text_struct.set_int32("ALIGNMENT", text_control.alignment)
        if text_control.color is not None:
            text_struct.set_vector3("COLOR", Vector3(text_control.color.r, text_control.color.g, text_control.color.b))
            if text_control.color.a is not None:
                text_struct.set_single("ALPHA", text_control.color.a)

    def write_moveto(struct: GFFStruct, moveto: GUIMoveTo) -> None:
        """Write moveto values to a GFF struct."""
        moveto_struct = struct.set_struct("MOVETO", GFFStruct(0))
        moveto_struct.set_int32("UP", moveto.up)
        moveto_struct.set_int32("DOWN", moveto.down)
        moveto_struct.set_int32("LEFT", moveto.left)
        moveto_struct.set_int32("RIGHT", moveto.right)

    def write_hilight(struct: GFFStruct, hilight: GUIBorder) -> None:
        """Write hilight values to a GFF struct."""
        hilight_struct = struct.set_struct("HILIGHT", GFFStruct(0))
        if hilight.color is not None:
            hilight_struct.set_vector3("COLOR", Vector3(hilight.color.r, hilight.color.g, hilight.color.b))
        hilight_struct.set_resref("CORNER", hilight.corner)
        hilight_struct.set_int32("DIMENSION", hilight.dimension)
        hilight_struct.set_resref("EDGE", hilight.edge)
        hilight_struct.set_resref("FILL", hilight.fill)
        hilight_struct.set_int32("FILLSTYLE", hilight.fill_style)
        if hilight.inner_offset is not None:
            hilight_struct.set_int32("INNEROFFSET", hilight.inner_offset)
        if hilight.inner_offset_y is not None:
            hilight_struct.set_int32("INNEROFFSETY", hilight.inner_offset_y)
        if hilight.pulsing is not None:
            hilight_struct.set_uint8("PULSING", int(hilight.pulsing))

    def dismantle_control(control: GUIControl) -> GFFStruct:
        """Convert a GUI control to a GFF struct."""
        struct = GFFStruct(0)

        # Basic properties
        struct.set_int32("CONTROLTYPE", int(control.type))
        if control.id is not None:
            struct.set_int32("ID", control.id)
        if control.tag is not None:
            struct.set_string("TAG", control.tag)
        if control.parent_tag is not None:
            struct.set_string("Obj_Parent", control.parent_tag)
        if control.parent_id is not None:
            struct.set_int32("Obj_ParentID", control.parent_id)
        if control.locked is not None:
            struct.set_uint8("Obj_Locked", int(control.locked))
        if control.color is not None:
            if control.color.a is not None:
                struct.set_single("ALPHA", control.color.a)
            struct.set_vector3("COLOR", Vector3(control.color.r, control.color.g, control.color.b))

        if control.padding is not None:
            struct.set_int32("PADDING", control.padding)
        if control.looping is not None:
            struct.set_uint8("LOOPING", int(control.looping))
        if control.left_scrollbar is not None:
            struct.set_uint8("LEFTSCROLLBAR", int(control.left_scrollbar))

        # Extent
        write_extent(struct, int(control.position.x), int(control.position.y), int(control.size.x), int(control.size.y))

        # Border
        if control.border is not None:
            write_border(struct, control.border)

        # Text
        if control.gui_text is not None:
            write_text(struct, control.gui_text)

        # Hilight
        if control.hilight is not None:
            write_hilight(struct, control.hilight)

        # MoveTo
        if control.moveto is not None:
            write_moveto(struct, control.moveto)

        # ListBox specific
        if isinstance(control, GUIListBox):
            if control.proto_item is not None:
                write_proto_item(struct, control.proto_item)
            if control.scroll_bar is not None:
                write_scrollbar(struct, control.scroll_bar)

        # Handle child controls
        if control.children:
            controls_list = GFFList()
            for child in control.children:
                child_struct = dismantle_control(child)
                controls_list._structs.append(child_struct)
            struct.set_list("CONTROLS", controls_list)

        return struct

    if gui.root:
        gff.root = dismantle_control(gui.root)
        gff.root.struct_id = -1
    return gff

def read_gui(source: SOURCE_TYPES, offset: int = 0, size: int | None = None) -> GUI:
    """Read GUI data from bytes and return a GUI instance.

    Args:
        data: The bytes to read from.
        offset: The offset to start reading from.

    Returns:
        A new GUI instance.
    """
    gff: GFF = read_gff(source, offset, size)
    return construct_gui(gff)

def write_gui(gui: GUI, target: TARGET_TYPES, game: Game = Game.K2, file_format: ResourceType = ResourceType.GFF, *, use_deprecated: bool = True):
    """Write GUI instance to bytes.

    Args:
        gui: The GUI instance to write.

    Returns:
        The bytes representation of the GUI.
    """
    gff: GFF = dismantle_gui(gui, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format=file_format)

def bytes_gui(
    gui: GUI,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    """Convert GUI bytes to canonical form.

    Args:
        data: The bytes to convert.

    Returns:
        The canonical form of the GUI bytes.
    """
    gff: GFF = dismantle_gui(gui, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
