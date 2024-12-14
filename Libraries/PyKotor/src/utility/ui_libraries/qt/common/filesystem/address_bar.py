from __future__ import annotations

import os

from pathlib import Path
from typing import TYPE_CHECKING, cast

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import QSize, QTimer, Qt, Signal  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPen
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QApplication,
    QCompleter,
    QFileSystemModel,  # pyright: ignore[reportPrivateImportUsage]
    QHBoxLayout,
    QLineEdit,
    QMenu,
    QPushButton,
    QSizePolicy,
    QStyle,
    QToolBar,
    QToolButton,
    QWidget,
)

if TYPE_CHECKING:
    from qtpy.QtGui import QMouseEvent, QPaintEvent


class PathSepButton(QToolButton):
    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setText(text)
        self.setStyleSheet("""
            ShinyButton {
                border: none;
                padding: 2px 5px;
                background: transparent;
            }
            ShinyButton:hover {
                background-color: rgba(229, 243, 255, 0.5);
            }
        """)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 255, 255, 30))
        gradient.setColorAt(1, QColor(255, 255, 255, 10))

        painter.fillRect(self.rect(), gradient)
        super().paintEvent(event)


class PathButton(QToolButton):
    pathSelected = Signal(Path)

    def __init__(self, path: Path, parent: QWidget | None = None, *, is_last: bool = False):
        super().__init__(parent)
        self.path = path
        self.is_last = is_last
        self.setText(path.name or str(path))
        self.clicked.connect(self._on_clicked)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self._menu_contents: list[tuple[str, Path, QIcon]] = []
        self._recreate_menu_timer = QTimer(self)  # Fixes a Qt bug where the menu will not pop up a second time.
        self._recreate_menu_timer.setSingleShot(True)
        self._recreate_menu_timer.timeout.connect(self._recreate_menu)
        self.setStyleSheet("""
            PathButton {
                border: 1px solid #CCCCCC;
                padding: 2px 5px;
                border-radius: 2px;
                background: transparent;
            }
            PathButton:hover {
                background-color: #E0E0E0;
            }
            PathButton:pressed {
                background-color: #D0D0D0;
            }
        """)

    def _on_clicked(self):
        self.pathSelected.emit(self.path)

    def set_icon(self, icon: QIcon):
        self.setIcon(icon)

    def set_menu_items(self, contents: list[tuple[str, Path, QIcon]]):
        self._menu_contents = contents
        try:
            self.setMenu(QMenu(self))
            menu = self.menu()
            assert menu is not None, "menu is None somehow, this shouldn't happen"
        except RuntimeError:  # wrapped C/C++ object has been deleted
            return
        for name, path, icon in contents:
            action = QAction(icon, name, menu)
            action.triggered.connect(lambda _, p=path: self.pathSelected.emit(p))
            menu.addAction(action)
        menu.aboutToHide.connect(self._on_menu_about_to_hide)
        menu.setStyleSheet("QMenu { menu-scrollable: 1; }")

    def _on_menu_about_to_hide(self):
        self._recreate_menu_timer.start(0)

    def _recreate_menu(self):
        self.set_menu_items(self._menu_contents)

    def mousePressEvent(self, event: QMouseEvent):
        menu = self.menu()
        if menu is None:
            return
        if event.button() == Qt.MouseButton.LeftButton and not menu.geometry().contains(event.pos()):
            self._on_clicked()
        else:
            super().mousePressEvent(event)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 255, 255, 30))
        gradient.setColorAt(1, QColor(255, 255, 255, 10))

        painter.fillRect(self.rect(), gradient)
        super().paintEvent(event)


