# PyKotorEngine - Panda3D Game Engine for KotOR

A complete game engine implementation using Panda3D for rendering Knights of the Old Republic (KotOR) MDL/MDX models with full support for advanced features.

## Features

### ✅ Implemented

- **MDL/MDX Model Loading**: Full integration with PyKotor's MDL reader
- **Panda3D Geometry Conversion**: Converts MDL meshes to Panda3D GeomNodes
- **Tangent Space Support**: Per-vertex tangent/binormal for normal mapping
  - Implements mdlops algorithm (vendor/mdlops/MDLOpsM.pm:5470-5596)
  - KotOR-specific left-handed coordinate system
  - Texture mirroring detection
- **Skeletal Skinning**: Bone weights and indices for character animation
  - Bone lookup table preparation (vendor/reone:703-723)
  - Up to 4 bone influences per vertex
- **Scene Graph Management**: Hierarchical node structure
  - Follows reone architecture (vendor/reone/src/libs/scene/node/model.cpp)
- **Material System Foundation**: Vertex format with lightmap UV support
- **Example Viewer**: Simple MDL viewer application with camera controls

### 🚧 In Progress / Planned

- **Animation System**: Controller evaluation for skeletal animation
  - Bezier interpolation support
  - Animation blending
- **Advanced Materials**: Shader system for bump mapping, specular, etc.
- **Lighting**: Dynamic lights, shadows, lens flares
- **Particle Effects**: Emitter node rendering
- **Collision**: Walkmesh integration
- **Performance**: LOD system, culling, batching

## Architecture

```
PyKotorEngine/
├── src/pykotorengine/
│   ├── engine.py          # Main engine class (ShowBase wrapper)
│   ├── loaders/           # Resource loaders
│   │   └── mdl_loader.py  # MDL → Panda3D converter
│   ├── scene/             # Scene graph (TODO)
│   ├── animation/         # Controller evaluation (TODO)
│   ├── materials/         # Shader system (TODO)
│   └── rendering/         # Rendering pipeline (TODO)
├── examples/
│   └── simple_viewer.py   # Example MDL viewer
└── tests/                 # Unit tests (TODO)
```

## Installation

### Prerequisites

- Python 3.11+
- Panda3D 1.10.13+
- PyKotor (from `Libraries/PyKotor/`)

### Install Dependencies

```bash
# From PyKotorEngine directory
pip install -r requirements.txt

# Install Panda3D if not already installed
pip install panda3d>=1.10.13

# Ensure PyKotor is installed
cd ../../Libraries/PyKotor
pip install -e .
```

### Install PyKotorEngine

```bash
cd Engines/PyKotorEngine
pip install -e .
```

## Usage

### Simple Viewer Example

```bash
python examples/simple_viewer.py path/to/model.mdl
```

**Controls:**

- Mouse drag: Rotate camera
- Arrow keys: Move camera
- Mouse wheel: Zoom in/out
- ESC: Quit

### Programmatic Usage

```python
from pykotorengine.engine import KotorEngine
from pykotorengine.loaders.mdl_loader import MDLLoader

# Create engine
engine = KotorEngine()

# Load a model
loader = MDLLoader()
model = loader.load("path/to/character.mdl")

# Attach to scene
model.reparentTo(engine.scene_root)

# Run
engine.run_game_loop()
```

## Technical Details

### MDL to Panda3D Conversion

The `MDLLoader` converts PyKotor MDL structures to Panda3D geometry:

1. **Vertex Format Creation**
   - Position, Normal, UV (base)
   - Tangent, Binormal (for normal mapping)
   - Lightmap UV (if present)
   - Bone indices/weights (for skinning)

2. **Tangent Space Calculation**
   - Per-face tangent/binormal from position and UV
   - Averaged per-vertex with proper normalization
   - KotOR-specific handedness correction
   - Texture mirroring support
   - Reference: `Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py:1449-1578`

3. **Geometry Creation**
   - Converts MDL faces to GeomTriangles
   - Handles winding order (KotOR uses clockwise, Panda3D uses CCW)
   - Optimized for static geometry (UHStatic usage hint)

4. **Node Hierarchy**
   - Recursively converts MDL node tree
   - Preserves local transforms (position, orientation)
   - Supports mesh, light, emitter, reference nodes

### Vendor Reference Architecture

This implementation follows patterns from:

**reone (C++)**

- Scene graph: `vendor/reone/src/libs/scene/`
- Model nodes: `vendor/reone/src/libs/scene/node/model.cpp`
- Mesh conversion: `vendor/reone/src/libs/graphics/mesh.cpp`

**KotOR.js (TypeScript/Three.js)**

- Model loading: `vendor/KotOR.js/src/loaders/MDLLoader.ts`
- Scene nodes: `vendor/KotOR.js/src/three/odyssey/`

