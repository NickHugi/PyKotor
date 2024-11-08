from __future__ import annotations

import tempfile
import uuid

from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from loggerplus import RobustLogger
from qtpy.QtCore import QTimer, Signal
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import (
    QApplication,
    QFileDialog,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QShortcut,
)

from pykotor.resource.type import ResourceType
from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit
from toolset.gui.widgets.media_player_widget import MediaPlayerWidget
from toolset.gui.widgets.settings.installations import GlobalSettings

if TYPE_CHECKING:

    from qtpy.QtCore import QRect
    from qtpy.QtGui import QScreen
    from qtpy.QtWidgets import (
        QMenuBar,
        QWidget,
    )
    from typing_extensions import Literal

    from pykotor.common.language import LocalizedString
    from toolset.data.installation import HTInstallation

class Editor(QMainWindow):
    sig_new_file: Signal = Signal()
    sig_saved_file: Signal = Signal(str, str, ResourceType, bytes)
    sig_loaded_file: Signal = Signal(str, str, ResourceType, bytes)

    CAPSULE_FILTER: str = "*.mod *.erf *.rim *.sav"

    def __init__(
        self,
        parent: QWidget | None,
        title: str,
        icon_name: str,
        read_supported: list[ResourceType],
        write_supported: list[ResourceType],
        installation: HTInstallation | None = None,
    ):
        super().__init__(parent)
        self._is_capsule_editor: bool = False
        self._installation: HTInstallation | None = installation
        self._logger: RobustLogger = RobustLogger()
        self._global_settings: GlobalSettings = GlobalSettings()

        self._editor_title: str = title
        self._restype: ResourceType = next(iter(read_supported or write_supported), ResourceType.INVALID)
        self._resname: str = f"untitled_{uuid.uuid4().hex[:8]}"
        self._filepath: Path = self.setup_extract_path() / f"{self._resname}.{self._restype.extension}"
        self._revert: bytes = b""
        self._global_settings: GlobalSettings = GlobalSettings()

        self.media_player: MediaPlayerWidget = MediaPlayerWidget(self)
        self.setWindowTitle(title)
        self._setup_icon(icon_name)

        self.setup_editor_filters(read_supported, write_supported)

    @abstractmethod
    def build(self) -> tuple[bytes, bytes]: ...

    def _setup_menus(self):
        menubar: QMenuBar | None = self.menuBar()
        assert menubar is not None, "menubar is somehow None"
        menubar_menu: QMenu | None = menubar.actions()[0].menu()
        if not isinstance(menubar_menu, QMenu):
            raise TypeError(f"self.menuBar().actions()[0].menu() returned a {type(menubar_menu).__name__} object, expected QMenu.")
        for action in menubar_menu.actions():
            if action.text() == "New":
                action.triggered.connect(self.new)
                action.setShortcut("Ctrl+N")
            if action.text() == "Open":
                action.triggered.connect(self.open)
                action.setShortcut("Ctrl+O")
            if action.text() == "Save":
                action.triggered.connect(self.save)
                action.setShortcut("Ctrl+S")
            if action.text() == "Save As":
                action.triggered.connect(self.save_as)
                action.setShortcut("Ctrl+Shift+S")
            if action.text() == "Revert":
                action.triggered.connect(self.revert)
                action.setShortcut("Ctrl+R")
            if action.text() == "Exit":
                action.triggered.connect(self.close)
                action.setShortcut("Ctrl+Q")
        QShortcut("Ctrl+N", self).activated.connect(self.new)
        QShortcut("Ctrl+O", self).activated.connect(self.open)
        QShortcut("Ctrl+S", self).activated.connect(self.save)
        QShortcut("Ctrl+Shift+S", self).activated.connect(self.save_as)
        QShortcut("Ctrl+R", self).activated.connect(self.revert)
        QShortcut("Ctrl+Q", self).activated.connect(self.close)

    def _setup_icon(
        self,
        icon_resname: str,
    ):
        icon_version: Literal["x", "2", "1"] = "x" if self._installation is None else "2" if self._installation.tsl else "1"
        icon_path_str: str = f":/images/icons/k{icon_version}/{icon_resname}.png"
        self.setWindowIcon(QIcon(QPixmap(icon_path_str)))

    def setup_extract_path(self) -> Path:
        extract_path: Path = Path(GlobalSettings().extractPath)
        if not extract_path.exists() or not extract_path.is_dir():
            extract_path_str: str = QFileDialog.getExistingDirectory(None, "Select a temp directory")
            if not extract_path_str.strip():
                extract_path_str = tempfile.gettempdir()
            GlobalSettings().extractPath = extract_path_str
            extract_path = Path(extract_path_str)
        return extract_path

    def refresh_window_title(self):
        """Refreshes the window title based on the current state of the editor."""
        installation_name: str = self._installation.name if self._installation else "No Installation"
        title: str = f"{self._editor_title}({installation_name})[*]"
        if self._filepath and self._resname and self._restype:
            relpath: Path = self._filepath.relative_to(self._filepath.parent.parent) if self._filepath.parent.parent.name else self._filepath.parent
            from toolset.gui.editors.erf import ERFEditor

            if (is_bif_file(relpath) or is_capsule_file(self._filepath)) and not isinstance(self, ERFEditor):
                relpath /= f"{self._resname}.{self._restype.extension}"
            title = f"{relpath} - {title}"
        self.setWindowTitle(title)

    def setup_editor_filters(
        self,
        read_supported: list[ResourceType],
        write_supported: list[ResourceType],
    ):
        write_supported = read_supported.copy() if read_supported is write_supported else write_supported
        additional_formats: set[str] = {"XML", "JSON", "CSV", "ASCII", "YAML"}
        for add_format in additional_formats:
            read_supported.extend(
                ResourceType.__members__[f"{restype.name}_{add_format}"] for restype in read_supported if f"{restype.name}_{add_format}" in ResourceType.__members__
            )
            write_supported.extend(
                ResourceType.__members__[f"{restype.name}_{add_format}"] for restype in write_supported if f"{restype.name}_{add_format}" in ResourceType.__members__
            )
        self._read_supported: list[ResourceType] = read_supported
        self._write_supported: list[ResourceType] = write_supported

        self._save_filter: str = "All valid files ("
        for resource in write_supported:
            self._save_filter += f'*.{resource.extension}{"" if write_supported[-1] == resource else " "}'
        self._save_filter += f" {self.CAPSULE_FILTER});;"
        for resource in write_supported:
            self._save_filter += f"{resource.category} File (*.{resource.extension});;"
        self._save_filter += f"Save into module ({self.CAPSULE_FILTER})"

        self._open_filter: str = "All valid files ("
        for resource in read_supported:
            self._open_filter += f'*.{resource.extension}{"" if read_supported[-1] == resource else " "}'
        self._open_filter += f" {self.CAPSULE_FILTER});;"
        for resource in read_supported:
            self._open_filter += f"{resource.category} File (*.{resource.extension});;"
        self._open_filter += f"Load from module ({self.CAPSULE_FILTER})"

    def center_and_adjust_window(self):
        primary_screen: QScreen | None = QApplication.primaryScreen()
        if primary_screen is None:
            return
        screen: QRect = primary_screen.geometry()
        new_x: int = (screen.width() - self.width()) // 2
        new_y: int = (screen.height() - self.height()) // 2

        self.move(
            max(0, min(new_x, screen.width() - self.width())),
            max(0, min(new_y, screen.height() - self.height())),
        )

    def _load_locstring(
        self,
        textbox: QLineEdit | QPlainTextEdit | LocalizedStringLineEdit,
        locstring: LocalizedString,
    ):
        if isinstance(textbox, LocalizedStringLineEdit):
            textbox.set_locstring(locstring)
            return
        setText: Callable[[str], None] = textbox.setPlainText if isinstance(textbox, QPlainTextEdit) else textbox.setText
        class_name: Literal["QLineEdit", "QPlainTextEdit"] = "QLineEdit" if isinstance(textbox, QLineEdit) else "QPlainTextEdit"
        if locstring.stringref == -1:
            text = str(locstring)
            setText(text if text != "-1" else "")
            textbox.setStyleSheet(f"{textbox.styleSheet()} {class_name} {{background-color: white;}}")
        elif self._installation is not None:
            setText(self._installation.talktable().string(locstring.stringref))
            textbox.setStyleSheet(f"{textbox.styleSheet()} {class_name} {{background-color: #fffded;}}")
        textbox.locstring = locstring  # type: ignore[attr-defined]

    def blink_window(
        self,
        *,
        sound: bool = True,
    ):
        if sound:
            with suppress(Exception):
                self.play_sound("dr_metal_lock")
        self.setWindowOpacity(0.7)
        QTimer.singleShot(125, lambda: self.setWindowOpacity(1))

    def filepath(self) -> str | None:
        return str(self._filepath)