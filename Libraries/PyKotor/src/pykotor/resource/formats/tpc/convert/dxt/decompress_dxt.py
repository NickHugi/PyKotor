from __future__ import annotations


def dxt1_to_rgb(dxt1_data: bytes | bytearray, width: int, height: int) -> bytearray:
    def unpack_565(color):
        r = (color >> 11) & 0x1F
        g = (color >> 5) & 0x3F
        b = color & 0x1F
        return (r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)

    def interpolate_colors(c0, c1, t):
        return tuple((1 - t) * a + t * b for a, b in zip(c0, c1))

    rgb_data = bytearray(width * height * 3)
    block_count_x = (width + 3) // 4
    block_count_y = (height + 3) // 4
    data_length = len(dxt1_data)

    for block_y in range(block_count_y):
        for block_x in range(block_count_x):
            block_offset = (block_y * block_count_x + block_x) * 8

            # Check if we have enough data for this block (8 bytes for DXT1)
            if block_offset >= data_length or block_offset + 8 > data_length:
                # Fill remaining pixels with black
                for y in range(4):
                    for x in range(4):
                        pixel_x = block_x * 4 + x
                        pixel_y = block_y * 4 + y
                        if pixel_x < width and pixel_y < height:
                            pixel_offset = (pixel_y * width + pixel_x) * 3
                            rgb_data[pixel_offset:pixel_offset+3] = [0, 0, 0]
                continue

            color0 = int.from_bytes(dxt1_data[block_offset:block_offset+2], "little")
            color1 = int.from_bytes(dxt1_data[block_offset+2:block_offset+4], "little")
            color_indices = int.from_bytes(dxt1_data[block_offset+4:block_offset+8], "little")

            c0 = unpack_565(color0)
            c1 = unpack_565(color1)

            color_table = [
                c0,
                c1,
                interpolate_colors(c0, c1, 2/3) if color0 > color1 else interpolate_colors(c0, c1, 1/2),
                interpolate_colors(c0, c1, 1/3) if color0 > color1 else (0, 0, 0)
            ]

            for y in range(4):
                for x in range(4):
                    pixel_x = block_x * 4 + x
                    pixel_y = block_y * 4 + y
                    if pixel_x < width and pixel_y < height:
                        color_index = (color_indices >> (2 * (y * 4 + x))) & 0x3
                        color = color_table[color_index]
                        pixel_offset = (pixel_y * width + pixel_x) * 3
                        rgb_data[pixel_offset:pixel_offset+3] = [int(c) for c in color]

    return rgb_data

