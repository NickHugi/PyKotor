from __future__ import annotations

import traceback

from contextlib import suppress
from typing import TYPE_CHECKING, Any

import qtpy

from qtpy.QtCore import Qt
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QApplication, QHBoxLayout, QLabel, QMenu, QMessageBox, QWidget

from pykotor.common.geometry import SurfaceMaterial, Vector2
from pykotor.common.misc import Color
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.lyt import read_lyt
from pykotor.resource.generics.pth import PTH, bytes_pth, read_pth
from pykotor.resource.type import ResourceType
from toolset.data.misc import ControlItem
from toolset.gui.editor import Editor
from toolset.gui.helpers.callback import BetterMessageBox
from toolset.gui.widgets.settings.git import GITSettings
from toolset.gui.widgets.settings.module_designer import ModuleDesignerSettings
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    import os

    from collections.abc import Callable

    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QKeyEvent, QMouseEvent
    from qtpy.QtWidgets import QStatusBar

    from pykotor.common.geometry import Vector3
    from pykotor.extract.file import ResourceIdentifier, ResourceResult
    from pykotor.resource.formats.bwm.bwm_data import BWM
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.generics.git import GITInstance
    from toolset.data.installation import HTInstallation


class CustomStdout:
    def __init__(self, editor: PTHEditor):
        self.prevStatusOut: str = ""
        self.prevStatusErr: str = ""
        self.mousePos = Vector2.from_null()  # Initialize with a default position
        self.editor: PTHEditor = editor

        sbar = editor.statusBar()
        assert sbar is not None
        self.editorStatusBar: QStatusBar = sbar

    def write(self, text):  # Update status bar with stdout content
        self.updateStatusBar(stdout=text)

    def flush(self):  # Required for compatibility
        ...

    def updateStatusBar(
        self,
        stdout: str = "",
        stderr: str = "",
    ):
        # Update stderr if provided
        if stderr:
            self.prevStatusErr = stderr

        # If a message is provided (e.g., from the decorator), use it as the last stdout
        if stdout:
            self.prevStatusOut = stdout

        # Construct the status text using last known values
        left_status = str(self.mousePos)
        center_status = str(self.prevStatusOut)
        right_status = str(self.prevStatusErr)
        self.editor.updateStatusBar(left_status, center_status, right_status)


