from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from qtpy.QtCore import QPoint, QRect, QSize, Signal
from qtpy.QtGui import QBrush, QColor, QKeyEvent, QMouseEvent, QPainter, QPen
from qtpy.QtWidgets import QWidget

if TYPE_CHECKING:
    from pykotor.resource.formats.lyt.lyt_data import LYT, LYTRoom, LYTTrack, LYTDoorHook, LYTObstacle
    from toolset.gui.widgets.renderer.module import ModuleRenderer
    from pykotor.common.geometry import Vector2, Vector3
    from glm import vec3


class LYTEditor(QWidget):
    roomPlaced: Signal = Signal(object)
    roomMoved: Signal = Signal(object, object)
    roomResized: Signal = Signal(object, object)
    roomRotated: Signal = Signal(object, float)
    doorHookPlaced: Signal = Signal(object)
    textureChanged: Signal = Signal(object)

    def __init__(self, parent: ModuleRenderer):
        super().__init__(parent)
        self.parent = parent
        self.lyt: LYT | None = None
        self.selectedRoom: Optional[LYTRoom] = None
        self.selectedTrack: Optional[LYTTrack] = None
        self.selectedObstacle: Optional[LYTObstacle] = None
        self.selectedDoorHook: Optional[LYTDoorHook] = None
        self.gridSize = 10
        self.snapToGrid = True
        self.showGrid = True
        self.mouseDown: set[int] = set()
        self.mousePos: Vector2 = Vector2(0, 0)
        self.mousePrev: Vector2 = Vector2(0, 0)
        self.isDragging: bool = False
        self.isResizing: bool = False
        self.isRotating: bool = False
        self.isPlacingDoorHook: bool = False
        self.selectedRoomResizeCorner: Optional[int] = None
        self.selectedRoomRotationPoint: Optional[Vector2] = None

    def setLYT(self, lyt: LYT):
        self.lyt = lyt

    def render(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw grid
        if self.showGrid:
            self.drawGrid(painter)

        # Draw rooms
        for room in self.lyt.rooms:
            self.drawRoom(painter, room)

        # Draw tracks
        for track in self.lyt.tracks:
            self.drawTrack(painter, track)

        # Draw obstacles
        for obstacle in self.lyt.obstacles:
            self.drawObstacle(painter, obstacle)

        # Draw doorhooks
        for doorhook in self.lyt.doorhooks:
            self.drawDoorHook(painter, doorhook)

        # Draw selected room
        if self.selectedRoom:
            self.drawSelectedRoom(painter, self.selectedRoom)

        # Draw selected track
        if self.selectedTrack:
            self.drawSelectedTrack(painter, self.selectedTrack)

        # Draw selected obstacle
        if self.selectedObstacle:
            self.drawSelectedObstacle(painter, self.selectedObstacle)

        # Draw selected doorhook
        if self.selectedDoorHook:
            self.drawSelectedDoorHook(painter, self.selectedDoorHook)

        painter.end()

    def drawGrid(self, painter: QPainter):
        pen = QPen(QColor(128, 128, 128), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)

        for x in range(0, self.width(), self.gridSize):
            painter.drawLine(x, 0, x, self.height())

        for y in range(0, self.height(), self.gridSize):
            painter.drawLine(0, y, self.width(), y)

    def drawRoom(self, painter: QPainter, room: LYTRoom):
        pen = QPen(QColor(0, 0, 0), 1)
        brush = QBrush(QColor(128, 128, 128, 128))
        painter.setPen(pen)
        painter.setBrush(brush)

        rect = QRect(
            int(room.position.x),
            int(room.position.y),
            int(room.size.x),
            int(room.size.y),
        )
        painter.drawRect(rect)

    def drawTrack(self, painter: QPainter, track: LYTTrack):
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)

        start = QPoint(int(track.start.x), int(track.start.y))
        end = QPoint(int(track.end.x), int(track.end.y))
        painter.drawLine(start, end)

    def drawObstacle(self, painter: QPainter, obstacle: LYTObstacle):
        pen = QPen(QColor(255, 255, 0), 2)
        painter.setPen(pen)

        center = QPoint(int(obstacle.position.x), int(obstacle.position.y))
        radius = obstacle.radius
        painter.drawEllipse(center, radius, radius)

    def drawDoorHook(self, painter: QPainter, doorhook: LYTDoorHook):
        pen = QPen(QColor(0, 255, 0), 2)
        painter.setPen(pen)

        center = QPoint(int(doorhook.position.x), int(doorhook.position.y))
        painter.drawRect(QRect(center.x() - 2, center.y() - 2, 4, 4))

    def drawSelectedRoom(self, painter: QPainter, room: LYTRoom):
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)

        rect = QRect(
            int(room.position.x),
            int(room.position.y),
            int(room.size.x),
            int(room.size.y),
        )
        painter.drawRect(rect)

        # Draw resize handles
        handleSize = 8
        for i in range(4):
            x = rect.x() + (i % 2) * rect.width()
            y = rect.y() + (i // 2) * rect.height()
            painter.drawRect(QRect(x - handleSize // 2, y - handleSize // 2, handleSize, handleSize))

    def drawSelectedTrack(self, painter: QPainter, track: LYTTrack):
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)

        start = QPoint(int(track.start.x), int(track.start.y))
        end = QPoint(int(track.end.x), int(track.end.y))
        painter.drawLine(start, end)

        # Draw handles at start and end
        handleSize = 8
        painter.drawRect(QRect(start.x() - handleSize // 2, start.y() - handleSize // 2, handleSize, handleSize))
        painter.drawRect(QRect(end.x() - handleSize // 2, end.y() - handleSize // 2, handleSize, handleSize))

    def drawSelectedObstacle(self, painter: QPainter, obstacle: LYTObstacle):
        pen = QPen(QColor(255, 255, 0), 2)
        painter.setPen(pen)

        center = QPoint(int(obstacle.position.x), int(obstacle.position.y))
        radius = obstacle.radius
        painter.drawEllipse(center, radius, radius)

    def drawSelectedDoorHook(self, painter: QPainter, doorhook: LYTDoorHook):
        pen = QPen(QColor(0, 255, 0), 2)
        painter.setPen(pen)

        center = QPoint(int(doorhook.position.x), int(doorhook.position.y))
        painter.drawRect(QRect(center.x() - 2, center.y() - 2, 4, 4))

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

    def handleKeyRelease(self, e: QKeyEvent):
        pass

    def handleMousePress(self, e: QMouseEvent):
        self.mousePos = Vector2(e.x(), e.y())
        self.mousePrev = self.mousePos
        self.mouseDown.add(e.button())

        if self.lyt is None:
            return

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

        if self.lyt is None:
            return

        if self.isDragging:
            self.dragLYTElement(self.mousePos)
        elif self.isResizing:
            self.resizeSelectedRoom(self.mousePos)
        elif self.isRotating:
            self.rotateSelectedRoom(self.mousePos)

    def selectLYTElement(self, mousePos: Vector2):
        if self.lyt is None:
            return

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
        if self.lyt is None:
            return

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
        if self.lyt is None:
            return

        doorhook = LYTDoorHook(Vector3(mousePos.x, mousePos.y, 0))
        self.doorHookPlaced.emit(doorhook)
        self.update()

    def snapToGrid(self, point: Vector2) -> Vector2:
        if self.snapToGrid:
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

    def placeDoorHook(self):
        self.isPlacingDoorHook = True

    def setGridSize(self, gridSize: int):
        self.gridSize = gridSize
        self.update()

    def setSnapToGrid(self, snapToGrid: bool):
        self.snapToGrid = snapToGrid
        self.update()

    def setShowGrid(self, showGrid: bool):
        self.showGrid = showGrid
        self.update()
