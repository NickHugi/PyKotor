# KotOR GUI Format Documentation

## Overview

GUI files (.gui) in KotOR 1 and 2 are GFF format files that define user interface elements. The format uses a hierarchical structure where controls can contain other controls as children.

## Control Types

| Type ID | Name | Description |
|---------|------|-------------|
| 0 | Control | Base control type |
| 2 | Panel | Container that can hold other controls |
| 4 | Label | Static text display |
| 5 | ProtoItem | Template for list items |
| 6 | Button | Clickable button |
| 7 | CheckBox | Toggle control |
| 8 | Slider | Value slider |
| 9 | ScrollBar | Scrolling control |
| 10 | Progress | Progress indicator |
| 11 | ListBox | Scrollable list |

## Common Structures

All controls can contain these common structures:

### EXTENT Struct
Defines position and size:
```
EXTENT
  LEFT: int32      # X position
  TOP: int32       # Y position
  WIDTH: int32     # Width
  HEIGHT: int32    # Height
```

### BORDER Struct
Defines border appearance:
```
BORDER
  COLOR: Vector3   # RGB color
  CORNER: ResRef   # Corner texture
  DIMENSION: int32 # Border thickness
  EDGE: ResRef     # Edge texture
  FILL: ResRef     # Fill texture
  FILLSTYLE: int32 # Fill style (2 = textured)
  INNEROFFSET: int32  # Inner padding
  INNEROFFSETY: int32 # Vertical inner padding
  PULSING: uint8   # Pulsing effect (0/1)
```

### TEXT Struct
Defines text properties:
```
TEXT
  ALIGNMENT: int32  # Text alignment
  COLOR: Vector3    # RGB color
  FONT: ResRef      # Font resource
  TEXT: string      # Text content
  STRREF: uint32    # TLK string reference
  PULSING: uint8    # Text pulsing (0/1)
```

### HILIGHT Struct
Defines hover state appearance (same structure as BORDER)

### MOVETO Struct
Defines UI navigation:
```
MOVETO
  UP: int32    # Control ID above
  DOWN: int32  # Control ID below
  LEFT: int32  # Control ID left
  RIGHT: int32 # Control ID right
```

## Special Controls

### ListBox (Type 11)
A scrollable list that contains:

1. PROTOITEM struct - Template for list items:
```
PROTOITEM
  CONTROLTYPE: int32  # Must be 5
  TAG: string         # Always "PROTOITEM"
  TEXT: string        # Item text
  FONT: ResRef        # Item font
  COLOR: Vector3      # Text color
  BORDER: uint8       # Border flag (0/1)
  EXTENT: struct      # Item dimensions
  Obj_Parent: string  # Parent ListBox tag
  Obj_ParentID: int32 # Parent ListBox ID
```

2. SCROLLBAR struct - Scrollbar control:
```
SCROLLBAR
  CONTROLTYPE: int32  # Must be 9
  TAG: string         # Always "SCROLLBAR"
  MAXVALUE: int32     # Max scroll value
  VISIBLEVALUE: int32 # Visible items
  EXTENT: struct      # Scrollbar dimensions
  BORDER: struct      # Border appearance
  DIR: struct         # Up/down buttons
    IMAGE: ResRef     # Button texture
    ALIGNMENT: int32  # Button alignment
  THUMB: struct       # Scrollbar thumb
    IMAGE: ResRef     # Thumb texture
  Obj_Parent: string  # Parent ListBox tag
  Obj_ParentID: int32 # Parent ListBox ID
```

## Important Notes

1. Default/Special Values:
   - Control/Parent IDs: -1 indicates unset/invalid
   - String References (STRREF): 0xFFFFFFFF means no string reference
   - Resource References (ResRef): Empty string means no resource
   - Fill Style: 2 is the default for textured fills

2. Text Alignment Values:
   ```
   1: TopLeft       2: TopCenter      3: TopRight
   17: CenterLeft   18: Center        19: CenterRight
   33: BottomLeft   34: BottomCenter  35: BottomRight
   ```

3. Parent-Child Relationships:
   - Controls can contain other controls in a CONTROLS list
   - Each control references its parent via Obj_Parent (tag) and Obj_ParentID
   - Special controls like ListBox have fixed child relationships (ProtoItem, ScrollBar)

4. Control Identification:
   - Each control must have a unique ID
   - TAG is a string identifier, often matching the ID
   - Some controls have fixed tags (e.g. "PROTOITEM", "SCROLLBAR")
