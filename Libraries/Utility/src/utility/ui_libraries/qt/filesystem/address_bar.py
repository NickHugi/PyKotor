from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from qtpy.QtCore import Qt, Signal  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtWidgets import QAction, QCompleter, QLineEdit, QMenu, QSizePolicy, QStyle, QToolBar, QToolButton

from utility.ui_libraries.qt.debug.print_qobject import print_qt_class_calls

if TYPE_CHECKING:
    from qtpy.QtGui import QFocusEvent, QIcon, QMouseEvent
    from qtpy.QtWidgets import QWidget

@print_qt_class_calls()
class PathButton(QToolButton):
    pathSelected = Signal(Path)

    def __init__(self, path: Path, parent: QWidget | None = None, *, is_last: bool = False):
        super().__init__(parent)
        self.path = path
        self.menu: QMenu = QMenu(self)
        self.is_last = is_last
        self.setText(path.name or str(path))
        self.clicked.connect(self._on_clicked)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        if not is_last:
            self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            self.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
            self.setMenu(QMenu(self))

    def _on_clicked(self, checked: bool = False):
        if not self.menu or self.menu.isEmpty():
            self.pathSelected.emit(self.path)

    def set_icon(self, icon: QIcon):
        self.setIcon(icon)

    def set_menu_items(self, contents: list[tuple[str, Path, QIcon]]):
        self.menu.clear()
        for name, path, icon in contents:
            action = QAction(icon, name, self.menu)
            action.triggered.connect(lambda _, p=path: self.pathSelected.emit(p))
            self.menu.addAction(action)
        self.setMenu(self.menu)
        if not self.is_last:
            self.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

@print_qt_class_calls()
class PyQAddressBar(QToolBar):
    pathChanged: Signal = Signal(Path)
    editingFinished: Signal = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.current_path: Path = Path.home()
        self.buttons: list[PathButton] = []
        self.edit_mode: bool = False
        self.history: list[Path] = [self.current_path]
        self.history_index: int = 0

        self.setMovable(False)
        self.setFloatable(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)

        self.backButton: QAction = self.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack), "Back")
        self.backButton.triggered.connect(self.go_back)

        self.forwardButton: QAction = self.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward), "Forward")
        self.forwardButton.triggered.connect(self.go_forward)

        self.upButton: QAction = self.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp), "Up")
        self.upButton.triggered.connect(self.go_up)

        self.addSeparator()

        self.line_edit: QLineEdit = QLineEdit(self)
        self.completer: QCompleter = QCompleter(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.line_edit.setCompleter(self.completer)
        self.line_edit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.line_edit.hide()
        self.line_edit.editingFinished.connect(self._on_editing_finished)
        self.addWidget(self.line_edit)

        self.setMouseTracking(True)
        self.setToolTipDuration(10000)
        self.setToolTip("AddressBar")
        self.setCursor(Qt.CursorShape.IBeamCursor)

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
            if not is_last:
                self.addSeparator()

        self.toggle_edit_mode(edit_mode=False)
        self.update_navigation_buttons()
        self.updateGeometry()
        self.update()

    def _update_history(self, new_path: Path):
        if (
            self.history_index == -1
            or self.history[self.history_index] != new_path
        ):
            self.history = self.history[: self.history_index + 1]
            self.history.append(new_path)
            self.history_index = len(self.history) - 1
        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.backButton.setEnabled(self.history_index > 0)
        self.forwardButton.setEnabled(self.history_index < len(self.history) - 1)
        self.upButton.setEnabled(self.current_path != self.current_path.root)

    def toggle_edit_mode(self, *, edit_mode: bool):
        self.edit_mode = edit_mode
        if edit_mode:
            for button in self.buttons:
                button.hide()
            self.line_edit.show()
            self.line_edit.setFocus()
            self.line_edit.setText(str(self.current_path))
            self.line_edit.selectAll()
        else:
            self.line_edit.hide()
            for button in self.buttons:
                button.show()
        self.update()

    def go_back(self, checked: bool = False):
        if self.history_index > 0:
            self.history_index -= 1
            self.update_path(self.history[self.history_index])
            self.pathChanged.emit(self.current_path)

    def go_forward(self, checked: bool = False):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.update_path(self.history[self.history_index])
            self.pathChanged.emit(self.current_path)

    def go_up(self, checked: bool = False):
        parent = self.current_path.parent
        if parent != self.current_path:
            self.update_path(parent)
            self.pathChanged.emit(parent)

    def _on_editing_finished(self):
        if self.edit_mode:
            new_path_str = self.line_edit.text()
            try:
                new_path = Path(new_path_str).resolve()
                if new_path.exists():
                    if new_path != self.current_path:
                        self.update_path(new_path)
                        self.pathChanged.emit(new_path)
                else:
                    relative_path = self.current_path / new_path_str
                    if relative_path.exists():
                        self.update_path(relative_path)
                        self.pathChanged.emit(relative_path)
                    else:
                        self.line_edit.setText(str(self.current_path))
            except Exception:
                self.line_edit.setText(str(self.current_path))
        self.toggle_edit_mode(edit_mode=False)

    def create_path_button(self, path: Path, *, is_last: bool = False) -> PathButton:
        button = PathButton(path, self, is_last=is_last)
        button.pathSelected.connect(self._on_path_selected)
        self.buttons.append(button)
        self.addWidget(button)
        return button

    def _on_path_selected(self, path: Path):
        if path != self.current_path:
            self.update_path(path)
            self.pathChanged.emit(path)
            self.set_directory_contents(path, self._get_directory_contents(path))

    def focusOutEvent(self, event: QFocusEvent):
        if self.edit_mode:
            self.toggle_edit_mode(edit_mode=False)
        super().focusOutEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if not self.edit_mode:
            for button in self.buttons:
                if button.geometry().contains(event.pos()):
                    button.click()
                    return
            self.toggle_edit_mode(True)
        super().mousePressEvent(event)

    def set_path_icon(self, path: Path, icon: QIcon):
        for button in self.buttons:
            if button.path == path:
                button.setIcon(icon)
                break

    def _get_directory_contents(self, path: Path) -> list[tuple[str, Path, QIcon]]:
        return [(p.name, p, QIcon.fromTheme("folder" if p.is_dir() else "text-plain")) for p in path.iterdir()]

    def set_directory_contents(self, path: Path, contents: list[tuple[str, Path, QIcon]]):
        for button in self.buttons:
            if button.path == path:
                button.set_menu_items(contents)
                break

if __name__ == "__main__":
    import sys

    from qtpy.QtGui import QIcon
    from qtpy.QtWidgets import QApplication, QMainWindow

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Address Bar Test")
            self.setGeometry(100, 100, 800, 100)
            self.address_bar = PyQAddressBar(self)
            self.setCentralWidget(self.address_bar)
            self.address_bar.pathChanged.connect(self.on_path_changed)
            self.initialize_address_bar()

        def initialize_address_bar(self):
            initial_path = Path.home().joinpath("Documents")
            self.address_bar.update_path(initial_path)
            contents = [
                ("File1.txt", initial_path / "File1.txt", QIcon.fromTheme("text-plain")),
                ("File2.txt", initial_path / "File2.txt", self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack)),
                ("Folder1", initial_path / "Folder1", QIcon.fromTheme("folder")),
            ]
            self.address_bar.set_directory_contents(initial_path, contents)

        def on_path_changed(self, path: Path):
            print(f"Path changed to: {path}")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
