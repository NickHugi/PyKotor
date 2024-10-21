from __future__ import annotations


def bgra_to_grey(data: bytearray | bytes) -> bytearray:
    new_data = bytearray()
    for i in range(0, len(data), 4):
        b, g, r = data[i], data[i + 1], data[i + 2]
        grey = int(0.299 * r + 0.587 * g + 0.114 * b)
        new_data.append(grey)
    return new_data


def bgra_to_rgb(data: bytearray | bytes) -> bytearray:
    new_data = bytearray()
    for i in range(0, len(data), 4):
        new_data.extend([data[i + 2], data[i + 1], data[i]])  # Swap B and R, skip alpha
    return new_data


def rgba_to_bgra(data: bytes | bytearray) -> bytearray:
    new_data = bytearray()
    for i in range(0, len(data), 4):
        new_data.extend([data[i + 2], data[i + 1], data[i], data[i + 3]])  # Swap R and B
    return new_data


def bgra_to_rgba(data: bytearray | bytes) -> bytearray:
    new_data = bytearray()
    for i in range(0, len(data), 4):
        new_data.extend([data[i + 2], data[i + 1], data[i], data[i + 3]])  # Swap B and R
    return new_data


def bgr_to_rgb(data: bytearray | bytes) -> bytearray:
    new_data = bytearray()
    for i in range(0, len(data), 3):
        new_data.extend([data[i + 2], data[i + 1], data[i]])  # Swap B and R
    return new_data


def bgr_to_grey(data: bytearray | bytes) -> bytearray:
    new_data = bytearray()
    for i in range(0, len(data), 3):
        b, g, r = data[i], data[i + 1], data[i + 2]
        grey = int(0.299 * r + 0.587 * g + 0.114 * b)
        new_data.append(grey)
    return new_data


def rgb_to_bgr(data: bytearray | bytes) -> bytearray:
    new_data = bytearray()
    for i in range(0, len(data), 3):
        new_data.extend([data[i + 2], data[i + 1], data[i]])  # Swap R and B
    return new_data


def bgr_to_bgra(data: bytearray | bytes) -> bytearray:
    new_data = bytearray()
    for i in range(0, len(data), 3):
        new_data.extend([data[i], data[i + 1], data[i + 2], 255])  # Add alpha channel
    return new_data


def bgra_to_bgr(data: bytearray | bytes) -> bytearray:
    new_data = bytearray()
    for i in range(0, len(data), 4):
        new_data.extend([data[i], data[i + 1], data[i + 2]])  # Remove alpha channel
    return new_data


def rgb_to_bgra(data: bytearray | bytes) -> bytearray:
    new_data = bytearray()
    for i in range(0, len(data), 3):
        new_data.extend([data[i + 2], data[i + 1], data[i], 255])  # Swap R and B, add alpha channel
    return new_data


def bgr_to_rgba(data: bytearray | bytes) -> bytearray:
    new_data = bytearray()
    for i in range(0, len(data), 3):
        new_data.extend([data[i + 2], data[i + 1], data[i], 255])  # Swap B and R, add alpha channel
    return new_data
