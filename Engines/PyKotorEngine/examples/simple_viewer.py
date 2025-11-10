"""Simple KotOR MDL viewer using PyKotorEngine.

This example demonstrates basic usage of the PyKotorEngine to load and display
a KotOR MDL/MDX model in a Panda3D window.

Usage:
    python simple_viewer.py path/to/model.mdl [path/to/model.mdx]

References:
----------
    vendor/reone/src/apps/kotor/main.cpp - Application entry point
    /panda3d/panda3d-docs - ShowBase application
"""

import sys
from pathlib import Path

# Ensure PyKotor engine and libraries are on path
root = Path(__file__).parent.parent
engine_src = root / "src"
libraries_src = root.parents[2] / "Libraries" / "PyKotor" / "src"
for path in (engine_src, libraries_src):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from pykotor.engine.panda3d import KotorEngine, MDLLoader


class SimpleModelViewer(KotorEngine):
    """Simple MDL model viewer application.
    
    Extends KotorEngine with model loading and camera controls.
    
    References:
    ----------
        vendor/reone/src/apps/kotor/game.cpp - Game application
    """
    
    def __init__(self, mdl_path: str, mdx_path: str | None = None):
        """Initialize viewer and load model.
        
        Args:
        ----
            mdl_path: Path to MDL file
            mdx_path: Path to MDX file (optional)
        """
        super().__init__()
        
        self.mdl_path = mdl_path
        self.mdx_path = mdx_path
        
        # Load the model
        self.model = self._load_model()
        
        # Set up camera controls
        self._setup_camera_controls()
        
        print(f"\nModel loaded: {mdl_path}")
        print("Camera controls:")
        print("  Mouse drag: Rotate camera")
        print("  Mouse wheel: Zoom in/out")
        print("  Arrow keys: Move camera")
        print("  ESC: Quit")
    
    def _load_model(self):
        """Load the MDL model using MDLLoader.
        
        Returns:
        -------
            NodePath of the loaded model
        """
        print(f"Loading model: {self.mdl_path}")
        
        loader = MDLLoader(
            material_manager=self.material_manager,
            resource_loader=self.loader,
            texture_base_path=Path(self.mdl_path).parent,
        )
        model = loader.load(self.mdl_path, self.mdx_path)
        
        if model:
            # Attach to scene
            model.reparentTo(self.scene_root)
            
            # Center camera on model
            # /panda3d/panda3d-docs/programming/scene-graph - NodePath bounds
            bounds = model.getTightBounds()
            if bounds[0] and bounds[1]:
                center = (bounds[0] + bounds[1]) / 2
                size = (bounds[1] - bounds[0]).length()
                
                # Position camera to view entire model
                self.camera.setPos(center.x, center.y - size * 2, center.z + size * 0.5)
                self.camera.lookAt(center)
        
        return model
    
    def _setup_camera_controls(self):
        """Set up mouse and keyboard camera controls.
        
        References:
        ----------
            /panda3d/panda3d-docs/programming/camera-control - Camera controls
        """
        # Disable default mouse controls
        self.disableMouse()
        
        # Enable mouse camera rotation
        # This is a simple orbit camera - production code would use proper camera controller
        self.taskMgr.add(self._camera_task, "camera_task")
        
        # Keyboard controls for camera movement
        self.accept("arrow_up", self._move_camera, [0, 1, 0])
        self.accept("arrow_down", self._move_camera, [0, -1, 0])
        self.accept("arrow_left", self._move_camera, [-1, 0, 0])
        self.accept("arrow_right", self._move_camera, [1, 0, 0])
        
        # Mouse wheel zoom
        self.accept("wheel_up", self._zoom_camera, [0.9])
        self.accept("wheel_down", self._zoom_camera, [1.1])
        
        # ESC to quit
        self.accept("escape", sys.exit, [0])
    
    def _camera_task(self, task):
        """Camera orbit task.
        
        Simple orbit camera controlled by mouse.
        
        References:
        ----------
            /panda3d/panda3d-docs/programming/tasks - Task system
        """
        # Get mouse position
        if self.mouseWatcherNode.hasMouse():
            x = self.mouseWatcherNode.getMouseX()
            y = self.mouseWatcherNode.getMouseY()
            
            # Simple orbit: mouse X/Y controls camera heading/pitch
            # This is very basic - production code would track mouse delta
            if self.mouseWatcherNode.isButtonDown(0):  # Left mouse button
                self.camera.setH(x * 180)
                self.camera.setP(y * 90)
        
        return task.cont
    
    def _move_camera(self, dx, dy, dz):
        """Move camera in local space.
        
        Args:
        ----
            dx, dy, dz: Movement deltas
        """
        pos = self.camera.getPos()
        self.camera.setPos(pos.x + dx, pos.y + dy, pos.z + dz)
    
    def _zoom_camera(self, factor):
        """Zoom camera by moving along view vector.
        
        Args:
        ----
            factor: Zoom factor (< 1 zooms in, > 1 zooms out)
        """
        pos = self.camera.getPos()
        self.camera.setPos(pos * factor)


def main():
    """Main entry point for the simple viewer."""
    if len(sys.argv) < 2:
        print("Usage: python simple_viewer.py <mdl_path> [mdx_path]")
        print("\nExample:")
        print("  python simple_viewer.py path/to/character.mdl")
        print("  python simple_viewer.py path/to/character.mdl path/to/character.mdx")
        sys.exit(1)
    
    mdl_path = sys.argv[1]
    mdx_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Verify MDL file exists
    if not Path(mdl_path).exists():
        print(f"Error: MDL file not found: {mdl_path}")
        sys.exit(1)
    
    # Create and run viewer
    viewer = SimpleModelViewer(mdl_path, mdx_path)
    viewer.run_game_loop()


if __name__ == "__main__":
    main()

