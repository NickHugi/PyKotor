# From https://nwn.wiki/display/NWN1/TXI#TXI-TextureRelatedFields
# From DarthParametric and Drazgar in the DeadlyStream Discord.
from __future__ import annotations

import math
from typing import TYPE_CHECKING, ClassVar

from pykotor.tools.encoding import get_charset_from_encoding
from pykotor.utility.path import BasePath, Path

if TYPE_CHECKING:
    import os

    from pykotor.common.language import Language


class TXIBaseInformation:
    """Fields used within all txi files."""

    def __init__(self) -> None:
        #  Mipmap and Filter settings (0/1) can apply different graphical "softening" on the fonts (not affecting spacing etc.). Don't use it though, in most case it would hurt your eyes.
        #  The engine has broken mip use implementation. It incorrectly mixes mip levels, even on objects filling the screen.
        self.mipmap: int = 0  # The mipmap 0 setting shouldn't be changed. That tells the engine to use mip 0, i.e. the highest resolution of the image
        self.filter: int = 0  # (???)
        self.downsamplemin: int = 0  # (???) (probably unsupported or broken related to above)
        self.downsamplemax: int = 0  # (???) (probably unsupported or broken related to above)


class TXIMaterialInformation(TXIBaseInformation):
    def __init__(self) -> None:
        self.bumpmaptexture: int
        self.bumpyshinytexture: int
        self.envmaptexture: int
        self.bumpreplacementtexture: int
        self.blending: int
        self.decal: int


class TXITextureInformation(TXIBaseInformation):
    def __init__(self) -> None:
        super().__init__()
        self.proceduretype: int
        self.filerange: int
        self.defaultwidth: int
        self.defaultheight: int
        self.filter: int
        self.maptexelstopixels: int
        self.gamma: int
        self.isbumpmap: int
        self.clamp: int
        self.alphamean: int
        self.isdiffusebumpmap: int
        self.isspecularbumpmap: int
        self.bumpmapscaling: int
        self.specularcolor: int
        self.numx: int
        self.numy: int
        self.cube: int
        self.bumpintensity: int
        self.temporary: int
        self.useglobalalpha: int
        self.isenvironmentmapped: int
        self.pltreplacement: int


