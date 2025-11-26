# KotOR VIS File Format Documentation

VIS (Visibility) files describe which module rooms can be seen from other rooms. They drive the engine’s [occlusion culling](https://en.wikipedia.org/wiki/Hidden-surface_determination) so that only geometry visible from the player’s current room is rendered, reducing draw calls and overdraw.

## Table of Contents

- [KotOR VIS File Format Documentation](#kotor-vis-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [Format Overview](#format-overview)
  - [File Layout](#file-layout)
    - [Parent Lines](#parent-lines)
    - [Child Lines](#child-lines)
  - [Runtime Behavior](#runtime-behavior)
  - [Implementation Details](#implementation-details)

---

## Format Overview

- VIS files are plain [ASCII](https://en.wikipedia.org/wiki/ASCII) text; each parent room line lists how many child rooms follow.  
- Child room lines are indented by two spaces. Empty lines are ignored and names are case-insensitive.  
- Files usually ship as `moduleXXX.vis` pairs; the `moduleXXXs.vis` (or `.vis` appended inside ERF) uses the same syntax.  

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/vis/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/vis)  
**Reference:** [`vendor/reone/src/libs/resource/format/visreader.cpp:27-51`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/visreader.cpp#L27-L51)  

---

## File Layout

### Parent Lines

```vis
ROOM_NAME CHILD_COUNT
```

| Token | Description |
| ----- | ----------- |
| `ROOM_NAME` | Room label (typically the MDL ResRef of the room). |
| `CHILD_COUNT` | Number of child lines that follow immediately. |

Example:

```vis
room012 3
  room013
  room014
  room015
```

### Child Lines

- Each child line begins with two spaces followed by the visible room name.  
- There is no explicit delimiter; the parser trims whitespace.  
- A parent can list itself to force always-rendered rooms (rare but valid).  

**Reference:** [`vendor/KotOR.js/src/resource/VISObject.ts:71-126`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/VISObject.ts#L71-L126)  

---

## Runtime Behavior

- When the player stands in room `A`, the engine renders any room listed under `A` and recursively any linked lights or effects.  
- VIS files only control visibility; collision and pathfinding still rely on walkmeshes and module GFF data.  
- Editing VIS entries is a common optimization: removing unnecessary pairs prevents the renderer from drawing walls behind closed doors, while adding entries can fix disappearing geometry when doorways are wide open.

**NOTE**: VIS are NOT required by the game. Most modern hardware can run kotor significantly well even without these defined. The game however does not implement frustrum culling, so you may want to regardless.

**Performance Impact:**

VIS files are crucial for performance in large areas:

- **Without VIS**: Engine renders all rooms, even those behind walls/doors (thousands of unnecessary polygons)
- **With VIS**: Only visible rooms are submitted to the renderer (10-50x fewer draw calls)
- **Overly Restrictive VIS**: Causes pop-in where rooms suddenly appear when entering adjacent areas
- **Too Permissive VIS**: Wastes GPU resources rendering unseen geometry

**Common Issues:**

- **Missing Room**: Room not in any VIS list → never renders → appears invisible
- **One-way Visibility**: Room A lists B, but B doesn't list A → asymmetric rendering
- **Performance Problems**: All rooms list each other → defeats purpose of VIS optimization
- **Doorway Artifacts**: Door rooms not mutually visible → walls clip during door animations

Module designers balance between performance (fewer visible rooms) and visual quality (no pop-in/clipping). Testing VIS changes in-game is essential.  

PyKotor’s `VIS` class stores the data as a `dict[str, set[str]]`, exposing helpers like `set_visible()` and `set_all_visible()` for tooling (see [`vis_data.py:52-294`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/vis/vis_data.py#L52-L294)).

---

## Implementation Details

- **Parser:** [`Libraries/PyKotor/src/pykotor/resource/formats/vis/io_vis.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/vis/io_vis.py)  
- **Data Model:** [`Libraries/PyKotor/src/pykotor/resource/formats/vis/vis_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/vis/vis_data.py)  
- **Reference Implementations:**  
  - [`vendor/reone/src/libs/resource/format/visreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/visreader.cpp)  
  - [`vendor/xoreos/src/aurora/visfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/visfile.cpp)  
  - [`vendor/KotOR.js/src/resource/VISObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/VISObject.ts)  

These sources agree on the ASCII layout above, so VIS files authored with PyKotor behave identically across the other toolchains.

---
