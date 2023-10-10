from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, NamedTuple, Optional, Union

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint, QSize, QSortFilterProxyModel, QThread
from PyQt5.QtGui import (
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QIcon,
    QPixmap,
    QStandardItem,
    QStandardItemModel,
)
from PyQt5.QtWidgets import (
    QAction,
    QDialog,
    QFrame,
    QLabel,
    QMenu,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from pykotor.common.misc import EquipmentSlot, InventoryItem, ResRef
from pykotor.common.stream import BinaryReader
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier, ResourceResult
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.tlk import TLK, read_tlk
from pykotor.resource.generics.uti import UTI, read_uti
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath
from toolset.data.installation import HTInstallation

if TYPE_CHECKING:
    import os

_RESNAME_ROLE = QtCore.Qt.UserRole + 1
_FILEPATH_ROLE = QtCore.Qt.UserRole + 2
_SLOTS_ROLE = QtCore.Qt.UserRole + 3


class SlotMapping(NamedTuple):
    label: QLabel
    frame: DropFrame
    emptyImage: str


class InventoryEditor(QDialog):
    def __init__(
        self,
        parent: QWidget,
        installation: HTInstallation,
        capsules: list[Capsule],
        folders: list[str],
        inventory: list[InventoryItem],
        equipment: dict[EquipmentSlot, InventoryItem],
        droid: bool = False,
        hide_equipment: bool = False,
        is_store: bool = False,
    ):
        super().__init__(parent)

        from toolset.uic.dialogs.inventory import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.contentsTable.is_store = is_store

        self.ui.coreTree.setSortingEnabled(True)
        self.ui.coreTree.sortByColumn(0, QtCore.Qt.DescendingOrder)
        self.ui.modulesTree.setSortingEnabled(True)
        self.ui.modulesTree.sortByColumn(0, QtCore.Qt.DescendingOrder)
        self.ui.overrideTree.setSortingEnabled(True)
        self.ui.overrideTree.sortByColumn(0, QtCore.Qt.DescendingOrder)
        self.ui.coreSearchEdit.textEdited.connect(self.doSearch)
        self.ui.modulesSearchEdit.textEdited.connect(self.doSearch)
        self.ui.modulesSearchEdit.textEdited.connect(self.doSearch)

        self._installation: HTInstallation = installation
        self._capsules: list[Capsule] = capsules
        self._slotMap: dict[EquipmentSlot, SlotMapping] = {
            EquipmentSlot.IMPLANT: SlotMapping(self.ui.implantPicture, self.ui.implantFrame, ":/images/inventory/{}_implant.png"),
            EquipmentSlot.HEAD: SlotMapping(self.ui.headPicture, self.ui.headFrame, ":/images/inventory/{}_head.png"),
            EquipmentSlot.GAUNTLET: SlotMapping(
                self.ui.gauntletPicture,
                self.ui.gauntletFrame,
                ":/images/inventory/{}_gauntlet.png",
            ),
            EquipmentSlot.LEFT_ARM: SlotMapping(self.ui.armlPicture, self.ui.armlFrame, ":/images/inventory/{}_forearm_l.png"),
            EquipmentSlot.ARMOR: SlotMapping(self.ui.armorPicture, self.ui.armorFrame, ":/images/inventory/{}_armor.png"),
            EquipmentSlot.RIGHT_ARM: SlotMapping(self.ui.armrPicture, self.ui.armrFrame, ":/images/inventory/{}_forearm_r.png"),
            EquipmentSlot.LEFT_HAND: SlotMapping(self.ui.handlPicture, self.ui.handlFrame, ":/images/inventory/{}_hand_l.png"),
            EquipmentSlot.BELT: SlotMapping(self.ui.beltPicture, self.ui.beltFrame, ":/images/inventory/{}_belt.png"),
            EquipmentSlot.RIGHT_HAND: SlotMapping(self.ui.handrPicture, self.ui.handrFrame, ":/images/inventory/{}_hand_r.png"),
            EquipmentSlot.CLAW1: SlotMapping(self.ui.claw1Picture, self.ui.claw1Frame, ":/images/inventory/{}_gauntlet.png"),
            EquipmentSlot.CLAW2: SlotMapping(self.ui.claw2Picture, self.ui.claw2Frame, ":/images/inventory/{}_gauntlet.png"),
            EquipmentSlot.CLAW3: SlotMapping(self.ui.claw3Picture, self.ui.claw3Frame, ":/images/inventory/{}_gauntlet.png"),
            EquipmentSlot.HIDE: SlotMapping(self.ui.hidePicture, self.ui.hideFrame, ":/images/inventory/{}_armor.png"),
        }
        self._droid = droid
        self.inventory: list[InventoryItem] = inventory
        self.equipment: dict[EquipmentSlot, InventoryItem] = equipment
        self.is_store: bool = is_store

        self.ui.implantFrame.itemDropped.connect(
            lambda filepath, resname, name: self.setEquipment(EquipmentSlot.IMPLANT, resname, filepath, name),
        )
        self.ui.headFrame.itemDropped.connect(
            lambda filepath, resname, name: self.setEquipment(EquipmentSlot.HEAD, resname, filepath, name),
        )
        self.ui.gauntletFrame.itemDropped.connect(
            lambda filepath, resname, name: self.setEquipment(EquipmentSlot.GAUNTLET, resname, filepath, name),
        )
        self.ui.armlFrame.itemDropped.connect(
            lambda filepath, resname, name: self.setEquipment(EquipmentSlot.LEFT_ARM, resname, filepath, name),
        )
        self.ui.armorFrame.itemDropped.connect(
            lambda filepath, resname, name: self.setEquipment(EquipmentSlot.ARMOR, resname, filepath, name),
        )
        self.ui.armrFrame.itemDropped.connect(
            lambda filepath, resname, name: self.setEquipment(EquipmentSlot.RIGHT_ARM, resname, filepath, name),
        )
        self.ui.handlFrame.itemDropped.connect(
            lambda filepath, resname, name: self.setEquipment(EquipmentSlot.LEFT_HAND, resname, filepath, name),
        )
        self.ui.beltFrame.itemDropped.connect(
            lambda filepath, resname, name: self.setEquipment(EquipmentSlot.BELT, resname, filepath, name),
        )
        self.ui.handrFrame.itemDropped.connect(
            lambda filepath, resname, name: self.setEquipment(EquipmentSlot.RIGHT_HAND, resname, filepath, name),
        )
        self.ui.hideFrame.itemDropped.connect(
            lambda filepath, resname, name: self.setEquipment(EquipmentSlot.HIDE, resname, filepath, name),
        )
        self.ui.claw1Frame.itemDropped.connect(
            lambda filepath, resname, name: self.setEquipment(EquipmentSlot.CLAW1, resname, filepath, name),
        )
        self.ui.claw2Frame.itemDropped.connect(
            lambda filepath, resname, name: self.setEquipment(EquipmentSlot.CLAW2, resname, filepath, name),
        )
        self.ui.claw3Frame.itemDropped.connect(
            lambda filepath, resname, name: self.setEquipment(EquipmentSlot.CLAW3, resname, filepath, name),
        )

        self.ui.implantFrame.customContextMenuRequested.connect(
            lambda point: self.openItemContextMenu(self.ui.implantFrame, point),
        )
        self.ui.headFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.headFrame, point))
        self.ui.gauntletFrame.customContextMenuRequested.connect(
            lambda point: self.openItemContextMenu(self.ui.gauntletFrame, point),
        )
        self.ui.armlFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.armlFrame, point))
        self.ui.armorFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.armorFrame, point))
        self.ui.armrFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.armrFrame, point))
        self.ui.handlFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.handlFrame, point))
        self.ui.beltFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.beltFrame, point))
        self.ui.handrFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.handrFrame, point))
        self.ui.hideFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.hideFrame, point))
        self.ui.claw1Frame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.claw1Frame, point))
        self.ui.claw2Frame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.claw2Frame, point))
        self.ui.claw3Frame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.claw3Frame, point))

        self.ui.okButton.clicked.connect(self.accept)
        self.ui.cancelButton.clicked.connect(self.reject)

        self.ui.implantFrame.slot = EquipmentSlot.IMPLANT
        self.ui.headFrame.slot = EquipmentSlot.HEAD
        self.ui.gauntletFrame.slot = EquipmentSlot.GAUNTLET
        self.ui.armlFrame.slot = EquipmentSlot.LEFT_ARM
        self.ui.armorFrame.slot = EquipmentSlot.ARMOR
        self.ui.armrFrame.slot = EquipmentSlot.RIGHT_ARM
        self.ui.handlFrame.slot = EquipmentSlot.LEFT_HAND
        self.ui.beltFrame.slot = EquipmentSlot.BELT
        self.ui.handrFrame.slot = EquipmentSlot.RIGHT_HAND
        self.ui.hideFrame.slot = EquipmentSlot.HIDE
        self.ui.claw1Frame.slot = EquipmentSlot.CLAW1
        self.ui.claw2Frame.slot = EquipmentSlot.CLAW2
        self.ui.claw3Frame.slot = EquipmentSlot.CLAW3

        self.ui.contentsTable.setColumnWidth(0, 64)

        for slot in [slot for slot in EquipmentSlot if slot in self._slotMap]:
            image = self._slotMap[slot].emptyImage.format("droid" if droid else "human")
            self._slotMap[slot].label.setPixmap(QPixmap(image))

        for slot, item in self.equipment.items():
            self.setEquipment(slot, item.resref.get())

        for item in self.inventory:
            self.ui.contentsTable.addItem(item.resref.get(), item.droppable, item.infinite)

        self.ui.tabWidget_2.setVisible(not hide_equipment)

        self.buildItems()

    def accept(self) -> None:
        super().accept()
        self.inventory = []
        for i in range(self.ui.contentsTable.rowCount()):
            tableItem: ItemContainer = self.ui.contentsTable.item(i, 1)
            self.inventory.append(InventoryItem(ResRef(tableItem.resname), tableItem.droppable, tableItem.infinite))

        self.equipment = {}
        for widget in self.ui.standardEquipmentTab.children() + self.ui.naturalEquipmentTab.children():
            # Very hacky, but isinstance is not working (possibly due to how DropFrame is imported in _ui.py file.
            # Also make sure there is an item in the slot otherwise the GFF will create a struct for each slot.
            if "DropFrame" in str(type(widget)) and widget.resname:
                self.equipment[widget.slot] = InventoryItem(ResRef(widget.resname), widget.droppable, widget.infinite)

    def buildItems(self) -> None:
        itemBuilderDialog = ItemBuilderDialog(self, self._installation, self._capsules)
        if itemBuilderDialog.exec_():
            if self._installation.cacheCoreItems is None:
                coreModel = itemBuilderDialog.coreModel
                self._installation.cacheCoreItems = coreModel
            else:
                coreModel = self._installation.cacheCoreItems
            self.ui.coreTree.setModel(coreModel.proxyModel())

            self.ui.modulesTree.setModel(itemBuilderDialog.modulesModel.proxyModel())
            self.ui.overrideTree.setModel(itemBuilderDialog.overrideModel.proxyModel())
        else:
            self.reject()

    def getItemImage(self, uti: Optional[UTI]) -> QPixmap:
        return self._installation.getItemIconFromUTI(uti)

    def getItem(self, resname: str, filepath: os.PathLike | str) -> tuple[os.PathLike, str, UTI]:
        uti: UTI | None = None
        name: str = ""
        c_filepath = CaseAwarePath(filepath)
        if not c_filepath.exists():
            result = self._installation.resource(resname, ResourceType.UTI)
            if result is not None:
                uti = read_uti(result.data)
                filepath = result.filepath
                name = self._installation.string(uti.name, "[No Name]")
        elif c_filepath.endswith((".rim", ".mod", ".erf")):
            uti = read_uti(Capsule(filepath).resource(resname, ResourceType.UTI))
            name = self._installation.string(uti.name, "[No Name]")
        elif c_filepath.endswith(".bif"):
            uti = read_uti(self._installation.resource(resname, ResourceType.UTI, [SearchLocation.CHITIN]).data)
            name = self._installation.string(uti.name, "[No Name]")
        else:
            uti = read_uti(BinaryReader.load_file(filepath))
        return c_filepath, name, uti

    def setEquipment(self, slot: EquipmentSlot, resname: str, filepath: os.PathLike | str = "", name: str = "") -> None:
        slotPicture = self._slotMap[slot].label

        if resname != "":
            filepath, name, uti = self.getItem(resname, filepath)

            slotPicture.setToolTip(f"{resname}\n{filepath}\n{name}")
            slotPicture.setPixmap(self.getItemImage(uti))
            self._slotMap[slot].frame.setItem(resname, str(filepath), name, False, False)
        else:
            image = self._slotMap[slot].emptyImage.format("droid" if self._droid else "human")
            slotPicture.setToolTip("")
            slotPicture.setPixmap(QPixmap(image))

    def doSearch(self, text: str):
        self.ui.coreSearchEdit.setText(text)
        self.ui.modulesSearchEdit.setText(text)
        self.ui.overrideSearchEdit.setText(text)
        self.ui.coreTree.model().setFilterFixedString(text)
        self.ui.modulesTree.model().setFilterFixedString(text)
        self.ui.overrideTree.model().setFilterFixedString(text)

    def openItemContextMenu(self, widget: Union[QWidget, ItemContainer], point: QPoint) -> None:
        menu = QMenu(self)

        if widget.hasItem:
            if self.is_store:
                infiniteAction = QAction("Infinite")
                infiniteAction.setCheckable(True)
                infiniteAction.setChecked(widget.infinite)
                infiniteAction.triggered.connect(widget.toggleInfinite)
                menu.addAction(infiniteAction)
            else:
                droppableAction = QAction("Droppable")
                droppableAction.setCheckable(True)
                droppableAction.setChecked(widget.droppable)
                droppableAction.triggered.connect(widget.toggleDroppable)
                menu.addAction(droppableAction)

            removeAction = QAction("Remove Item")
            removeAction.triggered.connect(widget.removeItem)

            menu.addSeparator()
            menu.addAction(removeAction)
        else:
            noItemAction = QAction("No Item")
            noItemAction.setEnabled(False)
            menu.addAction(noItemAction)

        menu.addSeparator()
        setItemAction = QAction("Set Item ResRef")
        setItemAction.triggered.connect(lambda: self.promptSetItemResRefDialog(widget))
        menu.addAction(setItemAction)

        menu.exec_(widget.mapToGlobal(point))

    def promptSetItemResRefDialog(self, widget: DropFrame) -> None:
        dialog = SetItemResRefDialog()

        if dialog.exec_():
            self.setEquipment(widget.slot, dialog.resref())


