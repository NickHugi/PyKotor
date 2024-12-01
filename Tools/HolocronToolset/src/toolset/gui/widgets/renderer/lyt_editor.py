"""LYT Editor widget for editing module layouts."""

from __future__ import annotations

import math
import queue
import threading

from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from queue import Empty
from typing import TYPE_CHECKING, Any, Callable, cast
from uuid import uuid4

import qtpy

from PyQt6.QtCore import QPointF
from qtpy.QtCore import (
    QEvent,
    QLine,
    QLineF,
    QPoint,
    QRect,
    QThread,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QAction, QBrush, QColor, QLinearGradient, QPainter, QPen, QRadialGradient, QTransform
from qtpy.QtWidgets import (
    QApplication,
    QGraphicsItem,
    QGraphicsRectItem,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSlider,
    QToolBar,
    QUndoStack,
    QVBoxLayout,
    QWidget,
)

from pykotor.common.geometry import Vector2, Vector3, Vector4
from pykotor.resource.formats.bwm import BWM, BWMFace
from pykotor.resource.formats.lyt.lyt_data import (
    LYT,
    LYTDoorHook,
    LYTObstacle,
    LYTRoom,
    LYTTrack,
)
from pykotor.resource.generics.gui import GUI
from toolset.gui.widgets.renderer.module import ModuleRenderer
from toolset.gui.widgets.renderer.texture_browser import TextureBrowser
from toolset.uic.qtpy.editors.lyt import Ui_LYTEditor

if TYPE_CHECKING:
    from concurrent.futures import Future

    from qtpy.QtCore import QCoreApplication, QPointF
    from qtpy.QtGui import QCloseEvent, QMouseEvent, QPaintEvent, _QAction
    from qtpy.QtWidgets import _QToolBar

    from pykotor.common.module import MDL, Module, ModuleResource
    from pykotor.gl.scene import TPC, Camera, RenderObject, Scene
    from pykotor.gl.shader import Texture


class LYTEditor(QWidget):
    """Widget for editing LYT (Layout) files."""

    # Signals
    sig_lyt_updated = Signal(LYT)
    sig_walkmesh_updated = Signal(BWM)
    sig_room_moved = Signal(LYTRoom, Vector3)
    sig_room_rotated = Signal(LYTRoom, float)
    sig_room_resized = Signal(LYTRoom, Vector2)
    sig_door_hook_moved = Signal(LYTDoorHook, Vector3)
    sig_obstacle_moved = Signal(LYTObstacle, Vector3)
    sig_track_moved = Signal(LYTTrack, Vector3)
    sig_doorhook_added = Signal(LYTDoorHook)
    sig_rendering_optimized = Signal(bool)
    sig_room_selected = Signal(LYTRoom)
    sig_track_selected = Signal(LYTTrack)
    sig_obstacle_selected = Signal(LYTObstacle)
    sig_doorhook_selected = Signal(LYTDoorHook)
    sig_room_added = Signal(LYTRoom)
    sig_track_added = Signal(LYTTrack)
    sig_obstacle_added = Signal(LYTObstacle)
    sig_doorhook_placed = Signal(LYTDoorHook)
    sig_editing_walkmesh_changed = Signal(bool)
    sig_texture_changed = Signal(str)
    sig_task_completed = Signal(Any)

    def __init__(
        self,
        parent: ModuleRenderer,
    ):
        super().__init__(parent)
        self.ui = Ui_LYTEditor()
        self.ui.setupUi(self)

        # Grid settings
        self._show_grid: bool = True
        self._grid_size: float = 100.0
        self._snap_to_grid: bool = True

        # Initialize locks
        self.vertex_indices: list[int] = []
        self.vertex_coords: list[Vector3] = []
        self.layout_lock: threading.RLock = threading.RLock()
        self.render_lock: threading.RLock = threading.RLock()
        self.texture_lock: threading.RLock = threading.RLock()
        self.change_lock: threading.RLock = threading.RLock()
        self.task_queue_lock: threading.RLock = threading.RLock()
        self.task_consumer_lock: threading.RLock = threading.RLock()

        # Initialize queues and buffers
        self.error_queue: queue.Queue[Exception] = queue.Queue()
        self.task_queue: queue.Queue[Callable[[], Future[Any]]] = queue.Queue()
        self.main_thread_tasks: queue.Queue[Callable[[], Future[Any]]] = queue.Queue()
        self.error_queue: queue.Queue[Exception] = queue.Queue()
        self.change_buffer: list[tuple[str, str, LYTRoom | LYTTrack | LYTObstacle | LYTDoorHook]] = []

        # Initialize process pool
        self.process_pool: ProcessPoolExecutor = ProcessPoolExecutor(max_workers=4)

        # Initialize spatial grid
        self.spatial_grid: dict[int, dict[int, list[LYTRoom]]] = {}
        self.grid_size: int = 100  # Default grid size

        # Initialize state
        self._lyt: LYT = LYT()
        self.scene: Scene = parent.scene
        self.selected_element: Any = None
        self.current_tool: str = "select"
        self.is_shutting_down: bool = False
        self._show_grid: bool = True
        self._snap_to_grid: bool = False
        self.is_editing_walkmesh: bool = False
        self.is_placing_door_hook: bool = False
        self.is_dragging: bool = False
        self.is_resizing: bool = False
        self.is_rotating: bool = False
        self.mouse_pos: Vector2 = Vector2(0, 0)
        self.mouse_prev: Vector2 = Vector2(0, 0)

        # Initialize state
        self._lyt = LYT()
        self.selected_track: LYTTrack | None = None
        self.selected_obstacle: LYTObstacle | None = None
        self.selected_door_hook: LYTDoorHook | None = None
        self.selected_walkmesh_face: BWMFace | None = None
        self.selected_room_resize_corner: int | None = None
        self.selected_room_rotation_point: Vector2 | None = None

        self.undo_stack: QUndoStack = QUndoStack(self)
        self.texture_browser: TextureBrowser = TextureBrowser(self)
        self.textures: dict[str, Texture] = {}
        self.walkmesh: BWM | None = None

        # UI state
        self.is_dragging: bool = False
        self.is_resizing: bool = False
        self.is_rotating: bool = False
        self.is_placing_door_hook: bool = False
        self.is_editing_walkmesh: bool = False
        self._show_grid: bool = True
        self._snap_to_grid: bool = False
        self.grid_size: int = 100

        # Mouse state
        self.mouse_pos: Vector2 = Vector2(0, 0)
        self.mouse_prev: Vector2 = Vector2(0, 0)
        self.mouse_down: set[Qt.MouseButton] = set()

        # Initialize components
        self.undo_stack: QUndoStack = QUndoStack(self)
        self.texture_browser: TextureBrowser = TextureBrowser(self)
        self.walkmesh: BWM | None = None

        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """Initialize the UI layout."""
        layout = QVBoxLayout()

        # Add toolbar
        toolbar = QToolBar()
        layout.addWidget(toolbar)

        # Add buttons
        button_layout = QHBoxLayout()

        add_room_btn = QPushButton("Add Room")
        add_room_btn.clicked.connect(self.add_room)
        button_layout.addWidget(add_room_btn)

        add_track_btn = QPushButton("Add Track")
        add_track_btn.clicked.connect(self.add_track)
        button_layout.addWidget(add_track_btn)

        add_obstacle_btn = QPushButton("Add Obstacle")
        add_obstacle_btn.clicked.connect(self.add_obstacle)
        button_layout.addWidget(add_obstacle_btn)

        add_doorhook_btn = QPushButton("Add Door Hook")
        add_doorhook_btn.clicked.connect(self.add_door_hook)
        button_layout.addWidget(add_doorhook_btn)

        layout.addLayout(button_layout)

        # Add zoom controls
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))

        self.zoom_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.update_zoom)
        zoom_layout.addWidget(self.zoom_slider)

        layout.addLayout(zoom_layout)

        # Add texture list
        self.texture_list = QListWidget()
        self.texture_list.itemClicked.connect(self.on_texture_selected)
        layout.addWidget(self.texture_list)

        self.setLayout(layout)

    def setup_connections(self):
        """Set up signal/slot connections."""
        # Connect texture browser signals
        self.texture_browser.sig_texture_selected.connect(self.on_texture_selected)

        # Connect parent signals
        parent: ModuleRenderer = cast(ModuleRenderer, self.parent())
        parent.sig_scene_initialized.connect(self.update)

    def get_lyt(self) -> LYT:
        """Get the current LYT data."""
        return self._lyt

    def set_lyt(self, lyt: LYT):
        """Set the LYT data to edit."""
        self._lyt = lyt
        self.update()
        self.sig_lyt_updated.emit(lyt)

    def add_track(self, model: str = ""):
        """Add a new track."""
        track = LYTTrack(model=model, position=Vector3(0, 0, 0))
        with self.layout_lock:
            self._lyt.tracks.append(track)
        self.update()
        self.sig_track_added.emit(track)

    def add_door_hook(self):
        """Add a new door hook."""
        if not self._lyt.rooms:
            return

        hook: LYTDoorHook = LYTDoorHook(room=self._lyt.rooms[0].model, door=f"door_{len(self._lyt.doorhooks)}", position=Vector3(0, 0, 0), orientation=Vector4(0, 0, 0, 1))

        with self.layout_lock:
            self._lyt.doorhooks.append(hook)
        self.update()
        self.sig_doorhook_added.emit(hook)

    def paintEvent(self, event: QPaintEvent):
        """Handle paint events."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw grid first
        if self._show_grid:
            self.draw_grid(painter)

        # Draw grid
        if self._show_grid:
            self.draw_grid(painter)

        with self.render_lock:
            # Draw rooms
            for room in self._lyt.rooms:
                self.draw_room(painter, room)

            # Draw tracks
            for track in self._lyt.tracks:
                self.draw_track(painter, track)

            # Draw obstacles
            for obstacle in self._lyt.obstacles:
                self.draw_obstacle(painter, obstacle)

            # Draw doorhooks
            for doorhook in self._lyt.doorhooks:
                self.draw_door_hook(painter, doorhook)

            # Draw selected elements
            if self.selected_room:
                self.draw_room(painter, self.selected_room)
            if self.selected_track:
                self.draw_track(painter, self.selected_track)
            if self.selected_obstacle:
                self.draw_obstacle(painter, self.selected_obstacle)
            if self.selected_door_hook:
                self.draw_door_hook(painter, self.selected_door_hook)

            # Draw walkmesh if editing
            if self.is_editing_walkmesh and self.walkmesh:
                self.draw_walkmesh(painter)

    def draw_grid(
        self,
        painter: QPainter,
    ):
        """Draw the editor grid."""
        pen: QPen = QPen(QColor(128, 128, 128), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)

        for x in range(0, self.width(), self.grid_size):
            painter.drawLine(x, 0, x, self.height())

        for y in range(0, self.height(), self.grid_size):
            painter.drawLine(0, y, self.width(), y)

    def draw_track(
        self,
        painter: QPainter,
        track: LYTTrack,
    ):
        """Draw a track."""
        painter.setPen(QPen(Qt.GlobalColor.red, 2))
        painter.drawLine(int(track.position.x), int(track.position.y), int(track.position.x + 100), int(track.position.y + 100))

    def draw_obstacle(
        self,
        painter: QPainter,
        obstacle: LYTObstacle,
        zoom: float = 1.0,
    ):
        """Draw an obstacle on the scene."""
        center, radius = self.get_obstacle_circle(obstacle, zoom)
        painter.setPen(QPen(Qt.GlobalColor.blue, 2))
        painter.setBrush(QBrush(Qt.GlobalColor.blue, Qt.BrushStyle.DiagCrossPattern))
        painter.drawEllipse(center, int(radius), int(radius))

    def draw_door_hook(
        self,
        painter: QPainter,
        doorhook: LYTDoorHook,
        zoom: float = 1.0,
    ):
        """Draw a door hook on the scene."""
        hook_size: float = 3.0 * zoom
        rect: QRect = QRect(
            int(doorhook.position.x * zoom - hook_size / 2),
            int(doorhook.position.y * zoom - hook_size / 2),
            int(hook_size),
            int(hook_size),
        )
        painter.setPen(QPen(Qt.GlobalColor.green, 2))
        painter.setBrush(QBrush(Qt.GlobalColor.green))
        painter.drawRect(rect)

    def get_room_rect(
        self,
        room: LYTRoom,
    ) -> QRect:
        """Get the rectangle for a room."""
        return QRect(
            int(room.position.x),
            int(room.position.y),
            100,  # Default size
            100,
        )

    def update_zoom(
        self,
        value: int,
    ):
        """Update camera zoom level."""
        if self.scene and hasattr(self.scene, "camera"):
            self.scene.camera.distance = value / 100.0
            self.update()

    def handle_mouse_press(
        self,
        e: QMouseEvent,
    ):
        pos: QPoint = e.pos() if qtpy.QT5 else e.position().toPoint()
        self.mouse_pos: Vector2 = Vector2(pos.x(), pos.y())
        self.mouse_prev: Vector2 = self.mouse_pos
        self.mouse_down: set[Qt.MouseButton] = set()
        self.mouse_down.add(e.button())

        if e.button() == Qt.MouseButton.LeftButton:
            if self.is_placing_door_hook:
                self.place_door_hook(self.mouse_pos)
                self.is_placing_door_hook = False
            else:
                self.select_lyt_element(self.mouse_pos)
                self.is_dragging = True
        elif e.button() == Qt.MouseButton.RightButton:
            if self.selected_room:
                self.selected_room_rotation_point = self.mouse_pos
                self.is_rotating = True
            elif self.selected_track:
                self.is_dragging = True
        elif e.button() == Qt.MouseButton.MiddleButton:
            self.is_dragging = True

    def handle_mouse_release(
        self,
        e: QMouseEvent,
    ):
        self.mouse_down.discard(e.button())
        self.is_dragging = False
        self.is_resizing = False
        self.is_rotating = False
        self.selected_room_resize_corner = None
        self.selected_room_rotation_point = None

    def handle_mouse_move(
        self,
        e: QMouseEvent,
    ):
        pos: QPoint = e.pos() if qtpy.QT5 else e.position().toPoint()
        self.mouse_pos: Vector2 = Vector2(pos.x(), pos.y())

        if self.is_dragging:
            self.drag_lyt_element(self.mouse_pos)
        elif self.is_resizing:
            self.resize_selected_room(self.mouse_pos)
        elif self.is_rotating:
            self.rotate_selected_room(self.mouse_pos)

    def select_lyt_element(
        self,
        mouse_pos: Vector2,
    ):
        # Check for room selection
        for room in self._lyt.rooms:
            rect = QRect(
                int(room.position.x),
                int(room.position.y),
                int(room.size.x),  # FIXME: size attribute does not exist.
                int(room.size.y),  # FIXME: size attribute does not exist.
            )
            if rect.contains(QPoint(int(mouse_pos.x), int(mouse_pos.y))):
                self.selected_room: LYTRoom | None = room
                self.selected_track = None
                self.selected_obstacle = None
                self.selected_door_hook = None
                return

        # Check for track selection
        for track in self._lyt.tracks:
            start = QPoint(int(track.position.x), int(track.position.y))
            end = QPoint(int(track.position.x + 100), int(track.position.y + 100))
            line = QLine(start, end)
            if line.ptDistanceToPoint(QPoint(int(mouse_pos.x), int(mouse_pos.y))) <= 5:
                self.selected_room = None
                self.selected_track: LYTTrack | None = track
                self.selected_obstacle = None
                self.selected_door_hook = None
                return

        # Check for obstacle selection
        for obstacle in self._lyt.obstacles:
            center = QPoint(int(obstacle.position.x), int(obstacle.position.y))
            radius: float = 50  # FIXME: radius attribute does not exist.
            if QPoint(int(mouse_pos.x), int(mouse_pos.y)).distanceToPoint(center) <= radius:  # FIXME: distanceToPoint method does not exist.
                self.selected_room = None
                self.selected_track = None
                self.selected_obstacle: LYTObstacle | None = obstacle
                self.selected_door_hook = None
                return

        # Check for doorhook selection
        for doorhook in self._lyt.doorhooks:
            center = QPoint(int(doorhook.position.x), int(doorhook.position.y))
            if QRect(center.x() - 2, center.y() - 2, 4, 4).contains(QPoint(int(mouse_pos.x), int(mouse_pos.y))):
                self.selected_room: LYTRoom | None = None
                self.selected_track: LYTTrack | None = None
                self.selected_obstacle: LYTObstacle | None = None
                self.selected_door_hook: LYTDoorHook | None = doorhook
                return

        # Deselect if no element is selected
        self.selected_room: LYTRoom | None = None
        self.selected_track: LYTTrack | None = None
        self.selected_obstacle: LYTObstacle | None = None
        self.selected_door_hook: LYTDoorHook | None = None

    def drag_lyt_element(
        self,
        mouse_pos: Vector2,
    ):
        delta: Vector2 = mouse_pos - self.mouse_prev
        self.mouse_prev = mouse_pos

        if self.selected_room:
            self.move_room(self.selected_room, delta)
        elif self.selected_track:
            if Qt.MouseButton.RightButton in self.mouse_down:
                self.move_track_end(self.selected_track, delta)
            else:
                self.move_track_start(self.selected_track, delta)
        elif self.selected_obstacle:
            self.move_obstacle(self.selected_obstacle, delta)
        elif self.selected_door_hook:
            self.move_door_hook(self.selected_door_hook, delta)

        self.update()

    def move_room(
        self,
        room: LYTRoom,
        delta: Vector2,
    ):
        new_position: Vector3 = Vector3(room.position.x + delta.x, room.position.y + delta.y, room.position.z)
        self.sig_room_moved.emit(room, new_position)

    def move_track_start(
        self,
        track: LYTTrack,
        delta: Vector2,
    ):
        new_start: Vector3 = Vector3(track.position.x + delta.x, track.position.y + delta.y, track.position.z)
        self.sig_track_moved.emit(track, new_start)

    def move_track_end(
        self,
        track: LYTTrack,
        delta: Vector2,
    ):
        new_end: Vector3 = Vector3(track.position.x + 100, track.position.y + 100, track.position.z)
        self.sig_track_moved.emit(track, new_end)

    def move_obstacle(
        self,
        obstacle: LYTObstacle,
        delta: Vector2,
    ):
        new_position = Vector3(obstacle.position.x + delta.x, obstacle.position.y + delta.y, obstacle.position.z)
        self.sig_obstacle_moved.emit(obstacle, new_position)

    def move_door_hook(
        self,
        doorhook: LYTDoorHook,
        delta: Vector2,
    ):
        new_position = Vector3(doorhook.position.x + delta.x, doorhook.position.y + delta.y, doorhook.position.z)
        self.sig_door_hook_moved.emit(doorhook, new_position)

    def resize_selected_room(
        self,
        mouse_pos: Vector2,
    ):
        if self.selected_room is None or self.selected_room_resize_corner is None:
            return

        delta: Vector2 = mouse_pos - self.mouse_prev
        self.mouse_prev = mouse_pos

        # Calculate new size based on resize corner
        new_size: Vector2 = Vector2(self.selected_room.size.x, self.selected_room.size.y)  # FIXME: size attribute does not exist.
        if self.selected_room_resize_corner == 0:
            new_size.x += delta.x
            new_size.y += delta.y
        elif self.selected_room_resize_corner == 1:
            new_size.x += delta.x
        elif self.selected_room_resize_corner == 2:  # noqa: PLR2004
            new_size.x += delta.x
            new_size.y -= delta.y
        elif self.selected_room_resize_corner == 3:  # noqa: PLR2004
            new_size.y -= delta.y
        elif self.selected_room_resize_corner == 4:  # noqa: PLR2004
            new_size.y += delta.y
        elif self.selected_room_resize_corner == 5:  # noqa: PLR2004
            new_size.x -= delta.x
            new_size.y += delta.y
        elif self.selected_room_resize_corner == 6:  # noqa: PLR2004
            new_size.x -= delta.x
        elif self.selected_room_resize_corner == 7:  # noqa: PLR2004
            new_size.x -= delta.x
            new_size.y -= delta.y

        # Update room size
        self.sig_room_resized.emit(self.selected_room, new_size)
        self.update()

    def rotate_selected_room(
        self,
        mouse_pos: Vector2,
    ):
        if self.selected_room is None or self.selected_room_rotation_point is None:
            return

        delta: Vector2 = mouse_pos - self.mouse_prev
        self.mouse_prev = mouse_pos

        # Calculate rotation angle
        angle: float = math.degrees(math.atan2(delta.y, delta.x))

        # Update room rotation
        self.sig_room_rotated.emit(self.selected_room, angle)
        self.update()

    def load_textures(self):
        """Load textures from module resources."""
        module = self.parent().scene._module
        if not module:
            return

        # Load textures from module's resources
        textures = module.get_resources("tpc")
        textures.extend(module.get_resources("tga"))

        # Add to texture browser
        for tex_res in textures:
            texture = tex_res.resource()
            self.texture_browser.add_texture(tex_res.resname, texture)

    def load_textures_task(self) -> list[ModuleResource[MDL]]:
        # Implement texture loading logic here
        # This method will be executed in a separate thread
        scene_module: Module | None = self.parent().scene._module  # noqa: SLF001
        assert scene_module is not None
        textures: list[ModuleResource[TPC]] = scene_module.textures()
        with self.texture_lock:
            self.textures = textures
        return textures

    def on_textures_loaded(
        self,
        result: Future,
    ):
        self.udpate_texture_list()

    def udpate_texture_list(self):
        with self.texture_lock:
            self.texturelist.clear()
            for texture_name in self.textures:
                self.texturelist.addItem(QListWidgetItem(texture_name))

    def apply_texture(
        self,
        texture_name: str,
    ):
        self.add_background_task(self.apply_texture_task, (texture_name,))

    def connect_rooms_automatically(self):
        if not self.scene.layout or len(self._lyt.rooms) < 2:
            return

        new_doorhooks: list[LYTDoorHook] = []
        connected_rooms: set[tuple[LYTRoom, LYTRoom]] = set()
        doorhook_groups: dict[tuple[LYTRoom, LYTRoom], list[LYTDoorHook]] = {}

        for i, room1 in enumerate(self._lyt.rooms):
            for room2 in self._lyt.rooms[i + 1 :]:
                if (room1, room2) in connected_rooms or (room2, room1) in connected_rooms:
                    continue

                shared_edge: tuple[str, float, float] | None = self.get_shared_edge(room1, room2)
                if not shared_edge:
                    continue

                new_doorhooks.extend(self.create_door_hooks(room1, room2, shared_edge))
                connected_rooms.append((room1, room2))

        # Remove existing doorhooks that are no longer valid
        valid_doorhooks: list[LYTDoorHook] = []
        for doorhook in self._lyt.doorhooks:
            connected_rooms: list[LYTRoom] = self.get_connected_rooms(doorhook)
            if len(connected_rooms) == 2:
                valid_doorhooks.append(doorhook)
                key = tuple(sorted(connected_rooms, key=lambda r: r.id))  # FIXME: id attribute does not exist.
                if key not in doorhook_groups:
                    doorhook_groups[key] = []
                doorhook_groups[key].append(doorhook)

        # Add new doorhooks
        for doorhook in new_doorhooks:
            connected_rooms = self.get_connected_rooms(doorhook)
            if len(connected_rooms) == 2:
                key = tuple(sorted(connected_rooms, key=lambda r: r.id))  # FIXME: id attribute does not exist.
                if key not in doorhook_groups:
                    doorhook_groups[key] = []
                doorhook_groups[key].append(doorhook)
                valid_doorhooks.append(doorhook)

        # Update the LYT with the new set of doorhooks
        self._lyt.doorhooks = valid_doorhooks

        # Optimize doorhook placement
        for group in doorhook_groups.values():
            if len(group) > 1:
                self.optimize_group_placement(group)

        # Update the spatial partitioning
        self.optimize_rendering()
        # Notify listeners of the update
        self.update()
        self.sig_lyt_updated.emit(self.scene.layout)

    def get_connected_rooms(
        self,
        doorhook: LYTDoorHook,
    ) -> list[LYTRoom]:
        return [room for room in self._lyt.rooms if self.is_door_hook_on_room_edge(doorhook, room)]

    def optimize_group_placement(self, doorhooks: list[LYTDoorHook]):
        if not doorhooks:
            return

        # Sort doorhooks based on their position
        doorhooks.sort(key=lambda dh: (dh.position.x, dh.position.y))

        # Evenly space the doorhooks along the shared edge
        edge_length: float = self.get_edge_length(doorhooks[0], doorhooks[-1])
        spacing: float = edge_length / (len(doorhooks) + 1)  # FIXME: this is unused?

        for i, doorhook in enumerate(doorhooks):
            t: float = (i + 1) / (len(doorhooks) + 1)
            new_pos: Vector3 = self.interpolate_position(doorhooks[0].position, doorhooks[-1].position, t)
            doorhook.position = new_pos

    def get_edge_length(
        self,
        start_hook: LYTDoorHook,
        end_hook: LYTDoorHook,
    ) -> float:
        return ((end_hook.position.x - start_hook.position.x) ** 2 + (end_hook.position.y - start_hook.position.y) ** 2) ** 0.5

    def interpolate_position(
        self,
        start: Vector3,
        end: Vector3,
        t: float,
    ) -> Vector3:
        return Vector3(start.x + (end.x - start.x) * t, start.y + (end.y - start.y) * t, start.z + (end.z - start.z) * t)

    def create_door_hooks(
        self,
        room1: LYTRoom,
        room2: LYTRoom,
        shared_edge: tuple[str, float, float],
    ) -> list[LYTDoorHook]:
        edge_type: str
        start: float
        end: float
        edge_type, start, end = shared_edge
        doorhooks: list[LYTDoorHook] = []

        # Create multiple doorhooks along the shared edge
        num_doors = max(1, int((end - start) / 100))  # One door per 100 units, minimum 1
        for i in range(num_doors):
            t = (i + 0.5) / num_doors  # Position along the edge
            if edge_type == "vertical":
                door_x: float = max(room2.position.x, room1.position.x)
                door_y: float = start + (end - start) * t
            else:  # horizontal
                door_x: float = start + (end - start) * t
                door_y: float = max(room2.position.y, room1.position.y)
            doorhooks.append(
                LYTDoorHook(  # pyright: ignore[reportCallIssue]
                    room=uuid4().hex[:15],
                    door=uuid4().hex[:15],
                    position=Vector3(door_x, door_y, 0),
                    orientation=Vector4(0, 0, 1, 0),
                )
            )  # FIXME: arguments missing for door, room, orientation

        return doorhooks

    def get_shared_edge(
        self,
        room1: LYTRoom,
        room2: LYTRoom,
    ) -> tuple[str, float, float] | None:
        r1_left: float = room1.position.x
        r1_right: float = room1.position.x + room1.size.x  # FIXME: size attribute does not exist.
        r1_top: float = room1.position.y
        r1_bottom: float = room1.position.y + room1.size.y  # FIXME: size attribute does not exist.
        r2_left: float = room2.position.x
        r2_right: float = room2.position.x + room2.size.x  # FIXME: size attribute does not exist.
        r2_top: float = room2.position.y
        r2_bottom: float = room2.position.y + room2.size.y  # FIXME: size attribute does not exist.

        tolerance = 0.001  # Small tolerance for floating-point comparisons

        # Check for vertical adjacency
        if abs(r1_right - r2_left) < tolerance:
            top: float = max(r1_top, r2_top)
            bottom: float = min(r1_bottom, r2_bottom)
            if bottom > top:
                return "vertical", top, bottom
        elif abs(r1_left - r2_right) < tolerance:
            top: float = max(r1_top, r2_top)
            bottom: float = min(r1_bottom, r2_bottom)
            if bottom > top:
                return "vertical", top, bottom

        # Check for horizontal adjacency
        if abs(r1_bottom - r2_top) < tolerance:
            left: float = max(r1_left, r2_left)
            right: float = min(r1_right, r2_right)
            if right > left:
                return "horizontal", left, right
        elif abs(r1_top - r2_bottom) < tolerance:
            left: float = max(r1_left, r2_left)
            right: float = min(r1_right, r2_right)
            if right > left:
                return "horizontal", left, right

        return None

    def is_door_hook_valid(
        self,
        doorhook: LYTDoorHook,
    ) -> bool:
        """Check if the doorhook is on the edge of any room."""
        return any(self.is_door_hook_on_room_edge(doorhook, room) for room in self._lyt.rooms)

    def is_door_hook_on_room_edge(
        self,
        doorhook: LYTDoorHook,
        room: LYTRoom,
    ) -> bool:
        tolerance: float = 0.001
        x: float = doorhook.position.x
        y: float = doorhook.position.y

        # Check if the doorhook is on any of the room's edges
        on_left: bool = abs(x - room.position.x) < tolerance
        on_right: bool = abs(x - (room.position.x + room.size.x)) < tolerance  # FIXME: size attribute does not exist.
        on_top: bool = abs(y - room.position.y) < tolerance
        on_bottom: bool = abs(y - (room.position.y + room.size.y)) < tolerance  # FIXME: size attribute does not exist.

        return (
            ((on_left or on_right) and (room.position.y <= y <= room.position.y + room.size.y))  # FIXME: size attribute does not exist.
            or ((on_top or on_bottom) and (room.position.x <= x <= room.position.x + room.size.x))  # FIXME: size attribute does not exist.
        )

    def optimize_door_hook_placement(self):
        # Group doorhooks by their connecting rooms
        doorhook_groups: dict[tuple[LYTRoom, LYTRoom], list[LYTDoorHook]] = {}
        for doorhook in self._lyt.doorhooks:
            connected_rooms: list[LYTRoom] = self.get_connected_rooms(doorhook)
            if connected_rooms:
                key = tuple(sorted(connected_rooms))  # FIXME: list[LYTRoom]" is incompatible with "Iterable[SupportsRichComparisonT@sorted]
                if key not in doorhook_groups:
                    doorhook_groups[key] = []
                doorhook_groups[key].append(doorhook)

        # Optimize placement for each group
        for group in doorhook_groups.values():
            if len(group) > 1:
                self.optimize_group_placement(group)

    def manual_door_placement(
        self,
        room: LYTRoom,
    ):
        self.is_placing_door_hook = True
        self.selected_room = room

    def snap_to_grid(self, point: Vector2) -> Vector2:
        if self._snap_to_grid:
            return Vector2(
                round(point.x / self.grid_size) * self.grid_size,
                round(point.y / self.grid_size) * self.grid_size,
            )
        return point

    def get_room_resize_corner(
        self,
        mouse_pos: Vector2,
    ) -> int | None:
        if self.selected_room is None:
            return None

        rect = QRect(
            int(self.selected_room.position.x),
            int(self.selected_room.position.y),
            int(self.selected_room.size.x),  # FIXME: size attribute does not exist.
            int(self.selected_room.size.y),  # FIXME: size attribute does not exist.
        )

        handleSize = 8
        for i in range(8):
            x = rect.x() + (i % 2) * rect.width()
            y = rect.y() + (i // 2) * rect.height()
            if QRect(x - handleSize // 2, y - handleSize // 2, handleSize, handleSize).contains(QPoint(int(mouse_pos.x), int(mouse_pos.y))):
                return i

        return None

    def resize_room(self, mouse_pos: Vector2):
        if self.selected_room is None:
            return

        self.selected_room_resize_corner = self.get_room_resize_corner(mouse_pos)
        if self.selected_room_resize_corner is not None:
            self.is_resizing = True
            self.mouse_prev = mouse_pos

    def get_room_rotation_point(
        self,
        mouse_pos: Vector2,
    ) -> Vector2 | None:
        if self.selected_room is None:
            return None

        rect = QRect(
            int(self.selected_room.position.x),
            int(self.selected_room.position.y),
            int(self.selected_room.size.x),  # FIXME: size attribute does not exist.
            int(self.selected_room.size.y),  # FIXME: size attribute does not exist.
        )

        # Check if mouse is within the room
        if rect.contains(QPoint(int(mouse_pos.x), int(mouse_pos.y))):
            return mouse_pos

        return None

    def rotate_room(
        self,
        mouse_pos: Vector2,
    ):
        if self.selected_room is None:
            return

        self.selected_room_rotation_point = self.get_room_rotation_point(mouse_pos)
        if self.selected_room_rotation_point is not None:
            self.is_rotating = True
            self.mouse_prev = mouse_pos

    def set_grid_size(self, grid_size: int):
        self.grid_size = grid_size
        self.update()

    def set_snap_to_grid(self, *, snap_to_grid: bool):
        self._snap_to_grid = snap_to_grid
        self.update()

    def set_show_grid(self, *, show_grid: bool):
        self._show_grid: bool = show_grid
        self.update()

    def edit_walkmesh(self):
        if not self.walkmesh:
            self.generate_walkmesh()

        self.is_editing_walkmesh = True
        self.selected_walkmesh_face = None
        self.update()

    def handle_walkmesh_edit(
        self,
        mouse_pos: Vector2,
    ):
        if not self.is_editing_walkmesh or not self.walkmesh:
            return

        clicked_face: BWMFace | None = self.get_walkmesh_face_at(mouse_pos)

        if clicked_face:
            if self.selected_walkmesh_face == clicked_face:
                # If the same face is clicked again, enter vertex edit mode
                self.edit_walkmesh_vertices(clicked_face)
            else:
                self.selected_walkmesh_face: BWMFace | None = clicked_face
        else:
            self.selected_walkmesh_face = None

        self.update()

    def get_walkmesh_face_at(
        self,
        point: Vector2,
    ) -> BWMFace | None:
        assert self.walkmesh is not None
        for face in self.walkmesh.faces:
            if self.is_point_in_polygon(point, [face.v1, face.v2, face.v3]):
                return face
        return None

    def is_point_in_polygon(
        self,
        point: Vector2,
        vertices: list[Vector3],
    ) -> bool:
        n: int = len(vertices)
        inside: bool = False
        p1x, p1y = vertices[0].x, vertices[0].y
        for i in range(n + 1):
            p2x, p2y = vertices[i % n].x, vertices[i % n].y
            if point.y > min(p1y, p2y) and point.y <= max(p1y, p2y) and point.x <= max(p1x, p2x):
                if p1y != p2y:
                    xinters = (point.y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                if p1x == p2x or point.x <= xinters:
                    inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def edit_walkmesh_vertices(self, face: BWMFace):
        # TODO: Implement vertex editing logic here
        # For example, you could enter a mode where clicking near a vertex allows you to drag it
        pass

    def draw_selected_walkmesh_face(
        self,
        painter: QPainter,
        face: BWMFace,
    ):
        pen = QPen(QColor(255, 0, 0, 200), 2)
        painter.setPen(pen)
        painter.drawPolygon([QPoint(int(v.x), int(v.y)) for v in [face.v1, face.v2, face.v3]])

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events."""
        self.mouse_down.discard(event.button())
        self.is_dragging = False
        self.is_resizing = False
        self.is_rotating = False

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events."""
        pos: QPointF = event.position()
        self.mouse_pos: Vector2 = Vector2(pos.x(), pos.y())

        if self.is_dragging:
            self.handle_drag()
        elif self.is_resizing:
            self.handle_resize()
        elif self.is_rotating:
            self.handle_rotate()

        self.mouse_prev = self.mouse_pos

    def on_texture_selected(self, item: QListWidgetItem):
        texture_name = item.text()
        self.apply_texture(texture_name)
        self.sig_texture_changed.emit(texture_name)

    def apply_texture_task(self, texture_name: str):
        # This method will be executed in a separate thread
        # Implement the logic to apply the texture to the selected element
        with self.layout_lock:
            if self.selected_room:  # FIXME: lytroom does not store textures.
                self.selected_room.texture = texture_name  # FIXME: texture attribute does not exist in a LYTRoom.
            elif self.selected_track:
                self.selected_track.texture = texture_name  # FIXME: texture attribute does not exist in a LYTTrack.

    def on_texture_applied(self, result):
        self.sig_texture_changed.emit(result)
        self.update()

    def optimize_rendering(self):
        # Implement spatial partitioning for efficient rendering of large layouts
        with self.layout_lock:
            if not self.scene.layout or not self._lyt.rooms:
                return

            # Simple grid-based spatial partitioning
            self.spatial_grid.clear()

            for room in self._lyt.rooms:
                grid_x = int(room.position.x / self.grid_size)
                grid_y = int(room.position.y / self.grid_size)
                grid_key: tuple[int, int] = (grid_x, grid_y)
                if grid_key not in self.spatial_grid:
                    self.spatial_grid[grid_key] = []
                self.spatial_grid[grid_key].append(room)

            self.sig_rendering_optimized.emit()

    def get_visible_rooms(self) -> set[LYTRoom]:
        visible_rooms: set[LYTRoom] = set()
        camera: Camera = self.parent().scene.camera
        view_rect: QRect = QRect(int(camera.x - camera.width / 2), int(camera.y - camera.height / 2), int(camera.width), int(camera.height))

        grid_x_start = int(view_rect.left() / self.grid_size)
        grid_x_end = int(view_rect.right() / self.grid_size)
        grid_y_start = int(view_rect.top() / self.grid_size)
        grid_y_end = int(view_rect.bottom() / self.grid_size)

        for x in range(grid_x_start, grid_x_end + 1):
            for y in range(grid_y_start, grid_y_end + 1):
                grid_key: tuple[int, int] = (x, y)
                if grid_key in self.spatial_grid:
                    visible_rooms.update(self.spatial_grid[grid_key])

        return visible_rooms

    def parent(self) -> ModuleRenderer:
        from toolset.gui.widgets.renderer.module import ModuleRenderer

        assert isinstance(self.parent(), ModuleRenderer)
        return self.parent()

    def on_task_completed(
        self,
        task: Callable,
        result: Any,
    ):
        with self.task_consumer_lock:
            self.main_thread_tasks.put((task, result, {}))
            app: QCoreApplication | None = QApplication.instance()
            assert app is not None, "QApplication instance not found?"
            app.postEvent(self, QEvent(QEvent.Type.User))
        self.sig_task_completed.emit(result)

    def process_background_tasks(self):
        if self.is_shutting_down:
            return

        with self.task_queue_lock:
            while not self.task_queue.empty():
                try:
                    task, args, kwargs = self.task_queue.get(block=False)
                except Empty:
                    break

                with self.task_consumer_lock:
                    for consumer in self.task_consumers:
                        try:
                            if not consumer.is_busy():  # FIXME: is_busy method does not exist.
                                consumer.add_task(task, args, kwargs)  # FIXME: add_task method does not exist.
                                break
                            # If all consumers are busy, put the task back in the queue
                            self.task_queue.put((task, args))
                            break
                        except Empty:
                            break
                for consumer in self.task_consumers:
                    try:
                        if not consumer.is_busy():  # FIXME: is_busy method does not exist.
                            consumer.add_task(task, args)  # FIXME: add_task method does not exist.
                            break
                        # If all consumers are busy, put the task back in the queue
                        self.task_queue.put((task, args))
                        break
                    except Empty:
                        break

    def process_main_thread_tasks(self):
        while not self.main_thread_tasks.empty():
            try:
                task, result = self.main_thread_tasks.get(block=False)
                if task == self.load_textures_task:
                    self.on_textures_loaded(result)
                elif task == self.apply_texture_task:
                    self.on_texture_applied(result)
                # Add more task completions as needed
            except Empty:  # noqa: PERF203
                break

        self.process_errors()
        self.process_changes()

    def process_errors(self):
        while not self.error_queue.empty():
            try:
                task, exception = self.error_queue.get(block=False)
                error_message = f"Error in task {task!r}: {exception!s}"
                print(error_message)
                # You can add more robust error handling here, such as logging to a file or showing a dialog
                # self.showErrorDialog(error_message)
                # TODO: Implement more robust error handling here, e.g., showing an error dialog
            except Empty:  # noqa: PERF203
                break

    def process_changes(self):
        """Applies all pending changes to the LYT data and updates the UI."""
        with self.change_lock:
            if self.change_buffer:
                with self.layout_lock:
                    for change in self.change_buffer:
                        # Apply the change to self.scene.layout
                        action, element_type, data = change
                        if action == "add":
                            if element_type == "room" and isinstance(data, LYTRoom):
                                self._lyt.rooms.append(data)
                            elif element_type == "track" and isinstance(data, LYTTrack):
                                self._lyt.tracks.append(data)
                            elif element_type == "obstacle" and isinstance(data, LYTObstacle):
                                self._lyt.obstacles.append(data)
                            elif element_type == "doorhook" and isinstance(data, LYTDoorHook):
                                self._lyt.doorhooks.append(data)
                        elif action == "update":
                            # Implement update logic for each element type
                            pass
                        elif action == "delete":
                            if element_type == "room" and isinstance(data, LYTRoom):
                                self._lyt.rooms.remove(data)
                            elif element_type == "track" and isinstance(data, LYTTrack):
                                self._lyt.tracks.remove(data)
                            elif element_type == "obstacle" and isinstance(data, LYTObstacle):
                                self._lyt.obstacles.remove(data)
                            elif element_type == "doorhook" and isinstance(data, LYTDoorHook):
                                self._lyt.doorhooks.remove(data)
                self.sig_lyt_updated.emit(self.scene.layout)
                self.change_buffer.clear()
            self.update()

    def update_lyt(self):
        with self.layout_lock, self.render_lock:
            lyt_copy: LYT | None = deepcopy(self.scene.layout)
            assert lyt_copy is not None
            self.sig_lyt_updated.emit(lyt_copy)
        self.update()

    def draw_grid(
        self,
        painter: QPainter,
    ):
        """Draw the editor grid."""
        pen: QPen = QPen(QColor(128, 128, 128), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)

        # Draw vertical lines
        for x in range(0, self.width(), int(self._grid_size)):
            painter.drawLine(x, 0, x, self.height())

        # Draw horizontal lines  
        for y in range(0, self.height(), int(self._grid_size)):
            painter.drawLine(0, y, self.width(), y)

    def snap_to_grid(
        self,
        point: Vector2,
    ) -> Vector2:
        """Snap a point to the grid."""
        if not self._snap_to_grid:
            return point
            
        return Vector2(
            round(point.x / self._grid_size) * self._grid_size,
            round(point.y / self._grid_size) * self._grid_size
        )

    def toggle_grid(
        self,
        state: bool,
    ):
        """Toggle grid visibility."""
        self._show_grid = state
        self.update()

    def toggle_snap(
        self,
        state: bool,
    ):
        """Toggle snap-to-grid functionality."""
        self._snap_to_grid = state

    def set_grid_size(
        self,
        size: int,
    ):
        """Set the grid size."""
        self._grid_size = float(size)
        self.update()

    def draw_room(
        self,
        painter: QPainter,
        room: LYTRoom,
        zoom: float = 1.0,
    ):
        """Draw a room with connection points and visual feedback."""
        try:
            # Get module and model data
            module = self.parent().scene._module
            if not module:
                return

            mdl_res = module.get_resource(room.model, "mdl")
            if not mdl_res:
                return

            # Snap position if enabled
            position = room.position
            if self._snap_to_grid:
                snapped = self.snap_to_grid(Vector2(position.x, position.y))
                position = Vector3(snapped.x, snapped.y, position.z)

            mdl = mdl_res.resource()

            # Get room bounds from MDL
            bounds = mdl.get_bounding_box()
            size = bounds.size

            position = room.position
            orientation = room.orientation

            rect = QRect(
                int(position.x * zoom),
                int(position.y * zoom),
                int(size.x * zoom),
                int(size.y * zoom)
            )

            # Draw selection highlight if this is the selected room
            if room == self.selected_room:
                # Draw resize handles
                handle_size = 8 * zoom
                handles = [
                    (rect.topLeft(), "nw-resize"),
                    (rect.topRight(), "ne-resize"),
                    (rect.bottomLeft(), "sw-resize"),
                    (rect.bottomRight(), "se-resize"),
                    (QPoint(rect.center().x(), rect.top()), "n-resize"),
                    (QPoint(rect.center().x(), rect.bottom()), "s-resize"),
                    (QPoint(rect.left(), rect.center().y()), "w-resize"),
                    (QPoint(rect.right(), rect.center().y()), "e-resize")
                ]

                for handle_pos, cursor in handles:
                    handle_rect = QRect(
                        handle_pos.x() - handle_size//2,
                        handle_pos.y() - handle_size//2,
                        handle_size,
                        handle_size
                    )
                    painter.setPen(QPen(Qt.GlobalColor.yellow))
                    painter.setBrush(QBrush(Qt.GlobalColor.white))
                    painter.drawRect(handle_rect)

                # Draw rotation handle
                rotation_handle_pos = QPoint(
                    rect.center().x(),
                    rect.top() - 20 * zoom
                )
                painter.setPen(QPen(Qt.GlobalColor.blue, 2))
                painter.drawLine(rect.center(), rotation_handle_pos)
                painter.setBrush(QBrush(Qt.GlobalColor.blue))
                painter.drawEllipse(
                    rotation_handle_pos.x() - handle_size//2,
                    rotation_handle_pos.y() - handle_size//2,
                    handle_size,
                    handle_size
                )

                # Draw selection outline
                painter.setPen(QPen(QColor(255, 255, 0), 2, Qt.PenStyle.DashLine))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(rect.adjusted(-2, -2, 2, 2))

            # Draw main room rectangle with gradient
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            if room == self.selected_room:
                gradient.setColorAt(0, QColor(180, 200, 255, 180))
                gradient.setColorAt(1, QColor(140, 170, 255, 180))
                painter.setPen(QPen(Qt.GlobalColor.blue, 2))
            else:
                gradient.setColorAt(0, QColor(220, 220, 220, 180))
                gradient.setColorAt(1, QColor(200, 200, 200, 180))
                painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.setBrush(QBrush(gradient))

            # Apply rotation if needed
            if orientation.z != 0:
                painter.save()
                painter.translate(rect.center())
                painter.rotate(math.degrees(orientation.z))
                painter.translate(-rect.center())
                painter.drawRect(rect)
                painter.restore()
            else:
                painter.drawRect(rect)

            # Draw connection points with improved visualization
            connection_points = self.get_room_connection_points(room)
            for point, is_valid in connection_points:
                # Draw connection point glow
                if is_valid:
                    glow_size = 16 * zoom
                    glow_gradient = QRadialGradient(
                        point.x() * zoom,
                        point.y() * zoom,
                        glow_size
                    )
                    glow_gradient.setColorAt(0, QColor(0, 255, 0, 100))
                    glow_gradient.setColorAt(1, QColor(0, 255, 0, 0))
                    painter.setBrush(QBrush(glow_gradient))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(
                        int((point.x - glow_size/2) * zoom),
                        int((point.y - glow_size/2) * zoom),
                        int(glow_size),
                        int(glow_size)
                    )

                # Draw connection point
                point_color = QColor(0, 255, 0) if is_valid else QColor(128, 128, 128)
                point_size = 8 * zoom
                painter.setPen(QPen(point_color, 2))
                painter.setBrush(QBrush(point_color.lighter(120)))
                painter.drawEllipse(
                    int((point.x - point_size/2) * zoom),
                    int((point.y - point_size/2) * zoom),
                    int(point_size),
                    int(point_size)
                )

            # Draw room info with shadow
            text = f"{room.model}\n{int(size.x)}x{int(size.y)}"
            painter.setPen(QColor(0, 0, 0, 100))
            painter.drawText(rect.adjusted(1, 1, 1, 1), Qt.AlignmentFlag.AlignCenter, text)
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

        except Exception as e:
            print(f"Error drawing room: {e}")

    def update_room_property(
        self,
        property_name: str,
        value: Any,
    ):
        """Update a room property and emit appropriate signals."""
        if not self.selected_room:
            return

        if property_name == "position":
            old_pos: Vector3 = self.selected_room.position
            self.selected_room.position = value
            self.sig_room_moved.emit(self.selected_room, value - old_pos)

        self.update()

    def handle_task_exception(
        self,
        task: Callable,
        exception: Exception,
    ):
        with self.task_consumer_lock:
            self.error_queue.put((task, exception))
            qApp: QCoreApplication | None = QApplication.instance()
            assert qApp is not None, "QApplication instance not found?"
            qApp.postEvent(self, QEvent(QEvent.Type.User))

    def add_background_task(
        self,
        task: Callable,
        args: tuple,
    ):
        with self.task_queue_lock:
            self.task_queue.put((task, args, {}))
            qApp: QCoreApplication | None = QApplication.instance()
            assert qApp is not None, "QApplication instance not found?"
            qApp.postEvent(self, QEvent(QEvent.Type.User))  # Trigger event processing

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.User:
            self.process_main_thread_tasks()
            self.process_background_tasks()
            self.process_changes()
            return True
        return super().event(event)

    def add_change(
        self,
        change: tuple[str, str, LYTRoom | LYTTrack | LYTObstacle | LYTDoorHook],
    ):
        with self.change_lock:
            self.change_buffer.append(change)
            app: QCoreApplication | None = QApplication.instance()
            assert app is not None, "QApplication instance not found?"
            app.postEvent(self, QEvent(QEvent.Type.User))  # Trigger event processing

    def show_error_dialog(
        self,
        message: str,
    ):
        # Implement this method to show an error dialog to the user
        qApp: QCoreApplication | None = QApplication.instance()
        if qApp is not None and qApp.thread() == QThread.currentThread():
            QMessageBox.critical(self, "Error", message)

    def get_selected_room(self) -> LYTRoom | None:
        """Get the currently selected room."""
        return self.selected_room if hasattr(self, "selected_room") else None

    def get_selected_item(self) -> Any:
        """Get the currently selected item."""
        return (self.selected_room or
                self.selected_track or
                self.selected_obstacle or
                self.selected_door_hook)

    def update_room(
        self,
        room: LYTRoom,
    ):
        self.add_change(("update", "room", room))

    def delete_room(
        self,
        room: LYTRoom,
    ):
        self.add_change(("delete", "room", room))

    def select_room(
        self,
        room: LYTRoom,
    ):
        self.selected_room = room
        self.update()

    def duplicate_room(
        self,
        room: LYTRoom,
    ) -> LYTRoom:
        new_room: LYTRoom = deepcopy(room)
        self._lyt.rooms.append(new_room)
        self.update()
        return new_room

    def duplicate_selected_room(self) -> LYTRoom | None:
        if self.selected_room:
            return self.duplicate_room(self.selected_room)
        return None

    def get_obstacle_circle(
        self,
        obstacle: LYTObstacle,
        zoom: float = 1.0,
    ) -> tuple[QPoint, float]:
        """Get the center point and radius for an obstacle."""
        # Default radius if not specified
        default_radius: float = 5.0
        radius: float = getattr(obstacle, "radius", default_radius)

        center: QPoint = QPoint(int(obstacle.position.x * zoom), int(obstacle.position.y * zoom))
        return center, radius * zoom

    def initUI(self):
        """Initialize the UI layout."""
        self.setAcceptDrops(True)

        layout = QVBoxLayout()
        
        # Add grid controls
        grid_controls = QHBoxLayout()
        
        self.show_grid_cb = QCheckBox("Show Grid")
        self.show_grid_cb.setChecked(self._show_grid)
        self.show_grid_cb.stateChanged.connect(self.toggle_grid)
        grid_controls.addWidget(self.show_grid_cb)
        
        self.snap_grid_cb = QCheckBox("Snap to Grid") 
        self.snap_grid_cb.setChecked(self._snap_to_grid)
        self.snap_grid_cb.stateChanged.connect(self.toggle_snap)
        grid_controls.addWidget(self.snap_grid_cb)
        
        self.grid_size_spin = QSpinBox()
        self.grid_size_spin.setRange(10, 1000)
        self.grid_size_spin.setValue(int(self._grid_size))
        self.grid_size_spin.valueChanged.connect(self.set_grid_size)
        grid_controls.addWidget(QLabel("Grid Size:"))
        grid_controls.addWidget(self.grid_size_spin)
        
        layout.addLayout(grid_controls)

        # Add buttons for LYT editing operations
        button_layout: QHBoxLayout = QHBoxLayout()
        add_room_button: QPushButton = QPushButton("Add Room")
        add_room_button.clicked.connect(self.add_room)
        button_layout.addWidget(add_room_button)

        add_track_button: QPushButton = QPushButton("Add Track")
        add_track_button.clicked.connect(self.add_track)
        button_layout.addWidget(add_track_button)

        add_obstacle_button: QPushButton = QPushButton("Add Obstacle")
        add_obstacle_button.clicked.connect(self.add_obstacle)
        button_layout.addWidget(add_obstacle_button)

        place_door_hook_button: QPushButton = QPushButton("Place Door Hook")
        place_door_hook_button.clicked.connect(self.place_door_hook)
        button_layout.addWidget(place_door_hook_button)
        layout.addLayout(button_layout)

        # Add zoom slider
        zoom_layout: QHBoxLayout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.update_zoom)
        zoom_layout.addWidget(self.zoom_slider)
        layout.addLayout(zoom_layout)

        # Add texture browser
        self.texturelist: QListWidget = QListWidget()
        self.texturelist.itemClicked.connect(self.on_texture_selected)
        layout.addWidget(self.texturelist)

        self.setLayout(layout)

        layout: QVBoxLayout = QVBoxLayout()

        # Add buttons for LYT editing operations
        button_layout: QHBoxLayout = QHBoxLayout()
        add_room_button: QPushButton = QPushButton("Add Room")
        add_room_button.clicked.connect(self.add_room)
        button_layout.addWidget(add_room_button)

        add_track_button: QPushButton = QPushButton("Add Track")
        add_track_button.clicked.connect(self.add_track)
        button_layout.addWidget(add_track_button)

        add_obstacle_button: QPushButton = QPushButton("Add Obstacle")
        add_obstacle_button.clicked.connect(self.add_obstacle)
        button_layout.addWidget(add_obstacle_button)

        place_door_hook_button: QPushButton = QPushButton("Place Door Hook")
        place_door_hook_button.clicked.connect(self.place_door_hook)
        button_layout.addWidget(place_door_hook_button)
        layout.addLayout(button_layout)

        # Add zoom slider
        zoom_layout: QHBoxLayout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.update_zoom)
        zoom_layout.addWidget(self.zoom_slider)
        layout.addLayout(zoom_layout)

        # Add texture browser
        self.texturelist: QListWidget = QListWidget()
        self.texturelist.itemClicked.connect(self.on_texture_selected)
        layout.addWidget(self.texturelist)

        self.setLayout(layout)

    def set_current_tool(self, tool: str):
        """Set the current editing tool."""
        self.current_tool = tool
        self.update_cursor()
        self.update_ui_state()

    def update_cursor(self):
        """Update cursor based on current tool."""
        cursor_map = {
            "select": Qt.CursorShape.ArrowCursor,
            "move": Qt.CursorShape.SizeAllCursor,
            "rotate": Qt.CursorShape.CrossCursor,
            "scale": Qt.CursorShape.SizeFDiagCursor
        }
        self.setCursor(cursor_map.get(self.current_tool, Qt.CursorShape.ArrowCursor))

    def update_ui_state(self):
        """Update UI elements based on current tool."""
        self.update()
        if hasattr(self, "tool_group"):
            for action in self.tool_group.actions():
                action.setChecked(action.text().lower() == self.current_tool)

    def mousePressEvent(
        self,
        event: QMouseEvent,
    ):
        """Handle mouse press events."""
        try:
            # Use Scene's pick method with error handling
            picked_object: RenderObject | None = self.scene.pick(event.pos().x(), event.pos().y())
            if picked_object and hasattr(picked_object, "data"):
                self.selected_element = picked_object.data
                self.update_element_properties()
        except Exception as e:  # noqa: BLE001
            print(f"Error in mouse press: {e}")
            # Fallback to default selection behavior
            super().mousePressEvent(event)

        pos: QPointF = event.position()
        self.mouse_pos: Vector2 = Vector2(pos.x(), pos.y())
        self.mouse_prev: Vector2 = self.mouse_pos
        self.mouse_down.add(event.button())

        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_placing_door_hook:
                self.place_door_hook(self.mouse_pos)
                self.is_placing_door_hook = False
            else:
                self.select_lyt_element(self.mouse_pos)
                self.is_dragging = True

        elif event.button() == Qt.MouseButton.RightButton:
            if self.selected_room:
                self.is_rotating = True
            elif self.selected_track:
                self.is_dragging = True

        elif event.button() == Qt.MouseButton.MiddleButton:
            self.is_dragging = True

    def add_room(
        self,
        model: str = "",
        position: Vector3 | None = None,
    ):
        """Add a new room."""
        # Get module and area data
        module = self.parent().scene._module
        if not module:
            return

        area = module.get_area()
        if not area:
            return

        # Load model to get dimensions
        mdl_res = module.get_resource(model, "mdl")
        if not mdl_res:
            return

        mdl = mdl_res.resource()

        # Create room with data from MDL/ARE
        room: LYTRoom = LYTRoom(
            model=model,
            position=position or Vector3(0, 0, 0),
            orientation=Vector4(0, 0, 0, 1)
        )
        room.id = str(uuid4())  # Add unique ID

        # Snap to grid if enabled
        if self._snap_to_grid:
            room.position.x = round(room.position.x / self.grid_size) * self.grid_size
            room.position.y = round(room.position.y / self.grid_size) * self.grid_size

        # Find valid connection points with existing rooms
        self.highlight_connection_points(room)

        with self.layout_lock:
            self._lyt.rooms.append(room)

        self.update()
        self.sig_room_added.emit(room)
        return room

    def add_obstacle(
        self,
        model: str = "",
    ):
        """Add a new obstacle."""
        obstacle: LYTObstacle = LYTObstacle(model=model, position=Vector3(0, 0, 0))
        with self.layout_lock:
            self._lyt.obstacles.append(obstacle)
        self.update()
        self.sig_obstacle_added.emit(obstacle)

    def update_track(
        self,
        track: LYTTrack,
    ):
        self.add_change(("update", "track", track))

    def delete_track(
        self,
        track: LYTTrack,
    ):
        self.add_change(("delete", "track", track))

    def create_door_hook(
        self,
        position: Vector3,
        room: LYTRoom,
    ) -> LYTDoorHook:
        """Create a new door hook with proper initialization."""
        return LYTDoorHook(
            room=room.model,
            door="",  # Empty string as default door name
            position=position,
            orientation=Vector4(0, 0, 0, 1),  # Default orientation as quaternion
        )

    def distance_to_line(
        self,
        point: QPoint,
        start: QPoint,
        end: QPoint,
    ) -> float:
        """Calculate the distance from a point to a line segment."""
        line: QLineF = QLineF(start, end)
        return line.pointDistance(point)

    def distance_to_point(
        self,
        point1: QPoint,
        point2: QPoint,
    ) -> float:
        """Calculate the distance between two points."""
        return math.sqrt((point1.x() - point2.x()) ** 2 + (point1.y() - point2.y()) ** 2)

    def handle_room_selection(self, pos: QPointF):
        """Handle room selection at given position."""
        item: QGraphicsItem | None = self.scene.itemAt(pos, QTransform())
        if isinstance(item, QGraphicsRectItem) and hasattr(item, "room"):
            self.selected_room: LYTRoom = item.data(Qt.ItemDataRole.UserRole)
            self.sig_room_selected.emit(item.data(Qt.ItemDataRole.UserRole))
            self.update_selection()

    def update_room_position(
        self,
        room: LYTRoom,
        delta: Vector3,
    ):
        """Update room position and notify listeners."""
        room.position += delta
        self.update_scene()
        self.sig_room_moved.emit(room, delta)

    def update_room_rotation(self, room: LYTRoom, angle: float):
        """Update room rotation and notify listeners."""
        # Convert angle to quaternion
        half_angle: float = angle / 2.0
        self.update_scene()
        self.sig_room_rotated.emit(room, angle)

    def get_room_center(
        self,
        room: LYTRoom,
    ) -> Vector3:
        """Get the center position of a room."""
        size: Vector3 = getattr(room, "size", Vector3(10, 10, 0))
        return room.position + Vector3(size.x / 2, size.y / 2, 0)

    def highlight_selected_room(self):
        """Highlight the currently selected room."""
        if not self.selected_room:
            return

        # Find the room's graphics item
        for item in self.scene.items():
            if isinstance(item, QGraphicsRectItem) and item.data(Qt.ItemDataRole.UserRole) == self.selected_room:
                # Create highlight effect
                highlight: QGraphicsRectItem = self.addRect(item.rect())
                highlight.setPos(item.pos())
                highlight.setPen(QPen(Qt.GlobalColor.yellow, 2, Qt.PenStyle.DashLine))
                highlight.setZValue(item.zValue() + 1)

    def create_room_graphics(
        self,
        room: LYTRoom,
    ) -> QGraphicsRectItem:
        """Create graphics item for a room."""
        size: Vector3 = getattr(room, "size", Vector3(10, 10, 0))
        item: QGraphicsRectItem = QGraphicsRectItem(0, 0, size.x, size.y)
        item.setPos(room.position.x, room.position.y)
        item.setPen(QPen(Qt.GlobalColor.black, 2))
        item.setBrush(QBrush(Qt.GlobalColor.lightGray))
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        item.setData(Qt.ItemDataRole.UserRole, room)  # Store reference to room
        return item

    def update_room_graphics(
        self,
        room: LYTRoom,
    ):
        """Update graphics for a room."""
        # Find and update existing room item
        for item in self.scene.items():
            if isinstance(item, QGraphicsRectItem) and item.data(Qt.ItemDataRole.UserRole) == room:
                size: Vector3 = getattr(room, "size", Vector3(10, 10, 0))
                item.setRect(0, 0, size.x, size.y)
                item.setPos(room.position.x, room.position.y)
                break

    def update_element_properties(self):
        # Remove detailed property editing since UI lacks specific spin boxes
        if isinstance(self.selected_element, LYTRoom):
            # Update rooms list instead of detailed editing
            self.ui.roomsList.clear()
            for room in self._lyt.rooms:
                self.ui.roomsList.addItem(room.model)
        elif isinstance(self.selected_element, LYTObstacle):
            # Update obstacles list
            self.ui.obstaclesList.clear()
            for obstacle in self._lyt.obstacles:
                self.ui.obstaclesList.addItem(f"Obstacle at {obstacle.position}")
        elif isinstance(self.selected_element, LYTDoorHook):
            # Update doorhooks list
            self.ui.doorhooksList.clear()
            for doorhook in self._lyt.doorhooks:
                self.ui.doorhooksList.addItem(f"Door Hook at {doorhook.position}")
        elif isinstance(self.selected_element, LYTTrack):
            # Update tracks list
            self.ui.tracksList.clear()
            for track in self._lyt.tracks:
                self.ui.tracksList.addItem(f"Track from {track.start_room.model if track.start_room else 'Unknown'}")

    def init_connections(self):
        """Initialize UI connections."""
        # Connect list selection methods
        self.ui.roomsList.itemClicked.connect(self.on_room_selected)
        self.ui.obstaclesList.itemClicked.connect(self.on_obstacle_selected)
        self.ui.doorhooksList.itemClicked.connect(self.on_doorhook_selected)
        self.ui.tracksList.itemClicked.connect(self.on_track_selected)

        # Connect buttons
        self.ui.addRoomButton.clicked.connect(self.add_room)
        self.ui.addTrackButton.clicked.connect(self.add_track)
        self.ui.addObstacleButton.clicked.connect(self.add_obstacle)
        self.ui.addDoorHookButton.clicked.connect(self.add_door_hook)

        # Connect texture browser
        self.ui.textureBrowser.itemClicked.connect(self.on_texture_selected)

        # Connect zoom slider
        self.ui.zoomSlider.valueChanged.connect(self.update_zoom)

        # Add tool buttons to toolbar
        toolbar: _QToolBar = QToolBar()

        select_action: _QAction = QAction("Select", self)
        select_action.setCheckable(True)
        select_action.setChecked(True)
        select_action.triggered.connect(lambda: self.set_current_tool("select"))
        toolbar.addAction(select_action)

        move_action: _QAction = QAction("Move", self)
        move_action.setCheckable(True)
        move_action.triggered.connect(lambda: self.set_current_tool("move"))
        toolbar.addAction(move_action)

        rotate_action: _QAction = QAction("Rotate", self)
        rotate_action.setCheckable(True)
        rotate_action.triggered.connect(lambda: self.set_current_tool("rotate"))
        toolbar.addAction(rotate_action)

        # Add toolbar to layout
        self.ui.verticalLayout.insertWidget(0, toolbar)

    def on_room_selected(self, item: QListWidgetItem):
        """Handle room selection from list."""
        room = item.data(Qt.ItemDataRole.UserRole)
        if room:
            self.selected_element = room
            self.update_element_properties()

    def on_obstacle_selected(self, item: QListWidgetItem):
        """Handle obstacle selection from list."""
        obstacle = item.data(Qt.ItemDataRole.UserRole)
        if obstacle:
            self.selected_element = obstacle
            self.update_element_properties()

    def on_doorhook_selected(self, item: QListWidgetItem):
        """Handle door hook selection from list."""
        doorhook = item.data(Qt.ItemDataRole.UserRole)
        if doorhook:
            self.selected_element = doorhook
            self.update_element_properties()

    def on_track_selected(self, item: QListWidgetItem):
        """Handle track selection from list."""
        track = item.data(Qt.ItemDataRole.UserRole)
        if track:
            self.selected_element = track
            self.update_element_properties()

    def generate_walkmesh(self):
        """Generate walkmesh with proper error handling."""
        try:
            if not self._lyt or not self._lyt.rooms:
                return

            self.walkmesh = BWM()
            faces: list[BWMFace] = []

            for room in self._lyt.rooms:
                # Get room properties with safe defaults
                position: Vector3 = getattr(room, "position", Vector3(0, 0, 0))
                size: Vector3 = getattr(room, "size", Vector3(10, 10, 0))

                vertices: list[Vector3] = [
                    Vector3(position.x, position.y, 0),
                    Vector3(position.x + size.x, position.y, 0),
                    Vector3(position.x + size.x, position.y + size.y, 0),
                    Vector3(position.x, position.y + size.y, 0),
                ]

                face = BWMFace(v1=vertices[0], v2=vertices[1], v3=vertices[2])
                faces.append(face)

            self.walkmesh.faces = faces
            self.sig_walkmesh_updated.emit(self.walkmesh)
            self.update()

        except Exception as e:  # noqa: BLE001
            print(f"Error generating walkmesh: {e}")

    def place_door_hook(self, mouse_pos: Vector2):
        """Place a door hook with proper initialization."""
        room = self.selected_room
        if room is None:
            return

        tolerance = 5  # pixels

        # Check if mouse is on room edge
        if (
            abs(mouse_pos.x - room.position.x) < tolerance
            or abs(mouse_pos.x - (room.position.x + getattr(room, "size", Vector3(10, 10, 0)).x)) < tolerance
            or abs(mouse_pos.y - room.position.y) < tolerance
            or abs(mouse_pos.y - (room.position.y + getattr(room, "size", Vector3(10, 10, 0)).y)) < tolerance
        ):
            # Create doorhook with proper initialization
            doorhook = LYTDoorHook(room=room.model, door=f"door_{len(self._lyt.doorhooks)}", position=Vector3(mouse_pos.x, mouse_pos.y, 0), orientation=Vector4(0, 0, 0, 1))

            self._lyt.doorhooks.append(doorhook)
            self.sig_doorhook_added.emit(doorhook)
            self.update()

    def closeEvent(
        self,
        event: QCloseEvent,
    ):
        """Clean up resources on close."""
        self.is_shutting_down = True
        if hasattr(self, "process_pool"):
            self.process_pool.shutdown()
        super().closeEvent(event)

    def load_lyt(self, lyt):
        # Load the LYT data into the editor
        self.lyt = lyt
        self.render_lyt()

    def render_lyt(self):
        # Render the LYT elements for editing
        pass

    def remove_room(self, room):
        # Remove a room from the LYT
        pass
