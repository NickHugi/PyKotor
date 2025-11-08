from __future__ import annotations


def rgb_to_dxt1(
    rgb_data: bytes | bytearray,
    width: int,
    height: int,
) -> bytearray:
    dxt1_data = bytearray()
    for y in range(0, height, 4):
        for x in range(0, width, 4):
            block: list[int] = _extract_block(rgb_data, x, y, width, height, 3)
            dest = bytearray(8)
            _compress_dxt1_block(dest, block)
            dxt1_data.extend(dest)
    return dxt1_data


def rgba_to_dxt3(
    rgba_data: bytes | bytearray,
    width: int,
    height: int,
) -> bytearray:
    dxt3_data = bytearray()
    for y in range(0, height, 4):
        for x in range(0, width, 4):
            block: list[int] = _extract_block(rgba_data, x, y, width, height, 4)
            dest = bytearray(16)
            _compress_dxt3_block(dest, block)
            dxt3_data.extend(dest)
    return dxt3_data


def rgba_to_dxt5(
    rgba_data: bytes | bytearray,
    width: int,
    height: int,
) -> bytearray:
    dxt5_data = bytearray()
    for y in range(0, height, 4):
        for x in range(0, width, 4):
            block: list[int] = _extract_block(rgba_data, x, y, width, height, 4)
            dest = bytearray(16)
            _compress_dxt5_block(dest, block)
            dxt5_data.extend(dest)
    return dxt5_data


def _extract_block(
    src: bytes | bytearray,
    x: int,
    y: int,
    w: int,
    h: int,
    channels: int,
) -> list[int]:  # noqa: PLR0913
    block: list[int] = []
    for by in range(4):
        for bx in range(4):
            sx: int = x + bx
            sy: int = y + by
            if sx < w and sy < h:
                idx: int = (sy * w + sx) * channels
                block.extend(src[idx : idx + channels])
                if channels == 3:
                    block.append(255)  # Add alpha for RGB
            else:
                block.extend([0] * 4)
    return block


def _compress_dxt1_block(
    dest: bytearray,
    src: list[int],
) -> None:
    _compress_color_block(dest, src)

def _compress_dxt3_block(
    dest: bytearray,
    src: list[int],
) -> None:
    _compress_alpha_block_dxt3(dest, src)
    _compress_color_block(dest[8:], src)

def _compress_alpha_block_dxt3(
    dest: bytearray,
    src: list[int],
) -> None:
    for i in range(8):
        alpha1: int = src[i * 8 + 3] >> 4
        alpha2: int = src[i * 8 + 7] >> 4
        dest[i] = (alpha2 << 4) | alpha1


def _compress_dxt5_block(dest: bytearray, src: list[int]) -> None:
    _compress_alpha_block_dxt5(dest, src)
    _compress_color_block(dest[8:], src)


def _compress_alpha_block_dxt5(
    dest: bytearray,
    src: list[int],
) -> None:
    alpha: list[int] = [src[i * 4 + 3] for i in range(16)]
    min_a: int = min(alpha)
    max_a: int = max(alpha)

    if min_a == max_a:
        dest[0] = max_a
        dest[1] = min_a
        dest[2:8] = [0] * 6
        return

    if min_a > max_a:
        min_a, max_a = max_a, min_a

    dest[0] = max_a
    dest[1] = min_a

    indices = 0
    for i in range(16):
        if alpha[i] == 0:
            code = 6
        elif alpha[i] == 255:  # noqa: PLR2004
            code = 7
        else:
            t: int = (alpha[i] - min_a) * 7 // (max_a - min_a)
            code: int = min(7, t)

        indices |= code << (3 * i)

    for i in range(6):
        dest[2 + i] = (indices >> (8 * i)) & 255


