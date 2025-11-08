from __future__ import annotations


def rotate_rgb_rgba(data: bytearray, width: int, height: int, bytes_per_pixel: int, times: int) -> bytearray:
    """Rotate RGB/BGR/RGBA/BGRA image data in 90° steps, clock-wise for positive times, counter-clockwise for negative times.

    :param data: The image data as a bytearray
    :param width: The width of the image
    :param height: The height of the image
    :param bytes_per_pixel: The number of bytes per pixel (3 for RGB/BGR, 4 for RGBA/BGRA)
    :param times: The number of 90° rotations to perform (positive for clockwise, negative for counter-clockwise)
    :return: The rotated image data as a bytearray
    """
    times = times % 4  # Normalize to 0-3 range
    if times == 0:
        return data

    new_data = bytearray(len(data))

    for y in range(height):
        for x in range(width):
            src_idx = (y * width + x) * bytes_per_pixel
            if times in (1, -3):
                dst_idx = ((width - 1 - x) * height + y) * bytes_per_pixel
            elif times in (2, -2):
                dst_idx = ((height - 1 - y) * width + (width - 1 - x)) * bytes_per_pixel
            elif times in (3, -1):
                dst_idx = (x * height + (height - 1 - y)) * bytes_per_pixel
            else:
                dst_idx = src_idx  # This case should never happen due to the normalization, but it satisfies the type checker

            for i in range(bytes_per_pixel):
                new_data[dst_idx + i] = data[src_idx + i]

    return new_data

def flip_vertically_rgb_rgba(data: bytearray, width: int, height: int, bytes_per_pixel: int) -> bytearray:
    """Flip RGB/BGR/RGBA/BGRA image data vertically.

    :param data: The image data as a bytearray
    :param width: The width of the image
    :param height: The height of the image
    :param bytes_per_pixel: The number of bytes per pixel (3 for RGB/BGR, 4 for RGBA/BGRA)
    :return: The vertically flipped image data as a bytearray
    """
    new_data = bytearray(len(data))
    row_size = width * bytes_per_pixel

    for y in range(height):
        src_row_start = y * row_size
        dst_row_start = (height - 1 - y) * row_size
        new_data[dst_row_start:dst_row_start + row_size] = data[src_row_start:src_row_start + row_size]

    return new_data

def flip_horizontally_rgb_rgba(data: bytearray, width: int, height: int, bytes_per_pixel: int) -> bytearray:
    """Flip RGB/BGR/RGBA/BGRA image data horizontally.

    :param data: The image data as a bytearray
    :param width: The width of the image
    :param height: The height of the image
    :param bytes_per_pixel: The number of bytes per pixel (3 for RGB/BGR, 4 for RGBA/BGRA)
    :return: The horizontally flipped image data as a bytearray
    """
    new_data = bytearray(len(data))
    row_size = width * bytes_per_pixel

    for y in range(height):
        row_start = y * row_size
        for x in range(width):
            src_pixel_start = row_start + x * bytes_per_pixel
            dst_pixel_start = row_start + (width - 1 - x) * bytes_per_pixel
            for i in range(bytes_per_pixel):
                new_data[dst_pixel_start + i] = data[src_pixel_start + i]

    return new_data
