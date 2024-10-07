from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtGui import QAction, QIcon, QKeySequence

if TYPE_CHECKING:
    from utility.ui_libraries.qt.common.actions_dispatcher import MenuActionsDispatcher

class FileExplorerActions:
    """Creates actions for a file explorer. Any and all possible actions should be defined here.

    triggered connections are also defined here. If an action is simple enough that it does not need preparation with app-specific/main process context
    it should lambda to call queue_task directly. it should NOT create a prepare task unless it absolutely has to.
    The goal is to define simpler direct queue_task actions and prefer them over preparation actions.

    e.g. open_file/open_folder can simply call queue task and pass the filepath, while more complicated things like cut/copy/paste will need to prepare the clipboard.
    a third scenario is a file dialog/main window/widget will need to handle 'open in new tab' and handle view-related context itself.
    """
    def __init__(self, menu_handler: MenuActionsDispatcher):
        self.menu_handler: MenuActionsDispatcher = menu_handler

        # Open actions
        self.actionOpen = QAction(QIcon.fromTheme("document-open"), "Open")
        self.actionOpen.setShortcut(QKeySequence("Enter"))
        self.actionOpen.triggered.connect(lambda: self.menu_handler.queue_task("open_item", self.menu_handler.get_selected_paths()))

        self.actionOpenInNewWindow = QAction(QIcon.fromTheme("window-new"), "Open in New Window")
        self.actionOpenInNewWindow.setShortcut(QKeySequence("Shift+Enter"))
        # openInNewWindow trigger implemented in explorer/browser widget

        self.actionOpenInNewTab = QAction(QIcon.fromTheme("tab-new"), "Open in New Tab")
        self.actionOpenInNewTab.setShortcut(QKeySequence("Ctrl+T"))
        # actionOpenInNewTab trigger implemented in explorer/browser widget

        self.actionOpenWith = QAction(QIcon.fromTheme("document-open"), "Open With...")
        self.actionOpenWith.setShortcut(QKeySequence("Alt+Enter"))
        self.actionOpenWith.triggered.connect(lambda: self.menu_handler.queue_task("open_with", self.menu_handler.get_selected_paths()))

        self.actionProperties = QAction(QIcon.fromTheme("document-properties"), "Properties")
        self.actionProperties.setShortcut(QKeySequence("Alt+Enter"))
        self.actionProperties.triggered.connect(lambda: self.menu_handler.queue_task("get_properties", self.menu_handler.get_selected_paths()))

        self.actionOpenTerminal = QAction(QIcon.fromTheme("utilities-terminal"), "Open Terminal")
        self.actionOpenTerminal.setShortcut(QKeySequence("Shift+F10"))
        self.actionOpenTerminal.triggered.connect(lambda: self.menu_handler.queue_task("open_terminal", self.menu_handler.get_selected_paths()))

        self.actionCut = QAction(QIcon.fromTheme("edit-cut"), "Cut")
        self.actionCut.setShortcut(QKeySequence.StandardKey.Cut)
        self.actionCut.triggered.connect(self.menu_handler.on_cut_items)

        self.actionCopy = QAction(QIcon.fromTheme("edit-copy"), "Copy")
        self.actionCopy.setShortcut(QKeySequence.StandardKey.Copy)
        self.actionCopy.triggered.connect(self.menu_handler.on_copy_items)

        self.actionPaste = QAction(QIcon.fromTheme("edit-paste"), "Paste")
        self.actionPaste.setShortcut(QKeySequence.StandardKey.Paste)
        self.actionPaste.triggered.connect(self.menu_handler.on_paste_items)

        self.actionDelete = QAction(QIcon.fromTheme("edit-delete"), "Delete")
        self.actionDelete.setShortcut(QKeySequence.StandardKey.Delete)
        self.actionDelete.triggered.connect(lambda: self.menu_handler.queue_task("delete_items", self.menu_handler.get_selected_paths()))

        self.actionRename = QAction(QIcon.fromTheme("edit-rename"), "Rename")
        self.actionRename.setShortcut("F2")
        self.actionRename.triggered.connect(lambda: self.menu_handler.queue_task("rename_item", self.menu_handler.get_selected_paths()))

        # ... (other actions)

        # Multi-selection actions
        self.actionCopyItems = QAction(QIcon.fromTheme("edit-copy"), "Copy Items")
        self.actionCopyItems.setShortcut(QKeySequence.StandardKey.Copy)
        self.actionCopyItems.triggered.connect(self.menu_handler.on_copy_items)

        self.actionCutItems = QAction(QIcon.fromTheme("edit-cut"), "Cut Items")
        self.actionCutItems.setShortcut(QKeySequence.StandardKey.Cut)
        self.actionCutItems.triggered.connect(self.menu_handler.on_cut_items)

        self.actionDeleteItems = QAction(QIcon.fromTheme("edit-delete"), "Delete Items")
        self.actionDeleteItems.setShortcut(QKeySequence.StandardKey.Delete)
        self.actionDeleteItems.triggered.connect(lambda: self.menu_handler.queue_task("delete_items", self.menu_handler.get_selected_paths()))

        # View actions
        # all of these action triggers implemented in explorer/browser widget.
        self.actionLargeIcons = QAction(QIcon.fromTheme("view-list-icons"), "Large Icons")
        self.actionLargeIcons.setShortcut(QKeySequence("Ctrl+Shift+1"))
        self.actionMediumIcons = QAction(QIcon.fromTheme("view-list-icons"), "Medium Icons")
        self.actionMediumIcons.setShortcut(QKeySequence("Ctrl+Shift+2"))
        self.actionSmallIcons = QAction(QIcon.fromTheme("view-list-icons"), "Small Icons")
        self.actionSmallIcons.setShortcut(QKeySequence("Ctrl+Shift+3"))
        self.actionList = QAction(QIcon.fromTheme("view-list-details"), "List")
        self.actionList.setShortcut(QKeySequence("Ctrl+Shift+4"))
        self.actionDetails = QAction(QIcon.fromTheme("view-list-tree"), "Details")
        self.actionDetails.setShortcut(QKeySequence("Ctrl+Shift+5"))
        self.actionTiles = QAction(QIcon.fromTheme("view-list-icons"), "Tiles")
        self.actionTiles.setShortcut(QKeySequence("Ctrl+Shift+6"))
        self.actionContent = QAction(QIcon.fromTheme("view-list-text"), "Content")
        self.actionContent.setShortcut(QKeySequence("Ctrl+Shift+7"))
        self.actionShowHiddenItems = QAction(QIcon.fromTheme("view-hidden"), "Hidden items")
        self.actionShowHiddenItems.setCheckable(True)
        self.actionShowHiddenItems.setShortcut(QKeySequence("Ctrl+H"))
        self.actionRefresh = QAction(QIcon.fromTheme("view-refresh"), "Refresh")
        self.actionRefresh.setShortcut(QKeySequence("F5"))
        self.actionShowExecutables = QAction(QIcon.fromTheme("application-x-executable"), "File name extensions")
        self.actionShowExecutables.setCheckable(True)
        self.actionShowExecutables.setShortcut(QKeySequence("Alt+V, F"))
        self.actionShowDirs = QAction(QIcon.fromTheme("folder"), "Item check boxes")
        self.actionShowDirs.setCheckable(True)
        self.actionShowDirs.setShortcut(QKeySequence("Alt+V, B"))
        self.actionShowFiles = QAction(QIcon.fromTheme("text-x-generic"), "Show Files")
        self.actionShowFiles.setCheckable(True)
        self.actionShowFiles.setShortcut(QKeySequence("Alt+V, S"))
        self.actionShowSymlinks = QAction(QIcon.fromTheme("emblem-symbolic-link"), "Show Symlinks")
        self.actionShowSymlinks.setCheckable(True)
        self.actionShowSymlinks.setShortcut(QKeySequence("Alt+V, L"))
        self.actionShowDotAndDotDot = QAction(QIcon.fromTheme("folder"), "Show Dot and DotDot")
        self.actionShowDotAndDotDot.setCheckable(True)
        self.actionShowDotAndDotDot.setShortcut(QKeySequence("Alt+V, D"))
        self.actionShowWritable = QAction(QIcon.fromTheme("document-edit"), "Show Writable")
        self.actionShowWritable.setCheckable(True)
        self.actionShowWritable.setShortcut(QKeySequence("Alt+V, W"))
        self.actionShowReadable = QAction(QIcon.fromTheme("document-open"), "Show Readable")
        self.actionShowReadable.setCheckable(True)
        self.actionShowReadable.setShortcut(QKeySequence("Alt+V, R"))
        self.actionShowSystem = QAction(QIcon.fromTheme("computer"), "Show System")
        self.actionShowSystem.setCheckable(True)
        self.actionShowSystem.setShortcut(QKeySequence("Alt+V, Y"))
        self.actionShowAllDirectories = QAction(QIcon.fromTheme("folder-open"), "Show All Directories")
        self.actionShowAllDirectories.setCheckable(True)
        self.actionShowAllDirectories.setShortcut(QKeySequence("Alt+V, A"))

        # Sort actions
        self.actionSortByName = QAction(QIcon.fromTheme("view-sort-ascending"), "Name")
        self.actionSortByName.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.actionSortByName.triggered.connect(lambda: menu_handler.prepare_sort("name"))

        self.actionSortByDateModified = QAction(QIcon.fromTheme("view-sort-ascending"), "Date modified")
        self.actionSortByDateModified.setShortcut(QKeySequence("Ctrl+Shift+E"))
        self.actionSortByDateModified.triggered.connect(lambda: menu_handler.prepare_sort("date_modified"))

        self.actionSortByType = QAction(QIcon.fromTheme("view-sort-ascending"), "Type")
        self.actionSortByType.setShortcut(QKeySequence("Ctrl+Shift+T"))
        self.actionSortByType.triggered.connect(lambda: menu_handler.prepare_sort("type"))

        self.actionSortBySize = QAction(QIcon.fromTheme("view-sort-ascending"), "Size")
        self.actionSortBySize.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.actionSortBySize.triggered.connect(lambda: menu_handler.prepare_sort("size"))

        self.actionSortByDateCreated = QAction(QIcon.fromTheme("view-sort-ascending"), "Date created")
        self.actionSortByDateCreated.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.actionSortByDateCreated.triggered.connect(lambda: menu_handler.prepare_sort("date_created"))

        self.actionSortByAuthor = QAction(QIcon.fromTheme("view-sort-ascending"), "Authors")
        self.actionSortByAuthor.setShortcut(QKeySequence("Ctrl+Shift+A"))
        self.actionSortByAuthor.triggered.connect(lambda: menu_handler.prepare_sort("author"))

        self.actionSortByTitle = QAction(QIcon.fromTheme("view-sort-ascending"), "Title")
        self.actionSortByTitle.setShortcut(QKeySequence("Ctrl+Shift+I"))
        self.actionSortByTitle.triggered.connect(lambda: menu_handler.prepare_sort("title"))

        self.actionSortByTags = QAction(QIcon.fromTheme("view-sort-ascending"), "Tags")
        self.actionSortByTags.setShortcut(QKeySequence("Ctrl+Shift+G"))
        self.actionSortByTags.triggered.connect(lambda: menu_handler.prepare_sort("tags"))

        self.actionToggleSortOrder = QAction(QIcon.fromTheme("view-sort"), "Toggle Sort Order")
        self.actionToggleSortOrder.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self.actionToggleSortOrder.triggered.connect(menu_handler.toggle_sort_order)

        # Group by actions
        self.actionGroupByNone = QAction(QIcon.fromTheme("view-group"), "(None)")
        self.actionGroupByNone.setShortcut(QKeySequence("Alt+G, N"))
        self.actionGroupByName = QAction(QIcon.fromTheme("view-group"), "Name")
        self.actionGroupByName.setShortcut(QKeySequence("Alt+G, A"))
        self.actionGroupByDateModified = QAction(QIcon.fromTheme("view-group"), "Date modified")
        self.actionGroupByDateModified.setShortcut(QKeySequence("Alt+G, M"))
        self.actionGroupByType = QAction(QIcon.fromTheme("view-group"), "Type")
        self.actionGroupByType.setShortcut(QKeySequence("Alt+G, T"))
        self.actionGroupBySize = QAction(QIcon.fromTheme("view-group"), "Size")
        self.actionGroupBySize.setShortcut(QKeySequence("Alt+G, S"))
        self.actionGroupByDateCreated = QAction(QIcon.fromTheme("view-group"), "Date created")
        self.actionGroupByDateCreated.setShortcut(QKeySequence("Alt+G, C"))
        self.actionGroupByAuthor = QAction(QIcon.fromTheme("view-group"), "Authors")
        self.actionGroupByAuthor.setShortcut(QKeySequence("Alt+G, U"))
        self.actionGroupByTitle = QAction(QIcon.fromTheme("view-group"), "Title")
        self.actionGroupByTitle.setShortcut(QKeySequence("Alt+G, I"))
        self.actionGroupByTags = QAction(QIcon.fromTheme("view-group"), "Tags")
        self.actionGroupByTags.setShortcut(QKeySequence("Alt+G, G"))

        # Share actions
        # share/email are a maybe depending on the difficulty.
        self.actionShare = QAction(QIcon.fromTheme("document-send"), "Share")
        self.actionShare.setShortcut(QKeySequence("Alt+S, H"))
        self.actionShare.triggered.connect(lambda: self.menu_handler.queue_task("share", self.menu_handler.get_selected_paths()))
        self.actionEmail = QAction(QIcon.fromTheme("mail-send"), "Email")
        self.actionEmail.setShortcut(QKeySequence("Alt+S, E"))
        self.actionEmail.triggered.connect(lambda: self.menu_handler.queue_task("email", self.menu_handler.get_selected_paths()))
        self.actionZip = QAction(QIcon.fromTheme("application-x-archive"), "Zip")
        self.actionZip.setShortcut(QKeySequence("Alt+S, Z"))

        # Selection actions
        # handled in actions_dispatcher.py
        self.actionSelectAll = QAction(QIcon.fromTheme("edit-select-all"), "Select All")
        self.actionSelectAll.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.actionSelectNone = QAction(QIcon.fromTheme("edit-select-none"), "Select None")
        self.actionSelectNone.setShortcut(QKeySequence("Ctrl+Shift+A"))
        self.actionInvertSelection = QAction(QIcon.fromTheme("edit-select-invert"), "Invert Selection")
        self.actionInvertSelection.setShortcut(QKeySequence("Ctrl+I"))

        # New actions
        self.actionNewFolder = QAction(QIcon.fromTheme("folder-new"), "New folder")
        self.actionNewFolder.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.actionNewFolder.triggered.connect(lambda: self.menu_handler.queue_task("new_folder"))

        self.actionNewItem = QAction(QIcon.fromTheme("document-new"), "New item")
        self.actionNewItem.setShortcut(QKeySequence("Ctrl+N"))
        self.actionNewItem.triggered.connect(lambda: self.menu_handler.queue_task("new_item"))

        self.actionNewTextDocument = QAction(QIcon.fromTheme("document-new"), "New Text Document")
        self.actionNewTextDocument.setShortcut(QKeySequence("Ctrl+Shift+T"))
        self.actionNewTextDocument.triggered.connect(lambda: self.menu_handler.queue_task("new_text_document", self.menu_handler.fs_model.rootPath()))

        self.actionNewSpreadsheet = QAction(QIcon.fromTheme("x-office-spreadsheet"), "New Spreadsheet")
        self.actionNewSpreadsheet.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.actionNewPresentation = QAction(QIcon.fromTheme("x-office-presentation"), "New Presentation")
        self.actionNewPresentation.setShortcut(QKeySequence("Ctrl+Shift+P"))
        self.actionCreateNewFolder = QAction(QIcon.fromTheme("folder-new"), "Create New Folder")
        self.actionCreateNewFolder.setShortcut(QKeySequence("Ctrl+Shift+F"))
        self.actionCreateNewFolder.triggered.connect(lambda: self.menu_handler.queue_task("new_folder"))

        self.actionNewBitmapImage = QAction(QIcon.fromTheme("image-x-generic"), "Bitmap image")
        self.actionNewBitmapImage.setShortcut(QKeySequence("Ctrl+Shift+B"))
        self.actionNewWordDocument = QAction(QIcon.fromTheme("x-office-document"), "Microsoft Word Document")
        self.actionNewWordDocument.setShortcut(QKeySequence("Ctrl+Shift+W"))
        self.actionNewExcelWorksheet = QAction(QIcon.fromTheme("x-office-spreadsheet"), "Microsoft Excel Worksheet")
        self.actionNewExcelWorksheet.setShortcut(QKeySequence("Ctrl+Shift+E"))
        self.actionNewPowerPointPresentation = QAction(QIcon.fromTheme("x-office-presentation"), "Microsoft PowerPoint Presentation")
        self.actionNewPowerPointPresentation.setShortcut(QKeySequence("Ctrl+Shift+P"))
        self.actionNewCompressedFolder = QAction(QIcon.fromTheme("archive-insert"), "Compressed (zipped) Folder")
        self.actionNewCompressedFolder.setShortcut(QKeySequence("Ctrl+Shift+Z"))

        # Send To actions
        self.actionSendToDesktop = QAction(QIcon.fromTheme("user-desktop"), "Desktop (create shortcut)")
        self.actionSendToDesktop.setShortcut(QKeySequence("Alt+S, D"))
        self.actionSendToDesktop.triggered.connect(lambda: self.menu_handler.queue_task("send_to_desktop", self.menu_handler.get_selected_paths()))

        self.actionSendToDocuments = QAction(QIcon.fromTheme("folder-documents"), "Documents")
        self.actionSendToDocuments.setShortcut(QKeySequence("Alt+S, O"))
        self.actionSendToDocuments.triggered.connect(lambda: self.menu_handler.queue_task("send_to_documents", self.menu_handler.get_selected_paths()))

        self.actionSendToCompressedFolder = QAction(QIcon.fromTheme("archive-insert"), "Compressed (zipped) Folder")
        self.actionSendToCompressedFolder.setShortcut(QKeySequence("Alt+S, C"))
        self.actionSendToCompressedFolder.triggered.connect(lambda: self.menu_handler.queue_task("send_to_compressed_folder", self.menu_handler.get_selected_paths()))

        self.actionSendToMailRecipient = QAction(QIcon.fromTheme("mail-send"), "Mail Recipient")
        self.actionSendToMailRecipient.setShortcut(QKeySequence("Alt+S, M"))
        self.actionSendToBluetoothDevice = QAction(QIcon.fromTheme("bluetooth"), "Bluetooth Device")
        self.actionSendToBluetoothDevice.setShortcut(QKeySequence("Alt+S, B"))

        # Shift-held actions
        self.actionOpenAsAdmin = QAction(QIcon.fromTheme("dialog-password"), "Open as Administrator")
        self.actionOpenAsAdmin.setShortcut(QKeySequence("Ctrl+Shift+A"))
        self.actionTakeOwnership = QAction(QIcon.fromTheme("dialog-password"), "Take Ownership")
        self.actionTakeOwnership.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self.actionTakeOwnership.triggered.connect(lambda: self.menu_handler.queue_task("take_ownership", self.menu_handler.get_selected_paths()))

        self.actionOpenPowerShell = QAction(QIcon.fromTheme("utilities-terminal"), "Open PowerShell Window Here")
        self.actionOpenPowerShell.setShortcut(QKeySequence("Shift+F10"))
        self.actionAddToArchive = QAction(QIcon.fromTheme("archive-insert"), "Add to Archive")
        self.actionAddToArchive.setShortcut(QKeySequence("Ctrl+Shift+Z"))
        self.actionAddToArchive.triggered.connect(lambda: self.menu_handler.queue_task("add_to_archive", self.menu_handler.get_selected_paths()))

        self.actionScanWithAntivirus = QAction(QIcon.fromTheme("security-high"), "Scan with Antivirus")
        self.actionScanWithAntivirus.setShortcut(QKeySequence("Ctrl+Shift+V"))
        self.actionScanWithAntivirus.triggered.connect(lambda: self.menu_handler.queue_task("scan_with_antivirus", self.menu_handler.get_selected_paths()))
        self.actionExtendedProperties = QAction(QIcon.fromTheme("document-properties"), "Extended Properties")
        self.actionExtendedProperties.setShortcut(QKeySequence("Ctrl+Shift+X"))

        # Empty space actions
        self.actionPasteEmpty = QAction(QIcon.fromTheme("edit-paste"), "Paste")
        self.actionPasteEmpty.setShortcut(QKeySequence.StandardKey.Paste)
        self.actionPasteShortcutEmpty = QAction(QIcon.fromTheme("insert-link"), "Paste Shortcut")
        self.actionPasteShortcutEmpty.setShortcut(QKeySequence("Ctrl+Shift+V"))
        self.actionPropertiesEmpty = QAction(QIcon.fromTheme("document-properties"), "Properties")
        self.actionPropertiesEmpty.setShortcut(QKeySequence("Alt+Enter"))
        self.actionPropertiesEmpty.triggered.connect(lambda: self.menu_handler.queue_task("get_properties", self.menu_handler.get_current_directory()))

        # Empty space shift-held actions
        self.actionOpenCommandWindowEmpty = QAction(QIcon.fromTheme("utilities-terminal"), "Open command window here")
        self.actionOpenCommandWindowEmpty.setShortcut(QKeySequence("Shift+F10"))
        self.actionOpenPowerShellWindowEmpty = QAction(QIcon.fromTheme("utilities-terminal"), "Open PowerShell window here")
        self.actionOpenPowerShellWindowEmpty.setShortcut(QKeySequence("Shift+F10"))
        self.actionShowHideHiddenItems = QAction(QIcon.fromTheme("view-hidden"), "Show/Hide hidden items")
        self.actionShowHideHiddenItems.setShortcut(QKeySequence("Ctrl+H"))
        self.actionPersonalize = QAction(QIcon.fromTheme("preferences-desktop-theme"), "Personalize")
        self.actionPersonalize.setShortcut(QKeySequence("Ctrl+Shift+P"))
        self.actionDisplaySettings = QAction(QIcon.fromTheme("preferences-desktop-display"), "Display settings")
        self.actionDisplaySettings.setShortcut(QKeySequence("Ctrl+Shift+D"))

        # View actions
        self.actionViewExtraLargeIcons = QAction(QIcon.fromTheme("view-list-icons"), "Extra large icons")
        self.actionViewExtraLargeIcons.setShortcut(QKeySequence("Ctrl+Shift+1"))
        self.actionViewContent = QAction(QIcon.fromTheme("view-preview"), "Content")
        self.actionViewContent.setShortcut(QKeySequence("Ctrl+Shift+7"))

        # Set shortcuts
        self.actionPrint = QAction(QIcon.fromTheme("document-print"), "Print")
        self.actionPrint.setShortcut(QKeySequence.StandardKey.Print)
        self.actionCopyPath = QAction(QIcon.fromTheme("edit-copy"), "Copy Path")
        self.actionCopyPath.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.actionCopyPath.triggered.connect(lambda: self.menu_handler.queue_task("copy_path", self.menu_handler.get_selected_paths()))

        self.actionCopyAsPath = QAction(QIcon.fromTheme("edit-copy"), "Copy as Path")
        self.actionCopyAsPath.setShortcut(QKeySequence("Ctrl+Alt+C"))
        self.actionCopyAsPath.triggered.connect(lambda: self.menu_handler.queue_task("copy_as_path", self.menu_handler.get_selected_paths()))

        self.actionCreateShortcut = QAction(QIcon.fromTheme("insert-link"), "Create Shortcut")
        self.actionCreateShortcut.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.actionCreateShortcut.triggered.connect(lambda: self.menu_handler.queue_task("create_shortcut", self.menu_handler.get_selected_paths()))

        self.actionCompress = QAction(QIcon.fromTheme("archive-insert"), "Compress")
        self.actionCompress.setShortcut(QKeySequence("Ctrl+Alt+Z"))
        self.actionCompress.triggered.connect(self.menu_handler.prepare_compress)

        self.actionExtract = QAction(QIcon.fromTheme("archive-extract"), "Extract")
        self.actionExtract.setShortcut(QKeySequence("Ctrl+Alt+X"))
        self.actionExtract.triggered.connect(self.menu_handler.prepare_extract)

        self.actionShare = QAction(QIcon.fromTheme("document-share"), "Share")
        self.actionShare.setShortcut(QKeySequence("Alt+S"))

        self.actionEdit = QAction(QIcon.fromTheme("document-edit"), "Edit")
