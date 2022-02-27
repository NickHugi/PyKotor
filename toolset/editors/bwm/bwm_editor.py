import math
import struct
from typing import Optional, Tuple, Dict, List

from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QPixmap, QPaintEvent, QPainter, QPen, QColor, QPainterPath, QBrush, QMouseEvent, QImage, \
    QWheelEvent
from PyQt5.QtWidgets import QWidget, QListWidgetItem, QShortcut
from pykotor.common.geometry import Vector3, SurfaceMaterial, Vector2
from pykotor.resource.formats.bwm import load_bwm, BWM, BWMFace, write_bwm
from pykotor.resource.generics.git import GITTrigger, GIT
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from editors.bwm import bwm_editor_ui
from editors.editor import Editor


_TRANS_FACE_ROLE = QtCore.Qt.UserRole + 1
_TRANS_EDGE_ROLE = QtCore.Qt.UserRole + 2


class BWMEditor(Editor):
    def __init__(self, parent: QWidget, installation: Optional[HTInstallation] = None):
        supported = [ResourceType.WOK, ResourceType.DWK, ResourceType.PWK]
        super().__init__(parent, "Walkmesh Painter", supported, supported, installation)

        self.ui = bwm_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()

        iconVersion = "x" if installation is None else "2" if installation.tsl else "1"
        iconPath = ":/images/icons/k{}/walkmesh.png".format(iconVersion)
        self.setWindowIcon(QIcon(QPixmap(iconPath)))

        self._bwm: Optional[BWM] = None

        self.materialColors: Dict[SurfaceMaterial, QColor] = {
            SurfaceMaterial.UNDEFINED:      QColor(0xf45086),
            SurfaceMaterial.OBSCURING:      QColor(0x555555),
            SurfaceMaterial.DIRT:           QColor(0x800000),
            SurfaceMaterial.GRASS:          QColor(0x33cc33),
            SurfaceMaterial.STONE:          QColor(0x808080),
            SurfaceMaterial.WATER:          QColor(0x0066ff),
            SurfaceMaterial.NON_WALK:       QColor(0xff00ff),
            SurfaceMaterial.TRANSPARENT:    QColor(0xb3ffff),
            SurfaceMaterial.CARPET:         QColor(0xffff00),
            SurfaceMaterial.METAL:          QColor(0x4d4d4d),
            SurfaceMaterial.PUDDLES:        QColor(0x00ffaa),
            SurfaceMaterial.SWAMP:          QColor(0x00995c),
            SurfaceMaterial.MUD:            QColor(0xcc6600),
            SurfaceMaterial.LEAVES:         QColor(0x009933),
            SurfaceMaterial.LAVA:           QColor(0xff944d),
            SurfaceMaterial.BOTTOMLESS_PIT: QColor(0xe6e6e6),
            SurfaceMaterial.DEEP_WATER:     QColor(0x9999ff),
            SurfaceMaterial.DOOR:           QColor(0xffb3b3),
            SurfaceMaterial.NON_WALK_GRASS: QColor(0xb3ffb3),
            SurfaceMaterial.TRIGGER:        QColor(0x4d0033)
        }
        self.ui.drawArea.materialColors = self.materialColors
        self.rebuildMaterials()

        self.ui.transList.itemSelectionChanged.connect(self.onTransitionSelect)
        self.ui.drawArea.mouseDragged.connect(lambda x, y: self.changeFace(self._bwm.faceAt(x, y)))
        self.ui.drawArea.mouseMoved.connect(self.mouseMoved)
        # self.ui.drawArea.mouseScrolled.connect(lambda scroll: self.ui.drawArea.zoom(scroll//50))
        QShortcut("+", self).activated.connect(lambda: self.ui.drawArea.zoom(2))
        QShortcut("-", self).activated.connect(lambda: self.ui.drawArea.zoom(-2))

        self.new()

    def rebuildMaterials(self) -> None:
        self.ui.materialList.clear()
        for material in self.materialColors:
            color = self.materialColors[material]
            image = QImage(struct.pack('BBB', color.red(), color.green(), color.blue()) * 16 * 16, 16, 16, QImage.Format_RGB888)
            icon = QIcon(QPixmap(image))
            text = material.name.replace("_", " ").title()
            item = QListWidgetItem(icon, text)
            item.setData(QtCore.Qt.UserRole, material)
            self.ui.materialList.addItem(item)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        self._bwm = load_bwm(data)
        self.ui.drawArea.setWalkmeshes([self._bwm])

        def addTransItem(face, edge, transition):
            if transition is not None:
                item = QListWidgetItem("Transition to: {}".format(transition))
                item.setData(_TRANS_FACE_ROLE, face)
                item.setData(_TRANS_EDGE_ROLE, edge)
                self.ui.transList.addItem(item)

        self.ui.transList.clear()
        for face in self._bwm.faces:
            addTransItem(face, 1, face.trans1)
            addTransItem(face, 2, face.trans2)
            addTransItem(face, 3, face.trans3)

    def build(self) -> bytes:
        data = bytearray()
        write_bwm(self._bwm, data)
        return data

    def new(self) -> None:
        super().new()

    def mouseMoved(self, x: float, y: float) -> None:
        coords = self.ui.drawArea.toWalkmeshCoords(x, y)
        text = "(x: {0:.2f}, y: {0:.2f})".format(coords.x, coords.y)
        self.statusBar().showMessage(text + " Zoom: {}".format(self.ui.drawArea.currentZoom()))

    def changeFace(self, face: BWMFace):
        newMaterial = self.ui.materialList.currentItem().data(QtCore.Qt.UserRole)
        if face and face.material != newMaterial:
            face.material = newMaterial
            self.ui.drawArea.repaint()

    def onTransitionSelect(self) -> None:
        if self.ui.transList.currentItem():
            item = self.ui.transList.currentItem()
            self.ui.drawArea.setHighlighted(item.data(_TRANS_FACE_ROLE))
        else:
            self.ui.drawArea.setHighlighted(None)


