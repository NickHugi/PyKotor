from __future__ import annotations

import traceback

from contextlib import suppress
from typing import TYPE_CHECKING, Any

import pyperclip

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QMenu, QStatusBar, QWidget

from pykotor.common.geometry import SurfaceMaterial, Vector2
from pykotor.common.misc import Color
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.lyt import read_lyt
from pykotor.resource.generics.pth import PTH, bytes_pth, read_pth
from pykotor.resource.type import ResourceType
from toolset.data.misc import ControlItem
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.git import GITSettings
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    import os

    from collections.abc import Callable

    from PyQt5.QtCore import QPoint
    from PyQt5.QtGui import QKeyEvent, QMouseEvent

    from pykotor.common.geometry import Vector3
    from pykotor.extract.file import ResourceIdentifier, ResourceResult
    from pykotor.resource.formats.bwm.bwm_data import BWM
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.generics.git import GITInstance
    from toolset.data.installation import HTInstallation


class CustomStdout:
    def __init__(self, editor: PTHEditor):
        self.last_stdout: str = ""
        self.last_stderr: str = ""
        self.mouse_pos = Vector2.from_null()  # Initialize with a default position
        self.editor: PTHEditor = editor
        self.status_bar = editor.statusBar()

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
            self.last_stderr = stderr

        # If a message is provided (e.g., from the decorator), use it as the last stdout
        if stdout:
            self.last_stdout = stdout

        # Construct the status text using last known values
        left_status = str(self.mouse_pos)
        center_status = str(self.last_stdout)
        right_status = str(self.last_stderr)
        self.editor.updateStatusBar(left_status, center_status, right_status)


def status_bar_decorator(func):
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
            editor.stdout.updateStatusBar(func_call_repr)
            result = func(self, *args, **kwargs)
            # Update the status bar to show the function call
            return result
        except Exception as e:
            traceback.print_exc()
            error_message = str(universal_simplify_exception(e))
            editor.stdout.updateStatusBar(stderr=error_message)  # Update the status bar with the error
            raise  # Re-raise the exception after logging it to the status bar

    return wrapper


