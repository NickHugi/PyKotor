from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy.QtWidgets import QFileDialog

from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.ssf import SSF, SSFSound, read_ssf, write_ssf
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QLineEdit, QWidget

    from pykotor.extract.installation import Installation
    from pykotor.extract.talktable import StringResult


class SSFEditor(Editor):
    def __init__(self, parent: QWidget | None, installation: Installation | None = None):
        """Initialize Soundset Editor window.

        Args:
        ----
            parent: {Parent widget}
            installation: {Installation object}.

        Processing Logic:
        ----------------
            - Call super().__init__ to initialize base editor
            - Get talktable from installation if provided
            - Import and setup UI
            - Setup menus and signals
            - Call new() to start with empty soundset
        """
        supported: list[ResourceType] = [ResourceType.SSF]
        super().__init__(parent, "Soundset Editor", "soundset", supported, supported, installation)

        self._talktable: TalkTable | None = installation.talktable() if installation else None

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.ssf import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.ssf import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.ssf import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.ssf import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self.new()
        self.setMinimumSize(577, 437)

    def _setupSignals(self):
        """Connects signals to update text boxes.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            - Connects valueChanged signals from spin boxes to updateTextBoxes method
            - Connects triggered signal from actionSetTLK to selectTalkTable method
        """
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

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        """Loads sound data from an SSF file.

        Args:
        ----
            filepath: {PathLike or string}: Path to SSF file
            resref: {string}: Resource reference
            restype: {ResourceType}: Resource type
            data: {bytes}: SSF data

        Loads sound data from an SSF file and sets values of UI spin boxes:
            - Reads SSF data from file
            - Sets values of spin boxes for different sound events like battlecries, attacks, abilities etc
            - Populates UI with sound data from file.
        """
        super().load(filepath, resref, restype, data)
        ssf: SSF = read_ssf(data)

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

    def build(self) -> tuple[bytes, bytes]:
        """Builds sound data from UI values.

        Args:
        ----
            self: {The class instance}: Provides UI element values

        Returns:
        -------
            tuple[bytes, bytes]: {The built sound data and empty string}

        Processing Logic:
        ----------------
            - Initialize SSF object
            - Set data for each sound type from corresponding UI element value
            - Serialize SSF to bytearray
            - Return bytearray and empty string.
        """
        ssf = SSF()

        ssf.set_data(SSFSound.BATTLE_CRY_1, self.ui.battlecry1StrrefSpin.value())
        ssf.set_data(SSFSound.BATTLE_CRY_2, self.ui.battlecry2StrrefSpin.value())
        ssf.set_data(SSFSound.BATTLE_CRY_3, self.ui.battlecry3StrrefSpin.value())
        ssf.set_data(SSFSound.BATTLE_CRY_4, self.ui.battlecry4StrrefSpin.value())
        ssf.set_data(SSFSound.BATTLE_CRY_5, self.ui.battlecry5StrrefSpin.value())
        ssf.set_data(SSFSound.BATTLE_CRY_6, self.ui.battlecry6StrrefSpin.value())
        ssf.set_data(SSFSound.SELECT_1, self.ui.select1StrrefSpin.value())
        ssf.set_data(SSFSound.SELECT_2, self.ui.select2StrrefSpin.value())
        ssf.set_data(SSFSound.SELECT_3, self.ui.select3StrrefSpin.value())
        ssf.set_data(SSFSound.ATTACK_GRUNT_1, self.ui.attack1StrrefSpin.value())
        ssf.set_data(SSFSound.ATTACK_GRUNT_2, self.ui.attack2StrrefSpin.value())
        ssf.set_data(SSFSound.ATTACK_GRUNT_3, self.ui.attack3StrrefSpin.value())
        ssf.set_data(SSFSound.PAIN_GRUNT_1, self.ui.pain1StrrefSpin.value())
        ssf.set_data(SSFSound.PAIN_GRUNT_2, self.ui.pain2StrrefSpin.value())
        ssf.set_data(SSFSound.LOW_HEALTH, self.ui.lowHpStrrefSpin.value())
        ssf.set_data(SSFSound.DEAD, self.ui.deadStrrefSpin.value())
        ssf.set_data(SSFSound.CRITICAL_HIT, self.ui.criticalStrrefSpin.value())
        ssf.set_data(SSFSound.TARGET_IMMUNE, self.ui.immuneStrrefSpin.value())
        ssf.set_data(SSFSound.LAY_MINE, self.ui.layMineStrrefSpin.value())
        ssf.set_data(SSFSound.DISARM_MINE, self.ui.disarmMineStrrefSpin.value())
        ssf.set_data(SSFSound.BEGIN_STEALTH, self.ui.beginStealthStrrefSpin.value())
        ssf.set_data(SSFSound.BEGIN_SEARCH, self.ui.beginSearchStrrefSpin.value())
        ssf.set_data(SSFSound.BEGIN_UNLOCK, self.ui.beginUnlockStrrefSpin.value())
        ssf.set_data(SSFSound.UNLOCK_FAILED, self.ui.unlockFailedStrrefSpin.value())
        ssf.set_data(SSFSound.UNLOCK_SUCCESS, self.ui.unlockSuccessStrrefSpin.value())
        ssf.set_data(SSFSound.SEPARATED_FROM_PARTY, self.ui.partySeparatedStrrefSpin.value())
        ssf.set_data(SSFSound.REJOINED_PARTY, self.ui.rejoinPartyStrrefSpin.value())
        ssf.set_data(SSFSound.POISONED, self.ui.poisonedStrrefSpin.value())

        data = bytearray()
        write_ssf(ssf, data)
        return data, b""

    def new(self):
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

    def updateTextBoxes(self):
        """Updates text boxes with sound and text from talktable.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Gets stringref values from UI elements
            - Batches stringref lookups to talktable
            - Loops through pairs of UI elements and assigns text/sound from talktable.
        """
        if self._talktable is None:
            return

        pairs: dict[tuple[QLineEdit, QLineEdit], int] = {
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
            (self.ui.poisonedSoundEdit, self.ui.poisonedTextEdit): self.ui.poisonedStrrefSpin.value(),
        }

        batch: dict[int, StringResult] = self._talktable.batch(list(pairs.values()))

        for pair, stringref in pairs.items():
            text, sound = batch[stringref]
            pair[0].setText(str(sound))
            pair[1].setText(text)

    def selectTalkTable(self):
        filepath, filter = QFileDialog.getOpenFileName(self, "Select a TLK file", "", "TalkTable (*.tlk)")
        if filepath:
            self._talktable = TalkTable(filepath)
        self.updateTextBoxes()
