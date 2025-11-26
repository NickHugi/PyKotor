from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtGui import QColor, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QShortcut  # pyright: ignore[reportPrivateImportUsage]

from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.jrl import JRL, dismantle_jrl, read_jrl
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.resource.generics.jrl import JRLEntry, JRLQuest


class SAVEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        supported: list[ResourceType] = [ResourceType.SAV, ResourceType.RES]
        super().__init__(parent, "Save Editor", "save", supported, supported, installation)
        self.resize(400, 250)

        from toolset.uic.qtpy.editors.sav import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._add_help_action()
        self._setup_signals()
        if installation is not None:  # will only be none in the unittests
            self._setup_installation(installation)

        self._jrl: JRL = JRL()
        self._model: QStandardItemModel = QStandardItemModel(self)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.new()

    def _setup_signals(self):
        QShortcut("Del", self).activated.connect(self.on_delete_shortcut)

    def _setup_installation(
        self,
        installation: HTInstallation,
    ):
        self._installation = installation

        planets: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_PLANETS)
        if planets is None:
            return
        for row in planets:
            (
                installation.talktable().string(row.get_integer("name", 0))  # pyright: ignore[reportUnusedExpression]
                or row.get_string("label").replace("_", " ").title()
            )

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)

        self._jrl = read_jrl(data)

        self._model.clear()
        for quest in self._jrl.quests:
            quest_item = QStandardItem()
            quest_item.setData(quest)
            self.refresh_quest_item(quest_item)
            self._model.appendRow(quest_item)

            for entry in quest.entries:
                entry_item = QStandardItem()
                entry_item.setData(entry)
                self.refresh_entry_item(entry_item)
                quest_item.appendRow(entry_item)

    def build(self) -> tuple[bytes, bytes]:
        data = bytearray()
        write_gff(dismantle_jrl(self._jrl), data)
        return data, b""

    def new(self):
        super().new()
        self._jrl = JRL()
        self._model.clear()

    def refresh_entry_item(
        self,
        entry_item: QStandardItem,
    ):
        text: str = f"[{entry_item.data().entry_id}] {self._installation.string(entry_item.data().text)}"
        entry_item.setForeground(QColor(0x880000 if entry_item.data().end else 0x000000))
        entry_item.setText(text)

    def refresh_quest_item(
        self,
        quest_item: QStandardItem,
    ):
        text: str = self._installation.string(quest_item.data().name, "[Unnamed]")
        quest_item.setText(text)

    def remove_quest(
        self,
        quest_item: QStandardItem,
    ):
        quest: JRLQuest = quest_item.data()
        self._model.removeRow(quest_item.row())
        self._jrl.quests.remove(quest)

    def remove_entry(
        self,
        entry_item: QStandardItem,
    ):
        entry: JRLEntry = entry_item.data()
        entry_item.parent().removeRow(entry_item.row())
        for quest in self._jrl.quests:
            if entry in quest.entries:
                quest.entries.remove(entry)
                break

    def add_entry(
        self,
        quest_item: QStandardItem,
        new_entry: JRLEntry,
    ):
        entry_item = QStandardItem()
        entry_item.setData(new_entry)
        self.refresh_entry_item(entry_item)
        quest_item.appendRow(entry_item)
        quest: JRLQuest = quest_item.data()
        quest.entries.append(new_entry)

    def add_quest(
        self,
        new_quest: JRLQuest,
    ):
        quest_item = QStandardItem()
        quest_item.setData(new_quest)
        self.refresh_quest_item(quest_item)
        self._model.appendRow(quest_item)
        self._jrl.quests.append(new_quest)