def _compress_color_block(
    dest: bytearray,
    src: list[int],
) -> None:
    if all(src[i : i + 4] == src[0:4] for i in range(4, 64, 4)):
        r, g, b = src[0], src[1], src[2]
        mask: int = 0xAAAAAAAA
        max16: int = as_16bit(quantize_rb(r), quantize_g(g), quantize_rb(b))
        min16: int = as_16bit(quantize_rb(r), quantize_g(g), quantize_rb(b))
    else:
        dblock: list[int] = dither_block(src)
        max16, min16 = optimize_colors_block(dblock)
        if max16 != min16:
            color = eval_colors(max16, min16)
            mask = match_colors_block(src, color)
        else:
            mask = 0

        for _ in range(2):
            lastmask: int = mask
            if refine_block(src, max16, min16, mask):
                if max16 != min16:
                    color: list[int] = eval_colors(max16, min16)
                    mask = match_colors_block(src, color)
                else:
                    mask = 0
                    break
            if mask == lastmask:
                break

    if max16 < min16:
        max16, min16 = min16, max16
        mask ^= 0x55555555

    dest[0] = max16 & 0xFF
    dest[1] = max16 >> 8
    dest[2] = min16 & 0xFF
    dest[3] = min16 >> 8
    dest[4] = mask & 0xFF
    dest[5] = (mask >> 8) & 0xFF
    dest[6] = (mask >> 16) & 0xFF
    dest[7] = (mask >> 24) & 0xFF


def dither_block(block: list[int]) -> list[int]:
    dblock: list[int] = block.copy()
    err: list[int] = [0] * 8
    for ch in range(3):
        for y in range(4):
            for x in range(4):
                idx: int = (y * 4 + x) * 4 + ch
                old: int = dblock[idx]
                new: int = quantize_rb(old) if ch != 1 else quantize_g(old)
                dblock[idx] = new
                err_val: int = old - new
                if x < 3:  # noqa: PLR2004
                    dblock[idx + 4] += (err_val * 7) >> 4
                if y < 3:  # noqa: PLR2004
                    if x > 0:
                        dblock[idx + 12] += (err_val * 3) >> 4
                    dblock[idx + 16] += (err_val * 5) >> 4
                    if x < 3:
                        dblock[idx + 20] += err_val >> 4
    return dblock


def optimize_colors_block(block: list[int]) -> tuple[int, int]:
    cov: list[int] = [0] * 6
    mu: list[int] = [0] * 3
    min_color: list[int] = [255] * 3
    max_color: list[int] = [0] * 3

    for i in range(16):
        r, g, b = block[i * 4 : i * 4 + 3]
        mu[0] += r
        mu[1] += g
        mu[2] += b
        min_color[0] = min(min_color[0], r)
        min_color[1] = min(min_color[1], g)
        min_color[2] = min(min_color[2], b)
        max_color[0] = max(max_color[0], r)
        max_color[1] = max(max_color[1], g)
        max_color[2] = max(max_color[2], b)

    mu[0] = (mu[0] + 8) >> 4
    mu[1] = (mu[1] + 8) >> 4
    mu[2] = (mu[2] + 8) >> 4

    for i in range(16):
        r = block[i * 4] - mu[0]
        g = block[i * 4 + 1] - mu[1]
        b = block[i * 4 + 2] - mu[2]
        cov[0] += r * r
        cov[1] += r * g
        cov[2] += r * b
        cov[3] += g * g
        cov[4] += g * b
        cov[5] += b * b

    vfr: int = max_color[0] - min_color[0]
    vfg: int = max_color[1] - min_color[1]
    vfb: int = max_color[2] - min_color[2]

    for _ in range(4):  # Power iteration
        r: int = vfr * cov[0] + vfg * cov[1] + vfb * cov[2]
        g: int = vfr * cov[1] + vfg * cov[3] + vfb * cov[4]
        b: int = vfr * cov[2] + vfg * cov[4] + vfb * cov[5]
        vfr, vfg, vfb = r, g, b

    magn: int = max(abs(vfr), abs(vfg), abs(vfb))
    if magn < 4.0:  # noqa: PLR2004
        v_r, v_g, v_b = 299, 587, 114
    else:
        v_r = int(vfr * 512 / magn)
        v_g = int(vfg * 512 / magn)
        v_b = int(vfb * 512 / magn)

    min_d: float = float("inf")
    max_d: float = float("-inf")
    min_p: int = 0
    max_p: int = 0
    for i in range(16):
        dot: int = block[i * 4] * v_r + block[i * 4 + 1] * v_g + block[i * 4 + 2] * v_b
        if dot < min_d:
            min_d = dot
            min_p = i
        if dot > max_d:
            max_d = dot
            max_p = i

    return (
        as_16bit(block[max_p * 4], block[max_p * 4 + 1], block[max_p * 4 + 2]),
        as_16bit(block[min_p * 4], block[min_p * 4 + 1], block[min_p * 4 + 2]),
    )


