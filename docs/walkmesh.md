# KotOR Walkmesh (WOK/BWM) Cheat Sheet

This document summarises how Binary WalkMeshes (BWM), stored on disk as WOK
files, are represented and manipulated in PyKotor. The format derives from
BioWare’s Aurora / Neverwinter Nights engine and is used by both KotOR games.

## Runtime Model ([`pykotor.resource.formats.bwm`](Libraries/PyKotor/src/pykotor/resource/formats/bwm/))

- **[`BWM`](Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L25)** – In-memory walkmesh model. Holds the ordered `faces` list plus

  positional hooks used by the engine. Helper methods expose geometry,
  adjacency, perimeters, and AABB (bounding volume) construction.

- **[`BWMFace`](Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L497)** – A single triangle with:
  - `v1`, `v2`, `v3` vertex objects (instances of `Vector3`);
  - `material` (`SurfaceMaterial`), which determines whether the face is
    walkable;
  - `trans1`, `trans2`, `trans3`, optional per-edge transition indices used by
    the engine (e.g., doorway triggers). **They are not unique identifiers** and
    do **not** encode adjacency.
- **Adjacency** – Derived purely from geometry. Two walkable faces are adjacent
  when they share the same two vertex objects along an edge.
- **Perimeters / [`BWMEdge`](Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L624)** – Boundary edges (edges with no walkable neighbour)
  computed from adjacency. Each edge stores the face, edge index (0–2) and an
  optional transition value. `final=True` marks the end of a perimeter loop.
- **AABB Tree** ([`BWMNodeAABB`](Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L535)) – Broad-phase acceleration structure for fast
  intersection checks (e.g., ray casts, point-in-triangle tests).
- **Identity-aware indexing** – Faces and vertices implement value-based
  equality for comparison/tests, so when computing global edge indices the code
  must recover list positions by **identity** (`is`). The helper
  `_index_by_identity` guarantees the correct face index even when faces compare
  equal by value. Never call `list.index(face)` in these code paths.

## Binary Layout Highlights ([`io_bwm.py`](Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py))

[`BWMBinaryReader`](Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L42) and [`BWMBinaryWriter`](Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L177) convert between BWM instances and the
on-disk format. The major sections are:

1. Header: `"BWM "` magic + `"V1.0"` version.
2. Walkmesh properties: type (`BWMType`), hook vectors, absolute/relative
   positions.
3. Vertices: float32 triplets.
4. Faces: triplets of uint32 vertex indices.
5. Materials: uint32 surface material per face.
6. Derived data: face normals (float32) and planar distances (float32).
7. AABB nodes: bounds, optional face index (or `0xFFFFFFFF`), significant plane,
   left/right child indices (1-based, or `0xFFFFFFFF`).
8. Walkable adjacencies: three 32-bit ints per walkable face; `-1` indicates no
   neighbour.
9. Edges: `(edge_index, transition)` pairs for perimeter edges where
   `edge_index = face_index * 3 + local_edge_index`.
10. Perimeters: 1-based indices into the edge array for edges flagged as final.

All index lookups during serialisation use identity-based searches (`is`) to
ensure consistency with the runtime model.

## High-level Tips for Contributors

- Use `_index_by_identity` (or equivalent identity-based iteration) when mapping
  faces back to indices. Value-based equality can and will collide.
- Treat `trans1`/`trans2`/`trans3` as optional metadata only. They do not define
  adjacency and should not be used to deduce unique faces.
- The walkmesh logic assumes vertices are shared by object identity. Avoid
  cloning `Vector3` instances arbitrarily unless you also update all references.
- When adding new features, keep the binary writer sections in sync with the
  reader; each count/offset must match the actual packed data length.

For deeper reference, see: `bwm_data.py` (runtime model), `io_bwm.py`
(binary I/O), unit tests in `tests/test_pykotor/resource/formats/test_wok.py`,
and the original KotOR/NWN toolset documentation.
