# KotOR BWM File Format Documentation

This document provides a detailed description of the BWM (Binary WalkMesh) file format used in Knights of the Old Republic (KotOR) games. BWM files, stored on disk as WOK files, define walkable surfaces for [pathfinding](https://en.wikipedia.org/wiki/Pathfinding) and [collision detection](https://en.wikipedia.org/wiki/Collision_detection) in game areas.

**Related formats:** BWM files are used in conjunction with [GFF ARE files](GFF-File-Format#are-area) which define area properties and contain references to walkmesh files.

## Table of Contents

- [KotOR BWM File Format Documentation](#kotor-bwm-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [Walkmesh Properties](#walkmesh-properties)
    - [Data Table Offsets](#data-table-offsets)
    - [Vertices](#vertices)
    - [Faces](#faces)
    - [Materials](#materials)
    - [Derived Data](#derived-data)
    - [AABB Tree](#aabb-tree)
    - [Walkable Adjacencies](#walkable-adjacencies)
    - [Edges](#edges)
    - [Perimeters](#perimeters)
  - [Runtime Model](#runtime-model)
    - [BWM Class](#bwm-class)
    - [BWMFace Class](#bwmface-class)
    - [BWMEdge Class](#bwmedge-class)
    - [BWMNodeAABB Class](#bwmnodeaabb-class)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

BWM (Binary WalkMesh) files define walkable surfaces using triangular faces. Each face has material properties that determine whether it's walkable, adjacency information for pathfinding, and optional edge transitions for area connections. The format supports two distinct walkmesh types: area walkmeshes (WOK) for level geometry and placeable/door walkmeshes (PWK/DWK) for interactive objects.

Walkmeshes serve multiple critical functions in KotOR:

- **[Pathfinding](https://en.wikipedia.org/wiki/Pathfinding)**: NPCs and the player use walkmeshes to navigate areas, with adjacency data enabling [pathfinding algorithms](https://en.wikipedia.org/wiki/Pathfinding) to find routes between walkable faces
- **[Collision Detection](https://en.wikipedia.org/wiki/Collision_detection)**: The engine uses walkmeshes to prevent characters from walking through walls, objects, and impassable terrain
- **Spatial Queries**: [AABB trees](https://en.wikipedia.org/wiki/Bounding_volume_hierarchy) enable efficient [ray casting](https://en.wikipedia.org/wiki/Ray_casting) (mouse clicks, projectiles) and [point-in-triangle](https://en.wikipedia.org/wiki/Point_in_polygon) tests (determining which face a character stands on)
- **Area Transitions**: Edge transitions link walkmeshes to door connections and area boundaries, enabling seamless movement between rooms

The binary format uses a header-based structure where offsets point to various data tables, allowing efficient random access to vertices, faces, materials, and acceleration structures. This design enables the engine to load only necessary portions of large walkmeshes or stream data as needed.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/)

**Reference Implementations:**

- [`vendor/reone/src/libs/graphics/format/bwmreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp) - C++ BWM reader with complete parsing logic
- [`vendor/reone/include/reone/graphics/format/bwmreader.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/format/bwmreader.h) - BWM reader header with type definitions
- [`vendor/reone/include/reone/graphics/walkmesh.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/walkmesh.h) - Runtime walkmesh class definition
- [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py) - Python BWM reader for Blender import
- [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py) - Python BWM writer for Blender export with adjacency calculation
- [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp) - xoreos walkmesh loader with [pathfinding](https://en.wikipedia.org/wiki/Pathfinding) integration
- [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts) - Complete TypeScript walkmesh implementation with [raycasting](https://en.wikipedia.org/wiki/Ray_casting) and spatial queries
- [`vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshEdge.ts) - WalkmeshEdge class for perimeter edge handling
- [`vendor/KotOR.js/src/odyssey/WalkmeshPerimeter.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshPerimeter.ts) - WalkmeshPerimeter class for boundary loop management

---

## Binary Format

### File Header

| Name         | Type    | Offset | Size | Description                                    |
| ------------ | ------- | ------ | ---- | ---------------------------------------------- |
| Magic        | char[4] | 0x00   | 4    | Always `"BWM "` (space-padded)                 |
| Version      | char[4] | 0x04   | 4    | Always `"V1.0"`                                 |

The file header begins with an 8-byte signature that must exactly match `"BWM V1.0"` (the space after "BWM" is significant). This signature serves as both a file type identifier and version marker. The version string "V1.0" indicates this is the first and only version of the BWM format used in KotOR games. Implementations should validate this header before proceeding with file parsing to ensure they're reading a valid BWM file.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:28`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L28), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:52-59`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L52-L59), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:73-75`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L73-L75), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:450-453`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L450-L453)

### Walkmesh Properties

The walkmesh properties section immediately follows the header and contains type information, hook vectors, and position data. This section is 52 bytes total (from offset 0x08 to 0x3C), providing essential metadata about the walkmesh's purpose and positioning.

| Name                    | Type      | Offset | Size | Description                                                      |
| ----------------------- | --------- | ------ | ---- | ---------------------------------------------------------------- |
| Type                    | uint32    | 0x08   | 4    | Walkmesh type (0=PWK/DWK, 1=WOK/Area)                            |
| Relative Use Position 1 | float32[3]| 0x0C   | 12   | Relative use hook position 1 (x, y, z)                           |
| Relative Use Position 2 | float32[3]| 0x18   | 12   | Relative use hook position 2 (x, y, z)                           |
| Absolute Use Position 1 | float32[3]| 0x24   | 12   | Absolute use hook position 1 (x, y, z)                           |
| Absolute Use Position 2 | float32[3]| 0x30   | 12   | Absolute use hook position 2 (x, y, z)                           |
| Position                | float32[3]| 0x3C   | 12   | Walkmesh position offset (x, y, z)                               |

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:30-38`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L30-L38), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:62-67`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L62-L67), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:450-476`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L450-L476)

**Walkmesh Types:**

KotOR uses different walkmesh types for different purposes, each optimized for its specific use case:

- **WOK (Type 1)**: Area walkmesh - defines walkable regions in game areas
  - Stored as `<area_name>.wok` files (e.g., `m12aa.wok` for Dantooine area)
  - Large planar surfaces covering entire rooms or outdoor areas for player movement and NPC pathfinding
  - Often split across multiple rooms in complex areas, with each room having its own walkmesh
  - Includes complete spatial acceleration ([AABB tree](https://en.wikipedia.org/wiki/Bounding_volume_hierarchy)), adjacencies for [pathfinding](https://en.wikipedia.org/wiki/Pathfinding), edges for transitions, and perimeters for boundary detection
  - Used by the [pathfinding](https://en.wikipedia.org/wiki/Pathfinding) system to compute routes between walkable faces
  - **Reference**: [`vendor/reone/include/reone/graphics/format/bwmreader.h:40-43`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/format/bwmreader.h#L40-L43), [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:52-64`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L52-L64), [`vendor/KotOR.js/src/enums/odyssey/OdysseyWalkMeshType.ts:11-14`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/odyssey/OdysseyWalkMeshType.ts#L11-L14)
  
- **PWK/DWK (Type 0)**: Placeable/Door walkmesh - collision for placeable objects and doors
  - **PWK**: Stored as `<model_name>.pwk` files - collision geometry for containers, furniture, and other interactive placeable objects
    - Prevents the player from walking through solid objects like crates, tables, and containers
    - Typically much simpler than area walkmeshes, containing only the essential collision geometry
  - **DWK**: Stored as `<door_model>.dwk` files, often with multiple states:
    - `<name>0.dwk` - Closed door state
    - `<name>1.dwk` - Partially open state (if applicable)
    - `<name>2.dwk` - Fully open state
    - Door walkmeshes update dynamically as doors open and close, switching between states
    - The engine loads the appropriate DWK file based on the door's current animation state
  - Compact collision geometry optimized for small objects rather than large areas
  - Does not include AABB tree or adjacency data (simpler structure, faster loading)
  - Hook vectors (USE1, USE2) define interaction points where the player can activate doors or placeables
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:152-233`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L152-L233), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:181-233`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L181-L233)

**Hook Vectors** are reference points used by the engine for positioning and interaction:

- **Relative Hook Positions** (Relative Use Position 1/2): Positions relative to the walkmesh origin, used when the walkmesh itself may be transformed or positioned
  - For doors: Define where the player must stand to interact with the door (relative to door model)
  - For placeables: Define interaction points relative to the object's local coordinate system
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:63-66`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L63-L66), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:309-310`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L309-L310)

- **Absolute Hook Positions** (Absolute Use Position 1/2): Positions in world space, used when the walkmesh position is known
  - For doors: Precomputed world-space interaction points (position + relative hook)
  - For placeables: World-space interaction points accounting for object placement
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:313-318`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L313-L318)

- **Position**: The walkmesh's origin offset in world space
  - For area walkmeshes (WOK): Typically `(0, 0, 0)` as areas define their own coordinate system
  - For placeable/door walkmeshes: The position where the object is placed in the area
  - Used to transform vertices from local to world coordinates
  - **Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:37-38`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L37-L38), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:67`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L67), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:103`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L103)

Hook vectors enable the engine to:

- Spawn creatures at designated locations relative to walkable surfaces
- Position triggers and encounters at specific points
- Align objects to the walkable surface (e.g., placing items on tables)
- Define door interaction points (USE1, USE2) where the player can activate doors or placeables
- **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:216-224`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L216-L224)

### Data Table Offsets

After the walkmesh properties, the header contains offset and count information for all data tables:

| Name                | Type   | Offset | Size | Description                                                      |
| ------------------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| Vertex Count        | uint32 | 0x48   | 4    | Number of vertices                                               |
| Vertex Offset       | uint32 | 0x4C   | 4    | Offset to vertex array                                           |
| Face Count          | uint32 | 0x50   | 4    | Number of faces                                                  |
| Face Indices Offset | uint32 | 0x54   | 4    | Offset to face indices array                                     |
| Materials Offset    | uint32 | 0x58   | 4    | Offset to materials array                                       |
| Normals Offset      | uint32 | 0x5C   | 4    | Offset to face normals array                                     |
| Distances Offset    | uint32 | 0x60   | 4    | Offset to planar distances array                                 |
| AABB Count          | uint32 | 0x64   | 4    | Number of AABB nodes (WOK only, 0 for PWK/DWK)                  |
| AABB Offset         | uint32 | 0x68   | 4    | Offset to AABB nodes array (WOK only)                            |
| Unknown             | uint32 | 0x6C   | 4    | Unknown field (typically 0)                                      |
| Adjacency Count     | uint32 | 0x70   | 4    | Number of walkable faces for adjacency (WOK only)                |
| Adjacency Offset    | uint32 | 0x74   | 4    | Offset to adjacency array (WOK only)                            |
| Edge Count          | uint32 | 0x78   | 4    | Number of perimeter edges (WOK only)                            |
| Edge Offset         | uint32 | 0x7C   | 4    | Offset to edge array (WOK only)                                  |
| Perimeter Count     | uint32 | 0x80   | 4    | Number of perimeter markers (WOK only)                           |
| Perimeter Offset    | uint32 | 0x84   | 4    | Offset to perimeter array (WOK only)                            |

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:40-64`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L40-L64), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:68-83`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L68-L83), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:79-94`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L79-L94)

### Vertices

| Name     | Type      | Size | Description                                                      |
| -------- | --------- | ---- | ---------------------------------------------------------------- |
| Vertices | float32[3]| 12×N | Array of vertex positions (X, Y, Z triplets)                    |

Vertices are stored as absolute world coordinates in 32-bit [IEEE floating-point](https://en.wikipedia.org/wiki/IEEE_754) format. Each vertex is 12 bytes (three float32 values), and vertices are typically shared between multiple faces to reduce memory usage and ensure geometric consistency.

**Vertex Coordinate Systems:**

The coordinate system used for vertices depends on the walkmesh type and how implementations choose to process them:

- **For area walkmeshes (WOK)**: Vertices are stored in [world space](https://en.wikipedia.org/wiki/World_coordinates) coordinates. However, some implementations (like kotorblender) subtract the walkmesh position during reading to work in [local coordinates](https://en.wikipedia.org/wiki/Local_coordinates), which simplifies geometric operations. The walkmesh position is then added back when transforming to [world space](https://en.wikipedia.org/wiki/World_coordinates). This approach allows the walkmesh to be positioned anywhere in the world while keeping local calculations simple.
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:85-89`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L85-L89) - Subtracts position during reading
  - **Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:94-103`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L94-L103) - Reads vertices directly without offset

- **For placeable/door walkmeshes (PWK/DWK)**: Vertices are stored relative to the object's local origin. When the object is placed in an area, the engine applies a [transformation matrix](https://en.wikipedia.org/wiki/Transformation_matrix) (including translation, rotation, and scale) to convert these [local coordinates](https://en.wikipedia.org/wiki/Local_coordinates) to [world space](https://en.wikipedia.org/wiki/World_coordinates). This allows the same walkmesh to be reused for multiple instances of the same object at different positions and orientations.
  - **Reference**: [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:182-206`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L182-L206) - Applies transformation matrix to vertices

**Vertex Sharing and Indexing:**

Vertices are shared by reference through the index system: multiple faces can reference the same vertex index, ensuring that adjacent faces share exact vertex positions. This is critical for adjacency calculations, as two faces are considered adjacent only if they share exactly two vertices (forming a shared edge). The vertex array is typically deduplicated during walkmesh generation, with similar vertices (within a small tolerance) merged to reduce memory usage and ensure geometric consistency.

- **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:155-166`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L155-L166) - Vertex deduplication using SimilarVertex class
- **Reference**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:264-269`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L264-L269) - Vertex array reading

### Faces

| Name  | Type     | Size | Description                                                      |
| ----- | -------- | ---- | ---------------------------------------------------------------- |
| Faces | uint32[3]| 12×N | Array of face vertex indices (triplets referencing vertex array) |

Each face is a triangle defined by three vertex indices (0-based) into the vertex array. Each face entry is 12 bytes (three uint32 values). The vertex indices define the triangle's vertices in counter-clockwise order when viewed from the front (the side the [normal](https://en.wikipedia.org/wiki/Normal_(geometry)) points toward).

**Face Ordering:**
Faces are typically ordered with walkable faces first, followed by non-walkable faces. This ordering is important because:

- Adjacency data is stored only for walkable faces, and the adjacency array index corresponds to the walkable face's position in the walkable face list (not the overall face list)
- The engine can quickly iterate through walkable faces for pathfinding without checking material types
- Non-walkable faces are still needed for collision detection (preventing characters from walking through walls)

**Face Winding:**
The vertex order determines the face's normal direction (via the right-hand rule). The engine uses this to determine which side of the face is "up" (walkable) versus "down" (non-walkable). Faces should be oriented such that their normals point upward for walkable surfaces.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:105-114`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L105-L114), [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:74-87`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L74-L87), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:91-95`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L91-L95), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:175-194`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L175-L194), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:271-281`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L271-L281)

### Materials

| Name      | Type   | Size | Description                                                      |
| --------- | ------ | ---- | ---------------------------------------------------------------- |
| Materials | uint32  | 4×N  | Surface material index per face (determines walkability)         |

**Surface Materials:**

Each face is assigned a material type that determines its physical properties and interaction behavior. The material ID is stored as a `uint32` per face.

**Complete Material List:**

| ID | Name              | Walkable | Description                                                      |
|----|-------------------|----------|------------------------------------------------------------------|
| 0  | NotDefined        | No       | Undefined material (default)                                     |
| 1  | Dirt              | Yes      | Standard walkable dirt surface                                   |
| 2  | Obscuring         | No       | Blocks line of sight but may be walkable                        |
| 3  | Grass             | Yes      | Walkable with grass sound effects                                |
| 4  | Stone             | Yes      | Walkable with stone sound effects                                |
| 5  | Wood              | Yes      | Walkable with wood sound effects                                 |
| 6  | Water             | Yes      | Shallow water - walkable with water sounds                       |
| 7  | Nonwalk           | No       | Impassable surface - blocks character movement                  |
| 8  | Transparent       | No       | Transparent non-walkable surface                                 |
| 9  | Carpet            | Yes      | Walkable with muffled footstep sounds                           |
| 10 | Metal             | Yes      | Walkable with metallic sound effects                            |
| 11 | Puddles           | Yes      | Walkable water puddles                                          |
| 12 | Swamp             | Yes      | Walkable swamp terrain                                          |
| 13 | Mud               | Yes      | Walkable mud surface                                             |
| 14 | Leaves            | Yes      | Walkable with leaf sound effects                                 |
| 15 | Lava              | No       | Damage-dealing surface (non-walkable)                            |
| 16 | BottomlessPit     | Yes      | Walkable but dangerous (fall damage)                            |
| 17 | DeepWater         | No       | Deep water - typically non-walkable or swim areas                |
| 18 | Door              | Yes      | Door surface (special handling)                                 |
| 19 | Snow              | No       | Snow surface (non-walkable)                                      |
| 20 | Sand              | Yes      | Walkable sand surface                                            |
| 21 | BareBones         | Yes      | Walkable bare surface                                            |
| 22 | StoneBridge       | Yes      | Walkable stone bridge surface                                    |

Materials control not just walkability but also:

- Footstep sound effects during movement
- Visual effects (ripples on water, dust on dirt)
- Damage-over-time mechanics (lava, acid)
- AI pathfinding cost (creatures prefer some surfaces over others)
- Line-of-sight blocking (obscuring materials)

**Reference**: [`vendor/kotorblender/io_scene_kotor/constants.py:27-51`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/constants.py#L27-L51), [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:159-160`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L159-L160)

### Derived Data

| Name           | Type    | Size | Description                                                      |
| -------------- | ------- | ---- | ---------------------------------------------------------------- |
| Face Normals   | float32[3] | 12×N | Normal vectors for each face (normalized)                        |
| Planar Distances | float32 | 4×N | D component of plane equation (ax + by + cz + d = 0) for each face |

Face normals are precomputed unit vectors perpendicular to each face. They are calculated using the cross product of two edge vectors: `normal = normalize((v2 - v1) × (v3 - v1))`. The normal direction follows the right-hand rule based on vertex winding order, with normals typically pointing upward for walkable surfaces.

Planar distances are the D component of the plane equation `ax + by + cz + d = 0`, where (a, b, c) is the face normal. The D component is calculated as `d = -normal · vertex1` for each face, where vertex1 is typically the first vertex of the triangle. This precomputed value allows the engine to quickly test point-plane relationships without recalculating the plane equation each time.

These derived values are stored in the file to avoid recomputation during runtime, which is especially important for large walkmeshes where thousands of faces need to be tested for intersection or containment queries.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:125-134`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L125-L134), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:100-107`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L100-L107), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:700-710`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L700-L710) - Normal and plane coefficient calculation during rebuild

### AABB Tree

| Name          | Type    | Size | Description                                                      |
| ------------- | ------- | ---- | ---------------------------------------------------------------- |
| AABB Nodes    | varies  | varies | Bounding box tree nodes for spatial acceleration (WOK only)      |

Each AABB node is 44 bytes and contains:

| Name                  | Type    | Size | Description                                                      |
| --------------------- | ------- | ---- | ---------------------------------------------------------------- |
| Bounds Min            | float32[3] | 12  | Minimum bounding box coordinates (x, y, z)                      |
| Bounds Max            | float32[3] | 12  | Maximum bounding box coordinates (x, y, z)                       |
| Face Index            | int32   | 4    | Face index for leaf nodes, -1 (0xFFFFFFFF) for internal nodes   |
| Unknown               | uint32  | 4    | Unknown field (typically 4)                                       |
| Most Significant Plane| uint32  | 4    | Split axis/plane identifier (see below)                          |
| Left Child Index      | uint32  | 4    | 1-based index to left child node, 0xFFFFFFFF for no child       |
| Right Child Index     | uint32  | 4    | 1-based index to right child node, 0xFFFFFFFF for no child     |

**Most Significant Plane Values:**

- `0x00`: No children (leaf node)
- `0x01`: Positive X axis split
- `0x02`: Positive Y axis split
- `0x03`: Positive Z axis split
- `0xFFFFFFFE` (-2): Negative X axis split
- `0xFFFFFFFD` (-3): Negative Y axis split
- `0xFFFFFFFC` (-4): Negative Z axis split

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:136-171`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L136-L171), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:114-132`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L114-L132), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:218-248`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L218-L248)

**AABB Tree Purpose:**

The Axis-Aligned Bounding Box (AABB) tree is a spatial acceleration structure that dramatically improves performance for common operations. Without it, the engine would need to test every face individually (O(N) complexity), which becomes prohibitively slow for large walkmeshes with thousands of faces. The tree reduces this to O(log N) average case complexity.

**Key Operations Enabled:**

- **Ray Casting**: Finding where a ray intersects the walkmesh
  - Mouse clicks: Determining which walkable face the player clicked on for movement commands
  - Projectiles: Testing if projectiles hit walkable surfaces or obstacles
  - Line of sight: Checking if a line between two points intersects the walkmesh
  - **Reference**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:603-614`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L603-L614)

- **Point Queries**: Determining which face a character is standing on
  - Character positioning: Finding the walkable face beneath a character's position
  - Elevation calculation: Computing the Z coordinate for a character at a given (X, Y) position
  - Collision response: Determining surface normals and materials for physics calculations
  - **Reference**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:497-504`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L497-L504), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:506-521`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L506-L521)

- **Pathfinding**: Quickly rejecting faces that aren't near the path
  - Broad-phase collision: Eliminating faces that are far from the path before expensive geometric tests
  - Spatial culling: Reducing the number of faces considered during pathfinding calculations

- **Collision Detection**: Testing object-walkmesh intersections
  - Bounding box tests: Quickly determining if an object's bounding box intersects the walkmesh
  - Broad-phase filtering: Eliminating faces that cannot possibly intersect before detailed tests

**Tree Traversal Algorithm:**

The tree traversal follows a recursive divide-and-conquer approach that efficiently narrows down the search space:

1. **Start at Root**: Test the ray/point/box against the root node's bounding box. If there's no intersection, the entire walkmesh can be rejected immediately.
2. **Recurse into Children**: If the root intersects, recursively test both child nodes. The tree structure naturally partitions space, so only relevant subtrees need to be explored.
3. **Prune Branches**: If a node's bounding box doesn't intersect, skip that entire subtree. This is the key optimization: entire regions of the walkmesh can be eliminated with a single bounding box test.
4. **Test Leaf Faces**: When reaching a leaf node (face index >= 0), perform the actual geometric test on that face. This is the expensive operation (ray-triangle intersection, point-in-triangle test, etc.), but by this point, most irrelevant faces have already been eliminated.
5. **Return Results**: Collect all intersecting faces from leaf nodes. For raycasting, typically only the closest intersection is needed, so implementations can short-circuit once the first valid intersection is found.

This approach dramatically reduces the number of faces that need geometric testing, as most faces are eliminated by bounding box tests. For a walkmesh with thousands of faces, the AABB tree can reduce the number of geometric tests from O(N) to O(log N) in the average case.

**Raycasting Implementation Details:**

The reone implementation demonstrates a practical raycasting algorithm using the AABB tree. It uses an iterative approach with a stack to traverse the tree, testing ray-AABB intersections before descending into child nodes. The algorithm filters faces by surface material (using a set of walkable surface IDs) and only tests faces that match the desired surface types. This is particularly useful for mouse picking, where only walkable surfaces should be selectable.

- **Reference**: [`vendor/reone/src/libs/graphics/walkmesh.cpp:24-100`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/walkmesh.cpp#L24-L100) - Complete raycasting implementation with AABB tree traversal
- **Reference**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:603-614`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L603-L614) - Raycasting using Three.js raycaster with walkmesh integration

**Point Query Implementation:**

Point queries (determining which face a character is standing on) use similar tree traversal but test point-in-box containment instead of ray-AABB intersection. The KotOR.js implementation demonstrates point-in-triangle testing using barycentric coordinates, which is more accurate than simple bounding box tests.

- **Reference**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:497-504`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L497-L504) - Point walkability check
- **Reference**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:506-521`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L506-L521) - Nearest walkable point calculation using triangle closest point
- **Reference**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:478-495`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L478-L495) - 2D point-in-triangle test using sign-based method

**Tree Structure:**

- **Internal Nodes**: Split space along one axis (X, Y, or Z) and point to child nodes
  - The "Most Significant Plane" field indicates which axis the node splits along
  - Left and right children represent the two halves of space created by the split
  - Internal nodes have `face_index = -1` (0xFFFFFFFF) to indicate they're not leaf nodes
  - **Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:160-168`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L160-L168)

- **Leaf Nodes**: Contain a single face index (>= 0) and represent a single walkable face
  - Leaf nodes have no children (left and right child indices are 0xFFFFFFFF)
  - The bounding box of a leaf node tightly bounds its associated face
  - **Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:161-162`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L161-L162)

- **Tree Balance**: The tree is typically balanced for optimal search performance
  - Balanced trees ensure O(log N) worst-case performance
  - Unbalanced trees can degrade to O(N) in worst-case scenarios
  - Tree construction algorithms (e.g., surface area heuristic) aim to create balanced trees

- **Child Index Encoding**:
  - Child indices are 1-based (not 0-based) for internal consistency
  - `0xFFFFFFFF` indicates no child (leaf node or edge of tree)
  - To access a child node: `child_node = aabb_nodes[child_index - 1]` (convert to 0-based)
  - **Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:164-167`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L164-L167), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:232-233`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L232-L233)

**Tree Construction:**

AABB trees are typically constructed using algorithms that recursively partition space to create a balanced tree structure:

- **Surface Area Heuristic (SAH)**: Splits space to minimize the expected cost of traversal. This algorithm evaluates potential split planes and chooses the one that minimizes the expected number of node visits during queries. SAH considers the surface area of child nodes and the probability of queries intersecting each child, resulting in more optimal trees than simple median splits.
- **Median Split**: Splits along the median of face positions (simpler but less optimal). This approach is faster to compute but may produce less balanced trees, leading to suboptimal query performance.
- **Reference**: [`vendor/kotorblender/io_scene_kotor/aabb.py`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/aabb.py) - AABB tree generation implementation using surface area heuristic

The tree construction process typically involves:
1. Computing bounding boxes for all faces
2. Recursively splitting space along the best axis (determined by SAH or median)
3. Creating internal nodes that split space and leaf nodes that contain face indices
4. Building parent-child relationships between nodes
5. Storing the tree in a flat array format with 1-based child indices for efficient serialization

### Walkable Adjacencies

| Name            | Type    | Size | Description                                                      |
| --------------- | ------- | ---- | ---------------------------------------------------------------- |
| Adjacencies     | int32[3]| 12×N | Three adjacency indices per walkable face (-1 = no neighbor)     |

Adjacencies are stored only for walkable faces (faces with walkable materials). Each walkable face has exactly three adjacency entries, one for each edge (edges 0, 1, and 2). The adjacency count in the header equals the number of walkable faces, not the total face count.

**Adjacency Encoding:**

The adjacency index is a clever encoding that stores both the adjacent face index and the specific edge within that face in a single integer:

- **Encoding Formula**: `adjacency_index = face_index * 3 + edge_index`
  - `face_index`: The index of the adjacent walkable face in the overall face array
  - `edge_index`: The local edge index (0, 1, or 2) within that adjacent face
  - This encoding allows the engine to know not just which face is adjacent, but which edge of that face connects to the current edge
- **No Neighbor**: `-1` (0xFFFFFFFF) indicates no adjacent walkable face on that edge
  - This occurs when the edge is a boundary edge (perimeter edge)
  - Boundary edges may have corresponding entries in the edges array with transition information

**Adjacency Calculation:**

Adjacency is determined purely from geometry: two walkable faces are adjacent when they share exactly two vertices (forming a shared edge). The adjacency data is precomputed during walkmesh generation by:

1. Iterating through all pairs of walkable faces (typically using nested loops, comparing each face with all subsequent faces)
2. Checking if they share two vertices (indicating a shared edge). This is done by comparing vertex indices or vertex coordinates (depending on implementation)
3. Determining which edges of each face form the shared edge. Each face has three edges (edge 0: v1-v2, edge 1: v2-v3, edge 2: v3-v1), and the algorithm must identify which edge of face A matches which edge of face B
4. Encoding the adjacency relationship using the formula `adjacency_index = face_index * 3 + edge_index` for both faces, creating a bidirectional adjacency relationship

The kotorblender implementation demonstrates a practical adjacency calculation algorithm that sorts edges by vertex indices to facilitate matching. It iterates through walkable faces, comparing edges between faces to find shared edges, and updates the adjacency matrix bidirectionally.

- **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:241-273`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L241-L273) - Complete adjacency calculation algorithm with edge matching
- **Reference**: [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:155-169`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L155-L169) - Adjacency decoding and mapping to face indices

**Pathfinding Usage:**

Adjacency data is critical for pathfinding algorithms (A*, Dijkstra, etc.) that compute routes across walkable surfaces:

- The pathfinding system uses adjacency to traverse from one walkable face to another. Each face becomes a node in the pathfinding graph, with adjacency relationships defining the edges between nodes.
- When a character moves from face A to face B, the adjacency data tells the engine which edge was crossed. This information is used for:
  - Smooth character movement: The engine can interpolate movement along the shared edge
  - Elevation changes: Adjacent faces may have different Z coordinates, requiring the character to step up or down
  - Edge-based path smoothing: Paths can be optimized to follow edges rather than cutting across faces
- The adjacency encoding (`face_index * 3 + edge_index`) allows the pathfinding system to know not just which face to move to, but which specific edge connects the faces, enabling precise movement calculations.
- This enables smooth movement across walkable surfaces and proper handling of elevation changes, as the engine can compute the exact transition point between faces.
- **Reference**: [`vendor/xoreos/src/engines/kotorbase/path/pathfinding.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/pathfinding.h) - Pathfinding system using adjacency data
- **Reference**: [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:155-169`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L155-L169) - Adjacency decoding for pathfinding integration

**Important Notes:**

- Adjacency is only defined between walkable faces; non-walkable faces are not included in adjacency calculations
- The adjacency array index corresponds to the walkable face's position in the walkable face list (faces sorted by walkability)
- When decoding an adjacency index: `face_index = adjacency_index // 3`, `edge_index = adjacency_index % 3`
- **Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:58-59`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L58-L59), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:155-169`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L155-L169), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:305-337`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L305-L337), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:241-273`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L241-L273)

### Edges

| Name  | Type     | Size | Description                                                      |
| ----- | -------- | ---- | ---------------------------------------------------------------- |
| Edges | varies   | varies | Perimeter edge data (edge_index, transition pairs) (WOK only)  |

The edges array contains perimeter edges (boundary edges with no walkable neighbor). Each edge entry is 8 bytes:

| Name        | Type   | Size | Description                                                      |
| ----------- | ------ | ---- | ---------------------------------------------------------------- |
| Edge Index  | uint32 | 4    | Encoded edge index: `face_index * 3 + local_edge_index`        |
| Transition  | int32  | 4    | Transition ID for room/area connections, -1 if no transition     |

**Edge Index Encoding:**

The edge index uses the same encoding as adjacency indices: `edge_index = face_index * 3 + local_edge_index`. This identifies:

- Which face the edge belongs to (`face_index = edge_index // 3`)
- Which edge of that face (0, 1, or 2) (`local_edge_index = edge_index % 3`)

**Perimeter Edges:**

Perimeter edges are edges of walkable faces that have no adjacent walkable neighbor. These edges form the boundaries of walkable regions and are critical for:

- **Area Transitions**: Edges with non-negative transition IDs link to door connections or area boundaries
  - When a character crosses such an edge, the engine can trigger area transitions or door opening animations
  - Transition IDs typically reference entries in area layout (LYT) files or door data structures
- **Boundary Detection**: Perimeter edges define the limits of walkable space
  - Characters cannot move beyond perimeter edges (they're blocked by walls, cliffs, or area boundaries)
  - The pathfinding system uses perimeter edges to detect when a path reaches an area boundary
- **Visual Debugging**: Perimeter edges can be visualized to show walkmesh boundaries in level editors

**Edge Generation:**

Edges are identified during walkmesh generation by:

1. Iterating through all walkable faces and their three edges
2. Checking each edge's adjacency entry in the adjacency array
3. If an edge has `-1` adjacency (no walkable neighbor), it's a perimeter edge - meaning this edge forms a boundary of the walkable region
4. The edge is added to the edges array with its transition ID (if any). Transition IDs are typically stored in a separate data structure (like roomlinks in kotorblender) that maps edge indices to transition IDs

The kotorblender implementation shows a sophisticated edge generation algorithm that also constructs perimeter loops by following connected perimeter edges. It uses a visited set to ensure each edge is only processed once, and builds perimeter loops by following edges that share vertices.

- **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:275-307`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L275-L307) - Edge generation and perimeter loop construction
- **Reference**: [`vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:61-108`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshEdge.ts#L61-L108) - Edge update method that calculates edge line geometry and normals
- **Reference**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:716-782`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L716-L782) - Perimeter building algorithm that constructs closed loops from edges

**Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:140-145`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L140-L145), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:275-307`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L275-L307), [`vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:15-110`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshEdge.ts#L15-L110), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:339-345`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L339-L345), [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:164-179`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L164-L179)

### Perimeters

| Name      | Type   | Size | Description                                                      |
| --------- | ------ | ---- | ---------------------------------------------------------------- |
| Perimeters | uint32 | 4×N  | 1-based indices into edge array marking end of perimeter loops (WOK only) |

Perimeters mark the end of closed loops of perimeter edges. Each perimeter value is a **1-based index** into the edge array, indicating where a perimeter loop ends. This allows the engine to traverse complete boundary loops for pathfinding and area transitions.

**Perimeter Loop Structure:**

Perimeter edges form closed loops (polygons) that define the boundaries of walkable regions. The perimeters array breaks the edges array into these loops:

- **Loop 1**: Edges from index 0 (1-based) to `perimeters[0]` (1-based)
- **Loop 2**: Edges from `perimeters[0] + 1` (1-based) to `perimeters[1]` (1-based)
- **Loop N**: Edges from `perimeters[N-2] + 1` (1-based) to `perimeters[N-1]` (1-based)

**Why 1-Based Indices:**

The perimeters array uses 1-based indices (not 0-based) to match the game engine's expectations. When reading:

- Subtract 1 to convert to 0-based array indexing: `edge_index_0based = perimeter_value - 1`
- The first perimeter value points to the last edge of the first loop
- Subsequent perimeter values point to the last edge of subsequent loops

**Perimeter Usage:**

Perimeters enable the engine to:

- **Traverse Boundary Loops**: The engine can iterate through complete boundary loops to detect area boundaries, room connections, and transition points
- **Pathfinding**: When a path reaches a perimeter edge, the engine knows it's at a boundary and can check for transitions or alternative routes
- **Area Loading**: Perimeter edges with transitions can trigger loading of adjacent areas or rooms
- **Visualization**: Perimeter loops can be rendered as closed polygons in level editors to show walkmesh boundaries

**Perimeter Generation:**

Perimeters are computed during walkmesh generation by constructing closed loops from perimeter edges:

1. Starting with an unvisited perimeter edge from the edges array
2. Following connected perimeter edges (edges that share a vertex) to form a loop. The algorithm tracks the current vertex and searches for the next edge that starts at that vertex
3. When the loop closes (returns to the starting vertex), mark the end index in the perimeters array. The perimeters array stores 1-based indices pointing to the last edge of each loop
4. Repeat until all perimeter edges are assigned to loops. Some walkmeshes may have multiple disconnected perimeter loops (e.g., islands of walkable space)

The KotOR.js implementation demonstrates a perimeter building algorithm that uses a shift-based approach: it removes edges from a working set as they're added to perimeters, ensuring each edge is only used once. The algorithm tracks the start and next vertices to follow the loop, and marks perimeters as closed when they return to the starting vertex.

- **Reference**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:716-782`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L716-L782) - Complete perimeter building implementation with loop detection
- **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:275-307`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L275-L307) - Perimeter loop construction during edge generation

**Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:147-149`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L147-L149), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:302-303`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L302-L303), [`vendor/KotOR.js/src/odyssey/WalkmeshPerimeter.ts:12-20`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshPerimeter.ts#L12-L20), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:347-352`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L347-L352), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:716-782`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L716-L782)

---

## Runtime Model

The runtime model provides high-level, in-memory representations of walkmesh data that are easier to work with than raw binary structures. These classes abstract away the binary format details and provide convenient methods for common operations.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:25-496`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L25-L496)

### BWM Class

The `BWM` class represents a complete walkmesh in memory, providing a high-level interface for working with walkmesh data.

**Key Attributes:**

- **`faces`**: Ordered list of `BWMFace` objects representing all triangular faces in the walkmesh
  - Faces are typically ordered with walkable faces first, followed by non-walkable faces
  - The face list is the primary data structure for accessing walkmesh geometry
- **`walkmesh_type`**: Type of walkmesh (`BWMType.AreaModel` for WOK, `BWMType.PlaceableOrDoor` for PWK/DWK)
- **`position`**: 3D position offset for the walkmesh in world space
- **Positional hooks**: `relative_hook1`, `relative_hook2`, `absolute_hook1`, `absolute_hook2` - Used by the engine for positioning and interaction points

**Helper Methods:**

- `walkable_faces()`: Returns a filtered list of only walkable faces (for pathfinding)
- `unwalkable_faces()`: Returns a filtered list of only non-walkable faces (for collision detection)
- `vertices()`: Returns unique vertex objects referenced by faces (identity-based uniqueness)
- Methods for computing adjacencies, perimeters, and AABB trees from geometry

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:126-289`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L126-L289), [`vendor/reone/include/reone/graphics/walkmesh.h:27-89`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/walkmesh.h#L27-L89), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:24-205`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L24-L205)

### BWMFace Class

Each `BWMFace` represents a single triangular face in the walkmesh, containing all information needed for collision detection, pathfinding, and rendering.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:497-534`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L497-L534)

**Key Attributes:**

- **`v1`, `v2`, `v3`**: Vertex objects (`Vector3` instances) defining the triangle's three corners
  - Vertices are shared by reference: multiple faces can reference the same vertex object
  - This ensures geometric consistency and enables efficient adjacency calculations
- **`material`**: `SurfaceMaterial` enum determining walkability and physical properties
  - Controls whether the face is walkable, blocks line of sight, produces sound effects, etc.
- **`trans1`, `trans2`, `trans3`**: Optional per-edge transition indices
  - These are **NOT** unique identifiers and do **NOT** encode geometric adjacency
  - They reference area/room transition data (e.g., door connections, area boundaries)
  - Only present on edges that have corresponding entries in the edges array
  - **Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:164-179`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L164-L179)

**Important**: Adjacency is derived purely from geometry. Two walkable faces are adjacent when they share the same two vertex objects along an edge. The adjacency relationship is computed by comparing vertex references, not by using transition indices.

**Reference**: [`vendor/KotOR.js/src/three/odyssey/OdysseyFace3.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/three/odyssey/OdysseyFace3.ts) - TypeScript face implementation with adjacency handling

### BWMEdge Class

The `BWMEdge` class represents a boundary edge (an edge with no walkable neighbor) computed from adjacency data.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:624-650`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L624-L650)

**Key Attributes:**

- **Face reference**: The `BWMFace` object this edge belongs to
- **Edge index**: The local edge index (0, 1, or 2) within the face
  - Edge 0: between `v1` and `v2`
  - Edge 1: between `v2` and `v3`
  - Edge 2: between `v3` and `v1`
- **Transition value**: Optional transition ID linking to area/room transition data
  - `-1` indicates no transition (just a boundary edge)
  - Non-negative values reference door connections or area boundaries
- **`final`**: Boolean flag marking the end of a perimeter loop
  - Used when constructing perimeter loops from edges

**Usage**: Edges are computed from adjacency data by identifying edges with `-1` adjacency (no walkable neighbor). They're used for area transitions, boundary detection, and perimeter construction.

**Reference**: [`vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:15-110`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshEdge.ts#L15-L110) - Complete edge implementation with line calculations and normals

### BWMNodeAABB Class

The `BWMNodeAABB` class represents a node in the AABB tree, providing spatial acceleration for intersection queries.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:535-623`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L535-L623)

**Key Attributes:**

- **Bounds**: Minimum and maximum bounding box coordinates (x, y, z) defining the node's spatial extent
- **Face index**: For leaf nodes, the index of the associated face; `-1` for internal nodes
- **Split plane**: The axis (X, Y, or Z) along which this node splits space
- **Left/Right children**: References to child nodes (for internal nodes) or `None` (for leaf nodes)

**Usage**: AABB nodes enable efficient broad-phase collision detection and spatial queries. The tree structure allows the engine to quickly eliminate large portions of the walkmesh that cannot possibly intersect with a query, dramatically improving performance for ray casting, point queries, and collision detection.

**Reference**: [`vendor/reone/include/reone/graphics/walkmesh.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/walkmesh.h) - AABB node structure in reone, [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:432-448`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L432-L448) - AABB node reading

---

## Implementation Details

This section covers important implementation considerations and best practices when working with BWM files.

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:42-176`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L42-L176)

The binary reader follows a standard pattern that efficiently loads walkmesh data using the offset-based structure:

1. **Validate header**: Check magic "BWM " and version "V1.0" to ensure file format compatibility
2. **Read walkmesh properties**: Load type, hook vectors, and position. The type determines which data tables will be present (WOK files have AABB trees, adjacencies, edges, and perimeters; PWK/DWK files do not)
3. **Read data table offsets**: Load all offset and count values from the header. These offsets allow random access to different data sections without reading the entire file sequentially
4. **Seek and read data tables**: For each data table (vertices, faces, materials, normals, distances), seek to the specified offset and read the appropriate number of elements. This approach enables streaming and partial loading of large walkmeshes
5. **Process WOK-specific data** (if type is WOK): Load AABB tree nodes, adjacency data, edges, and perimeters. The AABB tree is constructed by linking nodes based on child indices
6. **Process edges and transitions**: Extract transition information from the edges array and apply it to the corresponding faces. This links perimeter edges to area/room transition data
7. **Construct runtime `BWM` object**: Create the high-level walkmesh representation with all loaded data, ready for use by the game engine

The reone implementation demonstrates a clean separation of concerns, with separate methods for loading each data type. The xoreos implementation shows integration with pathfinding systems, where walkmesh data is directly fed into pathfinding data structures.

- **Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:27-92`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L27-L92) - Complete BWM reading implementation with method separation
- **Reference**: [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:42-113`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L42-L113) - Walkmesh loading with pathfinding integration

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:177-350`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L177-L350)

The binary writer must perform several complex operations to generate a valid BWM file:

1. **Calculate all data table offsets**: This requires a "peek" phase where the writer determines the size of each data table before writing. The writer must:
   - Deduplicate and count vertices
   - Sort faces (walkable first, then non-walkable)
   - Calculate adjacency data size (number of walkable faces)
   - Generate AABB tree and count nodes (for WOK files)
   - Compute edges and perimeters
   - Calculate the total size of each section to determine offsets

2. **Write header with offsets**: Write the magic, version, walkmesh properties, and all offset/count values. The offsets must be accurate, as they're used by readers to locate data tables.

3. **Write data tables in order**: Write vertices, face indices, materials, normals, planar distances, AABB nodes (if WOK), adjacencies (if WOK), edges (if WOK), and perimeters (if WOK) in the order specified by the offsets.

4. **Compute adjacencies from geometry**: The runtime model doesn't store adjacency data directly, so it must be computed by comparing face geometry. This involves:
   - Iterating through all pairs of walkable faces
   - Finding shared edges (two common vertices)
   - Encoding adjacency relationships using the `face_index * 3 + edge_index` formula

5. **Generate AABB tree if writing WOK file**: AABB tree generation is a complex operation that typically uses algorithms like:
   - Surface Area Heuristic (SAH): Splits space to minimize expected traversal cost
   - Median Split: Simpler but less optimal, splits along the median of face positions
   - The tree must be balanced for optimal performance

6. **Compute edges and perimeters from adjacency data**: 
   - Identify perimeter edges (edges with `-1` adjacency)
   - Group edges into closed loops (perimeters)
   - Store transition IDs from the runtime model's edge transition data

The kotorblender implementation demonstrates a two-phase approach: a "peek" phase that calculates all sizes and offsets, followed by a "save" phase that writes all data. This ensures accurate offset calculation.

- **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:77-153`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L77-L153) - Peek phase that calculates all offsets
- **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:196-239`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L196-L239) - AABB tree generation using surface area heuristic

**Additional Reference Implementations:**

- **reone (C++)**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp) - Complete BWM reading implementation with AABB tree construction
- **kotorblender (Python)**:
  - [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py) - Blender import with vertex offset handling
  - [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py) - Blender export with adjacency calculation and AABB tree generation
- **xoreos (C++)**: [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp) - Walkmesh loading with pathfinding integration and vertex transformation
- **KotOR.js (TypeScript)**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts) - Complete TypeScript walkmesh implementation with raycasting, point queries, AABB tree traversal, and perimeter building. Includes integration with Three.js for rendering and spatial queries
- **reone (C++) - Runtime Operations**: [`vendor/reone/src/libs/graphics/walkmesh.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/walkmesh.cpp) - Runtime walkmesh operations including raycasting with AABB tree traversal and surface material filtering

