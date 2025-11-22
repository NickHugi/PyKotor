# KotOR BWM File Format Documentation

This document provides a detailed description of the BWM (Binary WalkMesh) file format used in Knights of the Old Republic (KotOR) games. BWM files, stored on disk as WOK files, define walkable surfaces for pathfinding and collision detection in game areas.

## Table of Contents

- [KotOR BWM File Format Documentation](#kotor-bwm-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [Walkmesh Properties](#walkmesh-properties)
    - [Vertices](#vertices)
    - [Faces](#faces)
    - [Materials](#materials)
    - [Derived Data](#derived-data)
    - [AABB Tree](#aabb-tree)
    - [Walkable Adjacencies](#walkable-adjacencies)
    - [Edges](#edges)
    - [Perimeters](#perimeters)
  - [Runtime Model](#runtime-model)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

BWM files define walkable surfaces using triangular faces. Each face has material properties that determine whether it's walkable, and adjacency information for pathfinding.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/)

**Reference**: [`vendor/reone/src/libs/resource/format/bwmreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bwmreader.cpp)

---

## Binary Format

### File Header

| Name         | Type    | Offset | Size | Description                                    |
| ------------ | ------- | ------ | ---- | ---------------------------------------------- |
| Magic        | char[4] | 0      | 4    | Always `"BWM "` (space-padded)                 |
| Version      | char[4] | 4      | 4    | Always `"V1.0"`                                 |

### Walkmesh Properties

| Name              | Type    | Size | Description                                                      |
| ----------------- | ------- | ---- | ---------------------------------------------------------------- |
| Type              | uint32  | 4    | Walkmesh type (see BWMType enum)                                |
| Hook Vectors      | float[3]| 12   | Position hooks used by the engine                               |
| Absolute/Relative Positions | varies | varies | Position data based on type                                    |

### Vertices

| Name     | Type      | Size | Description                                                      |
| -------- | --------- | ---- | ---------------------------------------------------------------- |
| Vertices | float32[3]| 12×N | Array of vertex positions (X, Y, Z triplets)                    |

### Faces

| Name  | Type     | Size | Description                                                      |
| ----- | -------- | ---- | ---------------------------------------------------------------- |
| Faces | uint32[3]| 12×N | Array of face vertex indices (triplets referencing vertex array) |

### Materials

| Name      | Type   | Size | Description                                                      |
| --------- | ------ | ---- | ---------------------------------------------------------------- |
| Materials | uint32  | 4×N  | Surface material index per face (determines walkability)         |

### Derived Data

| Name           | Type    | Size | Description                                                      |
| -------------- | ------- | ---- | ---------------------------------------------------------------- |
| Face Normals   | float32[3] | 12×N | Normal vectors for each face                                    |
| Planar Distances | float32 | 4×N | D component of plane equation for each face                      |

### AABB Tree

| Name          | Type    | Size | Description                                                      |
| ------------- | ------- | ---- | ---------------------------------------------------------------- |
| AABB Nodes    | varies  | varies | Bounding box tree nodes for spatial acceleration                |

Each AABB node contains:
- Bounds (min/max coordinates)
- Face index (or `0xFFFFFFFF` for internal nodes)
- Significant plane
- Left/right child indices (1-based, or `0xFFFFFFFF` for leaf nodes)

### Walkable Adjacencies

| Name            | Type    | Size | Description                                                      |
| --------------- | ------- | ---- | ---------------------------------------------------------------- |
| Adjacencies     | int32[3]| 12×N | Three adjacency indices per walkable face (-1 = no neighbor)     |

### Edges

| Name  | Type     | Size | Description                                                      |
| ----- | -------- | ---- | ---------------------------------------------------------------- |
| Edges | varies   | varies | Perimeter edge data (edge_index, transition pairs)             |

### Perimeters

| Name      | Type   | Size | Description                                                      |
| --------- | ------ | ---- | ---------------------------------------------------------------- |
| Perimeters | uint32 | 4×N  | 1-based indices into edge array for edges flagged as final      |

---

## Runtime Model

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:25-496`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L25-L496)

### BWM Class

The `BWM` class represents a walkmesh in memory:

- **`faces`**: Ordered list of `BWMFace` objects
- **Positional hooks**: Used by the engine for positioning
- Helper methods for geometry, adjacency, perimeters, and AABB construction

### BWMFace Class

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:497-534`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L497-L534)

Each face contains:
- `v1`, `v2`, `v3`: Vertex objects (`Vector3` instances)
- `material`: `SurfaceMaterial` enum determining walkability
- `trans1`, `trans2`, `trans3`: Optional per-edge transition indices (not unique identifiers, do not encode adjacency)

**Important**: Adjacency is derived purely from geometry. Two walkable faces are adjacent when they share the same two vertex objects along an edge.

### BWMEdge Class

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:624-650`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L624-L650)

Boundary edges (edges with no walkable neighbor) computed from adjacency:
- Face reference
- Edge index (0-2)
- Optional transition value
- `final=True` marks the end of a perimeter loop

### BWMNodeAABB Class

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:535-623`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L535-L623)

Broad-phase acceleration structure for fast intersection checks (ray casts, point-in-triangle tests).

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:42-176`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L42-L176)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:177-350`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L177-L350)

**Important Notes**:
- Use identity-based searches (`is`) when mapping faces back to indices
- Value-based equality can collide
- `trans1`/`trans2`/`trans3` are optional metadata only, not adjacency definitions
- Vertices are shared by object identity

---

This documentation aims to provide a comprehensive overview of the KotOR BWM file format, focusing on the detailed file structure and data formats used within the games.
