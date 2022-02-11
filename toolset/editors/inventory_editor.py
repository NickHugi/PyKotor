from __future__ import annotations

import time
from contextlib import suppress
from typing import Dict, List, NamedTuple, Optional, Union, Tuple

from PyQt5 import QtCore
from PyQt5.QtCore import QThread, QSortFilterProxyModel, QPoint, QSize
from PyQt5.QtGui import QImage, QPixmap, QStandardItemModel, QStandardItem, QDropEvent, QDragEnterEvent, QDragMoveEvent, \
    QIcon, QTransform
from PyQt5.QtWidgets import QDialog, QWidget, QLabel, QProgressBar, QVBoxLayout, QFrame, QTreeView, QMenu, QAction, \
    QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem
from pykotor.common.misc import InventoryItem, EquipmentSlot, ResRef
from pykotor.common.stream import BinaryReader
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import FileQuery
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import load_gff
from pykotor.resource.formats.tlk import TLK, load_tlk
from pykotor.resource.formats.tpc import TPCTextureFormat, TPC
from pykotor.resource.formats.twoda import TwoDA
from pykotor.resource.generics.uti import construct_uti, UTI
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from editors import inventory_editor_ui

import resources_rc


_RESNAME_ROLE = QtCore.Qt.UserRole + 1
_FILEPATH_ROLE = QtCore.Qt.UserRole + 2
_SLOTS_ROLE = QtCore.Qt.UserRole + 3


class SlotMapping(NamedTuple):
    label: QLabel
    frame: DropFrame
    emptyImage: str


class InventoryEditor(QDialog):
    def __init__(self, parent: QWidget, installation: HTInstallation, capsules: List[Capsule], folders: List[str],
                 inventory: List[InventoryItem], equipment: Dict[EquipmentSlot, InventoryItem], droid: bool = False):
        super().__init__(parent)

        self.ui = inventory_editor_ui.Ui_Dialog()
        self.ui.setupUi(self)

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
        self._capsules: List[Capsule] = capsules
        self._slotMap: Dict[EquipmentSlot, SlotMapping] = {
            EquipmentSlot.IMPLANT: SlotMapping(self.ui.implantPicture, self.ui.implantFrame, ":/images/inventory/{}_implant.png"),
            EquipmentSlot.HEAD: SlotMapping(self.ui.headPicture, self.ui.headFrame, ":/images/inventory/{}_head.png"),
            EquipmentSlot.GAUNTLET: SlotMapping(self.ui.gauntletPicture, self.ui.gauntletFrame, ":/images/inventory/{}_gauntlet.png"),
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
        self.inventory: List[InventoryItem] = inventory
        self.equipment: Dict[EquipmentSlot, InventoryItem] = equipment

        self.ui.implantFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.IMPLANT, resname, filepath, name))
        self.ui.headFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.HEAD, resname, filepath, name))
        self.ui.gauntletFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.GAUNTLET, resname, filepath, name))
        self.ui.armlFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.LEFT_ARM, resname, filepath, name))
        self.ui.armorFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.ARMOR, resname, filepath, name))
        self.ui.armrFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.RIGHT_ARM, resname, filepath, name))
        self.ui.handlFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.LEFT_HAND, resname, filepath, name))
        self.ui.beltFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.BELT, resname, filepath, name))
        self.ui.handrFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.RIGHT_HAND, resname, filepath, name))
        self.ui.hideFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.HIDE, resname, filepath, name))
        self.ui.claw1Frame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.CLAW1, resname, filepath, name))
        self.ui.claw2Frame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.CLAW2, resname, filepath, name))
        self.ui.claw3Frame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.CLAW3, resname, filepath, name))

        self.ui.implantFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.implantPicture, point))
        self.ui.headFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.headFrame, point))
        self.ui.gauntletFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.gauntletFrame, point))
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

        for slot in EquipmentSlot:
            image = self._slotMap[slot].emptyImage.format("droid" if droid else "human")
            self._slotMap[slot].label.setPixmap(QPixmap(image))

        for slot, item in self.equipment.items():
            self.setEquipment(slot, item.resref.get())

        for item in self.inventory:
            self.ui.contentsTable.addItem(item.resref.get(), item.droppable)

        self.buildItems()

    def accept(self) -> None:
        super().accept()
        self.inventory = []
        for i in range(self.ui.contentsTable.rowCount()):
            tableItem: ItemContainer = self.ui.contentsTable.item(i, 1)
            self.inventory.append(InventoryItem(ResRef(tableItem.resname), tableItem.droppable))

        self.equipment = {}
        for widget in self.ui.standardEquipmentTab.children() + self.ui.naturalEquipmentTab.children():
            # Very hacky, but isinstance is not working (possibly due to how DropFrame is imported in _ui.py file.
            if 'DropFrame' in str(type(widget)):
                self.equipment[widget.slot] = InventoryItem(ResRef(widget.resname), widget.droppable)

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
        pixmap = QPixmap(":/images/inventory/unknown.png")
        baseitems = self._installation.htGetCache2DA(HTInstallation.TwoDA_BASEITEMS)

        with suppress(Exception):
            itemClass = baseitems.get_cell(uti.base_item, "itemclass")
            variation = uti.model_variation if uti.model_variation != 0 else uti.texture_variation
            textureResname = "i{}_{}".format(itemClass, str(variation).rjust(3, "0"))
            texture = self._installation.htGetCacheTPC(textureResname)

            if texture is not None:
                width, height, rgba = texture.convert(TPCTextureFormat.RGBA, 0)
                image = QImage(rgba, width, height, QImage.Format_RGBA8888)
                pixmap = QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))
                return pixmap

        return pixmap

    def getItem(self, resname: str, filepath: str) -> Tuple[str, str, UTI]:
        uti = None
        name = ""
        if filepath == "":
            result = self._installation.resource(resname, ResourceType.UTI)
            if result.data is not None:
                uti = construct_uti(load_gff(result.data))
                filepath = result.filepath
                name = uti.name.determine(self._installation.talktable(), "[No Name]")
        elif filepath.endswith(".rim") or filepath.endswith(".mod") or filepath.endswith(".erf"):
            uti = construct_uti(load_gff(Capsule(filepath).resource(resname, ResourceType.UTI)))
            name = uti.name.determine(self._installation.talktable(), "[No Name]")
        elif filepath.endswith(".bif"):
            uti = construct_uti(load_gff(self._installation.resource(resname, ResourceType.UTI, skip_modules=True, skip_override=True).data))
            name = uti.name.determine(self._installation.talktable(), "[No Name]")
        else:
            uti = construct_uti(load_gff(BinaryReader.load_file(filepath)))
        return filepath, name, uti

    def setEquipment(self, slot: EquipmentSlot, resname: str, filepath: str = "", name: str = "") -> None:
        slotPicture = self._slotMap[slot].label
        slotFrame = self._slotMap[slot].frame

        if resname != "":
            filepath, name, uti = self.getItem(resname, filepath)

            slotPicture.setToolTip("{}\n{}\n{}".format(resname, filepath, name))
            slotPicture.setPixmap(self.getItemImage(uti))
            slotFrame.setItem(resname, filepath, name)
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
            droppableAction = QAction("Droppable")
            droppableAction.setCheckable(True)
            droppableAction.setChecked(widget.droppable)
            droppableAction.triggered.connect(widget.toggleDroppable)
            removeAction = QAction("Remove Item")
            removeAction.triggered.connect(widget.removeItem)

            menu.addAction(droppableAction)
            menu.addSeparator()
            menu.addAction(removeAction)
        else:
            noItemAction = QAction("No item")
            noItemAction.setEnabled(False)
            menu.addAction(noItemAction)

        menu.exec_(widget.mapToGlobal(point))


