# GUI

Part of the [GFF File Format Documentation](GFF-File-Format).


GUI files define the layout and behavior of the user interface. They are GFF files describing hierarchies of panels, buttons, labels, and other controls.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/gui.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/gui.py)

## Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Tag` | CExoString | Unique GUI identifier |
| `ObjName` | CExoString | Object name (unused) |
| `Comment` | CExoString | Developer comment |

## Control Structure

GUI files contain a `Controls` list, which holds the top-level UI elements. Each control can contain child controls, forming a tree structure.

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Controls` | List | List of child controls |
| `Type` | Int | Control type identifier |
| `ID` | Int | Unique Control ID |
| `Tag` | CExoString | Control tag |

**Control Types:**

| ID | Name | Description |
| -- | ---- | ----------- |
| -1 | Invalid | Invalid control type |
| 0 | Control | Base container (rarely used) |
| 2 | Panel | Background panel/container |
| 4 | ProtoItem | Prototype item template (for ListBox items) |
| 5 | Label | Static text label |
| 6 | Button | Clickable button |
| 7 | CheckBox | Toggle checkbox |
| 8 | Slider | Sliding value control |
| 9 | ScrollBar | Scroll bar control |
| 10 | Progress | Progress bar indicator |
| 11 | ListBox | List of items with scrolling |

## Common Properties

All controls share these base properties:

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CONTROLTYPE` | Int | Control type identifier (see Control Types) |
| `ID` | Int | Unique control ID for script references |
| `TAG` | CExoString | Control tag identifier |
| `Obj_Locked` | Byte | Lock state (0=unlocked, 1=locked) |
| `Obj_Parent` | CExoString | Parent control tag (for hierarchy) |
| `Obj_ParentID` | Int | Parent control ID (for hierarchy) |
| `ALPHA` | Float | Opacity/transparency (0.0=transparent, 1.0=opaque) |
| `COLOR` | Vector | Control color modulation (RGB, 0.0-1.0) |
| `EXTENT` | Struct | Position and size rectangle |
| `BORDER` | Struct | Border rendering properties |
| `HILIGHT` | Struct | Highlight appearance (hover state) |
| `TEXT` | Struct | Text display properties |
| `MOVETO` | Struct | D-pad navigation targets |

**EXTENT Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `LEFT` | Int | X position relative to parent (pixels) |
| `TOP` | Int | Y position relative to parent (pixels) |
| `WIDTH` | Int | Control width (pixels) |
| `HEIGHT` | Int | Control height (pixels) |

**Positioning System:**

- Coordinates are relative to parent control
- Base resolution is 640x480, scaled for higher resolutions
- Negative values allowed for positioning outside parent bounds
- Root control (GUI) uses screen-relative coordinates

**BORDER Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CORNER` | ResRef | Corner texture (TPC/TGA) |
| `EDGE` | ResRef | Edge texture (TPC/TGA) |
| `FILL` | ResRef | Fill/background texture (TPC/TGA) |
| `FILLSTYLE` | Int | Fill rendering style (-1=None, 0=Empty, 1=Solid, 2=Texture) |
| `DIMENSION` | Int | Border thickness in pixels |
| `INNEROFFSET` | Int | Inner padding X-axis (pixels) |
| `INNEROFFSETY` | Int | Inner padding Y-axis (pixels, optional) |
| `COLOR` | Vector | Border color modulation (RGB, 0.0-1.0) |
| `PULSING` | Byte | Pulsing animation flag (0=off, 1=on) |

**Border Rendering:**

- **CORNER**: 4 corner pieces (top-left, top-right, bottom-left, bottom-right)
- **EDGE**: 4 edge pieces (top, right, bottom, left)
- **FILL**: Center fill area (scaled to fit)
- **DIMENSION**: Thickness of border edges
- **FILLSTYLE**: Controls how fill texture is rendered (tiled, stretched, solid color)
- Border pieces are tiled/repeated along edges

**TEXT Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TEXT` | CExoString | Direct text content (overrides STRREF if set) |
| `STRREF` | DWord | TLK string reference (0xFFFFFFFF = unused) |
| `FONT` | ResRef | Font texture resource (TPC/TGA) |
| `ALIGNMENT` | Int | Text alignment flags (bitfield) |
| `COLOR` | Vector | Text color (RGB, 0.0-1.0) |
| `PULSING` | Byte | Pulsing animation flag (0=off, 1=on) |

