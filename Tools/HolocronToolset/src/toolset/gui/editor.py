from __future__ import annotations

import tempfile

from abc import abstractmethod
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Callable, cast

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QBuffer, QIODevice, QPoint, QTimer, QUrl, Qt
from qtpy.QtGui import QGuiApplication, QIcon, QPixmap
from qtpy.QtMultimedia import QMediaPlayer
from qtpy.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QShortcut,
    QSlider,
    QStyle,
    QWidget,
)

from pykotor.common.module import Module
from pykotor.common.stream import BinaryReader
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.erf import ERFType, read_erf, write_erf
from pykotor.resource.formats.erf.erf_data import ERF
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff
from pykotor.resource.formats.rim import read_rim, write_rim
from pykotor.resource.type import ResourceType
from pykotor.tools import module
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_capsule_file, is_rim_file
from pykotor.tools.path import CaseAwarePath
from toolset.gui.dialogs.load_from_module import LoadFromModuleDialog
from toolset.gui.dialogs.save.to_bif import BifSaveDialog, BifSaveOption
from toolset.gui.dialogs.save.to_module import SaveToModuleDialog
from toolset.gui.dialogs.save.to_rim import RimSaveDialog, RimSaveOption
from toolset.gui.widgets.settings.installations import GlobalSettings
from ui import stylesheet_resources  # noqa: PLC0415, F401, I001  # pylint: disable=C0415
from utility.error_handling import assert_with_variable_trace, format_exception_with_variables, universal_simplify_exception
from utility.logger_util import RobustRootLogger, remove_any
from utility.system.path import Path

if qtpy.API_NAME == "PySide2":
    from toolset.rcc import resources_rc_pyside2  # noqa: PLC0415, F401  # pylint: disable=C0415
elif qtpy.API_NAME == "PySide6":
    from toolset.rcc import resources_rc_pyside6  # noqa: PLC0415, F401  # pylint: disable=C0415
elif qtpy.API_NAME == "PyQt5":
    from toolset.rcc import resources_rc_pyqt5  # noqa: PLC0415, F401  # pylint: disable=C0415
elif qtpy.API_NAME == "PyQt6":
    from toolset.rcc import resources_rc_pyqt6  # noqa: PLC0415, F401  # pylint: disable=C0415
else:
    raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

if TYPE_CHECKING:
    import os

    from PyQt6.QtMultimedia import QMediaPlayer as PyQt6MediaPlayer
    from PySide6.QtMultimedia import QMediaPlayer as PySide6MediaPlayer
    from qtpy.QtGui import QFocusEvent, QMouseEvent, QShowEvent
    from typing_extensions import Literal

    from pykotor.common.language import LocalizedString
    from pykotor.resource.formats.rim.rim_data import RIM
    from toolset.data.installation import HTInstallation
    from utility.system.path import PurePath


class MediaPlayerWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.buffer: QBuffer = QBuffer(self)
        self.player: QMediaPlayer = QMediaPlayer(self)
        self.setupMediaPlayer()
        self._setupSignals()

        self.hideWidget()

    def setupMediaPlayer(self):
        self.speed_levels: list[float] = [1, 1.25, 1.5, 2, 5, 10]
        self.current_speed_index: int = 0

        self.playPauseButton: QPushButton = QPushButton()
        self.playPauseButton.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.playPauseButton.setFixedSize(24, 24)

        self.stopButton: QPushButton = QPushButton()
        self.stopButton.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.stopButton.setFixedSize(24, 24)

        self.muteButton: QPushButton = QPushButton()
        self.muteButton.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))
        self.muteButton.setFixedSize(24, 24)

        buttonLayout: QHBoxLayout = QHBoxLayout()
        for button in [self.playPauseButton, self.stopButton, self.muteButton]:
            buttonLayout.addWidget(button)
            buttonLayout.setAlignment(button, Qt.AlignmentFlag.AlignBottom)
        self.timeLabel: QLabel = QLabel("00:00 / 00:00")
        self.setupTimeSlider()

        buttonLayout.addWidget(self.timeLabel)
        buttonLayout.addWidget(self.timeSlider, 1)

        buttonLayout.setContentsMargins(0, 0, 0, 0)
        buttonLayout.setSpacing(0)
        self.setLayout(buttonLayout)
        self.hideWidget()

    def setupTimeSlider(self):
        self.timeSlider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self.timeSlider.setMouseTracking(True)
        self.dragPosition = QPoint()

        def sliderMousePressEvent(ev: QMouseEvent, slider: QSlider = self.timeSlider):
            if ev.button() == Qt.LeftButton:
                self.player.pause()
                self.dragPosition = ev.pos()  # Store click position
                ev.accept()
            super(QSlider, slider).mousePressEvent(ev)
        def sliderMouseMoveEvent(ev: QMouseEvent, slider: QSlider = self.timeSlider):
            if ev.buttons() == Qt.LeftButton and not self.dragPosition.isNull():
                value = int((ev.pos().x() / slider.width()) * slider.maximum())
                slider.setValue(value)
                self.player.setPosition(value)
                ev.accept()
            super(QSlider, slider).mouseMoveEvent(ev)
        def sliderMouseReleaseEvent(ev: QMouseEvent, slider: QSlider = self.timeSlider):
            if ev.button() == Qt.LeftButton and not self.dragPosition.isNull():
                # Set the final value and clear dragPosition
                value = int((ev.pos().x() / slider.width()) * slider.maximum())
                slider.setValue(value)
                self.player.setPosition(value)
                self.player.play()
                self.dragPosition = QPoint()  # Reset drag position
                ev.accept()
            super(QSlider, slider).mouseReleaseEvent(ev)
        def sliderFocusOutEvent(ev: QFocusEvent, slider: QSlider = self.timeSlider):
            if not self.dragPosition.isNull():
                value = int((self.dragPosition.x() / slider.width()) * slider.maximum())
                slider.setValue(value)
                self.player.setPosition(value)
                self.player.play()
                ev.accept()
            super(QSlider, slider).focusOutEvent(ev)
        self.timeSlider.mouseMoveEvent = sliderMouseMoveEvent  # type: ignore[method-override]
        self.timeSlider.mousePressEvent = sliderMousePressEvent  # type: ignore[method-override]
        self.timeSlider.mouseReleaseEvent = sliderMouseReleaseEvent  # type: ignore[method-override]
        self.timeSlider.focusOutEvent = sliderFocusOutEvent  # type: ignore[method-override]

    def playPauseButtonClick(self):
        if self.player.state() == QMediaPlayer.State.PlayingState:
            self.playPauseButton.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
            self.player.pause()
        else:
            self.playPauseButton.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            self.player.play()

    def _setupSignals(self):
        self.player.mediaStatusChanged.connect(self.mediaStateChanged)
        self.player.positionChanged.connect(self.positionChanged)
        self.player.durationChanged.connect(self.durationChanged)
        self.player.stateChanged.connect(self.stateChanged)

        self.playPauseButton.clicked.connect(self.playPauseButtonClick)
        self.stopButton.clicked.connect(lambda *args: self.player.stop() or self.hideWidget())
        self.muteButton.clicked.connect(self.toggleMute)

    def stateChanged(self, state: QMediaPlayer.MediaStatus):
        if state == QMediaPlayer.State.PlayingState:
            self.showWidget()

    def format_time(self, msecs: int) -> str:
        secs = msecs // 1000
        mins = secs // 60
        hrs = mins // 60
        return f"{hrs:02}:{mins % 60:02}:{secs % 60:02}"

    def mediaStateChanged(self, state: QMediaPlayer.MediaStatus):
        if state == QMediaPlayer.MediaStatus.EndOfMedia:
            self.timeSlider.setValue(self.timeSlider.maximum())
            self.hideWidget()
        if state == QMediaPlayer.State.PlayingState:
            self.playPauseButton.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        else:
            self.playPauseButton.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))

    def changePlaybackSpeed(self, direction: int):
        """Some qt bug prevents this from working properly. Requires a start and a play in order to take effect."""
        self.current_speed_index = max(0, min(len(self.speed_levels) - 1, self.current_speed_index + direction))
        newRate = self.speed_levels[self.current_speed_index]
        wasPlaying = self.player.state() == QMediaPlayer.State.PlayingState
        currentPosition = self.player.position()
        self.player.setPlaybackRate(newRate)
        self.player.setPosition(currentPosition)
        if wasPlaying:
            self.player.play()

    def toggleMute(self):
        self.player.setMuted(not self.player.isMuted())
        if self.player.isMuted():
            self.muteButton.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolumeMuted))
        else:
            self.muteButton.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))

    def positionChanged(self, position: int):
        if not self.timeSlider.isSliderDown():
            self.timeSlider.setValue(position)
        current_time = self.format_time(position)
        total_time = self.format_time(self.timeSlider.maximum())
        self.timeLabel.setText(f"{current_time} / {total_time}")

    def durationChanged(self, duration: int):
        self.timeSlider.setRange(0, duration)
        total_time = self.format_time(duration)
        current_time = self.format_time(self.timeSlider.value())
        self.timeLabel.setText(f"{current_time} / {total_time}")

    def showWidget(self):
        self.show()
        self.playPauseButton.show()
        self.stopButton.show()
        self.muteButton.show()
        self.timeLabel.show()
        self.timeSlider.show()

    def hideWidget(self):
        self.hide()
        self.playPauseButton.hide()
        self.stopButton.hide()
        self.muteButton.hide()
        self.timeLabel.hide()
        self.timeSlider.hide()

    def setVisible(self, visible: bool):  # noqa: FBT001
        """Override to control visibility based on player state."""
        if self.player.state() == QMediaPlayer.State.PlayingState:
            return
        super().setVisible(visible)

    def showEvent(self, event: QShowEvent):
        """Override to prevent showing unless playing."""
        if self.player.state() != QMediaPlayer.State.PlayingState:
            return
        super().showEvent(event)


