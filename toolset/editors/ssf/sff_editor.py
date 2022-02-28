from typing import Optional

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QFileDialog, QWidget
from pykotor.extract.installation import Installation
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.ssf import load_ssf, SSFSound, SSF, write_ssf
from pykotor.resource.type import ResourceType

from editors.editor import Editor
from editors.ssf import sff_editor_ui


class SSFEditor(Editor):
    def __init__(self, parent: QWidget, installation: Optional[Installation] = None):
        supported = [ResourceType.SSF]
        super().__init__(parent, "Soundset Editor", supported, supported, installation)

        self._talktable: Optional[TalkTable] = installation.talktable() if installation else None

        self.ui = sff_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        iconVersion = "x" if installation is None else "2" if installation.tsl else "1"
        iconPath = ":/images/icons/k{}/soundset.png".format(iconVersion)
        self.setWindowIcon(QIcon(QPixmap(iconPath)))

        self.new()

    def _setupSignals(self) -> None:
        self.ui.battlecry1StrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.battlecry2StrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.battlecry3StrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.battlecry4StrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.battlecry5StrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.battlecry6StrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.select1StrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.select2StrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.select3StrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.attack1StrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.attack2StrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.attack3StrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.pain1StrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.pain2StrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.lowHpStrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.deadStrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.criticalStrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.immuneStrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.layMineStrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.disarmMineStrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.beginStealthStrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.beginSearchStrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.beginUnlockStrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.unlockFailedStrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.unlockSuccessStrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.partySeparatedStrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.rejoinPartyStrrefSpin.valueChanged.connect(self.updateTextBoxes)
        self.ui.poisonedStrrefSpin.valueChanged.connect(self.updateTextBoxes)

        self.ui.actionSetTLK.triggered.connect(self.selectTalkTable)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)
        ssf = load_ssf(data)

        self.ui.battlecry1StrrefSpin.setValue(ssf.get(SSFSound.BATTLE_CRY_1))
        self.ui.battlecry2StrrefSpin.setValue(ssf.get(SSFSound.BATTLE_CRY_2))
        self.ui.battlecry3StrrefSpin.setValue(ssf.get(SSFSound.BATTLE_CRY_3))
        self.ui.battlecry4StrrefSpin.setValue(ssf.get(SSFSound.BATTLE_CRY_4))
        self.ui.battlecry5StrrefSpin.setValue(ssf.get(SSFSound.BATTLE_CRY_5))
        self.ui.battlecry6StrrefSpin.setValue(ssf.get(SSFSound.BATTLE_CRY_6))
        self.ui.select1StrrefSpin.setValue(ssf.get(SSFSound.SELECT_1))
        self.ui.select2StrrefSpin.setValue(ssf.get(SSFSound.SELECT_2))
        self.ui.select3StrrefSpin.setValue(ssf.get(SSFSound.SELECT_3))
        self.ui.attack1StrrefSpin.setValue(ssf.get(SSFSound.ATTACK_GRUNT_1))
        self.ui.attack2StrrefSpin.setValue(ssf.get(SSFSound.ATTACK_GRUNT_2))
        self.ui.attack3StrrefSpin.setValue(ssf.get(SSFSound.ATTACK_GRUNT_3))
        self.ui.pain1StrrefSpin.setValue(ssf.get(SSFSound.PAIN_GRUNT_1))
        self.ui.pain2StrrefSpin.setValue(ssf.get(SSFSound.PAIN_GRUNT_2))
        self.ui.lowHpStrrefSpin.setValue(ssf.get(SSFSound.LOW_HEALTH))
        self.ui.deadStrrefSpin.setValue(ssf.get(SSFSound.DEAD))
        self.ui.criticalStrrefSpin.setValue(ssf.get(SSFSound.CRITICAL_HIT))
        self.ui.immuneStrrefSpin.setValue(ssf.get(SSFSound.TARGET_IMMUNE))
        self.ui.layMineStrrefSpin.setValue(ssf.get(SSFSound.LAY_MINE))
        self.ui.disarmMineStrrefSpin.setValue(ssf.get(SSFSound.DISARM_MINE))
        self.ui.beginSearchStrrefSpin.setValue(ssf.get(SSFSound.BEGIN_SEARCH))
        self.ui.beginUnlockStrrefSpin.setValue(ssf.get(SSFSound.BEGIN_UNLOCK))
        self.ui.beginStealthStrrefSpin.setValue(ssf.get(SSFSound.BEGIN_STEALTH))
        self.ui.unlockSuccessStrrefSpin.setValue(ssf.get(SSFSound.UNLOCK_SUCCESS))
        self.ui.unlockFailedStrrefSpin.setValue(ssf.get(SSFSound.UNLOCK_FAILED))
        self.ui.partySeparatedStrrefSpin.setValue(ssf.get(SSFSound.SEPARATED_FROM_PARTY))
        self.ui.rejoinPartyStrrefSpin.setValue(ssf.get(SSFSound.REJOINED_PARTY))
        self.ui.poisonedStrrefSpin.setValue(ssf.get(SSFSound.POISONED))

    def build(self) -> bytes:
        ssf = SSF()

        ssf.set(SSFSound.BATTLE_CRY_1, self.ui.battlecry1StrrefSpin.value())
        ssf.set(SSFSound.BATTLE_CRY_2, self.ui.battlecry2StrrefSpin.value())
        ssf.set(SSFSound.BATTLE_CRY_3, self.ui.battlecry3StrrefSpin.value())
        ssf.set(SSFSound.BATTLE_CRY_4, self.ui.battlecry4StrrefSpin.value())
        ssf.set(SSFSound.BATTLE_CRY_5, self.ui.battlecry5StrrefSpin.value())
        ssf.set(SSFSound.BATTLE_CRY_6, self.ui.battlecry6StrrefSpin.value())
        ssf.set(SSFSound.SELECT_1, self.ui.select1StrrefSpin.value())
        ssf.set(SSFSound.SELECT_2, self.ui.select2StrrefSpin.value())
        ssf.set(SSFSound.SELECT_3, self.ui.select3StrrefSpin.value())
        ssf.set(SSFSound.ATTACK_GRUNT_1, self.ui.attack1StrrefSpin.value())
        ssf.set(SSFSound.ATTACK_GRUNT_2, self.ui.attack2StrrefSpin.value())
        ssf.set(SSFSound.ATTACK_GRUNT_3, self.ui.attack3StrrefSpin.value())
        ssf.set(SSFSound.PAIN_GRUNT_1, self.ui.pain1StrrefSpin.value())
        ssf.set(SSFSound.PAIN_GRUNT_2, self.ui.pain2StrrefSpin.value())
        ssf.set(SSFSound.LOW_HEALTH, self.ui.lowHpStrrefSpin.value())
        ssf.set(SSFSound.DEAD, self.ui.deadStrrefSpin.value())
        ssf.set(SSFSound.CRITICAL_HIT, self.ui.criticalStrrefSpin.value())
        ssf.set(SSFSound.TARGET_IMMUNE, self.ui.immuneStrrefSpin.value())
        ssf.set(SSFSound.LAY_MINE, self.ui.layMineStrrefSpin.value())
        ssf.set(SSFSound.DISARM_MINE, self.ui.disarmMineStrrefSpin.value())
        ssf.set(SSFSound.BEGIN_STEALTH, self.ui.beginStealthStrrefSpin.value())
        ssf.set(SSFSound.BEGIN_SEARCH, self.ui.beginSearchStrrefSpin.value())
        ssf.set(SSFSound.BEGIN_UNLOCK, self.ui.beginUnlockStrrefSpin.value())
        ssf.set(SSFSound.UNLOCK_FAILED, self.ui.unlockFailedStrrefSpin.value())
        ssf.set(SSFSound.UNLOCK_SUCCESS, self.ui.unlockSuccessStrrefSpin.value())
        ssf.set(SSFSound.SEPARATED_FROM_PARTY, self.ui.partySeparatedStrrefSpin.value())
        ssf.set(SSFSound.REJOINED_PARTY, self.ui.rejoinPartyStrrefSpin.value())
        ssf.set(SSFSound.POISONED, self.ui.poisonedStrrefSpin.value())

        data = bytearray()
        write_ssf(ssf, data)
        return data

    def new(self) -> None:
        super().new()

        self.ui.battlecry1StrrefSpin.setValue(0)
        self.ui.battlecry2StrrefSpin.setValue(0)
        self.ui.battlecry3StrrefSpin.setValue(0)
        self.ui.battlecry4StrrefSpin.setValue(0)
        self.ui.battlecry5StrrefSpin.setValue(0)
        self.ui.battlecry6StrrefSpin.setValue(0)
        self.ui.select1StrrefSpin.setValue(0)
        self.ui.select2StrrefSpin.setValue(0)
        self.ui.select3StrrefSpin.setValue(0)
        self.ui.attack1StrrefSpin.setValue(0)
        self.ui.attack2StrrefSpin.setValue(0)
        self.ui.attack3StrrefSpin.setValue(0)
        self.ui.pain1StrrefSpin.setValue(0)
        self.ui.pain2StrrefSpin.setValue(0)
        self.ui.lowHpStrrefSpin.setValue(0)
        self.ui.deadStrrefSpin.setValue(0)
        self.ui.criticalStrrefSpin.setValue(0)
        self.ui.immuneStrrefSpin.setValue(0)
        self.ui.layMineStrrefSpin.setValue(0)
        self.ui.disarmMineStrrefSpin.setValue(0)
        self.ui.beginSearchStrrefSpin.setValue(0)
        self.ui.beginUnlockStrrefSpin.setValue(0)
        self.ui.beginStealthStrrefSpin.setValue(0)
        self.ui.unlockSuccessStrrefSpin.setValue(0)
        self.ui.unlockFailedStrrefSpin.setValue(0)
        self.ui.partySeparatedStrrefSpin.setValue(0)
        self.ui.rejoinPartyStrrefSpin.setValue(0)
        self.ui.poisonedStrrefSpin.setValue(0)

    def updateTextBoxes(self) -> None:
        if self._talktable is None:
            return

        pairs = {
            (self.ui.battlecry1SoundEdit, self.ui.battlecry1TextEdit): self.ui.battlecry1StrrefSpin.value(),
            (self.ui.battlecry2SoundEdit, self.ui.battlecry2TextEdit): self.ui.battlecry2StrrefSpin.value(),
            (self.ui.battlecry3SoundEdit, self.ui.battlecry3TextEdit): self.ui.battlecry3StrrefSpin.value(),
            (self.ui.battlecry4SoundEdit, self.ui.battlecry4TextEdit): self.ui.battlecry4StrrefSpin.value(),
            (self.ui.battlecry5SoundEdit, self.ui.battlecry5TextEdit): self.ui.battlecry5StrrefSpin.value(),
            (self.ui.battlecry6SoundEdit, self.ui.battlecry6TextEdit): self.ui.battlecry6StrrefSpin.value(),
            (self.ui.select1SoundEdit, self.ui.select1TextEdit): self.ui.select1StrrefSpin.value(),
            (self.ui.select2SoundEdit, self.ui.select2TextEdit): self.ui.select2StrrefSpin.value(),
            (self.ui.select3SoundEdit, self.ui.select3TextEdit): self.ui.select3StrrefSpin.value(),
            (self.ui.attack1SoundEdit, self.ui.attack1TextEdit): self.ui.attack1StrrefSpin.value(),
            (self.ui.attack2SoundEdit, self.ui.attack2TextEdit): self.ui.attack2StrrefSpin.value(),
            (self.ui.attack3SoundEdit, self.ui.attack3TextEdit): self.ui.attack3StrrefSpin.value(),
            (self.ui.pain1SoundEdit, self.ui.pain1TextEdit): self.ui.pain1StrrefSpin.value(),
            (self.ui.pain2SoundEdit, self.ui.pain2TextEdit): self.ui.pain2StrrefSpin.value(),
            (self.ui.lowHpSoundEdit, self.ui.lowHpTextEdit): self.ui.lowHpStrrefSpin.value(),
            (self.ui.deadSoundEdit, self.ui.deadTextEdit): self.ui.deadStrrefSpin.value(),
            (self.ui.criticalSoundEdit, self.ui.criticalTextEdit): self.ui.criticalStrrefSpin.value(),
            (self.ui.immuneSoundEdit, self.ui.immuneTextEdit): self.ui.immuneStrrefSpin.value(),
            (self.ui.layMineSoundEdit, self.ui.layMineTextEdit): self.ui.layMineStrrefSpin.value(),
            (self.ui.disarmMineSoundEdit, self.ui.disarmMineTextEdit): self.ui.disarmMineStrrefSpin.value(),
            (self.ui.beginSearchSoundEdit, self.ui.beginSearchTextEdit): self.ui.beginSearchStrrefSpin.value(),
            (self.ui.beginStealthSoundEdit, self.ui.beginStealthTextEdit): self.ui.beginStealthStrrefSpin.value(),
            (self.ui.beginUnlockSoundEdit, self.ui.beginUnlockTextEdit): self.ui.beginUnlockStrrefSpin.value(),
            (self.ui.unlockSuccessSoundEdit, self.ui.unlockSuccessTextEdit): self.ui.unlockSuccessStrrefSpin.value(),
            (self.ui.unlockFailedSoundEdit, self.ui.unlockFailedTextEdit): self.ui.unlockFailedStrrefSpin.value(),
            (self.ui.partySeparatedSoundEdit, self.ui.partySeparatedTextEdit): self.ui.partySeparatedStrrefSpin.value(),
            (self.ui.rejoinPartySoundEdit, self.ui.rejoinPartyTextEdit): self.ui.rejoinPartyStrrefSpin.value(),
            (self.ui.poisonedSoundEdit, self.ui.poisonedTextEdit): self.ui.poisonedStrrefSpin.value()
        }

        batch = self._talktable.batch(list(pairs.values()))

        for pair, stringref in pairs.items():
            text, sound = batch[stringref]
            pair[0].setText(sound.get())
            pair[1].setText(text)

    def selectTalkTable(self) -> None:
        filepath, filter = QFileDialog.getOpenFileName(self, "Select a TLK file", "", "TalkTable (*.tlk)")
        if filepath:
            self._talktable = TalkTable(filepath)
        self.updateTextBoxes()
