# UTW (Waypoint)

Part of the [GFF File Format Documentation](GFF-File-Format).


UTW files define waypoint templates. Waypoints are invisible markers used for spawn points, navigation targets, map notes, and reference points for scripts.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utw.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utw.py)

## Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | Template identifier for this waypoint |
| `Tag` | CExoString | Unique tag for script/linking references |
| `LocalizedName` | CExoLocString | Waypoint name |
| `Description` | CExoLocString | Description (unused) |
| `Comment` | CExoString | Developer comment/notes |

## Map Note Functionality

| Field | Type | Description |
| ----- | ---- | ----------- |
| `HasMapNote` | Byte | Waypoint has a map note |
| `MapNoteEnabled` | Byte | Map note is initially visible |
| `MapNote` | CExoLocString | Text displayed on map |

**Map Notes:**

- If enabled, shows text on the in-game map
- Can be enabled/disabled via script (`SetMapPinEnabled`)
- Used for quest objectives and locations

## Linking & Appearance

| Field | Type | Description |
| ----- | ---- | ----------- |
| `LinkedTo` | CExoString | Tag of linked object (unused) |
| `Appearance` | Byte | Appearance type (1=Waypoint) |
| `PaletteID` | Byte | Toolset palette category |

**Usage:**

- **Spawn Points**: `CreateObject` uses waypoint location
- **Patrols**: AI walks between waypoints
- **Teleport**: `JumpToLocation` targets waypoints
- **Transitions**: Doors/Triggers link to waypoint tags
