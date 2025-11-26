from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from qtpy.QtGui import QColor, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QMenu,
    QMessageBox,
    QShortcut,  # pyright: ignore[reportPrivateImportUsage]
    QTreeView,
)

from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.jrl import JRL, JRLEntry, JRLQuest, JRLQuestPriority, dismantle_jrl, read_jrl
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import QItemSelection, QPoint
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.formats.twoda.twoda_data import TwoDA


class PhaseTask(Enum):
    """Enum for tracking quest phase tasks."""
    NONE = auto()
    KILL = auto()
    TALK = auto()
    ITEM = auto()
    LOCATION = auto()
    CUSTOM = auto()


class JRLEditor(Editor):
    """Journal Editor is designed for editing JRL files.

    Journal Editor is simular to the NWN counterpart which displays quests as root items in a tree plus their respective
    entries as child items. Entries that are marked as end nodes are highlighted a dark red color. The selected entry
    or quest can be edited at the bottom of the window.
    """

    # TODO(NickHugi): JRLEditor stores a tree model and a JRL instance. These two objects must be kept in sync with each other manually:
    # eg. if you code an entry to be deleted from the journal, ensure that you delete corresponding item in the tree.
    # It would be nice at some point to create our own implementation of QAbstractItemModel that automatically mirrors
    # the JRL object.

    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        supported: list[ResourceType] = [ResourceType.JRL]
        super().__init__(parent, "Journal Editor", "journal", supported, supported, installation)

        self._jrl: JRL = JRL()
        self._model: QStandardItemModel = QStandardItemModel(self)
        from toolset.uic.qtpy.editors.jrl import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.journalTree.setModel(self._model)
        self.ui.journalTree.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.ui.splitter.setSizes([99999999, 1])
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        self.resize(400, 250)

        self._setup_menus()
        self._add_help_action()
        self._setup_signals()
        if installation is not None:  # will only be none in the unittests
            self._setup_installation(installation)

        self.new()

    def _setup_signals(self):
        self.ui.journalTree.selectionChanged = self.on_selection_changed  # type: ignore[assignment]
        self.ui.journalTree.customContextMenuRequested.connect(self.on_context_menu_requested)

        self.ui.entryTextEdit.sig_double_clicked.connect(self.change_entry_text)

        # Make sure all these signals are excusively fired through user interaction NOT when values change
        # programmatically, otherwise values bleed into other items when onSelectionChanged() fires.
        self.ui.categoryNameEdit.sig_editing_finished.connect(self.on_value_updated)
        self.ui.categoryTag.editingFinished.connect(self.on_value_updated)
        self.ui.categoryPlotSelect.currentIndexChanged.connect(self.on_value_updated)
        self.ui.categoryPlanetSelect.activated.connect(self.on_value_updated)
        self.ui.categoryPrioritySelect.activated.connect(self.on_value_updated)
        self.ui.categoryCommentEdit.sig_key_released.connect(self.on_value_updated)
        self.ui.entryIdSpin.editingFinished.connect(self.on_value_updated)
        self.ui.entryXpSpin.editingFinished.connect(self.on_value_updated)
        from toolset.gui.common.localization import translate as tr
        self.ui.entryXpSpin.setToolTip(tr("The game multiplies the value set here by 1000 to calculate actual XP to award."))
        self.ui.entryEndCheck.clicked.connect(self.on_value_updated)

        QShortcut("Del", self).activated.connect(self.on_delete_shortcut)

    def _setup_installation(self, installation: HTInstallation):
        self._installation = installation
        self.ui.categoryNameEdit.set_installation(installation)

        planets: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_PLANETS)
        if planets is None:
            from toolset.gui.common.localization import translate as tr, trf
            QMessageBox(QMessageBox.Icon.Warning, tr("Missing 2DA"), trf("'{file}.2da' is missing from your installation. Please reinstall your game, this should be in the read-only bifs.", file=HTInstallation.TwoDA_PLANETS)).exec()
            return

        plot2DA: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_PLOT)
        if plot2DA:
            self.ui.categoryPlotSelect.clear()
            self.ui.categoryPlotSelect.setPlaceholderText("[Unset]")
            self.ui.categoryPlotSelect.set_items(
                [cell.title() for cell in plot2DA.get_column("label")],
                cleanup_strings=True,
            )
            self.ui.categoryPlotSelect.set_context(plot2DA, installation, HTInstallation.TwoDA_PLOT)

        self.ui.categoryPlanetSelect.clear()
        self.ui.categoryPlanetSelect.setPlaceholderText("[Unset]")
        for row in planets:
            text = self._installation.talktable().string(row.get_integer("name", 0)) or row.get_string("label").replace("_", " ").title()
            self.ui.categoryPlanetSelect.addItem(text)
        self.ui.categoryPlanetSelect.set_context(planets, self._installation, HTInstallation.TwoDA_PLANETS)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        """Load quest data from a file.

        Args:
        ----
            filepath: Path or name of the file to load from
            resref: Resource reference
            restype: Resource type
            data: Byte data of the file

        Processing Logic:
        ----------------
            - Read JRL data from byte data
            - Clear existing model
            - Iterate through quests in JRL
                - Create item for quest
                - Refresh item with quest data
                - Add to model
            - Iterate through entries in quest
            - Create item for entry
            - Refresh item with entry data
            - Add to quest item.
        """
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

    def refresh_entry_item(self, entryItem: QStandardItem):
        """Updates the specified item's (storing entry data) text.

        Args:
        ----
            entryItem: The item to refresh.
        """
        if self._installation is None:
            text: str = f"[{entryItem.data().entry_id}] {entryItem.data().text}"
        else:
            text: str = f"[{entryItem.data().entry_id}] {self._installation.string(entryItem.data().text)}"
        entryItem.setForeground(QColor(0x880000 if entryItem.data().end else 0x000000))
        entryItem.setText(text)

    def refresh_quest_item(self, questItem: QStandardItem):
        """Updates the specified item's (storing quest data) text.

        Args:
        ----
            questItem: The item to refresh.
        """
        if self._installation is None:
            text: str = questItem.data().name or "[Unnamed]"
        else:
            text: str = self._installation.string(questItem.data().name, "[Unnamed]")
        questItem.setText(text)

    def change_quest_name(self):
        """Opens a LocalizedStringDialog for editing the name of the selected quest."""
        assert self._installation is not None, "Installation is None"
        dialog = LocalizedStringDialog(self, self._installation, self.ui.categoryNameEdit.locstring())
        if dialog.exec():
            self.ui.categoryNameEdit.set_installation(self._installation)
            self.on_value_updated()
            item: QStandardItem = self._get_item()
            quest: JRLQuest = item.data()
            quest.name = dialog.locstring
            self.refresh_quest_item(item)

    def change_entry_text(self):
        """Opens a LocalizedStringDialog for editing the text of the selected entry."""
        assert self._installation is not None, "Installation is None"
        assert self.ui.entryTextEdit.locstring is not None, "Entry text is None"
        dialog = LocalizedStringDialog(self, self._installation, self.ui.entryTextEdit.locstring)
        if dialog.exec():
            self._load_locstring(self.ui.entryTextEdit, dialog.locstring)
            self.on_value_updated()
            item: QStandardItem = self._get_item()
            entry: JRLEntry = item.data()
            entry.text = dialog.locstring
            self.refresh_entry_item(item)

    def remove_quest(self, questItem: QStandardItem):
        """Removes a quest from the journal.

        Args:
        ----
            questItem: The item in the tree that stores the quest.
        """
        quest: JRLQuest = questItem.data()
        self._model.removeRow(questItem.row())
        self._jrl.quests.remove(quest)

    def remove_entry(self, entryItem: QStandardItem):
        """Removes an entry from the journal.

        Args:
        ----
            entryItem: The item in the tree that stores the entry.
        """
        entry: JRLEntry = entryItem.data()
        entry_parent = entryItem.parent()
        if entry_parent is not None:
            entry_parent.removeRow(entryItem.row())
        for quest in self._jrl.quests:
            if entry in quest.entries:
                quest.entries.remove(entry)
                break

    def add_entry(self, quest_item: QStandardItem, newEntry: JRLEntry):
        """Adds a entry to a quest in the journal.

        Args:
        ----
            questItem: The item in the tree that stores the quest.
            newEntry: The entry to add into the quest.
        """
        entry_item = QStandardItem()
        entry_item.setData(newEntry)
        self.refresh_entry_item(entry_item)
        quest_item.appendRow(entry_item)
        quest: JRLQuest = quest_item.data()
        quest.entries.append(newEntry)

    def add_quest(self, newQuest: JRLQuest):
        """Adds a quest to the journal.

        Args:
        ----
            newQuest: The new quest to be added in.
        """
        quest_item = QStandardItem()
        quest_item.setData(newQuest)
        self.refresh_quest_item(quest_item)
        self._model.appendRow(quest_item)
        self._jrl.quests.append(newQuest)

    def on_value_updated(self, *args, **kwargs):
        """Updates the selected item in the journal tree when values change.

        This method should be connected to all the widgets that store data related quest or entry text (besides the
        ones storing localized strings, those are updated elsewhere). This method will update either all the values
        for an entry or quest based off the aforementioned widgets.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Get the selected item from the journal tree
            - Check if it is a quest or entry
            - Update the appropriate fields on the item object
            - Refresh the entry item to update the display.
        """
        item: QStandardItem = self._get_item()
        data = item.data()
        if isinstance(data, JRLQuest):  # sourcery skip: extract-method
            data.name = self.ui.categoryNameEdit.locstring()
            data.tag = self.ui.categoryTag.text()
            data.plot_index = self.ui.categoryPlotSelect.currentIndex()
            data.planet_id = self.ui.categoryPlanetSelect.currentIndex() - 1
            data.priority = JRLQuestPriority(self.ui.categoryPrioritySelect.currentIndex())
            # data.comment = self.ui.categoryCommentEdit.toPlainText()
        elif isinstance(data, JRLEntry):
            if self.ui.entryTextEdit.locstring is not None:
                data.text = self.ui.entryTextEdit.locstring
            data.end = self.ui.entryEndCheck.isChecked()
            data.xp_percentage = self.ui.entryXpSpin.value()
            data.entry_id = self.ui.entryIdSpin.value()
            self.refresh_entry_item(item)

    def on_selection_changed(self, selection: QItemSelection, deselected: QItemSelection):
        """Updates UI on journal tree selection change.

        This method should be connected to a signal that emits when selection changes for the journalTree widget. It
        will update the widget values that store data for either entries or quests, depending what has been selected
        in the tree.

        Args:
        ----
            selection: QItemSelection - Current selection
            deselected: QItemSelection - Previously selected

        Updates UI elements based on selected item:
            - Sets category/entry details from selected Quest/Entry data
            - Blocks signals while updating to prevent duplicate calls
            - Handles selection of Quest or Entry differently
        """
        QTreeView.selectionChanged(self.ui.journalTree, selection, deselected)

        # Block signals to prevent recursive updates
        widgets_to_block = [
            self.ui.categoryCommentEdit,
            self.ui.entryTextEdit,
            self.ui.categoryNameEdit,
            self.ui.categoryPlotSelect,
            self.ui.categoryPlanetSelect,
            self.ui.categoryPrioritySelect,
            self.ui.entryEndCheck,
            self.ui.entryXpSpin,
            self.ui.entryIdSpin
        ]

        for widget in widgets_to_block:
            widget.blockSignals(True)

        try:
            if selection.indexes():
                index = selection.indexes()[0]
                item = self._model.itemFromIndex(index)
                if item is None:
                    return

                data = item.data()
                if isinstance(data, JRLQuest):
                    self.ui.questPages.setCurrentIndex(0)
                    if self._installation is not None:
                        self.ui.categoryNameEdit.set_locstring(data.name)
                    self.ui.categoryPlotSelect.setCurrentIndex(data.plot_index)
                    self.ui.categoryPlanetSelect.setCurrentIndex(data.planet_id + 1)
                    self.ui.categoryPrioritySelect.setCurrentIndex(data.priority.value)

                elif isinstance(data, JRLEntry):
                    self.ui.questPages.setCurrentIndex(1)
                    if self._installation is not None:
                        self._load_locstring(self.ui.entryTextEdit, data.text)
                    self.ui.entryEndCheck.setChecked(data.end)
                    self.ui.entryXpSpin.setValue(data.xp_percentage)
                    self.ui.entryIdSpin.setValue(data.entry_id)
        finally:
            # Always unblock signals
            for widget in widgets_to_block:
                widget.blockSignals(False)

    def on_context_menu_requested(self, point: QPoint):
        """Handle context menu requests for the journal tree widget.

        This method should be connected to the customContextMenuRequested of the journalTree object. This will popup the
        context menu and display various options depending on if there is an item selected in the tree and what kind
        of data the item stores (Quest or Entry).

        Args:
        ----
            point: QPoint: The position of the context menu request

        Processing Logic:
        ----------------
            - Get the index and item at the point of the context menu request
            - Create a QMenu object
            - Check if an item was selected and get its data
            - Add appropriate actions to the menu based on the data type
            - Popup the menu at the global position of the context menu request.
        """
        index = self.ui.journalTree.indexAt(point)
        item = self._model.itemFromIndex(index)

        menu = QMenu(self)

        if item:
            item = self._get_item()
            data = item.data()

            if isinstance(data, JRLQuest):
                menu.addAction("Add Entry").triggered.connect(lambda: self.add_entry(item, JRLEntry()))
                menu.addAction("Remove Quest").triggered.connect(lambda: self.remove_quest(item))
                # it's not easy to right click without selecting an item - add the 'addQuest' action here as well.
                menu.addSeparator()
                menu.addAction("Add Quest").triggered.connect(lambda: self.add_quest(JRLQuest()))
            elif isinstance(data, JRLEntry):
                menu.addAction("Remove Entry").triggered.connect(lambda: self.remove_entry(item))
        else:
            menu.addAction("Add Quest").triggered.connect(lambda: self.add_quest(JRLQuest()))

        jrlTree_viewport = self.ui.journalTree.viewport()
        assert jrlTree_viewport is not None, "Journal tree viewport is None"
        menu.popup(jrlTree_viewport.mapToGlobal(point))

    def on_delete_shortcut(self):
        """Deletes selected shortcut from journal tree.

        This method should be connected to the activated signal of a QShortcut. The method will delete the selected
        item from the tree.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Check if any items are selected in the journal tree
            - Get the index and item for the selected item
            - Check if the item is a root (quest) or child (entry) item
            - Call the appropriate method to remove the quest or entry.
        """
        if self.ui.journalTree.selectedIndexes():
            item = self._get_item()
            if item.parent() is None:  # ie. root item, therefore quest
                self.remove_quest(item)
            else:  # child item, therefore entry
                self.remove_entry(item)

    def _get_item(self) -> QStandardItem:
        index = self.ui.journalTree.selectedIndexes()[0]
        result = self._model.itemFromIndex(index)
        assert result is not None, f"Could not find journalTree index '{index}'"
        return result
