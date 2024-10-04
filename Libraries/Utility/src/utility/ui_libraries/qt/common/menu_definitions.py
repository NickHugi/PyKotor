from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import QSize, Qt
from qtpy.QtWidgets import QGroupBox, QHBoxLayout, QMenu, QToolButton, QVBoxLayout

from utility.ui_libraries.qt.common.action_definitions import FileExplorerActions

if TYPE_CHECKING:
    from qtpy.QtGui import QAction

    from utility.ui_libraries.qt.common.actions_dispatcher import MenuActionsDispatcher


class FileExplorerMenus:
    """Creates static menus for a file explorer."""
    def __init__(self, menu_handler: MenuActionsDispatcher):
        self.actions = FileExplorerActions(menu_handler)
        self.menu_file: QMenu = self.create_file_menu()
        self.menu_dir: QMenu = self.create_dir_menu()
        self.menu_file_shift: QMenu = self.create_file_shift_menu()
        self.menu_dir_shift: QMenu = self.create_dir_shift_menu()
        self.menu_empty: QMenu = self.create_empty_menu()
        self.menu_empty_shift: QMenu = self.create_empty_shift_menu()
        self.menu_mixed_selection: QMenu = self.create_mixed_selection_menu()
        self.menu_mixed_selection_shift: QMenu = self.create_mixed_selection_shift_menu()

    def create_multi_file_menu(self) -> QMenu:
        menu = QMenu()
        menu.addAction(self.actions.actionCopyFiles)
        menu.addAction(self.actions.actionCutFiles)
        menu.addAction(self.actions.actionDeleteFiles)
        return menu

    def create_multi_dir_menu(self) -> QMenu:
        menu = QMenu()
        menu.addAction(self.actions.actionCopyDirs)
        menu.addAction(self.actions.actionCutDirs)
        menu.addAction(self.actions.actionDeleteDirs)
        return menu

    def create_mixed_selection_menu(self) -> QMenu:
        menu = QMenu()
        menu.addAction(self.actions.actionCopyItems)
        menu.addAction(self.actions.actionCutItems)
        menu.addAction(self.actions.actionDeleteItems)
        return menu

    def create_mixed_selection_shift_menu(self) -> QMenu:
        menu = QMenu()
        menu.addAction(self.actions.actionCopyAsPath)
        menu.addSeparator()
        menu.addAction(self.actions.actionTakeOwnership)
        menu.addSeparator()
        menu.addAction(self.actions.actionOpenTerminal)
        menu.addAction(self.actions.actionOpenPowerShell)
        menu.addSeparator()
        menu.addAction(self.actions.actionAddToArchive)
        menu.addSeparator()
        menu.addAction(self.actions.actionScanWithAntivirus)
        menu.addSeparator()
        menu.addAction(self.actions.actionExtendedProperties)
        return menu

    def create_file_menu(self) -> QMenu:
        menu = QMenu()
        menu.addAction(self.actions.actionOpenFile)
        menu.addAction(self.actions.actionOpenWithFile)
        menu.addAction(self.actions.actionOpenInNewWindowFile)
        menu.addAction(self.actions.actionOpenInNewTabFile)
        menu.addAction(self.actions.actionEditFile)
        menu.addAction(self.actions.actionPrintFile)
        menu.addSeparator()
        menu.addAction(self.actions.actionCutFile)
        menu.addAction(self.actions.actionCopyFile)
        menu.addAction(self.actions.actionCopyPathFile)
        menu.addAction(self.actions.actionCopyAsPathFile)
        menu.addSeparator()
        menu.addAction(self.actions.actionCreateShortcutFile)
        menu.addAction(self.actions.actionDeleteFile)
        menu.addAction(self.actions.actionRenameFile)
        menu.addSeparator()
        menu.addAction(self.actions.actionCompressFile)
        menu.addAction(self.actions.actionExtractFile)
        menu.addSeparator()
        menu.addMenu(self.create_send_to_submenu())
        menu.addAction(self.actions.actionShareFile)
        menu.addSeparator()
        menu.addAction(self.actions.actionPropertiesFile)
        return menu

    def create_dir_menu(self) -> QMenu:
        menu = QMenu()
        menu.addAction(self.actions.actionOpenDir)
        menu.addAction(self.actions.actionOpenInNewWindowDir)
        menu.addAction(self.actions.actionOpenInNewTabDir)
        menu.addSeparator()
        menu.addAction(self.actions.actionCutDir)
        menu.addAction(self.actions.actionCopyDir)
        menu.addAction(self.actions.actionCopyPathDir)
        menu.addAction(self.actions.actionCopyAsPath)
        menu.addAction(self.actions.actionPasteDir)
        menu.addSeparator()
        menu.addAction(self.actions.actionCreateShortcutDir)
        menu.addAction(self.actions.actionDeleteDir)
        menu.addAction(self.actions.actionRenameDir)
        menu.addSeparator()
        menu.addAction(self.actions.actionCompressDir)
        menu.addAction(self.actions.actionExtractHereDir)
        menu.addSeparator()
        menu.addMenu(self.create_send_to_submenu())
        menu.addAction(self.actions.actionShareDir)
        menu.addSeparator()
        menu.addAction(self.actions.actionPropertiesDir)
        return menu

    def create_file_shift_menu(self) -> QMenu:
        menu = QMenu()
        menu.addAction(self.actions.actionOpenAsAdminFile)
        menu.addAction(self.actions.actionCopyAsPathFile)
        menu.addSeparator()
        menu.addAction(self.actions.actionTakeOwnershipFile)
        menu.addSeparator()
        menu.addAction(self.actions.actionOpenTerminalFile)
        menu.addAction(self.actions.actionOpenPowerShellFile)
        menu.addSeparator()
        menu.addAction(self.actions.actionAddToArchiveFile)
        menu.addSeparator()
        menu.addAction(self.actions.actionScanWithAntivirusFile)
        menu.addSeparator()
        menu.addAction(self.actions.actionExtendedPropertiesFile)
        return menu

    def create_dir_shift_menu(self) -> QMenu:
        menu = QMenu()
        menu.addAction(self.actions.actionOpenAsAdminDir)
        menu.addAction(self.actions.actionCopyAsPath)
        menu.addSeparator()
        menu.addAction(self.actions.actionTakeOwnership)
        menu.addSeparator()
        menu.addAction(self.actions.actionOpenTerminal)
        menu.addAction(self.actions.actionOpenPowerShell)
        menu.addSeparator()
        menu.addAction(self.actions.actionAddToArchive)
        menu.addSeparator()
        menu.addAction(self.actions.actionScanWithAntivirus)
        menu.addSeparator()
        menu.addAction(self.actions.actionExtendedProperties)
        return menu

    def create_empty_menu(self) -> QMenu:
        menu = QMenu()
        menu.addMenu(self.create_view_submenu())
        menu.addMenu(self.create_sort_by_submenu())
        menu.addMenu(self.create_group_by_submenu())
        menu.addSeparator()
        menu.addAction(self.actions.actionPasteEmpty)
        menu.addAction(self.actions.actionPasteShortcutEmpty)
        menu.addSeparator()
        menu.addMenu(self.create_new_submenu())
        menu.addSeparator()
        menu.addAction(self.actions.actionPropertiesEmpty)
        return menu

    def create_empty_shift_menu(self) -> QMenu:
        menu = QMenu()
        menu.addMenu(self.create_view_submenu_shift())
        menu.addMenu(self.create_sort_by_submenu_shift())
        menu.addMenu(self.create_group_by_submenu_shift())
        menu.addSeparator()
        menu.addAction(self.actions.actionOpenCommandWindowEmpty)
        menu.addAction(self.actions.actionOpenPowerShellWindowEmpty)
        menu.addSeparator()
        menu.addAction(self.actions.actionShowHideHiddenItems)
        menu.addSeparator()
        menu.addMenu(self.create_new_submenu_shift())
        menu.addSeparator()
        menu.addAction(self.actions.actionPersonalize)
        menu.addAction(self.actions.actionDisplaySettings)
        menu.addSeparator()
        menu.addAction(self.actions.actionPropertiesEmpty)
        return menu

    def create_send_to_submenu(self) -> QMenu:
        menu = QMenu("Send To")
        menu.addAction(self.actions.actionSendToDesktop)
        menu.addAction(self.actions.actionSendToDocuments)
        menu.addAction(self.actions.actionSendToCompressedFolder)
        menu.addAction(self.actions.actionSendToMailRecipient)
        menu.addAction(self.actions.actionSendToBluetoothDevice)
        return menu

    def create_view_submenu(self) -> QMenu:
        menu = QMenu("View")
        menu.addAction(self.actions.actionLargeIcons)
        menu.addAction(self.actions.actionMediumIcons)
        menu.addAction(self.actions.actionSmallIcons)
        menu.addAction(self.actions.actionList)
        menu.addAction(self.actions.actionDetails)
        menu.addAction(self.actions.actionTiles)
        return menu

    def create_view_submenu_shift(self) -> QMenu:
        menu = QMenu("View")
        menu.addAction(self.actions.actionViewExtraLargeIcons)
        menu.addAction(self.actions.actionLargeIcons)
        menu.addAction(self.actions.actionMediumIcons)
        menu.addAction(self.actions.actionSmallIcons)
        menu.addAction(self.actions.actionList)
        menu.addAction(self.actions.actionDetails)
        menu.addAction(self.actions.actionTiles)
        menu.addAction(self.actions.actionViewContent)
        return menu

    def create_sort_by_submenu(self) -> QMenu:
        menu = QMenu("Sort By")
        menu.addAction(self.actions.actionSortByName)
        menu.addAction(self.actions.actionSortBySize)
        menu.addAction(self.actions.actionSortByType)
        menu.addAction(self.actions.actionSortByDateModified)
        return menu

    def create_sort_by_submenu_shift(self) -> QMenu:
        menu = QMenu("Sort By")
        menu.addAction(self.actions.actionSortByName)
        menu.addAction(self.actions.actionSortBySize)
        menu.addAction(self.actions.actionSortByType)
        menu.addAction(self.actions.actionSortByDateModified)
        menu.addAction(self.actions.actionSortByDateCreated)
        menu.addAction(self.actions.actionSortByAuthor)
        menu.addAction(self.actions.actionSortByTags)
        return menu

    def create_group_by_submenu(self) -> QMenu:
        menu = QMenu("Group By")
        menu.addAction(self.actions.actionGroupByName)
        menu.addAction(self.actions.actionGroupBySize)
        menu.addAction(self.actions.actionGroupByType)
        menu.addAction(self.actions.actionGroupByDateModified)
        return menu

    def create_group_by_submenu_shift(self) -> QMenu:
        menu = QMenu("Group By")
        menu.addAction(self.actions.actionGroupByName)
        menu.addAction(self.actions.actionGroupBySize)
        menu.addAction(self.actions.actionGroupByType)
        menu.addAction(self.actions.actionGroupByDateModified)
        menu.addAction(self.actions.actionGroupByDateCreated)
        menu.addAction(self.actions.actionGroupByAuthor)
        menu.addAction(self.actions.actionGroupByTags)
        return menu

    def create_new_submenu(self) -> QMenu:
        menu = QMenu("New")
        menu.addAction(self.actions.actionNewFolder)
        menu.addAction(self.actions.actionNewTextDocument)
        menu.addAction(self.actions.actionNewBitmapImage)
        menu.addAction(self.actions.actionNewWordDocument)
        menu.addAction(self.actions.actionNewExcelWorksheet)
        menu.addAction(self.actions.actionNewPowerPointPresentation)
        return menu

    def create_new_submenu_shift(self) -> QMenu:
        menu = QMenu("New")
        menu.addAction(self.actions.actionNewFolder)
        menu.addAction(self.actions.actionNewTextDocument)
        menu.addAction(self.actions.actionNewBitmapImage)
        menu.addAction(self.actions.actionNewWordDocument)
        menu.addAction(self.actions.actionNewExcelWorksheet)
        menu.addAction(self.actions.actionNewPowerPointPresentation)
        menu.addAction(self.actions.actionNewCompressedFolder)
        return menu

    def setup_home_ribbon(self):
        self.home_ribbon_layout = QVBoxLayout()
        self.home_ribbon_layout.addWidget(self.create_ribbon_group("File", [self.actions.actionOpeninNewWindow, self.actions.actionOpenTerminal, self.actions.actionProperties, self.actions.actionExit]))
        self.home_ribbon_layout.addWidget(self.create_ribbon_group("Edit", [self.actions.actionCut, self.actions.actionCopy, self.actions.actionPaste, self.actions.actionDelete]))
        self.home_ribbon_layout.addWidget(self.create_ribbon_group("Select", [self.actions.actionSelectAll, self.actions.actionInvertSelection, self.actions.actionSelectNone]))
        self.home_ribbon_layout.addWidget(self.create_ribbon_group("Organize", [self.actions.actionCreateNewFolder, self.actions.actionRename]))

    def setup_view_ribbon(self):
        self.view_ribbon_layout = QVBoxLayout()
        self.view_ribbon_layout.addWidget(self.create_ribbon_group("Show/Hide", [self.actions.actionRefresh, self.actions.actionShowHiddenItems]))
        self.view_ribbon_layout.addWidget(self.create_ribbon_group("File Types", [self.actions.actionShowExecutables, self.actions.actionShowWritable, self.actions.actionShowReadable, self.actions.actionShowSystem]))
        self.view_ribbon_layout.addWidget(self.create_ribbon_group("Items", [self.actions.actionShowDirs, self.actions.actionShowAllDirectories, self.actions.actionShowFiles, self.actions.actionShowSymlinks, self.actions.actionShowDotAndDotDot]))


    def create_ribbon_group(self, title: str, _actions: list[QAction]):
        group = QGroupBox(title)
        layout = QHBoxLayout
        for action in _actions:
            button = QToolButton()
            button.setDefaultAction(action)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            button.setFixedSize(80, 70)
            button.setIconSize(QSize(32, 32))
            layout.addWidget(button)
        group.setLayout(layout)
        return group
