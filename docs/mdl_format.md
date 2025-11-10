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

```
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

The Model Header is 168 bytes in size (including the Geometry Header) and contains information specific to the model.

| Name                         | Type            | Offset | Description                               |
| ---------------------------- | --------------- | ------ | ----------------------------------------- |
| Geometry Header              | GeometryHeader  | 0      | Embedded Geometry Header (80 bytes).      |
| Model Type                   | UInt8           | 80     | Type of the model.                        |
| Unknown                      | UInt8           | 81     | Purpose unknown.                          |
| Padding                      | UInt8           | 82     | Padding byte.                             |
| Disable Fog                  | UInt8           | 83     | `0`: Fog enabled, `1`: Fog disabled.      |
| Child Model Count            | UInt32          | 84     | Number of child models.                   |
| Animation Array Offset       | UInt32          | 88     | Offset to the animation array.            |
| Animation Count              | UInt32          | 92     | Number of animations.                     |
| Animation Count (duplicate)  | UInt32          | 96     | Duplicate value of animation count.       |
| Unknown                      | UInt32          | 100    | Purpose unknown.                          |
| Bounding Box Min             | Float[3]        | 104    | Minimum coordinates of the bounding box.  |
| Bounding Box Max             | Float[3]        | 116    | Maximum coordinates of the bounding box.  |
| Radius                       | Float           | 128    | Radius of the model's bounding sphere.    |
| Animation Scale              | Float           | 132    | Scale factor for animations.              |
| Supermodel Name              | Byte[32]        | 136    | Name of the supermodel (if any).          |

### Geometry Header

The Geometry Header is 80 bytes in size and includes general information about the model's geometry.

| Name             | Type        | Offset | Description                                                                                     |
| ---------------- | ----------- | ------ | ----------------------------------------------------------------------------------------------- |
| Function Pointer | UInt32      | 0      | Pointer value used by the game engine (differs between KotOR 1 and KotOR 2).                    |
| Function Pointer | UInt32      | 4      | Another pointer value used by the game engine.                                                  |
| Model Name       | Byte[32]    | 8      | Name of the model.                                                                              |
| Root Node Offset | UInt32      | 40     | Offset to the root node.                                                                        |
| Node Count       | UInt32      | 44     | Total number of nodes in the model.                                                             |
| Unknown          | UInt32[7]   | 48     | Purpose unknown.                                                                                |
| Geometry Type    | Byte        | 76     | Type of geometry. `0x02`: Root Node, `0x05`: Animation Node.                                    |
| Padding          | Byte[3]     | 77     | Padding bytes to align the structure.                                                           |

### Names Header

The Names Header contains offsets and counts related to the names used in the model.

| Name                | Type    | Description                                 |
| ------------------- | ------- | ------------------------------------------- |
| Offset to Root Node | UInt32  | Offset to the root node.                    |
| Unused              | UInt32  | Unused field.                               |
| MDX File Size       | UInt32  | Size of the corresponding MDX file.         |
| MDX Offset          | UInt32  | Offset to MDX data.                         |
| Names Array Offset  | UInt32  | Offset to the array of names.               |
| Names Count         | UInt32  | Number of names in the array.               |
| Names Count         | UInt32  | Duplicate value of names count.             |

### Animation Header

The Animation Header contains information about animations within the model.

| Name                  | Type            | Description                          |
| --------------------- | --------------- | ------------------------------------ |
| Geometry Header       | GeometryHeader  | Embedded Geometry Header.            |
| Animation Length      | Float           | Duration of the animation.           |
| Transition Time       | Float           | Transition time to this animation.   |
| Animation Root        | Byte[32]        | Root node of the animation.          |
| Event Offset          | UInt32          | Offset to animation events.          |
| Event Count           | UInt32          | Number of animation events.          |
| Event Count (dup)     | UInt32          | Duplicate value of event count.      |
| Unknown               | UInt32          | Purpose unknown.                     |

### Event Structure

Each animation event has the following structure:

| Name            | Type   | Description                          |
| --------------- | ------ | ------------------------------------ |
| Activation Time | Float  | Time at which the event is activated |
| Event Name      | String | Name of the event                    |

---

## Node Structures

### Node Header

The Node Header is 80 bytes in size and is common to all node types.

| Name                     | Type        | Offset | Description                                                                        |
| ------------------------ | ----------- | ------ | ---------------------------------------------------------------------------------- |
| Node Type                | UInt16      | 0      | Bitmask indicating the type of node (see [Node Type Bitmasks](#node-type-bitmasks)) |
| Index Number             | UInt16      | 2      | Index of the node.                                                                 |
| Node Number              | UInt16      | 4      | Node number identifier.                                                            |
| Padding                  | UInt16      | 6      | Padding bytes.                                                                     |
| Root Node Offset         | UInt32      | 8      | Offset to the root node.                                                           |
| Parent Node Offset       | UInt32      | 12     | Offset to the parent node.                                                         |
| Position                 | Float[3]    | 16     | Position of the node in 3D space.                                                  |
| Rotation                 | Float[4]    | 28     | Rotation quaternion (x, y, z, w).                                                  |
| Child Array Offset       | UInt32      | 44     | Offset to the array of child nodes.                                                |
| Child Count              | UInt32      | 48     | Number of child nodes.                                                             |
| Child Count (duplicate)  | UInt32      | 52     | Duplicate value of child count.                                                    |
| Controller Array Offset  | UInt32      | 56     | Offset to the array of controllers.                                                |
| Controller Count         | UInt32      | 60     | Number of controllers.                                                             |
| Controller Count (dup)   | UInt32      | 64     | Duplicate value of controller count.                                               |
| Controller Data Offset   | UInt32      | 68     | Offset to controller data.                                                         |
| Controller Data Count    | UInt32      | 72     | Number of controller data entries.                                                 |
| Controller Data Count    | UInt32      | 76     | Duplicate value of controller data count.                                          |

### Trimesh Header

The Trimesh Header defines static meshes and is 332 bytes in KotOR 1 models and 340 bytes in KotOR 2 models.

| Name                         | Type         | Offset   | Description                                                                                 |
| ---------------------------- | ------------ | -------- | ------------------------------------------------------------------------------------------- |
| Function Pointer             | UInt32       | 0        | Pointer used by the game engine (differs between KotOR 1 and KotOR 2).                      |
| Function Pointer             | UInt32       | 4        | Another pointer used by the game engine.                                                    |
| Faces Offset                 | UInt32       | 8        | Offset to the faces array.                                                                  |
| Faces Count                  | UInt32       | 12       | Number of faces.                                                                            |
| Faces Count (duplicate)      | UInt32       | 16       | Duplicate value of faces count.                                                             |
| Bounding Box Min             | Float[3]     | 20       | Minimum coordinates of the bounding box.                                                    |
| Bounding Box Max             | Float[3]     | 32       | Maximum coordinates of the bounding box.                                                    |
| Radius                       | Float        | 44       | Radius of the mesh's bounding sphere.                                                       |
| Average Point                | Float[3]     | 48       | Average position of the vertices.                                                           |
| Diffuse Color                | Float[3]     | 60       | RGB diffuse color values (range 0.0 - 1.0).                                                 |
| Ambient Color                | Float[3]     | 72       | RGB ambient color values (range 0.0 - 1.0).                                                 |
| Transparency Hint            | UInt32       | 84       | Transparency mode hint.                                                                     |
| Texture Name                 | Byte[32]     | 88       | Name of the primary texture.                                                                |
| Lightmap Name                | Byte[32]     | 120      | Name of the lightmap texture.                                                               |
| Unknown                      | Byte[24]     | 152      | Purpose unknown.                                                                            |
| Vertex Indices Count Offset  | UInt32       | 176      | Offset to the array of vertex indices counts.                                               |
| Vertex Indices Count         | UInt32       | 180      | Number of vertex indices counts.                                                            |
| Vertex Indices Count (dup)   | UInt32       | 184      | Duplicate value of vertex indices counts.                                                   |
| Vertex Offsets Array Offset  | UInt32       | 188      | Offset to the array of vertex offsets.                                                      |
| Vertex Offsets Count         | UInt32       | 192      | Number of vertex offsets.                                                                   |
| Vertex Offsets Count (dup)   | UInt32       | 196      | Duplicate value of vertex offsets.                                                          |
| Inverted Counters Offset     | UInt32       | 200      | Offset to the array of inverted counters.                                                   |
| Inverted Counters Count      | UInt32       | 204      | Number of inverted counters.                                                                |
| Inverted Counters Count      | UInt32       | 208      | Duplicate value of inverted counters count.                                                 |
| Unknown                      | UInt32[3]    | 212      | Always `{ -1, -1, 0 }`.                                                                     |
| Saber Values                 | Byte[8]      | 224      | Specific values used for lightsaber meshes.                                                 |
| Unknown                      | UInt32       | 232      | Purpose unknown.                                                                            |
| UV Animation Parameters      | Float[4]     | 236      | Possibly UV animation parameters (direction, jitter, speed).                                |
| MDX Data Size                | UInt32       | 252      | Size of the per-vertex data in the MDX file.                                                |
| MDX Data Bitmap              | UInt32       | 256      | Bitmask indicating data present in the MDX file (see [MDX Data Bitmap Masks](#mdx-data-bitmap-masks)). |
| MDX Vertices Offset          | UInt32       | 260      | Offset to vertex positions in the MDX file.                                                 |
| MDX Normals Offset           | UInt32       | 264      | Offset to vertex normals in the MDX file.                                                   |
| MDX Vertex Colors Offset     | UInt32       | 268      | Offset to vertex colors in the MDX file.                                                    |
| MDX Texture 1 UVs Offset     | UInt32       | 272      | Offset to primary texture UVs in the MDX file.                                              |
| MDX Lightmap UVs Offset      | UInt32       | 276      | Offset to lightmap UVs in the MDX file.                                                     |
| MDX Texture 2 UVs Offset     | UInt32       | 280      | Offset to secondary texture UVs in the MDX file.                                            |
| MDX Texture 3 UVs Offset     | UInt32       | 284      | Offset to tertiary texture UVs in the MDX file.                                             |
| MDX Unknown Offset           | UInt32[4]    | 288      | Offsets to additional MDX data (possibly bump maps or other data).                          |
| Vertex Count                 | UInt16       | 304      | Number of vertices.                                                                         |
| Texture Count                | UInt16       | 306      | Number of textures used.                                                                    |
| Has Lightmap                 | Byte         | 308      | Indicates if the mesh uses a lightmap (`0`: No, `1`: Yes).                                  |
| Rotate Texture               | Byte         | 309      | Indicates if the texture is rotated.                                                        |
| Background Geometry          | Byte         | 310      | Indicates if the mesh is background geometry.                                               |
| Has Shadow                   | Byte         | 311      | Indicates if the mesh casts shadows.                                                        |
| Beaming                      | Byte         | 312      | Beaming effect flag.                                                                        |
| Has Render                   | Byte         | 313      | Indicates if the mesh is renderable.                                                        |
| Unknown                      | Byte         | 314      | Possibly a flag for UV animation.                                                           |
| Unknown                      | Byte         | 315      | Purpose unknown.                                                                            |
| Total Area                   | Float        | 316      | Total surface area of the mesh.                                                             |
| Unknown                      | UInt32       | 320      | Purpose unknown.                                                                            |
| **Unknown**                  | **UInt32**   | 324/324 | **Only present in KotOR 2 models.**                                                        |
| **Unknown**                  | **UInt32**   | 328/328 | **Only present in KotOR 2 models.**                                                        |
| MDX Data Offset              | UInt32       | 324/332 | Offset to the MDX data.                                                                     |
| Vertices Offset              | UInt32       | 328/336 | Offset to the vertices in the MDL file.                                                     |

### Danglymesh Header

The Danglymesh Header defines mesh nodes that have physics-based motion (dangling parts). It is 28 bytes in size.

| Name                   | Type    | Offset | Description                           |
| ---------------------- | ------- | ------ | ------------------------------------- |
| Constraints Offset     | UInt32  | 0      | Offset to the constraints array.      |
| Constraints Count      | UInt32  | 4      | Number of constraints.                |
| Constraints Count      | UInt32  | 8      | Duplicate value of constraints count. |
| Displacement           | Float   | 12     | Maximum displacement of vertices.     |
| Tightness              | Float   | 16     | Tightness of the spring effect.       |
| Period                 | Float   | 20     | Period of the oscillation.            |
| Unknown                | UInt32  | 24     | Purpose unknown.                      |

### Skinmesh Header

The Skinmesh Header defines skinned meshes that are influenced by bones (used in character models). It is 108 bytes in size.

| Name                                       | Type       | Offset | Description                                             |
| ------------------------------------------ | ---------- | ------ | ------------------------------------------------------- |
| Compile Weight Array                       | Int[3]     | 0      | Compilation weights (purpose uncertain).                |
| MDX Skin Weights Offset                    | UInt32     | 12     | Offset to skin weights in MDX file.                     |
| MDX Skin Bone Reference Indices Offset     | UInt32     | 16     | Offset to bone indices in MDX file.                     |
| Bones Map Offset                           | UInt32     | 20     | Offset to the bones map array.                          |
| Bones Map Count                            | UInt32     | 24     | Number of entries in the bones map.                     |
| QBones                                     | UInt32[3]  | 28     | Quaternion bone data (purpose uncertain).               |
| TBones                                     | UInt32[3]  | 40     | Translation bone data (purpose uncertain).              |
| Unknown                                    | UInt32[3]  | 52     | Purpose unknown.                                        |
| Unknown Array                              | UInt16[17] | 64     | Purpose unknown.                                        |
| Padding                                    | UInt16     | 98     | Padding bytes.                                          |

### Lightsaber Header

The Lightsaber Header is specific to lightsaber meshes and is 20 bytes in size.

| Name                   | Type    | Offset | Description                           |
| ---------------------- | ------- | ------ | ------------------------------------- |
| Vertices Offset        | UInt32  | 0      | Offset to the vertices array.         |
| TexCoords Offset       | UInt32  | 4      | Offset to texture coordinates.        |
| Normals Offset         | UInt32  | 8      | Offset to the normals array.          |
| Unknown                | UInt32  | 12     | Purpose unknown.                      |
| Unknown                | UInt32  | 16     | Purpose unknown.                      |

### Light Header

The Light Header defines properties for light nodes.

| Name                        | Type    | Offset | Description                                 |
| --------------------------- | ------- | ------ | ------------------------------------------- |
| Unknown Array               | UInt32  | 0      | Purpose unknown.                            |
| Unknown Array Count         | UInt32  | 4      | Number of entries in the unknown array.     |
| Unknown Array Count (dup)   | UInt32  | 8      | Duplicate value.                            |
| Lens Flare Sizes Offset     | UInt32  | 12     | Offset to lens flare sizes array.           |
| Lens Flare Sizes Count      | UInt32  | 16     | Number of lens flare sizes.                 |
| Lens Flare Sizes Count      | UInt32  | 20     | Duplicate value.                            |
| Flare Positions Offset      | UInt32  | 24     | Offset to flare positions array.            |
| Flare Positions Count       | UInt32  | 28     | Number of flare positions.                  |
| Flare Positions Count       | UInt32  | 32     | Duplicate value.                            |
| Flare Color Shifts Offset   | UInt32  | 36     | Offset to flare color shifts array.         |
| Flare Color Shifts Count    | UInt32  | 40     | Number of flare color shifts.               |
| Flare Color Shifts Count    | UInt32  | 44     | Duplicate value.                            |
| Flare Texture Names Offset  | UInt32  | 48     | Offset to flare texture names array.        |
| Flare Texture Names Count   | UInt32  | 52     | Number of flare texture names.              |
| Flare Texture Names Count   | UInt32  | 56     | Duplicate value.                            |
| Flare Radius                | Float   | 60     | Radius of the flare effect.                 |
| Light Priority              | UInt32  | 64     | Rendering priority of the light.            |
| Ambient Only                | UInt32  | 68     | Light affects ambient only (`0` or `1`).    |
| Dynamic Type                | UInt32  | 72     | Type of dynamic lighting.                   |
| Affect Dynamic              | UInt32  | 76     | Light affects dynamic objects (`0` or `1`). |
| Shadow                      | UInt32  | 80     | Light casts shadows (`0` or `1`).           |
| Flare                       | UInt32  | 84     | Flare effect enabled (`0` or `1`).          |
| Fading Light                | UInt32  | 88     | Light fades over distance (`0` or `1`).     |

### Emitter Header

The Emitter Header defines particle emitters and their properties.

| Name                     | Type         | Offset | Description                          |
| ------------------------ | ------------ | ------ | ------------------------------------ |
| Dead Space               | Float        |        | Distance before particles spawn.     |
| Blast Radius             | Float        |        | Radius of any explosive effects.     |
| Blast Length             | Float        |        | Length of blast effects.             |
| Branch Count             | UInt32       |        | Number of particle branches.         |
| Control Point Smoothing  | Float        |        | Smoothness of control points.        |
| X Grid                   | UInt32       |        | Grid size along X-axis.              |
| Y Grid                   | UInt32       |        | Grid size along Y-axis.              |
| Update                   | Byte[32]     |        | Update behavior scripts.             |
| Render                   | Byte[32]     |        | Render behavior scripts.             |
| Blend                    | Byte[32]     |        | Blending mode scripts.               |
| Texture                  | Byte[32]     |        | Texture name for particles.          |
| Chunk Name               | Byte[16]     |        | Associated chunk name.               |
| Two-Sided Texture        | UInt32       |        | Texture is two-sided (`0` or `1`).   |
| Loop                     | UInt32       |        | Particle system loops (`0` or `1`).  |
| Render Order             | UInt32       |        | Rendering order of particles.        |
| Frame Blending           | UInt32       |        | Frame blending enabled (`0` or `1`). |
| Depth Texture Name       | Byte[32]     |        | Depth texture name.                  |
| Padding                  | Byte         |        | Padding byte for alignment.          |
| Flags                    | UInt32       |        | Bitmask of emitter flags.            |

### Reference Header

The Reference Header allows models to reference other models.

| Name          | Type     | Offset | Description                                 |
| ------------- | -------- | ------ | ------------------------------------------- |
| Model ResRef  | Byte[32] |        | Resource reference to another model.        |
| Reattachable  | UInt32   |        | Indicates if reattachable (`0` or `1`).     |

---

## Controllers

### Controller Structure

Each controller is 16 bytes in size and defines how certain properties of a node change over time.

| Name             | Type     | Description                                                                                       |
| ---------------- | -------- | ------------------------------------------------------------------------------------------------- |
| Type             | UInt32   | Controller type identifier (see specific controller types).                                       |
| Unknown          | UInt16   | Always `0xFFFF`.                                                                                  |
| Data Row Count   | UInt16   | Number of data rows (keyframes).                                                                  |
| First Key Offset | UInt16   | Offset to the first keyframe.                                                                     |
| First Data Offset| UInt16   | Offset to the first data value.                                                                   |
| Column Count     | Byte     | Number of data columns per row.                                                                   |
| Unknown          | Byte[3]  | Padding bytes for alignment.                                                                      |

Data rows contain the time keys and corresponding values for each controller.

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

The `MDX Data Bitmap` field in the Trimesh Header uses bitmask flags to indicate which types of data are present for each vertex:

```c
#define MDX_VERTICES        0x00000001  // Vertex positions
#define MDX_TEX0_VERTICES   0x00000002  // Primary texture coordinates
#define MDX_TEX1_VERTICES   0x00000004  // Secondary texture coordinates
#define MDX_TEX2_VERTICES   0x00000008  // Tertiary texture coordinates
#define MDX_TEX3_VERTICES   0x00000010  // Quaternary texture coordinates
#define MDX_VERTEX_NORMALS  0x00000020  // Vertex normals
#define MDX_VERTEX_COLORS   0x00000040  // Vertex colors
#define MDX_TANGENT_SPACE   0x00000080  // Tangent space data
// Skin Mesh Specific Data
#define MDX_BONE_WEIGHTS    0x00000800  // Bone weights for skinning
#define MDX_BONE_INDICES    0x00001000  // Bone indices for skinning
```

### Skin Mesh Specific Data

For skin meshes, additional MDX data is used to define bone weights and indices:

- **Bone Weights Offset**: Offset to the bone weights data (4 floats per vertex).
- **Bone Indices Offset**: Offset to the bone indices data (4 floats per vertex).

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
   **Reference**: `vendor/mdlops/MDLOpsM.pm:465-488` - Heron's formula implementation

2. **Angle Weighting**: Faces contribute based on the angle at the vertex.

   ```c
   angle = arccos(dot(normalize(v1 - v0), normalize(v2 - v0)))
   weighted_normal = face_normal * angle
   ```

3. **Crease Angle Limiting**: Faces are excluded if the angle between their normals exceeds a threshold (e.g., 60 degrees).

### Tangent Space Calculation

For normal/bump mapping, tangent and bitangent vectors are calculated per face. KotOR uses a specific tangent space convention that differs from standard implementations.

**Reference**: `vendor/mdlops/MDLOpsM.pm:5470-5596` - Complete tangent space calculation  
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
       r = 2406.6388; // Magic factor from p_g0t01.mdl analysis (mdlops:5510-5512)
   }
   
   tangent = (deltaPos1 * deltaUV2.y - deltaPos2 * deltaUV1.y) * r;
   bitangent = (deltaPos2 * deltaUV1.x - deltaPos1 * deltaUV2.x) * r;
   
   // Normalize both vectors
   tangent = normalize(tangent);
   bitangent = normalize(bitangent);
   
   // Fix zero vectors from degenerate UVs (mdlops:5536-5539, 5563-5566)
   if (length(tangent) < epsilon) {
       tangent = vec3(1.0, 0.0, 0.0);
   }
   if (length(bitangent) < epsilon) {
       bitangent = vec3(1.0, 0.0, 0.0);
   }
   ```

