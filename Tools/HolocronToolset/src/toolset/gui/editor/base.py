from __future__ import annotations

import tempfile
import traceback
import uuid

from abc import abstractmethod
from contextlib import suppress
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Callable, Optional, Sequence, cast

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import (
    QBuffer,
    QIODevice,
    QTimer,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtMultimedia import QMediaPlayer
from qtpy.QtWidgets import (
    QApplication,
    QFileDialog,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPlainTextEdit,  # pyright: ignore[reportPrivateImportUsage]  # pyright: ignore[reportPrivateImportUsage]
)

from pykotor.common.module import Module
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bif import read_bif
from pykotor.resource.formats.erf import ERF, ERFType, read_erf, write_erf
from pykotor.resource.formats.gff import bytes_gff, read_gff
from pykotor.resource.formats.rim import read_rim, write_rim
from pykotor.resource.type import ResourceType
from pykotor.tools import module
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_capsule_file, is_rim_file
from toolset.gui.dialogs.load_from_module import LoadFromModuleDialog
from toolset.gui.dialogs.save.to_bif import BifSaveDialog, BifSaveOption
from toolset.gui.dialogs.save.to_module import SaveToModuleDialog
from toolset.gui.dialogs.save.to_rim import RimSaveDialog, RimSaveOption
from toolset.gui.widgets.edit.locstring import LocalizedStringLineEdit
from toolset.gui.widgets.media_player_widget import MediaPlayerWidget
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.error_handling import format_exception_with_variables, universal_simplify_exception
from utility.system.os_helper import remove_any

if TYPE_CHECKING:
    import os

    from pathlib import PurePath

    from PyQt6.QtMultimedia import QMediaPlayer as PyQt6MediaPlayer  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue]
    from PySide6.QtMultimedia import QMediaPlayer as PySide6MediaPlayer  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue]
    from qtpy.QtCore import QRect
    from qtpy.QtGui import QScreen, _QAction
    from qtpy.QtWidgets import QWidget, _QMenu
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.language import LocalizedString
    from pykotor.resource.formats.bif import BIF
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.formats.rim.rim_data import RIM
    from toolset.data.installation import HTInstallation