class ItemContainer:
    def __init__(self):
        self.resname: str = ""
        self.filepath: str = ""
        self.name: str = ""
        self.hasItem: bool = False
        self.droppable: bool = False

    def removeItem(self):
        self.resname: str = ""
        self.filepath: str = ""
        self.name: str = ""
        self.hasItem: bool = False
        self.droppable: bool = False

    def setItem(self, resname: str, filepath: str, name: str):
        self.resname: str = resname
        self.filepath: str = filepath
        self.name: str = name
        self.hasItem: bool = True
        self.droppable: bool = False

    def toggleDroppable(self):
        self.droppable = not self.droppable


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
                self.setItem(item.data(_RESNAME_ROLE), item.data(_FILEPATH_ROLE), item.text())
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

    def addItem(self, resname: str, droppable: bool):
        rowID = self.rowCount()
        self.insertRow(rowID)
        filepath, name, uti = self.window().getItem(resname, "")
        pixmap = self.window().getItemImage(uti)
        iconItem = QTableWidgetItem(QIcon(pixmap), "")
        iconItem.setSizeHint(QSize(48, 48))
        iconItem.setFlags(iconItem.flags() ^ QtCore.Qt.ItemIsEditable)
        nameItem = QTableWidgetItem(name)
        nameItem.setFlags(nameItem.flags() ^ QtCore.Qt.ItemIsEditable)
        resnameItem = InventoryTableResnameItem(resname, filepath, name)
        resnameItem.droppable = droppable
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
            resnameItem = InventoryTableResnameItem(item.data(_RESNAME_ROLE), item.data(_FILEPATH_ROLE), item.text())
            self.setItem(rowID, 0, iconItem)
            self.setItem(rowID, 1, resnameItem)
            self.setItem(rowID, 2, nameItem)

    def resnameChanged(self, tableItem: QTableWidgetItem):
        if isinstance(tableItem, InventoryTableResnameItem):
            filepath, name, uti = self.window().getItem(tableItem.text(), "")
            icon = QIcon(self.window().getItemImage(uti))

            tableItem.setItem(tableItem.text(), filepath, name)
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

            droppableAction = QAction("Droppable")
            droppableAction.setCheckable(True)
            droppableAction.setChecked(itemContainer.droppable)
            droppableAction.triggered.connect(itemContainer.toggleDroppable)
            removeAction = QAction("Remove Item")
            removeAction.triggered.connect(itemContainer.removeItem)

            menu.addAction(droppableAction)
            menu.addSeparator()
            menu.addAction(removeAction)

            menu.exec_(self.mapToGlobal(point))


