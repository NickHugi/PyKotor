from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy import QtCore
from qtpy.QtCore import QBuffer, QIODevice
from qtpy.QtWidgets import QListWidgetItem, QMessageBox

from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog

if TYPE_CHECKING:
    from toolset.gui.editors.uts_editor import UTSEditor


class UTSEditorUI:
    def __init__(self, editor: UTSEditor):
        self.editor = editor
        self.ui = editor.ui
        self._setup_signals()

    def _setup_signals(self):
        """Sets up signal connections for UI buttons and radio buttons."""
        self.ui.addSoundButton.clicked.connect(self.add_sound)
        self.ui.removeSoundButton.clicked.connect(self.remove_sound)
        self.ui.playSoundButton.clicked.connect(self.play_sound)
        self.ui.stopSoundButton.clicked.connect(self.editor.player.stop)
        self.ui.moveUpButton.clicked.connect(self.move_sound_up)
        self.ui.moveDownButton.clicked.connect(self.move_sound_down)

        self.ui.tagGenerateButton.clicked.connect(self.generate_tag)
        self.ui.resrefGenerateButton.clicked.connect(self.generate_resref)

        self.ui.styleOnceRadio.toggled.connect(self.change_style)
        self.ui.styleSeamlessRadio.toggled.connect(self.change_style)
        self.ui.styleRepeatRadio.toggled.connect(self.change_style)

        self.ui.playRandomRadio.toggled.connect(self.change_play)
        self.ui.playSpecificRadio.toggled.connect(self.change_play)
        self.ui.playEverywhereRadio.toggled.connect(self.change_play)

    def change_name(self):
        dialog = LocalizedStringDialog(self.editor, self.editor._installation, self.ui.nameEdit.locstring())
        if dialog.exec():
            self.editor._load_locstring(self.ui.nameEdit.ui.locstringText, dialog.locstring)

    def generate_tag(self):
        if self.ui.resrefEdit.text() == "":
            self.generate_resref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generate_resref(self):
        if self.editor._resname is not None and self.editor._resname != "":
            self.ui.resrefEdit.setText(self.editor._resname)
        else:
            self.ui.resrefEdit.setText("m00xx_trg_000")

    def change_style(self):
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

    def change_play(self):
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

    def play_sound(self):
        self.editor.player.stop()

        curItem = self.ui.soundList.currentItem()
        curItemText = curItem.text() if curItem else None
        if not curItem or not curItemText:
            return

        resname: str = curItemText
        data: bytes | None = self.editor._installation.sound(resname)

        if data:
            # PyQt5 and PySide2 code path
            from qtpy.QtMultimedia import QMediaContent
            self.editor.buffer = QBuffer(self.editor)
            self.editor.buffer.setData(data)
            self.editor.buffer.open(QIODevice.ReadOnly)
            self.editor.player.setMedia(QMediaContent(), self.editor.buffer)
            QtCore.QTimer.singleShot(0, self.editor.player.play)
        else:
            QMessageBox(QMessageBox.Icon.Critical, "Could not find audio file", f"Could not find audio resource '{resname}'.")

    def add_sound(self):
        item = QListWidgetItem("new sound")
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
        self.ui.soundList.addItem(item)

    def remove_sound(self):
        if self.ui.soundList.currentRow() == -1:
            return
        self.ui.soundList.takeItem(self.ui.soundList.currentRow())

    def move_sound_up(self):
        if self.ui.soundList.currentRow() == -1:
            return
        resname: str = self.ui.soundList.currentItem().text()
        row: int = self.ui.soundList.currentRow()
        self.ui.soundList.takeItem(self.ui.soundList.currentRow())
        self.ui.soundList.insertItem(row - 1, resname)
        self.ui.soundList.setCurrentRow(row - 1)
        item: QListWidgetItem | None = self.ui.soundList.item(row - 1)
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)

    def move_sound_down(self):
        if self.ui.soundList.currentRow() == -1:
            return
        resname: str = self.ui.soundList.currentItem().text()
        row: int = self.ui.soundList.currentRow()
        self.ui.soundList.takeItem(self.ui.soundList.currentRow())
        self.ui.soundList.insertItem(row + 1, resname)
        self.ui.soundList.setCurrentRow(row + 1)
        item: QListWidgetItem | None = self.ui.soundList.item(row + 1)
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)