**Critical Implementation Notes:**

**Identity vs. Value Equality:**

- Use identity-based searches (`is` operator) when mapping faces back to indices
- Value-based equality can collide: two different face objects with the same vertices are equal by value but distinct by identity
- When computing edge indices (`face_index * 3 + edge_index`), you must use the actual face object's index in the array, not search by value
- **Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:57-75`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L57-L75) - Identity-based indexing helper

**Transitions vs. Adjacency:**

- `trans1`/`trans2`/`trans3` are optional metadata only, **NOT** adjacency definitions
- Adjacency is computed purely from geometry (shared vertices between walkable faces)
- Transitions reference area/room data structures (doors, area boundaries) and are only present on perimeter edges
- **Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:70-75`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L70-L75) - Documentation on transitions

**Vertex Sharing:**

- Vertices are shared by object identity: multiple faces reference the same `Vector3` object
- This ensures geometric consistency: adjacent faces share exact vertex positions
- When modifying vertices, changes affect all faces that reference that vertex
- **Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:290-310`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L290-L310) - Vertex collection method

**Face Ordering:**

- Walkable faces are typically ordered before non-walkable faces in the face array
- This ordering is important because adjacency data indices correspond to walkable face positions
- When writing, maintain this ordering to ensure adjacency indices remain valid
- **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:175-194`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L175-L194) - Face sorting logic

**Format-Specific Features:**

- **AABB tree**: Only present in WOK (area) walkmeshes, not PWK/DWK
  - PWK/DWK files have `aabb_count = 0` and `aabb_offset = 0` in the header
  - AABB trees are expensive to compute and unnecessary for small placeable objects
- **Adjacency data**: Only stored for walkable faces
  - The adjacency count equals the number of walkable faces
  - Non-walkable faces don't participate in pathfinding, so they don't need adjacency data
- **Edge indices**: Encoded as `face_index * 3 + local_edge_index` (where local_edge_index is 0-2)
  - This encoding allows a single integer to identify both the face and the specific edge
  - Used in both adjacency indices and edge array entries

**Performance Considerations:**

- AABB trees dramatically improve performance for spatial queries (O(log N) vs O(N))
- Adjacency precomputation speeds up pathfinding by avoiding geometric tests during pathfinding
- Vertex sharing reduces memory usage and ensures geometric consistency
- Face ordering enables efficient iteration over walkable faces without material checks

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:1-75`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L1-L75) - Module-level documentation with implementation notes

---

This documentation aims to provide a comprehensive overview of the KotOR BWM file format, focusing on the detailed file structure and data formats used within the games.
