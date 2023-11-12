from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

from pykotor.common.geometry import Vector2
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
def write_bitmap_font(target: os.PathLike | str, font_path: str, resolution: tuple[int, int]) -> None:
    """Generates a bitmap font from a TTF font file.

    Args:
    ----
        target: Path or filename to save the font files
        font_path: Path to the TTF font file
        resolution: Tuple of texture width and height in pixels
    Returns:
        None

    Processing Logic:
    - Loads the TTF font and calculates grid cell size
    - Renders each character to the texture image
    - Calculates character UV coordinates
    - Saves texture image and generates TXI font data file
    """
    target_path = Path(target)
    txi_font_info = TXIFontInformation()

    # Set the texture resolution
    txi_font_info.texturewidth, txi_font_info.fontheight = resolution

    # Calculate grid cell size for a 16x16 grid
    characters_per_row = 16
    grid_cell_size = min(resolution[0] // characters_per_row, resolution[1] // characters_per_row)

    # Assuming a square grid cell, set the font size to fit within the cell
    font_size = grid_cell_size - 4  # Subtracting a bit for padding
    pil_font = ImageFont.truetype(font_path, font_size)

    # Create charset image
    charset_image = Image.new("RGBA", resolution, (0, 0, 0, 0))
    draw = ImageDraw.Draw(charset_image)

    cols = []
    rows = []
    x, y = 0, 0
    for i in range(256):  # Standard ASCII set
        char = chr(i)
        # Calculate bounding box
        bbox = draw.textbbox((0, 0), char, font=pil_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = x + (grid_cell_size - text_width) // 2
        text_y = y + (grid_cell_size - text_height) // 2

        draw.text((text_x, text_y), char, font=pil_font, fill=(255, 255, 255, 255))

        # Update cols for each character
        cols.append(Vector2(x / txi_font_info.texturewidth, y / txi_font_info.fontheight))

        x += grid_cell_size
        if x >= resolution[0]:
            x = 0
            y += grid_cell_size
            # Update rows at the start of each new line
            rows.append(Vector2(0, y / txi_font_info.fontheight))

    # Set cols and rows in txi_font_info
    txi_font_info.cols = cols
    txi_font_info.rows = rows

    charset_image.save(target_path, format="TGA")

    # Generate and save the TXI data
    txi_data = _generate_txi_data(txi_font_info)
    txi_target = target_path.with_suffix(".txi")
    with txi_target.open("w") as txi_file:
        txi_file.write(txi_data)


def _generate_txi_data(txi_font_info: TXIFontInformation) -> str:
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
{f' 0{os.linesep}'.join(str(v) for v in txi_font_info.cols)}
lowerrightcoords {txi_font_info.lowerrightcoords}
{f' 0{os.linesep}'.join(str(v) for v in txi_font_info.rows)}"""


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