def statusBarDecorator(func):
    def wrapper(*args, **kwargs):
        args = list(args)
        self: PTHEditor | PTHControlScheme = args.pop(0)
        # Create a representation of the function call
        args_repr = [repr(a) for a in args]  # List comprehension to get the repr of args
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  # List comprehension for kwargs
        signature = ", ".join(args_repr + kwargs_repr)  # Combine the args and kwargs representations
        func_call_repr = f"{func.__name__}({signature})"  # Construct the full function call representation

        editor = self if isinstance(self, PTHEditor) else self.editor
        try:
            editor.statusOut.updateStatusBar(func_call_repr)
            return func(self, *args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            error_message = str(universal_simplify_exception(e))
            editor.statusOut.updateStatusBar(stderr=error_message)  # Update the status bar with the error
            raise  # Re-raise the exception after logging it to the status bar

    return wrapper


def auto_decorate_methods(decorator: Callable[..., Any]) -> Callable[..., Any]:
    """Class decorator to automatically apply a decorator to all methods.

    Untested.
    """

    def class_decorator(cls):
        # Iterate over all attributes of cls
        for attr_name, attr_value in cls.__dict__.items():
            # Check if it's a callable (method) and not inherited
            if callable(attr_value) and attr_name not in dir(cls.__base__):
                # Wrap the method with the decorator
                setattr(cls, attr_name, decorator(attr_value))
        return cls

    return class_decorator


class PTHEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        supported: list[ResourceType] = [ResourceType.PTH]
        super().__init__(parent, "PTH Editor", "pth", supported, supported, installation)
        self.setupStatusBar()
        self.statusOut: CustomStdout = CustomStdout(self)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.pth import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.pth import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.pth import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.pth import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui: Ui_MainWindow = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self._pth: PTH = PTH()
        self._controls: PTHControlScheme = PTHControlScheme(self)

        self.settings: GITSettings = GITSettings()

        def intColorToQColor(num_color: int) -> QColor:
            color: Color = Color.from_rgba_integer(num_color)
            return QColor(int(color.r * 255), int(color.g * 255), int(color.b * 255), int(color.a * 255))

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

    def setupStatusBar(self):
        # Create labels for the different parts of the status message
        self.leftLabel = QLabel("Left Status")
        self.centerLabel = QLabel("Center Status")
        self.rightLabel = QLabel("Right Status")

        # Ensure the center label's text is centered
        self.centerLabel.setAlignment(Qt.AlignCenter)

        # Create a horizontal layout
        layout = QHBoxLayout()
        layout.addWidget(self.leftLabel)

        # Add a spacer item to push the center and right labels to the edge
        layout.addStretch()
        layout.addWidget(self.centerLabel)
        layout.addStretch()

        # Add the right label last
        layout.addWidget(self.rightLabel)

        # Create a widget to set as the status bar's widget
        statusWidget = QWidget()
        statusWidget.setLayout(layout)

        # Set the widget to the status bar
        self.statusBar().addPermanentWidget(statusWidget, 1)

    def updateStatusBar(
        self,
        left_status: str = "",
        center_status: str = "",
        right_status: str = "",
    ):
        # Update the text of each label
        try:
            self._coreUpdateStatusBar(left_status, center_status, right_status)
        except RuntimeError:  # wrapped C/C++ object of type QLabel has been deleted
            self.setupStatusBar()
            self._coreUpdateStatusBar(left_status, center_status, right_status)

    def _coreUpdateStatusBar(
        self,
        left_status: str,
        center_status: str,
        right_status: str,
    ):
        if left_status and left_status.strip():
            self.leftLabel.setText(left_status)
        if center_status and center_status.strip():
            self.centerLabel.setText(center_status)
        if right_status and right_status.strip():
            self.rightLabel.setText(right_status)

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        point: QPoint = event.pos()
        self.statusOut.mousePos = Vector2(point.x(), point.y())
        self.statusOut.updateStatusBar()

    def _setupSignals(self):
        self.ui.renderArea.mousePressed.connect(self.onMousePressed)
        self.ui.renderArea.mouseMoved.connect(self.onMouseMoved)
        self.ui.renderArea.mouseScrolled.connect(self.onMouseScrolled)
        self.ui.renderArea.mouseReleased.connect(self.onMouseReleased)
        self.ui.renderArea.customContextMenuRequested.connect(self.onContextMenu)
        self.ui.renderArea.keyPressed.connect(self.onKeyPressed)

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        super().load(filepath, resref, restype, data)

        order: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES]
        result: ResourceResult | None = self._installation.resource(resref, ResourceType.LYT, order)
        if result:
            self.loadLayout(read_lyt(result.data))
        else:
            BetterMessageBox("Layout not found", f"PTHEditor requires {resref}.lyt for this {resref}.{restype} but it could not be found.", icon=QMessageBox.Icon.Critical).exec_()

        pth: PTH = read_pth(data)
        self._loadPTH(pth)

    @statusBarDecorator
    def _loadPTH(self, pth: PTH):
        self._pth = pth
        self.ui.renderArea.centerCamera()
        self.ui.renderArea.setPth(pth)

    def build(self) -> tuple[bytes, bytes]:
        return bytes_pth(self._pth), b""

    def new(self):
        super().new()
        self._loadPTH(PTH())

    @statusBarDecorator
    def pth(self) -> PTH:
        return self._pth

    @statusBarDecorator
    def loadLayout(self, layout: LYT):
        walkmeshes: list[BWM] = []
        for room in layout.rooms:
            order: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES]
            findBWM: ResourceResult | None = self._installation.resource(room.model, ResourceType.WOK, order)
            if findBWM is not None:
                print(
                    "loadLayout",
                    "BWM Found",
                    f"{findBWM.resname}.{findBWM.restype}",
                    file=self.statusOut,
                )
                walkmeshes.append(read_bwm(findBWM.data))

        self.ui.renderArea.setWalkmeshes(walkmeshes)

    @statusBarDecorator
    def moveCameraToSelection(self):
        instance: GITInstance | None = self.ui.renderArea.instanceSelection.last()
        if instance:
            self.ui.renderArea.camera.setPosition(instance.position.x, instance.position.y)

    @statusBarDecorator
    def moveCamera(self, x: float, y: float):
        self.ui.renderArea.camera.nudgePosition(x, y)

    @statusBarDecorator
    def zoomCamera(self, amount: float):
        self.ui.renderArea.camera.nudgeZoom(amount)

    @statusBarDecorator
    def rotateCamera(self, angle: float):
        self.ui.renderArea.camera.nudgeRotation(angle)

    @statusBarDecorator
    def moveSelected(self, x: float, y: float):
        for point in self.ui.renderArea.pathSelection.all():
            point.x = x
            point.y = y

    @statusBarDecorator
    def selectNodeUnderMouse(self):
        if self.ui.renderArea.pathNodesUnderMouse():
            toSelect: list[Vector2] = [self.ui.renderArea.pathNodesUnderMouse()[0]]
            print("selectNodeUnderMouse", "toSelect:", toSelect)
            self.ui.renderArea.pathSelection.select(toSelect)
        else:
            print("selectNodeUnderMouse", "clear():", file=self.statusOut)
            self.ui.renderArea.pathSelection.clear()

    @statusBarDecorator
    def addNode(self, x: float, y: float):
        self._pth.add(x, y)

    @statusBarDecorator
    def removeNode(self, index: int):
        self._pth.remove(index)
        self.ui.renderArea.pathSelection.clear()

    @statusBarDecorator
    def removeEdge(self, source: int, target: int):
        self._pth.disconnect(source, target)

    @statusBarDecorator
    def addEdge(self, source: int, target: int):
        self._pth.connect(source, target)

    @statusBarDecorator
    def pointsUnderMouse(self) -> list[Vector2]:
        return self.ui.renderArea.pathNodesUnderMouse()

    @statusBarDecorator
    def selectedNodes(self) -> list[Vector2]:
        return self.ui.renderArea.pathSelection.all()

    # region Signal Callbacks
    @statusBarDecorator
    def onContextMenu(self, point: QPoint):
        globalPoint: QPoint = self.ui.renderArea.mapToGlobal(point)
        world: Vector3 = self.ui.renderArea.toWorldCoords(point.x(), point.y())
        self._controls.onRenderContextMenu(Vector2.from_vector3(world), globalPoint)

    @statusBarDecorator
    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: set[int], keys: set[int]):
        worldDelta: Vector2 = self.ui.renderArea.toWorldDelta(delta.x, delta.y)
        world: Vector3 = self.ui.renderArea.toWorldCoords(screen.x, screen.y)
        self._controls.onMouseMoved(screen, delta, Vector2.from_vector3(world), worldDelta, buttons, keys)

    @statusBarDecorator
    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        #print(f"onMouseScrolled(delta={delta!r})", file=self.stdout)
        self._controls.onMouseScrolled(delta, buttons, keys)

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        #print(f"onMousePressed(screen={screen!r})", file=self.stdout)
        self._controls.onMousePressed(screen, buttons, keys)

    @statusBarDecorator
    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        #print("onMouseReleased", file=self.stdout)
        self._controls.onMouseReleased(Vector2(0, 0), buttons, keys)

    @statusBarDecorator
    def onKeyPressed(self, buttons: set[int], keys: set[int]):
        #print("onKeyPressed", file=self.stdout)
        self._controls.onKeyboardPressed(buttons, keys)

    @statusBarDecorator
    def keyPressEvent(self, e: QKeyEvent):
        #print(f"keyPressEvent(e={e!r})", file=self.stdout)
        if e is None:
            return
        self.ui.renderArea.keyPressEvent(e)

    @statusBarDecorator
    def keyReleaseEvent(self, e: QKeyEvent):
        #print(f"keyReleaseEvent(e={e!r})", file=self.stdout)
        if e is None:
            return
        self.ui.renderArea.keyReleaseEvent(e)

    # endregion


