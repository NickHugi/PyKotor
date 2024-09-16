from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy.QtCore import QSize, Qt
from qtpy.QtGui import QBrush, QColor, QPainter, QPen, QTransform
from qtpy.QtWidgets import QFileDialog, QGraphicsEllipseItem, QGraphicsItem, QGraphicsLineItem, QGraphicsRectItem, QGraphicsScene, QListView, QMessageBox

from pykotor.common.geometry import SurfaceMaterial, Vector2, Vector3
from pykotor.common.misc import Color
from pykotor.resource.formats.lyt import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack, bytes_lyt, read_lyt
from pykotor.resource.type import ResourceType
from toolset.data.misc import ControlItem
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.lyt_editor import LYTEditorSettings

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation

class LYTEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        supported: list[ResourceType] = [ResourceType.LYT]
        super().__init__(parent, "LYT Editor", "lyt", supported, supported, installation)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.lyt import Ui_LYTEditor
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.lyt import Ui_LYTEditor
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.lyt import Ui_LYTEditor
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.lyt import Ui_LYTEditor
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui: Ui_LYTEditor = Ui_LYTEditor()
        self.ui.setupUi(self)
        self._setupMenus()

        self._lyt: LYT = LYT()
        self._controls: LYTControlScheme = LYTControlScheme(self)
        self.settings: LYTEditorSettings = LYTEditorSettings()

        self.scene = QGraphicsScene(self)
        self.ui.graphicsView.setScene(self.scene)

        self.materialColors: dict[SurfaceMaterial, QColor] = self._setupMaterialColors()

        self._setupConnections()
        self._setupGraphicsView()
        self._setupSidebar()

    def _setupMaterialColors(self) -> dict[SurfaceMaterial, QColor]:
        def intColorToQColor(num_color: int) -> QColor:
            color: Color = Color.from_rgba_integer(num_color)
            return QColor(int(color.r * 255), int(color.g * 255), int(color.b * 255), int(color.a * 255))

        return {
            SurfaceMaterial.UNDEFINED: intColorToQColor(self.settings.undefinedMaterialColour),
            SurfaceMaterial.OBSCURING: intColorToQColor(self.settings.obscuringMaterialColour),
            SurfaceMaterial.DIRT: intColorToQColor(self.settings.dirtMaterialColour),
            SurfaceMaterial.GRASS: intColorToQColor(self.settings.grassMaterialColour),
            SurfaceMaterial.STONE: intColorToQColor(self.settings.stoneMaterialColour),
            SurfaceMaterial.WOOD: intColorToQColor(self.settings.woodMaterialColour),
            SurfaceMaterial.WATER: intColorToQColor(self.settings.waterMaterialColour),
            SurfaceMaterial.NON_WALK: intColorToQColor(self.settings.nonWalkMaterialColour),
            SurfaceMaterial.TRANSPARENT: intColorToQColor(self.settings.transparentMaterialColour),
            SurfaceMaterial.CARPET: intColorToQColor(self.settings.carpetMaterialColour),
            SurfaceMaterial.METAL: intColorToQColor(self.settings.metalMaterialColour),
            SurfaceMaterial.PUDDLES: intColorToQColor(self.settings.puddlesMaterialColour),
            SurfaceMaterial.SWAMP: intColorToQColor(self.settings.swampMaterialColour),
            SurfaceMaterial.MUD: intColorToQColor(self.settings.mudMaterialColour),
            SurfaceMaterial.LEAVES: intColorToQColor(self.settings.leavesMaterialColour),
            SurfaceMaterial.LAVA: intColorToQColor(self.settings.lavaMaterialColour),
            SurfaceMaterial.BOTTOMLESS_PIT: intColorToQColor(self.settings.bottomlessPitMaterialColour),
            SurfaceMaterial.DEEP_WATER: intColorToQColor(self.settings.deepWaterMaterialColour),
            SurfaceMaterial.DOOR: intColorToQColor(self.settings.doorMaterialColour),
            SurfaceMaterial.NON_WALK_GRASS: intColorToQColor(self.settings.nonWalkGrassMaterialColour),
            SurfaceMaterial.TRIGGER: intColorToQColor(self.settings.nonWalkGrassMaterialColour),
        }

    def _setupConnections(self):
        self.ui.addRoomButton.clicked.connect(self.addRoom)
        self.ui.addTrackButton.clicked.connect(self.addTrack)
        self.ui.addObstacleButton.clicked.connect(self.addObstacle)
        self.ui.addDoorHookButton.clicked.connect(self.addDoorHook)  # FIXME: addDoorHookButton attribute not found
        self.ui.generateWalkmeshButton.clicked.connect(self.generateWalkmesh)
        self.ui.zoomSlider.valueChanged.connect(self.updateZoom)
        self.ui.importTextureButton.clicked.connect(self.importTexture)  # FIXME: importTextureButton attribute not found
        self.ui.importModelButton.clicked.connect(self.importModel)  # FIXME: importModelButton attribute not found 

    def _setupGraphicsView(self):
        self.ui.graphicsView.setRenderHint(QPainter.Antialiasing)
        self.ui.graphicsView.setDragMode(self.ui.graphicsView.ScrollHandDrag)
        self.ui.graphicsView.setTransformationAnchor(self.ui.graphicsView.AnchorUnderMouse)
        self.ui.graphicsView.setResizeAnchor(self.ui.graphicsView.AnchorUnderMouse)

    def _setupSidebar(self):
        # Setup texture browser
        self.ui.textureBrowser.setIconSize(QSize(64, 64))  # FIXME: textureBrowser attribute not found
        self.ui.textureBrowser.setViewMode(QListView.IconMode)  # FIXME: textureBrowser attribute not found
        self.ui.textureBrowser.setResizeMode(QListView.Adjust)  # FIXME: textureBrowser attribute not found
        self.ui.textureBrowser.setWrapping(True)  # FIXME: textureBrowser attribute not found

        # Setup room templates
        self.ui.roomTemplateList.addItems(["Square Room", "Circular Room", "L-Shaped Room"])  # FIXME: roomTemplateList attribute not found

    def addRoom(self):
        room = LYTRoom()
        room.position = Vector3(0, 0, 0)
        room.size = Vector2(10, 10)  # FIXME: size attribute not found
        self._lyt.rooms.append(room)
        self.updateScene()

    def addTrack(self):
        track = LYTTrack()
        track.start = Vector3(0, 0, 0)  # FIXME: start attribute not found
        track.end = Vector3(10, 10, 0)  # FIXME: end attribute not found
        self._lyt.tracks.append(track)
        self.updateScene()

    def addObstacle(self):
        obstacle = LYTObstacle()
        obstacle.position = Vector3(0, 0, 0)
        obstacle.radius = 5  # FIXME: radius attribute not found
        self._lyt.obstacles.append(obstacle)
        self.updateScene()

    def addDoorHook(self):
        doorhook = LYTDoorHook()
        doorhook.position = Vector3(0, 0, 0)
        self._lyt.doorhooks.append(doorhook)
        self.updateScene()

    def generateWalkmesh(self):
        # Implement walkmesh generation logic here
        pass

    def updateZoom(self, value):
        scale = value / 100.0
        self.ui.graphicsView.setTransform(QTransform().scale(scale, scale))

    def updateScene(self):
        self.scene.clear()
        for room in self._lyt.rooms:
            self.scene.addItem(RoomItem(room, self))
        for track in self._lyt.tracks:
            self.scene.addItem(TrackItem(track, self))
        for obstacle in self._lyt.obstacles:
            self.scene.addItem(ObstacleItem(obstacle, self))
        for doorhook in self._lyt.doorhooks:
            self.scene.addItem(DoorHookItem(doorhook, self))

    def importTexture(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Texture", "", "Image Files (*.png *.jpg *.bmp)")
        if file_path:
            # TODO: Implement texture import logic
            self.updateTextureBrowser()

    def importModel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Model", "", "Model Files (*.mdl)")
        if file_path:
            # TODO: Implement model import logic
            pass

    def updateTextureBrowser(self):
        # TODO: Update texture browser with imported textures
        pass

    def load(self, data: bytes, resref: str, restype: ResourceType, filepath: str) -> None:
        try:
            self._lyt = read_lyt(data)
            self.updateScene()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load LYT: {str(e)}")

    def build(self) -> tuple[bytes, ResourceType]:
        return bytes_lyt(self._lyt), ResourceType.LYT

class RoomItem(QGraphicsRectItem):
    def __init__(self, room: LYTRoom, editor: LYTEditor):
        super().__init__(0, 0, room.size.x, room.size.y)
        self.room = room
        self.editor = editor
        self.setPos(room.position.x, room.position.y)
        self.setPen(QPen(Qt.black))
        self.setBrush(QBrush(Qt.lightGray))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.room.position = Vector3(self.pos().x(), self.pos().y(), self.room.position.z)

class TrackItem(QGraphicsLineItem):
    def __init__(self, track: LYTTrack, editor: LYTEditor):
        super().__init__(track.start.x, track.start.y, track.end.x, track.end.y)
        self.track = track
        self.editor = editor
        self.setPen(QPen(Qt.red, 2))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

class ObstacleItem(QGraphicsEllipseItem):
    def __init__(self, obstacle: LYTObstacle, editor: LYTEditor):
        super().__init__(-obstacle.radius, -obstacle.radius, obstacle.radius * 2, obstacle.radius * 2)
        self.obstacle = obstacle
        self.editor = editor
        self.setPos(obstacle.position.x, obstacle.position.y)
        self.setPen(QPen(Qt.blue))
        self.setBrush(QBrush(Qt.blue, Qt.DiagCrossPattern))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.obstacle.position = Vector3(self.pos().x(), self.pos().y(), self.obstacle.position.z)

class DoorHookItem(QGraphicsRectItem):
    def __init__(self, doorhook: LYTDoorHook, editor: LYTEditor):
        super().__init__(-1, -1, 2, 2)
        self.doorhook = doorhook
        self.editor = editor
        self.setPos(doorhook.position.x, doorhook.position.y)
        self.setPen(QPen(Qt.green))
        self.setBrush(QBrush(Qt.green))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.doorhook.position = Vector3(self.pos().x(), self.pos().y(), self.doorhook.position.z)

class LYTControlScheme:
    def __init__(self, editor: LYTEditor):
        self.editor: LYTEditor = editor
        self.settings: LYTEditorSettings = LYTEditorSettings()

    @property
    def panCamera(self) -> ControlItem:
        return ControlItem(self.settings.moveCameraBind)

    @panCamera.setter
    def panCamera(self, value):
        self.settings.moveCameraBind = value

    @property
    def rotateCamera(self) -> ControlItem:
        return ControlItem(self.settings.rotateCameraBind)

    @rotateCamera.setter
    def rotateCamera(self, value):
        self.settings.rotateCameraBind = value

    @property
    def zoomCamera(self) -> ControlItem:
        return ControlItem(self.settings.zoomCameraBind)

    @zoomCamera.setter
    def zoomCamera(self, value):
        self.settings.zoomCameraBind = value

    @property
    def moveSelected(self) -> ControlItem:
        return ControlItem(self.settings.moveSelectedBind)

    @moveSelected.setter
    def moveSelected(self, value):
        self.settings.moveSelectedBind = value

    @property
    def selectUnderneath(self) -> ControlItem:
        return ControlItem(self.settings.selectUnderneathBind)

    @selectUnderneath.setter
    def selectUnderneath(self, value):
        self.settings.selectUnderneathBind = value

    @property
    def deleteSelected(self) -> ControlItem:
        return ControlItem(self.settings.deleteSelectedBind)

    @deleteSelected.setter
    def deleteSelected(self, value):
        self.settings.deleteSelectedBind = value
