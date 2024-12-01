
from __future__ import annotations

import concurrent.futures
import functools
import json
import os
import time

from concurrent.futures import ProcessPoolExecutor
from typing import TYPE_CHECKING, Any, Callable, Optional, cast

import qtpy

from toolset.gui.widgets.renderer.lyt_editor import LYTRenderer

from loggerplus import RobustLogger
from qtpy.QtCore import (
    QByteArray,
    QEvent,
    QMimeData,
    QModelIndex,
    QPoint,
    QSettings,
    QSize,
    QTimer,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QAction, QActionGroup, QDrag, QHelpEvent, QIcon, QKeySequence, QPainter, QPalette, QPixmap, QShortcut, QUndoCommand
from qtpy.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog, 
    QDockWidget,
    QErrorMessage,
    QFileDialog,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWhatsThis,
    QWidget,
)

from pykotor.common.geometry import Vector3
from pykotor.resource.formats.lyt.lyt_auto import write_lyt
from pykotor.resource.resource_auto import BWM
from toolset.data.lyt_structures import (
    ExtendedLYT as LYT,
    ExtendedLYTDoorHook as LYTDoorHook,
    ExtendedLYTObstacle as LYTObstacle,
    ExtendedLYTRoom as LYTRoom,
    ExtendedLYTTrack as LYTTrack,
)
from toolset.gui.dialogs.lyt_dialogs import ObstaclePropertiesDialog, RoomPropertiesDialog, TrackPropertiesDialog
from toolset.gui.editors.lyt import LYTEditor
from toolset.gui.widgets.customizable_toolbar import CustomizableToolBar
from toolset.gui.widgets.renderer.custom_toolbar import (
    CustomizableToolBar,  # FIXME: CustomizableToolBar not found
)
from toolset.gui.widgets.renderer.lyt_editor import LYTEditor
from toolset.gui.widgets.renderer.texture_browser import TextureBrowser
from toolset.gui.widgets.renderer.walkmesh_editor import DoorHookPropertiesDialog, WalkmeshEditor

if qtpy.QT5:
    from qtpy.QtWidgets import QUndoStack
elif qtpy.QT6:
    from qtpy.QtGui import QUndoStack
else:
    raise RuntimeError("Unsupported Qt version")
if TYPE_CHECKING:
    from concurrent.futures import Future

    from qtpy.QtCore import QAbstractItemModel, QObject
    from qtpy.QtGui import (
        QCloseEvent,
        QContextMenuEvent,
        QDragEnterEvent,
        QDragLeaveEvent,
        QDragMoveEvent,
        QDropEvent,
        QFocusEvent,
        QKeyEvent,
        QMouseEvent,
        QPaintEvent,
        QShowEvent,
        QWheelEvent,
        _QAction,
    )
    from qtpy.QtWidgets import _QMenu
    from typing_extensions import Literal

    from toolset.gui.widgets.renderer.module import ModuleRenderer


"""UI wrapper widget for the LYT editor.

Provides the user interface elements around the core LYT editor,
including toolbars, property panels, etc.
"""

