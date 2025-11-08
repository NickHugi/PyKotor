from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from pykotor.common.misc import ResRef
from pykotor.resource.generics.uts import UTS, dismantle_uts

if TYPE_CHECKING:
    from qtpy.QtWidgets import QListWidgetItem

    from pykotor.common.module import GFF
    from toolset.gui.editors.uts_editor import UTSEditor


class UTSData:
    def __init__(self, editor: UTSEditor):
        self.editor: UTSEditor = editor
        self.ui = editor.ui
        self._uts: UTS = UTS()

    def load_uts(
        self,
        uts: UTS,
    ):
        """Loads UTS data into UI controls."""
        self._uts = uts

        # Basic
        self.ui.nameEdit.set_locstring(uts.name)
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
            from qtpy import QtCore
            from qtpy.QtWidgets import QListWidgetItem

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

    def build_uts(self) -> UTS:
        """Builds a UTS from UI fields."""
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
            sound: QListWidgetItem | None = self.ui.soundList.item(i)
            if sound is None:
                continue
            uts.sounds.append(ResRef(sound.text()))

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

        return uts

    def dismantle_uts(
        self,
        uts: UTS,
    ) -> GFF:
        """Convert UTS to GFF format."""
        return dismantle_uts(uts)
