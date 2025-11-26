# GIT (Game Instance Template)

Part of the [GFF File Format Documentation](GFF-File-Format).


GIT files store dynamic instance data for areas, defining where creatures, doors, placeables, triggers, waypoints, stores, encounters, sounds, and cameras are positioned in the game world. While ARE files define static environmental properties, GIT files contain all runtime object placement and instance-specific properties.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/git.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/git.py)

## Area Properties

| Field | Type | Description |
| ----- | ---- | ----------- |
| `AmbientSndDay` | Int | Day ambient sound ID |
| `AmbientSndDayVol` | Int | Day ambient volume (0-127) |
| `AmbientSndNight` | Int | Night ambient sound ID |
| `AmbientSndNightVol` | Int | Night ambient volume |
| `EnvAudio` | Int | Environment audio type |
| `MusicBattle` | Int | Battle music track ID |
| `MusicDay` | Int | Standard/exploration music ID |
| `MusicNight` | Int | Night music track ID |
| `MusicDelay` | Int | Delay before music starts (seconds) |

**Audio Configuration:**

- **Ambient Sounds**: Looping background ambience
- **Music Tracks**: From `ambientmusic.2da` and `musicbattle.2da`
- **EnvAudio**: Reverb/echo type for area
- **MusicDelay**: Prevents instant music start

**Music System:**

- MusicDay plays during exploration
- MusicBattle triggers during combat
- MusicNight unused in KotOR (no day/night cycle)
- Smooth transitions between tracks

## Instance Lists

GIT files contain multiple lists defining object instances:

| List Field | Contains | Description |
| ---------- | -------- | ----------- |
| `Creature List` | GITCreature | Spawned NPCs and enemies |
| `Door List` | GITDoor | Placed doors |
| `Placeable List` | GITPlaceable | Containers, furniture, objects |
| `Encounter List` | GITEncounter | Encounter spawn zones |
| `TriggerList` | GITTrigger | Trigger volumes |
| `WaypointList` | GITWaypoint | Waypoint markers |
| `StoreList` | GITStore | Merchant vendors |
| `SoundList` | GITSound | Positional audio emitters |
| `CameraList` | GITCamera | Camera definitions |

**Instance Structure:**

Each instance type has common fields plus type-specific data:

**Common Instance Fields:**

- Position (X, Y, Z coordinates)
- Orientation (quaternion or Euler angles)
- Template ResRef (UTC, UTD, UTP, etc.)
- Tag override (optional)

## GITCreature Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTC template to spawn |
| `XPosition` | Float | World X coordinate |
| `YPosition` | Float | World Y coordinate |
| `ZPosition` | Float | World Z coordinate |
| `XOrientation` | Float | Orientation X component |
| `YOrientation` | Float | Orientation Y component |

**Creature Spawning:**

- Engine loads UTC template
- Applies position/orientation from GIT
- Creature initialized with template stats
- Scripts fire after spawn

## GITDoor Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTD template |
| `Tag` | CExoString | Instance tag override |
| `LinkedToModule` | ResRef | Destination module |
| `LinkedTo` | CExoString | Destination waypoint tag |
| `LinkedToFlags` | Byte | Transition flags |
| `TransitionDestin` | CExoLocString | Destination label (UI) |
| `X`, `Y`, `Z` | Float | Position coordinates |
| `Bearing` | Float | Door orientation |
| `TweakColor` | DWord | Door color tint |
| `Hitpoints` | Short | Current HP override |

**Door Linking:**

- **LinkedToModule**: Target module ResRef
- **LinkedTo**: Waypoint tag in target module
- **TransitionDestin**: Loading screen text
- Doors can teleport between modules

**Door Instances:**

- Inherit properties from UTD template
- GIT can override HP, tag, linked destination
- Position/orientation instance-specific

## GITPlaceable Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTP template |
| `Tag` | CExoString | Instance tag override |
| `X`, `Y`, `Z` | Float | Position coordinates |
| `Bearing` | Float | Rotation angle |
| `TweakColor` | DWord | Color tint |
| `Hitpoints` | Short | Current HP override |
| `Useable` | Byte | Can be used override |

**Placeable Spawning:**

- Template defines behavior, appearance
- GIT defines placement and orientation
- Can override usability and HP at instance level

## GITTrigger Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTT template |
| `Tag` | CExoString | Instance tag |
| `TransitionDestin` | CExoLocString | Transition label |
| `LinkedToModule` | ResRef | Destination module |
| `LinkedTo` | CExoString | Destination waypoint |
| `LinkedToFlags` | Byte | Transition flags |
| `X`, `Y`, `Z` | Float | Trigger position |
| `XPosition`, `YPosition`, `ZPosition` | Float | Position (alternate) |
| `XOrientation`, `YOrientation`, `ZOrientation` | Float | Orientation |
| `Geometry` | List | Trigger volume vertices |