class LYTEditorWidget(QWidget):
    """UI wrapper widget for the LYT editor.

    Provides the user interface elements and coordinates between the core editor,
    texture browser, and walkmesh editor components.
    """
    # Signals for coordinating UI state changes
    sig_lyt_updated = Signal(LYT)  # Emitted when LYT data changes
    sig_walkmesh_updated = Signal(BWM)  # Emitted when walkmesh changes
    sig_ui_state_changed = Signal(str)  # Emitted when UI state changes (tool selection etc)

    # Qt constants
    HORIZONTAL = Qt.Orientation.Horizontal
    VERTICAL = Qt.Orientation.Vertical
    POINTING_HAND_CURSOR = Qt.CursorShape.PointingHandCursor
    CLOSED_HAND_CURSOR = Qt.CursorShape.ClosedHandCursor
    ARROW_CURSOR = Qt.CursorShape.ArrowCursor
    LEFT_BUTTON = Qt.MouseButton.LeftButton
    MIDDLE_BUTTON = Qt.MouseButton.MiddleButton
    COPY_ACTION = Qt.DropAction.CopyAction
    MOVE_ACTION = Qt.DropAction.MoveAction
    KEY_DELETE = Qt.Key.Key_Delete
    KEY_F2 = Qt.Key.Key_F2
    ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
    ALIGN_BOTTOM = Qt.AlignmentFlag.AlignBottom
    ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight
    TOOL_TIP = QEvent.Type.ToolTip
    ANTIALIASING = QPainter.RenderHint.Antialiasing
    TEXT_COLOR = QPalette.ColorRole.Text
    DISPLAY_ROLE = Qt.ItemDataRole.DisplayRole
    INFORMATION = QMessageBox.Icon.Information
    DOCKWIDGET_MOVABLE = QDockWidget.DockWidgetFeature.DockWidgetMovable
    DOCKWIDGET_FLOATABLE = QDockWidget.DockWidgetFeature.DockWidgetFloatable
    TICKS_BELOW = QSlider.TickPosition.TicksBelow

    def __init__(self, parent: ModuleRenderer):
        super().__init__(parent)
        self.parent_ref = parent

        # Core editing components
        self.lyt_renderer = LYTRenderer(parent)  # Core rendering component
        self.texture_browser = TextureBrowser(self)  # Texture management
        self.walkmesh_editor = WalkmeshEditor(self)  # Walkmesh editing

        # UI state
        self.current_tool = "select"
        self.ui_state = {}
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)

        # Initialize actions
        self._undo_action: _QAction = QAction("Undo", self)
        self._undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self._undo_action.setIcon(QIcon(":/icons/undo.png"))
        self._undo_action.setToolTip("Undo last action")

        self._redo_action: _QAction = QAction("Redo", self)
        self._redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self._redo_action.setIcon(QIcon(":/icons/redo.png"))
        self._redo_action.setToolTip("Redo last action")

        self.process_pool: ProcessPoolExecutor = ProcessPoolExecutor(
            max_workers=max(1, os.cpu_count() - 1),
            initializer=self._worker_init,
        )
        self.status_bar: QStatusBar = QStatusBar(self)
        self.active_tasks: int = 0
        self.task_queue: list[tuple[Callable[..., Any], Any]] = []
        self.undo_stack: QUndoStack = QUndoStack(self)
        self.zoom_pan_widget: ZoomPanWidget = ZoomPanWidget(self)
        self.settings: QSettings = QSettings("PyKotor", "HolocronToolset")
        self.current_tool: str | None = None
        self.setAcceptDrops(True)
        self.initUI()
        self.last_action_time: float = time.time()
        self.layout_config: dict[str, Any] = {}
        self.search_results: list[Any] = []
        self.help_overlay: QWidget | None = None
        self.context_help: dict[QWidget, str] = {}
        self.setup_context_help()
        self.setup_drag_and_drop()
        self.setup_tool_selector()
        self.setupRealTimePreview()
        self.setup_undo_view()
        self.setup_error_handler()

        self.current_lyt: LYT | None = None
        self.room_templates: dict[str, LYTRoom] = {}
        self.custom_textures: dict[str, QPixmap] = {}
        self.selected_room: LYTRoom | None = None

        self.setup_lyt_tools()

        # Initialize LYT rendering
        self.load_current_lyt()

    def _worker_init(self):
        # Initialize worker process with necessary resources

        # Add any other necessary imports or initializations for worker processes
        RobustLogger().debug("Worker process initialized")

    def initUI(self):
        main_layout = QVBoxLayout(self)

        # Create main toolbar
        self.main_toolbar: CustomizableToolBar = CustomizableToolBar("LYT Editor Toolbar")
        self.main_toolbar.setIconSize(QSize(24, 24))
        self.setup_main_toolbar()
        main_layout.addWidget(self.main_toolbar)

        # Create main splitter for resizable widgets
        self.main_splitter: QSplitter = QSplitter(Qt.Orientation.Horizontal)

        # Add LYTEditor
        self.main_splitter.addWidget(self.lyt_editor)

        # Create right-side panel
        self.right_panel: QWidget = QWidget()
        self.right_layout: QVBoxLayout = QVBoxLayout(self.right_panel)

        # Add texture browser
        self.texture_dock: QDockWidget = QDockWidget("Textures", self)
        self.texture_dock.setWidget(self.texture_browser)
        self.texture_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.right_layout.addWidget(self.texture_dock)

        # Add walkmesh editor
        self.walkmesh_dock: QDockWidget = QDockWidget("Walkmesh Editor", self)
        self.walkmesh_dock.setWidget(self.walkmesh_editor)
        self.walkmesh_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.right_layout.addWidget(self.walkmesh_dock)

        self.main_splitter.addWidget(self.right_panel)

        # Make the splitter handle more visible
        self.main_splitter.setHandleWidth(5)
        self.main_splitter.setStyleSheet("QSplitter::handle { background-color: palette(mid); }")

        main_layout.addWidget(self.main_splitter)
        main_layout.addWidget(self.status_bar)
        self.setLayout(main_layout)
        self.setMinimumSize(800, 600)  # Set minimum size for better usability

        # Restore layout state
        self.restore_layout_state()

        # Setup shortcuts
        self.setup_shortcuts()

    def setup_undo_view(self):
        from qtpy.QtWidgets import QUndoView

        self.undo_view: QUndoView = QUndoView(self.undo_stack)
        self.undo_view.setWindowTitle("Command History")
        self.undo_view.show()

    def setup_error_handler(self):
        self.error_dialog: QErrorMessage = QErrorMessage(self)
        self.error_dialog.setWindowTitle("Error")
        self.error_dialog.setMinimumSize(400, 300)
        self.error_dialog.setPalette(self.error_dialog.palette())

    def setup_tool_selector(self):
        tool_group = QActionGroup(self)
        tool_group.setExclusive(True)

        select_tool = QAction(QIcon("path/to/select_icon.png"), "Select", self)
        select_tool.setCheckable(True)
        select_tool.setChecked(True)
        self.current_tool = "select"

        room_tool = QAction(QIcon("path/to/room_icon.png"), "Room", self)
        room_tool.setCheckable(True)

        door_tool = QAction(QIcon("path/to/door_icon.png"), "Door", self)
        door_tool.setCheckable(True)

        tool_group.addAction(select_tool)
        tool_group.addAction(room_tool)
        tool_group.addAction(door_tool)
        tool_group.triggered.connect(self.on_tool_selected)

    def setupRealTimePreview(self):
        self.preview_timer: QTimer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_realtime_preview)
        self.lyt_editor.sig_lyt_updated.connect(self.schedule_preview_update)
        self.texture_browser.sig_texture_changed.connect(self.schedule_preview_update)

    def setup_main_toolbar(self):
        # Room actions
        self.room_actions: list[_QAction] = []
        room_menu: _QMenu = QMenu("Room Actions", self)
        add_room_action: _QAction = room_menu.addAction(QIcon("path/to/add_room_icon.png"), "Add Room")
        add_room_action.triggered.connect(self.lyt_editor.add_room)
        resize_room_action: _QAction = room_menu.addAction(QIcon("path/to/resize_room_icon.png"), "Resize Room")
        resize_room_action.triggered.connect(self.lyt_editor.resize_room)
        rotate_room_action: _QAction = room_menu.addAction(QIcon("path/to/rotate_room_icon.png"), "Rotate Room")
        rotate_room_action.triggered.connect(self.lyt_editor.rotate_room)
        connect_rooms_action: _QAction = room_menu.addAction(QIcon("path/to/connect_rooms_icon.png"), "Connect Rooms")
        connect_rooms_action.triggered.connect(self.connect_rooms)
        self.room_actions.extend([add_room_action, resize_room_action, rotate_room_action, connect_rooms_action])

        room_tool_button = QToolButton()
        room_tool_button.setMenu(room_menu)
        room_tool_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        room_tool_button.setIcon(QIcon("path/to/room_icon.png"))
        room_tool_button.setToolTip(self.get_tool_tip("room_actions"))
        self.main_toolbar.addWidget(room_tool_button, "Room Actions")

        # Walkmesh actions
        self.walkmesh_actions: list[_QAction] = []
        walkmesh_menu: _QMenu = QMenu("Walkmesh Actions", self)

        generate_walkmesh_action: _QAction = walkmesh_menu.addAction(QIcon("path/to/generate_walkmesh_icon.png"), "Generate Walkmesh")
        generate_walkmesh_action.triggered.connect(self.generate_walkmesh)
        edit_walkmesh_action: _QAction = walkmesh_menu.addAction(QIcon("path/to/edit_walkmesh_icon.png"), "Edit Walkmesh")
        edit_walkmesh_action.triggered.connect(self.edit_walkmesh)

        walkmesh_tool_button = QToolButton()
        walkmesh_tool_button.setMenu(walkmesh_menu)
        walkmesh_tool_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        walkmesh_tool_button.setIcon(QIcon("path/to/walkmesh_icon.png"))
        walkmesh_tool_button.setToolTip(self.get_tool_tip("walkmesh_actions"))
        self.main_toolbar.addWidget(walkmesh_tool_button, "Walkmesh Actions")
        self.walkmesh_actions.extend([generate_walkmesh_action, edit_walkmesh_action])

        # Texture actions
        self.texture_actions: list[_QAction] = []
        texture_menu = QMenu("Texture Actions", self)
        import_texture_action: _QAction = texture_menu.addAction(QIcon("path/to/import_texture_icon.png"), "Import Texture")
        import_texture_action.triggered.connect(self.import_texture)
        manage_textures_action: _QAction = texture_menu.addAction(QIcon("path/to/manage_textures_icon.png"), "Manage Textures")
        manage_textures_action.triggered.connect(self.manage_textures)

        texture_tool_button = QToolButton()
        texture_tool_button.setMenu(texture_menu)
        texture_tool_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        texture_tool_button.setIcon(QIcon("path/to/texture_icon.png"))
        texture_tool_button.setToolTip(self.get_tool_tip("texture_actions"))
        self.main_toolbar.addWidget(texture_tool_button, "Texture Actions")
        self.texture_actions.extend([import_texture_action, manage_textures_action])

        # Undo/Redo actions
        undo_action: _QAction | None = self.undo_stack.createUndoAction(self, "Undo")  # pyright: ignore[reportAssignmentType]
        undo_action.setIcon(QIcon("path/to/undo_icon.png"))  # pyright: ignore[reportOptionalMemberAccess]
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)  # pyright: ignore[reportOptionalMemberAccess]
        undo_action.setToolTip(self.get_tool_tip("undo"))  # pyright: ignore[reportOptionalMemberAccess]
        self.main_toolbar.addAction(undo_action, "Edit")

        redo_action: _QAction | None = self.undo_stack.createRedoAction(self, "Redo")  # pyright: ignore[reportAssignmentType]
        redo_action.setIcon(QIcon("path/to/redo_icon.png"))  # pyright: ignore[reportOptionalMemberAccess]
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)  # pyright: ignore[reportOptionalMemberAccess]
        redo_action.setToolTip(self.get_tool_tip("redo"))  # pyright: ignore[reportOptionalMemberAccess]
        self.main_toolbar.addAction(redo_action, "Edit")

        # Zoom actions
        zoom_in_action = QAction(QIcon("path/to/zoom_in_icon.png"), "Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_pan_widget.zoom_in)
        zoom_in_action.setToolTip("Zoom In (Ctrl++)")
        self.main_toolbar.addAction(zoom_in_action, "View")

        zoom_out_action = QAction(QIcon("path/to/zoom_out_icon.png"), "Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_pan_widget.zoom_out)
        zoom_out_action.setToolTip("Zoom Out (Ctrl+-)")
        self.main_toolbar.addAction(zoom_out_action, "View")

        # Add tool selector
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.tool_group.actions()[0])
        self.main_toolbar.addAction(self.tool_group.actions()[1])
        self.main_toolbar.addAction(self.tool_group.actions()[2])

        # Add zoom slider
        self.setup_zoom_slider()

    def get_tool_tip(self, key: str) -> str:
        tooltips: dict[str, str] = {
            "room_actions": "Room Actions\nCtrl+A: Add Room\nCtrl+R: Resize Room\nCtrl+T: Rotate Room\nCtrl+C: Connect Rooms\nDel: Delete Room\nF2: Rename Room\nCtrl+D: Duplicate Room",
            "walkmesh_actions": "Walkmesh Actions\nCtrl+G: Generate Walkmesh\nCtrl+E: Edit Walkmesh\nCtrl+W: Toggle Walkmesh Visibility",
            "texture_actions": "Texture Actions\nCtrl+I: Import Texture\nCtrl+M: Manage Textures\nCtrl+B: Open Texture Browser",
            "undo": "Undo last action (Ctrl+Z)",
            "redo": "Redo last undone action (Ctrl+Y)",
        }
        return tooltips.get(key, "")

    def set_context_help(
        self,
        widget: QWidget,
        help_text: str,
    ):
        widget.setWhatsThis(help_text)
        self.context_help[widget] = help_text

    def setup_context_help(self):
        self.set_context_help(self.lyt_editor, "LYT Editor: Create and edit rooms, tracks, and obstacles.")
        self.set_context_help(self.texture_browser, "Texture Browser: Manage and apply textures to rooms.")
        self.set_context_help(self.walkmesh_editor, "Walkmesh Editor: Edit and generate walkmeshes for your layout.")
        self.set_context_help(self.main_toolbar, "Main Toolbar: Quick access to common actions and tools.")
        self.set_context_help(self.zoom_pan_widget, "Zoom and Pan: Control the view of your layout.")

        for action in self.room_actions:
            self.set_context_help(action, f"{action.text()}: {action.toolTip()}")
        for action in self.walkmesh_actions:
            self.set_context_help(action, f"{action.text()}: {action.toolTip()}")
        for action in self.texture_actions:
            self.set_context_help(action, f"{action.text()}: {action.toolTip()}")

    def on_tool_selected(self, action: _QAction):
        self.current_tool = action.text().lower()
        self.lyt_editor.set_current_tool(self.current_tool)  # FIXME: set_current_tool attribute not found

    def setup_drag_and_drop(self):
        self.setAcceptDrops(True)
        self.lyt_editor.setAcceptDrops(True)
        self.texture_browser.setAcceptDrops(True)
        self.walkmesh_editor.setAcceptDrops(True)
        self.zoom_pan_widget.setAcceptDrops(True)

    def setup_zoom_slider(self):
        self.zoom_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.zoom_slider.setTickInterval(10)
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_value_changed)
        self.main_toolbar.addWidget(self.zoom_slider)

    def save_layout_state(self):
        self.settings.setValue("LYTEditorWidget/geometry", self.saveGeometry())
        self.settings.setValue("LYTEditorWidget/windowState", self.saveState())  # FIXME: saveState attribute not found
        self.settings.setValue("LYTEditorWidget/mainSplitterState", self.main_splitter.saveState())
        self.settings.setValue("LYTEditorWidget/rightPanelLayout", json.dumps(self.save_right_panel_layout()))

    def save_right_panel_layout(self) -> dict[str, dict[str, Any]]:
        return {
            "texture_dock": {"visible": self.texture_dock.isVisible(), "geometry": self.texture_dock.saveGeometry().toHex().decode()},
            "walkmesh_dock": {"visible": self.walkmesh_dock.isVisible(), "geometry": self.walkmesh_dock.saveGeometry().toHex().decode()},
        }

    def restore_layout_state(self):
        geometry = self.settings.value("LYTEditorWidget/geometry")
        if geometry:
            self.restoreGeometry(geometry)

        self.main_toolbar.restore_state(self.settings.value("LYTEditorWidget/toolbarState"))

        state = self.settings.value("LYTEditorWidget/windowState")
        if state:
            self.restore_state(state)  # FIXME: restoreState attribute not found

        splitter_state = self.settings.value("LYTEditorWidget/mainSplitterState")
        if splitter_state:
            self.main_splitter.restoreState(splitter_state)

        self.restore_right_panel_layout(json.loads(self.settings.value("LYTEditorWidget/rightPanelLayout", "{}")))

    def closeEvent(self, event: QCloseEvent):
        self.save_layout_state()
        self.settings.setValue("LYTEditorWidget/toolbarState", self.main_toolbar.saveState())
        super().closeEvent(event)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+A"), self, self.lyt_editor.add_room)
        QShortcut(QKeySequence("Ctrl+R"), self, self.lyt_editor.resize_room)
        QShortcut(QKeySequence("Ctrl+T"), self, self.lyt_editor.rotate_room)
        QShortcut(QKeySequence("Ctrl+C"), self, self.connect_rooms)
        QShortcut(QKeySequence("Ctrl+G"), self, self.generate_walkmesh)
        QShortcut(QKeySequence("Ctrl+E"), self, self.edit_walkmesh)
        QShortcut(QKeySequence("Ctrl+I"), self, self.import_texture)
        QShortcut(QKeySequence("Ctrl+M"), self, self.manage_textures)
        QShortcut(QKeySequence("Ctrl++"), self, self.zoom_pan_widget.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self.zoom_pan_widget.zoom_out)

        # Add keyboard navigation
        QShortcut(QKeySequence("Tab"), self, self.focusNextChild)
        QShortcut(QKeySequence("Shift+Tab"), self, self.focusPreviousChild)
        QShortcut(QKeySequence("Space"), self, self.activate_focused_widget)
        QShortcut(QKeySequence("Ctrl+F"), self, self.show_search_dialog)
        QShortcut(QKeySequence("Ctrl+W"), self, self.toggle_walkmesh_visibility)
        QShortcut(QKeySequence("Ctrl+B"), self, self.open_texture_browser)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_lyt)
        QShortcut(QKeySequence("Ctrl+F"), self, self.show_search_dialog)
        QShortcut(QKeySequence("Ctrl+Z"), self, self.undo_stack.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self.undo_stack.redo)
        QShortcut(QKeySequence("Ctrl+Shift+R"), self, self.reset_layout)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self.save_custom_layout)
        QShortcut(QKeySequence("Ctrl+D"), self, self.duplicate_selected_room)
        QShortcut(QKeySequence("Ctrl+Shift+F"), self, self.toggle_fullscreen)
        QShortcut(QKeySequence("Ctrl+H"), self, self.toggle_help_overlay)
        QShortcut(QKeySequence("Ctrl+/"), self, self.show_context_help)
        QShortcut(QKeySequence("F1"), self, self.show_help_overlay)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.quick_search)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self.zoom_pan_widget.reset_zoom_pan)
        QShortcut(QKeySequence("Ctrl+L"), self, self.toggle_layer_visibility)
        QShortcut(QKeySequence("Esc"), self, self.cancel_current_operation)

    def activate_focused_widget(self):
        focused_widget = self.focusWidget()
        if isinstance(focused_widget, QAction):
            focused_widget.trigger()

    def contextMenuEvent(self, event: QContextMenuEvent):
        context_menu = QMenu(self)

        room_submenu: _QMenu | None = context_menu.addMenu("Room Actions")  # pyright: ignore[reportAssignmentType]
        room_submenu.addAction("Add Room", self.lyt_editor.add_room)  # pyright: ignore[reportOptionalMemberAccess]
        room_submenu.addAction("Resize Room", self.lyt_editor.resize_room)  # pyright: ignore[reportOptionalMemberAccess]
        room_submenu.addAction("Rotate Room", self.lyt_editor.rotate_room)  # pyright: ignore[reportOptionalMemberAccess]
        room_submenu.addAction("Connect Rooms", self.connect_rooms)  # pyright: ignore[reportOptionalMemberAccess]

        walkmesh_submenu: _QMenu | None = context_menu.addMenu("Walkmesh Actions")  # pyright: ignore[reportAssignmentType]
        walkmesh_submenu.addAction("Generate Walkmesh", self.generate_walkmesh)  # pyright: ignore[reportOptionalMemberAccess]
        walkmesh_submenu.addAction("Edit Walkmesh", self.edit_walkmesh)  # pyright: ignore[reportOptionalMemberAccess]

        texture_submenu: _QMenu | None = context_menu.addMenu("Texture Actions")  # pyright: ignore[reportAssignmentType]
        texture_submenu.addAction("Import Texture", self.import_texture)  # pyright: ignore[reportOptionalMemberAccess]
        texture_submenu.addAction("Manage Textures", self.manage_textures)  # pyright: ignore[reportOptionalMemberAccess]

        context_menu.addSeparator()
        context_menu.addAction("Undo", self.undo_stack.undo)
        context_menu.addAction("Redo", self.undo_stack.redo)
        context_menu.addAction("Save LYT", self.save_lyt)
        context_menu.addAction("Search", self.show_search_dialog)
        context_menu.addAction("Reset Layout", self.reset_layout)
        context_menu.addAction("Toggle Fullscreen", self.toggle_fullscreen)
        context_menu.addAction("Toggle Help Overlay", self.toggle_help_overlay)
        context_menu.addAction("Show Context Help", self.show_context_help)
        context_menu.addAction("Quick Search", self.quick_search)
        context_menu.addAction("Toggle Layer Visibility", self.toggle_layer_visibility)
        context_menu.addAction("Cancel Current Operation", self.cancel_current_operation)

        context_menu.exec(self.mapToGlobal(event.pos()))

    def set_lyt(self, lyt: LYT) -> None:
        """Set the LYT data and update all editors."""
        self.lyt_editor.set_lyt(lyt)
        self.walkmesh_editor.set_lyt(lyt)
        self.module_renderer.set_lyt(lyt)
        self.update_scene()

    def get_lyt_path(self) -> str:
        """Get the path to the current LYT file."""
        return self._lyt_path if hasattr(self, "_lyt_path") else ""

    def save_state(self) -> QByteArray:
        """Save the editor state."""
        state = QByteArray()
        state.append(self.lyt_editor.saveState())
        state.append(self.walkmesh_editor.saveState())
        return state

    def restore_state(self, state: QByteArray) -> None:
        """Restore the editor state."""
        if state:
            self.lyt_editor.restoreState(state)
            self.walkmesh_editor.restoreState(state)

    def set_current_tool(self, tool: str) -> None:
        """Set the current editing tool."""
        self.lyt_editor.set_current_tool(tool)
        self.update_scene()

    def update_scene(self) -> None:
        """Update all editor views."""
        self.lyt_editor.update_preview()
        self.walkmesh_editor.update_preview()
        self.module_renderer.update_preview()

    def toggle_walkmesh_visibility(self) -> None:
        """Toggle walkmesh visibility."""
        self.walkmesh_editor.toggle_visibility()

    def manage_textures(self) -> None:
        """Open texture management dialog."""
        self.texture_browser.manage_textures()

    def auto_connect_rooms(self) -> None:
        """Automatically connect rooms based on proximity."""
        self.lyt_editor.auto_connect_rooms()
        self.update_scene()

    def get_selected_room(self) -> Optional[LYTRoom]:
        """Get the currently selected room."""
        return self.lyt_editor.get_selected_room()

    def get_selected_texture(self) -> Optional[str]:
        """Get the currently selected texture."""
        return self.texture_browser.get_selected_texture()

    def get_selected_item(self) -> Optional[Any]:
        """Get the currently selected item."""
        return self.lyt_editor.get_selected_item()

    def clear_highlights(self) -> None:
        """Clear all highlights."""
        self.lyt_editor.clear_highlights()

    def highlight_room(self, room: LYTRoom) -> None:
        """Highlight a room."""
        self.lyt_editor.highlight_room(room)

    def highlight_texture(self, texture: str) -> None:
        """Highlight a texture."""
        self.texture_browser.highlight_texture(texture)

    def select_room(self, room: LYTRoom) -> None:
        """Select a room."""
        self.lyt_editor.select_room(room)

    def select_texture(self, texture: str) -> None:
        """Select a texture."""
        self.texture_browser.select_texture(texture)

    def get_textures(self) -> list[str]:
        """Get list of available textures."""
        return self.texture_browser.get_textures()

    def add_texture(self, texture: str) -> None:
        """Add a new texture."""
        self.texture_browser.add_texture(texture)

    def remove_texture(self, texture: str) -> None:
        """Remove a texture."""
        self.texture_browser.remove_texture(texture)

    def import_texture(self, path: str) -> None:
        """Import a texture from file."""
        self.texture_browser.import_texture(path)

    def serialize(self) -> bytes:
        """Serialize the LYT data."""
        return self.lyt_editor.get_lyt().serialize()

    def deserialize(self, data: bytes) -> None:
        """Deserialize LYT data."""
        lyt = LYT.deserialize(data)
        self.set_lyt(lyt)

    def submit_task(self, task: Callable[..., Any], *args: Any, **kwargs: Any) -> concurrent.futures.Future:
        self.task_queue.append((task, args, kwargs))
        QTimer.singleShot(0, self._process_task_queue)
        future = concurrent.futures.Future()
        return future

    def _process_task_queue(self):
        if not self.task_queue:
            return

        current_time = time.time()
        if current_time - self.last_action_time < 0.1:
            QTimer.singleShot(100, self._process_task_queue)
            return

        task, args, kwargs = self.task_queue.pop(0)
        self.active_tasks += 1
        self.update_status_bar()
        self.last_action_time = current_time
        RobustLogger().debug(f"Submitting task: {task.__name__}")
        self.process_pool.submit(self._task_wrapper, task, *args, **kwargs)

    def _delayed_submit_task(
        self,
        future: concurrent.futures.Future[tuple[Callable[..., Any], Any]],
        task: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ):
        try:
            result: concurrent.futures.Future[tuple[Callable[..., Any], Any]] = self.submit_task(task, *args, **kwargs)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)

    def _task_wrapper(
        self,
        task: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        result = task(*args, **kwargs)
        from typing import NamedTuple

        ft = NamedTuple("TaskResult", [("success", bool), ("data", object)])  # noqa: UP014
        return ft(success=True, data=result)

    def on_task_completed(
        self,
        future: concurrent.futures.Future[tuple[Callable[..., Any], Any]],
    ):
        try:
            task, result = future.result()
            if isinstance(result, functools.partial):
                if result.success:  # FIXME: success attribute not found
                    self.sig_lyt_updated.emit(self.get_lyt())
                elif result.error:  # FIXME: error attribute not found
                    self.show_error_message(str(result.error))
            RobustLogger().info(f"Task {task.__name__} completed successfully")
        except Exception as e:  # noqa: BLE001
            self.on_task_exception(task, e)
        finally:
            self.active_tasks -= 1
            self.update_status_bar()
            RobustLogger().debug(f"Completed task: {task.__name__}")

    def connect_rooms(self):
        future: concurrent.futures.Future[tuple[Callable[..., Any], Any]] = self.submit_task(self._connect_rooms)
        future.add_done_callback(self.on_connect_rooms_completed)

    def generate_walkmesh(self):
        if self.current_lyt:
            future: concurrent.futures.Future[tuple[Callable[..., Any], Any]] = self.submit_task(self.walkmesh_editor.generate_walkmesh, self.current_lyt)
            future.add_done_callback(self.on_walkmesh_generated)
        else:
            QMessageBox.warning(self, "Generate Walkmesh", "No LYT loaded. Please load or create a LYT first.")

    def edit_walkmesh(self):
        self.walkmesh_editor.edit_walkmesh()  # FIXME: edit_walkmesh attribute not found

    def import_texture(self):
        self.undo_stack.push(ImportTextureCommand(self.texture_browser))

    def manage_textures(self):
        self.texture_browser.manage_textures()  # FIXME: manage_textures attribute not found

    def _connect_rooms(self) -> tuple[Any, Any]:
        old_state = self.lyt_editor.get_lyt().serialize()  # FIXME: get_lyt attribute not found
        self.lyt_editor.auto_connect_rooms()  # FIXME: auto_connect_rooms attribute not found
        new_state = self.lyt_editor.get_lyt().serialize()  # FIXME: get_lyt attribute not found
        return old_state, new_state

    def on_connect_rooms_completed(
        self,
        future: concurrent.futures.Future[tuple[Any, Any]],
    ):
        try:
            old_state, new_state = future.result()
            self.undo_stack.push(ConnectRoomsCommand(self.lyt_editor, old_state, new_state))
        except Exception as e:  # noqa: BLE001
            self.show_error_message(f"Error connecting rooms: {e}")

    def dragEnterEvent(self, event: QDragEnterEvent):
        mime_data: QMimeData | None = event.mimeData()
        if mime_data is not None and (mime_data.hasUrls() or mime_data.hasText() or mime_data.hasFormat("application/x-qabstractitemmodeldatalist")):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        mime_data: QMimeData | None = event.mimeData()
        if mime_data is not None and (mime_data.hasUrls() or mime_data.hasText() or mime_data.hasFormat("application/x-qabstractitemmodeldatalist")):
            event.acceptProposedAction()
        if mime_data is not None and mime_data.hasUrls():
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_ext = os.path.splitext(file_path)[1].lower()  # noqa: PTH122
                    if file_ext in (".tga", ".dds", ".jpg", ".png"):
                        self.import_texture(file_path, event.pos())
                    elif file_ext == ".lyt":
                        self.import_lyt(file_path)
                    else:
                        self.show_error_message(f"Unsupported file type: {file_path}")
        elif mime_data is not None and mime_data.hasText():
            # Assume it's a room template or other LYT component
            component_data = mime_data.text()
            self.add_lyt_component(component_data, event.pos())  # FIXME: add_lyt_component attribute not found
        elif mime_data is not None and mime_data.hasFormat("application/x-qabstractitemmodeldatalist"):
            # Handle drag and drop from texture browser
            model: QAbstractItemModel | None = cast(QModelIndex, event.source()).model()  # pyright: ignore[reportAssignmentType]
            index: QModelIndex | None = event.source().currentIndex()  # FIXME: currentIndex attribute not found
            if index is not None:
                texture_name = model.data(index, Qt.ItemDataRole.DisplayRole)
                self.apply_texture_to_selected_room(texture_name, event.pos())

    def dragMoveEvent(self, event: QDragMoveEvent):
        mime_data: QMimeData | None = event.mimeData()
        if mime_data is not None and (mime_data.hasUrls() or mime_data.hasText() or mime_data.hasFormat("application/x-qabstractitemmodeldatalist")):
            event.acceptProposedAction()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        event.accept()

    def import_lyt(self, file_path: str):
        # Implement LYT import logic here
        self.show_info_message(f"Importing LYT file: {file_path}")
        # Add actual import logic

    def apply_texture_to_selected_room(self, texture_name: str):
        # Implement logic to apply the texture to the selected room
        ...

    def on_walkmesh_generated(self, future: concurrent.futures.Future):
        try:
            walkmesh: BWM | None = future.result()
            if walkmesh is not None and isinstance(walkmesh, BWM):
                self.walkmesh_editor.set_walkmesh(walkmesh)
                self.sig_walkmesh_updated.emit(walkmesh)
                self.show_info_message("Walkmesh generated successfully")
            else:
                self.show_error_message("Unexpected result from walkmesh generation")
        except Exception as e:
            self.show_error_message(f"Error generating walkmesh: {e!s}")
        finally:
            self.active_tasks -= 1
            self.update_status_bar()

    def on_task_exception(
        self,
        task: Callable[..., Any],
        error: Exception,
    ):
        self.show_error_message(str(error))
        RobustLogger().error(f"Task exception in {task.__name__}: {error!s}")

    def update_status_bar(self):
        lyt: LYT | None = self.get_lyt()
        selected_room = self.lyt_editor.get_selected_room()  # FIXME: get_selected_room attribute not found
        selected_texture = self.texture_browser.get_selected_texture()  # FIXME: get_selected_texture attribute not found
        room_info = f"Selected Room: {selected_room.name if selected_room else 'None'}" if selected_room else ""
        walkmesh_info: Literal["Walkmesh visible", "Walkmesh hidden"] = "Walkmesh visible" if self.walkmesh_editor.isVisible() else "Walkmesh hidden"
        search_info = f"Search results: {len(self.search_results)}" if self.search_results else ""
        status_message = f"Active tasks: {self.active_tasks} | Rooms: {len(lyt.rooms) if lyt else 0} | Zoom: {self.zoom_pan_widget.zoom_factor:.2f}x | {room_info} | Selected Texture: {selected_texture if selected_texture else 'None'} | {walkmesh_info} | {search_info}"
        self.status_bar.showMessage(status_message)

    def show_error_message(
        self,
        message: str,
    ):
        self.error_dialog.showMessage(f"An error occurred: {message}\n\nPlease check the log for more details.")
        self.error_dialog.show()
        RobustLogger().error(f"Error: {message}")

    def show_info_message(self, message: str):
        info_box = QMessageBox(self)
        info_box.setIcon(QMessageBox.Icon.Information)
        info_box.setText(message)
        info_box.setWindowTitle("Information")
        info_box.exec()
        RobustLogger().info(message)

    def update_palette(self, palette: QPalette):
        self.setPalette(palette)
        self.lyt_editor.setPalette(palette)
        self.texture_browser.setPalette(palette)
        self.walkmesh_editor.setPalette(palette)
        self.zoom_pan_widget.setPalette(palette)

    def update_style_sheet(self, stylesheet: str):
        self.setStyleSheet(stylesheet)
        self.lyt_editor.setStyleSheet(stylesheet)
        self.texture_browser.setStyleSheet(stylesheet)
        self.walkmesh_editor.setStyleSheet(stylesheet)
        self.zoom_pan_widget.setStyleSheet(stylesheet)

    def setup_zoom_pan_widget(self):
        self.zoom_pan_widget.setParent(self.lyt_editor)
        self.zoom_pan_widget.resize(100, 100)
        self.zoom_pan_widget.move(10, 10)
        self.zoom_pan_widget.lower()
        self.zoom_pan_widget.show()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText("LYT Component")
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected_item()
        elif event.key() == Qt.Key.Key_F2:
            self.rename_selected_item()
        super().keyPressEvent(event)

    def delete_selected_item(self):
        selected_item = self.lyt_editor.get_selected_item()  # FIXME: get_selected_item attribute not found
        if selected_item:
            self.undo_stack.push(DeleteItemCommand(self.lyt_editor, selected_item))

    def rename_selected_item(self):
        selected_item = self.lyt_editor.get_selected_item()  # FIXME: get_selected_item attribute not found
        if selected_item:
            self.undo_stack.push(RenameItemCommand(self.lyt_editor, selected_item))

    def show_search_dialog(self):
        search_text, ok = QInputDialog.getText(self, "Search", "Enter search term:")
        if ok and search_text:
            self.perform_search(search_text)

    def perform_search(self, search_text: str):
        future = self.submit_task(self._perform_search, search_text)
        future.add_done_callback(lambda f: self.update_search_results(f.result()))
        self.update_status_bar()

    def _perform_search(self, search_text: str) -> list[tuple[str, str]]:
        results: list[tuple[str, str]] = []
        lyt = self.get_lyt()
        if lyt:
            results.extend(("Room", room.model) for room in lyt.rooms if search_text.lower() in room.model.lower())
            results.extend(("Texture", texture) for texture in self.texture_browser.get_textures() if search_text.lower() in texture.lower())  # FIXME: get_textures attribute not found
            results.extend(("Track", track.model) for track in lyt.tracks if search_text.lower() in track.model.lower())
            results.extend(("Obstacle", obstacle.model) for obstacle in lyt.obstacles if search_text.lower() in obstacle.model.lower())
        return results

    def update_search_results(self, results: list[tuple[str, str]]):
        """Updates the search results displayed in the layout editor widget.

        This method processes the provided results, showing them if available, or displaying an informational message if no results are found.
        """
        self.search_results = results
        if self.search_results:
            self.show_search_results(self.search_results)
        else:
            self.show_info_message("No results found")
        self.highlight_search_results(results)
        self.update_status_bar()

    def focusInEvent(self, event: QFocusEvent):
        super().focusInEvent(event)
        cast(QApplication, QApplication.instance()).focusChanged.connect(self.on_focus_changed)

    def on_focus_changed(self, old: QWidget, new: QWidget):
        if new and new.parent() == self:
            self.update_status_bar()

    def toggle_walkmesh_visibility(self):
        self.walkmesh_editor.toggle_visibility()  # FIXME: toggleVisibility attribute not found
        self.update_status_bar()

    def open_texture_browser(self):
        self.texture_browser.show()

    def save_lyt(self):
        lyt: LYT | None = self.get_lyt()
        if lyt:
            try:
                write_lyt(lyt, self.get_lyt_path())  # FIXME: get_lyt_path attribute not found
                self.show_info_message("LYT saved successfully")
                RobustLogger().info("LYT saved successfully")
            except Exception as e:  # noqa: BLE001
                self.show_error_message(f"Error saving LYT: {e!s}")
                RobustLogger().error(f"Error saving LYT: {e!s}")

    def show_search_results(self, results: list[tuple[str, str]]):
        result_dialog = QDialog(self)
        result_dialog.setWindowTitle("Search Results")
        layout = QVBoxLayout(result_dialog)
        for result_type, result_name in results:
            result_label = QLabel(f"{result_type}: {result_name}")
            result_label.mousePressEvent = functools.partial(self.goto_search_result, result_type, result_name)
            result_label.setCursor(Qt.CursorShape.PointingHandCursor)
            result_label.setToolTip("Click to go to this item")
            layout.addWidget(result_label)
        layout.addWidget(QPushButton("Close", clicked=result_dialog.accept))
        result_dialog.setModal(False)
        result_dialog.exec()

    def reset_layout(self):
        self.main_splitter.setSizes([int(self.width() * 0.7), int(self.width() * 0.3)])
        self.texture_dock.show()
        self.walkmesh_dock.show()
        self.show_info_message("Layout has been reset to default")

    def save_custom_layout(self):
        self.layout_config = {
            "main_splitter": self.main_splitter.saveState().data(),
            "texture_dock": {"visible": self.texture_dock.isVisible(), "geometry": self.texture_dock.saveGeometry().data()},
            "walkmesh_dock": {"visible": self.walkmesh_dock.isVisible(), "geometry": self.walkmesh_dock.saveGeometry().data()},
        }
        self.settings.setValue("LYTEditorWidget/customLayout", json.dumps(self.layout_config))
        self.show_info_message("Custom layout has been saved")

    def restore_right_panel_layout(self, layout_data: dict):
        if "texture_dock" in layout_data:
            self.texture_dock.setVisible(layout_data["texture_dock"]["visible"])
            self.texture_dock.restoreGeometry(QByteArray.fromHex(layout_data["texture_dock"]["geometry"].encode()))
        if "walkmesh_dock" in layout_data:
            self.walkmesh_dock.setVisible(layout_data["walkmesh_dock"]["visible"])
            self.walkmesh_dock.restoreGeometry(QByteArray.fromHex(layout_data["walkmesh_dock"]["geometry"].encode()))

    def duplicate_selected_room(self):
        selected_room = self.lyt_editor.get_selected_room()  # FIXME: get_selected_room attribute not found
        if selected_room:
            self.undo_stack.push(DuplicateRoomCommand(self.lyt_editor, selected_room))

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def highlight_search_results(self, results: list[tuple[str, str]]):
        self.lyt_editor.clear_highlights()  # FIXME: clear_highlights attribute not found
        for result_type, result_name in results:
            if result_type == "Room":
                self.lyt_editor.highlight_room(result_name)  # FIXME: highlight_room attribute not found
            elif result_type == "Texture":
                self.texture_browser.highlight_texture(result_name)  # FIXME: highlight_texture attribute not found

    def goto_search_result(self, result_type: str, result_name: str, event: QMouseEvent):
        if result_type == "Room":
            self.lyt_editor.select_room(result_name)  # FIXME: select_room attribute not found
        elif result_type == "Texture":
            self.texture_browser.select_texture(result_name)  # FIXME: select_texture attribute not found

    def toggle_help_overlay(self):
        if hasattr(self, "help_overlay") and self.help_overlay.isVisible():
            self.help_overlay.hide()
        else:
            self.show_help_overlay()

    def show_help_overlay(self):
        from toolset.gui.widgets.help_overlay import HelpOverlay

        self.help_overlay = HelpOverlay(self)  # FIXME: HelpOverlay attribute not found
        self.help_overlay.addSection("Keyboard Shortcuts", self.get_keyboard_shortcuts_help())
        self.help_overlay.addSection("Mouse Controls", self.get_mouse_controls_help())
        self.help_overlay.addSection("General Tips", self.get_general_tips_help())
        self.help_overlay.show()

    def get_keyboard_shortcuts_help(self):
        return """
        Ctrl+A: Add Room
        Ctrl+R: Resize Room
        Ctrl+T: Rotate Room
        Ctrl+C: Connect Rooms
        Ctrl+G: Generate Walkmesh
        Ctrl+E: Edit Walkmesh
        Ctrl+I: Import Texture
        Ctrl+M: Manage Textures
        Ctrl++: Zoom In
        Ctrl+-: Zoom Out
        Ctrl+Z: Undo
        Ctrl+Y: Redo
        Ctrl+S: Save LYT
        Ctrl+F: Search
        Ctrl+W: Toggle Walkmesh Visibility
        Ctrl+B: Open Texture Browser
        Ctrl+D: Duplicate Selected Room
        Ctrl+Shift+F: Toggle Fullscreen
        Ctrl+H or F1: Toggle Help Overlay
        Ctrl+/: Show Context Help
        """

    def get_mouse_controls_help(self):
        return """
        Left Click: Select item
        Right Click: Open context menu
        Middle Click + Drag: Pan view
        Scroll Wheel: Zoom in/out
        Drag and Drop: Move items or import textures
        """

    def get_general_tips_help(self):
        return """
        - Use the search function (Ctrl+F) to quickly find rooms or textures
        - Customize your layout and save it for future use
        - Right-click on items for additional options
        - Use the Undo/Redo functions to revert or repeat actions
        - Press F1 or Ctrl+H at any time to show this help overlay
        """

    def show_context_help(self):
        focused_widget: QWidget | None = QApplication.focusWidget()
        if focused_widget is None:
            return
        QWhatsThis.enterWhatsThisMode()
        QWhatsThis.showText(focused_widget.mapToGlobal(QPoint(0, 0)), focused_widget.whatsThis(), focused_widget)

    def quick_search(self):
        search_text, ok = QInputDialog.getText(self, "Quick Search", "Enter search term:")
        if ok and search_text:
            future: Future[list[tuple[str, str]]] = self.submit_task(self.perform_quick_search, search_text)
            future.add_done_callback(lambda f: self.on_quick_search_completed(f.result()))

    def perform_quick_search(self, search_text: str) -> list[tuple[str, str]]:
        results: list[tuple[str, str]] = []
        lyt = self.get_lyt()
        if lyt:
            results.extend(("Room", room.model) for room in lyt.rooms if search_text.lower() in room.model.lower())
            results.extend(("Texture", texture) for texture in self.texture_browser.get_textures() if search_text.lower() in texture.lower())  # FIXME: get_textures attribute not found
            results.extend(("Track", track.model) for track in lyt.tracks if search_text.lower() in track.model.lower())
            results.extend(("Obstacle", obstacle.model) for obstacle in lyt.obstacles if search_text.lower() in obstacle.model.lower())
        return results

    def on_quick_search_completed(self, results: list[tuple[str, str]]):
        if results:
            self.show_quick_search_results(results)
        else:
            self.show_info_message("No results found")

    def show_quick_search_results(self, results: list[tuple[str, str]]):
        result_dialog = QDialog(self)
        result_dialog.setWindowTitle("Quick Search Results")
        layout = QVBoxLayout(result_dialog)
        for result_type, result_name in results:
            result_label = QLabel(f"{result_type}: {result_name}")
            result_label.mousePressEvent = functools.partial(self.goto_search_result, result_type, result_name)
            result_label.setCursor(Qt.CursorShape.PointingHandCursor)
            result_label.setToolTip("Click to go to this item")
            layout.addWidget(result_label)
        layout.addWidget(QPushButton("Close", clicked=result_dialog.accept))
        result_dialog.setModal(False)
        result_dialog.exec()

    def toggle_layer_visibility(self):
        self.lyt_editor.toggle_layer_visibility()  # FIXME: toggle_layer_visibility attribute not found
        self.update_status_bar()

    def cancel_current_operation(self):
        self.lyt_editor.cancel_current_operation()  # FIXME: cancelCurrentOperation attribute not found
        self.current_tool = "select"
        self.tool_group.actions()[0].setChecked(True)  # FIXME: tool_group attribute not found

    def on_zoom_slider_value_changed(self, value: int):
        self.zoom_pan_widget.set_zoom_factor(value / 100)

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        self.restore_layout_state()
        self.update_status_bar()

    def schedule_preview_update(self):
        self.preview_timer.start(100)  # 100ms debounce

    def update_realtime_preview(self):
        # Update the preview based on the current LYT state
        self.lyt_editor.update_preview()  # FIXME: update_preview attribute not found
        self.walkmesh_editor.update_preview()  # FIXME: update_preview attribute not found

    def setup_lyt_tools(self):
        self.lyt_toolbar = QToolBar("LYT Tools")
        self.addToolBar(self.lyt_toolbar)  # FIXME: addToolBar attribute not found

        self.add_room_action = QAction("Add Room", self)
        self.add_room_action.triggered.connect(self.add_room)
        self.lyt_toolbar.addAction(self.add_room_action)

        self.edit_room_action = QAction("Edit Room", self)
        self.edit_room_action.triggered.connect(self.editRoom)
        self.lyt_toolbar.addAction(self.edit_room_action)

        self.add_track_action = QAction("Add Track", self)
        self.add_track_action.triggered.connect(self.add_track)
        self.lyt_toolbar.addAction(self.add_track_action)

        self.add_obstacle_action = QAction("Add Obstacle", self)
        self.add_obstacle_action.triggered.connect(self.add_obstacle)
        self.lyt_toolbar.addAction(self.add_obstacle_action)

        self.add_doorhook_action = QAction("Add Doorhook", self)
        self.add_doorhook_action.triggered.connect(self.add_door_hook)
        self.lyt_toolbar.addAction(self.add_doorhook_action)

    def add_room(self):
        room = LYTRoom()
        room.position = Vector3(0, 0, 0)  # Default position
        room.size = Vector3(10, 10, 3)  # Default size
        self.current_lyt.rooms.append(room)
        self.selected_room = room
        self.update_lyt_preview()

    def editRoom(self):
        if self.selected_room:
            # Open a dialog to edit room properties
            dialog = RoomPropertiesDialog(self.selected_room, self)  # FIXME: RoomPropertiesDialog needs to be created
            if dialog.exec():
                self.update_lyt_preview()

    def add_track(self):
        if self.selected_room:
            track = LYTTrack()
            track.start_room = self.selected_room
            # Open a dialog to select end room and set other properties
            dialog = TrackPropertiesDialog(self.current_lyt.rooms, track, self)  # FIXME: TrackPropertiesDialog needs to be created
            if dialog.exec():
                self.current_lyt.tracks.append(track)
                self.update_lyt_preview()

    def add_obstacle(self):
        obstacle = LYTObstacle()
        # Open a dialog to set obstacle properties
        dialog = ObstaclePropertiesDialog(obstacle, self)  # FIXME: ObstaclePropertiesDialog needs to be created
        if dialog.exec():
            self.current_lyt.obstacles.append(obstacle)
            self.update_lyt_preview()

    def add_door_hook(self):
        if self.selected_room:
            doorhook = LYTDoorHook()
            doorhook.room = self.selected_room
            # Open a dialog to set doorhook properties
            dialog = DoorHookPropertiesDialog(doorhook, self)  # FIXME: DoorHookPropertiesDialog needs to be created
            if dialog.exec():
                self.current_lyt.doorhooks.append(doorhook)
                self.update_lyt_preview()

    def update_lyt_preview(self):
        if self.current_lyt:
            self.lyt_editor.set_lyt(self.current_lyt)
            self.sig_lyt_updated.emit(self.current_lyt)
            self.parent_ref.scene.set_lyt(self.current_lyt)
            self.walkmesh_editor.set_lyt(self.current_lyt)

    def import_custom_texture(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Texture", "", "Image Files (*.png *.jpg *.bmp)")
        if file_path:
            texture_name = os.path.basename(file_path)  # noqa: PTH119
            self.custom_textures[texture_name] = QPixmap(file_path)
            self.texture_browser.add_texture(texture_name, self.custom_textures[texture_name])  # FIXME: addTexture attribute not found

    def load_current_lyt(self):
        if self.parent_ref.module:
            lyt_resource = self.parent_ref.module.layout()
            if lyt_resource:
                self.current_lyt = lyt_resource.resource()
            if not self.current_lyt:
                self.current_lyt = LYT()
                # Generate a basic layout based on the module's area
                self.current_lyt.rooms.append(LYTRoom())
                self.current_lyt.rooms[0].position = Vector3(0, 0, 0)
                self.current_lyt.rooms[0].model = "default_room"
        self.update_lyt_preview()

    def save_lyt(self):
        if self.current_lyt and self.parent_ref.module:
            lyt_resource = self.parent_ref.module.layout()
            if lyt_resource:
                lyt_resource.save(self.current_lyt)
                QMessageBox.information(self, "LYT Saved", "The layout has been saved successfully.")
            else:
                QMessageBox.warning(self, "Save Failed", "Unable to save LYT: No layout resource found in the module.")
        else:
            QMessageBox.warning(self, "Save Failed", "No current LYT or module available.")

    def edit_room_properties(self, room: LYTRoom) -> None:
        dialog = RoomPropertiesDialog(room, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_scene()

    def edit_track_properties(self, track: LYTTrack) -> None:
        dialog = TrackPropertiesDialog(track, self._lyt.rooms, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_scene()

    def edit_obstacle_properties(self, obstacle: LYTObstacle) -> None:
        dialog = ObstaclePropertiesDialog(obstacle, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_scene()

    def edit_doorhook_properties(self, doorhook: LYTDoorHook) -> None:
        dialog = DoorHookPropertiesDialog(doorhook, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_scene()


class ConnectRoomsCommand(QUndoCommand):
    def __init__(self, lyt_editor: LYTEditor, old_state: str, new_state: str):
        super().__init__("Connect Rooms")
        self.lyt_editor: LYTEditor = lyt_editor
        self.old_state: str = old_state
        self.new_state: str = new_state

    def redo(self):
        self.lyt_editor.get_lyt().deserialize(self.new_state)  # FIXME: deserialize attribute not found

    def undo(self):
        self.lyt_editor.get_lyt().deserialize(self.old_state)  # FIXME: deserialize attribute not found


class EditWalkmeshCommand(QUndoCommand):
    def __init__(
        self,
        walkmesh_editor: WalkmeshEditor,
    ):
        super().__init__("Edit Walkmesh")
        self.walkmesh_editor: WalkmeshEditor = walkmesh_editor
        self.old_state: str | None = None
        self.new_state: str | None = None

    def redo(self):
        self.old_state = self.walkmesh_editor.get_walkmesh().serialize()  # FIXME: get_walkmesh attribute not found
        self.walkmesh_editor.start_editing()  # FIXME: start_editing attribute not found
        self.new_state = self.walkmesh_editor.get_walkmesh().serialize()  # FIXME: get_walkmesh attribute not found

    def undo(self):
        self.walkmesh_editor.get_walkmesh().deserialize(self.old_state)  # FIXME: deserialize attribute not found


class ImportTextureCommand(QUndoCommand):
    def __init__(self, texture_browser: TextureBrowser, file_path: str | None = None):
        super().__init__("Import Texture")
        self.texture_browser: TextureBrowser = texture_browser
        self.imported_texture: QPixmap | None = None
        self.file_path: str | None = file_path

    def redo(self):
        self.imported_texture = self.texture_browser.import_texture()

    def undo(self):
        if self.imported_texture:
            self.texture_browser.remove_texture(self.imported_texture)  # FIXME: remove_texture attribute not found


class DeleteItemCommand(QUndoCommand):
    def __init__(self, lyt_editor: LYTEditor, item: Any):
        super().__init__("Delete Item")
        self.lyt_editor: LYTEditor = lyt_editor
        self.item: Any = item
        self.old_state: str | None = None

    def redo(self):
        self.old_state = self.lyt_editor.get_lyt().serialize()  # FIXME: serialize attribute not found
        self.lyt_editor.delete_item(self.item)  # FIXME: delete_item attribute not found

    def undo(self):
        self.lyt_editor.get_lyt().deserialize(self.old_state)  # FIXME: deserialize attribute not found


class RenameItemCommand(QUndoCommand):
    def __init__(
        self,
        lyt_editor: LYTEditor,
        item: Any,
    ):
        super().__init__("Rename Item")
        self.lyt_editor: LYTEditor = lyt_editor
        self.item: Any = item
        self.old_name: str = item.name
        self.new_name: str | None = None

    def redo(self):
        if not self.new_name:
            self.new_name, ok = QInputDialog.getText(None, "Rename Item", "Enter new name:", text=self.old_name)
            if not ok:
                return
        self.item.name = self.new_name

    def undo(self):
        self.item.name = self.old_name


class DuplicateRoomCommand(QUndoCommand):
    def __init__(
        self,
        lyt_editor: LYTEditor,
        room: Any,
    ):
        super().__init__("Duplicate Room")
        self.lyt_editor: LYTEditor = lyt_editor
        self.original_room: LYTRoom = room
        self.new_room: LYTRoom | None = None

    def redo(self):
        self.new_room = self.lyt_editor.duplicate_room(self.original_room)  # FIXME: duplicate_room attribute not found
        self.lyt_editor.select_room(self.new_room)  # FIXME: select_room attribute not found

    def undo(self):
        self.lyt_editor.delete_room(self.new_room)  # FIXME: delete_room attribute not found
        self.lyt_editor.select_room(self.original_room)  # FIXME: select_room attribute not found


class ZoomPanWidget(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.zoom_factor: float = 1.0
        self.pan_offset: QPoint = QPoint(0, 0)
        self.last_pan_pos: QPoint = QPoint()
        self.panning: bool = False
        self.setMouseTracking(True)

    def zoom_in(self):
        self.zoom_factor *= 1.2
        self.zoom_factor = min(self.zoom_factor, 5.0)  # Limit max zoom
        self.update()

    def zoom_out(self):
        self.zoom_factor /= 1.2
        self.zoom_factor = max(self.zoom_factor, 0.1)  # Limit min zoom
        self.update()

    def set_zoom_factor(self, factor: float):
        self.zoom_factor = max(min(factor, 5.0), 0.1)
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.last_pan_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.panning:
            delta = event.pos() - self.last_pan_pos
            self.pan_offset += delta
            self.last_pan_pos = event.pos()
            self.update()

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def eventFilter(
        self,
        obj: QObject,
        event: QEvent,
    ) -> bool:
        if event.type() == QEvent.Type.ToolTip and isinstance(obj, QWidget) and isinstance(event, QHelpEvent):
            help_text = obj.toolTip()
            if help_text:
                QToolTip.showText(event.globalPos(), help_text)
            else:
                QToolTip.hideText()
            return True
        return super().eventFilter(obj, event)

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        for child in self.findChildren(QWidget):
            child.installEventFilter(self)
        self.installEventFilter(self)

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self.palette().color(QPalette.ColorRole.Text))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"Zoom: {self.zoom_factor:.2f}x")
        if self.panning:
            painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight), "Panning")

    def reset_zoom_pan(self):
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)

from copy import deepcopy
from typing import TYPE_CHECKING

from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import QWidget

from pykotor.common.geometry import Vector3
from toolset.data.lyt_structures import (
    ExtendedLYT as LYT,
    ExtendedLYTDoorHook as LYTDoorHook,
    ExtendedLYTObstacle as LYTObstacle,
    ExtendedLYTRoom as LYTRoom,
    ExtendedLYTTrack as LYTTrack,
)

if TYPE_CHECKING:
    from qtpy.QtGui import QPaintEvent

class LYTEditorWidget(QWidget):
    """Widget for editing LYT (Layout) files."""

    # Signals
    sig_lyt_updated = Signal(LYT)
    sig_room_selected = Signal(LYTRoom)
    sig_track_selected = Signal(LYTTrack)
    sig_obstacle_selected = Signal(LYTObstacle)
    sig_doorhook_selected = Signal(LYTDoorHook)

    def __init__(self, parent: LYTEditor):
        super().__init__(parent)
        self._lyt: LYT | None = None
        self.selected_room: LYTRoom | None = None
        self.selected_track: LYTTrack | None = None
        self.selected_obstacle: LYTObstacle | None = None
        self.selected_doorhook: LYTDoorHook | None = None

        self._setup_ui()

    def _setup_ui(self):
        """Initialize the UI."""
        self.setMinimumSize(400, 300)

    def set_lyt(self, lyt: LYT):
        """Set the LYT data to edit."""
        self._lyt = deepcopy(lyt)
        self.update()

    def get_lyt(self) -> LYT | None:
        """Get the current LYT data."""
        return self._lyt

    def paintEvent(self, event: QPaintEvent):
        """Handle paint events."""
        if not self._lyt:
            return

        # TODO: Implement LYT rendering
        pass
