from __future__ import annotations

import traceback

from contextlib import suppress
from typing import TYPE_CHECKING, Any

from qtpy.QtCore import Qt
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QApplication, QHBoxLayout, QLabel, QMenu, QMessageBox, QWidget

from pykotor.common.misc import Color
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.lyt import read_lyt
from pykotor.resource.generics.pth import PTH, bytes_pth, read_pth
from pykotor.resource.type import ResourceType
from toolset.data.misc import ControlItem
from toolset.gui.editor import Editor
from toolset.gui.helpers.callback import BetterMessageBox
from toolset.gui.widgets.settings.editor_settings.git import GITSettings
from toolset.gui.widgets.settings.widgets.module_designer import ModuleDesignerSettings
from utility.common.geometry import SurfaceMaterial, Vector2
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    import os

    from collections.abc import Callable

    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QKeyEvent, QMouseEvent
    from qtpy.QtWidgets import QStatusBar

    from pykotor.extract.file import ResourceIdentifier, ResourceResult
    from pykotor.resource.formats.bwm.bwm_data import BWM
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.generics.git import GITInstance
    from toolset.data.installation import HTInstallation
    from utility.common.geometry import Vector3


class CustomStdout:
    def __init__(self, editor: PTHEditor):
        self.prev_status_out: str = ""
        self.prev_status_error: str = ""
        self.mouse_pos = Vector2.from_null()  # Initialize with a default position
        self.editor: PTHEditor = editor

        sbar = editor.statusBar()
        assert sbar is not None
        self.editor_status_bar: QStatusBar = sbar

    def write(self, text):  # Update status bar with stdout content
        self.update_status_bar(stdout=text)

    def flush(self):  # Required for compatibility
        ...

    def update_status_bar(
        self,
        stdout: str = "",
        stderr: str = "",
    ):
        # Update stderr if provided
        if stderr:
            self.prev_status_error = stderr

        # If a message is provided (e.g., from the decorator), use it as the last stdout
        if stdout:
            self.prev_status_out = stdout

        # Construct the status text using last known values
        left_status = str(self.mouse_pos)
        center_status = str(self.prev_status_out)
        right_status = str(self.prev_status_error)
        self.editor.update_status_bar(left_status, center_status, right_status)


