from __future__ import annotations

import math

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from qtpy.QtCore import QRectF, Qt, pyqtSignal as Signal
from qtpy.QtGui import QBrush, QColor, QPainter, QPen
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGraphicsEllipseItem,
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

from pykotor.common.geometry import Vector3
from pykotor.resource.formats.bwm.bwm_data import BWM
from pykotor.resource.formats.lyt.lyt_data import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack
from toolset.gui.widgets.renderer.texture_browser import TextureBrowser

if TYPE_CHECKING:
    from qtpy.QtCore import QPointF
    from qtpy.QtGui import QMouseEvent, QWheelEvent
    from qtpy.QtWidgets import QGraphicsItem


class LYTEditor(QWidget):
    sig_lyt_updated = Signal(LYT)
    sig_walkmesh_updated = Signal(BWM)

    def __init__(self, parent):
        super().__init__(parent)
        self.lyt: LYT = LYT()
        self.scene = QGraphicsScene(self)
        self.selected_element: Optional[QGraphicsItem] = None
        self.current_tool: str = "select"
        
        self.undo_stack: QUndoStack = QUndoStack(self)
        
        self.texture_browser: TextureBrowser = TextureBrowser(self)
        self.textures: Dict[str, str] = {}
        
        self.walkmesh: Optional[BWM] = None
        
        self.initUI()
        self.init_connections()

    def initUI(self):
        loadUi("Tools/HolocronToolset/src/ui/widgets/renderer/lyt_editor.ui", self)
        self.graphicsView.setScene(self.scene)
        self.graphicsView.setRenderHint(QPainter.Antialiasing)
        
        self.add_room_button.clicked.connect(self.add_room)
        self.editRoomButton.clicked.connect(self.editRoom)
        self.deleteRoomButton.clicked.connect(self.deleteRoom)
        
        self.add_track_button.clicked.connect(self.add_track)
        self.editTrackButton.clicked.connect(self.editTrack)
        self.deleteTrackButton.clicked.connect(self.deleteTrack)
        
        self.addObstacleButton.clicked.connect(self.add_obstacle)
        self.editObstacleButton.clicked.connect(self.editObstacle)
        self.deleteObstacleButton.clicked.connect(self.deleteObstacle)
        
        self.addDoorhookButton.clicked.connect(self.add_door_hook)
        self.editDoorhookButton.clicked.connect(self.editDoorHook)
        self.deleteDoorhookButton.clicked.connect(self.deleteDoorHook)
        
        self.generateWalkmeshButton.clicked.connect(self.generate_walkmesh)
        
        self.zoom_slider.valueChanged.connect(self.update_zoom)

    def init_connections(self):
        self.roomsList.itemClicked.connect(self.onRoomSelected)
        self.tracksList.itemClicked.connect(self.onTrackSelected)
        self.obstaclesList.itemClicked.connect(self.onObstacleSelected)
        self.doorhooksList.itemClicked.connect(self.onDoorhookSelected)

    def set_lyt(self, lyt: LYT):
        self.lyt = lyt
        self.updateLists()
        self.updateScene()
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

    def editRoom(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsRectItem):
            room = self.selected_element.data(0)
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

    def deleteRoom(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsRectItem):
            room = self.selected_element.data(0)
            command = DeleteRoomCommand(self, room)
            self.undo_stack.push(command)

    def add_track(self):
        if len(self.lyt.rooms) < 2:
            QMessageBox.warning(self, "Add Track", "At least two rooms are required to add a track.")
            return
        dialog = TrackPropertiesDialog(self, self.lyt.rooms)
        if dialog.exec():
            track = LYTTrack()
            track.start_room = dialog.start_room
            track.end_room = dialog.end_room
            command = AddTrackCommand(self, track)
            self.undo_stack.push(command)

    def editTrack(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsLineItem):
            track = self.selected_element.data(0)
            dialog = TrackPropertiesDialog(self, self.lyt.rooms, track)
            if dialog.exec():
                old_track = LYTTrack()
                old_track.start_room = track.start_room
                old_track.end_room = track.end_room
                
                track.start_room = dialog.start_room
                track.end_room = dialog.end_room
                
                command = EditTrackCommand(self, track, old_track)
                self.undo_stack.push(command)

    def deleteTrack(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsLineItem):
            track = self.selected_element.data(0)
            command = DeleteTrackCommand(self, track)
            self.undo_stack.push(command)

    def add_obstacle(self):
        dialog = ObstaclePropertiesDialog(self)
        if dialog.exec():
            obstacle = LYTObstacle()
            obstacle.position = dialog.position
            obstacle.radius = dialog.radius
            command = AddObstacleCommand(self, obstacle)
            self.undo_stack.push(command)

    def editObstacle(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsEllipseItem):
            obstacle = self.selected_element.data(0)
            dialog = ObstaclePropertiesDialog(self, obstacle)
            if dialog.exec():
                old_obstacle = LYTObstacle()
                old_obstacle.position = obstacle.position
                old_obstacle.radius = obstacle.radius
                
                obstacle.position = dialog.position
                obstacle.radius = dialog.radius
                
                command = EditObstacleCommand(self, obstacle, old_obstacle)
                self.undo_stack.push(command)

    def deleteObstacle(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsEllipseItem):
            obstacle = self.selected_element.data(0)
            command = DeleteObstacleCommand(self, obstacle)
            self.undo_stack.push(command)

    def add_door_hook(self):
        if not self.lyt.rooms:
            QMessageBox.warning(self, "Add Door Hook", "At least one room is required to add a door hook.")
            return
        dialog = DoorHookPropertiesDialog(self, self.lyt.rooms)
        if dialog.exec():
            doorhook = LYTDoorHook()
            doorhook.room = dialog.room
            doorhook.position = dialog.position
            doorhook.orientation = dialog.orientation
            command = AddDoorHookCommand(self, doorhook)
            self.undo_stack.push(command)

    def editDoorHook(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsRectItem):
            doorhook = self.selected_element.data(0)
            dialog = DoorHookPropertiesDialog(self, self.lyt.rooms, doorhook)
            if dialog.exec():
                old_doorhook = LYTDoorHook()
                old_doorhook.room = doorhook.room
                old_doorhook.position = doorhook.position
                old_doorhook.orientation = doorhook.orientation
                
                doorhook.room = dialog.room
                doorhook.position = dialog.position
                doorhook.orientation = dialog.orientation
                
                command = EditDoorHookCommand(self, doorhook, old_doorhook)
                self.undo_stack.push(command)

    def deleteDoorHook(self):
        if self.selected_element and isinstance(self.selected_element, QGraphicsRectItem):
            doorhook = self.selected_element.data(0)
            command = DeleteDoorHookCommand(self, doorhook)
            self.undo_stack.push(command)

    def generate_walkmesh(self):
        self.walkmesh = BWM()
        for room in self.lyt.rooms:
            self.addRoomToWalkmesh(room)
        for obstacle in self.lyt.obstacles:
            self.addObstacleToWalkmesh(obstacle)
        self.sig_walkmesh_updated.emit(self.walkmesh)

    def addRoomToWalkmesh(self, room: LYTRoom):
        # Create a simple rectangular walkmesh for the room
        x, y, z = room.position.x, room.position.y, room.position.z
        width, height = room.size.x, room.size.y
        
        vertices = [
            (x, y, z),
            (x + width, y, z),
            (x + width, y + height, z),
            (x, y + height, z)
        ]
        
        faces = [
            (0, 1, 2),
            (0, 2, 3)
        ]
        
        for face in faces:
            self.walkmesh.add_face([Vector3(*vertices[i]) for i in face])

    def addObstacleToWalkmesh(self, obstacle: LYTObstacle):
        # Create a simple circular walkmesh for the obstacle
        x, y, z = obstacle.position.x, obstacle.position.y, obstacle.position.z
        radius = obstacle.radius
        num_segments = 16
        
        vertices = []
        for i in range(num_segments):
            angle = 2 * math.pi * i / num_segments
            vx = x + radius * math.cos(angle)
            vy = y + radius * math.sin(angle)
            vertices.append((vx, vy, z))
        
        center = (x, y, z)
        vertices.append(center)
        
        for i in range(num_segments):
            j = (i + 1) % num_segments
            self.walkmesh.add_face([
                Vector3(*vertices[i]),
                Vector3(*vertices[j]),
                Vector3(*center)
            ])

    def update_zoom(self, value: int):
        zoom_factor = value / 100.0
        self.graphicsView.resetTransform()
        self.graphicsView.scale(zoom_factor, zoom_factor)

    def updateLists(self):
        self.roomsList.clear()
        self.tracksList.clear()
        self.obstaclesList.clear()
        self.doorhooksList.clear()
        
        for room in self.lyt.rooms:
            self.roomsList.addItem(QListWidgetItem(room.model))
        
        for track in self.lyt.tracks:
            self.tracksList.addItem(QListWidgetItem(f"Track {self.lyt.tracks.index(track)}"))
        
        for obstacle in self.lyt.obstacles:
            self.obstaclesList.addItem(QListWidgetItem(f"Obstacle {self.lyt.obstacles.index(obstacle)}"))
        
        for doorhook in self.lyt.doorhooks:
            self.doorhooksList.addItem(QListWidgetItem(f"Door Hook {self.lyt.doorhooks.index(doorhook)}"))

    def updateScene(self):
        self.scene.clear()
        for room in self.lyt.rooms:
            self.addRoomToScene(room)
        for track in self.lyt.tracks:
            self.addTrackToScene(track)
        for obstacle in self.lyt.obstacles:
            self.addObstacleToScene(obstacle)
        for doorhook in self.lyt.doorhooks:
            self.addDoorHookToScene(doorhook)

    def addRoomToScene(self, room: LYTRoom):
        rect = QGraphicsRectItem(QRectF(room.position.x, room.position.y, room.size.x, room.size.y))
        rect.setBrush(QBrush(QColor(200, 200, 200, 100)))
        rect.setData(0, room)
        self.scene.addItem(rect)

    def addTrackToScene(self, track: LYTTrack):
        line = QGraphicsLineItem(track.start_room.position.x, track.start_room.position.y,
                                 track.end_room.position.x, track.end_room.position.y)
        line.setPen(QPen(QColor(255, 0, 0), 2))
        line.setData(0, track)
        self.scene.addItem(line)

    def addObstacleToScene(self, obstacle: LYTObstacle):
        ellipse = QGraphicsEllipseItem(obstacle.position.x - obstacle.radius,
                                       obstacle.position.y - obstacle.radius,
                                       obstacle.radius * 2, obstacle.radius * 2)
        ellipse.setBrush(QBrush(QColor(0, 255, 0, 100)))
        ellipse.setData(0, obstacle)
        self.scene.addItem(ellipse)

    def addDoorHookToScene(self, doorhook: LYTDoorHook):
        rect = QGraphicsRectItem(QRectF(doorhook.position.x - 5, doorhook.position.y - 5, 10, 10))
        rect.setBrush(QBrush(QColor(0, 0, 255, 100)))
        rect.setData(0, doorhook)
        self.scene.addItem(rect)

    def onRoomSelected(self, item: QListWidgetItem):
        index = self.roomsList.row(item)
        room = self.lyt.rooms[index]
        self.selectElementInScene(room)

    def onTrackSelected(self, item: QListWidgetItem):
        index = self.tracksList.row(item)
        track = self.lyt.tracks[index]
        self.selectElementInScene(track)

    def onObstacleSelected(self, item: QListWidgetItem):
        index = self.obstaclesList.row(item)
        obstacle = self.lyt.obstacles[index]
        self.selectElementInScene(obstacle)

    def onDoorhookSelected(self, item: QListWidgetItem):
        index = self.doorhooksList.row(item)
        doorhook = self.lyt.doorhooks[index]
        self.selectElementInScene(doorhook)

    def selectElementInScene(self, element: Any):
        for item in self.scene.items():
            if item.data(0) == element:
                self.selected_element = item
                item.setSelected(True)
                break

    def mousePressEvent(self, event: QMouseEvent):
        if self.current_tool == "select":
            self.selectElementAt(event.pos())
        elif self.current_tool in ["move", "rotate"]:
            self.startTransform(event.pos())

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.current_tool in ["move", "rotate"] and self.selected_element:
            self.updateTransform(event.pos())

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.current_tool in ["move", "rotate"] and self.selected_element:
            self.endTransform()

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoomIn()
            else:
                self.zoomOut()
            event.accept()
        else:
            super().wheelEvent(event)

    def zoomIn(self):
        self.graphicsView.scale(1.2, 1.2)

    def zoomOut(self):
        self.graphicsView.scale(1 / 1.2, 1 / 1.2)

    def selectElementAt(self, pos: QPointF):
        item = self.scene.itemAt(self.graphicsView.mapToScene(pos.toPoint()), self.graphicsView.transform())
        if item:
            self.selected_element = item
            item.setSelected(True)

    def startTransform(self, pos: QPointF):
        self.transform_start = self.graphicsView.mapToScene(pos.toPoint())

    def updateTransform(self, pos: QPointF):
        if not self.selected_element:
            return
        current_pos = self.graphicsView.mapToScene(pos.toPoint())
        delta = current_pos - self.transform_start
        if self.current_tool == "move":
            self.selected_element.moveBy(delta.x(), delta.y())
        elif self.current_tool == "rotate":
            element = self.selected_element.data(0)
            if isinstance(element, (LYTRoom, LYTObstacle, LYTDoorHook)):
                center = self.selected_element.boundingRect().center()
                angle = math.atan2(delta.y(), delta.x())
                self.selected_element.set_rotation(math.degrees(angle))
        self.transform_start = current_pos

    def endTransform(self):
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
    def __init__(self, parent=None, room: Optional[LYTRoom] = None):
        super().__init__(parent)
        self.setWindowTitle("Room Properties")
        self.room = room

        layout = QFormLayout()

        self.model_edit = QLineEdit(self)
        layout.addRow("Model:", self.model_edit)

        self.pos_x = QDoubleSpinBox(self)
        self.pos_y = QDoubleSpinBox(self)
        self.pos_z = QDoubleSpinBox(self)
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(self.pos_x)
        pos_layout.addWidget(self.pos_y)
        pos_layout.addWidget(self.pos_z)
        layout.addRow("Position (X, Y, Z):", pos_layout)

        self.size_x = QDoubleSpinBox(self)
        self.size_y = QDoubleSpinBox(self)
        size_layout = QHBoxLayout()
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

    def accept(self):
        self.model = self.model_edit.text()
        self.position = Vector3(self.pos_x.value(), self.pos_y.value(), self.pos_z.value())
        self.size = Vector3(self.size_x.value(), self.size_y.value(), 0)
        super().accept()

