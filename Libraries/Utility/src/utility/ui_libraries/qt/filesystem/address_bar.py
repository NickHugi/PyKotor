from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from qtpy.QtCore import Qt, Signal  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtWidgets import QAction, QLineEdit, QMenu, QSizePolicy, QStyle, QToolBar, QToolButton

from utility.ui_libraries.qt.debug.print_qobject import print_qt_class_calls

if TYPE_CHECKING:
    from qtpy.QtGui import QFocusEvent, QIcon, QMouseEvent
    from qtpy.QtWidgets import QWidget


@print_qt_class_calls()
class PathButton(QToolButton):
    path_selected = Signal(Path)

    def __init__(self, path: Path, parent: QWidget | None = None, *, is_last: bool = False):
        super().__init__(parent)
        self.path = path
        self.is_last = is_last
        self.setText(path.name or str(path))
        self.clicked.connect(self._on_clicked)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        if not is_last:
            self.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
            self.setMenu(QMenu(self))

    def _on_clicked(self, checked: bool = False):  # noqa: FBT001, FBT002
        if not self.menu() or self.menu().isEmpty():
            self.path_selected.emit(self.path)

    def set_icon(self, icon: QIcon):
        self.setIcon(icon)

    def set_menu_items(self, contents: list[tuple[str, Path, QIcon]]):
        menu = self.menu()
        if menu is None:
            menu = QMenu(self)
        menu.clear()
        for name, path, icon in contents:
            action = QAction(icon, name, menu)
            action.triggered.connect(lambda _, p=path: self.path_selected.emit(p))
            menu.addAction(action)
        self.setMenu(menu)


@print_qt_class_calls()
class PyQAddressBar(QToolBar):
    path_changed: Signal = Signal(Path)
    editing_finished: Signal = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.current_path: Path = Path.home()
        self.buttons: list[PathButton] = []
        self.edit_mode: bool = False
        self.history: list[Path] = [self.current_path]  # Initialize with current path
        self.history_index: int = 0  # Set initial index to 0

        self.setMovable(False)
        self.setFloatable(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)

        # Add navigation buttons
        self.back_button: QAction = self.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack), "Back")
        self.back_button.triggered.connect(self.go_back)

        self.forward_button: QAction = self.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward), "Forward")
        self.forward_button.triggered.connect(self.go_forward)

        self.up_button: QAction = self.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp), "Up")
        self.up_button.triggered.connect(self.go_up)

        self.addSeparator()

        self.line_edit: QLineEdit = QLineEdit(self)
        self.line_edit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.line_edit.hide()
        self.line_edit.editingFinished.connect(self._on_editing_finished)
        self.addWidget(self.line_edit)

        self.setMouseTracking(True)
        self.setToolTipDuration(10000)
        self.setToolTip("AddressBar")
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def create_path_button(self, path: Path, *, is_last: bool = False) -> PathButton:
        button = PathButton(path, self, is_last=is_last)
        button.path_selected.connect(self._on_path_selected)
        self.buttons.append(button)
        self.addWidget(button)
        return button

    def update_path(self, path: Path):
        new_path = path.resolve()
        if new_path != self.current_path:
            self._update_history(new_path)

        self.current_path = new_path
        self.line_edit.setText(str(self.current_path))
        for button in self.buttons:
            button.deleteLater()
        self.buttons.clear()

        paths = list(reversed([self.current_path, *dict.fromkeys(self.current_path.parents)]))
        for i, current_path in enumerate(paths):
            is_last = i == len(paths) - 1
            button = self.create_path_button(current_path, is_last=is_last)
            if not is_last and i > 0:
                self.addSeparator()

        self.toggle_edit_mode(False)  # noqa: FBT003
        self.update_navigation_buttons()
        self.updateGeometry()
        self.update()

    def _update_history(self, new_path: Path):
        if self.history_index == -1 or self.history[self.history_index] != new_path:
            self.history = self.history[: self.history_index + 1]
            self.history.append(new_path)
            self.history_index = len(self.history) - 1
        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.back_button.setEnabled(self.history_index > 0)
        self.forward_button.setEnabled(self.history_index < len(self.history) - 1)
        self.up_button.setEnabled(self.current_path != self.current_path.root)

    def toggle_edit_mode(self, edit_mode: bool):  # noqa: FBT001
        self.edit_mode = edit_mode
        if edit_mode:
            for button in self.buttons:
                button.hide()
            self.line_edit.show()
            self.line_edit.setFocus()
            self.line_edit.selectAll()
        else:
            self.line_edit.hide()
            for button in self.buttons:
                button.show()
        self.update()

    def go_back(self, checked: bool = False):  # noqa: FBT001, FBT002
        if self.history_index > 0:
            self.history_index -= 1
            self.update_path(self.history[self.history_index])
            self.path_changed.emit(self.current_path)

    def go_forward(self, checked: bool = False):  # noqa: FBT001, FBT002
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.update_path(self.history[self.history_index])
            self.path_changed.emit(self.current_path)

    def go_up(self, checked: bool = False):  # noqa: FBT001, FBT002
        parent = self.current_path.parent
        if parent != self.current_path:
            self.update_path(parent)
            self.path_changed.emit(parent)

    def _on_editing_finished(self):
        new_path = Path(self.line_edit.text()).resolve()
        if new_path.exists():
            if new_path != self.current_path:
                self.update_path(new_path)
                self.path_changed.emit(new_path)
        else:
            # If the path doesn't exist, revert to the current path
            self.line_edit.setText(str(self.current_path))
        self.toggle_edit_mode(False)  # noqa: FBT003

    def _on_path_selected(self, path: Path):
        if path != self.current_path:
            self.update_path(path)
            self.path_changed.emit(path)

    def focusOutEvent(self, event: QFocusEvent):
        if self.edit_mode:
            self.toggle_edit_mode(False)  # noqa: FBT003
        super().focusOutEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if not self.edit_mode:
            for button in self.buttons:
                if button.geometry().contains(event.pos()):
                    button.click()
                    return
            self.toggle_edit_mode(True)  # noqa: FBT003
        super().mousePressEvent(event)

    def set_path_icon(self, path: Path, icon: QIcon):
        for button in self.buttons:
            if button.path == path:
                button.setIcon(icon)
                break

    def set_directory_contents(self, path: Path, contents: list[tuple[str, Path, QIcon]]):
        for button in self.buttons:
            if button.path == path:
                button.set_menu_items(contents)
                break
