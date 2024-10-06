# -*- coding: utf-8 -*-

# 
# Copyright (C) 2016 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only
# 

################################################################################
## Form generated from reading UI file 'qfiledialog.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QListWidgetItem, QSizePolicy,
    QSplitter, QStackedWidget, QToolButton, QVBoxLayout,
    QWidget)

from private.qfiledialog_p import (QFileDialogComboBox, QFileDialogLineEdit, QFileDialogListView, QFileDialogTreeView)
from private.qsidebar_p import QSidebar

class Ui_QFileDialog(object):
    def setupUi(self, QFileDialog):
        if not QFileDialog.objectName():
            QFileDialog.setObjectName(u"QFileDialog")
        QFileDialog.resize(521, 316)
        QFileDialog.setSizeGripEnabled(True)
        self.gridLayout = QGridLayout(QFileDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.lookInLabel = QLabel(QFileDialog)
        self.lookInLabel.setObjectName(u"lookInLabel")

        self.gridLayout.addWidget(self.lookInLabel, 0, 0, 1, 1)

        self.hboxLayout = QHBoxLayout()
        self.hboxLayout.setObjectName(u"hboxLayout")
        self.lookInCombo = QFileDialogComboBox(QFileDialog)
        self.lookInCombo.setObjectName(u"lookInCombo")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lookInCombo.sizePolicy().hasHeightForWidth())
        self.lookInCombo.setSizePolicy(sizePolicy)
        self.lookInCombo.setMinimumSize(QSize(50, 0))

        self.hboxLayout.addWidget(self.lookInCombo)

        self.backButton = QToolButton(QFileDialog)
        self.backButton.setObjectName(u"backButton")

        self.hboxLayout.addWidget(self.backButton)

        self.forwardButton = QToolButton(QFileDialog)
        self.forwardButton.setObjectName(u"forwardButton")

        self.hboxLayout.addWidget(self.forwardButton)

        self.toParentButton = QToolButton(QFileDialog)
        self.toParentButton.setObjectName(u"toParentButton")

        self.hboxLayout.addWidget(self.toParentButton)

        self.newFolderButton = QToolButton(QFileDialog)
        self.newFolderButton.setObjectName(u"newFolderButton")

        self.hboxLayout.addWidget(self.newFolderButton)

        self.listModeButton = QToolButton(QFileDialog)
        self.listModeButton.setObjectName(u"listModeButton")

        self.hboxLayout.addWidget(self.listModeButton)

        self.detailModeButton = QToolButton(QFileDialog)
        self.detailModeButton.setObjectName(u"detailModeButton")

        self.hboxLayout.addWidget(self.detailModeButton)


        self.gridLayout.addLayout(self.hboxLayout, 0, 1, 1, 2)

        self.splitter = QSplitter(QFileDialog)
        self.splitter.setObjectName(u"splitter")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy1)
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.sidebar = QSidebar(self.splitter)
        self.sidebar.setObjectName(u"sidebar")
        self.splitter.addWidget(self.sidebar)
        self.frame = QFrame(self.splitter)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Raised)
        self.vboxLayout = QVBoxLayout(self.frame)
        self.vboxLayout.setSpacing(0)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.vboxLayout.setContentsMargins(0, 0, 0, 0)
        self.stackedWidget = QStackedWidget(self.frame)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.vboxLayout1 = QVBoxLayout(self.page)
        self.vboxLayout1.setSpacing(0)
        self.vboxLayout1.setObjectName(u"vboxLayout1")
        self.vboxLayout1.setContentsMargins(0, 0, 0, 0)
        self.listView = QFileDialogListView(self.page)
        self.listView.setObjectName(u"listView")

        self.vboxLayout1.addWidget(self.listView)

        self.stackedWidget.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.vboxLayout2 = QVBoxLayout(self.page_2)
        self.vboxLayout2.setSpacing(0)
        self.vboxLayout2.setObjectName(u"vboxLayout2")
        self.vboxLayout2.setContentsMargins(0, 0, 0, 0)
        self.treeView = QFileDialogTreeView(self.page_2)
        self.treeView.setObjectName(u"treeView")

        self.vboxLayout2.addWidget(self.treeView)

        self.stackedWidget.addWidget(self.page_2)

        self.vboxLayout.addWidget(self.stackedWidget)

        self.splitter.addWidget(self.frame)

        self.gridLayout.addWidget(self.splitter, 1, 0, 1, 3)

        self.fileNameLabel = QLabel(QFileDialog)
        self.fileNameLabel.setObjectName(u"fileNameLabel")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.fileNameLabel.sizePolicy().hasHeightForWidth())
        self.fileNameLabel.setSizePolicy(sizePolicy2)
        self.fileNameLabel.setMinimumSize(QSize(0, 0))

        self.gridLayout.addWidget(self.fileNameLabel, 2, 0, 1, 1)

        self.fileNameEdit = QFileDialogLineEdit(QFileDialog)
        self.fileNameEdit.setObjectName(u"fileNameEdit")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(1)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.fileNameEdit.sizePolicy().hasHeightForWidth())
        self.fileNameEdit.setSizePolicy(sizePolicy3)

        self.gridLayout.addWidget(self.fileNameEdit, 2, 1, 1, 1)

        self.buttonBox = QDialogButtonBox(QFileDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Vertical)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.gridLayout.addWidget(self.buttonBox, 2, 2, 2, 1)

        self.fileTypeLabel = QLabel(QFileDialog)
        self.fileTypeLabel.setObjectName(u"fileTypeLabel")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.fileTypeLabel.sizePolicy().hasHeightForWidth())
        self.fileTypeLabel.setSizePolicy(sizePolicy4)

        self.gridLayout.addWidget(self.fileTypeLabel, 3, 0, 1, 1)

        self.fileTypeCombo = QComboBox(QFileDialog)
        self.fileTypeCombo.setObjectName(u"fileTypeCombo")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.fileTypeCombo.sizePolicy().hasHeightForWidth())
        self.fileTypeCombo.setSizePolicy(sizePolicy5)

        self.gridLayout.addWidget(self.fileTypeCombo, 3, 1, 1, 1)

        QWidget.setTabOrder(self.lookInCombo, self.backButton)
        QWidget.setTabOrder(self.backButton, self.forwardButton)
        QWidget.setTabOrder(self.forwardButton, self.toParentButton)
        QWidget.setTabOrder(self.toParentButton, self.newFolderButton)
        QWidget.setTabOrder(self.newFolderButton, self.listModeButton)
        QWidget.setTabOrder(self.listModeButton, self.detailModeButton)
        QWidget.setTabOrder(self.detailModeButton, self.sidebar)
        QWidget.setTabOrder(self.sidebar, self.treeView)
        QWidget.setTabOrder(self.treeView, self.listView)
        QWidget.setTabOrder(self.listView, self.fileNameEdit)
        QWidget.setTabOrder(self.fileNameEdit, self.buttonBox)
        QWidget.setTabOrder(self.buttonBox, self.fileTypeCombo)

        self.retranslateUi(QFileDialog)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(QFileDialog)
    # setupUi

    def retranslateUi(self, QFileDialog):
        self.lookInLabel.setText(QCoreApplication.translate("QFileDialog", u"Look in:", None))
