# KotOR LYT File Format Documentation

LYT (Layout) files define how area room models are positioned inside a module. They are plain-text descriptors that list room placements, swoop-track props, obstacles, and door hook transforms. The engine combines this data with MDL/MDX geometry to assemble the final area.

## Table of Contents

- [KotOR LYT File Format Documentation](#kotor-lyt-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [Format Overview](#format-overview)
  - [Syntax](#syntax)
    - [Room Definitions](#room-definitions)
    - [Track Definitions](#track-definitions)
    - [Obstacle Definitions](#obstacle-definitions)
    - [Door Hooks](#door-hooks)
  - [Coordinate System](#coordinate-system)
  - [Implementation Details](#implementation-details)

---

## Format Overview

- LYT files are [ASCII](https://en.wikipedia.org/wiki/ASCII) text with a deterministic order: `beginlayout`, optional sections, then `donelayout`.  
- Every section declares a count and then lists entries on subsequent lines.  
- All implementations (`vendor/reone`, `vendor/xoreos`, `vendor/KotOR.js`, `vendor/Kotor.NET`) parse identical tokens; KotOR-Unity mirrors the same structure.  

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt)

---

## Syntax

```plaintext
beginlayout
roomcount <N>
  <room_model> <x> <y> <z>
trackcount <N>
  <track_model> <x> <y> <z>
obstaclecount <N>
  <obstacle_model> <x> <y> <z>
doorhookcount <N>
  <room_name> <door_name> <x> <y> <z> <qx> <qy> <qz> <qw> [optional floats]
donelayout
```

### Room Definitions

| Token | Description |
| ----- | ----------- |
| `roomcount` | Declares how many rooms follow. |
| `<room_model>` | ResRef of the MDL/MDX/WOK triple (max 16 chars, no spaces). |
| `<x y z>` | World-space position for the room’s origin. |

Rooms are case-insensitive; PyKotor lowercases entries for caching and resource lookup.

**Reference:** [`vendor/reone/src/libs/resource/format/lytreader.cpp:37-77`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/lytreader.cpp#L37-L77)

### Track Definitions

Tracks are only used by swoop racing layouts. Each entry contains the model ResRef plus its position. The section is optional.

**Reference:** [`vendor/KotOR.js/src/resource/LYTObject.ts:73-83`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LYTObject.ts#L73-L83)

### Obstacle Definitions

Mirrors the track format; typically only present in KotOR II racing modules. Most shipped KotOR I layouts omit this block entirely.

### Door Hooks

Door hooks bind door models (DYN or placeable) to rooms. Each entry contains:

| Token | Description |
| ----- | ----------- |
| `<room_name>` | Target room (must match a `roomcount` entry) |
| `<door_name>` | Hook identifier (used in module files) |
| `<x y z>` | Position of door origin |
| `<qx qy qz qw>` | Quaternion orientation |
| `[optional floats]` | Some builds (notably xoreos/KotOR-Unity) record five extra floats; PyKotor ignores them while preserving compatibility. |

**Reference:** [`vendor/xoreos/src/aurora/lytfile.cpp:161-200`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/lytfile.cpp#L161-L200)

---

## Coordinate System

- Units are meters in the same left-handed coordinate system as MDL models.  
- PyKotor validates that room ResRefs and hook targets are lowercase and conform to resource naming restrictions.  
- The engine expects rooms to be pre-aligned so that adjoining doors share positions/rotations; VIS files then control visibility between those rooms.  

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py:150-267`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py#L150-L267)

---

## Implementation Details

- **Parser:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/io_lyt.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt/io_lyt.py)  
- **Data Model:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py)  
- **Reference Implementations:**  
  - [`vendor/reone/src/libs/resource/format/lytreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/lytreader.cpp)  
  - [`vendor/xoreos/src/aurora/lytfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/lytfile.cpp)  
  - [`vendor/KotOR.js/src/resource/LYTObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LYTObject.ts)  
  - [`vendor/Kotor.NET/Kotor.NET/Formats/KotorLYT/LYT.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorLYT/LYT.cs)  

All of the projects listed above agree on the plain-text token sequence; KotOR-Unity and NorthernLights consume the same format without introducing additional metadata.
