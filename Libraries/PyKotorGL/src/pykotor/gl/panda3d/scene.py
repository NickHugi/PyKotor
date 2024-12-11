"""Panda3D-based scene management for KotOR module loading."""

from __future__ import annotations

import math

from typing import TYPE_CHECKING, Any

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.Task import Task
from panda3d.core import LQuaternion, Point3, WindowProperties

from pykotor.common.module import Module
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.gl.panda3d.loader import load_mdl, load_tpc
from pykotor.resource.formats.twoda import TwoDA, read_2da
from pykotor.resource.type import ResourceType
from pykotor.tools import creature

if TYPE_CHECKING:
    from panda3d.core import NodePath

    from pykotor.common.module import ModuleResource
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.generics.git import GIT

SEARCH_ORDER_2DA = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]
SEARCH_ORDER = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]


def get_resource_data(resource: ModuleResource[Any] | None) -> bytes | None:
    """Get bytes data from a module resource."""
    if not resource:
        return None
    data = resource.data
    if callable(data):
        return data()
    return data


class KotorRenderer(ShowBase):
    """Panda3D renderer with KotOR module loading support."""

    def __init__(
        self,
        *,
        installation: Installation | None = None,
        module: Module | None = None,
    ):
        super().__init__()

        self.installation: Installation | None = installation
        if installation:
            self.set_installation(installation)

        self._module: Module | None = module

        # Root node for all module content
        self.module_root: NodePath = self.render.attachNewNode("module_root")

        # Set up camera
        self.camera.reparentTo(self.render)
        self.camera.setPos(0, -50, 20)  # Start position
        self.camera.lookAt(0, 0, 0)  # Look at center

        # Camera movement variables
        self.camera_speed = 30.0  # Units per second
        self.mouse_sensitivity = 0.3
        self.last_mouse = None
        self.keys = {}

        # Set up input handling
        self.accept("w", self.update_key, ["w", True])
        self.accept("w-up", self.update_key, ["w", False])
        self.accept("s", self.update_key, ["s", True])
        self.accept("s-up", self.update_key, ["s", False])
        self.accept("a", self.update_key, ["a", True])
        self.accept("a-up", self.update_key, ["a", False])
        self.accept("d", self.update_key, ["d", True])
        self.accept("d-up", self.update_key, ["d", False])
        self.accept("space", self.update_key, ["space", True])
        self.accept("space-up", self.update_key, ["space", False])
        self.accept("shift", self.update_key, ["shift", True])
        self.accept("shift-up", self.update_key, ["shift", False])

        # Add the camera update task
        self.taskMgr.add(self.update_camera, "UpdateCameraTask")

        # Disable mouse cursor and enable relative mouse mode
        self.disable_mouse()
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(props)

        # Load module if provided
        if module:
            self.load_module(module)

    def set_installation(self, installation: Installation) -> None:
        """Set up KotOR installation and load required 2DA files."""

        def load_2da(name: str) -> TwoDA:
            resource = installation.resource(name, ResourceType.TwoDA, SEARCH_ORDER_2DA)
            if not resource:
                return TwoDA()
            return read_2da(resource.data)

        self.table_doors = load_2da("genericdoors")
        self.table_placeables = load_2da("placeables")
        self.table_creatures = load_2da("appearance")
        self.table_heads = load_2da("heads")
        self.table_baseitems = load_2da("baseitems")

    def load_module(self, module: Module) -> None:
        """Load a module and all its content into the scene."""
        self._module = module

        # Clear existing content
        self.module_root.removeNode()
        self.module_root = self.render.attachNewNode("module_root")

        # Load GIT/LYT
        git_resource = module.git()
        lyt_resource = module.layout()
        if git_resource is not None and lyt_resource is not None:
            self.git = git_resource.resource()
            self.layout = lyt_resource.resource()
        else:
            return

        # Load rooms
        if self.layout is not None:
            self._load_rooms(self.layout)

        if self.git is None:
            return

        self._load_cameras(self.git)
        self._load_creatures(self.git)
        self._load_doors(self.git)
        self._load_encounters(self.git)
        self._load_placeables(self.git)
        self._load_sounds(self.git)
        self._load_stores(self.git)
        self._load_triggers(self.git)
        self._load_waypoints(self.git)

    def _load_rooms(self, layout: LYT) -> None:
        """Load room models from layout."""
        for room in layout.rooms:
            room_node = self._load_model(room.model)
            if room_node:
                room_node.reparentTo(self.module_root)
                room_node.setPos(room.position.x, room.position.y, room.position.z)

    def _load_doors(self, git: GIT) -> None:
        """Load door models from GIT."""
        assert self._module is not None
        for door in git.doors:
            door_node = self.module_root.attachNewNode(door.resref + ".utd")
            door_node.setPos(door.position.x, door.position.y, door.position.z)
            door_node.setH(door.bearing)

            door_resource = self._module.door(str(door.resref))
            if door_resource:
                utd = door_resource.resource()
                if utd:
                    model_name = self.table_doors.get_row(utd.appearance_id).get_string("modelname")
                    door_node = self._load_model(model_name)
                    if door_node:
                        door_node.reparentTo(self.module_root)
                        door_node.setPos(door.position.x, door.position.y, door.position.z)
                        door_node.setH(door.bearing)

    def _load_placeables(self, git: GIT) -> None:
        """Load placeable models from GIT."""
        assert self._module is not None
        for placeable in git.placeables:
            placeable_node = self.module_root.attachNewNode(placeable.resref + ".utp")
            placeable_node.setPos(placeable.position.x, placeable.position.y, placeable.position.z)
            placeable_node.setH(placeable.bearing)

            placeable_resource = self._module.placeable(str(placeable.resref))
            if placeable_resource:
                utp = placeable_resource.resource()
                if utp:
                    model_name = self.table_placeables.get_row(utp.appearance_id).get_string("modelname")
                    placeable_node = self._load_model(model_name)
                    if placeable_node:
                        placeable_node.reparentTo(self.module_root)
                        placeable_node.setPos(placeable.position.x, placeable.position.y, placeable.position.z)
                        placeable_node.setH(placeable.bearing)

    def _load_creatures(self, git: GIT) -> None:
        """Load creature models from GIT."""
        assert self._module is not None
        for git_creature in git.creatures:
            creature_node = self.module_root.attachNewNode(git_creature.resref + ".utc")
            creature_node.setPos(git_creature.position.x, git_creature.position.y, git_creature.position.z)
            creature_node.setH(git_creature.bearing)

            creature_resource = self._module.creature(str(git_creature.resref))
            if creature_resource and self.installation:
                utc = creature_resource.resource()
                if utc:
                    # Get body model
                    body_model, body_tex = creature.get_body_model(utc, self.installation, appearance=self.table_creatures, baseitems=self.table_baseitems)

                    if body_model:
                        creature_node = self._load_model(body_model)
                        if creature_node:
                            creature_node.reparentTo(self.module_root)
                            creature_node.setPos(git_creature.position.x, git_creature.position.y, git_creature.position.z)
                            creature_node.setH(git_creature.bearing)

                            if body_tex:
                                self._load_texture(body_tex, creature_node)

                            # Load head if present
                            head_model, head_tex = creature.get_head_model(utc, self.installation, appearance=self.table_creatures, heads=self.table_heads)

                            if head_model and head_model.strip():
                                head_hook = creature_node.find("**/headhook")
                                if not head_hook.isEmpty():
                                    head_node = self._load_model(head_model)
                                    if head_node is not None:
                                        head_node.reparentTo(head_hook)
                                        if head_tex and head_tex.strip():
                                            self._load_texture(head_tex, head_node)

    def _load_cameras(self, git: GIT) -> None:
        """Load camera nodes from GIT."""
        for i, camera in enumerate(git.cameras):
            camera_node = self.module_root.attachNewNode(f"camera_{i}")
            camera_node.setPos(camera.position.x, camera.position.y, camera.position.z + camera.height)
            quat = LQuaternion(camera.orientation.w, camera.orientation.x, camera.orientation.y, camera.orientation.z)
            euler = quat.getHpr()
            camera_node.setHpr(
                euler[1],  # Pitch
                euler[2] - 90 + math.degrees(camera.pitch),  # Yaw
                -euler[0] + 90,  # Roll
            )

    def _load_sounds(self, git: GIT) -> None:
        """Load sound nodes from GIT."""
        for sound in git.sounds:
            sound_node = self.module_root.attachNewNode(sound.resref + ".uts")
            sound_node.setPos(sound.position.x, sound.position.y, sound.position.z)

    def _load_triggers(self, git: GIT) -> None:
        """Load trigger nodes from GIT."""
        for trigger in git.triggers:
            trigger_node = self.module_root.attachNewNode(trigger.resref + ".utt")
            trigger_node.setPos(trigger.position.x, trigger.position.y, trigger.position.z)

    def _load_encounters(self, git: GIT) -> None:
        """Load encounter nodes from GIT."""
        for encounter in git.encounters:
            encounter_node = self.module_root.attachNewNode(encounter.resref + ".ute")
            encounter_node.setPos(encounter.position.x, encounter.position.y, encounter.position.z)

    def _load_waypoints(self, git: GIT) -> None:
        """Load waypoint nodes from GIT."""
        for waypoint in git.waypoints:
            waypoint_node = self.module_root.attachNewNode(waypoint.resref + ".utw")
            waypoint_node.setPos(waypoint.position.x, waypoint.position.y, waypoint.position.z)

    def _load_stores(self, git: GIT) -> None:
        """Load store nodes from GIT."""
        for store in git.stores:
            store_node = self.module_root.attachNewNode(store.resref + ".utm")
            store_node.setPos(store.position.x, store.position.y, store.position.z)

    def _load_model(self, name: str) -> NodePath | None:
        """Load MDL from module or installation."""
        assert self.installation is not None

        mdl = self.installation.resource(name, ResourceType.MDL, SEARCH_ORDER)
        mdx = self.installation.resource(name, ResourceType.MDX, SEARCH_ORDER)
        if mdl is not None and mdx is not None:
            return load_mdl(mdl.data[12:], mdx.data)

        return None

    def _load_texture(self, name: str, model: NodePath) -> None:
        """Load TPC from module or installation and apply to model."""
        assert self.installation is not None

        # Then try installation
        tpc = self.installation.texture(
            name,
            [
                SearchLocation.CUSTOM_MODULES,
                SearchLocation.OVERRIDE,
                SearchLocation.TEXTURES_TPA,
                SearchLocation.CHITIN,
            ],
            capsules=None if self._module is None else self._module.capsules(),
        )
        if tpc is not None:
            tex = load_tpc(tpc)
            model.setTexture(tex)

    def update_key(self, key: str, value: bool) -> None:
        """Update the key state dictionary."""
        self.keys[key] = value

    def update_camera(self, task: Task) -> int:
        """Update camera position and rotation based on input."""
        dt = globalClock.getDt()

        # Get the mouse movement
        if self.mouseWatcherNode.hasMouse():
            x = self.mouseWatcherNode.getMouseX()
            y = self.mouseWatcherNode.getMouseY()

            if self.last_mouse is not None:
                dx = x - self.last_mouse[0]
                dy = y - self.last_mouse[1]

                # Update camera rotation
                h = self.camera.getH() - dx * self.mouse_sensitivity * 100
                p = self.camera.getP() - dy * self.mouse_sensitivity * 100
                p = max(-89, min(89, p))  # Clamp pitch to prevent flipping
                self.camera.setHpr(h, p, 0)

            self.last_mouse = (x, y)

        # Get the camera's direction vectors
        forward = self.camera.getMat().getRow3(1)
        left = self.camera.getMat().getRow3(0)
        up = Point3(0, 0, 1)

        # Calculate movement direction
        move_vec = Point3(0, 0, 0)

        if self.keys.get("w"):
            move_vec += forward
        if self.keys.get("s"):
            move_vec -= forward
        if self.keys.get("a"):
            move_vec += left
        if self.keys.get("d"):
            move_vec -= left
        if self.keys.get("space"):
            move_vec += up
        if self.keys.get("shift"):
            move_vec -= up

        # Normalize and apply movement
        if move_vec.length() > 0:
            move_vec.normalize()
            speed = self.camera_speed
            if self.keys.get("control"):  # Sprint
                speed *= 2.0
            self.camera.setPos(self.camera.getPos() + move_vec * speed * dt)

        return Task.cont


