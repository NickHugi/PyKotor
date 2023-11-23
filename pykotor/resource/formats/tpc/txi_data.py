# From https://nwn.wiki/display/NWN1/TXI#TXI-TextureRelatedFields
# From DarthParametric and Drazgar in the DeadlyStream Discord.
from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.utility.path import Path

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
        self.isdoublebyte: int = 0  # unused?

        self.fontheight: float  # Float between 0 and 1.
        self.baselineheight: float  # Float between 0 and 1. presumably sets where the text sits. Probably to account for stuff like French that has those accents that hang underneath characters.
        self.texturewidth: float  # Float between 0 and 1. Actual displayed width of the texture, allows stretching/compressing along the X axis.
        self.fontwidth: float  # Float between 0 and 1. Actually stretches down somehow. Heavily distorts the text when modified. Perhaps this is the Y axis and texturewidth is the X axis?
        self.spacingR: float  # Float between 0 and 1. Do NOT exceed the maximum of 0.002600
        self.caretindent: float  # Float between 0 and 1.
        # self.dbmapping:  # unused in KOTOR
        self.upper_left_coords: list[tuple[float, float, int]]  # each float is 0 to 1, 3rd tuple item is always 0
        self.lower_right_coords: list[tuple[float, float, int]]  # each float is 0 to 1, 3rd tuple item is always 0