class ItemContainer:
    def __init__(self, droppable: bool = False, infinite: bool = False):
        self.resname: str = ""
        self.filepath: str = ""
        self.name: str = ""
        self.hasItem: bool = False
        self.droppable: bool = droppable
        self.infinite: bool = infinite

    def removeItem(self):
        self.resname = ""
        self.filepath = ""
        self.name = ""
        self.hasItem = False
        self.droppable = False
        self.infinite = False

    def setItem(self, resname: str, filepath: str, name: str, droppable: bool, infinite: bool):
        self.resname = resname
        self.filepath = filepath
        self.name = name
        self.hasItem = True
        self.droppable = droppable
        self.infinite = infinite

    def toggleDroppable(self):
        self.droppable = not self.droppable

    def toggleInfinite(self):
        self.infinite = not self.infinite


class DropFrame(ItemContainer, QFrame):
    itemDropped = QtCore.pyqtSignal(object, object, object)

    def __init__(self, parent):
        QFrame.__init__(self)
        ItemContainer.__init__(self)
        self.setFrameShape(QFrame.Box)
        self.setAcceptDrops(True)
        self.slot: EquipmentSlot = EquipmentSlot.HIDE

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:
        if isinstance(e.source(), QTreeView):
            tree: QTreeView = e.source()
            proxyModel: QSortFilterProxyModel = tree.model()
            model: ItemModel = proxyModel.sourceModel()
            index = proxyModel.mapToSource(tree.selectedIndexes()[0])
            item = model.itemFromIndex(index)
            if item.data(_SLOTS_ROLE) & self.slot.value:
                e.accept()

    def dragMoveEvent(self, e: QDragMoveEvent):
        if isinstance(e.source(), QTreeView):
            tree: QTreeView = e.source()
            proxyModel: QSortFilterProxyModel = tree.model()
            model: ItemModel = proxyModel.sourceModel()
            index = proxyModel.mapToSource(tree.selectedIndexes()[0])
            item = model.itemFromIndex(index)
            if item.data(_SLOTS_ROLE) & self.slot.value:
                e.accept()

    def dropEvent(self, e: QDropEvent) -> None:
        if isinstance(e.source(), QTreeView):
            e.setDropAction(QtCore.Qt.CopyAction)

            tree: QTreeView = e.source()
            proxyModel: QSortFilterProxyModel = tree.model()
            model: ItemModel = proxyModel.sourceModel()
            index = proxyModel.mapToSource(tree.selectedIndexes()[0])
            item = model.itemFromIndex(index)
            if item.data(_SLOTS_ROLE) & self.slot.value:
                e.accept()
                self.setItem(item.data(_RESNAME_ROLE), item.data(_FILEPATH_ROLE), item.text(), False, False)
                self.itemDropped.emit(self.filepath, self.resname, self.name)

    def removeItem(self):
        ItemContainer.removeItem(self)
        self.window().setEquipment(self.slot, "")

    def toggleDroppable(self):
        ItemContainer.toggleDroppable(self)