**Geometry Struct:**

- List of Vector3 points
- Defines trigger boundary polygon
- Planar geometry (Z-axis extrusion)

**Trigger Types:**

- **Area Transition**: LinkedToModule set
- **Script Trigger**: Fires scripts from UTT
- **Generic Trigger**: Custom behavior

## GITWaypoint Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTW template |
| `Tag` | CExoString | Waypoint identifier |
| `Appearance` | DWord | Waypoint appearance type |
| `LinkedTo` | CExoString | Linked waypoint tag |
| `X`, `Y`, `Z` | Float | Position coordinates |
| `XOrientation`, `YOrientation` | Float | Orientation |
| `HasMapNote` | Byte | Has map note |
| `MapNote` | CExoLocString | Map note text |
| `MapNoteEnabled` | Byte | Map note visible |

**Waypoint Usage:**

- **Spawn Points**: Character entry locations
- **Pathfinding**: AI navigation targets
- **Script Targets**: "Go to waypoint X"
- **Map Notes**: Player-visible markers

## GITEncounter Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTE template |
| `Tag` | CExoString | Encounter identifier |
| `X`, `Y`, `Z` | Float | Spawn position |
| `Geometry` | List | Spawn zone boundary |

**Encounter System:**

- Geometry defines trigger zone
- Engine spawns creatures from UTE when entered
- Respawn behavior from UTE template

## GITStore Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTM template |
| `Tag` | CExoString | Store identifier |
| `X`, `Y`, `Z` | Float | Position (for UI, not physical) |
| `XOrientation`, `YOrientation` | Float | Orientation |

**Store System:**

- Stores don't have physical presence
- Position used for toolset only
- Accessed via conversations or scripts

## GITSound Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | UTS template |
| `Tag` | CExoString | Sound identifier |
| `X`, `Y`, `Z` | Float | Emitter position |
| `MaxDistance` | Float | Audio falloff distance |
| `MinDistance` | Float | Full volume radius |
| `RandomRangeX`, `RandomRangeY` | Float | Position randomization |
| `Volume` | Byte | Volume level (0-127) |

**Positional Audio:**

- 3D sound emitter at position
- Volume falloff over distance
- Random offset for variation

## GITCamera Instances

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CameraID` | Int | Camera identifier |
| `FOV` | Float | Field of view (degrees) |
| `Height` | Float | Camera height |
| `MicRange` | Float | Audio capture range |
| `Orientation` | Vector4 | Camera rotation (quaternion) |
| `Pitch` | Float | Camera pitch angle |
| `Position` | Vector3 | Camera position |

**Camera System:**

- Defines fixed camera angles
- Used for cutscenes and dialogue
- FOV controls zoom level

## Implementation Notes

**GIT Loading Process:**

1. **Parse GIT**: Read GFF structure
2. **Load Templates**: Read UTC, UTD, UTP, etc. files
3. **Instantiate Objects**: Create runtime objects from templates
4. **Apply Overrides**: GIT position, HP, tag overrides applied
5. **Link Objects**: Resolve LinkedTo references
6. **Execute Spawn Scripts**: Fire OnSpawn events
7. **Activate Triggers**: Register trigger geometry

**Instance vs. Template:**

- **Template (UTC/UTD/UTP/etc.)**: Defines what the object is
- **Instance (GIT entry)**: Defines where the object is
- GIT can override specific template properties
- Multiple instances can share one template

**Performance Considerations:**

- Large instance counts impact load time
- Complex trigger geometry affects collision checks
- Many sounds can overwhelm audio system
- Creature AI scales with creature count

**Dynamic vs. Static:**

- **GIT**: Dynamic, saved with game progress
- **ARE**: Static, never changes
- GIT instances can be destroyed, moved, modified
- ARE properties remain constant

**Save Game Integration:**

- GIT state saved in save files
- Instance positions, HP, inventory preserved
- Destroyed objects marked as deleted
- New dynamic objects added to save

**Common GIT Patterns:**

**Ambush Spawns:**

- Creatures placed outside player view
- Positioned for tactical advantage
- Often linked to trigger activation

**Progression Gates:**

- Locked doors requiring keys/skills
- Triggers that load new modules
- Waypoints marking objectives

**Interactive Areas:**

- Clusters of placeables (containers)
- NPCs for dialogue
- Stores for shopping
- Workbenches for crafting

**Navigation Networks:**

- Waypoints for AI pathfinding
- Logical connections via LinkedTo
- Map notes for player guidance

**Audio Atmosphere:**

- Ambient sound emitters positioned strategically
- Varied volumes and ranges
- Random offsets for natural feel