**Text Alignment Values:**

- **1**: Top-Left
- **2**: Top-Center
- **3**: Top-Right
- **17**: Center-Left
- **18**: Center (most common)
- **19**: Center-Right
- **33**: Bottom-Left
- **34**: Bottom-Center
- **35**: Bottom-Right

**Text Resolution:**

- If both `TEXT` and `STRREF` are set, `TEXT` takes precedence
- Font textures contain character glyphs in fixed grid
- Text color modulates font texture (white = full color, black = no color)

**MOVETO Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `UP` | Int | Control ID to navigate to when pressing Up |
| `DOWN` | Int | Control ID to navigate to when pressing Down |
| `LEFT` | Int | Control ID to navigate to when pressing Left |
| `RIGHT` | Int | Control ID to navigate to when pressing Right |

**Navigation System:**

- Used for keyboard/D-pad navigation
- Value of -1 or 0 indicates no navigation in that direction
- Engine automatically wraps navigation at list boundaries
- Essential for controller/keyboard-only gameplay

**HILIGHT Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CORNER` | ResRef | Corner texture for highlight state |
| `EDGE` | ResRef | Edge texture for highlight state |
| `FILL` | ResRef | Fill texture for highlight state |
| `FILLSTYLE` | Int | Fill style for highlight |
| `DIMENSION` | Int | Border thickness |
| `INNEROFFSET` | Int | Inner padding X-axis |
| `INNEROFFSETY` | Int | Inner padding Y-axis (optional) |
| `COLOR` | Vector | Highlight color modulation |
| `PULSING` | Byte | Pulsing animation flag |

**Highlight Behavior:**

- Shown when mouse hovers over control
- Replaces or overlays BORDER when active
- Used for interactive feedback
- Color typically brighter/more saturated than border

**SELECTED Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CORNER` | ResRef | Corner texture for selected state |
| `EDGE` | ResRef | Edge texture for selected state |
| `FILL` | ResRef | Fill texture for selected state |
| `FILLSTYLE` | Int | Fill style for selected state |
| `DIMENSION` | Int | Border thickness |
| `INNEROFFSET` | Int | Inner padding X-axis |
| `INNEROFFSETY` | Int | Inner padding Y-axis (optional) |
| `COLOR` | Vector | Selected state color modulation |
| `PULSING` | Byte | Pulsing animation flag |

**HILIGHTSELECTED Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CORNER` | ResRef | Corner texture for highlight+selected state |
| `EDGE` | ResRef | Edge texture for highlight+selected state |
| `FILL` | ResRef | Fill texture for highlight+selected state |
| `FILLSTYLE` | Int | Fill style |
| `DIMENSION` | Int | Border thickness |
| `INNEROFFSET` | Int | Inner padding X-axis |
| `INNEROFFSETY` | Int | Inner padding Y-axis (optional) |
| `COLOR` | Vector | Combined state color modulation |
| `PULSING` | Byte | Pulsing animation flag |

**State Priority:**

1. **HILIGHTSELECTED**: When control is both highlighted (hovered) and selected
2. **HILIGHT**: When control is highlighted (hovered) but not selected
3. **SELECTED**: When control is selected but not highlighted
4. **BORDER**: Default appearance

## Control-Specific Fields

**ListBox (Type 11):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `PROTOITEM` | Struct | Template for list item appearance |
| `SCROLLBAR` | Struct | Embedded scrollbar control |
| `PADDING` | Int | Spacing between items (pixels) |
| `MAXVALUE` | Int | Maximum scroll value (total items - visible items) |
| `CURVALUE` | Int | Current scroll position |
| `LOOPING` | Byte | Loop scrolling (0=no, 1=yes) |
| `LEFTSCROLLBAR` | Byte | Scrollbar on left side (0=right, 1=left) |

**ListBox Behavior:**

- **PROTOITEM**: Defines appearance template for each list item
- **SCROLLBAR**: Embedded scrollbar for navigating long lists
- **PADDING**: Vertical spacing between items
- **MAXVALUE**: Maximum scroll offset (when all items visible, MAXVALUE=0)
- **LOOPING**: When enabled, scrolling past end wraps to beginning
- **LEFTSCROLLBAR**: Positions scrollbar on left instead of right

**PROTOITEM Struct (for ListBox):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CONTROLTYPE` | Int | Always 4 (ProtoItem) |
| `EXTENT` | Struct | Item size and position |
| `BORDER` | Struct | Item border appearance |
| `HILIGHT` | Struct | Item highlight on hover |
| `HILIGHTSELECTED` | Struct | Item highlight when selected |
| `SELECTED` | Struct | Item appearance when selected |
| `TEXT` | Struct | Item text properties |
| `ISSELECTED` | Byte | Default selected state |

