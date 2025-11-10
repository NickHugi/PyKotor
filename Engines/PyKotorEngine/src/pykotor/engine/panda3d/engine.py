"""Panda3D implementation of KotOR engine.

This module provides the main engine class using Panda3D's ShowBase.

References:
----------
    vendor/xoreos/src/graphics/windowman.cpp - Window and OpenGL initialization
    vendor/reone/src/libs/game/game.cpp - Game class architecture
    /panda3d/panda3d-docs/programming/showbase - ShowBase documentation
"""

from __future__ import annotations

from pathlib import Path

from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight,
    AntialiasAttrib,
    DirectionalLight,
    Vec4,
    loadPrcFileData,
    NodePath,
)

from pykotor.engine.panda3d.scene_graph import Panda3DSceneGraph
from pykotor.engine.panda3d.materials import Panda3DMaterialManager


class KotorEngine(ShowBase):
    """Main KotOR engine class using Panda3D.
    
    This class extends ShowBase to provide KotOR-specific functionality.
    
    References:
    ----------
        vendor/xoreos/src/graphics/windowman.cpp:49-146 - Window/OpenGL setup
        vendor/reone/src/libs/game/game.cpp:45-120 - Game initialization
        vendor/KotOR.js/src/Game.ts - Three.js equivalent
        /panda3d/panda3d-docs/introduction/tutorial/starting-panda3d - ShowBase
    
    Attributes:
    ----------
        scene_root: Root NodePath for KotOR scene content
        scene_graph: Scene graph manager
    """
    
    def __init__(self):
        """Initialize the KotOR engine.
        
        Sets up Panda3D configuration and initializes the rendering system.
        
        References:
        ----------
            vendor/xoreos/src/graphics/windowman.cpp:70-86 - init()
            vendor/xoreos/src/graphics/windowman.cpp:94-146 - initRender()
            /panda3d/panda3d-docs/programming/configuration/accessing-config-vars - loadPrcFileData
        """
        # Configure Panda3D before ShowBase initialization
        # References:
        # - vendor/xoreos/src/graphics/windowman.cpp:56 - Window title
        # - /panda3d/panda3d-docs - loadPrcFileData usage
        loadPrcFileData("", "window-title KotOR Engine - PyKotor")
        
        # Window size
        # References:
        # - vendor/xoreos/src/graphics/windowman.cpp:77-78 - Window dimensions
        # - vendor/reone test files - Default 1024x768
        loadPrcFileData("", "win-size 1280 720")
        
        # Frame rate meter for debugging
        loadPrcFileData("", "show-frame-rate-meter true")
        
        # V-sync
        # Reference: vendor/xoreos/src/graphics/windowman.cpp - No explicit v-sync config
        loadPrcFileData("", "sync-video false")
        
        # OpenGL version
        # Reference: vendor/xoreos/src/graphics/windowman.cpp:108-112 - OpenGL 3.2/2.1
        loadPrcFileData("", "gl-version 3 3")
        
        # Notification level
        loadPrcFileData("", "notify-level warning")
        
        # Antialiasing
        # Reference: vendor/xoreos/src/graphics/windowman.cpp:105-106 - MULTISAMPLE
        loadPrcFileData("", "default-antialias-enable true")
        
        # Initialize ShowBase
        # Reference: /panda3d/panda3d-docs - ShowBase.__init__(self)
        ShowBase.__init__(self)
        
        # Set up antialiasing on the scene
        # Reference: /panda3d/panda3d-docs - render.setAntialias(AntialiasAttrib.MAuto)
        self.render.setAntialias(AntialiasAttrib.MAuto)
        
        # Create scene root for KotOR content
        # References:
        # - vendor/reone/src/libs/scene/graph.cpp:30-35 - SceneGraph root
        # - /panda3d/panda3d-docs - NodePath creation
        self.scene_root: NodePath = self.render.attachNewNode("kotor_scene")
        
        # Create scene graph manager
        self.scene_graph = Panda3DSceneGraph("main_scene", self.scene_root)
        self.material_manager = Panda3DMaterialManager(self.loader, Path.cwd())
        
        # Set up default lighting
        # Reference: vendor/reone/src/libs/scene/graph.cpp:150-180 - Lighting setup
        self._setup_default_lighting()
        
        # Configure camera
        # References:
        # - vendor/reone/src/libs/scene/graph.cpp:100-120 - Camera setup
        # - /panda3d/panda3d-docs - camera.setPos()
        self.camera.setPos(0, -10, 2)
        self.camera.lookAt(0, 0, 0)
        
        print("PyKotorEngine initialized (Panda3D)")
        print(f"Panda3D version: {self.getVersionString()}")
        print(f"OpenGL version: {self.win.getGsg().getDriverVersion()}")
    
    def _setup_default_lighting(self) -> None:
        """Set up default scene lighting.
        
        Creates ambient and directional lights.
        
        References:
        ----------
            vendor/reone/src/libs/scene/graph.cpp:150-180 - Lighting initialization
            vendor/reone/src/libs/scene/node/light.cpp:80-120 - Light setup
            /panda3d/panda3d-docs - AmbientLight, DirectionalLight
        """
        # Ambient light
        # Reference: vendor/reone/src/libs/scene/node/light.cpp:80-85
        ambient = AmbientLight("ambient_light")
        ambient.setColor(Vec4(0.3, 0.3, 0.3, 1.0))
        self.ambient_light = self.render.attachNewNode(ambient)
        self.scene_root.setLight(self.ambient_light)
        
        # Directional light (sun)
        # Reference: vendor/reone/src/libs/scene/node/light.cpp:90-120
        sun = DirectionalLight("sun_light")
        sun.setColor(Vec4(0.8, 0.8, 0.7, 1.0))
        self.sun_light = self.render.attachNewNode(sun)
        self.sun_light.setHpr(45, -45, 0)
        self.scene_root.setLight(self.sun_light)
    
    def run_game_loop(self) -> None:
        """Start the main game loop.
        
        References:
        ----------
            vendor/reone/src/libs/game/game.cpp:200-250 - Main loop
            /panda3d/panda3d-docs - base.run()
        """
        print("Starting KotOR Engine main loop...")
        self.run()


def create_engine() -> KotorEngine:
    """Factory function to create a KotorEngine instance.
    
    Returns:
    -------
        Initialized KotorEngine
    
    References:
    ----------
        vendor/reone/src/libs/game/game.cpp:30-45 - Game creation
    """
    return KotorEngine()

