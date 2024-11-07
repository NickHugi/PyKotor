from __future__ import annotations

import json
import random
import re
import weakref

from collections import deque
from typing import TYPE_CHECKING, Any, Iterable, Optional, cast

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import QByteArray, QDataStream, QIODevice, QItemSelectionModel, QMimeData, QModelIndex, QPropertyAnimation, QRect, QTimer, Qt
from qtpy.QtGui import QDrag, QFont, QKeySequence, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QApplication,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QDockWidget,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWhatsThis,
    QWidget,
)

from pykotor.common.misc import Game, ResRef
from pykotor.extract.installation import SearchLocation
from pykotor.resource.generics.dlg import DLG, DLGComputerType, DLGConversationType, DLGEntry, DLGLink, DLGReply, read_dlg, write_dlg
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.dialog_animation import EditAnimationDialog
from toolset.gui.dialogs.edit.dialog_model import CutsceneModelDialog
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor
from toolset.gui.editors.dlg.constants import QT_STANDARD_ITEM_FORMAT, _DLG_MIME_DATA_ROLE, _LINK_PARENT_NODE_PATH_ROLE, _MODEL_INSTANCE_ID_ROLE
from toolset.gui.editors.dlg.list_widgets import DLGListWidget, DLGListWidgetItem
from toolset.gui.editors.dlg.model import DLGStandardItem, DLGStandardItemModel
from toolset.gui.editors.dlg.settings import DLGSettings
from toolset.gui.editors.dlg.tree_view import DLGTreeView
from toolset.gui.editors.dlg.widget_windows import ReferenceChooserDialog
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.ui_libraries.qt.adapters.itemmodels.filters import NoScrollEventFilter
from utility.ui_libraries.qt.widgets.itemviews.html_delegate import HTMLDelegate

if qtpy.API_NAME in ("PyQt6", "PySide6"):
    from qtpy.QtGui import QUndoStack
else:
    from qtpy.QtWidgets import QUndoStack  # type: ignore[assignment]


if TYPE_CHECKING:
    import os

    from pathlib import PureWindowsPath

    from qtpy.QtCore import QAbstractItemModel, QItemSelection, QModelIndex, QObject, QPoint
    from qtpy.QtGui import QClipboard, QCloseEvent, QFocusEvent, QKeyEvent, QMouseEvent, QShowEvent, QStandardItem
    from qtpy.QtWidgets import QScrollBar, QStatusBar
    from typing_extensions import Literal, Self  # pyright: ignore[reportMissingModuleSource]

    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.resource.generics.dlg import DLGAnimation, DLGNode, DLGStunt
    from toolset.uic.qtpy.editors.dlg import Ui_MainWindow