class Editor(QMainWindow):
    sig_new_file: Signal = Signal()
    sig_saved_file: Signal = Signal(str, str, ResourceType, bytes)
    sig_loaded_file: Signal = Signal(str, str, ResourceType, bytes)

    CAPSULE_FILTER: str = "*.mod *.erf *.rim *.sav *.bif"

    def __init__(  # noqa: PLR0913
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
        menubar_menu = menubar.actions()[0].menu()
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

    def _setup_icon(
        self,
        icon_resname: str,
    ):
        icon_version: Literal["x", "2", "1"] = "x" if self._installation is None else "2" if self._installation.tsl else "1"
        icon_path_str: str = f":/images/icons/k{icon_version}/{icon_resname}.png"
        self.setWindowIcon(QIcon(QPixmap(icon_path_str)))

    def setup_extract_path(self) -> Path:
        extract_path: Path = Path(GlobalSettings().extractPath)
        if extract_path.exists() and extract_path.is_dir():
            return extract_path
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
            read_supported.extend(ResourceType.__members__[f"{restype.name}_{add_format}"] for restype in read_supported if f"{restype.name}_{add_format}" in ResourceType.__members__)  # noqa: E501
            write_supported.extend(ResourceType.__members__[f"{restype.name}_{add_format}"] for restype in write_supported if f"{restype.name}_{add_format}" in ResourceType.__members__)  # noqa: E501
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

    def save_as(self):  # noqa: C901
        def show_invalid(exc: Exception | None, msg: str):
            msgBox = QMessageBox(
                QMessageBox.Icon.Critical,
                "Invalid filename/extension",
                f"Check the filename and try again. Could not save!{f'<br><br>{msg}' if msg else ''}",
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            if exc is not None:
                msgBox.setDetailedText(traceback.format_exc())
            msgBox.exec()

        filepath_str, _filter = QFileDialog.getSaveFileName(self, "Save As", str(self._filepath), self._save_filter, "")
        if not filepath_str:
            return
        error_msg, exc = "", None
        try:
            identifier = ResourceIdentifier.from_path(filepath_str)
            if identifier.restype.is_invalid:
                show_invalid(None, str(identifier))
                return
        except ValueError as e:
            exc = e
            RobustLogger().exception(f"ValueError raised, assuming invalid filename/extension '{filepath_str}'")
            error_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
            show_invalid(exc, error_msg)
            return

        if is_capsule_file(filepath_str) and f"Save into module ({self.CAPSULE_FILTER})" in self._save_filter:
            if self._resname is None or self._restype is None:
                self._resname = "new"
                self._restype = self._write_supported[0]

            dialog2 = SaveToModuleDialog(self._resname, self._restype, self._write_supported)
            if dialog2.exec():
                self._resname = dialog2.resname()
                self._restype = dialog2.restype()
                self._filepath = Path(filepath_str)
        else:
            self._filepath = Path(filepath_str)
            self._resname, self._restype = identifier.unpack()
        self.save()

        self.refresh_window_title()
        menu_bar: QMenuBar | None = self.menuBar()
        assert menu_bar is not None, "menu_bar is somehow None"
        menu: _QMenu | None = menu_bar.actions()[0].menu()
        assert menu is not None, "menu is somehow None"
        for action in menu.actions():
            if action.text() == "Revert":
                action.setEnabled(True)

    def save(self):
        if self._filepath is None:
            self.save_as()
            return

        try:
            data, data_ext = self.build()
            if data is None:
                return
            from toolset.gui.editors.gff import GFFEditor

            if (
                self._global_settings.attemptKeepOldGFFFields
                and self._restype is not None
                and self._restype.is_gff()
                and not isinstance(self, GFFEditor)
                and self._revert is not None
            ):  # noqa: E501
                old_gff: GFF = read_gff(self._revert)
                new_gff: GFF = read_gff(data)
                new_gff.root.add_missing(old_gff.root)
                data: bytes = bytes_gff(new_gff)
            self._revert = data

            self.refresh_window_title()

            if is_bif_file(self._filepath):
                self._save_ends_with_bif(data, data_ext)
            elif is_capsule_file(self._filepath.parent):
                self._save_nested_capsule(data, data_ext)
            elif is_rim_file(self._filepath.name):
                self._save_ends_with_rim(data, data_ext)
            elif is_any_erf_type_file(self._filepath):
                self._save_ends_with_erf(data, data_ext)
            else:
                self._save_ends_with_other(data, data_ext)
        except Exception as e:  # noqa: BLE001
            self.blink_window()
            RobustLogger().critical("Failed to write to file", exc_info=True)
            msg_box = QMessageBox(QMessageBox.Icon.Critical, "Failed to write to file", str(universal_simplify_exception(e)).replace("\n", "<br>"))
            msg_box.setDetailedText(format_exception_with_variables(e))
            msg_box.exec()
        else:
            self.setWindowModified(False)

    def _save_ends_with_bif(
        self,
        data: bytes,
        data_ext: bytes,
    ):
        dialog = BifSaveDialog(self)
        dialog.exec()
        if dialog.option == BifSaveOption.MOD:
            str_filepath, filter = QFileDialog.getSaveFileName(self, "Save As", "", ".MOD File (*.mod)", "")
            if not str(str_filepath).strip():
                return
            r_filepath = Path(str_filepath)
            dialog2 = SaveToModuleDialog(self._resname, self._restype, self._write_supported)
            if dialog2.exec():
                self._resname = dialog2.resname()
                self._restype = dialog2.restype()
                self._filepath = r_filepath
                self.save()
        elif dialog.option == BifSaveOption.Override:
            assert self._installation is not None
            self._filepath = self._installation.override_path() / f"{self._resname}.{self._restype.extension}"
            self.save()

    def _save_ends_with_rim(
        self,
        data: bytes,
        data_ext: bytes,
    ):
        if self._global_settings.disableRIMSaving:
            dialog = RimSaveDialog(self)
            dialog.exec()
            if dialog.option == RimSaveOption.MOD:
                self._filepath = self._filepath.parent / f"{Module.filepath_to_root(self._filepath)}.mod"
                self.save()
            elif dialog.option == RimSaveOption.Override:
                assert self._installation is not None
                self._filepath = self._installation.override_path() / f"{self._resname}.{self._restype.extension}"
                self.save()
            return

        rim: RIM = read_rim(self._filepath)

        if self._restype is ResourceType.MDL:
            rim.set_data(self._resname, ResourceType.MDX, data_ext)

        rim.set_data(self._resname, self._restype, data)

        write_rim(rim, self._filepath)
        self.sig_saved_file.emit(str(self._filepath), self._resname, self._restype, bytes(data))

        if self._installation is not None:
            self._installation.reload_module(self._filepath.name)

    def _save_nested_capsule(
        self,
        data: bytes | bytearray,
        data_ext: bytes,
    ):
        nested_paths: list[PurePath] = []
        if is_any_erf_type_file(self._filepath) or is_rim_file(self._filepath):
            nested_paths.append(self._filepath)

        r_parent_filepath: Path = self._filepath.parent
        while (
            (
                ResourceType.from_extension(r_parent_filepath.suffix).name
                in (
                    ResourceType.ERF,
                    ResourceType.MOD,
                    ResourceType.SAV,
                    ResourceType.RIM,
                    ResourceType.BIF,
                )
            )
            and not r_parent_filepath.exists()
            and not r_parent_filepath.is_dir()
        ):
            nested_paths.append(r_parent_filepath)
            self._filepath = r_parent_filepath
            r_parent_filepath = self._filepath.parent

        det_restype: ResourceType = ResourceType.from_extension(r_parent_filepath.suffix)
        if det_restype is ResourceType.RIM:
            bioware_archive = read_rim(self._filepath)
        elif det_restype is ResourceType.ERF:
            bioware_archive = read_erf(self._filepath)
        elif det_restype is ResourceType.BIF:
            bioware_archive = read_bif(self._filepath)
        else:
            raise ValueError(f"Unexpected resource type: {det_restype}")
        nested_capsules: list[tuple[PurePath, ERF | RIM | BIF]] = [
            (
                self._filepath,
                bioware_archive,
            )
        ]
        for capsule_path in reversed(nested_paths[:-1]):
            nested_erf_or_rim_data: bytes | None = bioware_archive.get(
                capsule_path.stem,
                ResourceType.from_extension(capsule_path.suffix),
            )
            if nested_erf_or_rim_data is None:
                msg: str = f"You must save the ERFEditor for '{capsule_path.relative_to(r_parent_filepath)}' to before modifying its nested resources. Do so and try again."
                raise ValueError(msg)

            bioware_archive = read_rim(nested_erf_or_rim_data) if ResourceType.from_extension(capsule_path.suffix) is ResourceType.RIM else read_erf(nested_erf_or_rim_data)
            nested_capsules.append((capsule_path, bioware_archive))

        this_erf_or_rim = None
        for index, (_capsule_path, this_erf_or_rim) in enumerate(reversed(nested_capsules)):
            if index == 0:
                if not self._is_capsule_editor:
                    this_erf_or_rim.set_data(self._resname, self._restype, bytes(data))
                continue
            child_index: int = len(nested_capsules) - index
            child_capsule_path, child_erf_or_rim = nested_capsules[child_index]
            if self._filepath != child_capsule_path or not self._is_capsule_editor:
                data = bytearray()
                write_erf(child_erf_or_rim, data) if isinstance(child_erf_or_rim, ERF) else write_rim(child_erf_or_rim, data)
            this_erf_or_rim.set_data(child_capsule_path.stem, ResourceType.from_extension(child_capsule_path.suffix), bytes(data))

        assert this_erf_or_rim is not None, "this_erf_or_rim is None somehow? This should be impossible."
        write_erf(this_erf_or_rim, self._filepath) if isinstance(this_erf_or_rim, ERF) else write_rim(this_erf_or_rim, self._filepath)
        self.sig_saved_file.emit(str(self._filepath), self._resname, self._restype, bytes(data))

    def _save_ends_with_erf(
        self,
        data: bytes,
        data_ext: bytes,
    ):
        erftype: ERFType = ERFType.from_extension(self._filepath)

        if self._filepath.is_file():
            erf: ERF = read_erf(self._filepath)
        elif self._filepath.with_suffix(".rim").is_file():
            module.rim_to_mod(self._filepath)
            erf = read_erf(self._filepath)
        else:
            print(f"Saving '{self._resname}.{self._restype}' to a blank new {erftype.name} file at '{self._filepath}'")
            erf = ERF(erftype)
        erf.erf_type = erftype

        if self._restype is ResourceType.MDL:
            erf.set_data(self._resname, ResourceType.MDX, data_ext)

        erf.set_data(self._resname, self._restype, data)

        write_erf(erf, self._filepath)
        self.sig_saved_file.emit(str(self._filepath), self._resname, self._restype, bytes(data))
        if self._installation is not None and self._filepath.parent == self._installation.module_path():
            self._installation.reload_module(self._filepath.name)

    def _save_ends_with_other(
        self,
        data: bytes,
        data_ext: bytes,
    ):
        self._filepath.write_bytes(data)
        if self._restype is ResourceType.MDL:
            self._filepath.with_suffix(".mdx").write_bytes(data_ext)
        self.sig_saved_file.emit(str(self._filepath), self._resname, self._restype, bytes(data))

    def open(self):
        filepath_str, _filter = QFileDialog.getOpenFileName(self, "Open file", "", self._open_filter, "")
        if not str(filepath_str).strip():
            return
        r_filepath = Path(filepath_str)

        if is_capsule_file(r_filepath) and f"Load from module ({self.CAPSULE_FILTER})" in self._open_filter:
            self._load_module_from_dialog_info(r_filepath)
        else:
            data: bytes = r_filepath.read_bytes()
            res_ident: ResourceIdentifier = ResourceIdentifier.from_path(r_filepath).validate()
            self.load(r_filepath, res_ident.resname, res_ident.restype, data)

    def _load_module_from_dialog_info(
        self,
        r_filepath: Path,
    ):
        dialog = LoadFromModuleDialog(Capsule(r_filepath), self._read_supported)
        if dialog.exec():
            resname: str | None = dialog.resname()
            restype: ResourceType | None = dialog.restype()
            data: bytes | None = dialog.data()
            assert resname is not None
            assert restype is not None
            assert data is not None
            self.load(r_filepath, resname, restype, data)

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

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        self._filepath = Path(filepath)
        self._resname = resref
        self._restype = restype
        self._revert = data
        menu_bar: QMenuBar | None = cast(Optional[QMenuBar], self.menuBar())
        assert menu_bar is not None, "Menu bar is None somehow? This should be impossible."
        menu_bar_actions: Sequence[_QAction] = menu_bar.actions()  # pyright: ignore[reportAssignmentType]
        if len(menu_bar_actions) > 0:
            menu: _QMenu | None = menu_bar_actions[0].menu()
            assert menu is not None, "Menu is somehow None"
            for action in menu_bar_actions:
                if action.text() == "Revert":
                    action.setEnabled(True)
                    break
        self.refresh_window_title()
        self.sig_loaded_file.emit(str(self._filepath), self._resname, self._restype, data)

    def new(self):
        self._revert = b""
        self._filepath = self.setup_extract_path() / f"{self._resname}.{self._restype.extension}"
        menu_bar: QMenuBar | None = cast(Optional[QMenuBar], self.menuBar())
        assert menu_bar is not None, "Menu bar is None somehow? This should be impossible."
        menu: _QMenu | None = menu_bar.actions()[0].menu()
        assert menu is not None, "Menu is somehow None"
        menu_bar_actions: Sequence[_QAction] = menu.actions()  # pyright: ignore[reportAssignmentType]
        if len(menu_bar_actions) > 0:
            for action in menu_bar_actions:
                if action.text() != "Revert":
                    continue
                action.setEnabled(False)
        self.refresh_window_title()
        self.sig_new_file.emit()

    def revert(self):
        if self._revert is None:
            print("No data to revert from")
            self.blink_window()
            return
        self.load(self._filepath, self._resname, self._restype, self._revert)

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

    def play_byte_source_media(
        self,
        data: bytes | None,
    ) -> bool:
        if not data:
            self.blink_window()
            return False
        if qtpy.QT5:
            from qtpy.QtMultimedia import QMediaContent  # pyright: ignore[reportAttributeAccessIssue]

            self.media_player.buffer = buffer = QBuffer(self)
            buffer.setData(data)
            buffer.open(QIODevice.OpenModeFlag.ReadOnly)
            self.media_player.player.setMedia(QMediaContent(), buffer)  # pyright: ignore[reportAttributeAccessIssue]
            QTimer.singleShot(0, self.media_player.player.play)

        elif qtpy.QT6:
            from qtpy.QtMultimedia import QAudioOutput

            # Create buffer and load data
            buffer = QBuffer(self)
            buffer.setData(data)
            buffer.open(QIODevice.OpenModeFlag.ReadOnly)

            # Set up player
            player: PyQt6MediaPlayer | PySide6MediaPlayer = cast(Any, self.media_player.player)
            audio_output = QAudioOutput(self)
            audio_output.setVolume(1)
            player.setAudioOutput(audio_output)

            # Use the buffer directly instead of a file
            player.setSourceDevice(buffer)
            player.play()
        return True

    def play_sound(
        self,
        resname: str,
        order: list[SearchLocation] | None = None,
    ) -> bool:
        """Plays a sound resource."""
        if not resname or not resname.strip() or self._installation is None:
            self.blink_window(sound=False)
            return False

        self.media_player.player.stop()

        data: bytes | None = self._installation.sound(
            resname,
            order
            if order is not None
            else [
                SearchLocation.MUSIC,
                SearchLocation.VOICE,
                SearchLocation.SOUND,
                SearchLocation.OVERRIDE,
                SearchLocation.CHITIN,
            ],
        )
        if not data:
            self.blink_window(sound=False)
        return self.play_byte_source_media(data)

    def remove_temp_audio_file(
        self,
        status: QMediaPlayer.MediaStatus,
        file_path: os.PathLike | str,
    ):
        if status != QMediaPlayer.MediaStatus.EndOfMedia:
            return
        try:
            self.media_player.player.stop()
            QTimer.singleShot(33, lambda: remove_any(file_path))
        except OSError:
            RobustLogger().exception(f"Error removing temporary file '{file_path}'")

    def filepath(self) -> str | None:
        return str(self._filepath)
