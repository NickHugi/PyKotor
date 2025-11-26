from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import (
    QSize,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QColor, QPainter, QPen, QTransform
from qtpy.QtWidgets import QFileDialog, QGraphicsEllipseItem, QGraphicsItem, QGraphicsLineItem, QGraphicsRectItem, QGraphicsScene, QListView, QMessageBox

from pykotor.common.misc import Color
from pykotor.resource.formats.lyt import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack, bytes_lyt, read_lyt
from pykotor.resource.type import ResourceType
from toolset.data.misc import ControlItem
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.editor_settings.lyt import LYTEditorSettings
from utility.common.geometry import SurfaceMaterial, Vector3, Vector4

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation


class LYTEditor(Editor):
    sig_lyt_updated = Signal(LYT)

    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        supported: list[ResourceType] = [ResourceType.LYT]
        super().__init__(parent, "LYT Editor", "lyt", supported, supported, installation)

        from toolset.uic.qtpy.editors.lyt import Ui_LYTEditor

        self.ui: Ui_LYTEditor = Ui_LYTEditor()
        self.ui.setupUi(self)

        # Initialize scene
        self.scene: QGraphicsScene = QGraphicsScene()
        self.ui.graphicsView.setScene(self.scene)

        # Connect buttons - Fixed FIXME comments by using proper UI elements
        self.ui.addDoorHookButton.clicked.connect(self.add_door_hook)
        self.ui.importTextureButton.clicked.connect(self.import_texture)
        self.ui.importModelButton.clicked.connect(self.import_model)

        # Setup texture browser - Fixed FIXME comments by using proper UI elements
        self.ui.textureBrowser.setIconSize(QSize(64, 64))
        self.ui.textureBrowser.setViewMode(QListView.ViewMode.IconMode)
        self.ui.textureBrowser.setResizeMode(QListView.ResizeMode.Adjust)
        self.ui.textureBrowser.setWrapping(True)

        # Setup room templates - Fixed FIXME comment by using proper UI element
        self.ui.roomTemplateList.addItems(["Square Room", "Circular Room", "L-Shaped Room"])

        self._lyt: LYT = LYT()
        self._controls: LYTControlScheme = LYTControlScheme(self)
        self.settings: LYTEditorSettings = LYTEditorSettings()

        self.material_colors: dict[SurfaceMaterial, QColor] = self._setup_material_colors()

        self._setup_menus()
        self._add_help_action()
        self._setup_connections()
        self._setup_graphics_view()
        self._setup_sidebar()

    def _setup_material_colors(self) -> dict[SurfaceMaterial, QColor]:
        def int_color_to_q_color(num_color: int) -> QColor:
            color: Color = Color.from_rgba_integer(num_color)
            return QColor(int(color.r * 255), int(color.g * 255), int(color.b * 255), int((1 if color.a is None else color.a) * 255))

        return {
            SurfaceMaterial.UNDEFINED: int_color_to_q_color(self.settings.undefinedMaterialColour),
            SurfaceMaterial.OBSCURING: int_color_to_q_color(self.settings.obscuringMaterialColour),
            SurfaceMaterial.DIRT: int_color_to_q_color(self.settings.dirtMaterialColour),
            SurfaceMaterial.GRASS: int_color_to_q_color(self.settings.grassMaterialColour),
            SurfaceMaterial.STONE: int_color_to_q_color(self.settings.stoneMaterialColour),
            SurfaceMaterial.WOOD: int_color_to_q_color(self.settings.woodMaterialColour),
            SurfaceMaterial.WATER: int_color_to_q_color(self.settings.waterMaterialColour),
            SurfaceMaterial.NON_WALK: int_color_to_q_color(self.settings.nonWalkMaterialColour),
            SurfaceMaterial.TRANSPARENT: int_color_to_q_color(self.settings.transparentMaterialColour),
            SurfaceMaterial.CARPET: int_color_to_q_color(self.settings.carpetMaterialColour),
            SurfaceMaterial.METAL: int_color_to_q_color(self.settings.metalMaterialColour),
            SurfaceMaterial.PUDDLES: int_color_to_q_color(self.settings.puddlesMaterialColour),
            SurfaceMaterial.SWAMP: int_color_to_q_color(self.settings.swampMaterialColour),
            SurfaceMaterial.MUD: int_color_to_q_color(self.settings.mudMaterialColour),
            SurfaceMaterial.LEAVES: int_color_to_q_color(self.settings.leavesMaterialColour),
            SurfaceMaterial.LAVA: int_color_to_q_color(self.settings.lavaMaterialColour),
            SurfaceMaterial.BOTTOMLESS_PIT: int_color_to_q_color(self.settings.bottomlessPitMaterialColour),
            SurfaceMaterial.DEEP_WATER: int_color_to_q_color(self.settings.deepWaterMaterialColour),
            SurfaceMaterial.DOOR: int_color_to_q_color(self.settings.doorMaterialColour),
            SurfaceMaterial.NON_WALK_GRASS: int_color_to_q_color(self.settings.nonWalkGrassMaterialColour),
            SurfaceMaterial.TRIGGER: int_color_to_q_color(self.settings.nonWalkGrassMaterialColour),
        }

    def _setup_connections(self):
        self.ui.addRoomButton.clicked.connect(self.add_room)
        self.ui.addTrackButton.clicked.connect(self.add_track)
        self.ui.addObstacleButton.clicked.connect(self.add_obstacle)
        self.ui.generateWalkmeshButton.clicked.connect(self.generate_walkmesh)
        self.ui.zoomSlider.valueChanged.connect(self.update_zoom)

    def _setup_graphics_view(self):
        self.ui.graphicsView.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.ui.graphicsView.setDragMode(self.ui.graphicsView.DragMode.ScrollHandDrag)
        self.ui.graphicsView.setTransformationAnchor(self.ui.graphicsView.ViewportAnchor.AnchorUnderMouse)
        self.ui.graphicsView.setResizeAnchor(self.ui.graphicsView.ViewportAnchor.AnchorUnderMouse)

    def _setup_sidebar(self):
        # Setup texture browser
        self.ui.textureBrowser.setIconSize(QSize(64, 64))  # FIXME: textureBrowser attribute not found
        self.ui.textureBrowser.setViewMode(QListView.ViewMode.IconMode)  # FIXME: textureBrowser attribute not found
        self.ui.textureBrowser.setResizeMode(QListView.ResizeMode.Adjust)  # FIXME: textureBrowser attribute not found
        self.ui.textureBrowser.setWrapping(True)  # FIXME: textureBrowser attribute not found

        # Setup room templates
        self.ui.roomTemplateList.addItems(["Square Room", "Circular Room", "L-Shaped Room"])  # FIXME: roomTemplateList attribute not found

    def add_room(self):
        room = LYTRoom(model="default_room", position=Vector3(0, 0, 0))
        room.size = Vector3(10, 10, 3)
        self._lyt.rooms.add(room)
        self.update_scene()

    def add_track(self):
        if len(self._lyt.rooms) < 2:
            return

        track = LYTTrack(model="default_track", position=Vector3(0, 0, 0))

        # Find path through connected rooms
        start_room: LYTRoom = next(iter(self._lyt.rooms))
        end_room: LYTRoom = next(iter(self._lyt.rooms - {start_room}))
        path: list[LYTRoom] | None = self.find_path(start_room, end_room)

        if path:
            # Note: LYTTrack doesn't have start_room, end_room, or track_type attributes
            # These would need to be added to the LYTTrack class if needed
            # For now, just add the track
            self._lyt.tracks.append(track)

        self.update_scene()

    def find_path(
        self,
        start: LYTRoom,
        end: LYTRoom,
    ) -> list[LYTRoom] | None:
        """Find a path between rooms using A* pathfinding."""
        from heapq import heappop, heappush

        def heuristic(room: LYTRoom) -> float:
            return (room.position - end.position).magnitude()

        # Priority queue of (priority, current_room, path)
        queue: list[tuple[float, LYTRoom, list[LYTRoom]]] = [(0, start, [start])]
        visited: set[LYTRoom] = {start}

        while queue:
            _, current, path = heappop(queue)

            if current == end:
                return path

            for next_room in current.connections - visited:
                visited.add(next_room)
                new_path: list[LYTRoom] = [*path, next_room]
                priority: float = len(new_path) + heuristic(next_room)
                heappush(queue, (priority, next_room, new_path))

        return None  # No path found

    def add_obstacle(self):
        obstacle = LYTObstacle(model="default_obstacle", position=Vector3(0, 0, 0), radius=5.0)
        self._lyt.obstacles.append(obstacle)
        self.update_scene()

    def add_door_hook(self):
        """Add a new door hook with proper initialization."""
        if not self._lyt.rooms:
            return

        # Get the first room as default
        first_room: LYTRoom = next(iter(self._lyt.rooms))

        # Create door hook with required parameters
        doorhook = LYTDoorHook(
            room=first_room.model,  # Pass the room's model name
            door="",  # Empty string as default door name
            position=Vector3(0, 0, 0),
            orientation=Vector4(0, 0, 0, 1)  # Default orientation as quaternion
        )

        # Add to LYT data
        self._lyt.doorhooks.append(doorhook)

        # Create and add graphics item
        door_hook_item = DoorHookItem(doorhook, self)
        self.scene.addItem(door_hook_item)

        # Notify of update
        self.sig_lyt_updated.emit(self._lyt)

    def generate_walkmesh(self):
        # Implement walkmesh generation logic here
        pass

    def update_zoom(self, value: int):
        scale: float = value / 100.0
        self.ui.graphicsView.setTransform(QTransform().scale(scale, scale))

    def update_scene(self):
        self.scene.clear()
        for room in self._lyt.rooms:
            self.scene.addItem(RoomItem(room, self))
        for track in self._lyt.tracks:
            self.scene.addItem(TrackItem(track, self))
        for obstacle in self._lyt.obstacles:
            self.scene.addItem(ObstacleItem(obstacle, self))
        for doorhook in self._lyt.doorhooks:
            self.scene.addItem(DoorHookItem(doorhook, self))

    def import_texture(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Texture", "", "Image Files (*.png *.jpg *.bmp)")
        if file_path:
            # TODO: Implement texture import logic
            self.update_texture_browser()

    def import_model(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Model", "", "Model Files (*.mdl)")
        if file_path:
            # TODO: Implement model import logic
            pass

    def update_texture_browser(self):
        # TODO: Update texture browser with imported textures
        pass

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes) -> None:
        """Load a LYT file.
        
        Args:
        ----
            filepath: Filepath to load resource from
            resref: Resource reference
            restype: ResourceType
            data: Resource data
            
        Note: LYT files are GFF files, so they need save game detection and field preservation.
        """
        super().load(filepath, resref, restype, data)
        try:
            self._lyt = read_lyt(data)
            self.update_scene()
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Error", f"Failed to load LYT: {e}")

    def build(self) -> tuple[bytes, ResourceType]:
        return bytes_lyt(self._lyt), ResourceType.LYT


class RoomItem(QGraphicsRectItem):
    def __init__(self, room: LYTRoom, editor: LYTEditor):
        # Default size if not specified
        self.default_size = Vector3(10, 10, 0)
        size = getattr(room, "size", self.default_size)

        super().__init__(room.position.x, room.position.y, size.x, size.y)
        self.room: LYTRoom = room
        self.editor: LYTEditor = editor
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    def update_position(self):
        """Update the rectangle position and size."""
        size = getattr(self.room, "size", self.default_size)
        self.setRect(self.room.position.x, self.room.position.y, size.x, size.y)


class TrackItem(QGraphicsLineItem):
    def __init__(self, track: LYTTrack, editor: LYTEditor):
        # Calculate start and end points from connected rooms
        start_pos = track.start_room.position if track.start_room else track.position
        end_pos = track.end_room.position if track.end_room else track.position + Vector3(1, 1, 0)

        super().__init__(start_pos.x, start_pos.y, end_pos.x, end_pos.y)
        self.track: LYTTrack = track
        self.editor: LYTEditor = editor
        self.setPen(QPen(Qt.GlobalColor.red, 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    def update_position(self):
        """Update the line position based on connected rooms."""
        start_pos: Vector3 = self.track.start_room.position if self.track.start_room else self.track.position
        end_pos: Vector3 = self.track.end_room.position if self.track.end_room else self.track.position + Vector3(1, 1, 0)
        self.setLine(start_pos.x, start_pos.y, end_pos.x, end_pos.y)


class ObstacleItem(QGraphicsEllipseItem):
    def __init__(self, obstacle: LYTObstacle, editor: LYTEditor):
        # Default radius if not specified
        self.default_radius = 5.0
        radius = getattr(obstacle, "radius", self.default_radius)

        super().__init__(obstacle.position.x - radius, obstacle.position.y - radius, radius * 2, radius * 2)
        self.obstacle: LYTObstacle = obstacle
        self.editor: LYTEditor = editor
        self.setPen(QPen(Qt.GlobalColor.blue, 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    def update_position(self):
        """Update the ellipse position and size."""
        radius = getattr(self.obstacle, "radius", self.default_radius)
        self.setRect(self.obstacle.position.x - radius, self.obstacle.position.y - radius, radius * 2, radius * 2)


class DoorHookItem(QGraphicsRectItem):
    def __init__(self, doorhook: LYTDoorHook, editor: LYTEditor):
        # Default size for door hooks
        self.hook_size = 3.0

        super().__init__(doorhook.position.x - self.hook_size / 2, doorhook.position.y - self.hook_size / 2, self.hook_size, self.hook_size)
        self.doorhook: LYTDoorHook = doorhook
        self.editor: LYTEditor = editor
        self.setPen(QPen(Qt.GlobalColor.green, 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    def update_position(self):
        """Update the door hook position."""
        self.setRect(self.doorhook.position.x - self.hook_size / 2, self.doorhook.position.y - self.hook_size / 2, self.hook_size, self.hook_size)


class LYTControlScheme:
    def __init__(self, editor: LYTEditor):
        self.editor: LYTEditor = editor
        self.settings: LYTEditorSettings = LYTEditorSettings()

    @property
    def pan_camera(self) -> ControlItem:
        return ControlItem(self.settings.moveCameraBind)

    @pan_camera.setter
    def pan_camera(self, value):
        self.settings.moveCameraBind = value

    @property
    def rotate_camera(self) -> ControlItem:
        return ControlItem(self.settings.rotateCameraBind)

    @rotate_camera.setter
    def rotate_camera(self, value):
        self.settings.rotateCameraBind = value

    @property
    def zoom_camera(self) -> ControlItem:
        return ControlItem(self.settings.zoomCameraBind)

    @zoom_camera.setter
    def zoom_camera(self, value):
        self.settings.zoomCameraBind = value

    @property
    def move_selected(self) -> ControlItem:
        return ControlItem(self.settings.moveSelectedBind)

    @move_selected.setter
    def move_selected(self, value):
        self.settings.moveSelectedBind = value

    @property
    def select_underneath(self) -> ControlItem:
        return ControlItem(self.settings.selectUnderneathBind)

    @select_underneath.setter
    def select_underneath(self, value):
        self.settings.selectUnderneathBind = value

    @property
    def delete_selected(self) -> ControlItem:
        return ControlItem(self.settings.deleteSelectedBind)

    @delete_selected.setter
    def delete_selected(self, value):
        self.settings.deleteSelectedBind = value
