from __future__ import annotations

import math
import multiprocessing
import queue

from copy import deepcopy
from queue import Empty
from threading import Lock
from typing import TYPE_CHECKING, Any, Callable, Optional

from qtpy.QtCore import QEvent, QLine, QMutex, QMutexLocker, QPoint, QRect, QThread, Qt, Signal  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtGui import QBrush, QColor, QPainter, QPen
from qtpy.QtWidgets import QApplication, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSlider, QVBoxLayout, QWidget

from pykotor.common.geometry import Vector2, Vector3
from pykotor.resource.formats.bwm import BWM, BWMFace
from pykotor.resource.formats.lyt import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack
from toolset.gui.widgets.renderer.texture_browser import TextureBrowser
from utility.system.app_process.task_consumer import TaskConsumer

if TYPE_CHECKING:
    from qtpy.QtGui import QDragEnterEvent, QDropEvent, QKeyEvent, QMouseEvent

    from pykotor.resource.formats.lyt.lyt_data import LYTRoomTemplate
    from toolset.gui.widgets.renderer.module import ModuleRenderer


class LYTEditor(QWidget):
    roomPlaced: Signal = Signal(object)
    roomMoved: Signal = Signal(object, object)
    roomResized: Signal = Signal(object, object)
    roomRotated: Signal = Signal(object, float)
    doorHookPlaced: Signal = Signal(object)
    textureChanged: Signal = Signal(object)
    lytUpdated: Signal = Signal(object)
    walkmeshUpdated: Signal = Signal(object)
    taskCompleted: Signal = Signal(object)
    renderingOptimized: Signal = Signal()

    def __init__(self, parent: ModuleRenderer):
        super().__init__(parent)
        self.setParent(parent)
        self.lyt: LYT = LYT()
        self.selectedRoom: LYTRoom | None = None
        self.selectedTrack: LYTTrack | None = None
        self.selectedObstacle: LYTObstacle | None = None
        self.selectedDoorHook: LYTDoorHook | None = None
        self.gridSize: int = 10
        self._snapToGrid: bool = True
        self._showGrid: bool = True
        self.mouseDown: set[int] = set()
        self.mousePos: Vector2 = Vector2(0, 0)
        self.mousePrev: Vector2 = Vector2(0, 0)
        self.isDragging: bool = False
        self.isResizing: bool = False
        self.isRotating: bool = False
        self.isPlacingDoorHook: bool = False
        self.selectedRoomResizeCorner: int | None = None
        self.selectedRoomRotationPoint: Vector2 | None = None
        self.walkmesh: BWM | None = None
        self.isEditingWalkmesh: bool = False
        self.selectedWalkmeshFace: BWMFace | None = None

        self.roomTemplates: list[LYTRoomTemplate] = []  # list to store room templates
        self.textureBrowser: TextureBrowser = TextureBrowser(self)
        self.textures: dict[str, str] = {}  # dictionary to store texture names and paths

        self.task_consumers: list[TaskConsumer] = [
            TaskConsumer(
                task_queue=self.task_queue,
                result_queue=self.changes_queue,
                error_queue=self.error_queue,
                lock=self.task_queue_lock,
            )
            for _ in range(4)
        ]
        self.task_consumer_lock: Lock = Lock()
        self.task_queue: multiprocessing.JoinableQueue[tuple[Callable[..., Any], tuple, dict]] = multiprocessing.JoinableQueue()
        self.spatial_grid: dict[tuple[int, int], list[LYTRoom]] = {}
        self.grid_size: int = 1000
        self.lyt_lock: Lock = Lock()
        self.texture_lock: Lock = Lock()
        self.task_queue_lock: Lock = Lock()
        self.is_shutting_down: bool = False
        self.main_thread_tasks: multiprocessing.Queue[tuple[Callable[..., Any], tuple, dict]] = multiprocessing.Queue()
        self.error_queue: multiprocessing.Queue[tuple[Callable[..., Any], Exception]] = multiprocessing.Queue()
        self.changes_queue: multiprocessing.Queue[tuple[str, str, Any]] = multiprocessing.Queue()
        self.change_buffer: list[tuple[str, str, Any]] = []
        self.change_lock: Lock = Lock()
        self.render_lock: QMutex = QMutex(QMutex.RecursionMode.Recursive)  # New lock for rendering

        self.initUI()

    def initUI(self):
        self.setAcceptDrops(True)

        layout = QVBoxLayout()

        # Add buttons for LYT editing operations
        buttonLayout = QHBoxLayout()
        addRoomButton = QPushButton("Add Room")
        addRoomButton.clicked.connect(self.addRoom)
        buttonLayout.addWidget(addRoomButton)

        addTrackButton = QPushButton("Add Track")
        addTrackButton.clicked.connect(self.addTrack)
        buttonLayout.addWidget(addTrackButton)

        addObstacleButton = QPushButton("Add Obstacle")
        addObstacleButton.clicked.connect(self.addObstacle)
        buttonLayout.addWidget(addObstacleButton)

        placeDoorHookButton = QPushButton("Place Door Hook")
        placeDoorHookButton.clicked.connect(self.placeDoorHook)
        buttonLayout.addWidget(placeDoorHookButton)
        layout.addLayout(buttonLayout)

        # Add zoom slider
        zoomLayout = QHBoxLayout()
        zoomLayout.addWidget(QLabel("Zoom:"))
        self.zoomSlider = QSlider(Qt.Horizontal)
        self.zoomSlider.setRange(10, 200)
        self.zoomSlider.setValue(100)
        self.zoomSlider.valueChanged.connect(self.updateZoom)
        zoomLayout.addWidget(self.zoomSlider)
        layout.addLayout(zoomLayout)

        # Add texture browser
        self.texturelist = QListWidget()
        self.texturelist.itemClicked.connect(self.onTextureSelected)
        layout.addWidget(self.texturelist)

        self.setLayout(layout)
        # Add more UI initialization code here

    def setLYT(self, lyt: LYT):
        self.lyt = lyt
        self.update()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-room-template"):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasFormat("application/x-room-template"):
            # Extract room template data and create a new room
            roomTemplate = event.mimeData().data("application/x-room-template")
            self.createRoomFromTemplate(roomTemplate)
            event.accept()
        else:
            event.ignore()

    def createRoomFromTemplate(self, roomTemplate: LYTRoomTemplate):
        # Logic to create a room from the given template
        newRoom = LYTRoom(position=Vector3(0, 0, 0), size=Vector2(100, 100))
        self.lyt.rooms.append(newRoom)
        self.update()
        self.textureBrowser.textureChanged.connect(self.applyTexture)
        self.loadTextures()

    @property
    def render(self):
        painter = QPainter(self.parent())
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw grid
        if self._showGrid:
            self.drawGrid(painter)

        with QMutexLocker(self.render_lock):
            # Draw rooms
            visible_rooms = self.getVisibleRooms()
            for room in visible_rooms:
                self.drawRoom(painter, room, self.parent().scene.camera.distance)

            # Draw tracks
            for track in self.lyt.tracks:
                self.drawTrack(painter, track, self.parent().scene.camera.distance)

            # Draw obstacles
            for obstacle in self.lyt.obstacles:
                self.drawObstacle(painter, obstacle, self.parent().scene.camera.distance)

            # Draw doorhooks
            for doorhook in self.lyt.doorhooks:
                self.drawDoorHook(painter, doorhook, self.parent().scene.camera.distance)

            # Draw selected elements
            self.drawSelectedElements(painter, self.parent().scene.camera.distance)

        # Draw walkmesh if in editing mode (outside of render_lock to avoid potential deadlock)
        if self.isEditingWalkmesh and self.walkmesh:
            self.drawWalkmesh(painter, self.parent().scene.camera.distance)

        painter.end()

    def drawGrid(self, painter: QPainter):
        pen = QPen(QColor(128, 128, 128), 1, Qt.DashLine)
        painter.setPen(pen)

        for x in range(0, self.width(), self.gridSize):
            painter.drawLine(x, 0, x, self.height())

        for y in range(0, self.height(), self.gridSize):
            painter.drawLine(0, y, self.width(), y)

    def drawRoom(self, painter: QPainter, room: LYTRoom, zoom: float):
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

    def drawTrack(self, painter: QPainter, track: LYTTrack, zoom: float):
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)

        start = QPoint(int(track.start.x), int(track.start.y)) * zoom
        end = QPoint(int(track.end.x), int(track.end.y)) * zoom
        painter.drawLine(start, end)

    def drawObstacle(self, painter: QPainter, obstacle: LYTObstacle, zoom: float):
        pen = QPen(QColor(255, 255, 0), 2)
        painter.setPen(pen)

        center = QPoint(int(obstacle.position.x), int(obstacle.position.y)) * zoom
        radius = obstacle.radius * zoom
        painter.drawEllipse(center, radius, radius)

    def drawDoorHook(self, painter: QPainter, doorhook: LYTDoorHook, zoom: float):
        pen = QPen(QColor(0, 255, 0), 2)
        painter.setPen(pen)

        center = QPoint(int(doorhook.position.x), int(doorhook.position.y)) * zoom
        zoomInt = int(zoom)
        painter.drawRect(QRect(center.x() - 2 * zoomInt, center.y() - 2 * zoomInt, 4 * zoomInt, 4 * zoomInt))

    def drawSelectedElements(self, painter: QPainter, zoom: float):
        if self.selectedRoom:
            self.drawSelectedRoom(painter, self.selectedRoom, zoom)
        if self.selectedTrack:
            self.drawSelectedTrack(painter, self.selectedTrack, zoom)
        if self.selectedObstacle:
            self.drawSelectedObstacle(painter, self.selectedObstacle, zoom)
        if self.selectedDoorHook:
            self.drawSelectedDoorHook(painter, self.selectedDoorHook, zoom)

        # Draw walkmesh if in editing mode
        if self.isEditingWalkmesh and self.walkmesh:
            self.drawWalkmesh(painter, zoom)

    def drawSelectedRoom(self, painter: QPainter, room: LYTRoom, zoom: float):
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)

        rect = QRect(
            int(room.position.x),
            int(room.position.y),
            int(room.size.x * zoom),
            int(room.size.y * zoom),
        )
        painter.drawRect(rect)

        # Draw resize handles
        handleSize = 8
        for i in range(4):
            x = rect.x() + (i % 2) * rect.width()
            y = rect.y() + (i // 2) * rect.height()
            painter.drawRect(QRect(x - handleSize // 2, y - handleSize // 2, handleSize, handleSize).scaled(zoom, zoom))

    def drawSelectedTrack(self, painter: QPainter, track: LYTTrack, zoom: float):
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)

        start = QPoint(int(track.start.x), int(track.start.y)) * zoom
        end = QPoint(int(track.end.x), int(track.end.y)) * zoom
        painter.drawLine(start, end)

        # Draw handles at start and end
        handleSize = 8
        painter.drawRect(QRect(start.x() - handleSize // 2, start.y() - handleSize // 2, handleSize, handleSize).scaled(zoom, zoom))
        painter.drawRect(QRect(end.x() - handleSize // 2, end.y() - handleSize // 2, handleSize, handleSize).scaled(zoom, zoom))

    def drawSelectedObstacle(self, painter: QPainter, obstacle: LYTObstacle, zoom: float):
        pen = QPen(QColor(255, 255, 0), 2)
        painter.setPen(pen)

        center = QPoint(int(obstacle.position.x), int(obstacle.position.y)) * zoom
        radius = obstacle.radius * zoom
        painter.drawEllipse(center, radius, radius)

    def drawSelectedDoorHook(self, painter: QPainter, doorhook: LYTDoorHook, zoom: float):
        pen = QPen(QColor(0, 255, 0), 2)
        painter.setPen(pen)

        center = QPoint(int(doorhook.position.x), int(doorhook.position.y)) * zoom
        painter.drawRect(QRect(center.x() - 2 * zoom, center.y() - 2 * zoom, 4 * zoom, 4 * zoom))

    def drawWalkmesh(self, painter: QPainter, zoom: float):
        pen = QPen(QColor(0, 0, 255, 128), 1)
        painter.setPen(pen)
        for face in self.walkmesh.faces:
            points = [QPoint(int(v.x * zoom), int(v.y * zoom)) for v in face.vertices]
            painter.drawPolygon(points)

    def handleKeyPress(self, e: QKeyEvent):
        if e.key() == Qt.Key.Key_Delete:
            if self.selectedRoom:
                self.lyt.rooms.remove(self.selectedRoom)
                self.selectedRoom = None
            if self.selectedTrack:
                self.lyt.tracks.remove(self.selectedTrack)
                self.selectedTrack = None
            if self.selectedObstacle:
                self.lyt.obstacles.remove(self.selectedObstacle)
                self.selectedObstacle = None
            if self.selectedDoorHook:
                self.lyt.doorhooks.remove(self.selectedDoorHook)
                self.selectedDoorHook = None
            self.update()

    def handleMousePress(self, e: QMouseEvent):
        self.mousePos = Vector2(e.x(), e.y())
        self.mousePrev = self.mousePos
        self.mouseDown.add(e.button())

        if e.button() == Qt.MouseButton.LeftButton:
            if self.isPlacingDoorHook:
                self.placeDoorHook(self.mousePos)
                self.isPlacingDoorHook = False
            else:
                self.selectLYTElement(self.mousePos)
                self.isDragging = True
        elif e.button() == Qt.MouseButton.RightButton:
            if self.selectedRoom:
                self.selectedRoomRotationPoint = self.mousePos
                self.isRotating = True
            elif self.selectedTrack:
                self.isDragging = True
        elif e.button() == Qt.MouseButton.MiddleButton:
            self.isDragging = True

    def handleMouseRelease(self, e: QMouseEvent):
        self.mouseDown.discard(e.button())
        self.isDragging = False
        self.isResizing = False
        self.isRotating = False
        self.selectedRoomResizeCorner = None
        self.selectedRoomRotationPoint = None

    def handleMouseMove(self, e: QMouseEvent):
        self.mousePos = Vector2(e.x(), e.y())

        if self.isDragging:
            self.dragLYTElement(self.mousePos)
        elif self.isResizing:
            self.resizeSelectedRoom(self.mousePos)
        elif self.isRotating:
            self.rotateSelectedRoom(self.mousePos)

    def selectLYTElement(self, mousePos: Vector2):
        # Check for room selection
        for room in self.lyt.rooms:
            rect = QRect(
                int(room.position.x),
                int(room.position.y),
                int(room.size.x),
                int(room.size.y),
            )
            if rect.contains(QPoint(int(mousePos.x), int(mousePos.y))):
                self.selectedRoom = room
                self.selectedTrack = None
                self.selectedObstacle = None
                self.selectedDoorHook = None
                return

        # Check for track selection
        for track in self.lyt.tracks:
            start = QPoint(int(track.start.x), int(track.start.y))
            end = QPoint(int(track.end.x), int(track.end.y))
            line = QLine(start, end)
            if line.ptDistanceToPoint(QPoint(int(mousePos.x), int(mousePos.y))) <= 5:
                self.selectedRoom = None
                self.selectedTrack = track
                self.selectedObstacle = None
                self.selectedDoorHook = None
                return

        # Check for obstacle selection
        for obstacle in self.lyt.obstacles:
            center = QPoint(int(obstacle.position.x), int(obstacle.position.y))
            radius = obstacle.radius
            if QPoint(int(mousePos.x), int(mousePos.y)).distanceToPoint(center) <= radius:
                self.selectedRoom = None
                self.selectedTrack = None
                self.selectedObstacle = obstacle
                self.selectedDoorHook = None
                return

        # Check for doorhook selection
        for doorhook in self.lyt.doorhooks:
            center = QPoint(int(doorhook.position.x), int(doorhook.position.y))
            if QRect(center.x() - 2, center.y() - 2, 4, 4).contains(QPoint(int(mousePos.x), int(mousePos.y))):
                self.selectedRoom = None
                self.selectedTrack = None
                self.selectedObstacle = None
                self.selectedDoorHook = doorhook
                return

        # Deselect if no element is selected
        self.selectedRoom = None
        self.selectedTrack = None
        self.selectedObstacle = None
        self.selectedDoorHook = None

    def dragLYTElement(self, mousePos: Vector2):
        delta = mousePos - self.mousePrev
        self.mousePrev = mousePos

        if self.selectedRoom:
            self.moveRoom(self.selectedRoom, delta)
        elif self.selectedTrack:
            if Qt.MouseButton.RightButton in self.mouseDown:
                self.moveTrackEnd(self.selectedTrack, delta)
            else:
                self.moveTrackStart(self.selectedTrack, delta)
        elif self.selectedObstacle:
            self.moveObstacle(self.selectedObstacle, delta)
        elif self.selectedDoorHook:
            self.moveDoorHook(self.selectedDoorHook, delta)

        self.update()

    def moveRoom(self, room: LYTRoom, delta: Vector2):
        newPosition = Vector3(room.position.x + delta.x, room.position.y + delta.y, room.position.z)
        self.roomMoved.emit(room, newPosition)

    def moveTrackStart(self, track: LYTTrack, delta: Vector2):
        newStart = Vector3(track.start.x + delta.x, track.start.y + delta.y, track.start.z)
        self.roomMoved.emit(track, newStart)

    def moveTrackEnd(self, track: LYTTrack, delta: Vector2):
        newEnd = Vector3(track.end.x + delta.x, track.end.y + delta.y, track.end.z)
        self.roomMoved.emit(track, newEnd)

    def moveObstacle(self, obstacle: LYTObstacle, delta: Vector2):
        newPosition = Vector3(obstacle.position.x + delta.x, obstacle.position.y + delta.y, obstacle.position.z)
        self.roomMoved.emit(obstacle, newPosition)

    def moveDoorHook(self, doorhook: LYTDoorHook, delta: Vector2):
        newPosition = Vector3(doorhook.position.x + delta.x, doorhook.position.y + delta.y, doorhook.position.z)
        self.roomMoved.emit(doorhook, newPosition)

    def resizeSelectedRoom(self, mousePos: Vector2):
        if self.selectedRoom is None or self.selectedRoomResizeCorner is None:
            return

        delta = mousePos - self.mousePrev
        self.mousePrev = mousePos

        # Calculate new size based on resize corner
        newSize = Vector2(self.selectedRoom.size.x, self.selectedRoom.size.y)
        if self.selectedRoomResizeCorner == 0:
            newSize.x += delta.x
            newSize.y += delta.y
        elif self.selectedRoomResizeCorner == 1:
            newSize.x += delta.x
        elif self.selectedRoomResizeCorner == 2:
            newSize.x += delta.x
            newSize.y -= delta.y
        elif self.selectedRoomResizeCorner == 3:
            newSize.y -= delta.y
        elif self.selectedRoomResizeCorner == 4:
            newSize.y += delta.y
        elif self.selectedRoomResizeCorner == 5:
            newSize.x -= delta.x
            newSize.y += delta.y
        elif self.selectedRoomResizeCorner == 6:
            newSize.x -= delta.x
        elif self.selectedRoomResizeCorner == 7:
            newSize.x -= delta.x
            newSize.y -= delta.y

        # Update room size
        self.roomResized.emit(self.selectedRoom, newSize)
        self.update()

    def rotateSelectedRoom(self, mousePos: Vector2):
        if self.selectedRoom is None or self.selectedRoomRotationPoint is None:
            return

        delta = mousePos - self.mousePrev
        self.mousePrev = mousePos

        # Calculate rotation angle
        angle = math.degrees(math.atan2(delta.y, delta.x))

        # Update room rotation
        self.roomRotated.emit(self.selectedRoom, angle)
        self.update()

    def placeDoorHook(self, mousePos: Vector2):
        doorhook = LYTDoorHook(Vector3(mousePos.x, mousePos.y, 0))
        self.doorHookPlaced.emit(doorhook)
        self.update()

    def loadTextures(self):
        # Load textures from the module
        self.addBackgroundTask(self.loadTexturesTask, ())

    def loadTexturesTask(self):
        # Implement texture loading logic here
        # This method will be executed in a separate thread
        textures = self.parent().scene.module.textures()
        with self.texture_lock:
            self.textures = textures
        return textures

    def onTexturesLoaded(self, result):
        self.updateTexturelist()

    def updateTexturelist(self):
        with self.texture_lock:
            self.texturelist.clear()
            for texture_name in self.textures:
                self.texturelist.addItem(QListWidgetItem(texture_name))

    def applyTexture(self, textureName: str):
        self.addBackgroundTask(self.applyTextureTask, (textureName,))

    def connectRoomsAutomatically(self):
        if not self.lyt or len(self.lyt.rooms) < 2:
            return

        new_doorhooks = []
        connected_rooms = set()
        doorhook_groups = {}

        for i, room1 in enumerate(self.lyt.rooms):
            for room2 in self.lyt.rooms[i + 1 :]:
                if (room1, room2) in connected_rooms or (room2, room1) in connected_rooms:
                    continue

                shared_edge = self.getSharedEdge(room1, room2)
                if shared_edge:
                    new_doorhooks.extend(self.createDoorHooks(room1, room2, shared_edge))
                    connected_rooms.add((room1, room2))

        # Remove existing doorhooks that are no longer valid
        valid_doorhooks = []
        for doorhook in self.lyt.doorhooks:
            connected_rooms = self.getConnectedRooms(doorhook)
            if len(connected_rooms) == 2:
                valid_doorhooks.append(doorhook)
                key = tuple(sorted(connected_rooms, key=lambda r: r.id))
                if key not in doorhook_groups:
                    doorhook_groups[key] = []
                doorhook_groups[key].append(doorhook)

        # Add new doorhooks
        for doorhook in new_doorhooks:
            connected_rooms = self.getConnectedRooms(doorhook)
            if len(connected_rooms) == 2:
                key = tuple(sorted(connected_rooms, key=lambda r: r.id))
                if key not in doorhook_groups:
                    doorhook_groups[key] = []
                doorhook_groups[key].append(doorhook)
                valid_doorhooks.append(doorhook)

        # Update the LYT with the new set of doorhooks
        self.lyt.doorhooks = valid_doorhooks

        # Optimize doorhook placement
        for group in doorhook_groups.values():
            if len(group) > 1:
                self.optimizeGroupPlacement(group)

        # Update the spatial partitioning
        self.optimizeRendering()
        # Notify listeners of the update
        self.update()
        self.lytUpdated.emit(self.lyt)

    def getConnectedRooms(self, doorhook: LYTDoorHook) -> list[LYTRoom]:
        return [room for room in self.lyt.rooms if self.isDoorHookOnRoomEdge(doorhook, room)]

    def optimizeGroupPlacement(self, doorhooks: list[LYTDoorHook]):
        if not doorhooks:
            return

        # Sort doorhooks based on their position
        doorhooks.sort(key=lambda dh: (dh.position.x, dh.position.y))

        # Evenly space the doorhooks along the shared edge
        edge_length = self.getEdgeLength(doorhooks[0], doorhooks[-1])
        spacing = edge_length / (len(doorhooks) + 1)

        for i, doorhook in enumerate(doorhooks):
            t = (i + 1) / (len(doorhooks) + 1)
            new_pos = self.interpolatePosition(doorhooks[0].position, doorhooks[-1].position, t)
            doorhook.position = new_pos

    def getEdgeLength(self, start_hook: LYTDoorHook, end_hook: LYTDoorHook) -> float:
        return ((end_hook.position.x - start_hook.position.x) ** 2 + (end_hook.position.y - start_hook.position.y) ** 2) ** 0.5

    def interpolatePosition(self, start: Vector3, end: Vector3, t: float) -> Vector3:
        return Vector3(start.x + (end.x - start.x) * t, start.y + (end.y - start.y) * t, start.z + (end.z - start.z) * t)

    def createDoorHooks(self, room1: LYTRoom, room2: LYTRoom, shared_edge: tuple[str, float, float]) -> list[LYTDoorHook]:
        edge_type, start, end = shared_edge
        doorhooks = []

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
            doorhooks.append(LYTDoorHook(Vector3(door_x, door_y, 0)))

        return doorhooks

    def getSharedEdge(self, room1: LYTRoom, room2: LYTRoom) -> tuple[str, float, float] | None:
        r1_left, r1_right = room1.position.x, room1.position.x + room1.size.x
        r1_top, r1_bottom = room1.position.y, room1.position.y + room1.size.y
        r2_left, r2_right = room2.position.x, room2.position.x + room2.size.x
        r2_top, r2_bottom = room2.position.y, room2.position.y + room2.size.y

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
        return any(self.isDoorHookOnRoomEdge(doorhook, room) for room in self.lyt.rooms)

    def isDoorHookOnRoomEdge(self, doorhook: LYTDoorHook, room: LYTRoom) -> bool:
        tolerance = 0.001
        x, y = doorhook.position.x, doorhook.position.y

        # Check if the doorhook is on any of the room's edges
        on_left = abs(x - room.position.x) < tolerance
        on_right = abs(x - (room.position.x + room.size.x)) < tolerance
        on_top = abs(y - room.position.y) < tolerance
        on_bottom = abs(y - (room.position.y + room.size.y)) < tolerance

        return (
            (on_left or on_right)
            and (room.position.y <= y <= room.position.y + room.size.y)
            or (on_top or on_bottom)
            and (room.position.x <= x <= room.position.x + room.size.x)
        )

    def optimizeDoorHookPlacement(self):
        # Group doorhooks by their connecting rooms
        doorhook_groups = {}
        for doorhook in self.lyt.doorhooks:
            connected_rooms = self.getConnectedRooms(doorhook)
            if connected_rooms:
                key = tuple(sorted(connected_rooms))
                if key not in doorhook_groups:
                    doorhook_groups[key] = []
                doorhook_groups[key].append(doorhook)

        # Optimize placement for each group
        for group in doorhook_groups.values():
            if len(group) > 1:
                self.optimizeGroupPlacement(group)

    def manualDoorPlacement(self, room: LYTRoom):
        self.isPlacingDoorHook = True
        self.selectedRoom = room

    def placeDoorHook(self, mousePos: Vector2):
        """Check if the mouse position is on the edge of the selected room."""
        room = self.selectedRoom
        tolerance = 5  # pixels

        if (
            abs(mousePos.x - room.position.x) < tolerance
            or abs(mousePos.x - (room.position.x + room.size.x)) < tolerance
            or abs(mousePos.y - room.position.y) < tolerance
            or abs(mousePos.y - (room.position.y + room.size.y)) < tolerance
        ):
            doorhook = LYTDoorHook(Vector3(mousePos.x, mousePos.y, 0))
            self.lyt.doorhooks.append(doorhook)
            self.doorHookPlaced.emit(doorhook)
            self.update()

    def snapToGrid(self, point: Vector2) -> Vector2:
        if self._snapToGrid:
            return Vector2(
                round(point.x / self.gridSize) * self.gridSize,
                round(point.y / self.gridSize) * self.gridSize,
            )
        return point

    def getRoomResizeCorner(self, mousePos: Vector2) -> Optional[int]:
        if self.selectedRoom is None:
            return None

        rect = QRect(
            int(self.selectedRoom.position.x),
            int(self.selectedRoom.position.y),
            int(self.selectedRoom.size.x),
            int(self.selectedRoom.size.y),
        )

        handleSize = 8
        for i in range(8):
            x = rect.x() + (i % 2) * rect.width()
            y = rect.y() + (i // 2) * rect.height()
            if QRect(x - handleSize // 2, y - handleSize // 2, handleSize, handleSize).contains(QPoint(int(mousePos.x), int(mousePos.y))):
                return i

        return None

    def resizeRoom(self, mousePos: Vector2):
        if self.selectedRoom is None:
            return

        self.selectedRoomResizeCorner = self.getRoomResizeCorner(mousePos)
        if self.selectedRoomResizeCorner is not None:
            self.isResizing = True
            self.mousePrev = mousePos

    def getRoomRotationPoint(self, mousePos: Vector2) -> Optional[Vector2]:
        if self.selectedRoom is None:
            return None

        rect = QRect(
            int(self.selectedRoom.position.x),
            int(self.selectedRoom.position.y),
            int(self.selectedRoom.size.x),
            int(self.selectedRoom.size.y),
        )

        # Check if mouse is within the room
        if rect.contains(QPoint(int(mousePos.x), int(mousePos.y))):
            return mousePos

        return None

    def rotateRoom(self, mousePos: Vector2):
        if self.selectedRoom is None:
            return

        self.selectedRoomRotationPoint = self.getRoomRotationPoint(mousePos)
        if self.selectedRoomRotationPoint is not None:
            self.isRotating = True
            self.mousePrev = mousePos

    def setGridSize(self, gridSize: int):
        self.gridSize = gridSize
        self.update()

    def setSnapToGrid(self, snapToGrid: bool):
        self._snapToGrid = snapToGrid
        self.update()

    def setShowGrid(self, showGrid: bool):
        self._showGrid = showGrid
        self.update()

    def generateWalkmesh(self):
        if not self.lyt or not self.lyt.rooms:
            return

        self.walkmesh = BWM()

        for room in self.lyt.rooms:
            # Create a simple rectangular face for each room
            vertices = [
                Vector3(room.position.x, room.position.y, 0),
                Vector3(room.position.x + room.size.x, room.position.y, 0),
                Vector3(room.position.x + room.size.x, room.position.y + room.size.y, 0),
                Vector3(room.position.x, room.position.y + room.size.y, 0),
            ]
            face = BWMFace(*vertices)
            self.walkmesh.faces.append(face)

        self.walkmeshUpdated.emit(self.walkmesh)
        self.update()

    def editWalkmesh(self):
        if not self.walkmesh:
            self.generateWalkmesh()

        self.isEditingWalkmesh = True
        self.selectedWalkmeshFace = None
        self.update()

    def handleWalkmeshEdit(self, mousePos: Vector2):
        if not self.isEditingWalkmesh or not self.walkmesh:
            return

        clickedFace = self.getWalkmeshFaceAt(mousePos)

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
            if self.isPointInPolygon(point, face.vertices):
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
        painter.drawPolygon([QPoint(int(v.x), int(v.y)) for v in face.vertices])

    def updateLYT(self):
        # Update the LYT data and notify listeners
        self.lytUpdated.emit(self.lyt)
        self.update()

    def mousePressEvent(self, e: QMouseEvent):
        super().mousePressEvent(e)
        if self.isEditingWalkmesh:
            self.handleWalkmeshEdit(Vector2(e.x(), e.y()))

    def mouseMoveEvent(self, e: QMouseEvent):
        super().mouseMoveEvent(e)
        if self.isEditingWalkmesh and self.selectedWalkmeshFace:
            # TODO: Implement logic for moving vertices or the entire face
            pass

    def mouseReleaseEvent(self, e: QMouseEvent):
        super().mouseReleaseEvent(e)
        # TODO: Add any necessary cleanup for walkmesh editing here

    def addObstacle(self, model_name: str = ""):
        # TODO: Implement obstacle addition logic
        newObstacle = LYTObstacle(model=model_name, position=Vector3(50, 50, 0), radius=25)
        self.lyt.obstacles.append(newObstacle)
        self.update()

    def onTextureSelected(self, item: QListWidgetItem):
        textureName = item.text()
        self.applyTexture(textureName)

    def applyTextureTask(self, textureName: str):
        # This method will be executed in a separate thread
        # Implement the logic to apply the texture to the selected element
        with self.lyt_lock:
            if self.selectedRoom:  # FIXME: lytroom does not store textures.
                self.selectedRoom.texture = textureName
            elif self.selectedTrack:
                self.selectedTrack.texture = textureName
        return textureName

    def onTextureApplied(self, result):
        self.textureChanged.emit(result)
        self.update()

    def optimizeRendering(self):
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

    def getVisibleRooms(self) -> set[LYTRoom]:
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
                            if not consumer.is_busy():
                                consumer.add_task(task, args, kwargs)
                                break
                            # If all consumers are busy, put the task back in the queue
                            self.task_queue.put((task, args))
                            break
                        except queue.Empty:
                            break
                for consumer in self.task_consumers:
                    try:
                        if not consumer.is_busy():
                            consumer.add_task(task, args)
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
                if task == self.loadTexturesTask:
                    self.onTexturesLoaded(result)
                elif task == self.applyTextureTask:
                    self.onTextureApplied(result)
                # Add more task completions as needed
            except Empty:  # noqa: PERF203
                break

        self.processErrors()
        self.processChanges()

    def processErrors(self):
        while not self.error_queue.empty():
            try:
                task, exception = self.error_queue.get(block=False)
                error_message = f"Error in task {task!r}: {exception!s}"
                print(error_message)
                # You can add more robust error handling here, such as logging to a file or showing a dialog
                # self.showErrorDialog(error_message)
                # Implement more robust error handling here, e.g., showing an error dialog
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
                self.lytUpdated.emit(self.lyt)
                self.change_buffer.clear()
            self.update()

    def updateLYT(self):
        with self.lyt_lock, self.render_lock:
            lyt_copy = deepcopy(self.lyt)
            self.lytUpdated.emit(lyt_copy)
        self.update()

    def updateZoom(self, value: int):
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

    def addBackgroundTask(self, task: Callable, args: tuple):
        with self.task_queue_lock:
            self.task_queue.put((task, args, {}))
            qApp = QApplication.instance()
            assert qApp is not None, "QApplication instance not found?"
            qApp.postEvent(self, QEvent(QEvent.Type.User))  # Trigger event processing

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.User:
            self.processMainThreadTasks()
            self.processBackgroundTasks()
            self.processChanges()
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

    def addRoom(self, model_name: str = ""):
        # Implement room addition logic
        newRoom = LYTRoom(model=model_name, position=Vector3(0, 0, 0))
        self.lyt.rooms.append(newRoom)
        self.update()

    def updateRoom(self, room: LYTRoom):
        self.addChange(("update", "room", room))

    def deleteRoom(self, room: LYTRoom):
        self.addChange(("delete", "room", room))

    # Add more methods for specific LYT operations (e.g., addRoom, updateRoom, deleteRoom, etc.)
    # Implement similar methods for tracks, obstacles, and doorhooks

    def addTrack(self, model_name: str = ""):
        # Implement track addition logic
        newTrack = LYTTrack(model=model_name, position=Vector3(0, 0, 0))
        self.lyt.tracks.append(newTrack)
        self.update()

    def updateTrack(self, track: LYTTrack):
        self.addChange(("update", "track", track))

    def deleteTrack(self, track: LYTTrack):
        self.addChange(("delete", "track", track))