class InventoryTable(QTableWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.itemChanged.connect(self.resnameChanged)
        self.customContextMenuRequested.connect(self.openContextMenu)
        self.is_store: bool = False

    def addItem(self, resname: str, droppable: bool, infinite: bool):
        rowID = self.rowCount()
        self.insertRow(rowID)
        filepath, name, uti = self.window().getItem(resname, "")
        pixmap = self.window().getItemImage(uti)
        iconItem = QTableWidgetItem(QIcon(pixmap), "")
        iconItem.setSizeHint(QSize(48, 48))
        iconItem.setFlags(iconItem.flags() ^ QtCore.Qt.ItemIsEditable)
        nameItem = QTableWidgetItem(name)
        nameItem.setFlags(nameItem.flags() ^ QtCore.Qt.ItemIsEditable)
        resnameItem = InventoryTableResnameItem(resname, filepath, name, droppable, infinite)
        self.setItem(rowID, 0, iconItem)
        self.setItem(rowID, 1, resnameItem)
        self.setItem(rowID, 2, nameItem)

    def dropEvent(self, e: QDropEvent) -> None:
        if isinstance(e.source(), QTreeView):
            e.setDropAction(QtCore.Qt.CopyAction)

            tree: QTreeView = e.source()
            proxyModel: QSortFilterProxyModel = tree.model()
            model: ItemModel = proxyModel.sourceModel()
            index = proxyModel.mapToSource(tree.selectedIndexes()[0])
            item = model.itemFromIndex(index)
            e.accept()
            rowID = self.rowCount()
            self.insertRow(rowID)
            filepath, name, uti = self.window().getItem(item.data(_RESNAME_ROLE), item.data(_FILEPATH_ROLE))
            pixmap = self.window().getItemImage(uti)
            iconItem = QTableWidgetItem(QIcon(pixmap), "")
            iconItem.setSizeHint(QSize(48, 48))
            iconItem.setFlags(iconItem.flags() ^ QtCore.Qt.ItemIsEditable)
            nameItem = QTableWidgetItem(item.text())
            nameItem.setFlags(nameItem.flags() ^ QtCore.Qt.ItemIsEditable)
            resnameItem = InventoryTableResnameItem(
                item.data(_RESNAME_ROLE),
                item.data(_FILEPATH_ROLE),
                item.text(),
                False,
                False,
            )
            self.setItem(rowID, 0, iconItem)
            self.setItem(rowID, 1, resnameItem)
            self.setItem(rowID, 2, nameItem)

    def resnameChanged(self, tableItem: QTableWidgetItem):
        if isinstance(tableItem, InventoryTableResnameItem):
            filepath, name, uti = self.window().getItem(tableItem.text(), "")
            icon = QIcon(self.window().getItemImage(uti))

            tableItem.setItem(tableItem.text(), filepath, name, tableItem.droppable, tableItem.infinite)
            self.item(tableItem.row(), 0).setIcon(icon)
            nameItem = QTableWidgetItem(name)
            nameItem.setFlags(nameItem.flags() ^ QtCore.Qt.ItemIsEditable)
            self.setItem(tableItem.row(), 2, nameItem)

    def openContextMenu(self, point: QPoint):
        if len(self.selectedIndexes()) == 0:
            return

        itemContainer = self.item(self.selectionModel().selectedRows(1)[0].row(), 1)
        if isinstance(itemContainer, ItemContainer):
            menu = QMenu(self)
            if self.is_store:
                infiniteAction = QAction("Infinite")
                infiniteAction.setCheckable(True)
                infiniteAction.setChecked(itemContainer.infinite)
                infiniteAction.triggered.connect(itemContainer.toggleInfinite)
                menu.addAction(infiniteAction)
            else:
                droppableAction = QAction("Droppable")
                droppableAction.setCheckable(True)
                droppableAction.setChecked(itemContainer.droppable)
                droppableAction.triggered.connect(itemContainer.toggleDroppable)
                menu.addAction(droppableAction)

            removeAction = QAction("Remove Item")
            removeAction.triggered.connect(itemContainer.removeItem)

            menu.addSeparator()
            menu.addAction(removeAction)

            menu.exec_(self.mapToGlobal(point))


class InventoryTableResnameItem(ItemContainer, QTableWidgetItem):
    def __init__(self, resname: str, filepath: str, name: str, droppable: bool, infinite: bool):
        ItemContainer.__init__(self, droppable, infinite)
        QTableWidgetItem.__init__(self, resname)
        self.setItem(resname, filepath, name, droppable, infinite)

    def removeItem(self):
        self.tableWidget().removeRow(self.row())


class ItemBuilderDialog(QDialog):
    """Popup dialog responsible for extracting a list of resources from the game files."""

    def __init__(self, parent: QWidget, installation: HTInstallation, capsules: list[Capsule]):
        super().__init__(parent)

        self._progressBar = QProgressBar(self)
        self._progressBar.setMaximum(0)
        self._progressBar.setValue(0)
        self._progressBar.setTextVisible(False)

        self.resize(250, 40)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._progressBar)

        self.setWindowTitle("Building Item Lists...")

        self.coreModel = ItemModel(installation.main_window)
        self.modulesModel = ItemModel(self.parent())
        self.overrideModel = ItemModel(self.parent())
        self._tlk: TLK = read_tlk(installation.path() / "dialog.tlk")
        self._installation: HTInstallation = installation
        self._capsules: list[Capsule] = capsules

        self._worker = ItemBuilderWorker(installation, capsules)
        self._worker.utiLoaded.connect(self.utiLoaded)
        self._worker.finished.connect(self.finished)
        self._worker.start()

    def utiLoaded(self, uti: UTI, result: ResourceResult) -> None:
        baseitems = self._installation.htGetCache2DA(HTInstallation.TwoDA_BASEITEMS)
        name = self._installation.string(uti.name, result.resname) if uti is not None else result.resname

        # Split category by base item:

        slots = baseitems.get_row(uti.base_item).get_integer("equipableslots", 0) if uti is not None else 0
        category = self.getCategory(uti)

        if result.filepath.endswith(".bif") or result.filepath.endswith(".key"):
            self.coreModel.addItem(result.resname, category, result.filepath, name, slots)
        elif result.filepath.endswith(".rim") or result.filepath.endswith(".mod") or result.filepath.endswith(".erf"):
            self.modulesModel.addItem(result.resname, category, result.filepath, name, slots)
        else:
            self.overrideModel.addItem(result.resname, category, result.filepath, name, slots)

    def finished(self) -> None:
        self.accept()

    def getCategory(self, uti: Optional[UTI]) -> str:
        baseitems = self._installation.htGetCache2DA(HTInstallation.TwoDA_BASEITEMS)
        slots = baseitems.get_row(uti.base_item).get_integer("equipableslots", 0) if uti is not None else -1
        droid = baseitems.get_row(uti.base_item).get_integer("droidorhuman", 0) == 2 if uti is not None else False

        if slots & (EquipmentSlot.CLAW1.value | EquipmentSlot.CLAW2.value | EquipmentSlot.CLAW3.value):
            return "Creature Claw"
        if slots & EquipmentSlot.HEAD.value:
            return "Droid Sensors" if droid else "Headgear"
        if slots & EquipmentSlot.IMPLANT.value and not droid:
            return "Implants"
        if slots & EquipmentSlot.GAUNTLET.value and not droid:
            return "Gauntlets"
        if slots & EquipmentSlot.IMPLANT.value and droid:
            return "Droid Utilities"
        if slots & EquipmentSlot.LEFT_ARM.value:
            return "Droid Special Weapons" if droid else "Shields"
        if slots & EquipmentSlot.ARMOR.value:
            return "Droid Plating" if droid else "Armor"
        if slots & EquipmentSlot.LEFT_HAND.value:
            return "Weapons (Single)"
        if slots & EquipmentSlot.RIGHT_HAND.value:
            return "Weapons (Double)"
        if slots & EquipmentSlot.BELT.value:
            return "Droid Shields" if droid else "Belts"
        if slots & EquipmentSlot.HIDE.value:
            return "Creature Hide"
        if slots == 0:
            return "Miscellaneous"
        return "Unknown"