2. **KotOR-Specific Handedness Correction**:

   **Important**: KotOR expects tangent space to NOT form a right-handed coordinate system.  
   **Reference**: `vendor/mdlops/MDLOpsM.pm:5570-5587`

   ```c
   // KotOR wants dot(cross(N,T), B) < 0 (NOT right-handed)
   if (dot(cross(normal, tangent), bitangent) > 0.0f) {
       tangent = -tangent;
   }
   ```

3. **Texture Mirroring Detection and Correction**:

   **Reference**: `vendor/mdlops/MDLOpsM.pm:5588-5596`

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

Models can be classified using specific flags:

| Flag          | Value |
| ------------- | ----- |
| Effect        | 0x01  |
| Tile          | 0x02  |
| Character     | 0x04  |
| Door          | 0x08  |
| Lightsaber    | 0x10  |
| Placeable     | 0x20  |
| Flyer         | 0x40  |
| Other         | 0x00  |

---

## File Identification

### Binary vs ASCII Format

- **Binary Model**: The first 4 bytes are all zeros (`0x00000000`).
- **ASCII Model**: The first 4 bytes contain non-zero values (text header).

### KotOR 1 vs KotOR 2 Models

The game version can be determined by specific values in the Geometry Header:

- **KotOR 1**:
  - Function Pointer at offset 0: `4273776` (regular), `4273392` (animation).
