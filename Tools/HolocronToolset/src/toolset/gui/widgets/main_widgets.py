#!/usr/bin/env python3
from __future__ import annotations

import multiprocessing

from abc import abstractmethod
from time import sleep
from typing import TYPE_CHECKING, Any, ClassVar, Tuple, cast

import qtpy

from loggerplus import RobustLogger
from qtpy import QtCore
from qtpy.QtCore import QPoint, QSortFilterProxyModel, QThread, QTimer, Qt
from qtpy.QtGui import (
    QCursor,
    QIcon,
    QImage,
    QMouseEvent,
    QPixmap,
    QStandardItem,
    QStandardItemModel,
    QTransform,
)
from qtpy.QtWidgets import QHeaderView, QMenu, QToolTip, QWidget

from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.gff import GFFContent
from pykotor.resource.formats.tpc import TPC, TPCTextureFormat
from pykotor.resource.type import ResourceType
from toolset.gui.dialogs.load_from_location_result import ResourceItems

if TYPE_CHECKING:
    from multiprocessing.managers import SyncManager
    from qtpy.QtCore import QEvent, QModelIndex, QObject
    from qtpy.QtGui import (
        QEnterEvent,
        QLeaveEvent,
        QResizeEvent,
    )

    from pykotor.extract.file import FileResource
    from toolset.data.installation import HTInstallation


class MainWindowList(QWidget):
    requestOpenResource: ClassVar[QtCore.Signal] = QtCore.Signal(object, object)  # pyright: ignore[reportPrivateImportUsage]
    requestExtractResource: ClassVar[QtCore.Signal] = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    requestMakeUnskippable: ClassVar[QtCore.Signal] = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    requestConvertGFF: ClassVar[QtCore.Signal] = QtCore.Signal(object, object)  # pyright: ignore[reportPrivateImportUsage]  # resources, target_game
    requestConvertTPC: ClassVar[QtCore.Signal] = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    requestConvertTGA: ClassVar[QtCore.Signal] = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    sectionChanged: ClassVar[QtCore.Signal] = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]

    @abstractmethod
    def selectedResources(self) -> list[FileResource]: ...