class ItemBuilderWorker(QThread):
    utiLoaded = QtCore.pyqtSignal(object, object)
    finished = QtCore.pyqtSignal()

    def __init__(self, installation: HTInstallation, capsules: list[Capsule]):
        super().__init__()
        self._installation = installation
        self._capsules = capsules

    def run(self) -> None:
        queries = []
        if self._installation.cacheCoreItems is None:
            queries.extend(
                [
                    ResourceIdentifier(resource.resname(), resource.restype())
                    for resource in self._installation.chitin_resources()
                    if resource.restype() == ResourceType.UTI
                ],
            )
        for resource in self._installation.override_resources(""):
            if resource.restype() == ResourceType.UTI:
                queries.append(ResourceIdentifier(resource.resname(), resource.restype()))
        for resource in list(self._capsules):
            if resource.restype() == ResourceType.UTI:
                queries.append(ResourceIdentifier(resource.resname(), resource.restype()))

        results = self._installation.resources(
            queries,
            [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.CUSTOM_MODULES],
            capsules=self._capsules,
        )
        for result in results.values():
            uti = None
            with suppress(Exception):
                uti = read_uti(result.data)
            self.utiLoaded.emit(uti, result)
        self.finished.emit()


class ItemModel(QStandardItemModel):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self._categoryItems = {}
        self._proxyModel = QSortFilterProxyModel(self)
        self._proxyModel.setSourceModel(self)
        self._proxyModel.setRecursiveFilteringEnabled(True)
        self._proxyModel.setFilterCaseSensitivity(False)
        self._proxyModel.setRecursiveFilteringEnabled(True)
        self._proxyModel.setSourceModel(self)

    def proxyModel(self) -> QSortFilterProxyModel:
        return self._proxyModel

    def _getCategoryItem(self, category: str) -> QStandardItem:
        if category not in self._categoryItems:
            categoryItem = QStandardItem(category)
            categoryItem.setSelectable(False)
            self._categoryItems[category] = categoryItem
            self.appendRow(categoryItem)
        return self._categoryItems[category]

    def addItem(self, resname: str, category: str, filepath: str, name: str, slots: int) -> None:
        item = QStandardItem(name if name != "" else resname)
        item.setToolTip(f"{resname}\n{filepath}\n{name}")
        item.setData(filepath, _FILEPATH_ROLE)
        item.setData(resname, _RESNAME_ROLE)
        item.setData(slots, _SLOTS_ROLE)
        self._getCategoryItem(category).appendRow(item)


class SetItemResRefDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        from editors import ui_setitemresref

        self.ui = ui_setitemresref.Ui_Dialog()
        self.ui.setupUi(self)

    def resref(self) -> str:
        return self.ui.resrefEdit.text()
