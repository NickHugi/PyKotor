from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.geometry import SurfaceMaterial, Vector2
from pykotor.common.misc import Color
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.lyt import LYT, read_lyt
from pykotor.resource.generics.pth import PTH, bytes_pth, read_pth
from pykotor.resource.type import ResourceType
from PyQt5.QtGui import QColor, QKeyEvent
from PyQt5.QtWidgets import QMenu, QWidget
from toolset.data.misc import ControlItem
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.git import GITSettings

if TYPE_CHECKING:
    import os

    from pykotor.extract.file import ResourceIdentifier
    from PyQt5.QtCore import QPoint
    from toolset.data.installation import HTInstallation


class PTHEditor(Editor):
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        supported = [ResourceType.PTH]
        super().__init__(parent, "PTH Editor", "pth", supported, supported, installation)

        from toolset.uic.editors.pth import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self._pth: PTH = PTH()
        self._controls: PTHControlScheme = PTHControlScheme(self)

        self.settings = GITSettings()

        def intColorToQColor(intvalue):
            color = Color.from_rgba_integer(intvalue)
            return QColor(int(color.r*255), int(color.g*255), int(color.b*255), int(color.a*255))
        self.materialColors: dict[SurfaceMaterial, QColor] = {
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
        self.nameBuffer: dict[ResourceIdentifier, str] = {}
        self.tagBuffer: dict[ResourceIdentifier, str] = {}

        self.ui.renderArea.materialColors = self.materialColors
        self.ui.renderArea.hideWalkmeshEdges = True
        self.ui.renderArea.highlightBoundaries = False

        self.new()

    def _setupSignals(self):
        self.ui.renderArea.mousePressed.connect(self.onMousePressed)
        self.ui.renderArea.mouseMoved.connect(self.onMouseMoved)
        self.ui.renderArea.mouseScrolled.connect(self.onMouseScrolled)
        self.ui.renderArea.mouseReleased.connect(self.onMouseReleased)
        self.ui.renderArea.customContextMenuRequested.connect(self.onContextMenu)
        self.ui.renderArea.keyPressed.connect(self.onKeyPressed)

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        super().load(filepath, resref, restype, data)

        order = [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES]
        result = self._installation.resource(resref, ResourceType.LYT, order)
        if result:
            self.loadLayout(read_lyt(result.data))

        pth = read_pth(data)
        self._loadPTH(pth)

    def _loadPTH(self, pth: PTH):
        self._pth = pth
        self.ui.renderArea.centerCamera()
        self.ui.renderArea.setPth(pth)

    def build(self) -> tuple[bytes, bytes]:
        return bytes_pth(self._pth), b""

    def new(self):
        super().new()
        self._loadPTH(PTH())

    def pth(self) -> PTH:
        return self._pth

    def loadLayout(self, layout: LYT):
        walkmeshes = []
        for room in layout.rooms:
            order = [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES]
            findBWM = self._installation.resource(room.model, ResourceType.WOK, order)
            if findBWM is not None:
                walkmeshes.append(read_bwm(findBWM.data))

        self.ui.renderArea.setWalkmeshes(walkmeshes)

    def moveCameraToSelection(self):
        instance = self.ui.renderArea.instanceSelection.last()
        if instance:
            self.ui.renderArea.camera.setPosition(instance.position.x, instance.position.y)

    def moveCamera(self, x: float, y: float):
        self.ui.renderArea.camera.nudgePosition(x, y)

    def zoomCamera(self, amount: float):
        self.ui.renderArea.camera.nudgeZoom(amount)

    def rotateCamera(self, angle: float):
        self.ui.renderArea.camera.nudgeRotation(angle)

    def moveSelected(self, x: float, y: float):
        for point in self.ui.renderArea.pathSelection.all():
            point.x = x
            point.y = y

    def selectNodeUnderMouse(self):
        if self.ui.renderArea.pathNodesUnderMouse():
            toSelect = [self.ui.renderArea.pathNodesUnderMouse()[0]]
            self.ui.renderArea.pathSelection.select(toSelect)
        else:
            self.ui.renderArea.pathSelection.clear()

    def addNode(self, x: float, y: float):
        self._pth.add(x, y)

    def removeNode(self, index: int):
        self._pth.remove(index)
        self.ui.renderArea.pathSelection.clear()

    def removeEdge(self, source: int, target: int):
        self._pth.disconnect(source, target)

    def addEdge(self, source: int, target: int):
        self._pth.connect(source, target)

    def pointsUnderMouse(self) -> list[Vector2]:
        return self.ui.renderArea.pathNodesUnderMouse()

    def selectedNodes(self) -> list[Vector2]:
        return self.ui.renderArea.pathSelection.all()

    # region Signal Callbacks
    def onContextMenu(self, point: QPoint):
        globalPoint = self.ui.renderArea.mapToGlobal(point)
        world = self.ui.renderArea.toWorldCoords(point.x(), point.y())
        self._controls.onRenderContextMenu(world, globalPoint)

    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: set[int], keys: set[int]):
        worldDelta = self.ui.renderArea.toWorldDelta(delta.x, delta.y)
        world = self.ui.renderArea.toWorldCoords(screen.x, screen.y)
        self._controls.onMouseMoved(screen, delta, world, worldDelta, buttons, keys)

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        self._controls.onMouseScrolled(delta, buttons, keys)

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self._controls.onMousePressed(screen, buttons, keys)

    def onMouseReleased(self, buttons: set[int], keys: set[int]):
        self._controls.onMouseReleased(Vector2(0, 0), buttons, keys)

    def onKeyPressed(self, buttons: set[int], keys: set[int]):
        self._controls.onKeyboardPressed(buttons, keys)

    def keyPressEvent(self, e: QKeyEvent | None):
        self.ui.renderArea.keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent | None):
        self.ui.renderArea.keyReleaseEvent(e)
    # endregion