class TXIFontInformation(TXIBaseInformation):
    DEFAULT_RESOLUTION: ClassVar[int] = 512
    DEFAULT_FONT_NAMES: ClassVar[list[str]] = [  # TODO: figure out which ones the game actually uses.
        "fnt_galahad14",  # Main menu?
        "dialogfont10x10",
        "dialogfont10x10a",
        "dialogfont10x10b",
        "dialogfont12x16",
        "dialogfont16x16",
        "dialogfont16x16a",
        "dialogfont16x16a",
        "dialogfont16x16b",
        "dialogfont32x32",  # It is possible this is the only one used in k1.
        "fnt_console",     # 127 chars, also has a large horizontally-wide rectangle probably used as the consolebox display
        "fnt_credits",
        "fnt_creditsa",
        "fnt_creditsb",
        "fnt_d10x10b",
        "fnt_d16x16",
        "fnt_d16x16a",
        "fnt_d16x16b",
        "fnt_dialog16x16",
    ]

    def __init__(self) -> None:
        super().__init__()
        # Actual fields
        self.numchars: int = 256  # Tested. Unsure if this is actually required, or if the game simply takes from the 'upperleftcoords' and 'lowerrightcoords' sizes.
        self.spacingR: float = 0  # Untested. Float between 0 and 1. According to research, should NEVER exceed the maximum of 0.002600
        self.spacingB: float = 0  # Confirmed. Float between 0 and 1. Spacing between each multiline string rendered ingame.
        self.caretindent: float = -0.010000  # Untested. Probably determines the accent information above the character. Probably negative since Y is inverted so this checks out.
        self.fontwidth: float = 1.000000  # Untested. Float between 0 and 1. Actually stretches down somehow. Heavily distorts the text when modified.

        # This could easily be used for DBCS (double byte encodings).
        # It may be unimplemented in KOTOR. Or hopefully, nobody's figured out how to use it.
        # Figuring this out would likely be the solution for supporting languages like Korean, Japanese, Chinese, and Vietnamese.
        # Otherwise a new engine, or implementing an overlay (like discord/steam/rivatuner's) into kotor to bypass kotor's bitmap fonts for displayed text.
        self.isdoublebyte: bool = False  # (???) Potentially for multi-byte encodings? Might not even be a bool.
        self.dbmapping: object = None  # (???) Potentially for multi-byte encodings?

        self.fontheight: float  # Float between 0 and 1.
        self.baselineheight: float  # Untested. Float between 0 and 1.
        self.texturewidth: float  # Tested. Float between 0 and 1. Actual displayed width of the texture, allows stretching/compressing along the X axis.

        self.upper_left_coords: list[tuple[float, float, int]]  # The top left coordinates for the character box the game draws. each float is 0 to 1. 3rd tuple int is always 0
        self.lower_right_coords: list[tuple[float, float, int]]  # The bottom right coordinates for the character box the game draws. each float is 0 to 1. 3rd tuple int is always 0
        #
        # The 3rd int in the upperleftcoords and bottomright coords is unknown. It could be any of the following:
        #
        # Layer or Depth Information: In some graphic systems, a third coordinate can be used to represent the depth or
        # layer, especially in 3D rendering contexts. However, for 2D font rendering, this is less
        # likely unless there is some form of layering or depth effect involved.
        #
        # Reserved for Future Use or Extension: It's common in software development to include elements
        # in data structures that are reserved for potential future use. This allows for extending the
        # functionality without breaking existing formats or compatibility.
        #
        # Indicator or Flag: This integer could serve as a flag or an indicator for specific conditions or states.
        #
        # Alignment or Padding: In some data structures, additional elements
        # are included for alignment purposes, ensuring that the data aligns well with memory boundaries

    def __str__(self):
        # Format the coordinates (left 4 spaces are not required, but make formatting cleaner)
        ul_coords_str = "\n".join([f"    {x:.6f} {y:.6f} {not_z}" for x, y, not_z in self.upper_left_coords])
        lr_coords_str = "\n".join([f"    {x:.6f} {y:.6f} {not_z}" for x, y, not_z in self.lower_right_coords])

        return f"""
mipmap {self.mipmap}
filter {self.filter}
numchars {self.numchars}
fontheight {self.fontheight:.6f}
baselineheight {self.baselineheight:.6f}
texturewidth {self.texturewidth:.6f}
fontwidth {self.fontwidth:.6f}
spacingR {self.spacingR:.6f}
spacingB {self.spacingB:.6f}
caretindent {self.caretindent:.6f}
isdoublebyte {int(self.isdoublebyte)}
upperleftcoords {self.ul_coords_count}
{ul_coords_str}
lowerrightcoords {self.lr_coords_count}
{lr_coords_str}
"""
    @property
    def ul_coords_count(self) -> int:
        return len(self.upper_left_coords)

    @property
    def lr_coords_count(self) -> int:
        return len(self.upper_left_coords)

    def get_scaling_factor(self) -> float:
        return 2 ** (math.log2(self.DEFAULT_RESOLUTION) - 1)

    def coords_from_normalized(self, upper_left_coords, lower_right_coords, resolution):
        """Converts normalized coordinates to bounding boxes.

        Args:
        ----
            upper_left_coords: List of tuples containing normalized upper left coordinates of boxes
            lower_right_coords: List of tuples containing normalized lower right coordinates of boxes
            resolution: Tuple containing image width and height

        Returns:
        -------
            boxes: List of bounding boxes as lists of [x1,y1,x2,y2] coordinates
        Processing Logic:
            - Loops through upper_left_coords and lower_right_coords and zips them
            - Converts normalized coords to pixel coords using resolution
            - Appends pixel coords as a list representing a bounding box
            - Returns list of bounding boxes.
        """
        boxes = []
        for (ulx, uly, _), (lrx, lry, _) in zip(upper_left_coords, lower_right_coords):
            # Convert normalized coords back to pixel coords
            pixel_ulx = ulx * resolution[0]
            pixel_uly = (1 - uly) * resolution[1]  # Y is inverted
            pixel_lrx = lrx * resolution[0]
            pixel_lry = (1 - lry) * resolution[1]  # Y is inverted
            boxes.append([int(pixel_ulx), int(pixel_uly), int(pixel_lrx), int(pixel_lry)])
        return boxes

    def normalize_coords(
        self,
        boxes: list[tuple[float, float, float, float]],
        resolution: tuple[int, int]
    ) -> tuple[list[tuple[float, float, int]], list[tuple[float, float, int]]]:
        """Converts boxes to normalized coordinates.

        Args:
        ----
            boxes: list of bounding boxes as tuples of floats
            resolution: tuple of ints specifying image width and height

        Returns:
        -------
            tuple: tuple containing lists of normalized upper left and lower right box coordinates
        Processing Logic:
            - Loops through each bounding box
            - Extracts upper left and lower right coordinates from each box
            - Normalizes the coordinates by dividing by image width/height
            - Appends normalized upper left and lower right coords to separate lists
            - Returns a tuple of the two lists of normalized coordinates.
        """
        upper_left_coords: list[tuple[float, float, int]] = []
        lower_right_coords: list[tuple[float, float, int]] = []

        for box in boxes:
            ulx, uly, lrx, lry = box
            # Convert pixel coords to normalized coords
            norm_ulx = ulx / resolution[0]
            norm_uly = 1 - (uly / resolution[1])  # Y is inverted
            norm_lrx = lrx / resolution[0]
            norm_lry = 1 - (lry / resolution[1])  # Y is inverted
            upper_left_coords.append((norm_ulx, norm_uly, 0))
            lower_right_coords.append((norm_lrx, norm_lry, 0))

        return upper_left_coords, lower_right_coords

    def set_font_metrics(
        self,
        resolution: tuple[int, int],
        max_char_height: float,
        baseline_height: float,
        custom_scaling: float,
    ):
        res_const: float = resolution[0] / TXIFontInformation.DEFAULT_RESOLUTION
        scaling_factor: float = 2 ** (math.log2(res_const) - 1)

        self.texturewidth: float = resolution[0] / 100 / res_const * custom_scaling
        self.fontheight: float = max_char_height / resolution[1] * self.texturewidth / scaling_factor * custom_scaling
        self.baselineheight = baseline_height / resolution[1] / TXIFontInformation.DEFAULT_RESOLUTION

