
################################################################################
## Form generated from reading UI file 'tlk.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMenuBar,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTableView


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(463, 577)
        self.actionGoTo = QAction(MainWindow)
        self.actionGoTo.setObjectName("actionGoTo")
        self.actionFind = QAction(MainWindow)
        self.actionFind.setObjectName("actionFind")
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSaveAs = QAction(MainWindow)
        self.actionSaveAs.setObjectName("actionSaveAs")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName("actionRevert")
        self.actionClose = QAction(MainWindow)
        self.actionClose.setObjectName("actionClose")
        self.actionInsert = QAction(MainWindow)
        self.actionInsert.setObjectName("actionInsert")
        self.actionAuto_detect_slower = QAction(MainWindow)
        self.actionAuto_detect_slower.setObjectName("actionAuto_detect_slower")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName("splitter")
        self.splitter.setOrientation(Qt.Vertical)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.searchBox = QGroupBox(self.layoutWidget)
        self.searchBox.setObjectName("searchBox")
        self.horizontalLayout_2 = QHBoxLayout(self.searchBox)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.searchEdit = QLineEdit(self.searchBox)
        self.searchEdit.setObjectName("searchEdit")

        self.horizontalLayout_2.addWidget(self.searchEdit)

        self.searchButton = QPushButton(self.searchBox)
        self.searchButton.setObjectName("searchButton")

        self.horizontalLayout_2.addWidget(self.searchButton)


        self.horizontalLayout_3.addWidget(self.searchBox)

        self.jumpBox = QGroupBox(self.layoutWidget)
        self.jumpBox.setObjectName("jumpBox")
        self.horizontalLayout_4 = QHBoxLayout(self.jumpBox)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.jumpSpinbox = QSpinBox(self.jumpBox)
        self.jumpSpinbox.setObjectName("jumpSpinbox")
        self.jumpSpinbox.setMinimum(-2147483648)
        self.jumpSpinbox.setMaximum(2147483647)

        self.horizontalLayout_4.addWidget(self.jumpSpinbox)

        self.jumpButton = QPushButton(self.jumpBox)
        self.jumpButton.setObjectName("jumpButton")

        self.horizontalLayout_4.addWidget(self.jumpButton)


        self.horizontalLayout_3.addWidget(self.jumpBox)

        self.horizontalLayout_3.setStretch(0, 5)
        self.horizontalLayout_3.setStretch(1, 3)

        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.talkTable = RobustTableView(self.layoutWidget)
        self.talkTable.setObjectName("talkTable")
        self.talkTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.talkTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.talkTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.talkTable.horizontalHeader().setVisible(False)
        self.talkTable.horizontalHeader().setHighlightSections(False)
        self.talkTable.horizontalHeader().setStretchLastSection(True)

        self.verticalLayout.addWidget(self.talkTable)

        self.splitter.addWidget(self.layoutWidget)
        self.layoutWidget1 = QWidget(self.splitter)
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.verticalLayout_2 = QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.textEdit = QPlainTextEdit(self.layoutWidget1)
        self.textEdit.setObjectName("textEdit")
        self.textEdit.setEnabled(False)
        self.textEdit.setMaximumSize(QSize(16777215, 200))

        self.verticalLayout_2.addWidget(self.textEdit)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QLabel(self.layoutWidget1)
        self.label.setObjectName("label")

        self.horizontalLayout.addWidget(self.label)

        self.soundEdit = QLineEdit(self.layoutWidget1)
        self.soundEdit.setObjectName("soundEdit")
        self.soundEdit.setEnabled(False)
        self.soundEdit.setMaxLength(16)

        self.horizontalLayout.addWidget(self.soundEdit)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.splitter.addWidget(self.layoutWidget1)

        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 463, 21))
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuLanguage = QMenu(self.menubar)
        self.menuLanguage.setObjectName("menuLanguage")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuLanguage.menuAction())
        self.menuView.addAction(self.actionGoTo)
        self.menuView.addAction(self.actionFind)
        self.menuView.addAction(self.actionInsert)
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionClose)
        self.menuLanguage.addAction(self.actionAuto_detect_slower)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "MainWindow", None))
        self.actionGoTo.setText(QCoreApplication.translate("MainWindow", "Go to", None))
        self.actionFind.setText(QCoreApplication.translate("MainWindow", "Find", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", "New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", "Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", "Save", None))
        self.actionSaveAs.setText(QCoreApplication.translate("MainWindow", "Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", "Revert", None))
        self.actionClose.setText(QCoreApplication.translate("MainWindow", "Exit", None))
        self.actionInsert.setText(QCoreApplication.translate("MainWindow", "Insert", None))
        self.actionAuto_detect_slower.setText(QCoreApplication.translate("MainWindow", "Auto-detect (slower)", None))
        self.searchBox.setTitle(QCoreApplication.translate("MainWindow", "Search", None))
        self.searchButton.setText(QCoreApplication.translate("MainWindow", "Search", None))
        self.jumpBox.setTitle(QCoreApplication.translate("MainWindow", "Go To Line", None))
        self.jumpButton.setText(QCoreApplication.translate("MainWindow", "Jump", None))
        self.label.setText(QCoreApplication.translate("MainWindow", "Sound ResRef:", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", "Tools", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
        self.menuLanguage.setTitle(QCoreApplication.translate("MainWindow", "Language", None))
    # retranslateUi

