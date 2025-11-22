# KotOR MDL/MDX File Format Documentation

This document provides a detailed description of the MDL/MDX file format used in Knights of the Old Republic (KotOR) games. The MDL (Model) and MDX (Model Extension) files together define 3D models, including geometry, animations, and other related data.

## Table of Contents

- [KotOR MDL/MDX File Format Documentation](#kotor-mdlmdx-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [File Headers](#file-headers)
    - [MDL File Header](#mdl-file-header)
    - [Model Header](#model-header)
    - [Geometry Header](#geometry-header)
    - [Names Header](#names-header)
    - [Animation Header](#animation-header)
    - [Event Structure](#event-structure)
  - [Node Structures](#node-structures)
    - [Node Header](#node-header)
    - [Trimesh Header](#trimesh-header)
    - [Danglymesh Header](#danglymesh-header)
    - [Skinmesh Header](#skinmesh-header)
    - [Lightsaber Header](#lightsaber-header)
    - [Light Header](#light-header)
    - [Emitter Header](#emitter-header)
    - [Reference Header](#reference-header)
  - [Controllers](#controllers)
    - [Controller Structure](#controller-structure)
  - [Additional Controller Types](#additional-controller-types)
    - [Light Controllers](#light-controllers)
    - [Emitter Controllers](#emitter-controllers)
  - [Node Types](#node-types)
    - [Node Type Bitmasks](#node-type-bitmasks)
    - [Common Node Type Combinations](#common-node-type-combinations)
  - [MDX Data Format](#mdx-data-format)
    - [MDX Data Bitmap Masks](#mdx-data-bitmap-masks)
    - [Skin Mesh Specific Data](#skin-mesh-specific-data)
  - [Vertex and Face Data](#vertex-and-face-data)
    - [Vertex Structure](#vertex-structure)
    - [Face Structure](#face-structure)
  - [Vertex Data Processing](#vertex-data-processing)
    - [Vertex Normal Calculation](#vertex-normal-calculation)
    - [Tangent Space Calculation](#tangent-space-calculation)
  - [Model Classification Flags](#model-classification-flags)
  - [File Identification](#file-identification)
    - [Binary vs ASCII Format](#binary-vs-ascii-format)
    - [KotOR 1 vs KotOR 2 Models](#kotor-1-vs-kotor-2-models)
  - [Model Hierarchy](#model-hierarchy)
    - [Node Relationships](#node-relationships)
    - [Node Transformations](#node-transformations)
  - [Smoothing Groups](#smoothing-groups)
  - [ASCII MDL Format](#ascii-mdl-format)
    - [Model Header Section](#model-header-section)
    - [Geometry Section](#geometry-section)
    - [Node Definitions](#node-definitions)
    - [Animation Data](#animation-data)
  - [Controller Data Formats](#controller-data-formats)
    - [Single Controllers](#single-controllers)
    - [Keyed Controllers](#keyed-controllers)
    - [Special Controller Cases](#special-controller-cases)
  - [Skin Meshes and Skeletal Animation](#skin-meshes-and-skeletal-animation)
    - [Bone Mapping and Lookup Tables](#bone-mapping-and-lookup-tables)
      - [Bone Map (`bonemap`)](#bone-map-bonemap)
      - [Bone Serial and Node Number Lookups](#bone-serial-and-node-number-lookups)
    - [Vertex Skinning](#vertex-skinning)
      - [Bone Weight Format (MDX)](#bone-weight-format-mdx)
      - [Vertex Transformation](#vertex-transformation)
    - [Bind Pose Data](#bind-pose-data)
      - [QBones (Quaternion Rotations)](#qbones-quaternion-rotations)
      - [TBones (Translation Vectors)](#tbones-translation-vectors)
      - [Bone Matrix Computation](#bone-matrix-computation)
  - [Additional References](#additional-references)
    - [Editors](#editors)
    - [See Also](#see-also)

---

## File Structure Overview

KotOR models are defined using two files:

- **MDL**: Contains the primary model data, including geometry and node structures.
- **MDX**: Contains additional mesh data, such as vertex buffers.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/mdl/`](Libraries/PyKotor/src/pykotor/resource/formats/mdl/)

The MDL file begins with a file header, followed by a model header, geometry header, and various node structures. Offsets within the MDL file are typically relative to the start of the file, excluding the first 12 bytes (the file header).

Below is an overview of the typical layout:

```plaintext
+-----------------------------+
| MDL File Header             |
+-----------------------------+
| Model Header                |
+-----------------------------+
| Geometry Header             |
+-----------------------------+
| Name Header                 |
+-----------------------------+
| Animations                  |
+-----------------------------+
| Nodes                       |
+-----------------------------+
```

---

## File Headers

### MDL File Header

The MDL file header is 12 bytes in size and contains the following fields:

| Name         | Type    | Offset | Description            |
| ------------ | ------- | ------ | ---------------------- |
| Unused       | UInt32  | 0      | Always set to `0`.     |
| MDL Size     | UInt32  | 4      | Size of the MDL file.  |
| MDX Size     | UInt32  | 8      | Size of the MDX file.  |

### Model Header

The Model Header is 92 bytes in size and immediately follows the Geometry Header. Together with the Geometry Header (80 bytes), the combined structure is 172 bytes from the start of the MDL data section (offset 12 in the file).

| Name                         | Type            | Offset | Description                                                                 |
| ---------------------------- | --------------- | ------ | --------------------------------------------------------------------------- |
| Classification               | UInt8           | 0      | Model classification type (see [Model Classification Flags](#model-classification-flags)). |
| Subclassification            | UInt8           | 1      | Model subclassification value.                                              |
| Unknown                      | UInt8           | 2      | Purpose unknown (possibly smoothing-related).                               |
| Affected By Fog              | UInt8           | 3      | `0`: Not affected by fog, `1`: Affected by fog.                             |
| Child Model Count            | UInt32          | 4      | Number of child models.                                                     |
| Animation Array Offset       | UInt32          | 8      | Offset to the animation array.                                              |
| Animation Count              | UInt32          | 12     | Number of animations.                                                       |
| Animation Count (duplicate)  | UInt32          | 16     | Duplicate value of animation count.                                         |
| Parent Model Pointer         | UInt32          | 20     | Pointer to parent model (context-dependent).                                |
| Bounding Box Min             | Float[3]        | 24     | Minimum coordinates of the bounding box (X, Y, Z).                          |
| Bounding Box Max             | Float[3]        | 36     | Maximum coordinates of the bounding box (X, Y, Z).                          |
| Radius                       | Float           | 48     | Radius of the model's bounding sphere.                                      |
| Animation Scale              | Float           | 52     | Scale factor for animations (typically 1.0).                                |
| Supermodel Name              | Byte[32]        | 56     | Name of the supermodel (null-terminated string).                            |

### Geometry Header

The Geometry Header is 80 bytes in size and is located at offset 12 in the file (immediately after the File Header). It contains fundamental model information and game engine version identifiers.

| Name                        | Type        | Offset | Description                                                                                     |
| --------------------------- | ----------- | ------ | ----------------------------------------------------------------------------------------------- |
| Function Pointer 0          | UInt32      | 0      | Game engine version identifier (see [KotOR 1 vs KotOR 2 Models](#kotor-1-vs-kotor-2-models)).  |
| Function Pointer 1          | UInt32      | 4      | Secondary function pointer used by the game engine.                                             |
| Model Name                  | Byte[32]    | 8      | Name of the model (null-terminated string).                                                     |
| Root Node Offset            | UInt32      | 40     | Offset to the root node structure (relative to MDL data offset 12).                             |
| Node Count                  | UInt32      | 44     | Total number of nodes in the model hierarchy.                                                   |
| Unknown Array Definition 1  | UInt32[3]   | 48     | Array definition structure (offset, count, count duplicate). Purpose unknown.                   |
| Unknown Array Definition 2  | UInt32[3]   | 60     | Array definition structure (offset, count, count duplicate). Purpose unknown.                   |
| Reference Count             | UInt32      | 72     | Count of reference nodes or related structures.                                                 |
| Geometry Type               | UInt8       | 76     | Type of geometry header: `0x00`: Model geometry, `0x01`: Animation geometry.                    |
| Padding                     | UInt8[3]    | 77     | Padding bytes for alignment.                                                                    |

### Names Header

The Names Header is located at file offset 180 (28 bytes). It contains metadata for node name lookup and MDX file information. This section bridges the model header data and the animation/node structures.

| Name                | Type    | Offset | Description                                                                 |
| ------------------- | ------- | ------ | --------------------------------------------------------------------------- |
| Root Node Offset    | UInt32  | 0      | Offset to the root node (often a duplicate of the geometry header value).   |
| Unknown/Padding     | UInt32  | 4      | Unknown field, typically unused or padding.                                 |
| MDX Data Size       | UInt32  | 8      | Size of the MDX file data in bytes.                                         |
| MDX Data Offset     | UInt32  | 12     | Offset to MDX data within the MDX file (typically 0).                       |
| Names Array Offset  | UInt32  | 16     | Offset to the array of name string offsets.                                 |
| Names Count         | UInt32  | 20     | Number of node names in the array.                                          |
| Names Count (dup)   | UInt32  | 24     | Duplicate value of names count.                                             |

### Animation Header

Each animation begins with a Geometry Header (80 bytes) followed by an Animation Header (56 bytes), for a combined size of 136 bytes.

| Name                  | Type            | Offset | Description                                                |
| --------------------- | --------------- | ------ | ---------------------------------------------------------- |
| Geometry Header       | GeometryHeader  | 0      | Standard 80-byte Geometry Header (geometry type = `0x01`).|
| Animation Length      | Float           | 80     | Duration of the animation in seconds.                      |
| Transition Time       | Float           | 84     | Transition/blend time to this animation in seconds.        |
| Animation Root        | Byte[32]        | 88     | Root node name for the animation (null-terminated string). |
| Event Array Offset    | UInt32          | 120    | Offset to animation events array.                          |
| Event Count           | UInt32          | 124    | Number of animation events.                                |
| Event Count (dup)     | UInt32          | 128    | Duplicate value of event count.                            |
| Unknown               | UInt32          | 132    | Purpose unknown.                                           |

### Event Structure

Each animation event is 36 bytes in size and triggers game actions at specific animation timestamps.

| Name            | Type      | Offset | Description                                                          |
| --------------- | --------- | ------ | -------------------------------------------------------------------- |
| Activation Time | Float     | 0      | Time in seconds when the event triggers during animation playback.   |
| Event Name      | Byte[32]  | 4      | Name of the event (null-terminated string, e.g., "detonate").        |

---

## Node Structures

### Node Header

The Node Header is 80 bytes in size and is present in all node types. It defines the node's position in the hierarchy, its transform, and references to child nodes and animation controllers.

| Name                     | Type        | Offset | Description                                                                        |
| ------------------------ | ----------- | ------ | ---------------------------------------------------------------------------------- |
| Node Type Flags          | UInt16      | 0      | Bitmask indicating node features (see [Node Type Bitmasks](#node-type-bitmasks)). |
| Node Index               | UInt16      | 2      | Sequential index of this node in the model.                                        |
| Node Name Index          | UInt16      | 4      | Index into the names array for this node's name.                                   |
| Padding                  | UInt16      | 6      | Padding for alignment.                                                             |
| Root Node Offset         | UInt32      | 8      | Offset to the model's root node.                                                   |
| Parent Node Offset       | UInt32      | 12     | Offset to this node's parent node (0 if root).                                     |
| Position                 | Float[3]    | 16     | Node position in local space (X, Y, Z).                                            |
| Orientation              | Float[4]    | 28     | Node orientation as quaternion (W, X, Y, Z).                                       |
| Child Array Offset       | UInt32      | 44     | Offset to array of child node offsets.                                             |
| Child Count              | UInt32      | 48     | Number of child nodes.                                                             |
| Child Count (dup)        | UInt32      | 52     | Duplicate value of child count.                                                    |
| Controller Array Offset  | UInt32      | 56     | Offset to array of controller structures.                                          |
| Controller Count         | UInt32      | 60     | Number of controllers attached to this node.                                       |
| Controller Count (dup)   | UInt32      | 64     | Duplicate value of controller count.                                               |
| Controller Data Offset   | UInt32      | 68     | Offset to controller keyframe/data array.                                          |
| Controller Data Count    | UInt32      | 72     | Number of floats in controller data array.                                         |
| Controller Data Count    | UInt32      | 76     | Duplicate value of controller data count.                                          |

### Trimesh Header

The Trimesh Header defines static mesh geometry and is 332 bytes in KotOR 1 and 340 bytes in KotOR 2 models. This header immediately follows the 80-byte Node Header.

| Name                         | Type         | Offset     | Description                                                                                 |
| ---------------------------- | ------------ | ---------- | ------------------------------------------------------------------------------------------- |
| Function Pointer 0           | UInt32       | 0          | Game engine function pointer (version-specific).                                            |
| Function Pointer 1           | UInt32       | 4          | Secondary game engine function pointer.                                                     |
| Faces Array Offset           | UInt32       | 8          | Offset to face definitions array.                                                           |
| Faces Count                  | UInt32       | 12         | Number of triangular faces in the mesh.                                                     |
| Faces Count (dup)            | UInt32       | 16         | Duplicate of faces count.                                                                   |
| Bounding Box Min             | Float[3]     | 20         | Minimum bounding box coordinates (X, Y, Z).                                                 |
| Bounding Box Max             | Float[3]     | 32         | Maximum bounding box coordinates (X, Y, Z).                                                 |
| Radius                       | Float        | 44         | Bounding sphere radius.                                                                     |
| Average Point                | Float[3]     | 48         | Average vertex position (centroid).                                                         |
| Diffuse Color                | Float[3]     | 60         | Material diffuse color (R, G, B, range 0.0-1.0).                                            |
| Ambient Color                | Float[3]     | 72         | Material ambient color (R, G, B, range 0.0-1.0).                                            |
| Transparency Hint            | UInt32       | 84         | Transparency rendering mode.                                                                |
| Texture 0 Name               | Byte[32]     | 88         | Primary diffuse texture name (null-terminated).                                             |
| Texture 1 Name               | Byte[32]     | 120        | Secondary texture name, often lightmap (null-terminated).                                   |
| Texture 2 Name               | Byte[12]     | 152        | Tertiary texture name (null-terminated).                                                    |
| Texture 3 Name               | Byte[12]     | 164        | Quaternary texture name (null-terminated).                                                  |
| Indices Count Array Offset   | UInt32       | 176        | Offset to vertex indices count array.                                                       |
| Indices Count Array Count    | UInt32       | 180        | Number of entries in indices count array.                                                   |
| Indices Count Array Count    | UInt32       | 184        | Duplicate of indices count array count.                                                     |
| Indices Offset Array Offset  | UInt32       | 188        | Offset to vertex indices offset array.                                                      |
| Indices Offset Array Count   | UInt32       | 192        | Number of entries in indices offset array.                                                  |
| Indices Offset Array Count   | UInt32       | 196        | Duplicate of indices offset array count.                                                    |
| Inverted Counter Array Offset| UInt32       | 200        | Offset to inverted counter array.                                                           |
| Inverted Counter Array Count | UInt32       | 204        | Number of entries in inverted counter array.                                                |
| Inverted Counter Array Count | UInt32       | 208        | Duplicate of inverted counter array count.                                                  |
| Unknown Values               | Int32[3]     | 212        | Typically `{-1, -1, 0}`. Purpose unknown.                                                   |
| Saber Unknown Data           | Byte[8]      | 224        | Data specific to lightsaber meshes.                                                         |
| Unknown                      | UInt32       | 232        | Purpose unknown.                                                                            |
| UV Direction X               | Float        | 236        | UV animation direction X component.                                                         |
| UV Direction Y               | Float        | 240        | UV animation direction Y component.                                                         |
| UV Jitter                    | Float        | 244        | UV animation jitter amount.                                                                 |
| UV Jitter Speed              | Float        | 248        | UV animation jitter speed.                                                                  |
| MDX Vertex Size              | UInt32       | 252        | Size in bytes of each vertex in MDX data.                                                   |
| MDX Data Flags               | UInt32       | 256        | Bitmask of present vertex attributes (see [MDX Data Bitmap Masks](#mdx-data-bitmap-masks)).|
| MDX Vertices Offset          | Int32        | 260        | Relative offset to vertex positions in MDX (or -1 if none).                                 |
| MDX Normals Offset           | Int32        | 264        | Relative offset to vertex normals in MDX (or -1 if none).                                   |
| MDX Vertex Colors Offset     | Int32        | 268        | Relative offset to vertex colors in MDX (or -1 if none).                                    |
| MDX Tex 0 UVs Offset         | Int32        | 272        | Relative offset to primary texture UVs in MDX (or -1 if none).                              |
| MDX Tex 1 UVs Offset         | Int32        | 276        | Relative offset to secondary texture UVs in MDX (or -1 if none).                            |
| MDX Tex 2 UVs Offset         | Int32        | 280        | Relative offset to tertiary texture UVs in MDX (or -1 if none).                             |
| MDX Tex 3 UVs Offset         | Int32        | 284        | Relative offset to quaternary texture UVs in MDX (or -1 if none).                           |
| MDX Tangent Space Offset     | Int32        | 288        | Relative offset to tangent space data in MDX (or -1 if none).                               |
| MDX Unknown Offset 1         | Int32        | 292        | Relative offset to unknown MDX data (or -1 if none).                                        |
| MDX Unknown Offset 2         | Int32        | 296        | Relative offset to unknown MDX data (or -1 if none).                                        |
| MDX Unknown Offset 3         | Int32        | 300        | Relative offset to unknown MDX data (or -1 if none).                                        |
| Vertex Count                 | UInt16       | 304        | Number of vertices in the mesh.                                                             |
| Texture Count                | UInt16       | 306        | Number of textures used by the mesh.                                                        |
| Lightmapped                  | UInt8        | 308        | `1` if mesh uses lightmap, `0` otherwise.                                                   |
| Rotate Texture               | UInt8        | 309        | `1` if texture should rotate, `0` otherwise.                                                |
| Background Geometry          | UInt8        | 310        | `1` if background geometry, `0` otherwise.                                                  |
| Shadow                       | UInt8        | 311        | `1` if mesh casts shadows, `0` otherwise.                                                   |
| Beaming                      | UInt8        | 312        | `1` if beaming effect enabled, `0` otherwise.                                               |
| Render                       | UInt8        | 313        | `1` if mesh is renderable, `0` if hidden.                                                   |
| Unknown Flag                 | UInt8        | 314        | Purpose unknown (possibly UV animation enable).                                             |
| Padding                      | UInt8        | 315        | Padding byte.                                                                               |
| Total Area                   | Float        | 316        | Total surface area of all faces.                                                            |
| Unknown                      | UInt32       | 320        | Purpose unknown.                                                                            |
| **K2 Unknown 1**             | **UInt32**   | **324**    | **KotOR 2 only:** Additional unknown field.                                                 |
| **K2 Unknown 2**             | **UInt32**   | **328**    | **KotOR 2 only:** Additional unknown field.                                                 |
| MDX Data Offset              | UInt32       | 324/332    | Absolute offset to this mesh's vertex data in the MDX file.                                 |
| MDL Vertices Offset          | UInt32       | 328/336    | Offset to vertex coordinate array in MDL file (for walkmesh/AABB nodes).                    |

### Danglymesh Header

The Danglymesh Header extends the Trimesh Header with 28 additional bytes for physics simulation parameters. Total size is 360 bytes (K1) or 368 bytes (K2). The danglymesh extension immediately follows the trimesh data.

| Name                   | Type    | Offset     | Description                                                                      |
| ---------------------- | ------- | ---------- | -------------------------------------------------------------------------------- |
| *Trimesh Header*       | *...*   | *0-331*    | *Standard Trimesh Header (332 bytes K1, 340 bytes K2).*                          |
| Constraints Offset     | UInt32  | 332/340    | Offset to vertex constraint values array.                                        |
| Constraints Count      | UInt32  | 336/344    | Number of vertex constraints (matches vertex count).                             |
| Constraints Count (dup)| UInt32  | 340/348    | Duplicate of constraints count.                                                  |
| Displacement           | Float   | 344/352    | Maximum displacement distance for physics simulation.                            |
| Tightness              | Float   | 348/356    | Tightness/stiffness of the spring simulation (0.0-1.0).                          |
| Period                 | Float   | 352/360    | Oscillation period in seconds.                                                   |
| Unknown                | UInt32  | 356/364    | Purpose unknown.                                                                 |

### Skinmesh Header

The Skinmesh Header extends the Trimesh Header with 100 additional bytes for skeletal animation data. Total size is 432 bytes (K1) or 440 bytes (K2). The skinmesh extension immediately follows the trimesh data.

| Name                                  | Type       | Offset     | Description                                                                      |
| ------------------------------------- | ---------- | ---------- | -------------------------------------------------------------------------------- |
| *Trimesh Header*                      | *...*      | *0-331*    | *Standard Trimesh Header (332 bytes K1, 340 bytes K2).*                          |
| Unknown Weights                       | Int32[3]   | 332/340    | Purpose unknown (possibly compilation weights).                                  |
| MDX Bone Weights Offset               | UInt32     | 344/352    | Offset to bone weight data in MDX file (4 floats per vertex).                    |
| MDX Bone Indices Offset               | UInt32     | 348/356    | Offset to bone index data in MDX file (4 floats per vertex, cast to uint16).    |
| Bone Map Offset                       | UInt32     | 352/360    | Offset to bone map array (maps local bone indices to skeleton bone numbers).    |
| Bone Map Count                        | UInt32     | 356/364    | Number of bones referenced by this mesh (max 16).                                |
| QBones Offset                         | UInt32     | 360/368    | Offset to quaternion bind pose array (4 floats per bone).                        |
| QBones Count                          | UInt32     | 364/372    | Number of quaternion bind poses.                                                 |
| QBones Count (dup)                    | UInt32     | 368/376    | Duplicate of QBones count.                                                       |
| TBones Offset                         | UInt32     | 372/380    | Offset to translation bind pose array (3 floats per bone).                       |
| TBones Count                          | UInt32     | 376/384    | Number of translation bind poses.                                                |
| TBones Count (dup)                    | UInt32     | 380/388    | Duplicate of TBones count.                                                       |
| Unknown Array                         | UInt32[3]  | 384/392    | Purpose unknown.                                                                 |
| Bone Node Serial Numbers              | UInt16[16] | 396/404    | Serial indices of bone nodes (0xFFFF for unused slots).                          |
| Padding                               | UInt16     | 428/436    | Padding for alignment.                                                           |

### Lightsaber Header

The Lightsaber Header extends the Trimesh Header with 20 additional bytes for lightsaber blade geometry. Total size is 352 bytes (K1) or 360 bytes (K2). The lightsaber extension immediately follows the trimesh data.

| Name                   | Type    | Offset     | Description                                                                      |
| ---------------------- | ------- | ---------- | -------------------------------------------------------------------------------- |
| *Trimesh Header*       | *...*   | *0-331*    | *Standard Trimesh Header (332 bytes K1, 340 bytes K2).*                          |
| Vertices Offset        | UInt32  | 332/340    | Offset to vertex position array in MDL file (3 floats × 8 vertices × 20 pieces).|
| TexCoords Offset       | UInt32  | 336/344    | Offset to texture coordinates array in MDL file (2 floats × 8 vertices × 20).   |
| Normals Offset         | UInt32  | 340/348    | Offset to vertex normals array in MDL file (3 floats × 8 vertices × 20).        |
| Unknown 1              | UInt32  | 344/352    | Purpose unknown.                                                                 |
| Unknown 2              | UInt32  | 348/356    | Purpose unknown.                                                                 |

### Light Header

The Light Header follows the Node Header and defines light source properties including lens flare effects. Total size is 92 bytes.

| Name                        | Type    | Offset | Description                                                                      |
| --------------------------- | ------- | ------ | -------------------------------------------------------------------------------- |
| Unknown/Padding             | Float[4]| 0      | Purpose unknown, possibly padding or reserved values.                            |
| Flare Sizes Offset          | UInt32  | 16     | Offset to flare sizes array (floats).                                            |
| Flare Sizes Count           | UInt32  | 20     | Number of flare size entries.                                                    |
| Flare Sizes Count (dup)     | UInt32  | 24     | Duplicate of flare sizes count.                                                  |
| Flare Positions Offset      | UInt32  | 28     | Offset to flare positions array (floats, 0.0-1.0 along light ray).               |
| Flare Positions Count       | UInt32  | 32     | Number of flare position entries.                                                |
| Flare Positions Count (dup) | UInt32  | 36     | Duplicate of flare positions count.                                              |
| Flare Color Shifts Offset   | UInt32  | 40     | Offset to flare color shift array (RGB floats).                                  |
| Flare Color Shifts Count    | UInt32  | 44     | Number of flare color shift entries.                                             |
| Flare Color Shifts Count    | UInt32  | 48     | Duplicate of flare color shifts count.                                           |
| Flare Texture Names Offset  | UInt32  | 52     | Offset to flare texture name string offsets array.                               |
| Flare Texture Names Count   | UInt32  | 56     | Number of flare texture names.                                                   |
| Flare Texture Names Count   | UInt32  | 60     | Duplicate of flare texture names count.                                          |
| Flare Radius                | Float   | 64     | Radius of the flare effect.                                                      |
| Light Priority              | UInt32  | 68     | Rendering priority for light culling/sorting.                                    |
| Ambient Only                | UInt32  | 72     | `1` if light only affects ambient, `0` for full lighting.                        |
| Dynamic Type                | UInt32  | 76     | Type of dynamic lighting behavior.                                               |
| Affect Dynamic              | UInt32  | 80     | `1` if light affects dynamic objects, `0` otherwise.                             |
| Shadow                      | UInt32  | 84     | `1` if light casts shadows, `0` otherwise.                                       |
| Flare                       | UInt32  | 88     | `1` if lens flare effect enabled, `0` otherwise.                                 |
| Fading Light                | UInt32  | 92     | `1` if light intensity fades with distance, `0` otherwise.                       |

### Emitter Header

The Emitter Header follows the Node Header and defines particle emitter properties and behavior. Total size is 224 bytes.

| Name                     | Type         | Offset | Description                                                                      |
| ------------------------ | ------------ | ------ | -------------------------------------------------------------------------------- |
| Dead Space               | Float        | 0      | Minimum distance from emitter before particles become visible.                   |
| Blast Radius             | Float        | 4      | Radius of explosive/blast particle effects.                                      |
| Blast Length             | Float        | 8      | Length/duration of blast effects.                                                |
| Branch Count             | UInt32       | 12     | Number of branching paths for particle trails.                                   |
| Control Point Smoothing  | Float        | 16     | Smoothing factor for particle path control points.                               |
| X Grid                   | UInt32       | 20     | Grid subdivisions along X axis for particle spawning.                            |
| Y Grid                   | UInt32       | 24     | Grid subdivisions along Y axis for particle spawning.                            |
| Padding/Unknown          | UInt32       | 28     | Purpose unknown or padding.                                                      |
| Update Script            | Byte[32]     | 32     | Update behavior script name (e.g., "single", "fountain").                        |
| Render Script            | Byte[32]     | 64     | Render mode script name (e.g., "normal", "billboard_to_local_z").                |
| Blend Script             | Byte[32]     | 96     | Blend mode script name (e.g., "normal", "lighten").                              |
| Texture Name             | Byte[32]     | 128    | Particle texture name (null-terminated).                                         |
| Chunk Name               | Byte[16]     | 160    | Associated model chunk name (null-terminated).                                   |
| Two-Sided Texture        | UInt32       | 176    | `1` if texture should render two-sided, `0` for single-sided.                    |
| Loop                     | UInt32       | 180    | `1` if particle system loops, `0` for single playback.                           |
| Render Order             | UInt16       | 184    | Rendering priority/order for particle sorting.                                   |
| Frame Blending           | UInt8        | 186    | `1` if frame blending enabled, `0` otherwise.                                    |
| Depth Texture Name       | Byte[32]     | 187    | Depth/softparticle texture name (null-terminated).                               |
| Padding                  | UInt8        | 219    | Padding byte for alignment.                                                      |
| Flags                    | UInt32       | 220    | Emitter behavior flags bitmask (P2P, bounce, inherit, etc.).                     |

### Reference Header

The Reference Header follows the Node Header and allows models to reference external model files. Total size is 36 bytes. This is commonly used for attachable models like weapons or helmets.

| Name          | Type     | Offset | Description                                                                      |
| ------------- | -------- | ------ | -------------------------------------------------------------------------------- |
| Model ResRef  | Byte[32] | 0      | Referenced model resource name without extension (null-terminated).              |
| Reattachable  | UInt32   | 32     | `1` if model can be detached and reattached dynamically, `0` if permanent.       |

---

## Controllers

### Controller Structure

Each controller is 16 bytes in size and defines animation data for a node property over time. Controllers reference shared keyframe/data arrays stored separately in the model.

| Name              | Type     | Offset | Description                                                                                    |
| ----------------- | -------- | ------ | ---------------------------------------------------------------------------------------------- |
| Type              | UInt32   | 0      | Controller type identifier (e.g., 8=position, 20=orientation, 36=scale).                       |
| Unknown           | UInt16   | 4      | Purpose unknown, typically `0xFFFF`.                                                           |
| Row Count         | UInt16   | 6      | Number of keyframe rows (timepoints) for this controller.                                      |
| Time Index        | UInt16   | 8      | Index into controller data array where time values begin.                                      |
| Data Index        | UInt16   | 10     | Index into controller data array where property values begin.                                  |
| Column Count      | UInt8    | 12     | Number of float values per keyframe (e.g., 3 for position XYZ, 4 for quaternion WXYZ).        |
| Padding           | UInt8[3] | 13     | Padding bytes for 16-byte alignment.                                                           |

**Note:** If bit 4 (value 0x10) is set in the column count byte, the controller uses Bezier interpolation and stores 3× the data per keyframe (value, in-tangent, out-tangent).

---

## Additional Controller Types

### Light Controllers

Controllers specific to light nodes:

| Type | Description                      |
| ---- | -------------------------------- |
| 76   | Color (light color)              |
| 88   | Radius (light radius)            |
| 96   | Shadow Radius                    |
| 100  | Vertical Displacement            |
| 140  | Multiplier (light intensity)     |

### Emitter Controllers

Controllers specific to emitter nodes:

| Type | Description                         |
| ---- | ----------------------------------- |
| 80   | Alpha End (final alpha value)       |
| 84   | Alpha Start (initial alpha value)   |
| 88   | Birth Rate (particle spawn rate)    |
| 92   | Bounce Coefficient                  |
| 96   | Combine Time                        |
| 100  | Drag                                |
| 104  | FPS (frames per second)             |
| 108  | Frame End                           |
| 112  | Frame Start                         |
| 116  | Gravity                             |
| 120  | Life Expectancy                     |
| 124  | Mass                                |
| 128  | P2P Bezier 2                        |
| 132  | P2P Bezier 3                        |
| 136  | Particle Rotation                   |
| 140  | Random Velocity                     |
| 144  | Size Start                          |
| 148  | Size End                            |
| 152  | Size Start Y                        |
| 156  | Size End Y                          |
| 160  | Spread                              |
| 164  | Threshold                           |
| 168  | Velocity                            |
| 172  | X Size                              |
| 176  | Y Size                              |
| 180  | Blur Length                         |
| 184  | Lightning Delay                     |
| 188  | Lightning Radius                    |
| 192  | Lightning Scale                     |
| 196  | Lightning Subdivide                 |
| 200  | Lightning Zig Zag                   |
| 216  | Alpha Mid                           |
| 220  | Percent Start                       |
| 224  | Percent Mid                         |
| 228  | Percent End                         |
| 232  | Size Mid                            |
| 236  | Size Mid Y                          |
| 240  | Random Birth Rate                   |
| 252  | Target Size                         |
| 256  | Number of Control Points            |
| 260  | Control Point Radius                |
| 264  | Control Point Delay                 |
| 268  | Tangent Spread                      |
| 272  | Tangent Length                      |
| 284  | Color Mid                           |
| 380  | Color End                           |
| 392  | Color Start                         |
| 502  | Emitter Detonate                    |

---

## Node Types

### Node Type Bitmasks

Node types in KotOR models are defined using bitmask combinations. Each type of data a node contains corresponds to a specific bitmask.

```c
#define NODE_HAS_HEADER    0x00000001
#define NODE_HAS_LIGHT     0x00000002
#define NODE_HAS_EMITTER   0x00000004
#define NODE_HAS_CAMERA    0x00000008
#define NODE_HAS_REFERENCE 0x00000010
#define NODE_HAS_MESH      0x00000020
#define NODE_HAS_SKIN      0x00000040
#define NODE_HAS_ANIM      0x00000080
#define NODE_HAS_DANGLY    0x00000100
#define NODE_HAS_AABB      0x00000200
#define NODE_HAS_SABER     0x00000800
```

### Common Node Type Combinations

Common node types are created by combining these bitmasks:

| Node Type   | Bitmask Combination                                      | Value  |
| ----------- | -------------------------------------------------------- | ------ |
| Dummy       | `NODE_HAS_HEADER`                                        | 0x001  |
| Light       | `NODE_HAS_HEADER` \| `NODE_HAS_LIGHT`                    | 0x003  |
| Emitter     | `NODE_HAS_HEADER` \| `NODE_HAS_EMITTER`                  | 0x005  |
| Reference   | `NODE_HAS_HEADER` \| `NODE_HAS_REFERENCE`                | 0x011  |
| Mesh        | `NODE_HAS_HEADER` \| `NODE_HAS_MESH`                     | 0x021  |
| Skin Mesh   | `NODE_HAS_HEADER` \| `NODE_HAS_MESH` \| `NODE_HAS_SKIN`  | 0x061  |
| Anim Mesh   | `NODE_HAS_HEADER` \| `NODE_HAS_MESH` \| `NODE_HAS_ANIM`  | 0x0A1  |
| Dangly Mesh | `NODE_HAS_HEADER` \| `NODE_HAS_MESH` \| `NODE_HAS_DANGLY`| 0x121  |
| AABB Mesh   | `NODE_HAS_HEADER` \| `NODE_HAS_MESH` \| `NODE_HAS_AABB`  | 0x221  |
| Saber Mesh  | `NODE_HAS_HEADER` \| `NODE_HAS_MESH` \| `NODE_HAS_SABER` | 0x821  |

---

## MDX Data Format

The MDX file contains additional mesh data that complements the MDL file. The data is organized based on flags indicating the presence of different data types.

### MDX Data Bitmap Masks

The `MDX Data Flags` field in the Trimesh Header uses bitmask flags to indicate which vertex attributes are present in the MDX file:

```c
#define MDX_VERTICES        0x00000001  // Vertex positions (3 floats: X, Y, Z)
#define MDX_TEX0_VERTICES   0x00000002  // Primary texture coordinates (2 floats: U, V)
#define MDX_TEX1_VERTICES   0x00000004  // Secondary texture coordinates (2 floats: U, V) 
#define MDX_TEX2_VERTICES   0x00000008  // Tertiary texture coordinates (2 floats: U, V)
#define MDX_TEX3_VERTICES   0x00000010  // Quaternary texture coordinates (2 floats: U, V)
#define MDX_VERTEX_NORMALS  0x00000020  // Vertex normals (3 floats: X, Y, Z)
#define MDX_VERTEX_COLORS   0x00000040  // Vertex colors (3 floats: R, G, B)
#define MDX_TANGENT_SPACE   0x00000080  // Tangent space data (9 floats: tangent XYZ, bitangent XYZ, normal XYZ)
// Skin Mesh Specific Data (set programmatically, not stored in MDX Data Flags field)
#define MDX_BONE_WEIGHTS    0x00000800  // Bone weights for skinning (4 floats)
#define MDX_BONE_INDICES    0x00001000  // Bone indices for skinning (4 floats, cast to uint16)
```

**Note:** The bone weight and bone index flags (`0x00000800`, `0x00001000`) are not actually stored in the MDX Data Flags field but are used internally by parsers to track skin mesh vertex data presence.

### Skin Mesh Specific Data

For skin meshes, additional vertex attributes are stored in the MDX file for skeletal animation:

- **Bone Weights** (MDX Bone Weights Offset): 4 floats per vertex representing influence weights. Weights sum to 1.0 and correspond to the bone indices. A weight of 0.0 indicates no influence.
  
- **Bone Indices** (MDX Bone Indices Offset): 4 floats per vertex (cast to uint16) representing indices into the mesh's bone map array. Each index maps to a skeleton bone that influences the vertex.

The MDX data for skin meshes is interleaved based on the MDX Vertex Size and the active flags. The bone weight and bone index data are stored as separate attributes and accessed via their respective offsets.

---

## Vertex and Face Data

### Vertex Structure

Each vertex has the following structure:

| Name | Type  | Description         |
| ---- | ----- | ------------------- |
| X    | Float | X-coordinate        |
| Y    | Float | Y-coordinate        |
| Z    | Float | Z-coordinate        |

### Face Structure

Each face (triangle) is defined by:

| Name                | Type    | Description                                      |
| ------------------- | ------- | ------------------------------------------------ |
| Normal              | Vertex  | Normal vector of the face plane.                 |
| Plane Coefficient   | Float   | D component of the face plane equation.          |
| Material            | UInt32  | Material index (refers to `surfacemat.2da`).     |
| Face Adjacency 1    | UInt16  | Index of adjacent face 1.                        |
| Face Adjacency 2    | UInt16  | Index of adjacent face 2.                        |
| Face Adjacency 3    | UInt16  | Index of adjacent face 3.                        |
| Vertex 1            | UInt16  | Index of the first vertex.                       |
| Vertex 2            | UInt16  | Index of the second vertex.                      |
| Vertex 3            | UInt16  | Index of the third vertex.                       |

---

## Vertex Data Processing

### Vertex Normal Calculation

Vertex normals are computed using surrounding face normals, with optional weighting methods:

1. **Area Weighting**: Faces contribute to the vertex normal based on their surface area.

   ```c
   area = 0.5f * length(cross(edge1, edge2))
   weighted_normal = face_normal * area
   ```

   **Reference**: [`vendor/mdlops/MDLOpsM.pm:465-488`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L465-L488) - Heron's formula implementation
   Uses Heron's formula for area calculation.

2. **Angle Weighting**: Faces contribute based on the angle at the vertex.

   ```c
   angle = arccos(dot(normalize(v1 - v0), normalize(v2 - v0)))
   weighted_normal = face_normal * angle
   ```

3. **Crease Angle Limiting**: Faces are excluded if the angle between their normals exceeds a threshold (e.g., 60 degrees).

### Tangent Space Calculation

For normal/bump mapping, tangent and bitangent vectors are calculated per face. KotOR uses a specific tangent space convention that differs from standard implementations.

**Reference**: [`vendor/mdlops/MDLOpsM.pm:5470-5596`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L5470-L5596) - Complete tangent space calculation  
**Based on**: [OpenGL Tutorial - Normal Mapping](http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-13-normal-mapping/) with KotOR-specific modifications

1. **Per-Face Tangent and Bitangent**:

   ```c
   deltaPos1 = v1 - v0;
   deltaPos2 = v2 - v0;
   deltaUV1 = uv1 - uv0;
   deltaUV2 = uv2 - uv0;

   float r = 1.0f / (deltaUV1.x * deltaUV2.y - deltaUV1.y * deltaUV2.x);
   
   // Handle divide-by-zero from overlapping texture vertices
   if (r == 0.0f) {
       r = 2406.6388; // Magic factor from p_g0t01.mdl analysis ([mdlops:5510-5512](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L5510-L5512))
   }
   
   tangent = (deltaPos1 * deltaUV2.y - deltaPos2 * deltaUV1.y) * r;
   bitangent = (deltaPos2 * deltaUV1.x - deltaPos1 * deltaUV2.x) * r;
   
   // Normalize both vectors
   tangent = normalize(tangent);
   bitangent = normalize(bitangent);
   
   // Fix zero vectors from degenerate UVs ([mdlops:5536-5539, 5563-5566](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L5536-L5566))
   if (length(tangent) < epsilon) {
       tangent = vec3(1.0, 0.0, 0.0);
   }
   if (length(bitangent) < epsilon) {
       bitangent = vec3(1.0, 0.0, 0.0);
   }
   ```

2. **KotOR-Specific Handedness Correction**:

   **Important**: KotOR expects tangent space to NOT form a right-handed coordinate system.
   **Reference**: [`vendor/mdlops/MDLOpsM.pm:5570-5587`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L5570-L5587)

   ```c
   // KotOR wants dot(cross(N,T), B) < 0 (NOT right-handed)
   if (dot(cross(normal, tangent), bitangent) > 0.0f) {
       tangent = -tangent;
   }
   ```

3. **Texture Mirroring Detection and Correction**:

   **Reference**: [`vendor/mdlops/MDLOpsM.pm:5588-5596`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L5588-L5596)

   ```c
   // Detect texture mirroring via UV triangle orientation
   tNz = (uv0.x - uv1.x) * (uv2.y - uv1.y) - (uv0.y - uv1.y) * (uv2.x - uv1.x);
   
   // If texture is mirrored, invert both tangent and bitangent
   if (tNz > 0.0f) {
       tangent = -tangent;
       bitangent = -bitangent;
   }
   ```

4. **Per-Vertex Tangent Space**: Averaged from connected face tangents and bitangents, using the same weighting methods as normals.

---

## Model Classification Flags

The Model Header's Classification byte (offset 0 in Model Header, offset 92 from MDL data start) uses these values to categorize the model type:

| Classification | Value | Description                                                    |
| -------------- | ----- | -------------------------------------------------------------- |
| Other          | 0x00  | Uncategorized or generic model.                                |
| Effect         | 0x01  | Visual effect model (particles, beams, explosions).            |
| Tile           | 0x02  | Tileset/environmental geometry model.                          |
| Character      | 0x04  | Character or creature model (player, NPC, creature).           |
| Door           | 0x08  | Door model with open/close animations.                         |
| Lightsaber     | 0x10  | Lightsaber weapon model with dynamic blade.                    |
| Placeable      | 0x20  | Placeable object model (furniture, containers, switches).      |
| Flyer          | 0x40  | Flying vehicle or creature model.                              |

**Note:** These values are not bitmask flags and should not be combined. Each model has exactly one classification value.

---

## File Identification

### Binary vs ASCII Format

- **Binary Model**: The first 4 bytes are all zeros (`0x00000000`).
- **ASCII Model**: The first 4 bytes contain non-zero values (text header).

### KotOR 1 vs KotOR 2 Models

The game version can be determined by examining Function Pointer 0 in the Geometry Header (offset 12 in file, offset 0 in MDL data):

| Platform/Version    | Geometry Function Ptr | Animation Function Ptr |
| ------------------- | --------------------- | ---------------------- |
| KotOR 1 (PC)        | `4273776` (0x413750)  | `4273392` (0x4135D0)   |
| KotOR 2 (PC)        | `4285200` (0x416610)  | `4284816` (0x416490)   |
| KotOR 1 (Xbox)      | `4254992` (0x40EE90)  | `4254608` (0x40ED10)   |
| KotOR 2 (Xbox)      | `4285872` (0x416950)  | `4285488` (0x4167D0)   |

**Usage:** Parsers should check this value to determine:

- Whether the model is from KotOR 1 or KotOR 2 (affects Trimesh Header size: 332 vs 340 bytes)
- Whether this is a model geometry header (`0x00`) or animation geometry header (`0x01`)

---

## Model Hierarchy

### Node Relationships

- Each node can have a parent node, forming a hierarchy.
- The root node is referenced in the Geometry Header.
- Nodes inherit transformations from their parents.

### Node Transformations

1. **Position Transform**:
   - Stored in controller type `8`.
   - Accumulated through the node hierarchy.
   - Applied as translation after orientation.

2. **Orientation Transform**:
   - Stored in controller type `20`.
   - Uses quaternion multiplication.
   - Applied before position translation.

---

## Smoothing Groups

- **Automatic Smoothing**: Groups are created based on face connectivity and normal angles.
- **Threshold Angles**: Faces with normals within a certain angle are grouped.

---

## ASCII MDL Format

KotOR models can be represented in an ASCII format, which is human-readable.

### Model Header Section

```plaintext
newmodel <model_name>
setsupermodel <model_name> <supermodel_name>
classification <classification_flags>
ignorefog <0_or_1>
setanimationscale <scale_factor>
```

### Geometry Section

```plaintext
beginmodelgeom <model_name>
  bmin <x> <y> <z>
  bmax <x> <y> <z>
  radius <value>
```

### Node Definitions

```plaintext
node <node_type> <node_name>
  parent <parent_name>
  position <x> <y> <z>
  orientation <x> <y> <z> <w>
  scale <value>
  <additional_properties>
endnode
```

### Animation Data

```plaintext
newanim <animation_name> <model_name>
  length <duration>
  transtime <transition_time>
  animroot <root_node>
  event <time> <event_name>
  node <node_type> <node_name>
    parent <parent_name>
    <controllers>
  endnode
doneanim <animation_name> <model_name>
```

---

## Controller Data Formats

### Single Controllers

For constant values that don't change over time:

```plaintext
<controller_name> <value>
```

**Reference**: [`vendor/mdlops/MDLOpsM.pm:3734-3754`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L3734-L3754) - Single controller reading  
**Example**: `position 0.0 1.5 0.0` (static position at X=0, Y=1.5, Z=0)

### Keyed Controllers

For animated values that change over time:

- **Linear Interpolation**:

  ```plaintext
  <controller_name>key
    <time> <value>
    ...
  endlist
  ```

  **Reference**: [`vendor/mdlops/MDLOpsM.pm:3760-3802`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L3760-L3802) - Keyed controller reading  
  **Example**:

  ```plaintext
  positionkey
    0.0 0.0 0.0 0.0
    1.0 0.0 1.0 0.0
    2.0 0.0 0.0 0.0
  endlist
  ```

  Linear interpolation between keyframes.

- **Bezier Interpolation**:

  **Reference**: [`vendor/mdlops/MDLOpsM.pm:1704-1710, 1721-1756`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1704-L1756) - Bezier flag detection and data reading  
  **Format**: Each keyframe stores 3 values per column: (value, in_tangent, out_tangent)

  ```plaintext
  <controller_name>bezierkey
    <time> <value> <in_tangent> <out_tangent>
    ...
  endlist
  ```

  **Example**:

  ```plaintext
  positionbezierkey
    0.0 0.0 0.0 0.0  0.0 0.3 0.0  0.0 0.3 0.0
    1.0 0.0 1.0 0.0  0.0 0.7 0.0  0.0 0.7 0.0
  endlist
  ```
  
  **Binary Storage**: Bezier controllers use bit 4 (value 0x10) in the column count field to indicate bezier interpolation ([mdlops:1704-1710](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1704-L1710)). When this flag is set, the data section contains 3 times as many floats per keyframe ([mdlops:1721-1723](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1721-L1723)).
  
  **Interpolation**: Bezier curves provide smooth, non-linear interpolation between keyframes using control points (tangents) that define the curve shape entering and leaving each keyframe.

### Special Controller Cases

1. **Compressed Quaternion Orientation** (`MDLControllerType.ORIENTATION` with column_count=2):

   **Reference**: [`vendor/mdlops/MDLOpsM.pm:1714-1719`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1714-L1719) - Compressed quaternion detection  
   **Format**: Single 32-bit packed value instead of 4 floats

   ```python
   X: bits 0-10  (11 bits, bitmask 0x7FF, effective range [0, 1023] maps to [-1, 1])
   Y: bits 11-21 (11 bits, bitmask 0x7FF, effective range [0, 1023] maps to [-1, 1])
   Z: bits 22-31 (10 bits, bitmask 0x3FF, effective range [0, 511] maps to [-1, 1])
   W: computed from unit constraint (|q| = 1)
   ```

   Decompression: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:850-868`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L850-L868)
   **Decompression**: Extract bits using bitmasks, divide by effective range (1023 for X/Y, 511 for Z), then subtract 1.0 to map to [-1, 1] range.

2. **Position Delta Encoding** (ASCII only):

   **Reference**: [`vendor/mdlops/MDLOpsM.pm:3788-3793`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L3788-L3793)  
   In ASCII format animations, position controller values are stored as deltas from the geometry node's static position.

   ```python
   animated_position = geometry_position + position_controller_value
   ```

3. **Angle-Axis to Quaternion Conversion** (ASCII only):

   **Reference**: [`vendor/mdlops/MDLOpsM.pm:3718-3728, 3787`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L3718-L3787)  
   ASCII orientation controllers use angle-axis representation `[x, y, z, angle]` which is converted to quaternion `[x, y, z, w]` on import:

   ```c
   sin_a = sin(angle / 2);
   quat.x = axis.x * sin_a;
   quat.y = axis.y * sin_a;
   quat.z = axis.z * sin_a;
   quat.w = cos(angle / 2);
   ```

---

## Skin Meshes and Skeletal Animation

### Bone Mapping and Lookup Tables

Skinned meshes require bone mapping to connect mesh vertices to skeleton bones across model parts.

**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:703-723`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L703-L723) - `prepareSkinMeshes()`

#### Bone Map (`bonemap`)

Maps local bone indices (0-15) to global skeleton bone numbers. Each skinned mesh part can reference different bones from the full character skeleton.

**Example**: Body part might use bones 0-10, while head uses bones 5-15. The bone map translates local indices to the correct skeleton bones.

#### Bone Serial and Node Number Lookups

After loading, bone lookup tables must be prepared for efficient matrix computation:

```python
def prepare_bone_lookups(skin_mesh, all_nodes):
    for local_idx, bone_idx in enumerate(skin_mesh.bonemap):
        # Skip invalid bone slots (0xFFFF)
        if bone_idx == 0xFFFF:
            continue
        
        # Ensure lookup arrays are large enough
        if bone_idx >= len(skin_mesh.bone_serial):
            skin_mesh.bone_serial.extend([0] * (bone_idx + 1 - len(skin_mesh.bone_serial)))
            skin_mesh.bone_node_number.extend([0] * (bone_idx + 1 - len(skin_mesh.bone_node_number)))
        
        # Store serial position and node number
        bone_node = all_nodes[local_idx]
        skin_mesh.bone_serial[bone_idx] = local_idx
        skin_mesh.bone_node_number[bone_idx] = bone_node.node_id
```

### Vertex Skinning

Each vertex can be influenced by up to 4 bones with normalized weights.

**References**:

- [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:261-268`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L261-L268) - Bone weight/index reading
- [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:478-485`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L478-L485) - Skinning data structure

#### Bone Weight Format (MDX)

Per-vertex data stored in MDX file:

- 4 bone indices (as floats, cast to int)
- 4 bone weights (as floats, should sum to 1.0)

**Layout**:

```plaintext
Offset   Type        Description
+0       float[4]    Bone indices (cast to uint16)
+16      float[4]    Bone weights (normalized to sum to 1.0)
```

#### Vertex Transformation

```c
// For each vertex
vec3 skinned_position = vec3(0.0);
vec3 skinned_normal = vec3(0.0);

for (int i = 0; i < 4; i++) {
    if (vertex.bone_weights[i] > 0.0) {
        int bone_idx = vertex.bone_indices[i];
        mat4 bone_matrix = getBoneMatrix(bone_idx);
        
        skinned_position += bone_matrix * vec4(vertex.position, 1.0) * vertex.bone_weights[i];
        skinned_normal += mat3(bone_matrix) * vertex.normal * vertex.bone_weights[i];
    }
}

// Renormalize skinned normal
skinned_normal = normalize(skinned_normal);
```

### Bind Pose Data

**References**:

- [`vendor/mdlops/MDLOpsM.pm:1760-1768`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1760-L1768) - Bind pose arrays
- Skin mesh stores bind pose transforms for each bone

#### QBones (Quaternion Rotations)

Array of quaternions representing each bone's bind pose orientation:

```c
struct QBone {
    float x, y, z, w;  // Quaternion components
};
```

#### TBones (Translation Vectors)

Array of Vector3 representing each bone's bind pose position:

```c
struct TBone {
    float x, y, z;  // Position in model space
};
```

#### Bone Matrix Computation

```c
mat4 computeBoneMatrix(int bone_idx, Animation anim, float time) {
    // Get bind pose
    quat q_bind = skin.qbones[bone_idx];
    vec3 t_bind = skin.tbones[bone_idx];
    mat4 inverse_bind = inverse(translate(t_bind) * mat4_cast(q_bind));
    
    // Get current pose from animation
    quat q_current = evaluateQuaternionController(bone_node, anim, time);
    vec3 t_current = evaluatePositionController(bone_node, anim, time);
    mat4 current = translate(t_current) * mat4_cast(q_current);
    
    // Final bone matrix: inverse bind pose * current pose
    return current * inverse_bind;
}
```

**Note**: KotOR uses left-handed coordinate system, ensure proper matrix conventions.

---

## Additional References

### Editors

- [MDLEdit](https://deadlystream.com/files/file/1150-mdledit/)
- [MDLOps](https://deadlystream.com/files/file/779-mdlops/)
- [Toolbox Aurora](https://deadlystream.com/topic/3714-toolkaurora/)
- [KotorBlender](https://deadlystream.com/files/file/889-kotorblender/)
- [KOTORmax](https://deadlystream.com/files/file/1151-kotormax/)

### See Also

- [KotOR/TSL Model Format MDL/MDX Technical Details](https://deadlystream.com/topic/4501-kotortsl-model-format-mdlmdx-technical-details/)
- [MDL Info (Archived)](https://web.archive.org/web/20151002081059/https://home.comcast.net/~cchargin/kotor/mdl_info.html)
- [xoreos Model Definitions](https://github.com/th3w1zard1/xoreos/blob/master/src/graphics/aurora/model_kotor.h)
- [xoreos Model Implementation](https://github.com/th3w1zard1/xoreos/blob/master/src/graphics/aurora/model_kotor.cpp)

---

This documentation aims to provide a comprehensive and structured overview of the KotOR MDL/MDX file format, focusing on the detailed file structure and data formats used within the games.
