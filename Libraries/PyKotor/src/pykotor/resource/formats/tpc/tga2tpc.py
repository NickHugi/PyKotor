"""
CLI utility that mirrors the behaviour of the historic ``tga2tpc`` tool.

Usage
-----

.. code-block:: bash

    python -m pykotor.resource.formats.tpc.tga2tpc --input texture.tga --output texture.tpc \\
        --compression auto --txi texture.txi --numx 4 --numy 4 --fps 15

The implementation is intentionally self-contained and converts through the
``pykotor`` writers so produced files match the rest of the toolchain.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Sequence

from pykotor.resource.formats.tpc.io_tpc import TPCBinaryWriter
from pykotor.resource.formats.tpc.tga import TGAImage, read_tga
from pykotor.resource.formats.tpc.tpc_data import TPC, TPCLayer, TPCMipmap, TPCTextureFormat


def _has_alpha_channel(frame: TGAImage) -> bool:
    """Return True when any pixel in the frame has transparency."""
    return any(frame.data[i] != 0xFF for i in range(3, len(frame.data), 4))


def _is_grayscale(frame: TGAImage) -> bool:
    """Return True if the RGB channels are identical for every pixel."""
    data = frame.data
    for i in range(0, len(data), 4):
        r, g, b = data[i : i + 3]
        if r != g or g != b:
            return False
    return True


def _split_flipbook(image: TGAImage, num_x: int, num_y: int) -> list[TGAImage]:
    if num_x <= 0 or num_y <= 0:
        raise ValueError("Flipbook requires positive --numx and --numy values")

    if image.width % num_x != 0 or image.height % num_y != 0:
        raise ValueError("Image dimensions are not divisible by the requested flipbook grid")

    frame_width = image.width // num_x
    frame_height = image.height // num_y
    frames: list[TGAImage] = []
    stride = image.width * 4
    for tile_y in range(num_y):
        for tile_x in range(num_x):
            buffer = bytearray(frame_width * frame_height * 4)
            for row in range(frame_height):
                src_offset = ((tile_y * frame_height) + row) * stride + tile_x * frame_width * 4
                dst_offset = row * frame_width * 4
                buffer[dst_offset : dst_offset + frame_width * 4] = image.data[src_offset : src_offset + frame_width * 4]
            frames.append(TGAImage(width=frame_width, height=frame_height, data=bytes(buffer)))
    return frames


def _split_cubemap(image: TGAImage) -> list[TGAImage]:
    if image.height % image.width != 0 or image.height // image.width != 6:
        raise ValueError("Cubemap source must be stacked vertically with height == 6 * width")

    face_height = image.height // 6
    stride = image.width * 4
    faces: list[TGAImage] = []
    for face in range(6):
        buffer = bytearray(image.width * face_height * 4)
        for row in range(face_height):
            src = (face * face_height + row) * stride
            dst = row * image.width * 4
            buffer[dst : dst + image.width * 4] = image.data[src : src + image.width * 4]
        faces.append(TGAImage(width=image.width, height=face_height, data=bytes(buffer)))
    return faces


def _ensure_line(lines: list[str], key: str, value: str) -> None:
    """Append a TXI directive if it is not already present."""
    lower = key.lower()
    if any(entry.lower().startswith(lower) for entry in lines):
        return
    lines.append(f"{key} {value}")


def _compose_txi_lines(
    user_lines: Sequence[str] | None,
    *,
    cube: bool,
    num_x: int,
    num_y: int,
    fps: float,
) -> list[str]:
    lines = [line.rstrip() for line in user_lines or [] if line.strip()]

    if cube:
        _ensure_line(lines, "cube", "1")

    if num_x > 0 and num_y > 0 and fps > 0:
        _ensure_line(lines, "proceduretype", "cycle")
        _ensure_line(lines, "numx", str(num_x))
        _ensure_line(lines, "numy", str(num_y))
        _ensure_line(lines, "fps", f"{fps:g}")

    return lines


def _create_layer(
    frame: TGAImage,
    *,
    generate_mipmaps: bool,
) -> TPCLayer:
    layer = TPCLayer()
    if generate_mipmaps:
        layer.set_single(frame.width, frame.height, frame.data, TPCTextureFormat.RGBA)
    else:
        layer.mipmaps = [
            TPCMipmap(
                width=frame.width,
                height=frame.height,
                tpc_format=TPCTextureFormat.RGBA,
                data=bytearray(frame.data),
            )
        ]
    return layer


def _select_target_format(
    compression: str,
    *,
    grayscale: bool,
    has_alpha: bool,
) -> TPCTextureFormat:
    if compression == "auto":
        if grayscale:
            return TPCTextureFormat.Greyscale
        return TPCTextureFormat.DXT5 if has_alpha else TPCTextureFormat.DXT1
    if compression == "none":
        if grayscale:
            return TPCTextureFormat.Greyscale
        return TPCTextureFormat.RGBA if has_alpha else TPCTextureFormat.RGB
    if compression == "dxt1":
        return TPCTextureFormat.DXT1
    if compression == "dxt5":
        return TPCTextureFormat.DXT5
    raise ValueError(f"Unsupported compression mode: {compression}")


def _build_texture(
    frames: Sequence[TGAImage],
    *,
    compression: str,
    generate_mipmaps: bool,
    txi_lines: Sequence[str],
    cube: bool,
    num_x: int,
    num_y: int,
    alpha_test: float,
) -> TPC:
    if not frames:
        raise ValueError("At least one frame is required to build a texture")

    has_alpha = any(_has_alpha_channel(frame) for frame in frames)
    grayscale = all(_is_grayscale(frame) for frame in frames)

    tpc = TPC()
    tpc.layers = [_create_layer(frame, generate_mipmaps=generate_mipmaps) for frame in frames]
    tpc._format = TPCTextureFormat.RGBA  # noqa: SLF001
    tpc.alpha_test = alpha_test

    target_format = _select_target_format(compression, grayscale=grayscale, has_alpha=has_alpha)
    if target_format != TPCTextureFormat.RGBA:
        tpc.convert(target_format)
    else:
        tpc._format = TPCTextureFormat.RGBA  # noqa: SLF001

    payload = "\n".join(txi_lines).strip()
    if payload:
        tpc.txi = payload

    if cube:
        if len(tpc.layers) != 6:
            raise ValueError(f"Cubemap textures must provide 6 faces, found {len(tpc.layers)}")
        tpc.is_cube_map = True
    elif tpc._txi.features.cube:  # noqa: SLF001
        tpc.is_cube_map = True

    flipbook_layers = num_x * num_y
    if flipbook_layers > 0:
        if flipbook_layers != len(tpc.layers):
            raise ValueError(
                f"Flipbook metadata (numx*numy={flipbook_layers}) does not match layer count {len(tpc.layers)}",
            )
        tpc.is_animated = True
    elif tpc._txi.features.is_flipbook:  # noqa: SLF001
        tpc.is_animated = True

    return tpc


def _load_txi_lines(path: Path | None) -> list[str]:
    if not path:
        return []
    if not path.exists():
        raise FileNotFoundError(f"TXI file '{path}' not found")
    return path.read_text(encoding="utf-8", errors="ignore").splitlines()


def _write_sidecar_txi(path: Path, texture: TPC) -> None:
    payload = str(texture.txi).strip()
    if not payload:
        return
    if not payload.endswith("\n"):
        payload += "\n"
    path.write_text(payload, encoding="ascii", errors="ignore")


def run_cli(argv: Iterable[str]) -> int:
    parser = argparse.ArgumentParser(description="Convert TGA images into BioWare TPC textures.")
    parser.add_argument("--input", "-i", type=Path, required=True, help="Source TGA image")
    parser.add_argument("--output", "-o", type=Path, required=True, help="Destination TPC file")
    parser.add_argument("--txi", type=Path, help="Optional TXI file to merge into the texture")
    parser.add_argument("--emit-txi", action="store_true", help="Write the generated TXI data alongside the TPC")
    parser.add_argument("--compression", choices=["auto", "dxt1", "dxt5", "none"], default="auto", help="Compression strategy")
    parser.add_argument("--numx", type=int, default=0, help="Flipbook columns")
    parser.add_argument("--numy", type=int, default=0, help="Flipbook rows")
    parser.add_argument("--fps", type=float, default=0.0, help="Flipbook playback rate")
    parser.add_argument("--cube", action="store_true", help="Treat the input as a cubemap (six faces stacked vertically)")
    parser.add_argument("--no-mipmaps", action="store_true", help="Do not generate mipmaps")
    parser.add_argument("--alpha-test", type=float, default=1.0, help="Alpha test threshold (stored in header)")

    args = parser.parse_args(list(argv))

    if not args.input.exists():
        raise FileNotFoundError(f"TGA file '{args.input}' not found")

    with args.input.open("rb") as handle:
        base_image = read_tga(handle)

    if args.cube:
        frames = _split_cubemap(base_image)
    elif args.numx and args.numy:
        frames = _split_flipbook(base_image, args.numx, args.numy)
    else:
        frames = [base_image]

    txi_lines = _compose_txi_lines(
        _load_txi_lines(args.txi),
        cube=args.cube,
        num_x=args.numx,
        num_y=args.numy,
        fps=args.fps,
    )

    texture = _build_texture(
        frames,
        compression=args.compression,
        generate_mipmaps=not args.no_mipmaps,
        txi_lines=txi_lines,
        cube=args.cube,
        num_x=args.numx,
        num_y=args.numy,
        alpha_test=args.alpha_test,
    )

    TPCBinaryWriter(texture, args.output).write()

    if args.emit_txi:
        txi_path = args.output.with_suffix(".txi")
        _write_sidecar_txi(txi_path, texture)

    return 0


def main() -> None:
    try:
        raise SystemExit(run_cli(sys.argv[1:]))
    except BrokenPipeError:  # pragma: no cover - convenience for pipelines
        pass


if __name__ == "__main__":  # pragma: no cover
    main()

