# PyKotorEngine Refactoring Summary

## Problem Statement

The original implementation had these issues:
1. Used `pykotorengine` namespace instead of reusing `pykotor`
2. Duplicated code that should be abstract and reusable
3. Mixed backend-agnostic logic with Panda3D-specific code
4. Could not be shared with GL/Qt5 implementations

## Solution: Proper Abstraction and Namespace

### New Directory Structure

```
Libraries/PyKotor/src/pykotor/
├── resource/formats/mdl/         # MDL data structures (already exists)
└── engine/                        # NEW: Abstract engine interfaces
    ├── __init__.py
    ├── scene/
    │   ├── __init__.py
    │   └── base.py               # ISceneGraph abstract interface
    └── animation/
        ├── __init__.py
        └── base.py               # IAnimationController, IAnimationState, IAnimationManager

Engines/PyKotorEngine/src/
└── pykotor/                      # NO __init__.py - reuses pykotor namespace
    └── engine/
        └── panda3d/              # Panda3D-specific implementations
            ├── __init__.py
            ├── engine.py         # KotorEngine (Panda3D ShowBase)
            ├── scene_graph.py    # Panda3DSceneGraph(ISceneGraph)
            ├── animation.py      # Panda3D animation implementations
            ├── mdl_loader.py     # MDL to Panda3D Geom converter
            └── materials/
                ├── __init__.py
                ├── manager.py    # Material management
                ├── shader.vert
                └── shader.frag
```

### Key Architectural Changes

#### 1. Abstract Interfaces in Libraries/PyKotor

**Purpose**: Define backend-agnostic contracts that can be implemented by GL, Qt5, or Panda3D.

##### Scene Graph Interface (`pykotor.engine.scene.base.ISceneGraph`)
```python
class ISceneGraph(ABC):
    """Abstract scene graph interface.
    
    Can be implemented by:
    - Panda3D (NodePath system)
    - OpenGL (custom scene graph)
    - Qt5 (QGraphicsScene)
    """
    @abstractmethod
    def clear(self) -> None: ...
    
    @abstractmethod
    def update(self, dt: float) -> None: ...
    
    @abstractmethod
    def add_model_root(self, model: Any) -> None: ...
    
    @abstractmethod
    def set_ambient_light_color(self, color: tuple[float, float, float]) -> None: ...
    
    # ... more abstract methods
```

##### Animation Interfaces (`pykotor.engine.animation.base`)
```python
class IAnimationController(ABC):
    """Abstract controller interface."""
    @abstractmethod
    def get_value_at_time(self, time: float) -> Any: ...
    
    @abstractmethod
    def apply(self, node: Any, value: Any) -> None: ...

class IAnimationState(ABC):
    """Abstract animation state interface."""
    @abstractmethod
    def update(self, dt: float) -> bool: ...
    
    @abstractmethod
    def play(self) -> None: ...

class IAnimationManager(ABC):
    """Abstract animation manager interface."""
    @abstractmethod
    def play_animation(self, name: str, loop: bool, speed: float) -> bool: ...
    
    @abstractmethod
    def update(self, dt: float) -> None: ...
```

#### 2. Panda3D Implementations in Engine

**Purpose**: Implement the abstract interfaces using Panda3D-specific code.

##### Scene Graph (`pykotor.engine.panda3d.scene_graph.Panda3DSceneGraph`)
```python
from pykotor.engine.scene.base import ISceneGraph
from panda3d.core import NodePath, AmbientLight, DirectionalLight

class Panda3DSceneGraph(ISceneGraph):
    """Panda3D implementation using NodePath system."""
    
    def __init__(self, name: str, root: NodePath):
        super().__init__(name)
        self.root = root  # Panda3D-specific
        self._model_roots: list[NodePath] = []  # Panda3D-specific
    
    def add_model_root(self, model_np: NodePath) -> None:
        # Panda3D-specific implementation
        model_np.reparentTo(self.root)
        self._model_roots.append(model_np)
```

##### Animation System (`pykotor.engine.panda3d.animation`)
```python
from pykotor.engine.animation.base import (
    IAnimationController,
    IAnimationState,
    IAnimationManager
)
from panda3d.core import NodePath, Vec3, Quat

class Panda3DPositionController(IAnimationController):
    """Panda3D implementation using Vec3."""
    
    def apply(self, node: NodePath, value: Vec3) -> None:
        node.setPos(value)  # Panda3D-specific

class Panda3DAnimationState(IAnimationState):
    """Panda3D implementation of animation state."""
    # ... implementation

class Panda3DAnimationManager(IAnimationManager):
    """Panda3D implementation coordinating animations."""
    # ... implementation
```