print("Starting demo...")
demo: KotorRenderer | None = None

if __name__ == "__main__":
    from pathlib import Path

    from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel, DirectOptionMenu
    from direct.showbase.ShowBase import ShowBase
    from panda3d.core import TextNode, WindowProperties

    from pykotor.common.misc import Game
    from pykotor.extract.installation import Installation
    from pykotor.tools.path import find_kotor_paths_from_default

    class MyApp(ShowBase):
        def __init__(self):
            ShowBase.__init__(self)
            self.selected_game = None
            self.selected_installation_path = None
            self.selected_level = None
            self.game_menu = None
            self.should_exit = False

            # Set up window properties
            props = WindowProperties()
            props.setTitle("KotOR Module Viewer")
            props.setSize(800, 600)
            self.win.requestProperties(props)

            # Set up background
            self.setBackgroundColor(0.12, 0.12, 0.14)  # Dark background

            self.select_game_installation_and_level()

        def select_game_installation_and_level(self):
            # Find KotOR installation paths
            paths: dict[Game, list[Path]] = find_kotor_paths_from_default()  # pyright: ignore[reportAssignmentType]
            if not paths:
                print("Could not find KotOR installation")
                self.should_exit = True
                return

            # Create main container frame with more padding
            frame = DirectFrame(
                frameColor=(0.16, 0.16, 0.18, 0.95),
                frameSize=(-1.0, 1.0, -0.7, 0.7),  # Wider frame
                pos=(0, 0, 0),
                relief=1
            )

            # Title bar
            title_frame = DirectFrame(
                frameColor=(0.18, 0.18, 0.2, 1),
                frameSize=(-1.0, 1.0, -0.1, 0.1),
                pos=(0, 0, 0.6),
                parent=frame,
                relief=1
            )

            DirectLabel(
                text="KotOR Module Viewer",
                scale=0.08,  # Larger text
                pos=(0, 0, 0),
                parent=title_frame,
                text_fg=(0.95, 0.95, 0.95, 1),
                text_align=TextNode.ACenter,
                text_shadow=(0, 0, 0, 0.5),
                text_shadowOffset=(0.002, 0.002)
            )

            # Content container with better spacing
            content_frame = DirectFrame(
                frameColor=(0.16, 0.16, 0.18, 0),
                frameSize=(-0.9, 0.9, -0.5, 0.5),
                pos=(0, 0, 0),
                parent=frame
            )

            # Row height and spacing
            row_height = 0.15
            label_scale = 0.07
            menu_scale = 0.07
            button_scale = 0.07

            # Game selection row
            game_label = DirectLabel(
                text="Game",
                scale=label_scale,
                pos=(-0.85, 0, 0.3),
                parent=content_frame,
                text_align=TextNode.ALeft,
                text_fg=(0.9, 0.9, 0.9, 1)
            )

            game_options = [game.name for game in paths.keys()]
            self.game_menu = DirectOptionMenu(
                text="Select Game",
                scale=menu_scale,
                items=game_options,
                initialitem=0,
                pos=(-0.3, 0, 0.3),
                parent=content_frame,
                frameSize=(-0.6, 0.6, -0.25, 0.25),
                popupMarker_scale=0.3,
                frameColor=(0.12, 0.12, 0.14, 1),  # Darker background
                highlightColor=(0.18, 0.18, 0.2, 1),
                text_fg=(0.9, 0.9, 0.9, 1),
                item_text_fg=(0.9, 0.9, 0.9, 1),
                item_frameColor=(0.12, 0.12, 0.14, 0.95)
            )

            game_button = DirectButton(
                text="Choose",
                scale=button_scale,
                pos=(0.5, 0, 0.3),
                command=self.update_installations,
                parent=content_frame,
                frameSize=(-0.6, 0.6, -0.4, 0.4),  # Much larger clickable area
                frameColor=(0.2, 0.5, 0.9, 1),
                pressEffect=0.9,
                relief=1,
                text_fg=(1, 1, 1, 1)
            )

            # Installation selection row
            installation_label = DirectLabel(
                text="Path",
                scale=label_scale,
                pos=(-0.85, 0, 0),
                parent=content_frame,
                text_align=TextNode.ALeft,
                text_fg=(0.9, 0.9, 0.9, 1)
            )

            self.installation_menu = DirectOptionMenu(
                text="Select Installation",
                scale=menu_scale,
                items=["No installations found"],
                pos=(-0.3, 0, 0),
                parent=content_frame,
                frameSize=(-0.6, 0.6, -0.25, 0.25),
                popupMarker_scale=0.3,
                frameColor=(0.12, 0.12, 0.14, 1),  # Darker background
                highlightColor=(0.18, 0.18, 0.2, 1),
                text_fg=(0.9, 0.9, 0.9, 1),
                item_text_fg=(0.9, 0.9, 0.9, 1),
                item_frameColor=(0.12, 0.12, 0.14, 0.95)
            )

            installation_button = DirectButton(
                text="Choose",
                scale=button_scale,
                pos=(0.5, 0, 0),
                command=self.update_levels,
                parent=content_frame,
                frameSize=(-0.6, 0.6, -0.4, 0.4),  # Much larger clickable area
                frameColor=(0.2, 0.5, 0.9, 1),
                pressEffect=0.9,
                relief=1,
                text_fg=(1, 1, 1, 1)
            )

            # Level selection row
            level_label = DirectLabel(
                text="Level",
                scale=label_scale,
                pos=(-0.85, 0, -0.3),
                parent=content_frame,
                text_align=TextNode.ALeft,
                text_fg=(0.9, 0.9, 0.9, 1)
            )

            self.level_menu = DirectOptionMenu(
                text="Select Level",
                scale=menu_scale,
                items=["No levels found"],
                pos=(-0.3, 0, -0.3),
                parent=content_frame,
                frameSize=(-0.6, 0.6, -0.25, 0.25),
                popupMarker_scale=0.3,
                frameColor=(0.12, 0.12, 0.14, 1),  # Darker background
                highlightColor=(0.18, 0.18, 0.2, 1),
                text_fg=(0.9, 0.9, 0.9, 1),
                item_text_fg=(0.9, 0.9, 0.9, 1),
                item_frameColor=(0.12, 0.12, 0.14, 0.95)
            )

            # Store paths
            self.paths = paths

            # Load button
            load_button = DirectButton(
                text="Load Module",
                scale=0.08,
                pos=(0, 0, -0.5),
                command=self.confirm_selection,
                parent=frame,
                frameSize=(-0.8, 0.8, -0.4, 0.4),  # Much larger clickable area
                frameColor=(0.2, 0.7, 0.4, 1),
                pressEffect=0.9,
                relief=1,
                text_fg=(1, 1, 1, 1)
            )

        def update_installations(self):
            if self.game_menu is None:
                return

            selected_game = self.game_menu.get()
            game_enum = Game[selected_game]
            installation_paths = self.paths[game_enum]

            if installation_paths:
                self.installation_menu["items"] = [str(path) for path in installation_paths]
                self.installation_menu.set(0)
            else:
                self.installation_menu["items"] = ["No installations found"]
                self.installation_menu.set(0)

            # Reset level menu
            self.level_menu["items"] = ["No levels found"]
            self.level_menu.set(0)

        def update_levels(self):
            selected_path = self.installation_menu.get()
            if selected_path and selected_path != "No installations found":
                self.selected_installation = Installation(Path(selected_path))
                levels = self.selected_installation.modules_list()
                if levels:
                    self.level_menu["items"] = levels
                    self.level_menu.set(0)
                else:
                    self.level_menu["items"] = ["No levels found"]
                    self.level_menu.set(0)

        def confirm_selection(self):
            if self.game_menu is None or self.installation_menu is None or self.level_menu is None:
                return

            selected_level = self.level_menu.get()
            if selected_level == "No levels found":
                return

            self.selected_game = self.game_menu.get()
            self.selected_installation_path = self.installation_menu.get()
            self.selected_level = selected_level

            if all(
                [
                    self.selected_game,
                    self.selected_installation_path and self.selected_installation_path != "No installations found",
                    self.selected_level and self.selected_level != "No levels found",
                ]
            ):
                self.should_exit = True

        def run(self):
            """Override run to handle clean exit."""
            while not self.should_exit:
                self.taskMgr.step()

            # Clean up
            self.destroy()
            return self.selected_game, self.selected_installation, self.selected_level

    # Run the selection UI first
    app = MyApp()
    selected_game, selected_installation, selected_level = app.run()

    # Only proceed if we have valid selections
    if all([selected_game, selected_installation, selected_level]):
        print(f"Selected Game: {selected_game}")
        print(f"Selected Installation: {selected_installation}")
        print(f"Selected Level: {selected_level}")

        # Now create and run the renderer
        demo = KotorRenderer(
            installation=selected_installation,
            module=Module(str(selected_level), selected_installation),
        )
        demo.run()

print("Demo finished.")