# TODO: Creating a child editor from this class is not intuitive, document the requirements at some point.
class Editor(QMainWindow):
    """Editor is a base class for all file-specific editors.

    Provides methods for saving and loading files that are stored directly in folders and for files that are encapsulated in a MOD or RIM.
    """

    newFile = QtCore.Signal()
    savedFile = QtCore.Signal(object, object, object, object)
    loadedFile = QtCore.Signal(object, object, object, object)

    CAPSULE_FILTER = "*.mod *.erf *.rim *.sav"

    def __init__(
        self,
        parent: QWidget | None,
        title: str,
        iconName: str,
        readSupported: list[ResourceType],
        writeSupported: list[ResourceType],
        installation: HTInstallation | None = None,
    ):
        """Initializes the editor.

        Args:
        ----
            parent: QWidget: The parent widget
            title: str: The title of the editor window
            iconName: str: The name of the icon to display
            readSupported: list[ResourceType]: The supported resource types for reading
            writeSupported: list[ResourceType]: The supported resource types for writing
            installation: HTInstallation | None: The installation context

        Initializes editor properties:
            - Sets up title, icon and parent widget
            - Sets supported read/write resource types
            - Initializes file filters for opening and saving
            - Sets up other editor properties.
        """
        super().__init__(parent)
        self._is_capsule_editor: bool = False
        self._installation: HTInstallation | None = installation
        self._logger = RobustRootLogger()
        self._global_settings: GlobalSettings = GlobalSettings()

        self._filepath: Path | None = None
        self._resname: str | None = None
        self._restype: ResourceType | None = None
        self._revert: bytes | None = None

        writeSupported = readSupported.copy() if readSupported is writeSupported else writeSupported
        additional_formats = {"XML", "JSON", "CSV", "ASCII", "YAML"}
        for add_format in additional_formats:
            readSupported.extend(
                ResourceType.__members__[f"{restype.name}_{add_format}"]
                for restype in readSupported if f"{restype.name}_{add_format}" in ResourceType.__members__
            )
            writeSupported.extend(
                ResourceType.__members__[f"{restype.name}_{add_format}"]
                for restype in writeSupported if f"{restype.name}_{add_format}" in ResourceType.__members__
            )
        self._readSupported: list[ResourceType] = readSupported
        self._writeSupported: list[ResourceType] = writeSupported
        self._global_settings: GlobalSettings = GlobalSettings()

        self._editorTitle: str = title
        self.setWindowTitle(title)
        self._setupIcon(iconName)
        self.mediaPlayer: MediaPlayerWidget = MediaPlayerWidget(self)
        self.layout().addWidget(self.mediaPlayer)

        self._saveFilter: str = "All valid files ("
        for resource in writeSupported:
            self._saveFilter += f'*.{resource.extension}{"" if writeSupported[-1] == resource else " "}'
        self._saveFilter += f" {self.CAPSULE_FILTER});;"
        for resource in writeSupported:
            self._saveFilter += f"{resource.category} File (*.{resource.extension});;"
        self._saveFilter += f"Save into module ({self.CAPSULE_FILTER})"

        self._openFilter: str = "All valid files ("
        for resource in readSupported:
            self._openFilter += f'*.{resource.extension}{"" if readSupported[-1] == resource else " "}'
        self._openFilter += f" {self.CAPSULE_FILTER});;"
        for resource in readSupported:
            self._openFilter += f"{resource.category} File (*.{resource.extension});;"
        self._openFilter += f"Load from module ({self.CAPSULE_FILTER})"


    def showEvent(self, event: QShowEvent):
        # Set minimum size based on the current size
        self.setMinimumSize(
            self.size().width() + QApplication.font().pointSize() * 2,
            self.size().height(),
        )
        #QTimer.singleShot(0, lambda event=event: self.adjustPosition(event))

    def adjustPosition(self, event: QShowEvent | None = None):  # sourcery skip: extract-method
        if event is not None:
            super().showEvent(event)
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        window_geometry = self.geometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        self.move(x, y-50)

        main_window = next(
            (
                widget
                for widget in QApplication.topLevelWidgets()
                if isinstance(widget, QMainWindow)
                and widget.__class__.__name__ == "ToolWindow"
            ),
            None,
        )

        if not main_window:
            self._logger.error("Main ToolWindow not found")
            return

        main_geometry = main_window.geometry()
        editor_geometry = self.geometry()
        if editor_geometry.intersects(main_geometry):
            new_x = main_geometry.right() + 10
            if new_x + editor_geometry.width() > screen_geometry.right():
                new_x = main_geometry.left() - editor_geometry.width() - 10
            new_y = main_geometry.top()
            if new_y + editor_geometry.height() > screen_geometry.bottom():
                new_y = screen_geometry.bottom() - editor_geometry.height()
            if new_x < screen_geometry.left():
                new_x = screen_geometry.left()
            if new_y < screen_geometry.top():
                new_y = screen_geometry.top()
            self.move(new_x, new_y-50)
            main_geometry = main_window.geometry()
            editor_geometry = self.geometry()
            if editor_geometry.intersects(main_geometry):
                new_mw_x = editor_geometry.width()+10
                if new_mw_x < screen_geometry.left():
                    new_mw_x = screen_geometry.left()
                main_window.move(new_mw_x, main_window.pos().y())

    def setSecondaryWidgetPosition(self, widget: QWidget, position: Literal["left", "right", "top", "bottom"]):
        if isinstance(widget, QDockWidget):
            widget.setFloating(True)

        widget.resize(widget.width(), self.height())
        self.move(self.pos().x(), self.pos().y() - 50)

        if position == "right":
            relevant_editor_coord = self.mapToGlobal(self.rect().topRight())
        elif position == "left":
            relevant_editor_coord = self.mapToGlobal(self.rect().topLeft())
        elif position == "top":
            relevant_editor_coord = self.mapToGlobal(self.rect().topLeft())
        elif position == "bottom":
            relevant_editor_coord = self.mapToGlobal(self.rect().bottomLeft())
        else:
            raise ValueError("Invalid position argument. Must be 'left', 'right', 'top', or 'bottom'.")

        if position == "right":
            widget.move(relevant_editor_coord.x(), relevant_editor_coord.y())
        elif position == "left":
            widget.move(relevant_editor_coord.x() - widget.width(), relevant_editor_coord.y())
        elif position == "top":
            widget.move(relevant_editor_coord.x(), relevant_editor_coord.y() - widget.height())
        elif position == "bottom":
            widget.move(relevant_editor_coord.x(), relevant_editor_coord.y())

        editor_bottom_y = self.geometry().bottom()
        dock_bottom_y = widget.geometry().bottom()
        title_bar_height = dock_bottom_y - editor_bottom_y

        if position in ("right", "left", "bottom"):
            widget.move(relevant_editor_coord.x(), relevant_editor_coord.y() - title_bar_height)
        elif position == "top":
            widget.move(relevant_editor_coord.x() - widget.width(), relevant_editor_coord.y() - widget.height() - title_bar_height)

        # Ensure the widget and the editor are on screen and move them if necessary
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        widget_geometry = widget.geometry()
        editor_geometry = self.geometry()

        # Check if either the widget or the editor is off screen
        if not screen_geometry.contains(widget_geometry) or not screen_geometry.contains(editor_geometry):
            move_x = move_y = 0

            if widget_geometry.right() > screen_geometry.right():
                move_x = screen_geometry.right() - widget_geometry.right()
            elif widget_geometry.left() < screen_geometry.left():
                move_x = screen_geometry.left() - widget_geometry.left()

            if widget_geometry.bottom() > screen_geometry.bottom():
                move_y = screen_geometry.bottom() - widget_geometry.bottom()
            elif widget_geometry.top() < screen_geometry.top():
                move_y = screen_geometry.top() - widget_geometry.top()

            self.move(self.x() + move_x, self.y() + move_y)
            widget.move(widget.x() + move_x, widget.y() + move_y)

        widget.show()

    def _setupMenus(self):
        """Sets up menu actions and keyboard shortcuts.

        Processing Logic:
        ----------------
            - Loops through menu actions and connects signals for New, Open, Save, Save As, Revert and Exit
            - Sets Revert action to disabled
            - Connects keyboard shortcuts for New, Open, Save, Save As, Revert and Exit.
        """
        menubar = self.menuBar().actions()[0].menu()
        if not isinstance(menubar, QMenu):
            raise TypeError(f"self.menuBar().actions()[0].menu() returned a {type(menubar).__name__} object, expected QMenu.")
        for action in menubar.actions():
            if action.text() == "New":  # sourcery skip: extract-method
                action.triggered.connect(self.new)
            if action.text() == "Open":
                action.triggered.connect(self.open)
            if action.text() == "Save":
                action.triggered.connect(self.save)
            if action.text() == "Save As":
                action.triggered.connect(self.saveAs)
            if action.text() == "Revert":
                action.triggered.connect(self.revert)
            if action.text() == "Revert":
                action.setEnabled(False)
            if action.text() == "Exit":
                action.triggered.connect(self.close)  # type: ignore[]
        QShortcut("Ctrl+N", self).activated.connect(self.new)
        QShortcut("Ctrl+O", self).activated.connect(self.open)
        QShortcut("Ctrl+S", self).activated.connect(self.save)
        QShortcut("Ctrl+Shift+S", self).activated.connect(self.saveAs)
        QShortcut("Ctrl+R", self).activated.connect(self.revert)
        QShortcut("Ctrl+Q", self).activated.connect(self.exit)

    def _setupIcon(self, iconName: str):
        iconVersion = "x" if self._installation is None else "2" if self._installation.tsl else "1"
        iconPath = f":/images/icons/k{iconVersion}/{iconName}.png"
        self.setWindowIcon(QIcon(QPixmap(iconPath)))

    def refreshWindowTitle(self):
        """Refreshes the window title based on the current state of the editor."""
        installationName = "No Installation" if self._installation is None else self._installation.name
        if self._filepath is None or self._resname is None or self._restype is None:
            self.setWindowTitle(f"{self._editorTitle}({installationName})")
            return

        relpath = self._filepath.relative_to(self._filepath.parent.parent) if self._filepath.parent.parent.name else self._filepath.parent
        if is_bif_file(relpath) or is_capsule_file(self._filepath):
            from toolset.gui.editors.erf import ERFEditor
            if not isinstance(self, ERFEditor):
                relpath /= f"{self._resname}.{self._restype.extension}"
        self.setWindowTitle(f"{relpath} - {self._editorTitle}({installationName})")

    def getOpenedFileName(self) -> str:
        if self._filepath is not None and self._filepath.name and self._restype is not None:
            return (
                f"{self._resname or ''}.{self._restype.extension}"
                if is_bif_file(self._filepath) or is_capsule_file(self._filepath)
                else self._filepath.name
            )
        return ""

    def saveAs(self):
        """Saves the file with the selected filepath.

        Processing Logic:
        ----------------
            - Gets the selected filepath and filter from a file dialog
            - Checks if the filepath is a capsule file and filter is for modules
            - If so, shows a dialog to select resource reference and type
            - Sets filepath, reference and type attributes from selection
            - Calls the save method
            - Refreshes the window title
            - Enables the Revert menu item
        """
        filepath_str, _filter = QFileDialog.getSaveFileName(self, "Save As", self.getOpenedFileName(), self._saveFilter, "")
        if not filepath_str:
            return
        error_msg, e, invalid = "", None, False
        try:
            identifier = ResourceIdentifier.from_path(filepath_str)
            if identifier.restype.is_invalid:
                invalid = True
        except ValueError as e:
            invalid = True
            RobustRootLogger().exception("ValueError raised, assuming invalid filename/extension '%s'", filepath_str)
            error_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
        if invalid:
            msgBox = QMessageBox(
                QMessageBox.Icon.Critical,
                "Invalid filename/extension",
                f"Check the filename and try again. Could not save!{f'<br><br>{error_msg}' if error_msg else ''}",
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            if error_msg:
                msgBox.setDetailedText(format_exception_with_variables(e))
            msgBox.exec_()
            return

        if is_capsule_file(filepath_str) and f"Save into module ({self.CAPSULE_FILTER})" in self._saveFilter:
            if self._resname is None or self._restype is None:
                self._resname = "new"
                self._restype = self._writeSupported[0]

            dialog2 = SaveToModuleDialog(self._resname, self._restype, self._writeSupported)
            if dialog2.exec_():
                self._resname = dialog2.resname()
                self._restype = dialog2.restype()
                self._filepath = Path(filepath_str)
        else:
            self._filepath = Path(filepath_str)
            self._resname, self._restype = identifier.unpack()
        self.save()

        self.refreshWindowTitle()
        for action in self.menuBar().actions()[0].menu().actions():
            if action.text() == "Revert":
                action.setEnabled(True)

    def save(self):
        """Saves the current data to file.

        Processing Logic:
        ----------------
            - Builds the data and extension to save
            - Checks the file extension and calls the appropriate save method
            - Catches any exceptions and writes to an error log.
        """
        if self._filepath is None:
            self.saveAs()
            return

        try:
            data, data_ext = self.build()
            if data is None:  # HACK: nsseditor
                return
            from toolset.gui.editors.gff import GFFEditor

            if (  # HACK: we need a proper save editor, but this is better than nothing.
                self._global_settings.attemptKeepOldGFFFields
                and self._restype is not None
                and self._restype.is_gff()
                and not isinstance(self, GFFEditor)
                and self._revert is not None
            ):
                print("Adding deleted fields from original gff into final gff.")
                old_gff = read_gff(self._revert)
                new_gff = read_gff(data)
                new_gff.root.add_missing(old_gff.root)
                data = bytes_gff(new_gff)
            self._revert = data

            self.refreshWindowTitle()

            if is_bif_file(self._filepath):
                self._saveEndsWithBif(data, data_ext)
            elif is_capsule_file(self._filepath.parent):
                self._saveNestedCapsule(data, data_ext)
            elif is_rim_file(self._filepath.name):
                self._saveEndsWithRim(data, data_ext)
            elif is_any_erf_type_file(self._filepath):
                self._saveEndsWithErf(data, data_ext)
            else:
                self._saveEndsWithOther(data, data_ext)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self.blinkWindow()
            RobustRootLogger().critical("Failed to write to file", exc_info=True)
            msgBox = QMessageBox(QMessageBox.Icon.Critical, "Failed to write to file", str(universal_simplify_exception(e)).replace("\n", "<br>"))
            msgBox.setDetailedText(format_exception_with_variables(e))
            msgBox.exec_()

    def _saveEndsWithBif(self, data: bytes, data_ext: bytes):
        """Saves data if dialog returns specific options.

        Args:
        ----
            data: bytes - Data to save
            data_ext: bytes - File extension

        Processing Logic:
        ----------------
            - Show save dialog to choose MOD or override save
            - If MOD chosen, show second dialog to set resref/restype
            - Set filepath based on option
            - Call save method.
        """
        dialog = BifSaveDialog(self)
        dialog.exec_()
        if dialog.option == BifSaveOption.MOD:
            str_filepath, filter = QFileDialog.getSaveFileName(self, "Save As", "", ".MOD File (*.mod)", "")
            if not str_filepath.strip():
                print(f"User cancelled filepath lookup in _saveEndsWithBif ({self._resname}.{self._restype})")
                return

            assert self._resname is not None
            assert self._restype is not None
            r_filepath = Path(str_filepath)
            dialog2 = SaveToModuleDialog(self._resname, self._restype, self._writeSupported)
            if dialog2.exec_():
                self._resname = dialog2.resname()
                self._restype = dialog2.restype()
                self._filepath = r_filepath
                self.save()
        elif dialog.option == BifSaveOption.Override:
            assert self._resname is not None
            assert self._restype is not None
            assert self._installation is not None
            self._filepath = self._installation.override_path() / f"{self._resname}.{self._restype.extension}"
            self.save()
        else:
            print(f"User closed out of BifSaveDialog in _saveEndsWithBif (({self._resname}.{self._restype}))")

    def _saveEndsWithRim(self, data: bytes, data_ext: bytes):
        """Saves resource data to a RIM file.

        Args:
        ----
            data: {Bytes containing resource data}
            data_ext: {Bytes containing additional resource data like MDX for MDL}.

        Processing Logic:
        ----------------
        Saves resource data to RIM file:
            - Checks for RIM saving disabled setting and shows dialog
            - Writes data to RIM file
            - Updates installation cache.
        """  # sourcery skip: class-extract-method
        assert self._filepath is not None, assert_with_variable_trace(self._filepath is not None)
        assert self._resname is not None, assert_with_variable_trace(self._resname is not None)
        assert self._restype is not None, assert_with_variable_trace(self._restype is not None)

        if self._global_settings.disableRIMSaving:
            dialog = RimSaveDialog(self)
            dialog.exec_()
            if dialog.option == RimSaveOption.MOD:
                folderpath: Path = self._filepath.parent
                filename: str = f"{Module.find_root(self._filepath)}.mod"
                self._filepath = folderpath / filename
                # Re-save with the updated filepath
                self.save()
            elif dialog.option == RimSaveOption.Override:
                assert self._installation is not None
                self._filepath = self._installation.override_path() / f"{self._resname}.{self._restype.extension}"
                self.save()
            return

        rim: RIM = read_rim(self._filepath)

        # MDL is a special case - we need to save the MDX file with the MDL file.
        if self._restype is ResourceType.MDL:
            rim.set_data(self._resname, ResourceType.MDX, data_ext)

        rim.set_data(self._resname, self._restype, data)

        write_rim(rim, self._filepath)
        self.savedFile.emit(str(self._filepath), self._resname, self._restype, data)

        # Update installation cache
        if self._installation is not None:
            self._installation.reload_module(self._filepath.name)

    def _saveNestedCapsule(self, data: bytes, data_ext: bytes):
        assert self._filepath is not None, assert_with_variable_trace(self._filepath is not None)
        assert self._resname is not None, assert_with_variable_trace(self._resname is not None)
        assert self._restype is not None, assert_with_variable_trace(self._restype is not None)

        # Determine the physical file and the nested paths.
        c_filepath: CaseAwarePath = CaseAwarePath.pathify(self._filepath)
        nested_paths: list[PurePath] = []
        if is_any_erf_type_file(c_filepath) or is_rim_file(c_filepath):
            nested_paths.append(c_filepath)

        c_parent_filepath = c_filepath.parent
        while (  # Iterate all parents until we find a physical folder on disk.
            ResourceType.from_extension(c_parent_filepath.suffix).name
            in (ResourceType.ERF, ResourceType.MOD, ResourceType.SAV, ResourceType.RIM)
        ) and not c_parent_filepath.safe_isdir():
            nested_paths.append(c_parent_filepath)
            c_filepath = c_parent_filepath
            c_parent_filepath = c_filepath.parent

        # At this point, c_filepath points to the physical ERF/RIM on disk
        # and c_parent_filepath points to the physical folder containing the file.
        erf_or_rim: ERF | RIM = read_rim(c_filepath) if ResourceType.from_extension(c_parent_filepath.suffix) is ResourceType.RIM else read_erf(c_filepath)
        nested_capsules: list[tuple[PurePath, ERF | RIM]] = [(c_filepath, erf_or_rim)]
        for capsule_path in reversed(nested_paths[:-1]):
            nested_erf_or_rim_data = erf_or_rim.get(capsule_path.stem, ResourceType.from_extension(capsule_path.suffix))
            if nested_erf_or_rim_data is None:  # TODO(th3w1zard1): loop through all windows and send hotkey ctrl+s?
                msg = f"You must save the ERFEditor for '{capsule_path.relative_to(c_parent_filepath)}' to before modifying its nested resources. Do so and try again."
                raise ValueError(msg)

            erf_or_rim = read_rim(nested_erf_or_rim_data) if ResourceType.from_extension(capsule_path.suffix) is ResourceType.RIM else read_erf(nested_erf_or_rim_data)
            nested_capsules.append((capsule_path, erf_or_rim))

        # Let's now save each erf/rim to its parent.
        for index, (capsule_path, this_erf_or_rim) in enumerate(reversed(nested_capsules)):
            rel_capsule_path = capsule_path.relative_to(c_parent_filepath)
            if index == 0:
                if not self._is_capsule_editor:
                    print(f"Saving non ERF/RIM '{self._resname}.{self._restype.extension}' to '{rel_capsule_path}'")
                    this_erf_or_rim.set_data(self._resname, self._restype, data)
                continue
            child_index = len(nested_capsules) - index
            child_capsule_path, child_erf_or_rim = nested_capsules[child_index]
            if self._filepath != child_capsule_path or not self._is_capsule_editor:
                data = bytearray()
                print(f"Saving {child_capsule_path.relative_to(c_parent_filepath)} to {capsule_path.relative_to(c_parent_filepath)}")
                write_erf(child_erf_or_rim, data) if isinstance(child_erf_or_rim, ERF) else write_rim(child_erf_or_rim, data)
            this_erf_or_rim.set_data(child_capsule_path.stem, ResourceType.from_extension(child_capsule_path.suffix), bytes(data))

        print(f"All nested capsules saved, finally saving physical file '{c_filepath}'")
        write_erf(this_erf_or_rim, c_filepath) if isinstance(this_erf_or_rim, ERF) else write_rim(this_erf_or_rim, c_filepath)
        self.savedFile.emit(str(c_filepath), self._resname, self._restype, data)

    def _saveEndsWithErf(self, data: bytes, data_ext: bytes):
        # Create the mod file if it does not exist.
        """Saves data to an ERF/MOD file with the given extension.

        Args:
        ----
            data: {Bytes of data to save}
            data_ext: {Bytes of associated file extension if saving MDL}.

        Processing Logic:
        ----------------
            - Create the mod file if it does not exist
            - Read the existing ERF file
            - Set the ERF type based on file extension
            - For MDL, also save the MDX file data
            - Save the provided data and file reference
            - Write updated ERF back to file
            - Emit a signal that a file was saved
            - Reload the module in the installation cache.
        """
        assert self._filepath is not None, assert_with_variable_trace(self._filepath is not None)
        assert self._resname is not None, assert_with_variable_trace(self._resname is not None)
        assert self._restype is not None, assert_with_variable_trace(self._restype is not None)

        erftype: ERFType = ERFType.from_extension(self._filepath)
        c_filepath: CaseAwarePath = CaseAwarePath.pathify(self._filepath)

        if c_filepath.is_file():
            erf: ERF = read_erf(c_filepath)
        elif c_filepath.with_suffix(".rim").is_file():
            module.rim_to_mod(c_filepath)
            erf = read_erf(c_filepath)
        else:  # originally in a bif, user chose to save into erf/mod.
            print(f"Saving '{self._resname}.{self._restype}' to a blank new {erftype.name} file at '{c_filepath}'")
            erf = ERF(erftype)  # create a new ERF I guess.
        erf.erf_type = erftype

        # MDL is a special case - we need to save the MDX file with the MDL file.
        if self._restype is ResourceType.MDL:
            assert data_ext is not None, assert_with_variable_trace(data_ext is not None)
            erf.set_data(self._resname, ResourceType.MDX, data_ext)

        erf.set_data(self._resname, self._restype, data)

        write_erf(erf, c_filepath)
        self.savedFile.emit(str(c_filepath), self._resname, self._restype, data)

        # Update installation cache
        if self._installation is not None and c_filepath.parent == self._installation.module_path():
            self._installation.reload_module(c_filepath.name)

    def _saveEndsWithOther(self, data: bytes, data_ext: bytes):
        assert self._filepath is not None, assert_with_variable_trace(self._filepath is not None)
        c_filepath: CaseAwarePath = CaseAwarePath.pathify(self._filepath)
        with c_filepath.open("wb") as file:
            file.write(data)

        # MDL is a special case - we need to save the MDX file with the MDL file.
        if self._restype is ResourceType.MDL:
            with c_filepath.with_suffix(".mdx").open("wb") as file:
                file.write(data_ext)
        self.savedFile.emit(self._filepath, self._resname, self._restype, data)

    def open(self):
        """Opens a file dialog to select a file to open.

        Processing Logic:
        ----------------
            - Use QFileDialog to open a file dialog and get the selected filepath
            - Check if the selected file is a capsule file
            - If it is, show a LoadFromModuleDialog to get additional module data
            - Otherwise, directly load the file by path, reference, type and content
        """
        filepath_str, filter = QFileDialog.getOpenFileName(self, "Open file", "", self._openFilter)
        if not filepath_str.strip():
            return
        r_filepath = Path(filepath_str)

        if is_capsule_file(r_filepath) and f"Load from module ({self.CAPSULE_FILTER})" in self._openFilter:
            dialog = LoadFromModuleDialog(Capsule(r_filepath), self._readSupported)  # type: ignore[arg-type]
            if dialog.exec_():
                self._load_module_from_dialog_info(dialog, r_filepath)
        else:
            data: bytes = BinaryReader.load_file(r_filepath)
            res_ident: ResourceIdentifier = ResourceIdentifier.from_path(r_filepath).validate()
            self.load(r_filepath, *res_ident.unpack(), data)

    def _load_module_from_dialog_info(self, dialog: LoadFromModuleDialog, c_filepath: Path):
        resname: str | None = dialog.resname()
        restype: ResourceType | None = dialog.restype()
        data: bytes | None = dialog.data()
        assert resname is not None, assert_with_variable_trace(resname is not None)
        assert restype is not None, assert_with_variable_trace(restype is not None)
        assert data is not None, assert_with_variable_trace(data is not None)

        self.load(c_filepath, resname, restype, data)

    @abstractmethod
    def build(self) -> tuple[bytes, bytes]: ...

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        """Load a resource from a file.

        Args:
        ----
            filepath: Filepath to load resource from
            resref (str): Resource reference
            restype: ResourceType
            data (bytes): Resource data.

        Processing Logic:
        ----------------
            - Convert filepath to Path object if string
            - Set internal properties like filepath, resref, restype, data
            - Enable "Revert" menu item
            - Refresh window title
            - Emit loadedFile signal with load details.
        """
        self._filepath = Path.pathify(filepath)  # type: ignore[reportGeneralTypeIssues]
        self._resname = resref
        self._restype = restype
        self._revert = data
        for action in self.menuBar().actions()[0].menu().actions():
            if action.text() == "Revert":
                action.setEnabled(True)
                break
        self.refreshWindowTitle()
        self.loadedFile.emit(str(self._filepath), self._resname, self._restype, data)

    def exit(self):
        self.close()

    def new(self):
        self._revert = None
        self._filepath = None
        for action in self.menuBar().actions()[0].menu().actions():
            if action.text() != "Revert":
                continue
            action.setEnabled(False)
        self.refreshWindowTitle()
        self.newFile.emit()

    def revert(self):
        if self._revert is None:
            print("No data to revert from")
            self.blinkWindow()
            return
        assert self._filepath is not None, assert_with_variable_trace(self._filepath is not None)
        assert self._resname is not None, assert_with_variable_trace(self._resname is not None)
        assert self._restype is not None, assert_with_variable_trace(self._restype is not None)
        self.load(self._filepath, self._resname, self._restype, self._revert)

    def _loadLocstring(self, textbox: QLineEdit | QPlainTextEdit, locstring: LocalizedString):
        """Loads a LocalizedString into a textbox.

        Args:
        ----
            textbox: QLineEdit or QPlainTextEdit - Textbox to load string into
            locstring: LocalizedString - String to load


        Processing Logic:
        ----------------
            - Determines if textbox is QLineEdit or QPlainTextEdit
            - Sets textbox's locstring property
            - Checks if locstring has stringref or not
            - Sets textbox text and style accordingly.
        """
        setText: Callable[[str], None] = textbox.setPlainText if isinstance(textbox, QPlainTextEdit) else textbox.setText
        className = "QLineEdit" if isinstance(textbox, QLineEdit) else "QPlainTextEdit"

        textbox.locstring = locstring  # type: ignore[reportAttributeAccessIssue]
        theme = GlobalSettings().selectedTheme
        if locstring.stringref == -1:
            text = str(locstring)
            setText(text if text != "-1" else "")
            # Check theme condition for setting stylesheet
            if theme in ("Native", "Fusion (Light)"):
                textbox.setStyleSheet(f"{textbox.styleSheet()} {className} {{background-color: white;}}")
            else:
                textbox.setStyleSheet(f"{textbox.styleSheet()} {className} {{background-color: white; color: black;}}")
        elif self._installation is not None:
            setText(self._installation.talktable().string(locstring.stringref))
            # Check theme condition for setting stylesheet
            if theme in ("Native", "Fusion (Light)"):
                textbox.setStyleSheet(f"{textbox.styleSheet()} {className} {{background-color: #fffded;}}")
            else:
                textbox.setStyleSheet(f"{textbox.styleSheet()} {className} {{background-color: #fffded; color: black;}}")

    def blinkWindow(self, *, sound: bool = True):
        if sound:
            with suppress(Exception):
                self.playSound("dr_metal_lock")
        self.setWindowOpacity(0.7)
        QTimer.singleShot(125, lambda: self.setWindowOpacity(1))

    def play_byte_source_media(self, data: bytes | None) -> bool:
        if qtpy.API_NAME in ["PyQt5", "PySide2"]:
            from qtpy.QtMultimedia import QMediaContent
            if data:
                self.mediaPlayer.buffer = buffer = QBuffer(self)
                buffer.setData(data)
                buffer.open(QIODevice.OpenModeFlag.ReadOnly)
                self.mediaPlayer.player.setMedia(QMediaContent(), buffer)
                QTimer.singleShot(0, self.mediaPlayer.player.play)  # IMPORTANT!! in pyqt5/pyside2, ONLY works when singleShot from a timer. No idea why.
            else:
                self.blinkWindow()
                return False
            return True

        if qtpy.API_NAME in ["PyQt6", "PySide6"]:
            if data:
                self._play_byte_data_qt6(data)
            else:
                self.blinkWindow()
                return False
            return True
        raise RuntimeError(f"Unsupported QT_API value: {qtpy.API_NAME}")

    def _play_byte_data_qt6(self, data: bytes):
        from qtpy.QtMultimedia import QAudioOutput
        tempFile = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tempFile.write(data)
        tempFile.flush()
        tempFile.seek(0)
        tempFile.close()

        player: PyQt6MediaPlayer | PySide6MediaPlayer = cast(Any, self.mediaPlayer.player)
        audioOutput = QAudioOutput(self)  # type: ignore[reportCallIssue]
        player.setAudioOutput(audioOutput)  # type: ignore[attr-name]
        player.setSource(QUrl.fromLocalFile(tempFile.name))  # type: ignore[attr-name]
        audioOutput.setVolume(1)  # IMPORTANT!! volume starts off at 0% otherwise.
        player.mediaStatusChanged.connect(lambda status, file_name=tempFile.name: self.removeTempAudioFile(status, file_name))
        player.play()

    def playSound(self, resname: str, order: list[SearchLocation] | None = None) -> bool:
        """Plays a sound resource."""
        if not resname or not resname.strip() or self._installation is None:
            self.blinkWindow(sound=False)
            return False

        self.mediaPlayer.player.stop()

        data: bytes | None = self._installation.sound(
            resname,
            order if order is not None else [
                SearchLocation.MUSIC,
                SearchLocation.VOICE,
                SearchLocation.SOUND,
                SearchLocation.OVERRIDE,
                SearchLocation.CHITIN,
            ],
        )
        if not data:
            self.blinkWindow(sound=False)
        return self.play_byte_source_media(data)

    def removeTempAudioFile(
        self,
        status: QMediaPlayer.MediaStatus,
        filePathStr: str,
    ):
        print("<SDM> [removeTempAudioFile scope] status: ", status)
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            try:
                self.mediaPlayer.player.stop()
                QTimer.singleShot(33, lambda: remove_any(filePathStr))
            except OSError:
                self._logger.exception(f"Error removing temporary file {filePathStr}")

    def filepath(self) -> str | None:
        return str(self._filepath)
