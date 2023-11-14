from __future__ import annotations

import contextlib

with contextlib.suppress(ImportError):
    from PIL import Image, ImageDraw, ImageFont  # HACK: fix later

from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader
from pykotor.helpers.path import Path
from pykotor.resource.formats.tpc import (
    TPC,
    TPCBinaryReader,
    TPCBinaryWriter,
    TPCBMPWriter,
    TPCTGAReader,
    TPCTGAWriter,
)
from pykotor.resource.formats.tpc.txi_data import TXIFontInformation
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType
from pykotor.tools.path import CaseAwarePath

if TYPE_CHECKING:
    import os

    from pykotor.common.language import Language


def detect_tpc(
    source: SOURCE_TYPES | object,
    offset: int = 0,
) -> ResourceType:
    """Returns what format the TPC data is believed to be in. This function performs a basic check and does not guarantee
    accuracy of the result or integrity of the data.

    Args:
    ----
        source: Source of the TPC data.
        offset: Offset into the source data.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.

    Returns:
    -------
        The format of the TPC data.
    """

    def do_check(
        first100: bytes,
    ) -> ResourceType:
        file_format = ResourceType.TPC
        if len(first100) < 100:
            file_format = ResourceType.TGA
        else:
            for i in range(15, 100):
                if first100[i] != 0:
                    file_format = ResourceType.TGA
        return file_format

    try:
        if isinstance(source, (str, CaseAwarePath)):
            with BinaryReader.from_file(source, offset) as reader:
                file_format = do_check(reader.read_bytes(100))
        elif isinstance(source, (bytes, bytearray)):
            file_format = do_check(source[:100])
        elif isinstance(source, BinaryReader):
            file_format = do_check(source.read_bytes(100))
            source.skip(-100)
        else:
            file_format = ResourceType.INVALID
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        raise
    except OSError:
        file_format = ResourceType.INVALID

    return file_format


