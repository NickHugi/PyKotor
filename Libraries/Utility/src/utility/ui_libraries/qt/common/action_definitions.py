from __future__ import annotations

from qtpy.QtCore import Qt
from qtpy.QtGui import QAction, QIcon, QKeySequence


class FileExplorerActions:
    """Creates actions for a file browser/manager/explorer. Any and all possible actions should be defined here."""
    def __init__(self):  # noqa: PLR0915
        # Open actions
        self.actionOpen = QAction(QIcon.fromTheme("document-open"), "Open")
        self.actionOpen.setShortcut(QKeySequence.StandardKey.Open)

        self.actionOpenAsAdmin = QAction(QIcon.fromTheme("dialog-password"), "Open as Administrator")
        self.actionOpenAsAdmin.setShortcut(QKeySequence("Ctrl+Shift+A"))

        self.actionOpenInNewWindow = QAction(QIcon.fromTheme("window-new"), "Open in New Window")
        self.actionOpenInNewWindow.setShortcut(QKeySequence("Ctrl+Enter"))

        self.actionOpenInNewTab = QAction(QIcon.fromTheme("tab-new"), "Open in New Tab")
        self.actionOpenInNewTab.setShortcut(QKeySequence("Alt+Enter"))

        self.actionOpenWith = QAction(QIcon.fromTheme("document-open"), "Open With...")
        self.actionOpenWith.setShortcut(QKeySequence("Alt+O"))

        self.actionProperties = QAction(QIcon.fromTheme("document-properties"), "Properties")
        self.actionProperties.setShortcut(QKeySequence("Alt+P"))

        self.actionOpenTerminal = QAction(QIcon.fromTheme("utilities-terminal"), "Open Terminal")
        self.actionOpenTerminal.setShortcut(QKeySequence("Shift+F10"))

        self.actionCut = QAction(QIcon.fromTheme("edit-cut"), "Cut")
        self.actionCut.setShortcut(QKeySequence.StandardKey.Cut)

        self.actionCopy = QAction(QIcon.fromTheme("edit-copy"), "Copy")
        self.actionCopy.setShortcut(QKeySequence.StandardKey.Copy)

        self.actionPaste = QAction(QIcon.fromTheme("edit-paste"), "Paste")
        self.actionPaste.setShortcut(QKeySequence.StandardKey.Paste)

        self.actionDelete = QAction(QIcon.fromTheme("edit-delete"), "Delete")
        self.actionDelete.setShortcut(QKeySequence.StandardKey.Delete)

        self.actionRename = QAction(QIcon.fromTheme("edit-rename"), "Rename")
        self.actionRename.setShortcut(QKeySequence(Qt.Key.Key_F2))

        self.actionExtraLargeIcons = QAction(QIcon.fromTheme("view-list-icons"), "Extra large icons")
        self.actionExtraLargeIcons.setShortcut(QKeySequence("Ctrl+Shift+1"))

        self.actionLargeIcons = QAction(QIcon.fromTheme("view-list-icons"), "Large icons")
        self.actionLargeIcons.setShortcut(QKeySequence("Ctrl+Shift+2"))

        self.actionMediumIcons = QAction(QIcon.fromTheme("view-list-icons"), "Medium icons")
        self.actionMediumIcons.setShortcut(QKeySequence("Ctrl+Shift+3"))

        self.actionSmallIcons = QAction(QIcon.fromTheme("view-list-icons"), "Small icons")
        self.actionSmallIcons.setShortcut(QKeySequence("Ctrl+Shift+4"))

        self.actionListView = QAction(QIcon.fromTheme("view-list-details"), "List")
        self.actionListView.setShortcut(QKeySequence("Ctrl+Shift+5"))

        self.actionDetailView = QAction(QIcon.fromTheme("view-list-tree"), "Details")
        self.actionDetailView.setShortcut(QKeySequence("Ctrl+Shift+6"))

        self.actionTiles = QAction(QIcon.fromTheme("view-list-icons"), "Tiles")
        self.actionTiles.setShortcut(QKeySequence("Ctrl+Shift+7"))

        self.actionContent = QAction(QIcon.fromTheme("view-list-text"), "Content")
        self.actionContent.setShortcut(QKeySequence("Ctrl+Shift+8"))

        self.actionShowHideHiddenItems = QAction(QIcon.fromTheme("view-hidden"), "Show/Hide hidden items")
        self.actionShowHideHiddenItems.setCheckable(True)
        self.actionShowHideHiddenItems.setShortcut(QKeySequence("Ctrl+H"))

        self.actionRefresh = QAction(QIcon.fromTheme("view-refresh"), "Refresh")
        self.actionRefresh.setShortcut(QKeySequence("F5"))

        self.actionShowSystem = QAction(QIcon.fromTheme("computer"), "Show System")
        self.actionShowSystem.setCheckable(True)
        self.actionShowSystem.setShortcut(QKeySequence("Alt+V, Y"))

        self.actionShowAllDirectories = QAction(QIcon.fromTheme("folder-open"), "Show All Directories")
        self.actionShowAllDirectories.setCheckable(True)
        self.actionShowAllDirectories.setShortcut(QKeySequence("Alt+V, A"))

        self.actionSortByName = QAction(QIcon.fromTheme("view-sort-ascending"), "Name")
        self.actionSortByName.setShortcut(QKeySequence("Ctrl+Shift+N"))

        self.actionSortByDateModified = QAction(QIcon.fromTheme("view-sort-ascending"), "Date modified")
        self.actionSortByDateModified.setShortcut(QKeySequence("Ctrl+Shift+E"))

        self.actionSortByType = QAction(QIcon.fromTheme("view-sort-ascending"), "Type")
        self.actionSortByType.setShortcut(QKeySequence("Ctrl+Shift+T"))

        self.actionSortBySize = QAction(QIcon.fromTheme("view-sort-ascending"), "Size")
        self.actionSortBySize.setShortcut(QKeySequence("Ctrl+Shift+S"))

        self.actionSortByDateCreated = QAction(QIcon.fromTheme("view-sort-ascending"), "Date created")
        self.actionSortByDateCreated.setShortcut(QKeySequence("Ctrl+Shift+C"))

        self.actionSortByAuthor = QAction(QIcon.fromTheme("view-sort-ascending"), "Authors")
        self.actionSortByAuthor.setShortcut(QKeySequence("Ctrl+Shift+A"))

        self.actionSortByTitle = QAction(QIcon.fromTheme("view-sort-ascending"), "Title")
        self.actionSortByTitle.setShortcut(QKeySequence("Ctrl+Shift+I"))

        self.actionSortByTags = QAction(QIcon.fromTheme("view-sort-ascending"), "Tags")
        self.actionSortByTags.setShortcut(QKeySequence("Ctrl+Shift+G"))

        self.actionToggleSortOrder = QAction(QIcon.fromTheme("view-sort"), "Toggle Sort Order")
        self.actionToggleSortOrder.setShortcut(QKeySequence("Ctrl+Shift+O"))

        self.actionGroupByNone = QAction(QIcon.fromTheme("view-group"), "(None)")
        self.actionGroupByNone.setShortcut(QKeySequence("Alt+G, N"))

        self.actionGroupByName = QAction(QIcon.fromTheme("view-group"), "Name")
        self.actionGroupByName.setShortcut(QKeySequence("Alt+G, A"))

        self.actionGroupByDateModified = QAction(QIcon.fromTheme("view-group"), "Date modified")
        self.actionGroupByDateModified.setShortcut(QKeySequence("Alt+G, M"))

        self.actionGroupByDateCreated = QAction(QIcon.fromTheme("view-group"), "Date created")
        self.actionGroupByDateCreated.setShortcut(QKeySequence("Alt+G, C"))

        self.actionSelectAll = QAction(QIcon.fromTheme("edit-select-all"), "Select All")
        self.actionSelectAll.setShortcut(QKeySequence.StandardKey.SelectAll)

        self.actionGroupByType = QAction(QIcon.fromTheme("view-group"), "Type")
        self.actionGroupByType.setShortcut(QKeySequence("Alt+G, T"))

        self.actionGroupBySize = QAction(QIcon.fromTheme("view-group"), "Size")
        self.actionGroupBySize.setShortcut(QKeySequence("Alt+G, S"))

        self.actionSelectNone = QAction(QIcon.fromTheme("edit-select-none"), "Select None")
        self.actionSelectNone.setShortcut(QKeySequence("Ctrl+Shift+A"))

        self.actionNewFolder = QAction(QIcon.fromTheme("folder-new"), "New folder")
        self.actionNewFolder.setShortcut(QKeySequence("Ctrl+Shift+N"))

        self.actionNewBlankFile = QAction(QIcon.fromTheme("document-new"), "New Blank File")
        self.actionNewBlankFile.setShortcut(QKeySequence("Ctrl+N"))

        self.actionNewTextDocument = QAction(QIcon.fromTheme("document-new"), "New Text Document")
        self.actionNewTextDocument.setShortcut(QKeySequence("Ctrl+Shift+T"))

        self.actionCreateNewFolder = QAction(QIcon.fromTheme("folder-new"), "Create New Folder")
        self.actionCreateNewFolder.setShortcut(QKeySequence("Ctrl+Shift+F"))

        self.actionNewCompressedFolder = QAction(QIcon.fromTheme("archive-insert"), "Compressed (zipped) Folder")
        self.actionNewCompressedFolder.setShortcut(QKeySequence("Ctrl+Shift+Z"))

        self.actionSendToDesktop = QAction(QIcon.fromTheme("user-desktop"), "Desktop (create shortcut)")
        self.actionSendToDesktop.setShortcut(QKeySequence("Alt+S, D"))

        self.actionSendToDocuments = QAction(QIcon.fromTheme("folder-documents"), "Documents")
        self.actionSendToDocuments.setShortcut(QKeySequence("Alt+S, O"))

        self.actionSendToCompressedFolder = QAction(QIcon.fromTheme("archive-insert"), "Compressed (zipped) Folder")
        self.actionSendToCompressedFolder.setShortcut(QKeySequence("Alt+S, C"))

        self.actionTakeOwnership = QAction(QIcon.fromTheme("dialog-password"), "Take Ownership")
        self.actionTakeOwnership.setShortcut(QKeySequence("Ctrl+Shift+O"))

        self.actionAddToArchive = QAction(QIcon.fromTheme("archive-insert"), "Add to Archive")
        self.actionAddToArchive.setShortcut(QKeySequence("Ctrl+Shift+Z"))

        self.actionPersonalize = QAction(QIcon.fromTheme("preferences-desktop-theme"), "Personalize")
        self.actionPersonalize.setShortcut(QKeySequence("Ctrl+Shift+P"))

        self.actionDisplaySettings = QAction(QIcon.fromTheme("preferences-desktop-display"), "Display settings")
        self.actionDisplaySettings.setShortcut(QKeySequence("Ctrl+Shift+D"))

        self.actionViewContent = QAction(QIcon.fromTheme("view-list-text"), "Content")
        self.actionViewContent.setShortcut(QKeySequence("Ctrl+Shift+7"))

        self.actionCopyPath = QAction(QIcon.fromTheme("edit-copy"), "Copy Path")
        self.actionCopyPath.setShortcut(QKeySequence("Ctrl+Shift+C"))

        self.actionPinToQuickAccess = QAction(QIcon.fromTheme("bookmark-new"), "Pin to Quick access")
        self.actionPinToQuickAccess.setShortcut(QKeySequence("Ctrl+Q"))

        self.actionPasteShortcut = QAction(QIcon.fromTheme("insert-link"), "Paste Shortcut")
        self.actionPasteShortcut.setShortcut(QKeySequence("Ctrl+Shift+V"))

        self.actionCopyAsPath = QAction(QIcon.fromTheme("edit-copy"), "Copy as Path")
        self.actionCopyAsPath.setShortcut(QKeySequence("Ctrl+Alt+C"))

        self.actionCreateShortcut = QAction(QIcon.fromTheme("insert-link"), "Create Shortcut")
        self.actionCreateShortcut.setShortcut(QKeySequence("Ctrl+Shift+S"))

        self.actionCompress = QAction(QIcon.fromTheme("archive-insert"), "Compress")
        self.actionCompress.setShortcut(QKeySequence("Ctrl+Alt+Z"))

        self.actionExtract = QAction(QIcon.fromTheme("archive-extract"), "Extract")
        self.actionExtract.setShortcut(QKeySequence("Ctrl+Alt+X"))

        self.actionEdit = QAction(QIcon.fromTheme("document-edit"), "Edit")
        self.actionEdit.setShortcut(QKeySequence("F2"))

        self.actionCopyTo = QAction(QIcon.fromTheme("edit-copy"), "Copy To...")
        self.actionCopyTo.setShortcut(QKeySequence("F5"))

        self.actionMoveTo = QAction(QIcon.fromTheme("edit-cut"), "Move To...")
        self.actionMoveTo.setShortcut(QKeySequence("F6"))

        self.actionDuplicateFile = QAction(QIcon.fromTheme("edit-copy"), "Duplicate")
        self.actionDuplicateFile.setShortcut(QKeySequence("Ctrl+D"))

        self.actionSetFileAttributes = QAction(QIcon.fromTheme("document-properties"), "Set File Attributes...")
        self.actionSetFileAttributes.setShortcut(QKeySequence("Ctrl+B"))

        self.actionInvertSelection = QAction("Invert Selection")
        self.actionInvertSelection.setShortcut(QKeySequence("Ctrl+I"))

        self.actionGoBack = QAction(QIcon.fromTheme("go-previous"), "Back")
        self.actionGoBack.setShortcut(QKeySequence.StandardKey.Back)

        self.actionGoForward = QAction(QIcon.fromTheme("go-next"), "Forward")
        self.actionGoForward.setShortcut(QKeySequence.StandardKey.Forward)

        self.actionGoUp = QAction(QIcon.fromTheme("go-up"), "Up One Level")
        self.actionGoUp.setShortcut(QKeySequence("Alt+Up"))

        self.actionGoToRoot = QAction(QIcon.fromTheme("go-home"), "Go to Root")
        self.actionGoToRoot.setShortcut(QKeySequence("Ctrl+/"))

        self.actionAddBookmark = QAction(QIcon.fromTheme("bookmark-new"), "Add Bookmark")
        self.actionAddBookmark.setShortcut(QKeySequence("Ctrl+D"))

        self.actionOrganizeBookmarks = QAction(QIcon.fromTheme("bookmarks-organize"), "Organize Bookmarks...")
        self.actionOrganizeBookmarks.setShortcut(QKeySequence("Ctrl+B"))

        self.actionCompareByContent = QAction(QIcon.fromTheme("document-compare"), "Compare by Content")
        self.actionCompareByContent.setShortcut(QKeySequence("Ctrl+M"))

        self.actionCustomizeToolbars = QAction(QIcon.fromTheme("configure-toolbars"), "Customize Toolbars...")
        self.actionCustomizeToolbars.setShortcut(QKeySequence("Ctrl+Shift+Alt+T"))

        self.actionOptions = QAction(QIcon.fromTheme("configure"), "Options...")
        self.actionOptions.setShortcut(QKeySequence("Ctrl+,"))

        self.actionHelp = QAction(QIcon.fromTheme("help-contents"), "Help")
        self.actionHelp.setShortcut(QKeySequence.StandardKey.HelpContents)

        self.actionViewThumbnails = QAction(QIcon.fromTheme("view-preview"), "Thumbnails")
        self.actionViewThumbnails.setShortcut(QKeySequence("Ctrl+Shift+T"))

        self.actionShowCommandPrompt = QAction(QIcon.fromTheme("utilities-terminal"), "Show Command Prompt")
        self.actionShowCommandPrompt.setShortcut(QKeySequence("Ctrl+P"))

        self.actionSaveDirectoryListing = QAction(QIcon.fromTheme("document-save"), "Save Directory Listing...")
        self.actionSaveDirectoryListing.setShortcut(QKeySequence("Ctrl+Shift+S"))

        self.actionDestroyFiles = QAction(QIcon.fromTheme("edit-delete-shred"), "Destroy File(s)...")
        self.actionDestroyFiles.setShortcut(QKeySequence("Ctrl+Shift+Delete"))
        self.actionShowFileOperations = QAction(QIcon.fromTheme("view-process-all"), "Show File Operations")
        self.actionShowFileOperations.setShortcut(QKeySequence("Ctrl+Shift+O"))

        self.actionPreviewPane = QAction(QIcon.fromTheme("view-preview"), "Preview Pane")
        self.actionPreviewPane.setShortcut(QKeySequence("Ctrl+Shift+P"))

        self.actionDetailsPane = QAction(QIcon.fromTheme("view-list-tree"), "Details Pane")
        self.actionDetailsPane.setShortcut(QKeySequence("Ctrl+Shift+D"))

        self.actionNavigationPane = QAction(QIcon.fromTheme("view-list-icons"), "Navigation Pane")
        self.actionNavigationPane.setShortcut(QKeySequence("Ctrl+Shift+N"))

        self.actionBatchRename = QAction(QIcon.fromTheme("edit-rename"), "Batch Rename")
        self.actionBatchRename.setShortcut(QKeySequence("Ctrl+Shift+R"))

        self.actionDuplicateFinder = QAction(QIcon.fromTheme("edit-find-replace"), "Find Duplicate Files")
        self.actionDuplicateFinder.setShortcut(QKeySequence("Ctrl+Shift+D"))

        self.actionHashGenerator = QAction(QIcon.fromTheme("document-encrypt"), "Generate File Hashes")
        self.actionHashGenerator.setShortcut(QKeySequence("Ctrl+Shift+H"))

        self.actionPermissionsEditor = QAction(QIcon.fromTheme("document-edit-sign"), "Edit File Permissions")
        self.actionPermissionsEditor.setShortcut(QKeySequence("Ctrl+Shift+E"))

        self.actionFileShredder = QAction(QIcon.fromTheme("edit-delete-shred"), "Securely Delete Files")
        self.actionFileShredder.setShortcut(QKeySequence("Ctrl+Shift+Del"))

        self.actionFileComparison = QAction(QIcon.fromTheme("document-compare"), "Compare Files")
        self.actionFileComparison.setShortcut(QKeySequence("Ctrl+Shift+M"))

        self.actionOpenInTerminal = QAction(QIcon.fromTheme("utilities-terminal"), "Open in Terminal")
        self.actionOpenInTerminal.setShortcut(QKeySequence("Ctrl+Shift+T"))

        self.actionCustomizeContextMenu = QAction(QIcon.fromTheme("configure"), "Customize Context Menu")
        self.actionCustomizeContextMenu.setShortcut(QKeySequence("Ctrl+Shift+X"))
