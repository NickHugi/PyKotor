from __future__ import annotations


def rotate_dxt1(
    data: bytearray,
    width: int,
    height: int,
    times: int,
) -> bytearray:
    """Rotate DXT1 compressed image data in 90° steps, clock-wise for positive times, counter-clockwise for negative times.

    :param data: The DXT1 compressed image data as a bytearray
    :param width: The width of the image (must be a multiple of 4)
    :param height: The height of the image (must be a multiple of 4)
    :param times: The number of 90° rotations to perform (positive for clockwise, negative for counter-clockwise)
    :return: The rotated DXT1 compressed image data as a bytearray
    """
    times = times % 4
    if times == 0:
        return data

    blocks_x: int = width // 4
    blocks_y: int = height // 4
    new_data = bytearray(len(data))

    for by in range(blocks_y):
        for bx in range(blocks_x):
            src_block_idx: int = (by * blocks_x + bx) * 8
            dst_block_idx = src_block_idx
            if times in (1, -3):
                dst_block_idx = ((blocks_x - 1 - bx) * blocks_y + by) * 8
            elif times in (2, -2):
                dst_block_idx = ((blocks_y - 1 - by) * blocks_x + (blocks_x - 1 - bx)) * 8
            elif times in (3, -1):
                dst_block_idx = (bx * blocks_y + (blocks_y - 1 - by)) * 8
            else:
                dst_block_idx = src_block_idx

            # Copy color data
            new_data[dst_block_idx : dst_block_idx + 4] = data[src_block_idx : src_block_idx + 4]

            # Rotate pixel indices
            pixels: int = int.from_bytes(data[src_block_idx + 4 : src_block_idx + 8], "little")
            rotated_pixels = 0
            for i in range(16):
                src_pixel: int = (pixels >> (i * 2)) & 0b11
                if times in (1, -3):
                    dst_pixel = ((i % 4) * 4 + (3 - i // 4)) * 2
                elif times in (2, -2):
                    dst_pixel = (15 - i) * 2
                elif times in (3, -1):
                    dst_pixel = ((3 - i % 4) * 4 + (i // 4)) * 2
                else:
                    dst_pixel = i * 2
                rotated_pixels |= src_pixel << dst_pixel

            new_data[dst_block_idx + 4 : dst_block_idx + 8] = rotated_pixels.to_bytes(4, "little")

    return new_data


def rotate_dxt5(
    data: bytearray,
    width: int,
    height: int,
    times: int,
) -> bytearray:
    """Rotate DXT5 compressed image data in 90° steps, clock-wise for positive times, counter-clockwise for negative times.

    :param data: The DXT5 compressed image data as a bytearray
    :param width: The width of the image (must be a multiple of 4)
    :param height: The height of the image (must be a multiple of 4)
    :param times: The number of 90° rotations to perform (positive for clockwise, negative for counter-clockwise)
    :return: The rotated DXT5 compressed image data as a bytearray
    """
    times = times % 4
    if times == 0:
        return data

    blocks_x: int = width // 4
    blocks_y: int = height // 4
    new_data = bytearray(len(data))

    for by in range(blocks_y):
        for bx in range(blocks_x):
            src_block_idx: int = (by * blocks_x + bx) * 16
            dst_block_idx: int = src_block_idx  # Default value, will be overwritten
            if times in (1, -3):
                dst_block_idx = ((blocks_x - 1 - bx) * blocks_y + by) * 16
            elif times in (2, -2):
                dst_block_idx = ((blocks_y - 1 - by) * blocks_x + (blocks_x - 1 - bx)) * 16
            elif times in (3, -1):
                dst_block_idx = (bx * blocks_y + (blocks_y - 1 - by)) * 16
            else:
                dst_block_idx = src_block_idx

            # Copy alpha min/max
            new_data[dst_block_idx : dst_block_idx + 2] = data[src_block_idx : src_block_idx + 2]

            # Rotate alpha indices
            alpha_indices: int = int.from_bytes(data[src_block_idx + 2 : src_block_idx + 8], "little")
            rotated_alpha = 0
            for i in range(16):
                src_alpha = (alpha_indices >> (i * 3)) & 0b111
                if times in (1, -3):
                    dst_alpha = ((i % 4) * 4 + (3 - i // 4)) * 3
                elif times in (2, -2):
                    dst_alpha = (15 - i) * 3
                elif times in (3, -1):
                    dst_alpha = ((3 - i % 4) * 4 + (i // 4)) * 3
                else:
                    dst_alpha = i * 3
                rotated_alpha |= src_alpha << dst_alpha

            new_data[dst_block_idx + 2 : dst_block_idx + 8] = rotated_alpha.to_bytes(6, "little")

            # Copy color data
            new_data[dst_block_idx + 8 : dst_block_idx + 12] = data[src_block_idx + 8 : src_block_idx + 12]

            # Rotate color indices (same as DXT1)
            pixels: int = int.from_bytes(data[src_block_idx + 12 : src_block_idx + 16], "little")
            rotated_pixels = 0
            for i in range(16):
                src_pixel = (pixels >> (i * 2)) & 0b11
                if times in (1, -3):
                    dst_pixel = ((i % 4) * 4 + (3 - i // 4)) * 2
                elif times in (2, -2):
                    dst_pixel = (15 - i) * 2
                elif times in (3, -1):
                    dst_pixel = ((3 - i % 4) * 4 + (i // 4)) * 2
                else:
                    dst_pixel = i * 2
                rotated_pixels |= src_pixel << dst_pixel

            new_data[dst_block_idx + 12 : dst_block_idx + 16] = rotated_pixels.to_bytes(4, "little")

    return new_data


def flip_vertically_dxt(
    data: bytearray,
    width: int,
    height: int,
    block_size: int,
) -> bytearray:
    """Flip DXT1 or DXT5 compressed image data vertically.

    :param data: The DXT compressed image data as a bytearray
    :param width: The width of the image (must be a multiple of 4)
    :param height: The height of the image (must be a multiple of 4)
    :param block_size: The size of each block in bytes (8 for DXT1, 16 for DXT5)
    :return: The vertically flipped DXT compressed image data as a bytearray
    """
    blocks_x: int = width // 4
    blocks_y: int = height // 4
    new_data = bytearray(len(data))

    for by in range(blocks_y):
        src_row_start: int = by * blocks_x * block_size
        dst_row_start: int = (blocks_y - 1 - by) * blocks_x * block_size
        new_data[dst_row_start : dst_row_start + blocks_x * block_size] = data[src_row_start : src_row_start + blocks_x * block_size]

    return new_data


def flip_horizontally_dxt(
    data: bytearray,
    width: int,
    height: int,
    bytes_per_block: int,
) -> bytearray:
    """Flip DXT1 or DXT5 compressed image data horizontally.

    :param data: The DXT compressed image data as a bytearray
    :param width: The width of the image (must be a multiple of 4)
    :param height: The height of the image (must be a multiple of 4)
    :param bytes_per_block: The number of bytes per block (8 for DXT1, 16 for DXT3/DXT5)
    :return: The horizontally flipped DXT compressed image data as a bytearray
    """
    blocks_x: int = width // 4
    blocks_y: int = height // 4
    new_data = bytearray(len(data))

    for by in range(blocks_y):
        for bx in range(blocks_x):
            src_block_idx: int = (by * blocks_x + bx) * bytes_per_block
            dst_block_idx: int = (by * blocks_x + (blocks_x - 1 - bx)) * bytes_per_block

            # Copy block data
            new_data[dst_block_idx : dst_block_idx + bytes_per_block] = data[src_block_idx : src_block_idx + bytes_per_block]

            # Flip pixel indices horizontally
            if bytes_per_block == 8:  # DXT1
                pixels: int = int.from_bytes(new_data[dst_block_idx + 4 : dst_block_idx + 8], "little")
                flipped_pixels = 0
                for i in range(4):
                    row = (pixels >> (i * 8)) & 0xFF
                    flipped_row = ((row & 0b11) << 6) | ((row & 0b1100) << 2) | ((row & 0b110000) >> 2) | ((row & 0b11000000) >> 6)
                    flipped_pixels |= flipped_row << (i * 8)
                new_data[dst_block_idx + 4 : dst_block_idx + 8] = flipped_pixels.to_bytes(4, "little")
            elif bytes_per_block == 16:  # DXT5
                # Flip alpha indices
                alpha_indices = int.from_bytes(new_data[dst_block_idx + 2 : dst_block_idx + 8], "little")
                flipped_alpha = 0
                for i in range(4):
                    row = (alpha_indices >> (i * 12)) & 0xFFF
                    flipped_row = ((row & 0b111) << 9) | ((row & 0b111000) << 3) | ((row & 0b111000000) >> 3) | ((row & 0b111000000000) >> 9)
                    flipped_alpha |= flipped_row << (i * 12)
                new_data[dst_block_idx + 2 : dst_block_idx + 8] = flipped_alpha.to_bytes(6, "little")

                # Flip color indices (same as DXT1)
                pixels = int.from_bytes(new_data[dst_block_idx + 12 : dst_block_idx + 16], "little")
                flipped_pixels = 0
                for i in range(4):
                    row = (pixels >> (i * 8)) & 0xFF
                    flipped_row = ((row & 0b11) << 6) | ((row & 0b1100) << 2) | ((row & 0b110000) >> 2) | ((row & 0b11000000) >> 6)
                    flipped_pixels |= flipped_row << (i * 8)
                new_data[dst_block_idx + 12 : dst_block_idx + 16] = flipped_pixels.to_bytes(4, "little")

    return new_data
