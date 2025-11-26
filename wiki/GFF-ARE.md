# ARE (Area)

Part of the [GFF File Format Documentation](GFF-File-Format).


ARE files define static area properties including lighting, weather, ambient audio, grass rendering, fog settings, script hooks, and minimap data. ARE files contain environmental and atmospheric data for game areas, while dynamic object placement is handled by GIT files.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/are.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py)

## Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Tag` | CExoString | Unique area identifier |
| `Name` | CExoLocString | Area name (localized) |
| `Comments` | CExoString | Developer notes/documentation |
| `Creator_ID` | DWord | Toolset creator identifier (unused at runtime) |
| `ID` | DWord | Unique area ID (unused at runtime) |
| `Version` | DWord | Area version (unused at runtime) |
| `Flags` | DWord | Area flags (unused in KotOR) |

## Lighting & Sun

| Field | Type | Description |
| ----- | ---- | ----------- |
| `SunAmbientColor` | Color | Ambient light color RGB |
| `SunDiffuseColor` | Color | Sun diffuse light color RGB |
| `SunShadows` | Byte | Enable shadow rendering |
| `ShadowOpacity` | Byte | Shadow opacity (0-255) |
| `DynAmbientColor` | Color | Dynamic ambient light RGB |

**Lighting System:**

- **SunAmbientColor**: Base ambient illumination (affects all surfaces)
- **SunDiffuseColor**: Directional sunlight color
- **SunShadows**: Enables real-time shadow casting
- **ShadowOpacity**: Controls shadow darkness
- **DynAmbientColor**: Secondary ambient for dynamic lighting

## Fog Settings

| Field | Type | Description |
| ----- | ---- | ----------- |
| `SunFogOn` | Byte | Enable fog rendering |
| `SunFogNear` | Float | Fog start distance |
| `SunFogFar` | Float | Fog end distance |
| `SunFogColor` | Color | Fog color RGB |

**Fog Rendering:**

- **SunFogOn=1**: Fog active
- **SunFogNear**: Distance where fog begins (world units)
- **SunFogFar**: Distance where fog is opaque
- **SunFogColor**: Fog tint color (atmosphere)

**Fog Calculation:**

- Linear interpolation from Near to Far
- Objects beyond Far fully obscured
- Creates depth perception and atmosphere

## Moon Lighting (Unused)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `MoonAmbientColor` | Color | Moon ambient light (unused) |
| `MoonDiffuseColor` | Color | Moon diffuse light (unused) |
| `MoonFogOn` | Byte | Moon fog toggle (unused) |
| `MoonFogNear` | Float | Moon fog start (unused) |
| `MoonFogFar` | Float | Moon fog end (unused) |
| `MoonFogColor` | Color | Moon fog color (unused) |
| `MoonShadows` | Byte | Moon shadows (unused) |
| `IsNight` | Byte | Night time flag (unused) |

**Moon System:**

- Defined in file format but not used by KotOR engine
- Intended for day/night cycle (not implemented)
- Always use Sun settings for lighting

## Grass Rendering

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Grass_TexName` | ResRef | Grass texture name |
| `Grass_Density` | Float | Grass blade density (0.0-1.0) |
| `Grass_QuadSize` | Float | Size of grass patches |
| `Grass_Ambient` | Color | Grass ambient color RGB |
| `Grass_Diffuse` | Color | Grass diffuse color RGB |
| `Grass_Emissive` (KotOR2) | Color | Grass emissive color RGB |
| `Grass_Prob_LL` | Float | Spawn probability lower-left |
| `Grass_Prob_LR` | Float | Spawn probability lower-right |
| `Grass_Prob_UL` | Float | Spawn probability upper-left |
| `Grass_Prob_UR` | Float | Spawn probability upper-right |

**Grass System:**

- **Grass_TexName**: Texture for grass blades (TGA/TPC)
- **Grass_Density**: Coverage density (1.0 = full coverage)
- **Grass_QuadSize**: Patch size in world units
- **Probability Fields**: Control grass distribution across area

**Grass Rendering:**

1. Area divided into grid based on QuadSize
2. Each quad has spawn probability from corner interpolation
3. Density determines blades per quad
4. Grass billboards oriented to camera

## Weather System (KotOR2)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `ChanceRain` (KotOR2) | Int | Rain probability (0-100) |
| `ChanceSnow` (KotOR2) | Int | Snow probability (0-100) |
| `ChanceLightning` (KotOR2) | Int | Lightning probability (0-100) |

**Weather Effects:**

- Random weather based on probability
- Particle effects for rain/snow
- Lightning provides flash and sound

## Dirty/Dust Settings (KotOR2)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `DirtyARGBOne` (KotOR2) | DWord | First dust color ARGB |
| `DirtySizeOne` (KotOR2) | Float | First dust particle size |
| `DirtyFormulaOne` (KotOR2) | Int | First dust formula type |
| `DirtyFuncOne` (KotOR2) | Int | First dust function |
| `DirtyARGBTwo` (KotOR2) | DWord | Second dust color ARGB |
| `DirtySizeTwo` (KotOR2) | Float | Second dust particle size |
| `DirtyFormulaTwo` (KotOR2) | Int | Second dust formula type |
| `DirtyFuncTwo` (KotOR2) | Int | Second dust function |
| `DirtyARGBThree` (KotOR2) | DWord | Third dust color ARGB |
| `DirtySizeThree` (KotOR2) | Float | Third dust particle size |
| `DirtyFormulaThre` (KotOR2) | Int | Third dust formula type |
| `DirtyFuncThree` (KotOR2) | Int | Third dust function |

**Dust Particle System:**

- Three independent dust layers
- Each layer has color, size, and behavior
- Creates atmospheric dust/smoke effects

## Environment & Camera

| Field | Type | Description |
| ----- | ---- | ----------- |
| `DefaultEnvMap` | ResRef | Default environment map texture |
| `CameraStyle` | Int | Camera behavior type |
| `AlphaTest` | Byte | Alpha testing threshold |
| `WindPower` | Int | Wind strength for effects |
| `LightingScheme` | Int | Lighting scheme identifier (unused) |

**Environment Mapping:**

- `DefaultEnvMap`: Cubemap for reflective surfaces
- Applied to models without specific envmaps

**Camera Behavior:**

- `CameraStyle`: Determines camera constraints
- Defines zoom, rotation, and collision behavior

## Area Behavior Flags

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Unescapable` | Byte | Cannot use save/travel functions |
| `DisableTransit` | Byte | Cannot travel to other modules |
| `StealthXPEnabled` | Byte | Award stealth XP |
| `StealthXPLoss` | Int | Stealth detection XP penalty |
| `StealthXPMax` | Int | Maximum stealth XP per area |