def read_tpc(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> TPC:
    """Returns an TPC instance from the source. The file format (TPC or TGA) is automatically determined before
    parsing the data.

    Args:
    ----
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.
        ValueError: If the file was corrupted or the format could not be determined.

    Returns:
    -------
        An TPC instance.
    """
    file_format = detect_tpc(source, offset)

    if file_format is ResourceType.INVALID:
        msg = "Failed to determine the format of the GFF file."
        raise ValueError(msg)

    if file_format == ResourceType.TPC:
        return TPCBinaryReader(source, offset, size or 0).load()
    if file_format == ResourceType.TGA:
        return TPCTGAReader(source, offset, size or 0).load()
    return None


def write_tpc(
    tpc: TPC,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.TPC,
) -> None:
    """Writes the TPC data to the target location with the specified format (TPC, TGA or BMP).

    Args:
    ----
        tpc: The TPC file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
    ------
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if file_format == ResourceType.TGA:
        TPCTGAWriter(tpc, target).write()
    elif file_format == ResourceType.BMP:
        TPCBMPWriter(tpc, target).write()
    elif file_format == ResourceType.TPC:
        TPCBinaryWriter(tpc, target).write()
    else:
        msg = "Unsupported format specified; use TPC, TGA or BMP."
        raise ValueError(msg)

# TODO: this is still a WIP
def write_bitmap_font(target: os.PathLike | str, font_path: str, resolution: tuple[int, int], lang: Language) -> None:
    """Generates a bitmap font from a TTF font file."""
    target_path = Path(target)
    txi_font_info = TXIFontInformation()

    # idk
    txi_font_info.spacingR = 0.0

    # Set the texture resolution in proportion
    txi_font_info.texturewidth = resolution[0] / max(resolution)
    txi_font_info.fontheight = resolution[1] / max(resolution)

    # Calculate grid cell size for a 16x16 grid
    characters_per_row = 16
    grid_cell_size = min(resolution[0] // characters_per_row, resolution[1] // characters_per_row)

    # Assuming a square grid cell, set the font size to fit within the cell
    font_size = grid_cell_size - 4  # Subtracting a bit for padding
    pil_font = ImageFont.truetype(font_path, font_size)

    # Create charset image
    charset_image = Image.new("RGBA", resolution, (0, 0, 0, 0))
    draw = ImageDraw.Draw(charset_image)

    baseline_heights = []
    character_widths = []
    txi_font_info.upper_left_coords = []
    txi_font_info.lower_right_coords = []

    x, y = 0, 0
    for i in range(256):  # Standard ASCII set
        char = bytes([i]).decode(lang.get_encoding(), errors="replace")
        bbox = draw.textbbox((0, 0), char, font=pil_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = x + (grid_cell_size - text_width) // 2
        text_y = y + (grid_cell_size - text_height) // 2

        draw.text((text_x, text_y), char, language=lang.get_bcp47_code(), font=pil_font, fill=(255, 255, 255, 255))

        # Calculate normalized coordinates
        norm_x1 = text_x / resolution[0]
        norm_y1 = text_y / resolution[1]
        norm_x2 = (text_x + text_width) / resolution[0]
        norm_y2 = (text_y + text_height) / resolution[1]

        # Determine grid position
        grid_x = i % 16
        grid_y = i // 16

        # Calculate normalized coordinates for upper left
        norm_x1 = grid_x / 16
        norm_y1 = grid_y / 16

        # Calculate normalized coordinates for lower right
        norm_x2 = (grid_x + 1) / 16
        norm_y2 = (grid_y + 1) / 16

        # Append to lists
        txi_font_info.upper_left_coords.append((norm_x1, 1 - norm_y1, 0))
        txi_font_info.lower_right_coords.append((norm_x2, 1 - norm_y2, 0))
        baseline_heights.append(bbox[1])
        character_widths.append(text_width)

    if character_widths:
        average_char_width = sum(character_widths) / len(character_widths)
        txi_font_info.fontwidth = average_char_width / grid_cell_size
        caret_proportion = 0.1  # Adjust this value as needed
        txi_font_info.caretindent = (average_char_width * caret_proportion) / grid_cell_size

    # Check if baseline_heights is not empty to avoid division by zero
    if baseline_heights:
        average_baseline_height = sum(baseline_heights) / len(baseline_heights)
        # Normalize the baseline height
        txi_font_info.baselineheight = average_baseline_height / resolution[1]

    charset_image.save(target_path, format="TGA")

    # Generate and save the TXI data
    txi_data = _generate_txi_data(txi_font_info)
    txi_target = target_path.with_suffix(".txi")
    with txi_target.open("w") as txi_file:
        txi_file.write(txi_data)


def _generate_txi_data(txi_font_info: TXIFontInformation) -> str:
    # Format the upper left coordinates
    ul_coords_str = "\n".join([f"{x:.6f} {y:.6f} {z}" for x, y, z in txi_font_info.upper_left_coords])

    # Format the lower right coordinates
    lr_coords_str = "\n".join([f"{x:.6f} {y:.6f} {z}" for x, y, z in txi_font_info.lower_right_coords])
    return f"""mipmap {txi_font_info.mipmap}
filter {txi_font_info.filter}
numchars {txi_font_info.numchars}
fontheight {txi_font_info.fontheight}
baselineheight {txi_font_info.baselineheight}
texturewidth {txi_font_info.texturewidth}
fontwidth {txi_font_info.fontwidth}
spacingR {txi_font_info.spacingR}
spacingB {txi_font_info.spacingB}
caretindent {txi_font_info.caretindent}
isdoublebyte {txi_font_info.isdoublebyte}
upperleftcoords {txi_font_info.upperleftcoords}
{ul_coords_str}
lowerrightcoords {txi_font_info.lowerrightcoords}
{lr_coords_str}"""


def bytes_tpc(
    tpc: TPC,
    file_format: ResourceType = ResourceType.TPC,
) -> bytes:
    """Returns the TPC data in the specified format (TPC, TGA or BMP) as a bytes object.

    This is a convenience method that wraps the write_tpc() method.

    Args:
    ----
        tpc: The target TPC object.
        file_format: The file format.

    Raises:
    ------
        ValueError: If the specified format was unsupported.

    Returns:
    -------
        The TPC data.
    """
    data = bytearray()
    write_tpc(tpc, data, file_format)
    return data
