from __future__ import annotations

import math

from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional

import qtpy

from qtpy.QtCore import QRectF, Qt, pyqtSignal as Signal
from qtpy.QtGui import QBrush, QColor, QPainter, QPen, QUndoCommand
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QHBoxLayout,
    QLineEdit,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QUndoStack,
    QVBoxLayout,
    QWidget,
)
from qtpy.uic import loadUi

from pykotor.resource.formats.bwm.bwm_data import BWM
from pykotor.resource.formats.lyt.lyt_data import (
    LYT,
    LYTDoorHook,
    LYTObstacle,
    LYTRoom,
    LYTTrack,
)
from toolset.gui.widgets.renderer.lyt_editor import LYTEditor
from toolset.gui.widgets.renderer.texture_browser import TextureBrowser
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from qtpy.QtCore import QPointF
    from qtpy.QtGui import QMouseEvent, QWheelEvent
    from qtpy.QtWidgets import QGraphicsItem

    from toolset.gui.widgets.renderer.lyt_editor import LYTEditor, LYTRenderer


class WalkmeshEditor(QWidget):
    sig_lyt_updated: ClassVar[Signal] = Signal(LYT)
    sig_walkmesh_updated: ClassVar[Signal] = Signal(BWM)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.walkmesh: BWM = BWM()
        self.scene: QGraphicsScene = QGraphicsScene(self)
        self.selected_element: Optional[QGraphicsItem] = None
        self.current_tool: str = "select"

        self.undo_stack: QUndoStack = QUndoStack(self)

        self.texture_browser: TextureBrowser = TextureBrowser(self)
        self.textures: Dict[str, str] = {}

        self.initUI()
        self.init_connections()

    def toggle_visibility(self):
        """Toggle walkmesh visibility."""
        self.setVisible(not self.isVisible())

    def start_editing(self):
        """Start walkmesh editing mode."""
        self.is_editing_walkmesh = True
        self.selected_walkmesh_face = None
        self.update()

    def initUI(self):
        loadUi("Tools/HolocronToolset/src/toolset/uic/qtpy/editors/walkmesh.py", self)
        self.graphics_view.setScene(self.scene)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.add_room_button.clicked.connect(self.add_room)
        self.edit_room_button.clicked.connect(self.edit_room)
        self.delete_room_button.clicked.connect(self.delete_room)

        self.add_track_button.clicked.connect(self.add_track)
        self.edit_track_button.clicked.connect(self.edit_track)
        self.delete_track_button.clicked.connect(self.delete_track)

        self.add_obstacle_button.clicked.connect(self.add_obstacle)
        self.edit_obstacle_button.clicked.connect(self.edit_obstacle)
        self.delete_obstacle_button.clicked.connect(self.delete_obstacle)

        self.add_doorhook_button.clicked.connect(self.add_door_hook)
        self.edit_doorhook_button.clicked.connect(self.edit_doorhook)
        self.delete_doorhook_button.clicked.connect(self.delete_door_hook)

        self.generate_walkmesh_button.clicked.connect(self.generate_walkmesh)

        self.zoom_slider.valueChanged.connect(self.update_zoom)

    def init_connections(self):
        self.rooms_list.itemClicked.connect(self.on_room_selected)
        self.tracks_list.itemClicked.connect(self.on_track_selected)
        self.obstacles_list.itemClicked.connect(self.on_obstacle_selected)
        self.doorhooks_list.itemClicked.connect(self.on_doorhook_selected)

    def set_lyt(self, lyt: LYT):
        self.lyt: LYT = lyt
        self.update_lists()
        self.update_scene()
        self.sig_lyt_updated.emit(self.lyt)

    def get_lyt(self) -> LYT:
        return self.lyt

    def add_room(self):
        dialog = RoomPropertiesDialog(self)
        if dialog.exec():
            room = LYTRoom()
            room.position = dialog.position
            room.size = dialog.size
            room.model = dialog.model
            command = AddRoomCommand(self, room)
            self.undo_stack.push(command)

    def edit_room(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsRectItem):
            room: LYTRoom = self.selected_element.data(0)
            dialog = RoomPropertiesDialog(self, room)
            if dialog.exec():
                old_room = LYTRoom()
                old_room.position = room.position
                old_room.size = room.size
                old_room.model = room.model

                room.position = dialog.position
                room.size = dialog.size
                room.model = dialog.model

                command = EditRoomCommand(self, room, old_room)
                self.undo_stack.push(command)

    def delete_room(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsRectItem):
            room: LYTRoom = self.selected_element.data(0)
            command = DeleteRoomCommand(self, room)
            self.undo_stack.push(command)

    def add_track(self):
        if len(self.lyt.rooms) < 2:  # noqa: PLR2004
            from toolset.gui.common.localization import translate as tr
            QMessageBox.warning(self, tr("Add Track"), tr("At least two rooms are required to add a track."))
            return
        dialog = TrackPropertiesDialog(self, self.lyt.rooms)
        if dialog.exec():
            track: LYTTrack = LYTTrack()
            track.start_room = dialog.start_room
            track.end_room = dialog.end_room
            command = AddTrackCommand(self, track)
            self.undo_stack.push(command)

    def edit_track(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsLineItem):
            track: LYTTrack = self.selected_element.data(0)
            dialog = TrackPropertiesDialog(self, self.lyt.rooms, track)
            if dialog.exec():
                old_track = LYTTrack()
                old_track.start_room = track.start_room
                old_track.end_room = track.end_room

                track.start_room = dialog.start_room
                track.end_room = dialog.end_room

                command = EditTrackCommand(self, track, old_track)
                self.undo_stack.push(command)

    def delete_track(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsLineItem):
            track: LYTTrack = self.selected_element.data(0)
            command = DeleteTrackCommand(self, track)
            self.undo_stack.push(command)

    def add_obstacle(self):
        dialog = ObstaclePropertiesDialog(self)
        if dialog.exec():
            obstacle: LYTObstacle = LYTObstacle()
            obstacle.position = dialog.position
            obstacle.radius = dialog.radius
            command = AddObstacleCommand(self, obstacle)
            self.undo_stack.push(command)

    def edit_obstacle(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsEllipseItem):
            obstacle: LYTObstacle = self.selected_element.data(0)
            dialog: ObstaclePropertiesDialog = ObstaclePropertiesDialog(self, obstacle)
            if dialog.exec():
                old_obstacle: LYTObstacle = LYTObstacle()
                old_obstacle.position = obstacle.position
                old_obstacle.radius = obstacle.radius

                obstacle.position = dialog.position
                obstacle.radius = dialog.radius

                command = EditObstacleCommand(self, obstacle, old_obstacle)
                self.undo_stack.push(command)

    def delete_obstacle(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsEllipseItem):
            obstacle: LYTObstacle = self.selected_element.data(0)
            command = DeleteObstacleCommand(self, obstacle)
            self.undo_stack.push(command)

    def add_door_hook(self):
        if not self.lyt.rooms:
            from toolset.gui.common.localization import translate as tr
            QMessageBox.warning(self, tr("Add Door Hook"), tr("At least one room is required to add a door hook."))
            return
        dialog = DoorHookPropertiesDialog(self, self.lyt.rooms)
        if dialog.exec():
            doorhook: LYTDoorHook = LYTDoorHook()
            doorhook.room = dialog.room
            doorhook.position = dialog.position
            doorhook.orientation = dialog.orientation
            command = AddDoorHookCommand(self, doorhook)
            self.undo_stack.push(command)

    def edit_doorhook(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsRectItem):
            doorhook: LYTDoorHook = self.selected_element.data(0)
            dialog: DoorHookPropertiesDialog = DoorHookPropertiesDialog(self, self.lyt.rooms, doorhook)
            if dialog.exec():
                old_doorhook: LYTDoorHook = LYTDoorHook()
                old_doorhook.room = doorhook.room
                old_doorhook.position = doorhook.position
                old_doorhook.orientation = doorhook.orientation

                doorhook.room = dialog.room
                doorhook.position = dialog.position
                doorhook.orientation = dialog.orientation

                command = EditDoorHookCommand(self, doorhook, old_doorhook)
                self.undo_stack.push(command)

    def delete_door_hook(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsRectItem):
            doorhook: LYTDoorHook = self.selected_element.data(0)
            command = DeleteDoorHookCommand(self, doorhook)
            self.undo_stack.push(command)

    def generate_walkmesh(self):
        self.walkmesh: BWM = BWM()
        for room in self.lyt.rooms:
            self.add_room_to_walkmesh(room)
        for obstacle in self.lyt.obstacles:
            self.add_obstacle_to_walkmesh(obstacle)
        self.sig_walkmesh_updated.emit(self.walkmesh)

    def add_room_to_walkmesh(
        self,
        room: LYTRoom,
    ):
        # Create a simple rectangular walkmesh for the room
        x: float = room.position.x
        y: float = room.position.y
        z: float = room.position.z
        width: float = room.size.x
        height: float = room.size.y

        vertices: list[tuple[float, float, float]] = [
            (x, y, z),
            (x + width, y, z),
            (x + width, y + height, z),
            (x, y + height, z)
        ]

        faces: list[tuple[int, int, int]] = [
            (0, 1, 2),
            (0, 2, 3)
        ]

        for face in faces:
            self.walkmesh.add_face([Vector3(*vertices[i]) for i in face])

    def add_obstacle_to_walkmesh(
        self,
        obstacle: LYTObstacle,
    ):
        # Create a simple circular walkmesh for the obstacle
        x: float = obstacle.position.x
        y: float = obstacle.position.y
        z: float = obstacle.position.z
        radius: float = obstacle.radius
        num_segments: int = 16

        vertices: list[tuple[float, float, float]] = []
        for i in range(num_segments):
            angle: float = 2 * math.pi * i / num_segments
            vx: float = x + radius * math.cos(angle)
            vy: float = y + radius * math.sin(angle)
            vertices.append((vx, vy, z))

        center: tuple[float, float, float] = (x, y, z)
        vertices.append(center)

        for i in range(num_segments):
            j = (i + 1) % num_segments
            self.walkmesh.add_face(
                [
                    Vector3(*vertices[i]),
                    Vector3(*vertices[j]),
                    Vector3(*center),
                ]
            )

    def update_zoom(
        self,
        value: int,
    ):
        zoom_factor: float = value / 100.0
        self.graphics_view.resetTransform()
        self.graphics_view.scale(zoom_factor, zoom_factor)

    def update_lists(self):
        self.rooms_list.clear()
        self.tracks_list.clear()
        self.obstacles_list.clear()
        self.doorhooks_list.clear()

        for room in self.lyt.rooms:
            self.rooms_list.addItem(QListWidgetItem(room.model))

        for track in self.lyt.tracks:
            self.tracks_list.addItem(QListWidgetItem(f"Track {self.lyt.tracks.index(track)}"))

        for obstacle in self.lyt.obstacles:
            self.obstacles_list.addItem(QListWidgetItem(f"Obstacle {self.lyt.obstacles.index(obstacle)}"))

        for doorhook in self.lyt.doorhooks:
            self.doorhooks_list.addItem(QListWidgetItem(f"Door Hook {self.lyt.doorhooks.index(doorhook)}"))

    def update_scene(self):
        self.scene.clear()
        for room in self.lyt.rooms:
            self.add_room_to_scene(room)
        for track in self.lyt.tracks:
            self.add_track_to_scene(track)
        for obstacle in self.lyt.obstacles:
            self.add_obstacle_to_scene(obstacle)
        for doorhook in self.lyt.doorhooks:
            self.add_door_hook_to_scene(doorhook)

    def add_room_to_scene(
        self,
        room: LYTRoom,
    ):
        rect = QGraphicsRectItem(QRectF(room.position.x, room.position.y, room.size.x, room.size.y))
        rect.setBrush(QBrush(QColor(200, 200, 200, 100)))
        rect.setData(0, room)
        self.scene.addItem(rect)

    def add_track_to_scene(
        self,
        track: LYTTrack,
    ):
        line = QGraphicsLineItem(
            track.start_room.position.x,
            track.start_room.position.y,
            track.end_room.position.x,
            track.end_room.position.y,
        )
        line.setPen(QPen(QColor(255, 0, 0), 2))
        line.setData(0, track)
        self.scene.addItem(line)

    def add_obstacle_to_scene(
        self,
        obstacle: LYTObstacle,
    ):
        ellipse: QGraphicsEllipseItem = QGraphicsEllipseItem(
            obstacle.position.x - obstacle.radius,
            obstacle.position.y - obstacle.radius,
            obstacle.radius * 2,
            obstacle.radius * 2,
        )
        ellipse.setBrush(QBrush(QColor(0, 255, 0, 100)))
        ellipse.setData(0, obstacle)
        self.scene.addItem(ellipse)

    def add_door_hook_to_scene(
        self,
        doorhook: LYTDoorHook,
    ):
        rect = QGraphicsRectItem(QRectF(doorhook.position.x - 5, doorhook.position.y - 5, 10, 10))
        rect.setBrush(QBrush(QColor(0, 0, 255, 100)))
        rect.setData(0, doorhook)
        self.scene.addItem(rect)

    def on_room_selected(self, item: QListWidgetItem):
        index: int = self.rooms_list.row(item)
        room: LYTRoom = self.lyt.rooms[index]
        self.select_element_in_scene(room)

    def on_track_selected(self, item: QListWidgetItem):
        index: int = self.tracks_list.row(item)
        track: LYTTrack = self.lyt.tracks[index]
        self.select_element_in_scene(track)

    def on_obstacle_selected(self, item: QListWidgetItem):
        index: int = self.obstacles_list.row(item)
        obstacle: LYTObstacle = self.lyt.obstacles[index]
        self.select_element_in_scene(obstacle)

    def on_doorhook_selected(self, item: QListWidgetItem):
        index: int = self.doorhooks_list.row(item)
        doorhook: LYTDoorHook = self.lyt.doorhooks[index]
        self.select_element_in_scene(doorhook)

    def select_element_in_scene(self, element: Any):
        for item in self.scene.items():
            if item.data(0) == element:
                self.selected_element = item
                item.setSelected(True)
                break

    def mousePressEvent(self, event: QMouseEvent):
        pos = event.pos().toPointF() if qtpy.QT5 else event.position()
        if self.current_tool == "select":
            self.select_element_at(pos)
        elif self.current_tool in ["move", "rotate"]:
            self.start_transform(pos)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.current_tool in ["move", "rotate"] and self.selected_element:
            self.update_transform(event.pos().toPointF() if qtpy.QT5 else event.position())

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.current_tool in ["move", "rotate"] and self.selected_element:
            self.end_transform()

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def zoom_in(self):
        self.graphics_view.scale(1.2, 1.2)

    def zoom_out(self):
        self.graphics_view.scale(1 / 1.2, 1 / 1.2)

    def select_element_at(self, pos: QPointF):
        # Select the element at the given position
        item: QGraphicsItem | None = self.scene.itemAt(self.graphics_view.mapToScene(pos.toPoint()), self.graphics_view.transform())
        if item:
            self.selected_element = item
            item.setSelected(True)

    def start_transform(self, pos: QPointF):
        self.transform_start: QPointF = self.graphics_view.mapToScene(pos.toPoint())

    def update_transform(self, pos: QPointF):
        if not self.selected_element:
            return
        current_pos: QPointF = self.graphics_view.mapToScene(pos.toPoint())
        delta: QPointF = current_pos - self.transform_start
        if self.current_tool == "move":
            self.selected_element.moveBy(delta.x(), delta.y())
        elif self.current_tool == "rotate":
            element = self.selected_element.data(0)
            if isinstance(element, (LYTRoom, LYTObstacle, LYTDoorHook)):
                center = self.selected_element.boundingRect().center()
                angle = math.atan2(delta.y(), delta.x())
                self.selected_element.set_rotation(math.degrees(angle))
        self.transform_start = current_pos

    def end_transform(self):
        if not self.selected_element:
            return
        element = self.selected_element.data(0)
        if isinstance(element, LYTRoom):
            command = MoveRoomCommand(self, element, element.position, Vector3(self.selected_element.pos().x(), self.selected_element.pos().y(), element.position.z))
        elif isinstance(element, LYTObstacle):
            command = MoveObstacleCommand(self, element, element.position, Vector3(self.selected_element.pos().x(), self.selected_element.pos().y(), element.position.z))
        elif isinstance(element, LYTDoorHook):
            command = MoveDoorHookCommand(self, element, element.position, Vector3(self.selected_element.pos().x(), self.selected_element.pos().y(), element.position.z))
        else:
            return
        self.undo_stack.push(command)

class RoomPropertiesDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        room: LYTRoom | None = None,
    ):
        super().__init__(parent)
        from toolset.gui.common.localization import translate as tr
        self.setWindowTitle(tr("Room Properties"))
        self.room: LYTRoom | None = room

        layout = QFormLayout()

        self.model_edit: QLineEdit = QLineEdit(self)
        layout.addRow("Model:", self.model_edit)

        self.pos_x: QDoubleSpinBox = QDoubleSpinBox(self)
        self.pos_y: QDoubleSpinBox = QDoubleSpinBox(self)
        self.pos_z: QDoubleSpinBox = QDoubleSpinBox(self)
        pos_layout: QHBoxLayout = QHBoxLayout()
        pos_layout.addWidget(self.pos_x)
        pos_layout.addWidget(self.pos_y)
        pos_layout.addWidget(self.pos_z)
        layout.addRow("Position (X, Y, Z):", pos_layout)

        self.size_x: QDoubleSpinBox = QDoubleSpinBox(self)
        self.size_y: QDoubleSpinBox = QDoubleSpinBox(self)
        size_layout: QHBoxLayout = QHBoxLayout()
        size_layout.addWidget(self.size_x)
        size_layout.addWidget(self.size_y)
        layout.addRow("Size (Width, Height):", size_layout)

        if room:
            self.model_edit.setText(room.model)
            self.pos_x.setValue(room.position.x)
            self.pos_y.setValue(room.position.y)
            self.pos_z.setValue(room.position.z)
            self.size_x.setValue(room.size.x)
            self.size_y.setValue(room.size.y)

        buttons = QHBoxLayout()
        ok_button: QPushButton = QPushButton("OK")
        cancel_button: QPushButton = QPushButton("Cancel")
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        main_layout: QVBoxLayout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(buttons)

        self.setLayout(main_layout)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def accept(self):
        self.model: str = self.model_edit.text()
        self.position: Vector3 = Vector3(self.pos_x.value(), self.pos_y.value(), self.pos_z.value())
        self.size: Vector3 = Vector3(self.size_x.value(), self.size_y.value(), 0)
        super().accept()

class TrackPropertiesDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        rooms: list[LYTRoom] | None = None,
        track: LYTTrack | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Track Properties")
        self.rooms: list[LYTRoom] = rooms or []
        self.track: LYTTrack | None = track

        layout = QFormLayout()

        self.start_room_combo = QComboBox(self)
        self.end_room_combo = QComboBox(self)
        for room in self.rooms:
            self.start_room_combo.addItem(room.model, room)
            self.end_room_combo.addItem(room.model, room)

        layout.addRow("Start Room:", self.start_room_combo)
        layout.addRow("End Room:", self.end_room_combo)

        if track:
            start_index: int = self.rooms.index(track.start_room)
            end_index: int = self.rooms.index(track.end_room)
            self.start_room_combo.setCurrentIndex(start_index)
            self.end_room_combo.setCurrentIndex(end_index)

        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(buttons)

        self.setLayout(main_layout)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def accept(self):
        self.start_room: LYTRoom = self.start_room_combo.currentData()
        self.end_room: LYTRoom = self.end_room_combo.currentData()
        super().accept()

class ObstaclePropertiesDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        obstacle: LYTObstacle | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Obstacle Properties")
        self.obstacle: LYTObstacle | None = obstacle

        layout = QFormLayout()

        self.pos_x: QDoubleSpinBox = QDoubleSpinBox(self)
        self.pos_y: QDoubleSpinBox = QDoubleSpinBox(self)
        self.pos_z: QDoubleSpinBox = QDoubleSpinBox(self)
        pos_layout: QHBoxLayout = QHBoxLayout()
        pos_layout.addWidget(self.pos_x)
        pos_layout.addWidget(self.pos_y)
        pos_layout.addWidget(self.pos_z)
        layout.addRow("Position (X, Y, Z):", pos_layout)

        self.radius: QDoubleSpinBox = QDoubleSpinBox(self)
        layout.addRow("Radius:", self.radius)

        if obstacle:
            self.pos_x.setValue(obstacle.position.x)
            self.pos_y.setValue(obstacle.position.y)
            self.pos_z.setValue(obstacle.position.z)
            self.radius.setValue(obstacle.radius)

        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(buttons)

        self.setLayout(main_layout)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def accept(self):
        self.position: Vector3 = Vector3(self.pos_x.value(), self.pos_y.value(), self.pos_z.value())
        self.radius: float = self.radius.value()
        super().accept()

class DoorHookPropertiesDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        rooms: list[LYTRoom] | None = None,
        doorhook: LYTDoorHook | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Door Hook Properties")
        self.rooms: list[LYTRoom] = rooms or []
        self.doorhook: LYTDoorHook | None = doorhook

        layout = QFormLayout()

        self.room_combo = QComboBox(self)
        for room in self.rooms:
            self.room_combo.addItem(room.model, room)

        layout.addRow("Room:", self.room_combo)

        self.pos_x: QDoubleSpinBox = QDoubleSpinBox(self)
        self.pos_y: QDoubleSpinBox = QDoubleSpinBox(self)
        self.pos_z: QDoubleSpinBox = QDoubleSpinBox(self)
        pos_layout: QHBoxLayout = QHBoxLayout()
        pos_layout.addWidget(self.pos_x)
        pos_layout.addWidget(self.pos_y)
        pos_layout.addWidget(self.pos_z)
        layout.addRow("Position (X, Y, Z):", pos_layout)

        self.orientation: QDoubleSpinBox = QDoubleSpinBox(self)
        self.orientation.setMinimum(0)
        self.orientation.setMaximum(359.99)
        layout.addRow("Orientation (degrees):", self.orientation)

        if doorhook is not None:
            room_index: int = self.rooms.index(doorhook.room)
            self.room_combo.setCurrentIndex(room_index)
            self.pos_x.setValue(doorhook.position.x)
            self.pos_y.setValue(doorhook.position.y)
            self.pos_z.setValue(doorhook.position.z)
            self.orientation.setValue(math.degrees(doorhook.orientation))

        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(buttons)

        self.setLayout(main_layout)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def accept(self):
        self.room: LYTRoom = self.room_combo.currentData()
        self.position: Vector3 = Vector3(self.pos_x.value(), self.pos_y.value(), self.pos_z.value())
        self.orientation: float = math.radians(self.orientation.value())
        super().accept()

