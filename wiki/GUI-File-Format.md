# KotOR GUI File Format Documentation

This document provides a detailed description of the GUI (Graphical User Interface) file format used in Knights of the Old Republic (KotOR) games. GUI files are GFF format files that define the user interface elements in KotOR 1 and 2.

## Table of Contents

- [KotOR GUI File Format Documentation](#kotor-gui-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [File Structure](#file-structure)
  - [Control Types](#control-types)
  - [Special Values](#special-values)
  - [Implementation Details](#implementation-details)

---

## Overview

GUI files (.gui) are GFF format files that define the user interface elements in KotOR 1 and 2. They use a hierarchical structure with a root panel containing child controls.

## File Structure

GUI files use the standard GFF format structure. See the [GFF File Format](GFF-File-Format) documentation for details on the GFF structure.

GUI-specific data is stored in GFF structs with the following organization:
- Root struct contains GUI metadata and root control references
- Control structs contain position, size, properties, and child control references
- Each control type has specific fields defined in its struct

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/gui.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/gui.py)

## Implementation Details

The GUI system is implemented in [`Libraries/PyKotor/src/pykotor/resource/generics/gui.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/gui.py) with the following key components:

- Rendering: Uses Three.js for WebGL-based rendering
- Textures: Supports texture mapping with configurable UV coordinates
- Materials: Uses custom shader materials for effects
- Events: Full event system for mouse and keyboard interaction
- Layout: Supports absolute and relative positioning

## Special Values

- Control/Parent IDs: -1 indicates unset/invalid ID
- String References (STRREF): 0xFFFFFFFF (4294967295) indicates no string reference
- Resource References (resref): "" (empty string) indicates no resource
- Fill Style: -1 indicates no fill

## Control Types

| Type ID | Name | Description |
|---------|------|-------------|
| 0 | CONTROL | Base control type |
| 2 | PANEL | Container control that can hold other controls |
| 4 | LABEL | Static text display |
| 5 | PROTOITEM | Template for list items |
| 6 | BUTTON | Clickable button control |
| 7 | CHECKBOX | Toggle control |
| 8 | SLIDER | Value slider control |
| 9 | SCROLLBAR | Scrolling control |
| 10 | PROGRESSBAR | Progress indicator |
| 11 | LISTBOX | Scrollable list of items |

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/gui.py:21`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/gui.py#L21)

## Main GUI Class

The main [`GUI`](Libraries/PyKotor/src/pykotor/resource/generics/gui.py#L153) class represents a GUI resource in KotOR games.
## Common Properties

All controls share these base properties:

### Basic Properties

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| [CONTROLTYPE](Libraries/PyKotor/src/pykotor/resource/generics/gui.py#L21) | sint32 | Type of control | Required |
| ID | sint32 | Unique identifier | Required |
| TAG | exostring | Control identifier | Required |
| Obj_Locked | byte | Lock state (0/1) | 0 |
| Obj_Parent | exostring | Parent control tag | "" |
| Obj_ParentID | sint32 | Parent control ID | -1 |
| PARENTID | sint32 | Alternative parent ID reference | -1 |
| Obj_Layer | sint32 | Z-order layer | 0 |
| ALPHA | float | Opacity (0.0-1.0) | 1.0 |
| COLOR | vector | Control color (RGB as 3 doubles) | KotOR 1: [0.0, 0.658824, 0.980392], KotOR 2: [0.101961, 0.698039, 0.549020] |

### [EXTENT](Libraries/PyKotor/src/pykotor/resource/generics/gui.py#L66) Struct

Defines position and size:

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| LEFT | sint32 | X position | 0 |
| TOP | sint32 | Y position | 0 |
| WIDTH | sint32 | Width | Required |
| HEIGHT | sint32 | Height | Required |

### [BORDER](Libraries/PyKotor/src/pykotor/resource/generics/gui.py#L51) Struct

Defines border appearance:

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| CORNER | resref | Corner texture | "" |
| EDGE | resref | Edge texture | "" |
| FILL | resref | Fill texture | "" |
| FILLSTYLE | sint32 | Fill style (-1=None, 0=Empty, 1=Solid, 2=Texture) | -1 |
| DIMENSION | sint32 | Border thickness | 0 |
| INNEROFFSET | sint32 | Inner padding | 0 |
| INNEROFFSETY | sint32 | Vertical inner padding | 0 |
| COLOR | vector | Border color (RGB) | KotOR 1: [1.0, 1.0, 1.0], KotOR 2: [0.101961, 0.698039, 0.549020] |
| PULSING | byte | Pulsing effect (0/1) | 0 |

### [TEXT](Libraries/PyKotor/src/pykotor/resource/generics/gui.py#L76) Struct

Defines text properties:

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| [ALIGNMENT](Libraries/PyKotor/src/pykotor/resource/generics/gui.py#L37) | sint32 | Text alignment | 18 (Center) |
| COLOR | vector | Text color (RGB) | KotOR 1: [1.0, 1.0, 1.0], KotOR 2: [0.101961, 0.698039, 0.549020] |
| FONT | resref | Font resource | "fnt_d16x16" |
| TEXT | exostring | Text content | "" |
| STRREF | uint32 | TLK string reference | 0xFFFFFFFF |
| PULSING | byte | Text pulsing effect (0/1) | 0 |

Text Alignment Values:

- 1: TopLeft
- 2: TopCenter  
- 3: TopRight
- 17: CenterLeft
- 18: Center (Default)
- 19: CenterRight
- 33: BottomLeft
- 34: BottomCenter
- 35: BottomRight

### [MOVETO](Libraries/PyKotor/src/pykotor/resource/generics/gui.py#L88) Struct

Defines D-pad/keyboard navigation:

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| UP | sint32 | Control ID above | -1 |
| DOWN | sint32 | Control ID below | -1 |
| LEFT | sint32 | Control ID left | -1 |
| RIGHT | sint32 | Control ID right | -1 |

### HILIGHT Struct

Defines hover state appearance:

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| CORNER | resref | Corner texture for hover state | "" |
| EDGE | resref | Edge texture for hover state | "" |
| FILL | resref | Fill texture for hover state | "" |
| FILLSTYLE | sint32 | Fill style (-1=None, 0=Empty, 1=Solid, 2=Texture) | -1 |
| DIMENSION | sint32 | Border thickness in hover state | 0 |
| INNEROFFSET | sint32 | Inner padding in hover state | 0 |
| INNEROFFSETY | sint32 | Vertical inner padding in hover state | 0 |
| COLOR | vector | Hover state color (RGB) | [1.0, 1.0, 1.0] |
| PULSING | byte | Pulsing effect in hover state (0/1) | 0 |

### [SELECTED](Libraries/PyKotor/src/pykotor/resource/generics/gui.py#L276) Struct

Defines selected state appearance:

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| CORNER | resref | Corner texture for selected state | "" |
| EDGE | resref | Edge texture for selected state | "" |
| FILL | resref | Fill texture for selected state | "" |
| FILLSTYLE | sint32 | Fill style (-1=None, 0=Empty, 1=Solid, 2=Texture) | -1 |
| DIMENSION | sint32 | Border thickness in selected state | 0 |
| INNEROFFSET | sint32 | Inner padding in selected state | 0 |
| INNEROFFSETY | sint32 | Vertical inner padding in selected state | 0 |
| COLOR | vector | Selected state color (RGB) | [1.0, 1.0, 1.0] |
| PULSING | byte | Pulsing effect in selected state (0/1) | 0 |

### [HILIGHTSELECTED](Libraries/PyKotor/src/pykotor/resource/generics/gui.py#L291) Struct

Defines appearance when both selected and hovered:

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| CORNER | resref | Corner texture for selected hover state | "" |
| EDGE | resref | Edge texture for selected hover state | "" |
| FILL | resref | Fill texture for selected hover state | "" |
| FILLSTYLE | sint32 | Fill style (-1=None, 0=Empty, 1=Solid, 2=Texture) | -1 |
| DIMENSION | sint32 | Border thickness in selected hover state | 0 |
| INNEROFFSET | sint32 | Inner padding in selected hover state | 0 |
| INNEROFFSETY | sint32 | Vertical inner padding in selected hover state | 0 |
| COLOR | vector | Selected hover state color (RGB) | [1.0, 1.0, 1.0] |
| PULSING | byte | Pulsing effect in selected hover state (0/1) | 0 |

## Control-Specific Properties

### ListBox (Type 11)

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| PROTOITEM | struct | Template for list items | Required |
| SCROLLBAR | struct | Scrollbar control | Required |
| LOOPING | byte | Wrap around at ends | 0 |
| PADDING | sint32 | Item spacing | 0 |
| LEFTSCROLLBAR | byte | Scrollbar position | 1 |
| MAXVALUE | sint32 | Maximum scroll value | 0 |
| CURVALUE | sint32 | Current scroll position | 0 |
| VISIBLEITEMS | sint32 | Number of visible items | 6 |
| SELECTEDINDEX | sint32 | Currently selected item index | -1 |
| SELECTIONMODE | sint32 | Selection behavior (0=None, 1=Single, 2=Multiple) | 1 |

### ScrollBar (Type 9)

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| DIR | struct | Arrow buttons appearance | Required |
| THUMB | struct | Draggable thumb appearance | Required |
| DRAWMODE | byte | Render mode | 0 |
| MAXVALUE | sint32 | Maximum value | 100 |
| VISIBLEVALUE | sint32 | Visible items | 0 |
| CURVALUE | sint32 | Current value | 0 |
| CONTROLTYPE | sint32 | Must be 9 | 9 |
| Obj_Parent | exostring | Parent control tag | "" |
| Tag | exostring | Control identifier | Required |
| Obj_ParentID | sint32 | Parent control ID | -1 |
| EXTENT | struct | Position and size | Required |
| BORDER | struct | Border properties | Optional |

DIR/THUMB struct:

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| IMAGE | resref | Button texture | "" |
| DRAWSTYLE | sint32 | Draw mode (0=Normal, 1=Stretched, 2=Tiled) | 0 |
| FLIPSTYLE | sint32 | Flip mode | 0 |
| ROTATE | float | Rotation angle | 0.0 |
| ALIGNMENT | sint32 | Position alignment | 0 |
| ROTATESTYLE | sint32 | Rotation mode (0-3) | 0 |

### ProgressBar (Type 10)

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| PROGRESS | struct | Progress indicator appearance | Required |
| STARTFROMLEFT | byte | Fill direction | 1 |

### CheckBox (Type 7)

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| SELECTED | struct | Selected state appearance | Required |
| HILIGHTSELECTED | struct | Selected hover state appearance | Required |
| ISSELECTED | byte | Current state | 0 |

### Slider (Type 8)

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| THUMB | struct | Slider thumb appearance | Required |
| MAXVALUE | sint32 | Maximum slider value | 100 |
| CURVALUE | sint32 | Current slider value | 0 |
| DIRECTION | sint32 | Orientation (0=horizontal, 1=vertical) | 0 |

### Button (Type 6)

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| HILIGHT | struct | Hover state appearance | Optional |
| MOVETO | struct | D-pad navigation | Optional |
| COLOR | vector | Button color | KotOR 1: [0.0, 0.658824, 0.980392], KotOR 2: [0.101961, 0.698039, 0.549020] |
| HILIGHT_COLOR | vector | Hover color | KotOR 1: [1.0, 1.0, 0.0], KotOR 2: [0.8, 0.8, 0.698039] |

### Label (Type 4)

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| TEXT | struct | Text properties | Required |
| BORDER | struct | Border properties | Optional |

### Panel (Type 2)

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| BORDER | struct | Border properties | Optional |
| CONTROLS | list | Child controls | [] |

### ProtoItem (Type 5)

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| CONTROLTYPE | sint32 | Type of control | Required |
| Obj_Parent | exostring | Parent control tag | "" |
| Tag | exostring | Control identifier | Required |
| Obj_ParentID | sint32 | Parent control ID | -1 |
| EXTENT | struct | Position and size | Required |
| BORDER | struct | Border properties | Optional |
| TEXT | struct | Text properties | Optional |
| HILIGHT | struct | Hover state appearance | Optional |
| SELECTED | struct | Selected state appearance | Optional |
| HILIGHTSELECTED | struct | Selected hover state appearance | Optional |
| ISSELECTED | byte | Current state | 0 |

## KotOR 2 Specific Properties

KotOR 2 adds some additional properties and features:

### Text Colors

Default text colors in KotOR 2 dialogs:

- Normal: RGB(0.101961, 0.698039, 0.549020)
- Enemy: RGB(0.745098, 0.105882, 0.0)
- Friendly: RGB(0.321569, 0.462745, 0.917647)

### Developer Notes

KotOR 2 GUIs can contain developer notes in curly braces {} within text strings. These are hidden by default unless the "showdevnotes" config option is enabled.

## Control Nesting and Hierarchy

GUI controls can be nested in a parent-child relationship structure. The following rules apply:

1. Parent References:

- Controls reference their parent through:
  - `Obj_Parent`: String tag of parent control
  - `Obj_ParentID`: Integer ID of parent (-1 if no parent)
  - `PARENTID`: Alternative parent ID reference (-1 if unset)

2. Control Types:

- Panels (CONTROLTYPE=2) typically serve as containers
- Other controls (buttons, labels, etc.) can be children
- No strict limit on nesting depth, but shallow hierarchies are recommended

3. Typical Structure:

```
Root Panel
  ├── Child Controls (buttons, labels)
  │     └── Optional deeper nesting
  └── More Child Controls
```

4. Z-Ordering:

- Controls are rendered in order of their Obj_Layer property
- Child controls appear above their parents
- Within the same layer, controls are rendered in order of addition
