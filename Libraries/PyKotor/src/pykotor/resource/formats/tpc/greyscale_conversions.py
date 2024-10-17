from __future__ import annotations


def grey_to_rgba(data: bytearray | bytes, width: int, height: int) -> bytearray:
    new_data = bytearray()
    for brightness in data:
        new_data.extend([brightness, brightness, brightness, 255])
    return new_data


def grey_to_rgb(data: bytearray | bytes, width: int, height: int) -> bytearray:
    new_data = bytearray()
    for brightness in data:
        new_data.extend([brightness, brightness, brightness])
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