def calculate_character_metrics(
    pil_font,
    charset_list,
    baseline_char="0",  # ( 0 should be in every code page )
) -> tuple[int, int, int]:
    """Calculates and returns metrics like baseline height, maximum underhang height, and maximum character height."""
    from PIL import Image, ImageDraw  # Import things here to separate from HoloPatcher code.

    # Create a temporary image for measurements
    temp_image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_image)

    # Get the bounding box of the baseline character
    baseline_bbox = temp_draw.textbbox((0, 0), baseline_char, font=pil_font)
    baseline_height = baseline_bbox[3] - baseline_bbox[1]

    max_underhang_height = 0
    max_char_height = 0
    for char in charset_list:
        char_bbox: tuple[int, int, int, int] = temp_draw.textbbox((0, 0), char, font=pil_font)
        underhang_height = char_bbox[3] - baseline_bbox[3]
        char_height = char_bbox[3] - char_bbox[1]

        max_underhang_height = max(max_underhang_height, underhang_height)
        max_char_height = max(max_char_height, char_height + underhang_height)

    return baseline_height, max_underhang_height, max_char_height



def write_bitmap_fonts(
    target: os.PathLike | str,
    font_path: os.PathLike | str,
    resolution: tuple[int, int],
    lang: Language,
    draw_box=False,
    custom_scaling=1.0,
    font_color=None,
) -> None:
    target_path = (Path(target) if isinstance(target, BasePath) else Path(target)).resolve()
    target_path.mkdir(parents=True, exist_ok=True)

    for font_name in TXIFontInformation.DEFAULT_FONT_NAMES:
        if font_name == "fnt_console":
            continue

        write_bitmap_font(
            target_path / font_name,
            font_path,
            resolution,
            lang,
            draw_box,
            custom_scaling,
            font_color,
        )