**mdlops (Perl)**

- Tangent space: `vendor/mdlops/MDLOpsM.pm:5470-5596`
- Controller handling: `vendor/mdlops/MDLOpsM.pm:1649-1778`

### Coordinate System

**KotOR → Panda3D Conversions:**

- Winding order: Reverse (clockwise → counter-clockwise)
- Tangent space: KotOR uses non-right-handed system
- Bone transforms: Applied via bone lookup tables

## Development

### Project Structure

Follows PyKotor conventions:

- `Engines/PyKotorEngine/` - Main engine directory
- `src/pykotorengine/` - Python package namespace
- `examples/` - Example applications
- `tests/` - Unit tests (pytest)

### Running Tests

```bash
pytest tests/
```

### Code Quality

- Type hints throughout (Python 3.11+)
- Vendor references in docstrings
- Follows PyKotor documentation style

## Vendor Integration

### Completed

- ✅ **Tangent Space** (mdlops:5470-5596)
- ✅ **Skin Bone Preparation** (reone:703-723)
- ✅ **Bezier Controller Support** (mdlops:1704-1778)
- ✅ **Scene Graph Architecture** (reone scene/)

### Planned

- ⏳ **Controller Evaluation** (KotOR.js controllers/)
- ⏳ **Walkmesh** (mdlops:8500-9000)
- ⏳ **Lighting System** (reone scene/node/light.cpp)
- ⏳ **Particle System** (reone scene/node/emitter.cpp)

## Performance Considerations

### Optimizations

1. **Fast Loading**: Uses PyKotor's `fast_load` for rendering-only models
2. **Static Geometry**: GeomVertexData uses `UHStatic` hint
3. **Bone Lookup Tables**: Pre-computed for efficient skinning
4. **Tangent Space Caching**: Computed once per vertex

### Future Optimizations

- Instancing for repeated geometry
- LOD system for distant models
- Frustum culling
- Texture atlasing
- Batch rendering

## References

### Panda3D Documentation

- Scene Graph: `/panda3d/panda3d-docs/programming/scene-graph`
- Geometry: `/panda3d/panda3d-docs/programming/internal-structures/procedural-generation`
- Materials: `/panda3d/panda3d-docs/programming/texturing`
- Shaders: `/panda3d/panda3d-docs/programming/shaders`

### PyKotor Integration

- MDL Format: `Libraries/PyKotor/src/pykotor/resource/formats/mdl/`
- MDL Reader: `Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py`
- Tangent Space: `io_mdl.py:1449-1578`
- Skin Preparation: `mdl_data.py:1120-1160, 207-232`

### Vendor Projects

- **reone**: `vendor/reone/src/libs/scene/` - C++ engine reference
- **KotOR.js**: `vendor/KotOR.js/src/` - TypeScript/Three.js implementation
- **mdlops**: `vendor/mdlops/MDLOpsM.pm` - Perl tools and algorithms
- **kotorblender**: `vendor/kotorblender/` - Blender addon reference

## License

GNU General Public License v3.0 - Same as PyKotor project

## Contributing

This engine is part of the PyKotor project. Contributions should:

1. Follow existing code style and documentation patterns
2. Include vendor references in docstrings
3. Add tests for new functionality
4. Update this README with new features

## Roadmap

### Phase 1: Core Rendering ✅

- [x] Engine initialization
- [x] MDL loading and conversion
- [x] Tangent space support
- [x] Skeletal skinning foundation
- [x] Basic scene graph
- [x] Example viewer

### Phase 2: Animation 🚧

- [ ] Controller evaluation system
- [ ] Linear interpolation
- [ ] Bezier interpolation
- [ ] Animation blending
- [ ] Bone matrix computation

### Phase 3: Materials & Lighting

- [ ] Material system
- [ ] Shader pipeline
- [ ] Normal/bump mapping
- [ ] Specular maps
- [ ] Dynamic lights
- [ ] Shadows

### Phase 4: Effects

- [ ] Particle system
- [ ] Emitter nodes
- [ ] Lens flares
- [ ] Environment effects

### Phase 5: Optimization & Polish

- [ ] LOD system
- [ ] Frustum culling
- [ ] Performance profiling
- [ ] Memory optimization

## Acknowledgments

- **Panda3D Team** - Excellent Python game engine
- **PyKotor Contributors** - MDL format implementation
- **reone Team** - C++ engine reference architecture
- **KotOR.js Team** - Three.js implementation reference
- **mdlops** - Format reverse engineering and algorithms
- **BioWare** - Original KotOR games

---

**Status**: Alpha - Core functionality implemented, animation and materials in progress

**Last Updated**: 2025-11-10