- **KotOR 2**:
  - Function Pointer at offset 0: `4285200` (regular), `4284816` (animation).

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

**Reference**: `vendor/mdlops/MDLOpsM.pm:3734-3754` - Single controller reading  
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

  **Reference**: `vendor/mdlops/MDLOpsM.pm:3760-3802` - Keyed controller reading  
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

  **Reference**: `vendor/mdlops/MDLOpsM.pm:1704-1710, 1721-1756` - Bezier flag detection and data reading  
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
  
  **Binary Storage**: Bezier controllers use bit 4 (value 0x10) in the column count field to indicate bezier interpolation (mdlops:1704-1710). When this flag is set, the data section contains 3 times as many floats per keyframe (mdlops:1721-1723).
  
  **Interpolation**: Bezier curves provide smooth, non-linear interpolation between keyframes using control points (tangents) that define the curve shape entering and leaving each keyframe.

### Special Controller Cases

1. **Compressed Quaternion Orientation** (`MDLControllerType.ORIENTATION` with column_count=2):
   
   **Reference**: `vendor/mdlops/MDLOpsM.pm:1714-1719` - Compressed quaternion detection  
   **Format**: Single 32-bit packed value instead of 4 floats
   
   ```
   X: bits 0-10  (11 bits, range [0, 2047] maps to [-1, 1])
   Y: bits 11-21 (11 bits, range [0, 2047] maps to [-1, 1])
   Z: bits 22-31 (10 bits, range [0, 1023] maps to [-1, 1])
   W: computed from unit constraint (|q| = 1)
   ```
   
   Decompression: `vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:850-868`