**ScrollBar (Type 9):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `DIR` | Struct | Direction arrow buttons appearance |
| `THUMB` | Struct | Draggable thumb appearance |
| `MAXVALUE` | Int | Maximum scroll value |
| `VISIBLEVALUE` | Int | Number of visible items in viewport |
| `CURVALUE` | Int | Current scroll position |
| `DRAWMODE` | Byte | Drawing mode (0=normal, other values unused) |

**ScrollBar Behavior:**

- **MAXVALUE**: Total scrollable range
- **VISIBLEVALUE**: Size of visible area (determines thumb size)
- **CURVALUE**: Current scroll offset (0 to MAXVALUE)
- Thumb size = (VISIBLEVALUE / MAXVALUE) × track length

**DIR Struct (ScrollBar Direction Buttons):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `IMAGE` | ResRef | Arrow button texture |
| `ALIGNMENT` | Int | Image alignment (typically 18=center) |
| `DRAWSTYLE` | Int | Drawing style (unused) |
| `FLIPSTYLE` | Int | Flip/rotation style (unused) |
| `ROTATE` | Float | Rotation angle (unused) |

**THUMB Struct (ScrollBar Thumb):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `IMAGE` | ResRef | Thumb texture |
| `ALIGNMENT` | Int | Image alignment (typically 18=center) |
| `DRAWSTYLE` | Int | Drawing style (unused) |
| `FLIPSTYLE` | Int | Flip/rotation style (unused) |
| `ROTATE` | Float | Rotation angle (unused) |

**ProgressBar (Type 10):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `PROGRESS` | Struct | Progress fill appearance |
| `CURVALUE` | Int | Current progress value (0-100) |
| `MAXVALUE` | Int | Maximum value (typically 100) |
| `STARTFROMLEFT` | Byte | Fill direction (0=right, 1=left) |

**ProgressBar Behavior:**

- **CURVALUE**: Current progress (0-100, or 0-MAXVALUE)
- **STARTFROMLEFT**: When 1, fills left-to-right; when 0, fills right-to-left
- Progress = (CURVALUE / MAXVALUE) × width