class ResourceStandardItem(QStandardItem):
    def __init__(self, *args: Any, resource: FileResource, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.resource: FileResource = resource


class ResourceList(MainWindowList):
    requestReload: ClassVar[QtCore.Signal] = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    requestRefresh: ClassVar[QtCore.Signal] = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]

    HORIZONTAL_HEADER_LABELS: ClassVar[list[str]] = ["ResRef", "Type"]

    def __init__(self, parent: QWidget):
        """Initializes the ResourceList widget.

        Args:
        ----
            parent (QWidget): The parent widget

        Processing Logic:
        ----------------
            - Initializes the UI from the designer file
            - Sets up the signal connections
            - Creates a ResourceModel and sets it as the model for the tree view
            - Creates a QStandardItemModel for the section combo box
            - Sets the section model as the model for the combo box.
        """
        super().__init__(parent)
        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.widgets.resource_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.resource_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.resource_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.resource_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.tooltipText: str = ""
        self.flattened: bool = False
        self.autoResizeEnabled: bool = True
        self.expandedState: bool = False
        self.original_items: list[tuple[QStandardItem, list[list[QStandardItem]]]] = []

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setupSignals()

        self.modulesModel: ResourceModel = ResourceModel()
        self.modulesModel.proxyModel().setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.resourceTree.setModel(self.modulesModel.proxyModel())  # pyright: ignore[reportArgumentType]
        self.ui.resourceTree.sortByColumn(0, Qt.SortOrder.AscendingOrder)  # pyright: ignore[reportArgumentType]
        self.sectionModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.sectionModel)  # pyright: ignore[reportArgumentType]

        # Connect the header context menu request signal
        header: QHeaderView | None = self.ui.resourceTree.header()  # pyright: ignore[reportAssignmentType]
        assert header is not None
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # pyright: ignore[reportArgumentType]
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)  # pyright: ignore[reportArgumentType]

        header.customContextMenuRequested.connect(self.onHeaderContextMenu)

        # Connect expand/collapse signals to autoFitColumns if enabled
        self.ui.resourceTree.expanded.connect(self.onTreeItemExpanded)
        self.ui.resourceTree.collapsed.connect(self.onTreeItemCollapsed)

        # Install event filter on the viewport
        viewport: QWidget | None = self.ui.resourceTree.viewport()  # pyright: ignore[reportAssignmentType]
        assert viewport is not None
        viewport.installEventFilter(self)  # pyright: ignore[reportArgumentType]
        self.setMouseTracking(True)
        self.ui.resourceTree.setMouseTracking(True)

        self.tooltipTimer = QTimer(self)
        self.tooltipTimer.setSingleShot(True)
        self.tooltipTimer.timeout.connect(self.showTooltip)

    def onHeaderContextMenu(self, point: QPoint):
        """Show context menu for the header."""
        menu = QMenu(self)

        # Flatten/Unflatten
        flatten_action = menu.addAction("Flatten")
        assert flatten_action is not None
        flatten_action.setCheckable(True)
        flatten_action.setChecked(self.flattened)
        flatten_action.triggered.connect(self.toggleFlatten)

        # Collapse/Expand All
        expand_collapse_action = menu.addAction("Expand All")
        assert expand_collapse_action is not None
        expand_collapse_action.setCheckable(True)
        expand_collapse_action.setChecked(self.expandedState)
        expand_collapse_action.triggered.connect(self.toggleExpandCollapse)

        # Auto-fit Columns
        auto_fit_columns_action = menu.addAction("Auto-fit Columns")
        assert auto_fit_columns_action is not None
        auto_fit_columns_action.setCheckable(True)
        auto_fit_columns_action.setChecked(self.autoResizeEnabled)
        auto_fit_columns_action.triggered.connect(self.toggleAutoFitColumns)

        # Alternate Row Colors
        alternate_row_colors_action = menu.addAction("Alternate Row Colors")
        assert alternate_row_colors_action is not None
        alternate_row_colors_action.setCheckable(True)
        alternate_row_colors_action.setChecked(self.ui.resourceTree.alternatingRowColors())
        alternate_row_colors_action.triggered.connect(self.ui.resourceTree.setAlternatingRowColors)

        header: QHeaderView | None = self.ui.resourceTree.header()  # pyright: ignore[reportAssignmentType]
        assert header is not None
        menu.exec_(header.mapToGlobal(point))

    def toggleFlatten(self):
        """Toggle the flatten state of the tree view."""
        if self.flattened:
            self.unflattenTree()
        else:
            self.flattenTree()
        self.flattened = not self.flattened
        if self.autoResizeEnabled:
            self.autoFitColumns()

    def flattenTree(self):
        """Flatten the tree structure into a single level."""
        flat_items: list[tuple[FileResource, tuple[ResourceStandardItem, QStandardItem]]] = []

        for i in range(self.modulesModel.rowCount()):
            category_item: QStandardItem | None = self.modulesModel.item(i)
            assert category_item is not None
            for j in range(category_item.rowCount()):
                resourceItem: ResourceStandardItem = cast("ResourceStandardItem", category_item.child(j, 0))
                resourceItem.__class__ = ResourceStandardItem

                flat_items.append(
                    cast(
                        "Tuple[FileResource, Tuple[ResourceStandardItem, QStandardItem]]",
                        (
                            resourceItem.resource,
                            tuple(category_item.child(j, col).clone() for col in range(category_item.columnCount())),  # pyright: ignore[reportOptionalMemberAccess]
                        ),
                    )
                )

        self._clearModulesModel()
        for resource, cloned_resource_row in flat_items:
            cloned_resource_row[0].resource = resource
            self.modulesModel.appendRow(cloned_resource_row)

    def unflattenTree(self):
        """Restore the original tree structure."""
        resources = []
        for i in range(self.modulesModel.rowCount()):
            item: ResourceStandardItem | QStandardItem | None = self.modulesModel.item(i, 0)
            if not isinstance(item, ResourceStandardItem):
                continue
            resources.append(item.resource)
        self._clearModulesModel()
        self.setResources(resources, clearExisting=False)

    def _clearModulesModel(self):
        self.modulesModel.clear()
        self.modulesModel.setColumnCount(2)
        self.modulesModel.setHorizontalHeaderLabels(["ResRef", "Type"])

    def collapseAll(self):
        autoResizeEnabled = self.autoResizeEnabled
        if autoResizeEnabled:  # Temporarily disable autoresize column logic while the collapse happens.
            self.autoResizeEnabled = False
        self.ui.resourceTree.collapseAll()
        self.autoResizeEnabled = autoResizeEnabled

    def expandAll(self):
        autoResizeEnabled = self.autoResizeEnabled
        if autoResizeEnabled:  # Temporarily disable autoresize column logic while the expand happens.
            self.autoResizeEnabled = False
        self.ui.resourceTree.expandAll()
        self.autoResizeEnabled = autoResizeEnabled

    def toggleExpandCollapse(self):
        """Toggle between expanding and collapsing all items in the tree."""
        if self.expandedState:
            self.collapseAll()
        else:
            self.expandAll()
        self.expandedState = not self.expandedState

    def resetColumnWidths(self):
        header = self.ui.resourceTree.header()
        assert header is not None
        for col in range(header.count()):
            header.resizeSection(col, header.defaultSectionSize())

    def autoFitColumns(self):
        header = self.ui.resourceTree.header()
        assert header is not None
        for col in range(header.count()):
            self.ui.resourceTree.resizeColumnToContents(col)

    def toggleAutoFitColumns(self):
        self.autoResizeEnabled = not self.autoResizeEnabled
        if self.autoResizeEnabled:
            self.autoFitColumns()
        else:
            self.resetColumnWidths()

    def onTreeItemExpanded(self, index):
        if self.autoResizeEnabled:
            self.autoFitColumns()

    def onTreeItemCollapsed(self, index):
        if self.autoResizeEnabled:
            self.autoFitColumns()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        if event.type() == QtCore.QEvent.Type.MouseMove and obj is self.ui.resourceTree.viewport():
            assert isinstance(event, QMouseEvent)
            self.mouseMoveEvent(event)
            return True
        return super().eventFilter(obj, event)

    def showTooltip(self):
        QToolTip.showText(QCursor.pos(), self.tooltipText, self.ui.resourceTree)  # pyright: ignore[reportArgumentType]

    def setupSignals(self):
        self.ui.searchEdit.textEdited.connect(self.onFilterStringUpdated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.onSectionChanged)
        self.ui.reloadButton.clicked.connect(self.onReloadClicked)
        self.ui.refreshButton.clicked.connect(self.onRefreshClicked)
        self.ui.resourceTree.customContextMenuRequested.connect(self.onResourceContextMenu)
        self.ui.resourceTree.doubleClicked.connect(self.onResourceDoubleClicked)

    def enterEvent(self, event: QEnterEvent):  # type: ignore[override, note]
        self.tooltipTimer.stop()
        QToolTip.hideText()
        super().enterEvent(event)

    def leaveEvent(self, event: QLeaveEvent):  # type: ignore[override, note]
        self.tooltipTimer.stop()
        QToolTip.hideText()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):  # type: ignore[override, note]
        index = self.ui.resourceTree.indexAt(event.pos())  # type: ignore[arg-type]
        if index.isValid():
            model_index: QModelIndex = cast("QSortFilterProxyModel", self.ui.resourceTree.model()).mapToSource(index)  # pyright: ignore[reportArgumentType]
            item: ResourceStandardItem | QStandardItem | None = cast(
                "QStandardItemModel",
                cast("QSortFilterProxyModel", self.ui.resourceTree.model()).sourceModel(),
            ).itemFromIndex(model_index)
            if isinstance(item, ResourceStandardItem):
                self.tooltipText = str(item.resource.filepath())
                self.tooltipPos = event.globalPos()
                self.tooltipTimer.start(1100)  # Set the delay to 3000ms (3 seconds)
            else:
                self.tooltipTimer.stop()
                QToolTip.hideText()
        else:
            self.tooltipTimer.stop()
            QToolTip.hideText()
        super().mouseMoveEvent(event)

    def hideReloadButton(self):
        self.ui.reloadButton.setVisible(False)

    def hideSection(self):
        self.ui.line.setVisible(False)
        self.ui.sectionCombo.setVisible(False)
        self.ui.refreshButton.setVisible(False)

    def currentSection(self) -> str:
        return self.ui.sectionCombo.currentData()

    def changeSection(
        self,
        section: str,
    ):
        for i in range(self.ui.sectionCombo.count()):
            if section in self.ui.sectionCombo.itemText(i):
                RobustLogger().debug("changing to section '%s'", section)
                self.ui.sectionCombo.setCurrentIndex(i)

    def setResources(
        self,
        resources: list[FileResource],
        customCategory: str | None = None,
        *,
        clearExisting: bool = True,
    ):
        """Adds and removes FileResources from the modules model.

        Args:
        ----
            resources: {list[FileResource]}: List of FileResource objects to set
        """
        allResources: list[QStandardItem] = self.modulesModel.allResourcesItems()
        resourceSet: set[FileResource] = set(resources)
        resourceItemMap: dict[FileResource, ResourceStandardItem] = {
            item.resource: item
            for item in allResources
            if isinstance(item, ResourceStandardItem)
        }
        for resource in resourceSet:
            if resource in resourceItemMap:
                resourceItemMap[resource].resource = resource
            else:
                self.modulesModel.addResource(resource, customCategory)
        if clearExisting:
            for item in allResources:
                if not isinstance(item, ResourceStandardItem):
                    continue
                if item.resource in resourceSet:
                    continue
                item.parent().removeRow(item.row())  # pyright: ignore[reportOptionalMemberAccess]  # type: ignore[union-attr]
        self.modulesModel.removeUnusedCategories()
        if self.autoResizeEnabled:
            self.autoFitColumns()

    def setSections(
        self,
        sections: list[QStandardItem],
    ):
        self.sectionModel.clear()
        for section in sections:
            self.sectionModel.insertRow(self.sectionModel.rowCount(), section)
        if self.autoResizeEnabled:
            self.autoFitColumns()

    def setResourceSelection(
        self,
        resource: FileResource,
    ):
        model: ResourceModel = cast("ResourceModel", cast("QSortFilterProxyModel", self.ui.resourceTree.model()).sourceModel())
        assert isinstance(model, ResourceModel)

        def select(parent, child):
            self.ui.resourceTree.expand(parent)
            self.ui.resourceTree.scrollTo(child)
            self.ui.resourceTree.setCurrentIndex(child)

        for item in model.allResourcesItems():
            if not isinstance(item, ResourceStandardItem):
                continue
            resource_from_item: FileResource = item.resource
            if resource_from_item == resource:
                itemIndex: QModelIndex = model.proxyModel().mapFromSource(item.index())
                QTimer.singleShot(1, lambda index=itemIndex, item=item: select(item.parent().index(), index))

    def selectedResources(self) -> list[FileResource]:
        return self.modulesModel.resourceFromIndexes(self.ui.resourceTree.selectedIndexes())  # type: ignore[arg-type]

    def allResources(self) -> list[FileResource]:
        """Returns all FileResource objects in the model."""
        all_items = self.modulesModel.allResourcesItems()
        return [item.resource for item in all_items if isinstance(item, ResourceStandardItem)]

    def _getSectionUserRoleData(self):
        return self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)


    def onFilterStringUpdated(self):
        self.modulesModel.proxyModel().setFilterString(self.ui.searchEdit.text())

    def onSectionChanged(self):
        self.sectionChanged.emit(self._getSectionUserRoleData())

    def onReloadClicked(self):
        self.requestReload.emit(self._getSectionUserRoleData())

    def onRefreshClicked(self):
        self._clearModulesModel()
        self.requestRefresh.emit()

    def onResourceContextMenu(self, point: QPoint):
        resources: list[FileResource] = self.selectedResources()
        all_resources: list[FileResource] = self.allResources()

        if not resources:
            return
        menu = QMenu(self)

        # Add "Select All" option if there are multiple files
        if len(all_resources) > len(resources):
            menu.addAction(f"Select All ({len(all_resources)} files)").triggered.connect(  # type: ignore[union-attr]
                lambda: self._selectAllResources(all_resources, point)
            )
            menu.addSeparator()

        menu.addAction("Open").triggered.connect(lambda: self.requestOpenResource.emit(resources, True))  # type: ignore[union-attr]
        if all(resource.restype().contents == "gff" for resource in resources):
            menu.addAction("Open with GFF Editor").triggered.connect(lambda: self.requestOpenResource.emit(resources, False))  # type: ignore[union-attr]
        menu.addSeparator()

        # Add comparison submenu
        if len(resources) >= 1:
            compare_menu = menu.addMenu("Compare")

            if len(resources) == 1:
                compare_menu.addAction("Compare with...").triggered.connect(  # type: ignore[union-attr]
                    lambda: self._show_resource_comparison(resources[0])
                )
            elif len(resources) == 2:
                compare_menu.addAction("Compare Selected (Side-by-Side)").triggered.connect(  # type: ignore[union-attr]
                    lambda: self._show_resource_comparison(resources[0], resources[1])
                )

            compare_menu.addSeparator()
            compare_menu.addAction("Diff with Installation...").triggered.connect(  # type: ignore[union-attr]
                lambda: self._show_kotordiff_for_resources(resources)
            )
            compare_menu.addAction("Create TSLPatchData...").triggered.connect(  # type: ignore[union-attr]
                lambda: self._show_tslpatchdata_editor_for_resources(resources)
            )

        # Convert GFF between K1 and TSL
        gff_types = set(GFFContent.get_extensions())
        if all(resource.restype().extension in gff_types for resource in resources):
            convert_menu = menu.addMenu("Convert GFF")
            convert_menu.addAction("To K1 Format").triggered.connect(lambda: self.requestConvertGFF.emit(resources, "K1"))  # type: ignore[union-attr]
            convert_menu.addAction("To TSL Format").triggered.connect(lambda: self.requestConvertGFF.emit(resources, "TSL"))  # type: ignore[union-attr]

        # Convert TPC/TGA
        if all(resource.restype() is ResourceType.TPC for resource in resources):
            menu.addAction("Convert to TGA").triggered.connect(lambda: self.requestConvertTGA.emit(resources))  # type: ignore[union-attr]
        elif all(resource.restype() is ResourceType.TGA for resource in resources):
            menu.addAction("Convert to TPC").triggered.connect(lambda: self.requestConvertTPC.emit(resources))  # type: ignore[union-attr]

        menu.addSeparator()
        builder = ResourceItems(resources=resources)
        builder.viewport = lambda: self.ui.resourceTree
        builder.runContextMenu(point, menu=menu)

    def _selectAllResources(self, all_resources: list[FileResource], point: QPoint):
        """Select all resources and re-show context menu with batch operations."""
        if not all_resources:
            return

        # Select all items in the tree
        self.ui.resourceTree.selectAll()

        # Create a new context menu for all resources
        menu = QMenu(self)
        menu.addAction("Open").triggered.connect(lambda: self.requestOpenResource.emit(all_resources, True))  # type: ignore[union-attr]
        if all(resource.restype().contents == "gff" for resource in all_resources):
            menu.addAction("Open with GFF Editor").triggered.connect(lambda: self.requestOpenResource.emit(all_resources, False))  # type: ignore[union-attr]
        menu.addSeparator()

        # Add comparison submenu
        if len(all_resources) >= 1:
            compare_menu = menu.addMenu("Compare")
            compare_menu.addAction("Diff with Installation...").triggered.connect(  # type: ignore[union-attr]
                lambda: self._show_kotordiff_for_resources(all_resources)
            )
            compare_menu.addAction("Create TSLPatchData...").triggered.connect(  # type: ignore[union-attr]
                lambda: self._show_tslpatchdata_editor_for_resources(all_resources)
            )

        # Add batch patcher operations
        from pykotor.resource.formats.gff import GFFContent
        from pykotor.resource.type import ResourceType

        # Make dialogs unskippable
        if all(resource.restype() is ResourceType.DLG for resource in all_resources):
            menu.addAction("Make Unskippable").triggered.connect(lambda: self.requestMakeUnskippable.emit(all_resources))  # type: ignore[union-attr]

        # Convert GFF between K1 and TSL
        gff_types = set(GFFContent.get_extensions())
        if all(resource.restype().extension in gff_types for resource in all_resources):
            convert_menu = menu.addMenu("Convert GFF")
            convert_menu.addAction("To K1 Format").triggered.connect(lambda: self.requestConvertGFF.emit(all_resources, "K1"))  # type: ignore[union-attr]
            convert_menu.addAction("To TSL Format").triggered.connect(lambda: self.requestConvertGFF.emit(all_resources, "TSL"))  # type: ignore[union-attr]

        # Convert TPC/TGA
        if all(resource.restype() is ResourceType.TPC for resource in all_resources):
            menu.addAction("Convert to TGA").triggered.connect(lambda: self.requestConvertTGA.emit(all_resources))  # type: ignore[union-attr]
        elif all(resource.restype() is ResourceType.TGA for resource in all_resources):
            menu.addAction("Convert to TPC").triggered.connect(lambda: self.requestConvertTPC.emit(all_resources))  # type: ignore[union-attr]

        menu.addSeparator()
        builder = ResourceItems(resources=all_resources)
        builder.viewport = lambda: self.ui.resourceTree
        builder.runContextMenu(point, menu=menu)

    def _show_resource_comparison(self, resource1: FileResource, resource2: FileResource | None = None):
        """Show side-by-side resource comparison dialog."""
        from toolset.gui.dialogs.resource_comparison import ResourceComparisonDialog
        from toolset.utils.window import addWindow

        dialog = ResourceComparisonDialog(self, resource1, resource2)
        addWindow(dialog)

    def _show_kotordiff_for_resources(self, resources: list[FileResource]):
        """Show KotorDiff window pre-configured for these resources."""
        # This would need parent window reference to get installations
        # For now, just show a message
        from qtpy.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "KotorDiff",
            "Open KotorDiff from Tools menu to compare installations.",
        )

    def _show_tslpatchdata_editor_for_resources(self, resources: list[FileResource]):
        """Show TSLPatchData editor for these resources."""
        from toolset.gui.dialogs.tslpatchdata_editor import TSLPatchDataEditor
        from toolset.utils.window import addWindow

        dialog = TSLPatchDataEditor(self)
        addWindow(dialog)

    def onResourceDoubleClicked(self):
        self.requestOpenResource.emit(self.selectedResources(), None)

    def resizeEvent(self, event: QResizeEvent):  # type: ignore[override, note]
        super().resizeEvent(event)
        self.ui.resourceTree.setColumnWidth(1, 10)
        self.ui.resourceTree.setColumnWidth(0, self.ui.resourceTree.width() - 80)
        header: QHeaderView | None = self.ui.resourceTree.header()  # pyright: ignore[reportAssignmentType]
        assert header is not None
        header.setSectionResizeMode(QHeaderView.Interactive)  # type: ignore[arg-type]


class ResourceProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.filter_string: str = ""

    def setFilterString(self, filter_string: str):
        self.filter_string = filter_string.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model: QStandardItemModel = self.sourceModel()  # pyright: ignore[reportAssignmentType]  # type: ignore[assignment]

        resref_index = model.index(source_row, 0, source_parent)
        item: ResourceStandardItem | QStandardItem | None = model.itemFromIndex(resref_index)
        if isinstance(item, ResourceStandardItem):
            # Get the file name and resource name
            filename = item.resource.filepath().name.lower()
            resname = item.resource.filename().lower()

            # Check if the filter string is a substring of either the filename or the resource name
            if self.filter_string in filename or self.filter_string in resname:
                return True

        return False


class ResourceModel(QStandardItemModel):
    """A data model used by the different trees (Core, Modules, Override).

    This class provides an easy way to add resources while sorting them into categories.
    """

    def __init__(self):
        super().__init__()
        self._categoryItems: dict[str, QStandardItem] = {}
        self._proxyModel: ResourceProxyModel = ResourceProxyModel(self)
        self._proxyModel.setSourceModel(self)
        self._proxyModel.setRecursiveFilteringEnabled(True)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ResRef", "Type"])

    def proxyModel(self) -> ResourceProxyModel:
        return self._proxyModel

    def clear(self):
        super().clear()
        self._categoryItems = {}
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ResRef", "Type"])

    def _addResourceIntoCategory(
        self,
        resourceType: ResourceType,
        customCategory: str | None = None,
    ) -> QStandardItem:
        chosen_category = resourceType.category if customCategory is None else customCategory
        if chosen_category not in self._categoryItems:
            categoryItem = QStandardItem(chosen_category)
            categoryItem.setSelectable(False)
            unusedItem = QStandardItem("")
            unusedItem.setSelectable(False)
            self._categoryItems[chosen_category] = categoryItem
            self.appendRow([categoryItem, unusedItem])
        return self._categoryItems[chosen_category]

    def addResource(
        self,
        resource: FileResource,
        customCategory: str | None = None,
    ):
        self._addResourceIntoCategory(resource.restype(), customCategory).appendRow(
            [
                ResourceStandardItem(resource.resname(), resource=resource),
                QStandardItem(resource.restype().extension.upper()),
            ]
        )

    def resourceFromIndexes(
        self,
        indexes: list[QModelIndex],
        *,
        proxy: bool = True,
    ) -> list[FileResource]:
        items = []
        for index in indexes:
            sourceIndex = self._proxyModel.mapToSource(index) if proxy else index
            items.append(self.itemFromIndex(sourceIndex))
        return self.resourceFromItems(items)  # type: ignore[arg-type]

    def resourceFromItems(
        self,
        items: list[QStandardItem],
    ) -> list[FileResource]:
        return [item.resource for item in items if isinstance(item, ResourceStandardItem)]  # pyright: ignore[reportAttributeAccessIssue]

    def allResourcesItems(self) -> list[QStandardItem]:
        """Returns a list of all QStandardItem objects in the model that represent resource files."""
        resources = (
            category.child(i, 0)
            for category in self._categoryItems.values()
            for i in range(category.rowCount())
        )
        return [item for item in resources if item is not None]

    def removeUnusedCategories(self):
        for row in range(self.rowCount())[::-1]:
            item = self.item(row)
            if item.rowCount() != 0:  # pyright: ignore[reportOptionalMemberAccess]  # type: ignore[union-attr]
                continue
            text = item.text()  # pyright: ignore[reportOptionalMemberAccess]  # type: ignore[union-attr]
            if text not in self._categoryItems:
                continue
            del self._categoryItems[text]
            self.removeRow(row)