class RobustAddressBar(QWidget):
    pathChanged: Signal = Signal(Path)
    returnPressed: Signal = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.current_path: Path = Path.home()
        self.buttons: list[PathButton] = []
        self.edit_mode: bool = False
        self.history: list[Path] = [self.current_path]
        self.history_index: int = 0
        self.fs_model: QFileSystemModel = QFileSystemModel(self)

        self.setLayout(QHBoxLayout(self))
        layout: QHBoxLayout | None = cast(QHBoxLayout, self.layout())
        assert layout is not None, "layout is None somehow, this shouldn't happen"
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setFixedHeight(30)

        self.toolbar: QToolBar = QToolBar(self)
        self.toolbar.setMovable(True)
        self.toolbar.setFloatable(True)
        self.toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.toolbar.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

        self.toolbar.setStyleSheet("QToolBar { border: none; }")
        backButton: QAction | None = self.toolbar.addAction(
            cast(QStyle, self.style()).standardIcon(QStyle.StandardPixmap.SP_ArrowBack),
            "Back",
        )
        assert backButton is not None, "backButton is None somehow, this shouldn't happen"
        self.backButton: QAction = backButton
        self.backButton.setIcon(QIcon.fromTheme("go-previous"))
        self.backButton.triggered.connect(self.go_back)

        forwardButton: QAction | None = self.toolbar.addAction(
            cast(QStyle, self.style()).standardIcon(QStyle.StandardPixmap.SP_ArrowForward),
            "Forward",
        )
        assert forwardButton is not None, "forwardButton is None somehow, this shouldn't happen"
        self.forwardButton: QAction = forwardButton
        self.forwardButton.triggered.connect(self.go_forward)
        self.forwardButton.setIcon(QIcon.fromTheme("go-next"))

        upButton: QAction | None = self.toolbar.addAction(
            cast(QStyle, self.style()).standardIcon(QStyle.StandardPixmap.SP_ArrowUp),
            "Up",
        )
        assert upButton is not None, "upButton is None somehow, this shouldn't happen"
        self.upButton: QAction = upButton
        self.upButton.triggered.connect(self.go_up)
        self.upButton.setIcon(QIcon.fromTheme("go-up"))

        self.toolbar.addSeparator()

        layout.addWidget(self.toolbar)

        self.setMouseTracking(True)
        self.setToolTipDuration(10000)
        self.setToolTip("AddressBar")

        self.address_widget = QWidget()
        self.address_widget.setObjectName("addressWidget")
        self.address_widget.setStyleSheet("#addressWidget { background-color: white; border: 1px solid #CCCCCC; border-radius: 2px; }")
        self.address_layout = QHBoxLayout(self.address_widget)
        self.address_layout.setContentsMargins(2, 2, 2, 2)
        self.address_layout.setSpacing(0)
        self.address_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.address_widget, 1)  # Give it more space in the layout

        self.line_edit: QLineEdit = QLineEdit(self)
        self.line_edit.setFrame(False)
        self.line_edit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.line_edit, 1)  # Give it more space in the layout

        self.completer: QCompleter = QCompleter(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive if os.name == "nt" else Qt.CaseSensitivity.CaseSensitive)
        self.completer.setModel(self.fs_model)
        self.line_edit.setCompleter(self.completer)

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.line_edit.editingFinished.connect(self._on_editing_finished)
        self.line_edit.installEventFilter(self)
        self.line_edit.returnPressed.connect(self.returnPressed.emit)

        self.refreshButton = QPushButton(self.address_widget)
        self.refreshButton.setIcon(QIcon.fromTheme("view-refresh"))
        self.refreshButton.setToolTip("Refresh")
        self.refreshButton.clicked.connect(self.refresh)
        layout.addWidget(self.refreshButton)  # Add refresh button to the far right side

    def refresh(self):
        self.update_path(self.current_path)

    def set_model(self, model: QFileSystemModel):
        self.fs_model = model
        self.completer.setModel(model)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw a light gray border
        painter.setPen(QPen(QColor(204, 204, 204), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 2, 2)

        super().paintEvent(event)

    def update_path(self, path: Path):
        new_path = path.absolute()
        if new_path != self.current_path:
            self._update_history(new_path)

        self.current_path = new_path
        self.line_edit.setText(str(self.current_path))

        for i in reversed(range(self.address_layout.count())):
            item = self.address_layout.itemAt(i)
            if item is None:
                continue
            w = item.widget()
            if w is None:
                continue
            w.hide()
            w.setVisible(False)
            self.address_layout.removeWidget(w)
            w.deleteLater()

        QTimer.singleShot(0, self.update_path_part2)
        QApplication.processEvents()
        self.address_layout.update()
        self.address_layout.invalidate()

    def update_path_part2(self):
        paths = list(reversed([self.current_path, *self.current_path.parents]))
        for i, current_path in enumerate(paths):
            is_last = i == len(paths) - 1
            button = self.create_path_button(current_path, is_last=is_last)
            self.address_layout.addWidget(button)
            if not is_last:
                separator = PathSepButton(">")
                separator.setEnabled(False)
                separator.setFixedWidth(15)
                self.address_layout.addWidget(separator)

        self.toggle_edit_mode(edit_mode=False)
        self.update_navigation_buttons()
        self.updateGeometry()
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(600, 30)  # Adjust the size as needed

    def _update_history(self, new_path: Path):
        if self.history_index == -1 or self.history[self.history_index] != new_path:
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
            self.address_widget.hide()
            self.line_edit.show()
            self.line_edit.setFocus()
            self.line_edit.setText(str(self.current_path))
            self.line_edit.selectAll()
        else:
            self.line_edit.hide()
            self.address_widget.show()
        self.update()

    def go_back(self, checked: bool = False):  # noqa: FBT001, FBT002
        if self.history_index > 0:
            self.history_index -= 1
            self.update_path(self.history[self.history_index])
            self.pathChanged.emit(self.current_path)

    def go_forward(self, checked: bool = False):  # noqa: FBT001, FBT002
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.update_path(self.history[self.history_index])
            self.pathChanged.emit(self.current_path)

    def go_up(self, checked: bool = False):  # noqa: FBT001, FBT002
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
            except Exception:  # noqa: BLE001
                RobustLogger().warning("Failed to change path", exc_info=True, stack_info=False)
                self.line_edit.setText(str(self.current_path))
        self.toggle_edit_mode(edit_mode=False)

    def create_path_button(
        self,
        path: Path,
        *,
        is_last: bool = False,
    ) -> PathButton:
        button = PathButton(path, self, is_last=is_last)
        button.set_menu_items(self._get_directory_contents(path))
        button.pathSelected.connect(self._on_path_selected)
        self.buttons.append(button)
        self.address_layout.addWidget(button)
        return button

    def _on_path_selected(self, path: Path):
        if path != self.current_path:
            self.update_path(path)
            self.pathChanged.emit(path)

    def mousePressEvent(self, event: QMouseEvent):
        if not self.edit_mode:
            for button in self.buttons:
                try:
                    if button.geometry().contains(event.pos()):
                        return
                except RuntimeError:  # wrapped C/C++ object has been deleted  # noqa: PERF203, S112
                    continue
            self.toggle_edit_mode(edit_mode=True)
        super().mousePressEvent(event)

    def set_path_icon(self, path: Path, icon: QIcon):
        for button in self.buttons:
            if button.path == path:
                button.set_icon(icon)
                break

    def _get_directory_contents(self, path: Path) -> list[tuple[str, Path, QIcon]]:
        contents: list[tuple[str, Path, QIcon]] = []
        if self.fs_model is None:
            contents = self._scan_directory(path)
            return contents

        index = self.fs_model.index(str(path))
        for i in range(self.fs_model.rowCount(index)):
            child_index = self.fs_model.index(i, 0, index)
            child_path = Path(self.fs_model.filePath(child_index))
            if child_path.is_dir():
                icon = self.fs_model.fileIcon(child_index)
                contents.append((child_path.name, child_path, icon))
        else:
            contents = self._scan_directory(path)
        return contents

    def _scan_directory(self, path: Path) -> list[tuple[str, Path, QIcon]]:
        contents: list[tuple[str, Path, QIcon]] = []
        try:
            with os.scandir(path) as it:
                for entry in it:
                    try:
                        if entry.is_dir():
                            icon = QIcon()  # Placeholder for directory icon
                            contents.append((entry.name, Path(entry.path), icon))
                    except Exception as e:  # noqa: BLE001, PERF203
                        RobustLogger().warning(f"Failed to scan directory {path}: {e}", exc_info=True, stack_info=False)
        except Exception as e:  # noqa: BLE001, PERF203
            RobustLogger().warning(f"Failed to scan directory {path}: {e}", exc_info=True, stack_info=False)
        else:
            return contents
        return contents

    def set_directory_contents(self, path: Path, contents: list[tuple[str, Path, QIcon]]):
        for button in self.buttons:
            if button.path == path:
                button.set_menu_items(contents)
                break


if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication, QMainWindow, QTreeView, QVBoxLayout

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Address Bar Test")
            self.setGeometry(100, 100, 800, 600)

            central_widget = QWidget()
            layout = QVBoxLayout(central_widget)

            self.address_bar: RobustAddressBar = RobustAddressBar(self)
            layout.addWidget(self.address_bar)

            self.tree_view: QTreeView = QTreeView()
            self.fs_model: QFileSystemModel = QFileSystemModel()
            self.fs_model.setRootPath("")
            self.tree_view.setModel(self.fs_model)
            layout.addWidget(self.tree_view)

            self.setCentralWidget(central_widget)

            self.address_bar.set_model(self.fs_model)
            self.address_bar.pathChanged.connect(self.on_path_changed)
            self.tree_view.clicked.connect(self.on_tree_view_clicked)

            self.initialize_address_bar()

        def initialize_address_bar(self):
            initial_path = Path.home()
            self.address_bar.update_path(initial_path)
            self.tree_view.setRootIndex(self.fs_model.index(str(initial_path)))

        def on_path_changed(self, path: Path):
            print(f"Path changed to: {path}")
            self.tree_view.setRootIndex(self.fs_model.index(str(path)))

        def on_tree_view_clicked(self, index):
            path = self.fs_model.filePath(index)
            self.address_bar.update_path(Path(path))

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