**PROGRESS Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CORNER` | ResRef | Corner texture for progress fill |
| `EDGE` | ResRef | Edge texture for progress fill |
| `FILL` | ResRef | Fill texture for progress bar |
| `FILLSTYLE` | Int | Fill rendering style |
| `DIMENSION` | Int | Border thickness |
| `INNEROFFSET` | Int | Inner padding X-axis |
| `INNEROFFSETY` | Int | Inner padding Y-axis (optional) |
| `COLOR` | Vector | Progress fill color modulation |
| `PULSING` | Byte | Pulsing animation flag |

**CheckBox (Type 7):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `SELECTED` | Struct | Appearance when checked |
| `HILIGHTSELECTED` | Struct | Appearance when checked and hovered |
| `ISSELECTED` | Byte | Default checked state (0=unchecked, 1=checked) |

**CheckBox Behavior:**

- Toggles between checked/unchecked on click
- **ISSELECTED**: Initial state
- **SELECTED**: Visual appearance when checked
- **HILIGHTSELECTED**: Visual appearance when checked and hovered

**Slider (Type 8):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `THUMB` | Struct | Slider thumb appearance |
| `CURVALUE` | Int | Current slider value |
| `MAXVALUE` | Int | Maximum slider value |
| `DIRECTION` | Int | Orientation (0=horizontal, 1=vertical) |

**Slider Behavior:**

- **CURVALUE**: Current position (0 to MAXVALUE)
- **MAXVALUE**: Maximum value (typically 100)
- **DIRECTION**: 0=horizontal (left-right), 1=vertical (top-bottom)
- Thumb position = (CURVALUE / MAXVALUE) × track length

**Slider THUMB Struct:**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `IMAGE` | ResRef | Thumb texture |
| `ALIGNMENT` | Int | Image alignment |
| `DRAWSTYLE` | Int | Drawing style (unused) |
| `FLIPSTYLE` | Int | Flip/rotation style (unused) |
| `ROTATE` | Float | Rotation angle (unused) |

**Button (Type 6):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `HILIGHT` | Struct | Hover state appearance |
| `MOVETO` | Struct | D-pad navigation targets |
| `TEXT` | Struct | Button label text |

**Button Behavior:**

- Clickable control with text label
- **HILIGHT**: Shown on mouse hover
- **TEXT**: Button label (can use STRREF for localization)
- **MOVETO**: Keyboard/D-pad navigation

**Label (Type 5):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TEXT` | Struct | Text display properties |

**Label Behavior:**

- Static text display (non-interactive)
- **TEXT**: Text content, font, alignment, color
- Used for UI labels, descriptions, headers

**Panel (Type 2):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CONTROLS` | List | Child controls list |
| `BORDER` | Struct | Panel border (optional background) |
| `COLOR` | Vector | Panel color modulation |
| `ALPHA` | Float | Panel transparency |

**Panel Behavior:**

- Container for child controls
- **CONTROLS**: List of child controls (any type)
- **BORDER**: Optional background/border
- Child controls positioned relative to panel

**ProtoItem (Type 4):**

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TEXT` | Struct | Item label text |
| `BORDER` | Struct | Item border appearance |
| `HILIGHT` | Struct | Item highlight on hover |
| `HILIGHTSELECTED` | Struct | Item highlight when selected |
| `SELECTED` | Struct | Item appearance when selected |
| `ISSELECTED` | Byte | Default selected state |

**ProtoItem Behavior:**

- Template for list items (used by ListBox)
- Defines appearance of individual list entries
- **ISSELECTED**: Initial selection state
- States: Normal, Highlighted, Selected, Highlighted+Selected

## Implementation Notes

**Control Hierarchy:**

- GUI root contains `CONTROLS` list of top-level controls
- Controls can have child controls via `CONTROLS` list
- Child controls positioned relative to parent's EXTENT
- Parent visibility affects children (hidden parent hides children)
- Z-order: Children render above parents, later controls render above earlier ones (rendering order determined by control list order)