#if QT_CONFIG(tooltip)
        self.backButton.setToolTip(QCoreApplication.translate("QFileDialog", u"Back", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.backButton.setAccessibleName(QCoreApplication.translate("QFileDialog", u"Back", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(accessibility)
        self.backButton.setAccessibleDescription(QCoreApplication.translate("QFileDialog", u"Go back", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(shortcut)
        self.backButton.setShortcut(QCoreApplication.translate("QFileDialog", u"Alt+Left", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.forwardButton.setToolTip(QCoreApplication.translate("QFileDialog", u"Forward", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.forwardButton.setAccessibleName(QCoreApplication.translate("QFileDialog", u"Forward", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(accessibility)
        self.forwardButton.setAccessibleDescription(QCoreApplication.translate("QFileDialog", u"Go forward", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(shortcut)
        self.forwardButton.setShortcut(QCoreApplication.translate("QFileDialog", u"Alt+Right", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.toParentButton.setToolTip(QCoreApplication.translate("QFileDialog", u"Parent Directory", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.toParentButton.setAccessibleName(QCoreApplication.translate("QFileDialog", u"Parent Directory", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(accessibility)
        self.toParentButton.setAccessibleDescription(QCoreApplication.translate("QFileDialog", u"Go to the parent directory", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(shortcut)
        self.toParentButton.setShortcut(QCoreApplication.translate("QFileDialog", u"Alt+Up", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.newFolderButton.setToolTip(QCoreApplication.translate("QFileDialog", u"Create New Folder", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.newFolderButton.setAccessibleName(QCoreApplication.translate("QFileDialog", u"Create New Folder", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(accessibility)
        self.newFolderButton.setAccessibleDescription(QCoreApplication.translate("QFileDialog", u"Create a New Folder", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(tooltip)
        self.listModeButton.setToolTip(QCoreApplication.translate("QFileDialog", u"List View", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.listModeButton.setAccessibleName(QCoreApplication.translate("QFileDialog", u"List View", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(accessibility)
        self.listModeButton.setAccessibleDescription(QCoreApplication.translate("QFileDialog", u"Change to list view mode", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(tooltip)
        self.detailModeButton.setToolTip(QCoreApplication.translate("QFileDialog", u"Detail View", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.detailModeButton.setAccessibleName(QCoreApplication.translate("QFileDialog", u"Detail View", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(accessibility)
        self.detailModeButton.setAccessibleDescription(QCoreApplication.translate("QFileDialog", u"Change to detail view mode", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(accessibility)
        self.sidebar.setAccessibleName(QCoreApplication.translate("QFileDialog", u"Sidebar", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(accessibility)
        self.sidebar.setAccessibleDescription(QCoreApplication.translate("QFileDialog", u"List of places and bookmarks", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(accessibility)
        self.listView.setAccessibleName(QCoreApplication.translate("QFileDialog", u"Files", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(accessibility)
        self.treeView.setAccessibleName(QCoreApplication.translate("QFileDialog", u"Files", None))
#endif // QT_CONFIG(accessibility)
        self.fileTypeLabel.setText(QCoreApplication.translate("QFileDialog", u"Files of type:", None))
        pass
    # retranslateUi