class DLGEditor(Editor):
    @property
    def editor(
        self,
    ) -> Self:
        return self

    @editor.setter
    def editor(
        self,
        value: Self,
    ): ...

    def __init__(
        self,
        parent: QWidget | None = None,
        installation: HTInstallation | None = None,
    ):
        """Initializes the Dialog Editor window."""
        supported: list[ResourceType] = [ResourceType.DLG]
        super().__init__(parent, "Dialog Editor", "dialog", supported, supported, installation)
        self._installation: HTInstallation

        from toolset.uic.qtpy.editors.dlg import Ui_MainWindow

        self._copy: DLGLink | None = None
        self._focused: bool = False
        self._node_loaded_into_ui: bool = True
        self.core_dlg: DLG = DLG()
        self.undo_stack: QUndoStack = QUndoStack()  # TODO(th3w1zard1): move _process_link and _remove_link_from_item logic to QUndoCommand classes once stable.  # noqa: TD003

        self.ui: Ui_MainWindow = Ui_MainWindow()
        self.ui.setupUi(self)
        self.original_tooltips: dict[QWidget, str] = {}
        self.search_results: list[DLGStandardItem] = []
        self.current_search_text: str = ""
        self.current_result_index: int = 0
        self.whats_this_toggle: bool = False

        # Status Bar
        self.status_bar_anim_timer: QTimer = QTimer(self)
        self.tip_label: QLabel = QLabel()
        font: QFont = self.tip_label.font()
        font.setPointSize(10)
        self.tip_label.setFont(font)
        self.tips_start_from_right_side: bool = True
        status_bar: QStatusBar | None = self.statusBar()
        assert status_bar is not None
        status_bar.addWidget(self.tip_label)
        self.vo_id_edit_timer: QTimer = QTimer(self)

        self.setup_dlg_tree_mvc()
        self.setup_extra_widgets()
        self._setup_signals()
        self._setup_menus()
        if installation:
            self._setup_installation(installation)

        self.dialog_references: ReferenceChooserDialog | None = None
        self.reference_history: list[tuple[list[weakref.ref[DLGLink]], str]] = []
        self.current_reference_index: int = -1

        self.keys_down: set[int] = set()
        self.no_scroll_event_filter: NoScrollEventFilter = NoScrollEventFilter(self)
        self.no_scroll_event_filter.setup_filter()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.tips: list[str] = [
            "Use the 'View' and 'Settings' menu to customize dlg editor settings. All of your changes will be saved for next time you load the editor.",
            "Tip: Drag and Drop is supported, even between different DLGs!",
            "Tip: Accidentally closed a side widget? Right click the Menu to reopen the dock panels.",
            "Tip: Hold CTRL and scroll to change the text size.",
            "Tip: Hold ALT and scroll to change the indentation.",
            "Tip: Hold CTRL+SHIFT and scroll to change the vertical spacing.",
            "Tip: 'Delete all references' will delete all EntriesList/RepliesList/StartingList links to the node, leaving it orphaned.",
            "Tip: Drag any item to the left dockpanel to pin it for easy access",
            "Tip: Orphaned Nodes will automatically be added to the top left list, drag back in to reintegrate.",
            "Tip: Use ':' after an attribute name in the search bar to filter items by specific properties, e.g., 'is_child:1'.",
            "Tip: Combine keywords with AND/OR in the search bar to refine your search results, such as 'script1:k_swg AND listener:PLAYER'",
            "Tip: Use double quotes to search for exact phrases in item descriptions, such as '\"urgent task\"'.",
            "Tip: Search for attributes without a value after ':' to find items where any non-null property exists, e.g., 'assigned:'.",
            "TIp: Double-click me to view all tips.",
        ]
        self.status_bar_anim_timer.start(30000)

        self.set_all_whats_this()
        self.setup_extra_tooltip_mode()
        self.new()

    def revert_tooltips(self):
        for widget, original_tooltip in self.original_tooltips.items():
            widget.setToolTip(original_tooltip)
        self.original_tooltips.clear()

    def showEvent(
        self,
        event: QShowEvent,
    ):
        super().showEvent(event)
        QTimer.singleShot(0, lambda *args: self.show_scrolling_tip())
        self.resize(self.width() + 200, self.height())
        self.resizeDocks(
            [
                self.ui.rightDockWidget,  # type: ignore[arg-type]
                self.left_dock_widget,
            ],
            [
                self.ui.rightDockWidget.minimumSizeHint().width(),
                self.left_dock_widget.minimumSizeHint().width(),
            ],
            Qt.Orientation.Horizontal,
        )
        self.resizeDocks(
            [
                self.ui.topDockWidget,  # type: ignore[arg-type]
            ],
            [
                self.ui.topDockWidget.minimumSizeHint().height(),
            ],
            Qt.Orientation.Vertical,
        )

    def show_scrolling_tip(self):
        tip: str = random.choice(self.tips)  # noqa: S311
        self.tip_label.setText(tip)
        self.tip_label.adjustSize()
        self.start_tooltip_ui_animation()

    def start_tooltip_ui_animation(self):
        status_bar: QStatusBar | None = self.statusBar()
        assert status_bar is not None
        if self.tips_start_from_right_side:
            start_x = -self.tip_label.width()
            end_x = status_bar.width()
        else:
            start_x = status_bar.width()
            end_x = -self.tip_label.width()

        self.tip_label.setGeometry(start_x, 0, self.tip_label.width(), 10)
        self.statusbar_animation = QPropertyAnimation(self.tip_label, b"geometry")
        self.statusbar_animation.setDuration(30000)
        self.statusbar_animation.setStartValue(QRect(start_x, 0, self.tip_label.width(), 10))
        self.statusbar_animation.setEndValue(QRect(end_x, 0, self.tip_label.width(), 10))
        if qtpy.API_NAME != "PySide6":  # disconnect() seems to have a different signature
            self.statusbar_animation.finished.connect(self.toggle_scrollbar_tip_direction)
        self.statusbar_animation.start()

    def toggle_scrollbar_tip_direction(self):
        self.tips_start_from_right_side = not self.tips_start_from_right_side
        self.statusbar_animation.disconnect()
        self.start_tooltip_ui_animation()

    def show_all_tips(
        self,
        checked: bool = False,  # noqa: FBT001, FBT002
    ):
        dialog: QDialog = QDialog(self)
        dialog.setWindowTitle("All Tips")
        layout: QVBoxLayout = QVBoxLayout(dialog)

        text_edit: QTextEdit = QTextEdit(dialog)
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Arial", 10))
        text_edit.setHtml("<ul>" + "".join(f"<li>{tip}</li>" for tip in self.tips) + "</ul>")
        layout.addWidget(text_edit)

        close_button: QPushButton = QPushButton("Close", dialog)
        close_button.clicked.connect(dialog.accept)
        close_button.setFont(QFont("Arial", 10))
        button_layout: QHBoxLayout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        fixed_width: int = 800  # Adjust this value as needed
        dialog.setFixedWidth(fixed_width)
        dialog.setSizeGripEnabled(True)
        dialog.exec()

    def setup_dlg_tree_mvc(self):
        self.model: DLGStandardItemModel = DLGStandardItemModel(self.ui.dialogTree)
        self.model.editor = self
        self.ui.dialogTree.editor = self
        self.ui.dialogTree.setModel(self.model)
        self.ui.dialogTree.setItemDelegate(HTMLDelegate(self.ui.dialogTree))
        self.verify_hierarchy(self.ui.dialogTree)
        self.verify_hierarchy(self.model)

    def verify_hierarchy(
        self,
        widget: QObject,
        level: int = 0,
    ):
        parent: QObject | None = widget
        while parent is not None:
            print(f"Level {level}: Checking parent {parent.__class__.__name__} with name {parent.objectName()}")
            if isinstance(parent, DLGEditor):
                return
            parent = parent.parent()
            level += 1
        raise RuntimeError(f"DLGEditor is not in the parent hierarchy, attempted {level} levels.")

    def _setup_signals(self):  # noqa: PLR0915
        """Connects UI signals to update node/link on change."""
        self.ui.actionReloadTree.triggered.connect(lambda: self._load_dlg(self.core_dlg))
        self.ui.dialogTree.expanded.connect(self.on_item_expanded)
        self.ui.dialogTree.customContextMenuRequested.connect(self.on_tree_context_menu)

        def on_double_click(*args, **kwargs):
            sel_model: QItemSelectionModel | None = self.ui.dialogTree.selectionModel()
            assert sel_model is not None
            self.edit_text(
                indexes=sel_model.selectedIndexes(),
                source_widget=self.ui.dialogTree,
            )

        self.ui.dialogTree.doubleClicked.connect(on_double_click)
        sel_model: QItemSelectionModel | None = self.ui.dialogTree.selectionModel()
        assert sel_model is not None
        sel_model.selectionChanged.connect(self.on_selection_changed)

        self.go_to_button.clicked.connect(self.handle_go_to)
        self.find_button.clicked.connect(self.handle_find)
        self.back_button.clicked.connect(self.handle_back)
        self.find_input.returnPressed.connect(self.handle_find)

        # Debounce timer to delay a cpu-intensive task.
        self.vo_id_edit_timer.setSingleShot(True)
        self.vo_id_edit_timer.setInterval(500)
        self.vo_id_edit_timer.timeout.connect(self.populate_combobox_on_void_edit_finished)

        self.tip_label.mouseDoubleClickEvent = self.show_all_tips  # pyright: ignore[reportAttributeAccessIssue]
        self.tip_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tip_label.customContextMenuRequested.connect(self.show_all_tips)
        self.status_bar_anim_timer.timeout.connect(self.show_scrolling_tip)

        script_text_entry_tooltip = """
A ResRef to a script, where the entry point is its <code>main()</code> function.
<br><br>
<i>Right-click for more options</i>
"""
        self.ui.script1Label.setToolTip(script_text_entry_tooltip)
        self.ui.script2Label.setToolTip(script_text_entry_tooltip)
        self.ui.script1ResrefEdit.setToolTip(script_text_entry_tooltip)
        self.ui.script2ResrefEdit.setToolTip(script_text_entry_tooltip)
        self.ui.script1ResrefEdit.currentTextChanged.connect(self.on_node_update)
        self.ui.script2ResrefEdit.currentTextChanged.connect(self.on_node_update)

        conditional_text_entry_tooltip = """
A ResRef to a script that defines the conditional function <code>int StartingConditional()</code>.
<br><br>
Should return 1 or 0, representing a boolean.
<br><br>
<i>Right-click for more options</i>
"""
        self.ui.conditional1Label.setToolTip(conditional_text_entry_tooltip)
        self.ui.conditional2Label.setToolTip(conditional_text_entry_tooltip)
        self.ui.condition1ResrefEdit.setToolTip(conditional_text_entry_tooltip)
        self.ui.condition2ResrefEdit.setToolTip(conditional_text_entry_tooltip)
        self.ui.condition1ResrefEdit.currentTextChanged.connect(self.on_node_update)
        self.ui.condition2ResrefEdit.currentTextChanged.connect(self.on_node_update)

        self.ui.soundComboBox.currentTextChanged.connect(self.on_node_update)
        self.ui.voiceComboBox.currentTextChanged.connect(self.on_node_update)

        self.ui.soundButton.clicked.connect(lambda: self.play_sound(self.ui.soundComboBox.currentText(), [SearchLocation.SOUND, SearchLocation.VOICE]) and None or None)
        self.ui.voiceButton.clicked.connect(lambda: self.play_sound(self.ui.voiceComboBox.currentText(), [SearchLocation.VOICE]) and None or None)

        self.ui.soundComboBox.set_button_delegate("Play", lambda text: self.play_sound(text, [SearchLocation.SOUND, SearchLocation.VOICE]))
        self.ui.voiceComboBox.set_button_delegate("Play", lambda text: self.play_sound(text, [SearchLocation.VOICE]))

        self.ui.speakerEdit.textEdited.connect(self.on_node_update)
        self.ui.listenerEdit.textEdited.connect(self.on_node_update)
        self.ui.script1Param1Spin.valueChanged.connect(self.on_node_update)
        self.ui.script1Param2Spin.valueChanged.connect(self.on_node_update)
        self.ui.script1Param3Spin.valueChanged.connect(self.on_node_update)
        self.ui.script1Param4Spin.valueChanged.connect(self.on_node_update)
        self.ui.script1Param5Spin.valueChanged.connect(self.on_node_update)
        self.ui.script1Param6Edit.textEdited.connect(self.on_node_update)
        self.ui.script2Param1Spin.valueChanged.connect(self.on_node_update)
        self.ui.script2Param2Spin.valueChanged.connect(self.on_node_update)
        self.ui.script2Param3Spin.valueChanged.connect(self.on_node_update)
        self.ui.script2Param4Spin.valueChanged.connect(self.on_node_update)
        self.ui.script2Param5Spin.valueChanged.connect(self.on_node_update)
        self.ui.script2Param6Edit.textEdited.connect(self.on_node_update)
        self.ui.condition1Param1Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition1Param2Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition1Param3Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition1Param4Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition1Param5Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition1Param6Edit.textEdited.connect(self.on_node_update)
        self.ui.condition1NotCheckbox.stateChanged.connect(self.on_node_update)
        self.ui.condition2Param1Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition2Param2Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition2Param3Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition2Param4Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition2Param5Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition2Param6Edit.textEdited.connect(self.on_node_update)
        self.ui.condition2NotCheckbox.stateChanged.connect(self.on_node_update)
        self.ui.emotionSelect.currentIndexChanged.connect(self.on_node_update)
        self.ui.expressionSelect.currentIndexChanged.connect(self.on_node_update)
        self.ui.soundCheckbox.toggled.connect(self.on_node_update)
        self.ui.soundCheckbox.toggled.connect(self.handle_sound_checked)
        self.ui.plotIndexCombo.currentIndexChanged.connect(self.on_node_update)
        self.ui.plotXpSpin.valueChanged.connect(self.on_node_update)
        self.ui.questEdit.textEdited.connect(self.on_node_update)
        self.ui.questEntrySpin.valueChanged.connect(self.on_node_update)
        self.ui.cameraIdSpin.valueChanged.connect(self.on_node_update)
        self.ui.cameraAngleSelect.currentIndexChanged.connect(self.on_node_update)
        self.ui.cameraEffectSelect.currentIndexChanged.connect(self.on_node_update)
        self.ui.nodeUnskippableCheckbox.toggled.connect(self.on_node_update)
        self.ui.nodeIdSpin.valueChanged.connect(self.on_node_update)
        self.ui.alienRaceNodeSpin.valueChanged.connect(self.on_node_update)
        self.ui.postProcSpin.valueChanged.connect(self.on_node_update)
        self.ui.delaySpin.valueChanged.connect(self.on_node_update)
        self.ui.logicSpin.valueChanged.connect(self.on_node_update)
        self.ui.waitFlagSpin.valueChanged.connect(self.on_node_update)
        self.ui.fadeTypeSpin.valueChanged.connect(self.on_node_update)
        self.ui.commentsEdit.textChanged.connect(self.on_node_update)

        self.ui.cameraAnimSpin.valueChanged.connect(self.on_node_update)
        self.ui.cameraAnimSpin.setMinimum(1200)
        self.ui.cameraAnimSpin.setMaximum(65535)

        self.ui.addStuntButton.clicked.connect(self.on_add_stunt_clicked)
        self.ui.removeStuntButton.clicked.connect(self.on_remove_stunt_clicked)
        self.ui.editStuntButton.clicked.connect(self.on_edit_stunt_clicked)

        self.ui.addAnimButton.clicked.connect(self.on_add_anim_clicked)
        self.ui.removeAnimButton.clicked.connect(self.on_remove_anim_clicked)
        self.ui.editAnimButton.clicked.connect(self.on_edit_anim_clicked)

        self.ui.cameraModelSelect.activated.connect(self.on_node_update)

    def setup_extra_widgets(self):
        self.setup_left_dock_widget()
        self.setup_menu_extras()

        # Go-to bar
        self.go_to_bar: QWidget = QWidget(self)
        self.go_to_bar.setVisible(False)
        self.go_to_layout: QHBoxLayout = QHBoxLayout(self.go_to_bar)
        self.go_to_input: QLineEdit = QLineEdit(self.go_to_bar)
        self.go_to_button: QPushButton = QPushButton("Go", self.go_to_bar)
        self.go_to_layout.addWidget(self.go_to_input)
        self.go_to_layout.addWidget(self.go_to_button)
        self.ui.verticalLayout_main.insertWidget(0, self.go_to_bar)  # type: ignore[arg-type]

        # Find bar
        self.find_bar: QWidget = QWidget(self)
        self.find_bar.setVisible(False)
        self.find_layout: QHBoxLayout = QHBoxLayout(self.find_bar)
        self.find_input: QLineEdit = QLineEdit(self.find_bar)
        self.find_button: QPushButton = QPushButton("", self.find_bar)
        q_style: QStyle | None = self.style()
        assert q_style is not None
        self.find_button.setIcon(q_style.standardIcon(QStyle.StandardPixmap.SP_ArrowForward))
        self.back_button: QPushButton = QPushButton("", self.find_bar)
        self.back_button.setIcon(q_style.standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        self.results_label: QLabel = QLabel(self.find_bar)
        self.find_layout.addWidget(self.find_input)
        self.find_layout.addWidget(self.back_button)
        self.find_layout.addWidget(self.find_button)
        self.find_layout.addWidget(self.results_label)
        self.ui.verticalLayout_main.insertWidget(0, self.find_bar)  # type: ignore[arg-type]
        self.setup_completer()

    def setup_completer(self):
        temp_entry: DLGEntry = DLGEntry()
        temp_link: DLGLink = DLGLink(temp_entry)
        entry_attributes: set[str] = {
            attr[0] for attr in temp_entry.__dict__.items() if not attr[0].startswith("_") and not callable(attr[1]) and not isinstance(attr[1], list)
        }
        link_attributes: set[str] = {
            attr[0] for attr in temp_link.__dict__.items() if not attr[0].startswith("_") and not callable(attr[1]) and not isinstance(attr[1], (DLGEntry, DLGReply))
        }
        suggestions: list[str] = [f"{key}:" for key in [*entry_attributes, *link_attributes, "stringref", "strref"]]

        self.find_input_completer: QCompleter = QCompleter(suggestions, self.find_input)
        self.find_input_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.find_input_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.find_input_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.find_input_completer.setMaxVisibleItems(10)
        self.find_input.setCompleter(self.find_input_completer)

    def show_go_to_bar(self):
        self.go_to_bar.setVisible(True)
        self.go_to_input.setFocus()

    def show_find_bar(self):
        self.find_bar.setVisible(True)
        self.find_input.setFocus()

    def handle_go_to(self):
        input_text = self.go_to_input.text()
        self.custom_go_to_function(input_text)
        self.go_to_bar.setVisible(False)

    def handle_find(self):
        input_text: str = self.find_input.text()
        if not self.search_results or input_text != self.current_search_text:
            self.search_results = self.find_item_matching_display_text(input_text)
            self.current_search_text = input_text
            self.current_result_index = 0
        if not self.search_results:
            self.results_label.setText("No results found")
            return
        self.current_result_index = (self.current_result_index + 1) % len(self.search_results)
        self.highlight_result(self.search_results[self.current_result_index])
        self.update_results_label()

    def handle_back(self):
        if not self.search_results:
            return
        self.current_result_index = (self.current_result_index - 1 + len(self.search_results)) % len(self.search_results)
        self.highlight_result(self.search_results[self.current_result_index])
        self.update_results_label()

    def custom_go_to_function(
        self,
        input_text: str,
    ): ...  # TODO(th3w1zard1): allow quick jumps to EntryList/ReplyList nodes.  # noqa: FIX002, TD003

    def parse_query(
        self,
        input_text: str,
    ) -> list[tuple[str, str | None, Literal["AND", "OR", None]]]:
        pattern = r'("[^"]*"|\S+)'
        tokens: list[str] = re.findall(pattern, input_text)
        normalized_tokens: list[str] = []

        for token in tokens:
            if token.startswith('"') and token.endswith('"'):
                normalized_tokens.append(token[1:-1])
            else:
                normalized_tokens.extend(re.split(r"\s+", token))

        conditions: list[tuple[str, str | None, Literal["AND", "OR", None]]] = []
        operator: Literal["AND", "OR", None] = None
        i = 0

        while i < len(normalized_tokens):
            token = normalized_tokens[i].upper()
            if token in ("AND", "OR"):
                operator = token
                i += 1
                continue

            next_index: int | None = i + 1 if i + 1 < len(normalized_tokens) else None
            if ":" in normalized_tokens[i]:
                try:
                    key, sep, value = normalized_tokens[i].partition(":")
                    if value == "":
                        conditions.append((key.strip().lower(), None, operator))
                    else:
                        conditions.append((key.strip().lower(), value.strip().lower() if value else None, operator))
                finally:
                    operator = None
            elif next_index and normalized_tokens[next_index].upper() in ("AND", "OR"):
                conditions.append((normalized_tokens[i], "", operator))
                operator = None
            elif not next_index:
                conditions.append((normalized_tokens[i], "", operator))
                operator = None

            i += 1

        return conditions

    def find_item_matching_display_text(  # noqa: C901
        self,
        input_text: str,
    ) -> list[DLGStandardItem]:  # noqa: C901
        conditions: list[tuple[str, str | None, Literal["AND", "OR"] | None]] = self.parse_query(input_text)
        matching_items: list[DLGStandardItem] = []

        def condition_matches(  # noqa: C901
            key: str,
            value: str | None,
            operator: Literal["AND", "OR", None],  # noqa: ARG001
            item: DLGStandardItem,
        ) -> bool:
            if not isinstance(item, DLGStandardItem) or item.link is None:
                return False
            sentinel: object = object()
            link_value: Any = getattr(item.link, key, sentinel)
            node_value: Any = getattr(item.link.node, key, sentinel)

            def check_value(  # noqa: PLR0911
                attr_value: Any,
                search_value: str | None,
            ) -> bool:  # noqa: PLR0911
                if attr_value is sentinel:
                    return False
                if search_value is None:  # This indicates a truthiness check
                    return bool(attr_value) and attr_value not in (0xFFFFFFFF, -1)
                if isinstance(attr_value, int):
                    try:
                        return attr_value == int(search_value)
                    except ValueError:
                        return False
                elif isinstance(attr_value, bool):
                    if search_value.lower() in ["true", "1"]:
                        return attr_value is True
                    if search_value.lower() in ["false", "0"]:
                        return attr_value is False
                return search_value.lower() in str(attr_value).lower()

            if check_value(link_value, value) or check_value(node_value, value):
                return True
            if key in ("strref", "stringref"):
                if value is not None:
                    try:
                        return int(value.strip()) in item.link.node.text._substrings  # noqa: SLF001
                    except ValueError:
                        return False
                return bool(item.link.node.text)
            return False

        def evaluate_conditions(
            item: DLGStandardItem,
        ) -> bool:
            item_text: str = item.text().lower()
            if input_text.lower() in item_text:
                return True
            result: bool = not conditions
            for condition in conditions:
                key, value, operator = condition
                if operator == "AND":
                    result = result and condition_matches(key, value, operator, item)
                elif operator == "OR":
                    result = result or condition_matches(key, value, operator, item)
                else:
                    result = condition_matches(key, value, operator, item)
            return result

        def search_item(
            item: DLGStandardItem,
        ):
            if evaluate_conditions(item):
                matching_items.append(item)
            for row in range(item.rowCount()):
                child_item: DLGStandardItem = cast(DLGStandardItem, item.child(row))
                if child_item:
                    search_item(child_item)

        def search_children(
            parent_item: DLGStandardItem,
        ):
            for row in range(parent_item.rowCount()):
                child_item: DLGStandardItem = cast(DLGStandardItem, parent_item.child(row))
                search_item(child_item)
                search_children(child_item)

        search_children(cast(DLGStandardItem, self.model.invisibleRootItem()))
        return list({*matching_items})

    def highlight_result(
        self,
        item: DLGStandardItem,
    ):
        index: QModelIndex = self.model.indexFromItem(item)
        parent: QModelIndex = index.parent()
        while parent.isValid():
            self.ui.dialogTree.expand(parent)
            parent = parent.parent()
        self.ui.dialogTree.setCurrentIndex(index)
        self.ui.dialogTree.setFocus()
        sel_model: QItemSelectionModel | None = self.ui.dialogTree.selectionModel()
        assert sel_model is not None
        sel_model.select(
            index,
            QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows,
        )
        self.ui.dialogTree.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)

    def update_results_label(self):
        self.results_label.setText(f"{self.current_result_index + 1} / {len(self.search_results)}")

    def get_stylesheet(self) -> str:
        return """
        .link-container:hover .link-hover-text {
            display: block;
        }
        .link-container:hover .link-text {
            display: none;
        }
        .link-hover-text {
            display: none;
        }
        """

    def setup_left_dock_widget(self):  # noqa: PLR0915
        self.left_dock_widget: QDockWidget = QDockWidget("Orphaned Nodes and Pinned Items", self)
        self.left_dock_widget_container: QWidget = QWidget()
        self.left_dock_layout: QVBoxLayout = QVBoxLayout(self.left_dock_widget_container)

        # Orphaned Nodes List
        self.orphaned_nodes_list: DLGListWidget = DLGListWidget(self)
        self.orphaned_nodes_list.use_hover_text = False
        self.orphaned_nodes_list.setWordWrap(True)
        self.orphaned_nodes_list.setItemDelegate(HTMLDelegate(self.orphaned_nodes_list))
        self.orphaned_nodes_list.setDragEnabled(True)
        self.orphaned_nodes_list.setAcceptDrops(False)
        orphan_viewport: QWidget | None = self.orphaned_nodes_list.viewport()
        assert orphan_viewport is not None
        orphan_viewport.setAcceptDrops(False)
        self.orphaned_nodes_list.setDropIndicatorShown(False)
        self.orphaned_nodes_list.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)

        # Pinned Items List
        self.pinned_items_list: DLGListWidget = DLGListWidget(self)
        self.pinned_items_list.setWordWrap(True)
        self.pinned_items_list.setItemDelegate(HTMLDelegate(self.pinned_items_list))
        self.pinned_items_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.pinned_items_list.setAcceptDrops(True)
        pinned_viewport: QWidget | None = self.pinned_items_list.viewport()
        assert pinned_viewport is not None
        pinned_viewport.setAcceptDrops(True)
        self.pinned_items_list.setDragEnabled(True)
        self.pinned_items_list.setDropIndicatorShown(True)
        self.pinned_items_list.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)

        # Add both lists to the layout
        self.left_dock_layout.addWidget(QLabel("Orphaned Nodes"))
        self.left_dock_layout.addWidget(self.orphaned_nodes_list)
        self.left_dock_layout.addWidget(QLabel("Pinned Items"))
        self.left_dock_layout.addWidget(self.pinned_items_list)

        # Set the container as the widget for the dock
        self.left_dock_widget.setWidget(self.left_dock_widget_container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock_widget)
        self.setStyleSheet(self.get_stylesheet())

        def mimeData(
            items: Iterable[DLGListWidgetItem],
            list_widget: DLGListWidget,
        ) -> QMimeData:
            mime_data = QMimeData()
            listwidget_data = QByteArray()

            stream_listwidget = QDataStream(listwidget_data, QIODevice.OpenModeFlag.WriteOnly)
            for item in items:
                index: QModelIndex = list_widget.indexFromItem(item)
                stream_listwidget.writeInt32(index.row())
                stream_listwidget.writeInt32(index.column())
                stream_listwidget.writeInt32(3)
                stream_listwidget.writeInt32(int(Qt.ItemDataRole.DisplayRole))
                stream_listwidget.writeQString(item.data(Qt.ItemDataRole.DisplayRole))
                stream_listwidget.writeInt32(_DLG_MIME_DATA_ROLE)
                stream_listwidget.writeQString(json.dumps(item.link.to_dict()))
                stream_listwidget.writeInt32(_MODEL_INSTANCE_ID_ROLE)
                stream_listwidget.writeInt64(id(self))
                # stream_listwidget.writeInt32(int(_LINK_PARENT_NODE_PATH_ROLE))
                # stream_listwidget.writeQString(item.data(_LINK_PARENT_NODE_PATH_ROLE))

            mime_data.setData(
                QT_STANDARD_ITEM_FORMAT,
                listwidget_data,
            )
            return mime_data

        def left_dock_widget_start_drag(
            supported_actions: Qt.DropAction,
            source_widget: DLGListWidget,
        ):
            selected_items: list[DLGListWidgetItem] = source_widget.selectedItems()
            if not selected_items:
                print("No selected items being dragged? (probably means someone JUST dropped into list)")
                return

            drag = QDrag(source_widget)
            mime_data: QMimeData = mimeData(selected_items, source_widget)
            drag.setMimeData(mime_data)
            drag.exec(supported_actions)

        def start_drag_orphaned(supportedActions: Qt.DropAction):
            left_dock_widget_start_drag(supportedActions, self.orphaned_nodes_list)

        def start_drag_pinned(supportedActions: Qt.DropAction):
            left_dock_widget_start_drag(supportedActions, self.pinned_items_list)

        self.orphaned_nodes_list.startDrag = start_drag_orphaned  # pyright: ignore[reportAttributeAccessIssue]
        self.pinned_items_list.startDrag = start_drag_pinned  # pyright: ignore[reportAttributeAccessIssue]

    def restore_orphaned_node(
        self,
        link: DLGLink,
    ):
        print(f"restoreOrphanedNodes(link={link})")
        selected_orphan_item: DLGListWidgetItem | None = self.orphaned_nodes_list.currentItem()
        if selected_orphan_item is None:
            print("restoreOrphanedNodes: No left_dock_widget selected item.")
            self.blink_window()
            return
        selected_tree_indexes: list[QModelIndex] = self.ui.dialogTree.selectedIndexes()
        if not selected_tree_indexes or not selected_tree_indexes[0]:
            QMessageBox(QMessageBox.Icon.Information, "No target specified", "Select a position in the tree to insert this orphan at then try again.")
            return
        selected_tree_item: DLGStandardItem | None = cast(
            Optional[DLGStandardItem],
            self.model.itemFromIndex(selected_tree_indexes[0]),
        )
        if selected_tree_item is None:
            print("restoreOrphanedNodes: selected index was not a standard item.")
            self.blink_window()
            return
        old_link_to_current_orphan: DLGLink = selected_orphan_item.link
        if isinstance(old_link_to_current_orphan.node, type(selected_tree_item.link.node)):  # pyright: ignore[reportOptionalMemberAccess]
            target_parent: DLGStandardItem | None = selected_tree_item.parent()
            intended_link_list_index_row = selected_tree_item.row()
        else:
            target_parent = selected_tree_item
            intended_link_list_index_row = 0
        new_link_path: str = f"StartingList\\{intended_link_list_index_row}" if target_parent is None else target_parent.link.node.path()  # pyright: ignore[reportOptionalMemberAccess]
        link_parent_path, link_partial_path, linked_to_path = self.get_item_dlg_paths(selected_orphan_item)
        link_full_path: str = link_partial_path if link_parent_path is None else f"{link_parent_path}\\{link_partial_path}"
        confirm_message: str = f"The orphan '{linked_to_path}' (originally linked from {link_full_path}) will be newly linked from {new_link_path} with this action. Continue?"
        reply: QMessageBox.StandardButton = QMessageBox.question(
            self,
            "Restore Orphaned Node",
            confirm_message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            print(f"orphan '{linked_to_path}' (originally linked from {selected_orphan_item.data(_LINK_PARENT_NODE_PATH_ROLE)}) is to be linked from {new_link_path}")
            item: DLGStandardItem = self.model.insert_link_to_parent_as_item(
                target_parent,
                DLGLink.from_dict(old_link_to_current_orphan.to_dict()),
                intended_link_list_index_row,
            )
            self.model.load_dlg_item_rec(item)

            intended_link_list_index_row: int = self.orphaned_nodes_list.row(selected_orphan_item)
            self.orphaned_nodes_list.takeItem(intended_link_list_index_row)

    def delete_orphaned_node_permanently(
        self,
        link: DLGLink,
    ):
        print(f"delete_orphaned_node_permanently(link={link})")
        selected_orphan_item: DLGListWidgetItem | None = self.orphaned_nodes_list.currentItem()
        if selected_orphan_item is None:
            print("delete_orphaned_node_permanently: No left_dock_widget selected item.")
            self.blink_window()
            return
        self.orphaned_nodes_list.takeItem(self.orphaned_nodes_list.row(selected_orphan_item))

    def setup_menu_extras(self):  # noqa: PLR0915
        self.view_menu: QMenu = self.ui.menubar.addMenu("View")  # type: ignore[arg-type]
        self.settings_menu: QMenu = self.ui.menubar.addMenu("Settings")  # type: ignore[arg-type]
        self.advanced_menu: QMenu | None = self.view_menu.addMenu("Advanced")
        assert self.advanced_menu is not None
        self.refresh_menu: QMenu | None = self.advanced_menu.addMenu("Refresh")
        assert self.refresh_menu is not None
        self.tree_menu: QMenu | None = self.refresh_menu.addMenu("TreeView")
        assert self.tree_menu is not None

        cast(QAction, self.ui.menubar.addAction("Help")).triggered.connect(self.show_all_tips)
        whats_this_action: QAction = QAction(cast(QStyle, self.style()).standardIcon(QStyle.StandardPixmap.SP_TitleBarContextHelpButton), "", self)
        whats_this_action.triggered.connect(QWhatsThis.enterWhatsThisMode)
        whats_this_action.setToolTip("Enter WhatsThis? mode.")
        self.ui.menubar.addAction(whats_this_action)  # pyright: ignore[reportArgumentType, reportCallIssue]

        # Common view settings
        self.ui.dialogTree._add_menu_action(  # noqa: SLF001
            self.view_menu,
            "Uniform Row Heights",
            self.ui.dialogTree.uniformRowHeights,
            self.ui.dialogTree.setUniformRowHeights,
            settings_key="uniformRowHeights",
        )
        self.ui.dialogTree._add_menu_action(  # noqa: SLF001
            self.view_menu,
            "Alternating Row Colors",
            self.ui.dialogTree.alternatingRowColors,
            self.ui.dialogTree.setAlternatingRowColors,
            settings_key="alternatingRowColors",
        )
        self.ui.dialogTree._add_menu_action(  # noqa: SLF001
            self.view_menu,
            "Show/Hide Branch Connectors",
            self.ui.dialogTree.branch_connectors_drawn,
            self.ui.dialogTree.draw_connectors,
            settings_key="drawBranchConnectors",
        )
        self.ui.dialogTree._add_menu_action(  # noqa: SLF001
            self.view_menu,
            "Expand Items on Double Click",
            self.ui.dialogTree.expandsOnDoubleClick,
            self.ui.dialogTree.setExpandsOnDoubleClick,
            settings_key="expandsOnDoubleClick",
        )
        self.ui.dialogTree._add_menu_action(  # noqa: SLF001
            self.view_menu,
            "Tree Indentation",
            self.ui.dialogTree.indentation,
            self.ui.dialogTree.setIndentation,
            settings_key="indentation",
            param_type=int,
        )

        # Text and Icon Display Settings
        display_settings_menu: QMenu | None = self.view_menu.addMenu("Display Settings")
        assert display_settings_menu is not None
        self.ui.dialogTree._add_exclusive_menu_action(  # noqa: SLF001
            display_settings_menu,
            "Text Elide Mode",
            self.ui.dialogTree.textElideMode,
            lambda x: self.ui.dialogTree.setTextElideMode(Qt.TextElideMode(x)),
            options={
                "Elide Left": Qt.TextElideMode.ElideLeft,
                "Elide Right": Qt.TextElideMode.ElideRight,
                "Elide Middle": Qt.TextElideMode.ElideMiddle,
                "Elide None": Qt.TextElideMode.ElideNone,
            },
            settings_key="textElideMode",
        )
        self.ui.dialogTree._add_menu_action(  # noqa: SLF001
            display_settings_menu,
            "Font Size",
            self.ui.dialogTree.get_text_size,
            self.ui.dialogTree.set_text_size,
            settings_key="fontSize",
            param_type=int,
        )
        self.ui.dialogTree._add_menu_action(  # noqa: SLF001
            display_settings_menu,
            "Vertical Spacing",
            lambda: self.ui.dialogTree.itemDelegate().custom_vertical_spacing,  # pyright: ignore[reportAttributeAccessIssue]
            lambda x: self.ui.dialogTree.itemDelegate().setVerticalSpacing(x),  # pyright: ignore[reportAttributeAccessIssue]
            settings_key="verticalSpacing",
            param_type=int,
        )

        # Focus and scrolling settings
        self.ui.dialogTree._add_exclusive_menu_action(  # noqa: SLF001
            self.settings_menu,
            "Focus Policy",
            self.ui.dialogTree.focusPolicy,
            self.ui.dialogTree.setFocusPolicy,
            options={
                "No Focus": Qt.FocusPolicy.NoFocus,
                "Tab Focus": Qt.FocusPolicy.TabFocus,
                "Click Focus": Qt.FocusPolicy.ClickFocus,
                "Strong Focus": Qt.FocusPolicy.StrongFocus,
                "Wheel Focus": Qt.FocusPolicy.WheelFocus,
            },
            settings_key="focusPolicy",
        )
        self.ui.dialogTree._add_exclusive_menu_action(  # noqa: SLF001
            self.settings_menu,
            "Horizontal Scroll Mode",
            self.ui.dialogTree.horizontalScrollMode,
            self.ui.dialogTree.setHorizontalScrollMode,
            options={
                "Scroll Per Item": QAbstractItemView.ScrollMode.ScrollPerItem,
                "Scroll Per Pixel": QAbstractItemView.ScrollMode.ScrollPerPixel,
            },
            settings_key="horizontalScrollMode",
        )
        self.ui.dialogTree._add_exclusive_menu_action(  # noqa: SLF001
            self.settings_menu,
            "Vertical Scroll Mode",
            self.ui.dialogTree.verticalScrollMode,
            self.ui.dialogTree.setVerticalScrollMode,
            options={
                "Scroll Per Item": QAbstractItemView.ScrollMode.ScrollPerItem,
                "Scroll Per Pixel": QAbstractItemView.ScrollMode.ScrollPerPixel,
            },
            settings_key="verticalScrollMode",
        )
        self.ui.dialogTree._add_menu_action(  # noqa: SLF001
            self.settings_menu,
            "Auto Scroll",
            self.ui.dialogTree.hasAutoScroll,
            self.ui.dialogTree.setAutoScroll,
            settings_key="autoScroll",
        )
        self.ui.dialogTree._add_menu_action(  # noqa: SLF001
            self.settings_menu,
            "Auto Fill Background",
            self.autoFillBackground,
            self.setAutoFillBackground,
            settings_key="autoFillBackground",
        )

        self.ui.dialogTree._add_simple_action(self.advanced_menu, "Repaint", self.repaint)  # noqa: SLF001
        self.ui.dialogTree._add_simple_action(self.advanced_menu, "Update", self.update)  # noqa: SLF001
        self.ui.dialogTree._add_simple_action(self.advanced_menu, "Resize Column To Contents", lambda: self.ui.dialogTree.resizeColumnToContents(0))  # noqa: SLF001
        self.ui.dialogTree._add_simple_action(self.advanced_menu, "Update Geometries", self.ui.dialogTree.updateGeometries)  # noqa: SLF001
        self.ui.dialogTree._add_simple_action(self.advanced_menu, "Reset", self.ui.dialogTree.reset)  # noqa: SLF001

        self.ui.dialogTree._add_exclusive_menu_action(  # noqa: SLF001
            self.settings_menu,
            "TSL Widget Handling",
            lambda: "Default",
            self.set_tsl_widget_handling,
            options={
                "Enable": "Enable",
                "Disable": "Disable",
                "Show": "Show",
                "Hide": "Hide",
                "Default": "Default",
            },
            settings_key="tsl_widget_handling",
        )

        # FIXME(th3w1zard1):  # noqa: TD005, FIX001, TD003
        # self._add_menu_action(settingsMenu, "Show/Hide Extra ToolTips on Hover",
        #                    lambda: self.whats_this_toggle,
        #                    lambda _value: self.setupExtraTooltipMode(),
        #                    settings_key="showVerboseHoverHints",
        #                    param_type=bool)

        # Advanced Menu: Miscellaneous advanced settings
        self.ui.dialogTree._add_simple_action(self.tree_menu, "Repaint", self.ui.dialogTree.repaint)  # noqa: SLF001
        self.ui.dialogTree._add_simple_action(self.tree_menu, "Update", self.ui.dialogTree.update)  # noqa: SLF001
        self.ui.dialogTree._add_simple_action(self.tree_menu, "Resize Column To Contents", lambda: self.ui.dialogTree.resizeColumnToContents(0))  # noqa: SLF001
        self.ui.dialogTree._add_simple_action(self.tree_menu, "Update Geometries", self.ui.dialogTree.updateGeometries)  # noqa: SLF001
        self.ui.dialogTree._add_simple_action(self.tree_menu, "Reset", self.ui.dialogTree.reset)  # noqa: SLF001

        list_widget_menu: QMenu | None = self.refresh_menu.addMenu("ListWidget")
        assert list_widget_menu is not None
        self.ui.dialogTree._add_simple_action(list_widget_menu, "Repaint", self.pinned_items_list.repaint)  # noqa: SLF001
        self.ui.dialogTree._add_simple_action(list_widget_menu, "Update", self.pinned_items_list.update)  # noqa: SLF001
        self.ui.dialogTree._add_simple_action(list_widget_menu, "Reset Horizontal Scroll Mode", lambda: self.pinned_items_list.resetHorizontalScrollMode())  # noqa: SLF001
        self.ui.dialogTree._add_simple_action(list_widget_menu, "Reset Vertical Scroll Mode", lambda: self.pinned_items_list.resetVerticalScrollMode())  # noqa: SLF001
        self.ui.dialogTree._add_simple_action(list_widget_menu, "Update Geometries", self.pinned_items_list.updateGeometries)  # noqa: SLF001
        self.ui.dialogTree._add_simple_action(list_widget_menu, "Reset", self.pinned_items_list.reset)  # noqa: SLF001
        self.ui.dialogTree._add_simple_action(list_widget_menu, "layoutChanged", lambda: self.pinned_items_list.model().layoutChanged.emit())  # noqa: SLF001  # pyright: ignore[reportOptionalMemberAccess]

        view_port_menu: QMenu | None = self.refresh_menu.addMenu("Viewport")
        assert view_port_menu is not None
        view_port: QWidget | None = self.ui.dialogTree.viewport()
        assert view_port is not None
        self.ui.dialogTree._add_simple_action(view_port_menu, "Repaint", view_port.repaint)  # noqa: SLF001
        self.ui.dialogTree._add_simple_action(view_port_menu, "Update", view_port.update)  # noqa: SLF001

        model_menu: QMenu | None = self.refresh_menu.addMenu("Model")
        assert model_menu is not None
        self.ui.dialogTree._add_simple_action(model_menu, "Emit Layout Changed", lambda: self.ui.dialogTree.model().layoutChanged.emit())  # pyright: ignore[reportOptionalMemberAccess]  # noqa: SLF001

        window_menu: QMenu | None = self.refresh_menu.addMenu("Window")
        assert window_menu is not None
        self.ui.dialogTree._add_simple_action(window_menu, "Repaint", self.repaint)  # noqa: SLF001

    def set_tsl_widget_handling(
        self,
        state: Literal["Default", "Disable", "Enable", "Hide", "Show"],
    ):
        DLGSettings().set("tsl_widget_handling", state)
        widgets_to_handle: list[Any] = [
            self.ui.script1Param1Spin,
            self.ui.script1Param2Spin,
            self.ui.script1Param3Spin,
            self.ui.script1Param4Spin,
            self.ui.script1Param5Spin,
            self.ui.script1Param6Edit,
            self.ui.script2ResrefEdit,
            self.ui.script2Param1Spin,
            self.ui.script2Param2Spin,
            self.ui.script2Param3Spin,
            self.ui.script2Param4Spin,
            self.ui.script2Param5Spin,
            self.ui.script2Param6Edit,
            self.ui.condition1Param1Spin,
            self.ui.condition1Param2Spin,
            self.ui.condition1Param3Spin,
            self.ui.condition1Param4Spin,
            self.ui.condition1Param5Spin,
            self.ui.condition1Param6Edit,
            self.ui.condition1NotCheckbox,
            self.ui.condition2ResrefEdit,
            self.ui.condition2Param1Spin,
            self.ui.condition2Param2Spin,
            self.ui.condition2Param3Spin,
            self.ui.condition2Param4Spin,
            self.ui.condition2Param5Spin,
            self.ui.condition2Param6Edit,
            self.ui.condition2NotCheckbox,
            self.ui.emotionSelect,
            self.ui.expressionSelect,
            self.ui.nodeUnskippableCheckbox,
            self.ui.nodeIdSpin,
            self.ui.alienRaceNodeSpin,
            self.ui.postProcSpin,
            self.ui.logicSpin,
            # labels
            self.ui.script2Label,
            self.ui.conditional2Label,
            self.ui.emotionLabel,
            self.ui.expressionLabel,
            self.ui.nodeIdLabel,
            self.ui.alienRaceNodeLabel,
            self.ui.postProcNodeLabel,
            self.ui.logicLabel,
        ]
        for widget in widgets_to_handle:
            self.handle_widget_with_tsl(widget, state)

    def handle_widget_with_tsl(
        self,
        widget: QWidget | QLabel,
        state: Literal["Default", "Disable", "Enable", "Hide", "Show"],
    ):
        """Customizes widget behavior based on TSL state."""
        widget.show()
        widget.setEnabled(True)
        if state == "Default":
            widget.setEnabled(self._installation.tsl)
            if self._installation.tsl:
                widget.setToolTip("")
            else:
                widget.setToolTip("This widget is only available in KOTOR II.")
        elif state == "Disable":
            widget.setEnabled(False)
            widget.setToolTip("This widget is only available in KOTOR II.")
        elif state == "Enable":
            widget.setEnabled(True)
        elif state == "Hide":
            widget.hide()
        elif state == "Show":
            widget.show()

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        """Loads a dialogue file."""
        super().load(filepath, resref, restype, data)
        dlg: DLG = read_dlg(data)
        self._load_dlg(dlg)
        self.refresh_stunt_list()
        self.ui.onAbortCombo.set_combo_box_text(str(dlg.on_abort))
        self.ui.onEndEdit.set_combo_box_text(str(dlg.on_end))
        self.ui.voIdEdit.setText(dlg.vo_id)
        self.ui.voIdEdit.textChanged.connect(self.restart_void_edit_timer)
        self.ui.ambientTrackCombo.set_combo_box_text(str(dlg.ambient_track))
        self.ui.cameraModelSelect.set_combo_box_text(str(dlg.camera_model))
        self.ui.conversationSelect.setCurrentIndex(dlg.conversation_type.value)
        self.ui.computerSelect.setCurrentIndex(dlg.computer_type.value)
        self.ui.skippableCheckbox.setChecked(dlg.skippable)
        self.ui.skippableCheckbox.setToolTip("Should the user be allowed to skip dialog lines/cutscenes in this file?")
        self.ui.animatedCutCheckbox.setChecked(bool(dlg.animated_cut))
        self.ui.oldHitCheckbox.setChecked(dlg.old_hit_check)
        self.ui.oldHitCheckbox.setToolTip("It is likely OldHitCheck is a deprecated remnant of a previous game.")
        self.ui.unequipHandsCheckbox.setChecked(dlg.unequip_hands)
        self.ui.unequipAllCheckbox.setChecked(dlg.unequip_items)
        self.ui.entryDelaySpin.setValue(dlg.delay_entry)
        self.ui.replyDelaySpin.setValue(dlg.delay_reply)
        relevant_script_resnames: list[str] = sorted({res.resname().lower() for res in self._installation.get_relevant_resources(ResourceType.NCS, self._filepath)})
        self.ui.script2ResrefEdit.populate_combo_box(relevant_script_resnames)
        self.ui.condition2ResrefEdit.populate_combo_box(relevant_script_resnames)
        self.ui.script1ResrefEdit.populate_combo_box(relevant_script_resnames)
        self.ui.condition1ResrefEdit.populate_combo_box(relevant_script_resnames)
        self.ui.onEndEdit.populate_combo_box(relevant_script_resnames)
        self.ui.onAbortCombo.populate_combo_box(relevant_script_resnames)
        self.ui.cameraModelSelect.populate_combo_box(sorted({res.resname().lower() for res in self._installation.get_relevant_resources(ResourceType.MDL, self._filepath)}))

    def restart_void_edit_timer(self):
        """Restarts the timer whenever text is changed."""
        self.vo_id_edit_timer.stop()
        self.vo_id_edit_timer.start()

    def populate_combobox_on_void_edit_finished(self):
        """Slot to be called when text editing is finished.

        The editors the game devs themselves used probably did something like this
        """
        if not hasattr(self, "all_voices"):
            self.blink_window()
            return
        vo_id_lower: str = self.ui.voIdEdit.text().strip().lower()
        if vo_id_lower:
            filtered_voices: list[str] = [voice for voice in self.all_voices if vo_id_lower in voice.lower()]
        else:
            filtered_voices = self.all_voices
        self.ui.voiceComboBox.populate_combo_box(filtered_voices)

    def _load_dlg(
        self,
        dlg: DLG,
    ):
        """Loads a dialog tree into the UI view."""
        if "(Light)" in GlobalSettings().selectedTheme or GlobalSettings().selectedTheme == "Native":
            self.ui.dialogTree.setStyleSheet("")
        self.orphaned_nodes_list.clear()
        self._focused = False
        self.core_dlg = dlg
        self.model.orig_to_orphan_copy = {
            weakref.ref(orig_link): copied_link
            for orig_link, copied_link in zip(
                dlg.starters,
                [DLGLink.from_dict(link.to_dict()) for link in dlg.starters],
            )
        }
        self.populate_combobox_on_void_edit_finished()

        self.model.reset_model()
        assert self.model.rowCount() == 0 and self.model.columnCount() == 0, "Model is not empty after resetModel() call!"  # noqa: PT018
        self.model.ignoring_updates = True
        for start in dlg.starters:  # descending order - matches what the game does.
            item = DLGStandardItem(link=start)
            self.model.appendRow(item)
            self.model.load_dlg_item_rec(item)
        self.orphaned_nodes_list.reset()
        self.orphaned_nodes_list.clear()
        orphan_model: QAbstractItemModel | None = self.orphaned_nodes_list.model()
        assert orphan_model is not None
        orphan_model.layoutChanged.emit()
        self.model.ignoring_updates = False
        assert self.model.rowCount() != 0 or not dlg.starters, "Model is empty after _load_dlg(dlg: DLG) call!"  # noqa: PT018
        assert self.model.node_to_items or not dlg.starters, "node_to_items is empty in the model somehow!"
        assert self.model.link_to_items or not dlg.starters, "link_to_items is empty in the model somehow!"

    def build(self) -> tuple[bytes, bytes]:
        """Builds a dialogue from UI components."""
        self.core_dlg.on_abort = ResRef(self.ui.onAbortCombo.currentText())
        self.core_dlg.on_end = ResRef(self.ui.onEndEdit.currentText())
        self.core_dlg.vo_id = self.ui.voIdEdit.text()
        self.core_dlg.ambient_track = ResRef(self.ui.ambientTrackCombo.currentText())
        self.core_dlg.camera_model = ResRef(self.ui.cameraModelSelect.currentText())
        self.core_dlg.conversation_type = DLGConversationType(self.ui.conversationSelect.currentIndex())
        self.core_dlg.computer_type = DLGComputerType(self.ui.computerSelect.currentIndex())
        self.core_dlg.skippable = self.ui.skippableCheckbox.isChecked()
        self.core_dlg.animated_cut = self.ui.animatedCutCheckbox.isChecked()
        self.core_dlg.old_hit_check = self.ui.oldHitCheckbox.isChecked()
        self.core_dlg.unequip_hands = self.ui.unequipHandsCheckbox.isChecked()
        self.core_dlg.unequip_items = self.ui.unequipAllCheckbox.isChecked()
        self.core_dlg.delay_entry = self.ui.entryDelaySpin.value()
        self.core_dlg.delay_reply = self.ui.replyDelaySpin.value()

        data = bytearray()
        game_to_use: Game = self._installation.game()
        tsl_widget_handling_setting: str = DLGSettings().tsl_widget_handling("Default")
        if game_to_use.is_k1() and tsl_widget_handling_setting == "Enable":
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("Save TSL Fields?")
            msg_box.setText("You have tsl_widget_handling set to 'Enable', but your loaded installation set to K1. Would you like to save TSL fields?")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            response: int = msg_box.exec()
            if response == QMessageBox.StandardButton.Yes:
                game_to_use = Game.K2

        write_dlg(self.core_dlg, data, game_to_use)
        # dismantle_dlg(self.editor.core_dlg).compare(read_gff(data), log_func=print)  # use for debugging (don't forget to import)

        return data, b""

    def new(self):
        super().new()
        self._load_dlg(DLG())

    def _setup_installation(
        self,
        installation: HTInstallation,
    ):
        """Sets up the installation for the UI."""
        self._installation = installation
        installation.setup_file_context_menu(self.ui.script1ResrefEdit, [ResourceType.NSS, ResourceType.NCS])
        if installation.game().is_k1():
            required: list[str] = [HTInstallation.TwoDA_VIDEO_EFFECTS, HTInstallation.TwoDA_DIALOG_ANIMS]

        else:
            required = [
                HTInstallation.TwoDA_EMOTIONS,
                HTInstallation.TwoDA_EXPRESSIONS,
                HTInstallation.TwoDA_VIDEO_EFFECTS,
                HTInstallation.TwoDA_DIALOG_ANIMS,
            ]
        installation.ht_batch_cache_2da(required)

        self.all_voices: list[str] = sorted({res.resname() for res in installation._streamwaves}, key=str.lower)  # noqa: SLF001
        self.all_sounds: list[str] = sorted({res.resname() for res in [*installation._streamwaves, *installation._streamsounds]}, key=str.lower)  # noqa: SLF001
        self.all_music: list[str] = sorted({res.resname() for res in installation._streammusic}, key=str.lower)  # noqa: SLF001
        self._setup_tsl_emotions_and_expressions(installation)
        self.ui.soundComboBox.populate_combo_box(self.all_sounds)  # noqa: SLF001
        self.ui.ambientTrackCombo.populate_combo_box(self.all_music)
        self.ui.ambientTrackCombo.set_button_delegate("Play", lambda text: self.play_sound(text))
        installation.setup_file_context_menu(self.ui.cameraModelSelect, [ResourceType.MDL], [SearchLocation.CHITIN, SearchLocation.OVERRIDE])
        installation.setup_file_context_menu(self.ui.ambientTrackCombo, [ResourceType.WAV, ResourceType.MP3], [SearchLocation.MUSIC])
        installation.setup_file_context_menu(self.ui.soundComboBox, [ResourceType.WAV, ResourceType.MP3], [SearchLocation.SOUND, SearchLocation.VOICE])
        installation.setup_file_context_menu(self.ui.voiceComboBox, [ResourceType.WAV, ResourceType.MP3], [SearchLocation.VOICE])
        installation.setup_file_context_menu(self.ui.condition1ResrefEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onEndEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onAbortCombo, [ResourceType.NSS, ResourceType.NCS])

        vid_effects: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_VIDEO_EFFECTS)
        if vid_effects is not None:
            self.ui.cameraEffectSelect.clear()
            self.ui.cameraEffectSelect.setPlaceholderText("[Unset]")
            self.ui.cameraEffectSelect.set_items(
                [label.replace("VIDEO_EFFECT_", "").replace("_", " ").title() for label in vid_effects.get_column("label")],
                cleanup_strings=False,
                ignore_blanks=True,
            )
            self.ui.cameraEffectSelect.set_context(vid_effects, installation, HTInstallation.TwoDA_VIDEO_EFFECTS)

        plot2DA: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_PLOT)
        if plot2DA is not None:
            self.ui.plotIndexCombo.clear()
            self.ui.plotIndexCombo.addItem("[None]", -1)
            self.ui.plotIndexCombo.set_items(
                [cell.title() for cell in plot2DA.get_column("label")],
                cleanup_strings=True,
            )
            self.ui.plotIndexCombo.set_context(plot2DA, installation, HTInstallation.TwoDA_PLOT)

    def _setup_tsl_emotions_and_expressions(
        self,
        installation: HTInstallation,
    ):
        """Set up UI elements for TSL installation selection."""
        emotions: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_EMOTIONS)
        if emotions:
            self.ui.emotionSelect.clear()
            self.ui.emotionSelect.set_items(emotions.get_column("label"))
            self.ui.emotionSelect.set_context(emotions, installation, HTInstallation.TwoDA_EMOTIONS)

        expressions: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_EXPRESSIONS)
        if expressions:
            self.ui.expressionSelect.clear()
            self.ui.expressionSelect.set_items(expressions.get_column("label"))
            self.ui.expressionSelect.set_context(expressions, installation, HTInstallation.TwoDA_EXPRESSIONS)

        installation.setup_file_context_menu(self.ui.script2ResrefEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.condition2ResrefEdit, [ResourceType.NSS, ResourceType.NCS])

    def edit_text(
        self,
        e: QMouseEvent | QKeyEvent | None = None,
        indexes: list[QModelIndex] | None = None,
        source_widget: DLGListWidget | DLGTreeView | None = None,
    ):
        """Edits the text of the selected dialog node."""
        if not indexes:
            self.blink_window()
            return
        for index in indexes:
            model_to_use: DLGListWidget | QAbstractItemModel | None = source_widget if isinstance(source_widget, DLGListWidget) else index.model()
            assert isinstance(
                model_to_use,
                (DLGStandardItemModel, QStandardItemModel),
            ), f"`modelToUse = source_widget if isinstance(source_widget, DLGListWidget) else index.model()` {model_to_use.__class__}: {model_to_use} cannot be None."
            item: DLGStandardItem | QStandardItem | None = model_to_use.itemFromIndex(index)
            assert item is not None, "modelToUse.itemFromIndex(index) should not return None here in edit_text"
            assert isinstance(item, (DLGStandardItem, DLGListWidgetItem))
            if item.link is None:
                continue

            dialog = LocalizedStringDialog(self, self._installation, item.link.node.text)
            if not dialog.exec():
                continue
            item.link.node.text = dialog.locstring
            if isinstance(item, DLGStandardItem):
                self.model.update_item_display_text(item)
            elif isinstance(source_widget, DLGListWidget):
                source_widget.update_item(item)

    def copy_path(
        self,
        node_or_link: DLGNode | DLGLink | None,
    ):
        """Copies the node path to the user's clipboard."""
        if node_or_link is None:
            return
        paths: list[PureWindowsPath] = self.core_dlg.find_paths(node_or_link)  # pyright: ignore[reportArgumentType]

        if not paths:
            print("No paths available.")
            self.blink_window()
            return

        if len(paths) == 1:
            path = str(paths[0])
            print("<SDM> [copyPath scope] path: ", path)

        else:
            path = "\n".join(f"  {i + 1}. {p}" for i, p in enumerate(paths))

        cb: QClipboard | None = QApplication.clipboard()
        if cb is None:
            return
        cb.setText(path)

    def _check_clipboard_for_json_node(self):
        cb: QClipboard | None = QApplication.clipboard()
        if cb is None:
            return
        clipboard_text: str = cb.text()

        try:
            node_data: dict[str | int, Any] = json.loads(clipboard_text)
            if isinstance(node_data, dict) and "type" in node_data:
                self._copy = DLGLink.from_dict(node_data)
        except json.JSONDecodeError:
            ...
        except Exception:
            self._logger.exception("Invalid JSON node on clipboard.")

    def expand_to_root(
        self,
        item: DLGStandardItem,
    ):
        parent: DLGStandardItem | None = item.parent()
        while parent is not None:
            self.ui.dialogTree.expand(parent.index())
            parent = parent.parent()

    def jump_to_original(
        self,
        copied_item: DLGStandardItem,
    ):
        """Jumps to the original node of a copied item."""
        assert copied_item.link is not None
        source_node: DLGNode = copied_item.link.node
        items: deque[DLGStandardItem | QStandardItem | None] = deque([self.model.item(i, 0) for i in range(self.model.rowCount())])

        while items:
            item: DLGStandardItem | QStandardItem | None = items.popleft()
            if not isinstance(item, DLGStandardItem):
                continue
            if item.link is None:
                continue
            if item.link.node == source_node:
                self.expand_to_root(item)
                self.ui.dialogTree.setCurrentIndex(item.index())
                break
            items.extend([item.child(i, 0) for i in range(item.rowCount())])
        else:
            self._logger.error(f"Failed to find original node for node {source_node!r}")

    def focus_on_node(
        self,
        link: DLGLink | None,
    ) -> DLGStandardItem | None:
        """Focuses the dialog tree on a specific link node."""
        if link is None:
            return None
        if "(Light)" in GlobalSettings().selectedTheme or GlobalSettings().selectedTheme == "Native":
            self.ui.dialogTree.setStyleSheet("QTreeView { background: #FFFFEE; }")
        self.model.clear()
        self._focused = True

        item = DLGStandardItem(link=link)
        self.model.layoutAboutToBeChanged.emit()
        self.model.ignoring_updates = True
        self.model.appendRow(item)
        self.model.load_dlg_item_rec(item)
        self.model.ignoring_updates = False
        self.model.layoutChanged.emit()
        return item

    def save_expanded_items(self) -> list[QModelIndex]:
        expanded_items: list[QModelIndex] = []

        def save_items_recursively(
            index: QModelIndex,
        ):
            if not index.isValid():
                self.blink_window()
                return
            if self.ui.dialogTree.isExpanded(index):
                expanded_items.append(index)
            for i in range(self.model.rowCount(index)):
                item: DLGStandardItem | None = self.model.itemFromIndex(index)
                if item is None:
                    continue
                item_child: QStandardItem | None = item.child(i, 0)
                if item_child is None:
                    continue
                save_items_recursively(item_child.index())

        save_items_recursively(self.ui.dialogTree.rootIndex())
        return expanded_items

    def save_scroll_position(self) -> int:
        vert_scroll_bar: QScrollBar | None = self.ui.dialogTree.verticalScrollBar()
        assert vert_scroll_bar is not None
        return vert_scroll_bar.value()

    def save_selected_item(self) -> QModelIndex | None:
        sel_model: QItemSelectionModel | None = self.ui.dialogTree.selectionModel()
        if sel_model is not None and sel_model.hasSelection():
            return sel_model.currentIndex()
        return None

    def restore_expanded_items(
        self,
        expanded_items: list[QModelIndex],
    ):
        for index in expanded_items:
            self.ui.dialogTree.setExpanded(index, True)

    def restore_scroll_position(
        self,
        scroll_position: int,
    ):
        vert_scroll_bar: QScrollBar | None = self.ui.dialogTree.verticalScrollBar()
        assert vert_scroll_bar is not None
        vert_scroll_bar.setValue(scroll_position)

    def restore_selected_items(
        self,
        selected_index: QModelIndex,
    ):
        if selected_index and selected_index.isValid():
            self.ui.dialogTree.setCurrentIndex(selected_index)
            self.ui.dialogTree.scrollTo(selected_index)

    def update_tree_view(self):
        expanded_items: list[QModelIndex] = self.save_expanded_items()
        scroll_position: int = self.save_scroll_position()
        selected_index: QModelIndex | None = self.save_selected_item()
        self.ui.dialogTree.reset()

        self.restore_expanded_items(expanded_items)
        self.restore_scroll_position(scroll_position)
        self.restore_selected_items(selected_index)  # pyright: ignore[reportArgumentType]

    def on_list_context_menu(
        self,
        point: QPoint,
        source_widget: DLGListWidget,
    ):
        """Displays context menu for tree items."""
        item: DLGListWidgetItem | None = source_widget.itemAt(point)
        if item is not None:
            menu: QMenu = self._get_link_context_menu(source_widget, item)
            menu.addSeparator()
            cast(QAction, menu.addAction("Jump to in Tree")).triggered.connect(lambda *args: self.jump_to_node(item.link))
            sel_model: QItemSelectionModel | None = self.ui.dialogTree.selectionModel()
            if sel_model is not None and source_widget is self.orphaned_nodes_list and sel_model.selectedIndexes():
                restore_action: QAction | None = menu.addAction("Insert Orphan at Selected Point")
                assert restore_action is not None
                restore_action.triggered.connect(lambda: self.restore_orphaned_node(item.link))
                menu.addSeparator()
        else:
            menu = QMenu(source_widget)

        def unpin_item(*args, item=item):
            if item is None:
                return
            idx: int = source_widget.indexFromItem(item).row()
            source_widget.takeItem(idx)

        cast(QAction, menu.addAction("Unpin")).triggered.connect(unpin_item)
        menu.addSeparator()
        cast(QAction, menu.addAction("Clear List")).triggered.connect(source_widget.clear)

        view_port: QWidget | None = source_widget.viewport()
        assert view_port is not None
        menu.popup(view_port.mapToGlobal(point))

    def on_tree_context_menu(
        self,
        point: QPoint,
    ):
        """Displays context menu for tree items."""
        index: QModelIndex = self.ui.dialogTree.indexAt(point)
        item: DLGStandardItem | None = self.model.itemFromIndex(index)
        if item is not None:
            menu: QMenu = self._get_link_context_menu(self.ui.dialogTree, item)
        else:
            menu = QMenu(self)
            if not self._focused:
                cast(QAction, menu.addAction("Add Entry")).triggered.connect(self.model.add_root_node)
            else:

                def reset_tree(*args):
                    self._load_dlg(self.core_dlg)

                cast(QAction, menu.addAction("Reset Tree")).triggered.connect(reset_tree)
        view_port: QWidget | None = self.ui.dialogTree.viewport()
        assert view_port is not None
        menu.popup(view_port.mapToGlobal(point))

    def set_expand_recursively(  # noqa: PLR0913, C901
        self,
        item: DLGStandardItem,
        seen_nodes: set[DLGNode],
        *,
        expand: bool,
        maxdepth: int = 11,
        depth: int = 0,
        is_root: bool = True,
    ):
        """Recursively expand/collapse all children of the given item."""
        if depth > maxdepth >= 0:
            return
        item_index: QModelIndex = item.index()
        if not item_index.isValid():
            return
        if not isinstance(item, DLGStandardItem):
            return  # future expand dummy
        if item.link is None:
            return
        link: DLGLink = item.link
        if link.node in seen_nodes:
            return
        seen_nodes.add(link.node)
        if expand:
            self.ui.dialogTree.expand(item_index)
        elif not is_root:
            self.ui.dialogTree.collapse(item_index)
        for row in range(item.rowCount()):
            child_item: DLGStandardItem = cast(DLGStandardItem, item.child(row))
            if child_item is None:
                continue
            child_index: QModelIndex = child_item.index()
            if not child_index.isValid():
                continue
            self.set_expand_recursively(child_item, seen_nodes, expand=expand, maxdepth=maxdepth, depth=depth + 1, is_root=False)

    def _get_link_context_menu(  # noqa: PLR0915, C901
        self,
        source_widget: DLGListWidget | DLGTreeView,
        item: DLGStandardItem | DLGListWidgetItem,
    ) -> QMenu:
        """Sets context menu actions for a dialog tree item."""
        self._check_clipboard_for_json_node()
        not_an_orphan: bool = source_widget is not self.orphaned_nodes_list
        assert item.link is not None
        node_type: Literal["Entry", "Reply"] = "Entry" if isinstance(item.link.node, DLGEntry) else "Reply"
        other_node_type: Literal["Entry", "Reply"] = "Reply" if isinstance(item.link.node, DLGEntry) else "Entry"

        menu = QMenu(source_widget)

        # Actions for both list widget and tree view
        edit_text_action: QAction | None = menu.addAction("Edit Text")
        assert edit_text_action is not None
        edit_text_action.triggered.connect(lambda *args: self.edit_text(indexes=source_widget.selectedIndexes(), source_widget=source_widget))
        edit_text_action.setShortcut(QKeySequence(Qt.Key.Key_Enter, Qt.Key.Key_Return))

        focus_action: QAction | None = menu.addAction("Focus")
        assert focus_action is not None
        focus_action.triggered.connect(lambda: self.focus_on_node(item.link))
        focus_action.setShortcut(QKeySequence(Qt.Key.Key_F))
        focus_action.setEnabled(bool(item.link.node.links))
        focus_action.setVisible(not_an_orphan)

        find_references_action: QAction | None = menu.addAction("Find References")
        assert find_references_action is not None
        find_references_action.triggered.connect(lambda: self.find_references(item))
        find_references_action.setVisible(not_an_orphan)

        # Play menu for both
        play_menu: QMenu | None = menu.addMenu("Play")
        assert play_menu is not None
        play_menu.mousePressEvent = lambda event: (print("play_menu.mousePressEvent"), self._play_node_sound(item.link.node), QMenu.mousePressEvent(play_menu, event))  # type: ignore[method-assign]
        play_sound_action: QAction | None = play_menu.addAction("Play Sound")
        assert play_sound_action is not None
        play_sound_action.triggered.connect(lambda: self.play_sound("" if item.link is None else str(item.link.node.sound)) and None or None)
        play_voice_action: QAction | None = play_menu.addAction("Play Voice")
        assert play_voice_action is not None
        play_voice_action.triggered.connect(lambda: self.play_sound("" if item.link is None else str(item.link.node.vo_resref)) and None or None)
        play_sound_action.setEnabled(bool(self.ui.soundComboBox.currentText().strip()))
        play_voice_action.setEnabled(bool(self.ui.voiceComboBox.currentText().strip()))
        play_menu.setEnabled(bool(self.ui.soundComboBox.currentText().strip() or self.ui.voiceComboBox.currentText().strip()))
        menu.addSeparator()

        # Copy actions for both
        copy_node_action: QAction | None = menu.addAction(f"Copy {node_type} to Clipboard")
        assert copy_node_action is not None
        copy_node_action.triggered.connect(lambda: self.model.copy_link_and_node(item.link))
        copy_node_action.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_C))

        copy_gff_path_action: QAction | None = menu.addAction("Copy GFF Path")
        assert copy_gff_path_action is not None
        copy_gff_path_action.triggered.connect(lambda: self.copy_path(None if item.link is None else item.link.node))
        copy_gff_path_action.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_C))
        copy_gff_path_action.setVisible(not_an_orphan)
        menu.addSeparator()

        if isinstance(source_widget, DLGTreeView):
            # Tree view only actions
            expand_all_children_action: QAction | None = menu.addAction("Expand All Children")
            assert expand_all_children_action is not None
            expand_all_children_action.triggered.connect(lambda: self.set_expand_recursively(item, set(), expand=True))  # pyright: ignore[reportArgumentType]
            expand_all_children_action.setShortcut(QKeySequence(Qt.Key.Key_Shift, Qt.Key.Key_Return))
            collapse_all_children_action: QAction | None = menu.addAction("Collapse All Children")
            assert collapse_all_children_action is not None

            def collapse_all_children(*args, item=item):
                if not isinstance(item, DLGStandardItem):
                    return
                self.set_expand_recursively(item, set(), expand=False)

            collapse_all_children_action.triggered.connect(collapse_all_children)
            collapse_all_children_action.setShortcut(QKeySequence(Qt.Key.Key_Shift | Qt.Key.Key_Alt | Qt.Key.Key_Return))
            menu.addSeparator()

            # Paste actions
            paste_link_action: QAction | None = menu.addAction(f"Paste {other_node_type} from Clipboard as Link")
            paste_new_action: QAction | None = menu.addAction(f"Paste {other_node_type} from Clipboard as Deep Copy")
            assert paste_link_action is not None
            assert paste_new_action is not None
            if self._copy is None:
                paste_link_action.setEnabled(False)
                paste_new_action.setEnabled(False)
            else:
                copied_node_type: Literal["Entry", "Reply"] = "Entry" if isinstance(self._copy.node, DLGEntry) else "Reply"
                paste_link_action.setText(f"Paste {copied_node_type} from Clipboard as Link")
                paste_new_action.setText(f"Paste {copied_node_type} from Clipboard as Deep Copy")
                if node_type == copied_node_type:
                    paste_link_action.setEnabled(False)
                    paste_new_action.setEnabled(False)

            paste_link_action.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_V))
            paste_link_action.triggered.connect(lambda: self.model.paste_item(item, as_new_branches=False))  # pyright: ignore[reportArgumentType]
            paste_new_action.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_V))

            def paste_new_handler():
                if not isinstance(item, DLGStandardItem):
                    return
                self.model.paste_item(item, as_new_branches=True)

            paste_new_action.triggered.connect(paste_new_handler)  # pyright: ignore[reportArgumentType, reportCallIssue]
            menu.addSeparator()

            # Add/Move actions
            add_node_action: QAction | None = menu.addAction(f"Add {other_node_type}")
            assert add_node_action is not None
            add_node_action.triggered.connect(lambda: self.model.add_child_to_item(item))  # pyright: ignore[reportArgumentType]
            add_node_action.setShortcut(Qt.Key.Key_Insert)
            menu.addSeparator()

            move_up_action: QAction | None = menu.addAction("Move Up")
            assert move_up_action is not None
            move_up_action.triggered.connect(lambda: self.model.shift_item(item, -1))  # pyright: ignore[reportArgumentType]
            move_up_action.setShortcut(QKeySequence(Qt.Key.Key_Shift, Qt.Key.Key_Up))
            move_down_action: QAction | None = menu.addAction("Move Down")
            assert move_down_action is not None
            move_down_action.triggered.connect(lambda: self.model.shift_item(item, 1))  # pyright: ignore[reportArgumentType]
            move_down_action.setShortcut(QKeySequence(Qt.Key.Key_Shift, Qt.Key.Key_Down))
            menu.addSeparator()

            # Remove action
            remove_link_action: QAction | None = menu.addAction(f"Remove {node_type}")
            assert remove_link_action is not None
            remove_link_action.setShortcut(Qt.Key.Key_Delete)

            def on_remove_link(*args, item=item):
                if not isinstance(item, DLGStandardItem):
                    return
                self.model.remove_link(item)

            remove_link_action.triggered.connect(on_remove_link)  # pyright: ignore[reportArgumentType]
            menu.addSeparator()

        delete_all_references_action = QAction(f"Delete ALL References to {node_type}", menu)  # type: ignore[assignment]

        def delete_all_references(
            *args,
            item=item,
        ):
            if not isinstance(item, DLGStandardItem):
                return
            if item.link is None:
                return
            self.model.delete_node_everywhere(item.link.node)

        delete_all_references_action.triggered.connect(delete_all_references)  # pyright: ignore[reportOptionalMemberAccess]
        delete_all_references_action.setShortcut(QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Delete))
        delete_all_references_action.setVisible(not_an_orphan)
        menu.addAction(delete_all_references_action)

        return menu

    def _play_node_sound(
        self,
        node: DLGEntry | DLGReply,
    ):
        if str(node.sound).strip():
            self.play_sound(
                str(node.sound).strip(),
                [SearchLocation.SOUND, SearchLocation.VOICE],
            )
        elif str(node.vo_resref).strip():
            self.play_sound(str(node.vo_resref).strip(), [SearchLocation.VOICE])
        else:
            self.blink_window()

    def find_references(
        self,
        item: DLGStandardItem | DLGListWidgetItem,
    ):
        assert item.link is not None
        self.reference_history = self.reference_history[: self.current_reference_index + 1]
        item_html: str = item.data(Qt.ItemDataRole.DisplayRole)
        self.current_reference_index += 1
        references: list[weakref.ReferenceType] = [
            this_item.ref_to_link
            for link in self.model.link_to_items
            for this_item in self.model.link_to_items[link]
            if this_item.link is not None and item.link in this_item.link.node.links
        ]
        self.reference_history.append((references, item_html))
        self.show_reference_dialog(references, item_html)

    def get_item_dlg_paths(
        self,
        item: DLGStandardItem | DLGListWidgetItem,
    ) -> tuple[str, str, str]:
        link_parent_path = item.data(_LINK_PARENT_NODE_PATH_ROLE)
        assert item.link is not None
        link_path: str = item.link.partial_path(is_starter=item.link in self.core_dlg.starters)
        linked_to_path: str = item.link.node.path()
        return link_parent_path, link_path, linked_to_path

    def show_reference_dialog(
        self,
        references: list[weakref.ref[DLGLink]],
        item_html: str,
    ):
        if self.dialog_references is None:
            self.dialog_references = ReferenceChooserDialog(references, self, item_html)
            self.dialog_references.item_chosen.connect(self.on_reference_chosen)
        else:
            self.dialog_references.update_references(references, item_html)
        if self.dialog_references.isHidden():
            self.dialog_references.show()

    def on_reference_chosen(
        self,
        item: DLGListWidgetItem,
    ):
        link: DLGLink[Any] = item.link
        self.jump_to_node(link)

    def jump_to_node(
        self,
        link: DLGLink | None,
    ):
        if link is None:
            return
        if link not in self.model.link_to_items:
            return
        item: DLGStandardItem = self.model.link_to_items[link][0]
        self.highlight_result(item)

    def navigate_back(self):
        if self.current_reference_index > 0:
            self.current_reference_index -= 1
            references, item_html = self.reference_history[self.current_reference_index]
            self.show_reference_dialog(references, item_html)

    def navigate_forward(self):
        if self.current_reference_index < len(self.reference_history) - 1:
            self.current_reference_index += 1
            references, item_html = self.reference_history[self.current_reference_index]
            self.show_reference_dialog(references, item_html)

    # region Events
    def focusOutEvent(
        self,
        e: QFocusEvent,
    ):  # pyright: ignore[reportIncompatibleMethodOverride]
        self.keys_down.clear()  # Clears the set when focus is lost
        super().focusOutEvent(e)  # Ensures that the default handler is still executed
        print("dlgedit.focusOutEvent: clearing all keys/buttons held down.")

    def closeEvent(
        self,
        event: QCloseEvent,
    ):
        super().closeEvent(event)
        self.media_player.player.stop()
        if self.ui.rightDockWidget.isVisible():
            self.ui.rightDockWidget.close()
        if self.ui.topDockWidget.isVisible():
            self.ui.topDockWidget.close()
        self.save_widget_states()

    def save_widget_states(self):
        """Iterates over child widgets and saves their geometry and state."""

    def _handle_shift_item_keybind(
        self,
        selected_index: QModelIndex,
        selected_item: DLGStandardItem,
        key: Qt.Key | int,
    ):
        # sourcery skip: extract-duplicate-method
        above_index: QModelIndex = self.ui.dialogTree.indexAbove(selected_index)
        below_index: QModelIndex = self.ui.dialogTree.indexBelow(selected_index)
        view_port: QWidget | None = self.ui.dialogTree.viewport()
        assert view_port is not None
        if self.keys_down in (
            {Qt.Key.Key_Shift, Qt.Key.Key_Up},
            {Qt.Key.Key_Shift, Qt.Key.Key_Up, Qt.Key.Key_Alt},
        ):
            if above_index.isValid():
                self.ui.dialogTree.setCurrentIndex(above_index)
            self.model.shift_item(selected_item, -1, no_selection_update=True)
        elif self.keys_down in (
            {Qt.Key.Key_Shift, Qt.Key.Key_Down},
            {Qt.Key.Key_Shift, Qt.Key.Key_Down, Qt.Key.Key_Alt},
        ):
            below_index: QModelIndex = self.ui.dialogTree.indexBelow(selected_index)

            if below_index.isValid():
                self.ui.dialogTree.setCurrentIndex(below_index)
            self.model.shift_item(selected_item, 1, no_selection_update=True)
        elif above_index.isValid() and key == Qt.Key.Key_Up and not self.ui.dialogTree.visualRect(above_index).contains(view_port.rect()):
            self.ui.dialogTree.scrollTo(above_index)
        elif below_index.isValid() and key == Qt.Key.Key_Down and not self.ui.dialogTree.visualRect(below_index).contains(view_port.rect()):
            self.ui.dialogTree.scrollTo(below_index)

    def keyPressEvent(  # noqa: PLR0912, C901, PLR0911, PLR0915
        self,
        event: QKeyEvent,
        *,
        is_tree_view_call: bool = False,
    ):  # sourcery skip: extract-duplicate-method
        if not is_tree_view_call:
            if not self.ui.dialogTree.hasFocus():
                super().keyPressEvent(event)
                return
            self.ui.dialogTree.keyPressEvent(event)  # this'll call us back immediately, just ensures we don't get called twice for the same event.
            return
        super().keyPressEvent(event)
        key: int = event.key()
        selected_index: QModelIndex = self.ui.dialogTree.currentIndex()
        if not selected_index.isValid():
            return

        selected_item: DLGStandardItem | None = self.model.itemFromIndex(selected_index)
        if selected_item is None:
            if key == Qt.Key.Key_Insert:
                self.model.add_root_node()
            return

        if event.isAutoRepeat() or key in self.keys_down:
            if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                self.keys_down.add(key)
                self._handle_shift_item_keybind(selected_index, selected_item, key)
            return  # Ignore auto-repeat events and prevent multiple executions on single key
        assert selected_item.link is not None
        if not self.keys_down:
            self.keys_down.add(key)
            if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                self.model.remove_link(selected_item)
            elif key in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                if self.ui.dialogTree.hasFocus():
                    self.edit_text(event, self.ui.dialogTree.selectedIndexes(), self.ui.dialogTree)
                elif self.orphaned_nodes_list.hasFocus():
                    self.edit_text(event, self.orphaned_nodes_list.selectedIndexes(), self.orphaned_nodes_list)
                elif self.pinned_items_list.hasFocus():
                    self.edit_text(event, self.pinned_items_list.selectedIndexes(), self.pinned_items_list)
                elif self.find_bar.hasFocus() or self.find_input.hasFocus():
                    self.handle_find()
            elif key == Qt.Key.Key_F:
                self.focus_on_node(selected_item.link)
            elif key == Qt.Key.Key_Insert:
                self.model.add_child_to_item(selected_item)
            elif key == Qt.Key.Key_P:
                sound_resname: str = self.ui.soundComboBox.currentText().strip()
                voice_resname: str = self.ui.voiceComboBox.currentText().strip()
                if sound_resname:
                    self.play_sound(sound_resname, [SearchLocation.SOUND, SearchLocation.VOICE])
                elif voice_resname:
                    self.play_sound(voice_resname, [SearchLocation.VOICE])
                else:
                    self.blink_window()
            return

        self.keys_down.add(key)
        self._handle_shift_item_keybind(selected_index, selected_item, key)
        if self.keys_down in (
            {Qt.Key.Key_Shift, Qt.Key.Key_Return},
            {Qt.Key.Key_Shift, Qt.Key.Key_Enter},
        ):
            self.set_expand_recursively(selected_item, set(), expand=True)
        elif self.keys_down in (
            {Qt.Key.Key_Shift, Qt.Key.Key_Return, Qt.Key.Key_Alt},
            {Qt.Key.Key_Shift, Qt.Key.Key_Enter, Qt.Key.Key_Alt},
        ):
            self.set_expand_recursively(selected_item, set(), expand=False, maxdepth=-1)
        elif Qt.Key.Key_Control in self.keys_down or bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if key == Qt.Key.Key_G:
                ...
                # self.show_go_to_bar()
            elif key == Qt.Key.Key_F:
                self.show_find_bar()
            elif Qt.Key.Key_C in self.keys_down:
                if Qt.Key.Key_Alt in self.keys_down:
                    self.copy_path(selected_item.link.node)
                else:
                    self.model.copy_link_and_node(selected_item.link)
            elif Qt.Key.Key_Enter in self.keys_down or Qt.Key.Key_Return in self.keys_down:
                if self.find_bar.hasFocus() or self.find_input.hasFocus():
                    self.handle_find()
                else:
                    self.jump_to_original(selected_item)
            elif Qt.Key.Key_V in self.keys_down:
                self._check_clipboard_for_json_node()
                if not self._copy:
                    print("No node/link copy in memory or on clipboard.")
                    self.blink_window()
                    return
                if self._copy.node.__class__ is selected_item.link.node.__class__:
                    print("Cannot paste link/node here.")
                    self.blink_window()
                    return
                self.model.paste_item(
                    selected_item,
                    as_new_branches=Qt.Key.Key_Alt in self.keys_down,
                )
            elif Qt.Key.Key_Delete in self.keys_down:
                if Qt.Key.Key_Shift in self.keys_down:
                    self.model.delete_node_everywhere(selected_item.link.node)
                else:
                    self.model.delete_selected_node()

    def keyReleaseEvent(
        self,
        event: QKeyEvent,
    ):
        super().keyReleaseEvent(event)
        key: int = event.key()

        if key in self.keys_down:
            self.keys_down.remove(key)

    def update_labels(self):  # noqa: C901, PLR0915
        def update_label(  # noqa: C901, PLR0912
            label: QLabel,
            widget: QWidget,
            default_value: int | str | tuple[int | str, ...],
        ):
            def is_default(value, default):
                return value in default if isinstance(default, tuple) else value == default

            font: QFont = label.font()
            if isinstance(widget, QCheckBox):
                is_default_value: bool = is_default(widget.isChecked(), default_value)
            elif isinstance(widget, QLineEdit):
                is_default_value = is_default(widget.text(), default_value)
            elif isinstance(widget, QPlainTextEdit):
                is_default_value = is_default(widget.toPlainText(), default_value)
            elif isinstance(widget, QComboBox):
                if isinstance(default_value, tuple):
                    # Iterate through the tuple to check both currentText and currentIndex based on the type of each element in the tuple
                    is_default_value = False
                    for d in default_value:
                        if isinstance(d, int) and is_default(widget.currentIndex(), d):
                            is_default_value = True
                            break
                        if isinstance(d, str) and is_default(widget.currentText(), d):
                            is_default_value = True
                            break
                elif isinstance(default_value, int):
                    is_default_value = is_default(widget.currentIndex(), default_value)
                elif isinstance(default_value, str):
                    is_default_value = is_default(widget.currentText(), default_value)
                else:
                    is_default_value = False
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                is_default_value = is_default(widget.value(), default_value)
            else:
                is_default_value = False
            original_text: str = label.text().replace("* ", "", 1)  # Remove any existing asterisk
            if not is_default_value:
                label.setText(f"* {original_text}")
                font.setWeight(QFont.Weight.Bold if qtpy.QT6 else 65)  # pyright: ignore[reportArgumentType]
            else:
                label.setText(original_text)
                font.setWeight(QFont.Weight.Normal)
            label.setFont(font)

        update_label(self.ui.speakerEditLabel, self.ui.speakerEdit, "")  # type: ignore[arg-type]
        update_label(self.ui.questLabel, self.ui.questEdit, "")  # type: ignore[arg-type]
        update_label(self.ui.plotXpPercentLabel, self.ui.plotXpSpin, 1)  # type: ignore[arg-type]
        update_label(self.ui.plotIndexLabel, self.ui.plotIndexCombo, -1)  # type: ignore[arg-type]
        update_label(self.ui.questEntryLabel, self.ui.questEntrySpin, 0)  # type: ignore[arg-type]
        update_label(self.ui.listenerTagLabel, self.ui.listenerEdit, "")  # type: ignore[arg-type]
        update_label(self.ui.script1Label, self.ui.script1ResrefEdit, "")  # type: ignore[arg-type]
        update_label(self.ui.script2Label, self.ui.script2ResrefEdit, "")  # type: ignore[arg-type]
        update_label(self.ui.conditional1Label, self.ui.condition1ResrefEdit, "")  # type: ignore[arg-type]
        update_label(self.ui.conditional2Label, self.ui.condition2ResrefEdit, "")  # type: ignore[arg-type]
        update_label(self.ui.emotionLabel, self.ui.emotionSelect, "[Modded Entry #0]")  # type: ignore[arg-type]
        update_label(self.ui.expressionLabel, self.ui.expressionSelect, "[Modded Entry #0]")  # type: ignore[arg-type]
        update_label(self.ui.soundLabel, self.ui.soundComboBox, "")  # type: ignore[arg-type]
        update_label(self.ui.voiceLabel, self.ui.voiceComboBox, "")  # type: ignore[arg-type]
        update_label(self.ui.cameraIdLabel, self.ui.cameraIdSpin, -1)  # type: ignore[arg-type]
        update_label(self.ui.cameraAnimLabel, self.ui.cameraAnimSpin, (0, -1))  # type: ignore[arg-type]
        update_label(self.ui.cameraVidEffectLabel, self.ui.cameraEffectSelect, -1)  # type: ignore[arg-type]
        update_label(self.ui.cameraAngleLabel, self.ui.cameraAngleSelect, "Auto")  # type: ignore[arg-type]
        update_label(self.ui.nodeIdLabel, self.ui.nodeIdSpin, (0, -1))  # type: ignore[arg-type]
        update_label(self.ui.alienRaceNodeLabel, self.ui.alienRaceNodeSpin, 0)  # type: ignore[arg-type]
        update_label(self.ui.postProcNodeLabel, self.ui.postProcSpin, 0)  # type: ignore[arg-type]
        update_label(self.ui.delayNodeLabel, self.ui.delaySpin, (0, -1))  # type: ignore[arg-type]
        update_label(self.ui.logicLabel, self.ui.logicSpin, 0)  # type: ignore[arg-type]
        update_label(self.ui.waitFlagsLabel, self.ui.waitFlagSpin, 0)  # type: ignore[arg-type]
        update_label(self.ui.fadeTypeLabel, self.ui.fadeTypeSpin, 0)  # type: ignore[arg-type]

    def handle_sound_checked(
        self,
        *args,
    ):
        if not self._node_loaded_into_ui:
            return
        if not self.ui.soundCheckbox.isChecked():
            # self.ui.soundComboBox.setDisabled(True)
            # self.ui.voiceComboBox.setDisabled(True)
            self.ui.soundButton.setDisabled(True)
            self.ui.soundButton.setToolTip("Exists must be checked.")
            # self.ui.soundComboBox.setToolTip("Exists must be checked.")
            # self.ui.voiceComboBox.setToolTip("Exists must be checked.")
        else:
            # self.ui.soundComboBox.setEnabled(True)
            # self.ui.voiceComboBox.setEnabled(True)
            self.ui.voiceButton.setEnabled(True)
            self.ui.voiceButton.setToolTip("")
            # self.ui.soundComboBox.setToolTip("")
            # self.ui.voiceComboBox.setToolTip("")

    def set_all_whats_this(self):  # noqa: PLR0915
        self.ui.actionNew.setWhatsThis("Create a new dialogue file")
        self.ui.actionOpen.setWhatsThis("Open an existing dialogue file")
        self.ui.actionSave.setWhatsThis("Save the current dialogue file")
        self.ui.actionSaveAs.setWhatsThis("Save the current dialogue file with a new name")
        self.ui.actionRevert.setWhatsThis("Revert changes to the last saved state")
        self.ui.actionExit.setWhatsThis("Exit the application")
        self.ui.actionReloadTree.setWhatsThis("Reload the dialogue tree")
        self.ui.actionUnfocus.setWhatsThis("Unfocus the current selection")

        self.ui.questEdit.setWhatsThis("Field: Quest\nType: String")
        self.ui.plotXpSpin.setWhatsThis("Field: PlotXPPercentage\nType: Float")
        self.ui.questEntryLabel.setWhatsThis("Label for Quest Entry field")
        self.ui.questLabel.setWhatsThis("Label for Quest field")
        self.ui.listenerEdit.setWhatsThis("Field: Listener\nType: String")
        self.ui.listenerTagLabel.setWhatsThis("Label for Listener Tag field")
        self.ui.speakerEdit.setWhatsThis("Field: Speaker\nType: String")
        self.ui.questEntrySpin.setWhatsThis("Field: QuestEntry\nType: Int32")
        self.ui.speakerEditLabel.setWhatsThis("Label for Speaker Tag field")
        self.ui.plotXpPercentLabel.setWhatsThis("Label for Plot XP Percentage field")
        self.ui.plotIndexLabel.setWhatsThis("Label for Plot Index field")
        self.ui.plotIndexCombo.setWhatsThis("Field: PlotIndex\nType: Int32")
        self.ui.commentsEdit.setWhatsThis("Field: Comment\nType: String")

        self.ui.script1Label.setWhatsThis("Field: Script1\nType: ResRef")
        self.ui.script2Label.setWhatsThis("Field: Script2\nType: ResRef")
        self.ui.script1ResrefEdit.setWhatsThis("Field: Script1\nType: ResRef")
        self.ui.script2ResrefEdit.setWhatsThis("Field: Script2\nType: ResRef")
        self.ui.script1Param1Spin.setWhatsThis("Field: ActionParam1\nType: Int32")
        self.ui.script1Param2Spin.setWhatsThis("Field: ActionParam2\nType: Int32")
        self.ui.script1Param3Spin.setWhatsThis("Field: ActionParam3\nType: Int32")
        self.ui.script1Param4Spin.setWhatsThis("Field: ActionParam4\nType: Int32")
        self.ui.script1Param5Spin.setWhatsThis("Field: ActionParam5\nType: Int32")
        self.ui.script1Param6Edit.setWhatsThis("Field: ActionParamStrA\nType: String")
        self.ui.script2Param1Spin.setWhatsThis("Field: ActionParam1b\nType: Int32")
        self.ui.script2Param2Spin.setWhatsThis("Field: ActionParam2b\nType: Int32")
        self.ui.script2Param3Spin.setWhatsThis("Field: ActionParam3b\nType: Int32")
        self.ui.script2Param4Spin.setWhatsThis("Field: ActionParam4b\nType: Int32")
        self.ui.script2Param5Spin.setWhatsThis("Field: ActionParam5b\nType: Int32")
        self.ui.script2Param6Edit.setWhatsThis("Field: ActionParamStrB\nType: String")
        self.ui.condition1ResrefEdit.setWhatsThis("Field: Active\nType: ResRef")
        self.ui.condition2ResrefEdit.setWhatsThis("Field: Active2\nType: ResRef")
        self.ui.condition1Param1Spin.setWhatsThis("Field: Param1\nType: Int32")
        self.ui.condition1Param2Spin.setWhatsThis("Field: Param2\nType: Int32")
        self.ui.condition1Param3Spin.setWhatsThis("Field: Param3\nType: Int32")
        self.ui.condition1Param4Spin.setWhatsThis("Field: Param4\nType: Int32")
        self.ui.condition1Param5Spin.setWhatsThis("Field: Param5\nType: Int32")
        self.ui.condition1Param6Edit.setWhatsThis("Field: ParamStrA\nType: String")
        self.ui.condition2Param1Spin.setWhatsThis("Field: Param1b\nType: Int32")
        self.ui.condition2Param2Spin.setWhatsThis("Field: Param2b\nType: Int32")
        self.ui.condition2Param3Spin.setWhatsThis("Field: Param3b\nType: Int32")
        self.ui.condition2Param4Spin.setWhatsThis("Field: Param4b\nType: Int32")
        self.ui.condition2Param5Spin.setWhatsThis("Field: Param5b\nType: Int32")
        self.ui.condition2Param6Edit.setWhatsThis("Field: ParamStrB\nType: String")
        self.ui.condition1NotCheckbox.setWhatsThis("Field: Not\nType: UInt8 (boolean)")
        self.ui.condition2NotCheckbox.setWhatsThis("Field: Not2\nType: UInt8 (boolean)")
        self.ui.emotionSelect.setWhatsThis("Field: Emotion\nType: Int32")
        self.ui.expressionSelect.setWhatsThis("Field: FacialAnim\nType: Int32")
        self.ui.nodeIdSpin.setWhatsThis("Field: NodeID\nType: Int32")
        self.ui.nodeUnskippableCheckbox.setWhatsThis("Field: NodeUnskippable\nType: UInt8 (boolean)")
        self.ui.postProcSpin.setWhatsThis("Field: PostProcNode\nType: Int32")
        self.ui.alienRaceNodeSpin.setWhatsThis("Field: AlienRaceNode\nType: Int32")
        self.ui.delaySpin.setWhatsThis("Field: Delay\nType: Int32")
        self.ui.logicSpin.setWhatsThis("Field: Logic\nType: Int32")
        self.ui.waitFlagSpin.setWhatsThis("Field: WaitFlags\nType: Int32")
        self.ui.fadeTypeSpin.setWhatsThis("Field: FadeType\nType: Int32")
        self.ui.soundCheckbox.setWhatsThis("Field: SoundExists\nType: UInt8 (boolean)")
        self.ui.soundComboBox.setWhatsThis("Field: Sound\nType: ResRef")
        self.ui.soundButton.setWhatsThis("Play the selected sound")
        self.ui.voiceComboBox.setWhatsThis("Field: VO_ResRef\nType: ResRef")
        self.ui.voiceButton.setWhatsThis("Play the selected voice")
        self.ui.addAnimButton.setWhatsThis("Add a new animation")
        self.ui.removeAnimButton.setWhatsThis("Remove the selected animation")
        self.ui.editAnimButton.setWhatsThis("Edit the selected animation")
        self.ui.animsList.setWhatsThis("List of current animations")
        self.ui.cameraIdSpin.setWhatsThis("Field: CameraID\nType: Int32")
        self.ui.cameraAnimSpin.setWhatsThis("Field: CameraAnimation\nType: Int32")
        self.ui.cameraAngleSelect.setWhatsThis("Field: CameraAngle\nType: Int32")
        self.ui.cameraEffectSelect.setWhatsThis("Field: CamVidEffect\nType: Int32")
        self.ui.cutsceneModelLabel.setWhatsThis("Label for Cutscene Model field")
        self.ui.addStuntButton.setWhatsThis("Add a new stunt")
        self.ui.removeStuntButton.setWhatsThis("Remove the selected stunt")
        self.ui.editStuntButton.setWhatsThis("Edit the selected stunt")
        self.ui.cameraModelSelect.setWhatsThis("Field: CameraModel\nType: ResRef")
        self.ui.oldHitCheckbox.setWhatsThis("Field: OldHitCheck\nType: UInt8 (boolean)")

        self.ui.ambientTrackCombo.setWhatsThis("Field: AmbientTrack\nType: ResRef")
        self.ui.voiceOverIDLabel.setWhatsThis("Label for Voiceover ID field")
        self.ui.computerTypeLabel.setWhatsThis("Label for Computer Type field")
        self.ui.conversationSelect.setWhatsThis("Field: ConversationType\nType: Int32")
        self.ui.computerSelect.setWhatsThis("Field: ComputerType\nType: Int32")
        self.ui.onAbortCombo.setWhatsThis("Field: EndConverAbort\nType: ResRef")
        self.ui.convoEndsScriptLabel.setWhatsThis("Label for Conversation Ends script")
        self.ui.convoTypeLabel.setWhatsThis("Label for Conversation Type field\nBIF dialogs use Type 3.")
        self.ui.ambientTrackLabel.setWhatsThis("Label for Ambient Track field")
        self.ui.convoAbortsScriptLabel.setWhatsThis("Label for Conversation Aborts script")
        self.ui.voIdEdit.setWhatsThis("Field: VO_ID\nType: String")
        self.ui.onEndEdit.setWhatsThis("Field: EndConversation\nType: ResRef")
        self.ui.delayEntryLabel.setWhatsThis("Label for Delay Entry field")
        self.ui.replyDelaySpin.setWhatsThis("Field: DelayReply\nType: Int32")
        self.ui.delayReplyLabel.setWhatsThis("Label for Delay Reply field")
        self.ui.entryDelaySpin.setWhatsThis("Field: DelayEntry\nType: Int32")
        self.ui.skippableCheckbox.setWhatsThis("Field: Skippable\nType: UInt8 (boolean)")
        self.ui.unequipHandsCheckbox.setWhatsThis("Field: UnequipHItem\nType: UInt8 (boolean)")
        self.ui.unequipAllCheckbox.setWhatsThis("Field: UnequipItems\nType: UInt8 (boolean)")
        self.ui.animatedCutCheckbox.setWhatsThis("Field: AnimatedCut\nType: Int32")

    def setup_extra_tooltip_mode(
        self,
        widget: QWidget | None = None,
    ):
        if widget is None:
            widget = self
        for child in widget.findChildren(QWidget):
            whats_this_text: str = child.whatsThis()
            if not whats_this_text or not whats_this_text.strip():
                continue
            if (
                "<br>" in child.toolTip()
            ):  # FIXME(th3w1zard1): existing html tooltips for some reason become plaintext when setToolTip is called more than once.  # noqa: TD003
                continue
            if child not in self.original_tooltips:
                self.original_tooltips[child] = child.toolTip()
            original_tooltip: str = self.original_tooltips[child]
            new_tooltip: str = whats_this_text
            if original_tooltip and original_tooltip.strip():
                new_tooltip += f"\n\n{original_tooltip}"

            child.setToolTip(new_tooltip)

    def on_selection_changed(  # noqa: PLR0915
        self,
        selection: QItemSelection,
    ):
        """Updates UI fields based on selected dialog node."""
        if self.model.ignoring_updates:
            return
        self._node_loaded_into_ui = False
        selection_indices: list[QModelIndex] = selection.indexes()
        if not selection_indices:
            return
        for index in selection_indices:
            item: DLGStandardItem | None = self.model.itemFromIndex(index)

            assert item is not None
            assert item.link is not None
            self.ui.condition1ResrefEdit.set_combo_box_text(str(item.link.active1))
            self.ui.condition1Param1Spin.setValue(item.link.active1_param1)
            self.ui.condition1Param2Spin.setValue(item.link.active1_param2)
            self.ui.condition1Param3Spin.setValue(item.link.active1_param3)
            self.ui.condition1Param4Spin.setValue(item.link.active1_param4)
            self.ui.condition1Param5Spin.setValue(item.link.active1_param5)
            self.ui.condition1Param6Edit.setText(item.link.active1_param6)
            self.ui.condition1NotCheckbox.setChecked(item.link.active1_not)
            self.ui.condition2ResrefEdit.set_combo_box_text(str(item.link.active2))
            self.ui.condition2Param1Spin.setValue(item.link.active2_param1)
            self.ui.condition2Param2Spin.setValue(item.link.active2_param2)
            self.ui.condition2Param3Spin.setValue(item.link.active2_param3)
            self.ui.condition2Param4Spin.setValue(item.link.active2_param4)
            self.ui.condition2Param5Spin.setValue(item.link.active2_param5)
            self.ui.condition2Param6Edit.setText(item.link.active2_param6)
            self.ui.condition2NotCheckbox.setChecked(item.link.active2_not)

            if isinstance(item.link.node, DLGEntry):
                self.ui.speakerEditLabel.setVisible(True)
                self.ui.speakerEdit.setVisible(True)
                self.ui.speakerEdit.setText(item.link.node.speaker)
            elif isinstance(item.link.node, DLGReply):
                self.ui.speakerEditLabel.setVisible(False)
                self.ui.speakerEdit.setVisible(False)
            else:
                raise TypeError(f"Node was type {item.link.node.__class__.__name__} ({item.link.node}), expected DLGEntry/DLGReply")

            self.ui.listenerEdit.setText(item.link.node.listener)

            self.ui.script1ResrefEdit.set_combo_box_text(str(item.link.node.script1))
            self.ui.script1Param1Spin.setValue(item.link.node.script1_param1)
            self.ui.script1Param2Spin.setValue(item.link.node.script1_param2)
            self.ui.script1Param3Spin.setValue(item.link.node.script1_param3)
            self.ui.script1Param4Spin.setValue(item.link.node.script1_param4)
            self.ui.script1Param5Spin.setValue(item.link.node.script1_param5)
            self.ui.script1Param6Edit.setText(item.link.node.script1_param6)
            self.ui.script2ResrefEdit.set_combo_box_text(str(item.link.node.script2))
            self.ui.script2Param1Spin.setValue(item.link.node.script2_param1)
            self.ui.script2Param2Spin.setValue(item.link.node.script2_param2)
            self.ui.script2Param3Spin.setValue(item.link.node.script2_param3)
            self.ui.script2Param4Spin.setValue(item.link.node.script2_param4)
            self.ui.script2Param5Spin.setValue(item.link.node.script2_param5)
            self.ui.script2Param6Edit.setText(item.link.node.script2_param6)

            self.refresh_anim_list()
            self.ui.emotionSelect.setCurrentIndex(item.link.node.emotion_id)
            self.ui.expressionSelect.setCurrentIndex(item.link.node.facial_id)
            self.ui.soundCheckbox.setChecked(bool(item.link.node.sound_exists))
            self.ui.soundComboBox.set_combo_box_text(str(item.link.node.sound))
            self.ui.voiceComboBox.set_combo_box_text(str(item.link.node.vo_resref))

            self.ui.plotIndexCombo.setCurrentIndex(item.link.node.plot_index)
            self.ui.plotXpSpin.setValue(item.link.node.plot_xp_percentage)
            self.ui.questEdit.setText(item.link.node.quest)
            self.ui.questEntrySpin.setValue(item.link.node.quest_entry or 0)

            self.ui.cameraIdSpin.setValue(-1 if item.link.node.camera_id is None else item.link.node.camera_id)
            self.ui.cameraAnimSpin.setValue(-1 if item.link.node.camera_anim is None else item.link.node.camera_anim)

            self.ui.cameraAngleSelect.setCurrentIndex(0 if item.link.node.camera_angle is None else item.link.node.camera_angle)
            self.ui.cameraEffectSelect.setCurrentIndex(-1 if item.link.node.camera_effect is None else item.link.node.camera_effect)

            self.ui.nodeUnskippableCheckbox.setChecked(item.link.node.unskippable)
            self.ui.nodeIdSpin.setValue(item.link.node.node_id)
            self.ui.alienRaceNodeSpin.setValue(item.link.node.alien_race_node)
            self.ui.postProcSpin.setValue(item.link.node.post_proc_node)
            self.ui.delaySpin.setValue(item.link.node.delay)
            self.ui.logicSpin.setValue(item.link.logic)
            self.ui.waitFlagSpin.setValue(item.link.node.wait_flags)
            self.ui.fadeTypeSpin.setValue(item.link.node.fade_type)

            self.ui.commentsEdit.setPlainText(item.link.node.comment)
            self.update_labels()
            self.handle_sound_checked()
        self._node_loaded_into_ui = True

    def on_node_update(  # noqa: PLR0915, C901, PLR0912
        self,
        *args,
        **kwargs,
    ):
        """Updates node properties based on UI selections."""
        if not self._node_loaded_into_ui:
            return
        selected_indices: list[QModelIndex] = self.ui.dialogTree.selectedIndexes()
        if not selected_indices:
            return
        for index in selected_indices:
            if not index.isValid():
                RobustLogger().warning("onNodeUpdate: index invalid")
                continue
            item: DLGStandardItem | None = self.model.itemFromIndex(index)
            if item is None or item.isDeleted():
                RobustLogger().warning("onNodeUpdate: no item for this selected index, or item was deleted.")
                continue
            assert item.link is not None, "onNodeUpdate: item.link was None"

            item.link.active1 = ResRef(self.ui.condition1ResrefEdit.currentText())
            item.link.active1_param1 = self.ui.condition1Param1Spin.value()
            item.link.active1_param2 = self.ui.condition1Param2Spin.value()
            item.link.active1_param3 = self.ui.condition1Param3Spin.value()
            item.link.active1_param4 = self.ui.condition1Param4Spin.value()
            item.link.active1_param5 = self.ui.condition1Param5Spin.value()
            item.link.active1_param6 = self.ui.condition1Param6Edit.text()
            item.link.active1_not = self.ui.condition1NotCheckbox.isChecked()
            item.link.active2 = ResRef(self.ui.condition2ResrefEdit.currentText())
            item.link.active2_param1 = self.ui.condition2Param1Spin.value()
            item.link.active2_param2 = self.ui.condition2Param2Spin.value()
            item.link.active2_param3 = self.ui.condition2Param3Spin.value()
            item.link.active2_param4 = self.ui.condition2Param4Spin.value()
            item.link.active2_param5 = self.ui.condition2Param5Spin.value()
            item.link.active2_param6 = self.ui.condition2Param6Edit.text()
            item.link.active2_not = self.ui.condition2NotCheckbox.isChecked()
            item.link.logic = bool(self.ui.logicSpin.value())

            item.link.node.listener = self.ui.listenerEdit.text()
            if isinstance(item.link.node, DLGEntry):
                item.link.node.speaker = self.ui.speakerEdit.text()
            item.link.node.script1 = ResRef(self.ui.script1ResrefEdit.currentText())
            item.link.node.script1_param1 = self.ui.script1Param1Spin.value()
            item.link.node.script1_param2 = self.ui.script1Param2Spin.value()
            item.link.node.script1_param3 = self.ui.script1Param3Spin.value()
            item.link.node.script1_param4 = self.ui.script1Param4Spin.value()
            item.link.node.script1_param5 = self.ui.script1Param5Spin.value()
            item.link.node.script1_param6 = self.ui.script1Param6Edit.text()
            item.link.node.script2 = ResRef(self.ui.script2ResrefEdit.currentText())
            item.link.node.script2_param1 = self.ui.script2Param1Spin.value()
            item.link.node.script2_param2 = self.ui.script2Param2Spin.value()
            item.link.node.script2_param3 = self.ui.script2Param3Spin.value()
            item.link.node.script2_param4 = self.ui.script2Param4Spin.value()
            item.link.node.script2_param5 = self.ui.script2Param5Spin.value()
            item.link.node.script2_param6 = self.ui.script2Param6Edit.text()

            item.link.node.emotion_id = self.ui.emotionSelect.currentIndex()
            item.link.node.facial_id = self.ui.expressionSelect.currentIndex()
            item.link.node.sound = ResRef(self.ui.soundComboBox.currentText())
            item.link.node.sound_exists = self.ui.soundCheckbox.isChecked()
            item.link.node.vo_resref = ResRef(self.ui.voiceComboBox.currentText())

            item.link.node.plot_index = self.ui.plotIndexCombo.currentIndex()
            item.link.node.plot_xp_percentage = self.ui.plotXpSpin.value()
            item.link.node.quest = self.ui.questEdit.text()
            item.link.node.quest_entry = self.ui.questEntrySpin.value()

            item.link.node.camera_id = self.ui.cameraIdSpin.value()
            item.link.node.camera_anim = self.ui.cameraAnimSpin.value()
            item.link.node.camera_angle = self.ui.cameraAngleSelect.currentIndex()
            item.link.node.camera_effect = self.ui.cameraEffectSelect.currentData()

            if item.link.node.camera_id >= 0 and item.link.node.camera_angle == 0:
                self.ui.cameraAngleSelect.setCurrentIndex(6)
            elif item.link.node.camera_id == -1 and item.link.node.camera_angle == 7:  # noqa: PLR2004
                self.ui.cameraAngleSelect.setCurrentIndex(0)

            item.link.node.unskippable = self.ui.nodeUnskippableCheckbox.isChecked()
            item.link.node.node_id = self.ui.nodeIdSpin.value()
            item.link.node.alien_race_node = self.ui.alienRaceNodeSpin.value()
            item.link.node.post_proc_node = self.ui.postProcSpin.value()
            item.link.node.delay = self.ui.delaySpin.value()
            item.link.node.wait_flags = self.ui.waitFlagSpin.value()
            item.link.node.fade_type = self.ui.fadeTypeSpin.value()
            item.link.node.comment = self.ui.commentsEdit.toPlainText()
            self.update_labels()
            self.handle_sound_checked()
            self.model.sig_core_dlg_item_data_changed.emit(item)
            if not self.ui.cameraModelSelect.currentText() or not self.ui.cameraModelSelect.currentText().strip():
                self.ui.cameraAnimSpin.blockSignals(True)
                self.ui.cameraAnimSpin.setValue(-1)
                self.ui.cameraAnimSpin.blockSignals(False)
                self.ui.cameraAnimSpin.setDisabled(True)
                self.ui.cameraAnimSpin.setToolTip("You must setup your custom `CameraModel` first (in the 'File Globals' dockpanel at the top.)")
            elif self.ui.cameraAngleSelect.currentText() != "Animated Camera":
                self.ui.cameraAnimSpin.blockSignals(True)
                self.ui.cameraAnimSpin.setValue(-1)
                self.ui.cameraAnimSpin.blockSignals(False)
                self.ui.cameraAnimSpin.setDisabled(True)
                self.ui.cameraAnimSpin.setToolTip("CameraAngle must be set to 'Animated' to use this feature.")
            else:
                self.ui.cameraAnimSpin.setDisabled(False)
                self.ui.cameraAnimSpin.setToolTip("")

            if self.ui.cameraIdSpin.value() == -1 and self.ui.cameraAngleSelect.currentText() == "Static Camera":
                self.ui.cameraIdSpin.setStyleSheet("QSpinBox { color: red; }")
                self.ui.cameraIdLabel.setStyleSheet("QLabel { color: red; }")
                self.ui.cameraAngleSelect.setStyleSheet("QComboBox { color: red; }")
                self.ui.cameraAngleLabel.setStyleSheet("QLabel { color: red; }")
                self.ui.cameraIdSpin.setToolTip("A Camera ID must be defined for Static Cameras.")
                self.ui.cameraAngleSelect.setToolTip("A Camera ID must be defined for Static Cameras.")
            else:
                self.ui.cameraIdSpin.setStyleSheet("")
                self.ui.cameraAngleSelect.setStyleSheet("")
                self.ui.cameraAngleLabel.setStyleSheet("")
                self.ui.cameraIdLabel.setStyleSheet("")
                self.ui.cameraIdSpin.setToolTip("")
                self.ui.cameraAngleSelect.setToolTip("")

    def on_item_expanded(
        self,
        index: QModelIndex,
    ):
        # self.ui.dialogTree.model().layoutAboutToBeChanged.emit()  # emitting this causes annoying ui jitter as it resizes.
        item: DLGStandardItem | None = self.model.itemFromIndex(index)
        assert item is not None
        if not item.is_loaded():
            self._fully_load_future_expand_item(item)
        self.ui.dialogTree.debounce_layout_changed(pre_change_emit=False)

    def _fully_load_future_expand_item(
        self,
        item: DLGStandardItem,
    ):
        self.model.ignoring_updates = True
        item.removeRow(0)  # Remove the placeholder dummy
        assert item.link is not None
        for child_link in item.link.node.links:
            child_item = DLGStandardItem(link=child_link)
            item.appendRow(child_item)
            self.model.load_dlg_item_rec(child_item)
        self.model.ignoring_updates = False

    def on_add_stunt_clicked(self):
        dialog = CutsceneModelDialog(self)
        if dialog.exec():
            self.core_dlg.stunts.append(dialog.stunt())
            self.refresh_stunt_list()

    def on_remove_stunt_clicked(self):
        sel_stunt_items: list[QListWidgetItem] = self.ui.stuntList.selectedItems()
        if not sel_stunt_items:
            QMessageBox(QMessageBox.Icon.Information, "No stunts selected", "Select an existing stunt from the above list first, or create one.").exec()
            return
        stunt: DLGStunt = sel_stunt_items[0].data(Qt.ItemDataRole.UserRole)
        self.core_dlg.stunts.remove(stunt)
        self.refresh_stunt_list()

    def on_edit_stunt_clicked(self):
        selected_stunt_items: list[QListWidgetItem] = self.ui.stuntList.selectedItems()
        if not selected_stunt_items:
            QMessageBox(QMessageBox.Icon.Information, "No stunts selected", "Select an existing stunt from the above list first, or create one.").exec()
            return
        stunt: DLGStunt = selected_stunt_items[0].data(Qt.ItemDataRole.UserRole)
        dialog = CutsceneModelDialog(self, stunt)
        if dialog.exec():
            stunt.stunt_model = dialog.stunt().stunt_model
            stunt.participant = dialog.stunt().participant
            self.refresh_stunt_list()

    def refresh_stunt_list(self):
        self.ui.stuntList.clear()
        for stunt in self.core_dlg.stunts:
            text: str = f"{stunt.stunt_model} ({stunt.participant})"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, stunt)
            self.ui.stuntList.addItem(item)  # pyright: ignore[reportArgumentType, reportCallIssue]

    def on_add_anim_clicked(self):
        selectedIndexes: list[QModelIndex] = self.ui.dialogTree.selectedIndexes()
        if not selectedIndexes:
            QMessageBox(QMessageBox.Icon.Information, "No nodes selected", "Select an item from the tree first.").exec()
            return
        item: DLGStandardItem | None = self.model.itemFromIndex(self.ui.dialogTree.selectedIndexes()[0])
        dialog = EditAnimationDialog(self, self._installation)
        if dialog.exec():
            assert item is not None
            assert item.link is not None
            item.link.node.animations.append(dialog.animation())
            self.refresh_anim_list()

    def on_remove_anim_clicked(self):
        selected_tree_indexes: list[QModelIndex] = self.ui.dialogTree.selectedIndexes()
        if not selected_tree_indexes:
            QMessageBox(QMessageBox.Icon.Information, "No nodes selected", "Select an item from the tree first.").exec()
            return
        selected_anim_items: list[QListWidgetItem] = self.ui.animsList.selectedItems()
        if not selected_anim_items:
            QMessageBox(QMessageBox.Icon.Information, "No animations selected", "Select an existing animation from the above list first, or create one.").exec()
            return
        sel_item: DLGStandardItem | None = self.model.itemFromIndex(selected_tree_indexes[0])
        if sel_item is None or sel_item.isDeleted() or sel_item.link is None:
            self.blink_window()
            return
        sel_item.link.node.animations.remove(selected_anim_items[0].data(Qt.ItemDataRole.UserRole))
        self.refresh_anim_list()

    def on_edit_anim_clicked(self):
        selected_tree_indexes: list[QModelIndex] = self.ui.dialogTree.selectedIndexes()
        if not selected_tree_indexes:
            QMessageBox(QMessageBox.Icon.Information, "No nodes selected", "Select an item from the tree first.").exec()
            return
        selected_anim_items: list[QListWidgetItem] = self.ui.animsList.selectedItems()
        if not selected_anim_items:
            QMessageBox(QMessageBox.Icon.Information, "No animations selected", "Select an existing animation from the above list first.").exec()
            return
        anim_item: QListWidgetItem = selected_anim_items[0]  # type: ignore[arg-type]
        anim: DLGAnimation = anim_item.data(Qt.ItemDataRole.UserRole)
        dialog = EditAnimationDialog(self, self._installation, anim)
        if dialog.exec():
            anim.animation_id = dialog.animation().animation_id
            anim.participant = dialog.animation().participant
            self.refresh_anim_list()

    def refresh_anim_list(self):
        """Refreshes the animations list."""
        self.ui.animsList.clear()
        animations_2da: TwoDA | None = self._installation.ht_get_cache_2da(HTInstallation.TwoDA_DIALOG_ANIMS)
        if animations_2da is None:
            RobustLogger().error(f"refreshAnimList: {HTInstallation.TwoDA_DIALOG_ANIMS}.2da not found, the Animation List will not function!!")
            return

        for index in self.ui.dialogTree.selectedIndexes():
            if not index.isValid():
                continue
            item: DLGStandardItem | None = self.model.itemFromIndex(index)
            if item is None or item.link is None:
                continue
            for anim in item.link.node.animations:
                name: str = str(anim.animation_id)
                if animations_2da.get_height() > anim.animation_id:
                    name = animations_2da.get_cell(anim.animation_id, "name")
                text: str = f"{name} ({anim.participant})"
                anim_item = QListWidgetItem(text)
                anim_item.setData(Qt.ItemDataRole.UserRole, anim)
                self.ui.animsList.addItem(anim_item)  # pyright: ignore[reportArgumentType, reportCallIssue]