class WalkmeshRenderer(QWidget):
    doubleClicked = QtCore.pyqtSignal(object, object)
    """Emitted when widget is double clicked. Emits the coordinates in the BWM file from where the mouse was pressed."""

    mouseDragged = QtCore.pyqtSignal(object, object)
    """Emitted when mouse is down and moving accross the widget. Emits the coordinates in the BWM file from where the
       mouse was pressed."""

    mouseMoved = QtCore.pyqtSignal(object, object)
    """Emitted when mouse is has moved accross the widget. Emits the coordinates in the BWM file from where the mouse
       was pressed."""

    mouseScrolled = QtCore.pyqtSignal(object)
    """Emiitted when mouse has been scrolled."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._walkmeshes: List[BWM] = []
        self._positions: List[Vector3] = []
        self._git: Optional[GIT] = None
        self._painter: QPainter = QPainter(self)
        self._width: int = 0
        self._height: int = 0
        self._zoom: float = 11.0
        self._bbmin: Vector3 = Vector3.from_null()
        self._bbmax: Vector3 = Vector3.from_null()
        self._mousePressed: bool = False
        self._hightlight = None
        self.hideEdges: bool = False

        self.cursor().setShape(QtCore.Qt.CrossCursor)

        self.materialColors: Dict[SurfaceMaterial, int] = {}
        for material in SurfaceMaterial._member_names_:
            self.materialColors[material] = QColor(0xFFFFFF)

    def setHighlighted(self, face: BWMFace):
        self._hightlight = face
        self.repaint()

    def setWalkmeshes(self, walkmeshes: List[BWM], positions: List[Vector3] = None):
        self._walkmeshes = walkmeshes
        self._bbmin = Vector3(1000000, 1000000, 1000000)
        self._bbmax = Vector3(-1000000, -1000000, -1000000)

        positions = [] if positions is None else positions
        while len(positions) < len(walkmeshes):
            positions.append(Vector3.from_null())

        for i, walkmesh in enumerate(walkmeshes):
            bbmin, bbmax = walkmesh.box()
            bbmin += positions[i]
            bbmax += positions[i]
            self._bbmin.x = min(bbmin.x, self._bbmin.x)
            self._bbmin.y = min(bbmin.y, self._bbmin.y)
            self._bbmin.z = min(bbmin.z, self._bbmin.z)
            self._bbmax.x = max(bbmax.x, self._bbmax.x)
            self._bbmax.y = max(bbmax.y, self._bbmax.y)
            self._bbmax.z = max(bbmax.z, self._bbmax.z)

        width, height = self.zoomedSize()
        self.setMinimumWidth(width)
        self.setMinimumHeight(height)
        self.repaint()

        # Fit all to screen
        sizeX = math.fabs(self._bbmax.x - self._bbmin.x)
        sizeY = math.fabs(self._bbmax.y - self._bbmin.y)
        zoom = min(self.window().width() / sizeX, self.window().height() / sizeY) if sizeX != 0 and sizeY != 0 else 6
        self.setZoom(zoom - 5)

    def setGit(self, git: GIT) -> None:
        self._git = git

    def zoomedSize(self) -> Tuple[int, int]:
        bbmin = self._bbmin * self._zoom
        bbmax = self._bbmax * self._zoom
        width = math.fabs(bbmax.x - bbmin.x)
        height = math.fabs(bbmax.y - bbmin.y)
        return int(width), int(height)

    def paintEvent(self, e: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setBrush(QBrush(QColor(0)))
        painter.drawRect(0, 0, self.width(), self.height())

        for walkmesh in self._walkmeshes:
            for face in walkmesh.faces:
                self._drawFace(face)

        if self._git is not None:
            for trigger in self._git.triggers:
                self._drawTrigger(trigger)

    def _drawFace(self, face: BWMFace) -> None:
        painter = QPainter(self)

        pen = QPen(QColor(0x111111), 1, QtCore.Qt.SolidLine, QtCore.Qt.SquareCap) if not self.hideEdges else QPen(QtCore.Qt.NoPen)
        painter.setPen(pen)

        color = QColor(self.materialColors[face.material])
        painter.setBrush(QBrush(color))

        v1 = self.toRenderCoords(face.v1.x, face.v1.y)
        v2 = self.toRenderCoords(face.v2.x, face.v2.y)
        v3 = self.toRenderCoords(face.v3.x, face.v3.y)

        path = QPainterPath()
        path.moveTo(v1.x, v1.y)
        path.lineTo(v2.x, v2.y)
        path.lineTo(v3.x, v3.y)
        path.lineTo(v1.x, v1.y)
        path.closeSubpath()

        painter.drawPath(path)

        if face.trans1 is not None:
            self._drawTransition(v1, v2, self._hightlight == face)
        if face.trans2 is not None:
            self._drawTransition(v2, v3, self._hightlight == face)
        if face.trans3 is not None:
            self._drawTransition(v3, v1, self._hightlight == face)

    def _drawTransition(self, v1: Vector2, v2: Vector2, highlight: bool):
        painter = QPainter(self)

        if highlight:
            painter.setPen(QPen(QColor(0xFFDDDD), 6, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap))
            path = QPainterPath()
            path.moveTo(v1.x, v1.y)
            path.lineTo(v2.x, v2.y)
            path.closeSubpath()
            painter.drawPath(path)

        painter.setPen(QPen(QColor(0xFF1111), 2))
        path = QPainterPath()
        path.moveTo(v1.x, v1.y)
        path.lineTo(v2.x, v2.y)
        path.closeSubpath()
        painter.drawPath(path)

    def _drawTrigger(self, trigger: GITTrigger):
        path = QPainterPath()
        if trigger.geometry:
            offset = trigger.position
            start = self.toRenderCoords(trigger.geometry[0].x + offset.x, trigger.geometry[0].y + offset.y)
            path.moveTo(start.x, start.y)
            for point in trigger.geometry[1:]:
                move = self.toRenderCoords(point.x + offset.x, point.y + offset.y)
                path.lineTo(move.x, move.y)
        path.closeSubpath()

        painter = QPainter(self)
        # Draw trigger zone
        painter.setBrush(QBrush(QColor(255, 255, 0, 30)))
        painter.setPen(QPen(QColor(0xFFFF00), 1))
        painter.drawPath(path)

        # Draw trigger vertices
        painter.setPen(QPen(QtCore.Qt.NoPen))
        painter.setBrush(QBrush(QColor(0xAAAA66)))
        if trigger.geometry:
            offset = trigger.position
            for point in trigger.geometry:
                move = self.toRenderCoords(point.x + offset.x, point.y + offset.y)
                painter.drawEllipse(move.x-3, move.y-3, 6, 6)

    def toRenderCoords(self, x, y) -> Vector2:
        x *= self._zoom
        y *= self._zoom
        x -= math.fabs(self._bbmin.x * self._zoom)
        y -= math.fabs(self._bbmin.y * self._zoom)
        return Vector2(x, y)

    def toWalkmeshCoords(self, x, y) -> Vector2:
        x = (x + math.fabs(self._bbmin.x * self._zoom)) / self._zoom
        y = (y + math.fabs(self._bbmin.y * self._zoom)) / self._zoom
        return Vector2(x, y)

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        x, y = self.toWalkmeshCoords(e.x(), e.y())
        self.doubleClicked.emit(x, y)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        coords = self.toWalkmeshCoords(e.x(), e.y())
        self.mouseMoved.emit(coords.x, coords.y)
        if self._mousePressed:
            self.mouseDragged.emit(coords.x, coords.y)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        self._mousePressed = True

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        self._mousePressed = False

    def wheelEvent(self, e: QWheelEvent) -> None:
        self.mouseScrolled.emit(e.angleDelta())

    def currentZoom(self) -> float:
        return self._zoom

    def setZoom(self, zoom: float) -> None:
        self._zoom = zoom

        if self._zoom < 1:
            self._zoom = 1

        width, height = self.zoomedSize()
        self.setMinimumWidth(width)
        self.setMinimumHeight(height)

        self.repaint()

    def zoom(self, amount: float) -> None:
        self._zoom += amount
        if self._zoom < 1:
            self._zoom = 1
        if self._zoom > 100:
            self._zoom = 100

        width, height = self.zoomedSize()
        self.setMinimumWidth(width)
        self.setMinimumHeight(height)

        self.repaint()


