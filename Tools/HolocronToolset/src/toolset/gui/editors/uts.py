from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QBuffer, QIODevice
from qtpy.QtMultimedia import QMediaPlayer
from qtpy.QtWidgets import QListWidgetItem, QMessageBox

from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.uts import UTS, dismantle_uts, read_uts
from pykotor.resource.type import ResourceType
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtGui import QCloseEvent
    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation


class UTSEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation = None,
    ):
        """Initialize the Sound Editor window.

        Args:
        ----
            parent: {QWidget}: The parent widget of this window
            installation: {HTInstallation}: The installation object

        Processing Logic:
        ----------------
            - Initialize supported resource types
            - Initialize the superclass with window details
            - Initialize UTS object
            - Initialize media player and buffer
            - Load UI from designer file
            - Set up menus, signals and installation.
        """
        supported: list[ResourceType] = [ResourceType.UTS]
        super().__init__(parent, "Sound Editor", "sound", supported, supported, installation)

        self._uts: UTS = UTS()

        self.player = QMediaPlayer(self)
        self.buffer = QBuffer(self)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.uts import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.uts import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.uts import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.uts import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        if installation is not None:  # will only be none in the unittests
            self._setupInstallation(installation)

        self.new()

    def _setupSignals(self):
        """Sets up signal connections for UI buttons and radio buttons.

        Processing Logic:
        ----------------
            - Connects addSoundButton click signal to addSound method
            - Connects removeSoundButton click signal to removeSound method
            - Connects playSoundButton click signal to playSound method
            - Connects stopSoundButton click signal to player stop method
            - Connects moveUpButton and moveDownButton click signals to moveSoundUp and moveSoundDown methods
            - Connects tagGenerateButton and resrefGenerateButton click signals to generateTag and generateResref methods
            - Connects style radio buttons toggled signals to changeStyle method
            - Connects play random/specific/everywhere radio buttons toggled signals to changePlay method.
        """
        self.ui.addSoundButton.clicked.connect(self.addSound)
        self.ui.removeSoundButton.clicked.connect(self.removeSound)
        self.ui.playSoundButton.clicked.connect(self.playSound)
        self.ui.stopSoundButton.clicked.connect(self.player.stop)
        self.ui.moveUpButton.clicked.connect(self.moveSoundUp)
        self.ui.moveDownButton.clicked.connect(self.moveSoundDown)

        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.resrefGenerateButton.clicked.connect(self.generateResref)

        self.ui.styleOnceRadio.toggled.connect(self.changeStyle)
        self.ui.styleSeamlessRadio.toggled.connect(self.changeStyle)
        self.ui.styleRepeatRadio.toggled.connect(self.changeStyle)

        self.ui.playRandomRadio.toggled.connect(self.changePlay)
        self.ui.playSpecificRadio.toggled.connect(self.changePlay)
        self.ui.playEverywhereRadio.toggled.connect(self.changePlay)

    def _setupInstallation(self, installation: HTInstallation):
        self._installation = installation
        self.ui.nameEdit.setInstallation(installation)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)

        uts: UTS = read_uts(data)
        self._loadUTS(uts)

    def _loadUTS(self, uts: UTS):
        """Loads UTS data into UI controls.

        Args:
        ----
            uts (UTS): UTS object to load

        Processing Logic:
        ----------------
            - Sets basic property values like name, tag, etc
            - Sets advanced playback options like random, specific position
            - Loads sounds list
            - Sets positioning options like style, distances
            - Loads comments.
        """
        self._uts = uts

        # Basic
        self.ui.nameEdit.setLocstring(uts.name)
        self.ui.tagEdit.setText(uts.tag)
        self.ui.resrefEdit.setText(str(uts.resref))
        self.ui.volumeSlider.setValue(uts.volume)
        self.ui.activeCheckbox.setChecked(uts.active)

        # Advanced
        self.ui.playRandomRadio.setChecked(False)
        self.ui.playSpecificRadio.setChecked(False)
        self.ui.playEverywhereRadio.setChecked(False)
        if uts.random_range_x != 0 and uts.random_range_y != 0:
            self.ui.playRandomRadio.setChecked(True)
        elif uts.positional:
            self.ui.playSpecificRadio.setChecked(True)
        else:
            self.ui.playEverywhereRadio.setChecked(True)

        self.ui.orderSequentialRadio.setChecked(uts.random_pick == 0)
        self.ui.orderRandomRadio.setChecked(uts.random_pick == 1)

        self.ui.intervalSpin.setValue(uts.interval)
        self.ui.intervalVariationSpin.setValue(uts.interval_variation)
        self.ui.volumeVariationSlider.setValue(uts.volume_variation)
        self.ui.pitchVariationSlider.setValue(int(uts.pitch_variation * 100))

        # Sounds
        self.ui.soundList.clear()
        for sound in uts.sounds:
            item = QListWidgetItem(str(sound))
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
            self.ui.soundList.addItem(item)

        # Positioning
        self.ui.styleOnceRadio.setChecked(False)
        self.ui.styleSeamlessRadio.setChecked(False)
        self.ui.styleRepeatRadio.setChecked(False)
        if uts.continuous and uts.looping:
            self.ui.styleSeamlessRadio.setChecked(True)
        elif uts.looping:
            self.ui.styleRepeatRadio.setChecked(True)
        else:
            self.ui.styleOnceRadio.setChecked(True)

        self.ui.cutoffSpin.setValue(uts.max_distance)
        self.ui.maxVolumeDistanceSpin.setValue(uts.min_distance)
        self.ui.heightSpin.setValue(uts.elevation)
        self.ui.northRandomSpin.setValue(uts.random_range_y)
        self.ui.eastRandomSpin.setValue(uts.random_range_x)

        # Comments
        self.ui.commentsEdit.setPlainText(uts.comment)

    def build(self) -> tuple[bytes, bytes]:
        """Builds a UTS from UI fields.

        Returns:
        -------
            tuple[bytes, bytes]: A tuple containing the unit data and log.

        Processing Logic:
        ----------------
            - Collects input from UI elements and assigns to _uts attribute
            - Loops through sound list adding each sound to _uts
            - Writes _uts to bytearray using dismantle_uts and write_gff
            - Returns bytearray tuple.
        """
        uts: UTS = deepcopy(self._uts)

        # Basic
        uts.name = self.ui.nameEdit.locstring()
        uts.tag = self.ui.tagEdit.text()
        uts.resref = ResRef(self.ui.resrefEdit.text())
        uts.volume = self.ui.volumeSlider.value()
        uts.active = self.ui.activeCheckbox.isChecked()

        # Advanced
        uts.random_range_x = self.ui.northRandomSpin.value()
        uts.random_range_y = self.ui.eastRandomSpin.value()
        uts.positional = self.ui.playSpecificRadio.isChecked()
        uts.random_pick = self.ui.orderRandomRadio.isChecked()
        uts.interval = self.ui.intervalSpin.value()
        uts.interval_variation = self.ui.intervalVariationSpin.value()
        uts.volume_variation = self.ui.volumeVariationSlider.value()
        uts.pitch_variation = self.ui.pitchVariationSlider.value() / 100

        # Sounds
        uts.sounds = []
        for i in range(self.ui.soundList.count()):
            sound = ResRef(self.ui.soundList.item(i).text())
            uts.sounds.append(sound)

        # Positioning
        uts.continuous = self.ui.styleSeamlessRadio.isChecked()
        uts.looping = self.ui.styleSeamlessRadio.isChecked() or self.ui.styleRepeatRadio.isChecked()
        uts.max_distance = self.ui.maxVolumeDistanceSpin.value()
        uts.min_distance = self.ui.cutoffSpin.value()
        uts.elevation = self.ui.heightSpin.value()
        uts.random_range_x = self.ui.northRandomSpin.value()
        uts.random_range_y = self.ui.eastRandomSpin.value()

        # Comments
        uts.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff = dismantle_uts(uts)
        write_gff(gff, data)

        return data, b""

    def new(self):
        super().new()
        self._loadUTS(UTS())

    def changeName(self):
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring())
        if dialog.exec_():
            self._loadLocstring(self.ui.nameEdit.ui.locstringText, dialog.locstring)

    def generateTag(self):
        if self.ui.resrefEdit.text() == "":
            self.generateResref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generateResref(self):
        if self._resname is not None and self._resname != "":
            self.ui.resrefEdit.setText(self._resname)
        else:
            self.ui.resrefEdit.setText("m00xx_trg_000")

    def changeStyle(self):
        def _set_ui_style_groups(boolean: bool):
            self.ui.intervalGroup.setEnabled(boolean)
            self.ui.orderGroup.setEnabled(boolean)
            self.ui.variationGroup.setEnabled(boolean)

        _set_ui_style_groups(True)
        if self.ui.styleSeamlessRadio.isChecked():
            _set_ui_style_groups(False)
        elif self.ui.styleRepeatRadio.isChecked():
            ...
        elif self.ui.styleOnceRadio.isChecked():
            self.ui.intervalGroup.setEnabled(False)

    def changePlay(self):
        def _set_ui_play_groups(boolean: bool):
            self.ui.rangeGroup.setEnabled(boolean)
            self.ui.heightGroup.setEnabled(boolean)
            self.ui.distanceGroup.setEnabled(boolean)

        _set_ui_play_groups(True)
        if self.ui.playRandomRadio.isChecked():
            ...
        elif self.ui.playSpecificRadio.isChecked():
            self.ui.rangeGroup.setEnabled(False)
            self.ui.northRandomSpin.setValue(0)
            self.ui.eastRandomSpin.setValue(0)
        elif self.ui.playEverywhereRadio.isChecked():
            _set_ui_play_groups(False)

    def playSound(self):
        self.player.stop()

        curItem = self.ui.soundList.currentItem()
        curItemText = curItem.text() if curItem else None
        if not curItem or not curItemText:
            return

        resname: str = curItemText
        data: bytes | None = self._installation.sound(resname)

        if data:
            # PyQt5 and PySide2 code path
            from qtpy.QtMultimedia import QMediaContent
            self.buffer = QBuffer(self)
            self.buffer.setData(data)
            self.buffer.open(QIODevice.ReadOnly)
            self.player.setMedia(QMediaContent(), self.buffer)
            QtCore.QTimer.singleShot(0, self.player.play)
        else:
            QMessageBox(QMessageBox.Icon.Critical, "Could not find audio file", f"Could not find audio resource '{resname}'.")

    def addSound(self):
        item = QListWidgetItem("new sound")
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
        self.ui.soundList.addItem(item)

    def removeSound(self):
        if self.ui.soundList.currentRow() == -1:
            return
        self.ui.soundList.takeItem(self.ui.soundList.currentRow())

    def moveSoundUp(self):
        if self.ui.soundList.currentRow() == -1:
            return
        resname: str = self.ui.soundList.currentItem().text()
        row: int = self.ui.soundList.currentRow()
        self.ui.soundList.takeItem(self.ui.soundList.currentRow())
        self.ui.soundList.insertItem(row - 1, resname)
        self.ui.soundList.setCurrentRow(row - 1)
        item: QListWidgetItem | None = self.ui.soundList.item(row - 1)
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)

    def moveSoundDown(self):
        if self.ui.soundList.currentRow() == -1:
            return
        resname: str = self.ui.soundList.currentItem().text()
        row: int = self.ui.soundList.currentRow()
        self.ui.soundList.takeItem(self.ui.soundList.currentRow())
        self.ui.soundList.insertItem(row + 1, resname)
        self.ui.soundList.setCurrentRow(row + 1)
        item: QListWidgetItem | None = self.ui.soundList.item(row + 1)
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)

    def closeEvent(self, e: QCloseEvent):
        self.player.stop()
