# PTH (Path)

Part of the [GFF File Format Documentation](GFF-File-Format).


PTH files define pathfinding data for modules, distinct from the navigation mesh (walkmesh). They store a network of waypoints and connections used for high-level AI navigation planning.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/pth.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/pth.py)

## Path Points

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Path_Points` | List | List of navigation nodes |

**Path_Points Struct Fields:**

- `X` (Float): X Coordinate
- `Y` (Float): Y Coordinate
- `Z` (Float): Z Coordinate (unused/flat)

## Path Connections

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Path_Connections` | List | List of edges between nodes |

**Path_Connections Struct Fields:**

- `Path_Source` (Int): Index of source point
- `Path_Dest` (Int): Index of destination point

## Usage

- **AI Navigation**: Used by NPCs to plot paths across large distances or complex areas where straight-line walkmesh navigation fails.
- **Legacy Support**: Often redundant in modern engines with navigation meshes, but used in Aurora/Odyssey for optimization.
- **Editor**: Visualized as a web of lines connecting nodes.

---