def eval_colors(
    color0: int,
    color1: int,
) -> list[int]:
    def expand_565(c: int) -> tuple[int, int, int]:
        return ((c >> 11) & 31) * 8, ((c >> 5) & 63) * 4, (c & 31) * 8

    c0: tuple[int, int, int] = expand_565(color0)
    c1: tuple[int, int, int] = expand_565(color1)

    colors: list[int] = [
        c0[0],
        c0[1],
        c0[2],
        255,
        c1[0],
        c1[1],
        c1[2],
        255,
        (2 * c0[0] + c1[0]) // 3,
        (2 * c0[1] + c1[1]) // 3,
        (2 * c0[2] + c1[2]) // 3,
        255,
        (c0[0] + 2 * c1[0]) // 3,
        (c0[1] + 2 * c1[1]) // 3,
        (c0[2] + 2 * c1[2]) // 3,
        255,
    ]

    return colors


def match_colors_block(
    block: list[int],
    color: list[int],
) -> int:
    mask: int = 0
    dir_r: int = color[0] - color[4]
    dir_g: int = color[1] - color[5]
    dir_b: int = color[2] - color[6]
    dots: list[int] = [0] * 16
    stops: list[int] = [0] * 4

    for i in range(16):
        dots[i] = block[i * 4] * dir_r + block[i * 4 + 1] * dir_g + block[i * 4 + 2] * dir_b

    for i in range(4):
        stops[i] = color[i * 4] * dir_r + color[i * 4 + 1] * dir_g + color[i * 4 + 2] * dir_b

    c0_point: int = (stops[1] + stops[3]) >> 1
    half_point: int = (stops[3] + stops[2]) >> 1
    c3_point: int = (stops[2] + stops[0]) >> 1

    for i in range(16):
        dot: int = dots[i]
        if dot < half_point:
            mask |= (3 if dot < c0_point else 1) << (i * 2)
        else:
            mask |= (2 if dot < c3_point else 0) << (i * 2)

    return mask


def refine_block(
    block: list[int],
    max16: int,
    min16: int,
    mask: int,
) -> bool:
    old_min, old_max = min16, max16
    at1_r = at1_g = at1_b = 0
    at2_r = at2_g = at2_b = 0
    akku = 0

    for i in range(16):
        step: int = mask & 3
        w1: int = [3, 0, 2, 1][step]
        r, g, b = block[i * 4 : i * 4 + 3]
        akku += [0x090000, 0x000900, 0x040102, 0x010402][step]
        at1_r += w1 * r
        at1_g += w1 * g
        at1_b += w1 * b
        at2_r += r
        at2_g += g
        at2_b += b
        mask >>= 2

    at2_r: int = 3 * at2_r - at1_r
    at2_g: int = 3 * at2_g - at1_g
    at2_b: int = 3 * at2_b - at1_b

    xx: int = akku >> 16
    yy: int = (akku >> 8) & 255
    xy: int = akku & 255

    denom: int = xx * yy - xy * xy
    if denom == 0:
        return False

    f_rb: float = (3 * 31) / 255 / denom
    f_g: float = f_rb * 63 / 31

    max16 = (
        (sclamp((at1_r * yy - at2_r * xy) * f_rb + 0.5, 0, 31) << 11)
        | (sclamp((at1_g * yy - at2_g * xy) * f_g + 0.5, 0, 63) << 5)
        | sclamp((at1_b * yy - at2_b * xy) * f_rb + 0.5, 0, 31)
    )

    min16 = (
        (sclamp((at2_r * xx - at1_r * xy) * f_rb + 0.5, 0, 31) << 11)
        | (sclamp((at2_g * xx - at1_g * xy) * f_g + 0.5, 0, 63) << 5)
        | sclamp((at2_b * xx - at1_b * xy) * f_rb + 0.5, 0, 31)
    )

    return old_min != min16 or old_max != max16


def as_16bit(
    r: int,
    g: int,
    b: int,
) -> int:
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def sclamp(
    y: float,
    p0: int,
    p1: int,
) -> int:
    x: int = int(y)
    return max(p0, min(x, p1))


def quantize_rb(x: int) -> int:
    return (x * 31 + 127) // 255


def quantize_g(x: int) -> int:
    return (x * 63 + 127) // 255