def write_bitmap_font(
    target: os.PathLike | str,
    font_path: os.PathLike | str,
    resolution: tuple[int, int],
    lang: Language,
    draw_boxes: bool = False,
    custom_scaling: float = 1.0,
    font_color=None,
) -> None:
    """Generates a bitmap font (TGA and TXI) from a TTF font file. Note the default 'draw_boxes', none of these boxes show up in the game (just outside the coords)."""
    if any(resolution) == 0:
        msg = f"resolution must be nonzero, got {resolution}"
        raise ZeroDivisionError(msg)

    from PIL import Image, ImageDraw, ImageFont  # Import things here to separate from HoloPatcher code.
    font_path, target_path = ((p if isinstance(p, BasePath) else Path(p)).resolve() for p in (font_path, target))  # type: ignore[attr-defined, reportGeneralTypeIssues]
    charset_list: list[str] = get_charset_from_encoding(lang.get_encoding())
    numchars: int = len([char for char in charset_list if char])

    # Calculate grid cell size
    characters_per_column, characters_per_row = math.ceil(math.sqrt(numchars)), math.ceil(math.sqrt(numchars))
    grid_cell_size: int = min(resolution[0] // characters_per_column, resolution[1] // characters_per_row)

    # Using a square grid cell, set the font size to fit within this cell
    pil_font = ImageFont.truetype(str(font_path), grid_cell_size)
    baseline_height, max_underhang_height, max_char_height = calculate_character_metrics(pil_font, charset_list)

    # Calculate total additional height needed for the underhang
    total_additional_height = (baseline_height - max_underhang_height) * characters_per_column
    # Adjust the resolution to include the additional height
    adjusted_resolution = (resolution[0] + total_additional_height, resolution[1] + total_additional_height)

    # Create charset image with adjusted resolution
    charset_image = Image.new("RGBA", adjusted_resolution, (0, 0, 0, 0))
    draw = ImageDraw.Draw(charset_image)

    # Initialize the grid position
    grid_x = 0
    grid_y = 0
    upper_left_coords = []
    lower_right_coords = []
    for char in charset_list:
        if not char:
            # append some coords around blank space (to keep character's byte indexing aligned)
            upper_left_coords.append((0.000001, 0.000001, 0))
            lower_right_coords.append((0.000002, 0.000002, 0))
            continue

        # Calculate cell dimensions
        cell_width = adjusted_resolution[0] / characters_per_column
        cell_height = adjusted_resolution[1] / characters_per_row

        # Calculate normalized coordinates for upper left
        norm_x1 = grid_x / characters_per_column
        norm_y1 = (grid_y * cell_height) / adjusted_resolution[1]
        # Calculate normalized coordinates for lower right
        norm_x2 = (grid_x + 1) / characters_per_row
        norm_y2 = ((grid_y + 1) * cell_height) / adjusted_resolution[1]

        # Convert normalized coordinates to pixels
        pixel_x1 = norm_x1 * adjusted_resolution[0]
        pixel_y1 = norm_y1 * adjusted_resolution[1]
        pixel_x2 = norm_x2 * adjusted_resolution[0]
        pixel_y2 = norm_y2 * adjusted_resolution[1]

        # Calculate character height and width
        char_bbox = draw.textbbox((pixel_x1, pixel_y1), char, font=pil_font)
        char_width = char_bbox[2] - char_bbox[0]
        char_height = char_bbox[3] - char_bbox[1]

        # Draw character. Adjust Y coordinates to move one cell downwards
        if char == "\n":
            draw.text((pixel_x1 + cell_width/2, pixel_y1 + cell_height - max_underhang_height), char, font=pil_font, fill=font_color or (255, 255, 255, 255))
        else:
            draw.text((pixel_x1 + cell_width/2, pixel_y1 + cell_height - max_underhang_height), char, anchor="ms", font=pil_font, fill=font_color or (255, 255, 255, 255))

        # Adjust text coordinates
        cell_center_x = pixel_x1 + cell_width / 2  # center of the cell
        pixel_x1 = cell_center_x - char_width / 2
        pixel_x2 = cell_center_x + char_width / 2
        pixel_y1 = pixel_y2 - max_char_height

        # Draw a red rectangle around the character based on actual text dimensions
        if draw_boxes:
            draw.rectangle((pixel_x1, pixel_y1, pixel_x2, pixel_y2), outline="red")

        # Calculate normalized coordinates
        norm_x1 = pixel_x1 / adjusted_resolution[0]
        norm_y1 = pixel_y1 / adjusted_resolution[1]
        norm_x2 = pixel_x2 / adjusted_resolution[0]
        norm_y2 = pixel_y2 / adjusted_resolution[1]

        # Invert Y-axis normalization
        norm_y1 = 1 - norm_y1
        norm_y2 = 1 - norm_y2

        # Ensure we're within 0 and 1 ( required due lack of libraqm for RTL languages, and low-effort TTFs )
        norm_x1, norm_x2 = max(0, min(norm_x1, 1)), max(0, min(norm_x2, 1))
        norm_y1, norm_y2 = max(0, min(norm_y1, 1)), max(0, min(norm_y2, 1))

        # Append to coordinate lists
        upper_left_coords.append((norm_x1, norm_y1, 0))
        lower_right_coords.append((norm_x2, norm_y2, 0))

        # Move to the next grid position
        grid_x = (grid_x + 1) % characters_per_row
        if grid_x == 0:
            grid_y += 1

    # Build txi fields
    txi_font_info = TXIFontInformation()
    txi_font_info.isdoublebyte = not lang.is_8bit_encoding()
    txi_font_info.numchars = numchars
    txi_font_info.upper_left_coords = upper_left_coords
    txi_font_info.lower_right_coords = lower_right_coords
    # Normalize and set font metrics
    txi_font_info.set_font_metrics(adjusted_resolution, max_char_height, baseline_height, custom_scaling)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    charset_image.save(target_path.with_suffix(".tga"), format="TGA")

    # Generate and save the TXI data
    txi_target = target_path.with_suffix(".txi")
    with txi_target.open("w") as txi_file:
        txi_file.write(str(txi_font_info))
