# From https://nwn.wiki/display/NWN1/TXI#TXI-TextureRelatedFields
# From DarthParametric and Drazgar in the DeadlyStream Discord.
from __future__ import annotations
from contextlib import suppress

import math
from typing import TYPE_CHECKING

from pykotor.tools.encoding import get_double_byte_charset, get_single_byte_charset
from pykotor.utility.path import BasePath, Path

if TYPE_CHECKING:
    import os

    from pykotor.common.language import Language


class TXIBaseInformation:
    def __init__(self) -> None:
        #  Mipmap and Filter settings (0/1) can apply different graphical "softening" on the fonts (not affecting spacing etc.). Don't use it though, in most case it would hurt your eyes.
        #  The engine has broken mip use implementation. It incorrectly mixes mip levels, even on objects filling the screen.
        self.mipmap: int = 0  # The mipmap 0 setting shouldn't be changed. That tells the engine to use mip 0, i.e. the highest resolution of the image
        self.filter: int = 0
        self.downsamplemin: int = 0  # unused in KOTOR
        self.downsamplemax: int = 0  # unused in KOTOR


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
    def __init__(self) -> None:
        super().__init__()
        self.numchars: int = 256
        self.upperleftcoords: int = 256
        self.lowerrightcoords: int = 256
        self.spacingB: float = 0  # Float between 0 and 1. spacingB should be left alone.
        self.isdoublebyte: int = 0  # Potentially for multi-byte encodings?

        self.fontheight: float  # Float between 0 and 1.
        self.baselineheight: float  # Float between 0 and 1. presumably sets where the text sits. Probably to account for stuff like French that has those accents that hang underneath characters.
        self.texturewidth: float  # Float between 0 and 1. Actual displayed width of the texture, allows stretching/compressing along the X axis.
        self.fontwidth: float  # Float between 0 and 1. Actually stretches down somehow. Heavily distorts the text when modified. Perhaps this is the Y axis and texturewidth is the X axis?
        self.spacingR: float  # Float between 0 and 1. Do NOT exceed the maximum of 0.002600
        self.caretindent: float  # Float between 0 and 1.
        self.dbmapping: int  # ???

        self.upper_left_coords: list[tuple[float, float, int]]  # The top left coordinates for the character box the game draws. each float is 0 to 1. 3rd tuple int is always 0
        self.lower_right_coords: list[tuple[float, float, int]]  # The bottom right coordinates for the character box the game draws. each float is 0 to 1. 3rd tuple int is always 0
        # The 3rd int in the upperleftcoords and bottomright coords is unknown. It could be any of the following:
        # Layer or Depth Information: In some graphic systems, a third coordinate can be used to represent the depth or
        # layer, especially in 3D rendering contexts. However, for 2D font rendering, this is less
        # likely unless there is some form of layering or depth effect involved.
        # Layer or Depth Information: In some graphic systems, a third coordinate can be used to represent the depth or layer, especially in 3D rendering contexts. However, for 2D font rendering, this is less likely unless there is some form of layering or depth effect involved.
        # Reserved for Future Use or Extension: It's common in software development to include elements
        # in data structures that are reserved for potential future use. This allows for extending the
        # functionality without breaking existing formats or compatibility.
        # Indicator or Flag: This integer could serve as a flag or an indicator for specific conditions or
        # states.
        # Alignment or Padding: In some data structures, additional elements
        # are included for alignment purposes, ensuring that the data aligns well with memory boundaries

def coords_to_boxes(upper_left_coords, lower_right_coords, resolution):
    boxes = []
    for (ulx, uly, _), (lrx, lry, _) in zip(upper_left_coords, lower_right_coords):
        # Convert normalized coords back to pixel coords
        pixel_ulx = ulx * resolution[0]
        pixel_uly = (1 - uly) * resolution[1]  # Y is inverted
        pixel_lrx = lrx * resolution[0]
        pixel_lry = (1 - lry) * resolution[1]  # Y is inverted
        boxes.append([int(pixel_ulx), int(pixel_uly), int(pixel_lrx), int(pixel_lry)])
    return boxes

def boxes_to_coords(boxes, resolution):
    upper_left_coords = []
    lower_right_coords = []

    for box in boxes:
        ulx, uly, lrx, lry = box
        # Convert pixel coords to normalized coords
        norm_ulx = ulx / resolution[0]
        norm_uly = 1 - (uly / resolution[1])  # Y is inverted
        norm_lrx = lrx / resolution[0]
        norm_lry = 1 - (lry / resolution[1])  # Y is inverted
        upper_left_coords.append([norm_ulx, norm_uly, 0])
        lower_right_coords.append([norm_lrx, norm_lry, 0])

    return upper_left_coords, lower_right_coords

def get_font_info(font, point_size: int):
    units_per_em = font["head"].unitsPerEm
    ascent = font["hhea"].ascent * point_size / units_per_em
    descent = font["hhea"].descent * point_size / units_per_em
    return ascent, descent, units_per_em