**Stealth System:**

- **StealthXPEnabled**: Area rewards stealth gameplay
- **StealthXPMax**: Cap on XP from stealth
- **StealthXPLoss**: Penalty when detected

**Area Restrictions:**

- **Unescapable**: Prevents save/load menus (story sequences)
- **DisableTransit**: Locks player in current location

## Skill Check Modifiers

| Field | Type | Description |
| ----- | ---- | ----------- |
| `ModSpotCheck` | Int | Awareness skill modifier (unused) |
| `ModListenCheck` | Int | Listen skill modifier (unused) |

**Skill Modifiers:**

- Intended to modify detection checks area-wide
- Not implemented in KotOR engine

## Script Hooks

| Field | Type | Description |
| ----- | ---- | ----------- |
| `OnEnter` | ResRef | Fires when entering area |
| `OnExit` | ResRef | Fires when leaving area |
| `OnHeartbeat` | ResRef | Fires periodically |
| `OnUserDefined` | ResRef | Fires on user-defined events |

**Script Execution:**

- **OnEnter**: Area initialization, cinematics, spawns
- **OnExit**: Cleanup, state saving
- **OnHeartbeat**: Periodic updates (every 6 seconds)
- **OnUserDefined**: Custom event handling

## Rooms & Minimap

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Rooms` | List | Room definitions for minimap |

**Rooms Struct Fields:**

- `RoomName` (CExoString): Room identifier
- `EnvAudio` (Int): Environment audio for room
- `AmbientScale` (Float): Ambient audio volume modifier

**Room System:**

- Defines minimap regions
- Each room has audio properties
- Audio transitions between rooms
- Minimap reveals room-by-room

## Implementation Notes

**Area Loading Sequence:**

1. **Parse ARE**: Load static properties from GFF
2. **Apply Lighting**: Set sun/ambient colors
3. **Setup Fog**: Configure fog parameters
4. **Load Grass**: Initialize grass rendering if configured
5. **Configure Weather**: Activate weather systems (KotOR2)
6. **Register Scripts**: Setup area event handlers
7. **Load GIT**: Spawn dynamic objects (separate file)

**Lighting Performance:**

- Ambient/Diffuse colors affect all area geometry
- Shadow rendering is expensive (SunShadows=0 for performance)
- Dynamic lighting for special effects only

**Grass Optimization:**

- High density grass impacts framerate significantly
- Probability fields allow targeted grass placement
- Grass LOD based on camera distance

**Audio Zones:**

- Rooms define audio transitions
- EnvAudio from ARE and Rooms determines soundscape
- Smooth fade between zones

**Common Area Configurations:**

**Outdoor Areas:**

- Bright sunlight (high diffuse)
- Fog for horizon
- Grass rendering
- Wind effects

**Indoor Areas:**

- Low ambient lighting
- No fog (usually)
- No grass
- Controlled camera

**Dark Areas:**

- Minimal ambient
- Strong diffuse for dramatic shadows
- Fog for atmosphere

**Special Areas:**

- Unescapable for story sequences
- Custom camera styles for unique views
- Specific environment maps for mood