def write_bitmap_fonts(target: os.PathLike | str, font_path: os.PathLike | str, resolution: tuple[int, int], lang: Language) -> None:
    font_path, target_path = ((p if isinstance(p, Path) else Path(p)).resolve() for p in (font_path, target))
    target_path.mkdir(parents=True, exist_ok=True)
    default_font_names = [
        "fnt_galahad14",
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
        write_bitmap_font(target_path / font_name, font_path, resolution, lang)

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

def get_character_dimensions_fallback(font, char: str, point_size: int, DPI=96):
    cmap = font["cmap"].getcmap(3, 1).cmap
    glyph_set = font.getGlyphSet()
    units_per_em = font["head"].unitsPerEm
    glyph_name = cmap.get(ord(char), ".notdef")
    glyph = glyph_set[glyph_name]

    point_to_pixels = point_size / 72 * DPI
    width = glyph.width * point_to_pixels / units_per_em if glyph.width != 0 else point_size
    height = None
    # Use the font's ascent and descent to calculate height
    ascent = font["hhea"].ascent * point_to_pixels / units_per_em
    descent = -font["hhea"].descent * point_to_pixels / units_per_em  # descent is typically negative
    height = ascent + descent
    if hasattr(glyph, "yMax") and hasattr(glyph, "yMin") and glyph.yMax != glyph.yMin:
        height = (glyph.yMax - glyph.yMin) * point_to_pixels / units_per_em
    else:
        height = point_size  # Default height if yMax and yMin are not available or the same

    return width, height

def get_character_dimensions(ttfont, char: str, point_size: int, DPI=96):
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    units_per_em = ttfont["head"].unitsPerEm
    cmap = next(c for c in ttfont["cmap"].tables if c.format == 4)
    glyph_id = cmap.cmap.get(ord(char))

    if glyph_id is None:
        print(f"Character {char} not found in font.")
        return *get_character_dimensions_fallback(ttfont, char, point_size, DPI), 0, 0

    # Glyph metrics
    h_metrics = ttfont["hmtx"].metrics[glyph_id]
    glyph_width = h_metrics[0]

    # Create a glyph pen
    pen = TTGlyphPen(ttfont.getGlyphSet())

    # Draw the glyph
    try:
        ttfont.getGlyphSet()[char].draw(pen)
    except Exception as e:
        print(f"Character '{char}':", repr(e))
        return *get_character_dimensions_fallback(ttfont, char, point_size, DPI), 0, 0
    glyph = pen.glyph()

    # Get glyph's bounding box
    glyf_table = ttfont["glyf"]
    boundsPen = BoundsPen(glyf_table)
    glyph.draw(boundsPen, glyf_table)

    xMin, yMin, xMax, yMax = boundsPen.bounds
    point_to_pixels = point_size / 72 * DPI
    ascent = ttfont["hhea"].ascent * point_to_pixels / units_per_em
    descent = -ttfont["hhea"].descent * point_to_pixels / units_per_em  # descent is typically negative
    height = ascent + descent
    scale = point_size / units_per_em * DPI / 72
    width = glyph_width * scale
    #height = (yMax - yMin) * scale
    overhang = yMax * scale if yMax > 0 else 0
    underhang = abs(yMin) * scale if yMin < 0 else 0

    return width, height, overhang, underhang


def write_bitmap_font(
    target: os.PathLike | str,
    font_path: os.PathLike | str,
    resolution: tuple[int, int],
    lang: Language,
    char_range: tuple[int, int] = (0, 256),
    spacingR = 0,
    draw_boxes = True,
) -> None:
    """Generates a bitmap font (TGA and TXI) from a TTF font file."""
    from fontTools.ttLib import TTFont
    from PIL import Image, ImageDraw, ImageFont  # Import things here to separate from HoloPatcher code.
    font_path, target_path = ((p if isinstance(p, Path) else Path(p)).resolve() for p in (font_path, target))

    txi_font_info = TXIFontInformation()
    txi_font_info.spacingR = spacingR

    # Calculate grid cell size for a 16x16 grid
    characters_per_row = 16
    grid_cell_size = min(resolution[0] // characters_per_row, resolution[1] // characters_per_row)

    # Load the TTF font with fontTools
    font = TTFont(str(font_path))
    ascent, descent, font_units_per_em = get_font_info(font, grid_cell_size)

    # Set the texture resolution in proportion
    txi_font_info.texturewidth = resolution[0] / 100
    txi_font_info.fontwidth = 1
    txi_font_info.fontheight = 1
    txi_font_info.caretindent = 0.1

    # Assuming a square grid cell, set the font size to fit within the cell
    pil_font = ImageFont.truetype(str(font_path), grid_cell_size)

    # Create charset image
    charset_image = Image.new("RGBA", resolution, (0, 0, 0, 0))
    draw = ImageDraw.Draw(charset_image)

    average_baseline_height = ascent / font_units_per_em
    #txi_font_info.baselineheight = average_baseline_height / resolution[1]
    #txi_font_info.fontheight = grid_cell_size / font_units_per_em
    txi_font_info.baselineheight = 0.080000
    txi_font_info.fontheight = 0.100000

    txi_font_info.upper_left_coords = []
    txi_font_info.lower_right_coords = []

    ascent, descent = pil_font.getmetrics()
    max_char_height = ascent + descent
    baseline_heights = []
    for i in range(*char_range):  # Standard ASCII set
        char = bytes([i]).decode(lang.get_encoding(), errors="ignore")

        # Determine grid position
        grid_x = i % 16
        grid_y = i // 16

        # Calculate normalized coordinates for upper left
        norm_x1 = grid_x / 16
        norm_y1 = grid_y / 16

        # Calculate normalized coordinates for lower right
        norm_x2 = (grid_x + 1) / 16
        norm_y2 = (grid_y + 1) / 16

        pixel_x1 = norm_x1 * resolution[0]
        pixel_y1 = norm_y1 * resolution[1]
        pixel_x2 = norm_x2 * resolution[0]
        pixel_y2 = norm_y2 * resolution[1]

        if draw_boxes:
            # Draw a yellow box representing the grid cell
            yellow_box = (pixel_x1, pixel_y1, pixel_x2, pixel_y2)
            draw.rectangle(yellow_box, outline="yellow")    # Draw the character onto the image

        if not char:  # for errors="ignore" tests. Coordinates match the whole cell size
            txi_font_info.upper_left_coords.append((norm_x1, 1 - norm_y1, 0))
            txi_font_info.lower_right_coords.append((norm_x2, 1 - norm_y2, 0))
            continue


        text_width, text_height, text_overhang, text_underhang = get_character_dimensions(font, char, grid_cell_size)
        char_bbox = draw.textbbox((0, 0), char, font=pil_font)

        char_width = char_bbox[2] - char_bbox[0]
        char_height = char_bbox[3] - char_bbox[1]

        text_x = pixel_x1
        text_y = pixel_y1 - text_underhang/2

        try:  # libraqm
            draw.text((text_x, text_y), char, language=lang.get_bcp47_code(), font=pil_font, fill=(255, 255, 255, 255))
        except Exception as e:
            print(f"Failed to draw text with preferred arguments: {e!r}. Using fallback..")
            draw.text((text_x, text_y), char, align="center", font=pil_font, fill=(255, 255, 255, 255))

        diff = 3
        if text_underhang > 0:
            diff = 5
            pixel_y2 += 3
        pixel_x2 = pixel_x1 + char_width
        pixel_y1 = pixel_y2 - char_height - diff # top
        pixel_y2 = pixel_y2  # bottom
        if draw_boxes:
            # Draw a red rectangle around the character based on actual text dimensions
            red_box = (pixel_x1, pixel_y1, pixel_x2, pixel_y2)
            #draw.rectangle(red_box, outline="red")

        # Calculate normalized coordinates for the red box
        norm_x1 = pixel_x1 / resolution[0]
        norm_y1 = pixel_y1 / resolution[1]
        norm_x2 = pixel_x2 / resolution[0]
        norm_y2 = pixel_y2 / resolution[1]

        # Invert Y-axis normalization
        norm_y1 = 1 - norm_y1
        norm_y2 = 1 - norm_y2

        # Ensure we're within 0 and 1.
        norm_x1, norm_x2 = max(0, min(norm_x1, 1)), max(0, min(norm_x2, 1))
        norm_y1, norm_y2 = max(0, min(norm_y1, 1)), max(0, min(norm_y2, 1))

        # Append to coordinate lists
        txi_font_info.upper_left_coords.append((norm_x1, norm_y1, 0))
        txi_font_info.lower_right_coords.append((norm_x2, norm_y2, 0))
        baseline_heights.append(text_height)

    # Check if baseline_heights is not empty to avoid division by zero
    if baseline_heights:
        average_baseline_height: float = sum(baseline_heights) / len(baseline_heights)
        #txi_font_info.baselineheight = average_baseline_height / resolution[1]

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
