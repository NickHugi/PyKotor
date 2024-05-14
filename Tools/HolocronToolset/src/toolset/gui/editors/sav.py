from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtGui import QColor, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QShortcut

from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.jrl import JRL, dismantle_jrl, read_jrl
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from PyQt5.QtWidgets import QWidget

    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.resource.generics.jrl import JRLEntry, JRLQuest


class SAVEditor(Editor):
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        supported: list[ResourceType] = [ResourceType.SAV, ResourceType.RES]
        super().__init__(parent, "Save Editor", "save", supported, supported, installation)
        self.resize(400, 250)

        from toolset.uic.editors.sav import Ui_MainWindow  # pylint: disable=C0415

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        if installation is not None:  # will only be none in the unittests
            self._setupInstallation(installation)

        self._jrl: JRL = JRL()
        self._model: QStandardItemModel = QStandardItemModel(self)

        self.new()

    def _setupSignals(self):
        QShortcut("Del", self).activated.connect(self.onDeleteShortcut)

    def _setupInstallation(self, installation: HTInstallation):
        self._installation = installation

        planets: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_PLANETS)
        for row in planets:
            (
                self._installation.talktable().string(row.get_integer("name", 0))
                or row.get_string("label").replace("_", " ").title()
            )

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        super().load(filepath, resref, restype, data)

        self._jrl = read_jrl(data)

        self._model.clear()
        for quest in self._jrl.quests:
            questItem = QStandardItem()
            questItem.setData(quest)
            self.refreshQuestItem(questItem)
            self._model.appendRow(questItem)

            for entry in quest.entries:
                entryItem = QStandardItem()
                entryItem.setData(entry)
                self.refreshEntryItem(entryItem)
                questItem.appendRow(entryItem)

    def build(self) -> tuple[bytes, bytes]:
        data = bytearray()
        write_gff(dismantle_jrl(self._jrl), data)
        return data, b""

    def new(self):
        super().new()
        self._jrl = JRL()
        self._model.clear()

    def refreshEntryItem(self, entryItem: QStandardItem):
        text: str = f"[{entryItem.data().entry_id}] {self._installation.string(entryItem.data().text)}"
        entryItem.setForeground(QColor(0x880000 if entryItem.data().end else 0x000000))
        entryItem.setText(text)

    def refreshQuestItem(self, questItem: QStandardItem):
        text: str = self._installation.string(questItem.data().name, "[Unnamed]")
        questItem.setText(text)

    def removeQuest(self, questItem: QStandardItem):
        quest: JRLQuest = questItem.data()
        self._model.removeRow(questItem.row())
        self._jrl.quests.remove(quest)

    def removeEntry(self, entryItem: QStandardItem):
        entry: JRLEntry = entryItem.data()
        entryItem.parent().removeRow(entryItem.row())
        for quest in self._jrl.quests:
            if entry in quest.entries:
                quest.entries.remove(entry)
                break

    def addEntry(self, questItem: QStandardItem, newEntry: JRLEntry):
        entryItem = QStandardItem()
        entryItem.setData(newEntry)
        self.refreshEntryItem(entryItem)
        questItem.appendRow(entryItem)
        quest: JRLQuest = questItem.data()
        quest.entries.append(newEntry)

    def addQuest(self, newQuest: JRLQuest):
        questItem = QStandardItem()
        questItem.setData(newQuest)
        self.refreshQuestItem(questItem)
        self._model.appendRow(questItem)
        self._jrl.quests.append(newQuest)
