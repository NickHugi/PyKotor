from __future__ import annotations

from pathlib import Path
from collections import defaultdict, Counter
import shutil
import traceback

from pykotor.resource.formats.tpc.tpc_auto import read_tpc
from pykotor.resource.formats.tpc.tpc_data import TPC


def analyze_textures(texture_dir: Path):
    categories = defaultdict(list)
    format_counts = Counter()
    size_ranges = defaultdict(int)
    mipmap_counts = Counter()
    layer_counts = Counter()
    total_size = 0
    error_count = 0

    for file in texture_dir.rglob("*.tpc"):
        try:
            print(file)
            size = file.stat().st_size
            process_texture(file, categories, format_counts, size_ranges, mipmap_counts, layer_counts, size)
            total_size += size
        except Exception:
            traceback.print_exc()
            error_count += 1

    print_summary(categories, format_counts, size_ranges, mipmap_counts, layer_counts, total_size, error_count)


def process_texture(
    file: Path,
    categories: dict[str, list[str]],
    format_counts: Counter,
    size_ranges: dict[str, int],
    mipmap_counts: Counter,
    layer_counts: Counter,
    size: int,
):
    tpc: TPC = read_tpc(file)

    # Categorize the texture
    if tpc.is_cube_map:
        category = "cubemaps"
    elif tpc.is_animated:
        category = "animated"
    else:
        category = "normal"

    format_category = tpc.format().name.lower()
    categories[f"{category}_{format_category}"].append(file.name)

    # Count formats
    format_counts[tpc.format()] += 1

    # Categorize size
    width, height = tpc.dimensions()
    size = width * height
    if size < 256 * 256:
        size_ranges["Small (<256x256)"] += 1
    elif size < 512 * 512:
        size_ranges["Medium (256x256 - 512x512)"] += 1
    else:
        size_ranges["Large (>512x512)"] += 1

    # Count mipmap levels
    mipmap_counts[len(tpc.layers[0].mipmaps)] += 1

    # Count layers
    layer_counts[len(tpc.layers)] += 1


def print_summary(
    categories: dict[str, list[str]],
    format_counts: Counter,
    size_ranges: dict[str, int],
    mipmap_counts: Counter,
    layer_counts: Counter,
    total_size: int,
    error_count: int,
):
    print("\nTexture Analysis Summary")
    print("========================")

    print("\nCategories:")
    for category, files in categories.items():
        print(f"  {category.capitalize()}: {len(files)} files")
        print(f"    Sample files: {', '.join(files[:5])}")

    print("\nTexture Formats:")
    for format, count in format_counts.most_common():
        print(f"  {format!r}: {count} files")

    print("\nTexture Sizes:")
    for size_range, count in size_ranges.items():
        print(f"  {size_range}: {count} files")

    print("\nMipmap Levels:")
    for level, count in mipmap_counts.most_common():
        print(f"  {level} levels: {count} files")

    print("\nLayer Counts:")
    for layers, count in layer_counts.most_common():
        print(f"  {layers} layers: {count} files")

    print(f"\nTotal number of textures: {sum(format_counts.values())}")
    print(f"Total size of all textures: {total_size / (1024*1024):.2f} MB")
    print(f"Number of errors encountered: {error_count}")

    # Additional potentially useful statistics
    print("\nAdditional Statistics:")
    print(f"  Average file size: {total_size / sum(format_counts.values()) / 1024:.2f} KB")
    print(f"  Compressed ratio: {len(categories['compressed']) / sum(format_counts.values()):.2%}")
    print(f"  Textures with multiple layers: {sum(count for layers, count in layer_counts.items() if layers > 1)}")
    print(f"  Textures without mipmaps: {mipmap_counts[1] if 1 in mipmap_counts else 0}")


if __name__ == "__main__":
    texture_dir = Path("tests/test_pykotor/test_files/textures")
    analyze_textures(texture_dir)