def auto_decorate_methods(decorator: Callable[..., Any]) -> Callable[..., Any]:
    """Class decorator to automatically apply a decorator to all methods."""
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
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        supported: list[ResourceType] = [ResourceType.PTH]
        super().__init__(parent, "PTH Editor", "pth", supported, supported, installation)
        self.setupStatusBar()
        self.stdout = CustomStdout(self)

        from toolset.uic.editors.pth import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self._pth: PTH = PTH()
        self._controls: PTHControlScheme = PTHControlScheme(self)

        self.settings = GITSettings()

        def intColorToQColor(num_color) -> QColor:
            color = Color.from_rgba_integer(num_color)
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
        self.setStatusBar(QStatusBar(self))
        self.statusBar().addPermanentWidget(statusWidget, 1)

    def updateStatusBar(
        self,
        left_status: str = "",
        center_status: str = "",
        right_status: str = "",
    ):
        # Update the text of each label
        try:
            self._core_update_status_bar(
                left_status, center_status, right_status
            )
        except RuntimeError:  # wrapped C/C++ object of type QLabel has been deleted
            self.setupStatusBar()
            self._core_update_status_bar(
                left_status, center_status, right_status
            )

    # TODO Rename this here and in `updateStatusBar`
    def _core_update_status_bar(self, left_status, center_status, right_status):
        if left_status and left_status.strip():
            self.leftLabel.setText(left_status)
        if center_status and center_status.strip():
            self.centerLabel.setText(center_status)
        if right_status and right_status.strip():
            self.rightLabel.setText(right_status)

    def mouseMoveEvent(self, event: QMouseEvent):
        self.stdout.mouse_pos = Vector2(*event.pos())
        self.stdout.updateStatusBar()

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

        pth: PTH = read_pth(data)
        self._loadPTH(pth)

    @status_bar_decorator
    def _loadPTH(self, pth: PTH):
        self._pth = pth
        self.ui.renderArea.centerCamera()
        self.ui.renderArea.setPth(pth)

    def build(self) -> tuple[bytes, bytes]:
        return bytes_pth(self._pth), b""

    def new(self):
        super().new()
        self._loadPTH(PTH())

    @status_bar_decorator
    def pth(self) -> PTH:
        return self._pth

    @status_bar_decorator
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
                    file=self.stdout,
                )
                walkmeshes.append(read_bwm(findBWM.data))

        self.ui.renderArea.setWalkmeshes(walkmeshes)

    @status_bar_decorator
    def moveCameraToSelection(self):
        instance: GITInstance | None = self.ui.renderArea.instanceSelection.last()
        if instance:
            self.ui.renderArea.camera.setPosition(instance.position.x, instance.position.y)

    @status_bar_decorator
    def moveCamera(self, x: float, y: float):
        self.ui.renderArea.camera.nudgePosition(x, y)

    @status_bar_decorator
    def zoomCamera(self, amount: float):
        self.ui.renderArea.camera.nudgeZoom(amount)

    @status_bar_decorator
    def rotateCamera(self, angle: float):
        self.ui.renderArea.camera.nudgeRotation(angle)

    @status_bar_decorator
    def moveSelected(self, x: float, y: float):
        for point in self.ui.renderArea.pathSelection.all():
            point.x = x
            point.y = y

    @status_bar_decorator
    def selectNodeUnderMouse(self):
        if self.ui.renderArea.pathNodesUnderMouse():
            toSelect: list[Vector2] = [self.ui.renderArea.pathNodesUnderMouse()[0]]
            print("selectNodeUnderMouse", "toSelect:", toSelect)
            self.ui.renderArea.pathSelection.select(toSelect)
        else:
            print("selectNodeUnderMouse", "clear():", file=self.stdout)
            self.ui.renderArea.pathSelection.clear()

    @status_bar_decorator
    def addNode(self, x: float, y: float):
        self._pth.add(x, y)

    @status_bar_decorator
    def removeNode(self, index: int):
        self._pth.remove(index)
        self.ui.renderArea.pathSelection.clear()

    @status_bar_decorator
    def removeEdge(self, source: int, target: int):
        self._pth.disconnect(source, target)

    @status_bar_decorator
    def addEdge(self, source: int, target: int):
        self._pth.connect(source, target)

    @status_bar_decorator
    def pointsUnderMouse(self) -> list[Vector2]:
        return self.ui.renderArea.pathNodesUnderMouse()

    @status_bar_decorator
    def selectedNodes(self) -> list[Vector2]:
        return self.ui.renderArea.pathSelection.all()

    # region Signal Callbacks
    @status_bar_decorator
    def onContextMenu(self, point: QPoint):
        globalPoint: QPoint = self.ui.renderArea.mapToGlobal(point)
        world: Vector3 = self.ui.renderArea.toWorldCoords(point.x(), point.y())
        self._controls.onRenderContextMenu(Vector2.from_vector3(world), globalPoint)

    @status_bar_decorator
    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: set[int], keys: set[int]):
        worldDelta: Vector2 = self.ui.renderArea.toWorldDelta(delta.x, delta.y)
        world: Vector3 = self.ui.renderArea.toWorldCoords(screen.x, screen.y)
        self._controls.onMouseMoved(screen, delta, Vector2.from_vector3(world), worldDelta, buttons, keys)

    @status_bar_decorator
    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        print(f"onMouseScrolled(delta={delta!r})", file=self.stdout)
        self._controls.onMouseScrolled(delta, buttons, keys)

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        print(f"onMousePressed(screen={screen!r})", file=self.stdout)
        self._controls.onMousePressed(screen, buttons, keys)

    @status_bar_decorator
    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        print("onMouseReleased", file=self.stdout)
        self._controls.onMouseReleased(Vector2(0, 0), buttons, keys)

    @status_bar_decorator
    def onKeyPressed(self, buttons: set[int], keys: set[int]):
        print("onKeyPressed", file=self.stdout)
        self._controls.onKeyboardPressed(buttons, keys)

    @status_bar_decorator
    def keyPressEvent(self, e: QKeyEvent | None):
        print(f"keyPressEvent(e={e!r})", file=self.stdout)
        if e is None:
            return
        self.ui.renderArea.keyPressEvent(e)

    @status_bar_decorator
    def keyReleaseEvent(self, e: QKeyEvent | None):
        print(f"keyReleaseEvent(e={e!r})", file=self.stdout)
        if e is None:
            return
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

    @status_bar_decorator
    def mouseMoveEvent(self, event: QMouseEvent):
        self.editor.stdout.mouse_pos = Vector2(*event.pos())

    @status_bar_decorator
    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        if self.zoomCamera.satisfied(buttons, keys):
            # A smaller zoom_step will provide finer control over the zoom level.
            if not delta.y:
                return  # sometimes it'll be zero when holding middlemouse-down.
            zoom_factor = 1.1 if delta.y > 0 else 0.9
            self.editor.zoomCamera(zoom_factor)

    @status_bar_decorator
    def onMouseMoved(
        self,
        screen: Vector2,
        screenDelta: Vector2,
        world: Vector2,
        worldDelta: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        self.editor.stdout.mouse_pos = screen
        if self.panCamera.satisfied(buttons, keys):
            self.editor.moveCamera(-worldDelta.x, -worldDelta.y)
        if self.rotateCamera.satisfied(buttons, keys):
            self.editor.rotateCamera(screenDelta.y)
        if self.moveSelected.satisfied(buttons, keys):
            self.editor.moveSelected(world.x, world.y)

    @status_bar_decorator
    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        if self.selectUnderneath.satisfied(buttons, keys):
            self.editor.selectNodeUnderMouse()

    @status_bar_decorator
    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        ...

    @status_bar_decorator
    def onKeyboardPressed(self, buttons: set[int], keys: set[int]):
        if self.deleteSelected.satisfied(buttons, keys):
            node = None
            try:
                node = self.editor.pth().find(self.editor.pointsUnderMouse()[0])
            except Exception:
                with suppress(Exception):
                    node = self.editor.pth().find(self.editor.selectedNodes()[0])
            if not node:
                return
            self.editor.removeNode(node)

    @status_bar_decorator
    def onKeyboardReleased(self, buttons: set[int], keys: set[int]):
        ...

    @status_bar_decorator
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
            file=self.editor.stdout,
        )

        menu = QMenu(self.editor)
        menu.addAction("Add Node").triggered.connect(lambda _: self.editor.addNode(world.x, world.y))
        menu.addAction("Copy XY coords").triggered.connect(lambda: pyperclip.copy(str(self.editor.stdout.mouse_pos)))
        if underMouseIndex is not None:
            menu.addAction("Remove Node").triggered.connect(lambda _: self.editor.removeNode(underMouseIndex))

        menu.addSeparator()

        if underMouseIndex is not None and selectedIndex is not None:
            menu.addAction("Add Edge").triggered.connect(lambda _: self.editor.addEdge(selectedIndex, underMouseIndex))
            menu.addAction("Remove Edge").triggered.connect(lambda _: self.editor.removeEdge(selectedIndex, underMouseIndex))

        menu.popup(screen)
