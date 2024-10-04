from __future__ import annotations

import math

from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont

from pykotor.resource.formats.txi import TXIFontInformation
from pykotor.tools.encoding import get_charset_from_singlebyte_encoding

if TYPE_CHECKING:
    import os

    from pykotor.common.language import Language


def calculate_character_metrics(
    pil_font: ImageFont.FreeTypeFont,
    charset_list: list[str],
    baseline_char: str = "0",  # ( 0 should be in every code page )
) -> tuple[int, int, int]:
    """Calculates and returns metrics like baseline height, maximum underhang height, and maximum character height."""
    # Create a temporary image for measurements
    temp_image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_image)

    # Get the bounding box of the baseline character
    baseline_bbox: tuple[int, int, int, int] = temp_draw.textbbox((0, 0), baseline_char, font=pil_font)
    baseline_height: int = baseline_bbox[3] - baseline_bbox[1]

    max_underhang_height: int = 0
    max_char_height: int = 0
    for char in charset_list:
        char_bbox = temp_draw.textbbox((0, 0), char, font=pil_font)

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
    draw_box: bool = False,
    custom_scaling: float = 1.0,
    font_color=None,
):
    target_path = Path(target)
    target_path.mkdir(parents=True, exist_ok=True)

    for font_name in TXIFontInformation.FONT_TEXTURES:
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
    draw_box: bool = False,
    custom_scaling: float = 1.0,
    font_color=None,
):
    """Generates a bitmap font (TGA and TXI) from a TTF font file. Note the default 'draw_boxes', none of these boxes show up in the game (just outside the coords)."""
    if any(resolution) == 0:
        msg = f"resolution must be nonzero, got {resolution}"
        raise ZeroDivisionError(msg)

    font_path, target_path = (Path(p) for p in (font_path, target))
    charset_list: list[str] = get_charset_from_singlebyte_encoding(lang.get_encoding())
    numchars: int = len([char for char in charset_list if char])

    # Calculate grid cell size
    characters_per_column, characters_per_row = math.ceil(math.sqrt(numchars)), math.ceil(math.sqrt(numchars))
    grid_cell_size: int = min(resolution[0] // characters_per_column, resolution[1] // characters_per_row)

    # Using a square grid cell, set the font size to fit within this cell
    pil_font = ImageFont.truetype(str(font_path), grid_cell_size)
    baseline_height, max_underhang_height, max_char_height = calculate_character_metrics(pil_font, charset_list)

    # Calculate total additional height needed for the underhang
    total_additional_height: int = (baseline_height) * characters_per_column
    # Adjust the resolution to include the additional height
    adjusted_resolution: tuple[int, int] = (resolution[0] + total_additional_height, resolution[1] + total_additional_height)

    # Calculate the multiplier
    multiplier_width = adjusted_resolution[0] / resolution[0]
    multiplier_height = adjusted_resolution[1] / resolution[1]

    # Calculate new resolution that will determine character size
    new_original_resolution = (int(resolution[0] / multiplier_width), int(resolution[1] / multiplier_height))

    # Recalculate everything with the new resolution
    font_size = min(new_original_resolution[0] // characters_per_column, new_original_resolution[1] // characters_per_row)
    pil_font = ImageFont.truetype(str(font_path), font_size)
    baseline_height, max_underhang_height, max_char_height = calculate_character_metrics(pil_font, charset_list)

    # Create charset image
    charset_image = Image.new("RGBA", resolution, (0, 0, 0, 0))
    draw = ImageDraw.Draw(charset_image)

    # Initialize the grid position
    grid_x = 0
    grid_y = 0
    upper_left_coords = []
    lower_right_coords = []
    for char in charset_list:
        if not char:  # don't use a cell for characters that can't be drawn.
            # append some coords around blank space (to keep character's byte indexing aligned)
            upper_left_coords.append((0.000001, 0.000001, 0))
            lower_right_coords.append((0.000002, 0.000002, 0))
            continue

        cell_height = resolution[1] / characters_per_row

        # Calculate normalized coordinates for upper left
        norm_x1 = grid_x / characters_per_column
        norm_y1 = (grid_y * cell_height) / resolution[1]
        # Calculate normalized coordinates for lower right
        norm_x2 = (grid_x + 1) / characters_per_row
        norm_y2 = ((grid_y + 1) * cell_height) / resolution[1]

        # Convert normalized coordinates to pixels
        pixel_x1 = norm_x1 * resolution[0]
        pixel_y1 = norm_y1 * resolution[1]
        pixel_x2 = norm_x2 * resolution[0]
        pixel_y2 = norm_y2 * resolution[1]

        # Calculate character height and width
        char_bbox = draw.textbbox((pixel_x1, pixel_y1), char, font=pil_font)
        char_width = char_bbox[2] - char_bbox[0]

        # Draw character. Adjust Y coordinates to move one cell downwards
        if char == "\n":
            draw.text((pixel_x1, pixel_y1 + cell_height - max_underhang_height), char, font=pil_font, fill=font_color or (255, 255, 255, 255))
        else:
            draw.text((pixel_x1, pixel_y1 + cell_height - max_underhang_height), char, anchor="ls", font=pil_font, fill=font_color or (255, 255, 255, 255))

        # Adjust text coordinates
        pixel_x2 = pixel_x1 + char_width
        pixel_y1 = pixel_y2 - max_char_height

        # Draw a red rectangle around the character based on actual text dimensions
        if draw_box:
            draw.rectangle((pixel_x1, pixel_y1, pixel_x2, pixel_y2), outline="red")

        # Calculate normalized coordinates
        norm_x1 = pixel_x1 / resolution[0]
        norm_y1 = pixel_y1 / resolution[1]
        norm_x2 = pixel_x2 / resolution[0]
        norm_y2 = pixel_y2 / resolution[1]

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
    txi_font_info.isdoublebyte = not lang.is_8bit_encoding()  # does nothing ingame?
    # txi_font_info.numchars = numchars
    txi_font_info.upper_left_coords = upper_left_coords
    txi_font_info.lower_right_coords = lower_right_coords
    # Normalize and set font metrics
    txi_font_info.set_font_metrics(resolution, max_char_height, baseline_height, custom_scaling)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    charset_image.save(target_path.with_suffix(".tga"), format="TGA")

    # Generate and save the TXI data
    txi_target = target_path.with_suffix(".txi")
    with txi_target.open("w", encoding="utf-8") as txi_file:
        txi_file.write(str(txi_font_info))
