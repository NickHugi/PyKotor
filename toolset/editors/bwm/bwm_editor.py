import math
import struct
from typing import Optional, Tuple, Dict

from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QPixmap, QPaintEvent, QPainter, QPen, QColor, QPainterPath, QBrush, QMouseEvent, QImage, \
    QWheelEvent
from PyQt5.QtWidgets import QWidget, QListWidgetItem, QShortcut
from pykotor.common.geometry import Vector3, SurfaceMaterial
from pykotor.resource.formats.bwm import load_bwm, BWM, BWMFace, write_bwm
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
        self.ui.drawArea.setWalkmesh(self._bwm)

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

    def mouseMoved(self, e: QMouseEvent) -> None:
        coords = self.ui.drawArea.toWalkmeshCoords(e, e)
        text = "(x: {0:.2f}, y: {0:.2f})".format(*coords)
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
        self._bwm: Optional[BWM] = None
        self._painter: QPainter = QPainter(self)
        self._width: int = 0
        self._height: int = 0
        self._zoom: float = 11.0
        self._bbmin: Vector3 = Vector3.from_null()
        self._bbmax: Vector3 = Vector3.from_null()
        self._mousePressed: bool = False
        self._hightlight = None

        self.cursor().setShape(QtCore.Qt.CrossCursor)

        self.materialColors: Dict[SurfaceMaterial, int] = {}
        for material in SurfaceMaterial._member_names_:
            self.materialColors[material] = QColor(0xFFFFFF)

    def setHighlighted(self, face: BWMFace):
        self._hightlight = face
        self.repaint()

    def setWalkmesh(self, bwm: BWM):
        self._bwm = bwm
        self._bbmin, self._bbmax = self._bwm.box()

        width, height = self.zoomedSize()
        self.setMinimumWidth(width)
        self.setMinimumHeight(height)
        self.repaint()

        # Fit all to screen
        sizeX = math.fabs(self._bbmax.x - self._bbmin.x)
        sizeY = math.fabs(self._bbmax.y - self._bbmin.y)
        zoom = min(self.window().width() / sizeX, self.window().height() / sizeY) if sizeX != 0 and sizeY != 0 else 6
        self.setZoom(zoom - 5)

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

        if self._bwm:
            for face in self._bwm.faces:
                self._drawFace(face)

    def _drawFace(self, face: BWMFace) -> None:
        painter = QPainter(self)

        pen = QPen(QColor(0x111111), 1, QtCore.Qt.SolidLine, QtCore.Qt.SquareCap)
        painter.setPen(pen)

        color = QColor(self.materialColors[face.material])
        painter.setBrush(QBrush(color))

        v1 = face.v1 * self._zoom
        v2 = face.v2 * self._zoom
        v3 = face.v3 * self._zoom
        v1.x -= math.fabs(self._bbmin.x * self._zoom)
        v1.y -= math.fabs(self._bbmin.y * self._zoom)
        v2.x -= math.fabs(self._bbmin.x * self._zoom)
        v2.y -= math.fabs(self._bbmin.y * self._zoom)
        v3.x -= math.fabs(self._bbmin.x * self._zoom)
        v3.y -= math.fabs(self._bbmin.y * self._zoom)

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

    def _drawTransition(self, v1: Vector3, v2: Vector3, highlight: bool):
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

    def toWalkmeshCoords(self, x, y) -> Tuple[float, float]:
        x = (x + math.fabs(self._bbmin.x * self._zoom)) / self._zoom
        y = (y + math.fabs(self._bbmin.y * self._zoom)) / self._zoom
        return x, y

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        x, y = self.toWalkmeshCoords(e.x(), e.y())
        self.doubleClicked.emit(x, y)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        coords = self.toWalkmeshCoords(e.x(), e.y())
        self.mouseMoved.emit(*coords)
        if self._mousePressed:
            self.mouseDragged.emit(*coords)

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


