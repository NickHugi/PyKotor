# KotOR TXI File Format Documentation

TXI (Texture Info) files are compact [ASCII](https://en.wikipedia.org/wiki/ASCII) descriptors that attach metadata to TPC textures. They control [mipmap](https://en.wikipedia.org/wiki/Mipmap) usage, filtering, [flipbook animation](https://en.wikipedia.org/wiki/Flip_book), [environment mapping](https://en.wikipedia.org/wiki/Reflection_mapping), [font atlases](https://en.wikipedia.org/wiki/Texture_atlas), and platform-specific downsampling. Every TXI file is parsed at runtime to configure how a TPC image is rendered.

## Table of Contents

- [KotOR TXI File Format Documentation](#kotor-txi-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [Format Overview](#format-overview)
  - [Syntax](#syntax)
    - [Command Lines](#command-lines)
    - [Coordinate Blocks](#coordinate-blocks)
  - [Command Reference](#command-reference)
    - [Rendering and Filtering](#rendering-and-filtering)
    - [Material and Environment Controls](#material-and-environment-controls)
    - [Animation and Flipbooks](#animation-and-flipbooks)
    - [Font Atlas Layout](#font-atlas-layout)
    - [Streaming and Platform Hints](#streaming-and-platform-hints)
  - [Relationship to TPC Textures](#relationship-to-tpc-textures)
  - [Implementation Details](#implementation-details)

---

## Format Overview

- TXI files are plain-text [key/value](https://en.wikipedia.org/wiki/Associative_array) lists; each command modifies a field in the TPC runtime metadata.  
- Commands are case-insensitive but conventionally lowercase. Values can be integers, floats, booleans (`0`/`1`), ResRefs, or multi-line coordinate tables.  
- A single TXI can be appended to the end of a `.tpc` file (as Bioware does) or shipped as a sibling `.txi` file; the parser treats both identically.  

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/txi/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/txi)  
**Reference:** [`vendor/reone/src/libs/graphics/format/txireader.cpp:28-139`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/txireader.cpp#L28-L139)  

---

## Syntax

### Command Lines

```
<command> <value(s)>
```

- Whitespace between command and value is ignored beyond the first separator.  
- Boolean toggles use `0` or `1`.  
- Multiple values (e.g., `channelscale 1.0 0.5 0.5`) are space-separated.  
- Comments are not supported; unknown commands are skipped.  

### Coordinate Blocks

Commands such as `upperleftcoords` and `lowerrightcoords` declare the number of rows, followed by that many lines of coordinates:

```
upperleftcoords 96
0.000000 0.000000 0
0.031250 0.000000 0
...
```

Each line encodes a UV triplet; UV coordinates follow standard [UV mapping](https://en.wikipedia.org/wiki/UV_mapping) conventions (normalized 0–1, `z` column unused).  

---

## Command Reference

> The tables below summarize the commands implemented by PyKotor’s `TXICommand` enum. Values map directly to the fields described in [`txi_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKyor/resource/formats/txi/txi_data.py#L700-L830).

### Rendering and Filtering

| Command | Accepted Values | Description |
| ------- | ---------------- | ----------- |
| `mipmap` | `0`/`1` | Toggles engine [mipmap](https://en.wikipedia.org/wiki/Mipmap) usage (KotOR's sampler mishandles secondary mips; Bioware textures usually set `0`). |
| `filter` | `0`/`1` | Enables simple [bilinear filtering](https://en.wikipedia.org/wiki/Bilinear_filtering) of font atlases; `<1>` applies a blur. |
| `clamp` | `0`/`1` | Forces address mode clamp instead of wrap. |
| `candownsample`, `downsamplemin`, `downsamplemax`, `downsamplefactor` | ints/floats | Hints used by Xbox texture reduction. |
| `priority` | integer | Streaming priority for on-demand textures (higher loads earlier). |
| `temporary` | `0`/`1` | Marks a texture as discardable after use. |
| `ondemand` | `0`/`1` | Delays texture loading until first reference. |

### Material and Environment Controls

| Command | Description |
| ------- | ----------- |
| `blending` | Selects additive or punchthrough blending (see [`TXIBlending.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/graphics/txi/TXIBlending.ts)). |
| `decal` | Toggles decal rendering so polygons project onto geometry. |
| `isbumpmap`, `isdiffusebumpmap`, `isspecularbumpmap` | Flag the texture as a bump/normal map; controls how material shaders sample it. |
| `bumpmaptexture`, `bumpyshinytexture`, `envmaptexture`, `bumpmapscaling` | Supply companion textures and scales for per-pixel lighting. |
| `cube` | Marks the texture as a [cube map](https://en.wikipedia.org/wiki/Cube_mapping); used with 6-face TPCs. |
| `unique` | Forces the renderer to keep a dedicated instance instead of sharing. |

### Animation and Flipbooks

Texture [flipbook animation](https://en.wikipedia.org/wiki/Flip_book) relies on [sprite sheets](https://en.wikipedia.org/wiki/Sprite_(computer_graphics)) that tile frames across the atlas:

| Command | Description |
| ------- | ----------- |
| `proceduretype` | Set to `cycle` to enable flipbook animation. |
| `numx`, `numy` | Horizontal/vertical frame counts. |
| `fps` | Frames per second for playback. |
| `speed` | Legacy alias for `fps` (still parsed for compatibility). |

When `proceduretype=cycle`, PyKotor splits the TPC into `numx × numy` layers and advances them at `fps` (see [`io_tpc.py:169-190`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py#L169-L190)).

### Font Atlas Layout

KotOR’s bitmap fonts use TXI commands to describe glyph boxes:

| Command | Description |
| ------- | ----------- |
| `baselineheight`, `fontheight`, `fontwidth`, `caretindent`, `spacingB`, `spacingR` | Control glyph metrics for UI fonts. |
| `rows`, `cols`, `numchars`, `numcharspersheet` | Describe how many glyphs are stored per sheet. |
| `upperleftcoords`, `lowerrightcoords` | Arrays of UV coordinates for each glyph corner. |
| `codepage`, `isdoublebyte`, `dbmapping` | Support multi-byte font atlases (Asian locales). |

KotOR.js exposes identical structures in [`src/resource/TXI.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/TXI.ts#L16-L255), ensuring the coordinates here match the engine’s expectations.

### Streaming and Platform Hints

| Command | Description |
| ------- | ----------- |
| `defaultwidth`, `defaultheight`, `defaultbpp` | Provide fallback metadata for UI textures when resolution switching. |
| `xbox_downsample`, `maxSizeHQ`, `maxSizeLQ`, `minSizeHQ`, `minSizeLQ` | Limit texture resolution on Xbox hardware. |
| `filerange` | Declares a sequence of numbered files (used by some animated sprites). |
| `controllerscript` | Associates a scripted controller for advanced animation (rare in KotOR). |

---

## Relationship to TPC Textures

- A TXI modifies the rendering pipeline for its paired TPC: mipmap flags alter sampler state, animation directives convert a single texture into multiple layers, and material directives attach bump/shine maps.  
- When embedded inside a `.tpc`, the TXI text starts immediately after the binary payload; PyKotor reads it by seeking past the texture data and consuming the remaining bytes as ASCII (`io_tpc.py:158-188`).  
- Exported `.txi` files are plain UTF-8 text and can be edited with any text editor; tools like `tga2tpc` and KotORBlender reserialize them alongside TPC assets.

### Empty TXI Files

Many TXI files in the game installation are **empty** (0 bytes). These empty TXI files serve as placeholders and indicate that the texture should use default rendering settings. When a TXI file is empty or missing, the engine falls back to default texture parameters.

**Examples of textures with empty TXI files:**
- `lda_bark04.txi` (0 bytes)
- `lda_flr11.txi` (0 bytes)
- `lda_grass07.txi` (0 bytes)
- `lda_grate01.txi` (0 bytes)
- `lda_ivy01.txi` (0 bytes)
- `lda_leaf02.txi` (0 bytes)
- `lda_lite01.txi` (0 bytes)
- `lda_rock06.txi` (0 bytes)
- `lda_sky0001.txi` through `lda_sky0005.txi` (0 bytes)
- `lda_trim02.txi`, `lda_trim03.txi`, `lda_trim04.txi` (0 bytes)
- `lda_unwal07.txi` (0 bytes)
- `lda_wall02.txi`, `lda_wall03.txi`, `lda_wall04.txi` (0 bytes)

**Examples of textures with non-empty TXI files:**
- `lda_ehawk01.txi` - Contains `envmaptexture CM_jedcom`
- `lda_ehawk01a.txi` - Contains `envmaptexture CM_jedcom`
- `lda_flr07.txi` - Contains `bumpyshinytexture CM_dantii` and `bumpmaptexture LDA_flr01B`

**Kit Generation Note:** When generating kits from module RIM files, empty TXI files should still be created as placeholders even if they don't exist in the installation. This ensures kit completeness and matches the expected kit structure where many textures have corresponding (empty) TXI files.  

---

## Implementation Details

- **Parser:** [`Libraries/PyKotor/src/pykotor/resource/formats/txi/io_txi.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/txi/io_txi.py)  
- **Data Model:** [`Libraries/PyKotor/src/pykotor/resource/formats/txi/txi_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/txi/txi_data.py)  
- **Reference Implementations:**  
  - [`vendor/reone/src/libs/graphics/format/txireader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/txireader.cpp)  
  - [`vendor/KotOR.js/src/resource/TXI.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/TXI.ts)  
  - [`vendor/tga2tpc`](https://github.com/th3w1zard1/tga2tpc) (original Bioware converter)  

These sources all interpret commands the same way, so the tables above map directly to the behavior you will observe in-game.

---

