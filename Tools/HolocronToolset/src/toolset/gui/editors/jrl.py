from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtGui import QColor, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QMenu, QShortcut, QTreeView

from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.jrl import JRL, JRLEntry, JRLQuest, JRLQuestPriority, dismantle_jrl, read_jrl
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget
    import os

    from PyQt5.QtCore import QItemSelection, QPoint

    from pykotor.resource.formats.twoda.twoda_data import TwoDA


class JRLEditor(Editor):
    """Journal Editor is designed for editing JRL files.

    Journal Editor is simular to the NWN counterpart which displays quests as root items in a tree plus their respective
    entries as child items. Entries that are marked as end nodes are highlighted a dark red color. The selected entry
    or quest can be edited at the bottom of the window.
    """

    # JRLEditor stores a tree model and a JRL instance. These two objects must be kept in sync with each other manually:
    # eg. if you code an entry to be deleted from the journal, ensure that you delete corresponding item in the tree.\
    # It would be nice at some point to create our own implementation of QAbstractItemModel that automatically mirrors
    # the JRL object.

    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        """Initializes the Journal Editor window.

        Args:
        ----
            parent: {QWidget}: Parent widget
            installation: {HTInstallation}: HTInstallation object

        Processing Logic:
        ----------------
            - Sets up the UI from the designed form
            - Initializes the JRL object and model
            - Connects menu and signal handlers
            - Sets the installation if provided
            - Displays an empty new journal by default.
        """
        supported: list[ResourceType] = [ResourceType.JRL]
        super().__init__(parent, "Journal Editor", "journal", supported, supported, installation)
        self.resize(400, 250)

        from toolset.uic.editors.jrl import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        self._setupInstallation(installation)

        self._jrl: JRL = JRL()
        self._model: QStandardItemModel = QStandardItemModel(self)

        self.ui.journalTree.setModel(self._model)

        # Make the bottom panel take as little space possible
        self.ui.splitter.setSizes([99999999, 1])

        self.new()

    def _setupSignals(self):
        """Setup signals for journal UI interactions.

        Args:
        ----
            self: {The class instance}: The class instance

        Processing Logic:
        ----------------
            - Connect selectionChanged signal on journal tree to onSelectionChanged handler
            - Connect customContextMenuRequested signal on journal tree to onContextMenuRequested handler
            - Connect doubleClicked signal on entry text edit to changeEntryText handler
            - Connect various editingFinished and activated signals on category/entry fields to onValueUpdated handler to only trigger on user interaction
            - Connect "Del" keyboard shortcut to onDeleteShortcut handler.
        """
        self.ui.journalTree.selectionChanged = self.onSelectionChanged
        self.ui.journalTree.customContextMenuRequested.connect(self.onContextMenuRequested)

        self.ui.entryTextEdit.doubleClicked.connect(self.changeEntryText)

        # Make sure all these signals are excusively fired through user interaction NOT when values change
        # programmatically, otherwise values bleed into other items when onSelectionChanged() fires.
        self.ui.categoryNameEdit.editingFinished.connect(self.onValueUpdated)
        self.ui.categoryTag.editingFinished.connect(self.onValueUpdated)
        self.ui.categoryPlotSpin.editingFinished.connect(self.onValueUpdated)
        self.ui.categoryPlanetSelect.activated.connect(self.onValueUpdated)
        self.ui.categoryPrioritySelect.activated.connect(self.onValueUpdated)
        self.ui.categoryCommentEdit.keyReleased.connect(self.onValueUpdated)
        self.ui.entryIdSpin.editingFinished.connect(self.onValueUpdated)
        self.ui.entryXpSpin.editingFinished.connect(self.onValueUpdated)
        self.ui.entryEndCheck.clicked.connect(self.onValueUpdated)

        QShortcut("Del", self).activated.connect(self.onDeleteShortcut)

    def _setupInstallation(self, installation: HTInstallation):
        self._installation = installation
        self.ui.categoryNameEdit.setInstallation(installation)

        planets: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_PLANETS)

        self.ui.categoryPlanetSelect.clear()
        self.ui.categoryPlanetSelect.addItem("[None]", -1)
        for row in planets:
            text = self._installation.talktable().string(row.get_integer("name", 0)) or row.get_string("label").replace("_", " ").title()
            self.ui.categoryPlanetSelect.addItem(text)

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
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
        """Updates the specified item's (storing entry data) text.

        Args:
        ----
            entryItem: The item to refresh.
        """
        text: str = f"[{entryItem.data().entry_id}] {self._installation.string(entryItem.data().text)}"
        entryItem.setForeground(QColor(0x880000 if entryItem.data().end else 0x000000))
        entryItem.setText(text)

    def refreshQuestItem(self, questItem: QStandardItem):
        """Updates the specified item's (storing quest data) text.

        Args:
        ----
            questItem: The item to refresh.
        """
        text: str = self._installation.string(questItem.data().name, "[Unnamed]")
        questItem.setText(text)

    def changeQuestName(self):
        """Opens a LocalizedStringDialog for editing the name of the selected quest."""
        dialog = LocalizedStringDialog(self, self._installation, self.ui.categoryNameEdit.locstring())
        if dialog.exec_():
            self.ui.categoryNameEdit.setInstallation(self._installation)
            self.onValueUpdated()
            item: QStandardItem = self._get_item()
            quest: JRLQuest = item.data()
            quest.name = dialog.locstring
            self.refreshQuestItem(item)

    def changeEntryText(self):
        """Opens a LocalizedStringDialog for editing the text of the selected entry."""
        dialog = LocalizedStringDialog(self, self._installation, self.ui.entryTextEdit.locstring)  # FIXME: locstring or locstring()?
        if dialog.exec_():
            self._loadLocstring(self.ui.entryTextEdit, dialog.locstring)
            self.onValueUpdated()
            item: QStandardItem = self._get_item()
            entry: JRLEntry = item.data()
            entry.text = dialog.locstring
            self.refreshEntryItem(item)

    def removeQuest(self, questItem: QStandardItem):
        """Removes a quest from the journal.

        Args:
        ----
            questItem: The item in the tree that stores the quest.
        """
        quest: JRLQuest = questItem.data()
        self._model.removeRow(questItem.row())
        self._jrl.quests.remove(quest)

    def removeEntry(self, entryItem: QStandardItem):
        """Removes an entry from the journal.

        Args:
        ----
            entryItem: The item in the tree that stores the entry.
        """
        entry: JRLEntry = entryItem.data()
        entryItem.parent().removeRow(entryItem.row())
        for quest in self._jrl.quests:
            if entry in quest.entries:
                quest.entries.remove(entry)
                break

    def addEntry(self, questItem: QStandardItem, newEntry: JRLEntry):
        """Adds a entry to a quest in the journal.

        Args:
        ----
            questItem: The item in the tree that stores the quest.
            newEntry: The entry to add into the quest.
        """
        entryItem = QStandardItem()
        entryItem.setData(newEntry)
        self.refreshEntryItem(entryItem)
        questItem.appendRow(entryItem)
        quest: JRLQuest = questItem.data()
        quest.entries.append(newEntry)

    def addQuest(self, newQuest: JRLQuest):
        """Adds a quest to the journal.

        Args:
        ----
            newQuest: The new quest to be added in.
        """
        questItem = QStandardItem()
        questItem.setData(newQuest)
        self.refreshQuestItem(questItem)
        self._model.appendRow(questItem)
        self._jrl.quests.append(newQuest)

    def onValueUpdated(self):
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
            data.plot_index = self.ui.categoryPlotSpin.value()
            data.planet_id = self.ui.categoryPlanetSelect.currentIndex() - 1
            data.priority = JRLQuestPriority(self.ui.categoryPrioritySelect.currentIndex())
            data.comment = self.ui.categoryCommentEdit.toPlainText()
        elif isinstance(data, JRLEntry):
            data.text = self.ui.entryTextEdit.locstring
            data.end = self.ui.entryEndCheck.isChecked()
            data.xp_percentage = self.ui.entryXpSpin.value()
            data.entry_id = self.ui.entryIdSpin.value()
            self.refreshEntryItem(item)

    def onSelectionChanged(self, selection: QItemSelection, deselected: QItemSelection):
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
        self.ui.categoryCommentEdit.blockSignals(True)
        self.ui.entryTextEdit.blockSignals(True)

        if selection.indexes():
            index = selection.indexes()[0]
            item = self._model.itemFromIndex(index)
            assert item is not None, f"Could not find journalTree index '{index}'"
            data = item.data()
            if isinstance(data, JRLQuest):  # sourcery skip: extract-method
                self.ui.questPages.setCurrentIndex(0)
                self.ui.categoryNameEdit.setLocstring(data.name)
                self.ui.categoryTag.setText(data.tag)
                self.ui.categoryPlotSpin.setValue(data.plot_index)
                self.ui.categoryPlanetSelect.setCurrentIndex(data.planet_id + 1)
                self.ui.categoryPrioritySelect.setCurrentIndex(data.priority.value)
                self.ui.categoryCommentEdit.setPlainText(data.comment)
            elif isinstance(data, JRLEntry):
                self.ui.questPages.setCurrentIndex(1)
                self._loadLocstring(self.ui.entryTextEdit, data.text)
                self.ui.entryEndCheck.setChecked(data.end)
                self.ui.entryXpSpin.setValue(data.xp_percentage)
                self.ui.entryIdSpin.setValue(data.entry_id)

        self.ui.categoryCommentEdit.blockSignals(False)
        self.ui.entryTextEdit.blockSignals(False)

    def onContextMenuRequested(self, point: QPoint):
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
                menu.addAction("Add Entry").triggered.connect(lambda: self.addEntry(item, JRLEntry()))
                menu.addAction("Remove Quest").triggered.connect(lambda: self.removeQuest(item))
            elif isinstance(data, JRLEntry):
                menu.addAction("Remove Entry").triggered.connect(lambda: self.removeEntry(item))
        else:
            menu.addAction("Add Quest").triggered.connect(lambda: self.addQuest(JRLQuest()))

        menu.popup(self.ui.journalTree.viewport().mapToGlobal(point))

    def onDeleteShortcut(self):
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
                self.removeQuest(item)
            else:  # child item, therefore entry
                self.removeEntry(item)

    def _get_item(self):
        index = self.ui.journalTree.selectedIndexes()[0]
        result = self._model.itemFromIndex(index)
        assert result is not None, f"Could not find journalTree index '{index}'"
        return result