class TrackPropertiesDialog(QDialog):
    def __init__(self, parent=None, rooms: List[LYTRoom] = None, track: Optional[LYTTrack] = None):
        super().__init__(parent)
        self.setWindowTitle("Track Properties")
        self.rooms = rooms or []
        self.track = track

        layout = QFormLayout()

        self.start_room_combo = QComboBox(self)
        self.end_room_combo = QComboBox(self)
        for room in self.rooms:
            self.start_room_combo.addItem(room.model, room)
            self.end_room_combo.addItem(room.model, room)

        layout.addRow("Start Room:", self.start_room_combo)
        layout.addRow("End Room:", self.end_room_combo)

        if track:
            start_index = self.rooms.index(track.start_room)
            end_index = self.rooms.index(track.end_room)
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

    def accept(self):
        self.start_room = self.start_room_combo.currentData()
        self.end_room = self.end_room_combo.currentData()
        super().accept()

class ObstaclePropertiesDialog(QDialog):
    def __init__(self, parent=None, obstacle: Optional[LYTObstacle] = None):
        super().__init__(parent)
        self.setWindowTitle("Obstacle Properties")
        self.obstacle = obstacle

        layout = QFormLayout()

        self.pos_x = QDoubleSpinBox(self)
        self.pos_y = QDoubleSpinBox(self)
        self.pos_z = QDoubleSpinBox(self)
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(self.pos_x)
        pos_layout.addWidget(self.pos_y)
        pos_layout.addWidget(self.pos_z)
        layout.addRow("Position (X, Y, Z):", pos_layout)

        self.radius = QDoubleSpinBox(self)
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

    def accept(self):
        self.position = Vector3(self.pos_x.value(), self.pos_y.value(), self.pos_z.value())
        self.radius = self.radius.value()
        super().accept()