class TextureList(MainWindowList):
    requestReload: ClassVar[QtCore.Signal] = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]

    requestRefresh: ClassVar[QtCore.Signal] = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]
    iconUpdate: ClassVar[QtCore.Signal] = QtCore.Signal(object, object)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.widgets.texture_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.texture_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415  # type: ignore[assignment]
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.texture_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415  # type: ignore[assignment]
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.texture_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415  # type: ignore[assignment]
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setupSignals()

        self._installation: HTInstallation | None = None
        self._scannedTextures: set[str] = set()
        self._shutting_down: bool = False

        self.texturesModel: QStandardItemModel = QStandardItemModel()
        self.texturesProxyModel: QSortFilterProxyModel = QSortFilterProxyModel()
        self.texturesProxyModel.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.texturesProxyModel.setSourceModel(self.texturesModel)
        self.ui.resourceList.setModel(self.texturesProxyModel)  # type: ignore[arg-type]

        self.sectionModel: QStandardItemModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.sectionModel)  # type: ignore[arg-type]

        # Use Manager for better Windows compatibility with spawn method
        self._manager: SyncManager = multiprocessing.Manager()

        # Queue for requesting texture loads from disk
        self._loadRequestQueue: multiprocessing.Queue = self._manager.Queue() # Queue for loaded TPC objects from disk
        self._loadedTextureQueue: multiprocessing.Queue = self._manager.Queue()
        # Queue for TPC conversion tasks
        self._taskQueue: multiprocessing.JoinableQueue = multiprocessing.JoinableQueue()
        # Queue for converted texture results
        self._resultQueue: multiprocessing.Queue = multiprocessing.Queue()

        # Texture loader process - loads TPCs from disk
        self._loader: TextureLoaderProcess | None = None

        # Texture conversion consumers - convert TPCs to RGB format
        self._consumers: list[TextureListConsumer] = [TextureListConsumer(self._taskQueue, self._resultQueue) for _ in range(multiprocessing.cpu_count())]
        for consumer in self._consumers:
            consumer.start()

        self._scanner: QThread = QThread(self)
        self._scanner.run = self.scan  # type: ignore[method-assign]
        self._scanner.start()

    def setupSignals(self):
        self.ui.searchEdit.textEdited.connect(self.onFilterStringUpdated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.onSectionChanged)
        self.ui.resourceList.doubleClicked.connect(self.onResourceDoubleClicked)
        self.iconUpdate.connect(self.onIconUpdate)

        vertScrollBar = self.ui.resourceList.verticalScrollBar()
        assert vertScrollBar is not None
        vertScrollBar.valueChanged.connect(self.onTextureListScrolled)
        self.ui.searchEdit.textChanged.connect(self.onTextureListScrolled)

    def doTerminations(self):
        # Signal scanner to stop gracefully
        self._shutting_down = True

        # Wait for scanner thread to finish (with timeout)
        if self._scanner.isRunning():
            self._scanner.quit()
            if not self._scanner.wait(2000):  # Wait up to 2 seconds
                RobustLogger().warning("Scanner thread did not stop gracefully, terminating forcefully: thread_id=%s", self._scanner)
                self._scanner.terminate()

        # Terminate consumer processes
        for consumer in self._consumers:
            consumer.terminate()

        # Terminate loader process if exists
        if self._loader is not None:
            self._loader.terminate()

        # Shutdown the manager server process
        try:
            self._manager.shutdown()
        except Exception as manager_exc:
            RobustLogger().warning("Error shutting down multiprocessing manager: manager_exc=%s", manager_exc)

    def setInstallation(self, installation: HTInstallation):
        self._installation = installation
        # Terminate old loader if exists
        if self._loader is not None:
            self._loader.terminate()
            self._loader = None
        # Start new loader process with installation path
        if installation is not None:
            try:
                self._loader = TextureLoaderProcess(
                    str(installation.path()),
                    installation.tsl,
                    self._loadRequestQueue,
                    self._loadedTextureQueue
                )
                self._loader.start()
                RobustLogger().info(f"Started TextureLoader process for installation: {installation.path()}")
            except PermissionError as perm_exc:
                RobustLogger().exception(f"Permission error starting TextureLoader process: {perm_exc}")
                RobustLogger().error("This is a Windows multiprocessing issue. Try running the application as administrator.")
                self._loader = None
            except Exception as start_exc:
                RobustLogger().exception(f"Failed to start TextureLoader process: {start_exc}")
                self._loader = None

    def setResources(
        self,
        resources: list[FileResource],
    ):
        blankImage = QImage(bytes(0 for _ in range(64 * 64 * 3)), 64, 64, QImage.Format.Format_RGB888)
        blankIcon = QIcon(QPixmap.fromImage(blankImage))

        self.texturesModel.clear()
        for resource in resources:
            item = QStandardItem(blankIcon, resource.resname())
            item.setToolTip(resource.resname())
            item.setData(False, Qt.ItemDataRole.UserRole)
            item.setData(resource, Qt.ItemDataRole.UserRole + 1)
            self.texturesModel.appendRow(item)

        if self._installation is not None:
            self.onTextureListScrolled()

    def setSections(
        self,
        sections: list[QStandardItem],
    ):
        self.sectionModel.clear()
        for section in sections:
            self.sectionModel.insertRow(self.sectionModel.rowCount(), section)

    def selectedResources(self) -> list[FileResource]:
        resources: list[FileResource] = []
        for proxyIndex in self.ui.resourceList.selectedIndexes():
            if not proxyIndex.isValid():
                continue
            sourceIndex = self.texturesProxyModel.mapToSource(proxyIndex)  # pyright: ignore[reportArgumentType]
            if not sourceIndex.isValid():
                continue
            item = self.texturesModel.item(sourceIndex.row())
            resources.append(item.data(Qt.ItemDataRole.UserRole + 1))  # type: ignore[union-attr]
        return resources

    def visibleItems(self) -> list[QStandardItem]:
        if self.texturesModel.rowCount() == 0:
            return []

        parent: QObject | None = self.parent()
        if parent is None:
            return []
        assert isinstance(parent, QWidget)
        scanWidth: int = parent.width()
        scanHeight: int = parent.height()

        proxyModel: QSortFilterProxyModel = self.texturesProxyModel
        model: QStandardItemModel = self.texturesModel

        firstItem: QStandardItem | None = None
        firstIndex: QModelIndex | None = None

        for y in range(2, 92, 2):
            for x in range(2, 92, 2):
                proxyIndex: QModelIndex = self.ui.resourceList.indexAt(QPoint(x, y))  # type: ignore[arg-type]
                index: QModelIndex = proxyModel.mapToSource(proxyIndex)
                item = model.itemFromIndex(index)
                if not firstItem and item:
                    firstItem = item
                    firstIndex = proxyIndex
                    break

        items: list[QStandardItem] = []

        if firstItem is not None and firstIndex is not None:
            widthCount: int = scanWidth // 92
            heightCount: int = scanHeight // 92 + 2
            numVisible: int = min(proxyModel.rowCount(), widthCount * heightCount)

            for i in range(numVisible):
                proxyIndex = proxyModel.index(firstIndex.row() + i, 0)
                if not proxyIndex.isValid():
                    continue
                sourceIndex: QModelIndex = proxyModel.mapToSource(proxyIndex)
                if not sourceIndex.isValid():
                    continue
                item = model.itemFromIndex(sourceIndex)
                if item is None:
                    continue
                items.append(item)

        return items

    def scan(self):
        """Scanner thread that processes loaded textures and conversion results."""
        while not self._shutting_down:
            # Check for loaded textures from disk and queue them for conversion
            try:
                while not self._loadedTextureQueue.empty():
                    if self._shutting_down:
                        RobustLogger().info("Scanner exiting due to shutdown flag: _shutting_down=%s", self._shutting_down)
                        return
                    row, resname, tpc = self._loadedTextureQueue.get_nowait()
                    if tpc is not None:
                        task = TextureListTask(row, tpc, resname)
                        self._taskQueue.put(task)
            except (BrokenPipeError, EOFError) as pipe_err:
                # Manager has been shut down, exit gracefully
                RobustLogger().info("Scanner exiting due to manager shutdown: pipe_err=%s", pipe_err)
                return
            except Exception as e:
                RobustLogger().exception("Error processing loaded texture: e=%s", e)

            # Check for converted texture results and update UI
            try:
                while not self._resultQueue.empty():
                    if self._shutting_down:
                        RobustLogger().info("Scanner exiting due to shutdown flag: _shutting_down=%s", self._shutting_down)
                        return
                    row, _resname, width, height, data = self._resultQueue.get_nowait()
                    image = QImage(data, width, height, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))
                    item = self.texturesModel.item(row, 0)
                    if item is not None:
                        self.iconUpdate.emit(item, QIcon(pixmap))
            except (BrokenPipeError, EOFError) as pipe_err:
                # Manager has been shut down, exit gracefully
                RobustLogger().info("Scanner exiting due to manager shutdown: pipe_err=%s", pipe_err)
                return
            except Exception as e:
                RobustLogger().exception("Error processing texture conversion result: e=%s", e)

            sleep(0.05)  # Reduced sleep time for more responsive UI

        RobustLogger().info("Scanner thread exiting normally: _shutting_down=%s", self._shutting_down)

    def onFilterStringUpdated(self):
        self.texturesProxyModel.setFilterFixedString(self.ui.searchEdit.text())

    def onSectionChanged(self):
        self.sectionChanged.emit(self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole))

    def onReloadClicked(self):
        self.requestReload.emit(self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole))

    def onRefreshClicked(self):
        self.requestRefresh.emit()

    def onTextureListScrolled(self):
        """Queue texture load requests without blocking the UI."""
        if self._installation is None:
            RobustLogger().debug("No installation loaded, nothing to scroll through")
            return

        if self._loader is None:
            RobustLogger().warning("Texture loader process not started")
            return

        # Queue load requests for visible items that haven't been loaded yet
        for item in self.visibleItems():
            itemText = item.text()
            lowerItemText = itemText.lower()

            if lowerItemText in self._scannedTextures:
                continue

            # Mark as scanned to avoid duplicate requests
            self._scannedTextures.add(lowerItemText)

            # Queue the load request - this won't block the UI
            load_request = TextureLoadRequest(
                item.row(),
                itemText,
                [SearchLocation.TEXTURES_GUI, SearchLocation.TEXTURES_TPA]
            )
            self._loadRequestQueue.put(load_request)
            item.setData(True, Qt.ItemDataRole.UserRole)

    def onIconUpdate(
        self,
        item: QStandardItem,
        icon: QIcon,
    ):
        try:  # FIXME(th3w1zard1): there's a race condition happening somewhere, causing the item to have previously been deleted.
            item.setIcon(icon)
        except RuntimeError:
            RobustLogger().exception("Could not update TextureList icon")

    def onResourceDoubleClicked(self):
        self.requestOpenResource.emit(self.selectedResources(), None)

    def resizeEvent(self, a0: QResizeEvent):  # pylint: disable=W0613  # pyright: ignore[reportIncompatibleMethodOverride]  # type: ignore[override, note]
        self.onTextureListScrolled()


