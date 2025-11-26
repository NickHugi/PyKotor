# KotOR TPC File Format Documentation

TPC (Texture Pack Container) is KotOR's native texture format. It supports paletteless [RGB](https://en.wikipedia.org/wiki/RGB_color_model)/[RGBA](https://en.wikipedia.org/wiki/RGBA_color_space), [Greyscale](https://en.wikipedia.org/wiki/Grayscale), and block-compressed [DXT1/DXT3/DXT5](https://en.wikipedia.org/wiki/S3_Texture_Compression) data, optional [mipmaps](https://en.wikipedia.org/wiki/Mipmap), [cube maps](https://en.wikipedia.org/wiki/Cube_mapping), and [flipbook animations](https://en.wikipedia.org/wiki/Flip_book) controlled by companion TXI files.

## Table of Contents

- [KotOR TPC File Format Documentation](#kotor-tpc-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Header Layout](#header-layout)
  - [Pixel Formats](#pixel-formats)
  - [Mipmaps, Layers, and Animation](#mipmaps-layers-and-animation)
  - [Cube Maps](#cube-maps)
  - [TXI Metadata](#txi-metadata)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

| Offset | Size | Description |
| ------ | ---- | ----------- |
| 0x00   | 4    | Data size (0 for uncompressed RGB; compressed textures store total bytes) |
| 0x04   | 4    | Alpha test/threshold float |
| 0x08   | 2    | Width (uint16) |
| 0x0A   | 2    | Height (uint16) |
| 0x0C   | 1    | Pixel encoding flag |
| 0x0D   | 1    | Mipmap count |
| 0x0E   | 0x72 | Reserved / padding |
| 0x80   | —    | Texture data (per layer, per mipmap) |
| ...    | —    | Optional [ASCII](https://en.wikipedia.org/wiki/ASCII) TXI footer |

This layout is identical across PyKotor, Reone, Xoreos, KotOR.js, and the original Bioware tools; KotOR-Unity and NorthernLights consume the same header.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc)

---

## Header Layout

| Field | Description |
| ----- | ----------- |
| `data_size` | If non-zero, specifies total compressed payload size; uncompressed textures set this to 0 and derive size from format/width/height. |
| `alpha_test` | [Float](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) threshold used by [punch-through rendering](https://en.wikipedia.org/wiki/Alpha_testing) (commonly `0.0` or `0.5`). |
| `pixel_encoding` | [Bitfield](https://en.wikipedia.org/wiki/Bit_field) describing format (see next section). |
| `mipmap_count` | Number of mip levels per layer (minimum 1). |
| Reserved | 0x72 bytes reserved; KotOR stores platform hints here but all implementations skip them. |

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py:112-167`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py#L112-L167)

---

## Pixel Formats

TPC supports the following encodings (documented in `TPCTextureFormat`):

| Encoding | Description | Notes |
| -------- | ----------- | ----- |
| `0x01` (Greyscale) | 8-bit luminance | Stored as linear bytes |
| `0x02` (RGB) | 24-bit RGB | Linear bytes, may be swizzled on Xbox |
| `0x04` (RGBA) | 32-bit RGBA | Linear bytes |
| `0x0C` (BGRA) | 32-bit BGRA swizzled | Xbox-specific swizzle; PyKotor deswizzles on load |
| DXT1 | Block-compressed (4×4 blocks, 8 bytes) | Detected via `data_size` and encoding flags |
| DXT3/DXT5 | Block-compressed (4×4 blocks, 16 bytes) | Chosen based on `pixel_type` and compression flag |

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/tpc_data.py:54-178`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/tpc_data.py#L54-L178)

---

## Mipmaps, Layers, and Animation

- Each texture can have multiple **layers** (used for cube maps or animated flipbooks).  
- Every layer stores `mipmap_count` levels. For uncompressed textures, each level’s size equals `width × height × bytes_per_pixel`; for DXT formats it equals the block size calculation.  
- Animated textures rely on TXI fields (`proceduretype cycle`, `numx`, `numy`, `fps`). PyKotor splits the sprite sheet into layers and recalculates mip counts per frame.  

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py:216-285`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py#L216-L285)

---

## Cube Maps

- Detected when the stored height is exactly six times the width for compressed textures (`DXT1/DXT5`).  
- PyKotor normalizes cube faces after reading (deswizzle + rotation) so that face ordering matches the high-level texture API.  
- Reone and KotOR.js use the same inference logic, so the cube-map detection below mirrors their behavior.  

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py:138-285`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py#L138-L285)

---

## TXI Metadata

- If bytes remain after the texture payload, they are treated as ASCII TXI content.  
- TXI commands drive animations, [environment mapping](https://en.wikipedia.org/wiki/Reflection_mapping), font metrics, downsampling directives, etc. See the [TXI File Format](TXI-File-Format) document for exhaustive command descriptions.  
- PyKotor automatically parses the TXI footer and exposes `TPC.txi` plus convenience flags (`is_animated`, `is_cube_map`).  

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py:159-188`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py#L159-L188)

---

## Implementation Details

- **Binary Reader/Writer:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py)  
- **Data Model & Conversion Utilities:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/tpc_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/tpc_data.py)  
- **Reference Implementations:**  
  - [`vendor/reone/src/libs/graphics/format/tpcreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/tpcreader.cpp)  
  - [`vendor/xoreos-tools/src/graphics/tpc.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/graphics/tpc.cpp)  
  - [`vendor/tga2tpc`](https://github.com/th3w1zard1/tga2tpc) (Bioware’s original converter)  
  - [`vendor/KotOR.js/src/loaders/TextureLoader.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/loaders/TextureLoader.ts)  

All of the engines listed above treat the header and mipmap data identically. The only notable difference is that KotOR.js stores textures as WebGL-friendly blobs internally, but it imports/exports the same TPC binary format.