class DoorHookPropertiesDialog(QDialog):
    def __init__(self, parent=None, rooms: List[LYTRoom] = None, doorhook: Optional[LYTDoorHook] = None):
        super().__init__(parent)
        self.setWindowTitle("Door Hook Properties")
        self.rooms = rooms or []
        self.doorhook = doorhook

        layout = QFormLayout()

        self.room_combo = QComboBox(self)
        for room in self.rooms:
            self.room_combo.addItem(room.model, room)

        layout.addRow("Room:", self.room_combo)

        self.pos_x = QDoubleSpinBox(self)
        self.pos_y = QDoubleSpinBox(self)
        self.pos_z = QDoubleSpinBox(self)
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(self.pos_x)
        pos_layout.addWidget(self.pos_y)
        pos_layout.addWidget(self.pos_z)
        layout.addRow("Position (X, Y, Z):", pos_layout)

        self.orientation = QDoubleSpinBox(self)
        self.orientation.setMinimum(0)
        self.orientation.setMaximum(359.99)
        layout.addRow("Orientation (degrees):", self.orientation)

        if doorhook:
            room_index = self.rooms.index(doorhook.room)
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

    def accept(self):
        self.room = self.room_combo.currentData()
        self.position = Vector3(self.pos_x.value(), self.pos_y.value(), self.pos_z.value())
        self.orientation = math.radians(self.orientation.value())
        super().accept()

class AddRoomCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, room: LYTRoom):
        super().__init__("Add Room")
        self.editor = editor
        self.room = room

    def redo(self):
        self.editor.lyt.rooms.append(self.room)
        self.editor.addRoomToScene(self.room)
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def undo(self):
        self.editor.lyt.rooms.remove(self.room)
        for item in self.editor.scene.items():
            if item.data(0) == self.room:
                self.editor.scene.removeItem(item)
                break
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

class EditRoomCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, room: LYTRoom, old_room: LYTRoom):
        super().__init__("Edit Room")
        self.editor = editor
        self.room = room
        self.old_room = old_room

    def redo(self):
        self.room.position = self.new_position
        self.room.size = self.new_size
        self.room.model = self.new_model
        self.editor.updateScene()
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def undo(self):
        self.room.position = self.old_room.position
        self.room.size = self.old_room.size
        self.room.model = self.old_room.model
        self.editor.updateScene()
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

class DeleteRoomCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, room: LYTRoom):
        super().__init__("Delete Room")
        self.editor = editor
        self.room = room

    def redo(self):
        self.editor.lyt.rooms.remove(self.room)
        for item in self.editor.scene.items():
            if item.data(0) == self.room:
                self.editor.scene.removeItem(item)
                break
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def undo(self):
        self.editor.lyt.rooms.append(self.room)
        self.editor.addRoomToScene(self.room)
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

class AddTrackCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, track: LYTTrack):
        super().__init__("Add Track")
        self.editor = editor
        self.track = track

    def redo(self):
        self.editor.lyt.tracks.append(self.track)
        self.editor.addTrackToScene(self.track)
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def undo(self):
        self.editor.lyt.tracks.remove(self.track)
        for item in self.editor.scene.items():
            if item.data(0) == self.track:
                self.editor.scene.removeItem(item)
                break
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

class EditTrackCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, track: LYTTrack, old_track: LYTTrack):
        super().__init__("Edit Track")
        self.editor = editor
        self.track = track
        self.old_track = old_track

    def redo(self):
        self.track.start_room = self.new_start_room
        self.track.end_room = self.new_end_room
        self.editor.updateScene()
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def undo(self):
        self.track.start_room = self.old_track.start_room
        self.track.end_room = self.old_track.end_room
        self.editor.updateScene()
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

class DeleteTrackCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, track: LYTTrack):
        super().__init__("Delete Track")
        self.editor = editor
        self.track = track

    def redo(self):
        self.editor.lyt.tracks.remove(self.track)
        for item in self.editor.scene.items():
            if item.data(0) == self.track:
                self.editor.scene.removeItem(item)
                break
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def undo(self):
        self.editor.lyt.tracks.append(self.track)
        self.editor.addTrackToScene(self.track)
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

class AddObstacleCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, obstacle: LYTObstacle):
        super().__init__("Add Obstacle")
        self.editor = editor
        self.obstacle = obstacle

    def redo(self):
        self.editor.lyt.obstacles.append(self.obstacle)
        self.editor.addObstacleToScene(self.obstacle)
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def undo(self):
        self.editor.lyt.obstacles.remove(self.obstacle)
        for item in self.editor.scene.items():
            if item.data(0) == self.obstacle:
                self.editor.scene.removeItem(item)
                break
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

class EditObstacleCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, obstacle: LYTObstacle, old_obstacle: LYTObstacle):
        super().__init__("Edit Obstacle")
        self.editor = editor
        self.obstacle = obstacle
        self.old_obstacle = old_obstacle

    def redo(self):
        self.obstacle.position = self.new_position
        self.obstacle.radius = self.new_radius
        self.editor.updateScene()
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def undo(self):
        self.obstacle.position = self.old_obstacle.position
        self.obstacle.radius = self.old_obstacle.radius
        self.editor.updateScene()
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

class DeleteObstacleCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, obstacle: LYTObstacle):
        super().__init__("Delete Obstacle")
        self.editor = editor
        self.obstacle = obstacle

    def redo(self):
        self.editor.lyt.obstacles.remove(self.obstacle)
        for item in self.editor.scene.items():
            if item.data(0) == self.obstacle:
                self.editor.scene.removeItem(item)
                break
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def undo(self):
        self.editor.lyt.obstacles.append(self.obstacle)
        self.editor.addObstacleToScene(self.obstacle)
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

class AddDoorHookCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, doorhook: LYTDoorHook):
        super().__init__("Add Door Hook")
        self.editor = editor
        self.doorhook = doorhook

    def redo(self):
        self.editor.lyt.doorhooks.append(self.doorhook)
        self.editor.addDoorHookToScene(self.doorhook)
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def undo(self):
        self.editor.lyt.doorhooks.remove(self.doorhook)
        for item in self.editor.scene.items():
            if item.data(0) == self.doorhook:
                self.editor.scene.removeItem(item)
                break
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

class EditDoorHookCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, doorhook: LYTDoorHook, old_doorhook: LYTDoorHook):
        super().__init__("Edit Door Hook")
        self.editor = editor
        self.doorhook = doorhook
        self.old_doorhook = old_doorhook

    def redo(self):
        self.doorhook.room = self.new_room
        self.doorhook.position = self.new_position
        self.doorhook.orientation = self.new_orientation
        self.editor.updateScene()
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def undo(self):
        self.doorhook.room = self.old_doorhook.room
        self.doorhook.position = self.old_doorhook.position
        self.doorhook.orientation = self.old_doorhook.orientation
        self.editor.updateScene()
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

class DeleteDoorHookCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, doorhook: LYTDoorHook):
        super().__init__("Delete Door Hook")
        self.editor = editor
        self.doorhook = doorhook

    def redo(self):
        self.editor.lyt.doorhooks.remove(self.doorhook)
        for item in self.editor.scene.items():
            if item.data(0) == self.doorhook:
                self.editor.scene.removeItem(item)
                break
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def undo(self):
        self.editor.lyt.doorhooks.append(self.doorhook)
        self.editor.addDoorHookToScene(self.doorhook)
        self.editor.updateLists()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

class MoveRoomCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, room: LYTRoom, old_pos: Vector3, new_pos: Vector3):
        super().__init__("Move Room")
        self.editor = editor
        self.room = room
        self.old_pos = old_pos
        self.new_pos = new_pos

    def redo(self):
        self.room.position = self.new_pos
        self.updateSceneItem()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def undo(self):
        self.room.position = self.old_pos
        self.updateSceneItem()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def updateSceneItem(self):
        for item in self.editor.scene.items():
            if item.data(0) == self.room:
                item.setPos(self.room.position.x, self.room.position.y)
                break

class MoveObstacleCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, obstacle: LYTObstacle, old_pos: Vector3, new_pos: Vector3):
        super().__init__("Move Obstacle")
        self.editor = editor
        self.obstacle = obstacle
        self.old_pos = old_pos
        self.new_pos = new_pos

    def redo(self):
        self.obstacle.position = self.new_pos
        self.updateSceneItem()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def undo(self):
        self.obstacle.position = self.old_pos
        self.updateSceneItem()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def updateSceneItem(self):
        for item in self.editor.scene.items():
            if item.data(0) == self.obstacle:
                item.setPos(self.obstacle.position.x - self.obstacle.radius,
                            self.obstacle.position.y - self.obstacle.radius)
                break

class MoveDoorHookCommand(QUndoCommand):
    def __init__(self, editor: LYTEditor, doorhook: LYTDoorHook, old_pos: Vector3, new_pos: Vector3):
        super().__init__("Move Door Hook")
        self.editor = editor
        self.doorhook = doorhook
        self.old_pos = old_pos
        self.new_pos = new_pos

    def redo(self):
        self.doorhook.position = self.new_pos
        self.updateSceneItem()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def undo(self):
        self.doorhook.position = self.old_pos
        self.updateSceneItem()
        self.editor.sig_lyt_updated.emit(self.editor.lyt)

    def updateSceneItem(self):
        for item in self.editor.scene.items():
            if item.data(0) == self.doorhook:
                item.setPos(self.doorhook.position.x - 5, self.doorhook.position.y - 5)
                break