**Reference**: [`vendor/reone/src/libs/gui/gui.cpp:80-92`](https://github.com/th3w1zard1/reone/blob/master/src/libs/gui/gui.cpp#L80-L92) shows children are added to parent controls, and [`vendor/reone/src/libs/gui/control.cpp:192-194`](https://github.com/th3w1zard1/reone/blob/master/src/libs/gui/control.cpp#L192-L194) shows children are updated/rendered in order

**Positioning System:**

- Base resolution: 640×480 pixels (engine default, scaled for higher resolutions)
- Coordinates are pixel-based, engine scales for higher resolutions
- EXTENT.LEFT/TOP: Position relative to parent (or screen for root)
- Negative coordinates allowed (positioning outside parent bounds)
- Root control EXTENT defines GUI bounds

**Reference**: [`vendor/reone/include/reone/gui/gui.h:38-39`](https://github.com/th3w1zard1/reone/blob/master/include/reone/gui/gui.h#L38-L39) defines `kDefaultResolutionX = 640` and `kDefaultResolutionY = 480`

**Color System:**

- **COLOR** (Vector3): RGB color modulation (0.0-1.0 range)
- **ALPHA** (Float): Transparency (0.0=transparent, 1.0=opaque)
- Colors multiply with textures (white=full color, black=no color)
- KotOR 1 default text color: RGB(0.0, 0.659, 0.980) - cyan
- KotOR 2 default text color: RGB(0.102, 0.698, 0.549) - teal (exact values from engine)
- Default highlight color: RGB(1.0, 1.0, 0.0) - yellow

**Reference**: [`vendor/KotOR.js/src/gui/GUIControl.ts:188-194`](https://github.com/KobaltBlu/KotOR.js/blob/master/src/gui/GUIControl.ts#L188-L194) defines default colors for KotOR 1 and 2

**Border Rendering:**

- Border consists of 9 pieces: 4 corners, 4 edges, 1 fill
- CORNER textures: Top-left, top-right, bottom-left, bottom-right
- EDGE textures: Top, right, bottom, left (tiled along length)
- FILL texture: Center area (scaled or tiled based on FILLSTYLE)
- DIMENSION: Thickness of border edges in pixels
- INNEROFFSET: Padding between border and content

**Text Rendering:**

- Fonts are texture-based (TPC/TGA files with character grid)
- Each character has fixed width/height in font texture
- TEXT field takes precedence over STRREF if both set
- STRREF references dialog.tlk for localized strings
- ALIGNMENT uses bitfield: horizontal (1=left, 2=center, 3=right) + vertical (0=top, 16=center, 32=bottom)
- Text color modulates font texture

**State Management:**

- **Normal**: BORDER struct defines appearance
- **Hover**: HILIGHT struct overlays/replaces BORDER
- **Selected**: SELECTED struct defines appearance (CheckBox, ListBox items)
- **Hover+Selected**: HILIGHTSELECTED struct (highest priority)
- State transitions handled automatically by engine

**Control IDs:**

- **ID** field: Unique identifier for script references
- Control IDs are used by scripts and engine systems to locate specific controls
- Some engine behaviors may depend on specific Control IDs or Tags
- IDs should remain stable across GUI versions to maintain script compatibility

**Note**: While control IDs are used extensively for script references, explicit evidence of hardcoded ID dependencies in the engine is not found in vendor implementations. However, control tags (TAG field) are commonly used for engine lookups.

**Navigation:**

- **MOVETO** struct defines D-pad/keyboard navigation
- Value is Control ID of target control
- -1 or 0 indicates no navigation in that direction
- Engine handles wrapping at list boundaries
- Essential for controller/keyboard-only gameplay

**ScrollBar Integration:**

- ListBox controls can embed SCROLLBAR
- ScrollBar.MAXVALUE = total items - visible items
- ScrollBar.VISIBLEVALUE = number of visible items
- ScrollBar.CURVALUE = current scroll offset
- Thumb size = (VISIBLEVALUE / MAXVALUE) × track length
- LEFTSCROLLBAR: Positions scrollbar on left side

**Pulsing Animation:**

- **PULSING** flag in BORDER, TEXT, HILIGHT, SELECTED structs
- When enabled, control pulses (fades in/out)
- Used for attention-grabbing effects
- Animation speed controlled by engine

**Texture Formats:**

- GUI textures use TPC (Targa Packed) or TGA format
- Textures often have alpha channels for transparency
- Border pieces designed to tile seamlessly
- Font textures contain character glyphs in fixed grid

**Performance Considerations:**

- Complex GUIs with many controls impact rendering
- Nested controls increase draw calls
- Large texture borders increase memory usage
- Pulsing animations require per-frame updates

**Common Patterns:**

- **Main Menu**: Root Panel with Button controls
- **Dialogue**: Panel with Label (message) and ListBox (replies)
- **Inventory**: ListBox with ProtoItem template
- **Character Sheet**: Panel with multiple Label and Button controls
- **Options Menu**: Panel with Slider and CheckBox controls

**KotOR-Specific Notes:**

- GUIs are loaded from `.gui` files (GFF format)
- Engine scales GUIs for different resolutions
- Some controls have hardcoded behaviors (e.g., inventory slots)
- Scripts can access controls by TAG or ID
- GUI state can be modified at runtime via scripts