def write_bitmap_fonts(
    target: os.PathLike | str,
    font_path: os.PathLike | str,
    resolution: tuple[int, int],
    lang: Language,
    draw_box=False,
) -> None:
    font_path, target_path = ((p if isinstance(p, BasePath) else Path(p)).resolve() for p in (font_path, target))  # type: ignore[reportGeneralTypeIssues]
    target_path.mkdir(parents=True, exist_ok=True)
    default_font_names = [
        "fnt_galahad14",  # Main menu stuff?
        "dialogfont10x10",
        "dialogfont10x10a",
        "dialogfont10x10b",
        "dialogfont12x16",
        "dialogfont16x16",
        "dialogfont16x16a",
        "dialogfont16x16a",
        "dialogfont16x16b",
#        "fnt_console",
        "fnt_credits",
        "fnt_creditsa",
        "fnt_creditsb",
        "fnt_d10x10b",
        "fnt_d16x16",
        "fnt_d16x16a",
        "fnt_d16x16b",
        "fnt_dialog16x16",
    ]
    for font_name in default_font_names:
        write_bitmap_font(
            target_path / font_name,
            font_path,
            resolution,
            lang,
            draw_box,
        )

def get_charset_from_encoding(encoding):
    charset = []
    for i in range(0x110000):
        try:
            char = chr(i)
            char.encode(encoding)
            charset.append(char)
        except UnicodeEncodeError:  # noqa: PERF203
            charset.append("")
    return charset

