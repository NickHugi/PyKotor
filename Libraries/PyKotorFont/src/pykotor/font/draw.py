from __future__ import annotations

import math

from pathlib import Path
from typing import TYPE_CHECKING, Any

from PIL import Image, ImageDraw, ImageFont

from pykotor.resource.formats.txi.txi_data import TXIFontInformation
from pykotor.tools.encoding import get_charset_from_singlebyte_encoding

if TYPE_CHECKING:
    import os

    from pykotor.common.language import Language


class _FontMetrics:
    """Internal class for font metric calculations."""

    def __init__(
        self,
        pil_font: ImageFont.FreeTypeFont,
        charset_list: list[str],
        baseline_char: str = "0",
    ):
        self.pil_font: ImageFont.FreeTypeFont = pil_font
        self.charset_list: list[str] = charset_list
        self.baseline_char: str = baseline_char
        self.baseline_height: int
        self.max_underhang_height: int
        self.max_char_height: int
        self.baseline_height, self.max_underhang_height, self.max_char_height = self._calculate_metrics()

    def _calculate_metrics(self) -> tuple[int, int, int]:
        temp_image: Image.Image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        temp_draw: ImageDraw.ImageDraw = ImageDraw.Draw(temp_image)

        baseline_bbox: tuple[float, float, float, float] = temp_draw.textbbox((0, 0), self.baseline_char, font=self.pil_font)
        baseline_height: int = int(baseline_bbox[3] - baseline_bbox[1])

        max_underhang_height: int = 0
        max_char_height: int = 0

        for char in self.charset_list:
            if not char:
                continue

            char_bbox: tuple[float, float, float, float] = temp_draw.textbbox((0, 0), char, font=self.pil_font)
            underhang_height: int = int(char_bbox[3] - baseline_bbox[3])
            char_height: int = int(char_bbox[3] - char_bbox[1])

            max_underhang_height: int = max(max_underhang_height, underhang_height)
            max_char_height: int = max(max_char_height, char_height + underhang_height)

        return baseline_height, max_underhang_height, max_char_height


class _BitmapGrid:
    """Internal class for grid calculations."""

    def __init__(self, resolution: tuple[int, int], num_chars: int):
        if any(r == 0 for r in resolution):
            msg = f"resolution must be nonzero, got {resolution}"
            raise ZeroDivisionError(msg)

        self.resolution: tuple[int, int] = resolution
        self.num_chars: int = num_chars
        self.chars_per_col: int = math.ceil(math.sqrt(num_chars))
        self.chars_per_row: int = math.ceil(math.sqrt(num_chars))
        self.cell_size: int = min(
            resolution[0] // self.chars_per_row,
            resolution[1] // self.chars_per_col
        )
        self.cell_height: float = resolution[1] / self.chars_per_row