class InventoryTableResnameItem(ItemContainer, QTableWidgetItem):
    def __init__(self, resname: str, filepath: str, name: str):
        ItemContainer.__init__(self)
        QTableWidgetItem.__init__(self, resname)
        self.setItem(resname, filepath, name)

    def removeItem(self):
        self.tableWidget().removeRow(self.row())


class ItemBuilderDialog(QDialog):
    """
    Popup dialog responsible for extracting a list of resources from the game files.
    """

    def __init__(self, parent: QWidget, installation: HTInstallation, capsules: List[Capsule]):
        super().__init__(parent)

        self._progressBar = QProgressBar(self)
        self._progressBar.setMaximum(0)
        self._progressBar.setValue(0)
        self._progressBar.setTextVisible(False)

        self.resize(250, 40)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._progressBar)

        self.setWindowTitle("Building Item Lists...")

        self.coreModel = ItemModel(installation.mainWindow)
        self.modulesModel = ItemModel(self.parent())
        self.overrideModel = ItemModel(self.parent())
        self._tlk: TLK = load_tlk(installation.path() + "dialog.tlk")
        self._installation: HTInstallation = installation
        self._capsules: List[Capsule] = capsules

        self._worker = ItemBuilderWorker(installation, capsules)
        self._worker.utiLoaded.connect(self.utiLoaded)
        self._worker.finished.connect(self.finished)
        self._worker.start()

    def utiLoaded(self, uti: UTI, result: SearchResult) -> None:
        baseitems = self._installation.htGetCache2DA(HTInstallation.TwoDA_BASEITEMS)
        name = uti.name.determine(self._tlk, "") if uti is not None else result.resname

        # Split category by base item:
        #  categoryNameID = baseitems.get_row(uti.base_item).get_integer("name")
        #  categoryLabel = baseitems.get_cell(uti.base_item, "label")
        #  category = self._tlk.get(categoryNameID).text if self._tlk.get(categoryNameID) is not None else categoryLabel

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
        elif slots & EquipmentSlot.HEAD.value:
            return "Droid Sensors" if droid else "Headgear"
        elif slots & EquipmentSlot.IMPLANT.value and not droid:
            return "Implants"
        elif slots & EquipmentSlot.GAUNTLET.value and not droid:
            return "Gauntlets"
        elif slots & EquipmentSlot.IMPLANT.value and droid:
            return "Droid Utilities"
        elif slots & EquipmentSlot.LEFT_ARM.value:
            return "Droid Special Weapons" if droid else "Shields"
        elif slots & EquipmentSlot.ARMOR.value:
            return "Droid Plating" if droid else "Armor"
        elif slots & EquipmentSlot.LEFT_HAND.value:
            return "Weapons (Single)"
        elif slots & EquipmentSlot.RIGHT_HAND.value:
            return "Weapons (Double)"
        elif slots & EquipmentSlot.BELT.value:
            return "Droid Shields" if droid else "Belts"
        elif slots & EquipmentSlot.HIDE.value:
            return "Creature Hide"
        elif slots == 0:
            return "Miscellaneous"
        else:
            return "Unknown"


class ItemBuilderWorker(QThread):
    utiLoaded = QtCore.pyqtSignal(object, object)
    finished = QtCore.pyqtSignal()

    def __init__(self, installation: HTInstallation, capsules: List[Capsule]):
        super().__init__()
        self._installation = installation
        self._capsules = capsules

    def run(self) -> None:
        queries = []
        if self._installation.cacheCoreItems is None:
            queries.extend([FileQuery(resource.resname(), resource.restype())
                            for resource in self._installation.chitin_resources()
                            if resource.restype() == ResourceType.UTI])
        for resource in self._installation.override_resources(""):
            if resource.restype() == ResourceType.UTI:
                queries.append(FileQuery(resource.resname(), resource.restype()))
        for capsule in self._capsules:
            for resource in capsule:
                if resource.restype() == ResourceType.UTI:
                    queries.append(FileQuery(resource.resname(), resource.restype()))

        results = self._installation.resource_batch(queries, capsules=self._capsules, skip_modules=True)
        for result in results:
            uti = None
            with suppress(Exception):
                uti = construct_uti(load_gff(result.data))
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
        item.setToolTip("{}\n{}\n{}".format(resname, filepath, name))
        item.setData(filepath, _FILEPATH_ROLE)
        item.setData(resname, _RESNAME_ROLE)
        item.setData(slots, _SLOTS_ROLE)
        self._getCategoryItem(category).appendRow(item)