class TextureListConsumer(multiprocessing.Process):
    def __init__(
        self,
        taskQueue: multiprocessing.JoinableQueue,
        resultQueue: multiprocessing.Queue,
    ):
        multiprocessing.Process.__init__(self)
        self.taskQueue: multiprocessing.JoinableQueue = taskQueue
        self.resultQueue: multiprocessing.Queue = resultQueue
        self.stopLoop: bool = False

    def run(self):
        while not self.stopLoop:
            next_task = self.taskQueue.get()

            answer = next_task()
            self.taskQueue.task_done()
            self.resultQueue.put(answer)


class TextureListTask:
    def __init__(
        self,
        row: int,
        tpc: TPC,
        resname: str,
    ):
        self.row: int = row
        self.tpc: TPC = tpc
        self.resname: str = resname

    def __repr__(self):
        return str(self.row)

    def __call__(self, *args, **kwargs) -> tuple[int, str, int, int, bytearray]:
        width, height, data = self.tpc.convert(TPCTextureFormat.RGB, self.bestMipmap(self.tpc))
        return self.row, self.resname, width, height, data

    def bestMipmap(self, tpc: TPC) -> int:
        for i in range(tpc.mipmap_count()):
            size = tpc.get(i).width
            if size <= 64:  # noqa: PLR2004
                return i
        return 0