def status_bar_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
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
            editor.status_out.update_status_bar(func_call_repr)
            return func(self, *args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            error_message = str(universal_simplify_exception(e))
            editor.status_out.update_status_bar(stderr=error_message)  # Update the status bar with the error
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
        self.setup_status_bar()
        self.status_out: CustomStdout = CustomStdout(self)

        from toolset.uic.qtpy.editors.pth import Ui_MainWindow
        self.ui: Ui_MainWindow = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._add_help_action()
        self._setup_signals()

        self._pth: PTH = PTH()
        self._controls: PTHControlScheme = PTHControlScheme(self)

        self.settings: GITSettings = GITSettings()

        def intColorToQColor(num_color: int) -> QColor:
            color: Color = Color.from_rgba_integer(num_color)
            return QColor(int(color.r * 255), int(color.g * 255), int(color.b * 255), int(color.a * 255))

        self.material_colors: dict[SurfaceMaterial, QColor] = {
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

        self.ui.renderArea.material_colors = self.material_colors
        self.ui.renderArea.hide_walkmesh_edges = True
        self.ui.renderArea.highlight_boundaries = False

        self.new()

    def setup_status_bar(self):
        # Create labels for the different parts of the status message
        self.leftLabel = QLabel("Left Status")
        self.centerLabel = QLabel("Center Status")
        self.rightLabel = QLabel("Right Status")

        # Ensure the center label's text is centered
        self.centerLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        sbar = self.statusBar()
        assert sbar is not None
        sbar.addPermanentWidget(statusWidget, 1)

    def update_status_bar(
        self,
        left_status: str = "",
        center_status: str = "",
        right_status: str = "",
    ):
        # Update the text of each label
        try:
            self._core_update_status_bar(left_status, center_status, right_status)
        except RuntimeError:  # wrapped C/C++ object of type QLabel has been deleted
            self.setup_status_bar()
            self._core_update_status_bar(left_status, center_status, right_status)

    def _core_update_status_bar(
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
        self.status_out.mouse_pos = Vector2(point.x(), point.y())
        self.status_out.update_status_bar()

    def _setup_signals(self):
        self.ui.renderArea.sig_mouse_pressed.connect(self.on_mouse_pressed)
        self.ui.renderArea.sig_mouse_moved.connect(self.on_mouse_moved)
        self.ui.renderArea.sig_mouse_scrolled.connect(self.on_mouse_scrolled)
        self.ui.renderArea.sig_mouse_released.connect(self.on_mouse_released)
        self.ui.renderArea.customContextMenuRequested.connect(self.on_context_menu)
        self.ui.renderArea.sig_key_pressed.connect(self.on_key_pressed)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)  # sourcery skip: class-extract-method

        order: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES]
        assert self._installation is not None
        result: ResourceResult | None = self._installation.resource(resref, ResourceType.LYT, order)
        if result:
            self.loadLayout(read_lyt(result.data))
        else:
            from toolset.gui.common.localization import translate as tr, trf
            from toolset.gui.helpers.callback import BetterMessageBox
            BetterMessageBox(tr("Layout not found"), trf("PTHEditor requires {resref}.lyt in order to load '{resref}.{restype}', but it could not be found.", resref=str(resref), restype=str(restype)), icon=QMessageBox.Icon.Critical).exec()

        pth: PTH = read_pth(data)
        self._loadPTH(pth)

    @status_bar_decorator
    def _loadPTH(self, pth: PTH):
        self._pth = pth
        self.ui.renderArea.center_camera()
        self.ui.renderArea.set_pth(pth)

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
        assert self._installation is not None
        walkmeshes: list[BWM] = []
        for room in layout.rooms:
            order: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES]
            findBWM: ResourceResult | None = self._installation.resource(room.model, ResourceType.WOK, order)
            if findBWM is not None:
                print(
                    "loadLayout",
                    "BWM Found",
                    f"{findBWM.resname}.{findBWM.restype}",
                    file=self.status_out,
                )
                walkmeshes.append(read_bwm(findBWM.data))

        self.ui.renderArea.set_walkmeshes(walkmeshes)

    @status_bar_decorator
    def moveCameraToSelection(self):
        instance: GITInstance | None = self.ui.renderArea.instance_selection.last()
        if instance:
            self.ui.renderArea.camera.set_position(instance.position.x, instance.position.y)

    @status_bar_decorator
    def move_camera(self, x: float, y: float):
        self.ui.renderArea.camera.nudge_position(x, y)

    @status_bar_decorator
    def zoom_camera(self, amount: float):
        self.ui.renderArea.camera.nudge_zoom(amount)

    @status_bar_decorator
    def rotate_camera(self, angle: float):
        self.ui.renderArea.camera.nudge_rotation(angle)

    @status_bar_decorator
    def move_selected(self, x: float, y: float):
        for point in self.ui.renderArea.path_selection.all():
            point.x = x
            point.y = y

    @status_bar_decorator
    def select_node_under_mouse(self):
        if self.ui.renderArea.path_nodes_under_mouse():
            to_select: list[Vector2] = [self.ui.renderArea.path_nodes_under_mouse()[0]]
            print("select_node_under_mouse", "to_select:", to_select)
            self.ui.renderArea.path_selection.select(to_select)
        else:
            print("select_node_under_mouse", "clear():", file=self.status_out)
            self.ui.renderArea.path_selection.clear()

    @status_bar_decorator
    def addNode(self, x: float, y: float):
        self._pth.add(x, y)

    @status_bar_decorator
    def remove_node(self, index: int):
        self._pth.remove(index)
        self.ui.renderArea.path_selection.clear()

    @status_bar_decorator
    def removeEdge(self, source: int, target: int):
        # Remove bidirectional connections like other path editors
        self._pth.disconnect(source, target)
        self._pth.disconnect(target, source)

    @status_bar_decorator
    def addEdge(self, source: int, target: int):
        # Create bidirectional connections like other path editors
        self._pth.connect(source, target)
        self._pth.connect(target, source)

    @status_bar_decorator
    def points_under_mouse(self) -> list[Vector2]:
        return self.ui.renderArea.path_nodes_under_mouse()

    @status_bar_decorator
    def selected_nodes(self) -> list[Vector2]:
        return self.ui.renderArea.path_selection.all()

    # region Signal Callbacks
    @status_bar_decorator
    def on_context_menu(self, point: QPoint):
        global_point: QPoint = self.ui.renderArea.mapToGlobal(point)
        world: Vector3 = self.ui.renderArea.to_world_coords(point.x(), point.y())
        self._controls.on_render_context_menu(Vector2.from_vector3(world), global_point)

    @status_bar_decorator
    def on_mouse_moved(self, screen: Vector2, delta: Vector2, buttons: set[int], keys: set[int]):
        world_delta: Vector2 = self.ui.renderArea.to_world_delta(delta.x, delta.y)
        world: Vector3 = self.ui.renderArea.to_world_coords(screen.x, screen.y)
        self._controls.on_mouse_moved(screen, delta, Vector2.from_vector3(world), world_delta, buttons, keys)

    @status_bar_decorator
    def on_mouse_scrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        #print(f"on_mouse_scrolled(delta={delta!r})", file=self.stdout)
        self._controls.on_mouse_scrolled(delta, buttons, keys)

    def on_mouse_pressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        #print(f"on_mouse_pressed(screen={screen!r})", file=self.stdout)
        self._controls.on_mouse_pressed(screen, buttons, keys)

    @status_bar_decorator
    def on_mouse_released(self, screen: Vector2, buttons: set[int], keys: set[int]):
        #print("on_mouse_released", file=self.stdout)
        self._controls.on_mouse_released(Vector2(0, 0), buttons, keys)

    @status_bar_decorator
    def on_key_pressed(self, buttons: set[int], keys: set[int]):
        #print("on_key_pressed", file=self.stdout)
        self._controls.on_keyboard_pressed(buttons, keys)

    @status_bar_decorator
    def keyPressEvent(self, e: QKeyEvent):
        #print(f"keyPressEvent(e={e!r})", file=self.stdout)
        if e is None:
            return
        self.ui.renderArea.keyPressEvent(e)

    @status_bar_decorator
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

    @status_bar_decorator
    def mouseMoveEvent(self, event: QMouseEvent):
        point: QPoint = event.pos()
        self.editor.status_out.mouse_pos = Vector2(point.x(), point.y())

    @status_bar_decorator
    def on_mouse_scrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        if self.zoom_camera.satisfied(buttons, keys):
            if not delta.y:
                return  # sometimes it'll be zero when holding middlemouse-down.
            sensSetting = ModuleDesignerSettings().zoomCameraSensitivity2d
            zoom_factor = calculate_zoom_strength(delta.y, sensSetting)
            #RobustLogger.debug(f"on_mouse_scrolled zoom_camera (delta.y={delta.y}, zoom_factor={zoom_factor}, sensSetting={sensSetting}))")
            self.editor.zoom_camera(zoom_factor)

    @status_bar_decorator
    def on_mouse_moved(self, screen: Vector2, screenDelta: Vector2, world: Vector2, world_delta: Vector2, buttons: set[int], keys: set[int]):
        self.editor.status_out.mouse_pos = screen
        shouldPanCamera = self.pan_camera.satisfied(buttons, keys)
        shouldrotate_camera = self.rotate_camera.satisfied(buttons, keys)
        if shouldPanCamera or shouldrotate_camera:
            self.editor.ui.renderArea.do_cursor_lock(screen)
        if shouldPanCamera:
            moveSens = ModuleDesignerSettings().moveCameraSensitivity2d / 100
            #RobustLogger.debug(f"on_mouse_scrolled move_camera (delta.y={screenDelta.y}, sensSetting={moveSens}))")
            self.editor.move_camera(-world_delta.x * moveSens, -world_delta.y * moveSens)
        if shouldrotate_camera:
            delta_magnitude = abs(screenDelta.x)
            direction = -1 if screenDelta.x < 0 else 1 if screenDelta.x > 0 else 0
            rotateSens = ModuleDesignerSettings().rotateCameraSensitivity2d / 1000
            rotateAmount = delta_magnitude * rotateSens * direction
            #RobustLogger.debug(f"on_mouse_scrolled rotate_camera (delta_value={delta_magnitude}, rotateAmount={rotateAmount}, sensSetting={rotateSens}))")
            self.editor.rotate_camera(rotateAmount)
        if self.move_selected.satisfied(buttons, keys):
            self.editor.move_selected(world.x, world.y)

    @status_bar_decorator
    def on_mouse_pressed(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        if self.select_underneath.satisfied(buttons, keys):
            self.editor.select_node_under_mouse()

    @status_bar_decorator
    def on_mouse_released(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]): ...

    @status_bar_decorator
    def on_keyboard_pressed(self, buttons: set[Qt.Key], keys: set[Qt.Key]):
        if self.delete_selected.satisfied(buttons, keys):
            node = None
            try:
                node = self.editor.pth().find(self.editor.points_under_mouse()[0])
            except Exception:
                with suppress(Exception):
                    node = self.editor.pth().find(self.editor.selected_nodes()[0])
            if node is None:
                return
            self.editor.remove_node(node)

    @status_bar_decorator
    def onKeyboardReleased(self, buttons: set[Qt.Key], keys: set[Qt.Key]): ...

    @status_bar_decorator
    def on_render_context_menu(self, world: Vector2, screen: QPoint):
        points_under_mouse: list[Vector2] = self.editor.points_under_mouse()
        selected_nodes: list[Vector2] = self.editor.selected_nodes()

        under_mouse_index: int | None = None
        if points_under_mouse and points_under_mouse[0]:
            for point in points_under_mouse:
                with suppress(ValueError, IndexError):
                    under_mouse_index = self.editor.pth().find(point)
                    if under_mouse_index is not None:
                        break
        selected_index: int | None = None
        if selected_nodes and selected_nodes[0]:
            for selected in selected_nodes:
                with suppress(ValueError, IndexError):
                    selected_index = self.editor.pth().find(selected)
                    if selected_index is not None:
                        break
        print(
            f"selected_index:{selected_index}",
            f"under_mouse_index:{under_mouse_index}",
            f"on_render_context_menu(world={world!r}, screen={screen!r})",
            file=self.editor.status_out,
        )

        menu = QMenu(self.editor)
        from toolset.gui.common.localization import translate as tr
        menu.addAction(tr("Add Node")).triggered.connect(lambda _=None: self.editor.addNode(world.x, world.y))
        menu.addAction(tr("Copy XY coords")).triggered.connect(lambda: QApplication.clipboard().setText(str(self.editor.status_out.mouse_pos)))  # pyright: ignore[reportOptionalMemberAccess]
        if under_mouse_index is not None:
            menu.addAction(tr("Remove Node")).triggered.connect(lambda _=None: self.editor.remove_node(under_mouse_index))

        menu.addSeparator()

        if under_mouse_index is not None and selected_index is not None:
            menu.addAction("Add Edge").triggered.connect(lambda _=None: self.editor.addEdge(selected_index, under_mouse_index))
            menu.addAction("Remove Edge").triggered.connect(lambda _=None: self.editor.removeEdge(selected_index, under_mouse_index))

        menu.popup(screen)

    # Use @property decorators to allow Users to change their settings without restarting the editor.
    @property
    def pan_camera(self) -> ControlItem:
        return ControlItem(self.settings.moveCameraBind)

    @pan_camera.setter
    def pan_camera(self, value):
        ...

    @property
    def rotate_camera(self) -> ControlItem:
        return ControlItem(self.settings.rotateCameraBind)

    @rotate_camera.setter
    def rotate_camera(self, value):
        ...

    @property
    def zoom_camera(self) -> ControlItem:
        return ControlItem(self.settings.zoomCameraBind)

    @zoom_camera.setter
    def zoom_camera(self, value):
        ...

    @property
    def move_selected(self) -> ControlItem:
        return ControlItem(self.settings.moveSelectedBind)

    @move_selected.setter
    def move_selected(self, value):
        ...

    @property
    def select_underneath(self) -> ControlItem:
        return ControlItem(self.settings.selectUnderneathBind)

    @select_underneath.setter
    def select_underneath(self, value):
        ...

    @property
    def delete_selected(self) -> ControlItem:
        return ControlItem(self.settings.deleteSelectedBind)

    @delete_selected.setter
    def delete_selected(self, value):
        ...