def calculate_zoom_strength(delta_y: float, sensSetting: int) -> float:
    m = 0.00202
    b = 1
    factor_in = (m * sensSetting + b)
    return 1 / abs(factor_in) if delta_y < 0 else abs(factor_in)


class PTHControlScheme:
    def __init__(self, editor: PTHEditor):
        self.editor: PTHEditor = editor
        self.settings: GITSettings = GITSettings()

    @statusBarDecorator
    def mouseMoveEvent(self, event: QMouseEvent):
        point: QPoint = event.pos()
        self.editor.statusOut.mousePos = Vector2(point.x(), point.y())

    @statusBarDecorator
    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        if self.zoomCamera.satisfied(buttons, keys):
            if not delta.y:
                return  # sometimes it'll be zero when holding middlemouse-down.
            sensSetting = ModuleDesignerSettings().zoomCameraSensitivity2d
            zoom_factor = calculate_zoom_strength(delta.y, sensSetting)
            #RobustRootLogger.debug(f"onMouseScrolled zoomCamera (delta.y={delta.y}, zoom_factor={zoom_factor}, sensSetting={sensSetting}))")
            self.editor.zoomCamera(zoom_factor)

    @statusBarDecorator
    def onMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector2, worldDelta: Vector2, buttons: set[int], keys: set[int]):
        self.editor.statusOut.mousePos = screen
        shouldPanCamera = self.panCamera.satisfied(buttons, keys)
        shouldRotateCamera = self.rotateCamera.satisfied(buttons, keys)
        if shouldPanCamera or shouldRotateCamera:
            self.editor.ui.renderArea.doCursorLock(screen)
        if shouldPanCamera:
            moveSens = ModuleDesignerSettings().moveCameraSensitivity2d / 100
            #RobustRootLogger.debug(f"onMouseScrolled moveCamera (delta.y={screenDelta.y}, sensSetting={moveSens}))")
            self.editor.moveCamera(-worldDelta.x * moveSens, -worldDelta.y * moveSens)
        if shouldRotateCamera:
            delta_magnitude = (screenDelta.x**2 + screenDelta.y**2)**0.5
            if abs(screenDelta.x) >= abs(screenDelta.y):
                direction = -1 if screenDelta.x < 0 else 1
            else:
                direction = -1 if screenDelta.y < 0 else 1
            rotateSens = ModuleDesignerSettings().rotateCameraSensitivity2d / 1000
            rotateAmount = delta_magnitude * rotateSens
            rotateAmount *= direction
            #RobustRootLogger.debug(f"onMouseScrolled rotateCamera (delta_value={delta_magnitude}, rotateAmount={rotateAmount}, sensSetting={rotateSens}))")
            self.editor.rotateCamera(rotateAmount)
        if self.moveSelected.satisfied(buttons, keys):
            self.editor.moveSelected(world.x, world.y)

    @statusBarDecorator
    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        if self.selectUnderneath.satisfied(buttons, keys):
            self.editor.selectNodeUnderMouse()

    @statusBarDecorator
    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]): ...

    @statusBarDecorator
    def onKeyboardPressed(self, buttons: set[int], keys: set[int]):
        if self.deleteSelected.satisfied(buttons, keys):
            node = None
            try:
                node = self.editor.pth().find(self.editor.pointsUnderMouse()[0])
            except Exception:
                with suppress(Exception):
                    node = self.editor.pth().find(self.editor.selectedNodes()[0])
            if node is None:
                return
            self.editor.removeNode(node)

    @statusBarDecorator
    def onKeyboardReleased(self, buttons: set[int], keys: set[int]): ...

    @statusBarDecorator
    def onRenderContextMenu(self, world: Vector2, screen: QPoint):
        pointsUnderMouse: list[Vector2] = self.editor.pointsUnderMouse()
        selectedNodes: list[Vector2] = self.editor.selectedNodes()

        underMouseIndex: int | None = None
        if pointsUnderMouse and pointsUnderMouse[0]:
            for point in pointsUnderMouse:
                with suppress(ValueError, IndexError):
                    underMouseIndex = self.editor.pth().find(point)
                    if underMouseIndex is not None:
                        break
        selectedIndex: int | None = None
        if selectedNodes and selectedNodes[0]:
            for selected in selectedNodes:
                with suppress(ValueError, IndexError):
                    selectedIndex = self.editor.pth().find(selected)
                    if selectedIndex is not None:
                        break
        print(
            f"selectedIndex:{selectedIndex}",
            f"underMouseIndex:{underMouseIndex}",
            f"onRenderContextMenu(world={world!r}, screen={screen!r})",
            file=self.editor.statusOut,
        )

        menu = QMenu(self.editor)
        menu.addAction("Add Node").triggered.connect(lambda _=None: self.editor.addNode(world.x, world.y))
        menu.addAction("Copy XY coords").triggered.connect(lambda: QApplication.clipboard().setText(str(self.editor.statusOut.mousePos)))
        if underMouseIndex is not None:
            menu.addAction("Remove Node").triggered.connect(lambda _=None: self.editor.removeNode(underMouseIndex))

        menu.addSeparator()

        if underMouseIndex is not None and selectedIndex is not None:
            menu.addAction("Add Edge").triggered.connect(lambda _=None: self.editor.addEdge(selectedIndex, underMouseIndex))
            menu.addAction("Remove Edge").triggered.connect(lambda _=None: self.editor.removeEdge(selectedIndex, underMouseIndex))

        menu.popup(screen)

    # Use @property decorators to allow Users to change their settings without restarting the editor.
    @property
    def panCamera(self) -> ControlItem:
        return ControlItem(self.settings.moveCameraBind)

    @panCamera.setter
    def panCamera(self, value):
        ...

    @property
    def rotateCamera(self) -> ControlItem:
        return ControlItem(self.settings.rotateCameraBind)

    @rotateCamera.setter
    def rotateCamera(self, value):
        ...

    @property
    def zoomCamera(self) -> ControlItem:
        return ControlItem(self.settings.zoomCameraBind)

    @zoomCamera.setter
    def zoomCamera(self, value):
        ...

    @property
    def moveSelected(self) -> ControlItem:
        return ControlItem(self.settings.moveSelectedBind)

    @moveSelected.setter
    def moveSelected(self, value):
        ...

    @property
    def selectUnderneath(self) -> ControlItem:
        return ControlItem(self.settings.selectUnderneathBind)

    @selectUnderneath.setter
    def selectUnderneath(self, value):
        ...

    @property
    def deleteSelected(self) -> ControlItem:
        return ControlItem(self.settings.deleteSelectedBind)

    @deleteSelected.setter
    def deleteSelected(self, value):
        ...
