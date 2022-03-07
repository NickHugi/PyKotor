from PyQt5 import QtCore
from PyQt5.QtCore import QIODevice, QBuffer
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QWidget, QMessageBox, QListWidgetItem
from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.uts import UTS, dismantle_uts, read_uts
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from editors.editor import Editor, LocalizedStringDialog
from editors.uts import uts_editor_ui


class UTSEditor(Editor):
    def __init__(self, parent: QWidget, installation: HTInstallation = None):
        supported = [ResourceType.UTS]
        super().__init__(parent, "Sound Editor", "sound", supported, supported, installation)

        self.ui = uts_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        self._setupInstallation(installation)

        self.player = QMediaPlayer(self)
        self.buffer = QBuffer(self)

        self._uts = UTS()

        self.new()

    def _setupSignals(self) -> None:
        self.ui.addSoundButton.clicked.connect(self.addSound)
        self.ui.removeSoundButton.clicked.connect(self.removeSound)
        self.ui.playSoundButton.clicked.connect(self.playSound)
        self.ui.stopSoundButton.clicked.connect(self.player.stop)
        self.ui.moveUpButton.clicked.connect(self.moveSoundUp)
        self.ui.moveDownButton.clicked.connect(self.moveSoundDown)

        self.ui.nameChangeButton.clicked.connect(self.changeName)
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.resrefGenerateButton.clicked.connect(self.generateResref)

        self.ui.styleOnceRadio.toggled.connect(self.changeStyle)
        self.ui.styleSeamlessRadio.toggled.connect(self.changeStyle)
        self.ui.styleRepeatRadio.toggled.connect(self.changeStyle)

        self.ui.playRandomRadio.toggled.connect(self.changePlay)
        self.ui.playSpecificRadio.toggled.connect(self.changePlay)
        self.ui.playEverywhereRadio.toggled.connect(self.changePlay)

    def _setupInstallation(self, installation: HTInstallation) -> None:
        self._installation = installation

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        uts = read_uts(data)
        self._loadUTS(uts)

    def _loadUTS(self, uts: UTS):
        self._uts = uts

        # Basic
        self._loadLocstring(self.ui.nameEdit, uts.name)
        self.ui.tagEdit.setText(uts.tag)
        self.ui.resrefEdit.setText(uts.resref.get())
        self.ui.volumeSlider.setValue(uts.volume)
        self.ui.activeCheckbox.setChecked(uts.active)

        # Advanced
        self.ui.playRandomRadio.setChecked(False)
        self.ui.playSpecificRadio.setChecked(False)
        self.ui.playEverywhereRadio.setChecked(False)
        if uts.random_range_y != 0 and uts.random_range_y != 0:
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
            item = QListWidgetItem(sound.get())
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
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

    def build(self) -> bytes:
        uts = self._uts

        # Basic
        uts.name = self.ui.nameEdit.locstring
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

        return data

    def new(self) -> None:
        super().new()
        self._loadUTS(UTS())

    def changeName(self) -> None:
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring)
        if dialog.exec_():
            self._loadLocstring(self.ui.nameEdit, dialog.locstring)

    def generateTag(self) -> None:
        if self.ui.resrefEdit.text() == "":
            self.generateResref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generateResref(self) -> None:
        if self._resref is not None and self._resref != "":
            self.ui.resrefEdit.setText(self._resref)
        else:
            self.ui.resrefEdit.setText("m00xx_trg_000")

    def changeStyle(self) -> None:
        self.ui.intervalGroup.setEnabled(True)
        self.ui.orderGroup.setEnabled(True)
        self.ui.variationGroup.setEnabled(True)

        if self.ui.styleSeamlessRadio.isChecked():
            self.ui.intervalGroup.setEnabled(False)
            self.ui.orderGroup.setEnabled(False)
            self.ui.variationGroup.setEnabled(False)
        elif self.ui.styleRepeatRadio.isChecked():
            ...
        elif self.ui.styleOnceRadio.isChecked():
            self.ui.intervalGroup.setEnabled(False)

    def changePlay(self) -> None:
        self.ui.rangeGroup.setEnabled(True)
        self.ui.heightGroup.setEnabled(True)
        self.ui.distanceGroup.setEnabled(True)

        if self.ui.playRandomRadio.isChecked():
            ...
        elif self.ui.playSpecificRadio.isChecked():
            self.ui.rangeGroup.setEnabled(False)
            self.ui.northRandomSpin.setValue(0)
            self.ui.eastRandomSpin.setValue(0)
        elif self.ui.playEverywhereRadio.isChecked():
            self.ui.rangeGroup.setEnabled(False)
            self.ui.heightGroup.setEnabled(False)
            self.ui.distanceGroup.setEnabled(False)

    def playSound(self) -> None:
        self.player.stop()

        if not self.ui.soundList.currentItem().text():
            return

        resname = self.ui.soundList.currentItem().text()
        data = self._installation.sound(resname)

        if data:
            self.buffer = QBuffer(self)
            self.buffer.setData(data)
            self.buffer.open(QIODevice.ReadOnly)
            self.player.setMedia(QMediaContent(), self.buffer)
            QtCore.QTimer.singleShot(0, self.player.play)
        else:
            QMessageBox(QMessageBox.Critical, "Could not find audio file", "Could not find audio resource '{}'.".format(resname))

    def addSound(self) -> None:
        item = QListWidgetItem("new sound")
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.ui.soundList.addItem(item)

    def removeSound(self) -> None:
        if self.ui.soundList.currentRow() == -1:
            return
        self.ui.soundList.takeItem(self.ui.soundList.currentRow())

    def moveSoundUp(self) -> None:
        if self.ui.soundList.currentRow() == -1:
            return
        resname = self.ui.soundList.currentItem().text()
        row = self.ui.soundList.currentRow()
        self.ui.soundList.takeItem(self.ui.soundList.currentRow())
        self.ui.soundList.insertItem(row - 1, resname)
        self.ui.soundList.setCurrentRow(row - 1)
        item = self.ui.soundList.item(row - 1)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)

    def moveSoundDown(self) -> None:
        if self.ui.soundList.currentRow() == -1:
            return
        resname = self.ui.soundList.currentItem().text()
        row = self.ui.soundList.currentRow()
        self.ui.soundList.takeItem(self.ui.soundList.currentRow())
        self.ui.soundList.insertItem(row + 1, resname)
        self.ui.soundList.setCurrentRow(row + 1)
        item = self.ui.soundList.item(row + 1)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)

    def closeEvent(self, e: QCloseEvent) -> None:
        self.player.stop()