#### 3. Import Pattern Changes

**Old (Wrong)**:
```python
from pykotorengine.scene.scene_graph import SceneGraph  # Wrong namespace
```

**New (Correct)**:
```python
from pykotor.engine.scene.base import ISceneGraph  # Abstract interface
from pykotor.engine.panda3d.scene_graph import Panda3DSceneGraph  # Panda3D impl
```

#### 4. Reusability Across Backends

Now the same abstract interfaces can be implemented for different backends:

```python
# Panda3D backend
from pykotor.engine.panda3d import KotorEngine, Panda3DSceneGraph

# OpenGL backend (future)
from pykotor.engine.opengl import GLSceneGraph  # Would implement ISceneGraph

# Qt5 backend (future)
from pykotor.engine.qt5 import Qt5SceneGraph  # Would implement ISceneGraph
```

### Benefits of This Architecture

1. **Code Reuse**: Abstract interfaces in `Libraries/PyKotor` can be used by:
   - PyKotorEngine (Panda3D)
   - PyKotorGL (OpenGL)
   - HolocronToolset (Qt5)
   - Any future backend

2. **Clean Separation**: 
   - Abstract logic in `Libraries/`
   - Backend-specific in `Engines/`

3. **Namespace Consistency**:
   - Everything under `pykotor.*` namespace
   - No duplicate `pykotorengine` namespace
   - Engine code at `pykotor.engine.panda3d.*`

4. **Testability**:
   - Can mock abstract interfaces for testing
   - Can test abstract logic without backend
   - Can test each backend implementation independently

5. **Maintainability**:
   - Changes to abstract interface affect all backends equally
   - Backend-specific optimizations stay isolated
   - Clear contracts via abstract base classes

### Migration Checklist

- [x] Create abstract interfaces in `Libraries/PyKotor/src/pykotor/engine/`
  - [x] `scene/base.py` - ISceneGraph, FogProperties
  - [x] `animation/base.py` - IAnimationController, IAnimationState, IAnimationManager
  
- [ ] Create Panda3D implementations in `Engines/PyKotorEngine/src/pykotor/engine/panda3d/`
  - [x] `scene_graph.py` - Panda3DSceneGraph(ISceneGraph)
  - [ ] `animation.py` - Panda3D animation controllers
  - [ ] `engine.py` - KotorEngine (ShowBase)
  - [ ] `mdl_loader.py` - MDL to Panda3D Geom converter
  - [ ] `materials/` - Material system

- [ ] Update all imports to use new namespace
  - [ ] Examples
  - [ ] Tests
  - [ ] Documentation

- [ ] Remove old `pykotorengine` directory completely

- [ ] Ensure no `__init__.py` in `Engines/PyKotorEngine/src/pykotor/` to reuse namespace

### Usage Example After Refactoring

```python
# Import abstract interface for type hints
from pykotor.engine.scene.base import ISceneGraph

# Import Panda3D-specific implementations
from pykotor.engine.panda3d import (
    KotorEngine,
    Panda3DSceneGraph,
    MDLLoader
)

# Create engine
engine = KotorEngine()

# Create scene graph (implements ISceneGraph)
scene: ISceneGraph = Panda3DSceneGraph("test_scene", engine.scene_root)

# Load model
loader = MDLLoader()
model = loader.load("model.mdl", "model.mdx")
scene.add_model_root(model)

# Run
engine.run()
```

### Next Steps

1. **Complete Panda3D Implementations**: Finish writing all Panda3D-specific classes
2. **Update Examples**: Refactor `simple_viewer.py` to use new namespace
3. **Update Tests**: Refactor tests to use new namespace and test abstract interfaces
4. **Update Documentation**: Update all docs to reflect new architecture
5. **Consider Future Backends**: Document how to implement new backends (GL, Qt5, etc.)

## Vendor Reference Preservation

All vendor references from the original implementation are preserved in:
- Abstract interfaces (architecture patterns)
- Panda3D implementations (specific techniques)
- No loss of documentation or citations

## Conclusion

This refactoring transforms PyKotorEngine from a monolithic Panda3D-specific implementation into a properly abstracted system following the project's architectural patterns:
- Abstract interfaces in `Libraries/PyKotor`
- Backend implementations in `Engines/`
- Proper namespace reuse (`pykotor.*`)
- Clean separation of concerns
- Reusable across GL/Qt5/Panda3D backends

The refactoring respects the user's requirement: "panda3d-specific code ONLY in pykotor.engine, everything else should be Libraries/PyKotor."