class AddRoomCommand(QUndoCommand):
    def __init__(
        self,
        renderer: LYTRenderer,
        room: LYTRoom,
    ):
        super().__init__("Add Room")
        self.renderer: LYTRenderer = renderer
        self.room: LYTRoom = room

    def redo(self):
        self.editor._lyt.rooms.append(self.room)
        self.editor.add_room_to_scene(self.room)
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def undo(self):
        self.editor._lyt.rooms.remove(self.room)
        for item in self.editor.scene.items():
            if item.data(0) == self.room:
                self.editor.scene.remove_item(item)
                break
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

class EditRoomCommand(QUndoCommand):
    def __init__(
        self,
        editor: LYTEditor,
        room: LYTRoom,
        old_room: LYTRoom,
    ):
        super().__init__("Edit Room")
        self.editor: LYTEditor = editor
        self.room: LYTRoom = room
        self.old_room: LYTRoom = old_room

    def redo(self):
        self.room.position = self.new_position
        self.room.size = self.new_size
        self.room.model = self.new_model
        self.editor.update_scene()
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def undo(self):
        self.room.position = self.old_room.position
        self.room.size = self.old_room.size
        self.room.model = self.old_room.model
        self.editor.update_scene()
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

class DeleteRoomCommand(QUndoCommand):
    def __init__(
        self,
        editor: LYTEditor,
        room: LYTRoom,
    ):
        super().__init__("Delete Room")
        self.editor: LYTEditor = editor
        self.room: LYTRoom = room

    def redo(self):
        self.editor._lyt.rooms.remove(self.room)
        for item in self.editor.scene.items():
            if item.data(0) == self.room:
                self.editor.scene.remove_item(item)
                break
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def undo(self):
        self.editor._lyt.rooms.append(self.room)
        self.editor.add_room_to_scene(self.room)
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

class AddTrackCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, track: LYTTrack):
        super().__init__("Add Track")
        self.editor: LYTEditor = editor
        self.track: LYTTrack = track

    def redo(self):
        self.editor._lyt.tracks.append(self.track)
        self.editor.add_track_to_scene(self.track)
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def undo(self):
        self.editor._lyt.tracks.remove(self.track)
        for item in self.editor.scene.items():
            if item.data(0) == self.track:
                self.editor.scene.removeItem(item)
                break
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

class EditTrackCommand(QUndoCommand):
    def __init__(
        self,
        editor: LYTEditor,
        track: LYTTrack,
        old_track: LYTTrack,
    ):
        super().__init__("Edit Track")
        self.editor: LYTEditor = editor
        self.track: LYTTrack = track
        self.old_track: LYTTrack = old_track

    def redo(self):
        self.track.start_room = self.new_start_room
        self.track.end_room = self.new_end_room
        self.editor.update_scene()
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def undo(self):
        self.track.start_room = self.old_track.start_room
        self.track.end_room = self.old_track.end_room
        self.editor.update_scene()
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

class DeleteTrackCommand(QUndoCommand):
    def __init__(
        self,
        editor: LYTEditor,
        track: LYTTrack,
    ):
        super().__init__("Delete Track")
        self.editor: LYTEditor = editor
        self.track: LYTTrack = track

    def redo(self):
        self.editor._lyt.tracks.remove(self.track)
        for item in self.editor.scene.items():
            if item.data(0) == self.track:
                self.editor.scene.remove_item(item)
                break
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def undo(self):
        self.editor._lyt.tracks.append(self.track)
        self.editor.add_track_to_scene(self.track)
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

class AddObstacleCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, obstacle: LYTObstacle):
        super().__init__("Add Obstacle")
        self.editor: LYTEditor = editor
        self.obstacle: LYTObstacle = obstacle

    def redo(self):
        self.editor._lyt.obstacles.append(self.obstacle)
        self.editor.add_obstacle_to_scene(self.obstacle)
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def undo(self):
        self.editor._lyt.obstacles.remove(self.obstacle)
        for item in self.editor.scene.items():
            if item.data(0) == self.obstacle:
                self.editor.scene.remove_item(item)
                break
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

class EditObstacleCommand(QUndoCommand):
    def __init__(
        self,
        editor: LYTEditor,
        obstacle: LYTObstacle,
        old_obstacle: LYTObstacle,
    ):
        super().__init__("Edit Obstacle")
        self.editor: LYTEditor = editor
        self.obstacle: LYTObstacle = obstacle
        self.old_obstacle: LYTObstacle = old_obstacle

    def redo(self):
        self.obstacle.position = self.new_position
        self.obstacle.radius = self.new_radius
        self.editor.update_scene()
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def undo(self):
        self.obstacle.position = self.old_obstacle.position
        self.obstacle.radius = self.old_obstacle.radius
        self.editor.update_scene()
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

class DeleteObstacleCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, obstacle: LYTObstacle):
        super().__init__("Delete Obstacle")
        self.editor: LYTEditor = editor
        self.obstacle: LYTObstacle = obstacle

    def redo(self):
        self.editor._lyt.obstacles.remove(self.obstacle)
        for item in self.editor.scene.items():
            if item.data(0) == self.obstacle:
                self.editor.scene.removeItem(item)
                break
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def undo(self):
        self.editor._lyt.obstacles.append(self.obstacle)
        self.editor.add_obstacle_to_scene(self.obstacle)
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

class AddDoorHookCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, doorhook: LYTDoorHook):
        super().__init__("Add Door Hook")
        self.editor: LYTEditor = editor
        self.doorhook: LYTDoorHook = doorhook

    def redo(self):
        self.editor._lyt.doorhooks.append(self.doorhook)
        self.editor.add_doorhook_to_scene(self.doorhook)
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def undo(self):
        self.editor._lyt.doorhooks.remove(self.doorhook)
        for item in self.editor.scene.items():
            if item.data(0) == self.doorhook:
                self.editor.scene.removeItem(item)
                break
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