class TextureLoadRequest:
    """Request to load a texture from disk."""
    def __init__(
        self,
        row: int,
        resname: str,
        search_locations: list[SearchLocation],
    ):
        self.row: int = row
        self.resname: str = resname
        self.search_locations: list[SearchLocation] = search_locations

    def __repr__(self):
        return f"TextureLoadRequest(row={self.row}, resname='{self.resname}')"


class TextureLoaderProcess(multiprocessing.Process):
    """Process that loads textures from disk without blocking the UI."""
    def __init__(
        self,
        installation_path: str,
        is_tsl: bool,
        request_queue: multiprocessing.Queue,
        result_queue: multiprocessing.Queue,
    ):
        multiprocessing.Process.__init__(self)
        self.installation_path: str = installation_path
        self.is_tsl: bool = is_tsl
        self.request_queue: multiprocessing.Queue = request_queue
        self.result_queue: multiprocessing.Queue = result_queue
        self.stopLoop: bool = False

    def run(self):
        """Load textures from disk in a separate process."""
        import queue
        import traceback

        from toolset.data.installation import HTInstallation

        # Create installation in this process
        try:
            installation = HTInstallation(self.installation_path, "TextureLoader", tsl=self.is_tsl)
            RobustLogger().info(f"TextureLoader process started successfully for installation: {self.installation_path}")
        except Exception as init_exc:
            RobustLogger().exception(f"Failed to initialize HTInstallation in TextureLoader process: {init_exc}")
            RobustLogger().error(f"Installation path: {self.installation_path}, TSL: {self.is_tsl}")
            RobustLogger().error(f"Traceback:\n{''.join(traceback.format_exc())}")
            return

        while not self.stopLoop:
            try:
                # Get load request with timeout to allow checking stopLoop
                try:
                    request: TextureLoadRequest = self.request_queue.get(timeout=0.1)
                except queue.Empty:  # noqa: S112
                    # Timeout is expected when queue is empty - don't log
                    continue
                except Exception as get_exc:
                    RobustLogger().exception(f"Unexpected error getting request from queue: {get_exc}")
                    RobustLogger().error(f"Traceback:\n{''.join(traceback.format_exc())}")
                    continue

                # Load texture from disk (this is the blocking operation)
                try:
                    textures = installation.textures(
                        [request.resname],
                        request.search_locations
                    )

                    tpc: TPC | None = textures.get(request.resname)
                    if tpc is None:
                        RobustLogger().debug(f"Texture '{request.resname}' not found, using empty TPC")
                        tpc = TPC()  # Empty TPC for missing textures

                    # Put loaded texture in result queue
                    self.result_queue.put((request.row, request.resname, tpc))
                    RobustLogger().debug(f"Successfully loaded and queued texture '{request.resname}' for row {request.row}")

                except Exception as load_exc:
                    RobustLogger().exception(f"Error loading texture '{request.resname}': {load_exc}")
                    RobustLogger().error(f"Request: {request}")
                    RobustLogger().error(f"Search locations: {request.search_locations}")
                    RobustLogger().error(f"Traceback:\n{''.join(traceback.format_exc())}")
                    # Still put empty TPC in queue so UI doesn't hang waiting
                    self.result_queue.put((request.row, request.resname, TPC()))

            except Exception as outer_exc:
                RobustLogger().exception(f"Unexpected error in TextureLoader main loop: {outer_exc}")
                RobustLogger().error(f"Traceback:\n{''.join(traceback.format_exc())}")

