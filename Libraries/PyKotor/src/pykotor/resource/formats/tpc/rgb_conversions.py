from __future__ import annotations


def rgb_to_rgba(data: bytearray | bytes, width: int, height: int) -> bytearray:
    new_data = bytearray()
    for i in range(0, len(data), 3):
        new_data.extend(data[i:i+3])  # Copy RGB values
        new_data.append(255)  # Add fully opaque alpha
    return new_data


def rgba_to_rgb(data: bytearray | bytes, width: int, height: int) -> bytearray:
    new_data = bytearray()
    for i in range(0, len(data), 4):
        new_data.extend(data[i:i+3])  # Copy only RGB values, skip alpha
    return new_data


def grey_to_rgb(data: bytearray | bytes, width: int, height: int) -> bytearray:
    new_data = bytearray()
    for pixel in data:
        new_data.extend([pixel, pixel, pixel])  # Repeat greyscale value for R, G, and B
    return new_data


def grey_to_rgba(data: bytearray | bytes, width: int, height: int) -> bytearray:
    new_data = bytearray()
    for pixel in data:
        new_data.extend([pixel, pixel, pixel, 255])  # Repeat greyscale value for R, G, and B, add opaque alpha
    return new_data


def rgba_to_grey(data: bytearray | bytes, width: int, height: int) -> bytearray:
    new_data = bytearray()
    for i in range(0, len(data), 4):
        r, g, b = data[i], data[i+1], data[i+2]
        grey = int(0.299 * r + 0.587 * g + 0.114 * b)
        new_data.append(grey)
    return new_data


def rgb_to_grey(data: bytearray | bytes, width: int, height: int) -> bytearray:
    new_data = bytearray()
    for i in range(0, len(data), 3):
        r, g, b = data[i], data[i+1], data[i+2]
        grey = int(0.299 * r + 0.587 * g + 0.114 * b)
        new_data.append(grey)
    return new_data