def dxt3_to_rgba(dxt3_data: bytes | bytearray, width: int, height: int) -> bytearray:
    def unpack_565(color: int) -> tuple[int, int, int]:
        r: int = (color >> 11) & 0x1F
        g: int = (color >> 5) & 0x3F
        b: int = color & 0x1F
        return (r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)

    def lerp(a: int, b: int, t: float) -> int:
        return int(a + (b - a) * t)

    rgba = bytearray(width * height * 4)
    block_count_x = (width + 3) // 4
    block_count_y = (height + 3) // 4
    data_length = len(dxt3_data)

    for block_y in range(block_count_y):
        for block_x in range(block_count_x):
            block_offset = (block_y * block_count_x + block_x) * 16

            # Check if we have enough data for this block (16 bytes for DXT3)
            if block_offset >= data_length or block_offset + 16 > data_length:
                # Fill remaining pixels with transparent black
                for y in range(4):
                    for x in range(4):
                        pixel_x = block_x * 4 + x
                        pixel_y = block_y * 4 + y
                        if pixel_x < width and pixel_y < height:
                            rgba_index = ((block_y * 4 + y) * width + block_x * 4 + x) * 4
                            rgba[rgba_index:rgba_index + 4] = [0, 0, 0, 0]
                continue

            alpha_values = dxt3_data[block_offset:block_offset + 8]
            color0 = int.from_bytes(dxt3_data[block_offset + 8:block_offset + 10], "little")
            color1 = int.from_bytes(dxt3_data[block_offset + 10:block_offset + 12], "little")
            color_indices = int.from_bytes(dxt3_data[block_offset + 12:block_offset + 16], "little")

            r0, g0, b0 = unpack_565(color0)
            r1, g1, b1 = unpack_565(color1)

            color_table: list[tuple[int, int, int]] = [
                (r0, g0, b0),
                (r1, g1, b1),
                (lerp(r0, r1, 2/3), lerp(g0, g1, 2/3), lerp(b0, b1, 2/3)),
                (lerp(r0, r1, 1/3), lerp(g0, g1, 1/3), lerp(b0, b1, 1/3))
            ]

            for y in range(4):
                for x in range(4):
                    pixel_index = x + y * 4
                    rgba_index = ((block_y * 4 + y) * width + block_x * 4 + x) * 4

                    alpha = (alpha_values[pixel_index // 2] >> (4 * (pixel_index % 2))) & 0xF
                    alpha = (alpha << 4) | alpha

                    color_index = (color_indices >> (2 * (15 - pixel_index))) & 0x3
                    color = color_table[color_index]

                    rgba[rgba_index] = color[0]
                    rgba[rgba_index + 1] = color[1]
                    rgba[rgba_index + 2] = color[2]
                    rgba[rgba_index + 3] = alpha

    return rgba


def dxt5_to_rgba(
    dxt5_data: bytes | bytearray,
    width: int,
    height: int,
) -> bytearray:
    def unpack_565(color: int) -> tuple[int, int, int]:
        r: int = (color >> 11) & 0x1F
        g: int = (color >> 5) & 0x3F
        b: int = color & 0x1F
        return (r << 3 | r >> 2, g << 2 | g >> 4, b << 3 | b >> 2)

    def interpolate_color(c0: tuple[int, int, int], c1: tuple[int, int, int], t: float) -> tuple[int, int, int]:
        return (
            int((1 - t) * c0[0] + t * c1[0]),
            int((1 - t) * c0[1] + t * c1[1]),
            int((1 - t) * c0[2] + t * c1[2])
        )

    def interpolate_alpha(a0: int, a1: int, t: float) -> int:
        return int((1 - t) * a0 + t * a1)

    rgba: bytearray = bytearray(width * height * 4)
    block_count_x: int = (width + 3) // 4
    block_count_y: int = (height + 3) // 4
    data_length: int = len(dxt5_data)

    for block_y in range(block_count_y):
        for block_x in range(block_count_x):
            block_offset: int = (block_y * block_count_x + block_x) * 16

            # Check if we have enough data for this block (16 bytes for DXT5)
            if block_offset >= data_length or block_offset + 16 > data_length:
                # Fill remaining pixels with transparent black
                for y in range(4):
                    for x in range(4):
                        pixel_x = block_x * 4 + x
                        pixel_y = block_y * 4 + y
                        if pixel_x < width and pixel_y < height:
                            fill_offset: int = (pixel_y * width + pixel_x) * 4
                            rgba[fill_offset:fill_offset + 4] = (0, 0, 0, 0)
                continue

            # Alpha
            alpha0: int = dxt5_data[block_offset]
            alpha1: int = dxt5_data[block_offset + 1]
            alpha_bits: int = int.from_bytes(dxt5_data[block_offset + 2:block_offset + 8], "little")

            # Color
            color0: int = int.from_bytes(dxt5_data[block_offset + 8:block_offset + 10], "little")
            color1: int = int.from_bytes(dxt5_data[block_offset + 10:block_offset + 12], "little")
            color_bits: int = int.from_bytes(dxt5_data[block_offset + 12:block_offset + 16], "little")

            c0: tuple[int, int, int] = unpack_565(color0)
            c1: tuple[int, int, int] = unpack_565(color1)

            for y in range(4):
                for x in range(4):
                    pixel_offset: int = ((block_y * 4 + y) * width + (block_x * 4 + x)) * 4

                    if (
                        block_x * 4 + x >= width
                        or block_y * 4 + y >= height
                    ):
                        continue

                    color_index: int = (color_bits >> (2 * (4 * y + x))) & 0x3
                    alpha_index: int = (alpha_bits >> (3 * (4 * y + x))) & 0x7

                    if color_index == 0:
                        color: tuple[int, int, int] = c0
                    elif color_index == 1:
                        color = c1
                    elif color_index == 2:  # noqa: PLR2004
                        color = interpolate_color(c0, c1, 1/3)
                    else:
                        color = interpolate_color(c0, c1, 2/3)

                    if alpha_index == 0:
                        alpha = alpha0
                    elif alpha_index == 1:
                        alpha = alpha1
                    elif alpha0 > alpha1:
                        alpha: int = interpolate_alpha(alpha0, alpha1, alpha_index / 7)
                    elif alpha_index == 6:  # noqa: PLR2004
                        alpha = 0
                    elif alpha_index == 7:  # noqa: PLR2004
                        alpha = 255
                    else:
                        alpha = interpolate_alpha(alpha0, alpha1, (alpha_index - 1) / 5)

                    rgba[pixel_offset:pixel_offset + 4] = (*color, alpha)

    return rgba