def write_bitmap_font(
    target: os.PathLike | str,
    font_path: os.PathLike | str,
    resolution: tuple[int, int],
    lang: Language,
    custom_scaling: float = 1.0,
    font_color=None,  # noqa: ANN001
    *,
    draw_debug_box: bool | None = None,
    draw_box: bool | None = None,
):
    """Generates a bitmap font (TGA and TXI) from a TTF font file. Note the default 'draw_boxes', none of these boxes show up in the game (just outside the coords)."""
    if any(resolution) == 0:
        msg = f"resolution must be nonzero, got {resolution}"
        raise ZeroDivisionError(msg)

    font_path, target_path = (Path(p) for p in (font_path, target))
    charset_list: list[str] = get_charset_from_singlebyte_encoding(lang.get_encoding() or "")
    num_chars: int = len([char for char in charset_list if char])

    # Calculate grid cell size
    grid = _BitmapGrid(resolution, num_chars)
    characters_per_column = grid.chars_per_col
    characters_per_row = grid.chars_per_row
    grid_cell_size: int = grid.cell_size

    # Using a square grid cell, set the font size to fit within this cell
    pil_font: ImageFont.FreeTypeFont = ImageFont.truetype(str(font_path), grid_cell_size)
    metrics: _FontMetrics = _FontMetrics(pil_font, charset_list)

    # Calculate total additional height needed for the underhang
    total_additional_height: int = (metrics.baseline_height) * characters_per_column
    # Adjust the resolution to include the additional height
    adjusted_resolution: tuple[int, int] = (resolution[0] + total_additional_height, resolution[1] + total_additional_height)

    # Calculate the multiplier
    multiplier_width: float = adjusted_resolution[0] / resolution[0]
    multiplier_height: float = adjusted_resolution[1] / resolution[1]

    # Calculate new resolution that will determine character size
    new_original_resolution: tuple[int, int] = (int(resolution[0] / multiplier_width), int(resolution[1] / multiplier_height))

    # Recalculate everything with the new resolution
    font_size: int = min(new_original_resolution[0] // characters_per_column, new_original_resolution[1] // characters_per_row)
    pil_font: ImageFont.FreeTypeFont = ImageFont.truetype(str(font_path), font_size)
    metrics: _FontMetrics = _FontMetrics(pil_font, charset_list)

    # Determine debug behavior
    debug_flag: bool = draw_debug_box if draw_debug_box is not None else bool(draw_box)

    # Create charset image
    charset_image: Image.Image = Image.new("RGBA", resolution, (0, 0, 0, 0))
    draw: ImageDraw.ImageDraw = ImageDraw.Draw(charset_image)

    # Initialize the grid position
    grid_x = 0
    grid_y = 0
    upper_left_coords: list[tuple[float, float, int]] = []
    lower_right_coords: list[tuple[float, float, int]] = []
    for char in charset_list:
        if not char:  # don't use a cell for characters that can't be drawn.
            # append some coords around blank space (to keep character's byte indexing aligned)
            upper_left_coords.append((0.000001, 0.000001, 0))
            lower_right_coords.append((0.000002, 0.000002, 0))
            continue
        cell_height: float = grid.cell_height

        # Calculate normalized coordinates for upper left
        norm_x1: float = grid_x / characters_per_column
        norm_y1: float = (grid_y * cell_height) / resolution[1]
        # Calculate normalized coordinates for lower right
        norm_x2: float = (grid_x + 1) / characters_per_row
        norm_y2: float = ((grid_y + 1) * cell_height) / resolution[1]

        # Convert normalized coordinates to pixels
        pixel_x1: float = norm_x1 * resolution[0]
        pixel_y1: float = norm_y1 * resolution[1]
        pixel_x2: float = norm_x2 * resolution[0]
        pixel_y2: float = norm_y2 * resolution[1]

        # Calculate character height and width
        char_bbox: tuple[int, int, int, int] = draw.textbbox((pixel_x1, pixel_y1), char, font=pil_font)
        char_width: int = char_bbox[2] - char_bbox[0]

        # Draw character. Adjust Y coordinates to move one cell downwards
        if char == "\n":
            draw.text((pixel_x1, pixel_y1 + cell_height - metrics.max_underhang_height), char, font=pil_font, fill=font_color or (255, 255, 255, 255))
        else:
            draw.text((pixel_x1, pixel_y1 + cell_height - metrics.max_underhang_height), char, anchor="ls", font=pil_font, fill=font_color or (255, 255, 255, 255))

        # Adjust text coordinates
        pixel_x2 = pixel_x1 + char_width
        pixel_y1 = pixel_y2 - metrics.max_char_height

        # Draw a red rectangle around the character based on actual text dimensions
        if debug_flag:
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
        grid_x: int = (grid_x + 1) % characters_per_row
        if grid_x == 0:
            grid_y += 1

    # Build txi fields
    txi_font_info = TXIFontInformation()
    txi_font_info.isdoublebyte = not lang.is_8bit_encoding()  # does nothing ingame?
    # txi_font_info.numchars = numchars
    txi_font_info.upper_left_coords = upper_left_coords
    txi_font_info.lower_right_coords = lower_right_coords
    # Normalize and set font metrics
    txi_font_info.set_font_metrics(resolution, metrics.max_char_height, metrics.baseline_height, custom_scaling)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    charset_image.save(target_path.with_suffix(".tga"), format="TGA")

    # Generate and save the TXI data
    target_path.with_suffix(".txi").write_text(str(txi_font_info), encoding="utf-8")


def write_bitmap_fonts(
    target: os.PathLike | str,
    font_path: os.PathLike | str,
    resolution: tuple[int, int],
    lang: Language,
    draw_box: bool = False,
    custom_scaling: float = 1.0,
    font_color: Any | None = None,
    *,
    draw_debug_box: bool | None = None,
) -> None:
    """Generate bitmap fonts for all KotOR font textures.

    Args:
        target: Directory where the output files should be saved
        font_path: Path to the TTF font file
        resolution: Tuple of (width, height) for the bitmap
        lang: Language for character encoding
        draw_box: Whether to draw debug boxes around characters (alias for draw_debug_box)
        custom_scaling: Custom scaling factor for the font
        font_color: RGBA color tuple for the font (default: white)
    """
    target_path: Path = Path(target)
    target_path.mkdir(parents=True, exist_ok=True)

    for font_name in TXIFontInformation.FONT_TEXTURES:
        if font_name == "fnt_console":
            continue

        write_bitmap_font(
            target_path / font_name,
            font_path,
            resolution,
            lang,
            custom_scaling,
            font_color,
            draw_debug_box=draw_debug_box,
            draw_box=draw_box,
        )