2. **Position Delta Encoding** (ASCII only):
   
   **Reference**: `vendor/mdlops/MDLOpsM.pm:3788-3793`  
   In ASCII format animations, position controller values are stored as deltas from the geometry node's static position.
   
   ```
   animated_position = geometry_position + position_controller_value
   ```

3. **Angle-Axis to Quaternion Conversion** (ASCII only):
   
   **Reference**: `vendor/mdlops/MDLOpsM.pm:3718-3728, 3787`  
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

**Reference**: `vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:703-723` - `prepareSkinMeshes()`

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
- `vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:261-268` - Bone weight/index reading
- `vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:478-485` - Skinning data structure

#### Bone Weight Format (MDX)

Per-vertex data stored in MDX file:
- 4 bone indices (as floats, cast to int)
- 4 bone weights (as floats, should sum to 1.0)

**Layout**:
```
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
- `vendor/mdlops/MDLOpsM.pm:1760-1768` - Bind pose arrays
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
- [xoreos Model Definitions](https://github.com/xoreos/xoreos/blob/master/src/graphics/aurora/model_kotor.h)
- [xoreos Model Implementation](https://github.com/xoreos/xoreos/blob/master/src/graphics/aurora/model_kotor.cpp)

---

This documentation aims to provide a comprehensive and structured overview of the KotOR MDL/MDX file format, focusing on the detailed file structure and data formats used within the games.