class EditDoorHookCommand(QUndoCommand):
    def __init__(
        self,
        editor: LYTEditor,
        doorhook: LYTDoorHook,
        old_doorhook: LYTDoorHook,
    ):
        super().__init__("Edit Door Hook")
        self.editor: LYTEditor = editor
        self.doorhook: LYTDoorHook = doorhook
        self.old_doorhook: LYTDoorHook = old_doorhook

    def redo(self):
        self.doorhook.room = self.new_room
        self.doorhook.position = self.new_position
        self.doorhook.orientation = self.new_orientation
        self.editor.update_scene()
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def undo(self):
        self.doorhook.room = self.old_doorhook.room
        self.doorhook.position = self.old_doorhook.position
        self.doorhook.orientation = self.old_doorhook.orientation
        self.editor.update_scene()
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

class DeleteDoorHookCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, doorhook: LYTDoorHook):
        super().__init__("Delete Door Hook")
        self.editor: LYTEditor = editor
        self.doorhook: LYTDoorHook = doorhook

    def redo(self):
        self.editor._lyt.doorhooks.remove(self.doorhook)
        for item in self.editor.scene.items():
            if item.data(0) == self.doorhook:
                self.editor.scene.removeItem(item)
                break
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def undo(self):
        self.editor._lyt.doorhooks.append(self.doorhook)
        self.editor.add_doorhook_to_scene(self.doorhook)
        self.editor.update_lists()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

class MoveRoomCommand(QUndoCommand):
    def __init__(
        self,
        editor: LYTEditor,
        room: LYTRoom,
        old_pos: Vector3,
        new_pos: Vector3,
    ):
        super().__init__("Move Room")
        self.editor: LYTEditor = editor
        self.room: LYTRoom = room
        self.old_pos: Vector3 = old_pos
        self.new_pos: Vector3 = new_pos

    def redo(self):
        self.room.position = self.new_pos
        self.update_scene_item()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def undo(self):
        self.room.position = self.old_pos
        self.update_scene_item()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def update_scene_item(self):
        for item in self.editor.scene.items():
            if item.data(0) == self.room:
                item.setPos(self.room.position.x, self.room.position.y)
                break

class MoveObstacleCommand(QUndoCommand):
    def __init__(
        self,
        editor: LYTEditor,
        obstacle: LYTObstacle,
        old_pos: Vector3,
        new_pos: Vector3,
    ):
        super().__init__("Move Obstacle")
        self.editor = editor
        self.obstacle: LYTObstacle = obstacle
        self.old_pos: Vector3 = old_pos
        self.new_pos: Vector3 = new_pos

    def redo(self):
        self.obstacle.position = self.new_pos
        self.update_scene_item()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def undo(self):
        self.obstacle.position = self.old_pos
        self.update_scene_item()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def update_scene_item(self):
        for item in self.editor.scene.items():
            if item.data(0) == self.obstacle:
                item.setPos(self.obstacle.position.x - self.obstacle.radius,
                            self.obstacle.position.y - self.obstacle.radius)
                break

class MoveDoorHookCommand(QUndoCommand):
    def __init__(
        self,
        editor: LYTEditor,
        doorhook: LYTDoorHook,
        old_pos: Vector3,
        new_pos: Vector3,
    ):
        super().__init__("Move Door Hook")
        self.editor: LYTEditor = editor
        self.doorhook: LYTDoorHook = doorhook
        self.old_pos: Vector3 = old_pos
        self.new_pos: Vector3 = new_pos

    def redo(self):
        self.doorhook.position = self.new_pos
        self.update_scene_item()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def undo(self):
        self.doorhook.position = self.old_pos
        self.update_scene_item()
        self.editor.sig_lyt_updated.emit(self.editor._lyt)

    def update_scene_item(self):
        for item in self.editor.scene.items():
            if item.data(0) == self.doorhook:
                item.setPos(self.doorhook.position.x - 5, self.doorhook.position.y - 5)
                break
