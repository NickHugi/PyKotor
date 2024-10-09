from __future__ import annotations

from enum import Enum

from qtpy.QtWidgets import QMenu

from utility.ui_libraries.qt.common.action_definitions import FileExplorerActions


class MenuContext(Enum):
    FILE = "file"
    DIR = "dir"
    MIXED = "mixed"
    EMPTY = "empty"


class FileExplorerMenus:
    """Creates dynamic menus for a file explorer."""
    def __init__(self):
        self.actions = FileExplorerActions()

    def create_menu(
        self,
        context: MenuContext,
        *,
        shift: bool = False,
        multi: bool = False,
    ) -> QMenu:
        menu = QMenu()

        if context in [MenuContext.FILE, MenuContext.DIR, MenuContext.MIXED]:
            if not shift:
                menu.addAction(self.actions.actionOpen)
                menu.addAction(self.actions.actionOpenInNewWindow)
                menu.addAction(self.actions.actionOpenInNewTab)
                if context == MenuContext.FILE:
                    menu.addAction(self.actions.actionOpenWith)
                    menu.addAction(self.actions.actionEdit)
                menu.addSeparator()
                menu.addAction(self.actions.actionCut)
                menu.addAction(self.actions.actionCopy)
                menu.addAction(self.actions.actionCopyPath)
                if not multi:
                    menu.addAction(self.actions.actionCopyAsPath)
                if context == MenuContext.DIR:
                    menu.addAction(self.actions.actionPaste)
                menu.addSeparator()
                menu.addAction(self.actions.actionCreateShortcut)
                menu.addAction(self.actions.actionDelete)
                menu.addAction(self.actions.actionRename)
                menu.addSeparator()
                menu.addAction(self.actions.actionCompress)
                menu.addAction(self.actions.actionExtract)
                menu.addSeparator()
                send_to_menu = menu.addMenu("Send To")
                send_to_menu.addAction(self.actions.actionSendToDesktop)
                send_to_menu.addAction(self.actions.actionSendToDocuments)
                send_to_menu.addAction(self.actions.actionSendToCompressedFolder)
            else:
                menu.addAction(self.actions.actionOpenAsAdmin)
                menu.addAction(self.actions.actionCopyAsPath)
                menu.addSeparator()
                menu.addAction(self.actions.actionTakeOwnership)
                menu.addSeparator()
                menu.addAction(self.actions.actionOpenTerminal)
                menu.addSeparator()
                menu.addAction(self.actions.actionAddToArchive)
            menu.addSeparator()
            menu.addAction(self.actions.actionProperties)

        elif context == MenuContext.EMPTY:
            view_menu = menu.addMenu("View")
            sort_menu = menu.addMenu("Sort By")
            group_menu = menu.addMenu("Group By")

            if shift:
                view_menu.addAction(self.actions.actionExtraLargeIcons)
                view_menu.addAction(self.actions.actionViewContent)
                sort_menu.addAction(self.actions.actionSortByAuthor)
                sort_menu.addAction(self.actions.actionSortByTags)
                group_menu.addAction(self.actions.actionGroupByDateCreated)

            view_menu.addAction(self.actions.actionLargeIcons)
            view_menu.addAction(self.actions.actionMediumIcons)
            view_menu.addAction(self.actions.actionSmallIcons)
            view_menu.addAction(self.actions.actionListView)
            view_menu.addAction(self.actions.actionDetailView)
            view_menu.addAction(self.actions.actionTiles)

            sort_menu.addAction(self.actions.actionSortByName)
            sort_menu.addAction(self.actions.actionSortByDateModified)
            sort_menu.addAction(self.actions.actionSortByType)
            sort_menu.addAction(self.actions.actionSortBySize)
            sort_menu.addAction(self.actions.actionSortByDateCreated)
            sort_menu.addSeparator()
            ascending_action = sort_menu.addAction("Ascending")
            ascending_action.setCheckable(True)
            ascending_action.setChecked(True)
            descending_action = sort_menu.addAction("Descending")
            descending_action.setCheckable(True)
            sort_menu.addSeparator()
            sort_menu.addAction("More...")

            group_menu.addAction(self.actions.actionGroupByName)
            group_menu.addAction(self.actions.actionGroupBySize)
            group_menu.addAction(self.actions.actionGroupByType)
            group_menu.addAction(self.actions.actionGroupByDateModified)
            group_menu.addSeparator()
            group_menu.addAction("More...")

            menu.addSeparator()
            menu.addAction(self.actions.actionPaste)
            menu.addAction(self.actions.actionPasteShortcut)
            menu.addSeparator()

            new_menu = menu.addMenu("New")
            new_menu.addAction(self.actions.actionNewFolder)
            new_menu.addAction(self.actions.actionNewTextDocument)
            if shift:
                new_menu.addAction(self.actions.actionNewCompressedFolder)

            menu.addSeparator()

            if shift:
                menu.addAction(self.actions.actionOpenTerminal)
                menu.addSeparator()
                menu.addAction(self.actions.actionShowHideHiddenItems)
                menu.addSeparator()
                menu.addAction(self.actions.actionPersonalize)
                menu.addAction(self.actions.actionDisplaySettings)
                menu.addSeparator()

            menu.addAction(self.actions.actionProperties)

        return menu