def write_bitmap_font(
    target: os.PathLike | str,
    font_path: os.PathLike | str,
    resolution: tuple[int, int],
    lang: Language,
    draw_boxes = True,
) -> None:
    """Generates a bitmap font (TGA and TXI) from a TTF font file."""
    if any(resolution) == 0:
        msg = f"resolution must be nonzero, got {resolution}"
        raise ZeroDivisionError(msg)
    from PIL import Image, ImageDraw, ImageFont  # Import things here to separate from HoloPatcher code.
    font_path, target_path = ((p if isinstance(p, BasePath) else Path(p)).resolve() for p in (font_path, target))  # type: ignore[attr-defined, reportGeneralTypeIssues]

    txi_font_info = TXIFontInformation()
    txi_font_info.spacingB = 0
    txi_font_info.spacingR = 0
    txi_font_info.texturewidth = 2.160000
    txi_font_info.fontwidth = 1
    txi_font_info.caretindent = -0.010000
    txi_font_info.baselineheight = 0.150000
    txi_font_info.fontheight = 0.080000

    # Determine doublebyte encodings.
    txi_font_info.isdoublebyte = 0 if lang.is_8bit_encoding() else 1
    charset_list: list[str] = get_charset_from_encoding(lang.get_encoding())
    numchars = len([char for char in charset_list if char])
    # Calculate grid cell size
    characters_per_row = math.ceil(math.sqrt(numchars))
    characters_per_column = math.ceil(math.sqrt(numchars))
    grid_cell_size: int = min(resolution[0] // characters_per_column, resolution[1] // characters_per_row)
    txi_font_info.upperleftcoords = numchars
    txi_font_info.lowerrightcoords = numchars
    txi_font_info.numchars = numchars

    # Assuming a square grid cell, set the font size to fit within the cell
    pil_font = ImageFont.truetype(str(font_path), grid_cell_size)

    # Create a temporary image for measurements
    temp_image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_image)

    # Get the bounding box of the baseline character
    baseline_char = "0"
    baseline_bbox = temp_draw.textbbox((0, 0), baseline_char, font=pil_font)
    baseline_height = baseline_bbox[3] - baseline_bbox[1]

    # Get the bounding box of the descender character
    descender_char = "y"
    descender_bbox = temp_draw.textbbox((0, 0), descender_char, font=pil_font)

    # Calculate underhang height
    underhang_height = descender_bbox[3] - baseline_bbox[3]

    # Calculate total additional height needed for the underhang
    total_additional_height = underhang_height * characters_per_column

    # Adjust the resolution to include the additional height
    adjusted_resolution = (resolution[0], resolution[1] + total_additional_height)
    txi_font_info.baselineheight = baseline_height / adjusted_resolution[1]
    # Calculate fontheight and texturewidth (approx based on 5 resolution tests)
    txi_font_info.fontheight = (4.88265e-4 * adjusted_resolution[0] - 3.54439e-4 * adjusted_resolution[1] -
                                1.86629e-7 * adjusted_resolution[0]**2 + 1.43077e-7 * adjusted_resolution[1]**2 +
                                0.128595)
    txi_font_info.texturewidth = (0.0302212 * adjusted_resolution[0] - 0.0238694 * adjusted_resolution[1] -
                                1.12594e-5 * adjusted_resolution[0]**2 + 9.13224e-6 * adjusted_resolution[1]**2 +
                                1.07333)

    # Create charset image with adjusted resolution
    charset_image = Image.new("RGBA", adjusted_resolution, (0, 0, 0, 0))
    draw = ImageDraw.Draw(charset_image)

    txi_font_info.upper_left_coords = []
    txi_font_info.lower_right_coords = []

    # Initialize the grid position
    grid_x = 0
    grid_y = 0


    for char in charset_list:
        if char:
            # Calculate cell dimensions
            cell_width = resolution[0] / characters_per_column
            cell_height = resolution[1] / characters_per_row

            # Adjust cell height to include padding for underhang
            padded_cell_height = cell_height + underhang_height

            # Calculate normalized coordinates for upper left
            norm_x1 = grid_x / characters_per_row
            norm_y1 = (grid_y * padded_cell_height) / resolution[1]

            # Calculate normalized coordinates for lower right
            norm_x2 = (grid_x + 1) / characters_per_row
            norm_y2 = ((grid_y + 1) * padded_cell_height) / resolution[1]

            # Convert normalized coordinates to pixels
            pixel_x1 = norm_x1 * resolution[0]
            pixel_y1 = norm_y1 * resolution[1]
            pixel_x2 = norm_x2 * resolution[0]
            pixel_y2 = norm_y2 * resolution[1]

            char_bbox = draw.textbbox((pixel_x1, pixel_y1), char, font=pil_font)

            char_width = char_bbox[2] - char_bbox[0]
            char_height = char_bbox[3] - char_bbox[1]

            if char == "\n":
                # Adjust Y coordinates to move one cell downwards
                draw.text((pixel_x1 + cell_width/2, pixel_y1 + cell_height - underhang_height), char, font=pil_font, fill=(255, 255, 255, 255))
            else:
                draw.text((pixel_x1 + cell_width/2, pixel_y1 + cell_height - underhang_height), char, anchor="ms", font=pil_font, fill=(255, 255, 255, 255))

            # Calculate center of the cell
            cell_center_x = pixel_x1 + cell_width / 2

            # Adjust red rectangle coordinates
            pixel_x1 = cell_center_x - char_width / 2
            pixel_x2 = cell_center_x + char_width / 2
            pixel_y1 = pixel_y2 - char_height - underhang_height*2 - max(0, baseline_height - char_height)
            pixel_y2 -= underhang_height
            if draw_boxes:
                # Draw a red rectangle around the character based on actual text dimensions
                red_box = (pixel_x1, pixel_y1, pixel_x2, pixel_y2)
                draw.rectangle(red_box, outline="red")

            # Calculate normalized coordinates for the red box
            norm_x1 = pixel_x1 / adjusted_resolution[0]
            norm_y1 = pixel_y1 / adjusted_resolution[1]
            norm_x2 = pixel_x2 / adjusted_resolution[0]
            norm_y2 = pixel_y2 / adjusted_resolution[1]

            # Invert Y-axis normalization
            norm_y1 = 1 - norm_y1
            norm_y2 = 1 - norm_y2

            # Ensure we're within 0 and 1 ( required due to inaccuracies with fallback from libraqm )
            norm_x1, norm_x2 = max(0, min(norm_x1, 1)), max(0, min(norm_x2, 1))
            norm_y1, norm_y2 = max(0, min(norm_y1, 1)), max(0, min(norm_y2, 1))

            # Append to coordinate lists
            txi_font_info.upper_left_coords.append((norm_x1, norm_y1, 0))
            txi_font_info.lower_right_coords.append((norm_x2, norm_y2, 0))

            # Move to the next grid position
            grid_x = (grid_x + 1) % characters_per_row
            if grid_x == 0:
                grid_y += 1
        else:
            pass
            #txi_font_info.upper_left_coords.append((0.000000, 0.000000, 0))
            #txi_font_info.lower_right_coords.append((0.000000, 0.000000, 0))

    target_path.parent.mkdir(parents=True, exist_ok=True)
    charset_image.save(target_path.with_suffix(".tga"), format="TGA")

    # Generate and save the TXI data
    txi_data = _generate_txi_data(txi_font_info)
    txi_target = target_path.with_suffix(".txi")
    with txi_target.open("w") as txi_file:
        txi_file.write(txi_data)

def _generate_txi_data(txi_font_info: TXIFontInformation) -> str:
    # Format the upper left coordinates
    ul_coords_str = "\n".join([f"    {x:.6f} {y:.6f} {z}" for x, y, z in txi_font_info.upper_left_coords])

    # Format the lower right coordinates
    lr_coords_str = "\n".join([f"    {x:.6f} {y:.6f} {z}" for x, y, z in txi_font_info.lower_right_coords])
    return f"""mipmap {txi_font_info.mipmap}
filter {txi_font_info.filter}
numchars {txi_font_info.numchars}
fontheight {txi_font_info.fontheight:.6f}
baselineheight {txi_font_info.baselineheight:.6f}
texturewidth {txi_font_info.texturewidth:.6f}
fontwidth {txi_font_info.fontwidth:.6f}
spacingR {txi_font_info.spacingR:.6f}
spacingB {txi_font_info.spacingB:.6f}
caretindent {txi_font_info.caretindent:.6f}
isdoublebyte {txi_font_info.isdoublebyte}
upperleftcoords {txi_font_info.upperleftcoords}
{ul_coords_str}
lowerrightcoords {txi_font_info.lowerrightcoords}
{lr_coords_str}"""
