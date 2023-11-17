# From https://nwn.wiki/display/NWN1/TXI#TXI-TextureRelatedFields
# From DarthParametric and Drazgar in the DeadlyStream Discord.
from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.helpers.path import Path

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
        self.lowerrightcoords: int = 0
        self.spacingB: float = 0  # Float between 0 and 1. spacingB should be left alone.
        self.isdoublebyte: int = 0  # unused?

        self.fontheight: float  # Float between 0 and 1.
        self.baselineheight: float  # Float between 0 and 1. presumably sets where the text sits. Probably to account for stuff like French that has those accents that hang underneath characters.
        self.texturewidth: float  # Float between 0 and 1. Actual displayed width of the texture, allows stretching/compressing along the X axis.
        self.fontwidth: float  # Float between 0 and 1. Actually stretches down somehow. Heavily distorts the text when modified. Perhaps this is the Y axis and texturewidth is the X axis?
        self.spacingR: float  # Float between 0 and 1. Do NOT exceed the maximum of 0.002600
        self.caretindent: float  # Float between 0 and 1.
        # self.dbmapping:  # unused in KOTOR
        self.upper_left_coords: list[tuple[float, float, int]]
        self.lower_right_coords: list[tuple[float, float, int]]

def write_bitmap_fonts(target: os.PathLike | str, font_path: os.PathLike | str, resolution: tuple[int, int], lang: Language) -> None:
    font_path, target_path = ((p if isinstance(p, Path) else Path(p)).resolve() for p in (font_path, target))
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
        "fnt_creditsa",
        "fnt_d10x10b",
        "fnt_d16x16",
        "fnt_d16x16a",
        "fnt_d16x16b",
        "fnt_dialog16x16",
    ]
    for font_name in default_font_names:
        write_bitmap_font(target_path / font_name, font_path, resolution, lang)

def write_bitmap_font(
    target: os.PathLike | str,
    font_path: os.PathLike | str,
    resolution: tuple[int, int],
    lang: Language,
    char_range: tuple[int, int] = (0, 256),
) -> None:
    """Generates a bitmap font (TGA and TXI) from a TTF font file."""
    from PIL import (  # Import things here to separate from HoloPatcher code.
        Image,
        ImageDraw,
        ImageFont,
    )
    font_path, target_path = ((p if isinstance(p, Path) else Path(p)).resolve() for p in (font_path, target))

    txi_font_info = TXIFontInformation()

    # idk
    txi_font_info.spacingR = 0.0

    # Set the texture resolution in proportion
    txi_font_info.texturewidth = resolution[0] / 100
    txi_font_info.fontheight = resolution[1] / max(resolution)

    # Calculate grid cell size for a 16x16 grid
    characters_per_row = 16
    grid_cell_size = min(resolution[0] // characters_per_row, resolution[1] // characters_per_row)

    # Assuming a square grid cell, set the font size to fit within the cell
    font_size = grid_cell_size - 4  # Subtracting a bit for padding
    pil_font = ImageFont.truetype(str(font_path), font_size)

    # Create charset image
    charset_image = Image.new("RGBA", resolution, (0, 0, 0, 0))
    draw = ImageDraw.Draw(charset_image)

    character_widths = []
    txi_font_info.upper_left_coords = []
    txi_font_info.lower_right_coords = []

    ascent, descent = pil_font.getmetrics()
    max_char_height = ascent + descent
    baseline_heights = []
    x, y = 0, 0
    for i in range(*char_range):  # Standard ASCII set
        char = bytes([i]).decode(lang.get_encoding(), errors="replace")
        bbox = draw.textbbox((0, 0), char, font=pil_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = x + (grid_cell_size - text_width) // 2  # Center horizontally
        text_y = y + (grid_cell_size - (max_char_height)) // 2  # Adjust vertical position upwards

        try:  # libraqm
            draw.text((text_x, text_y), char, language=lang.get_bcp47_code(), font=pil_font, fill=(255, 255, 255, 255))
        except Exception as e:
            print(f"Failed to draw text with preferred arguments: {e!r}. Using fallback..")
            draw.text((text_x, text_y), char, font=pil_font, fill=(255, 255, 255, 255))

        # Calculate normalized coordinates
        #norm_x1 = text_x / resolution[0]
        #norm_y1 = text_y / resolution[1]
        #norm_x2 = (text_x + text_width) / resolution[0]
        #norm_y2 = (text_y + text_height) / resolution[1]

        # Determine grid position
        grid_x = i % 16
        grid_y = i // 16
        x = grid_x * grid_cell_size
        y = grid_y * grid_cell_size

        # Calculate normalized coordinates for upper left
        norm_x1 = grid_x / 16
        norm_y1 = grid_y / 16

        # Calculate normalized coordinates for lower right
        norm_x2 = (grid_x + 1) / 16
        norm_y2 = (grid_y + 1) / 16

        # Append to lists
        txi_font_info.upper_left_coords.append((norm_x1, 1 - norm_y1, 0))
        txi_font_info.lower_right_coords.append((norm_x2, 1 - norm_y2, 0))
        character_widths.append(text_width)
        baseline_heights.append(bbox[1])
    # Check if baseline_heights is not empty to avoid division by zero
    if baseline_heights:
        average_baseline_height: float = sum(baseline_heights) / len(baseline_heights)
        # Normalize the baseline height
        txi_font_info.baselineheight = average_baseline_height / resolution[1]
    if character_widths:
        average_char_width: float = sum(character_widths) / len(character_widths)
        txi_font_info.fontwidth = average_char_width / grid_cell_size
        caret_proportion = 0.1  # Adjust this value as needed
        txi_font_info.caretindent = (average_char_width * caret_proportion) / grid_cell_size

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
