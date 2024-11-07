from __future__ import annotations

import json
import math
import queue

from copy import deepcopy
from queue import Empty
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Optional
from uuid import uuid4

from qtpy.QtCore import (
    QEvent,
    QLine,
    QMutexLocker,
    QPoint,
    QRect,
    QThread,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QBrush, QColor, QPainter, QPen
from qtpy.QtWidgets import QApplication, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSlider, QUndoStack, QVBoxLayout, QWidget
from qtpy.uic import loadUi

from pykotor.common.geometry import Vector2, Vector3, Vector4
from pykotor.common.module import ModuleResource
from pykotor.resource.formats.bwm import BWM, BWMFace
from pykotor.resource.formats.lyt import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack
from pykotor.resource.formats.mdl.mdl_data import MDL
from toolset.gui.widgets.renderer.texture_browser import TextureBrowser
from toolset.gui.widgets.renderer.walkmesh_editor import AddRoomCommand, MoveRoomCommand, RotateRoomCommand

if TYPE_CHECKING:
    from qtpy.QtCore import QMimeData
    from qtpy.QtGui import QDragEnterEvent, QDropEvent, QKeyEvent, QMouseEvent

    from pykotor.common.module import ModuleResource
    from pykotor.gl.scene import Scene
    from pykotor.resource.formats.mdl.mdl_data import MDL
    from toolset.gui.widgets.renderer.module import ModuleRenderer


class LYTEditor(QWidget):
    sig_lyt_updated: ClassVar[Signal] = Signal(LYT)
    sig_walkmesh_updated: ClassVar[Signal] = Signal(BWM)

    def __init__(self, parent: ModuleRenderer):
        super().__init__(parent)
        self.ui = loadUi("Tools/HolocronToolset/src/ui/widgets/renderer/lyt_editor.ui", self)

        self._lyt: LYT = LYT()
        self.scene: Scene = parent.scene
        self.selected_element: Optional[Any] = None
        self.current_tool: str = "select"

        self.undo_stack: QUndoStack = QUndoStack(self)

        self.texture_browser: TextureBrowser = TextureBrowser(self)
        self.textures: dict[str, str] = {}

        self.walkmesh: BWM | None = None

        self.init_connections()

    def init_connections(self):
        self.ui.actionAddRoom.triggered.connect(self.add_room)
        self.ui.actionAddTrack.triggered.connect(self.add_track)
        self.ui.actionAddObstacle.triggered.connect(self.add_obstacle)
        self.ui.actionAddDoorHook.triggered.connect(self.add_door_hook)
        self.ui.actionSelect.triggered.connect(lambda: self.set_current_tool("select"))
        self.ui.actionMove.triggered.connect(lambda: self.set_current_tool("move"))
        self.ui.actionRotate.triggered.connect(lambda: self.set_current_tool("rotate"))

    def init_connections(self):
        self.ui.actionAddRoom.triggered.connect(self.add_room)
        self.ui.actionAddTrack.triggered.connect(self.add_track)
        self.ui.actionAddObstacle.triggered.connect(self.add_obstacle)
        self.ui.actionAddDoorHook.triggered.connect(self.add_door_hook)
        self.ui.actionSelect.triggered.connect(lambda: self.set_current_tool("select"))
        self.ui.actionMove.triggered.connect(lambda: self.set_current_tool("move"))
        self.ui.actionRotate.triggered.connect(lambda: self.set_current_tool("rotate"))

    def set_lyt(self, lyt: LYT):
        self._lyt = lyt
        self.scene.set_lyt(lyt)
        self.sig_lyt_updated.emit(self._lyt)

    def get_lyt(self) -> LYT:
        return self._lyt

    def set_current_tool(self, tool: str):
        self.current_tool = tool

    def add_room(self):
        room = LYTRoom()
        room.position = Vector3(0, 0, 0)
        command = AddRoomCommand(self, room)
        self.undo_stack.push(command)

    def add_track(self):
        if len(self._lyt.rooms) < 2:
            return
        track = LYTTrack()
        track.start_room = self._lyt.rooms[0]
        track.end_room = self._lyt.rooms[1]
        self._lyt.tracks.append(track)
        self.scene.add_lyt_track(track)
        self.sig_lyt_updated.emit(self._lyt)

    def add_obstacle(self):
        obstacle = LYTObstacle()
        obstacle.position = Vector3(0, 0, 0)
        self._lyt.obstacles.append(obstacle)
        self.scene.add_lyt_obstacle(obstacle)
        self.sig_lyt_updated.emit(self._lyt)

    def add_door_hook(self):
        if not self._lyt.rooms:
            return
        doorhook = LYTDoorHook()
        doorhook.room = self._lyt.rooms[0]
        doorhook.position = Vector3(0, 0, 0)
        self._lyt.doorhooks.append(doorhook)
        self.scene.add_lyt_door_hook(doorhook)
        self.sig_lyt_updated.emit(self._lyt)

    def update_element_properties(self):
        if isinstance(self.selected_element, LYTRoom):
            self.ui.roomModelEdit.setText(self.selected_element.model)
            self.ui.roomPosXSpin.setValue(self.selected_element.position.x)
            self.ui.roomPosYSpin.setValue(self.selected_element.position.y)
            self.ui.roomPosZSpin.setValue(self.selected_element.position.z)
        elif isinstance(self.selected_element, LYTObstacle):
            self.ui.obstacleModelEdit.setText(self.selected_element.model)
            self.ui.obstaclePosXSpin.setValue(self.selected_element.position.x)
            self.ui.obstaclePosYSpin.setValue(self.selected_element.position.y)
            self.ui.obstaclePosZSpin.setValue(self.selected_element.position.z)
        elif isinstance(self.selected_element, LYTDoorHook):
            self.ui.doorHookPosXSpin.setValue(self.selected_element.position.x)
            self.ui.doorHookPosYSpin.setValue(self.selected_element.position.y)
            self.ui.doorHookPosZSpin.setValue(self.selected_element.position.z)
            self.updateDoorHookRoomCombo()
        elif isinstance(self.selected_element, LYTTrack):
            self.update_track_combos()

    def updateDoorHookRoomCombo(self):
        self.ui.doorHookRoomCombo.clear()
        for room in self._lyt.rooms:
            self.ui.doorHookRoomCombo.addItem(room.model, room)
        if isinstance(self.selected_element, LYTDoorHook):
            index = self.ui.doorHookRoomCombo.findData(self.selected_element.room)
            if index != -1:
                self.ui.doorHookRoomCombo.setCurrentIndex(index)

    def update_track_combos(self):
        self.ui.trackStartRoomCombo.clear()
        self.ui.trackEndRoomCombo.clear()
        for room in self._lyt.rooms:
            self.ui.trackStartRoomCombo.addItem(room.model, room)
            self.ui.trackEndRoomCombo.addItem(room.model, room)
        if isinstance(self.selected_element, LYTTrack):
            start_index = self.ui.trackStartRoomCombo.findData(self.selected_element.start_room)
            end_index = self.ui.trackEndRoomCombo.findData(self.selected_element.end_room)
            if start_index != -1 and end_index != -1:
                self.ui.trackStartRoomCombo.setCurrentIndex(start_index)
                self.ui.trackEndRoomCombo.setCurrentIndex(end_index)

    def mousePressEvent(self, event):
        if self.current_tool == "select":
            self.selected_element = self.scene.pick_lyt_element(event.x(), event.y())
            self.update_element_properties()
        elif self.current_tool in ["move", "rotate"]:
            if self.selected_element:
                self.scene.start_lyt_element_transform(self.selected_element, self.current_tool, event.x(), event.y())

    def mouseMoveEvent(self, event):
        if self.current_tool in ["move", "rotate"] and self.selected_element:
            self.scene.update_lyt_element_transform(event.x(), event.y())

    def mouseReleaseEvent(self, event):
        if self.current_tool in ["move", "rotate"] and self.selected_element:
            new_pos = self.scene.end_lyt_element_transform()
            if self.current_tool == "move":
                command = MoveRoomCommand(self, self.selected_element, self.selected_element.position, new_pos)
            elif self.current_tool == "rotate":
                command = RotateRoomCommand(self, self.selected_element, self.selected_element.rotation, new_pos)
            self.undo_stack.push(command)
            self.update_element_properties()
            self.sig_lyt_updated.emit(self._lyt)

    def generate_walkmesh(self):
        # Implement walkmesh generation logic here
        self.walkmesh = BWM()
        # ... generate walkmesh based on LYT data ...
        self.sig_walkmesh_updated.emit(self.walkmesh)

    def edit_walkmesh(self):
        if not self.walkmesh:
            self.generate_walkmesh()
        # Implement walkmesh editing logic here
        # This might involve creating a separate WalkmeshEditor widget

    def apply_texture(self, texture_name: str):
        if self.selected_element and hasattr(self.selected_element, "texture"):
            self.selected_element.texture = texture_name
            self.scene.update_lyt_element_texture(self.selected_element, texture_name)
            self.sig_lyt_updated.emit(self._lyt)

    def initUI(self):
        self.setAcceptDrops(True)

        layout = QVBoxLayout()

        # Add buttons for LYT editing operations
        button_layout = QHBoxLayout()
        add_room_button = QPushButton("Add Room")
        add_room_button.clicked.connect(self.add_room)
        button_layout.addWidget(add_room_button)

        add_track_button = QPushButton("Add Track")
        add_track_button.clicked.connect(self.add_track)
        button_layout.addWidget(add_track_button)

        add_obstacle_button = QPushButton("Add Obstacle")
        add_obstacle_button.clicked.connect(self.add_obstacle)
        button_layout.addWidget(add_obstacle_button)

        place_door_hook_button = QPushButton("Place Door Hook")
        place_door_hook_button.clicked.connect(self.place_door_hook)
        button_layout.addWidget(place_door_hook_button)
        layout.addLayout(button_layout)

        # Add zoom slider
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.update_zoom)
        zoom_layout.addWidget(self.zoom_slider)
        layout.addLayout(zoom_layout)

        # Add texture browser
        self.texturelist = QListWidget()
        self.texturelist.itemClicked.connect(self.on_texture_selected)
        layout.addWidget(self.texturelist)

        self.setLayout(layout)
        # Add more UI initialization code here

    def set_lyt(
        self,
        lyt: LYT,
    ):
        self.lyt: LYT = lyt
        self.update()

    def dragEnterEvent(
        self,
        event: QDragEnterEvent,
    ):
        mime_data: QMimeData | None = event.mimeData()
        assert mime_data is not None, "mime_data is None"
        if mime_data.hasFormat("application/x-room-template"):
            event.accept()
        else:
            event.ignore()

    def dropEvent(
        self,
        event: QDropEvent,
    ):
        mime_data: QMimeData | None = event.mimeData()
        assert mime_data is not None, "mime_data is None"
        if mime_data.hasFormat("application/x-room-template"):
            # Extract room template data and create a new room
            room_template: LYTRoom = LYTRoom.from_dict(json.loads(mime_data.data("application/x-room-template").data()))
            self.create_room_from_template(room_template)
            event.accept()
        else:
            event.ignore()

    def create_room_from_template(
        self,
        room_template: LYTRoom,
    ):
        # Logic to create a room from the given template
        new_room = LYTRoom(
            model=room_template.model,
            position=room_template.position,
        )
        self.lyt.rooms.append(new_room)
        self.update()
        self.texture_browser.textureChanged.connect(self.apply_texture)
        self.load_textures()

    @property
    def render(self):
        painter = QPainter(self.parent())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw grid
        if self._show_grid:
            self.draw_grid(painter)

        with QMutexLocker(self.render_lock):
            # Draw rooms
            visible_rooms: set[LYTRoom] = self.get_visible_rooms()
            for room in visible_rooms:
                self.draw_room(painter, room, self.parent().scene.camera.distance)

            # Draw tracks
            for track in self.lyt.tracks:
                self.draw_track(painter, track, self.parent().scene.camera.distance)

            # Draw obstacles
            for obstacle in self.lyt.obstacles:
                self.draw_obstacle(painter, obstacle, self.parent().scene.camera.distance)

            # Draw doorhooks
            for doorhook in self.lyt.doorhooks:
                self.draw_door_hook(painter, doorhook, self.parent().scene.camera.distance)

            # Draw selected elements
            self.draw_selected_elements(painter, self.parent().scene.camera.distance)

        # Draw walkmesh if in editing mode (outside of render_lock to avoid potential deadlock)
        if self.is_editing_walkmesh and self.walkmesh:
            self.draw_walkmesh(painter, self.parent().scene.camera.distance)

        painter.end()

    def draw_grid(
        self,
        painter: QPainter,
    ):
        pen = QPen(QColor(128, 128, 128), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)

        for x in range(0, self.width(), self.grid_size):
            painter.drawLine(x, 0, x, self.height())

        for y in range(0, self.height(), self.grid_size):
            painter.drawLine(0, y, self.width(), y)

    def draw_room(
        self,
        painter: QPainter,
        room: LYTRoom,
        zoom: float,
    ):
        pen = QPen(QColor(0, 0, 0), 1)
        brush = QBrush(QColor(128, 128, 128, 128))
        painter.setPen(pen)
        painter.setBrush(brush)

        rect = QRect(
            int(room.position.x),
            int(room.position.y),
            int(room.size.x * zoom),
            int(room.size.y * zoom),
        )
        painter.drawRect(rect.scaled(zoom, zoom))

    def draw_track(
        self,
        painter: QPainter,
        track: LYTTrack,
        zoom: float,
    ):
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)

        start: QPoint = QPoint(int(track.start.x), int(track.start.y)) * zoom  # FIXME: start and end attributes do not exist.
        end: QPoint = QPoint(int(track.end.x), int(track.end.y)) * zoom  # FIXME: start and end attributes do not exist.
        painter.drawLine(start, end)

    def draw_obstacle(
        self,
        painter: QPainter,
        obstacle: LYTObstacle,
        zoom: float,
    ):
        pen = QPen(QColor(255, 255, 0), 2)
        painter.setPen(pen)

        center = QPoint(int(obstacle.position.x), int(obstacle.position.y)) * zoom  # FIXME: position attribute does not exist.
        radius = obstacle.radius * zoom  # FIXME: radius attribute does not exist.
        painter.drawEllipse(center, radius, radius)

    def draw_door_hook(
        self,
        painter: QPainter,
        doorhook: LYTDoorHook,
        zoom: float,
    ):
        pen = QPen(QColor(0, 255, 0), 2)
        painter.setPen(pen)

        center = QPoint(int(doorhook.position.x), int(doorhook.position.y)) * zoom
        zoomInt = int(zoom)
        painter.drawRect(QRect(center.x() - 2 * zoomInt, center.y() - 2 * zoomInt, 4 * zoomInt, 4 * zoomInt))

    def draw_selected_elements(
        self,
        painter: QPainter,
        zoom: float,
    ):
        if self.selected_room:
            self.draw_selected_room(painter, self.selected_room, zoom)
        if self.selected_track:
            self.draw_selected_track(painter, self.selected_track, zoom)
        if self.selected_obstacle:
            self.draw_selected_obstacle(painter, self.selected_obstacle, zoom)
        if self.selected_door_hook:
            self.draw_selected_doorhook(painter, self.selected_door_hook, zoom)

        # Draw walkmesh if in editing mode
        if self.is_editing_walkmesh and self.walkmesh:
            self.draw_walkmesh(painter, zoom)

    def draw_selected_room(
        self,
        painter: QPainter,
        room: LYTRoom,
        zoom: float,
    ):
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)

        rect = QRect(
            int(room.position.x),
            int(room.position.y),
            int(room.size.x * zoom),  # FIXME: size attribute does not exist.
            int(room.size.y * zoom),  # FIXME: size attribute does not exist.
        )
        painter.drawRect(rect)

        # Draw resize handles
        handle_size = 8
        for i in range(4):
            x = rect.x() + (i % 2) * rect.width()
            y = rect.y() + (i // 2) * rect.height()
            painter.drawRect(
                QRect(
                    x - handle_size // 2,
                    y - handle_size // 2,
                    handle_size,
                    handle_size,
                ).scaled(zoom, zoom)
            )  # FIXME: scaled method does not exist.

    def draw_selected_track(
        self,
        painter: QPainter,
        track: LYTTrack,
        zoom: float,
    ):
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)

        start: QPoint = QPoint(int(track.start.x), int(track.start.y)) * zoom  # FIXME: start and end attributes do not exist.
        end: QPoint = QPoint(int(track.end.x), int(track.end.y)) * zoom  # FIXME: start and end attributes do not exist.
        painter.drawLine(start, end)

        # Draw handles at start and end
        handleSize = 8
        painter.drawRect(
            QRect(
                start.x() - handleSize // 2,
                start.y() - handleSize // 2,
                handleSize,
                handleSize,
            ).scaled(zoom, zoom)
        )  # FIXME: scaled method does not exist.
        painter.drawRect(QRect(end.x() - handleSize // 2, end.y() - handleSize // 2, handleSize, handleSize).scaled(zoom, zoom))  # FIXME: scaled method does not exist.

    def draw_selected_obstacle(self, painter: QPainter, obstacle: LYTObstacle, zoom: float):
        pen = QPen(QColor(255, 255, 0), 2)
        painter.setPen(pen)

        center = QPoint(int(obstacle.position.x), int(obstacle.position.y)) * zoom  # FIXME: position attribute does not exist.
        radius: float = obstacle.radius * zoom  # FIXME: radius attribute does not exist.
        painter.drawEllipse(center, radius, radius)

    def draw_selected_doorhook(
        self,
        painter: QPainter,
        doorhook: LYTDoorHook,
        zoom: float,
    ):
        pen = QPen(QColor(0, 255, 0), 2)
        painter.setPen(pen)

        center = QPoint(int(doorhook.position.x), int(doorhook.position.y)) * zoom
        painter.drawRect(QRect(center.x() - 2 * zoom, center.y() - 2 * zoom, 4 * zoom, 4 * zoom))

    def draw_walkmesh(
        self,
        painter: QPainter,
        zoom: float,
    ):
        pen = QPen(QColor(0, 0, 255, 128), 1)
        painter.setPen(pen)
        for face in self.walkmesh.faces:
            points: list[QPoint] = [QPoint(int(v.x * zoom), int(v.y * zoom)) for v in face.vertices]  # FIXME: vertices attribute does not exist.
            painter.drawPolygon(points)

    def handle_key_press(self, e: QKeyEvent):
        if e.key() == Qt.Key.Key_Delete:
            if self.selected_room:
                self.lyt.rooms.remove(self.selected_room)
                self.selected_room = None
            if self.selected_track:
                self.lyt.tracks.remove(self.selected_track)
                self.selected_track = None
            if self.selected_obstacle:
                self.lyt.obstacles.remove(self.selected_obstacle)
                self.selected_obstacle = None
            if self.selected_door_hook:
                self.lyt.doorhooks.remove(self.selected_door_hook)
                self.selected_door_hook = None
            self.update()

    def handle_mouse_press(self, e: QMouseEvent):
        self.mouse_pos: Vector2 = Vector2(e.x(), e.y())
        self.mouse_prev: Vector2 = self.mouse_pos
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

    def handle_mouse_release(self, e: QMouseEvent):
        self.mouse_down.discard(e.button())
        self.is_dragging = False
        self.is_resizing = False
        self.is_rotating = False
        self.selected_room_resize_corner = None
        self.selected_room_rotation_point = None

    def handleMouseMove(self, e: QMouseEvent):
        self.mouse_pos = Vector2(e.x(), e.y())

        if self.is_dragging:
            self.drag_lyt_element(self.mouse_pos)
        elif self.is_resizing:
            self.resize_selected_room(self.mouse_pos)
        elif self.is_rotating:
            self.rotate_selected_room(self.mouse_pos)

    def select_lyt_element(self, mouse_pos: Vector2):
        # Check for room selection
        for room in self.lyt.rooms:
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
        for track in self.lyt.tracks:
            start = QPoint(int(track.start.x), int(track.start.y))  # FIXME: start and end attributes do not exist.
            end = QPoint(int(track.end.x), int(track.end.y))  # FIXME: start and end attributes do not exist.
            line = QLine(start, end)
            if line.ptDistanceToPoint(QPoint(int(mouse_pos.x), int(mouse_pos.y))) <= 5:  # FIXME: ptDistanceToPoint method does not exist.
                self.selected_room = None
                self.selected_track: LYTTrack | None = track
                self.selected_obstacle = None
                self.selected_door_hook = None
                return

        # Check for obstacle selection
        for obstacle in self.lyt.obstacles:
            center = QPoint(int(obstacle.position.x), int(obstacle.position.y))
            radius: float = obstacle.radius  # FIXME: radius attribute does not exist.
            if QPoint(int(mouse_pos.x), int(mouse_pos.y)).distanceToPoint(center) <= radius:  # FIXME: distanceToPoint method does not exist.
                self.selected_room = None
                self.selected_track = None
                self.selected_obstacle: LYTObstacle | None = obstacle
                self.selected_door_hook = None
                return

        # Check for doorhook selection
        for doorhook in self.lyt.doorhooks:
            center = QPoint(int(doorhook.position.x), int(doorhook.position.y))
            if QRect(center.x() - 2, center.y() - 2, 4, 4).contains(QPoint(int(mouse_pos.x), int(mouse_pos.y))):
                self.selected_room = None
                self.selected_track = None
                self.selected_obstacle = None
                self.selected_door_hook: LYTDoorHook | None = doorhook
                return

        # Deselect if no element is selected
        self.selected_room = None
        self.selected_track = None
        self.selected_obstacle = None
        self.selected_door_hook = None

    def drag_lyt_element(self, mouse_pos: Vector2):
        delta = mouse_pos - self.mouse_prev
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
            self.moveDoorHook(self.selected_door_hook, delta)

        self.update()

    def move_room(
        self,
        room: LYTRoom,
        delta: Vector2,
    ):
        new_position = Vector3(room.position.x + delta.x, room.position.y + delta.y, room.position.z)
        self.room_moved.emit(room, new_position)

    def move_track_start(
        self,
        track: LYTTrack,
        delta: Vector2,
    ):
        new_start = Vector3(track.start.x + delta.x, track.start.y + delta.y, track.start.z)  # FIXME: start and end attributes do not exist.
        self.room_moved.emit(track, new_start)

    def move_track_end(
        self,
        track: LYTTrack,
        delta: Vector2,
    ):
        newEnd = Vector3(track.end.x + delta.x, track.end.y + delta.y, track.end.z)  # FIXME: start and end attributes do not exist.
        self.room_moved.emit(track, newEnd)

    def move_obstacle(
        self,
        obstacle: LYTObstacle,
        delta: Vector2,
    ):
        new_position = Vector3(obstacle.position.x + delta.x, obstacle.position.y + delta.y, obstacle.position.z)
        self.room_moved.emit(obstacle, new_position)

    def moveDoorHook(
        self,
        doorhook: LYTDoorHook,
        delta: Vector2,
    ):
        new_position = Vector3(doorhook.position.x + delta.x, doorhook.position.y + delta.y, doorhook.position.z)
        self.room_moved.emit(doorhook, new_position)

    def resize_selected_room(
        self,
        mouse_pos: Vector2,
    ):
        if self.selected_room is None or self.selected_room_resize_corner is None:
            return

        delta = mouse_pos - self.mouse_prev
        self.mouse_prev = mouse_pos

        # Calculate new size based on resize corner
        new_size = Vector2(self.selected_room.size.x, self.selected_room.size.y)  # FIXME: size attribute does not exist.
        if self.selected_room_resize_corner == 0:
            new_size.x += delta.x
            new_size.y += delta.y
        elif self.selected_room_resize_corner == 1:
            new_size.x += delta.x
        elif self.selected_room_resize_corner == 2:
            new_size.x += delta.x
            new_size.y -= delta.y
        elif self.selected_room_resize_corner == 3:
            new_size.y -= delta.y
        elif self.selected_room_resize_corner == 4:
            new_size.y += delta.y
        elif self.selected_room_resize_corner == 5:
            new_size.x -= delta.x
            new_size.y += delta.y
        elif self.selected_room_resize_corner == 6:
            new_size.x -= delta.x
        elif self.selected_room_resize_corner == 7:
            new_size.x -= delta.x
            new_size.y -= delta.y

        # Update room size
        self.roomResized.emit(self.selected_room, new_size)
        self.update()

    def rotate_selected_room(
        self,
        mouse_pos: Vector2,
    ):
        if self.selected_room is None or self.selected_room_rotation_point is None:
            return

        delta = mouse_pos - self.mouse_prev
        self.mouse_prev = mouse_pos

        # Calculate rotation angle
        angle = math.degrees(math.atan2(delta.y, delta.x))

        # Update room rotation
        self.roomRotated.emit(self.selected_room, angle)
        self.update()

    def place_door_hook(
        self,
        mouse_pos: Vector2,
    ):
        doorhook = LYTDoorHook(Vector3(mouse_pos.x, mouse_pos.y, 0))  # FIXME: arguments missing for door, room, orientation
        self.door_hook_placed.emit(doorhook)
        self.update()

    def load_textures(self):
        # Load textures from the module
        self.add_background_task(self.load_textures_task, ())

    def load_textures_task(self) -> list[ModuleResource[MDL]]:
        # Implement texture loading logic here
        # This method will be executed in a separate thread
        scene_module: Module | None = self.parent().scene._module  # noqa: SLF001
        assert scene_module is not None
        textures: list[ModuleResource[MDL]] = scene_module.textures()
        with self.texture_lock:
            self.textures = textures
        return textures

    def on_textures_loaded(self, result: Future):
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
        if not self.lyt or len(self.lyt.rooms) < 2:
            return

        new_doorhooks: list[LYTDoorHook] = []
        connected_rooms: set[tuple[LYTRoom, LYTRoom]] = set()
        doorhook_groups: dict[tuple[LYTRoom, LYTRoom], list[LYTDoorHook]] = {}

        for i, room1 in enumerate(self.lyt.rooms):
            for room2 in self.lyt.rooms[i + 1 :]:
                if (room1, room2) in connected_rooms or (room2, room1) in connected_rooms:
                    continue

                shared_edge: tuple[str, float, float] | None = self.getSharedEdge(room1, room2)
                if not shared_edge:
                    continue

                new_doorhooks.extend(self.createDoorHooks(room1, room2, shared_edge))
                connected_rooms.add((room1, room2))

        # Remove existing doorhooks that are no longer valid
        valid_doorhooks: list[LYTDoorHook] = []
        for doorhook in self.lyt.doorhooks:
            connected_rooms = self.get_connected_rooms(doorhook)
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
        self.lyt.doorhooks = valid_doorhooks

        # Optimize doorhook placement
        for group in doorhook_groups.values():
            if len(group) > 1:
                self.optimize_group_placement(group)

        # Update the spatial partitioning
        self.optimize_rendering()
        # Notify listeners of the update
        self.update()
        self.sig_lyt_updated.emit(self.lyt)

    def get_connected_rooms(self, doorhook: LYTDoorHook) -> list[LYTRoom]:
        return [room for room in self.lyt.rooms if self.is_door_hook_on_room_edge(doorhook, room)]

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

    def get_edge_length(self, start_hook: LYTDoorHook, end_hook: LYTDoorHook) -> float:
        return ((end_hook.position.x - start_hook.position.x) ** 2 + (end_hook.position.y - start_hook.position.y) ** 2) ** 0.5

    def interpolate_position(self, start: Vector3, end: Vector3, t: float) -> Vector3:
        return Vector3(start.x + (end.x - start.x) * t, start.y + (end.y - start.y) * t, start.z + (end.z - start.z) * t)

    def createDoorHooks(
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
                door_x = max(room2.position.x, room1.position.x)
                door_y = start + (end - start) * t
            else:  # horizontal
                door_x = start + (end - start) * t
                door_y = max(room2.position.y, room1.position.y)
            doorhooks.append(
                LYTDoorHook(  # pyright: ignore[reportCallIssue]
                    room=uuid4().hex[:15],
                    door=uuid4().hex[:15],
                    position=Vector3(door_x, door_y, 0),
                    orientation=Vector4(0, 0, 1, 0),
                )
            )  # FIXME: arguments missing for door, room, orientation

        return doorhooks

    def getSharedEdge(self, room1: LYTRoom, room2: LYTRoom) -> tuple[str, float, float] | None:
        r1_left, r1_right = room1.position.x, room1.position.x + room1.size.x  # FIXME: size attribute does not exist.
        r1_top, r1_bottom = room1.position.y, room1.position.y + room1.size.y  # FIXME: size attribute does not exist.
        r2_left, r2_right = room2.position.x, room2.position.x + room2.size.x  # FIXME: size attribute does not exist.
        r2_top, r2_bottom = room2.position.y, room2.position.y + room2.size.y  # FIXME: size attribute does not exist.

        tolerance = 0.001  # Small tolerance for floating-point comparisons

        # Check for vertical adjacency
        if abs(r1_right - r2_left) < tolerance:
            top = max(r1_top, r2_top)
            bottom = min(r1_bottom, r2_bottom)
            if bottom > top:
                return "vertical", top, bottom
        elif abs(r1_left - r2_right) < tolerance:
            top = max(r1_top, r2_top)
            bottom = min(r1_bottom, r2_bottom)
            if bottom > top:
                return "vertical", top, bottom

        # Check for horizontal adjacency
        if abs(r1_bottom - r2_top) < tolerance:
            left = max(r1_left, r2_left)
            right = min(r1_right, r2_right)
            if right > left:
                return "horizontal", left, right
        elif abs(r1_top - r2_bottom) < tolerance:
            left = max(r1_left, r2_left)
            right = min(r1_right, r2_right)
            if right > left:
                return "horizontal", left, right

        return None

    def isDoorHookValid(self, doorhook: LYTDoorHook) -> bool:
        """Check if the doorhook is on the edge of any room."""
        return any(self.is_door_hook_on_room_edge(doorhook, room) for room in self.lyt.rooms)

    def is_door_hook_on_room_edge(self, doorhook: LYTDoorHook, room: LYTRoom) -> bool:
        tolerance = 0.001
        x, y = doorhook.position.x, doorhook.position.y

        # Check if the doorhook is on any of the room's edges
        on_left = abs(x - room.position.x) < tolerance
        on_right = abs(x - (room.position.x + room.size.x)) < tolerance  # FIXME: size attribute does not exist.
        on_top = abs(y - room.position.y) < tolerance
        on_bottom = abs(y - (room.position.y + room.size.y)) < tolerance  # FIXME: size attribute does not exist.

        return (
            (on_left or on_right)
            and (room.position.y <= y <= room.position.y + room.size.y)  # FIXME: size attribute does not exist.
            or (on_top or on_bottom)
            and (room.position.x <= x <= room.position.x + room.size.x)  # FIXME: size attribute does not exist.
        )

    def optimizeDoorHookPlacement(self):
        # Group doorhooks by their connecting rooms
        doorhook_groups = {}
        for doorhook in self.lyt.doorhooks:
            connected_rooms = self.get_connected_rooms(doorhook)
            if connected_rooms:
                key = tuple(sorted(connected_rooms))  # FIXME: list[LYTRoom]" is incompatible with "Iterable[SupportsRichComparisonT@sorted]
                if key not in doorhook_groups:
                    doorhook_groups[key] = []
                doorhook_groups[key].append(doorhook)

        # Optimize placement for each group
        for group in doorhook_groups.values():
            if len(group) > 1:
                self.optimize_group_placement(group)

    def manualDoorPlacement(self, room: LYTRoom):
        self.is_placing_door_hook = True
        self.selected_room = room

    def place_door_hook(self, mouse_pos: Vector2):
        """Check if the mouse position is on the edge of the selected room."""
        room = self.selected_room
        tolerance = 5  # pixels

        if (
            abs(mouse_pos.x - room.position.x) < tolerance
            or abs(mouse_pos.x - (room.position.x + room.size.x)) < tolerance  # FIXME: size attribute does not exist.
            or abs(mouse_pos.y - room.position.y) < tolerance
            or abs(mouse_pos.y - (room.position.y + room.size.y)) < tolerance  # FIXME: size attribute does not exist.
        ):
            doorhook = LYTDoorHook(Vector3(mouse_pos.x, mouse_pos.y, 0))  # FIXME: arguments missing for door, room, orientation
            self.lyt.doorhooks.append(doorhook)
            self.door_hook_placed.emit(doorhook)
            self.update()

    def snapToGrid(self, point: Vector2) -> Vector2:
        if self._snapToGrid:
            return Vector2(
                round(point.x / self.grid_size) * self.grid_size,
                round(point.y / self.grid_size) * self.grid_size,
            )
        return point

    def getRoomResizeCorner(self, mouse_pos: Vector2) -> Optional[int]:
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

        self.selected_room_resize_corner = self.getRoomResizeCorner(mouse_pos)
        if self.selected_room_resize_corner is not None:
            self.is_resizing = True
            self.mouse_prev = mouse_pos

    def getRoomRotationPoint(self, mouse_pos: Vector2) -> Optional[Vector2]:
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

    def rotate_room(self, mouse_pos: Vector2):
        if self.selected_room is None:
            return

        self.selected_room_rotation_point = self.getRoomRotationPoint(mouse_pos)
        if self.selected_room_rotation_point is not None:
            self.is_rotating = True
            self.mouse_prev = mouse_pos

    def setGridSize(self, grid_size: int):
        self.grid_size = grid_size
        self.update()

    def setSnapToGrid(self, snapToGrid: bool):
        self._snapToGrid = snapToGrid
        self.update()

    def setShowGrid(self, show_grid: bool):
        self._show_grid: bool = show_grid
        self.update()

    def generate_walkmesh(self):
        if not self.lyt or not self.lyt.rooms:
            return

        self.walkmesh = BWM()

        for room in self.lyt.rooms:
            # Create a simple rectangular face for each room
            vertices = [
                Vector3(room.position.x, room.position.y, 0),
                Vector3(room.position.x + room.size.x, room.position.y, 0),  # FIXME: size attribute does not exist.
                Vector3(room.position.x + room.size.x, room.position.y + room.size.y, 0),  # FIXME: size attribute does not exist.
                Vector3(room.position.x, room.position.y + room.size.y, 0),  # FIXME: size attribute does not exist.
            ]
            face = BWMFace(*vertices)
            self.walkmesh.faces.append(face)

        self.sig_walkmesh_updated.emit(self.walkmesh)
        self.update()

    def edit_walkmesh(self):
        if not self.walkmesh:
            self.generate_walkmesh()

        self.is_editing_walkmesh = True
        self.selectedWalkmeshFace = None
        self.update()

    def handleWalkmeshEdit(self, mouse_pos: Vector2):
        if not self.is_editing_walkmesh or not self.walkmesh:
            return

        clickedFace = self.getWalkmeshFaceAt(mouse_pos)

        if clickedFace:
            if self.selectedWalkmeshFace == clickedFace:
                # If the same face is clicked again, enter vertex edit mode
                self.editWalkmeshVertices(clickedFace)
            else:
                self.selectedWalkmeshFace = clickedFace
        else:
            self.selectedWalkmeshFace = None

        self.update()

    def getWalkmeshFaceAt(self, point: Vector2) -> Optional[BWMFace]:
        for face in self.walkmesh.faces:
            if self.isPointInPolygon(point, face.vertices):  # FIXME: vertices attribute is not defined.
                return face
        return None

    def isPointInPolygon(self, point: Vector2, vertices: list[Vector3]) -> bool:
        n = len(vertices)
        inside = False
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

    def editWalkmeshVertices(self, face: BWMFace):
        # TODO: Implement vertex editing logic here
        # For example, you could enter a mode where clicking near a vertex allows you to drag it
        pass

    def drawSelectedWalkmeshFace(self, painter: QPainter, face: BWMFace):
        pen = QPen(QColor(255, 0, 0, 200), 2)
        painter.setPen(pen)
        painter.drawPolygon([QPoint(int(v.x), int(v.y)) for v in face.vertices])  # FIXME: vertices attribute is not defined.

    def updateLYT(self):
        # Update the LYT data and notify listeners
        self.sig_lyt_updated.emit(self.lyt)
        self.update()

    def mousePressEvent(self, e: QMouseEvent):
        super().mousePressEvent(e)
        if self.is_editing_walkmesh:
            self.handleWalkmeshEdit(Vector2(e.x(), e.y()))

    def mouseMoveEvent(self, e: QMouseEvent):
        super().mouseMoveEvent(e)
        if self.is_editing_walkmesh and self.selectedWalkmeshFace:
            # TODO: Implement logic for moving vertices or the entire face
            pass

    def mouseReleaseEvent(self, e: QMouseEvent):
        super().mouseReleaseEvent(e)
        # TODO: Add any necessary cleanup for walkmesh editing here

    def add_obstacle(self, model_name: str = ""):
        # TODO: Implement obstacle addition logic
        newObstacle = LYTObstacle(model=model_name, position=Vector3(50, 50, 0), radius=25)
        self.lyt.obstacles.append(newObstacle)
        self.update()

    def on_texture_selected(self, item: QListWidgetItem):
        textureName = item.text()
        self.apply_texture(textureName)

    def apply_texture_task(self, textureName: str):
        # This method will be executed in a separate thread
        # Implement the logic to apply the texture to the selected element
        with self.lyt_lock:
            if self.selected_room:  # FIXME: lytroom does not store textures.
                self.selected_room.texture = textureName  # FIXME: texture attribute does not exist in a LYTRoom.
            elif self.selected_track:
                self.selected_track.texture = textureName  # FIXME: texture attribute does not exist in a LYTTrack.
        return textureName

    def onTextureApplied(self, result):
        self.textureChanged.emit(result)
        self.update()

    def optimize_rendering(self):
        # Implement spatial partitioning for efficient rendering of large layouts
        with self.lyt_lock:
            if not self.lyt or not self.lyt.rooms:
                return

            # Simple grid-based spatial partitioning
            self.spatial_grid.clear()

            for room in self.lyt.rooms:
                grid_x = int(room.position.x / self.grid_size)
                grid_y = int(room.position.y / self.grid_size)
                grid_key = (grid_x, grid_y)
                if grid_key not in self.spatial_grid:
                    self.spatial_grid[grid_key] = []
                self.spatial_grid[grid_key].append(room)

            self.renderingOptimized.emit()

    def get_visible_rooms(self) -> set[LYTRoom]:
        visible_rooms: set[LYTRoom] = set()
        camera = self.parent().scene.camera
        view_rect: QRect = QRect(int(camera.x - camera.width / 2), int(camera.y - camera.height / 2), int(camera.width), int(camera.height))

        grid_x_start = int(view_rect.left() / self.grid_size)
        grid_x_end = int(view_rect.right() / self.grid_size)
        grid_y_start = int(view_rect.top() / self.grid_size)
        grid_y_end = int(view_rect.bottom() / self.grid_size)

        for x in range(grid_x_start, grid_x_end + 1):
            for y in range(grid_y_start, grid_y_end + 1):
                grid_key = (x, y)
                if grid_key in self.spatial_grid:
                    visible_rooms.update(self.spatial_grid[grid_key])

        return visible_rooms

    def parent(self) -> ModuleRenderer:
        from toolset.gui.widgets.renderer.module import ModuleRenderer

        assert isinstance(self.parent(), ModuleRenderer)
        return self.parent()

    def onTaskCompleted(self, task: Callable, result: Any):
        with self.task_consumer_lock:
            self.main_thread_tasks.put((task, result, {}))
            qApp = QApplication.instance()
            assert qApp is not None, "QApplication instance not found?"
            qApp.postEvent(self, QEvent(QEvent.Type.User))
        self.taskCompleted.emit(result)

    def processBackgroundTasks(self):
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
                        except queue.Empty:
                            break
                for consumer in self.task_consumers:
                    try:
                        if not consumer.is_busy():  # FIXME: is_busy method does not exist.
                            consumer.add_task(task, args)  # FIXME: add_task method does not exist.
                            break
                        # If all consumers are busy, put the task back in the queue
                        self.task_queue.put((task, args))
                        break
                    except queue.Empty:
                        break

    def processMainThreadTasks(self):
        while not self.main_thread_tasks.empty():
            try:
                task, result = self.main_thread_tasks.get(block=False)
                if task == self.load_textures_task:
                    self.on_textures_loaded(result)
                elif task == self.apply_texture_task:
                    self.onTextureApplied(result)
                # Add more task completions as needed
            except Empty:  # noqa: PERF203
                break

        self.processErrors()
        self.processChanges()  # FIXME: processChanges method does not exist.

    def processErrors(self):
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
                with self.lyt_lock:
                    for change in self.change_buffer:
                        # Apply the change to self.lyt
                        action, element_type, data = change
                        if action == "add":
                            if element_type == "room":
                                self.lyt.rooms.append(data)
                            elif element_type == "track":
                                self.lyt.tracks.append(data)
                            elif element_type == "obstacle":
                                self.lyt.obstacles.append(data)
                            elif element_type == "doorhook":
                                self.lyt.doorhooks.append(data)
                        elif action == "update":
                            # Implement update logic for each element type
                            pass
                        elif action == "delete":
                            if element_type == "room":
                                self.lyt.rooms.remove(data)
                            elif element_type == "track":
                                self.lyt.tracks.remove(data)
                            elif element_type == "obstacle":
                                self.lyt.obstacles.remove(data)
                            elif element_type == "doorhook":
                                self.lyt.doorhooks.remove(data)
                self.sig_lyt_updated.emit(self.lyt)
                self.change_buffer.clear()
            self.update()

    def updateLYT(self):
        with self.lyt_lock, self.render_lock:
            lyt_copy = deepcopy(self.lyt)
            self.sig_lyt_updated.emit(lyt_copy)
        self.update()

    def update_zoom(self, value: int):
        self.parent().scene.camera.distance = value / 100.0
        self.update()

    def closeEvent(self, event):
        self.is_shutting_down = True
        for consumer in self.task_consumers:
            consumer.stop()
        super().closeEvent(event)

    def handleTaskException(self, task: Callable, exception: Exception):
        with self.task_consumer_lock:
            self.error_queue.put((task, exception))
            qApp = QApplication.instance()
            assert qApp is not None, "QApplication instance not found?"
            qApp.postEvent(self, QEvent(QEvent.Type.User))

    def add_background_task(self, task: Callable, args: tuple):
        with self.task_queue_lock:
            self.task_queue.put((task, args, {}))
            qApp = QApplication.instance()
            assert qApp is not None, "QApplication instance not found?"
            qApp.postEvent(self, QEvent(QEvent.Type.User))  # Trigger event processing

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.User:
            self.processMainThreadTasks()
            self.processBackgroundTasks()
            self.processChanges()  # FIXME: processChanges method does not exist.
            return True
        return super().event(event)

    def addChange(self, change):
        with self.change_lock:
            self.change_buffer.append(change)
            qApp = QApplication.instance()
            assert qApp is not None, "QApplication instance not found?"
            qApp.postEvent(self, QEvent(QEvent.Type.User))  # Trigger event processing

    def showErrorDialog(self, message: str):
        # Implement this method to show an error dialog to the user
        qApp = QApplication.instance()
        if qApp is not None and qApp.thread() == QThread.currentThread():
            QMessageBox.critical(self, "Error", message)

    def add_room(self, model_name: str = ""):
        # Implement room addition logic
        newRoom = LYTRoom(model=model_name, position=Vector3(0, 0, 0))
        self.lyt.rooms.append(newRoom)
        self.update()

    def updateRoom(self, room: LYTRoom):
        self.addChange(("update", "room", room))

    def deleteRoom(self, room: LYTRoom):
        self.addChange(("delete", "room", room))

    # Add more methods for specific LYT operations (e.g., add_room, updateRoom, deleteRoom, etc.)
    # Implement similar methods for tracks, obstacles, and doorhooks

    def add_track(self, model_name: str = ""):
        # Implement track addition logic
        newTrack = LYTTrack(model=model_name, position=Vector3(0, 0, 0))
        self.lyt.tracks.append(newTrack)
        self.update()

    def updateTrack(self, track: LYTTrack):
        self.addChange(("update", "track", track))

    def deleteTrack(self, track: LYTTrack):
        self.addChange(("delete", "track", track))