class PTHControlScheme:
    def __init__(self, editor: PTHEditor):
        self.editor: PTHEditor = editor
        self.settings: GITSettings = GITSettings()

        self.panCamera: ControlItem = ControlItem(self.settings.moveCameraBind)
        self.rotateCamera: ControlItem = ControlItem(self.settings.rotateCameraBind)
        self.zoomCamera: ControlItem = ControlItem(self.settings.zoomCameraBind)
        self.moveSelected: ControlItem = ControlItem(self.settings.moveSelectedBind)
        self.selectUnderneath: ControlItem = ControlItem(self.settings.selectUnderneathBind)
        self.deleteSelected: ControlItem = ControlItem(self.settings.deleteSelectedBind)

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        if self.zoomCamera.satisfied(buttons, keys):
            self.editor.zoomCamera(delta.y / 50)

    def onMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector2, worldDelta: Vector2, buttons: set[int], keys: set[int]):
        if self.panCamera.satisfied(buttons, keys):
            self.editor.moveCamera(-worldDelta.x, -worldDelta.y)
        if self.rotateCamera.satisfied(buttons, keys):
            self.editor.rotateCamera(screenDelta.y)
        if self.moveSelected.satisfied(buttons, keys):
            self.editor.moveSelected(world.x, world.y)

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        if self.selectUnderneath.satisfied(buttons, keys):
            self.editor.selectNodeUnderMouse()

    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        ...

    def onKeyboardPressed(self, buttons: set[int], keys: set[int]):
        if self.deleteSelected.satisfied(buttons, keys):
            self.editor.deleteSelected()

    def onKeyboardReleased(self, buttons: set[int], keys: set[int]):
        ...

    def onRenderContextMenu(self, world: Vector2, screen: QPoint):
        targetNode = self.editor.pointsUnderMouse()[0] if self.editor.pointsUnderMouse() else None
        targetIndex = self.editor.pth().find(targetNode) if targetNode else None

        sourceNode = self.editor.selectedNodes()[0] if self.editor.pointsUnderMouse() else None
        sourceIndex = self.editor.pth().find(sourceNode) if targetNode else None

        menu = QMenu(self.editor)

        menu.addAction("Add Node").triggered.connect(lambda _: self.editor.addNode(world.x, world.y))

        if sourceIndex:
            menu.addAction("Remove Node").triggered.connect(lambda _: self.editor.removeNode(sourceIndex))

        menu.addSeparator()

        if sourceIndex and targetIndex:
            menu.addAction("Add Edge").triggered.connect(lambda _: self.editor.addEdge(sourceIndex, targetIndex))
            menu.addAction("Remove Edge").triggered.connect(lambda _: self.editor.removeEdge(sourceIndex, targetIndex))

        menu.popup(screen)
